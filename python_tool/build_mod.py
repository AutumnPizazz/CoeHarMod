#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CoeHarMod 打包脚本
根据核心文件定义打包模组
"""

import os
import shutil
import zipfile
import sys
from pathlib import Path

# 导入核心文件定义模块
from core_files import get_core_files, is_core_file


def build_mod_package(source_dir, version=None, output_dir=None):
    """
    构建mod压缩包

    Args:
        source_dir: 源目录路径
        version: 版本号（如果为None，则使用默认值"unknown"）
        output_dir: 输出目录路径（默认为源目录）
    """
    source_dir = Path(source_dir).resolve()
    if output_dir is None:
        output_dir = source_dir
    else:
        output_dir = Path(output_dir).resolve()

    # 如果没有提供版本号，使用默认值
    if version is None:
        version = "unknown"

    print(f"使用版本号: {version}")

    # 获取核心文件列表
    core_files_list = get_core_files(source_dir)
    print(f"识别到 {len(core_files_list)} 个核心文件")

    # 创建临时文件夹
    temp_folder = output_dir / 'CoeHarMod'
    zip_name = f"CoeHarMod_{version}.zip"
    zip_path = output_dir / zip_name

    # 清理临时文件夹（如果存在）
    if temp_folder.exists():
        shutil.rmtree(temp_folder)
    temp_folder.mkdir()

    print(f"创建临时文件夹: {temp_folder}")

    # 复制核心文件
    for file_path in core_files_list:
        rel_path = file_path.relative_to(source_dir)

        # 跳过文件夹本身
        if file_path.is_dir():
            continue

        # 跳过脚本本身
        if file_path.name == os.path.basename(__file__):
            continue

        # 跳过压缩包文件
        if file_path.name.startswith('CoeHarMod_') and file_path.suffix == '.zip':
            continue

        # 跳过 .gitignore 文件
        if file_path.name == '.gitignore':
            continue

        dest_path = temp_folder / rel_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, dest_path)
        print(f"复制文件: {rel_path}")

    # 创建压缩包
    print(f"\n创建压缩包: {zip_name}")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(temp_folder):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(temp_folder.parent)
                zipf.write(file_path, arcname)
                print(f"  添加到压缩包: {arcname}")

    # 清理临时文件夹
    shutil.rmtree(temp_folder)
    print(f"\n清理临时文件夹: {temp_folder}")

    print(f"\n✓ 打包完成！")
    print(f"  压缩包路径: {zip_path}")
    return zip_path


if __name__ == '__main__':
    # 获取版本号（从命令行参数或环境变量）
    version = os.environ.get('MOD_VERSION')

    if len(sys.argv) > 1:
        version = sys.argv[1]

    # 获取脚本所在目录的父目录（项目根目录）
    script_dir = Path(__file__).parent.resolve()
    project_dir = script_dir.parent.resolve()

    print("=" * 50)
    print("CoeHarMod 打包工具")
    print("=" * 50)
    print(f"项目目录: {project_dir}")

    try:
        build_mod_package(project_dir, version=version)
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()