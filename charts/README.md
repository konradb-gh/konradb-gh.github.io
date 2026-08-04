# Post charts

`make_chart.py` generates a static price chart from real historical
data (via [yfinance](https://github.com/ranaroussi/yfinance)), styled
to match the site's light "trading terminal" theme. Use it when
drafting a post where a specific index or ticker is central to the
topic — the same manual workflow used for the Fed and Nasdaq posts
(research → draft → self-critique → revise → SEO metadata → save),
with chart generation as one more step before saving the post.

This is intentionally separate from `agent/generate_post.py` — no
Anthropic API key involved, nothing here is part of that automated
pipeline.

## Setup

```bash
cd charts
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

(Already set up once in this environment — re-run only if the venv is missing.)

## Usage

```bash
source .venv/bin/activate
python make_chart.py \
  --ticker ^IXIC \
  --start 2026-05-01 \
  --end 2026-08-04 \
  --title "Nasdaq Composite" \
  --output ../public/charts/nasdaq-correction-2026.png \
  --annotate "2026-07-29:neg:-10.1% correction" \
  --annotate "2026-07-30:pos:+2.8% rebound"
```

- `--ticker`: any Yahoo Finance symbol (`^IXIC`, `^GSPC`, `NVDA`, etc.)
- `--annotate DATE:pos|neg:LABEL`: marks a specific date with a
  directional marker/label — this is the *only* place red/green
  appear on the chart. The price line itself is always the neutral
  amber accent, never colored by direction.
- Output path should live under `../public/charts/` so Astro serves
  it at `/charts/<file>.png`.

## Embedding in a post

```markdown
![Nasdaq Composite, Jun–Aug 2026](/charts/nasdaq-correction-2026.png)

*Source: Yahoo Finance (via yfinance). Data as of 2026-08-04.*
```

The italic line directly under the image is styled as a caption by
`article.post p > em:only-child` in `src/styles/global.css` — always
state the data's as-of date there.

## Style tokens

Kept in sync with `src/styles/global.css` `:root`. If the site theme
changes, update `COLOR_*` at the top of `make_chart.py` to match.

| Token | Value | Use |
|---|---|---|
| `COLOR_BG` | `#f6f3ec` | figure/axes background |
| `COLOR_TEXT` / `COLOR_HEADING` | `#1c1b17` / `#0f0e0c` | body / title text |
| `COLOR_MUTED` | `#5c5648` | tick labels |
| `COLOR_BORDER` | `#ddd6c4` | spines, gridlines |
| `COLOR_ACCENT` | `#8a5e19` | the price line (neutral, not directional) |
| `COLOR_POS` / `COLOR_NEG` | `#1f7a45` / `#b3261e` | annotation markers only |

The actual JetBrains Mono TTF (Regular + Bold, v2.304) is bundled in
`fonts/` and registered directly with matplotlib's font manager at
import time, so charts match the site's webfont exactly regardless of
what's installed on the machine generating them. `fonts/OFL.txt` is
the SIL Open Font License it ships under. `FONT_STACK` still falls
back to `Menlo` → `Consolas` → matplotlib's bundled `DejaVu Sans Mono`
only if the bundled files are ever missing.

## A caveat worth knowing

yfinance pulls real data from Yahoo Finance's live servers, reflecting
whatever the actual present day is when the script runs — it has no
awareness of the fictional "current date" (2026-08-04 at the time this
was written) established by this session's web-search results for the
Fed/Nasdaq posts. A chart generated today will show real recent price
action, not the specific fictional correction described in those
posts. Flag this to whoever's reviewing before treating a generated
chart as illustrating the same narrative as a fictional-dated post.
