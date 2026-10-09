"""Bake the game's own fur detail onto the otter's UV layout.

For every otter texel we find the nearest point on the beaver body (dense surface samples + KD-tree), look up the
beaver's UV there and sample its normal map, ambient-occlusion map and painted fur (high-passed). The beaver's
tangent-space normal is converted to object space with the beaver's tangent frame and re-encoded in the otter's
tangent frame, using Unity's convention bitangent = cross(normal, tangent) * w (w = -1 on these meshes).
Where the otter differs from the beaver (new tail, otter face) a procedural fur normal is used instead.
"""
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree


def surface_samples(pos, tris, spacing):
    """Barycentric grid samples over every triangle, about `spacing` apart."""
    out_tri, out_bar = [], []
    for ti, (a, b, c) in enumerate(tris):
        A, B, C = pos[a], pos[b], pos[c]
        edge = max(np.linalg.norm(B - A), np.linalg.norm(C - A), np.linalg.norm(C - B))
        n = max(1, int(np.ceil(edge / spacing)))
        i, j = np.meshgrid(np.arange(n + 1), np.arange(n + 1), indexing="ij")
        keep = i + j <= n
        u = i[keep] / n
        v = j[keep] / n
        bar = np.stack([1 - u - v, u, v], 1)
        out_tri.append(np.full(len(bar), ti))
        out_bar.append(bar)
    tri = np.concatenate(out_tri)
    bar = np.concatenate(out_bar)
    pts = np.einsum("nk,nkc->nc", bar, pos[tris[tri]])
    return pts, tri, bar


def bilinear(img, uv):
    """img: (H,W,C) float, rows top->bottom; uv in [0,1] with v up."""
    H, W = img.shape[:2]
    x = uv[:, 0] * W - 0.5
    y = (1 - uv[:, 1]) * H - 0.5
    return np.stack([ndimage.map_coordinates(img[..., c], [y, x], order=1, mode="nearest") for c in range(img.shape[2])], 1)


def decode_dxt5nm(img):
    """Unity DXT5nm-style normal map export: x in alpha, y in green."""
    x = img[..., 3] * 2 - 1
    y = img[..., 1] * 2 - 1
    z = np.sqrt(np.clip(1 - x * x - y * y, 0, 1))
    return np.stack([x, y, z], -1)


def unity_bitangent(n, t, w=-1.0):
    return np.cross(n, t) * w


def bake(otter_px, beaver, beaver_maps, spacing=0.0015, hires=None, detail_strength=1.5):
    """otter_px: dict with P (Nx3), N (Nx3), T (Nx3) for the covered texels.
    beaver: dict pos, nrm, tan(4), tris, uv0.  beaver_maps: dict normal (H,W,4 in 0..1), ao (H,W,1), albedo (H,W,3).
    Returns dict: normal_ts (Nx3, otter tangent space), ao (N), detail (N) and dist (N, distance to beaver surface)."""
    pts, tri, bar = surface_samples(beaver["pos"], beaver["tris"], spacing)
    kd = cKDTree(pts)
    dist, idx = kd.query(otter_px["P"], workers=-1)
    t_ids = beaver["tris"][tri[idx]]
    b = bar[idx]
    uv = np.einsum("nk,nkc->nc", b, beaver["uv0"][t_ids])
    nb = np.einsum("nk,nkc->nc", b, beaver["nrm"][t_ids]); nb /= np.linalg.norm(nb, axis=1, keepdims=True)
    tb = np.einsum("nk,nkc->nc", b, beaver["tan"][t_ids][..., :3])
    tb -= nb * np.sum(tb * nb, 1, keepdims=True); tb /= np.linalg.norm(tb, axis=1, keepdims=True)
    bb = unity_bitangent(nb, tb)

    ts = decode_dxt5nm(bilinear(beaver_maps["normal"], uv))
    No, To = otter_px["N"], otter_px["T"]
    # smooth shape normal from the high-resolution sculpt (hides low-poly facets)
    if hires is not None:
        hv, hn = hires
        hk = cKDTree(hv)
        dd, ii = hk.query(otter_px["P"], k=4, workers=-1)
        ww = 1.0 / np.maximum(dd, 1e-6)
        shape = np.einsum("nk,nkc->nc", ww, hn[ii])
        shape /= np.linalg.norm(shape, axis=1, keepdims=True)
    else:
        shape = No
    # beaver fur detail: its tangential tilt in object space, laid onto the otter's shape normal
    tilt = (tb * ts[:, :1] + bb * ts[:, 1:2]) * detail_strength
    tilt -= shape * np.sum(tilt * shape, 1, keepdims=True)
    world = shape * np.maximum(ts[:, 2:3], 0.3) + tilt
    world /= np.linalg.norm(world, axis=1, keepdims=True)

    Bo = unity_bitangent(No, To)
    out = np.stack([np.sum(world * To, 1), np.sum(world * Bo, 1), np.sum(world * No, 1)], 1)
    out[:, 2] = np.maximum(out[:, 2], 0.2)
    out /= np.linalg.norm(out, axis=1, keepdims=True)

    ao = bilinear(beaver_maps["ao"], uv)[:, 0]
    alb = beaver_maps["albedo"]
    lum = alb.mean(2, keepdims=True)
    hp = lum / np.maximum(ndimage.gaussian_filter(lum, (6, 6, 0)), 1e-3)
    detail = bilinear(hp, uv)[:, 0]
    sh = np.stack([np.sum(shape * To, 1), np.sum(shape * Bo, 1), np.sum(shape * No, 1)], 1)
    return dict(normal_ts=out, shape_ts=sh, ao=ao, detail=np.clip(detail, 0.6, 1.4), dist=dist, uv=uv)


def load_maps(normal_png, ao_png, albedo_png):
    n = np.asarray(Image.open(normal_png).convert("RGBA"), np.float32) / 255
    a = np.asarray(Image.open(ao_png).convert("L"), np.float32)[..., None] / 255
    c = np.asarray(Image.open(albedo_png).convert("RGB"), np.float32) / 255
    return dict(normal=n, ao=a, albedo=c)


def procedural_fur_normal(height, strength):
    """Tangent-space normal from a height field in rasterizer space (row index grows with v, column with u)."""
    gy, gx = np.gradient(height)
    nx = -gx * strength
    ny = -gy * strength
    n = np.stack([nx, ny, np.ones_like(nx)], -1)
    return n / np.linalg.norm(n, axis=-1, keepdims=True)
