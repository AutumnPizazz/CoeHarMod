#!/usr/bin/env python3
"""
Mod Wiki Builder for CoeHarMod
- Supports Unciv-style JSON (with comments)
- Outputs to docs/ (for GitHub Pages on main branch)
- Stores temp files in python/ directory
- Handles ModOptions.json correctly
"""
import json
import sys
from pathlib import Path
from urllib.request import urlopen
from typing import Dict, Any, List, Union

# ==================== 配置 ====================
MOD_ROOT = Path(__file__).parent.resolve()
PYTHON_DIR = MOD_ROOT / "python"  # ← 临时文件目录
JSON_DIR = MOD_ROOT / "jsons"
IMAGES_DIR = MOD_ROOT / "Images"
OUTPUT_DIR = MOD_ROOT / "docs"  # ← GitHub Pages 标准目录
BASE_TRANSLATIONS_URL = "https://raw.githubusercontent.com/yairm210/Unciv/master/android/assets/jsons/translations"

LANGUAGES = ["English", "Simplified_Chinese"]


# ==================== 工具函数 ====================

def strip_json_comments(json_str: str) -> str:
    """安全移除 JSON 注释（不破坏字符串内容）"""
    result = []
    in_string = False
    escape_next = False
    i = 0
    while i < len(json_str):
        char = json_str[i]
        if escape_next:
            escape_next = False
            result.append(char)
        elif char == '\\':
            escape_next = True
            result.append(char)
        elif char == '"':
            in_string = not in_string
            result.append(char)
        elif not in_string and json_str[i:i + 2] == '//':
            while i < len(json_str) and json_str[i] != '\n':
                i += 1
            continue
        elif not in_string and json_str[i:i + 2] == '/*':
            while i < len(json_str) and json_str[i:i + 2] != '*/':
                i += 1
            i += 2
            continue
        else:
            result.append(char)
        i += 1
    return ''.join(result)


def load_unciv_json(file_path: Path) -> Union[List[Dict], Dict]:
    """智能加载 Unciv JSON（兼容注释和纯 JSON）"""
    with open(file_path, encoding="utf-8-sig") as f:  # 处理 UTF-8 BOM
        content = f.read()

    # 先尝试原生解析
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # 去注释后重试
    clean_content = strip_json_comments(content)
    try:
        return json.loads(clean_content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {file_path}: {e}")


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
    """递归替换 [key] 占位符"""
    if depth > 5 or not isinstance(text, str):
        return text

    def replace_match(match):
        inner = match.group(1).strip()
        if inner.isdigit():
            return match.group(0)
        translated_inner = replace_placeholders(inner, trans, depth + 1)
        full_key = f"[{translated_inner}]"
        if full_key in trans:
            return trans[full_key]
        return f"[{translated_inner}]"

    result = re.sub(r"\$([^]]+)\$", replace_match, text)
    if result in trans:
        return trans[result]
    return result


def translate_value(value: Any, trans: Dict[str, str]) -> Any:
    """深度翻译任意值"""
    if isinstance(value, str):
        return replace_placeholders(value, trans)
    elif isinstance(value, dict):
        return {k: translate_value(v, trans) for k, v in value.items()}
    elif isinstance(value, list):
        return [translate_value(item, trans) for item in value]
    return value


def find_image(name: str) -> Path | None:
    """严格按 name 匹配图片"""
    if not name:
        return None
    image_path = IMAGES_DIR / f"{name}.png"
    if image_path.exists():
        return image_path.relative_to(MOD_ROOT)
    return None


# ==================== 主流程 ====================

def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    PYTHON_DIR.mkdir(exist_ok=True)  # 创建 python/ 目录

    if not JSON_DIR.exists():
        print(f"❌ 错误: jsons 目录不存在! 当前路径: {JSON_DIR}", file=sys.stderr)
        sys.exit(1)

    # 1. 下载基础翻译到 python/base_translations/
    base_trans_dir = PYTHON_DIR / "base_translations"
    base_trans_dir.mkdir(exist_ok=True)
    for lang in LANGUAGES:
        url = f"{BASE_TRANSLATIONS_URL}/{lang}.properties"
        target = base_trans_dir / f"{lang}.properties"
        if not target.exists():
            download_file(url, target)

    # 2. 生成文档
    for lang in LANGUAGES:
        print(f"\n🌍 Processing language: {lang}")
        lang_output = OUTPUT_DIR / lang
        lang_output.mkdir(parents=True, exist_ok=True)

        base_trans = load_properties(base_trans_dir / f"{lang}.properties")
        local_trans = load_properties(JSON_DIR / "translations" / f"{lang}.properties")
        merged_trans = {**base_trans, **local_trans}

        for json_file in JSON_DIR.glob("*.json"):
            if json_file.parent.name == "translations":
                continue

            print(f"  📄 {json_file.name}")
            try:
                data = load_unciv_json(json_file)
                # 支持对象或数组
                entries = data if isinstance(data, list) else [data]

                md_lines = [f"# {json_file.stem}\n"]
                for entry in entries:
                    if not isinstance(entry, dict) or "name" not in entry:
                        continue

                    translated_entry = {
                        k: translate_value(v, merged_trans)
                        for k, v in entry.items()
                    }

                    name = translated_entry["name"]
                    md_lines.append(f"## {name}\n")

                    if img_rel := find_image(entry.get("name")):
                        md_lines.append(f"![{name}]({img_rel})\n")

                    categories = []
                    for k, v in translated_entry.items():
                        if k.startswith("Class.") and v != "<hidden from users>":
                            categories.append(str(v))
                    if categories:
                        md_lines.append(f"**分类**: {', '.join(categories)}\n")

                    skip_keys = {"name", "uniques", "specialistSlots"}
                    for k, v in translated_entry.items():
                        if k in skip_keys or k.startswith("Class."):
                            continue
                        if isinstance(v, (dict, list)):
                            continue
                        md_lines.append(f"- **{k.title()}**: {v}")

                    if "specialistSlots" in translated_entry:
                        md_lines.append("\n**专家槽位**:")
                        for role, count in translated_entry["specialistSlots"].items():
                            md_lines.append(f"- {role}: {count}")

                    if "uniques" in translated_entry and isinstance(translated_entry["uniques"], list):
                        md_lines.append("\n**独特效果**:")
                        for u in translated_entry["uniques"]:
                            md_lines.append(f"- {u}")

                    md_lines.append("\n---\n")

                output_file = lang_output / f"{json_file.stem}.md"
                output_file.write_text("\n".join(md_lines), encoding="utf-8")

            except Exception as e:
                print(f"  ❌ Error processing {json_file}: {e}", file=sys.stderr)

    (OUTPUT_DIR / "index.md").write_text(
        "# CoeHarMod 百科\n\n"
        "- [English](English/)\n"
        "- [简体中文](Simplified_Chinese/)\n"
    )
    print(f"\n🎉 Wiki generated at: {OUTPUT_DIR}")


if __name__ == "__main__":
    import re  # 确保 re 在使用前导入

    main()