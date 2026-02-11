#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地打包 CoeHarMod 核心文件到桌面
"""

import sys
import os
from pathlib import Path

# 添加父目录到路径，以便导入 build_mod
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir / "python_tool"))

from build_mod import build_mod_package


if __name__ == '__main__':
    print("=" * 50)
    print("CoeHarMod 本地打包工具")
    print("=" * 50)
    
    # 源目录（项目根目录）
    source_dir = Path(__file__).parent.parent
    
    # 输出目录（桌面）
    desktop = Path.home() / "Desktop"
    
    print(f"\n源目录: {source_dir}")
    print(f"输出目录: {desktop}")
    
    # 询问版本号
    while True:
        version = input("\n请输入版本号 (例如: v3.3.8): ").strip()
        if version:
            break
        print("版本号不能为空，请重新输入。")
    
    try:
        print(f"\n开始打包版本 {version}...")
        output_path = build_mod_package(
            source_dir=source_dir,
            version=version,
            output_dir=desktop
        )
        
        print("\n" + "=" * 50)
        print(f"✓ 打包完成")
        print(f"  文件: {output_path}")
        print(f"  位置: {desktop}")
        print("=" * 50)
        
    except Exception as e:
        print("\n" + "=" * 50)
        print(f"✗ 打包失败: {e}")
        print("=" * 50)
        import traceback
        traceback.print_exc()
        sys.exit(1)