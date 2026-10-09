"""Icons drawn in Timberborn's own UI style.

* Building / crop tool icons: 112 px, tan (#BBA16C) line art, ~3.2 px round strokes, soft dark drop shadow.
* Good icons: 80 px, same style.
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


def line_icon(body, size, view=112, stroke=3.2, shadow=True):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {view} {view}" width="{size}" height="{size}">'
           f'<g fill="none" stroke="{TAN}" stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round">'
           f'{body}</g></svg>').replace("FILL", TAN)
    img = _png(svg, size, size)
    if not shadow:
        return img
    a = img.split()[3]
    sh = Image.new("RGBA", img.size, (20, 16, 10, 0))
    sh.putalpha(a.filter(ImageFilter.GaussianBlur(size / 90)).point(lambda v: int(v * 0.65)))
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    out.alpha_composite(sh, (max(1, size // 80), max(1, size // 56)))
    out.alpha_composite(img)
    return out


WAVES = ('<path d="M14 92 q6 -5 12 0 t12 0 t12 0 t12 0 t12 0 t12 0 t12 0"/>'
         '<path d="M14 102 q6 -5 12 0 t12 0 t12 0 t12 0 t12 0 t12 0 t12 0"/>')


def reed_filter():
    # a Folktails water-pump tank on legs with a reedy base and an outflow spout
    return ('<path d="M26 40 q16 -22 36 -22 q20 0 36 22 z"/>'          # domed cap
            '<rect x="50" y="12" width="16" height="7" rx="2"/>'
            '<path d="M32 40 v34 M92 40 v34 M30 74 h64"/>'             # tank sides and base
            '<path d="M62 50 q-7 9 -7 13 a7 7 0 0 0 14 0 q0 -4 -7 -13 z" fill="FILL"/>'
            '<path d="M92 50 h10 q4 0 4 4 v12"/>'
            '<path d="M22 86 q2 -18 -4 -30 M30 86 q0 -16 6 -26 M86 86 q0 -14 -4 -22 M96 86 q2 -16 8 -24"/>'
            '<path d="M18 55 l-2 -9 l4 4 z M36 59 l3 -9 l1 6 z" fill="FILL"/>'
            '<rect x="14.5" y="40" width="5" height="12" rx="2.5" fill="FILL"/>'
            '<rect x="100.5" y="52" width="5" height="12" rx="2.5" fill="FILL"/>'
            + WAVES)


def dig_site():
    # a spade biting into a block of earth, a little heap of dirt beside it
    return ('<path d="M20 70 h52 v26 h-52 z"/>'
            '<path d="M26 80 l8 -8 M38 88 l14 -14 M54 92 l14 -14" stroke-width="2.6"/>'
            '<path d="M66 18 l14 14"/>'                                  # handle grip
            '<path d="M73 25 l-20 28"/>'                                 # shaft
            '<path d="M44 49 l14 10 l-6 14 q-10 4 -16 -4 z" fill="FILL"/>'  # blade
            '<path d="M80 96 q4 -16 12 -16 q8 0 12 16 z"/>'
            '<circle cx="86" cy="72" r="2" fill="FILL"/><circle cx="96" cy="68" r="1.6" fill="FILL"/>')


def rinse_pod():
    # an upright soaking pod with a shower rose and falling drops
    return ('<path d="M34 96 v-46 q0 -22 28 -22 q28 0 28 22 v46 z"/>'
            '<path d="M34 64 h56"/>'
            '<path d="M48 22 h28 M62 22 v-8"/>'
            '<path d="M50 38 q-4 6 -4 9 a4 4 0 0 0 8 0 q0 -3 -4 -9 z" fill="FILL"/>'
            '<path d="M74 38 q-4 6 -4 9 a4 4 0 0 0 8 0 q0 -3 -4 -9 z" fill="FILL"/>'
            '<path d="M44 78 q6 -5 12 0 t12 0 t12 0"/>'
            '<path d="M24 96 h76"/>')


def river_holt(double=False):
    # a stick-built lodge dome sitting in the water
    dome = lambda x, w, h: (f'<path d="M{x} 82 q0 -{h} {w / 2} -{h} q{w / 2} 0 {w / 2} {h}"/>'
                            f'<path d="M{x + w * 0.38} 82 v-12 q0 -6 {w * 0.12} -6 q{w * 0.12} 0 {w * 0.12} 6 v12"/>'
                            f'<path d="M{x + 6} {82 - h * 0.55} l{w * 0.25} -6 M{x + w * 0.6} {82 - h * 0.75} l{w * 0.28} 8" stroke-width="2.4"/>')
    body = dome(20, 56, 40) if not double else dome(12, 46, 34) + dome(54, 46, 44)
    return body + '<path d="M14 82 h84"/>' + WAVES


def watercress_crop():
    leaf = lambda x, y, r, a: (f'<path transform="rotate({a} {x} {y})" d="M{x} {y} q-{r} -{r * 0.4} 0 -{r * 1.6} q{r} {r * 1.2} 0 {r * 1.6} z" fill="FILL"/>')
    return ('<path d="M56 86 v-30 M56 66 q-12 -6 -16 -18 M56 62 q12 -6 18 -16 M56 56 q-2 -10 2 -20"/>'
            + leaf(40, 48, 9, -40) + leaf(74, 46, 9, 40) + leaf(58, 36, 8, 5) + leaf(46, 62, 7, -70) + leaf(68, 60, 7, 70)
            + WAVES)


def wild_rice_crop():
    return ('<path d="M44 86 q2 -30 -6 -58 M60 86 q0 -34 6 -64 M74 86 q-2 -26 10 -48"/>'
            + "".join(f'<ellipse cx="{x}" cy="{y}" rx="2.4" ry="5" transform="rotate({a} {x} {y})" fill="FILL"/>'
                      for x, y, a in [(38, 30, -20), (35, 40, -30), (42, 38, 20), (66, 24, 10), (62, 34, -25), (70, 34, 25),
                                      (84, 40, 30), (80, 48, -20), (88, 50, 35)])
            + WAVES)


def watercress_good():
    leaf = lambda x, y, r, a: (f'<path transform="rotate({a} {x} {y})" d="M{x} {y} q-{r} -{r * 0.45} 0 -{r * 1.7} q{r} {r * 1.25} 0 {r * 1.7} z"/>')
    return ('<path d="M40 66 q-2 -14 -10 -24 M40 66 q2 -16 12 -26 M40 66 q0 -20 0 -32"/>'
            '<path d="M32 62 h16 l-2 8 h-12 z" fill="FILL"/>'
            + leaf(30, 42, 8, -35) + leaf(52, 40, 8, 35) + leaf(40, 32, 7, 0))


def wild_rice_good():
    return ('<path d="M18 52 q22 -14 44 -20 q-4 18 -26 26 q-12 4 -18 -6 z"/>'
            + "".join(f'<ellipse cx="{x}" cy="{y}" rx="2.2" ry="4.6" transform="rotate({a} {x} {y})" fill="FILL"/>'
                      for x, y, a in [(30, 44, 60), (40, 40, 60), (50, 36, 60), (34, 52, 60), (44, 48, 60), (54, 44, 60)]))


def cooked_rice_good():
    return ('<path d="M16 46 h48 q-2 20 -24 20 q-22 0 -24 -20 z"/>'
            '<path d="M22 46 q4 -10 18 -10 q14 0 18 10"/>'
            + "".join(f'<ellipse cx="{x}" cy="{y}" rx="1.6" ry="3" transform="rotate({a} {x} {y})" fill="FILL"/>'
                      for x, y, a in [(30, 42, 30), (38, 40, -20), (46, 41, 40), (52, 43, -30)])
            + '<path d="M30 30 q-4 -5 0 -10 q4 -5 0 -10 M42 28 q-4 -5 0 -10 q4 -5 0 -10" stroke-width="2.4"/>')


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


def dry_fur_symbol():
    # a droplet with a crack through it
    return ('<path d="M56 30 q-16 19 -16 29 a16 16 0 0 0 32 0 q0 -10 -16 -29 z" stroke-width="0"/>'
            '<path d="M58 42 l-6 9 l7 5 l-6 10 l4 6" fill="none" stroke="#5C0F0B" stroke-width="3.2"/>')


def taro_crop():
    # big heart-shaped leaves on long stems standing in water
    heart = lambda x, y, s, a: (f'<path transform="rotate({a} {x} {y})" d="M{x} {y} q-{s} -{s * 0.2} -{s * 0.9} -{s * 1.1} '
                                f'q-{s * 0.2} -{s * 0.7} {s * 0.5} -{s * 0.7} q{s * 0.3} 0 {s * 0.4} {s * 0.35} q{s * 0.1} -{s * 0.35} {s * 0.4} -{s * 0.35} '
                                f'q{s * 0.7} 0 {s * 0.5} {s * 0.7} q-{s * 0.1} {s * 0.9} -{s * 0.9} {s * 1.1} z"/>')
    return ('<path d="M56 86 q-2 -20 -14 -34 M56 86 q2 -24 16 -40 M56 86 v-30"/>'
            + heart(42, 52, 20, -25) + heart(72, 46, 20, 25) + heart(56, 52, 14, 0) + WAVES)


def taro_root_good():
    return ('<path d="M26 34 q-10 10 -4 22 q8 12 22 6 q14 -6 10 -20 q-4 -14 -16 -14 q-6 0 -12 6 z"/>'
            '<path d="M30 38 q6 -2 10 2 M28 48 q8 -2 14 2 M34 56 q6 -1 10 1" stroke-width="2.2"/>'
            '<path d="M38 22 q2 -6 8 -8 M38 22 q-4 -5 -10 -6"/>')


def roasted_taro_good():
    return ('<path d="M18 50 q0 -12 14 -14 h16 q14 2 14 14 q-4 10 -22 10 q-18 0 -22 -10 z"/>'
            '<path d="M26 44 l6 -6 M36 46 l8 -8 M48 46 l6 -6" stroke-width="2.4"/>'
            '<path d="M30 28 q-4 -5 0 -10 q4 -5 0 -10 M44 26 q-4 -5 0 -10 q4 -5 0 -10" stroke-width="2.4"/>')


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


def _fish(x, y, s=1.0, a=0, fill=False):
    """A side-on fish centred at (x, y), nose to the right, s=1 is about 30 px long."""
    f = ' fill="FILL"' if fill else ""
    return (f'<g transform="translate({x} {y}) rotate({a}) scale({s})">'
            f'<path d="M-9 0 q8 -10 20 -5 q4 2 6 5 q-2 3 -6 5 q-12 5 -20 -5 z"{f}/>'
            f'<path d="M-9 0 l-7 -6 v12 z"{f}/>'
            + ('' if fill else '<circle cx="11" cy="-1.5" r="1.2" fill="FILL"/><path d="M3 -5 q-2 5 0 10" stroke-width="2"/>')
            + '</g>')


def fishing_dock():
    # a little pier on posts with a rod bent over the water and a fish on the line
    return ('<path d="M10 64 h58"/>'                                       # deck
            '<path d="M16 64 v26 M36 64 v26 M58 64 v26"/>'                 # posts into the water
            '<path d="M18 64 v-22 h22 v22 M14 44 l15 -12 l15 12"/>'        # little hut
            '<path d="M58 62 L94 18" stroke-width="3.6"/>'                 # rod
            '<path d="M94 18 V58" stroke-width="1.8"/>'                    # line
            + _fish(94, 68, 0.8, 90) + WAVES)


def artesian_well():
    # a drill tower over a pipe, water welling up and spilling out both sides, with a gear for power
    return ('<path d="M46 18 h20 l4 46 h-28 z"/>'                          # tower
            '<path d="M48 32 h16 M47 46 h18" stroke-width="2.4"/>'
            '<path d="M52 18 v-6 h8 v6"/>'
            '<circle cx="84" cy="36" r="9"/><circle cx="84" cy="36" r="3" fill="FILL"/>'
            + "".join(f'<path d="M{84 + 9 * c:.1f} {36 + 9 * s:.1f} l{3.5 * c:.1f} {3.5 * s:.1f}" stroke-width="3"/>'
                      for c, s in [(__import__("math").cos(__import__("math").radians(d)), __import__("math").sin(__import__("math").radians(d))) for d in range(0, 360, 45)])
            + '<path d="M70 36 h5"/>'
            '<path d="M38 64 h36"/>'
            '<path d="M56 70 q-6 8 -6 12 a6 6 0 0 0 12 0 q0 -4 -6 -12 z" fill="FILL"/>'
            '<path d="M40 66 q-10 2 -16 12 M72 66 q10 2 16 12"/>'
            + WAVES)


def splash_pool():
    # a wooden pool frame in the water, a diving plank and a splash
    return ('<path d="M14 70 h84 M20 70 v20 M92 70 v20"/>'
            '<path d="M14 62 h22 v8"/>'                                    # plank
            '<path d="M36 62 l18 -4" stroke-width="3.6"/>'
            '<path d="M68 60 q-4 -14 -12 -20 M74 58 q2 -16 10 -22 M80 62 q8 -10 16 -12" stroke-width="2.8"/>'
            '<circle cx="62" cy="34" r="2.6" fill="FILL"/><circle cx="88" cy="32" r="2.2" fill="FILL"/><circle cx="96" cy="44" r="2" fill="FILL"/>'
            '<path d="M56 70 q8 -10 18 -6 q10 -4 18 6"/>'
            + WAVES)


def fish_good():
    return _fish(42, 42, 1.6, -12)


def grilled_fish_good():
    return (_fish(38, 50, 1.4, 0)
            + '<path d="M22 47 l5 7 M30 45 l6 9 M38 44 l6 9" stroke-width="2.2"/>'
            '<path d="M28 30 q-4 -5 0 -10 q4 -5 0 -10 M42 28 q-4 -5 0 -10 q4 -5 0 -10" stroke-width="2.4"/>')


def broken_well_symbol():
    # a droplet with a spanner across it
    return ('<path d="M48 26 q-15 18 -15 28 a15 15 0 0 0 30 0 q0 -10 -15 -28 z" stroke-width="0"/>'
            '<g transform="rotate(45 64 66)">'
            '<rect x="60" y="58" width="8" height="34" rx="3" stroke-width="0"/>'
            '<path d="M64 40 a12 12 0 1 0 0.1 0 z" stroke-width="0"/>'
            '<rect x="60" y="34" width="8" height="12" fill="#5C0F0B" stroke-width="0"/>'
            '</g>'
            '<path d="M48 26 q-15 18 -15 28 a15 15 0 0 0 30 0" fill="none" stroke="#5C0F0B" stroke-width="0"/>')


def water_tube():
    # a run of tube with a bend, a droplet riding inside
    return ('<path d="M18 64 h38 q6 0 6 -6 v-34 M18 80 h38 q22 0 22 -22 v-34"/>'
            '<path d="M14 60 v24 M58 24 h24" stroke-width="4.4"/>'
            '<path d="M32 58 v-0 M44 86 v0" stroke-width="0"/>'
            '<path d="M38 64 q-5 6 -5 9 a5 5 0 0 0 10 0 q0 -3 -5 -9 z" fill="FILL" stroke-width="0"/>'
            '<path d="M70 40 q-4 5 -4 7 a4 4 0 0 0 8 0 q0 -2 -4 -7 z" fill="FILL" stroke-width="0"/>'
            '<path d="M14 98 h84" stroke-width="2.4"/>')


def tube_outlet():
    # a barrel spout fed by a tube from behind, water pouring down into waves
    return ('<path d="M10 46 h22 M10 58 h22 M10 42 v20" />'
            '<path d="M32 36 h28 v34 h-28 z"/>'
            '<path d="M32 46 h28 M32 60 h28" stroke-width="2.4"/>'
            '<path d="M60 44 h16 q6 0 6 6 v4"/>'
            '<path d="M80 58 q-3 8 -3 16 M84 58 q2 10 0 20" stroke-width="2.6"/>'
            + WAVES)


def smokehouse():
    # a small hut with a smoking chimney and fish hanging under the eaves
    return ('<path d="M18 92 v-40 l30 -22 l30 22 v40 z"/>'
            '<path d="M62 40 v-18 h10 v26"/>'
            '<path d="M66 16 q-4 -5 0 -10 M74 18 q-4 -5 0 -10" stroke-width="2.4"/>'
            '<path d="M40 92 v-20 h16 v20"/>'
            + _fish(86, 60, 0.6, 90, fill=True) + _fish(98, 64, 0.55, 90, fill=True)
            + '<path d="M78 46 h26 M86 46 v4 M98 46 v8" stroke-width="2.2"/>')


def otter_slide():
    # a slide tower with a curving chute into the water
    return ('<path d="M18 92 V36 M42 92 V36 M14 36 h32 M14 24 l16 -10 l16 10 z"/>'
            '<path d="M22 48 h16 M22 60 h16 M22 72 h16" stroke-width="2.4"/>'
            '<path d="M42 40 q22 4 34 30 q8 14 22 16" stroke-width="3.6"/>'
            '<path d="M42 50 q18 4 28 26 q6 10 18 12" stroke-width="2"/>'
            '<circle cx="96" cy="74" r="2.4" fill="FILL"/><circle cx="102" cy="80" r="2" fill="FILL"/>'
            + WAVES)


def smoked_fish_good():
    return (_fish(40, 46, 1.5, -8, fill=True)
            + '<path d="M28 26 q-4 -5 0 -10 q4 -5 0 -10 M40 24 q-4 -5 0 -10 q4 -5 0 -10 M52 26 q-4 -5 0 -10" stroke-width="2.4"/>')


def no_room_symbol():
    # a droplet pressed against a level line: nowhere for the water to go
    return ('<path d="M56 26 q-14 17 -14 26 a14 14 0 0 0 28 0 q0 -9 -14 -26 z" stroke-width="0"/>'
            '<path d="M30 78 h52" fill="none" stroke-width="7"/>'
            '<path d="M38 88 l6 -6 M52 88 l6 -6 M66 88 l6 -6" fill="none" stroke-width="3.5"/>')


def slipway():
    # a ramp sliding down into the water with a splash
    return ('<path d="M16 40 h22 l44 40"/>'
            '<path d="M16 48 h18 l40 36" stroke-width="2.4"/>'
            '<path d="M30 46 l6 -6 M44 58 l6 -6 M58 70 l6 -6" stroke-width="2.4"/>'
            '<path d="M84 76 q4 -10 10 -12 M90 80 q6 -6 12 -6" stroke-width="2.6"/>'
            + WAVES)
