# CoeHarMod 项目记忆文档

> 项目文档生成时间: 2026-02-12

## 项目概述

**CoeHarMod**（和合共生模组）是一个为开源策略游戏 Unciv 开发的大型规则集模组，旨在提供比原版更丰富、更复杂的游戏体验。

### 基本信息

- **项目名称**: CoeHarMod
- **作者**: AutumnPizazz
- **项目地址**: [CoeHarMod](https://github.com/AutumnPizazz/CoeHarMod)
- **当前分支**: main
- **适配版本**: Unciv 4.19.11
- **最近版本**: v3.3.8

## 项目结构

```txt
D:\unciv3\mods\CoeHarMod\
├── jsons/                 # 模组核心配置文件（JSON 格式）
│   ├── Beliefs.json       # 宗教信条
│   ├── Buildings.json     # 建筑定义
│   ├── Cities.json        # 城市相关
│   ├── Eras.json          # 时代定义
│   ├── Nations.json       # 文明定义
│   ├── Policies.json      # 政策卡
│   ├── Relifions.json     # 宗教定义
│   ├── Units.json         # 单位定义
│   ├── VictoryTypes.json  # 胜利类型
│   ├── translations/      # 翻译文件
│   └── TileSets/          # 地形图集配置
├── Atlases.json           # 图集索引文件
├── *.atlas                # 图集配置文件（LibGDX 格式）
├── *.png                  # 图集纹理图片
├── sounds/                # 音效文件
└── python_tool/           # Python 构建工具
```

### 核心文件配置

模组运行所需的核心文件采用白名单机制定义（参见 `python_tool/core_files.py`）：

- `Atlases.json` - 图集索引
- `*.atlas` - LibGDX 图集配置文件
- `*.png` - 图集纹理图片
- `jsons/**` - 所有 JSON 配置文件
- `sounds/**` - 音效资源

## 核心功能特性

### 1. 多元胜利路径

- **科技胜利**: 航天港太空项目（火星殖民、星际探索、拉格朗日激光站等）
- **文化胜利**: 完成两个政策分支 + "乌托邦计划"
- **宗教胜利**: 宗教成为全球每一座城市的主流宗教
- **经济胜利**: "经济胜利建筑" + 全球最富有
- **外交胜利**: 外交支持 + "众拥之证"
- **征服胜利**: 占领所有主要文明首都
- **统一胜利**: 消灭所有敌对玩家
- **时间胜利**: 最大回合数最高总分

### 2. 深度文明系统

包含 30+ 文明，各具独特能力（UU）：

- 中国系列：秦朝（太尉）、汉朝（虎贲军）、唐朝（陌刀手）、明朝（虎蹲炮）、苏维埃中国（红军）
- 其他：拜占庭、印尼、马里、法兰西等
- 特色单位类型：武僧、吸血鬼、间谍、特种部队、游骑兵等

### 3. 政体与总督系统

- **政体建筑**: 五级演进树
- **通用总督**:
  - 马格努斯（生产力、住房、开拓者）
  - 瑞纳（贸易、商业区）
  - 阿玛尼（城邦、外交）
  - 维克多（军事、核武）
  - 平加拉（科技、伟人）
  - 梁（建造者、区域）
  - 莫克夏（文化、宗教）
  - 大维齐尔（综合型）

### 4. 游戏模式

通过建造特定建筑启用：

- **秘密结社（Camorrist）**: 虚空吟唱、明德夜莺、黄金黎明、血色契约
- **斗地主模式（Landlords）**: 非对称对抗
- **通用总督（Viceroy）**: 总督能力系统
- **世界奇观（WorldWonders）**: 奇观系统开关

### 5. 核心机制调整

#### 快乐与厌战系统

- **城均快乐**: 快乐÷城市数

- 每点平均快乐 → 全国 +5% 生产力/科研/文化/金币/信仰
- 平均快乐 < -2: 人口增长停止
- 平均快乐 < -4: 可能叛变

#### 战略资源

- **基本战略资源**: 铁、硝石、马、石油等
- **军营建筑**: +2 战略资源提供
- 区域和奇观可建在资源地块上（战略资源可改良，奢侈品不可）

#### 砍伐机制

- 固定收益（标准速度）: 森林+20锤, 雨林+10粮10锤, 沼泽+20粮
- 砍伐时间: 2回合

#### 攻城调整

- 攻城单位: +104% 战斗力（对海+70%）
- 城市基础血量: 400HP

## 技术栈

### 开发工具

- **Python 3**: 构建脚本（`python_tool/`）
- **PowerShell**: Windows 命令行操作
- **Git**: 版本控制

### 构建工具

1. **build_mod.py**: 主打包脚本
   - 根据核心文件定义打包模组
   - 输出: `CoeHarMod_{version}.zip`
2. **core_files.py**: 核心文件定义
   - 白名单机制
   - 支持模式匹配和路径过滤
3. **extract_changelog.py**: 从更新日志提取版本信息

### 自动化

- **GitHub Actions**:
  - `deploy.yml`: VitePress 文档站自动部署
  - `release.yml`: 自动发布模组（v.x.x.x 标签触发）

### 文档

- **VitePress**: 基于 Vue 的静态站点生成器
- **文档站**: https://autumnpizazz.github.io/CoeHarMod/

## 版本控制

### Git 配置

- **远程仓库**: https://github.com/AutumnPizazz/CoeHarMod.git
- **当前分支**: main
- **主分支 HEAD**: 1386c825ea8b00a14cad881398ff8378be0cd353

### 工作流状态

```txt
Modified: .gitignore
Untracked: IFLOW.md
```

## 关键文件说明

### 模组配置

- `jsons/ModOptions.json`: 模组元数据、作者、版本、常量配置
- `jsons/GlobalUniques.json`: 全局唯一效果定义

### 构建脚本

- `python_tool/build_mod.py`: 模组打包
- `python_tool/core_files.py`: 核心文件定义
- `python_tool/local_build.py`: 本地快速构建
- `python_tool/extract_changelog.py`: 更新日志解析

### docs文档

- `docs/index.md`: 文档站点首页
- `docs/CoeHarMod专区/更新日志.md`: 版本更新记录
- `docs/CoeHarMod专区/更新计划.md`: 未来开发计划
- `docs/原版专区/`: Unciv 原版攻略

## 开发注意事项

### 代码约定

1. **JSON 配置**: 所有游戏元素通过 JSON 定义
2. **中文优先**: 界面文本使用简体中文
3. **平衡性调整**: 优先考虑游戏平衡而非数值堆砌
4. **模块化设计**: 通过 JSON 配置实现可扩展性

### 构建流程

```powershell
# 本地打包
cd D:\unciv3\mods\CoeHarMod\python_tool
python build_mod.py [version]

# 快速打包（使用 bat 脚本）
本地快速打包CH.bat
```

### 文档更新

```powershell
cd D:\unciv3\mods\CoeHarMod\docs
npm install
npm run docs:build
npm run docs:dev  # 预览
```

## 社区资源

- **Unciv 官方仓库**: https://github.com/yairm210/Unciv
- **Unciv 中文社区群**: https://qm.qq.com/q/G5lpttg688
- **CoeHarMod 模组群**: https://qm.qq.com/q/amwSqibPmo

## 特殊说明

### Windows 兼容性

- 使用 PowerShell 语法（不支持 `&&` 链接）
- 使用 `dir` 代替 `ls`，`copy` 代替 `cp`，`type` 代替 `cat`
- 路径分隔符：`\`（但多数工具也接受 `/`）

### 工具可用性

- ✅ `git` - 版本控制
- ✅ `curl` - 网络请求
- ❌ `rg` (ripgrep) - 未安装
- ❌ `gh` (GitHub CLI) - 未安装
- ❌ `python` - 未安装（使用 python_tool 脚本时需单独安装）
- ❌ `ffmpeg` - 未安装

## 环境信息

- **操作系统**: Windows 10.0.26200 (win32)
- **Git 版本**: 2.48.1.windows.1
- **Python**: 未安装
- **Node.js**: 通过 npm 在 docs 目录使用
- **工作目录**: D:\unciv3\mods\CoeHarMod
