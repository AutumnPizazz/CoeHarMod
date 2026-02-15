"""
删除普通建筑的涨价效果，并将区域地标建筑的涨价幅度翻倍
逐行处理，保留注释和格式
"""
import re
import os

def process_buildings():
    input_file = r'D:\unciv3\mods\CoeHarMod\jsons\Buildings.json'
    output_file = input_file

    # 读取文件
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 统计信息
    stats = {
        'normal_buildings_removed': 0,
        'landmark_buildings_doubled': 0,
        'landmark_buildings_replaced': 0
    }

    # 处理每一行
    output_lines = []
    current_building_name = None
    in_uniques = False
    in_building = False
    bracket_depth = 0
    replaces_building = None

    for i, line in enumerate(lines):
        # 检查是否在建筑定义中
        if re.search(r'^\s*\{', line):
            in_building = True
            bracket_depth = 1
            current_building_name = None
            replaces_building = None
            in_uniques = False

        # 检测建筑名称
        name_match = re.search(r'"name":\s*"([^"]+)"', line)
        if name_match and in_building:
            current_building_name = name_match.group(1)

        # 检测 replaces
        replaces_match = re.search(r'"replaces":\s*"([^"]+)"', line)
        if replaces_match and in_building:
            replaces_building = replaces_match.group(1)

        # 检测是否进入 uniques 数组
        if re.search(r'"uniques":\s*\[', line):
            in_uniques = True

        # 处理涨价效果行
        if in_uniques:
            cost_increase_match = re.match(r'^\s*"Cost increases by \[(\d+)\] when built"', line)

            if cost_increase_match:
                value = int(cost_increase_match.group(1))

                # 判断是否是地标建筑
                is_landmark = (current_building_name and current_building_name.startswith('Building.DistrictUnique.'))
                is_replacement = (replaces_building and replaces_building.startswith('Building.DistrictUnique.'))

                if is_landmark or is_replacement:
                    # 地标建筑：翻倍
                    stats['landmark_buildings_doubled'] += 1
                    new_value = value * 2
                    line = re.sub(r'\[(\d+)\]', f'[{new_value}]', line)
                    output_lines.append(line)
                else:
                    # 普通建筑：删除
                    stats['normal_buildings_removed'] += 1
                    continue  # 跳过这一行
            else:
                output_lines.append(line)
        else:
            output_lines.append(line)

        # 检测是否退出 uniques 数组
        if in_uniques and ']' in line:
            # 检查这是否是 uniques 数组的结束
            # 简单检查：如果这一行有 ] 且之后没有其他内容（除了逗号）
            remaining = line.split(']')[1] if ']' in line else ''
            if not re.search(r'\S', remaining) or remaining.strip() in ['', ',', '},']:
                in_uniques = False

        # 跟踪大括号深度
        bracket_depth += line.count('{') - line.count('}')

        # 检测是否退出建筑定义
        if in_building and bracket_depth == 0:
            in_building = False
            current_building_name = None
            replaces_building = None

    # 写回文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(output_lines)

    # 打印统计信息
    print("=" * 60)
    print("建筑涨价效果修改完成")
    print("=" * 60)
    print(f"普通建筑删除涨价效果: {stats['normal_buildings_removed']}")
    print(f"区域地标建筑翻倍涨价幅度: {stats['landmark_buildings_doubled']}")
    print("=" * 60)
    print(f"修改后的文件已保存到: {output_file}")
    print("注释和格式已保留")

if __name__ == '__main__':
    process_buildings()