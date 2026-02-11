#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CoeHarMod 核心文件定义模块

使用白名单机制定义模组运行所需的核心文件
"""

from pathlib import Path
from typing import Set, List


def get_core_files(root_dir: Path) -> List[Path]:
    """
    获取所有核心文件的列表

    Args:
        root_dir: 项目根目录

    Returns:
        核心文件路径列表
    """
    core_files = []

    # Atlases.json
    atlases_json = root_dir / "Atlases.json"
    if atlases_json.exists():
        core_files.append(atlases_json)

    # *.atlas 文件
    for atlas_file in root_dir.glob("*.atlas"):
        core_files.append(atlas_file)

    # *.png 文件（图集纹理）
    for png_file in root_dir.glob("*.png"):
        core_files.append(png_file)

    # jsons 文件夹及其内容
    jsons_dir = root_dir / "jsons"
    if jsons_dir.exists() and jsons_dir.is_dir():
        core_files.append(jsons_dir)
        for item in jsons_dir.rglob("*"):
            core_files.append(item)

    # sounds 文件夹及其内容
    sounds_dir = root_dir / "sounds"
    if sounds_dir.exists() and sounds_dir.is_dir():
        core_files.append(sounds_dir)
        for item in sounds_dir.rglob("*"):
            core_files.append(item)

    return core_files


def get_core_file_patterns() -> Set[str]:
    """
    获取核心文件的 glob 模式集合

    Returns:
        核心文件 glob 模式集合
    """
    return {
        "Atlases.json",
        "*.atlas",
        "*.png",
        "jsons/**",
        "sounds/**"
    }


def is_core_file(file_path: Path, root_dir: Path) -> bool:
    """
    判断给定文件是否为核心文件

    Args:
        file_path: 要判断的文件路径
        root_dir: 项目根目录

    Returns:
        True 如果是核心文件，否则 False
    """
    # 计算相对路径
    try:
        rel_path = file_path.relative_to(root_dir)
    except ValueError:
        return False

    # 检查是否匹配核心文件模式
    patterns = get_core_file_patterns()

    # Atlases.json
    if rel_path.name == "Atlases.json":
        return True

    # *.atlas
    if file_path.suffix == ".atlas":
        return True

    # *.png
    if file_path.suffix == ".png":
        return True

    # jsons 文件夹及其内容
    if rel_path.parts[0] == "jsons":
        return True

    # sounds 文件夹及其内容
    if rel_path.parts[0] == "sounds":
        return True

    return False


if __name__ == "__main__":
    # 测试代码
    import sys

    root = Path(__file__).parent.parent
    print(f"项目根目录: {root}\n")

    print("核心文件模式:")
    for pattern in get_core_file_patterns():
        print(f"  - {pattern}")
    print()

    print("核心文件列表:")
    core_files = get_core_files(root)
    for f in core_files:
        print(f"  - {f.relative_to(root)}")

    print(f"\n总计: {len(core_files)} 个核心文件")