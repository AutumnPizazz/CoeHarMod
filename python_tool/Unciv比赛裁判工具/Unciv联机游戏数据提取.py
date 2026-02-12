#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unciv API 胜利面板数据读取工具

此程序通过Unciv的多人游戏API获取游戏数据，提取胜利面板数据并输出为CSV格式。
支持交互式窗口，便于打包为EXE。
"""

import json
import csv
import sys
import requests
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

# 默认服务器地址
DEFAULT_SERVER = "http://sp.unciv.cn:30123"


class ConfigManager:
    """配置管理器"""

    CONFIG_FILE = 'unciv_config.json'
    README_FILE = '使用说明.txt'

    @staticmethod
    def get_script_dir():
        """获取脚本目录（兼容exe模式）"""
        if getattr(sys, 'frozen', False):
            # 打包为exe时，使用exe所在目录
            return os.path.dirname(sys.executable)
        else:
            # 正常运行时，使用脚本所在目录
            return os.path.dirname(os.path.abspath(__file__))

    @staticmethod
    def ensure_files_exist():
        """确保配置文件和说明文件存在"""
        script_dir = ConfigManager.get_script_dir()
        config_path = os.path.join(script_dir, ConfigManager.CONFIG_FILE)
        readme_path = os.path.join(script_dir, ConfigManager.README_FILE)

        # 生成配置文件
        if not os.path.exists(config_path):
            default_config = {
                "服务器": "http://sp.unciv.cn:30123",
                "用户名": "",
                "密码": "",
                "游戏ID": "",
                "输出文件": "victory_data.csv",
                "score_config": ScoreConfig.DEFAULT_CONFIG
            }
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            print(f"已生成配置文件: {config_path}")

        # 生成说明文件
        if not os.path.exists(readme_path):
            readme_content = """Unciv比赛裁判工具 - 使用说明
==============================

一、配置文件说明
----------------
配置文件：unciv_config.json

所有参数都是中文，直接修改即可。

二、连接配置
----------------
服务器：Unciv服务器地址
用户名：登录用户名
密码：登录密码
游戏ID：要提取的游戏ID
输出文件：CSV输出文件路径

三、比赛得分配置
----------------
得分计算公式：(我的数值 - 对手平均数值) × 分子 / 分母

1. 基础配置
   基础分：所有文明起始得分（默认100）
   存活奖励：存活文明的额外加分（默认30）
   击败惩罚：被击败文明的扣分（默认-30）

2. 综合实力分（上限±20分）
   - 文明积分：反映文明整体发展水平
   - 军事实力：反映军事力量
   - 科技领先：反映科技研究进度
   
   配置格式：{"分母": 数值, "分子": 数值}
   例如：{"分母": 5, "分子": 1} 表示每5文明积分差距得1分

3. 发展指标分（上限±15分）
   - 人口：文明总人口
   - 城市数：拥有的城市数量
   - 领土：控制的地块数（估算公式：城市数×5+人口÷2）

4. 经济健康分（上限±10分）
   - 现金：当前现金储备
   - 回合金：每回合净收入

5. 文明进步分（上限±10分）
   - 已采纳政策：完成的社会政策数量

6. 幸福度（无上限）
   各自以0为基准计算，每±1幸福度得±1分

四、快速调整指南
----------------
- 想要军事更重要？
  → 修改"综合实力分.军事实力"，降低"分母"（如50改为25）或提高"分子"（如1改为2）

- 想要城市更重要？
  → 修改"发展指标分.城市数"，提高"分子"（如2改为5）

- 想要科技更重要？
  → 修改"综合实力分.科技领先"，降低"分母"（如2改为1）

- 想要经济更重要？
  → 修改"经济健康分"，降低各分母值

- 想要整体分数更高？
  → 提高各维度的"上限"值

五、注意事项
----------------
1. 城邦（City-State）不会参与得分计算
2. 看海玩家（0城市）不会参与得分计算
3. 每个文明的得分通过与所有其他玩家的平均值对比来计算
4. 各维度有上限设置，避免优势无限放大
5. 程序会自动跳过不参与计算的文明

六、运行程序
----------------
直接运行程序，根据提示输入服务器地址、用户名、密码和游戏ID即可。
"""
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            print(f"已生成说明文件: {readme_path}")

    @staticmethod
    def load_config() -> Dict[str, str]:
        """加载配置"""
        script_dir = ConfigManager.get_script_dir()
        config_path = os.path.join(script_dir, ConfigManager.CONFIG_FILE)

        if not os.path.exists(config_path):
            return {}

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            # 将中文参数名映射到内部使用的英文参数名
            mapped_config = {
                'server': config.get('服务器', ''),
                'username': config.get('用户名', ''),
                'password': config.get('密码', ''),
                'game_id': config.get('游戏ID', ''),
                'output_file': config.get('输出文件', 'victory_data.csv'),
            }
            return mapped_config
        except Exception as e:
            print(f"加载配置失败: {e}")
            return {}

    @staticmethod
    def save_config(config: Dict[str, str]) -> None:
        """保存配置"""
        try:
            script_dir = ConfigManager.get_script_dir()
            config_path = os.path.join(script_dir, ConfigManager.CONFIG_FILE)

            # 如果输出文件在脚本目录下，保存为相对路径
            output_file = config.get('output_file', 'victory_data.csv')
            abs_output = os.path.abspath(output_file)
            abs_script = os.path.abspath(script_dir)
            if abs_output.startswith(abs_script):
                output_file = os.path.relpath(abs_output, abs_script)

            # 使用中文参数名保存
            config_to_save = {
                '服务器': config.get('server', ''),
                '用户名': config.get('username', ''),
                '密码': config.get('password', ''),
                '游戏ID': config.get('game_id', ''),
                '输出文件': output_file,
            }

            # 保留原有的 score_config
            config_with_score = {}
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_with_score = json.load(f)
            config_with_score.update(config_to_save)

            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_with_score, f, ensure_ascii=False, indent=2)
            print(f"配置已保存到: {config_path}")
        except Exception as e:
            print(f"保存配置失败: {e}")


class ScoreConfig:
    """比赛得分配置"""

    # 默认配置
    DEFAULT_CONFIG = {
        '基础分': 100,
        '存活奖励': 30,
        '击败惩罚': -30,
        '综合实力分': {
            '上限': 20,
            '文明积分': {'分母': 5, '分子': 1},      # 每5文明积分差距 ±1分
            '军事实力': {'分母': 50, '分子': 1},     # 每50军事实力差距 ±1分
            '科技领先': {'分母': 2, '分子': 1}        # 每2科技差距 ±1分
        },
        '发展指标分': {
            '上限': 15,
            '人口': {'分母': 3, '分子': 1},        # 每3人口差距 ±1分
            '城市数': {'分母': 1, '分子': 2},       # 每1城市差距 ±2分
            '领土': {'分母': 10, '分子': 1}        # 每10领土差距 ±1分
        },
        '经济健康分': {
            '上限': 10,
            '现金': {'分母': 50, '分子': 1},              # 每50现金差距 ±1分
            '回合金': {'分母': 5, '分子': 1}       # 每5回合金差距 ±1分
        },
        '文明进步分': {
            '上限': 10,
            '已采纳政策': {'分母': 1, '分子': 2}       # 每1政策差距 ±2分
        }
    }

    def __init__(self, config: Dict[str, Any] = None):
        """初始化得分配置"""
        self.config = self.DEFAULT_CONFIG.copy()
        if config:
            self._merge_config(config)

    def _merge_config(self, config: Dict[str, Any]) -> None:
        """合并配置"""
        for key, value in config.items():
            if key in self.config and isinstance(self.config[key], dict) and isinstance(value, dict):
                self.config[key].update(value)
            else:
                self.config[key] = value

    @staticmethod
    def load_from_file(config_file: str) -> 'ScoreConfig':
        """从文件加载配置"""
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return ScoreConfig(config.get('score_config', {}))
            except Exception as e:
                print(f"加载得分配置失败: {e}")
        return ScoreConfig()

    def save_to_file(self, config_file: str) -> bool:
        """保存配置到文件"""
        try:
            # 如果文件已存在，读取并保留其他配置
            existing_config = {}
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    existing_config = json.load(f)

            # 更新得分配置
            existing_config['score_config'] = self.config

            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(existing_config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存得分配置失败: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(key, default)


class UncivAPIClient:
    """Unciv API客户端"""

    def __init__(self, base_url: str):
        """
        初始化API客户端

        Args:
            base_url: Unciv服务器URL
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        # 设置User-Agent
        self.session.headers.update({
            'User-Agent': 'Unciv'
        })
        self.username = None
        self.password = None

    def is_alive(self) -> bool:
        """检查服务器是否在线"""
        try:
            response = self.session.get(f"{self.base_url}/isalive", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return 'authVersion' in data
            return False
        except Exception as e:
            print(f"检查服务器状态失败: {e}")
            return False

    def login(self, username: str, password: str) -> bool:
        """登录Unciv账户（使用Basic Auth）"""
        self.username = username
        self.password = password
        try:
            # 使用Basic Auth测试连接
            response = self.session.get(
                f"{self.base_url}/auth",
                auth=(username, password),
                timeout=10
            )
            print(f"登录响应状态码: {response.status_code}")
            
            # V1 API: 200表示有权限，204表示无权限但账号存在，401表示认证失败
            if response.status_code in [200, 204]:
                print("登录成功")
                # 为后续请求设置认证
                self.session.auth = (username, password)
                return True
            else:
                print(f"登录失败: HTTP {response.status_code}")
                print(f"响应内容: {response.text}")
            return False
        except Exception as e:
            print(f"登录失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def list_files(self) -> List[str]:
        """获取文件列表"""
        try:
            response = self.session.get(f"{self.base_url}/files", timeout=30)
            print(f"文件列表响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                files_list = response.json()
                print(f"文件列表响应类型: {type(files_list)}")
                if isinstance(files_list, list):
                    print(f"找到 {len(files_list)} 个文件")
                    return files_list
                else:
                    print(f"响应不是列表: {files_list}")
            else:
                print(f"响应内容: {response.text}")
            return []
        except Exception as e:
            print(f"获取文件列表失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_file(self, file_name: str) -> Optional[str]:
        """获取文件内容（使用gameId作为路径参数）"""
        try:
            # 使用gameId作为路径参数: /files/{gameId}
            response = self.session.get(f"{self.base_url}/files/{file_name}", timeout=30)
            if response.status_code == 200:
                return response.text
            elif response.status_code == 404:
                print(f"文件不存在: {file_name}")
            else:
                print(f"获取文件失败: HTTP {response.status_code}")
                print(f"响应内容: {response.text}")
            return None
        except Exception as e:
            print(f"获取文件失败: {e}")
            return None


class VictoryDataExtractor:
    """从API获取的游戏数据中提取胜利面板数据"""

    def __init__(self, score_config: ScoreConfig = None):
        self.game_data = None
        self.score_config = score_config if score_config else ScoreConfig()

    def load_from_api(self, api_client: UncivAPIClient, game_id: str) -> bool:
        """从API加载游戏数据（V1 API）"""
        # V1 API: 直接使用游戏ID作为文件名
        print(f"\n正在下载游戏存档: {game_id}")
        
        # 直接获取文件
        save_data = api_client.get_file(game_id)
        if not save_data:
            print(f"错误: 无法下载存档文件 '{game_id}'")
            print("\n请确认:")
            print("1. 游戏ID是否正确")
            print("2. 服务器上是否存在该文件")
            return False

        # 解析存档
        try:
            import base64
            import gzip

            # 检查是否是base64编码
            if save_data.startswith('{') or save_data.startswith('['):
                # 直接是JSON
                self.game_data = json.loads(save_data)
            else:
                # Base64解码
                try:
                    decoded = base64.b64decode(save_data)
                    
                    # 检查是否是gzip
                    try:
                        decompressed = gzip.decompress(decoded)
                        self.game_data = json.loads(decompressed.decode('utf-8'))
                    except:
                        # 不是gzip，直接解析
                        self.game_data = json.loads(decoded.decode('utf-8'))
                except:
                    # 解析失败，直接作为JSON
                    self.game_data = json.loads(save_data)

            print(f"\n成功加载游戏数据")
            return True

        except Exception as e:
            print(f"解析游戏数据失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_victory_data(self) -> List[Dict[str, Any]]:
        """提取胜利面板数据"""
        if not self.game_data:
            return []

        civilizations = self.game_data.get('civilizations', [])
        ruleset = self.game_data.get('ruleset', {})
        nations = ruleset.get('nations', {})
        victory_data_list = []

        for civ in civilizations:
            civ_id = civ.get('civID', '')
            civ_name = civ.get('civName', civ_id)

            # 跳过野蛮人和观察者
            if civ.get('isBarbarian', False) or civ.get('isSpectator', False):
                continue

            # 判断是否是城邦
            nation_info = nations.get(civ_name, {})
            is_city_state = nation_info.get('cityStateType') is not None

            # 判断是否已击败
            is_defeated = self._is_civ_defeated(civ)

            # 构建文明数据
            civ_data = {
                '文明ID': civ_id,
                '文明名称': civ_name,
                '状态': '已击败' if is_defeated else '存活',
                '玩家类型': '人类' if civ.get('playerType') == 'Human' else 'AI',
                '是否城邦': is_city_state,
            }

            # 添加基础数据
            civ_data.update(self._get_basic_stats(civ))

            # 添加分数明细
            civ_data.update(self._get_score_breakdown(civ))

            victory_data_list.append(civ_data)

        # 计算比赛得分
        victory_data_list = self._calculate_match_score(victory_data_list, self.score_config)

        return victory_data_list

    def _is_civ_defeated(self, civ: Dict[str, Any]) -> bool:
        """判断文明是否被击败"""
        has_ever_owned_original_capital = civ.get('hasEverOwnedOriginalCapital', False)
        cities = civ.get('cities', [])
        units = civ.get('units', {}).get('mapUnits', [])

        if has_ever_owned_original_capital:
            return len(cities) == 0
        else:
            return len(units) == 0

    def _get_basic_stats(self, civ: Dict[str, Any]) -> Dict[str, Any]:
        """获取基础统计数据"""
        cities = civ.get('cities', [])
        gold = civ.get('gold', 0)

        # 从 statsHistory 中获取统计数据
        population = 0
        gold_per_turn = 0
        happiness = 0
        force = 0
        production = 0
        faith_per_turn = 0

        stats_history = civ.get('statsHistory', {})
        if stats_history and isinstance(stats_history, dict):
            # 获取最新回合 - 将键转换为整数后再比较
            # statsHistory 的键可能是字符串类型 ("0", "1", ...)，需要转为整数比较
            turns = []
            for key in stats_history.keys():
                try:
                    turns.append(int(key))
                except (ValueError, TypeError):
                    pass
            latest_turn = max(turns) if turns else None

            if latest_turn is not None:
                # 用字符串键获取数据
                latest_stats = stats_history.get(str(latest_turn))

                if latest_stats:
                    if isinstance(latest_stats, str):
                        # 新格式：解析统计字符串，例如: S27N1C2P6G26T7F1352H3W2A3
                        # 根据RankingType.kt:
                        # S = Score, N = Population, C = Growth, P = Production
                        # G = Gold, T = Territory, F = Force, H = Happiness
                        # W = Technologies, A = Culture
                        import re
                        patterns = {
                            'N': r'N(-?\d+)',   # Population
                            'G': r'G(-?\d+)',   # Gold per turn
                            'H': r'H(-?\d+)',   # Happiness
                            'F': r'F(-?\d+)',   # Force
                            'P': r'P(-?\d+)',   # Production
                            'A': r'A(-?\d+)',   # Culture
                        }
                        for key, pattern in patterns.items():
                            match = re.search(pattern, latest_stats)
                            if match:
                                value = int(match.group(1))
                                if key == 'N':
                                    population = value
                                elif key == 'G':
                                    gold_per_turn = value
                                elif key == 'H':
                                    happiness = value
                                elif key == 'F':
                                    force = value
                                elif key == 'P':
                                    production = value
                    elif isinstance(latest_stats, dict):
                        # 旧格式：直接从字典获取
                        population = latest_stats.get('N', 0)
                        gold_per_turn = latest_stats.get('G', 0)
                        happiness = latest_stats.get('H', 0)
                        force = latest_stats.get('F', 0)
                        production = latest_stats.get('P', 0)

        # 信仰 - 从 religionManager 获取
        religion_manager = civ.get('religion', {})
        faith_per_turn = 0  # 需要从 cities 计算或从其他地方获取

        # 科技数量
        tech_manager = civ.get('tech', {})
        researched_techs = tech_manager.get('techsResearched', [])
        tech_count = len(researched_techs)

        # 政策数量
        policies_manager = civ.get('policies', {})
        adopted_policies = policies_manager.get('adoptedPolicies', [])
        policy_count = len([p for p in adopted_policies if not p.endswith(' Complete')])

        # 计算总分
        total_score = self._calculate_total_score(civ)

        return {
            '人口': population,
            '现金': gold,
            '回合金': gold_per_turn,
            '幸福度': happiness,
            '军事实力': force,
            '产能': production,
            '城市数': len(cities),
            '已研究科技数': tech_count,
            '已采纳的政策数': policy_count,
            '总文明积分': round(total_score, 2),
        }

    def _calculate_total_score(self, civ: Dict[str, Any]) -> float:
        """计算总分"""
        breakdown = self._calculate_score_breakdown(civ)
        return sum(breakdown.values())

    def _calculate_score_breakdown(self, civ: Dict[str, Any]) -> Dict[str, float]:
        """计算分数明细 - 按照Civilization.kt的calculateScoreBreakdown方法"""
        cities = civ.get('cities', [])
        breakdown = {}

        # 获取mod常量
        mod_constants = self.game_data.get('ruleset', {}).get('modOptions', {}).get('constants', {})
        score_from_population = mod_constants.get('scoreFromPopulation', 1)
        score_from_wonders = mod_constants.get('scoreFromWonders', 25)

        # 计算地图大小修正因子
        tile_map = self.game_data.get('tileMap', {})
        map_parameters = tile_map.get('mapParameters', {})
        map_size = map_parameters.get('mapSize', {})
        shape = map_parameters.get('shape', '')

        # 根据地图形状计算总块数
        if shape in ['hexagonal', 'flatEarth']:
            radius = map_size.get('radius', 20)
            number_of_tiles = 1 + 3 * radius * (radius - 1)
        else:
            number_of_tiles = map_size.get('width', 80) * map_size.get('height', 80)

        # 地图大小修正因子：1276是中等地图的块数
        map_size_modifier = 1276 / max(number_of_tiles, 1)
        if map_size_modifier > 1:
            map_size_modifier = (map_size_modifier - 1) / 3 + 1

        # 城市分数
        breakdown['Cities'] = len(cities) * 10 * map_size_modifier

        # 人口分数 - 从 statsHistory 获取
        population = 0
        stats_history = civ.get('statsHistory', {})
        if stats_history and isinstance(stats_history, dict):
            # 将键转换为整数后再比较
            turns = []
            for key in stats_history.keys():
                try:
                    turns.append(int(key))
                except (ValueError, TypeError):
                    pass
            latest_turn = max(turns) if turns else None

            if latest_turn is not None:
                latest_stats = stats_history.get(str(latest_turn))
                if latest_stats:
                    if isinstance(latest_stats, str):
                        import re
                        pattern = r'N(-?\d+)'
                        match = re.search(pattern, latest_stats)
                        if match:
                            population = int(match.group(1))
                    elif isinstance(latest_stats, dict):
                        population = latest_stats.get('N', 0)
        breakdown['Population'] = population * score_from_population * map_size_modifier

        # 地块分数 - 只计算非水域地块
        # 从 statsHistory 获取领土数
        territory = 0
        stats_history = civ.get('statsHistory', {})
        if stats_history and isinstance(stats_history, dict):
            # 将键转换为整数后再比较
            turns = []
            for key in stats_history.keys():
                try:
                    turns.append(int(key))
                except (ValueError, TypeError):
                    pass
            latest_turn = max(turns) if turns else None

            if latest_turn is not None:
                latest_stats = stats_history.get(str(latest_turn))
                if latest_stats:
                    if isinstance(latest_stats, str):
                        import re
                        pattern = r'T(-?\d+)'
                        match = re.search(pattern, latest_stats)
                        if match:
                            territory = int(match.group(1))
                    elif isinstance(latest_stats, dict):
                        territory = latest_stats.get('T', 0)
        breakdown['Tiles'] = territory * 1 * map_size_modifier

        # 奇观分数 - 检查建筑是否是奇观
        wonder_count = 0
        ruleset = self.game_data.get('ruleset', {})
        buildings = ruleset.get('buildings', {})

        for city in cities:
            built_buildings = city.get('cityConstructions', {}).get('builtBuildings', [])
            for building_name in built_buildings:
                building_info = buildings.get(building_name, {})
                if building_info.get('isWonder', False):
                    wonder_count += 1
        breakdown['Wonders'] = score_from_wonders * wonder_count

        # 科技分数
        tech_manager = civ.get('tech', {})
        tech_count = len(tech_manager.get('techsResearched', []))
        breakdown['Technologies'] = tech_count * 4

        # 未来科技分数
        repeating_techs = tech_manager.get('repeatingTechsResearched', 0)
        breakdown['Future Tech'] = repeating_techs * 10

        return breakdown

    def _get_score_breakdown(self, civ: Dict[str, Any]) -> Dict[str, Any]:
        """获取分数明细"""
        breakdown = self._calculate_score_breakdown(civ)
        total_score = sum(breakdown.values())

        return {
            '分数': round(total_score, 2),
            '城市分数': round(breakdown.get('Cities', 0), 2),
            '人口分数': round(breakdown.get('Population', 0), 2),
            '地块分数': round(breakdown.get('Tiles', 0), 2),
            '奇观分数': round(breakdown.get('Wonders', 0), 2),
            '科技分数': round(breakdown.get('Technologies', 0), 2),
            '未来科技分数': round(breakdown.get('Future Tech', 0), 2),
        }

    def _calculate_match_score(self, civ_data_list: List[Dict[str, Any]], score_config: ScoreConfig = None) -> List[Dict[str, Any]]:
        """
        计算比赛得分 - 公平对决计分系统

        设计原则：
        1. 避免滚雪球效应 - 每个维度设置上下限
        2. 奖励全面发展 - 多维度综合评估
        3. 重视生存能力 - 被击败有显著惩罚
        4. 简单透明 - 易于理解和验证

        Args:
            civ_data_list: 文明数据列表
            score_config: 得分配置对象，如果为None则使用默认配置
        """
        if score_config is None:
            score_config = ScoreConfig()

        if not civ_data_list:
            return civ_data_list

        # 辅助函数：限制数值范围
        def clamp(value: int, min_val: int, max_val: int) -> int:
            return max(min_val, min(max_val, value))

        # 获取配置参数
        base_score = score_config.get('基础分', 100)
        victory_reward = score_config.get('存活奖励', 30)
        defeat_penalty = score_config.get('击败惩罚', -30)

        combat_config = score_config.get('综合实力分', {})
        combat_limit = combat_config.get('上限', 20)
        score_rule = combat_config.get('文明积分', {'分母': 5, '分子': 1})
        force_rule = combat_config.get('军事实力', {'分母': 50, '分子': 1})
        tech_rule = combat_config.get('科技领先', {'分母': 2, '分子': 1})

        development_config = score_config.get('发展指标分', {})
        development_limit = development_config.get('上限', 15)
        pop_rule = development_config.get('人口', {'分母': 3, '分子': 1})
        city_rule = development_config.get('城市数', {'分母': 1, '分子': 2})
        territory_rule = development_config.get('领土', {'分母': 10, '分子': 1})

        economic_config = score_config.get('经济健康分', {})
        economic_limit = economic_config.get('上限', 10)
        gold_rule = economic_config.get('现金', {'分母': 50, '分子': 1})
        gold_per_turn_rule = economic_config.get('回合金', {'分母': 5, '分子': 1})

        civilization_config = score_config.get('文明进步分', {})
        civilization_limit = civilization_config.get('上限', 10)
        policy_rule = civilization_config.get('已采纳政策', {'分母': 1, '分子': 2})

        # 辅助函数：根据规则计算得分
        def calculate_score(diff: int, rule: Dict[str, int]) -> int:
            """根据规则计算得分：得分 = 差距 × 分子 / 分母"""
            分母 = rule.get('分母', 1)
            分子 = rule.get('分子', 1)
            if 分母 == 0:
                return 0
            return diff * 分子 // 分母

        # 计算每个文明的得分
        for civ_data in civ_data_list:
            # 跳过城邦，不计算得分
            if civ_data.get('是否城邦', False):
                civ_data['比赛得分'] = 0
                civ_data['世界奇观'] = 0
                civ_data['自然奇观'] = 0
                civ_data['伟人诞生'] = 0
                continue

            # 跳过看海玩家（0城市或没有城市字段）
            city_count = civ_data.get('城市数', 0)
            if city_count == 0:
                civ_data['比赛得分'] = 0
                civ_data['世界奇观'] = 0
                civ_data['自然奇观'] = 0
                civ_data['伟人诞生'] = 0
                continue

            # 基础分
            score = base_score

            # 胜负判定
            status = civ_data.get('状态', '存活')
            if status == '已击败':
                score += defeat_penalty
            elif status == '存活':
                score += victory_reward

            # 计算与所有其他"非城邦、非看海"文明的平均差距
            other_civs = [c for c in civ_data_list
                         if c != civ_data
                         and not c.get('是否城邦', False)
                         and c.get('城市数', 0) > 0]
            if not other_civs:
                # 如果没有其他非城邦、非看海文明，则无法计算对比，给予基础分
                civ_data['比赛得分'] = round(score, 2)
                civ_data['世界奇观'] = 0
                civ_data['自然奇观'] = 0
                civ_data['伟人诞生'] = 0
                continue

            # 计算各维度与对手的平均差距
            avg_score_diff = 0
            avg_force_diff = 0
            avg_tech_diff = 0
            avg_pop_diff = 0
            avg_city_diff = 0
            avg_territory_diff = 0
            avg_gold_diff = 0
            avg_gold_per_turn_diff = 0
            avg_policy_diff = 0

            for other in other_civs:
                avg_score_diff += civ_data.get('总文明积分', 0) - other.get('总文明积分', 0)
                avg_force_diff += civ_data.get('军事实力', 0) - other.get('军事实力', 0)
                avg_tech_diff += civ_data.get('已研究科技数', 0) - other.get('已研究科技数', 0)
                avg_pop_diff += civ_data.get('人口', 0) - other.get('人口', 0)
                avg_city_diff += civ_data.get('城市数', 0) - other.get('城市数', 0)
                avg_gold_diff += civ_data.get('现金', 0) - other.get('现金', 0)
                avg_gold_per_turn_diff += civ_data.get('回合金', 0) - other.get('回合金', 0)
                avg_policy_diff += civ_data.get('已采纳的政策数', 0) - other.get('已采纳的政策数', 0)

                # 领土估算
                territory = civ_data.get('城市数', 0) * 5 + civ_data.get('人口', 0) // 2
                other_territory = other.get('城市数', 0) * 5 + other.get('人口', 0) // 2
                avg_territory_diff += territory - other_territory

            # 计算平均值
            n = len(other_civs)
            avg_score_diff = avg_score_diff // n
            avg_force_diff = avg_force_diff // n
            avg_tech_diff = avg_tech_diff // n
            avg_pop_diff = avg_pop_diff // n
            avg_city_diff = avg_city_diff // n
            avg_territory_diff = avg_territory_diff // n
            avg_gold_diff = avg_gold_diff // n
            avg_gold_per_turn_diff = avg_gold_per_turn_diff // n
            avg_policy_diff = avg_policy_diff // n

            # ===== 综合实力分 =====
            combat_power = 0
            combat_power += calculate_score(avg_score_diff, score_rule)   # 文明积分
            combat_power += calculate_score(avg_force_diff, force_rule)   # 军事实力
            combat_power += calculate_score(avg_tech_diff, tech_rule)     # 科技领先
            combat_power = clamp(combat_power, -combat_limit, combat_limit)
            score += combat_power

            # ===== 发展指标分 =====
            development_power = 0
            development_power += calculate_score(avg_pop_diff, pop_rule)           # 人口
            development_power += calculate_score(avg_city_diff, city_rule)         # 城市数
            development_power += calculate_score(avg_territory_diff, territory_rule)  # 领土
            development_power = clamp(development_power, -development_limit, development_limit)
            score += development_power

            # ===== 经济健康分 =====
            economic_power = 0
            economic_power += calculate_score(avg_gold_diff, gold_rule)           # 现金储备
            economic_power += calculate_score(avg_gold_per_turn_diff, gold_per_turn_rule)  # 回合金
            economic_power = clamp(economic_power, -economic_limit, economic_limit)
            score += economic_power

            # 幸福度：各自以0为基准，每正/负1快乐 ±1分
            happiness = civ_data.get('幸福度', 0)
            score += happiness

            # ===== 文明进步分 =====
            civilization_power = 0
            civilization_power += calculate_score(avg_policy_diff, policy_rule)  # 已采纳政策
            civilization_power = clamp(civilization_power, -civilization_limit, civilization_limit)
            score += civilization_power

            # 获取额外得分
            extra = self._get_extra_score(civ_data)

            # 添加比赛得分到数据
            civ_data['比赛得分'] = round(score, 2)
            civ_data['世界奇观'] = extra.get('世界奇观', 0)
            civ_data['自然奇观'] = extra.get('自然奇观', 0)
            civ_data['伟人诞生'] = extra.get('伟人诞生', 0)

        return civ_data_list

    def _get_extra_score(self, civ_data: Dict[str, Any]) -> Dict[str, int]:
        """获取额外得分信息（奇观、自然奇观、伟人的数量）"""
        extra = {
            '世界奇观': 0,
            '自然奇观': 0,
            '伟人诞生': 0
        }

        # 从原始游戏数据中获取
        civ_id = civ_data.get('文明ID', '')
        for civ in self.game_data.get('civilizations', []):
            if civ.get('civID') == civ_id:
                # 世界奇观数量
                cities = civ.get('cities', [])
                ruleset = self.game_data.get('ruleset', {})
                buildings = ruleset.get('buildings', {})

                for city in cities:
                    built_buildings = city.get('cityConstructions', {}).get('builtBuildings', [])
                    for building_name in built_buildings:
                        building_info = buildings.get(building_name, {})
                        if building_info.get('isWonder', False):
                            extra['世界奇观'] += 1

                # 自然奇观数量
                natural_wonders = civ.get('naturalWonders', [])
                extra['自然奇观'] = len(natural_wonders) if isinstance(natural_wonders, list) else 0

                # 伟人诞生数量 - 从已生产的单位中统计
                # 伟人是MapUnit，需要检查单位的baseUnit属性
                units = civ.get('units', {})
                map_units = units.get('mapUnits', [])
                ruleset = self.game_data.get('ruleset', {})
                units_info = ruleset.get('units', {})

                for unit in map_units:
                    if isinstance(unit, dict):
                        base_unit_name = unit.get('name', '')
                        unit_info = units_info.get(base_unit_name, {})
                        if unit_info.get('isGreatPerson', False):
                            extra['伟人诞生'] += 1

                break

        return extra


def export_to_csv(data: List[Dict[str, Any]], output_file: str) -> bool:
    """导出数据到CSV文件"""
    if not data:
        print("错误: 没有可导出的数据")
        return False

    # 获取所有字段名
    fieldnames = []
    for item in data:
        for key in item.keys():
            if key not in fieldnames:
                fieldnames.append(key)

    try:
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

        print(f"成功导出数据到: {os.path.abspath(output_file)}")
        print(f"共导出 {len(data)} 个文明的数据")
        return True
    except Exception as e:
        print(f"错误: 导出CSV失败 - {e}")
        return False


def interactive_mode():
    """交互模式"""
    print("=" * 60)
    print("Unciv比赛裁判工具")
    print("=" * 60)
    print()
    print("制作：SpringPizazz")
    print("欢迎加入中文社区QQ群：")
    print("  https://qm.qq.com/q/G5lpttg688")
    print("欢迎加入和合共生模组群：")
    print("  https://qm.qq.com/q/amwSqibPmo")
    print()
    print("=" * 60)
    print()

    # 确保配置文件和说明文件存在
    ConfigManager.ensure_files_exist()
    print()

    # 加载配置
    config = ConfigManager.load_config()
    
    print("上次使用的配置:")
    print(f"  服务器: {config['server']}")
    print(f"  用户名: {config['username'] if config['username'] else '(未设置)'}")
    print(f"  游戏ID: {config['game_id'] if config['game_id'] else '(未设置)'}")
    print(f"  输出文件: {config['output_file']}")
    print()

    # 输入服务器地址
    server = input(f"请输入服务器地址 (默认: {config['server']}): ").strip()
    if not server:
        server = config['server']

    # 输入用户名
    username = input(f"请输入用户名 (默认: {config['username']}): ").strip()
    if not username:
        username = config['username']
    
    if not username:
        print("错误: 用户名不能为空")
        input("\n按回车键退出...")
        return

    # 输入密码
    password = input("请输入密码: ").strip()
    if not password:
        password = config['password']
    
    if not password:
        print("错误: 密码不能为空")
        input("\n按回车键退出...")
        return

    # 输入游戏ID
    game_id = input(f"请输入游戏ID (默认: {config['game_id']}): ").strip()
    if not game_id:
        game_id = config['game_id']
    
    if not game_id:
        print("错误: 游戏ID不能为空")
        input("\n按回车键退出...")
        return

    # 输入输出文件
    output_file = input(f"请输入输出文件路径 (默认: {config['output_file']}): ").strip()
    if not output_file:
        output_file = config['output_file']

    # 保存配置
    new_config = {
        'server': server,
        'username': username,
        'password': password,
        'game_id': game_id,
        'output_file': output_file
    }
    ConfigManager.save_config(new_config)

    print()

    # 创建API客户端
    api_client = UncivAPIClient(server)

    # 检查服务器状态
    print(f"检查服务器: {server}")
    if not api_client.is_alive():
        print("错误: 服务器不在线或不可访问")
        input("\n按回车键退出...")
        return

    print("服务器在线")

    # 登录
    print("\n正在登录...")
    if not api_client.login(username, password):
        print("登录失败")
        input("\n按回车键退出...")
        return

    print("登录成功")

    # 加载游戏数据
    print(f"\n正在加载游戏数据 (ID: {game_id})...")

    # 加载得分配置
    script_dir = ConfigManager.get_script_dir()
    config_path = os.path.join(script_dir, ConfigManager.CONFIG_FILE)
    score_config = ScoreConfig.load_from_file(config_path)

    extractor = VictoryDataExtractor(score_config)
    if not extractor.load_from_api(api_client, game_id):
        print("加载游戏数据失败")
        input("\n按回车键退出...")
        return

    # 提取数据
    print("\n正在提取数据...")
    victory_data = extractor.get_victory_data()
    if not victory_data:
        print("错误: 无法提取数据")
        input("\n按回车键退出...")
        return

    # 显示数据摘要（简单列表格式）
    print('\n' + '=' * 60)
    print('数据摘要')
    print('=' * 60)
    for data in victory_data:
        print(f"\n文明: {data['文明名称']}")
        print(f"  状态: {data['状态']}")
        print(f"  人口: {data['人口']}")
        print(f"  现金: {data['现金']}")
        print(f"  回合金: {data['回合金']}")
        print(f"  幸福度: {data['幸福度']}")
        print(f"  军事实力: {data['军事实力']}")
        print(f"  产能: {data['产能']}")
        print(f"  城市数: {data['城市数']}")
        print(f"  已研究科技数: {data['已研究科技数']}")
        print(f"  已采纳的政策数: {data['已采纳的政策数']}")
        print(f"  总文明积分: {data['总文明积分']}")

    # 显示比赛得分表格
    print('\n' + '=' * 60)
    print('比赛得分')
    print('=' * 60)
    print_score_table(victory_data)

    # 询问是否导出CSV
    print('\n' + '=' * 60)
    export_choice = input("是否导出为CSV文件？(y/n): ").strip().lower()
    if export_choice == 'y':
        if victory_data:
            print(f"即将导出的字段: {list(victory_data[0].keys())}")
        if not export_to_csv(victory_data, output_file):
            input("\n按回车键退出...")
            return
    else:
        print("已取消CSV导出")

    print('\n' + '=' * 60)
    print('完成!')
    print('=' * 60)
    input("\n按回车键退出...")


def print_score_table(data: List[Dict[str, Any]]) -> None:
    """输出比赛得分表格（只包含文明名称、状态、比赛得分）"""
    if not data:
        return

    # 计算字符串的显示宽度（中文字符占2个宽度）
    def get_display_width(s: str) -> int:
        width = 0
        for char in s:
            if '\u4e00' <= char <= '\u9fff':  # 中文字符
                width += 2
            else:
                width += 1
        return width

    # 定义表格列
    columns = ['文明名称', '状态', '比赛得分']

    # 设置固定列宽
    col_widths = {
        '文明名称': 30,
        '状态': 10,
        '比赛得分': 12
    }

    # 辅助函数：填充字符串到指定显示宽度
    def pad_string(s: str, width: int, align: str = 'left') -> str:
        display_width = get_display_width(s)
        padding = width - display_width
        if padding <= 0:
            return s
        if align == 'right':
            return ' ' * padding + s
        elif align == 'center':
            left_pad = padding // 2
            right_pad = padding - left_pad
            return ' ' * left_pad + s + ' ' * right_pad
        else:  # left
            return s + ' ' * padding

    # 构建表头
    header_parts = []
    for col in columns:
        header_parts.append(pad_string(col, col_widths[col], 'center'))
    header_line = '| ' + ' | '.join(header_parts) + ' |'

    # 构建分隔线
    separator_parts = []
    for col in columns:
        separator_parts.append('-' * col_widths[col])
    separator_line = '+-' + '-+-'.join(separator_parts) + '-+'

    print(separator_line)
    print(header_line)
    print(separator_line)

    # 打印数据行
    for row in data:
        data_parts = []
        for col in columns:
            value = str(row.get(col, '-'))
            align = 'right' if col == '比赛得分' else 'left'
            data_parts.append(pad_string(value, col_widths[col], align))
        data_line = '| ' + ' | '.join(data_parts) + ' |'
        print(data_line)

    print(separator_line)


def print_table(data: List[Dict[str, Any]]) -> None:
    """在控制台输出格式化的表格"""
    if not data:
        return

    # 计算字符串的显示宽度（中文字符占2个宽度）
    def get_display_width(s: str) -> int:
        width = 0
        for char in s:
            if '\u4e00' <= char <= '\u9fff':  # 中文字符
                width += 2
            else:
                width += 1
        return width

    # 定义表格列
    columns = [
        '文明名称', '状态', '人口', '现金', '回合金',
        '幸福度', '军事实力', '产能', '城市数',
        '已研究科技数', '已采纳的政策数', '总文明积分',
        '比赛得分', '世界奇观', '自然奇观', '伟人诞生'
    ]

    # 设置固定列宽（显示宽度）
    col_widths = {
        '文明名称': 20,
        '状态': 8,
        '人口': 8,
        '现金': 10,
        '回合金': 10,
        '幸福度': 8,
        '军事实力': 10,
        '产能': 8,
        '城市数': 8,
        '已研究科技数': 12,
        '已采纳的政策数': 12,
        '总文明积分': 12,
        '比赛得分': 10,
        '世界奇观': 10,
        '自然奇观': 10,
        '伟人诞生': 10
    }

    # 辅助函数：填充字符串到指定显示宽度
    def pad_string(s: str, width: int, align: str = 'left') -> str:
        display_width = get_display_width(s)
        padding = width - display_width
        if padding <= 0:
            return s
        if align == 'right':
            return ' ' * padding + s
        elif align == 'center':
            left_pad = padding // 2
            right_pad = padding - left_pad
            return ' ' * left_pad + s + ' ' * right_pad
        else:  # left
            return s + ' ' * padding

    # 构建表头
    header_parts = []
    for col in columns:
        header_parts.append(pad_string(col, col_widths[col], 'center'))
    header_line = '| ' + ' | '.join(header_parts) + ' |'

    # 构建分隔线
    separator_parts = []
    for col in columns:
        separator_parts.append('-' * col_widths[col])
    separator_line = '+-' + '-+-'.join(separator_parts) + '-+'

    print(separator_line)
    print(header_line)
    print(separator_line)

    # 打印数据行
    for row in data:
        data_parts = []
        for col in columns:
            value = str(row.get(col, '-'))
            # 数字右对齐，文本左对齐
            align = 'right' if col in ['人口', '现金', '回合金', '幸福度', '军事实力', '产能', '城市数',
                                       '已研究科技数', '已采纳的政策数', '总文明积分', '比赛得分',
                                       '世界奇观', '自然奇观', '伟人诞生'] else 'left'
            data_parts.append(pad_string(value, col_widths[col], align))
        data_line = '| ' + ' | '.join(data_parts) + ' |'
        print(data_line)

    print(separator_line)


def main():
    """主函数"""
    # 如果有命令行参数，使用命令行模式
    if len(sys.argv) > 1:
        print("请使用交互式模式")
        print("直接运行程序，无需命令行参数")
        print(f"检测到的参数: {' '.join(sys.argv[1:])}")
        input("\n按回车键退出...")
        return 1

    # 交互式模式
    try:
        interactive_mode()
        return 0
    except KeyboardInterrupt:
        print('\n\n用户中断')
        return 0
    except Exception as e:
        print(f'\n错误: {e}')
        import traceback
        traceback.print_exc()
        input("\n按回车键退出...")
        return 1


if __name__ == '__main__':
    sys.exit(main())