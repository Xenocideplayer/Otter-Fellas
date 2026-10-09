"""Fishing Dock model: the Folktails water-pump hut without its pump lever, with a fishing rod over the water,
a fish on the line and a drying rack of fish on the deck.
usage: python3 make_fishing_dock.py WaterPump.Folktails.Model.timbermesh out.timbermesh"""
import math
import sys

import numpy as np

import procmesh as pm
import timbermesh as tm

src, out = sys.argv[1:3]
model = tm.read(src)
model.nodes = [n for n in model.nodes if not n.name.startswith(("#ElementAnimated", "#PistonAnimated"))]
model.name = "FishingDock.Otters"

LIGHT = "BaseWood_LightBrown.Folktails"
BROWN = "BaseWood_Brown.Folktails"
WHITE = "BaseWood_White.Folktails"
LINE_COL = (0.12, 0.10, 0.08, 1)
SILVER = np.array([0.72, 0.78, 0.80, 1])
BACK = np.array([0.30, 0.38, 0.42, 1])

m = pm.Mesh()


def fish(top, length, tilt_axis=(1, 0, 0), tilt=0.0, yaw=0.0):
    """A fish hanging tail-up from `top`: body below, tail fin at the top."""
    top = np.asarray(top, float)
    R = pm.rot_y(yaw)
    a = math.radians(tilt)
    T = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    A = R @ T  # columns: x = side-to-side, y = along the fish (tail up), z = belly-to-back
    centre = top - A[:, 1] * (length * 0.62)
    radii = np.array([length * 0.17, length * 0.5, length * 0.24])
    # colour: dark back, silver belly
    P0 = len(m._part(WHITE)["P"])
    pm.ellipsoid(m, WHITE, centre, radii, axes=A, seg=10, rings=7, color=SILVER)
    part = m.parts[WHITE]
    pts = part["P"][-1]
    side = (pts - centre) @ A[:, 2] / radii[2]
    t = np.clip((side + 0.2) / 1.0, 0, 1)[:, None]
    part["C"][-1] = SILVER * (1 - t) + BACK * t
    tail_base = centre + A[:, 1] * radii[1] * 0.85
    pm.triangle(m, WHITE, tail_base, tail_base + A[:, 1] * length * 0.3 + A[:, 2] * length * 0.18,
                tail_base + A[:, 1] * length * 0.3 - A[:, 2] * length * 0.18, color=tuple(BACK))
    # dorsal fin
    d0 = centre + A[:, 2] * radii[2] * 0.9
    pm.triangle(m, WHITE, d0 - A[:, 1] * length * 0.12, d0 + A[:, 1] * length * 0.14,
                d0 + A[:, 1] * length * 0.08 + A[:, 2] * length * 0.1, color=tuple(BACK))
    return tail_base + A[:, 1] * length * 0.05


# --- rod: butt in a holder on the old pump posts, tip out over the water behind the dock
butt = np.array([0.42, 0.50, 1.70])
holder = np.array([0.50, 0.82, 1.98])
tip = np.array([1.30, 1.95, 3.20])
pm.beam(m, BROWN, (0.24, 0.80, 1.98), (0.78, 0.80, 1.98), 0.07, 0.06)       # crossbar on the posts
pm.cylinder(m, LIGHT, butt, tip, 0.032, 0.012, seg=7)
pm.cylinder(m, BROWN, butt, butt + (tip - butt) * 0.16, 0.040, 0.038, seg=7)  # grip
for k in (0.45, 0.75):                                                       # line guides
    p = butt + (tip - butt) * k
    pm.cylinder(m, BROWN, p, p + (tip - butt) * 0.02, 0.030 * (1 - k) + 0.018, seg=6)
# line down to a fish that has just been pulled out of the water
fish_top = tip + np.array([0.0, -1.10, 0.0])
pm.beam(m, WHITE, tip, fish_top, 0.012, color=LINE_COL)
fish(fish_top, 0.36, tilt=8, yaw=30)

# --- drying rack in the back-right corner of the deck
for x in (1.45, 1.90):
    pm.beam(m, BROWN, (x, 0.0, 1.88), (x, 0.92, 1.88), 0.06)
pm.beam(m, LIGHT, (1.40, 0.86, 1.88), (1.95, 0.86, 1.88), 0.045)
for i, x in enumerate((1.56, 1.68, 1.80)):
    top = np.array([x, 0.84, 1.88])
    hang = top + np.array([0, -0.10, 0])
    pm.beam(m, WHITE, top, hang, 0.01, color=LINE_COL)
    fish(hang, 0.23 + 0.02 * (i % 2), yaw=90 + 8 * (i - 1))

model.nodes.append(m.node("#OtterFishingGear", parent=0))
tm.write(model, out)
print("nodes", [n.name for n in model.nodes])
