#!/usr/bin/env python3
"""Generate a static two-series normalized overlay chart styled to the
site's light "trading terminal" theme, using real historical data via
yfinance. Sibling to make_chart.py (single series) and
make_bar_chart.py (manually-sourced annual bars) — this one is for
comparing two different instruments over the same window, e.g. an oil
benchmark against an equity index, where the raw price levels aren't on
comparable scales.

Both series are indexed to 100 at the first common trading date so they
share one axis. The first series (--series1) is always drawn in the
site's neutral amber accent, matching the convention in make_chart.py;
the second series (--series2) uses the heading ink color so it reads as
a distinct but still muted, non-directional line. Vertical dashed
markers (--vline DATE:LABEL, repeatable) mark event dates without
implying a directional call the way the pos/neg annotations in
make_chart.py do.

Example:
    python make_overlay_chart.py \\
        --series1 CL=F --series1-label "WTI crude" \\
        --series2 ^GSPC --series2-label "S&P 500" \\
        --start 2026-02-27 --end 2026-08-06 \\
        --title "Oil vs. S&P 500, indexed to 100 at Feb 27 2026" \\
        --output ../public/charts/oil-vs-spx-2026.png \\
        --vline 2026-04-08:Ceasefire \\
        --vline 2026-05-07:"Strikes resume"
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
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

# Site theme tokens — keep in sync with src/styles/global.css :root
COLOR_BG = "#f6f3ec"
COLOR_HEADING = "#0f0e0c"
COLOR_MUTED = "#5c5648"
COLOR_BORDER = "#ddd6c4"
COLOR_ACCENT = "#8a5e19"

FONTS_DIR = Path(__file__).resolve().parent / "fonts"
for _weight in ("JetBrainsMono-Regular.ttf", "JetBrainsMono-Bold.ttf"):
    _font_path = FONTS_DIR / _weight
    if _font_path.exists():
        fm.fontManager.addfont(str(_font_path))

FONT_STACK = ["JetBrains Mono", "Menlo", "Consolas", "DejaVu Sans Mono", "monospace"]


class ChartError(RuntimeError):
    pass


def parse_vline(spec: str) -> tuple[str, str]:
    if ":" not in spec:
        raise ChartError(f'Bad --vline value {spec!r}; expected "DATE:LABEL"')
    date, label = spec.split(":", 1)
    return date, label


def fetch_close(ticker: str, start: str, end: str) -> pd.Series:
    data = yf.Ticker(ticker).history(start=start, end=end, auto_adjust=True)
    if data.empty:
        raise ChartError(f"No data returned for {ticker} between {start} and {end}")
    data.index = data.index.tz_localize(None)
    return data["Close"]


def make_overlay_chart(
    ticker1: str,
    label1: str,
    ticker2: str,
    label2: str,
    start: str,
    end: str,
    output_path: Path,
    title: str,
    vlines: list[tuple[str, str]] | None = None,
) -> None:
    s1 = fetch_close(ticker1, start, end)
    s2 = fetch_close(ticker2, start, end)

    df = pd.concat([s1, s2], axis=1).dropna()
    df.columns = [label1, label2]
    if df.empty:
        raise ChartError("No overlapping trading dates between the two series")

    indexed = df / df.iloc[0] * 100

    plt.rcParams["font.family"] = FONT_STACK

    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
    fig.patch.set_facecolor(COLOR_BG)
    ax.set_facecolor(COLOR_BG)

    ax.plot(indexed.index, indexed[label1], color=COLOR_ACCENT, linewidth=1.6, label=label1)
    ax.plot(indexed.index, indexed[label2], color=COLOR_HEADING, linewidth=1.6, label=label2)
    ax.axhline(100, color=COLOR_BORDER, linewidth=1, linestyle=(0, (2, 2)), zorder=1)

    for spine_name in ("top", "right"):
        ax.spines[spine_name].set_visible(False)
    for spine_name in ("left", "bottom"):
        ax.spines[spine_name].set_color(COLOR_BORDER)
        ax.spines[spine_name].set_linewidth(1)

    ax.grid(True, color=COLOR_BORDER, linewidth=0.6, alpha=0.6)
    ax.tick_params(colors=COLOR_MUTED, labelsize=9)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_color(COLOR_MUTED)

    ax.set_ylabel("Indexed to 100 at start", color=COLOR_MUTED, fontsize=9)

    ymin, ymax = ax.get_ylim()
    for date, vlabel in vlines or []:
        ts = pd.Timestamp(date)
        ax.axvline(ts, color=COLOR_MUTED, linewidth=1, linestyle=(0, (4, 3)), zorder=2)
        ax.text(
            ts,
            ymax,
            f" {vlabel}",
            color=COLOR_MUTED,
            fontsize=8,
            rotation=90,
            va="top",
            ha="right",
        )

    legend = ax.legend(
        loc="upper left",
        frameon=False,
        fontsize=9,
        labelcolor=COLOR_HEADING,
    )

    ax.set_title(
        title.upper(),
        color=COLOR_HEADING,
        fontsize=12,
        fontweight="bold",
        loc="left",
        pad=14,
    )

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, facecolor=COLOR_BG)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--series1", required=True, help="Yahoo Finance ticker for the first (amber) line")
    parser.add_argument("--series1-label", required=True)
    parser.add_argument("--series2", required=True, help="Yahoo Finance ticker for the second (heading-ink) line")
    parser.add_argument("--series2-label", required=True)
    parser.add_argument("--start", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="YYYY-MM-DD")
    parser.add_argument("--title", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--vline",
        action="append",
        default=[],
        metavar="DATE:LABEL",
        help="Mark a vertical event date, e.g. 2026-05-07:'Strikes resume'. Repeatable.",
    )
    args = parser.parse_args()

    try:
        vlines = [parse_vline(v) for v in args.vline]
        make_overlay_chart(
            ticker1=args.series1,
            label1=args.series1_label,
            ticker2=args.series2,
            label2=args.series2_label,
            start=args.start,
            end=args.end,
            output_path=Path(args.output),
            title=args.title,
            vlines=vlines,
        )
    except ChartError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
