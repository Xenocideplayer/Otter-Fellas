"""Procedurally paint otter fur textures in the otter's own UV layout.

Every texel is mapped back to its 3D position/normal on the otter (Unity space) and coloured by anatomy:
dark brown back, cream face/throat/chest, warmer belly, dark nose/paws/tail tip, glossy eyes, fur strokes,
baked ambient occlusion.
"""
import numpy as np
import trimesh
from PIL import Image
from scipy import ndimage


def _value_noise3(P, freq, seed):
    rng = np.random.default_rng(seed)
    g = rng.random((64, 64, 64))
    q = P * freq
    i = np.floor(q).astype(int)
    f = q - i
    f = f * f * (3 - 2 * f)
    out = 0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (f[:, 0] if dx else 1 - f[:, 0]) * (f[:, 1] if dy else 1 - f[:, 1]) * (f[:, 2] if dz else 1 - f[:, 2])
                out = out + w * g[(i[:, 0] + dx) % 64, (i[:, 1] + dy) % 64, (i[:, 2] + dz) % 64]
    return out


def fbm(P, freq, seed, octaves=4):
    tot, amp, norm = 0, 1.0, 0
    for o in range(octaves):
        tot = tot + amp * _value_noise3(P, freq * 2 ** o, seed + o)
        norm += amp
        amp *= 0.5
    return tot / norm


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def rasterize(uv, tris, pos, nrm, size):
    """Returns per-texel 3D position, normal, a coverage mask and per-texel vertex weights (for AO)."""
    H = W = size
    P = np.zeros((H, W, 3)); N = np.zeros((H, W, 3)); M = np.zeros((H, W), bool)
    TRI = np.full((H, W), -1, np.int64); BAR = np.zeros((H, W, 3))
    px = uv * [W, H]
    for ti, t in enumerate(tris):
        a, b, c = px[t]
        x0, x1 = int(np.floor(min(a[0], b[0], c[0]))), int(np.ceil(max(a[0], b[0], c[0])))
        y0, y1 = int(np.floor(min(a[1], b[1], c[1]))), int(np.ceil(max(a[1], b[1], c[1])))
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, W - 1), min(y1, H - 1)
        if x1 < x0 or y1 < y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        det = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(det) < 1e-12:
            continue
        l1 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / det
        l2 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / det
        l3 = 1 - l1 - l2
        eps = -0.02
        ok = (l1 >= eps) & (l2 >= eps) & (l3 >= eps)
        if not ok.any():
            continue
        yy = (ys[ok] - 0.5).astype(int); xx = (xs[ok] - 0.5).astype(int)
        L = np.stack([l1[ok], l2[ok], l3[ok]], 1)
        L = np.clip(L, 0, None); L /= L.sum(1, keepdims=True)
        P[yy, xx] = L @ pos[t]
        n = L @ nrm[t]
        N[yy, xx] = n / np.linalg.norm(n, axis=1, keepdims=True)
        M[yy, xx] = True
        TRI[yy, xx] = ti
        BAR[yy, xx] = L
    return P, N, M, TRI, BAR


def vertex_ao(pos, tris, nrm, rays=96, dist=0.12, seed=1):
    mesh = trimesh.Trimesh(pos, tris, process=False)
    rng = np.random.default_rng(seed)
    dirs = rng.normal(size=(rays, 3)); dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
    ao = np.zeros(len(pos))
    for i in range(0, len(pos), 64):
        p = pos[i:i + 64]; n = nrm[i:i + 64]
        D = np.repeat(dirs[None], len(p), 0)
        flip = np.einsum("ijk,ik->ij", D, n) < 0
        D[flip] *= -1
        O = np.repeat(p[:, None] + n[:, None] * 0.002, rays, 1)
        loc, idx_ray, _ = mesh.ray.intersects_location(O.reshape(-1, 3), D.reshape(-1, 3), multiple_hits=False)
        hit = np.zeros(len(p) * rays, bool)
        if len(idx_ray):
            dd = np.linalg.norm(loc - O.reshape(-1, 3)[idx_ray], axis=1)
            hit[idx_ray[dd < dist]] = True
        ao[i:i + 64] = 1 - hit.reshape(len(p), rays).mean(1)
    return ao


def dilate(img, mask, steps=12):
    img = img.copy(); m = mask.copy()
    for _ in range(steps):
        grown = ndimage.binary_dilation(m)
        new = grown & ~m
        if not new.any():
            break
        acc = np.zeros_like(img); cnt = np.zeros(img.shape[:2])
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                sh_img = np.roll(np.roll(img, dy, 0), dx, 1)
                sh_m = np.roll(np.roll(m, dy, 0), dx, 1)
                acc += sh_img * sh_m[..., None]; cnt += sh_m
        img[new] = acc[new] / np.maximum(cnt[new], 1)[:, None]
        m = grown
    return img


# palette: (back, belly) per variant. Muted browns in the same range as the game's own beaver textures (beaver back
# ~(0.43, 0.24, 0.15), belly ~(0.47, 0.28, 0.18), head ~(0.51, 0.34, 0.22)): river otters a little darker and cooler.
ADULT_VARIANTS = [
    ((0.38, 0.23, 0.15), (0.50, 0.34, 0.23)),
    ((0.32, 0.20, 0.13), (0.46, 0.31, 0.21)),
    ((0.43, 0.27, 0.17), (0.55, 0.38, 0.26)),
    ((0.34, 0.23, 0.16), (0.48, 0.35, 0.25)),
]
CHILD_VARIANTS = [
    ((0.46, 0.30, 0.19), (0.58, 0.42, 0.30)),
    ((0.41, 0.27, 0.17), (0.55, 0.40, 0.28)),
    ((0.50, 0.33, 0.21), (0.62, 0.46, 0.33)),
]
SICK_VARIANT = ((0.30, 0.31, 0.2), (0.45, 0.46, 0.32))
CREAM = np.array([0.70, 0.58, 0.45])   # a pale tan throat, soft like the beavers' lighter muzzles
DARK = np.array([0.27, 0.14, 0.11])
STRAW_A = np.array([0.83, 0.70, 0.38])
STRAW_B = np.array([0.62, 0.50, 0.25])
STRAW_EDGE = np.array([0.30, 0.21, 0.10])
SHELL = np.array([0.95, 0.86, 0.80])


def lerp(a, b, w):
    return a * (1 - w[..., None]) + b * w[..., None]


# The base fur carries only the otters' badge and a light strap: the game's job outfits (hats, aprons, tools) are put
# on over it, and a fully painted outfit underneath clashed with them.
SIMPLE_OUTFIT = True
STRAP_WIDTH = 0.6        # share of the full strap width kept in the simple outfit


def regions(P, N, L):
    """Masks shared by colour, normal and gloss maps."""
    x, y, z = P[..., 0], P[..., 1], P[..., 2]
    nz = N[..., 2]
    s = L["scale"]
    R = {}
    Z = np.zeros(P.shape[:2])
    for k in ("sash", "sash_edge", "weave", "shell", "shell_rib", "shell_rim", "buckle", "apron", "apron_stitch",
              "apron_patch", "belt", "belt_edge", "rivet", "cuff_cloth", "cuff_leather"):
        R[k] = Z.copy()
    if L.get("sash"):
        front = smoothstep(0.05, 0.35, nz)
        y0, k, w = L["sash"]
        if SIMPLE_OUTFIT:
            w = w * STRAP_WIDTH
        across = ((y - y0) - k * x) / np.sqrt(1 + k * k)
        along = (x + k * (y - y0)) / np.sqrt(1 + k * k)
        torso = smoothstep(0.125 * s, 0.11 * s, np.abs(x)) * smoothstep(0.12 * s, 0.15 * s, y) * smoothstep(0.40 * s, 0.37 * s, y)
        # leather crossbelt with stitched edges ("sash" = strap; "weave" = stitches/grain)
        R["sash"] = smoothstep(w * 0.5 + 0.0015, w * 0.5 - 0.0015, np.abs(across)) * torso
        R["sash_edge"] = smoothstep(0.0025, 0.0, np.abs(np.abs(across) - w * 0.5)) * torso
        dash = np.sin(along * 2 * np.pi / 0.007) > 0.1
        R["weave"] = smoothstep(0.0013, 0.0004, np.abs(np.abs(across) - (w * 0.5 - 0.0042))) * dash * R["sash"]
        # gold buckle up near the shoulder
        bx = L["buckle_x"]
        ab = (bx + k * (k * bx)) / np.sqrt(1 + k * k)
        ring = np.maximum(np.abs(along - ab) / 0.011, np.abs(across) / (w * 0.5 + 0.004))
        R["buckle"] = smoothstep(1.0, 0.92, ring) * smoothstep(0.62, 0.72, ring) * torso * front
        # gold diamond badge with a scallop shell where the strap crosses the chest
        c = np.array([L["clasp_x"], y0 + k * L["clasp_x"], 0.0])
        dx, dy = x - c[0], y - c[1]
        dia = (np.abs(dx) + np.abs(dy)) / (0.038 * s)
        R["shell_rim"] = smoothstep(1.0, 0.93, dia) * front                       # gold frame
        R["shell"] = smoothstep(0.78, 0.7, dia) * front                            # inner plate
        fan = np.hypot(dx, dy + 0.011 * s) * (1.0 + 0.5 * smoothstep(0.0, -0.015 * s, dy))
        shell = smoothstep(0.021 * s, 0.0185 * s, fan) * (dy > -0.015 * s) * front
        ang = np.arctan2(dy + 0.011 * s, dx)
        R["shell_rib"] = shell * (0.55 + 0.45 * np.cos(ang * 18))
        # patchwork apron over the belly and thighs (front only)
        ax_ = np.abs(x)
        top = L["apron_top"] - 0.25 * (ax_ / s) ** 2
        apron = smoothstep(0.05, 0.2, nz) * smoothstep(top + 0.002, top - 0.002, y) * smoothstep(0.035 * s, 0.05 * s, y)
        apron *= smoothstep(0.112 * s, 0.1 * s, ax_)
        R["apron"] = apron
        seeds = np.array([[-0.06, 0.22], [0.03, 0.235], [0.075, 0.17], [-0.03, 0.15], [0.02, 0.1], [-0.07, 0.08],
                          [0.07, 0.07], [-0.01, 0.045], [0.05, 0.13], [-0.075, 0.16]]) * [s, s]
        dd = np.stack([np.hypot(x - sx, (y - sy) * 1.15) for sx, sy in seeds], -1)
        order = np.sort(dd, -1)
        R["apron_patch"] = np.argmin(dd, -1).astype(np.float64)
        seam = smoothstep(0.0022 * s, 0.0008 * s, order[..., 1] - order[..., 0])
        stitch = np.sin((x + y) * 2 * np.pi / (0.006 * s)) > 0.2
        edge_d = np.minimum(np.abs(y - top), np.abs(ax_ - 0.106 * s))
        border = smoothstep(0.0015 * s, 0.0004 * s, np.abs(edge_d - 0.005 * s)) * (np.sin(y * 2 * np.pi / (0.006 * s)) > 0.2)
        R["apron_stitch"] = np.clip((seam * stitch + border), 0, 1) * apron
        # leather belt round the waist with two gold rivets in front
        by = L["belt_y"]
        R["belt"] = smoothstep(0.0105 * s, 0.0085 * s, np.abs(y - by)) * smoothstep(0.128 * s, 0.115 * s, ax_)
        R["belt_edge"] = smoothstep(0.002, 0.0, np.abs(np.abs(y - by) - 0.0095 * s)) * R["belt"]
        for rx in (-0.032, 0.032):
            R["rivet"] = np.maximum(R["rivet"], smoothstep(0.0045 * s, 0.0032 * s, np.hypot(x - rx * s, y - by)) * front)
        # wrist cuffs: green cloth with a leather band nearest the paw
        arm = smoothstep(0.1 * s, 0.13 * s, y)
        hx = L["hand_x"]
        R["cuff_cloth"] = smoothstep(hx - 0.042 * s, hx - 0.038 * s, ax_) * smoothstep(hx - 0.02 * s, hx - 0.024 * s, ax_) * arm
        R["cuff_leather"] = smoothstep(hx - 0.024 * s, hx - 0.02 * s, ax_) * smoothstep(hx - 0.01 * s, hx - 0.014 * s, ax_) * arm
    if SIMPLE_OUTFIT:
        for k in ("buckle", "apron", "apron_stitch", "belt", "belt_edge", "rivet", "cuff_cloth", "cuff_leather"):
            R[k] = Z.copy()
    # where the beaver's detail doesn't fit: the new tail and the otter face
    tail = smoothstep(L["tail_start_z"], L["tail_start_z"] - 0.03 * s, z) * smoothstep(0.24 * s, 0.18 * s, y)
    mc = np.array(L["muzzle_c"])
    face = smoothstep(0.105 * s, 0.06 * s, np.linalg.norm(P - mc, axis=-1)) * smoothstep(-0.35, 0.15, nz)
    R["procedural"] = np.clip(np.maximum(tail, face), 0, 1)
    return R


def paint(P, N, M, A, L, back, belly, R, detail):
    """P/N: texel positions/normals (Unity space). A: AO per texel. R: masks. detail: baked fur detail (1 = none)."""
    x, y, z = P[..., 0], P[..., 1], P[..., 2]
    nx, ny, nz = N[..., 0], N[..., 1], N[..., 2]
    ax = np.abs(x)
    back = np.array(back); belly = np.array(belly)
    flat = P[M]
    n1 = np.zeros(M.shape); n1[M] = fbm(flat, 18.0, 3)
    n2 = np.zeros(M.shape); n2[M] = fbm(flat * [1.0, 0.35, 1.0], 140.0, 11, 3)  # fur strokes, stretched along y
    s = L["scale"]

    col = back[None, None] * (0.94 + 0.12 * n1[..., None])
    # darker along the spine, like a painted dorsal shadow
    spine = smoothstep(-0.2, -0.7, nz) * smoothstep(0.06 * s, 0.0, ax) * smoothstep(0.05 * s, 0.15 * s, y)
    col = col * (1 - 0.18 * spine[..., None])

    # belly: warmer, lighter front of torso
    front = smoothstep(0.1, 0.6, nz) * smoothstep(0.08 * s, 0.16 * s, y) * (1 - smoothstep(0.30 * s, 0.36 * s, y)) * (1 - smoothstep(0.07 * s, 0.11 * s, ax))
    col = lerp(col, belly, front)

    # cream throat/chest bib + lower face, with a soft darker seam where the colours meet
    hy = L["head_y"]
    bib = smoothstep(0.15, 0.55, nz) * smoothstep(L["bib_low"], L["bib_low"] + 0.05 * s, y) * (1 - smoothstep(hy + 0.035 * s, hy + 0.055 * s, y))
    bib *= 1 - smoothstep(0.045 * s, 0.1 * s, ax - 0.25 * np.clip(y - L["bib_low"], 0, None))   # soft edge
    eye_y = L["eye"][1]          # pale lips and chin only: brown face up from just under the eyes, like a river otter
    muzzle = smoothstep(L["muzzle_z"] - 0.04 * s, L["muzzle_z"], z) * (1 - smoothstep(eye_y - 0.04 * s, eye_y - 0.02 * s, y)) * smoothstep(hy - 0.06 * s, hy - 0.03 * s, y)
    cream_w = np.clip(np.maximum(bib, muzzle), 0, 1)
    col = lerp(col, CREAM * (0.97 + 0.06 * n1[..., None]), cream_w * 0.85)

    # paws, feet and tail tip a shade darker
    paws = np.maximum(smoothstep(0.045 * s, 0.02 * s, y), smoothstep(L["hand_x"] - 0.03 * s, L["hand_x"], ax))
    tailtip = smoothstep(L["tail_tip_z"] + 0.12 * s, L["tail_tip_z"] + 0.02 * s, z) * (1 - smoothstep(0.12 * s, 0.2 * s, y))
    darker = np.clip(np.maximum(paws * 0.42, tailtip * 0.3), 0, 1)     # dark paws, as the beavers have
    col = col * (1 - darker[..., None])

    # ears: darker rim, warm pink inside (front-facing side)
    for sgn in (-1, 1):
        e = np.array(L["ear"]) * [sgn, 1, 1]
        de = np.linalg.norm(P - e, axis=-1)
        col = col * (1 - 0.15 * smoothstep(0.034 * s, 0.022 * s, de))[..., None]
        inner = smoothstep(0.02 * s, 0.012 * s, de) * smoothstep(0.0, 0.4, nz)
        col = lerp(col, np.array([0.52, 0.34, 0.28]), inner * 0.6)

    # nose: dark leathery rhinarium, wider at the top (rounded triangle), with a highlight and a mouth line below
    nc = np.array(L["nose"])
    rel = P - nc
    half_w = (0.025 + 0.4 * np.clip(rel[..., 1], -0.03, 0.03)) * s
    inside = (np.abs(rel[..., 0]) / np.maximum(half_w, 1e-4)) ** 2 + (rel[..., 1] / (0.018 * s)) ** 2
    nose_w = smoothstep(1.25, 0.85, inside) * smoothstep(-0.1, 0.3, nz) * (rel[..., 2] > -0.02 * s)
    col = lerp(col, DARK, nose_w)
    hl = smoothstep(0.006 * s, 0.0015 * s, np.linalg.norm(P - (nc + [0.006 * s, 0.006 * s, 0.01 * s]), axis=-1))
    col = col + 0.2 * hl[..., None]
    # philtrum + little smile (soft lines so they don't stair-step)
    mx = np.abs(rel[..., 0])
    ph = smoothstep(0.0024 * s, 0.0009 * s, mx) * smoothstep(-0.026 * s, -0.022 * s, rel[..., 1]) * smoothstep(-0.009 * s, -0.012 * s, rel[..., 1])
    curve = -0.031 * s + 40.0 * (mx - 0.009 * s) ** 2 / s          # a soft "ω" smile
    smile = smoothstep(0.0024 * s, 0.0009 * s, np.abs(rel[..., 1] - curve)) * smoothstep(0.021 * s, 0.018 * s, mx)
    mouth = np.maximum(ph, smile) * smoothstep(0.15, 0.35, nz) * (np.abs(rel[..., 2]) < 0.03 * s)
    col = col * (1 - 0.14 * mouth[..., None])            # only a hint of a mouth: the beavers have none painted

    # whiskers: thin light strokes fanning out across the cheeks
    for sgn in (-1, 1):
        base = np.array(L["whisker"]) + [sgn * 0.02 * s, -0.002 * s, 0]
        for ang in (-18, -6, 6, 16):
            dvec = np.array([sgn * np.cos(np.radians(ang)), np.sin(np.radians(ang))])
            q = (P[..., :2] - base[:2])
            t = np.clip(q @ dvec, 0, 0.075 * s)
            dist = np.linalg.norm(q - t[..., None] * dvec, axis=-1)
            wsk = smoothstep(0.0016 * s, 0.0006 * s, dist) * (t > 0.004 * s) * smoothstep(0.0, 0.25, nz)
            col = lerp(col, np.array([0.97, 0.95, 0.9]), wsk * 0.0)   # no painted whiskers (beavers have none)

    # whisker dots on the pads
    for sgn in (-1, 1):
        for (dx, dy) in [(0.012, 0.004), (0.022, 0.0), (0.03, -0.006), (0.017, -0.01), (0.027, -0.015)]:
            c = np.array(L["whisker"]) + [sgn * dx * s, dy * s, 0]
            dd = np.linalg.norm((P - c)[..., :2], axis=-1)
            w = smoothstep(0.003 * s, 0.0015 * s, dd) * smoothstep(0.2, 0.5, nz)
            col = col * (1 - 0.1 * w[..., None])

    # eyes, cartoon style: dark brown iris with a lighter ring, black pupil, a cream rim along the lower edge,
    # a heavy upper lid line, two catch-lights and a furry brow tuft
    for sgn in (-1, 1):
        c = np.array(L["eye"]) * [sgn, 1, 1]
        er = L["eye_r"] * 0.85   # smaller painted eyes, closer to the beavers' little dark eyes
        front_face = smoothstep(-0.1, 0.3, nz) * (np.abs(z - c[2]) < 0.06 * s)
        rel2 = (P - c)[..., :2] / [1.0, 1.12]
        d2 = np.linalg.norm(rel2, axis=-1)
        # brow tuft: a darker swoosh above and slightly outward
        bc = c + [sgn * 0.004 * s, er * 1.35, 0]
        bd = np.linalg.norm((P - bc)[..., :2] / [1.25, 0.55], axis=-1)
        brow = smoothstep(er * 1.25, er * 0.7, bd) * front_face
        col = col * (1 - 0.0 * brow[..., None])                       # no brow tuft
        rim = smoothstep(er * 1.22, er * 1.05, d2) * (rel2[..., 1] < -0.15 * er) * front_face
        col = lerp(col, np.array([0.93, 0.88, 0.78]), rim * 0.0)
        eye = smoothstep(er * 1.04, er * 0.9, d2) * front_face
        col = lerp(col, np.array([0.03, 0.02, 0.02]), eye)
        iris = smoothstep(er * 0.86, er * 0.7, d2) * front_face
        col = lerp(col, np.array([0.12, 0.08, 0.05]), iris)          # simple dark eyes, like the beavers'
        pupil = smoothstep(er * 0.52, er * 0.4, d2) * front_face
        col = lerp(col, np.array([0.02, 0.015, 0.01]), pupil)
        lid = smoothstep(er * 0.16, er * 0.0, np.abs(d2 - er * 1.0)) * (rel2[..., 1] > 0.1 * er) * front_face
        col = lerp(col, np.array([0.05, 0.03, 0.02]), lid * 0.0)
        for (gx, gy, gr) in ((-0.3, 0.32, 0.24),):
            gc = c + [sgn * gx * er, gy * er, 0]
            glint = smoothstep(er * gr, er * gr * 0.55, np.linalg.norm((P - gc)[..., :2], axis=-1)) * front_face
            col = lerp(col, np.array([0.98, 0.98, 0.96]), glint)

    # fur detail: the game's painted strands where they fit, procedural strokes elsewhere
    proc = R["procedural"]
    det = detail * (1 - proc) + (0.95 + 0.1 * n2) * proc
    col = col * det[..., None] ** 0.6

    # outfit (adults): patchwork apron, belt, leather strap with buckle, gold shell badge, wrist cuffs
    if L.get("sash"):
        patches = np.array([[0.33, 0.50, 0.60], [0.42, 0.58, 0.50], [0.50, 0.63, 0.67], [0.30, 0.45, 0.52],
                            [0.45, 0.60, 0.56], [0.36, 0.53, 0.63], [0.52, 0.64, 0.58], [0.31, 0.47, 0.55],
                            [0.40, 0.56, 0.64], [0.46, 0.62, 0.52]])
        cloth = patches[R["apron_patch"].astype(int) % len(patches)] * (0.85 + 0.3 * n1[..., None])
        col = lerp(col, cloth, R["apron"])
        col = lerp(col, np.array([0.90, 0.86, 0.74]), R["apron_stitch"] * 0.9)
        cuff = np.array([0.50, 0.55, 0.36]) * (0.85 + 0.3 * n1[..., None])
        col = lerp(col, cuff, R["cuff_cloth"])
        leather = np.array([0.36, 0.21, 0.12]) * (0.85 + 0.3 * n1[..., None])
        col = lerp(col, leather, np.maximum(R["cuff_leather"], R["belt"]))
        col = lerp(col, np.array([0.2, 0.11, 0.06]), R["belt_edge"] * 0.8)
        col = lerp(col, leather * (1.25 if SIMPLE_OUTFIT else 1.05), R["sash"] * (0.85 if SIMPLE_OUTFIT else 1.0))
        col = lerp(col, np.array([0.2, 0.11, 0.06]), R["sash_edge"] * 0.85)
        col = lerp(col, np.array([0.78, 0.66, 0.48]), R["weave"] * 0.8)
        gold = np.array([0.86, 0.66, 0.26])
        col = lerp(col, gold * (0.85 + 0.25 * n1[..., None]), np.maximum(R["buckle"], R["rivet"]))
        col = lerp(col, gold, R["shell_rim"])
        col = lerp(col, np.array([0.55, 0.38, 0.14]), R["shell"])
        col = lerp(col, np.array([0.95, 0.89, 0.76]) * (0.82 + 0.18 * (R["shell_rib"] > 0.5)[..., None]), (R["shell_rib"] > 0).astype(float))

    # painted fur clumps: soft vertical streaks with lighter tips, like hand-painted strokes
    clump = np.zeros(M.shape); clump[M] = fbm(flat * [1.0, 0.28, 1.0], 55.0, 21, 3)
    tips = smoothstep(0.55, 0.75, clump) * (1 - R["sash"]) * (1 - R["shell"])
    col = col * (0.95 + 0.1 * clump[..., None])
    col = col + 0.015 * tips[..., None] * (1 - cream_w[..., None] * 0.5)
    col = col * (0.72 + 0.28 * A[..., None])
    # painted light: tops and faces lighter, undersides and backs darker
    col = col * (0.9 + 0.16 * np.clip(ny, -1, 1)[..., None] + 0.04 * np.clip(nz, 0, 1)[..., None])
    return np.clip(col, 0, 1), dict(nose=nose_w, eyes=None)


def gloss_map(P, N, L, R):
    s = L["scale"]
    g = np.full(P.shape[:2], 0.16)
    for sgn in (-1, 1):
        c = np.array(L["eye"]) * [sgn, 1, 1]
        d2 = np.linalg.norm((P - c)[..., :2] / [1.0, 1.15], axis=-1)
        g = np.maximum(g, 0.5 * smoothstep(L["eye_r"] * 0.9, L["eye_r"] * 0.72, d2) * smoothstep(0.0, 0.35, N[..., 2]))
    nd = np.linalg.norm(P - np.array(L["nose"]), axis=-1)
    g = np.maximum(g, 0.4 * smoothstep(0.02 * s, 0.012 * s, nd))
    g = np.maximum(g, 0.7 * np.maximum(R["shell_rim"], np.maximum(R["buckle"], R["rivet"])))
    return g


def make_textures(otter, landmarks, variants, size, out_paths, beaver=None, beaver_maps=None, maps_prefix=None, hires=None):
    """Writes one diffuse texture per variant; with beaver data also writes <maps_prefix>Normal/AO/Gloss.png."""
    import bake_detail as bk
    import meshutil
    pos, nrm, tris, uv = otter["pos"], otter["nrm"], otter["tris"], otter["uv0"]
    P, N, M, TRI, BAR = rasterize(uv, tris, pos, nrm, size)
    ao_v = vertex_ao(pos, tris, nrm)
    A = np.ones(M.shape)
    A[M] = np.einsum("ij,ij->i", BAR[M], ao_v[tris[TRI[M]]])
    R = regions(P, N, landmarks)
    detail = np.ones(M.shape)
    if beaver is not None:
        tan = meshutil.tangents(pos, uv, tris, nrm)
        T = np.zeros_like(P)
        T[M] = np.einsum("ij,ijc->ic", BAR[M], tan[tris[TRI[M]]])
        T[M] -= N[M] * np.sum(T[M] * N[M], 1, keepdims=True)
        T[M] /= np.maximum(np.linalg.norm(T[M], axis=1, keepdims=True), 1e-9)
        b = bk.bake(dict(P=P[M], N=N[M], T=T[M]), beaver, beaver_maps, hires=hires)
        far = smoothstep(0.012 * landmarks["scale"], 0.03 * landmarks["scale"], b["dist"])
        R["procedural"][M] = np.maximum(R["procedural"][M], far)
        detail[M] = b["detail"]
        # ---- normal map
        flat = P[M]
        h = np.zeros(M.shape); h[M] = fbm(flat * [1.0, 0.35, 1.0], 140.0, 11, 3)
        h = h * 0.6 + R["weave"] * R["sash"] * 1.2 + R["shell_rib"] * 0.6
        pn = bk.procedural_fur_normal(ndimage.gaussian_filter(h, 0.7), 2.2)
        nt = np.zeros_like(P); nt[..., 2] = 1
        nt[M] = b["normal_ts"]
        sh = np.zeros_like(P); sh[..., 2] = 1
        sh[M] = b["shape_ts"]
        # procedural areas: smooth sculpt normal tilted by the procedural fur strokes
        pn_on_shape = sh + np.concatenate([pn[..., :2], np.zeros(M.shape + (1,))], -1)
        pn_on_shape /= np.linalg.norm(pn_on_shape, axis=-1, keepdims=True)
        w = R["procedural"][..., None]
        nmix = nt * (1 - w) + pn_on_shape * w
        # straw weave and shell bumps on top of everything
        bump = bk.procedural_fur_normal(ndimage.gaussian_filter(R["weave"] * R["sash"] + R["shell_rib"] * 0.6, 0.7), 2.5)
        nmix[..., :2] += bump[..., :2] * np.maximum(R["sash"], R["shell"])[..., None]
        nmix /= np.linalg.norm(nmix, axis=-1, keepdims=True)
        nmix = dilate(nmix, M, 16)
        nmix[~ndimage.binary_dilation(M, iterations=16)] = [0, 0, 1]
        rgba = np.concatenate([nmix * 0.5 + 0.5, np.ones(M.shape + (1,))], -1)
        # object-space copy (Blender axes) only for preview renders
        Bt = -np.cross(N, T)
        osn = T * nmix[..., :1] + Bt * nmix[..., 1:2] + N * nmix[..., 2:3]
        osn = osn[..., [0, 2, 1]]
        osn /= np.maximum(np.linalg.norm(osn, axis=-1, keepdims=True), 1e-9)
        osn = dilate(osn, M, 16)
        Image.fromarray((np.flipud(osn * 0.5 + 0.5) * 255 + 0.5).astype(np.uint8), "RGB").save(maps_prefix + "NormalOS_preview.png")
        # Blender tangent-space copy (Y along +V) so posed preview renders light correctly
        bv = meshutil.uv_bitangents(pos, uv, tris, nrm)
        Bv = np.zeros_like(P); Bv[M] = np.einsum("ij,ijc->ic", BAR[M], bv[tris[TRI[M]]])
        wn = T * nmix[..., :1] + Bt * nmix[..., 1:2] + N * nmix[..., 2:3]
        Bv -= N * np.sum(Bv * N, -1, keepdims=True)
        Bv /= np.maximum(np.linalg.norm(Bv, axis=-1, keepdims=True), 1e-9)
        bts = np.stack([np.sum(wn * T, -1), np.sum(wn * Bv, -1), np.sum(wn * N, -1)], -1)
        bts = dilate(bts, M, 16)
        bts[~ndimage.binary_dilation(M, iterations=16)] = [0, 0, 1]
        Image.fromarray((np.flipud(bts * 0.5 + 0.5) * 255 + 0.5).astype(np.uint8), "RGB").save(maps_prefix + "NormalTS_blender_preview.png")
        Image.fromarray((np.flipud(rgba) * 255 + 0.5).astype(np.uint8), "RGBA").save(maps_prefix + "Normal.png")
        # ---- ambient occlusion
        ao = A.copy()
        bao = np.ones(M.shape); bao[M] = b["ao"]
        ao = np.clip(ao ** 0.8 * (bao ** 0.6 * (1 - R["procedural"]) + R["procedural"]), 0, 1)
        ao = dilate(ao[..., None], M, 16)[..., 0]
        ao[~ndimage.binary_dilation(M, iterations=16)] = 1
        Image.fromarray((np.flipud(ao) * 255 + 0.5).astype(np.uint8), "L").convert("RGB").save(maps_prefix + "AO.png")
        # ---- metallic (R) / smoothness (A)
        g = gloss_map(P, N, landmarks, R)
        g = dilate(g[..., None], M, 16)[..., 0]
        g[~ndimage.binary_dilation(M, iterations=16)] = 0.16
        met = np.stack([np.zeros_like(g), g, np.zeros_like(g), g], -1)
        Image.fromarray((np.flipud(met) * 255 + 0.5).astype(np.uint8), "RGBA").save(maps_prefix + "Gloss.png")
    for (back, belly), path in zip(variants, out_paths):
        col, _ = paint(P, N, M, A, landmarks, back, belly, R, detail)
        col = dilate(col, M, 16)
        col[~ndimage.binary_dilation(M, iterations=16)] = np.array(back) * 0.8
        img = (np.flipud(col) * 255 + 0.5).astype(np.uint8)  # texture rows: v=1 at the top
        Image.fromarray(img, "RGB").save(path)
    return ao_v
