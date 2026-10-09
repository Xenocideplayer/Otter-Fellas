"""Building props for the Otters mod, built from the game's own wood/thatch materials.
usage: python3 make_props.py CattailMature.timbermesh out_dir

  ArtesianWellExtras.Otters.Model  - laid over the Aquifer Drill model: tube sockets on both side walls and the
                                     back, painted bands, a thatched cap with a pennant, barrels
  SmokehouseExtras.Otters.Model    - laid over the Bakery model: fish racks along both sides, a fish sign
  TubeOutletExtras.Otters.Model    - laid over the Discharge model: a tube collar where the tube plugs in
  OtterSlide.Otters.Model          - a complete slide: tower, ladder, thatched canopy, curved chute into water
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
THATCH = "ThatchedRoof.Folktails"
TEAL = (0.30, 0.62, 0.70, 1)
IRON = (0.36, 0.36, 0.38, 1)
LINE = (0.12, 0.10, 0.08, 1)
TUBE_Y = 0.37          # centre height of the game's tubes
DECK = 0.0


def yaw(deg):
    a = math.radians(deg) / 2
    return (0.0, math.sin(a), 0.0, math.cos(a))


def reeds(name, x, y, z, s, d):
    n = tm.Node(0, name, (x, y, z), yaw(d), (s, s * 1.15, s))
    n.vertex_count = cat.vertex_count
    n.vertex_properties = list(cat.vertex_properties)
    n.meshes = [tm.MeshPart(mp.indices, mp.material) for mp in cat.meshes]
    return n


def slot(name, x, y, z, d=0.0):
    return tm.Node(0, name, (x, y, z), yaw(d), (1.0, 1.0, 1.0))


def socket(m, inner, outer):
    """A pipe from the tower out to a wall, ending in a collar the game's tube plugs into."""
    inner = np.asarray(inner, float); outer = np.asarray(outer, float)
    pm.cylinder(m, WHITE, inner, outer, 0.12, seg=10, color=IRON)
    d = (outer - inner) / np.linalg.norm(outer - inner)
    pm.cylinder(m, WHITE, outer - d * 0.10, outer, 0.2, seg=10, color=(0.22, 0.22, 0.24, 1))
    pm.cylinder(m, WHITE, outer - d * 0.32, outer - d * 0.24, 0.16, seg=10, color=TEAL)


def barrel(m, x, z, h=0.55, r=0.2):
    pm.cylinder(m, LIGHT, (x, 0, z), (x, h, z), r, seg=10)
    for y in (0.08, h - 0.08):
        pm.cylinder(m, WHITE, (x, y - 0.025, z), (x, y + 0.025, z), r + 0.012, seg=10, color=IRON, caps=False)


# ------------------------------------------------------------------------------------------------- well
def well():
    m = pm.Mesh()
    tower = (1.5, 1.48)
    for end in ((0.02, 1.5), (2.98, 1.5), (1.5, 2.98)):      # left, right, back sockets
        socket(m, (tower[0], TUBE_Y, tower[1]), (end[0], TUBE_Y, end[1]))
    for y in (1.0, 2.25):                                       # otter-teal bands on the tower
        pm.cylinder(m, WHITE, (1.5, y, 1.48), (1.5, y + 0.09, 1.48), 0.305, seg=12, color=TEAL)
    # thatched cap and pennant
    pm.cylinder(m, BROWN, (1.5, 3.30, 1.48), (1.5, 3.40, 1.48), 0.36, seg=10)
    pm.cone(m, THATCH, (1.5, 3.38, 1.48), 0.62, 0.62, seg=10, uv_offset=(0.0, 0.48))
    pm.cylinder(m, BROWN, (1.5, 3.9, 1.48), (1.5, 4.55, 1.48), 0.025, seg=6)
    pm.triangle(m, WHITE, (1.5, 4.52, 1.48), (1.5, 4.30, 1.48), (1.5, 4.42, 1.98), color=TEAL)
    # a pair of barrels and a coil of rope in the back corners
    barrel(m, 0.38, 2.55)
    barrel(m, 0.62, 2.72, h=0.45, r=0.17)
    for i in range(3):
        pm.cylinder(m, WHITE, (2.55, 0.04 + i * 0.05, 2.6), (2.55, 0.08 + i * 0.05, 2.6), 0.22 - i * 0.02, seg=12,
                    color=(0.62, 0.52, 0.34, 1))
    return pm.single_node_model("ArtesianWellExtras.Otters", m)


# ------------------------------------------------------------------------------------------------- smokehouse
def smokehouse():
    m = pm.Mesh()
    for x, sgn in ((-0.10, -1), (2.10, 1)):
        for z in (0.35, 1.45, 2.6):
            pm.beam(m, BROWN, (x, 0.0, z), (x, 1.15, z), 0.06)
        pm.beam(m, LIGHT, (x, 1.10, 0.30), (x, 1.10, 2.65), 0.05)
        for i, z in enumerate(np.linspace(0.55, 2.4, 7)):
            top = np.array([x, 1.08, z])
            hang = top + np.array([0, -0.10, 0])
            pm.beam(m, WHITE, top, hang, 0.01, color=LINE)
            smoked = (0.62, 0.45, 0.28, 1) if i % 2 else (0.55, 0.38, 0.22, 1)
            pm.fish(m, WHITE, hang, 0.24 + 0.02 * (i % 3), yaw=90 * sgn + 6 * (i - 3), silver=smoked,
                    back=(0.30, 0.20, 0.12, 1))
    # sign over the door: a board with a fish on it
    pm.box(m, LIGHT, (0.62, 1.22, -0.06), (1.38, 1.48, -0.02))
    pm.fish(m, WHITE, (1.18, 1.35, -0.07), 0.42, yaw=0, hang=False, tilt=0)
    return pm.single_node_model("SmokehouseExtras.Otters", m)


# ------------------------------------------------------------------------------------------------- outlet
def outlet():
    m = pm.Mesh()
    pm.cylinder(m, WHITE, (0.5, TUBE_Y, 0.10), (0.5, TUBE_Y, -0.02), 0.13, seg=10, color=IRON)
    pm.cylinder(m, WHITE, (0.5, TUBE_Y, 0.06), (0.5, TUBE_Y, -0.02), 0.2, seg=10, color=(0.22, 0.22, 0.24, 1))
    pm.cylinder(m, WHITE, (0.5, TUBE_Y, 0.16), (0.5, TUBE_Y, 0.10), 0.16, seg=10, color=TEAL)
    return pm.single_node_model("TubeOutletExtras.Otters", m)


# ------------------------------------------------------------------------------------------------- slide
def slide_curve(t):
    """Chute centreline: off the back of the platform, steep at first, flattening into the water."""
    z = 0.95 + 1.95 * t
    y = 1.60 * (1 - t) ** 1.7 - 0.18 * t
    return np.array([1.0, y, z])


def otter_slide():
    m = pm.Mesh()
    P = 1.58  # platform height
    for x in (0.12, 1.88):
        for z in (0.12, 0.88):
            pm.beam(m, BROWN, (x, 0.0, z), (x, 2.25, z), 0.09)
    for i in range(7):                                                        # platform boards
        x0 = 0.06 + i * 0.27
        pm.box(m, LIGHT, (x0, P - 0.05, 0.06), (x0 + 0.25, P, 0.94), uv_offset=(0.11 * i, 0.0))
    for z in (0.12, 0.88):
        pm.box(m, BROWN, (0.06, P - 0.13, z - 0.04), (1.94, P - 0.05, z + 0.04))
    for a, b in [((0.12, 0.12), (1.88, 0.12)), ((0.12, 0.12), (0.12, 0.88)), ((1.88, 0.12), (1.88, 0.88))]:
        pm.beam(m, LIGHT, (a[0], P + 0.42, a[1]), (b[0], P + 0.42, b[1]), 0.06)  # railing
    # ladder up the front
    for x in (0.72, 1.28):
        pm.beam(m, BROWN, (x, 0.0, -0.06), (x, P + 0.05, 0.06), 0.05)
    for k in range(6):
        y = 0.22 + k * 0.25
        pm.cylinder(m, LIGHT, (0.72, y, -0.04 + 0.08 * y / P), (1.28, y, -0.04 + 0.08 * y / P), 0.025, seg=6)
    # thatched canopy
    pm.box(m, BROWN, (0.04, 2.20, 0.04), (1.96, 2.28, 0.96))
    pm.cylinder(m, THATCH, (1.0, 2.26, 0.5), (1.0, 2.86, 0.5), 1.22, 0.05, seg=4, uv_offset=(0.0, 0.48))
    pm.cylinder(m, BROWN, (1.0, 2.8, 0.5), (1.0, 3.25, 0.5), 0.022, seg=6)
    pm.triangle(m, WHITE, (1.0, 3.22, 0.5), (1.0, 3.02, 0.5), (1.38, 3.12, 0.5), color=TEAL)
    # the chute: painted teal trough on a curve, with wooden rails, propped on legs in the water
    N = 14
    pts = [slide_curve(t) for t in np.linspace(0, 1, N + 1)]
    for a, b in zip(pts[:-1], pts[1:]):
        pm.beam(m, WHITE, a, b, 0.62, 0.05, color=TEAL)
        for dx in (-0.33, 0.33):
            pm.beam(m, LIGHT, a + (dx, 0.09, 0), b + (dx, 0.09, 0), 0.05, 0.2)
    for t in (0.35, 0.68):
        p = slide_curve(t)
        for dx in (-0.3, 0.3):
            pm.beam(m, BROWN, (1.0 + dx, -1.0, p[2]), (1.0 + dx, p[1] - 0.03, p[2]), 0.07)
        pm.beam(m, BROWN, (0.7, p[1] - 0.06, p[2]), (1.3, p[1] - 0.06, p[2]), 0.06)
    nodes = [reeds("Reeds0", 1.55, -0.35, 2.35, 0.45, 70), reeds("Reeds1", -0.15, -0.35, 2.55, 0.42, 200),
             slot("#Slot#Seat.001", 0.45, P, 0.45, 180), slot("#Slot#Seat.002", 1.55, P, 0.45, 180)]
    for i, (x, z, d) in enumerate([(0.55, 2.55, 20), (1.45, 2.75, -40), (1.0, 2.25, 170)]):
        nodes.append(slot(f"#Slot#Floating.00{i + 1}", x, -0.30, z, d))
    return pm.single_node_model("OtterSlide.Otters", m, nodes)


for name, model in (("ArtesianWellExtras.Otters.Model", well()), ("SmokehouseExtras.Otters.Model", smokehouse()),
                    ("TubeOutletExtras.Otters.Model", outlet()), ("OtterSlide.Otters.Model", otter_slide())):
    tm.write(model, os.path.join(out, name + ".timbermesh"))
    print(name, sum(n.vertex_count for n in model.nodes), "verts")
