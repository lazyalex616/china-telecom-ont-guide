#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Copy only the bundled Skill, offline, with a default dry run and no overwrite."""

import argparse
import shutil
import sys
from pathlib import Path


NAME = "telecom-ont-maintenance"
SOURCE = Path(__file__).resolve().parents[1] / "skills" / NAME


def plan(target):
    if not (SOURCE / "SKILL.md").is_file():
        raise ValueError("未找到完整 Skill，请先解压整个下载包，不要只复制安装器")
    files = sorted(SOURCE.rglob("*"))
    if any(path.is_symlink() for path in files):
        raise ValueError("Skill 含符号链接，拒绝复制")
    if any(path.is_file() and path.suffix not in (".md", ".txt") for path in files):
        raise ValueError("Skill 中出现预期外文件，先审阅，不自动安装")
    destination = target.expanduser().absolute() / NAME
    if destination.exists() or destination.is_symlink():
        raise ValueError("已有同名目录或链接，未覆盖，请先审阅已有内容")
    count = sum(path.is_file() for path in files)
    return destination, count


def main():
    parser = argparse.ArgumentParser(description="离线安装这一份 Skill，默认只预览，不覆盖已有内容")
    parser.add_argument("--target", type=Path, default=Path.home() / ".agents" / "skills", help="Agent 实际支持的 Skills 父目录，默认 ~/.agents/skills")
    parser.add_argument("--apply", action="store_true", help="明确执行复制，否则不写入任何文件")
    args = parser.parse_args()
    destination, count = plan(args.target)
    print("计划：只复制 %s，共 %d 个文本文件" % (NAME, count))
    print("目标：%s" % destination)
    if not args.apply:
        print("预览结束，没有写入。确认目录适用于你的 Agent 后，再加 --apply。")
        return
    shutil.copytree(SOURCE, destination)
    print("已复制 Skill。按 Agent 自身说明重新加载，不代表已授权连接或修改设备。")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError):
        error = sys.exc_info()[1]
        message = str(error) if isinstance(error, ValueError) else "复制失败，可能有部分目录，请核查这一目录，不自动删除或覆盖"
        print("未安装：" + message, file=sys.stderr)
        sys.exit(1)
