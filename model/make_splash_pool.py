"""Splash Pool model: a Folktails-style log frame set into the river with a plank deck, a diving board, a
ladder, a bench and reeds, plus the slots otters use (2 seats on the bench, 4 floating in the pool).
Footprint and heights follow the Iron Teeth Swimming Pool (3 x 4, deck row at ground level, pool rows over
water, frame reaching one block down).
usage: python3 make_splash_pool.py CattailMature.timbermesh out.timbermesh"""
import math
import sys

import numpy as np

import procmesh as pm
import timbermesh as tm

cattail_path, out = sys.argv[1:3]
cat = [n for n in tm.read(cattail_path).nodes if n.vertex_count][0]

LIGHT = "BaseWood_LightBrown.Folktails"
BROWN = "BaseWood_Brown.Folktails"
PLANKS = "IrregularPlanks_Brown.Folktails"
WHITE = "BaseWood_White.Folktails"

m = pm.Mesh()
DECK = 0.20

# --- front deck (row 0): boards running front-to-back on two joists, posts into the ground
for i in range(10):
    x0 = 0.02 + i * 0.296
    pm.box(m, LIGHT, (x0, DECK - 0.06, 0.0), (x0 + 0.28, DECK, 1.06), uv_offset=(0.13 * i, 0.07 * i))
for z in (0.14, 0.86):
    pm.box(m, BROWN, (0.0, DECK - 0.15, z - 0.05), (3.0, DECK - 0.06, z + 0.05))
for x in (0.08, 2.92):
    pm.cylinder(m, BROWN, (x, -0.6, 0.08), (x, DECK - 0.06, 0.08), 0.07, seg=7)

# --- pool frame (rows 1-3): log rails at deck height and under the water, posts at the corners and sides
R = 0.075
corners = [(0.08, 1.02), (2.92, 1.02), (2.92, 3.92), (0.08, 3.92)]
for a, b in [((0.08, 1.02), (0.08, 3.92)), ((2.92, 1.02), (2.92, 3.92)), ((0.08, 3.92), (2.92, 3.92))]:
    for y, r in ((0.02, R), (-0.62, R * 0.85)):
        pm.cylinder(m, BROWN, (a[0], y, a[1]), (b[0], y, b[1]), r, seg=8, uv_offset=(0.3, y))
for x, z in corners + [(0.08, 2.47), (2.92, 2.47), (1.5, 3.92)]:
    pm.cylinder(m, BROWN, (x, -1.0, z), (x, 0.28, z), 0.095, seg=8)
    pm.cylinder(m, LIGHT, (x, 0.28, z), (x, 0.33, z), 0.11, 0.08, seg=8)          # little cap
# lashings where rails meet posts
for x, z in corners:
    pm.cylinder(m, WHITE, (x, -0.04, z), (x, 0.08, z), 0.105, seg=8, color=(0.62, 0.52, 0.34, 1))

# --- diving board off the deck, on a trestle
pm.box(m, BROWN, (2.12, DECK, 0.55), (2.48, DECK + 0.12, 0.75))
pm.box(m, LIGHT, (2.16, 0.0, 0.0), (2.44, 0.05, 1.35),
               rot=np.array([[1, 0, 0], [0, math.cos(-0.12), -math.sin(-0.12)], [0, math.sin(-0.12), math.cos(-0.12)]]),
               pivot=(2.3, 0.0, 0.0), offset=(0, DECK + 0.12, 0.55))

# --- ladder down into the pool on the left
for x in (0.42, 0.78):
    pm.beam(m, BROWN, (x, DECK, 1.02), (x, -0.85, 1.22), 0.05)
for k in range(4):
    t = (k + 0.5) / 4
    y = DECK + (-0.85 - DECK) * t; z = 1.02 + 0.2 * t
    pm.cylinder(m, LIGHT, (0.42, y, z), (0.78, y, z), 0.025, seg=6)

# --- bench on the deck, facing the water
pm.box(m, LIGHT, (0.12, DECK + 0.30, 0.20), (1.12, DECK + 0.36, 0.48))
for x in (0.2, 1.04):
    pm.box(m, BROWN, (x - 0.04, DECK, 0.24), (x + 0.04, DECK + 0.30, 0.44))

# --- a striped float ring hanging on the back post, and a towel over the bench end
ring_c = np.array([1.5, 0.05, 3.80])
seg = 12
for i in range(seg):
    a0 = 2 * math.pi * i / seg; a1 = 2 * math.pi * (i + 1) / seg
    p0 = ring_c + np.array([math.cos(a0) * 0.2, math.sin(a0) * 0.2, 0]); p1 = ring_c + np.array([math.cos(a1) * 0.2, math.sin(a1) * 0.2, 0])
    col = (0.85, 0.25, 0.18, 1) if i % 3 == 0 else (0.93, 0.90, 0.84, 1)
    pm.cylinder(m, WHITE, p0, p1, 0.055, seg=6, color=col, caps=False)
pm.box(m, WHITE, (1.02, DECK + 0.36, 0.18), (1.16, DECK + 0.38, 0.50), color=(0.30, 0.62, 0.70, 1))
pm.box(m, WHITE, (1.14, DECK + 0.10, 0.18), (1.16, DECK + 0.38, 0.50), color=(0.30, 0.62, 0.70, 1))

nodes = [tm.Node(-1, "SplashPool.Otters", (0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0), (1.0, 1.0, 1.0))]
body = m.node("SplashPoolBody", parent=0)
nodes.append(body)


def yaw(deg):
    a = math.radians(deg) / 2
    return (0.0, math.sin(a), 0.0, math.cos(a))


# reeds in the back corners, from the game's own cattails
for i, (x, z, s, d) in enumerate([(0.05, 3.55, 0.55, 20), (2.55, 3.6, 0.5, 200), (2.6, 1.1, 0.42, 120)]):
    n = tm.Node(0, f"Reeds{i}", (x, -0.35, z), yaw(d), (s, s * 1.15, s))
    n.vertex_count = cat.vertex_count
    n.vertex_properties = list(cat.vertex_properties)
    n.meshes = [tm.MeshPart(mp.indices, mp.material) for mp in cat.meshes]
    nodes.append(n)

# slots: seats on the bench face the pool (+z); floaters spread around the water
for i, x in enumerate((0.40, 0.84)):
    nodes.append(tm.Node(0, f"#Slot#Seat.00{i + 1}", (x, DECK + 0.32, 0.30), (0.0, 0.0, 0.0, 1.0), (1.0, 1.0, 1.0)))
for i, (x, z, d) in enumerate([(0.85, 2.05, 40), (2.10, 2.20, -60), (1.05, 3.20, 150), (2.05, 3.25, 210)]):
    nodes.append(tm.Node(0, f"#Slot#Floating.00{i + 1}", (x, -0.30, z), yaw(d), (1.0, 1.0, 1.0)))

model = tm.Model(0, "SplashPool.Otters", nodes)
tm.write(model, out)
print("nodes", len(nodes), "verts", body.vertex_count)
