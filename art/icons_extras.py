"""Icons for the Tube Valve, Clam Bed, clams and the Wellspring, in the same style as icons.py.

Every function returns an SVG body. Building icons are drawn on a 112 grid, goods on an 80 grid, status symbols
for status_icon (112 grid, rendered at 512). render(name, size) turns any of them into a finished PIL image:
    112 -> building / tool icon, 80 -> good icon, 512 -> status icon.
"""
import math

from icons import WAVES, line_icon, status_icon


def _clam(x, y, s=1.0, fill=False, a=0):
    """A clam shell seen from above, hinge at the bottom, centred at (x, y); s=1 is about 28 px wide."""
    f = ' fill="FILL"' if fill else ""
    ribs = "" if fill else "".join(
        f'<path d="M0 8 L{12 * math.cos(math.radians(d)):.1f} {8 - 16 * math.sin(math.radians(d)):.1f}" stroke-width="1.8"/>'
        for d in (40, 65, 90, 115, 140))
    return (f'<g transform="translate({x} {y}) rotate({a}) scale({s})">'
            f'<path d="M0 9 L-13 -1 Q-12 -13 0 -13 Q12 -13 13 -1 Z"{f}/>'
            f'<path d="M-5 9 h10 l-2 4 h-6 z"{f}/>'
            f'{ribs}</g>')


def tube_valve():
    # a straight run of tube with a valve body and a hand wheel on top
    return ('<path d="M10 66 h92 M10 88 h92"/>'
            '<path d="M10 62 v30 M102 62 v30" stroke-width="4.4"/>'
            '<path d="M44 66 v-12 h24 v12"/>'                                   # valve body
            '<path d="M56 54 v-14"/>'                                             # stem
            '<ellipse cx="56" cy="36" rx="24" ry="8"/>'                           # wheel rim
            '<path d="M36 33 L76 39 M36 39 L76 33" stroke-width="2.4"/>'          # spokes
            '<circle cx="56" cy="36" r="3.4" fill="FILL"/>'
            '<path d="M24 77 q-4 5 -4 7 a4 4 0 0 0 8 0 q0 -2 -4 -7 z" fill="FILL" stroke-width="0"/>'
            '<path d="M80 74 l8 6 l-8 6" stroke-width="2.6"/>'
            '<path d="M14 100 h84" stroke-width="2.4"/>')


def clam_bed():
    # stakes and net standing in the water over a bed of clams, a little walkway on the left
    return ('<path d="M8 50 h30 M14 50 v22 M32 50 v22"/>'                         # walkway on posts
            '<path d="M44 40 v40 M64 36 v44 M84 36 v44 M102 40 v40"/>'            # stakes
            '<path d="M44 40 l-2 -5 l2 -3 l2 3 z M102 40 l-2 -5 l2 -3 l2 3 z" fill="FILL" stroke-width="1.6"/>'
            '<path d="M44 46 L64 42 L84 42 L102 46 M44 58 L64 54 L84 54 L102 58" stroke-width="2"/>'
            '<path d="M54 44 v14 M74 42 v13 M93 44 v13" stroke-width="1.6"/>'
            + '<path d="M8 86 q6 -5 12 0 t12 0 t12 0 t12 0 t12 0 t12 0 t12 0 t12 0"/>'
            + _clam(52, 100, 0.55, fill=True) + _clam(72, 102, 0.5, fill=True) + _clam(90, 100, 0.45, fill=True)
            + '<path d="M8 108 h96" stroke-width="2.4"/>')


def wellspring():
    # the wonder: a log plinth with a door, a pool, a column and a bowl pouring water, a holt and pennant on top
    return ('<path d="M12 100 h88 M16 100 v-20 h80 v20"/>'                        # plinth
            '<path d="M50 100 v-12 q6 -6 12 0 v12"/>'                             # door
            '<path d="M22 80 v-6 h68 v6"/>'                                       # pool ring
            '<path d="M50 74 v-24 M62 74 v-24"/>'                                 # column
            '<path d="M26 40 h60 l-20 12 h-20 z"/>'                               # bowl
            '<path d="M26 40 q-8 4 -8 34 M86 40 q8 4 8 34" stroke-width="2.6"/>'  # streams
            '<path d="M42 40 q0 -16 14 -16 q14 0 14 16"/>'                        # holt
            '<path d="M56 24 v-14"/><path d="M56 10 l12 4 l-12 4 z" fill="FILL"/>'
            '<path d="M51 40 v-6 q5 -5 10 0 v6" stroke-width="2.2"/>')


def clams_good():
    return _clam(30, 44, 1.2) + _clam(52, 52, 1.0, a=18)


def grilled_clams_good():
    # an opened clam on a little grill, steam rising
    return ('<path d="M14 60 h52 M18 60 l-4 10 M62 60 l4 10" stroke-width="2.6"/>'
            '<path d="M18 54 h44" stroke-width="2"/>'
            + _clam(40, 44, 1.1)
            + '<path d="M30 24 q-4 -5 0 -10 q4 -5 0 -10 M44 22 q-4 -5 0 -10 q4 -5 0 -10" stroke-width="2.4"/>')


def clam_bed_no_water_symbol():
    # a clam over a crossed-out wave: not enough clean water
    return (_clam(56, 46, 1.25, fill=True).replace('fill="FILL"', 'fill="#BBA16C"')
            + '<path d="M30 76 q6 -6 13 0 t13 0 t13 0 t13 0" fill="none" stroke-width="5"/>'
            + '<path d="M36 90 L76 66" fill="none" stroke-width="6"/>')


def driftwood_catch():
    # a V of floating logs between posts funnelling driftwood towards a little deck with a winch
    return ('<path d="M8 40 h34 M14 40 v20 M36 40 v20"/>'                         # deck on posts
            '<path d="M18 40 v-10 M32 40 v-10 M16 30 h18" stroke-width="2.4"/>'   # winch frame
            '<circle cx="25" cy="30" r="4.5"/>'
            '<path d="M29 32 Q48 44 56 58" stroke-width="1.8"/>'                  # rope to the boom
            '<path d="M60 62 L100 32 M60 62 L104 84" stroke-width="7"/>'          # the boom logs
            '<path d="M100 22 v18 M104 76 v18" stroke-width="2.6"/>'              # posts
            '<path d="M70 56 l18 -6 M74 66 l20 3" stroke-width="5.5"/>'           # caught driftwood
            '<path d="M8 76 q6 -5 12 0 t12 0 t12 0 t12 0" stroke-width="2.2"/>'
            '<path d="M8 100 q6 -5 12 0 t12 0 t12 0 t12 0 t12 0 t12 0 t12 0 t12 0" stroke-width="2.2"/>')


def basking_deck():
    # a sun over a low deck with a flat stone and a mat, an otter tail curling off the edge
    return ('<circle cx="80" cy="26" r="11"/>'
            '<path d="M80 6 v6 M80 40 v6 M60 26 h6 M94 26 h6 M66 12 l4 4 M90 36 l4 4 M94 12 l-4 4 M66 40 l4 -4" stroke-width="2.4"/>'
            '<path d="M10 76 h92 M10 84 h92 M16 84 v16 M96 84 v16"/>'              # deck
            '<path d="M22 76 q20 -18 46 0" fill="FILL"/>'                         # flat stone
            '<path d="M72 76 v-4 h24 v4" stroke-width="2.4"/>'                    # mat
            '<path d="M10 84 q-6 8 2 14" stroke-width="3"/>')


def driftwood_no_current_symbol():
    # a log over a flat (still) line: no current to bring driftwood
    return ('<path d="M26 50 h60" fill="none" stroke-width="16" stroke-linecap="round" stroke="#BBA16C"/>'
            '<path d="M24 78 h64" fill="none" stroke-width="5"/>'
            '<path d="M36 92 L76 64" fill="none" stroke-width="6"/>')


def render(name, size):
    body = globals()[name]()
    if size == 512:
        return status_icon(body, 512)
    if size == 80:
        return line_icon(body, 80, view=80, stroke=3.0)
    return line_icon(body, size)


# (function, size, path relative to the version folder) -- rendered by make_art.py
ICONS = [("tube_valve", 112, "Buildings/Water/TubeValve/TubeValveIcon.png"),
         ("clam_bed", 112, "Buildings/Food/ClamBed/ClamBedIcon.png"),
         ("wellspring", 112, "Buildings/Monuments/Wellspring/WellspringIcon.png"),
         ("clams_good", 80, "Sprites/Goods/ClamsIcon.png"),
         ("grilled_clams_good", 80, "Sprites/Goods/GrilledClamsIcon.png"),
         ("clam_bed_no_water_symbol", 512, "Sprites/StatusIcons/OtterClamBedNoWater.png"),
         ("driftwood_catch", 112, "Buildings/Wood/DriftwoodCatch/DriftwoodCatchIcon.png"),
         ("basking_deck", 112, "Buildings/Wellbeing/BaskingDeck/BaskingDeckIcon.png"),
         ("driftwood_no_current_symbol", 512, "Sprites/StatusIcons/OtterDriftwoodNoCurrent.png")]
