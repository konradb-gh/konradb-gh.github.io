#!/usr/bin/env python3
"""Generate a static price chart styled to match the site's light
"trading terminal" theme, using real historical data via yfinance.

Used when drafting a post about a specific index/ticker — run this
directly (not part of agent/generate_post.py, no API key required),
save the output into public/charts/, and embed it in the post's
markdown with a caption noting the data's as-of date, e.g.:

    ![Nasdaq Composite, Jun-Aug 2026](/charts/nasdaq-correction-2026.png)

    *Source: Yahoo Finance (via yfinance). Data as of 2026-08-04.*

Example:
    python make_chart.py --ticker ^IXIC --start 2026-05-01 --end 2026-08-04 \\
        --title "Nasdaq Composite" --output ../public/charts/nasdaq-correction-2026.png \\
        --annotate 2026-07-29:neg:"-10.1% correction" \\
        --annotate 2026-07-30:pos:"+2.8% rebound"
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import matplotlib
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf

matplotlib.use("Agg")
# Font stack below tries JetBrains Mono / Consolas first; missing-font
# lookups are expected and handled by falling through the stack, so
# don't spam stderr with a findfont warning per text element.
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

# Site theme tokens — keep in sync with src/styles/global.css :root
COLOR_BG = "#f6f3ec"
COLOR_TEXT = "#1c1b17"
COLOR_HEADING = "#0f0e0c"
COLOR_MUTED = "#5c5648"
COLOR_BORDER = "#ddd6c4"
COLOR_ACCENT = "#8a5e19"
COLOR_POS = "#1f7a45"
COLOR_NEG = "#b3261e"

# The site's webfont, bundled directly (fonts/, OFL-licensed — see
# fonts/OFL.txt) so charts match exactly regardless of what's installed
# on the machine generating them. Falls back to system monospace fonts
# only if the bundled files are ever missing.
FONTS_DIR = Path(__file__).resolve().parent / "fonts"
for _weight in ("JetBrainsMono-Regular.ttf", "JetBrainsMono-Bold.ttf"):
    _font_path = FONTS_DIR / _weight
    if _font_path.exists():
        fm.fontManager.addfont(str(_font_path))

FONT_STACK = ["JetBrains Mono", "Menlo", "Consolas", "DejaVu Sans Mono", "monospace"]


class ChartError(RuntimeError):
    pass


def parse_annotation(spec: str) -> dict:
    parts = spec.split(":", 2)
    if len(parts) != 3:
        raise ChartError(f'Bad --annotate value {spec!r}; expected "DATE:pos|neg:label"')
    date, direction, label = parts
    if direction not in ("pos", "neg"):
        raise ChartError(f"Annotation direction must be 'pos' or 'neg', got {direction!r}")
    return {"date": date, "direction": direction, "label": label}


def fetch_history(ticker: str, start: str, end: str) -> pd.DataFrame:
    data = yf.Ticker(ticker).history(start=start, end=end, auto_adjust=True)
    if data.empty:
        raise ChartError(f"No data returned for {ticker} between {start} and {end}")
    data.index = data.index.tz_localize(None)
    return data


def make_chart(
    ticker: str,
    start: str,
    end: str,
    output_path: Path,
    title: str,
    annotations: list[dict] | None = None,
    price_field: str = "Close",
) -> None:
    data = fetch_history(ticker, start, end)
    if price_field not in data.columns:
        raise ChartError(f"{price_field!r} not in columns: {list(data.columns)}")

    plt.rcParams["font.family"] = FONT_STACK

    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
    fig.patch.set_facecolor(COLOR_BG)
    ax.set_facecolor(COLOR_BG)

    ax.plot(data.index, data[price_field], color=COLOR_ACCENT, linewidth=1.6)

    for spine_name in ("top", "right"):
        ax.spines[spine_name].set_visible(False)
    for spine_name in ("left", "bottom"):
        ax.spines[spine_name].set_color(COLOR_BORDER)
        ax.spines[spine_name].set_linewidth(1)

    ax.grid(True, color=COLOR_BORDER, linewidth=0.6, alpha=0.6)
    ax.tick_params(colors=COLOR_MUTED, labelsize=9)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_color(COLOR_MUTED)

    ax.set_title(
        title.upper(),
        color=COLOR_HEADING,
        fontsize=12,
        fontweight="bold",
        loc="left",
        pad=14,
    )

    for note in annotations or []:
        ts = pd.Timestamp(note["date"])
        if ts not in data.index:
            ts = data.index[data.index.get_indexer([ts], method="nearest")[0]]
        y = data.loc[ts, price_field]
        color = COLOR_POS if note["direction"] == "pos" else COLOR_NEG
        marker = "^" if note["direction"] == "pos" else "v"
        ax.scatter([ts], [y], color=color, s=36, zorder=5, marker=marker)
        ax.annotate(
            note["label"],
            xy=(ts, y),
            xytext=(0, 12 if note["direction"] == "pos" else -16),
            textcoords="offset points",
            ha="center",
            fontsize=8.5,
            color=color,
            fontweight="bold",
        )

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, facecolor=COLOR_BG)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ticker", required=True, help="Yahoo Finance ticker, e.g. ^IXIC, NVDA")
    parser.add_argument("--start", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="YYYY-MM-DD")
    parser.add_argument("--title", required=True, help="Chart title")
    parser.add_argument("--output", required=True, help="Output PNG path")
    parser.add_argument("--price-field", default="Close", help="Column to plot (default: Close)")
    parser.add_argument(
        "--annotate",
        action="append",
        default=[],
        metavar="DATE:pos|neg:LABEL",
        help="Mark a specific date, e.g. 2026-07-29:neg:'-10.1%% correction'. Repeatable.",
    )
    args = parser.parse_args()

    try:
        annotations = [parse_annotation(a) for a in args.annotate]
        make_chart(
            ticker=args.ticker,
            start=args.start,
            end=args.end,
            output_path=Path(args.output),
            title=args.title,
            annotations=annotations,
            price_field=args.price_field,
        )
    except ChartError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
