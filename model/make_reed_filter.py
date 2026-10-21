"""Reed Filter model: the Folktails water pump, but the intake over the water (the round barrel and the pipe
into the river) is a bundle of reeds tied with twine, and the pump's piston is a slim rod that plunges into it.

Writes the building model plus a reed-bundle pipe segment node (#OtterReedSegment) that the ReedPipe component
copies into each of the game's pipe segments in place of the wooden pipe, so the reeds reach down to the water
exactly as far as the pump's pipe would.

usage: python3 make_reed_filter.py WaterPump.Folktails.Model.timbermesh CattailMature.timbermesh out.timbermesh"""
import math
import sys

import numpy as np

import procmesh as pm
import timbermesh as tm

pump_path, cattail_path, out = sys.argv[1:4]
pump = tm.read(pump_path)
cat = [n for n in tm.read(cattail_path).nodes if n.vertex_count][0]

CENTRE = np.array([0.5, 0.0, 2.5])  # the intake tile over the water (x, -, z)
STEM = "Cattail"
STEM_COL = (0.41, 0.39, 0.17, 1.0)    # the game's cattail stem vertex colour
HEAD_COL = (0.40, 0.23, 0.08, 1.0)    # cattail head
TWINE = "BaseWood_LightBrown.Folktails"
TWINE_COL = (1.0, 0.86, 0.62, 1.0)
ROD = "BaseWood_Brown.Folktails"
rng = np.random.default_rng(7)


# ---------------------------------------------------------------- welded components of the pump body
def components(P, F):
    """Connected parts: faces that share an edge (vertices welded by position), like trimesh's face adjacency."""
    key = {tuple(k): i for i, k in enumerate(np.round(P, 6))}
    weld = np.array([key[tuple(k)] for k in np.round(P, 6)])
    parent = list(range(len(F)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    edges = {}
    for fi, f in enumerate(weld[F]):
        for x, y in ((f[0], f[1]), (f[1], f[2]), (f[2], f[0])):
            e = (min(x, y), max(x, y))
            if e in edges:
                ra, rb = find(fi), find(edges[e])
                if ra != rb:
                    parent[ra] = rb
            else:
                edges[e] = fi
    return np.array([find(i) for i in range(len(F))])


body = pump.nodes[0]
P = body.prop("position").array()
removed = 0
for mp in body.meshes:
    if mp.material != ROD:
        continue
    F = mp.indices.reshape(-1, 3)
    comp = components(P, F)
    drop = np.zeros(len(F), bool)
    cen = P[F].mean(1)
    on_tile = (cen[:, 0] < 1.02) & (cen[:, 2] > 2.001) & (cen[:, 1] < 0.5)
    for c in np.unique(comp):
        sel = comp == c
        v = P[np.unique(F[sel])]
        # the barrel (welded to the deck) and the pipe stub under it: the parts of the deck piece on the intake
        # tile, below the lever, and the stub that hangs wholly under that tile
        if v[:, 2].min() > 1.99 or v[:, 2].max() > 2.5:
            drop |= sel & on_tile
    removed += int(drop.sum())
    mp.indices = F[~drop].reshape(-1)
assert 195 <= removed <= 206, removed  # 166 barrel + 38 stub triangles, give or take its seams


# ---------------------------------------------------------------- reed pieces
def stem(mesh, p0, p1, r, seg=5, col=STEM_COL):
    """A slim prism using the stem strip of the cattail texture (u along the stem)."""
    p0 = np.asarray(p0, float); p1 = np.asarray(p1, float)
    axis, u, v = pm._frame(p1 - p0)
    Pp, N, UV, T = [], [], [], []
    for i in range(seg + 1):
        a = 2 * math.pi * i / seg
        d = math.cos(a) * u + math.sin(a) * v
        for t, p in ((0.0, p0), (1.0, p1)):
            Pp.append(p + d * r); N.append(d)
            UV.append((0.02 + 0.96 * t, 0.925 + 0.06 * i / seg))
    for i in range(seg):
        a, b, c, d = 2 * i, 2 * i + 1, 2 * i + 2, 2 * i + 3
        T += [(a, c, d), (a, d, b)]
    mesh.add(STEM, Pp, N, UV, T, col)


def head(mesh, p0, p1, r, seg=6):
    """A cattail head: a fat brown sausage on the head patch of the texture, with a thin spike above."""
    p0 = np.asarray(p0, float); p1 = np.asarray(p1, float)
    axis, u, v = pm._frame(p1 - p0)
    rings = [(0.0, 0.55), (0.12, 1.0), (0.88, 1.0), (1.0, 0.5)]
    Pp, N, UV, T = [], [], [], []
    for i in range(seg + 1):
        a = 2 * math.pi * i / seg
        d = math.cos(a) * u + math.sin(a) * v
        for t, k in rings:
            Pp.append(p0 + (p1 - p0) * t + d * r * k); N.append(d)
            UV.append((0.03 + 0.27 * i / seg, 0.775 + 0.12 * t))
    n = len(rings)
    for i in range(seg):
        for j in range(n - 1):
            a = i * n + j; b = a + 1; c = a + n; d = c + 1
            T += [(a, c, d), (a, d, b)]
    mesh.add(STEM, Pp, N, UV, T, HEAD_COL)
    stem(mesh, p1, p1 + axis * 0.07, r * 0.18, seg=3)


def ring(mesh, centre, y, r, h, seg=12):
    """A band of twine around the bundle."""
    pm.cylinder(mesh, TWINE, (centre[0], y - h / 2, centre[2]), (centre[0], y + h / 2, centre[2]), r, seg=seg,
                color=TWINE_COL, caps=False)


def bundle_stems(n_outer, n_inner, r_outer, r_inner):
    """Stem positions around a hollow core (the rod runs down the middle)."""
    pts = []
    for k, (n, r) in enumerate(((n_outer, r_outer), (n_inner, r_inner))):
        for i in range(n):
            a = 2 * math.pi * (i + 0.5 * k) / n + rng.uniform(-0.12, 0.12)
            rr = r + rng.uniform(-0.012, 0.012)
            pts.append((math.cos(a) * rr, math.sin(a) * rr, a))
    return pts


def leaves(mesh, base, scale, yaws):
    """A few of the game's own cattail leaf cards sprouting from the top of the bundle."""
    Pc = cat.prop("position").array(); Nc = cat.prop("normal").array(); UVc = cat.prop("uv0").array()
    Cc = cat.prop("color").array()
    F = np.concatenate([m.indices for m in cat.meshes]).reshape(-1, 3)
    comp = components(Pc, F)
    cards = [F[comp == k] for k in np.unique(comp)]
    cards = [q for q in cards if len(q) == 2 and Pc[q][:, :, 1].max() > 0.85]  # the long leaf cards
    for k, yaw in enumerate(yaws):
        quad = cards[k % len(cards)]
        vs = np.unique(np.concatenate(quad))
        P0 = Pc[vs].copy()
        P0[:, [0, 2]] -= P0[:, [0, 2]][np.argmin(P0[:, 1])]  # root of the card at the origin
        a = math.radians(yaw)
        R = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
        Pw = (P0 * [0.45 * scale, scale, 0.45 * scale]) @ R.T + base
        remap = {int(v): i for i, v in enumerate(vs)}
        tris = [[remap[int(i)] for i in t] for t in quad]
        mesh.add(STEM, Pw, Nc[vs] @ R.T, UVc[vs], tris, Cc[vs])
        mesh.add(STEM, Pw, -(Nc[vs] @ R.T), UVc[vs], [t[::-1] for t in tris], Cc[vs])


# ---------------------------------------------------------------- the bundle on the intake tile
reeds = pm.Mesh()
c = CENTRE
for x, z, a in bundle_stems(16, 9, 0.185, 0.115):
    lean = 0.035 * np.array([math.cos(a), 0, math.sin(a)])
    top = 0.62 + rng.uniform(-0.06, 0.08)
    p0 = c + (x, -0.06, z)
    p_tie = c + (x * 0.92, 0.42, z * 0.92)            # pulled in at the upper tie
    p1 = c + (x * 1.25, top, z * 1.25) + lean           # flaring out above it
    stem(reeds, p0, p_tie, 0.024)
    stem(reeds, p_tie, p1, 0.022)
    if rng.random() < 0.55:
        head(reeds, p1 - lean * 0.2, p1 + (0, 0.17, 0) + lean * 0.6, 0.036)
for y, r in ((0.06, 0.215), (0.40, 0.195)):
    ring(reeds, c, y, r, 0.07)
leaves(reeds, c + (0, 0.45, 0), 0.75, [20, 140, 255])
reeds_node = reeds.node("OtterReedBundle")

# ---------------------------------------------------------------- the piston: a rod into the bundle
piston = pump.nodes[3]
assert piston.name.startswith("#PistonAnimated"), piston.name
Pp = piston.prop("position").array()
for mp in piston.meshes:
    F = mp.indices.reshape(-1, 3)
    top = Pp[F][:, :, 1].min(1) > 0.30   # keep the pin where the lever grips the piston
    mp.indices = F[top].reshape(-1)
rod = pm.Mesh()
pm.cylinder(rod, ROD, (0, -0.54, 0), (0, 0.36, 0), 0.04, seg=8)
pm.cylinder(rod, TWINE, (0, -0.10, 0), (0, -0.02, 0), 0.055, seg=8, color=TWINE_COL)
rod_node = rod.node("OtterPistonRod", parent=3)


# ---------------------------------------------------------------- pipe segment template (one block deep)
seg = pm.Mesh()
for x, z, a in bundle_stems(14, 8, 0.165, 0.10):
    stem(seg, (x, -0.02, z), (x * 1.02, 1.04, z * 1.02), 0.024)
ring(seg, (0, 0, 0), 0.5, 0.19, 0.07)
seg_node = seg.node("#OtterReedSegment")
# Hidden where it sits in the model (it is only a template); ReedPipe copies it at full size into each pipe segment.
seg_node.scale = (1e-4, 1e-4, 1e-4)

pump.nodes += [reeds_node, rod_node, seg_node]
tm.write(pump, out)
print("removed", removed, "barrel triangles; nodes", [n.name for n in pump.nodes])
