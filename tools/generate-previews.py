"""Generate first-page preview JPGs for each library folder.

The landing page's Library section shows a small preview of a representative
PDF per folder. This script re-renders those JPGs from the source PDFs.

Reads:  cheat-sheets/unity-cheat-sheets.pdf
        deep-dives/game-mechanic-breakdowns.pdf
        roadmaps-and-project-ideas/game-dev-roadmaps.pdf
        unity-hacks/unity-hack-list.pdf
Writes: assets/previews/<folder>.jpg   (one per folder, ~600px wide, q78 JPEG)

Dependency:
    pip install pymupdf

Run from the repo root:
    python tools/generate-previews.py
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    import fitz  # pymupdf
except ImportError:
    print("pymupdf not installed. Run: pip install pymupdf", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "previews"

# Which PDF to preview for each folder. Chosen to be representative of the folder's
# style — change the filename here if you add a better-looking cover.
REPRESENTATIVES = {
    "cheat-sheets":               "unity-cheat-sheets.pdf",
    "deep-dives":                 "game-mechanic-breakdowns.pdf",
    "roadmaps-and-project-ideas": "game-dev-roadmaps.pdf",
    "unity-hacks":                "unity-hack-list.pdf",
}

TARGET_WIDTH_PX = 600


def render_preview(pdf_path: Path, out_path: Path) -> tuple[int, int, int]:
    """Render page 1 of the PDF to a JPG. Returns (width, height, size_bytes)."""
    doc = fitz.open(pdf_path)
    try:
        page = doc[0]
        zoom = TARGET_WIDTH_PX / page.rect.width
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        pix.pil_save(str(out_path), format="JPEG", quality=78, optimize=True)
        return pix.width, pix.height, out_path.stat().st_size
    finally:
        doc.close()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    missing = []

    for folder, filename in REPRESENTATIVES.items():
        pdf_path = ROOT / folder / filename
        if not pdf_path.exists():
            missing.append(pdf_path.relative_to(ROOT))
            continue
        out_path = OUT / f"{folder}.jpg"
        w, h, size = render_preview(pdf_path, out_path)
        print(f"  {folder}.jpg  ({w}x{h}, {size // 1024} KB)")

    if missing:
        print("\n[error] missing source PDFs:", file=sys.stderr)
        for p in missing:
            print(f"  {p}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
