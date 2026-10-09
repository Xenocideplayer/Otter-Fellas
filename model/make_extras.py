"""Models for the Tube Valve, the Clam Bed and the otters' wonder (the Wellspring), in the Folktails wood style.
usage: python3 make_extras.py CattailMature.timbermesh out_dir

  TubeValveWheel.Otters.Model        - laid over the game's tube models: a valve body on top of the tube, a stem
                                       and a wooden hand wheel; child nodes ValveOpenTag / ValveClosedTag (a teal or
                                       red flag on the hub) are switched by the WaterTubeValve component
  ClamBed.Otters.Model               - 3 x 3: a plank deck on the bank (row 0) and a staked net enclosure over the
                                       riverbed (rows 1-2, one block down) with a walkway, clams, baskets and a rake
  ClamBed.Otters.ConstructionStage0.Model
  Wellspring.Otters.Model            - 7 x 7 x 8 wonder: an octagonal log plinth with a door, a pool ring on top, a
                                       bundled-log column carrying a wide bowl that spills four streams into the
                                       pool, and a stick holt with a pennant on top
  Wellspring.Otters.ConstructionStage0..3.Model
"""
import math
import os
import sys

import numpy as np

import procmesh as pm
import timbermesh as tm

cattail_path, out = sys.argv[1:3]
os.makedirs(out, exist_ok=True)
cat = [n for n in tm.read(cattail_path).nodes if n.vertex_count][0]

LIGHT = "BaseWood_LightBrown.Folktails"
BROWN = "BaseWood_Brown.Folktails"
WHITE = "BaseWood_White.Folktails"
PLANKS = "IrregularPlanks_Brown.Folktails"
THATCH = "ThatchedRoof.Folktails"
TEAL = (0.30, 0.62, 0.70, 1)
RED = (0.72, 0.20, 0.14, 1)
IRON = (0.36, 0.36, 0.38, 1)
DARK_IRON = (0.22, 0.22, 0.24, 1)
ROPE = (0.62, 0.52, 0.34, 1)
WICKER = (0.80, 0.64, 0.40, 1)
WATER = (0.34, 0.62, 0.76, 1)
FOAM = (0.80, 0.90, 0.94, 1)
SHELLS = [(0.30, 0.30, 0.36, 1), (0.42, 0.40, 0.44, 1), (0.70, 0.66, 0.60, 1), (0.55, 0.50, 0.46, 1)]


def yaw(deg):
    a = math.radians(deg) / 2
    return (0.0, math.sin(a), 0.0, math.cos(a))


def slot(name, x, y, z, d=0.0):
    return tm.Node(0, name, (x, y, z), yaw(d), (1.0, 1.0, 1.0))


def reeds(name, x, y, z, s, d):
    n = tm.Node(0, name, (x, y, z), yaw(d), (s, s * 1.15, s))
    n.vertex_count = cat.vertex_count
    n.vertex_properties = list(cat.vertex_properties)
    n.meshes = [tm.MeshPart(mp.indices, mp.material) for mp in cat.meshes]
    return n


def ring(m, material, centre, radius, r, seg=14, color=(1, 1, 1, 1), y_axis=True):
    """A torus-ish ring of short cylinders lying flat (around the y axis)."""
    c = np.asarray(centre, float)
    for i in range(seg):
        a0 = 2 * math.pi * i / seg; a1 = 2 * math.pi * (i + 1) / seg
        p0 = c + np.array([math.cos(a0) * radius, 0, math.sin(a0) * radius])
        p1 = c + np.array([math.cos(a1) * radius, 0, math.sin(a1) * radius])
        pm.cylinder(m, material, p0, p1, r, seg=6, color=color, caps=False)


def clam(m, centre, size, rng, open_=False):
    """A small closed clam: a flattened, slightly ribbed ellipsoid."""
    col = SHELLS[rng.randint(len(SHELLS))]
    a = math.radians(rng.uniform(0, 360))
    A = pm.rot_y(math.degrees(a))
    tilt = rng.uniform(-0.25, 0.25)
    T = np.array([[1, 0, 0], [0, math.cos(tilt), -math.sin(tilt)], [0, math.sin(tilt), math.cos(tilt)]])
    pm.ellipsoid(m, WHITE, centre, (size, size * 0.42, size * 0.8), axes=A @ T, seg=8, rings=4, color=col)


def flag(m, base, height, color, width=0.16):
    base = np.asarray(base, float)
    pm.cylinder(m, BROWN, base, base + (0, height, 0), 0.012, seg=5)
    top = base + (0, height, 0)
    pm.triangle(m, WHITE, top, top - (0, width * 0.7, 0), top + (width, -width * 0.35, 0), color=color)


# ------------------------------------------------------------------------------------------------- tube valve
VALVE_C = np.array([0.5, 0.0, 0.5])


def tube_valve():
    m = pm.Mesh()
    x, z = VALVE_C[0], VALVE_C[2]
    pm.cylinder(m, WHITE, (x, 0.52, z), (x, 0.80, z), 0.2, seg=12, color=DARK_IRON)        # valve body over the tube
    pm.cylinder(m, WHITE, (x, 0.60, z), (x, 0.66, z), 0.215, seg=12, color=TEAL, caps=False)  # painted band
    pm.cylinder(m, WHITE, (x, 0.80, z), (x, 0.84, z), 0.13, seg=10, color=IRON)            # bonnet
    pm.cylinder(m, WHITE, (x, 0.84, z), (x, 0.98, z), 0.028, seg=6, color=IRON)            # stem
    # wooden hand wheel: rim, four spokes, hub
    ring(m, LIGHT, (x, 0.96, z), 0.17, 0.024, seg=14)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        pm.cylinder(m, BROWN, (x, 0.96, z), (x + math.cos(a) * 0.17, 0.96, z + math.sin(a) * 0.17), 0.016, seg=5,
                    caps=False)
    pm.cylinder(m, BROWN, (x, 0.94, z), (x, 0.99, z), 0.04, seg=8)
    pm.cylinder(m, BROWN, (x + 0.17, 0.96, z), (x + 0.17, 1.03, z), 0.018, seg=6)
    root = m.node("TubeValveWheel.Otters", parent=-1)
    tags = []
    for name, color in (("ValveOpenTag", TEAL), ("ValveClosedTag", RED)):
        t = pm.Mesh()
        flag(t, (x, 0.99, z), 0.26, color, width=0.17)
        pm.cylinder(t, WHITE, (x, 0.985, z), (x, 1.0, z), 0.045, seg=8, color=color)
        tags.append(t.node(name, parent=0))
    return tm.Model(0, "TubeValveWheel.Otters", [root, *tags])


# ------------------------------------------------------------------------------------------------- clam bed
DECK = 0.20
BED_FLOOR = -0.97


def deck(m, rng):
    for i in range(10):                                                       # boards across the bank row
        x0 = 0.02 + i * 0.296
        pm.box(m, LIGHT, (x0, DECK - 0.06, 0.0), (x0 + 0.28, DECK, 1.04), uv_offset=(0.13 * i, 0.07 * i))
    for zz in (0.12, 0.90):
        pm.box(m, BROWN, (0.0, DECK - 0.15, zz - 0.05), (3.0, DECK - 0.06, zz + 0.05))
    for x in (0.08, 1.5, 2.92):
        pm.cylinder(m, BROWN, (x, -0.5, 0.10), (x, DECK - 0.06, 0.10), 0.065, seg=7)


def stakes_and_net(m, height=0.32, full=True):
    """Stakes round the bed (rows 1-2) with net strung between them."""
    pts = []
    for zz in np.linspace(1.06, 2.94, 5):
        pts.append((0.07, zz))
    for xx in np.linspace(0.07, 2.93, 7)[1:-1]:
        pts.append((xx, 2.94))
    for zz in np.linspace(2.94, 1.06, 5):
        pts.append((2.93, zz))
    for i, (x, z) in enumerate(pts):
        h = height if full else height * (0.3 + 0.7 * ((i * 37) % 10) / 10) - 0.4
        pm.cylinder(m, BROWN, (x, -1.0, z), (x, h, z), 0.045, seg=6)
        pm.cone(m, LIGHT, (x, h, z), 0.07, 0.045, seg=6)
    if not full:
        return pts
    for a, b in zip(pts[:-1], pts[1:]):
        if np.hypot(a[0] - b[0], a[1] - b[1]) > 0.8:
            continue
        for y in (0.22, 0.02, -0.18, -0.38):
            pm.cylinder(m, WHITE, (a[0], y, a[1]), (b[0], y, b[1]), 0.009, seg=4, color=ROPE, caps=False)
        L = np.hypot(a[0] - b[0], a[1] - b[1])
        n = max(2, int(L / 0.12))
        for k in range(1, n):
            t = k / n
            x = a[0] + (b[0] - a[0]) * t; z = a[1] + (b[1] - a[1]) * t
            pm.cylinder(m, WHITE, (x, -0.42, z), (x, 0.24, z), 0.007, seg=4, color=ROPE, caps=False)
    return pts


def walkway(m):
    for k in range(6):                                                        # boards across the walkway
        z0 = 1.0 + k * 0.27
        pm.box(m, LIGHT, (1.22, 0.08, z0), (1.78, 0.13, z0 + 0.25), uv_offset=(0.2 * k, 0.1))
    for x in (1.27, 1.73):
        pm.box(m, BROWN, (x - 0.04, 0.0, 1.0), (x + 0.04, 0.08, 2.62))
        for zz in (1.45, 2.55):
            pm.cylinder(m, BROWN, (x, -1.0, zz), (x, 0.08, zz), 0.05, seg=6)


def basket(m, x, z, rng, h=0.26, r=0.15, full=True):
    pm.cylinder(m, WHITE, (x, DECK, z), (x, DECK + h, z), r, r * 1.15, seg=10, color=WICKER, caps=False)
    pm.cylinder(m, WHITE, (x, DECK, z), (x, DECK + 0.01, z), r, seg=10, color=WICKER)
    for y in (DECK + 0.06, DECK + h - 0.03):
        rr = r + (r * 0.15) * (y - DECK) / h
        ring(m, BROWN, (x, y, z), rr + 0.005, 0.012, seg=10)
    if full:
        for k in range(7):
            a = 2 * math.pi * k / 7 + rng.uniform(0, 0.4)
            rr = rng.uniform(0.0, r * 0.75)
            clam(m, (x + math.cos(a) * rr, DECK + h - 0.03 + rng.uniform(0, 0.03), z + math.sin(a) * rr), 0.055, rng)


def rake(m, base, top):
    base = np.asarray(base, float); top = np.asarray(top, float)
    pm.cylinder(m, LIGHT, base, top, 0.02, seg=6)
    d = (top - base) / np.linalg.norm(top - base)
    side = np.cross(d, [0, 1, 0]); side /= np.linalg.norm(side)
    head = base + d * 0.04
    pm.cylinder(m, BROWN, head - side * 0.16, head + side * 0.16, 0.022, seg=6)
    for k in range(6):
        p = head - side * 0.14 + side * (0.28 * k / 5)
        pm.cylinder(m, BROWN, p, p - d * 0.1 + np.array([0, -0.02, 0]), 0.008, seg=4)


def clam_bed():
    rng = np.random.RandomState(7)
    m = pm.Mesh()
    deck(m, rng)
    stakes_and_net(m)
    walkway(m)
    # clams on the riverbed in both halves, a few half buried
    for _ in range(46):
        x = rng.uniform(0.2, 2.8)
        if 1.12 < x < 1.88:
            continue
        z = rng.uniform(1.15, 2.85)
        clam(m, (x, BED_FLOOR + 0.02, z), rng.uniform(0.05, 0.075), rng)
    # baskets of clams and an empty one on the deck, a sorting table, a rake against the net
    basket(m, 0.42, 0.42, rng)
    basket(m, 0.80, 0.30, rng, h=0.22, r=0.13)
    basket(m, 2.55, 0.62, rng, full=False)
    pm.box(m, LIGHT, (1.95, DECK + 0.36, 0.14), (2.75, DECK + 0.41, 0.46))     # sorting table
    for x in (2.0, 2.7):
        for z in (0.19, 0.41):
            pm.box(m, BROWN, (x - 0.025, DECK, z - 0.025), (x + 0.025, DECK + 0.36, z + 0.025))
    for k in range(5):
        clam(m, (2.1 + 0.11 * k, DECK + 0.43, 0.30 + 0.04 * (k % 2)), 0.05, rng)
    rake(m, (0.25, DECK, 0.95), (0.12, DECK + 1.05, 1.02))
    # a teal pennant on the front-left stake
    flag(m, (0.07, 0.36, 1.06), 0.45, TEAL, width=0.22)
    nodes = [reeds("Reeds0", 2.75, -0.35, 2.75, 0.42, 30), reeds("Reeds1", 0.2, -0.35, 2.8, 0.38, 210),
             slot("#Slot#Entrance.001", 1.5, 0.13, 2.38, 0.0)]
    return pm.single_node_model("ClamBed.Otters", m, nodes)


def clam_bed_stage0():
    rng = np.random.RandomState(3)
    m = pm.Mesh()
    for i in range(4):                                                        # a few deck boards laid
        x0 = 0.02 + i * 0.296
        pm.box(m, LIGHT, (x0, DECK - 0.06, 0.0), (x0 + 0.28, DECK, 1.04), uv_offset=(0.13 * i, 0.07 * i))
    for zz in (0.12, 0.90):
        pm.box(m, BROWN, (0.0, DECK - 0.15, zz - 0.05), (3.0, DECK - 0.06, zz + 0.05))
    stakes_and_net(m, full=False)
    for k in range(4):                                                        # a stack of stakes and planks
        pm.cylinder(m, BROWN, (1.9, DECK + 0.05 + 0.09 * (k // 2), 0.25 + 0.1 * (k % 2)),
                    (2.85, DECK + 0.05 + 0.09 * (k // 2), 0.25 + 0.1 * (k % 2)), 0.045, seg=6)
    for k in range(3):
        pm.box(m, LIGHT, (1.9, DECK + 0.22 + 0.05 * k, 0.55), (2.85, DECK + 0.26 + 0.05 * k, 0.83))
    basket(m, 0.6, 0.5, rng, full=False)
    return pm.single_node_model("ClamBed.Otters.ConstructionStage0", m)


# ------------------------------------------------------------------------------------------------- wellspring
# 7 x 7 footprint with the corner blocks cut off (the Folktails wonder's block layout), centre (3.5, 3.5).
WC = np.array([3.5, 3.5])
PLINTH_H = 1.0          # top of the log plinth / deck
POOL_TOP = 1.62         # rim of the pool ring on the deck
POOL_WATER = 1.52
BOWL_Y0, BOWL_Y1 = 3.55, 4.45   # underside of the bowl: from the column out to the rim
BOWL_R = 2.2
BOWL_WATER = 4.66
HOLT_Y = 4.68


def octagon(inset=0.0, cut=1.0, size=7.0):
    """The footprint outline (x, z), counter-clockwise seen from above, moved inwards by `inset`."""
    c, s_ = cut, size
    pts = np.array([(c, 0), (s_ - c, 0), (s_, c), (s_, s_ - c), (s_ - c, s_), (c, s_), (0, s_ - c), (0, c)], float)
    if inset == 0:
        return pts
    n = len(pts)
    lines = []
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        d = (b - a) / np.linalg.norm(b - a)
        nrm = np.array([-d[1], d[0]])            # inward normal for a counter-clockwise outline
        if np.dot(WC - a, nrm) < 0:
            nrm = -nrm
        lines.append((a + nrm * inset, d))
    out_ = []
    for i in range(n):
        (p1, d1), (p2, d2) = lines[i - 1], lines[i]
        A = np.array([d1, -d2]).T
        t = np.linalg.solve(A, p2 - p1)
        out_.append(p1 + d1 * t[0])
    return np.array(out_)


def edges(poly):
    return [(poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly))]


def poly_slab(m, material, poly, y0, y1, color=(1, 1, 1, 1), sides=True):
    """A flat slab with a polygon outline (fan triangulated, planar UVs)."""
    c = poly.mean(axis=0)
    for y, nrm in ((y1, (0, 1, 0)), (y0, (0, -1, 0))):
        P = [(c[0], y, c[1])] + [(p[0], y, p[1]) for p in poly]
        UV = [(p[0] * pm.UV_PER_METRE, p[2] * pm.UV_PER_METRE) for p in P]
        tris = [(0, 1 + i, 1 + (i + 1) % len(poly)) for i in range(len(poly))]
        m.add(material, P, [nrm] * len(P), UV, tris, color)
    if sides and y1 - y0 > 1e-4:
        for a, b in edges(poly):
            d = b - a; L = np.linalg.norm(d)
            nrm = np.array([d[1], 0, -d[0]]) / L
            if np.dot(np.array([a[0] - c[0], 0, a[1] - c[1]]), nrm) < 0:
                nrm = -nrm
            P = [(a[0], y0, a[1]), (b[0], y0, b[1]), (b[0], y1, b[1]), (a[0], y1, a[1])]
            UV = [(0, y0 * pm.UV_PER_METRE), (L * pm.UV_PER_METRE, y0 * pm.UV_PER_METRE),
                  (L * pm.UV_PER_METRE, y1 * pm.UV_PER_METRE), (0, y1 * pm.UV_PER_METRE)]
            m.add(material, P, [nrm] * 4, UV, [(0, 1, 2), (0, 2, 3)], color)


def log_palisade(m, poly, y0, y1, r=0.11, skip=None, frac=1.0):
    """Upright logs along every edge of the outline (skip(x, z) -> True leaves a gap, e.g. for the door)."""
    k = 0
    for a, b in edges(poly):
        L = np.linalg.norm(b - a)
        n = max(1, int(round(L / (2 * r * 0.98))))
        for i in range(n):
            p = a + (b - a) * (i + 0.5) / n
            if skip and skip(p[0], p[1]):
                continue
            h = y0 + (y1 - y0) * (frac if frac >= 1 else min(1.0, frac * (0.6 + 0.8 * ((k * 53) % 17) / 17)))
            k += 1
            if h <= y0 + 0.05:
                continue
            mat = LIGHT if k % 3 else BROWN
            pm.cylinder(m, mat, (p[0], y0, p[1]), (p[0], h, p[1]), r, seg=7, uv_offset=(0.37 * k, 0.11 * k))
            pm.cylinder(m, mat, (p[0], h, p[1]), (p[0], h + 0.05, p[1]), r * 0.95, r * 0.6, seg=7)


def log_courses(m, poly, y0, courses, r=0.1, color=(1, 1, 1, 1), upto=None):
    """Horizontal logs stacked along each edge, overlapping at the corners like a log cabin."""
    for j in range(courses):
        y = y0 + r + j * 2 * r * 0.92
        for i, (a, b) in enumerate(edges(poly)):
            if upto is not None and i >= upto:
                break
            d = (b - a) / np.linalg.norm(b - a)
            a2 = a - d * r * 1.3; b2 = b + d * r * 1.3
            mat = BROWN if (i + j) % 2 else LIGHT
            pm.cylinder(m, mat, (a2[0], y, a2[1]), (b2[0], y, b2[1]), r, seg=7, color=color, uv_offset=(0.2 * i, 0.3 * j))


def door_skip(x, z):
    return z < 0.5 and 2.95 < x < 4.05


def plinth(m, frac=1.0, deck=True, door=True):
    outer = octagon(0.12)
    log_palisade(m, outer, 0.0, PLINTH_H - 0.04, skip=door_skip if door else None, frac=frac)
    if frac < 1:
        return
    # rim beams on top of the palisade, and a painted band
    for i, (a, b) in enumerate(edges(octagon(0.1))):
        d = (b - a) / np.linalg.norm(b - a)
        pm.beam(m, BROWN, (a[0] - d[0] * 0.08, PLINTH_H - 0.06, a[1] - d[1] * 0.08),
                (b[0] + d[0] * 0.08, PLINTH_H - 0.06, b[1] + d[1] * 0.08), 0.16, 0.12)
        pm.beam(m, WHITE, (a[0], 0.62, a[1]), (b[0], 0.62, b[1]), 0.25, 0.08, color=TEAL)
    if deck:
        poly_slab(m, PLANKS, octagon(0.2), PLINTH_H - 0.08, PLINTH_H, sides=False)
    if door:
        # door: frame, lintel, plank leaves, step
        for x in (2.97, 4.03):
            pm.beam(m, BROWN, (x, 0.0, 0.12), (x, 0.92, 0.12), 0.12)
        pm.beam(m, BROWN, (2.85, 0.90, 0.12), (4.15, 0.90, 0.12), 0.14, 0.14)
        pm.box(m, PLANKS, (3.03, 0.0, 0.16), (3.97, 0.86, 0.30), color=(0.75, 0.68, 0.6, 1))
        pm.box(m, WHITE, (3.47, 0.02, 0.10), (3.53, 0.84, 0.16), color=(0.25, 0.2, 0.16, 1))
        for x in (3.36, 3.64):
            pm.cylinder(m, WHITE, (x, 0.45, 0.10), (x, 0.45, 0.07), 0.03, seg=6, color=IRON)
        pm.box(m, LIGHT, (2.9, 0.0, -0.14), (4.1, 0.08, 0.12))
        # banners either side of the door: teal cloth with a pale wave
        for x in (2.25, 4.75):
            pm.box(m, WHITE, (x - 0.24, 0.18, 0.04), (x + 0.24, 0.92, 0.07), color=TEAL)
            for k in range(4):
                pm.box(m, WHITE, (x - 0.2 + k * 0.1, 0.48 + 0.04 * (k % 2), 0.035), (x - 0.1 + k * 0.1, 0.53 + 0.04 * (k % 2), 0.04),
                       color=FOAM)
            pm.cylinder(m, BROWN, (x - 0.3, 0.93, 0.05), (x + 0.3, 0.93, 0.05), 0.025, seg=6)


def pool_ring(m, courses=3, water=True, upto=None):
    ring_poly = octagon(0.78)
    log_courses(m, ring_poly, PLINTH_H, courses, r=0.1, upto=upto)
    if water:
        poly_slab(m, WHITE, octagon(0.9), POOL_WATER - 0.02, POOL_WATER, color=WATER, sides=False)


def column(m, top=BOWL_Y0 + 0.25, bands=True):
    logs = [(0.0, 0.0, 0.24)] + [(math.cos(a) * 0.42, math.sin(a) * 0.42, 0.2) for a in np.linspace(0, 2 * math.pi, 7)[:-1]]
    for i, (dx, dz, r) in enumerate(logs):
        x, z = WC[0] + dx, WC[1] + dz
        h = top + (0.08 if i == 0 else -0.04 * (i % 3))
        pm.cylinder(m, LIGHT if i % 2 else BROWN, (x, PLINTH_H - 0.05, z), (x, h, z), r, seg=8, uv_offset=(0.3 * i, 0))
    if bands:
        for y in (2.1, 3.0):
            pm.cylinder(m, WHITE, (WC[0], y, WC[1]), (WC[0], y + 0.12, WC[1]), 0.66, seg=12, color=TEAL)
            pm.cylinder(m, WHITE, (WC[0], y + 0.12, WC[1]), (WC[0], y + 0.16, WC[1]), 0.67, seg=12, color=ROPE, caps=False)


def bowl_frame(m, planked=True):
    c = np.array([WC[0], 0, WC[1]])
    for k in range(8):                                                        # struts from the column
        a = 2 * math.pi * (k + 0.5) / 8
        d = np.array([math.cos(a), 0, math.sin(a)])
        pm.beam(m, BROWN, c + d * 0.55 + (0, 2.35, 0), c + d * 1.75 + (0, BOWL_Y0 + 0.62, 0), 0.11)
        pm.beam(m, LIGHT, c + d * 0.62 + (0, BOWL_Y0 - 0.02, 0), c + d * (BOWL_R + 0.02) + (0, BOWL_Y1 + 0.02, 0), 0.1, 0.08)
    if planked:
        pm.cylinder(m, PLANKS, (WC[0], BOWL_Y0, WC[1]), (WC[0], BOWL_Y1, WC[1]), 0.62, BOWL_R, seg=16, caps=True)
        pm.cylinder(m, LIGHT, (WC[0], BOWL_Y1, WC[1]), (WC[0], BOWL_WATER + 0.12, WC[1]), BOWL_R, seg=16, caps=False)
        pm.cylinder(m, LIGHT, (WC[0], BOWL_WATER + 0.12, WC[1]), (WC[0], BOWL_Y1, WC[1]), BOWL_R - 0.08, seg=16, caps=False)
        ring(m, BROWN, (WC[0], BOWL_WATER + 0.12, WC[1]), BOWL_R - 0.04, 0.08, seg=16)
        ring(m, WHITE, (WC[0], BOWL_Y1 + 0.08, WC[1]), BOWL_R + 0.01, 0.05, seg=16, color=TEAL)
    else:
        ring(m, BROWN, (WC[0], BOWL_Y1 + 0.02, WC[1]), BOWL_R, 0.08, seg=16)
        ring(m, BROWN, (WC[0], BOWL_Y0 + 0.4, WC[1]), 1.45, 0.06, seg=12)


def bowl_water_and_streams(m):
    pm.cylinder(m, WHITE, (WC[0], BOWL_WATER - 0.02, WC[1]), (WC[0], BOWL_WATER, WC[1]), BOWL_R - 0.08, seg=16,
                color=WATER)
    for k in range(4):
        a = 2 * math.pi * (k + 0.5) / 4                                      # the four diagonals
        d = np.array([math.cos(a), 0, math.sin(a)])
        side = np.array([-d[2], 0, d[0]])
        c = np.array([WC[0], 0, WC[1]])
        lip0 = c + d * (BOWL_R - 0.15) + (0, BOWL_WATER - 0.02, 0)
        lip1 = c + d * (BOWL_R + 0.32) + (0, BOWL_WATER - 0.08, 0)
        # carved spout: a trough with side boards
        pm.beam(m, BROWN, lip0 - (0, 0.08, 0), lip1 - (0, 0.08, 0), 0.3, 0.06)
        for sgn in (-1, 1):
            pm.beam(m, LIGHT, lip0 + side * 0.15 * sgn, lip1 + side * 0.15 * sgn, 0.04, 0.16)
        pm.beam(m, WHITE, lip0 + (0, 0.0, 0), lip1 + (0, -0.01, 0), 0.22, 0.03, color=WATER)
        # the stream: arcs off the lip and falls into the pool ring below
        prev = lip1 + (0, -0.01, 0)
        for t in np.linspace(0.08, 1.0, 9):
            p = lip1 + d * (0.16 * math.sqrt(t)) + (0, -(BOWL_WATER - POOL_WATER - 0.08) * t, 0)
            w = 0.3 + 0.1 * t
            pm.beam(m, WHITE, prev, p, w, 0.04, color=tuple(np.array(WATER) * (1 - 0.3 * t) + np.array(FOAM) * 0.3 * t))
            prev = p
        splash = np.array([prev[0], POOL_WATER + 0.01, prev[2]])
        pm.ellipsoid(m, WHITE, splash, (0.3, 0.06, 0.3), seg=10, rings=4, color=FOAM)


def holt(m):
    c = np.array([WC[0], HOLT_Y, WC[1]])
    pm.ellipsoid(m, BROWN, c, (1.05, 1.2, 1.05), seg=14, rings=8)
    rng = np.random.RandomState(11)
    for k in range(46):                                                       # sticks laid over the dome
        th = rng.uniform(0.15, 1.45); ph = rng.uniform(0, 2 * math.pi)
        n = np.array([math.sin(th) * math.cos(ph), math.cos(th), math.sin(th) * math.sin(ph)])
        p = c + n * np.array([1.05, 1.2, 1.05])
        t = np.cross(n, [0, 1, 0]); t = t / (np.linalg.norm(t) + 1e-9)
        t = t * math.cos(rng.uniform(0, math.pi)) + np.cross(n, t) * math.sin(rng.uniform(0, math.pi))
        L = rng.uniform(0.45, 0.8)
        pm.cylinder(m, LIGHT if k % 3 else BROWN, p - t * L / 2 + n * 0.03, p + t * L / 2 + n * 0.03, 0.035, seg=5)
    # a doorway facing the front, with a little landing to dive off
    door = c + np.array([0, 0.0, -1.0])
    pm.ellipsoid(m, WHITE, door + (0, 0.32, 0.02), (0.32, 0.4, 0.1), seg=10, rings=5, color=(0.16, 0.12, 0.10, 1))
    pm.box(m, LIGHT, (WC[0] - 0.4, HOLT_Y - 0.06, WC[1] - 1.55), (WC[0] + 0.4, HOLT_Y + 0.02, WC[1] - 0.9))
    # pole and pennant
    top = c + (0, 1.15, 0)
    pm.cylinder(m, BROWN, top, top + (0, 1.65, 0), 0.04, seg=6)
    pm.triangle(m, WHITE, top + (0, 1.6, 0), top + (0, 1.25, 0), top + (0.62, 1.44, 0), color=TEAL)
    pm.cylinder(m, WHITE, top + (0, 1.65, 0), top + (0, 1.72, 0), 0.06, seg=8, color=TEAL)


def lily_pads(m, rng, n=9):
    for _ in range(n):
        a = rng.uniform(0, 2 * math.pi); r = rng.uniform(1.0, 2.2)
        x, z = WC[0] + math.cos(a) * r, WC[1] + math.sin(a) * r
        pm.cylinder(m, WHITE, (x, POOL_WATER, z), (x, POOL_WATER + 0.015, z), rng.uniform(0.12, 0.2), seg=9,
                    color=(0.36, 0.55, 0.24, 1))


def scaffold(m, pts, y1, levels=()):
    for x, z in pts:
        pm.cylinder(m, BROWN, (x, 0.0, z), (x, y1, z), 0.045, seg=6)
    for a, b in zip(pts, pts[1:] + pts[:1]):
        for y in levels:
            pm.cylinder(m, LIGHT, (a[0], y, a[1]), (b[0], y, b[1]), 0.035, seg=5)
        pm.cylinder(m, LIGHT, (a[0], 0.3, a[1]), (b[0], y1 - 0.2, b[1]), 0.025, seg=5)  # diagonal brace


def log_pile(m, x, z, n=6, length=1.4, along_x=True):
    k = 0
    for row in range(3):
        for i in range(n - row * 2):
            off = (i - (n - row * 2 - 1) / 2) * 0.17
            y = 0.08 + row * 0.15
            if along_x:
                pm.cylinder(m, LIGHT if k % 2 else BROWN, (x - length / 2, y, z + off), (x + length / 2, y, z + off), 0.08, seg=7)
            else:
                pm.cylinder(m, LIGHT if k % 2 else BROWN, (x + off, y, z - length / 2), (x + off, y, z + length / 2), 0.08, seg=7)
            k += 1


def plank_stack(m, x, z, n=5, length=1.2):
    for i in range(n):
        pm.box(m, LIGHT, (x - length / 2, 0.02 + i * 0.06, z - 0.2), (x + length / 2, 0.06 + i * 0.06, z + 0.2),
               uv_offset=(0.1 * i, 0.2 * i))


def ring_slots(prefix, n, radius, y, start=0.0, avoid_front=True):
    nodes = []
    k = 0
    for i in range(n * 3):
        if k >= n:
            break
        a = start + 2 * math.pi * i / (n + (2 if avoid_front else 0))
        x, z = WC[0] + math.cos(a) * radius, WC[1] + math.sin(a) * radius
        if avoid_front and z < WC[1] - radius * 0.8 and abs(x - WC[0]) < 0.9:
            continue
        face = math.degrees(math.atan2(WC[0] - x, WC[1] - z))
        k += 1
        nodes.append(slot(f"#Slot#{prefix}.{k:03d}", x, y, z, face))
    return nodes


def wellspring():
    rng = np.random.RandomState(5)
    m = pm.Mesh()
    plinth(m)
    pool_ring(m)
    lily_pads(m, rng)
    column(m)
    bowl_frame(m)
    bowl_water_and_streams(m)
    holt(m)
    # little teal pennants round the deck edge
    for p in octagon(0.25):
        flag(m, (p[0], PLINTH_H, p[1]), 0.6, TEAL, width=0.2)
    nodes = [reeds(f"Reeds{i}", WC[0] + math.cos(a) * 2.2, POOL_WATER - 0.35, WC[1] + math.sin(a) * 2.2, 0.5, 40 * i)
             for i, a in enumerate((0.4, 1.9, 2.6, 4.1, 5.2))]
    nodes += ring_slots("Working", 10, 3.08, PLINTH_H, start=math.radians(-60))
    nodes.append(slot("#Slot#Entrance.001", 3.5, 0.0, -0.35, 180.0))
    return pm.single_node_model("Wellspring.Otters", m, nodes)


def stage_slots():
    nodes = ring_slots("Building", 12, 3.85, 0.0, start=math.radians(-75))
    nodes += [slot(f"#Slot#Cutting.{i + 1:03d}", x, 0.0, z, d) for i, (x, z, d) in
              enumerate([(-0.45, 1.2, 90), (7.45, 1.2, -90), (-0.45, 5.6, 90), (7.45, 5.6, -90)])]
    nodes += [slot(f"#Slot#Digging.{i + 1:03d}", x, 0.0, z, d) for i, (x, z, d) in
              enumerate([(1.6, -0.45, 0), (5.4, -0.45, 0), (1.6, 7.45, 180), (5.4, 7.45, 180)])]
    return nodes


def wellspring_stage(k):
    rng = np.random.RandomState(20 + k)
    m = pm.Mesh()
    if k == 0:
        # the outline pegged out with logs, ropes and stakes; materials piled ready
        outer = octagon(0.15)
        for a, b in edges(outer):
            pm.cylinder(m, BROWN, (a[0], 0.08, a[1]), (b[0], 0.08, b[1]), 0.08, seg=7)
        for p in outer:
            pm.cylinder(m, LIGHT, (p[0], 0.0, p[1]), (p[0], 0.55, p[1]), 0.04, seg=6)
            pm.cone(m, LIGHT, (p[0], 0.55, p[1]), 0.06, 0.04, seg=6)
        for a, b in edges(outer):
            pm.cylinder(m, WHITE, (a[0], 0.45, a[1]), (b[0], 0.45, b[1]), 0.008, seg=4, color=ROPE, caps=False)
        poly_slab(m, PLANKS, octagon(1.6), 0.0, 0.06)
        pm.cylinder(m, LIGHT, (WC[0], 0.0, WC[1]), (WC[0], 0.9, WC[1]), 0.06, seg=6)
        flag(m, (WC[0], 0.9, WC[1]), 0.3, TEAL)
        log_pile(m, 1.9, 1.6)
        plank_stack(m, 5.1, 1.6)
        log_pile(m, 5.3, 5.2, along_x=False)
        plank_stack(m, 1.9, 5.3)
    else:
        plinth(m, frac=[0.55, 1.0, 1.0][k - 1], deck=k >= 2, door=True)
        if k == 1:
            poly_slab(m, PLANKS, octagon(1.6), 0.0, 0.06)
            column(m, top=1.4, bands=False)
            log_pile(m, 2.0, 2.0)
            plank_stack(m, 5.0, 2.0)
            scaffold(m, [(1.2, 1.0), (5.8, 1.0), (5.8, 6.0), (1.2, 6.0)], 1.4, levels=(0.8,))
        if k == 2:
            pool_ring(m, courses=2, water=False, upto=5)
            column(m, top=3.0, bands=False)
            sc = [(WC[0] + x, WC[1] + z) for x, z in ((-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, 1.0))]
            for x, z in sc:
                pm.cylinder(m, BROWN, (x, PLINTH_H, z), (x, 3.2, z), 0.045, seg=6)
            for a, b in zip(sc, sc[1:] + sc[:1]):
                for y in (1.9, 2.9):
                    pm.cylinder(m, LIGHT, (a[0], y, a[1]), (b[0], y, b[1]), 0.035, seg=5)
            pm.box(m, LIGHT, (WC[0] - 1.0, 2.88, WC[1] - 1.0), (WC[0] + 1.0, 2.94, WC[1] - 0.6))
            plank_stack(m, 1.3, 3.3, length=0.9)
        if k == 3:
            pool_ring(m, water=False)
            column(m)
            bowl_frame(m, planked=False)
            pts = [(WC[0] + 2.3 * math.cos(a), WC[1] + 2.3 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 5)[:-1] + math.pi / 4]
            for x, z in pts:
                pm.cylinder(m, BROWN, (x, PLINTH_H, z), (x, 4.8, z), 0.045, seg=6)
            for a, b in zip(pts, pts[1:] + pts[:1]):
                for y in (2.6, 4.2):
                    pm.cylinder(m, LIGHT, (a[0], y, a[1]), (b[0], y, b[1]), 0.035, seg=5)
    return pm.single_node_model(f"Wellspring.Otters.ConstructionStage{k}", m, stage_slots())


MODELS = [("TubeValveWheel.Otters.Model", tube_valve), ("ClamBed.Otters.Model", clam_bed),
          ("ClamBed.Otters.ConstructionStage0.Model", clam_bed_stage0), ("Wellspring.Otters.Model", wellspring)]
MODELS += [(f"Wellspring.Otters.ConstructionStage{k}.Model", (lambda k=k: wellspring_stage(k))) for k in range(4)]

if __name__ == "__main__":
    for name, make in MODELS:
        model = make()
        tm.write(model, os.path.join(out, name + ".timbermesh"))
        print(name, sum(n.vertex_count for n in model.nodes), "verts")
