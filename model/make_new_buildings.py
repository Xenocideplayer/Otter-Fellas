"""Models for the Driftwood Catch and the Basking Deck.

Driftwood Catch (3 x 3, like the Clam Bed: a deck row on the bank, two rows of river one block down): a log boom on
posts funnels driftwood towards the deck, a few caught logs bob inside it, a hand winch and a log pile on the deck.
Basking Deck (2 x 2 on the bank): a low sun deck with reed mats and a warm flat stone for otters to sprawl on.

Model space: x right, y up (0 = top of the bank), z back (towards the water); 1 unit = 1 block.
usage: python3 make_new_buildings.py out_dir
"""
import math
import os
import sys

import numpy as np

import procmesh as pm
import timbermesh as tm

out_dir = sys.argv[1]
os.makedirs(out_dir, exist_ok=True)

LIGHT = "BaseWood_LightBrown.Folktails"
BROWN = "BaseWood_Brown.Folktails"
WHITE = "BaseWood_White.Folktails"
THATCH = "ThatchedRoof.Folktails"
ROPE = (0.78, 0.68, 0.48, 1)
BARK = (0.78, 0.66, 0.55, 1)
WET = (0.62, 0.58, 0.55, 1)
STONE = (0.56, 0.56, 0.54, 1)
MAT = (0.86, 0.76, 0.50, 1)
TOWEL = [(0.36, 0.58, 0.66, 1), (0.82, 0.52, 0.36, 1)]
rng = np.random.default_rng(11)


def yaw(deg):
    a = math.radians(deg) / 2
    return (0.0, math.sin(a), 0.0, math.cos(a))


def slot(name, x, y, z, d=0.0):
    return tm.Node(0, name, (x, y, z), yaw(d), (1.0, 1.0, 1.0))


def log(m, p0, p1, r=0.075, color=BARK, wet=False):
    """A log: bark along the length, light cut ends."""
    pm.cylinder(m, BROWN, p0, p1, r, seg=8, caps=False, color=WET if wet else color,
                uv_offset=(rng.uniform(0, 1), rng.uniform(0, 1)))
    p0 = np.asarray(p0, float); p1 = np.asarray(p1, float)
    d = (p1 - p0) / np.linalg.norm(p1 - p0)
    pm.cylinder(m, LIGHT, p0 - d * 0.004, p0 + d * 0.004, r * 0.96, seg=8)
    pm.cylinder(m, LIGHT, p1 - d * 0.004, p1 + d * 0.004, r * 0.96, seg=8)


def post(m, x, z, y0, y1, r=0.055):
    pm.cylinder(m, BROWN, (x, y0, z), (x, y1, z), r, seg=7)
    pm.cone(m, LIGHT, (x, y1, z), 0.06, r, seg=7)


def rope(m, a, b, r=0.012):
    pm.cylinder(m, WHITE, a, b, r, seg=4, color=ROPE, caps=False)


def finish(name, m, extra_nodes=()):
    model = pm.single_node_model(name, m, extra_nodes)
    node = model.nodes[0]
    path = os.path.join(out_dir, name + ".Model.timbermesh")
    tm.write(model, path)
    print("wrote", path, node.vertex_count, "verts")


# ------------------------------------------------------------------------------------------- driftwood catch
DECK = 0.20
FLOAT_Y = -0.22


def deck(m, width=3.0, depth=1.04):
    n = int(width / 0.3)
    for i in range(n):
        x0 = 0.02 + i * (width - 0.04) / n
        pm.box(m, LIGHT, (x0, DECK - 0.06, 0.0), (x0 + (width - 0.04) / n - 0.02, DECK, depth), uv_offset=(0.13 * i, 0.07 * i))
    for zz in (0.12, depth - 0.14):
        pm.box(m, BROWN, (0.0, DECK - 0.15, zz - 0.05), (width, DECK - 0.06, zz + 0.05))
    for x in (0.08, width / 2, width - 0.08):
        pm.cylinder(m, BROWN, (x, -0.6, 0.10), (x, DECK - 0.06, 0.10), 0.065, seg=7)
        pm.cylinder(m, BROWN, (x, -1.0, depth - 0.08), (x, DECK - 0.06, depth - 0.08), 0.065, seg=7)


def driftwood_catch(stage0=False):
    m = pm.Mesh()
    deck(m)
    if stage0:
        for x, z in ((0.15, 2.85), (2.85, 2.85), (0.8, 2.0), (2.2, 2.0)):
            post(m, x, z, -1.0, -0.2)
        finish("DriftwoodCatch.Otters.ConstructionStage0", m)
        return
    # boom posts and a V of floating logs chained between them, opening upstream (away from the deck)
    apex_l, apex_r = np.array([1.18, FLOAT_Y, 1.22]), np.array([1.82, FLOAT_Y, 1.22])
    for x, z in ((0.15, 2.85), (2.85, 2.85), (0.62, 2.0), (2.38, 2.0), (1.05, 1.18), (1.95, 1.18)):
        post(m, x, z, -1.0, 0.42)
    for side, (far, mid, apex) in enumerate((((0.15, 2.85), (0.62, 2.0), apex_l), ((2.85, 2.85), (2.38, 2.0), apex_r))):
        pts = [np.array([far[0] + (0.07 if side == 0 else -0.07), FLOAT_Y, far[1] - 0.06]),
               np.array([mid[0] + (0.06 if side == 0 else -0.06), FLOAT_Y, mid[1]]), apex]
        for a, b in zip(pts[:-1], pts[1:]):
            d = (b - a) / np.linalg.norm(b - a)
            log(m, a + d * 0.05, b - d * 0.05, r=0.07, wet=True)
            rope(m, b - d * 0.05 + (0, 0.05, 0), b + (0, 0.05, 0))
        for p, q in zip(pts, ((far[0], 0.30, far[1]), (mid[0], 0.30, mid[1]), (apex[0] + (-0.13 if side == 0 else 0.13), 0.30, 1.18))):
            rope(m, p + (0, 0.06, 0), q)
    # driftwood caught in the funnel
    for (x, z, a, L) in ((1.5, 1.55, 15, 0.9), (1.25, 1.95, -35, 0.8), (1.78, 2.15, 60, 0.7), (1.45, 2.45, -10, 0.85)):
        d = np.array([math.cos(math.radians(a)), 0.0, math.sin(math.radians(a))])
        c = np.array([x, FLOAT_Y + rng.uniform(-0.02, 0.02), z])
        log(m, c - d * L / 2, c + d * L / 2, r=rng.uniform(0.055, 0.08), wet=True)
        if rng.random() < 0.6:  # a stub of a branch
            pm.cylinder(m, BROWN, c + d * L * 0.2, c + d * L * 0.2 + np.array([0.0, 0.1, 0.12]), 0.022, seg=5, color=WET)
    # winch on the deck, rope out to the boom's mouth
    for x in (1.28, 1.72):
        pm.box(m, BROWN, (x - 0.04, DECK, 0.62), (x + 0.04, DECK + 0.48, 0.70))
    pm.cylinder(m, LIGHT, (1.24, DECK + 0.38, 0.66), (1.76, DECK + 0.38, 0.66), 0.075, seg=10)
    for k in range(6):
        pm.cylinder(m, WHITE, (1.34 + 0.06 * k, DECK + 0.38, 0.66), (1.36 + 0.06 * k, DECK + 0.38, 0.66), 0.083, seg=10, color=ROPE)
    pm.beam(m, BROWN, (1.76, DECK + 0.38, 0.66), (1.92, DECK + 0.38, 0.66), 0.03)
    pm.beam(m, BROWN, (1.92, DECK + 0.38, 0.66), (1.92, DECK + 0.20, 0.66), 0.03)
    rope(m, (1.5, DECK + 0.42, 0.74), (1.5, FLOAT_Y + 0.08, 1.30))
    # landed logs drying on the deck, and a pike pole
    for row, (n, y) in enumerate(((4, DECK + 0.075), (3, DECK + 0.205))):
        for i in range(n):
            x = 2.25 + (i - (n - 1) / 2) * 0.15
            log(m, (x, y, 0.08), (x, y, 0.92), r=0.072)
    log(m, (0.18, DECK + 0.07, 0.25), (0.88, DECK + 0.07, 0.35), r=0.07)
    pm.cylinder(m, LIGHT, (0.30, DECK, 0.85), (0.95, DECK + 1.15, 1.02), 0.018, seg=5)
    pm.cone(m, WHITE, (0.95, DECK + 1.15, 1.02), 0.08, 0.02, seg=5, color=STONE)
    finish("DriftwoodCatch.Otters", m, [slot("#Slot#Entrance.001", 1.5, DECK, 0.9, 0.0)])


# ------------------------------------------------------------------------------------------- basking deck
BD = 0.16


def basking_deck(stage0=False):
    m = pm.Mesh()
    for i in range(7):                                                  # boards run front to back
        x0 = 0.03 + i * 0.278
        pm.box(m, LIGHT, (x0, BD - 0.05, 0.03), (x0 + 0.26, BD, 1.97), uv_offset=(0.11 * i, 0.05 * i))
    for zz in (0.15, 1.0, 1.85):
        pm.box(m, BROWN, (0.0, BD - 0.14, zz - 0.05), (2.0, BD - 0.05, zz + 0.05))
    for x in (0.08, 1.92):
        for zz in (0.15, 1.85):
            pm.cylinder(m, BROWN, (x, -0.3, zz), (x, BD - 0.05, zz), 0.06, seg=7)
    if stage0:
        finish("BaskingDeck.Otters.ConstructionStage0", m)
        return
    # reed mats with bound ends
    for (x0, z0, x1, z1) in ((0.15, 0.25, 0.85, 1.05), (1.15, 0.25, 1.85, 1.05)):
        pm.box(m, WHITE, (x0, BD, z0), (x1, BD + 0.025, z1), color=MAT)
        for zz in (z0 + 0.06, z1 - 0.06):
            pm.box(m, WHITE, (x0 - 0.01, BD, zz - 0.02), (x1 + 0.01, BD + 0.032, zz + 0.02), color=ROPE)
    # a rolled-up towel on each mat
    for k, x in enumerate((0.5, 1.5)):
        pm.cylinder(m, WHITE, (x - 0.22, BD + 0.08, 0.98), (x + 0.22, BD + 0.08, 0.98), 0.06, seg=8, color=TOWEL[k])
    # the big flat stone at the back, warm from the sun
    pm.ellipsoid(m, WHITE, (1.0, BD + 0.05, 1.5), (0.62, 0.11, 0.36), seg=12, rings=6, color=STONE)
    pm.ellipsoid(m, WHITE, (1.62, BD + 0.03, 1.72), (0.18, 0.08, 0.15), seg=8, rings=5, color=(0.5, 0.5, 0.48, 1))
    pm.ellipsoid(m, WHITE, (0.32, BD + 0.03, 1.78), (0.14, 0.06, 0.12), seg=8, rings=5, color=(0.6, 0.6, 0.57, 1))
    # a low rail with a hanging net bag and a sun pole with a pennant
    for x in (0.06, 1.94):
        pm.box(m, BROWN, (x - 0.03, BD, 1.92), (x + 0.03, BD + 0.42, 1.98))
    pm.beam(m, LIGHT, (0.03, BD + 0.40, 1.95), (1.97, BD + 0.40, 1.95), 0.05)
    pm.cylinder(m, BROWN, (1.92, BD, 0.08), (1.92, BD + 1.25, 0.08), 0.03, seg=6)
    pm.triangle(m, WHITE, (1.92, BD + 1.22, 0.08), (1.92, BD + 1.02, 0.08), (2.0 - 0.38, BD + 1.12, 0.08), color=(0.30, 0.55, 0.62, 1))
    for k in range(3):                                                   # shells drying on the rail
        pm.ellipsoid(m, WHITE, (0.5 + 0.45 * k, BD + 0.45, 1.95), (0.05, 0.02, 0.045), seg=6, rings=4,
                     color=(0.78, 0.74, 0.68, 1))
    slots = [slot("#Slot#Bask.001", 0.5, BD + 0.03, 0.62, 180.0), slot("#Slot#Bask.002", 1.5, BD + 0.03, 0.62, 180.0),
             slot("#Slot#Sun.001", 0.75, BD + 0.15, 1.45, 90.0), slot("#Slot#Sun.002", 1.35, BD + 0.15, 1.5, 270.0)]
    finish("BaskingDeck.Otters", m, slots)


driftwood_catch()
driftwood_catch(stage0=True)
basking_deck()
basking_deck(stage0=True)
