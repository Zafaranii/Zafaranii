"""Render data/contributions.json as an animated 53-week x 7-day heatmap SVG.

Boxes slide down into place on a diagonal stagger (col+row delay), play once
on load, then freeze -- no infinite loop.
"""
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "contributions.json"
OUT_PATH = ROOT / "contrib-heatmap.svg"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

BOX = 11
GAP = 3
CELL = BOX + GAP
LEFT_PAD = 28
TOP_PAD = 34
RIGHT_PAD = 16
BOTTOM_PAD = 46
FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def load_data():
    payload = json.loads(DATA_PATH.read_text())
    return payload


def weekday_index(date_str):
    # Python: Monday=0..Sunday=6. GitHub calendar weeks run Sunday..Saturday.
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return (dt.weekday() + 1) % 7  # Sunday=0 .. Saturday=6


def build_weeks(days):
    weeks = []
    current_week = [None] * 7
    if not days:
        return weeks

    first_wd = weekday_index(days[0]["date"])
    for i in range(first_wd):
        current_week[i] = None

    for day in days:
        wd = weekday_index(day["date"])
        if wd == 0 and any(c is not None for c in current_week):
            weeks.append(current_week)
            current_week = [None] * 7
        current_week[wd] = day

    if any(c is not None for c in current_week):
        weeks.append(current_week)
    return weeks


def month_labels(weeks):
    labels = []
    last_month = None
    for col, week in enumerate(weeks):
        for day in week:
            if day is None:
                continue
            month = int(day["date"][5:7])
            if month != last_month:
                labels.append((col, MONTH_NAMES[month - 1]))
                last_month = month
            break
    return labels


def render(payload):
    days = payload["days"]
    stats = payload["stats"]
    weeks = build_weeks(days)
    n_weeks = len(weeks)

    grid_width = LEFT_PAD + n_weeks * CELL + RIGHT_PAD
    height = TOP_PAD + 7 * CELL + BOTTOM_PAD

    footer = (
        f'{stats["total"]:,} contributions in the last year · '
        f'current streak {stats["current_streak"]}d · '
        f'longest streak {stats["longest_streak"]}d'
    )
    footer_font_size = 11
    footer_char_w = footer_font_size * 0.72
    legend_end_x = LEFT_PAD + 32 + len(PALETTE) * CELL + 30  # "Less" + swatches + "More"
    footer_start_min_gap = 24
    needed_width = legend_end_x + footer_start_min_gap + len(footer) * footer_char_w + RIGHT_PAD

    width = max(grid_width, needed_width)
    # Monospace advance width varies by renderer, so rather than trust the
    # estimate above, force the footer to render within a fixed pixel box
    # (SVG textLength) -- this guarantees it never clips the canvas edge.
    footer_available_px = width - RIGHT_PAD - legend_end_x - footer_start_min_gap

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" font-family="{FONT}">'
    )
    parts.append(f"""
  <style>
    .bg {{ fill: #0d1117; }}
    .label {{ fill: #8b949e; font-size: 10px; }}
    .footer {{ fill: #c9d1d9; font-size: 11px; }}
    .box {{
      opacity: 0;
      transform-box: fill-box;
      transform-origin: center;
      animation: reveal 0.5s ease-out forwards;
    }}
    @keyframes reveal {{
      0%   {{ opacity: 0; transform: translate(-6px, -6px) scale(0.6); }}
      100% {{ opacity: 1; transform: translate(0, 0) scale(1); }}
    }}
  </style>
""")
    parts.append(f'<rect class="bg" x="0" y="0" width="{width}" height="{height}" rx="6"/>')

    for col, label in month_labels(weeks):
        x = LEFT_PAD + col * CELL
        parts.append(f'<text class="label" x="{x}" y="{TOP_PAD - 10}">{label}</text>')

    weekday_labels = {1: "Mon", 3: "Wed", 5: "Fri"}
    for row, text in weekday_labels.items():
        y = TOP_PAD + row * CELL + BOX - 2
        parts.append(f'<text class="label" x="0" y="{y}">{text}</text>')

    for col, week in enumerate(weeks):
        for row, day in enumerate(week):
            if day is None:
                continue
            x = LEFT_PAD + col * CELL
            y = TOP_PAD + row * CELL
            level = max(0, min(day["level"], len(PALETTE) - 1))
            color = PALETTE[level]
            delay = (col + row) * 0.008
            title = f'{day["count"]} contributions on {day["date"]}'
            parts.append(
                f'<rect class="box" x="{x}" y="{y}" width="{BOX}" height="{BOX}" rx="2" '
                f'fill="{color}" style="animation-delay:{delay:.3f}s">'
                f'<title>{title}</title></rect>'
            )

    legend_y = TOP_PAD + 7 * CELL + 20
    legend_x = LEFT_PAD
    parts.append(f'<text class="label" x="{legend_x}" y="{legend_y + 8}">Less</text>')
    lx = legend_x + 32
    for level, color in enumerate(PALETTE):
        parts.append(f'<rect x="{lx}" y="{legend_y}" width="{BOX}" height="{BOX}" rx="2" fill="{color}"/>')
        lx += CELL
    parts.append(f'<text class="label" x="{lx + 4}" y="{legend_y + 8}">More</text>')

    parts.append(
        f'<text class="footer" x="{width - RIGHT_PAD}" y="{legend_y + 8}" text-anchor="end" '
        f'textLength="{footer_available_px:.1f}" lengthAdjust="spacingAndGlyphs">{footer}</text>'
    )

    parts.append("</svg>")
    return "\n".join(parts)


def main():
    payload = load_data()
    svg = render(payload)
    OUT_PATH.write_text(svg)
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
