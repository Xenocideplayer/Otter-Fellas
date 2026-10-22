"""Icons for the Tube Valve, Clam Bed, Wellspring, Driftwood Catch, Basking Deck, the Timber Tunnel set, clams, rice cakes and sushi, drawn with the helpers in icons.py.

Every function returns an SVG body. Building icons are drawn on a 112 grid, goods on an 80 grid, status symbols
for status_icon (112 grid, rendered at 512). render(name, size) turns any of them into a finished PIL image:
    112 -> building / tool icon, 80 -> good icon, 512 -> status icon.
"""
import math

from icons import (CUT, GOOD_STROKE, arrow, GOOD_THIN, THIN, box, cattail, deck, dots, door, drop, ell, flag, fish, good,
                   ground, grp, hatch, lantern, line_icon, log, reed, ripples, scallop, solid, splash, status_icon,
                   steam, swoosh, thin, water, waves, _arch)


def tube_valve():
    # a straight run of tube with banded joints, a valve bonnet and a hand wheel on top, a drop riding in the tube,
    # standing on trestles over hatched ground
    return ('<path d="M11 58 H101 M11 78 H101"/>'
            '<path d="M22 54 V82 M90 54 V82" stroke-width="4.4"/>'
            '<path d="M44 58 V48 H68 V58"/>' + thin("M44 53 H68")
            + '<path d="M56 48 V34"/>'
            '<ellipse cx="56" cy="30" rx="24" ry="8"/>'
            + thin("M33 28 L79 32 M33 32 L79 28 M56 22 V38")
            + dots(((56, 30),), 3.2)
            + drop(30, 72, 4) + drop(80, 72, 4)
            + '<path d="M30 78 V90 M82 78 V90"/>'
            + ground(11, 101, 90))


def clam_bed():
    # a plank walk on posts, stakes and netting standing in the water, a bed of scallops on the hatched bottom
    return (deck(11, 38, 44, 6, 9, posts=(15, 34), post_to=70)
            + '<path d="M46 38 V82 M68 34 V82 M90 38 V82"/>'
            + solid("M46 38 l-2.5 -5 l2.5 -4 l2.5 4 z M90 38 l-2.5 -5 l2.5 -4 l2.5 4 z")
            + thin("M46 44 Q57 48 68 42 Q79 48 90 44 M46 56 Q57 60 68 54 Q79 60 90 56 M57 46 V58 M79 46 V58", 2.2)
            + water(11, 101, 70, 0, 1, 12, 5.5)
            + scallop(34, 84, 0.52, -8, n=4) + scallop(58, 86, 0.48, 6, n=4) + scallop(82, 84, 0.52, 10, n=4)
            + ground(11, 101, 94, 6))


def wellspring():
    # the wonder: a log plinth with a door, a pool on it, a banded column holding up a bowl that brims over and
    # pours into the pool on both sides, a little holt with a pennant on top
    return ('<path d="M14 100 V86 H98 V100"/>' + thin("M14 93 H46 M66 93 H98")
            + door(56, 100, 14, 12)
            + '<path d="M22 86 V76 H90 V86"/>' + thin("M22 81 H90", 2.2)
            + '<path d="M50 76 V54 M62 76 V54"/>' + thin("M50 62 H62 M50 69 H62")
            + '<path d="M28 44 H84 Q80 54 66 54 H46 Q32 54 28 44 Z"/>'
            + thin("M28 45 Q18 48 22 74 M84 45 Q94 48 90 74", 2.8)
            + thin("M17 74 l-3 -3 M27 74 l3 -3 M85 74 l-3 -3 M95 74 l3 -3", 2.2)
            + '<path d="M44 44 Q44 30 56 30 Q68 30 68 44"/>' + thin("M48 38 l6 -3 M60 35 l6 3")
            + door(56, 44, 8, 8)
            + flag(56, 30, 14, 11))


def driftwood_catch():
    # a little deck with a winch, its rope out to driftwood logs caught against a boom post in the river
    return (deck(11, 40, 44, 6, 10, posts=(15, 36), post_to=74)
            + '<path d="M18 44 V30 M34 44 V30"/>' + '<circle cx="26" cy="32" r="5"/>' + dots(((26, 32),), 1.6)
            + thin("M26 32 l6 -7", 2.6)
            + '<path d="M31 34 Q44 38 48 58" stroke-width="1.8"/>'
            + '<path d="M98 30 V90"/>' + solid("M98 30 l-3 -5 l3 -4 l3 4 z")
            + log(46, 66, 84, 66, 10) + log(56, 55, 86, 53, 9)
            + thin("M64 51 l-5 -8 M61 46 l-6 -1", 2.6)
            + water(11, 101, 80, 9, 2, 12, 5.5))


def basking_deck():
    # a flat warm stone on a plank deck over the water, heat shimmering off it, the sun overhead
    return ('<circle cx="80" cy="24" r="10"/>'
            + thin("M80 6 v5 M80 37 v5 M62 24 h5 M93 24 h5 M67 11 l3.5 3.5 M90 34 l3.5 3.5 M93 11 l-3.5 3.5 M67 37 l3.5 -3.5")
            + '<path d="M16 64 L20 55 L32 50 L52 48 L66 52 L72 64"/>'
            + thin("M32 50 l4 7 l8 2 M52 48 l-2 6 M66 52 l-6 5")
            + thin("M30 42 q-3 -4 0 -8 q3 -4 0 -8 M42 40 q-3 -4 0 -8 q3 -4 0 -8 M54 42 q-3 -4 0 -8 q3 -4 0 -8")
            + scallop(88, 56, 0.42, 10, n=4)
            + deck(11, 101, 64, 6, 11, posts=(16, 56, 96), post_to=84)
            + water(11, 101, 88))


def _portal(cx, base, w, top):
    """A timber tunnel mouth: two posts, a lintel with its ends showing, corner braces."""
    hw = w / 2
    return (f'<path d="M{cx - hw} {base} V{top} M{cx + hw} {base} V{top}"/>'
            f'<path d="M{cx - hw - 6} {top - 2} H{cx + hw + 6}" stroke-width="4.4"/>'
            + thin(f"M{cx - hw} {top + 12} L{cx - hw + 10} {top} M{cx + hw} {top + 12} L{cx + hw - 10} {top}"))


def timber_tunnel():
    # a timber-framed tunnel mouth dug into a grassy bank of hatched earth, a lantern hung by the opening
    portal = box(30, 44, 82, 98, 3)
    lamp = box(83, 50, 97, 74, 2)
    bank = ell(56, 98, 45, 68, -4)
    return ('<path d="M11 98 Q14 32 56 30 Q98 32 101 98"/>'
            + _portal(56, 98, 40, 50)
            + solid(_arch(56, 98, 28, 58) + " z")
            + lantern(90, 48, 1.1)
            + reed(30, 42, -4, 10) + reed(31, 42, 5, 9) + reed(80, 40, -3, 11) + reed(81, 40, 6, 8)
            + hatch(lambda x, y: bank(x, y) and not portal(x, y) and not lamp(x, y) and y < 95, 12, 40, 100, 95)
            + '<path d="M11 98 H101"/>')


def timber_shaft():
    # a plank-lined shaft dug straight down with a ladder in it, a timber head-frame and pulley over it, hatched
    # earth either side, arrows up and down
    return ('<path d="M11 36 H38 M74 36 H101"/>'
            '<path d="M38 36 V100 M74 36 V100"/>'
            + thin("M48 30 V100 M64 30 V100") + thin("M48 44 H64 M48 56 H64 M48 68 H64 M48 80 H64 M48 92 H64", 2.4)
            + '<path d="M34 36 V14 M78 36 V14 M30 14 H82"/>' + thin("M34 26 L44 14 M78 26 L68 14")
            + '<circle cx="56" cy="21" r="4.5" stroke-width="2.6"/>' + thin("M60.5 21 V30", 2)
            + hatch(lambda x, y: not (35 <= x <= 77), 12, 40.5, 100, 100)
            + arrow(21, 22, 0.9) + arrow(91, 22, 0.9, down=True))


def sealed_timber_tunnel():
    # the timber tunnel mouth closed off by a braced plank door, the river lapping at the foot of the bank
    portal = box(30, 38, 82, 88, 3)
    bank = ell(56, 88, 45, 62, -4)
    return ('<path d="M11 88 Q14 26 56 24 Q98 26 101 88"/>'
            + _portal(56, 88, 40, 44)
            + f'<path d="{_arch(56, 88, 28, 52)}"/>'
            + thin("M49 88 V53 M56 88 V52 M63 88 V53")
            + '<path d="M30 70 H82" stroke-width="5"/>' + dots(((36, 70), (76, 70)), 0.1)
            + reed(30, 36, -4, 10) + reed(31, 36, 5, 9) + reed(80, 34, -3, 11) + reed(81, 34, 6, 8)
            + hatch(lambda x, y: bank(x, y) and not portal(x, y) and y < 85, 12, 34, 100, 85)
            + '<path d="M11 88 H101"/>' + water(11, 101, 95, 8, 1, 12, 5.5))


def tunnel_lodge():
    # a round log hall with a thatched cone roof and a pennant, timber tunnel mouths opening off both sides
    side = lambda cx: (f'<path d="{_arch(cx, 96, 18, 72)}"/>' + solid(_arch(cx, 96, 9, 78) + " z")
                       + f'<path d="M{cx - 13} 72 H{cx + 13}" stroke-width="4"/>')
    return ('<path d="M34 96 V62 M78 96 V62"/>'
            + thin("M34 72 H78 M34 84 H48 M64 84 H78")
            + '<path d="M26 64 L56 28 L86 64 Z"/>'
            + thin("M56 34 L40 62 M56 34 L50 64 M56 34 L62 64 M56 34 L72 62")
            + door(56, 96, 14, 18)
            + side(20) + side(92)
            + flag(56, 28, 14, 11)
            + ground(11, 101, 96))


def clams_good():
    # two scallops with their ribs and hinge ears
    return good(scallop(25, 46, 0.72, -14, base=GOOD_STROKE) + scallop(55, 36, 0.72, 14, base=GOOD_STROKE))


def grilled_clams_good():
    # an opened scallop on the half shell, the meat in the middle, on a little grill, steam rising
    return good(scallop(40, 46, 1.0, 0, base=GOOD_STROKE, meat=True)
                + '<path d="M10 62 H70"/>' + thin("M16 62 l-4 9 M64 62 l4 9 M24 67 H56", GOOD_THIN)
                + steam(28, 22, 3, 12, 14, GOOD_THIN))


def rice_cakes_good():
    # a stack of three puffed rice cakes, grains showing on the top one
    grain = lambda x, y, a: f'<ellipse cx="{x}" cy="{y}" rx="1.7" ry="3" transform="rotate({a} {x} {y})" fill="FILL" stroke-width="0.8"/>'
    return good('<ellipse cx="40" cy="24" rx="26" ry="9"/>'
                + '<path d="M14 24 V31 Q14 40 40 40 Q66 40 66 31 V24"/>'
                + '<path d="M13 38 Q11 40 11 43 V48 Q11 57 40 57 Q69 57 69 48 V43 Q69 40 67 38"/>'
                + '<path d="M10 55 Q8 57 8 60 V64 Q8 73 40 73 Q72 73 72 64 V60 Q72 57 70 55"/>'
                + grain(28, 22, 40) + grain(36, 26, -30) + grain(46, 21, 70) + grain(52, 26, 20) + grain(40, 19, -60)
                + dots(((22, 35), (40, 37), (58, 35), (20, 52), (40, 54), (60, 52), (18, 68), (40, 70), (62, 68)), 1.7))


def sushi_good():
    # a maki roll (seaweed round rice round fish) and a nigiri: rice with a striped slice of fish, tied with seaweed
    return good('<ellipse cx="22" cy="28" rx="14" ry="6.5"/>'
                + '<path d="M8 28 V46 Q8 53 22 53 Q36 53 36 46 V28"/>'
                + '<ellipse cx="22" cy="28" rx="8.5" ry="3.6" stroke-width="2.4"/>'
                + '<ellipse cx="22" cy="28" rx="4" ry="1.8" fill="FILL" stroke-width="1"/>'
                + '<path d="M36 62 Q36 52 54 52 Q72 52 72 62 Q72 70 54 70 Q36 70 36 62 z"/>'
                + '<path d="M33 54 Q36 42 54 42 Q70 42 76 50 Q72 56 56 54 Q42 54 33 54 z"/>'
                + thin("M41 47 l4 6 M48 44 l4 9 M62 44 l4 8 M69 46 l3 5", 2.4)
                + solid("M54 43 h5 v27 h-5 z"))


def clam_bed_no_water_symbol():
    # a scallop over a crossed-out wave: not enough clean water for the bed
    return (scallop(56, 46, 1.15, fill=True, rib_color=CUT).replace('fill="FILL"', 'fill="#BBA16C"')
            + '<path d="M32 78 q6 -6 12 0 t12 0 t12 0 t12 0" fill="none" stroke-width="5"/>'
            + '<path d="M38 92 L74 66" fill="none" stroke-width="6"/>')


def driftwood_no_current_symbol():
    # a log over a flat (still) line, crossed out: no current to bring driftwood
    return ('<path d="M34 40 H80 A8 11 0 0 1 80 62 H34 A8 11 0 0 1 34 40 Z" stroke-width="0"/>'
            f'<ellipse cx="80" cy="51" rx="5" ry="7.5" fill="none" stroke="{CUT}" stroke-width="2.6"/>'
            f'<circle cx="80" cy="51" r="1.8" fill="{CUT}" stroke-width="0"/>'
            f'<path d="M40 46 h16 M48 56 h18" fill="none" stroke="{CUT}" stroke-width="2.6"/>'
            '<path d="M28 76 h56" fill="none" stroke-width="5"/>'
            '<path d="M38 90 L74 66" fill="none" stroke-width="6"/>')


def render(name, size):
    body = globals()[name]()
    if size == 512:
        return status_icon(body, 512)
    if size == 80:
        return line_icon(body, 80, view=80, stroke=GOOD_STROKE)
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
         ("driftwood_no_current_symbol", 512, "Sprites/StatusIcons/OtterDriftwoodNoCurrent.png"),
         ("rice_cakes_good", 80, "Sprites/Goods/RiceCakesIcon.png"),
         ("sushi_good", 80, "Sprites/Goods/SushiIcon.png"),
         ("timber_tunnel", 112, "Buildings/Paths/TimberTunnel/TimberTunnelIcon.png"),
         ("timber_shaft", 112, "Buildings/Paths/TimberShaft/TimberShaftIcon.png"),
         ("sealed_timber_tunnel", 112, "Buildings/Paths/SealedTimberTunnel/SealedTimberTunnelIcon.png"),
         ("tunnel_lodge", 112, "Buildings/Paths/TunnelLodge/TunnelLodgeIcon.png")]
