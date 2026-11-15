#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build reviewed, offline Release artifacts. No network or device operations."""

import argparse
import base64
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import time
import unicodedata
from urllib.parse import unquote, urlsplit
import zipfile

import mistune


ROOT = Path(__file__).resolve().parents[1]
REPO = "https://github.com/lazyalex616/china-telecom-ont-guide"
SKILL = "telecom-ont-maintenance"
ROOT_FILES = {"README.md", "START-HERE.md", "AGENT-KIT.md", "LICENSE", "THIRD_PARTY_NOTICES.md", "requirements-release.txt"}
PREFIXES = {"docs/": {".md"}, "examples/": {".md", ".json"}, "assets/figures/": {".md", ".png"},
            "skills/" + SKILL + "/": {".md", ".txt"}, "tools/": {".py"}, "tests/": {".py"}, "releases/": {".md"}}


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args]).decode("utf-8").strip()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def slug(value):
    value = html.unescape(re.sub(r"<[^>]+>", "", value)).lower().strip()
    value = "".join(c for c in value if c in "-_" or not unicodedata.category(c).startswith(("P", "S")))
    return re.sub(r"\s", "-", value)


def page_id(name):
    return "page-" + name[:-3].replace("/", "-").lower()


class HandbookRenderer(mistune.HTMLRenderer):
    def __init__(self, source, pages, images, version, files):
        super().__init__(escape=True)
        self.source, self.pages, self.images = source, pages, images
        self.version, self.files, self.headings = version, files, {}

    def destination(self, url):
        parts = urlsplit(url)
        if parts.scheme or url.startswith("//"):
            return None, parts
        target = ((ROOT / self.source).parent / unquote(parts.path)).resolve() if parts.path else ROOT / self.source
        if not target.is_relative_to(ROOT):
            raise ValueError("文档相对链接越界")
        return target.relative_to(ROOT).as_posix(), parts

    def heading(self, text, level, **attrs):
        anchor = slug(text)
        count = self.headings.get(anchor, 0)
        self.headings[anchor] = count + 1
        anchor += "-" + str(count) if count else ""
        ident = page_id(self.source) + "--" + anchor
        return '<h%d id="%s">%s</h%d>\n' % (level, html.escape(ident, quote=True), text, level)

    def link(self, text, url, title=None):
        target, parts = self.destination(url)
        if target is not None:
            if target in self.pages:
                url = "#" + page_id(target) + ("--" + unquote(parts.fragment) if parts.fragment else "")
            else:
                url = REPO + "/blob/" + self.version + "/" + target + ("#" + parts.fragment if parts.fragment else "")
        return super().link(text, url, title)

    def image(self, text, url, title=None):
        target, _ = self.destination(url)
        if target is None or target not in self.files or not target.endswith(".png"):
            raise ValueError("离线手册只允许白名单内的本地 PNG 插图")
        if target in self.images:
            return '<a href="#%s">查看图解：%s</a>' % (self.images[target], html.escape(text))
        ident = "figure-" + str(len(self.images) + 1)
        self.images[target] = ident
        encoded = base64.b64encode(self.files[target]).decode("ascii")
        return '<img id="%s" src="data:image/png;base64,%s" alt="%s" loading="lazy">' % (ident, encoded, html.escape(text, quote=True))


class HTMLAudit(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.anchors, self.image_count = set(), [], 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ("script", "iframe", "object", "embed", "link", "base", "form"):
            raise ValueError("离线手册出现活动内容或外部资源标签")
        if any(key.startswith("on") for key in attrs):
            raise ValueError("离线手册出现事件处理代码")
        if "id" in attrs:
            if attrs["id"] in self.ids:
                raise ValueError("离线手册章节 ID 重复")
            self.ids.add(attrs["id"])
        if tag == "a" and attrs.get("href", "").startswith("#"):
            self.anchors.append(attrs["href"][1:])
        if tag == "img":
            if not attrs.get("src", "").startswith("data:image/png;base64,"):
                raise ValueError("离线手册图片并未内嵌")
            self.image_count += 1


def handbook(files, version, commit):
    pages = [name for name in ("START-HERE.md", "README.md") if name in files]
    pages += sorted(name for name in files if name.endswith(".md") and name not in pages and name != "AGENT-KIT.md" and not name.startswith("releases/"))
    titles = {}
    for name in pages:
        match = re.search(r"^#\s+(.+)$", files[name].decode("utf-8"), re.M)
        titles[name] = match.group(1) if match else name
    nav = "".join('<li><a href="#%s">%s</a></li>' % (page_id(name), html.escape(titles[name])) for name in pages)
    sections, images = [], {}
    for name in pages:
        renderer = HandbookRenderer(name, pages, images, version, files)
        render = mistune.create_markdown(renderer=renderer, plugins=["table", "strikethrough", "task_lists", "url"])
        sections.append('<section id="%s">%s<p class="back"><a href="#contents">返回目录</a></p></section>' % (page_id(name), render(files[name].decode("utf-8"))))
    style = """
*{box-sizing:border-box}body{margin:0;background:#f3f6fa;color:#17283f;font:17px/1.8 system-ui,'Microsoft YaHei',sans-serif}
main{max-width:1120px;margin:auto;padding:30px 34px;background:white}header{border-bottom:5px solid #087c99;padding-bottom:24px}
nav{padding:18px 28px;background:#edf5fa}h1,h2,h3{line-height:1.4;color:#12324c;scroll-margin-top:20px}h2{border-bottom:1px solid #cbd9e4;padding-bottom:8px}
section{padding-top:32px;border-bottom:2px solid #dfe7ef}a{color:#006e91;overflow-wrap:anywhere}img{display:block;width:100%;height:auto;margin:22px auto;border:1px solid #cbd9e4;border-radius:8px}
table{display:block;overflow-x:auto;border-collapse:collapse;max-width:100%;font-size:15px}th,td{border:1px solid #cbd9e4;padding:9px 12px;vertical-align:top}th{background:#edf5fa;text-align:left}
pre{overflow-x:auto;background:#102338;color:#f0f7ff;padding:18px;border-radius:8px;font-size:14px;line-height:1.65}code{font-family:Consolas,monospace;font-size:.92em}p>code,li>code,td>code{background:#edf3f7;padding:2px 4px}
blockquote{margin:20px 0;padding:8px 20px;border-left:5px solid #d19420;background:#fff8e9}li{margin:5px 0}.meta,.back{font-size:14px;color:#51687b}.back{text-align:right}
@media(max-width:640px){main{padding:18px 14px}body{font-size:16px}nav{padding:12px 18px}}
@media print{body,main{background:white}main{max-width:none;padding:0}nav,.back{display:none}section{break-before:page;border:0}img,pre,tr{break-inside:avoid}a{color:inherit}pre{white-space:pre-wrap;background:#f0f3f5;color:#111}}
"""
    document = '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
    document += '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src data:; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'">'
    document += '<meta name="referrer" content="no-referrer"><title>电信光猫维护离线手册 ' + version + '</title><style>' + style + '</style></head><body><main>'
    document += '<header><h1>电信光猫维护：离线图文手册</h1><p>先从装维师傅取得当前有效超密，再维护本人或已授权设备。</p>'
    document += '<p class="meta">版本 ' + version + ' · 来源提交 ' + commit[:12] + ' · 无脚本、无外部字体、无自动联网资源</p>'
    document += '<p>所有技术图已内嵌，重复插图链接回首次出现位置。代码和下载链接需要联网，阅读正文和图片不需要。手册不自动执行任何命令。</p></header>'
    document += '<nav id="contents"><h2>目录</h2><ol>' + nav + '</ol></nav>' + "".join(sections) + '</main></body></html>\n'
    audit = HTMLAudit()
    audit.feed(document)
    if set(audit.anchors) - audit.ids or audit.image_count != 4:
        raise ValueError("离线手册内部锚点或四张插图不完整")
    print("离线手册：%d 篇文档、4 张内嵌技术图，内部锚点完整，无脚本或外链资源" % len(pages))
    return document.encode("utf-8")


def write_zip(path, members, timestamp):
    with zipfile.ZipFile(path, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(members.items()):
            if name.startswith("/") or ".." in Path(name).parts:
                raise ValueError("发行包路径越界")
            info = zipfile.ZipInfo(name, time.gmtime(max(timestamp, 315532800))[:6])
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None or set(archive.namelist()) != set(members):
            raise ValueError("发行包 CRC 或文件清单不一致")
        if any(archive.read(name) != data for name, data in members.items()):
            raise ValueError("发行包字节不一致")
    print("已构建并逐文件核对：%s，%d 个文件" % (path.name, len(members)))


def package(path, root, files, metadata, timestamp):
    payload = dict(files)
    payload["BUILD-INFO.json"] = json_bytes(metadata)
    payload["PACKAGE-MANIFEST.json"] = json_bytes({name: {"sha256": digest(data), "size": len(data)} for name, data in sorted(payload.items())})
    write_zip(path, {root + "/" + name: data for name, data in payload.items()}, timestamp)


def main():
    parser = argparse.ArgumentParser(description="从干净的已提交源码生成离线发行附件，不联网、不发布")
    parser.add_argument("--version", required=True, help="例如 v1.0.0")
    parser.add_argument("--output", type=Path, default=ROOT / "dist", help="构建输出目录，已有同名文件不覆盖")
    args = parser.parse_args()
    if not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", args.version):
        parser.error("版本必须采用 v主版本.次版本.修订号")
    if git("status", "--porcelain"):
        raise ValueError("先审阅并提交工作区，再构建发行附件")
    commit = git("rev-parse", "HEAD")
    timestamp = int(git("show", "-s", "--format=%ct", "HEAD"))
    files = {}
    for name in git("ls-files", "-z").split("\x00"):
        if not name or not (name in ROOT_FILES or any(name.startswith(prefix) and Path(name).suffix in extensions for prefix, extensions in PREFIXES.items())):
            continue
        path = ROOT / name
        if path.is_symlink() or name.endswith((".local.json", ".secret.json")):
            raise ValueError("白名单中出现链接或私密运行文件")
        files[name] = path.read_bytes()
    required = {"START-HERE.md", "AGENT-KIT.md", "README.md", "LICENSE", "tools/install-skill.py", "skills/" + SKILL + "/SKILL.md", "releases/" + args.version + ".md"}
    if required - files.keys():
        raise ValueError("缺少必要发行材料")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    names = ["telecom-ont-toolkit-" + args.version + ".zip", "telecom-ont-agent-kit-" + args.version + ".zip", SKILL + ".skill", "telecom-ont-handbook-" + args.version + ".html", "SHA256SUMS.txt", "release-body.md"]
    if any((output / name).exists() for name in names):
        raise ValueError("输出已有同名文件，请指定一个新的输出目录，不覆盖已有附件")
    metadata = {"version": args.version, "source_commit": commit, "license": "MIT", "device_validation": "public adaptation: static only, no new production device tests"}
    offline = handbook(files, args.version, commit)
    package(output / names[0], "telecom-ont-toolkit-" + args.version, {**files, "offline-handbook.html": offline}, metadata, timestamp)
    agent = {name: data for name, data in files.items() if name.startswith("skills/" + SKILL + "/") or name == "tools/install-skill.py"}
    agent.update({"START-HERE.md": files["AGENT-KIT.md"], "LICENSE": files["LICENSE"]})
    package(output / names[1], "telecom-ont-agent-kit-" + args.version, agent, metadata, timestamp)
    write_zip(output / names[2], {name[len("skills/"):]: data for name, data in files.items() if name.startswith("skills/" + SKILL + "/")}, timestamp)
    (output / names[3]).write_bytes(offline)
    (output / names[4]).write_text("".join(digest((output / name).read_bytes()) + "  " + name + "\n" for name in names[:4]), encoding="utf-8")
    (output / names[5]).write_bytes(files["releases/" + args.version + ".md"])
    if git("status", "--porcelain"):
        raise ValueError("构建期间源码发生变化，不能发布")
    for name in names[:5]:
        print("附件：%s，%d 字节" % (name, (output / name).stat().st_size))
    print("构建完成，没有连接设备、安装 Skill 或上传 GitHub。")


if __name__ == "__main__":
    main()
