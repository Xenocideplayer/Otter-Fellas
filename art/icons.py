"""Icons drawn in Timberborn's own UI style.

* Building / crop tool icons: 112 px, tan (#BBA16C) line art, ~3.4 px round strokes with a slight hand-drawn
  wobble, a soft dark halo.
* Good icons: 80 px, a lighter tan with a crisp dark drop shadow underneath, like the game's goods.
* Faction logo: 98 px, rounded diamond outline with a solid symbol inside, in the faction colour.
* Status icons: 512 px, orange ring around a dark red disc with a tan symbol.
"""
import io

import cairosvg
from PIL import Image, ImageFilter

TAN = "#BBA16C"
OTTER_TEAL = "#6FD6E4"


def _png(svg, w, h):
    return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), output_width=w, output_height=h))).convert("RGBA")


GOOD_TAN = "#CAAC6B"   # good icons are a shade lighter than building icons in the game


def _wobble(img, amount, seed):
    """Nudge the drawing by a smooth random displacement so lines look drawn by hand, as the game's icons are."""
    import numpy as np
    from scipy import ndimage
    rng = np.random.default_rng(seed)
    w, h = img.size
    fields = []
    for _ in range(2):
        coarse = rng.normal(0, 1, (6, 6))
        f = ndimage.zoom(coarse, (h / 6, w / 6), order=3)[:h, :w]
        fields.append(f / (np.abs(f).max() + 1e-9) * amount)
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    src = np.asarray(img).astype(float)
    out = np.stack([ndimage.map_coordinates(src[..., c], [yy + fields[0], xx + fields[1]], order=1, mode="constant")
                    for c in range(4)], -1)
    return Image.fromarray(np.clip(out, 0, 255).astype("uint8"), "RGBA")


def _fit(body, view, stroke, fill):
    """Scale and centre a drawing so it fills about `fill` of the icon, as the game's icons do (theirs run nearly
    edge to edge; ours were drawn at many different sizes)."""
    probe = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {view} {view}" width="{view * 2}" height="{view * 2}">'
             f'<g fill="none" stroke="#000" stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round">'
             f'{body}</g></svg>').replace("FILL", "#000")
    box = _png(probe, view * 2, view * 2).split()[3].getbbox()
    if not box:
        return body
    x0, y0, x1, y1 = (v / 2 for v in box)
    s = min(fill * view / max(x1 - x0, y1 - y0), 1.5)
    if abs(s - 1) < 0.04 and abs((x0 + x1) / 2 - view / 2) < 2 and abs((y0 + y1) / 2 - view / 2) < 2:
        return body
    tx = view / 2 - s * (x0 + x1) / 2
    ty = view / 2 - s * (y0 + y1) / 2
    return f'<g transform="translate({tx:.2f} {ty:.2f}) scale({s:.4f})" stroke-width="{stroke / s:.3f}">{body}</g>'


def line_icon(body, size, view=112, stroke=3.4, shadow=True, good=None):
    """Tan line art like the game's icons. Building/crop icons (112) get the game's soft dark halo; good icons (80)
    are a lighter tan with the crisp dark drop shadow under them that the game's goods have."""
    good = (view == 80) if good is None else good
    color = GOOD_TAN if good else TAN
    body = _fit(body, view, stroke, 0.78 if good else 0.8)
    k = 4                                                  # draw big, wobble, then scale down (smooth edges)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {view} {view}" width="{size * k}" height="{size * k}">'
           f'<g fill="none" stroke="{color}" stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round">'
           f'{body}</g></svg>').replace("FILL", color)
    big = _png(svg, size * k, size * k)
    big = _wobble(big, 0.55 * k * size / view, seed=sum(map(ord, body)) % 100000)
    img = big.resize((size, size), Image.LANCZOS)
    if not shadow:
        return img
    a = img.split()[3]
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    if good:
        sh = Image.new("RGBA", img.size, (12, 10, 6, 0))
        sh.putalpha(a.filter(ImageFilter.GaussianBlur(size / 200)))
        out.alpha_composite(sh, (max(0, round(size / 160)), max(1, round(size / 32))))
    else:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        sh.putalpha(a.filter(ImageFilter.GaussianBlur(size / 50)).point(lambda v: int(min(255, v * 0.75))))
        out.alpha_composite(sh, (0, max(1, round(size / 110))))
    out.alpha_composite(img)
    return out



# ------------------------------------------------------------------------------------------------ drawing helpers
# The drawings follow the game's own icons: buildings are small scenes standing on a ground strip (hatched "////"
# like the Water Pump's, or rows of water waves like the Aquatic Farmhouse's), with doors, drops and holes as solid
# accents and a few interior strokes for planks, thatch and logs; plants grow out of the water with veined leaves;
# goods are outlines with interior detail (scales, ribs, grains, char marks) and steam on cooked food. Building
# drawings sit in about an 11..101 box of the 112 grid and goods in about 9..71 of the 80 grid, so _fit barely
# rescales them and the line weights stay as drawn. "FILL" is replaced with the line colour for solid parts.
import math
import re

STROKE = 3.4            # main line in the 112 box
THIN = 2.6              # interior detail lines
GOOD_STROKE = 4.0       # main line of the 80 px goods (the game's goods have a heavier line)
GOOD_THIN = 3.0
CUT = "#5C0F0B"         # status symbols: detail cut out of the tan symbol in the disc colour


def thin(d, w=THIN):
    return f'<path d="{d}" stroke-width="{w}"/>'


def solid(d):
    return f'<path d="{d}" fill="FILL"/>'


def dots(pts, r=1.8):
    return "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="FILL" stroke="none"/>' for x, y in pts)


def good(body):
    """Goods get the game's heavier line."""
    return f'<g stroke-width="{GOOD_STROKE}">{body}</g>'


def grp(x, y, s, body, base=STROKE, rot=0, flip=False):
    """Place a drawing made around (0, 0) at (x, y), scaled by s (mirrored if flip, turned by rot degrees),
    keeping every line its drawn thickness."""
    body = re.sub(r'stroke-width="([\d.]+)"', lambda m: f'stroke-width="{float(m.group(1)) / s:.2f}"', body)
    return (f'<g transform="translate({x} {y}) rotate({rot}) scale({-s if flip else s} {s})" '
            f'stroke-width="{base / s:.2f}">{body}</g>')


def hatch(inside, x0, y0, x1, y1, step=9.0, slope=1.15, w=None, minlen=3.0):
    """The game's "////" ground hatching over a box, kept only where inside(x, y) holds."""
    n = math.hypot(1, slope)
    dx, dy = 1 / n, -slope / n
    length = (y1 - y0) / -dy
    segs = []
    c = x0 - (y1 - y0) / slope
    while c < x1:
        run = prev = None
        t = 0.0
        while t <= length:
            x, y = c + dx * t, y1 + dy * t
            ok = x0 <= x <= x1 and inside(x, y)
            if ok and run is None:
                run = (x, y)
            elif not ok and run is not None:
                segs.append((run, prev))
                run = None
            prev = (x, y)
            t += 0.35
        if run is not None:
            segs.append((run, prev))
        c += step
    d = "".join(f"M{a[0]:.1f} {a[1]:.1f}L{b[0]:.1f} {b[1]:.1f}" for a, b in segs if math.dist(a, b) >= minlen)
    return f'<path d="{d}"' + (f' stroke-width="{w}"' if w else "") + "/>"


def ground(x0, x1, y, h=8.0, step=8.0, inside=None):
    """A ground line with a strip of short diagonal strokes under it, like the Water Pump's base."""
    return (f'<path d="M{x0} {y} H{x1}"/>'
            + hatch(inside or (lambda x, yy: True), x0 + 1, y + 4.5, x1 - 1, y + 4.5 + h, step))


def swoosh(x0, x1, y, t=2.4):
    """The tapered brush-stroke ground line under the Lodge / Terrain Block icons."""
    m = (x0 + x1) / 2
    return f'<path d="M{x0} {y} Q{m} {y - t * 1.6} {x1} {y} Q{m} {y + t * 1.6} {x0} {y} z" fill="FILL" stroke-width="1.6"/>'


def waves(x0, x1, y, h=13.0, a=6.0, w=None, phase=0):
    """One row of the game's water waves (Aquatic Farmhouse, Cattail): half-waves h long, a high."""
    n = max(1, int(round((x1 - x0) / h)))
    h = (x1 - x0) / n
    d = f"M{x0} {y}" + "".join(f" q{h / 2:.2f} {(-a if (k + phase) % 2 == 0 else a):.2f} {h:.2f} 0" for k in range(n))
    return f'<path d="{d}"' + (f' stroke-width="{w}"' if w else "") + "/>"


def water(x0, x1, y, gap=10.0, rows=2, h=13.0, a=6.0, w=None):
    """Rows of waves, each row shifted half a wave and a little shorter, like the game's."""
    return "".join(waves(x0 + r * h / 2, x1 - (r * h / 2 if r % 2 else 0), y + r * gap, h, a, w, phase=0) for r in range(rows))


def ripples(x0, x1, y, rows=2, gap=7.0):
    """The Water Pump's small "~~" waves beside its ground strip."""
    return water(x0, x1, y, gap, rows, h=5.5, a=4.5, w=THIN)


def drop(x, y, r):
    """A solid water drop, its round bottom centred at (x, y)."""
    t = y - 2.3 * r
    return solid(f"M{x} {t:.1f} Q{x + r * 1.15:.1f} {y - 0.9 * r:.1f} {x + r} {y} A{r} {r} 0 0 1 {x - r} {y} "
                 f"Q{x - r * 1.15:.1f} {y - 0.9 * r:.1f} {x} {t:.1f} z")


def steam(x, y, n=3, gap=9, h=16, w=THIN):
    out = ""
    for i in range(n):
        xx = x + i * gap
        out += f"M{xx} {y} q-3.5 {-h / 4} 0 {-h / 2} q3.5 {-h / 4} 0 {-h / 2}"
    return thin(out, w)


def cattail(x, base, top, lean=0.0, w=THIN):
    """A cattail: stem out of the water, solid seed head, a spike above it (the game's Cattail icon)."""
    hx = x + lean
    return (thin(f"M{x} {base} Q{x + lean * 0.2:.1f} {(base + top) / 2 + 8:.1f} {hx} {top + 15}", w)
            + f'<rect x="{hx - 3.3}" y="{top}" width="6.6" height="16" rx="3.3" fill="FILL" stroke-width="1.4"/>'
            + thin(f"M{hx} {top} v-6", 2.2))


def reed(x, base, dx, dy, w=THIN):
    """A reed leaf curving out of the water."""
    return thin(f"M{x} {base} q{dx * 0.15:.1f} {-dy * 0.7:.1f} {dx} {-dy}", w)


def splash_tuft(x, y, s=1.0):
    """The solid spiky splash at the foot of the game's Cattail icon."""
    return grp(x, y, s, solid("M-13 0 L-10 -5 L-7 -2.5 L-5 -10 L-2 -3.5 L1 -12 L3.5 -3.5 L7 -9 L8 -2.5 L12 -5 L13 0 z")
               + '<path d="M-13 0 H13" stroke-width="2"/>')


def splash(x, y, s=1.0):
    """Water thrown up where something lands in it: a little mound, two curls of spray and drops flying off them."""
    d = lambda px, py, r: (f'<path transform="rotate({r} {px} {py})" d="M{px} {py - 5} Q{px + 2.8} {py - 1.8} {px + 2.5} {py} '
                           f'A2.5 2.5 0 0 1 {px - 2.5} {py} Q{px - 2.8} {py - 1.8} {px} {py - 5} z" fill="FILL" stroke-width="1"/>')
    return grp(x, y, s, solid("M-11 0 Q-5 -7 0 -7 Q5 -7 11 0 z")
               + '<path d="M-6 -5 Q-9 -16 -18 -18 M6 -5 Q9 -16 18 -18" stroke-width="3"/>'
               + d(-23, -21, -50) + d(23, -21, 50) + d(-5, -19, -10) + d(5, -21, 15))


def arrow(x, y, s=1.0, down=False):
    """The game's solid upgrade arrow."""
    return grp(x, y, s, solid("M-4 6 V0 H-9 L0 -9 L9 0 H4 V6 z"), rot=180 if down else 0)


def flag(x, y, h=20, w=13):
    return f'<path d="M{x} {y} v{-h}"/>' + solid(f"M{x} {y - h} l{w} 4 l{-w} 5 z")


def lantern(x, y, s=1.0):
    """A little hanging lantern: hook, solid cap, glass with a solid flame."""
    return grp(x, y, s, '<path d="M0 0 v4" stroke-width="2"/>' + solid("M-5 8 L0 3 L5 8 z")
               + '<rect x="-4" y="8" width="8" height="10" rx="1.5" stroke-width="2.4"/>'
               + solid("M0 10 q2.2 3 0 6 q-2.2 -3 0 -6 z"))


def deck(x0, x1, y, h=6.0, seam=12.0, posts=(), post_to=None):
    """A plank deck seen edge-on: a slab with board ends, standing on posts."""
    xs = []
    x = x0 + seam
    while x < x1 - 3:
        xs.append(x)
        x += seam
    return (f'<path d="M{x0} {y} H{x1} V{y + h} H{x0} z"/>'
            + (thin("".join(f"M{v:.1f} {y} V{y + h}" for v in xs), 2.2) if xs else "")
            + ("".join(f'<path d="M{p} {y + h} V{post_to}"/>' for p in posts) if posts else ""))


def log(x0, y0, x1, y1, w=8.0, ring=True):
    """A log from (x0, y0) to (x1, y1): two sides, a rounded far end and a cut face with its heart at the near end."""
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -uy, ux
    h = w / 2
    a = math.degrees(math.atan2(uy, ux))
    return (f'<path d="M{x1 + nx * h:.1f} {y1 + ny * h:.1f} L{x0 + nx * h:.1f} {y0 + ny * h:.1f} '
            f'A{h * 0.6:.1f} {h:.1f} {a:.1f} 0 1 {x0 - nx * h:.1f} {y0 - ny * h:.1f} L{x1 - nx * h:.1f} {y1 - ny * h:.1f}"/>'
            + f'<ellipse cx="{x1:.1f}" cy="{y1:.1f}" rx="{h * 0.6:.1f}" ry="{h:.1f}" transform="rotate({a:.1f} {x1:.1f} {y1:.1f})"/>'
            + (dots(((round(x1, 1), round(y1, 1)),), max(1.2, h * 0.28)) if ring else ""))


def ell(cx, cy, rx, ry, m=0.0):
    """inside-test for an ellipse grown by margin m"""
    return lambda x, y: ((x - cx) / (rx + m)) ** 2 + ((y - cy) / (ry + m)) ** 2 < 1


def box(x0, y0, x1, y1, m=0.0):
    return lambda x, y: x0 - m <= x <= x1 + m and y0 - m <= y <= y1 + m


def _arch(cx, base, w, top):
    hw = w / 2
    return f"M{cx - hw} {base} V{top + hw} Q{cx - hw} {top} {cx} {top} Q{cx + hw} {top} {cx + hw} {top + hw} V{base}"


def door(cx, base, w, h):
    """A solid arched doorway."""
    return solid(_arch(cx, base, w, base - h) + " z")


# ---- otter things
def fish_body(scales=True, fill=False, gill=True):
    """A side-on fish around (0, 0), nose to the right, about 42 long and 22 tall."""
    f = ' fill="FILL"' if fill else ""
    out = (f'<path d="M-14 0 Q-4 -12.5 9 -9.5 Q17 -6.5 21 0 Q17 6.5 9 9.5 Q-4 12.5 -14 0 z"{f}/>'
           f'<path d="M-14 0 L-22 -9 Q-18.5 0 -22 9 z"{f}/>'
           '<path d="M-5 -9.5 Q0 -15.5 7 -10" stroke-width="2.4"/>')
    if not fill:
        out += dots(((14.5, -2.2),), 1.7)
        if gill:
            out += '<path d="M9.5 -7.5 Q5.5 0 9.5 7.5" stroke-width="2.2"/>'
        if scales:
            out += ('<path d="M-6 -4 q3 4 0 8 M0 -6 q3 4 0 8 M0 2 q3 4 0 6 M-6 4 q2 2 0 4" stroke-width="2"/>')
    return out


def fish(x, y, s=1.0, a=0, base=STROKE, **kw):
    return grp(x, y, s, fish_body(**kw), base=base, rot=a)


def scallop_body(ribs=True, fill=False, n=6, R=20.0, meat=False, rib_color=None):
    """The otters' scallop shell (their badge) around (0, 0): a fanned, scalloped shell, hinge at the bottom with its
    two little ears, ribs running out from the hinge. About 44 wide, 32 tall."""
    hx, hy = 0.0, 11.0
    a0, a1 = math.radians(162), math.radians(18)
    angs = [a0 + (a1 - a0) * k / n for k in range(n + 1)]
    P = [(hx + R * math.cos(t), hy - R * math.sin(t)) for t in angs]
    d = f"M{hx} {hy} L{P[0][0]:.1f} {P[0][1]:.1f}"
    for k in range(n):
        tm = (angs[k] + angs[k + 1]) / 2
        d += f" Q{hx + R * 1.16 * math.cos(tm):.1f} {hy - R * 1.16 * math.sin(tm):.1f} {P[k + 1][0]:.1f} {P[k + 1][1]:.1f}"
    d += " z"
    f = ' fill="FILL"' if fill else ""
    out = f'<path d="{d}"{f}/>' + f'<path d="M-3 {hy} L-10 {hy - 1} L-9 {hy + 5} H9 L10 {hy - 1} L3 {hy} z"{f} stroke-width="2.4"/>'
    if meat:                                   # an opened shell: the meat sits in the middle, ribs show round it
        out += f'<ellipse cx="0" cy="{hy - R * 0.45:.1f}" rx="{R * 0.42:.1f}" ry="{R * 0.32:.1f}" fill="FILL"/>'
        out += '<path d="' + "".join(f"M{hx + R * 0.66 * math.cos(t):.1f} {hy - R * 0.66 * math.sin(t):.1f} "
                                     f"L{hx + R * 0.88 * math.cos(t):.1f} {hy - R * 0.88 * math.sin(t):.1f} "
                                     for t in angs[1:-1]) + '" stroke-width="2.4"/>'
    elif ribs and (rib_color or not fill):
        rc = f' stroke="{rib_color}"' if rib_color else ""
        out += f'<path{rc} d="' + "".join(f"M{hx + 4 * math.cos(t):.1f} {hy - 4 * math.sin(t):.1f} "
                                     f"L{hx + R * 0.86 * math.cos(t):.1f} {hy - R * 0.86 * math.sin(t):.1f} "
                                     for t in angs[1:-1]) + '" stroke-width="2.2"/>'
    return out


def scallop(x, y, s=1.0, a=0, base=STROKE, **kw):
    return grp(x, y, s, scallop_body(**kw), base=base, rot=a)


def otter_head(x, y, s=1.0):
    """An otter's head peeking up: broad flat crown, small ears low on the sides, dot eyes, a solid nose over a
    puffy muzzle, whiskers."""
    return grp(x, y, s, '<path d="M-15 12 Q-17 -7 0 -7 Q17 -7 15 12"/>'
               + solid("M-14.6 4 a3.4 3.4 0 1 1 1.2 -6.4 z") + solid("M14.6 4 a3.4 3.4 0 1 0 -1.2 -6.4 z")
               + dots(((-6, -1), (6, -1)), 2.1) + solid("M-4 3.5 Q0 2 4 3.5 Q2.4 7.5 0 7.5 Q-2.4 7.5 -4 3.5 z")
               + '<path d="M-9 8 q-6 -1 -10 -4 M-9 10 q-6 1 -10 1 M9 8 q6 -1 10 -4 M9 10 q6 1 10 1" stroke-width="1.8"/>')


# Kept for anything that imported it: the two plain rows of waves along the bottom of the 112 box.
WAVES = water(11, 101, 88)


# ------------------------------------------------------------------------------------------------ buildings
def reed_filter():
    # the Water Pump's domed tank, a solid drop on its front, its spout pouring into the river; cattails at the
    # intake behind, hatched bank under the tank and ripples under the spout
    return ('<path d="M15 50 Q17 30 37 28 Q57 30 59 50 Z"/>'
            '<rect x="30" y="20" width="14" height="8" rx="2"/>'
            + thin("M24 43 l3 -6 M33 40 l1 -6 M42 40 l-1 -6 M51 43 l-3 -6")
            + '<path d="M19 88 V50 M55 88 V50"/>' + thin("M19 80 H55")
            + drop(37, 68, 7)
            + '<path d="M55 56 H70 Q80 56 80 66 V72 M55 66 H66 Q70 66 70 70 V72"/>'
            + '<path d="M67 73 H83"/>'
            + thin("M73 78 V85 M77 78 V87")
            + cattail(88, 88, 26, 1.5) + cattail(97, 88, 36, 3) + reed(92, 88, -6, 30) + reed(94, 88, 10, 22)
            + ground(11, 62, 88) + ripples(66, 101, 91))


def dig_site():
    # a stepped pit dug into the river bank, a spade stuck in the heap of spoil, clods flying out of the pit
    pit = lambda x, y: (21 < x < 53 and y < 89.5) or (35 < x < 53 and y < 98)
    return ('<path d="M11 78 H22 V88 H36 V98 H52 V78 H57"/>'
            + hatch(lambda x, y: not pit(x, y), 12, 82.5, 100, 101)
            + '<path d="M56 78 Q62 54 79 53 Q96 55 101 78 H56"/>'
            + dots(((70, 70), (80, 64), (90, 70), (78, 74), (86, 60)), 2.0)
            + '<path d="M86 18 L76 50"/>' + '<path d="M80 15 L93 19"/>'
            + solid("M68 47 L83 52 L79 66 Q72 72 66 66 Z")
            + solid("M27 66 q4 -5 8 -1 q4 -2 5 2 q-1 4 -6 4 q-6 0 -7 -5 z")
            + solid("M40 50 q3 -4 7 -1 q1 4 -2 5 q-5 1 -5 -4 z")
            + dots(((22, 58), (32, 44), (48, 38), (52, 56), (18, 46)), 2.0)
            + cattail(14, 78, 46, -1) + reed(15, 78, 8, 18))


def rinse_pod():
    # a stave tub with an otter soaking in it, a shower rose overhead raining on it, bubbles drifting up
    return ('<path d="M16 58 H86"/>'
            '<path d="M21 58 Q19 76 24 90 M81 58 Q83 76 78 90"/>'
            + '<path d="M20.5 68 Q51 72 81.5 68 M21.5 82 Q51 86 80.5 82" stroke-width="3"/>'
            + thin("M36 58 V66 M66 58 V66 M51 72 V82 M36 72 V82 M66 72 V82 M44 86 V90 M58 86 V90", 2.2)
            + otter_head(51, 46, 1.0)
            + '<path d="M93 90 V12 H62 V17"/>' + solid("M53 17 H71 L67 23 H57 Z")
            + thin("M56 28 l-1 5 M62 28 v6 M68 28 l1 5", 2.4)
            + '<circle cx="15" cy="46" r="4" stroke-width="2.6"/><circle cx="21" cy="32" r="3" stroke-width="2.6"/>'
            + '<circle cx="13" cy="22" r="2.2" stroke-width="2.2"/>'
            + ground(11, 101, 90))


def river_holt(double=False):
    # a stick-built holt dome at the water's edge, its sticks crossing at the top like the Lodge's ridge, a solid
    # doorway onto the water, reeds beside it
    def dome(cx, w, top, base=76, door_w=18, sticks=True):
        l, r = cx - w / 2, cx + w / 2
        out = f'<path d="M{l} {base} Q{l + 2} {top + 2} {cx} {top} Q{r - 2} {top + 2} {r} {base}"/>'
        out += f'<path d="M{cx - 9} {top + 6} L{cx + 7} {top - 10} M{cx + 9} {top + 6} L{cx - 7} {top - 10}"/>'
        if sticks:
            k = w / 80
            out += thin(f"M{cx - 30 * k:.1f} {base - 22 * k:.1f} l{14 * k:.1f} -6 M{cx - 22 * k:.1f} {top + 18 * k:.1f} l{13 * k:.1f} -4 "
                        f"M{cx + 12 * k:.1f} {top + 14 * k:.1f} l{14 * k:.1f} 5 M{cx + 18 * k:.1f} {base - 24 * k:.1f} l{14 * k:.1f} 6 "
                        f"M{cx - 34 * k:.1f} {base - 8 * k:.1f} l{9 * k:.1f} -2 M{cx + 26 * k:.1f} {base - 8 * k:.1f} l{9 * k:.1f} 2")
        out += door(cx, base, door_w, door_w * 1.15)
        return out
    if not double:
        body = dome(56, 78, 28) + cattail(13, 76, 40, -1) + reed(14, 76, 7, 20)
    else:
        # a small holt behind a big one, joined by a plank walk
        body = ('<path d="M12 76 Q12 44 29 43 Q38 43 42 50"/>'
                + '<path d="M22 47 L34 36 M33 47 L23 36"/>'
                + thin("M16 64 l8 -3 M20 54 l7 -2")
                + door(28, 76, 13, 15)
                + dome(70, 62, 22, door_w=17))
    return body + '<path d="M11 76 H101"/>' + water(11, 101, 87)


def wild_rice_crop():
    # three wild rice stalks standing in the water, each topped by an ear of outlined grains like the game's Wheat,
    # long leaves, a splash at their foot
    def ear(x, y, a, n=4, s=1.0):
        out = f'<path d="M0 0 V{-n * 7 - 4}" stroke-width="2.4"/>'
        for k in range(n):
            yy = -k * 7 - 4
            for side in (-1, 1):
                out += (f'<ellipse cx="{side * 3.6}" cy="{yy - 3}" rx="2.3" ry="4.6" '
                        f'transform="rotate({side * 28} {side * 3.6} {yy - 3})" stroke-width="2.2"/>')
        out += f'<ellipse cx="0" cy="{-n * 7 - 6}" rx="2.2" ry="4.4" stroke-width="2.2"/>'
        return grp(x, y, s, out, rot=a)
    return ('<path d="M50 84 Q46 62 34 46 M56 84 Q56 60 57 40 M62 84 Q68 64 80 48"/>'
            + ear(34, 46, -32) + ear(57, 40, 0, 5) + ear(80, 48, 32)
            + reed(52, 84, -30, 18) + reed(53, 84, -18, 30) + reed(60, 84, 22, 32) + reed(61, 84, 32, 16)
            + splash_tuft(56, 84, 1.1)
            + water(11, 101, 88))


def taro_crop():
    # big veined, heart-shaped taro leaves on long stems standing up out of the water
    def leaf(x, y, s, a):
        return grp(x, y, s, '<path d="M0 0 Q-8 9 -18 5 Q-26 -4 -21 -17 Q-13 -32 0 -41 Q13 -32 21 -17 Q26 -4 18 5 Q8 9 0 0 z"/>'
                   + thin("M0 -2 V-34 M0 -10 Q-7 -13 -12 -20 M0 -10 Q7 -13 12 -20 M0 -21 Q-5 -24 -8 -29 "
                          "M0 -21 Q5 -24 8 -29 M0 -3 Q-7 -3 -13 -1 M0 -3 Q7 -3 13 -1", 2.4), rot=a)
    return ('<path d="M55 86 Q50 70 34 66 M57 86 Q62 70 78 66 M56 86 V42"/>'
            + leaf(56, 42, 0.9, 0) + leaf(34, 66, 0.72, -66) + leaf(78, 66, 0.72, 66)
            + splash_tuft(56, 86, 1.0)
            + water(11, 101, 89))


def fishing_dock():
    # a plank pier on posts with a little thatched hut, a rod bent out over the water and a fish on the line
    return (deck(11, 70, 62, 6, 11, posts=(16, 40, 64), post_to=84)
            + '<path d="M14 62 V43 M40 62 V43"/>' + '<path d="M9 45 L27 28 L45 45"/>'
            + thin("M27 33 L19 44 M27 33 L35 44 M27 33 V44")
            + door(27, 62, 10, 12)
            + '<path d="M58 60 L94 13"/>' + '<path d="M94 13 L93 50" stroke-width="1.8"/>'
            + fish(85, 63, 0.8, -60, scales=False)
            + splash(78, 86, 0.6)
            + water(11, 101, 88))


def artesian_well():
    # a braced drilling tower on the left; on the right the wellhead, a column of water bursting up out of it and
    # spraying down both sides; hatched ground under it all
    ly = lambda y: 16 + 12 * (88 - y) / 64
    ry = lambda y: 50 - 12 * (88 - y) / 64
    return ('<path d="M16 88 L28 24 M50 88 L38 24 M23 24 H43"/><path d="M28 24 V16 H38 V24"/>'
            + thin(f"M{ly(70):.1f} 70 L{ry(47):.1f} 47 M{ry(70):.1f} 70 L{ly(47):.1f} 47 M{ly(70):.1f} 70 H{ry(70):.1f} M{ly(47):.1f} 47 H{ry(47):.1f}")
            + '<path d="M50 72 H64" stroke-width="2.6"/>'
            + '<path d="M64 88 V76 H90 V88"/>' + thin("M64 82 H90")
            + '<path d="M71 76 V70 H83 V76"/>'
            + thin("M74 66 V36 M80 66 V36")
            + splash(77, 36, 0.85)
            + thin("M66 32 Q60 38 59 54 M88 32 Q94 38 95 54 M70 40 Q66 46 66 56 M84 40 Q88 46 88 56", 2.4)
            + thin("M56 62 l-2 3 M98 62 l2 3", 2.4)
            + ground(11, 101, 88))


def splash_pool():
    # a plank-sided pool on the bank, a diving board on the left, a splash thrown up out of it
    return ('<path d="M28 62 H100"/><path d="M32 62 V90 M96 62 V90"/>'
            + thin("M32 72 H96 M32 82 H96") + waves(36, 92, 58, 7, 4.5, THIN)
            + '<path d="M14 90 V52 M24 90 V52"/>' + thin("M14 62 H24 M14 72 H24 M14 82 H24")
            + '<path d="M10 50 H40 Q46 50 48 46" stroke-width="4.4"/>'
            + splash(66, 58, 1.1)
            + ground(11, 101, 90))


def water_tube():
    # a run of tube bending upwards, banded joints, a solid drop riding in it, a trestle under it on the ground
    return ('<path d="M11 56 H56 Q72 56 72 40 V12 M11 72 H56 Q88 72 88 40 V12"/>'
            + '<path d="M36 52 V76 M68 32 H92" stroke-width="4.4"/>'
            + drop(23, 68, 3.6)
            + '<path d="M50 72 V88 M64 69 V88"/>' + thin("M50 80 H64")
            + ground(11, 101, 88))


def tube_outlet():
    # a tube coming in over the bank and turning down into a spout, water pouring out of it into the river
    return ('<path d="M11 38 H62 Q78 38 78 54 V62 M11 54 H58 Q64 54 64 60 V62"/>'
            + '<path d="M60 63 H82"/>'
            + '<path d="M32 34 V58" stroke-width="4.4"/>'
            + drop(46, 50, 3.4)
            + '<path d="M22 54 V80"/>'
            + thin("M67 68 V86 M71 68 V88 M75 68 V86", 2.6)
            + dots(((62, 82), (82, 80), (60, 74), (86, 74)), 1.8)
            + ground(11, 50, 80) + water(50, 101, 90, 9, 2, 12, 5.5))


def smokehouse():
    # a thatched plank hut with a smoking chimney, fish hanging head-down on a drying rack beside it
    return ('<path d="M14 90 V54 M48 90 V54"/>' + '<path d="M9 56 L31 34 L53 56"/>'
            + thin("M31 39 L21 54 M31 39 L27 56 M31 39 L35 56 M31 39 L41 54")
            + '<path d="M41 42 V24 H49 V50"/>' + steam(40, 19, 2, 9, 13)
            + thin("M14 68 H22 M40 68 H48 M14 80 H22 M40 80 H48")
            + door(31, 90, 12, 18)
            + '<path d="M58 90 V40 M101 90 V40 M55 42 H101"/>'
            + fish(70, 62, 0.8, 90, scales=False, gill=False) + fish(89, 66, 0.8, 90, scales=False, gill=False)
            + thin("M70 42 V44 M89 42 V48", 2)
            + ground(11, 101, 90))


def otter_slide():
    # a ladder tower on the bank, a curving chute down into the river, a splash where it lands
    return ('<path d="M15 88 V34 M37 88 V34 M11 34 H41"/>' + '<path d="M11 34 L26 20 L41 34"/>'
            + thin("M15 46 H37 M15 58 H37 M15 70 H37 M15 82 H37")
            + '<path d="M41 34 Q62 36 70 58 Q78 80 98 82"/>'
            + '<path d="M41 44 Q56 46 63 64 Q70 86 88 88"/>'
            + thin("M50 37 L47 46 M62 47 L57 53 M68 62 L62 66 M74 74 L68 78 M84 80 L80 86", 2.2)
            + splash(95, 82, 0.9)
            + ground(11, 44, 88) + water(46, 101, 91, 9, 2, 11, 5))


def slipway():
    # a planked ramp running from the hatched bank down into the river, a splash at its foot
    slope = lambda x: 44 + (x - 30) * 42 / 56
    return ('<path d="M11 44 H30 L86 86"/>' + '<path d="M11 50 H28 L80 89"/>'
            + thin("".join(f"M{x:.1f} {slope(x):.1f} l-3 4.5 " for x in (38, 48, 58, 68, 78)), 2.4)
            + hatch(lambda x, y: y > slope(x) + 9 and y < 88 and x < 76, 12, 48, 80, 88)
            + '<path d="M11 50 V88 H56"/>'
            + splash(89, 86, 0.85)
            + water(58, 101, 90, 9, 2, 11, 5))


# ------------------------------------------------------------------------------------------------ plants & goods
def wild_rice_good():
    # a stalk of wild rice like the game's Wheat: outlined grains paired up the stem, each with its whisker, a leaf
    p0, c, p1 = (14, 74), (36, 52), (60, 12)
    at = lambda t: ((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t * t * p1[0],
                    (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t * t * p1[1])
    grains = ""
    for k, t in enumerate((0.42, 0.56, 0.70, 0.84)):
        (x, y), (x2, y2) = at(t), at(t + 0.01)
        ang = math.degrees(math.atan2(y2 - y, x2 - x)) + 90
        for side in (-1, 1):
            a = ang + side * 32
            ux, uy = math.sin(math.radians(a)), -math.cos(math.radians(a))
            cx, cy = x + ux * 7, y + uy * 7
            grains += (f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="3.2" ry="6.4" transform="rotate({a:.0f} {cx:.1f} {cy:.1f})" stroke-width="3"/>'
                       + thin(f"M{cx + ux * 6.5:.1f} {cy + uy * 6.5:.1f} l{ux * 5:.1f} {uy * 5:.1f}", 2.2))
    tip = at(1.0)
    return good(f'<path d="M{p0[0]} {p0[1]} Q{c[0]} {c[1]} {p1[0]} {p1[1]}"/>' + grains
                + f'<ellipse cx="{tip[0] + 2:.1f}" cy="{tip[1] - 4:.1f}" rx="3" ry="6" transform="rotate(35 {tip[0] + 2:.1f} {tip[1] - 4:.1f})" stroke-width="3"/>'
                + '<path d="M24 62 Q10 60 8 46 Q22 48 27 58"/>' + thin("M24 60 L14 50", 2.4))


def cooked_rice_good():
    # a bowl heaped with cooked rice, grains showing, a painted band on the bowl, steam rising
    grain = lambda x, y, a: f'<ellipse cx="{x}" cy="{y}" rx="1.8" ry="3.4" transform="rotate({a} {x} {y})" fill="FILL" stroke-width="1"/>'
    return good('<path d="M8 42 Q10 66 40 66 Q70 66 72 42 Z"/>'
                + '<path d="M15 42 Q14 32 23 31 Q27 23 36 25 Q42 19 50 25 Q60 23 61 31 Q68 32 65 42"/>'
                + grain(26, 37, 30) + grain(34, 32, -20) + grain(44, 34, 40) + grain(53, 36, -30) + grain(40, 39, 10)
                + thin("M15 52 Q40 58 65 52", GOOD_THIN)
                + '<path d="M32 66 L30 72 H50 L48 66"/>'
                + steam(30, 18, 3, 10, 14, GOOD_THIN))


CORM = "M0 -24 Q12 -22 18 -8 Q26 12 12 22 Q0 28 -12 22 Q-26 12 -18 -8 Q-12 -22 0 -24 Z"


def taro_root_good():
    # a taro corm, round below and tapering up, with its bark rings, a stalk with a veined heart leaf on top
    leaf = grp(56, 20, 0.5, '<path d="M0 0 Q-8 9 -18 5 Q-26 -4 -21 -17 Q-13 -32 0 -41 Q13 -32 21 -17 Q26 -4 18 5 Q8 9 0 0 z"/>'
               + thin("M0 -3 V-32 M0 -12 Q-7 -14 -12 -21 M0 -12 Q7 -14 12 -21", 2.4), base=GOOD_STROKE, rot=62)
    return good(grp(36, 50, 1.0, f'<path d="{CORM}"/>'
                    + thin("M-13 -12 Q0 -6 13 -12 M-20 2 Q0 9 20 2 M-19 14 Q0 21 19 14", GOOD_THIN)
                    + thin("M-8 -8 l-2 4 M8 -8 l-1 4 M-12 6 l-2 4 M2 8 l-1 4 M13 6 l-1 4", 2.2), base=GOOD_STROKE)
                + '<path d="M36 26 Q40 16 54 20"/>' + leaf)


def roasted_taro_good():
    # a roasted taro and a halved one showing its speckled flesh, char stripes on the skin, steam rising
    return good(grp(22, 52, 0.7, f'<path d="{CORM}"/>' + thin("M-16 -2 l10 10 M-10 -14 l16 16 M6 -16 l10 10", 3.6),
                    base=GOOD_STROKE, rot=-18)
                + grp(58, 50, 0.74, f'<path d="{CORM}"/>' + '<path d="M0 -17 Q8 -15 12 -5 Q18 9 8 16 Q0 20 -8 16 Q-18 9 -12 -5 Q-8 -15 0 -17 Z" stroke-width="2.6"/>'
                      + dots(((-4, -2), (4, 2), (-2, 8), (5, -8), (-6, 12)), 1.8), base=GOOD_STROKE, rot=14)
                + steam(28, 24, 3, 12, 15, GOOD_THIN))


def fish_good():
    return good(fish(41, 40, 1.5, -12, base=GOOD_STROKE))


def grilled_fish_good():
    # a grilled fish with dark char stripes across it, steam rising
    return good(fish(40, 52, 1.4, 0, base=GOOD_STROKE, scales=False)
                + thin("M24 44 l6 14 M33 42 l6 16 M42 42 l5 15", 3.6)
                + steam(28, 30, 3, 11, 16, GOOD_THIN))


def smoked_fish_good():
    # a split, smoked fish hanging by its tail on a string, its backbone and ribs showing, smoke curling past
    body = ('<path d="M-14 0 Q-4 -12.5 9 -9.5 Q17 -6.5 21 0 Q17 6.5 9 9.5 Q-4 12.5 -14 0 z"/>'
            '<path d="M-14 0 L-22 -9 Q-18.5 0 -22 9 z"/>'
            '<path d="M-10 0 H15 M-6 0 l-3 -6 M0 0 l-3 -7 M6 0 l-3 -6 M-6 0 l-3 6 M0 0 l-3 7 M6 0 l-3 6" stroke-width="2.2"/>'
            + dots(((15, -4),), 1.6))
    return good(grp(36, 46, 1.4, body, base=GOOD_STROKE, rot=-60)
                + thin("M21 72 Q18 68 22 66", GOOD_THIN) + thin("M14 69 l-6 6", GOOD_THIN)
                + steam(54, 30, 2, 10, 18, GOOD_THIN) + thin("M62 52 q-4 -4 0 -8 q4 -4 0 -8", GOOD_THIN))


# ------------------------------------------------------------------------------------------------ status symbols
def dry_fur_symbol():
    # a drop with a jagged crack through it, flakes falling away: fur gone dry
    return ('<path d="M56 28 q-17 20 -17 31 a17 17 0 0 0 34 0 q0 -11 -17 -31 z" stroke-width="0"/>'
            f'<path d="M59 40 l-7 10 l8 5 l-7 11 l4 7" fill="none" stroke="{CUT}" stroke-width="3.6"/>'
            '<path d="M80 66 l4 3 l-3 4 z M32 70 l-4 2 l2 4 z M78 80 l3 1 l-1 3 z" stroke-width="1.5"/>')


def broken_well_symbol():
    # a drop, and a spanner laid across in front of it
    return ('<g transform="translate(56 56) scale(0.86) translate(-58 -54)">'
            '<path d="M46 28 q-15 18 -15 28 a15 15 0 0 0 30 0 q0 -10 -15 -28 z" stroke-width="0"/>'
            '<g transform="rotate(-45 64 64)">'
            f'<path d="M60 52 h8 v34 a4 4 0 0 1 -8 0 z M53 46 a11 11 0 1 1 22 0 a11 11 0 0 1 -6 9.8 h-10 a11 11 0 0 1 -6 -9.8 z" '
            f'fill="{CUT}" stroke="{CUT}" stroke-width="7"/>'
            '<path d="M60 52 h8 v34 a4 4 0 0 1 -8 0 z" stroke-width="0"/>'
            '<path d="M53 46 a11 11 0 1 1 22 0 a11 11 0 0 1 -6 9.8 h-10 a11 11 0 0 1 -6 -9.8 z" stroke-width="0"/>'
            f'<path d="M60 33 h8 v12 h-8 z" fill="{CUT}" stroke-width="0"/>'
            f'<circle cx="64" cy="78" r="1.8" fill="{CUT}" stroke-width="0"/>'
            '</g></g>')


def no_room_symbol():
    # a drop over a tub already brimming with water: nowhere for it to go
    return ('<path d="M56 24 q-10 12 -10 18 a10 10 0 0 0 20 0 q0 -6 -10 -18 z" stroke-width="0"/>'
            '<path d="M32 56 h48 l-4 26 q-1 4 -5 4 h-30 q-4 0 -5 -4 z" stroke-width="0"/>'
            '<path d="M29 54 h54" fill="none" stroke-width="5"/>'
            f'<path d="M36 64 q5 -4 10 0 t10 0 t10 0 t10 0 M38 74 q4.5 -4 9 0 t9 0 t9 0 t9 0" fill="none" stroke="{CUT}" stroke-width="3"/>')


# ------------------------------------------------------------------------------------------------ logo, status disc
def logo(color=OTTER_TEAL, size=98):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 98 98" width="{size}" height="{size}">'
           f'<rect x="27" y="27" width="44" height="44" rx="7" transform="rotate(45 49 49)" fill="none" stroke="{color}" stroke-width="5"/>'
           # solid droplet with a wave cut through it
           f'<path d="M49 28 q-14 17 -14 25 a14 14 0 0 0 28 0 q0 -8 -14 -25 z" fill="{color}"/>'
           f'<path d="M37 55 q4 -4 8 0 t8 0 t8 0" fill="none" stroke="#000" stroke-opacity="1" stroke-width="3.4" stroke-linecap="round"/>'
           '</svg>')
    img = _png(svg, size, size)
    # punch the wave out (transparent) instead of drawing it black
    r, g, b, a = img.split()
    import numpy as np
    arr = np.array(img)
    dark = (arr[..., 0] < 60) & (arr[..., 3] > 0)
    arr[dark, 3] = 0
    return Image.fromarray(arr)


def status_icon(symbol_body, size=512):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 112 112" width="{size}" height="{size}">'
           '<circle cx="56" cy="56" r="52" fill="#4A0B08"/>'
           '<circle cx="56" cy="56" r="45" fill="none" stroke="#F2A900" stroke-width="12"/>'
           '<circle cx="56" cy="56" r="52" fill="none" stroke="#4A0B08" stroke-width="3"/>'
           '<circle cx="56" cy="56" r="38.5" fill="#5C0F0B"/>'
           f'<g fill="{TAN}" stroke="{TAN}" stroke-linecap="round" stroke-linejoin="round">{symbol_body}</g></svg>')
    return _png(svg, size, size)


def shell_logo(color=OTTER_TEAL, size=98):
    """Rounded diamond with a solid scallop shell inside (the clasp on the otters' strap)."""
    import numpy as np
    ribs = "".join(f'<path d="M49 66 L{49 + 19 * __import__("math").cos(a):.1f} {60 - 19 * __import__("math").sin(a):.1f}" '
                   f'stroke="#000" stroke-width="2.2" stroke-linecap="round"/>'
                   for a in [__import__("math").radians(d) for d in (25, 52, 77, 103, 128, 155)])
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 98 98" width="{size}" height="{size}">'
           f'<rect x="27" y="27" width="44" height="44" rx="7" transform="rotate(45 49 49)" fill="none" stroke="{color}" stroke-width="5"/>'
           f'<path d="M49 68 L33 54 Q31 38 49 34 Q67 38 65 54 Z" fill="{color}"/>'          # fan
           f'<path d="M43 66 h12 l-2 5 h-8 z" fill="{color}"/>'                               # hinge
           f'{ribs}</svg>')
    img = _png(svg, size, size)
    arr = np.array(img)
    dark = (arr[..., 0] < 60) & (arr[..., 1] < 60) & (arr[..., 3] > 0)
    arr[dark, 3] = 0
    return Image.fromarray(arr)
