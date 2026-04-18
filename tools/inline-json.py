"""Inline JSON data into the HTML pages that display it.

Why: the static pages embed their data inside
    <script id="data" type="application/json">…</script>
blocks so the site works from file:// without a fetch. When the source JSON
changes (data.json, quizzes.json), those inline blocks go stale. This script
rewrites them.

Targets:
    humans-of-gaming/data.json  ->  humans-of-gaming/index.html
    practice/quizzes.json       ->  practice/index.html
                                ->  practice/quiz.html

Run from the repo root:
    python tools/inline-json.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TARGETS = [
    (
        ROOT / "humans-of-gaming" / "data.json",
        [ROOT / "humans-of-gaming" / "index.html"],
    ),
    (
        ROOT / "practice" / "quizzes.json",
        [ROOT / "practice" / "index.html", ROOT / "practice" / "quiz.html"],
    ),
]

# Match the literal data-block: <script id="data" type="application/json">…</script>
DATA_BLOCK = re.compile(
    r'(<script id="data" type="application/json">)(.*?)(</script>)',
    re.S,
)


def inline_into(json_path: Path, html_paths: list[Path]) -> int:
    """Load JSON, re-embed it in each target HTML file. Returns number of files changed."""
    if not json_path.exists():
        print(f"[error] missing source: {json_path}", file=sys.stderr)
        return -1

    data = json.loads(json_path.read_text(encoding="utf-8"))

    # Compact (no extra whitespace) and escape any "</script>" so the payload
    # can't terminate the script tag early.
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("</script>", "<\\/script>")
    wrapped = "\n" + payload + "\n"

    changed = 0
    for html_path in html_paths:
        if not html_path.exists():
            print(f"  [skip] missing target: {html_path.relative_to(ROOT)}")
            continue

        src = html_path.read_text(encoding="utf-8")
        if not DATA_BLOCK.search(src):
            print(f"  [skip] no data-block in {html_path.relative_to(ROOT)}")
            continue

        new = DATA_BLOCK.sub(
            lambda m: m.group(1) + wrapped + m.group(3),
            src,
            count=1,
        )
        if new != src:
            html_path.write_text(new, encoding="utf-8")
            print(f"  updated  {html_path.relative_to(ROOT)}")
            changed += 1
        else:
            print(f"  unchanged  {html_path.relative_to(ROOT)}")
    return changed


def main() -> int:
    total_changed = 0
    for json_path, html_paths in TARGETS:
        rel = json_path.relative_to(ROOT)
        print(f"{rel}  ({len(html_paths)} target(s))")
        result = inline_into(json_path, html_paths)
        if result < 0:
            return 1
        total_changed += result
    print(f"\nDone. {total_changed} file(s) rewritten.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
