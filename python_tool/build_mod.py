#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CoeHarMod 打包脚本
将指定目录下的所有文件（不包括文件夹）和jsons、sounds文件夹一起放在CoeHarMod文件夹中并压缩
"""

import os
import shutil
import zipfile
import re
from pathlib import Path


def get_mod_version(properties_file):
    """从properties文件中读取modVersion"""
    version_pattern = r'modVersion\s*=\s*([\d.]+)'
    with open(properties_file, 'r', encoding='utf-8') as f:
        for line in f:
            match = re.search(version_pattern, line)
            if match:
                return match.group(1)
    raise ValueError("未能在properties文件中找到modVersion")


def parse_gitignore(gitignore_path, base_dir):
    """
    解析.gitignore文件，返回忽略规则的集合
    
    Args:
        gitignore_path: .gitignore文件路径
        base_dir: 基础目录路径
    
    Returns:
        包含忽略规则的集合
    """
    ignore_rules = set()
    if not gitignore_path.exists():
        return ignore_rules
    
    with open(gitignore_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # 跳过空行和注释
            if not line or line.startswith('#'):
                continue
            ignore_rules.add(line)
    
    return ignore_rules


def should_ignore(path, ignore_rules, base_dir):
    """
    判断路径是否应该被忽略
    
    Args:
        path: 要检查的路径
        ignore_rules: 忽略规则集合
        base_dir: 基础目录路径
    
    Returns:
        True如果应该忽略，False否则
    """
    rel_path = path.relative_to(base_dir)
    path_str = str(rel_path).replace('\\', '/')
    path_str = '/' + path_str  # 添加前导斜杠以匹配从根目录开始的规则
    path_name = path.name
    
    for rule in ignore_rules:
        rule = rule.replace('\\', '/')
        
        # 跳过以/开头但不是从根目录开始的规则（目录相对规则）
        if rule.startswith('/') and not rule.startswith('//'):
            rule = rule[1:]
        
        # 处理通配符模式
        import fnmatch
        
        # 检查完整路径是否匹配
        if fnmatch.fnmatch(path_str, rule) or fnmatch.fnmatch(path_str, '*/' + rule):
            return True
        
        # 检查文件名是否匹配
        if fnmatch.fnmatch(path_name, rule):
            return True
        
        # 检查路径是否以规则结尾
        if rule.startswith('*/') and path_str.endswith(rule[1:]):
            return True
        
        # 处理目录规则（以/结尾）
        if rule.endswith('/'):
            # 检查是否在忽略的目录中
            dir_rule = rule[:-1]
            parts = path_str.split('/')
            if dir_rule in parts:
                return True
    
    return False


def build_mod_package(source_dir, output_dir=None):
    """
    构建mod压缩包
    
    Args:
        source_dir: 源目录路径
        output_dir: 输出目录路径（默认为源目录）
    """
    source_dir = Path(source_dir).resolve()
    if output_dir is None:
        output_dir = source_dir
    else:
        output_dir = Path(output_dir).resolve()
    
    # 读取.gitignore规则
    gitignore_path = source_dir / '.gitignore'
    ignore_rules = parse_gitignore(gitignore_path, source_dir)
    print(f"从.gitignore读取到 {len(ignore_rules)} 条忽略规则")
    
    # 读取版本号
    properties_file = source_dir / 'jsons' / 'translations' / 'Simplified_Chinese.properties'
    if not properties_file.exists():
        raise FileNotFoundError(f"找不到文件: {properties_file}")
    
    mod_version = get_mod_version(properties_file)
    print(f"检测到模组版本: {mod_version}")
    
    # 创建临时文件夹
    temp_folder = output_dir / 'CoeHarMod'
    zip_name = f"CoeHarMod_{mod_version}.zip"
    zip_path = output_dir / zip_name
    
    # 清理临时文件夹（如果存在）
    if temp_folder.exists():
        shutil.rmtree(temp_folder)
    temp_folder.mkdir()
    
    print(f"创建临时文件夹: {temp_folder}")
    
    # 需要复制的文件夹列表
    folders_to_copy = ['jsons', 'sounds']
    
    # 复制所有文件（不包括文件夹）
    for item in source_dir.iterdir():
        if item.is_file():
            # 跳过脚本本身
            if item.name == os.path.basename(__file__):
                continue
            # 跳过压缩包文件
            if item.name.startswith('CoeHarMod_') and item.suffix == '.zip':
                continue
            # 跳过.gitignore文件
            if item.name == '.gitignore':
                continue
            # 检查.gitignore规则
            if should_ignore(item, ignore_rules, source_dir):
                print(f"跳过文件（忽略规则）: {item.name}")
                continue
            shutil.copy2(item, temp_folder / item.name)
            print(f"复制文件: {item.name}")
    
    # 复制指定文件夹（递归复制，并过滤掉忽略的文件）
    for folder_name in folders_to_copy:
        folder_path = source_dir / folder_name
        if folder_path.exists() and folder_path.is_dir():
            dest_folder = temp_folder / folder_name
            
            # 递归复制文件夹，应用忽略规则
            for root, dirs, files in os.walk(folder_path):
                root_path = Path(root)
                rel_root = root_path.relative_to(source_dir)
                dest_root = temp_folder / rel_root
                
                # 创建目标目录
                dest_root.mkdir(parents=True, exist_ok=True)
                
                # 复制文件（过滤忽略的）
                for file in files:
                    file_path = root_path / file
                    if should_ignore(file_path, ignore_rules, source_dir):
                        print(f"跳过文件（忽略规则）: {rel_root / file}")
                        continue
                    shutil.copy2(file_path, dest_root / file)
                    print(f"复制文件: {rel_root / file}")
            
            print(f"复制文件夹: {folder_name}/")
    
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
    # 获取脚本所在目录的父目录（项目根目录）
    script_dir = Path(__file__).parent.resolve()
    project_dir = script_dir.parent.resolve()
    
    print("=" * 50)
    print("CoeHarMod 打包工具")
    print("=" * 50)
    print(f"项目目录: {project_dir}")
    
    try:
        build_mod_package(project_dir)
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()