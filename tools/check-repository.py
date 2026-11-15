#!/usr/bin/env python3
"""Static repository checks only. Never imports or runs the ONT tool."""

import ast
import json
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
errors = []


def problem(path, message, line=None):
    suffix = ":" + str(line) if line else ""
    errors.append(str(path.relative_to(ROOT)) + suffix + "：" + message)


def no_fences(text):
    lines = []
    fenced = False
    for line in text.splitlines():
        if re.match(r"^\s*(```|~~~)", line):
            fenced = not fenced
            lines.append("")
        else:
            lines.append("" if fenced else line)
    return "\n".join(lines)


def anchors(path):
    used = {}
    result = set()
    for line in no_fences(path.read_text(encoding="utf-8")).splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
        if not match:
            continue
        title = re.sub(r"`|\*", "", match.group(1)).lower().strip()
        title = "".join(c for c in title if c in "-_" or not unicodedata.category(c).startswith(("P", "S")))
        title = re.sub(r"\s", "-", title)
        count = used.get(title, 0)
        used[title] = count + 1
        result.add(title + ("-" + str(count) if count else ""))
    return result


files = [p for p in ROOT.rglob("*") if p.is_file() and not any(part in (".git", "__pycache__", ".venv") for part in p.relative_to(ROOT).parts)]
markdown_count = python_count = json_count = link_count = 0
for path in files:
    rel = path.relative_to(ROOT)
    if path.suffix.lower() in (".har", ".pcap", ".pcapng", ".cfg", ".jar", ".key", ".pfx", ".p12", ".dpapi") or path.name.endswith((".local.json", ".secret.json")):
        problem(path, "发现不应位于公开工作区的运行或原始文件")
    if path.suffix not in (".md", ".py", ".json") and path.name not in ("LICENSE", ".gitignore", ".gitattributes"):
        continue
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8", "strict")
    except UnicodeError:
        problem(path, "不是有效 UTF-8")
        continue
    if raw.startswith(b"\xef\xbb\xbf"):
        problem(path, "包含 UTF-8 BOM")
    if "\ufffd" in text:
        problem(path, "含解码替代字符")
    for number, line in enumerate(text.splitlines(), 1):
        if line.rstrip() != line:
            problem(path, "行尾空白", number)
        if re.search(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", line):
            problem(path, "疑似私钥头，不显示内容", number)
        if re.search(r"(?<!\d)1[3-9]\d{9}(?!\d)", line):
            problem(path, "疑似手机号，不显示内容", number)
        if re.search(r"(?i)(?<![0-9a-f])(?:[0-9a-f]{2}:){5}[0-9a-f]{2}(?![0-9a-f])", line):
            problem(path, "发现完整 MAC，公开示例应使用明确遮挡", number)
    if path.suffix == ".py":
        python_count += 1
        try:
            ast.parse(text, filename=str(rel))
        except SyntaxError:
            problem(path, "Python 语法检查失败")
    elif path.suffix == ".json":
        json_count += 1
        try:
            data = json.loads(text)
        except ValueError:
            problem(path, "JSON 格式错误")
            continue
        if path.name.endswith(".example.json"):
            if data.get("allow_time_change") is not False:
                problem(path, "示例必须默认禁止时间写入")
            for key, value in data.items():
                if key.endswith("password") and (not isinstance(value, str) or not value.startswith("REPLACE_")):
                    problem(path, "示例凭据不是明确占位符")
    elif path.suffix == ".md":
        markdown_count += 1
        body = no_fences(text)
        for target in re.findall(r"(?<!!)\[[^\]]+\]\(([^\s)]+)\)", body):
            link_count += 1
            parts = urlsplit(target)
            if parts.scheme or target.startswith("//"):
                if parts.scheme and parts.scheme not in ("https", "http", "mailto"):
                    problem(path, "不支持的外部链接协议")
                continue
            dest = (path.parent / unquote(parts.path)).resolve() if parts.path else path
            if not dest.is_relative_to(ROOT):
                problem(path, "相对链接越出公开仓库")
            elif not dest.exists():
                problem(path, "缺失链接目标：" + parts.path)
            elif parts.fragment and dest.suffix == ".md" and unquote(parts.fragment) not in anchors(dest):
                problem(path, "缺失章节锚点：" + parts.fragment)

skill = ROOT / "skills/telecom-ont-maintenance/SKILL.md"
if not skill.exists():
    errors.append("Skill 主文件缺失")
else:
    content = skill.read_text(encoding="utf-8")
    if not re.match(r"\A---\nname: telecom-ont-maintenance\ndescription: .+\n", content):
        problem(skill, "Skill frontmatter 缺失或名称不符")
    if len(content.splitlines()) >= 500:
        problem(skill, "Skill 主文件应少于 500 行")
    for path in (skill.parent / "references").glob("*.md"):
        if len(path.read_text(encoding="utf-8").splitlines()) > 300:
            problem(path, "过长 Skill 参考文件需要拆分或目录")

print("静态检查范围：%d 篇 Markdown，%d 个 Python，%d 个 JSON，%d 个链接" % (markdown_count, python_count, json_count, link_count))
if errors:
    for error in errors:
        print("失败：" + error)
    sys.exit(1)
print("通过：语法、示例、内部链接、基础隐私规则和 Skill 结构")
print("说明：未连接任何设备、未运行校时工具、未验证所有外部网页或固件；仍需人工脱敏审阅。")
