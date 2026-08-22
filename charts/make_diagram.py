#!/usr/bin/env python3
"""Generate schematic, illustrative/conceptual diagrams styled to match
the site's light "trading terminal" theme. Distinct from every other
script in this directory, which all plot real market data pulled via
yfinance — this one draws hand-specified shapes (timelines, flow
diagrams) for explaining a mechanism, not for reporting a price.

Two subcommands, sharing the same visual language (warm paper
background, amber accent, near-black ink, JetBrains Mono, sharp
corners, thin 1px borders):

  timeline  A horizontal sequence of dated events — e.g. a bond's
            cash flows from purchase to maturity. Each event is one of
            three kinds (outflow / coupon / maturity), styled
            distinctly so a reader can tell a repeating payment apart
            from the one-off events at the ends.

  flow      A two-party box-and-arrow diagram — e.g. who pays what in
            an interest rate swap — with an optional dashed
            "reference only" box for a notional amount that never
            actually changes hands.

Examples:
    python make_diagram.py timeline \\
        --title "Bond cash flows: $1,000 face value, $40 annual coupon" \\
        --output ../public/charts/bond-timeline-2026.png \\
        --xlabel "Year" \\
        --event "0:Pay $1,000:outflow" \\
        --event "1:$40 coupon:coupon" \\
        --event "2:$40 coupon:coupon" \\
        --event "3:$40 coupon:coupon" \\
        --event "4:$40 coupon:coupon" \\
        --event "5:$40 coupon +\\n$1,000 face value:maturity"

    python make_diagram.py flow \\
        --title "How an interest rate swap moves money" \\
        --output ../public/charts/interest-rate-swap-diagram-2026.png \\
        --left-label "The Company" \\
        --right-label "The Bank" \\
        --top-arrow-label "Pays a fixed rate" \\
        --bottom-arrow-label "Pays a floating rate" \\
        --notional-label "Notional amount: $300,000\\nreference only -- never actually exchanged"
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import matplotlib
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

matplotlib.use("Agg")
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

# Site theme tokens — keep in sync with src/styles/global.css :root
COLOR_BG = "#f6f3ec"
COLOR_HEADING = "#0f0e0c"
COLOR_TEXT = "#1c1b17"
COLOR_MUTED = "#5c5648"
COLOR_BORDER = "#ddd6c4"
COLOR_ACCENT = "#8a5e19"

FONTS_DIR = Path(__file__).resolve().parent / "fonts"
for _weight in ("JetBrainsMono-Regular.ttf", "JetBrainsMono-Bold.ttf"):
    _font_path = FONTS_DIR / _weight
    if _font_path.exists():
        fm.fontManager.addfont(str(_font_path))

FONT_STACK = ["JetBrains Mono", "Menlo", "Consolas", "DejaVu Sans Mono", "monospace"]

# These diagrams are full of literal dollar signs ("$1,000 face value").
# Without this, matplotlib treats any paired "$...$" on a single line as
# mathtext and silently mangles it (eats the "$", italicizes the rest) —
# whether that happens depends on line-wrapping, so it's invisible in
# some labels and not others unless this is off everywhere.
plt.rcParams["text.parse_math"] = False

EVENT_KINDS = ("outflow", "coupon", "maturity")


class ChartError(RuntimeError):
    pass


def _apply_title(ax, title: str) -> None:
    ax.set_title(
        title.upper(),
        color=COLOR_HEADING,
        fontsize=12,
        fontweight="bold",
        loc="left",
        pad=18,
    )


# ---------------------------------------------------------------------------
# timeline
# ---------------------------------------------------------------------------


def parse_event(spec: str) -> tuple[float, str, str]:
    parts = spec.split(":", 2)
    if len(parts) != 3:
        raise ChartError(f'Bad --event value {spec!r}; expected "YEAR:LABEL:KIND"')
    year_str, label, kind = parts
    if kind not in EVENT_KINDS:
        raise ChartError(f"Event kind must be one of {EVENT_KINDS}, got {kind!r}")
    try:
        year = float(year_str)
    except ValueError as exc:
        raise ChartError(f"Bad year in --event {spec!r}: {exc}") from exc
    return year, label.replace("\\n", "\n"), kind


def make_timeline(
    events: list[tuple[float, str, str]],
    output_path: Path,
    title: str,
    xlabel: str,
) -> None:
    plt.rcParams["font.family"] = FONT_STACK

    years = [e[0] for e in events]
    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=150)
    fig.patch.set_facecolor(COLOR_BG)
    ax.set_facecolor(COLOR_BG)

    baseline_y = 0
    ax.axhline(baseline_y, color=COLOR_BORDER, linewidth=1.2, zorder=1)

    for year, label, kind in events:
        if kind == "outflow":
            ax.scatter(
                [year], [baseline_y], s=90, facecolors=COLOR_BG, edgecolors=COLOR_HEADING,
                linewidths=1.6, zorder=5,
            )
            ax.annotate(
                label, xy=(year, baseline_y), xytext=(0, -34), textcoords="offset points",
                ha="center", va="top", fontsize=8.5, color=COLOR_HEADING, fontweight="bold",
            )
            ax.plot([year, year], [baseline_y, baseline_y - 20 / 72], color=COLOR_BORDER, linewidth=1, zorder=2)
        elif kind == "coupon":
            ax.scatter([year], [baseline_y], s=55, color=COLOR_ACCENT, zorder=5)
            ax.annotate(
                label, xy=(year, baseline_y), xytext=(0, 16), textcoords="offset points",
                ha="center", va="bottom", fontsize=8.5, color=COLOR_MUTED,
            )
        else:  # maturity
            ax.scatter(
                [year], [baseline_y], s=170, marker="s", color=COLOR_ACCENT,
                edgecolors=COLOR_HEADING, linewidths=1.4, zorder=6,
            )
            ax.annotate(
                label, xy=(year, baseline_y), xytext=(0, 26), textcoords="offset points",
                ha="center", va="bottom", fontsize=9, color=COLOR_HEADING, fontweight="bold",
            )

    span = max(years) - min(years) if len(years) > 1 else 1
    ax.set_xlim(min(years) - span * 0.12, max(years) + span * 0.12)
    ax.set_ylim(-1.1, 1.1)
    ax.set_yticks([])
    ax.set_xticks(years)
    ax.set_xticklabels([f"{int(y)}" if float(y).is_integer() else f"{y}" for y in years])
    ax.tick_params(colors=COLOR_MUTED, labelsize=9, length=0)

    for spine_name in ("top", "right", "left"):
        ax.spines[spine_name].set_visible(False)
    ax.spines["bottom"].set_visible(False)

    if xlabel:
        ax.set_xlabel(xlabel, color=COLOR_MUTED, fontsize=9)

    # Legend-as-key, spelled out in plain text rather than a matplotlib
    # legend box, to match the site's spare, label-driven style.
    ax.text(
        0.0, -0.34,
        "○ money paid out     ● coupon received     ■ maturity — principal + final coupon together",
        transform=ax.transAxes, color=COLOR_MUTED, fontsize=7.5, ha="left", va="top",
    )

    _apply_title(ax, title)

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, facecolor=COLOR_BG)
    plt.close(fig)


# ---------------------------------------------------------------------------
# flow
# ---------------------------------------------------------------------------


def make_flow(
    left_label: str,
    right_label: str,
    top_arrow_label: str,
    bottom_arrow_label: str,
    notional_label: str | None,
    output_path: Path,
    title: str,
) -> None:
    plt.rcParams["font.family"] = FONT_STACK

    fig, ax = plt.subplots(figsize=(8, 4.6), dpi=150)
    fig.patch.set_facecolor(COLOR_BG)
    ax.set_facecolor(COLOR_BG)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")

    box_w, box_h = 2.6, 1.6
    left_x, right_x = 0.6, 10 - 0.6 - box_w
    box_y = 2.8

    for x, label in ((left_x, left_label), (right_x, right_label)):
        ax.add_patch(
            Rectangle(
                (x, box_y), box_w, box_h,
                facecolor=COLOR_BG, edgecolor=COLOR_HEADING, linewidth=1.4, zorder=5,
            )
        )
        ax.text(
            x + box_w / 2, box_y + box_h / 2, label,
            ha="center", va="center", fontsize=11, fontweight="bold", color=COLOR_HEADING, zorder=6,
        )

    left_edge = left_x + box_w
    right_edge = right_x

    # Top arrow: left party -> right party.
    ax.annotate(
        "", xy=(right_edge, box_y + box_h * 0.72), xytext=(left_edge, box_y + box_h * 0.72),
        arrowprops=dict(arrowstyle="-|>", color=COLOR_ACCENT, linewidth=1.8, mutation_scale=18),
        zorder=4,
    )
    ax.text(
        (left_edge + right_edge) / 2, box_y + box_h * 0.72 + 0.22, top_arrow_label,
        ha="center", va="bottom", fontsize=9, color=COLOR_ACCENT, fontweight="bold",
    )

    # Bottom arrow: right party -> left party.
    ax.annotate(
        "", xy=(left_edge, box_y + box_h * 0.28), xytext=(right_edge, box_y + box_h * 0.28),
        arrowprops=dict(arrowstyle="-|>", color=COLOR_MUTED, linewidth=1.8, mutation_scale=18),
        zorder=4,
    )
    ax.text(
        (left_edge + right_edge) / 2, box_y + box_h * 0.28 - 0.22, bottom_arrow_label,
        ha="center", va="top", fontsize=9, color=COLOR_MUTED, fontweight="bold",
    )

    if notional_label:
        note_w, note_h = 5.4, 1.0
        note_x = (10 - note_w) / 2
        note_y = 0.55
        ax.add_patch(
            Rectangle(
                (note_x, note_y), note_w, note_h,
                facecolor="none", edgecolor=COLOR_MUTED, linewidth=1, linestyle=(0, (4, 3)), zorder=3,
            )
        )
        ax.text(
            note_x + note_w / 2, note_y + note_h / 2, notional_label.replace("\\n", "\n"),
            ha="center", va="center", fontsize=8.5, color=COLOR_MUTED, zorder=4,
        )

    _apply_title(ax, title)

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, facecolor=COLOR_BG)
    plt.close(fig)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_timeline = subparsers.add_parser("timeline", help="Horizontal sequence of dated events")
    p_timeline.add_argument("--title", required=True)
    p_timeline.add_argument("--output", required=True)
    p_timeline.add_argument("--xlabel", default="")
    p_timeline.add_argument(
        "--event", action="append", default=[], metavar="YEAR:LABEL:KIND",
        help="Repeatable. KIND is one of outflow, coupon, maturity. Use \\n in LABEL for a line break.",
    )

    p_flow = subparsers.add_parser("flow", help="Two-party box-and-arrow diagram")
    p_flow.add_argument("--title", required=True)
    p_flow.add_argument("--output", required=True)
    p_flow.add_argument("--left-label", required=True)
    p_flow.add_argument("--right-label", required=True)
    p_flow.add_argument("--top-arrow-label", required=True)
    p_flow.add_argument("--bottom-arrow-label", required=True)
    p_flow.add_argument("--notional-label", default=None, help="Use \\n for a line break.")

    args = parser.parse_args()

    try:
        if args.command == "timeline":
            events = [parse_event(e) for e in args.event]
            if not events:
                raise ChartError("At least one --event is required")
            make_timeline(
                events=events,
                output_path=Path(args.output),
                title=args.title,
                xlabel=args.xlabel,
            )
        else:
            make_flow(
                left_label=args.left_label,
                right_label=args.right_label,
                top_arrow_label=args.top_arrow_label,
                bottom_arrow_label=args.bottom_arrow_label,
                notional_label=args.notional_label,
                output_path=Path(args.output),
                title=args.title,
            )
    except ChartError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
