#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从更新日志中提取指定版本的内容
"""

import re
from pathlib import Path


def extract_changelog(version, changelog_path):
    """
    从更新日志文件中提取指定版本的内容

    Args:
        version: 版本号（如 "3.3.8"）
        changelog_path: 更新日志文件路径

    Returns:
        提取到的更新内容字符串
    """
    with open(changelog_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 先尝试匹配带适配后缀的版本号（如 v3.3.7-适配4.19.11）
    # 使用 ^# 匹配行首的 #，然后允许任意数量的 #（+），后面跟 v
    pattern = rf'^#+\s*v{re.escape(version)}-[^\n]*\n((?:.|\n)*?)(?=^\n#+\s*v|^\Z)'
    match = re.search(pattern, content, re.MULTILINE)

    if not match:
        # 尝试匹配不带适配后缀的版本号
        pattern = rf'^#+\s*v{re.escape(version)}[^\n]*\n((?:.|\n)*?)(?=^\n#+\s*v|^\Z)'
        match = re.search(pattern, content, re.MULTILINE)

    if match:
        changelog_content = match.group(1).strip()
        # 移除开头的 front matter（如果存在）
        changelog_content = re.sub(r'^---.*?---\n', '', changelog_content, flags=re.DOTALL)
        return changelog_content

    return "## 更新内容\n\n暂无此版本的更新日志。"


if __name__ == '__main__':
    import sys

    if len(sys.argv) != 2:
        print("用法: python extract_changelog.py <版本号>")
        sys.exit(1)

    version = sys.argv[1]
    changelog_path = Path(__file__).parent.parent / 'docs' / 'CoeHarMod专区' / '更新日志.md'

    result = extract_changelog(version, changelog_path)
    print(result)