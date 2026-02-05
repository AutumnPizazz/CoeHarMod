#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unciv模组百科生成器 - 主框架
功能：自动扫描 jsons/ 目录下的所有JSON文件，分类生成Markdown文档
目录结构：
    CoeHarMod/
    ├── python/
    │   └── generate_wiki.py    <- 本文件
    ├── jsons/
    │   ├── Buildings.json      <- 建筑数据
    │   ├── Units.json          <- 单位数据（待支持）
    │   └── ...                 <- 其他数据文件
    └── docs/                   <- 生成的文档目录（自动创建）
"""

import json
import os
import re
from pathlib import Path  # 现代路径处理库，比os.path更直观
from typing import List, Dict, Any, Optional


class WikiGenerator:
    """
    百科生成器主类
    负责：路径管理、文件扫描、分类路由、输出生成
    """

    def __init__(self):
        """初始化：自动计算所有关键路径"""
        # 本脚本所在目录：CoeHarMod/python/
        self.script_dir = Path(__file__).parent.absolute()

        # 模组根目录：CoeHarMod/（脚本的上级目录）
        self.mod_dir = self.script_dir.parent

        # JSON数据源目录：CoeHarMod/jsons/
        self.jsons_dir = self.mod_dir / "jsons"

        # 文档输出目录：CoeHarMod/docs/（会自动创建）
        self.output_dir = self.mod_dir / "docs"

        # 确保输出目录存在（exist_ok=True表示如果已存在不报错）
        self.output_dir.mkdir(exist_ok=True)

        print(f"[初始化] 模组目录: {self.mod_dir}")
        print(f"[初始化] JSON目录: {self.jsons_dir}")
        print(f"[初始化] 输出目录: {self.output_dir}")

    def run(self):
        """
        主入口函数：扫描并处理所有JSON文件
        工作流程：扫描 → 过滤 → 路由 → 生成
        """
        # 1. 扫描所有JSON文件
        json_files = self._scan_json_files()

        if not json_files:
            print("[警告] 未找到任何JSON文件，请检查目录结构")
            return

        print(f"\n[扫描] 发现 {len(json_files)} 个数据文件")

        # 2. 逐个处理每个文件
        for file_path in json_files:
            self._process_single_file(file_path)

        print(f"\n[完成] 所有文档已生成至: {self.output_dir}")

    def _scan_json_files(self) -> List[Path]:
        """
        扫描jsons目录下的所有.json文件
        返回：文件路径列表（Path对象）
        """
        if not self.jsons_dir.exists():
            raise FileNotFoundError(f"JSON目录不存在: {self.jsons_dir}")

        # 使用glob模式匹配所有.json文件（递归搜索子目录）
        return list(self.jsons_dir.rglob("*.json"))

    def _process_single_file(self, file_path: Path):
        """
        处理单个JSON文件：根据文件名路由到对应的处理器
        参数：file_path - JSON文件的完整路径
        """
        print(f"\n[处理] {file_path.name}")

        try:
            # 1. 读取并解析JSON（自动处理注释）
            raw_data = self._load_json_with_comments(file_path)

            # 2. 根据文件名决定处理策略（路由）
            # file_path.stem 是不带后缀的文件名，如 "Buildings"
            file_type = file_path.stem.lower()

            if "building" in file_type:
                # 建筑类数据（Buildings.json, CityBuildings.json等）
                self._handle_buildings(raw_data, file_path.stem)

            elif "unit" in file_type:
                # 单位类数据（Units.json, CivilianUnits.json等）
                self._handle_units(raw_data, file_path.stem)

            elif "tech" in file_type or "civic" in file_type:
                # 科技/市政树数据
                self._handle_techs(raw_data, file_path.stem)

            elif "policy" in file_type:
                # 政策卡数据
                self._handle_policies(raw_data, file_path.stem)

            else:
                # 未知类型：使用通用处理或跳过
                print(f"  [跳过] 未知数据类型: {file_type}")
                # 如需处理，取消下行注释：
                # self._handle_generic(raw_data, file_path.stem)

        except Exception as e:
            print(f"  [错误] 处理失败: {e}")
            # 出错时打印堆栈方便调试（开发阶段建议保留）
            import traceback
            traceback.print_exc()

    def _load_json_with_comments(self, file_path: Path) -> List[Dict]:
        """
        读取JSON文件并去除JavaScript风格注释（Unciv的JSON常带注释）
        参数：file_path - JSON文件路径
        返回：解析后的Python对象（通常是列表或字典）
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 正则表达式去除注释：
        # 1. /* ... */ 多行注释（含换行）
        # 2. // ... 单行注释
        # re.DOTALL让.能匹配换行符
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        content = re.sub(r'//.*', '', content)

        # 解析为Python对象
        return json.loads(content)

    def _handle_buildings(self, data: List[Dict], source_name: str):
        """
        处理建筑数据（ Buildings.json ）
        参数：
            data - JSON解析后的列表，每个元素是一个建筑定义
            source_name - 源文件名（用于创建子目录）
        """
        # 创建专属输出目录：docs/buildings/
        target_dir = self.output_dir / source_name.lower()
        target_dir.mkdir(exist_ok=True)

        print(f"  [建筑] 共 {len(data)} 个条目")

        # TODO: 在此处实现建筑数据的分类和Markdown生成
        # 提示：
        # 1. 遍历data列表，每个item是一个建筑字典
        # 2. 根据"name"字段判断类型（AWonder开头的是奇观等）
        # 3. 调用 _generate_building_md(item) 生成Markdown文本
        # 4. 使用 _save_markdown(text, target_dir, filename) 保存文件

        pass  # 占位符，删除后写你的逻辑

    def _handle_units(self, data: List[Dict], source_name: str):
        """
        处理单位数据（ Units.json ）
        与建筑处理类似，但字段和分类逻辑不同
        """
        target_dir = self.output_dir / source_name.lower()
        target_dir.mkdir(exist_ok=True)

        print(f"  [单位] 共 {len(data)} 个条目")
        # TODO: 实现单位数据处理逻辑
        pass

    def _handle_techs(self, data: List[Dict], source_name: str):
        """处理科技/市政数据"""
        print(f"  [科技] 共 {len(data)} 个条目")
        # TODO: 实现科技树处理逻辑
        pass

    def _handle_policies(self, data: List[Dict], source_name: str):
        """处理政策卡数据"""
        print(f"  [政策] 共 {len(data)} 个条目")
        # TODO: 实现政策卡处理逻辑
        pass

    def _handle_generic(self, data: Any, source_name: str):
        """
        通用处理器（备用）
        用于处理未识别的JSON文件，直接转存为格式化Markdown
        """
        target_dir = self.output_dir / "others"
        target_dir.mkdir(exist_ok=True)

        # 简单地将JSON结构转为Markdown表格或列表
        md_content = f"# {source_name}\n\n```json\n{json.dumps(data, indent=2, ensure_ascii=False)}\n```"

        output_file = target_dir / f"{source_name}.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_content)

        print(f"  [通用] 已保存原始结构到: {output_file}")

    def _save_markdown(self, content: str, directory: Path, filename: str):
        """
        工具函数：保存Markdown文件
        参数：
            content - Markdown文本内容
            directory - 目标目录（Path对象）
            filename - 文件名（自动添加.md后缀）
        """
        # 清理文件名中的非法字符（Windows不允许的符号：\/:*?"<>|）
        safe_filename = re.sub(r'[\\/:*?"<>|]', '_', filename)
        if not safe_filename.endswith('.md'):
            safe_filename += '.md'

        file_path = directory / safe_filename

        # 写入文件（使用UTF-8确保中文正常显示）
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return file_path


def main():
    """程序入口"""
    print("=" * 50)
    print("Unciv模组百科生成器")
    print("=" * 50)

    # 创建生成器实例并运行
    generator = WikiGenerator()
    generator.run()


if __name__ == '__main__':
    main()