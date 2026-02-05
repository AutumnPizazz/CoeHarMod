#!/usr/bin/env python3
"""
Mod Wiki Builder for CoeHarMod
Based on Unciv's Civilopedia logic (https://github.com/yairm210/Unciv)
"""
import json
import re
import sys
from pathlib import Path
from typing import Dict, Any, List
from urllib.request import urlopen

# ==================== 配置 ====================
MOD_ROOT = Path("python")
JSON_DIR = MOD_ROOT / "jsons"
IMAGES_DIR = MOD_ROOT / "Images"
OUTPUT_DIR = MOD_ROOT / "wiki-output"
BASE_TRANSLATIONS_URL = "https://raw.githubusercontent.com/yairm210/Unciv/master/android/assets/jsons/translations"

LANGUAGES = ["English", "Simplified_Chinese"]


# ==================== 工具函数 ====================

def download_file(url: str, target: Path):
    """安全下载文件"""
    try:
        with urlopen(url) as response, open(target, 'wb') as f:
            f.write(response.read())
        print(f"✅ Downloaded: {target.name}")
    except Exception as e:
        print(f"⚠️ Failed to download {url}: {e}", file=sys.stderr)


def load_properties(file_path: Path) -> Dict[str, str]:
    """加载 .properties 文件"""
    if not file_path.exists():
        return {}
    trans = {}
    with open(file_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                trans[key.strip()] = value.strip().replace("\\n", "\n")
    return trans


def replace_placeholders(text: str, trans: Dict[str, str], depth=0) -> str:
    """递归替换 [key] 占位符（模仿 Unciv 的 Translatable.replacePlaceholders）"""
    if depth > 5 or not isinstance(text, str):
        return text

    def replace_match(match):
        inner = match.group(1).strip()
        # 跳过纯数字（如 [1]）
        if inner.isdigit():
            return match.group(0)
        # 递归翻译内部
        translated_inner = replace_placeholders(inner, trans, depth + 1)
        # 尝试整体翻译（如 "Provides [1] [Resource.Unit.Scientist]"）
        full_key = f"[{translated_inner}]"
        if full_key in trans:
            return trans[full_key]
        return f"[{translated_inner}]"

    # 先处理最内层占位符
    result = re.sub(r"\$([^]]+)\$", replace_match, text)

    # 最后尝试翻译整个字符串（Unciv 中常见模式）
    if result in trans:
        return trans[result]
    return result


def translate_value(value: Any, trans: Dict[str, str]) -> Any:
    """深度翻译任意值（模仿 Unciv 的 TranslationFileReader）"""
    if isinstance(value, str):
        return replace_placeholders(value, trans)
    elif isinstance(value, dict):
        return {k: translate_value(v, trans) for k, v in value.items()}
    elif isinstance(value, list):
        return [translate_value(item, trans) for item in value]
    return value


def find_image(name: str) -> Path | None:
    """严格按 name 匹配图片（Unciv 图片命名规则）"""
    if not name:
        return None
    image_path = IMAGES_DIR / f"{name}.png"
    if image_path.exists():
        return image_path.relative_to(MOD_ROOT)
    return None


# ==================== 主流程 ====================

def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    # 1. 下载基础翻译
    base_trans_dir = MOD_ROOT / "base_translations"
    base_trans_dir.mkdir(exist_ok=True)
    for lang in LANGUAGES:
        url = f"{BASE_TRANSLATIONS_URL}/{lang}.properties"
        target = base_trans_dir / f"{lang}.properties"
        if not target.exists():
            download_file(url, target)

    # 2. 为每种语言生成文档
    for lang in LANGUAGES:
        print(f"\n🌍 Processing language: {lang}")
        lang_output = OUTPUT_DIR / lang
        lang_output.mkdir(parents=True, exist_ok=True)

        # 合并翻译：本地 > 基础
        base_trans = load_properties(base_trans_dir / f"{lang}.properties")
        local_trans = load_properties(JSON_DIR / "translations" / f"{lang}.properties")
        merged_trans = {**base_trans, **local_trans}  # 本地覆盖基础

        # 处理每个 JSON 文件
        for json_file in JSON_DIR.glob("*.json"):
            if json_file.parent.name == "translations":
                continue

            print(f"  📄 {json_file.name}")
            try:
                with open(json_file, encoding="utf-8") as f:
                    entries = json.load(f)

                md_lines = [f"# {json_file.stem}\n"]
                for entry in entries:
                    if not isinstance(entry, dict) or "name" not in entry:
                        continue

                    # 深度翻译条目
                    translated_entry = {
                        k: translate_value(v, merged_trans)
                        for k, v in entry.items()
                    }

                    name = translated_entry["name"]
                    md_lines.append(f"## {name}\n")

                    # 添加图片
                    if img_rel := find_image(entry.get("name")):
                        md_lines.append(f"![{name}]({img_rel})\n")

                    # 提取分类（Class.* 字段）
                    categories = []
                    for k, v in translated_entry.items():
                        if k.startswith("Class.") and v != "<hidden from users>":
                            categories.append(str(v))
                    if categories:
                        md_lines.append(f"**分类**: {', '.join(categories)}\n")

                    # 基础字段（跳过特殊字段）
                    skip_keys = {"name", "uniques", "specialistSlots"}
                    for k, v in translated_entry.items():
                        if k in skip_keys or k.startswith("Class."):
                            continue
                        if isinstance(v, (dict, list)):
                            continue  # 复杂结构暂不展开
                        md_lines.append(f"- **{k.title()}**: {v}")

                    # specialistSlots
                    if "specialistSlots" in translated_entry:
                        md_lines.append("\n**专家槽位**:")
                        for role, count in translated_entry["specialistSlots"].items():
                            md_lines.append(f"- {role}: {count}")

                    # uniques
                    if "uniques" in translated_entry and isinstance(translated_entry["uniques"], list):
                        md_lines.append("\n**独特效果**:")
                        for u in translated_entry["uniques"]:
                            md_lines.append(f"- {u}")

                    md_lines.append("\n---\n")

                # 写入文件
                output_file = lang_output / f"{json_file.stem}.md"
                output_file.write_text("\n".join(md_lines), encoding="utf-8")

            except Exception as e:
                print(f"  ❌ Error processing {json_file}: {e}", file=sys.stderr)

    # 生成首页
    (OUTPUT_DIR / "index.md").write_text(
        "# CoeHarMod 百科\n\n"
        "- [English](English/)\n"
        "- [简体中文](Simplified_Chinese/)\n"
    )
    print(f"\n🎉 Wiki generated at: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()