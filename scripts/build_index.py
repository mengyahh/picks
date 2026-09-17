"""Read all content/items/*.md frontmatter and write data/index.json.

Pure stdlib, no dependencies. Run after adding/editing/removing any item:

    python scripts/build_index.py
"""
import json
import os
import re

ROOT = os.path.join(os.path.dirname(__file__), "..")
ITEMS_DIR = os.path.join(ROOT, "content", "items")
OUT_PATH = os.path.join(ROOT, "data", "index.json")


def parse_scalar(value):
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [v.strip().strip('"').strip("'") for v in inner.split(",")]
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def parse_frontmatter(text):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
    if not m:
        raise ValueError("missing frontmatter")
    fm_text, body = m.group(1), m.group(2)
    data = {}
    for line in fm_text.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        key, _, value = line.partition(":")
        # strip inline comment starting with " #" (not inside brackets)
        value = value.strip()
        if "#" in value and not value.startswith("["):
            hash_idx = value.find(" #")
            if hash_idx != -1:
                value = value[:hash_idx].strip()
        data[key.strip()] = parse_scalar(value)
    return data, body.strip()


def main():
    items = []
    for name in sorted(os.listdir(ITEMS_DIR)):
        if not name.endswith(".md"):
            continue
        path = os.path.join(ITEMS_DIR, name)
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        fm, body = parse_frontmatter(text)
        fm["file"] = f"content/items/{name}"
        fm["excerpt"] = (body[:80] + "…") if len(body) > 80 else body
        items.append(fm)

    items.sort(key=lambda x: x.get("id", ""), reverse=True)

    types = sorted({i.get("type", "") for i in items if i.get("type")})
    categories = sorted({i.get("category", "") for i in items if i.get("category")})
    tags = sorted({t for i in items for t in (i.get("tags") or [])})

    out = {
        "items": items,
        "types": types,
        "categories": categories,
        "tags": tags,
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"Wrote {OUT_PATH} with {len(items)} items.")


if __name__ == "__main__":
    main()
