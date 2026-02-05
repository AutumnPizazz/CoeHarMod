#!/usr/bin/env python3
"""
模组维基构建器 - CoeHarMod - DEBUG TRANSLATION MATCHING
- 添加了详细的调试信息，显示加载的翻译键和查找的键
"""

import json
import sys
from pathlib import Path
from urllib.request import urlopen
from typing import Dict, Any, Union

MOD_ROOT = Path(__file__).parent.resolve()
PYTHON_DIR = MOD_ROOT / "python"
JSON_DIR = MOD_ROOT / "jsons"
IMAGES_DIR = MOD_ROOT / "Images"
OUTPUT_DIR = MOD_ROOT / "docs"

# 设置超时时间
DEFAULT_TIMEOUT = 10  # 秒

BASE_TRANSLATIONS_URL = "https://raw.githubusercontent.com/yairm210/Unciv/master/android/assets/jsons/translations"
LANGUAGES = ["English", "Simplified_Chinese"]


def strip_json_comments(json_str: str) -> str:
    """
    移除 JSON 中的 // 和 /* */ 注释，不影响字符串内容。
    """
    result = []
    in_string = False
    escape_next = False
    i = 0
    while i < len(json_str):
        c = json_str[i]
        if escape_next:
            escape_next = False
            result.append(c)
        elif c == '\\':
            escape_next = True
            result.append(c)
        elif c == '"':
            in_string = not in_string
            result.append(c)
        elif not in_string and json_str[i:i + 2] == '//':
            # 跳过 // 注释直到行尾
            while i < len(json_str) and json_str[i] != '\n':
                i += 1
            continue  # continue 循环，i 已经指向 \n
        elif not in_string and json_str[i:i + 2] == '/*':
            # 跳过 /* */ 注释
            while i < len(json_str) and json_str[i:i + 2] != '*/':
                i += 1
            i += 2  # 跳过 */
            continue
        else:
            result.append(c)
        i += 1
    return ''.join(result)


def load_unciv_json(file_path: Path) -> Union[list, dict]:
    """
    加载可能带有注释的 Unciv JSON 文件。
    """
    with open(file_path, encoding="utf-8-sig") as f:
        content = f.read()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass  # 忽略错误，尝试去除注释
    clean_content = strip_json_comments(content)
    return json.loads(clean_content)


def download_file(url: str, target: Path, timeout: int = DEFAULT_TIMEOUT):
    """
    下载文件，带超时和进度反馈。
    """
    if target.exists():
        print(f"ℹ️  跳过（已存在）: {target.name}")
        return
    try:
        print(f"⏳ 正在下载 {target.name}...", end='', flush=True)
        with urlopen(url, timeout=timeout) as resp, open(target, 'wb') as f:
            f.write(resp.read())
        print(" ✅")  # 下载状态后换行
    except Exception as e:
        print(f" ❌ (失败: {e})")
        print(f"⚠️  无法下载 {url}。请确保 {target} 存在或检查网络连接。", file=sys.stderr)


def load_properties(file_path: Path) -> Dict[str, str]:
    """
    从 .properties 文件加载翻译键值对。
    """
    trans = {}
    if not file_path.exists():
        print(f"⚠️  翻译文件缺失: {file_path}", file=sys.stderr)
        return trans
    print(f"🔍 Loading properties from: {file_path}")  # Debug
    with open(file_path, encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                parts = line.split("=", 1)
                if len(parts) >= 2:
                    key = parts[0].strip()
                    value = parts[1].strip().replace("\\n", "\n")
                    trans[key] = value
                    # Debug: Print the first few keys to see examples
                    if len(trans) <= 5:
                        print(f"  📌 Loaded key: '{key}' -> '{value}'")  # Debug
                else:
                    print(f"  ⚠️  Malformed line {line_num}: '{line}'")  # Debug
    print(f"  Loaded {len(trans)} keys from {file_path.name}")  # Debug
    return trans


def translate_translatable(text: str, trans: Dict[str, str], debug_context: str = "") -> str:
    """
    高效地模拟 Unciv 的 Translatable.toRawString() 行为。
    使用列表拼接代替字符串拼接，避免重复创建字符串对象。
    """
    if "[" not in text:
        return text

    result_parts = []
    last_end = 0
    i = 0
    while i < len(text):
        if text[i] == '[':
            # 找到 [ 的位置
            start = i
            # 寻找匹配的 ]
            bracket_count = 1
            j = i + 1
            while j < len(text) and bracket_count > 0:
                if text[j] == '[':
                    bracket_count += 1
                elif text[j] == ']':
                    bracket_count -= 1
                j += 1

            if bracket_count == 0:  # 找到了匹配的 ]
                # 添加 [ 之前的内容
                result_parts.append(text[last_end:start])
                # 提取 [ ] 内的键
                key = text[start + 1:j - 1]
                # 查找翻译
                replacement = trans.get(key, f"[{key}]")
                # Debug: Print every lookup
                print(f"  🔍 [{debug_context}] Looking up key: '{key}' - Found: {replacement != f'[{{key}}]'}")  # Debug
                if replacement != f"[{key}]":
                    print(f"      🔄 Translation: '{key}' -> '{replacement}'")  # Debug
                # 添加翻译后的内容
                result_parts.append(f"[{replacement}]")
                # 更新下次搜索的起始位置
                last_end = j
                i = j
            else:
                # 没找到匹配的 ]，当作普通字符处理
                i += 1
        else:
            i += 1

    # 添加最后一部分内容
    result_parts.append(text[last_end:])
    return "".join(result_parts)


def apply_translations(entry: dict, trans: Dict[str, str], debug_name: str) -> dict:
    """
    应用翻译到条目，只对特定字段（如 uniques）进行 Translatable 处理。
    这样可以避免不必要的递归和深度遍历。
    """
    new_entry = entry.copy()
    if "uniques" in new_entry:
        uniques = new_entry["uniques"]
        if isinstance(uniques, list):
            print(f"  📝 Processing uniques for {debug_name}")  # Debug
            new_entry["uniques"] = [translate_translatable(u, trans, f"{debug_name}_unique") for u in uniques]
        elif isinstance(uniques, str):
            print(f"  📝 Processing single unique string for {debug_name}")  # Debug
            new_entry["uniques"] = translate_translatable(uniques, trans, f"{debug_name}_unique")

    if "name" in new_entry and isinstance(new_entry["name"], str):
        print(f"  🏷️  Processing name for {debug_name}")  # Debug
        new_entry["name"] = translate_translatable(new_entry["name"], trans, f"{debug_name}_name")

    if "specialistSlots" in new_entry and isinstance(new_entry["specialistSlots"], dict):
        print(f"  🧑‍🔬 Processing specialistSlots for {debug_name}")  # Debug
        translated_slots = {}
        for slot_type, stat_key in new_entry["specialistSlots"].items():
            if isinstance(stat_key, str):
                translated_slots[slot_type] = translate_translatable(stat_key, trans, f"{debug_name}_slot_{slot_type}")
            else:
                translated_slots[slot_type] = stat_key  # 保持原始值（如果是数字等）
        new_entry["specialistSlots"] = translated_slots

    return new_entry


def find_image(name: str) -> Path | None:
    """
    查找指定名称的图片文件。
    """
    if not name:
        return None
    img_path = IMAGES_DIR / f"{name}.png"
    return img_path.relative_to(MOD_ROOT) if img_path.exists() else None


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    PYTHON_DIR.mkdir(exist_ok=True)

    if not JSON_DIR.exists():
        print(f"❌ 'jsons' 目录未找到", file=sys.stderr)
        sys.exit(1)

    # 下载基础翻译文件
    print("🔍 正在准备翻译文件...")
    base_trans_dir = PYTHON_DIR / "base_translations"
    base_trans_dir.mkdir(exist_ok=True)
    for lang in LANGUAGES:
        url = f"{BASE_TRANSLATIONS_URL}/{lang}.properties"
        target = base_trans_dir / f"{lang}.properties"
        download_file(url, target)

    # 生成维基
    for lang in LANGUAGES:
        print(f"\n🌍 正在构建 {lang} 维基...")
        lang_out = OUTPUT_DIR / lang
        lang_out.mkdir(parents=True, exist_ok=True)

        base_trans = load_properties(base_trans_dir / f"{lang}.properties")
        local_trans_path = JSON_DIR / "translations" / f"{lang}.properties"
        local_trans = load_properties(local_trans_path)
        merged_trans = {**base_trans, **local_trans}

        print(f"📊 Total loaded translation keys for {lang}: {len(merged_trans)}")  # Debug

        json_files = list(JSON_DIR.glob("*.json"))
        print(f"📝 发现 {len(json_files)} 个 JSON 文件待处理...")

        for idx, json_file in enumerate(json_files, 1):
            if json_file.parent.name == "translations":
                continue  # 跳过翻译文件本身

            print(
                f"  ({idx}/{len([f for f in json_files if f.parent.name != 'translations'])}) 正在处理: {json_file.name} ...",
                end='', flush=True)

            try:
                data = load_unciv_json(json_file)
                entries = data if isinstance(data, list) else [data]

                md_lines = [f"# {json_file.stem}\n"]
                for entry_idx, entry in enumerate(entries):
                    if not isinstance(entry, dict) or "name" not in entry:
                        continue

                    # 只对特定字段应用翻译
                    debug_entry_name = f"{json_file.stem}_{entry_idx}"
                    translated_entry = apply_translations(entry, merged_trans, debug_entry_name)

                    name = translated_entry["name"]
                    md_lines.append(f"## {name}\n")

                    if img_rel := find_image(entry["name"]):
                        md_lines.append(f"![{name}]({img_rel})\n")

                    # 类别
                    categories = [
                        str(v) for k, v in translated_entry.items()
                        if k.startswith("Class.") and v != "<hidden from users>"
                    ]
                    if categories:
                        md_lines.append(f"**Category**: {', '.join(categories)}\n")

                    # 基础字段
                    skip_keys = {"name", "uniques", "specialistSlots"}
                    for k, v in translated_entry.items():
                        if k in skip_keys or k.startswith("Class.") or isinstance(v, (dict, list)):
                            continue
                        md_lines.append(f"- **{k.title()}**: {v}")

                    # 专家槽位
                    if "specialistSlots" in translated_entry:
                        md_lines.append("\n**Specialist Slots**:")
                        for role, count in translated_entry["specialistSlots"].items():
                            md_lines.append(f"- {role}: {count}")

                    # 独特能力 - 已由 apply_translations 翻译！
                    if "uniques" in translated_entry and isinstance(translated_entry["uniques"], list):
                        md_lines.append("\n**Unique Abilities**:")
                        for u in translated_entry["uniques"]:
                            md_lines.append(f"- {u}")

                    md_lines.append("\n---\n")

                (lang_out / f"{json_file.stem}.md").write_text("\n".join(md_lines), encoding="utf-8")
                print(" ✅")  # 处理完成后换行并显示成功标志

            except Exception as e:
                print(f" ❌ (错误: {e})")  # 处理失败后换行并显示错误标志
                # print(f"  ❌ 处理 {json_file} 时出错: {e}", file=sys.stderr) # 原始错误详情

        print(f"✅ {lang} 维基构建完成！")

    # 创建索引页
    (OUTPUT_DIR / "index.md").write_text(
        "# CoeHarMod Wiki\n\n"
        "- [English](English/)\n"
        "- [简体中文](Simplified_Chinese/)\n"
    )
    print(f"\n🎉 全部完成！维基已生成到: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()