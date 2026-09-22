from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
required = [
    DOCS / "index.html",
    DOCS / "cathay.html",
    DOCS / "bretonnia.html",
    DOCS / "search-index.json",
    DOCS / "static" / "style.css",
    DOCS / "static" / "app.js",
    DOCS / "_headers",
]
missing = [str(p.relative_to(ROOT)) for p in required if not p.exists()]
if missing:
    print("FAIL: missing files:")
    for item in missing:
        print(" -", item)
    sys.exit(1)

index = json.loads((DOCS / "search-index.json").read_text(encoding="utf-8"))
if not isinstance(index, list) or not index:
    print("FAIL: search-index.json is empty or invalid")
    sys.exit(1)

missing_articles = []
for item in index:
    target = DOCS / item["url"]
    if not target.exists():
        missing_articles.append(item["url"])
if missing_articles:
    print("FAIL: missing article pages:")
    for item in missing_articles:
        print(" -", item)
    sys.exit(1)

print(f"OK: {len(index)} articles, core pages and Cloudflare headers verified.")
