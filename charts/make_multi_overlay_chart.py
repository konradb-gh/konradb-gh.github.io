#!/usr/bin/env python3
"""Generate a static multi-series normalized overlay chart styled to the
site's light "trading terminal" theme, using real historical data via
yfinance. Sibling to make_overlay_chart.py (fixed at exactly two series,
one amber, one heading-ink) — this one supports one "primary" series
(e.g. a commodity) plotted in the amber accent against any number of
"compare" series (e.g. several equity indices), all indexed to 100 at
the first common trading date and sharing one axis.

To keep the site's color rule intact (amber is reserved for a primary
price/value line; red/green are reserved for directional annotations,
never used here), every compare series is drawn in the same
heading-ink color and distinguished by line style instead of hue:
solid, dashed, dotted, dash-dot, in that order.

Example:
    python make_multi_overlay_chart.py \\
        --primary CL=F --primary-label "WTI crude" \\
        --compare ^DJI:"Dow Jones" --compare ^NDX:"Nasdaq 100" \\
        --compare ^IXIC:"Nasdaq Composite" \\
        --start 2026-02-27 --end 2026-08-06 \\
        --title "Oil vs. three equity indices since the Feb 28 strikes" \\
        --output ../public/charts/oil-vs-indices-2026.png \\
        --vline 2026-04-08:Ceasefire --vline 2026-05-07:"Strikes resume"
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
LINESTYLES = ["-", "--", ":", "-."]


class ChartError(RuntimeError):
    pass


def parse_compare(spec: str) -> tuple[str, str]:
    if ":" not in spec:
        raise ChartError(f'Bad --compare value {spec!r}; expected "TICKER:LABEL"')
    ticker, label = spec.split(":", 1)
    return ticker, label


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


def make_multi_overlay_chart(
    primary_ticker: str,
    primary_label: str,
    compares: list[tuple[str, str]],
    start: str,
    end: str,
    output_path: Path,
    title: str,
    vlines: list[tuple[str, str]] | None = None,
) -> None:
    series = {primary_label: fetch_close(primary_ticker, start, end)}
    for ticker, label in compares:
        series[label] = fetch_close(ticker, start, end)

    df = pd.concat(series.values(), axis=1)
    df.columns = list(series.keys())
    df = df.dropna()
    if df.empty:
        raise ChartError("No overlapping trading dates across all series")

    indexed = df / df.iloc[0] * 100

    plt.rcParams["font.family"] = FONT_STACK

    fig, ax = plt.subplots(figsize=(8.5, 5), dpi=150)
    fig.patch.set_facecolor(COLOR_BG)
    ax.set_facecolor(COLOR_BG)

    ax.plot(indexed.index, indexed[primary_label], color=COLOR_ACCENT, linewidth=1.8, label=primary_label, zorder=5)
    for i, (_, label) in enumerate(compares):
        ax.plot(
            indexed.index,
            indexed[label],
            color=COLOR_HEADING,
            linewidth=1.3,
            linestyle=LINESTYLES[i % len(LINESTYLES)],
            label=label,
            zorder=4,
        )
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

    ax.legend(loc="upper left", frameon=False, fontsize=8.5, labelcolor=COLOR_HEADING)

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
    parser.add_argument("--primary", required=True, help="Yahoo Finance ticker for the amber primary line")
    parser.add_argument("--primary-label", required=True)
    parser.add_argument(
        "--compare",
        action="append",
        default=[],
        metavar="TICKER:LABEL",
        help="A comparison series, drawn in heading-ink with a distinct line style. Repeatable.",
    )
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
        compares = [parse_compare(c) for c in args.compare]
        if not compares:
            raise ChartError("At least one --compare is required")
        vlines = [parse_vline(v) for v in args.vline]
        make_multi_overlay_chart(
            primary_ticker=args.primary,
            primary_label=args.primary_label,
            compares=compares,
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
