#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CoeHarMod 核心文件定义模块

使用白名单机制定义模组运行所需的核心文件
"""

from pathlib import Path
from typing import Set, List
import argparse


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


def get_git_checkout_paths() -> str:
    """
    获取 git checkout 命令所需的路径格式

    Returns:
        空格分隔的路径字符串，用于 git checkout 命令
    """
    paths = ["Atlases.json", "*.atlas", "*.png", "jsons/", "sounds/"]
    return " ".join(paths)


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

    # 空路径检查
    if not rel_path.parts:
        return False

    # jsons 文件夹及其内容
    if rel_path.parts[0] == "jsons":
        return True

    # sounds 文件夹及其内容
    if rel_path.parts[0] == "sounds":
        return True

    return False


def list_core_files(root_dir: Path, output_format: str = "relative") -> None:
    """
    列出核心文件

    Args:
        root_dir: 项目根目录
        output_format: 输出格式（relative, absolute, paths）
    """
    core_files = get_core_files(root_dir)

    if output_format == "relative":
        for f in core_files:
            print(f.relative_to(root_dir))
    elif output_format == "absolute":
        for f in core_files:
            print(f)
    elif output_format == "paths":
        # 只输出文件和文件夹的路径（不递归列出内部文件）
        seen_dirs = set()
        for f in core_files:
            if f.is_dir():
                rel_path = f.relative_to(root_dir)
                dir_str = str(rel_path).replace('\\', '/')
                if dir_str not in seen_dirs:
                    print(dir_str)
                    seen_dirs.add(dir_str)
            else:
                rel_path = f.relative_to(root_dir)
                path_str = str(rel_path).replace('\\', '/')
                # 检查是否已经在某个目录中
                parts = path_str.split('/')
                if parts[0] in seen_dirs:
                    continue
                print(path_str)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CoeHarMod 核心文件定义工具")
    parser.add_argument("--list-files", action="store_true", help="列出核心文件")
    parser.add_argument("--format", choices=["relative", "absolute", "paths"], default="relative",
                        help="输出格式 (relative: 相对路径, absolute: 绝对路径, paths: 文件夹和文件路径)")
    parser.add_argument("--git-paths", action="store_true", help="输出 git checkout 路径格式")
    args = parser.parse_args()

    root = Path(__file__).parent.parent

    if args.git_paths:
        print(get_git_checkout_paths())
    elif args.list_files:
        list_core_files(root, args.format)
    else:
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