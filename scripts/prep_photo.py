"""One-time photo prep: strip the background, boost local contrast, and
composite onto white so the background maps to the blank end of the ASCII
ramp. Run once per source photo.

Usage: python scripts/prep_photo.py assets/source-photo.jpg
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps
from rembg import remove

ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / "assets" / "source-prepped.png"


def crop_to_subject(cutout: Image.Image, pad_frac: float = 0.08) -> Image.Image:
    alpha = np.array(cutout.split()[-1])
    ys, xs = np.where(alpha > 20)
    if len(xs) == 0:
        return cutout
    x0, x1 = xs.min(), xs.max()
    y0, y1 = ys.min(), ys.max()
    pad_x = int((x1 - x0) * pad_frac)
    pad_y = int((y1 - y0) * pad_frac)
    w, h = cutout.size
    x0 = max(0, x0 - pad_x)
    y0 = max(0, y0 - pad_y)
    x1 = min(w, x1 + pad_x)
    y1 = min(h, y1 + pad_y)
    return cutout.crop((x0, y0, x1, y1))


def prep(src_path: Path) -> Image.Image:
    raw = ImageOps.exif_transpose(Image.open(src_path)).convert("RGBA")

    # 1. remove background -> RGBA with transparency where the subject isn't
    cutout = remove(raw)

    # 1b. crop tight to the subject so it fills the ASCII grid instead of
    # sitting in a sea of blank space
    cutout = crop_to_subject(cutout)

    # 2. boost local contrast with CLAHE on the luminance channel
    rgb = np.array(cutout.convert("RGB"))
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    lab = cv2.merge((l, a, b))
    contrasted = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

    boosted = Image.fromarray(contrasted).convert("RGBA")
    boosted.putalpha(cutout.split()[-1])  # keep the cutout's alpha mask

    # 3. composite onto pure white, then flatten to grayscale
    white_bg = Image.new("RGBA", boosted.size, (255, 255, 255, 255))
    flat = Image.alpha_composite(white_bg, boosted).convert("L")
    return flat


def main():
    if len(sys.argv) < 2:
        print("usage: python scripts/prep_photo.py <source-photo>", file=sys.stderr)
        sys.exit(1)

    src_path = Path(sys.argv[1])
    if not src_path.is_absolute():
        src_path = ROOT / src_path

    result = prep(src_path)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result.save(OUT_PATH)
    print(f"wrote {OUT_PATH} ({result.size[0]}x{result.size[1]})")


if __name__ == "__main__":
    main()
