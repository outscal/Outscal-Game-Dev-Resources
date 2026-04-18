"""Regenerate the Humans of Gaming story markdown files from data.json.

Reads:  humans-of-gaming/data.json     (canonical data)
Writes: humans-of-gaming/stories/NN-slug.md   (one per entry, numbered by date)
        humans-of-gaming/README.md            (index table, refreshed)

Order: ascending by createdAt; ties broken by the entry's original JSON index
for stable, reproducible numbering.

Run from the repo root:
    python tools/generate-stories.py
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "humans-of-gaming" / "data.json"
STORIES_DIR = ROOT / "humans-of-gaming" / "stories"
README = ROOT / "humans-of-gaming" / "README.md"


# --- HTML -> Markdown (for the tag set actually in the data: <p>, <br>, <strong>, <a>) ---

ATTR_RX = re.compile(r'''(\w+)\s*=\s*(?:"([^"]*)"|'([^']*)'|(\S+))''')


def attrs_of(s: str) -> dict[str, str]:
    return {
        m.group(1).lower(): (m.group(2) or m.group(3) or m.group(4) or "")
        for m in ATTR_RX.finditer(s)
    }


def html_to_md(html: str) -> str:
    if not html:
        return ""

    s = html.replace("&nbsp;", " ").replace("&amp;", "&")
    s = re.sub(r"<strong>(.*?)</strong>", r"**\1**", s, flags=re.S | re.I)

    def link_sub(m: re.Match) -> str:
        href = attrs_of(m.group(1)).get("href", "").strip()
        text = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        return f"[{text}]({href})" if href else text

    s = re.sub(r"<a\b([^>]*)>(.*?)</a>", link_sub, s, flags=re.S | re.I)

    # Treat both <br> and </p> as paragraph boundaries — this matches the
    # authoring style in the source data, where single <br> is used as a hard
    # sentence break.
    s = re.sub(r"<br\s*/?>", "\n\n", s, flags=re.I)
    s = re.sub(r"</p\s*>", "\n\n", s, flags=re.I)
    s = re.sub(r"<p\b[^>]*>", "", s, flags=re.I)

    # Strip any stray tags we didn't handle.
    s = re.sub(r"<[^>]+>", "", s)

    # Normalise whitespace: collapse runs of blank lines, trim line interiors.
    lines = [re.sub(r"\s+", " ", line).strip() for line in s.splitlines()]
    out, blank = [], 0
    for line in lines:
        if line:
            out.append(line)
            blank = 0
        else:
            blank += 1
            if blank == 1:
                out.append("")
    return "\n".join(out).strip() + "\n"


# --- YAML frontmatter (always-quoted strings, no deps) ---

def yaml_str(v: str) -> str:
    return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'


def frontmatter(fields: dict[str, str]) -> str:
    lines = ["---"]
    for k, v in fields.items():
        lines.append(f"{k}: {yaml_str(v)}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def clean_slug(s: str) -> str:
    # The source has stray leading/trailing dashes where a name had whitespace;
    # collapse consecutive dashes too.
    return re.sub(r"-+", "-", s.strip()).strip("-")


# --- Story + README generation ---

def build_story(num: int, entry: dict) -> tuple[str, str]:
    name = entry["candidate_name"].strip()
    slug = clean_slug(entry["user_name"])
    designation = (entry.get("candidate_designation") or "").strip()
    company = (entry.get("candidate_company") or "").strip()

    iso = entry["createdAt"]["$date"][:10]  # YYYY-MM-DD
    y, m, d = iso.split("-")
    published = f"{d}-{m}-{y}"

    fm = frontmatter({
        "name": name,
        "designation": designation,
        "company": company,
        "published": published,
    })

    summary_md = html_to_md(entry.get("summary", "")).strip()
    body_md = html_to_md(entry.get("full_description", "")).strip()

    summary_block = "\n".join(
        f"> {line}" if line else ">" for line in summary_md.splitlines()
    )

    body_parts = [
        "---",
        "",
        f"# {name}",
        "",
        f"**{designation} · {company}**",
        "",
        summary_block,
        "",
        "---",
        "",
        body_md,
    ]
    filename = f"{num:02d}-{slug}.md"
    content = fm + "\n" + "\n".join(body_parts).rstrip() + "\n"
    return filename, content


def build_readme(ordered: list[tuple[int, dict]]) -> str:
    header = (
        "# Humans of Gaming\n"
        "\n"
        "Stories from the people building games — founders, engineers, "
        "designers, producers. Forty-four conversations about how games "
        "actually get made: the winding paths, the first jobs, the bets "
        "that paid off.\n"
        "\n"
        f"**{len(ordered)} stories**, collected April–June 2023.\n"
        "\n"
        "## Index\n"
        "\n"
        "| № | Name | Role | Company |\n"
        "|---|------|------|---------|\n"
    )
    rows = []
    for num, entry in ordered:
        name = entry["candidate_name"].strip()
        slug = clean_slug(entry["user_name"])
        role = (entry.get("candidate_designation") or "").strip()
        company = (entry.get("candidate_company") or "").strip()
        link = f"stories/{num:02d}-{slug}.md"
        safe = lambda s: s.replace("|", "\\|")
        rows.append(
            f"| {num:02d} | [{safe(name)}]({link}) | {safe(role)} | {safe(company)} |"
        )
    footer = (
        "\n"
        "## Source\n"
        "\n"
        "Raw data for every story is in [`data.json`](data.json). "
        "Each markdown file in `stories/` is the same content formatted for reading.\n"
    )
    return header + "\n".join(rows) + "\n" + footer


def main() -> int:
    if not DATA.exists():
        print(f"[error] missing {DATA}", file=sys.stderr)
        return 1

    raw = json.loads(DATA.read_text(encoding="utf-8"))

    # Sort by (published date, original JSON index) for stable within-day order.
    indexed = list(enumerate(raw))
    indexed.sort(key=lambda t: (t[1]["createdAt"]["$date"], t[0]))
    ordered = [(n + 1, e) for n, (_, e) in enumerate(indexed)]

    # Nuke any stale files so a removed entry doesn't linger on disk.
    if STORIES_DIR.exists():
        shutil.rmtree(STORIES_DIR)
    STORIES_DIR.mkdir(parents=True)

    for num, entry in ordered:
        filename, content = build_story(num, entry)
        (STORIES_DIR / filename).write_text(content, encoding="utf-8")

    README.write_text(build_readme(ordered), encoding="utf-8")

    print(f"Wrote {len(ordered)} stories + README to {DATA.parent.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
