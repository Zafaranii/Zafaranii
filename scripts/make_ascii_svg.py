"""Downsample the prepped grayscale photo to a character grid and render it
as a self-typing monochrome SVG: each row wipes in left-to-right with a
small block cursor riding the edge, staggered top to bottom. Plays once,
then freezes -- no looping.
"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC_PATH = ROOT / "assets" / "source-prepped.png"
OUT_PATH = ROOT / "avi-ascii.svg"

RAMP = " .`:-=+*cs#%@"   # bright (sparse) -> dark (dense)
#        ^ leading space clears the background to nothing

COLS = 100
ROWS = 53

FONT_SIZE = 8
CHAR_W = FONT_SIZE * 0.6
CHAR_H = FONT_SIZE * 1.0

ROW_DUR = 0.6
ROW_STAGGER = 0.045
FILL_COLOR = "#c9d1d9"


def to_ascii_grid(img: Image.Image):
    gray = img.convert("L").resize((COLS, ROWS), Image.LANCZOS)
    pixels = gray.load()
    grid = []
    for y in range(ROWS):
        row = []
        for x in range(COLS):
            brightness = pixels[x, y]  # 0=dark .. 255=bright
            idx = round((255 - brightness) / 255 * (len(RAMP) - 1))
            row.append(RAMP[idx])
        grid.append("".join(row))
    return grid


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(grid):
    width = COLS * CHAR_W
    height = ROWS * CHAR_H

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.1f} {height:.1f}" '
        f'width="{width:.1f}" height="{height:.1f}">'
    )
    parts.append(
        '<style>text{font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;'
        f'font-size:{FONT_SIZE}px; fill:{FILL_COLOR}; white-space:pre;}}</style>'
    )
    parts.append(f'<rect x="0" y="0" width="{width:.1f}" height="{height:.1f}" fill="#0d1117"/>')

    defs = ['<defs>']
    body = []

    for r, row_text in enumerate(grid):
        stripped = row_text.rstrip()
        if not stripped:
            continue
        begin = r * ROW_STAGGER
        y = (r + 1) * CHAR_H - 2
        row_px_width = len(row_text) * CHAR_W
        clip_id = f"rowclip{r}"

        defs.append(
            f'<clipPath id="{clip_id}">'
            f'<rect x="0" y="{r * CHAR_H:.1f}" width="0" height="{CHAR_H:.1f}">'
            f'<animate attributeName="width" from="0" to="{row_px_width:.1f}" '
            f'begin="{begin:.3f}s" dur="{ROW_DUR}s" fill="freeze" calcMode="linear"/>'
            f'</rect></clipPath>'
        )

        body.append(f'<g clip-path="url(#{clip_id})">')
        body.append(f'<text x="0" y="{y:.1f}" xml:space="preserve">{esc(row_text)}</text>')
        body.append('</g>')

        cursor_y = r * CHAR_H
        body.append(
            f'<rect x="0" y="{cursor_y:.1f}" width="{CHAR_W * 0.7:.1f}" height="{CHAR_H * 0.85:.1f}" '
            f'fill="{FILL_COLOR}">'
            f'<animate attributeName="x" from="0" to="{max(row_px_width - CHAR_W, 0):.1f}" '
            f'begin="{begin:.3f}s" dur="{ROW_DUR}s" fill="freeze" calcMode="linear"/>'
            f'<animate attributeName="opacity" from="1" to="0" '
            f'begin="{begin + ROW_DUR:.3f}s" dur="0.15s" fill="freeze"/>'
            f'</rect>'
        )

    defs.append('</defs>')
    parts.extend(defs)
    parts.extend(body)
    parts.append('</svg>')
    return "\n".join(parts)


def main():
    if not SRC_PATH.exists():
        raise SystemExit(f"missing {SRC_PATH} -- run scripts/prep_photo.py first")
    img = Image.open(SRC_PATH)
    grid = to_ascii_grid(img)
    svg = render(grid)
    OUT_PATH.write_text(svg)
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
