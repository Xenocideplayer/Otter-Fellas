"""Adds the Wellspring's 'Default' node animation, which the game's wonder code requires (WonderAnimationController
looks up the model's animator; a model without any animation has none and the game crashes).
The animation: a crown of teal petals around the pennant pole rises out of the holt, opens and spins as the wonder
is activated, then rests.
usage: python3 add_wellspring_anim.py Wellspring.Otters.Model.timbermesh"""
import math
import sys

import numpy as np

import procmesh as pm
import timbermesh as tm

path = sys.argv[1]
model = tm.read(path)
model.nodes = [n for n in model.nodes if n.name != "#WellspringCrown"]

TEAL = (0.30, 0.62, 0.70, 1)
TEAL_DARK = (0.20, 0.45, 0.52, 1)
m = pm.Mesh()
pm.cylinder(m, "BaseWood_Brown.Folktails", (0, -0.05, 0), (0, 0.12, 0), 0.16, seg=10)
for i in range(8):
    a = 2 * math.pi * i / 8
    d = np.array([math.cos(a), 0.0, math.sin(a)])
    side = np.array([-math.sin(a), 0.0, math.cos(a)])
    base = d * 0.12 + np.array([0, 0.06, 0])
    tip = d * 0.62 + np.array([0, 0.30, 0])
    col = TEAL if i % 2 == 0 else TEAL_DARK
    pm.triangle(m, "BaseWood_White.Folktails", base - side * 0.10, base + side * 0.10, tip, color=col)
    pm.triangle(m, "BaseWood_White.Folktails", base - side * 0.10, tip, d * 0.40 + np.array([0, 0.12, 0]) - side * 0.16, color=col)
    pm.triangle(m, "BaseWood_White.Folktails", base + side * 0.10, d * 0.40 + np.array([0, 0.12, 0]) + side * 0.16, tip, color=col)
crown = m.node("#WellspringCrown", parent=0)
REST = np.array([3.5, 6.1, 3.5])
crown.position = tuple(REST)


def vec(fields):
    return b"".join(tm._float(i + 1, float(v)) for i, v in enumerate(fields))


FPS, SECONDS = 30.0, 6.0
frames = []
n = int(FPS * SECONDS)
for f in range(n):
    t = f / (n - 1)
    ease = 1 - (1 - t) ** 3
    rise = -0.45 * (1 - ease)
    angle = 2 * 2 * math.pi * ease            # two full turns, slowing to a stop
    s = 0.35 + 0.65 * min(1.0, t * 1.6)
    q = (0.0, math.sin(angle / 2), 0.0, math.cos(angle / 2))
    frames.append(tm._ld(1, vec(REST + np.array([0, rise, 0]))) + tm._ld(2, vec(q)) + tm._ld(3, vec((s, s, s))))
crown.node_animations = [tm.NodeAnimation("Default", FPS, frames)]
model.nodes.append(crown)
tm.write(model, path)
print("crown animation:", len(frames), "frames,", len(frames) / FPS, "s")
