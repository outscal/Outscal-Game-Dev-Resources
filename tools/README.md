# Build tools

Scripts that generate or update derived content. **Not part of the live site** — run them locally when the underlying data changes, then commit the output.

All scripts are idempotent: running them twice produces the same output as running them once.

---

## `inline-json.py`

Re-embeds `humans-of-gaming/data.json` and `practice/quizzes.json` into the HTML pages that display them. The pages load data from a `<script id="data" type="application/json">` block so they work without a fetch (and from `file://`); this script keeps those blocks in sync with the JSON on disk.

**Run when:** you edit `data.json` or `quizzes.json`.

```bash
python tools/inline-json.py
```

---

## `generate-stories.py`

Rebuilds `humans-of-gaming/stories/*.md` and `humans-of-gaming/README.md` from `data.json`. Stories are numbered by publish date (earliest first), and the HTML inside each entry becomes clean markdown.

**Run when:** entries are added, removed, or edited in `data.json`.

```bash
python tools/generate-stories.py
```

Stale files in `stories/` are deleted first, so a removed entry won't linger on disk.

---

## `generate-previews.py`

Renders page 1 of a representative PDF per library folder into `assets/previews/<folder>.jpg`. These thumbnails appear on the folder cards on the landing page.

**Run when:** you replace a representative PDF, or want to regenerate the previews for any reason.

Requires [PyMuPDF](https://pymupdf.readthedocs.io/):

```bash
pip install pymupdf
python tools/generate-previews.py
```

To change which PDF represents a folder, edit the `REPRESENTATIVES` dict at the top of the script.
