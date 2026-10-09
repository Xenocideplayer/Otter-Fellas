"""Faction art from the user's otter painting (art/user/otter_reference.png, black background).

usage: python3 from_painting.py <out dir>
Writes OttersFullNewGame.png (420x560, transparent), 512px portraits (adult, child, contaminated variants) on the
game's dark brushed frame, and OtterCutout.png (full-res cut-out, kept for other uses).
"""
import os
import sys

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)

src = np.asarray(Image.open(os.path.join(HERE, "user", "otter_reference.png")).convert("RGB")).astype(np.float32)
h, w = src.shape[:2]

# background = near-black pixels connected to the border
dark = src.max(-1) < 20
lab, _ = ndimage.label(dark)
border_labels = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
bg = np.isin(lab, border_labels[border_labels > 0])
fg = ~bg
fg = ndimage.binary_opening(fg, iterations=1)
fg = ndimage.binary_fill_holes(fg)
alpha = ndimage.gaussian_filter(fg.astype(np.float32), 1.2)
alpha = np.clip((alpha - 0.15) / 0.7, 0, 1)
# remove the dark fringe left from the black background on anti-aliased edges
edge = (alpha > 0) & (alpha < 1)
rgb = src.copy()
rgb[edge] = np.clip(rgb[edge] / np.maximum(alpha[edge, None], 0.35), 0, 255)
cut = Image.fromarray(np.dstack([rgb, alpha * 255]).astype(np.uint8), "RGBA")
cut.save(os.path.join(OUT, "OtterCutout.png"))
cut.resize((420, 560), Image.LANCZOS).save(os.path.join(OUT, "OttersFullNewGame.png"))


def brushed_frame(size, seed=3):
    rng = np.random.default_rng(seed)
    W, H = size
    y, x = np.mgrid[0:H, 0:W] / max(W, H)
    base = np.array([0.10, 0.20, 0.21]) * (1.15 - 0.6 * np.hypot(x - 0.45, y - 0.4))[..., None]
    n1 = ndimage.gaussian_filter(rng.random((H, W)), (1.2, 9)) - 0.5
    n2 = ndimage.gaussian_filter(rng.random((H, W)), (7, 1.5)) - 0.5
    col = base * (1 + 1.6 * n1[..., None] + 0.8 * n2[..., None])
    e = np.minimum.reduce([x, y, 1 - x, 1 - y]) * max(W, H)
    rough = (ndimage.gaussian_filter(rng.random((H, W)), (2, 12)) + ndimage.gaussian_filter(rng.random((H, W)), (12, 2))) * 45
    border = np.clip((e + rough - 52) / 6, 0, 1)
    return np.clip(col, 0, 1) * 255, border


def portrait(box, name, tint=None, seed=3, zoom=1.0):
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    half = (x1 - x0) / 2 / zoom
    crop = cut.crop((int(cx - half), int(cy - half), int(cx + half), int(cy + half))).resize((512, 512), Image.LANCZOS)
    a = np.asarray(crop).astype(np.float32)
    if tint is not None:
        # badwater contamination: sickly green cast and dark blotches
        rng = np.random.default_rng(seed)
        blot = ndimage.gaussian_filter(rng.random((512, 512)), 14)
        blot = np.clip((blot - 0.5) * 9, 0, 1)
        lum = a[..., :3].mean(-1, keepdims=True)
        a[..., :3] = a[..., :3] * 0.55 + lum * np.array(tint) * 0.45
        a[..., :3] *= (1 - 0.35 * blot[..., None])
    bgc, border = brushed_frame((512, 512), seed)
    al = a[..., 3:4] / 255
    rgb = a[..., :3] * al + bgc * (1 - al)
    rgb = rgb * border[..., None] + np.array([5, 6, 6]) * (1 - border[..., None])
    Image.fromarray(np.dstack([rgb, np.full((512, 512), 255)]).astype(np.uint8), "RGBA").save(os.path.join(OUT, name + ".png"))


HEAD = (318, 8, 878, 568)          # head and shoulders in the 1086x1448 painting
portrait(HEAD, "OttersAdult", seed=3)
portrait(HEAD, "OttersChild", seed=5, zoom=1.12)
portrait(HEAD, "OttersContaminatedAdult", tint=(0.55, 0.75, 0.35), seed=7)
portrait(HEAD, "OttersContaminatedChild", tint=(0.55, 0.75, 0.35), seed=9, zoom=1.12)
print("done")


def thumbnail(path):
    """960x540 Workshop thumbnail: the painted otter on a dark river-green backdrop with the title."""
    from PIL import ImageDraw, ImageFont
    W, H = 960, 540
    rng = np.random.default_rng(1)
    y, x = np.mgrid[0:H, 0:W] / W
    base = np.array([0.09, 0.19, 0.19]) * (1.25 - 0.7 * np.hypot(x - 0.35, y - 0.3))[..., None]
    n1 = ndimage.gaussian_filter(rng.random((H, W)), (1.5, 12)) - 0.5
    bgc = np.clip(base * (1 + 1.5 * n1[..., None]), 0, 1) * 255
    img = Image.fromarray(bgc.astype(np.uint8), "RGB").convert("RGBA")
    fig = cut.resize((int(1086 * 520 / 1448), 520), Image.LANCZOS)
    img.alpha_composite(fig, (40, 14))
    d = ImageDraw.Draw(img)
    try:
        big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 84)
        sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 25)
        small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 19)
    except OSError:
        big = sub = small = ImageFont.load_default()
    d.text((462, 160), "OTTERS", font=big, fill=(255, 246, 227), stroke_width=6, stroke_fill=(30, 20, 12))
    d.text((468, 262), "A water faction for Timberborn", font=sub, fill=(255, 236, 200), stroke_width=3, stroke_fill=(30, 20, 12))
    d.text((470, 304), "Clean water, warm dens, and a good swim.", font=small, fill=(200, 230, 228), stroke_width=2, stroke_fill=(20, 16, 10))
    img.convert("RGB").save(path, optimize=True)


thumbnail(os.path.join(OUT, "thumbnail.png"))
