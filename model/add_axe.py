"""Give the adult otter a hatchet and an overhead chop instead of the beaver's bite.

The hatchet is extra vertices in the otter body node (same material, UV'd onto two small wood and steel patches
painted into an unused corner of the otter textures). In every animation except the four tree-cutting ones the
hatchet's vertices all sit on one point inside the right paw, so it is invisible; in the cutting animations the
otter stands in its idle pose, raises the right paw over its head and chops, with the hatchet in the paw.

The cutting animations are rebuilt with a tiny procedural rig on the otter's own idle pose: a shoulder and an elbow
for the right arm (weights by distance to the arm in the rest pose) and a hip for the lean.

usage: python3 add_axe.py <model_out dir> [--fresh]
  reads  OtterAdult.Model.noaxe.timbermesh (copied from OtterAdult.Model.timbermesh the first time, or with --fresh
         right after build_models.py has exported a new body), textures/
  writes OtterAdult.Model.timbermesh and paints the hatchet patches into textures/OtterAdult*.png
"""
import math
import os
import shutil
import sys

import numpy as np
from PIL import Image

import procmesh as pm
import timbermesh as tm
import transfer as tr

out_dir = sys.argv[1]
src = os.path.join(out_dir, "OtterAdult.Model.noaxe.timbermesh")
dst = os.path.join(out_dir, "OtterAdult.Model.timbermesh")
if "--fresh" in sys.argv or not os.path.exists(src):
    shutil.copy(dst, src)

CUT_ANIMS = {"BeaverAdult_cut": "BeaverAdult_idle", "BeaverAdult_cut_flipped": "BeaverAdult_idle",
             "BeaverAdult_cut_underwater": "BeaverAdult_idle_underwater",
             "BeaverAdult_cut_underwater_flipped": "BeaverAdult_idle_underwater"}
FRAMES = 90             # same length as the beaver's cut (3.75 s at 24 fps): two chops per loop
CHOPS = 2

# rest-pose landmarks of the right arm (x > 0), measured on the otter mesh
SHOULDER = np.array([0.100, 0.335, 0.000])
HAND = np.array([0.205, 0.235, 0.060])
HIP = np.array([0.0, 0.13, 0.0])

# texture patches (uv centres) in an empty corner of the otter UV layout: 128 px blocks of the 2048 texture
WOOD_UV = (0.031, 0.469)
EDGE_UV = (0.031, 0.406)
STEEL_UV = (0.031, 0.344)
PATCHES = {(0, 1024): ((112, 74, 42), (0, 41)), (0, 1152): ((206, 210, 214), (190, 150)),
           (0, 1280): ((128, 133, 140), (170, 120))}   # (px x, px y) -> albedo, (metallic, smoothness)


def half(a):
    return np.asarray(a, np.float32).astype(np.float16).astype(np.float32)


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def rx(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def rz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def qpow(q, w):
    """Scale a rotation by weight w (nlerp from identity), per vertex."""
    ident = np.array([0, 0, 0, 1.0])
    q = np.where((q[..., 3:4] < 0), -q, q)
    r = ident * (1 - w[..., None]) + q * w[..., None]
    return r / np.linalg.norm(r, axis=-1, keepdims=True)


# ---------------------------------------------------------------- model and poses
model = tm.read(src)
node = [n for n in model.nodes if n.vertex_count][0]
N0 = node.vertex_count
rest = node.prop("position").array().astype(float)
anims = {a.name: a for a in node.vertex_animations}


def pose(name, f):
    fr = {p.name: p for p in anims[name].frames[f % len(anims[name].frames)]}
    return rest + fr["offset"].array(), fr["rotation"].array().astype(float)


def joint(P_pose, point, k=40):
    """Where a rest-pose point (possibly inside the body) ends up in a pose: follow its k nearest vertices."""
    near = np.argsort(np.linalg.norm(rest - point, axis=1))[:k]
    return P_pose[near].mean(0) + (point - rest[near].mean(0))


# ---------------------------------------------------------------- weights (rest pose)
axis = HAND - SHOULDER
L = np.linalg.norm(axis)
t = (rest - SHOULDER) @ axis / L ** 2
closest = SHOULDER + np.clip(t, 0, 1)[:, None] * axis
d = np.linalg.norm(rest - closest, axis=1)
arm_mask = (1 - smoothstep(0.055, 0.085, d)) * smoothstep(0.075, 0.115, rest[:, 0]) * (1 - smoothstep(0.36, 0.42, rest[:, 1]))
w_arm = smoothstep(-0.25, 0.15, t) * arm_mask
w_fore = smoothstep(0.38, 0.58, t) * arm_mask
w_lean = smoothstep(0.08, 0.26, rest[:, 1])
hand_idx = np.where((np.linalg.norm(rest - HAND, axis=1) < 0.03))[0]
print("arm verts", int((w_arm > 0.5).sum()), "forearm", int((w_fore > 0.5).sum()), "hand", len(hand_idx))

# ---------------------------------------------------------------- the hatchet, built in the idle pose's paw
P_idle, Q_idle = pose("BeaverAdult_idle", 0)
S_i, E_i, H_i = joint(P_idle, SHOULDER), joint(P_idle, SHOULDER + 0.5 * axis), joint(P_idle, HAND, 20)
fore = (H_i - E_i) / np.linalg.norm(H_i - E_i)
side = np.array([1.0, 0, 0])
handle_dir = rx(math.radians(16)) @ fore           # nearly in line with the forearm: level with the ground at the strike
handle_dir /= np.linalg.norm(handle_dir)
edge_dir = np.cross(side, handle_dir)              # the blade leads the downward swing
edge_dir /= np.linalg.norm(edge_dir)
if edge_dir @ np.array([0, 0, 1.0]) > 0:            # behind the handle while the paw hangs, so below it at the strike
    edge_dir = -edge_dir

axe = pm.Mesh()
MAT = node.meshes[0].material
grip = H_i + side * 0.0
p0 = grip - handle_dir * 0.045
p1 = grip + handle_dir * 0.200


def prism(p_a, p_b, r, uv, seg=6):
    a, u, v = pm._frame(p_b - p_a)
    P, Nn, UV, T = [], [], [], []
    for i in range(seg + 1):
        ang = 2 * math.pi * i / seg
        dd = math.cos(ang) * u + math.sin(ang) * v
        for p in (p_a, p_b):
            P.append(p + dd * r); Nn.append(dd); UV.append(uv)
    for i in range(seg):
        a0, b0, c0, d0 = 2 * i, 2 * i + 1, 2 * i + 2, 2 * i + 3
        T += [(a0, c0, d0), (a0, d0, b0)]
    axe.add(MAT, P, Nn, UV, T)
    for p, nrm in ((p_a, -a), (p_b, a)):
        P = [p] + [p + (math.cos(2 * math.pi * i / seg) * u + math.sin(2 * math.pi * i / seg) * v) * r for i in range(seg)]
        axe.add(MAT, P, [nrm] * len(P), [uv] * len(P), [(0, 1 + i, 1 + (i + 1) % seg) for i in range(seg)])


def quad_solid(corners_mid, thick_dir, thick, uv):
    """A flat wedge: polygon corners (in the blade plane) with per-corner thickness, closed into a solid."""
    top = [c + thick_dir * th / 2 for c, th in zip(corners_mid, thick)]
    bot = [c - thick_dir * th / 2 for c, th in zip(corners_mid, thick)]
    n = len(corners_mid)
    for poly, nrm in ((top, thick_dir), (bot, -thick_dir)):
        axe.add(MAT, poly, [nrm] * n, [uv] * n, [(0, i, i + 1) for i in range(1, n - 1)])
    for i in range(n):
        j = (i + 1) % n
        P = [top[i], top[j], bot[j], bot[i]]
        e = corners_mid[j] - corners_mid[i]
        nrm = np.cross(e, thick_dir); nrm /= np.linalg.norm(nrm) + 1e-9
        if nrm @ (corners_mid[i] - np.mean(corners_mid, 0)) < 0:
            nrm = -nrm
        axe.add(MAT, P, [nrm] * 4, [uv] * 4, [(0, 1, 2), (0, 2, 3)])


prism(p0, p1 + handle_dir * 0.012, 0.0115, WOOD_UV)                     # handle
prism(p0 - handle_dir * 0.006, p0 + handle_dir * 0.01, 0.0145, WOOD_UV)   # knob at the butt
head_c = p1 - handle_dir * 0.012
socket_w, edge_w, reach = 0.034, 0.072, 0.082
h, e = handle_dir, edge_dir
blade = [head_c - h * socket_w / 2, head_c + h * socket_w / 2,
         head_c + e * reach + h * edge_w / 2, head_c + e * reach - h * edge_w / 2]
quad_solid(blade, side, [0.026, 0.026, 0.006, 0.006], STEEL_UV)
edge = [head_c + e * (reach - 0.012) - h * edge_w * 0.47, head_c + e * (reach - 0.012) + h * edge_w * 0.47,
        head_c + e * (reach + 0.002) + h * edge_w / 2, head_c + e * (reach + 0.002) - h * edge_w / 2]
quad_solid(edge, side, [0.0085, 0.0085, 0.003, 0.003], EDGE_UV)
poll = [head_c - h * socket_w / 2, head_c + h * socket_w / 2, head_c - e * 0.03 + h * 0.012,
        head_c - e * 0.03 - h * 0.012]
quad_solid(poll, side, [0.028, 0.028, 0.022, 0.022], STEEL_UV)
axe_node = axe.node("axe")
A_pos = axe_node.prop("position").array().astype(float)          # in the idle pose
A_nrm = axe_node.prop("normal").array().astype(float)
A_tan = axe_node.prop("tangent").array().astype(float)
A_uv = axe_node.prop("uv0").array()
A_tris = np.concatenate([m.indices for m in axe_node.meshes]).reshape(-1, 3)
NA = len(A_pos)
q_axe_idle = tr.frame_quat(A_nrm, A_tan[:, :3])
print("hatchet verts", NA, "tris", len(A_tris))

# The hatchet's rest position (used only if an animation were missing): carried the same way into the rest pose's paw.
A_rest = A_pos - H_i + rest[hand_idx].mean(0)

# ---------------------------------------------------------------- the chop
# keys: (phase, shoulder swing deg (0 = paw hanging, -90 = forward, -180 = straight up), elbow bend deg, lean deg,
#        adduction deg (negative brings the paw in towards the middle, where the trunk is))
KEYS = [(0.00, -55, 25, 0, -20), (0.12, -70, 30, -1, -18), (0.40, -192, 80, -7, -8), (0.48, -175, 55, -4, -14),
        (0.56, -98, 8, 7, -34), (0.60, -82, 4, 9, -38), (0.70, -80, 6, 8, -36), (0.86, -60, 22, 2, -24),
        (1.00, -55, 25, 0, -20)]


def key_at(ph):
    ks = KEYS
    for (a, *va), (b, *vb) in zip(ks, ks[1:]):
        if a <= ph <= b:
            u = (ph - a) / (b - a)
            u = u * u * (3 - 2 * u)
            return [x + (y - x) * u for x, y in zip(va, vb)]
    return ks[-1][1:]


def chop_frame(base_P, base_Q, f):
    ph = (f * CHOPS / FRAMES) % 1.0
    sw, el, ln, ad = (math.radians(x) for x in key_at(ph))
    S, E, Hp = joint(base_P, SHOULDER), joint(base_P, SHOULDER + 0.5 * axis), joint(base_P, HIP)
    R_e = rx(-el)                       # flexing folds the forearm forward/up
    R_s = rx(sw) @ rz(ad)
    R_l = rx(ln)                        # positive leans the upper body forward (+z)
    q_e, q_s, q_l = (tr.mat_to_quat(M) for M in (R_e, R_s, R_l))

    def chain(P, w_f, w_a, w_l):
        P = P + w_f[:, None] * ((P - E) @ R_e.T + E - P)
        P = P + w_a[:, None] * ((P - S) @ R_s.T + S - P)
        P = P + w_l[:, None] * ((P - Hp) @ R_l.T + Hp - P)
        return P

    def qchain(Q, w_f, w_a, w_l):
        Q = tr.qmul(qpow(np.broadcast_to(q_e, Q.shape), w_f), Q)
        Q = tr.qmul(qpow(np.broadcast_to(q_s, Q.shape), w_a), Q)
        Q = tr.qmul(qpow(np.broadcast_to(q_l, Q.shape), w_l), Q)
        return Q

    P = chain(base_P, w_fore, w_arm, w_lean)
    Q = qchain(base_Q, w_fore, w_arm, w_lean)
    # the hatchet rides the paw: move it from the idle paw to this pose's paw, then through the rig
    ones = np.ones(NA)
    Hb = base_P[hand_idx].mean(0)
    AP = chain(A_pos - H_i + Hb, ones, ones, ones * w_lean[hand_idx].mean())
    AQ = qchain(q_axe_idle, ones, ones, ones * w_lean[hand_idx].mean())
    return P, Q, AP, AQ


# ---------------------------------------------------------------- rebuild every animation with the extra vertices
new_anims = []
for a in node.vertex_animations:
    frames = []
    if a.name in CUT_ANIMS:
        base = CUT_ANIMS[a.name]
        nb = len(anims[base].frames)
        for f in range(FRAMES):
            bP, bQ = pose(base, f % nb)
            P, Q, AP, AQ = chop_frame(bP, bQ, f)
            off = np.concatenate([P - rest, AP - A_rest])
            rot = np.concatenate([Q, AQ])
            frames.append([tm.VertexProperty.from_array("offset", half(off)),
                           tm.VertexProperty.from_array("rotation", half(rot))])
    else:
        for fr in a.frames:
            fr = {p.name: p for p in fr}
            off = fr["offset"].array(); rot = fr["rotation"].array()
            hide = (rest[hand_idx] + off[hand_idx]).mean(0)       # every hatchet vertex on one point in the paw
            off2 = np.concatenate([off, np.tile(hide, (NA, 1)) - A_rest])
            rot2 = np.concatenate([rot, np.tile(rot[hand_idx[0]], (NA, 1))])
            frames.append([tm.VertexProperty.from_array("offset", half(off2)),
                           tm.VertexProperty.from_array("rotation", half(rot2))])
    new_anims.append(tm.VertexAnimation(a.name, a.framerate, N0 + NA, frames))
    print(a.name, len(frames), end="; ", flush=True)
print()

# ---------------------------------------------------------------- vertex data
props = {p.name: p.array() for p in node.vertex_properties}
uv1_hand = props["uv1"][hand_idx[0]] if "uv1" in props else None
extra = {"position": A_rest, "normal": A_nrm, "tangent": np.c_[A_tan[:, :3], -np.ones(NA)],
         "color": np.ones((NA, 4)), "uv0": A_uv}
if uv1_hand is not None:
    extra["uv1"] = np.tile(uv1_hand, (NA, 1))
node.vertex_properties = [tm.VertexProperty.from_array(p.name, np.concatenate([p.array(), extra[p.name]]))
                          for p in node.vertex_properties]
node.vertex_count = N0 + NA
mp = node.meshes[0]
mp.indices = np.concatenate([mp.indices, (A_tris + N0).reshape(-1)])
node.vertex_animations = new_anims
assert all(np.isfinite(p.array()).all() for a in new_anims for fr in a.frames for p in fr)
tm.write(model, dst)
print("wrote", dst, node.vertex_count, "verts")

# ---------------------------------------------------------------- paint the patches into the textures
tex = os.path.join(out_dir, "textures")
rng = np.random.default_rng(3)
for name in os.listdir(tex):
    if not name.startswith("OtterAdult") or not name.endswith(".png") or "preview" in name:
        continue
    path = os.path.join(tex, name)
    im = np.array(Image.open(path))
    for (x, y), (albedo, (metal, smooth)) in PATCHES.items():
        blk = (slice(y, y + 128), slice(x, x + 128))
        if name.endswith("Normal.png"):
            im[blk][..., :3] = (128, 128, 255)
        elif name.endswith("AO.png"):
            im[blk][..., :3] = 255
        elif name.endswith("Gloss.png"):
            im[blk][..., 0] = metal
            im[blk][..., 3] = smooth
            if im.shape[2] > 2:
                im[blk][..., 1] = smooth
        else:
            noise = rng.normal(0, 6, (128, 128, 1))
            if albedo[0] < 150 and albedo[0] > 100:  # wood: a little grain
                noise += 8 * np.sin(np.arange(128)[None, :, None] * 0.7 + rng.normal(0, 0.4, (128, 1, 1)))
            im[blk][..., :3] = np.clip(np.array(albedo) + noise, 0, 255).astype(np.uint8)
    Image.fromarray(im).save(path)
    print("painted", name)
