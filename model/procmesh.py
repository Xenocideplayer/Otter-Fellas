"""Tiny procedural mesh kit for building props, written straight into Timberborn's model format.

Coordinates are the game's (Unity) model space: x right, y up, z towards the back of the building, metres =
blocks. Geometry uses the game's own tiling materials (BaseWood_*.Folktails etc.), so it is textured like the
vanilla buildings; vertex colour tints it (white materials + colour = painted parts, as the Lodge does).
"""
import math

import numpy as np

import timbermesh as tm

UV_PER_METRE = 0.5  # texel density of the vanilla Folktails buildings


class Mesh:
    def __init__(self):
        self.parts = {}  # (material) -> lists

    def _part(self, material):
        return self.parts.setdefault(material, {"P": [], "N": [], "UV": [], "C": [], "T": []})

    def add(self, material, P, N, UV, tris, color=(1, 1, 1, 1)):
        part = self._part(material)
        base = sum(len(p) for p in part["P"])
        P = np.asarray(P, float); N = np.asarray(N, float); UV = np.asarray(UV, float); tris = np.asarray(tris, int)
        # Front faces wind so that cross(b - a, c - a) points along the normal (as in the game's own models).
        fixed = []
        for a, b, c in tris:
            g = np.cross(P[b] - P[a], P[c] - P[a])
            fixed.append((a, b, c) if g @ (N[a] + N[b] + N[c]) >= 0 else (a, c, b))
        part["P"].append(P); part["N"].append(N); part["UV"].append(UV)
        color = np.asarray(color, float)
        part["C"].append(color if color.ndim == 2 else np.tile(color, (len(P), 1)))
        part["T"].append(np.asarray(fixed, int) + base)

    def node(self, name, parent=0):
        P, N, UV, C, meshes = [], [], [], [], []
        base = 0
        for material, part in self.parts.items():
            p = np.concatenate(part["P"]); P.append(p)
            N.append(np.concatenate(part["N"])); UV.append(np.concatenate(part["UV"])); C.append(np.concatenate(part["C"]))
            meshes.append(tm.MeshPart(np.concatenate(part["T"]).reshape(-1) + base, material))
            base += len(p)
        P = np.concatenate(P); N = np.concatenate(N); UV = np.concatenate(UV); C = np.concatenate(C)
        N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-12
        T = tangents(P, N, UV, np.concatenate([m.indices for m in meshes]).reshape(-1, 3))
        n = tm.Node(parent, name, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0), (1.0, 1.0, 1.0))
        n.vertex_count = len(P)
        n.vertex_properties = [tm.VertexProperty.from_array("position", P), tm.VertexProperty.from_array("normal", N),
                               tm.VertexProperty.from_array("tangent", T), tm.VertexProperty.from_array("color", C),
                               tm.VertexProperty.from_array("uv0", UV)]
        n.meshes = meshes
        return n


def tangents(P, N, UV, tris):
    """Tangent = dP/du, w = sign(cross(n, t) . dP/dv) -- the convention measured on the game's models."""
    tan = np.zeros((len(P), 3)); bit = np.zeros((len(P), 3))
    for a, b, c in tris:
        e1, e2 = P[b] - P[a], P[c] - P[a]
        (du1, dv1), (du2, dv2) = UV[b] - UV[a], UV[c] - UV[a]
        det = du1 * dv2 - du2 * dv1
        if abs(det) < 1e-10:
            continue
        t = (e1 * dv2 - e2 * dv1) / det
        s = (e2 * du1 - e1 * du2) / det
        for i in (a, b, c):
            tan[i] += t; bit[i] += s
    out = np.zeros((len(P), 4))
    for i in range(len(P)):
        n = N[i]; t = tan[i] - n * (n @ tan[i])
        if np.linalg.norm(t) < 1e-8:
            t = np.cross(n, [0, 1, 0] if abs(n[1]) < 0.9 else [1, 0, 0])
        t /= np.linalg.norm(t)
        w = 1.0 if np.cross(n, t) @ bit[i] >= 0 else -1.0
        out[i] = (*t, w)
    return out


def _frame(axis):
    axis = np.asarray(axis, float); axis /= np.linalg.norm(axis)
    up = np.array([0, 1, 0]) if abs(axis[1]) < 0.95 else np.array([1, 0, 0])
    u = np.cross(up, axis); u /= np.linalg.norm(u)
    v = np.cross(axis, u)
    return axis, u, v


def box(mesh, material, lo, hi, color=(1, 1, 1, 1), rot=None, pivot=None, uv_offset=(0.0, 0.0), offset=(0, 0, 0)):
    """Axis-aligned box from lo to hi, optionally rotated by matrix rot about pivot. Flat shaded, planar UVs."""
    lo = np.asarray(lo, float); hi = np.asarray(hi, float)
    faces = [((0, 1, 0), [(0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)], (0, 2)),
             ((0, -1, 0), [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)], (0, 2)),
             ((1, 0, 0), [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)], (2, 1)),
             ((-1, 0, 0), [(0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1)], (2, 1)),
             ((0, 0, 1), [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)], (0, 1)),
             ((0, 0, -1), [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], (0, 1))]
    R = np.eye(3) if rot is None else np.asarray(rot, float)
    piv = (lo + hi) / 2 if pivot is None else np.asarray(pivot, float)
    for n, corners, (ua, va) in faces:
        P = np.array([lo + (hi - lo) * np.array(c) for c in corners])
        UV = np.array([(p[ua] * UV_PER_METRE + uv_offset[0], p[va] * UV_PER_METRE + uv_offset[1]) for p in P])
        P = (P - piv) @ R.T + piv + np.asarray(offset, float)
        N = np.tile(R @ np.array(n, float), (4, 1))
        mesh.add(material, P, N, UV, [(0, 1, 2), (0, 2, 3)], color)


def beam(mesh, material, p0, p1, w, h=None, color=(1, 1, 1, 1)):
    """A square-section beam from p0 to p1."""
    h = w if h is None else h
    p0 = np.asarray(p0, float); p1 = np.asarray(p1, float)
    axis, u, v = _frame(p1 - p0)
    L = np.linalg.norm(p1 - p0)
    R = np.stack([u, v, axis], axis=1)  # local x->u, y->v, z->axis
    lo = np.array([-w / 2, -h / 2, 0]); hi = np.array([w / 2, h / 2, L])
    box(mesh, material, lo, hi, color, rot=R, pivot=np.zeros(3), offset=p0)


def cylinder(mesh, material, p0, p1, r0, r1=None, seg=8, color=(1, 1, 1, 1), caps=True, uv_offset=(0.0, 0.0)):
    r1 = r0 if r1 is None else r1
    p0 = np.asarray(p0, float); p1 = np.asarray(p1, float)
    axis, u, v = _frame(p1 - p0)
    L = np.linalg.norm(p1 - p0)
    slope = (r0 - r1) / max(L, 1e-6)
    P, N, UV, T = [], [], [], []
    for i in range(seg + 1):
        a = 2 * math.pi * i / seg
        d = math.cos(a) * u + math.sin(a) * v
        n = d + axis * slope; n /= np.linalg.norm(n)
        for t, r, p in ((0, r0, p0), (1, r1, p1)):
            P.append(p + d * r); N.append(n)
            UV.append((i / seg * 2 * math.pi * max(r0, r1) * UV_PER_METRE + uv_offset[0], t * L * UV_PER_METRE + uv_offset[1]))
    for i in range(seg):
        a, b, c, d = 2 * i, 2 * i + 1, 2 * i + 2, 2 * i + 3
        T += [(a, c, d), (a, d, b)]
    mesh.add(material, P, N, UV, T, color)
    if caps:
        for p, r, n in ((p0, r0, -axis), (p1, r1, axis)):
            if r <= 1e-4:
                continue
            P = [p]; UV = [(0.5, 0.5)]
            for i in range(seg):
                a = 2 * math.pi * i / seg
                P.append(p + (math.cos(a) * u + math.sin(a) * v) * r)
                UV.append((0.5 + math.cos(a) * r * UV_PER_METRE, 0.5 + math.sin(a) * r * UV_PER_METRE))
            mesh.add(material, P, [n] * len(P), UV, [(0, 1 + i, 1 + (i + 1) % seg) for i in range(seg)], color)


def ellipsoid(mesh, material, centre, radii, axes=None, seg=10, rings=6, color=(1, 1, 1, 1), uv_box=(0.4, 0.4, 0.05)):
    """Smooth ellipsoid; axes is a 3x3 matrix whose columns are the local x/y/z directions."""
    c = np.asarray(centre, float); r = np.asarray(radii, float)
    A = np.eye(3) if axes is None else np.asarray(axes, float)
    P, N, UV, T = [], [], [], []
    for j in range(rings + 1):
        th = math.pi * j / rings
        for i in range(seg + 1):
            ph = 2 * math.pi * i / seg
            s = np.array([math.sin(th) * math.cos(ph), math.cos(th), math.sin(th) * math.sin(ph)])
            P.append(c + A @ (s * r)); N.append(A @ (s / r))
            UV.append((uv_box[0] + uv_box[2] * i / seg, uv_box[1] + uv_box[2] * j / rings))
    for j in range(rings):
        for i in range(seg):
            a = j * (seg + 1) + i; b = a + 1; cc = a + seg + 1; d = cc + 1
            T += [(a, cc, d), (a, d, b)]
    mesh.add(material, P, N, UV, T, color)


def triangle(mesh, material, a, b, c, color=(1, 1, 1, 1), double=True, uv=((0.4, 0.4), (0.45, 0.4), (0.4, 0.45))):
    P = np.array([a, b, c], float)
    n = np.cross(P[1] - P[0], P[2] - P[0]); n /= np.linalg.norm(n)
    mesh.add(material, P, [n] * 3, uv, [(0, 1, 2)], color)
    if double:
        mesh.add(material, P, [-n] * 3, uv, [(0, 2, 1)], color)


def rot_y(deg):
    a = math.radians(deg)
    # Unity is left-handed: positive yaw turns +x towards -z
    return np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])


def fish(mesh, material, top, length, yaw=0.0, tilt=0.0, hang=True,
         silver=(0.72, 0.78, 0.80, 1), back=(0.30, 0.38, 0.42, 1)):
    """A fish, tail up from `top` when hang=True (otherwise lying along local y from `top`), with a dark back."""
    top = np.asarray(top, float)
    a = math.radians(tilt)
    T = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    A = rot_y(yaw) @ T
    if not hang:  # lie flat: along the local z axis
        A = A @ np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]])
    silver = np.asarray(silver, float); back = np.asarray(back, float)
    centre = top - A[:, 1] * (length * 0.62)
    radii = np.array([length * 0.17, length * 0.5, length * 0.24])
    ellipsoid(mesh, material, centre, radii, axes=A, seg=10, rings=7, color=tuple(silver))
    part = mesh.parts[material]
    side = (part["P"][-1] - centre) @ A[:, 2] / radii[2]
    t = np.clip((side + 0.2), 0, 1)[:, None]
    part["C"][-1] = silver * (1 - t) + back * t
    tail = centre + A[:, 1] * radii[1] * 0.85
    triangle(mesh, material, tail, tail + A[:, 1] * length * 0.3 + A[:, 2] * length * 0.18,
             tail + A[:, 1] * length * 0.3 - A[:, 2] * length * 0.18, color=tuple(back))
    d0 = centre + A[:, 2] * radii[2] * 0.9
    triangle(mesh, material, d0 - A[:, 1] * length * 0.12, d0 + A[:, 1] * length * 0.14,
             d0 + A[:, 1] * length * 0.08 + A[:, 2] * length * 0.1, color=tuple(back))


def cone(mesh, material, base, height, r, seg=8, color=(1, 1, 1, 1), uv_offset=(0.0, 0.0)):
    base = np.asarray(base, float)
    cylinder(mesh, material, base, base + np.array([0, height, 0]), r, 0.0, seg=seg, color=color, uv_offset=uv_offset)


def single_node_model(name, mesh, extra_nodes=()):
    """A model whose root carries the mesh, plus optional extra child nodes (slots, instanced props)."""
    root = mesh.node(name, parent=-1)
    return tm.Model(0, name, [root, *extra_nodes])
