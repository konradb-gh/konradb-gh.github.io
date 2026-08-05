#!/usr/bin/env python3
"""Generate a static annual bar chart styled to match the site's light
"trading terminal" theme, for manually-sourced yearly data (e.g. World
Gold Council central bank purchase tonnage) that isn't a yfinance price
series — see make_chart.py for that case.

Bars are always the neutral amber accent — this chart type has no
up/down direction to encode, so red/green stay unused here, consistent
with the site's rule that they're reserved for directional price moves.

Example:
    python make_bar_chart.py \\
        --title "Central Bank Net Gold Purchases" \\
        --ylabel "Tonnes" \\
        --output ../public/charts/central-bank-gold-purchases.png \\
        --bar "2015:579.6" --bar "2016:394.9" --bar "2017:378.6" \\
        --bar "2018:656.2" --bar "2019:605.4" --bar "2020:254.9" \\
        --bar "2021:450.1" --bar "2022:1080.0" --bar "2023:1050.8" \\
        --bar "2024:1092" --bar "2025:863" \\
        --avg-line 473 --avg-label "2010-2021 average"
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import matplotlib
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

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


def parse_bar(spec: str) -> tuple[str, float]:
    if ":" not in spec:
        raise ChartError(f'Bad --bar value {spec!r}; expected "LABEL:VALUE"')
    label, value = spec.rsplit(":", 1)
    try:
        return label, float(value)
    except ValueError as exc:
        raise ChartError(f"Bad numeric value in --bar {spec!r}: {exc}") from exc


def make_bar_chart(
    bars: list[tuple[str, float]],
    output_path: Path,
    title: str,
    ylabel: str = "",
    avg_line: float | None = None,
    avg_label: str = "",
) -> None:
    plt.rcParams["font.family"] = FONT_STACK
    labels = [b[0] for b in bars]
    values = [b[1] for b in bars]

    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
    fig.patch.set_facecolor(COLOR_BG)
    ax.set_facecolor(COLOR_BG)

    ax.bar(labels, values, color=COLOR_ACCENT, width=0.6, zorder=3)

    for spine_name in ("top", "right"):
        ax.spines[spine_name].set_visible(False)
    for spine_name in ("left", "bottom"):
        ax.spines[spine_name].set_color(COLOR_BORDER)
        ax.spines[spine_name].set_linewidth(1)

    ax.grid(True, axis="y", color=COLOR_BORDER, linewidth=0.6, alpha=0.6, zorder=0)
    ax.tick_params(colors=COLOR_MUTED, labelsize=9)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_color(COLOR_MUTED)

    if ylabel:
        ax.set_ylabel(ylabel, color=COLOR_MUTED, fontsize=9)

    if avg_line is not None:
        ax.axhline(avg_line, color=COLOR_MUTED, linewidth=1, linestyle=(0, (4, 3)), zorder=4)
        ax.text(
            len(bars) - 1,
            avg_line,
            f" {avg_label}" if avg_label else "",
            color=COLOR_MUTED,
            fontsize=8.5,
            va="bottom",
            ha="right",
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
    parser.add_argument("--title", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--ylabel", default="")
    parser.add_argument("--bar", action="append", default=[], metavar="LABEL:VALUE", help="Repeatable.")
    parser.add_argument("--avg-line", type=float, default=None)
    parser.add_argument("--avg-label", default="")
    args = parser.parse_args()

    try:
        bars = [parse_bar(b) for b in args.bar]
        if not bars:
            raise ChartError("At least one --bar is required")
        make_bar_chart(
            bars=bars,
            output_path=Path(args.output),
            title=args.title,
            ylabel=args.ylabel,
            avg_line=args.avg_line,
            avg_label=args.avg_label,
        )
    except ChartError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
