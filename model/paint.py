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


# palette: (back, belly) per variant; cream face is shared
ADULT_VARIANTS = [
    ((0.33, 0.22, 0.15), (0.52, 0.38, 0.27)),
    ((0.29, 0.20, 0.14), (0.47, 0.35, 0.25)),
    ((0.38, 0.26, 0.17), (0.57, 0.42, 0.29)),
    ((0.26, 0.18, 0.13), (0.44, 0.33, 0.24)),
]
CHILD_VARIANTS = [
    ((0.40, 0.29, 0.20), (0.60, 0.46, 0.33)),
    ((0.36, 0.26, 0.18), (0.56, 0.43, 0.31)),
    ((0.43, 0.31, 0.21), (0.64, 0.49, 0.35)),
]
CREAM = np.array([0.88, 0.78, 0.62])
DARK = np.array([0.13, 0.095, 0.08])


def paint(P, N, M, A, L, back, belly):
    """P/N: texel positions/normals (Unity space). A: AO per texel. L: anatomy landmarks dict."""
    x, y, z = P[..., 0], P[..., 1], P[..., 2]
    nx, ny, nz = N[..., 0], N[..., 1], N[..., 2]
    ax = np.abs(x)
    back = np.array(back); belly = np.array(belly)
    flat = P[M]
    n1 = np.zeros(M.shape); n1[M] = fbm(flat, 18.0, 3)
    n2 = np.zeros(M.shape); n2[M] = fbm(flat * [1.0, 0.35, 1.0], 140.0, 11, 3)  # fur strokes, stretched along y

    col = back[None, None] * (0.9 + 0.2 * n1[..., None])

    s = L["scale"]
    # belly: warmer, lighter front of torso
    front = smoothstep(0.1, 0.6, nz) * smoothstep(0.08 * s, 0.16 * s, y) * (1 - smoothstep(0.30 * s, 0.36 * s, y)) * (1 - smoothstep(0.07 * s, 0.11 * s, ax))
    col = col * (1 - front[..., None]) + belly * front[..., None]

    # cream throat/chest bib + lower face
    hy = L["head_y"]
    bib = smoothstep(0.15, 0.55, nz) * smoothstep(L["bib_low"], L["bib_low"] + 0.05 * s, y) * (1 - smoothstep(hy + 0.035 * s, hy + 0.055 * s, y))
    bib *= 1 - smoothstep(0.055 * s, 0.085 * s, ax - 0.25 * np.clip(y - L["bib_low"], 0, None))
    muzzle = smoothstep(L["muzzle_z"] - 0.04 * s, L["muzzle_z"], z) * (1 - smoothstep(hy + 0.04 * s, hy + 0.06 * s, y)) * smoothstep(hy - 0.06 * s, hy - 0.03 * s, y)
    cream_w = np.clip(np.maximum(bib, muzzle), 0, 1) * (0.85 + 0.15 * n1)
    col = col * (1 - cream_w[..., None]) + CREAM * cream_w[..., None]

    # paws, feet and tail tip a shade darker
    paws = np.maximum(smoothstep(0.045 * s, 0.02 * s, y), smoothstep(L["hand_x"] - 0.03 * s, L["hand_x"], ax))
    tailtip = smoothstep(L["tail_tip_z"] + 0.12 * s, L["tail_tip_z"] + 0.02 * s, z) * (1 - smoothstep(0.12 * s, 0.2 * s, y))
    darker = np.clip(np.maximum(paws * 0.32, tailtip * 0.4), 0, 1)
    col = col * (1 - darker[..., None])

    # ears: dark rim
    for sgn in (-1, 1):
        e = np.array(L["ear"]) * [sgn, 1, 1]
        de = np.linalg.norm(P - e, axis=-1)
        col = col * (1 - 0.5 * smoothstep(0.03 * s, 0.015 * s, de))[..., None]

    # nose: dark leathery rhinarium, wider at the top (rounded triangle), with a highlight and a mouth line below
    nc = np.array(L["nose"])
    rel = P - nc
    half_w = (0.017 + 0.35 * np.clip(rel[..., 1], -0.03, 0.03)) * s
    inside = (np.abs(rel[..., 0]) / np.maximum(half_w, 1e-4)) ** 2 + (rel[..., 1] / (0.013 * s)) ** 2
    nose_w = smoothstep(1.25, 0.85, inside) * smoothstep(-0.1, 0.3, nz) * (rel[..., 2] > -0.02 * s)
    col = col * (1 - nose_w[..., None]) + DARK * nose_w[..., None]
    hl = smoothstep(0.006 * s, 0.0015 * s, np.linalg.norm(P - (nc + [0.006 * s, 0.006 * s, 0.01 * s]), axis=-1))
    col = col + 0.4 * hl[..., None]
    # philtrum + little smile (soft lines so they don't stair-step)
    mx = np.abs(rel[..., 0])
    ph = smoothstep(0.0024 * s, 0.0009 * s, mx) * smoothstep(-0.026 * s, -0.022 * s, rel[..., 1]) * smoothstep(-0.009 * s, -0.012 * s, rel[..., 1])
    curve = -0.024 * s - 0.25 * mx + 9.0 * mx * mx / s
    smile = smoothstep(0.0024 * s, 0.0009 * s, np.abs(rel[..., 1] - curve)) * smoothstep(0.022 * s, 0.017 * s, mx)
    mouth = np.maximum(ph, smile) * smoothstep(0.15, 0.35, nz) * (np.abs(rel[..., 2]) < 0.03 * s)
    col = col * (1 - 0.55 * mouth[..., None])

    # whisker dots on the pads
    for sgn in (-1, 1):
        for (dx, dy) in [(0.012, 0.004), (0.022, 0.0), (0.03, -0.006), (0.017, -0.01), (0.027, -0.015)]:
            c = np.array(L["whisker"]) + [sgn * dx * s, dy * s, 0]
            dd = np.linalg.norm((P - c)[..., :2], axis=-1)
            w = smoothstep(0.003 * s, 0.0015 * s, dd) * smoothstep(0.2, 0.5, nz)
            col = col * (1 - 0.6 * w[..., None])

    # eyes: dark glossy with a white catch-light, slight cream ring
    for sgn in (-1, 1):
        c = np.array(L["eye"]) * [sgn, 1, 1]
        front_face = smoothstep(0.0, 0.35, nz) * (np.abs(z - c[2]) < 0.05 * s)
        d2 = np.linalg.norm((P - c)[..., :2] / [1.0, 1.15], axis=-1)
        ring = smoothstep(L["eye_r"] * 1.55, L["eye_r"] * 1.25, d2) * front_face
        col = col * (1 - 0.25 * ring[..., None]) + CREAM * 0.25 * ring[..., None]
        eye = smoothstep(L["eye_r"] * 1.05, L["eye_r"] * 0.85, d2) * front_face
        col = col * (1 - eye[..., None]) + np.array([0.05, 0.04, 0.04]) * eye[..., None]
        glint_c = c + [sgn * 0.004 * s, 0.005 * s, 0]
        glint = smoothstep(L["eye_r"] * 0.38, L["eye_r"] * 0.22, np.linalg.norm((P - glint_c)[..., :2], axis=-1)) * front_face
        col = col * (1 - glint[..., None]) + 0.95 * glint[..., None]

    # fur strokes and AO
    col = col * (0.88 + 0.24 * n2[..., None])
    col = col * (0.55 + 0.45 * A[..., None])
    # soft top light: backs and heads a hair lighter, undersides darker (matches the game's painted look)
    col = col * (0.9 + 0.12 * np.clip(ny, -1, 1)[..., None])
    return np.clip(col, 0, 1)


def make_textures(otter, landmarks, variants, size, out_paths, uv_key="uv0"):
    pos, nrm, tris, uv = otter["pos"], otter["nrm"], otter["tris"], otter[uv_key]
    P, N, M, TRI, BAR = rasterize(uv, tris, pos, nrm, size)
    ao_v = vertex_ao(pos, tris, nrm)
    A = np.ones(M.shape)
    A[M] = np.einsum("ij,ij->i", BAR[M], ao_v[tris[TRI[M]]])
    for (back, belly), path in zip(variants, out_paths):
        col = paint(P, N, M, A, landmarks, back, belly)
        col = dilate(col, M, 16)
        col[~ndimage.binary_dilation(M, iterations=16)] = np.array(back) * 0.8
        img = (np.flipud(col) * 255 + 0.5).astype(np.uint8)  # texture rows: v=1 at the top
        Image.fromarray(img, "RGB").save(path)
    return ao_v
