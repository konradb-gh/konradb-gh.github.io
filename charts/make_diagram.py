#!/usr/bin/env python3
"""Generate schematic, illustrative/conceptual diagrams styled to match
the site's light "trading terminal" theme. Distinct from every other
script in this directory, which all plot real market data pulled via
yfinance — this one draws hand-specified shapes (timelines, flow
diagrams) for explaining a mechanism, not for reporting a price.

Four subcommands, sharing the same visual language (warm paper
background, amber accent, near-black ink, JetBrains Mono, sharp
corners, thin 1px borders):

  timeline    A horizontal sequence of dated events — e.g. a bond's
              cash flows from purchase to maturity. Each event is one
              of three kinds (outflow / coupon / maturity), styled
              distinctly so a reader can tell a repeating payment
              apart from the one-off events at the ends.

  flow        A two-party box-and-arrow diagram — e.g. who pays what
              in an interest rate swap — with an optional dashed
              "reference only" note box for something like a notional
              amount that never actually changes hands.

  compare     A single before/after state change — one box, one
              labeled arrow, one box — e.g. a stock's reference price
              adjusting down on the ex-dividend date. Optional dashed
              note box underneath for a caveat that shouldn't look
              like it carries the same weight as the main mechanic.

  settlement  A multi-row comparison of how long each of several
              markets' settlement cycles takes, one row per market,
              each showing trade day / ex-date / record date as
              points along a shared day-offset axis — so markets with
              matching cycles visually align and markets with a gap
              between ex-date and record date visibly show it.

  ladder      A live order book, drawn as a price ladder — one
              horizontal bar per price level, bid levels in one color
              and ask levels in another, sorted so the best bid and
              best ask sit closest to the spread gap in the middle.

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
        --note-label "Notional amount: $300,000\\nreference only -- never actually exchanged"

    python make_diagram.py compare \\
        --title "The ex-date price adjustment" \\
        --output ../public/charts/dividend-price-adjustment-2026.png \\
        --left-label "Before ex-date\\n$50.00" \\
        --right-label "Ex-date open\\n$49.50" \\
        --arrow-label "Reference price adjusted\\ndown by the $0.50 dividend" \\
        --note-label "Mechanical starting point only --\\nreal trading still sets where it closes"

    python make_diagram.py settlement \\
        --title "Ex-date and record date, three settlement cycles" \\
        --output ../public/charts/dividend-settlement-comparison-2026.png \\
        --day-label "0:Trade day" --day-label "1:1 business day later" \\
        --day-label "2:2 business days later" \\
        --row "US -- T+1:1:1" \\
        --row "India -- T+1:1:1" \\
        --row "UK / EU -- T+2 (until Oct 2027):1:2"

    python make_diagram.py ladder \\
        --title "A live order book" \\
        --output ../public/charts/order-book-ladder-2026.png \\
        --level "42.30:500:ask" --level "42.15:250:ask" --level "42.05:300:ask" \\
        --level "41.95:400:bid" --level "41.80:350:bid" --level "41.60:600:bid"
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
# Buy/sell semantics only (e.g. the ladder subcommand's bid/ask bars) —
# every other subcommand sticks to ACCENT/MUTED for its two-sided contrasts.
COLOR_POS = "#1f7a45"
COLOR_NEG = "#b3261e"

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


def _draw_note_box(ax, label: str | None, *, center_x: float, y: float, width: float, height: float) -> None:
    """A dashed, de-emphasized box for a caveat that shouldn't read with
    the same weight as the diagram's main mechanic — a notional amount
    that never moves, a disclaimer that a mechanical adjustment isn't a
    guarantee, etc. No-op if label is None."""
    if not label:
        return
    x = center_x - width / 2
    ax.add_patch(
        Rectangle(
            (x, y), width, height,
            facecolor="none", edgecolor=COLOR_MUTED, linewidth=1, linestyle=(0, (4, 3)), zorder=3,
        )
    )
    ax.text(
        center_x, y + height / 2, label.replace("\\n", "\n"),
        ha="center", va="center", fontsize=8.5, color=COLOR_MUTED, zorder=4,
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
    note_label: str | None,
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

    _draw_note_box(ax, note_label, center_x=5.0, y=0.55, width=5.4, height=1.0)

    _apply_title(ax, title)

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, facecolor=COLOR_BG)
    plt.close(fig)


# ---------------------------------------------------------------------------
# compare
# ---------------------------------------------------------------------------


def make_compare(
    left_label: str,
    right_label: str,
    arrow_label: str,
    note_label: str | None,
    output_path: Path,
    title: str,
) -> None:
    plt.rcParams["font.family"] = FONT_STACK

    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=150)
    fig.patch.set_facecolor(COLOR_BG)
    ax.set_facecolor(COLOR_BG)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5.4)
    ax.axis("off")

    box_w, box_h = 2.3, 1.8
    left_x, right_x = 0.7, 10 - 0.7 - box_w
    box_y = 2.4

    for x, label in ((left_x, left_label), (right_x, right_label)):
        ax.add_patch(
            Rectangle(
                (x, box_y), box_w, box_h,
                facecolor=COLOR_BG, edgecolor=COLOR_HEADING, linewidth=1.4, zorder=5,
            )
        )
        ax.text(
            x + box_w / 2, box_y + box_h / 2, label.replace("\\n", "\n"),
            ha="center", va="center", fontsize=12, fontweight="bold", color=COLOR_HEADING, zorder=6,
            linespacing=1.6,
        )

    left_edge = left_x + box_w
    right_edge = right_x

    ax.annotate(
        "", xy=(right_edge, box_y + box_h / 2), xytext=(left_edge, box_y + box_h / 2),
        arrowprops=dict(arrowstyle="-|>", color=COLOR_ACCENT, linewidth=2, mutation_scale=20),
        zorder=4,
    )
    ax.text(
        (left_edge + right_edge) / 2, box_y + box_h / 2 + 0.26, arrow_label.replace("\\n", "\n"),
        ha="center", va="bottom", fontsize=9, color=COLOR_ACCENT, fontweight="bold",
    )

    _draw_note_box(ax, note_label, center_x=5.0, y=0.35, width=6.6, height=1.05)

    _apply_title(ax, title)

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, facecolor=COLOR_BG)
    plt.close(fig)


# ---------------------------------------------------------------------------
# settlement
# ---------------------------------------------------------------------------


def parse_row(spec: str) -> tuple[str, int, int]:
    parts = spec.split(":", 2)
    if len(parts) != 3:
        raise ChartError(f'Bad --row value {spec!r}; expected "LABEL:EX_DAY:RECORD_DAY"')
    label, ex_str, record_str = parts
    try:
        ex_day, record_day = int(ex_str), int(record_str)
    except ValueError as exc:
        raise ChartError(f"Bad day number in --row {spec!r}: {exc}") from exc
    if record_day < ex_day:
        raise ChartError(f"Record day can't come before ex-date day in --row {spec!r}")
    return label.replace("\\n", "\n"), ex_day, record_day


def parse_day_label(spec: str) -> tuple[int, str]:
    if ":" not in spec:
        raise ChartError(f'Bad --day-label value {spec!r}; expected "DAY:LABEL"')
    day_str, label = spec.split(":", 1)
    try:
        day = int(day_str)
    except ValueError as exc:
        raise ChartError(f"Bad day number in --day-label {spec!r}: {exc}") from exc
    return day, label


def make_settlement(
    rows: list[tuple[str, int, int]],
    day_labels: dict[int, str],
    output_path: Path,
    title: str,
) -> None:
    plt.rcParams["font.family"] = FONT_STACK

    max_day = max(r[2] for r in rows)
    n = len(rows)
    row_h = 1.0
    fig, ax = plt.subplots(figsize=(8, 1.6 + n * 1.15), dpi=150)
    fig.patch.set_facecolor(COLOR_BG)
    ax.set_facecolor(COLOR_BG)

    for i, (label, ex_day, record_day) in enumerate(rows):
        y = (n - 1 - i) * row_h

        ax.plot([0, max_day], [y, y], color=COLOR_BORDER, linewidth=1.2, zorder=1)
        ax.text(-0.15, y, label, ha="right", va="center", fontsize=9.5, fontweight="bold", color=COLOR_HEADING)

        # Trade day: neutral reference point, always day 0.
        ax.scatter([0], [y], s=70, facecolors=COLOR_BG, edgecolors=COLOR_MUTED, linewidths=1.4, zorder=5)

        if ex_day == record_day:
            ax.scatter(
                [ex_day], [y], s=170, marker="s", color=COLOR_ACCENT,
                edgecolors=COLOR_HEADING, linewidths=1.4, zorder=6,
            )
            ax.annotate(
                "Ex-date &\nrecord date", xy=(ex_day, y), xytext=(0, 22), textcoords="offset points",
                ha="center", va="bottom", fontsize=8, color=COLOR_HEADING, fontweight="bold",
            )
        else:
            ax.scatter([ex_day], [y], s=75, color=COLOR_ACCENT, zorder=6)
            ax.annotate(
                "Ex-date", xy=(ex_day, y), xytext=(0, 20), textcoords="offset points",
                ha="center", va="bottom", fontsize=8, color=COLOR_ACCENT, fontweight="bold",
            )
            ax.scatter(
                [record_day], [y], s=170, marker="s", color=COLOR_ACCENT,
                edgecolors=COLOR_HEADING, linewidths=1.4, zorder=6,
            )
            ax.annotate(
                "Record date", xy=(record_day, y), xytext=(0, 22), textcoords="offset points",
                ha="center", va="bottom", fontsize=8, color=COLOR_HEADING, fontweight="bold",
            )

    ax.set_xlim(-0.35 * max(max_day, 1) - 1.0, max_day + 0.6)
    ax.set_ylim(-0.75, (n - 1) * row_h + 1.0)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine_name in ("top", "right", "left", "bottom"):
        ax.spines[spine_name].set_visible(False)

    bottom_row_y = 0
    if day_labels:
        for day, label in sorted(day_labels.items()):
            ax.annotate(
                label, xy=(day, bottom_row_y), xytext=(0, -20), textcoords="offset points",
                ha="center", va="top", fontsize=8, color=COLOR_MUTED,
            )

    # Fixed axes-fraction offset for the key, independent of row count.
    ax.text(
        0.0, -0.12,
        "○ trade day     ● ex-date only     ■ record date (or both, when same day)",
        transform=ax.transAxes, color=COLOR_MUTED, fontsize=7.5, ha="left", va="top",
    )

    _apply_title(ax, title)

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, facecolor=COLOR_BG)
    plt.close(fig)


# ---------------------------------------------------------------------------
# ladder
# ---------------------------------------------------------------------------


def parse_level(spec: str) -> tuple[float, int, str]:
    parts = spec.split(":", 2)
    if len(parts) != 3:
        raise ChartError(f'Bad --level value {spec!r}; expected "PRICE:SIZE:SIDE"')
    price_str, size_str, side = parts
    if side not in ("bid", "ask"):
        raise ChartError(f"Level side must be 'bid' or 'ask', got {side!r}")
    try:
        price, size = float(price_str), int(size_str)
    except ValueError as exc:
        raise ChartError(f"Bad price/size in --level {spec!r}: {exc}") from exc
    return price, size, side


def make_ladder(
    levels: list[tuple[float, int, str]],
    output_path: Path,
    title: str,
) -> None:
    plt.rcParams["font.family"] = FONT_STACK

    # Asks displayed worst-to-best top-to-bottom, bids best-to-worst
    # top-to-bottom, so the best ask and best bid both land on the rows
    # immediately next to the spread gap in the middle.
    asks = sorted((lv for lv in levels if lv[2] == "ask"), key=lambda lv: lv[0])
    bids = sorted((lv for lv in levels if lv[2] == "bid"), key=lambda lv: -lv[0])
    if not asks or not bids:
        raise ChartError("Need at least one 'ask' level and one 'bid' level")

    rows = list(reversed(asks)) + bids
    n = len(rows)
    max_size = max(size for _, size, _ in rows)

    fig, ax = plt.subplots(figsize=(8, 1.4 + n * 0.62), dpi=150)
    fig.patch.set_facecolor(COLOR_BG)
    ax.set_facecolor(COLOR_BG)

    yticks, ylabels = [], []
    for i, (price, size, side) in enumerate(rows):
        y = n - 1 - i
        color = COLOR_NEG if side == "ask" else COLOR_POS
        ax.barh(y, size, height=0.58, color=color, zorder=5)
        ax.text(
            size + max_size * 0.03, y, f"{size:,} sh",
            va="center", ha="left", fontsize=8.5, color=COLOR_MUTED,
        )
        yticks.append(y)
        ylabels.append(f"${price:,.2f}")

    ax.set_yticks(yticks)
    ax.set_yticklabels(ylabels, fontsize=9.5, color=COLOR_HEADING, fontweight="bold")
    ax.set_xlim(0, max_size * 1.22)
    ax.set_xlabel("Shares waiting at this price", color=COLOR_MUTED, fontsize=9)
    ax.tick_params(axis="x", colors=COLOR_MUTED, labelsize=8.5)
    ax.tick_params(axis="y", length=0)
    for spine_name in ("top", "right", "left"):
        ax.spines[spine_name].set_visible(False)
    ax.spines["bottom"].set_color(COLOR_BORDER)

    best_ask_y = n - len(asks)
    best_bid_y = best_ask_y - 1
    mid_y = (best_ask_y + best_bid_y) / 2
    spread = asks[0][0] - bids[0][0]
    ax.axhline(mid_y, color=COLOR_BORDER, linewidth=1, linestyle=(0, (4, 3)), zorder=2)
    ax.text(
        max_size * 1.22, mid_y, f"Spread: ${spread:,.2f}",
        va="center", ha="right", fontsize=8.5, color=COLOR_ACCENT, fontweight="bold",
    )

    ax.text(
        0.0, -0.16, "■ ask — sellers waiting",
        transform=ax.transAxes, color=COLOR_NEG, fontsize=7.5, ha="left", va="top", fontweight="bold",
    )
    ax.text(
        0.34, -0.16, "■ bid — buyers waiting",
        transform=ax.transAxes, color=COLOR_POS, fontsize=7.5, ha="left", va="top", fontweight="bold",
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
    p_flow.add_argument("--note-label", default=None, help="Optional dashed note box. Use \\n for a line break.")

    p_compare = subparsers.add_parser("compare", help="Single before/after state change")
    p_compare.add_argument("--title", required=True)
    p_compare.add_argument("--output", required=True)
    p_compare.add_argument("--left-label", required=True, help="Use \\n for a line break.")
    p_compare.add_argument("--right-label", required=True, help="Use \\n for a line break.")
    p_compare.add_argument("--arrow-label", required=True, help="Use \\n for a line break.")
    p_compare.add_argument("--note-label", default=None, help="Optional dashed note box. Use \\n for a line break.")

    p_settlement = subparsers.add_parser("settlement", help="Multi-row market settlement-cycle comparison")
    p_settlement.add_argument("--title", required=True)
    p_settlement.add_argument("--output", required=True)
    p_settlement.add_argument(
        "--row", action="append", default=[], metavar="LABEL:EX_DAY:RECORD_DAY",
        help="Repeatable, one per market. Day numbers are business days after the trade day (0).",
    )
    p_settlement.add_argument(
        "--day-label", action="append", default=[], metavar="DAY:LABEL",
        help="Repeatable. Custom label for a tick on the shared day axis.",
    )

    p_ladder = subparsers.add_parser("ladder", help="Order book price ladder")
    p_ladder.add_argument("--title", required=True)
    p_ladder.add_argument("--output", required=True)
    p_ladder.add_argument(
        "--level", action="append", default=[], metavar="PRICE:SIZE:SIDE",
        help="Repeatable. SIDE is 'bid' or 'ask'. Needs at least one of each.",
    )

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
        elif args.command == "flow":
            make_flow(
                left_label=args.left_label,
                right_label=args.right_label,
                top_arrow_label=args.top_arrow_label,
                bottom_arrow_label=args.bottom_arrow_label,
                note_label=args.note_label,
                output_path=Path(args.output),
                title=args.title,
            )
        elif args.command == "compare":
            make_compare(
                left_label=args.left_label,
                right_label=args.right_label,
                arrow_label=args.arrow_label,
                note_label=args.note_label,
                output_path=Path(args.output),
                title=args.title,
            )
        elif args.command == "settlement":
            rows = [parse_row(r) for r in args.row]
            if not rows:
                raise ChartError("At least one --row is required")
            day_labels = dict(parse_day_label(d) for d in args.day_label)
            make_settlement(
                rows=rows,
                day_labels=day_labels,
                output_path=Path(args.output),
                title=args.title,
            )
        else:  # ladder
            levels = [parse_level(lv) for lv in args.level]
            if not levels:
                raise ChartError("At least one --level is required")
            make_ladder(
                levels=levels,
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
