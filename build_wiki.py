#!/usr/bin/env python3
"""
Mod Wiki Builder for CoeHarMod
- Fully supports Unciv-style JSON (with // and /* */ comments)
- Correctly translates complex 'uniques' like:
    "[+1 Culture] from every [Improvement.Library] <after discovering [Tech.Writing]>"
- Outputs to 'docs/' for GitHub Pages (served from main branch)
- Stores temp files in 'python/' directory
- No pollution of mod root directory
"""
import json
import re
import sys
from pathlib import Path
from urllib.request import urlopen
from typing import Dict, Any, List, Union

# ==================== Configuration ====================
MOD_ROOT = Path(__file__).parent.resolve()
PYTHON_DIR = MOD_ROOT / "python"  # Temporary files go here
JSON_DIR = MOD_ROOT / "jsons"
IMAGES_DIR = MOD_ROOT / "Images"
OUTPUT_DIR = MOD_ROOT / "docs"  # GitHub Pages standard

BASE_TRANSLATIONS_URL = "https://raw.githubusercontent.com/yairm210/Unciv/master/android/assets/jsons/translations"
LANGUAGES = ["English", "Simplified_Chinese"]


# ==================== Utility Functions ====================

def strip_json_comments(json_str: str) -> str:
    """Safely remove // and /* */ comments without breaking string content."""
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
    """Load JSON that may contain comments or be pure JSON."""
    with open(file_path, encoding="utf-8-sig") as f:
        content = f.read()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    clean_content = strip_json_comments(content)
    try:
        return json.loads(clean_content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {file_path}: {e}")


def download_file(url: str, target: Path):
    try:
        with urlopen(url) as response, open(target, 'wb') as f:
            f.write(response.read())
        print(f"✅ Downloaded: {target.name}")
    except Exception as e:
        print(f"⚠️ Failed to download {url}: {e}", file=sys.stderr)


def load_properties(file_path: Path) -> Dict[str, str]:
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


def translate_unique(unique_str: str, trans: Dict[str, str]) -> str:
    """
    Accurately translate Unciv 'uniques' by parsing structure,
    not treating as plain text.
    """

    # Handle <condition> blocks
    def handle_condition(match):
        inner = match.group(1).strip()
        if inner.startswith("after discovering [") and inner.endswith("]"):
            key = inner[18:-1]
            name = trans.get(key, key)
            prefix = trans.get("after discovering", "after discovering")
            return f"<{prefix} {name}>"
        elif inner.startswith("before discovering [") and inner.endswith("]"):
            key = inner[19:-1]
            name = trans.get(key, key)
            prefix = trans.get("before discovering", "before discovering")
            return f"<{prefix} {name}>"
        else:
            return f"<{trans.get(inner, inner)}>"

    # Handle [...] placeholders
    def handle_bracket(match):
        content = match.group(1)
        # Match [+N Stat] pattern
        stat_match = re.match(r'^([+-]\d+(?:\.\d+)?)\s+(.+)$', content)
        if stat_match:
            amount, stat_key = stat_match.groups()
            stat_name = trans.get(stat_key, stat_key)
            return f"{amount} {stat_name}"
        # Otherwise treat as translation key
        return trans.get(content, content)

    # Apply transformations
    result = re.sub(r'<([^<>]+)>', handle_condition, unique_str)
    result = re.sub(r'\[([^\[\]]+)]', handle_bracket, result)
    return result


def translate_value(value: Any, trans: Dict[str, str]) -> Any:
    """General-purpose translator for non-uniques fields."""
    if isinstance(value, str):
        # Simple placeholder replacement (for descriptions etc.)
        def repl(m):
            key = m.group(1)
            return trans.get(key, f"[{key}]")

        return re.sub(r'\[([^\[\]]+)]', repl, value)
    elif isinstance(value, dict):
        return {k: translate_value(v, trans) for k, v in value.items()}
    elif isinstance(value, list):
        return [translate_value(item, trans) for item in value]
    return value


def find_image(name: str) -> Path | None:
    if not name:
        return None
    image_path = IMAGES_DIR / f"{name}.png"
    if image_path.exists():
        return image_path.relative_to(MOD_ROOT)
    return None


# ==================== Main Process ====================

def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    PYTHON_DIR.mkdir(exist_ok=True)

    if not JSON_DIR.exists():
        print(f"❌ Error: 'jsons' directory not found at {JSON_DIR}", file=sys.stderr)
        sys.exit(1)

    # Download base translations into python/base_translations/
    base_trans_dir = PYTHON_DIR / "base_translations"
    base_trans_dir.mkdir(exist_ok=True)
    for lang in LANGUAGES:
        url = f"{BASE_TRANSLATIONS_URL}/{lang}.properties"
        target = base_trans_dir / f"{lang}.properties"
        if not target.exists():
            download_file(url, target)

    # Generate wiki for each language
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
                entries = data if isinstance(data, list) else [data]

                md_lines = [f"# {json_file.stem}\n"]
                for entry in entries:
                    if not isinstance(entry, dict) or "name" not in entry:
                        continue

                    # Translate basic fields (but NOT uniques)
                    translated_entry = {}
                    for k, v in entry.items():
                        if k == "uniques":
                            continue  # Handle separately
                        translated_entry[k] = translate_value(v, merged_trans)

                    name = translated_entry["name"]
                    md_lines.append(f"## {name}\n")

                    if img_rel := find_image(entry.get("name")):
                        md_lines.append(f"![{name}]({img_rel})\n")

                    # Categories (Class.*)
                    categories = []
                    for k, v in translated_entry.items():
                        if k.startswith("Class.") and v != "<hidden from users>":
                            categories.append(str(v))
                    if categories:
                        md_lines.append(f"**Category**: {', '.join(categories)}\n")

                    # Basic fields
                    skip_keys = {"name", "uniques", "specialistSlots"}
                    for k, v in translated_entry.items():
                        if k in skip_keys or k.startswith("Class."):
                            continue
                        if isinstance(v, (dict, list)):
                            continue
                        md_lines.append(f"- **{k.title()}**: {v}")

                    # Specialist slots
                    if "specialistSlots" in entry:
                        translated_slots = translate_value(entry["specialistSlots"], merged_trans)
                        md_lines.append("\n**Specialist Slots**:")
                        for role, count in translated_slots.items():
                            md_lines.append(f"- {role}: {count}")

                    # UNIQUES — handled with special logic!
                    if "uniques" in entry and isinstance(entry["uniques"], list):
                        md_lines.append("\n**Unique Abilities**:")
                        for u in entry["uniques"]:
                            if isinstance(u, str):
                                translated_u = translate_unique(u, merged_trans)
                                md_lines.append(f"- {translated_u}")
                            else:
                                md_lines.append(f"- {u}")  # fallback

                    md_lines.append("\n---\n")

                output_file = lang_output / f"{json_file.stem}.md"
                output_file.write_text("\n".join(md_lines), encoding="utf-8")

            except Exception as e:
                print(f"  ❌ Error processing {json_file}: {e}", file=sys.stderr)

    # Generate index
    (OUTPUT_DIR / "index.md").write_text(
        "# CoeHarMod Wiki\n\n"
        "- [English](English/)\n"
        "- [简体中文](Simplified_Chinese/)\n"
    )
    print(f"\n🎉 Wiki generated successfully in: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()