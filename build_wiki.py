#!/usr/bin/env python3
"""
Mod Wiki Builder for CoeHarMod - FINAL VERSION
- Exactly replicates Unciv's Translatable.toRawString() behavior
- Supports compound keys like "+1 Culture" if provided in translations
- No regex, no recursion, no crash
- Supports JSON with // and /* */ comments
- Outputs to docs/ for GitHub Pages
- Uses python/ for temp files
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

BASE_TRANSLATIONS_URL = "https://raw.githubusercontent.com/yairm210/Unciv/master/android/assets/jsons/translations"
LANGUAGES = ["English", "Simplified_Chinese"]


def strip_json_comments(json_str: str) -> str:
    """Remove // and /* */ comments without breaking strings."""
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
            while i < len(json_str) and json_str[i] != '\n':
                i += 1
            continue
        elif not in_string and json_str[i:i + 2] == '/*':
            while i < len(json_str) and json_str[i:i + 2] != '*/':
                i += 1
            i += 2
            continue
        else:
            result.append(c)
        i += 1
    return ''.join(result)


def load_unciv_json(file_path: Path) -> Union[list, dict]:
    with open(file_path, encoding="utf-8-sig") as f:
        content = f.read()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    clean_content = strip_json_comments(content)
    return json.loads(clean_content)


def download_file(url: str, target: Path):
    if target.exists():
        return
    try:
        with urlopen(url) as resp, open(target, 'wb') as f:
            f.write(resp.read())
        print(f"✅ Downloaded: {target.name}")
    except Exception as e:
        print(f"⚠️ Failed to download {url}: {e}", file=sys.stderr)


def load_properties(file_path: Path) -> Dict[str, str]:
    trans = {}
    if not file_path.exists():
        return trans
    with open(file_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                trans[key.strip()] = value.strip().replace("\\n", "\n")
    return trans


def translate_translatable(text: str, trans: Dict[str, str]) -> str:
    """
    EXACT REPLICATION of Unciv's Translatable.toRawString()
    Handles compound keys like "+1 Culture" if they exist in trans.
    """
    result = text
    # Only replace [key] patterns, left-to-right, one at a time
    while True:
        start = result.find("[")
        if start == -1:
            break
        end = result.find("]", start)
        if end == -1:
            break
        key = result[start + 1:end]
        # The key can be anything, including "+1 Culture" or "{Military} {Land}"
        replacement = trans.get(key, f"[{key}]")
        # Replace ONLY the first occurrence
        result = result[:start] + f"[{replacement}]" + result[end + 1:]
    return result


def translate_value(value: Any, trans: Dict[str, str]) -> Any:
    if isinstance(value, str):
        return translate_translatable(value, trans)
    elif isinstance(value, dict):
        return {k: translate_value(v, trans) for k, v in value.items()}
    elif isinstance(value, list):
        return [translate_value(item, trans) for item in value]
    return value


def find_image(name: str) -> Path | None:
    if not name:
        return None
    img_path = IMAGES_DIR / f"{name}.png"
    return img_path.relative_to(MOD_ROOT) if img_path.exists() else None


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    PYTHON_DIR.mkdir(exist_ok=True)

    if not JSON_DIR.exists():
        print(f"❌ 'jsons' directory not found", file=sys.stderr)
        sys.exit(1)

    # Download base translations
    base_trans_dir = PYTHON_DIR / "base_translations"
    base_trans_dir.mkdir(exist_ok=True)
    for lang in LANGUAGES:
        url = f"{BASE_TRANSLATIONS_URL}/{lang}.properties"
        target = base_trans_dir / f"{lang}.properties"
        download_file(url, target)

    # Generate wiki
    for lang in LANGUAGES:
        print(f"\n🌍 Building {lang} wiki...")
        lang_out = OUTPUT_DIR / lang
        lang_out.mkdir(parents=True, exist_ok=True)

        base_trans = load_properties(base_trans_dir / f"{lang}.properties")
        local_trans_path = JSON_DIR / "translations" / f"{lang}.properties"
        local_trans = load_properties(local_trans_path)
        merged_trans = {**base_trans, **local_trans}

        for json_file in JSON_DIR.glob("*.json"):
            if json_file.parent.name == "translations":
                continue

            try:
                data = load_unciv_json(json_file)
                entries = data if isinstance(data, list) else [data]

                md_lines = [f"# {json_file.stem}\n"]
                for entry in entries:
                    if not isinstance(entry, dict) or "name" not in entry:
                        continue

                    # Translate all fields using Translatable logic
                    translated_entry = translate_value(entry, merged_trans)

                    name = translated_entry["name"]
                    md_lines.append(f"## {name}\n")

                    if img_rel := find_image(entry["name"]):
                        md_lines.append(f"![{name}]({img_rel})\n")

                    # Categories
                    categories = [
                        str(v) for k, v in translated_entry.items()
                        if k.startswith("Class.") and v != "<hidden from users>"
                    ]
                    if categories:
                        md_lines.append(f"**Category**: {', '.join(categories)}\n")

                    # Basic fields
                    skip_keys = {"name", "uniques", "specialistSlots"}
                    for k, v in translated_entry.items():
                        if k in skip_keys or k.startswith("Class.") or isinstance(v, (dict, list)):
                            continue
                        md_lines.append(f"- **{k.title()}**: {v}")

                    # Specialist slots
                    if "specialistSlots" in translated_entry:
                        md_lines.append("\n**Specialist Slots**:")
                        for role, count in translated_entry["specialistSlots"].items():
                            md_lines.append(f"- {role}: {count}")

                    # Uniques - already translated by translate_value!
                    if "uniques" in translated_entry and isinstance(translated_entry["uniques"], list):
                        md_lines.append("\n**Unique Abilities**:")
                        for u in translated_entry["uniques"]:
                            md_lines.append(f"- {u}")

                    md_lines.append("\n---\n")

                (lang_out / f"{json_file.stem}.md").write_text("\n".join(md_lines), encoding="utf-8")

            except Exception as e:
                print(f"  ❌ Error in {json_file}: {e}", file=sys.stderr)

    # Index
    (OUTPUT_DIR / "index.md").write_text(
        "# CoeHarMod Wiki\n\n"
        "- [English](English/)\n"
        "- [简体中文](Simplified_Chinese/)\n"
    )
    print(f"\n🎉 Done! Wiki is in: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()