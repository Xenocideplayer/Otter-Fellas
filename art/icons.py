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
