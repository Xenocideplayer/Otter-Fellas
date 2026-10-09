"""Draws every image the Otters mod ships: portraits, faction logo, new-game art, building and status icons,
and the Workshop thumbnail. Run: python3 make_art.py <mod version folder> <mod root folder>
All art is vector (SVG) rendered with cairosvg, so it can be tweaked here and re-rendered."""
import json
import shutil
import os
import sys

import cairosvg

OUT = sys.argv[1] if len(sys.argv) > 1 else "out"
ROOT = sys.argv[2] if len(sys.argv) > 2 else OUT
PORTRAITS = sys.argv[3] if len(sys.argv) > 3 else None  # 3D renders of the otter model, used when present

# Palette
FUR = "#6e4a30"
FUR_DARK = "#4e3220"
FUR_LIGHT = "#8a5f3e"
CREAM = "#e8d2ab"
CREAM_SHADE = "#cfb489"
NOSE = "#24160e"
LINE = "#26170d"
WATER = "#4fa3c7"
WATER_DARK = "#2d7397"
ICON_TAN = "#d8bf8f"
ICON_LINE = "#3a2a1a"
CONTAM = "#7db03a"


def render(svg, path, width, height, sprite=True):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=path, output_width=width, output_height=height)
    if sprite:
        with open(path + ".meta.json", "w") as f:
            json.dump({"isSprite": True}, f, indent=2)


def head(cx, cy, s, fur=FUR, fur_dark=FUR_DARK, cream=CREAM, eye_r=5.0, contaminated=False, pup=False):
    """An otter head drawn around (cx, cy) at scale s (1.0 = 128 px portrait)."""
    def p(x, y):
        return f"{cx + x * s:.1f},{cy + y * s:.1f}"

    def n(v):
        return f"{v * s:.2f}"

    sw = n(3.0)
    out = []
    # ears (behind head)
    for ex in (-33, 33):
        out.append(f'<circle cx="{cx + ex * s:.1f}" cy="{cy - 14 * s:.1f}" r="{n(9)}" fill="{fur_dark}" stroke="{LINE}" stroke-width="{sw}"/>')
        out.append(f'<circle cx="{cx + ex * s:.1f}" cy="{cy - 14 * s:.1f}" r="{n(4.5)}" fill="{NOSE}" opacity="0.55"/>')
    # skull: broad and flat on top, wider at the cheeks
    out.append(
        f'<path d="M {p(-38, 6)} C {p(-40, -22)} {p(-22, -36)} {p(0, -36)} C {p(22, -36)} {p(40, -22)} {p(38, 6)} '
        f'C {p(37, 26)} {p(20, 36)} {p(0, 36)} C {p(-20, 36)} {p(-37, 26)} {p(-38, 6)} Z" '
        f'fill="{fur}" stroke="{LINE}" stroke-width="{sw}"/>')
    # darker crown
    out.append(
        f'<path d="M {p(-30, -14)} C {p(-24, -30)} {p(24, -30)} {p(30, -14)} C {p(16, -22)} {p(-16, -22)} {p(-30, -14)} Z" '
        f'fill="{fur_dark}" opacity="0.55"/>')
    # pale muzzle with puffy whisker pads
    out.append(
        f'<path d="M {p(-27, 14)} C {p(-27, 0)} {p(-12, -4)} {p(0, -2)} C {p(12, -4)} {p(27, 0)} {p(27, 14)} '
        f'C {p(27, 30)} {p(12, 35)} {p(0, 34)} C {p(-12, 35)} {p(-27, 30)} {p(-27, 14)} Z" '
        f'fill="{cream}" stroke="{LINE}" stroke-width="{n(2.2)}"/>')
    out.append(f'<ellipse cx="{cx - 11 * s:.1f}" cy="{cy + 16 * s:.1f}" rx="{n(11)}" ry="{n(9)}" fill="{cream}"/>')
    out.append(f'<ellipse cx="{cx + 11 * s:.1f}" cy="{cy + 16 * s:.1f}" rx="{n(11)}" ry="{n(9)}" fill="{cream}"/>')
    # whisker dots
    for wx, wy in ((-15, 15), (-10, 19), (-17, 21), (15, 15), (10, 19), (17, 21)):
        out.append(f'<circle cx="{cx + wx * s:.1f}" cy="{cy + wy * s:.1f}" r="{n(1.1)}" fill="{CREAM_SHADE}"/>')
    # whiskers
    for side in (-1, 1):
        for i, (dy, ex, ey) in enumerate(((14, 46, 8), (18, 48, 18), (22, 44, 28))):
            out.append(
                f'<path d="M {p(side * 18, dy)} Q {p(side * 34, dy - 2 + i)} {p(side * ex, ey)}" fill="none" '
                f'stroke="#f6ead2" stroke-width="{n(1.3)}" stroke-linecap="round" opacity="0.9"/>')
    # broad nose
    out.append(
        f'<path d="M {p(-9, 3)} C {p(-9, -2)} {p(9, -2)} {p(9, 3)} C {p(9, 8)} {p(3, 11)} {p(0, 11)} '
        f'C {p(-3, 11)} {p(-9, 8)} {p(-9, 3)} Z" fill="{NOSE}"/>')
    out.append(f'<ellipse cx="{cx - 3 * s:.1f}" cy="{cy + 2 * s:.1f}" rx="{n(2.6)}" ry="{n(1.4)}" fill="#ffffff" opacity="0.35"/>')
    # mouth
    out.append(
        f'<path d="M {p(0, 11)} L {p(0, 16)} M {p(-6, 19)} Q {p(0, 23)} {p(6, 19)}" fill="none" stroke="{LINE}" '
        f'stroke-width="{n(1.8)}" stroke-linecap="round"/>')
    # eyes
    er = eye_r * (1.25 if pup else 1.0)
    for ex in (-18, 18):
        out.append(f'<circle cx="{cx + ex * s:.1f}" cy="{cy - 6 * s:.1f}" r="{n(er)}" fill="{NOSE}"/>')
        out.append(f'<circle cx="{cx + (ex - 1.6) * s:.1f}" cy="{cy - 8 * s:.1f}" r="{n(er * 0.38)}" fill="#ffffff"/>')
    if contaminated:
        # badwater sickness: green blotches and a drip
        for bx, by, br in ((-24, -16, 6), (21, -20, 4.5), (28, 10, 5), (-30, 12, 4)):
            out.append(f'<circle cx="{cx + bx * s:.1f}" cy="{cy + by * s:.1f}" r="{n(br)}" fill="{CONTAM}" opacity="0.85"/>')
        out.append(
            f'<path d="M {p(-26, 20)} q {n(2)} {n(6)} 0 {n(10)} q {-2 * s:.2f} {-4 * s:.2f} 0 {-10 * s:.2f} Z" fill="{CONTAM}"/>')
    return "\n".join(out)


def shoulders(cx, base, s, fur=FUR, cream=CREAM):
    return (
        f'<path d="M {cx - 50 * s:.1f},{base:.1f} C {cx - 48 * s:.1f},{base - 30 * s:.1f} {cx - 30 * s:.1f},{base - 40 * s:.1f} {cx:.1f},{base - 40 * s:.1f} '
        f'C {cx + 30 * s:.1f},{base - 40 * s:.1f} {cx + 48 * s:.1f},{base - 30 * s:.1f} {cx + 50 * s:.1f},{base:.1f} Z" fill="{fur}" stroke="{LINE}" stroke-width="{3 * s:.2f}"/>'
        f'<path d="M {cx - 20 * s:.1f},{base:.1f} C {cx - 20 * s:.1f},{base - 22 * s:.1f} {cx + 20 * s:.1f},{base - 22 * s:.1f} {cx + 20 * s:.1f},{base:.1f} Z" fill="{cream}"/>')


def svg(w, h, body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{body}</svg>'


def portrait(contaminated=False, pup=False):
    s = 0.9 if pup else 1.0
    fur = "#80583a" if pup else FUR
    body = shoulders(64, 128, 1.0 if not pup else 0.85, fur=fur)
    body += head(64, 62 if not pup else 70, s, fur=fur, contaminated=contaminated, pup=pup)
    return svg(128, 128, body)


def logo():
    # Otter head over two waves, in the game's tan icon colour.
    b = [f'<circle cx="64" cy="64" r="58" fill="none" stroke="{ICON_TAN}" stroke-width="6"/>']
    b.append(f'<g transform="translate(64,54) scale(0.78)">')
    b.append(f'<circle cx="-33" cy="-14" r="9" fill="{ICON_TAN}"/><circle cx="33" cy="-14" r="9" fill="{ICON_TAN}"/>')
    b.append(f'<path d="M -38 6 C -40 -22 -22 -36 0 -36 C 22 -36 40 -22 38 6 C 37 26 20 36 0 36 C -20 36 -37 26 -38 6 Z" fill="{ICON_TAN}"/>')
    b.append(f'<path d="M -9 3 C -9 -2 9 -2 9 3 C 9 8 3 11 0 11 C -3 11 -9 8 -9 3 Z" fill="{ICON_LINE}"/>')
    b.append(f'<circle cx="-18" cy="-6" r="5" fill="{ICON_LINE}"/><circle cx="18" cy="-6" r="5" fill="{ICON_LINE}"/>')
    b.append(f'<path d="M 0 11 L 0 16 M -6 19 Q 0 23 6 19" fill="none" stroke="{ICON_LINE}" stroke-width="2.5" stroke-linecap="round"/>')
    for side in (-1, 1):
        b.append(f'<path d="M {side*18} 16 L {side*42} 10 M {side*18} 20 L {side*44} 22" stroke="{ICON_LINE}" stroke-width="2" stroke-linecap="round"/>')
    b.append('</g>')
    for i, y in enumerate((92, 106)):
        b.append(f'<path d="M 26 {y} q 9 -7 18 0 t 18 0 t 18 0 t 18 0 t 4 0" fill="none" stroke="{ICON_TAN}" stroke-width="5.5" stroke-linecap="round"/>')
    return svg(128, 128, "".join(b))


def full_avatar():
    W, H = 420, 560
    b = []
    # water at the feet
    b.append(f'<ellipse cx="210" cy="512" rx="190" ry="40" fill="{WATER}" opacity="0.55"/>')
    b.append(f'<ellipse cx="210" cy="512" rx="140" ry="26" fill="{WATER_DARK}" opacity="0.35"/>')
    # long tapered tail sweeping behind
    b.append(f'<path d="M 262 430 C 318 446 366 474 396 522 C 398 528 392 532 386 528 C 352 506 312 492 262 482 Z" '
             f'fill="{FUR_DARK}" stroke="{LINE}" stroke-width="5" stroke-linejoin="round"/>')
    # body
    b.append(f'<path d="M 128 470 C 104 380 118 270 160 232 C 190 205 232 205 262 232 C 304 270 318 380 292 470 '
             f'C 270 506 150 506 128 470 Z" fill="{FUR}" stroke="{LINE}" stroke-width="5"/>')
    # belly
    b.append(f'<path d="M 164 462 C 148 390 158 300 182 262 C 198 244 222 244 238 262 C 262 300 272 390 256 462 '
             f'C 236 486 184 486 164 462 Z" fill="{CREAM}" opacity="0.95"/>')
    # feet
    for fx in (172, 248):
        b.append(f'<ellipse cx="{fx}" cy="496" rx="34" ry="14" fill="{FUR_DARK}" stroke="{LINE}" stroke-width="4"/>')
        for t in (-18, -6, 6, 18):
            b.append(f'<path d="M {fx + t} 490 L {fx + t} 504" stroke="{LINE}" stroke-width="2" opacity="0.6"/>')
    # cattail reed, held out to the side
    b.append(f'<path d="M 338 128 C 334 240 330 360 326 490" fill="none" stroke="#6f8a3a" stroke-width="7" stroke-linecap="round"/>')
    b.append(f'<path d="M 337 66 L 339 40" stroke="#6f8a3a" stroke-width="4" stroke-linecap="round"/>')
    b.append(f'<rect x="324" y="62" width="28" height="80" rx="14" fill="#7a4a24" stroke="{LINE}" stroke-width="4"/>')
    b.append(f'<path d="M 330 380 C 354 396 372 430 368 452" fill="none" stroke="#7d9a44" stroke-width="5" stroke-linecap="round"/>')
    # right arm reaching to the reed
    b.append(f'<path d="M 258 262 C 284 268 306 270 324 268 C 340 266 342 290 326 292 C 300 296 276 294 252 290 Z" '
             f'fill="{FUR_LIGHT}" stroke="{LINE}" stroke-width="4" stroke-linejoin="round"/>')
    b.append(f'<ellipse cx="334" cy="280" rx="14" ry="16" fill="{FUR_DARK}" stroke="{LINE}" stroke-width="4"/>')
    # left arm, paw resting on the belly
    b.append(f'<path d="M 164 256 C 150 286 156 318 182 334 C 196 342 210 332 202 320 C 186 308 180 286 186 262 Z" '
             f'fill="{FUR_LIGHT}" stroke="{LINE}" stroke-width="4" stroke-linejoin="round"/>')
    b.append(f'<ellipse cx="200" cy="328" rx="13" ry="11" fill="{FUR_DARK}" stroke="{LINE}" stroke-width="4"/>')
    # head
    b.append(head(210, 160, 2.45))
    # wet sheen and drips
    b.append(f'<path d="M 176 262 C 168 300 168 340 174 380" fill="none" stroke="#ffffff" stroke-width="5" opacity="0.18" stroke-linecap="round"/>')
    for dx, dy in ((112, 250), (300, 330), (120, 360)):
        b.append(f'<path d="M {dx} {dy} q 6 10 0 16 q -6 -6 0 -16 Z" fill="{WATER}" opacity="0.8"/>')
    return svg(W, H, "".join(b))


def icon(body):
    # Game icons are a tan silhouette with a soft dark edge.
    return svg(112, 112,
               '<defs><filter id="sh" x="-20%" y="-20%" width="140%" height="140%">'
               '<feDropShadow dx="0" dy="1.5" stdDeviation="1.6" flood-color="#000000" flood-opacity="0.75"/></filter></defs>'
               f'<g filter="url(#sh)" fill="{ICON_TAN}" stroke="{ICON_TAN}">{body}</g>')


def dig_site_icon():
    return icon(
        # mound of dug earth
        '<path d="M 12 92 C 24 70 44 62 58 62 C 74 62 92 72 100 92 Z" stroke="none"/>'
        # hole cut into it
        f'<path d="M 34 92 C 40 80 70 80 76 92 Z" fill="{ICON_LINE}" stroke="none"/>'
        # shovel: handle, grip and blade
        '<path d="M 70 18 L 54 66" stroke-width="7" stroke-linecap="round" fill="none"/>'
        '<path d="M 62 12 L 82 18" stroke-width="7" stroke-linecap="round" fill="none"/>'
        '<path d="M 44 58 L 64 64 L 58 84 C 54 92 40 88 40 80 Z" stroke="none"/>'
        # down arrow
        '<path d="M 90 30 L 90 52" stroke-width="6" stroke-linecap="round" fill="none"/>'
        '<path d="M 80 46 L 90 58 L 100 46 Z" stroke="none"/>')


def reed_filter_icon():
    return icon(
        # droplet
        '<path d="M 50 14 C 62 34 78 52 78 70 C 78 88 64 100 50 100 C 36 100 22 88 22 70 C 22 52 38 34 50 14 Z" stroke="none"/>'
        # filter mesh inside the drop
        f'<g stroke="{ICON_LINE}" stroke-width="3.2" fill="none" stroke-linecap="round">'
        '<path d="M 34 64 L 66 64"/><path d="M 31 74 L 69 74"/><path d="M 34 84 L 66 84"/>'
        '<path d="M 42 58 L 42 92"/><path d="M 50 54 L 50 96"/><path d="M 58 58 L 58 92"/></g>'
        # cattail reeds beside it
        '<path d="M 92 104 C 90 80 90 56 94 36" stroke-width="3.5" fill="none" stroke-linecap="round"/>'
        '<rect x="88" y="34" width="11" height="26" rx="5.5" stroke="none"/>'
        '<path d="M 82 104 C 82 88 80 74 84 62" stroke-width="3" fill="none" stroke-linecap="round"/>')


def rinse_pod_icon():
    return icon(
        # tub
        '<path d="M 14 54 L 98 54 C 96 80 82 96 56 96 C 30 96 16 80 14 54 Z" stroke="none"/>'
        f'<path d="M 22 62 L 90 62" stroke="{ICON_LINE}" stroke-width="3" fill="none"/>'
        '<path d="M 30 96 L 26 106 M 82 96 L 86 106" stroke-width="6" stroke-linecap="round" fill="none"/>'
        # otter ears and head peeking over the rim
        '<path d="M 38 54 C 38 36 74 36 74 54 Z" stroke="none"/>'
        '<circle cx="40" cy="40" r="5" stroke="none"/><circle cx="72" cy="40" r="5" stroke="none"/>'
        f'<circle cx="49" cy="46" r="2.6" fill="{ICON_LINE}" stroke="none"/><circle cx="63" cy="46" r="2.6" fill="{ICON_LINE}" stroke="none"/>'
        # bubbles and a falling droplet
        '<circle cx="22" cy="40" r="5" fill="none" stroke-width="3"/><circle cx="90" cy="32" r="7" fill="none" stroke-width="3"/>'
        '<circle cx="84" cy="14" r="4" fill="none" stroke-width="3"/>'
        '<path d="M 56 6 C 60 14 64 18 64 23 C 64 28 60 31 56 31 C 52 31 48 28 48 23 C 48 18 52 14 56 6 Z" stroke="none"/>')


def dry_fur_status():
    # A cracked, empty water drop on an orange warning disc.
    return svg(128, 128,
               '<circle cx="64" cy="64" r="58" fill="#e08a2e" stroke="#3a2412" stroke-width="7"/>'
               '<path d="M 64 18 C 78 40 96 60 96 80 C 96 100 82 112 64 112 C 46 112 32 100 32 80 C 32 60 50 40 64 18 Z" '
               'fill="#fbe7c2" stroke="#3a2412" stroke-width="6"/>'
               '<path d="M 60 44 L 70 62 L 56 74 L 68 92 L 62 104" fill="none" stroke="#3a2412" stroke-width="6" '
               'stroke-linejoin="round" stroke-linecap="round"/>')


def thumbnail():
    W, H = 960, 540
    b = [f'<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#9fd3e6"/>'
         f'<stop offset="1" stop-color="#5aa7c9"/></linearGradient></defs>',
         f'<rect width="{W}" height="{H}" fill="url(#sky)"/>',
         f'<path d="M 0 360 C 160 330 320 390 480 360 C 640 330 800 390 960 360 L 960 540 L 0 540 Z" fill="{WATER_DARK}"/>',
         f'<path d="M 0 400 C 160 380 320 420 480 400 C 640 380 800 420 960 400 L 960 540 L 0 540 Z" fill="#245f7e" opacity="0.8"/>']
    # cattails on the bank
    for x in (52, 82, 112):
        b.append(f'<path d="M {x} 430 C {x - 4} 380 {x + 6} 320 {x + 2} 280" stroke="#56742c" stroke-width="7" fill="none"/>')
        b.append(f'<rect x="{x - 9}" y="262" width="20" height="64" rx="10" fill="#6e4422"/>')
    full = full_avatar().split(">", 1)[1].rsplit("</svg>", 1)[0]
    b.append(f'<g transform="translate(600,20) scale(0.92)">{full}</g>')
    b.append('<text x="70" y="150" font-family="DejaVu Sans, Arial, sans-serif" font-size="110" font-weight="bold" '
             'fill="#fff6e3" stroke="#2b1c12" stroke-width="7" paint-order="stroke">Otters</text>')
    b.append('<text x="76" y="215" font-family="DejaVu Sans, Arial, sans-serif" font-size="30" font-weight="bold" '
             'fill="#fff6e3" stroke="#2b1c12" stroke-width="3" paint-order="stroke">A water faction for Timberborn</text>')
    return svg(W, H, "".join(b))


def avatar(name, make_svg, w, h):
    path = os.path.join(OUT, "Sprites", "Avatars", name + ".png")
    src = os.path.join(PORTRAITS, name + ".png") if PORTRAITS else None
    if src and os.path.exists(src):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        shutil.copy(src, path)
        with open(path + ".meta.json", "w") as f:
            json.dump({"isSprite": True}, f, indent=2)
    else:
        render(make_svg(), path, w, h)


def save_icon(img, rel, root=None):
    path = os.path.join(root or OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    with open(path + ".meta.json", "w") as f:
        json.dump({"isSprite": True}, f, indent=2)


def main():
    import icons as I
    avatar("OttersAdult", portrait, 128, 128)
    avatar("OttersChild", lambda: portrait(pup=True), 128, 128)
    avatar("OttersContaminatedAdult", lambda: portrait(contaminated=True), 128, 128)
    avatar("OttersContaminatedChild", lambda: portrait(contaminated=True, pup=True), 128, 128)
    avatar("OttersFullNewGame", full_avatar, 420, 560)
    save_icon(I.shell_logo(), "Sprites/Avatars/OttersLogo.png")
    save_icon(I.status_icon(I.dry_fur_symbol(), 512), "Sprites/StatusIcons/OtterDryFur.png")
    b = I.line_icon
    save_icon(b(I.dig_site(), 112), "Buildings/Landscaping/OtterDigSite/OtterDigSiteIcon.png")
    save_icon(b(I.reed_filter(), 112), "Buildings/Water/ReedFilter/ReedFilterIcon.png")
    save_icon(b(I.rinse_pod(), 112), "Buildings/Wellbeing/RinsePod/RinsePodIcon.png")
    save_icon(b(I.river_holt(), 112), "Buildings/Housing/RiverHolt/RiverHoltIcon.png")
    save_icon(b(I.river_holt(True), 112), "Buildings/Housing/BigRiverHolt/BigRiverHoltIcon.png")
    save_icon(b(I.wild_rice_crop(), 112), "NaturalResources/Crops/WildRice/WildRiceIcon.png")
    save_icon(b(I.taro_crop(), 112), "NaturalResources/Crops/WaterTaro/WaterTaroIcon.png")
    g = lambda body: I.line_icon(body, 80, view=80, stroke=3.0)
    save_icon(g(I.wild_rice_good()), "Sprites/Goods/WildRiceIcon.png")
    save_icon(g(I.cooked_rice_good()), "Sprites/Goods/CookedWildRiceIcon.png")
    save_icon(g(I.taro_root_good()), "Sprites/Goods/TaroRootIcon.png")
    save_icon(g(I.roasted_taro_good()), "Sprites/Goods/RoastedTaroIcon.png")
    if not (PORTRAITS and os.path.exists(os.path.join(PORTRAITS, "..", "thumbnail.png"))):
        render(thumbnail(), os.path.join(ROOT, "thumbnail.png"), 960, 540, sprite=False)


if __name__ == "__main__":
    main()
