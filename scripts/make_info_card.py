"""Hand-authored neofetch-style SVG info card. Lines fade + slide in on a
short stagger. Set STATIC=1 to emit a frozen frame for local previews."""
import os
from pathlib import Path

OUT_PATH = Path(__file__).resolve().parent.parent / "info-card.svg"
STATIC = os.environ.get("STATIC") == "1"

FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
WIDTH = 540
LINE_H = 26
TOP_PAD = 56

FIELDS = [
    ("Name", "Marwan Hazem"),
    ("Role", "Software Engineer, Backend"),
    ("Now", "Building APIs & backend systems"),
    ("Prev", "Debugging what worked 5 minutes ago"),
    ("Stack", "Python · FastAPI · Django · Flask · .NET/C#"),
    ("Data", "MySQL · PostgreSQL · Firebase"),
    ("Highlights", "Building DuckyCart (duckycart.me)"),
    ("Location", "Giza, Egypt"),
]

ACCENT = "#39d353"
KEY_COLOR = "#7ee787"
VAL_COLOR = "#c9d1d9"
MUTED = "#8b949e"

HEIGHT = TOP_PAD + len(FIELDS) * LINE_H + 24


def esc(s):
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def render():
    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
        f'width="{WIDTH}" height="{HEIGHT}" font-family="{FONT}">'
    )

    anim = "" if STATIC else """
  <style>
    .row {
      opacity: 0;
      transform: translateX(-8px);
      animation: typein 0.35s ease-out forwards;
    }
    @keyframes typein {
      to { opacity: 1; transform: translateX(0); }
    }
  </style>
"""
    parts.append(anim)

    parts.append(f'<rect x="0" y="0" width="{WIDTH}" height="{HEIGHT}" rx="8" fill="#0d1117" stroke="#30363d"/>')

    parts.append('<circle cx="20" cy="20" r="6" fill="#ff5f56"/>')
    parts.append('<circle cx="40" cy="20" r="6" fill="#ffbd2e"/>')
    parts.append('<circle cx="60" cy="20" r="6" fill="#27c93f"/>')
    parts.append(
        f'<text x="{WIDTH / 2}" y="24" text-anchor="middle" font-size="12" fill="{MUTED}">'
        f'marwan@github ~ % neofetch</text>'
    )
    parts.append(f'<line x1="0" y1="38" x2="{WIDTH}" y2="38" stroke="#21262d"/>')

    label_x = 24
    val_x = 150
    for i, (key, val) in enumerate(FIELDS):
        y = TOP_PAD + i * LINE_H
        row_class = "" if STATIC else 'class="row" style="animation-delay:%.2fs"' % (i * 0.12)
        parts.append(f'<g {row_class}>')
        parts.append(f'<text x="{label_x}" y="{y}" font-size="13" fill="{KEY_COLOR}">{esc(key)}</text>')
        parts.append(f'<text x="{val_x}" y="{y}" font-size="13" fill="{VAL_COLOR}">{esc(val)}</text>')
        parts.append("</g>")

    swatches_y = HEIGHT - 16
    colors = ["#0d1117", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0", "#c9d1d9", "#ffffff"]
    sx = label_x
    for c in colors:
        parts.append(f'<rect x="{sx}" y="{swatches_y}" width="14" height="10" rx="2" fill="{c}" stroke="#30363d" stroke-width="0.5"/>')
        sx += 18

    parts.append("</svg>")
    return "\n".join(parts)


def main():
    OUT_PATH.write_text(render())
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
