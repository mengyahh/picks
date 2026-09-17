"""Optional: batch-process /inbox images via the Claude API (vision) to draft
content/items/*.md files automatically.

This is an ADVANCED / OPTIONAL alternative to the recommended workflow of
just asking Claude Code to look at the /inbox folder in a normal session
(see README.md). Use this script if you want a fully offline/scriptable
pipeline, e.g. for batch-importing many images at once.

Requires:
  - Python 3.9+  (no third-party packages; uses urllib + base64 from stdlib)
  - an Anthropic API key in the ANTHROPIC_API_KEY environment variable

Usage:
  set ANTHROPIC_API_KEY=sk-ant-...      (PowerShell: $env:ANTHROPIC_API_KEY="sk-ant-...")
  python scripts/analyze_inbox.py

For every image in /inbox, this writes a draft content/items/<id>.md,
copies the image into assets/images/, and moves the source image into
/inbox/processed/. Review every draft before committing — check the
suggested type/category/tags and fill in `source` if you know it.
"""
import base64
import datetime
import json
import mimetypes
import os
import re
import shutil
import sys
import urllib.request

ROOT = os.path.join(os.path.dirname(__file__), "..")
INBOX_DIR = os.path.join(ROOT, "inbox")
PROCESSED_DIR = os.path.join(INBOX_DIR, "processed")
ITEMS_DIR = os.path.join(ROOT, "content", "items")
IMAGES_DIR = os.path.join(ROOT, "assets", "images")

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-5"

TYPES = ["concept", "case", "quote", "visual", "note"]
CATEGORIES = [
    "生活哲學與自我成長",
    "商業模式與服務創新",
    "地方創生與活動企劃",
    "空間與建築設計",
    "飲食與料理",
    "手作工藝",
]

PROMPT = f"""你正在幫忙整理一個個人靈感知識庫。請分析這張截圖/照片，並以 JSON 回覆（不要有其他文字），格式如下：

{{
  "has_text": true/false,
  "transcript": "若圖片有清楚的文字內容，逐字轉錄全文；若幾乎無文字（如純照片），留空字串",
  "description": "若圖片無文字或文字很少，用 2-4 句話描述畫面內容、風格、值得記錄的重點；若已有 transcript 則可留空",
  "title": "簡短標題（15字以內）",
  "type": "從這些選項選一個: {TYPES}",
  "category": "從這些選項選一個: {CATEGORIES}",
  "tags": ["3-6個細分標籤"],
  "summary": "一句話摘要（40字以內）"
}}

分類原則：
- type=note 是「收藏他人文章/貼文」，quote 是「台詞/金句」，case 是「真實商業模式/案例」，visual 是「以圖像為主、文字很少的視覺參考」，concept 是「抽象概念/理論」。
- category 六選一，若真的完全不屬於任何一類才另外標註為「未分類」。
"""


def call_claude(image_path):
    with open(image_path, "rb") as f:
        img_bytes = f.read()
    media_type = mimetypes.guess_type(image_path)[0] or "image/jpeg"
    b64 = base64.b64encode(img_bytes).decode("ascii")

    body = json.dumps({
        "model": MODEL,
        "max_tokens": 1500,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}},
                {"type": "text", "text": PROMPT},
            ],
        }],
    }).encode("utf-8")

    req = urllib.request.Request(API_URL, data=body, method="POST", headers={
        "content-type": "application/json",
        "x-api-key": os.environ["ANTHROPIC_API_KEY"],
        "anthropic-version": "2023-06-01",
    })
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
    text = result["content"][0]["text"]
    match = re.search(r"\{.*\}", text, re.S)
    return json.loads(match.group(0))


def next_id(date_str):
    n = 1
    while True:
        candidate = f"{date_str}-{n:03d}"
        if not os.path.exists(os.path.join(ITEMS_DIR, candidate + ".md")):
            return candidate
        n += 1


def yaml_list(values):
    return "[" + ", ".join(values) + "]"


def write_item(analysis, image_ext, src_image_path):
    date_str = datetime.date.today().isoformat()
    item_id = next_id(date_str)
    image_rel = f"images/{item_id}{image_ext}"

    shutil.copy2(src_image_path, os.path.join(IMAGES_DIR, item_id + image_ext))

    body = analysis.get("transcript") or ""
    if analysis.get("description"):
        body = (body + "\n\n" if body else "") + analysis["description"]
    body += "\n\n（AI 草稿，請人工檢查分類與內容是否貼切）"

    frontmatter = (
        "---\n"
        f"id: {item_id}\n"
        f"title: {analysis.get('title', '未命名')}\n"
        f"type: {analysis.get('type', 'note')}\n"
        f"category: {analysis.get('category', '')}\n"
        f"tags: {yaml_list(analysis.get('tags', []))}\n"
        "source: \n"
        f"image: {image_rel}\n"
        f"summary: {analysis.get('summary', '')}\n"
        "---\n"
    )

    out_path = os.path.join(ITEMS_DIR, item_id + ".md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(frontmatter + body.strip() + "\n")
    return out_path


def main():
    if "ANTHROPIC_API_KEY" not in os.environ:
        print("Set ANTHROPIC_API_KEY first.")
        sys.exit(1)

    os.makedirs(PROCESSED_DIR, exist_ok=True)
    files = [
        f for f in sorted(os.listdir(INBOX_DIR))
        if os.path.isfile(os.path.join(INBOX_DIR, f))
        and f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
    ]
    if not files:
        print("Inbox is empty.")
        return

    for name in files:
        src = os.path.join(INBOX_DIR, name)
        print(f"Analyzing {name} ...")
        try:
            analysis = call_claude(src)
        except Exception as e:
            print(f"  failed: {e}")
            continue
        ext = os.path.splitext(name)[1].lower()
        out_path = write_item(analysis, ext, src)
        shutil.move(src, os.path.join(PROCESSED_DIR, name))
        print(f"  -> {out_path}")

    print("Done. Run `python scripts/build_index.py` next, then review the drafts.")


if __name__ == "__main__":
    main()
