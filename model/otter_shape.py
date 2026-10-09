"""Build the otter body as a signed distance field derived from the beaver's volume, then mesh it.

Everything here is in Unity space (Y up, +Z = where the character faces). Units are metres; a beaver is ~0.53 tall.
The beaver volume keeps arms/legs/head where the beaver animations expect them; on top of that we:
  * cut away the flat paddle tail and add a long round tapering otter tail,
  * slim the torso and belly, slightly widen and flatten the head,
  * add whisker pads, a button nose and small round ears, drop the buck teeth.
"""
import numpy as np
import trimesh
from scipy import ndimage
from skimage import measure

VOXEL = 0.004


# ------------------------------------------------------------------ SDF primitives
def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return b * (1 - h) + a * h - k * h * (1 - h)


def smax(a, b, k):
    return -smin(-a, -b, k)


def sphere(P, c, r):
    return np.linalg.norm(P - np.asarray(c), axis=-1) - r


def ellipsoid(P, c, radii):
    q = (P - np.asarray(c)) / np.asarray(radii)
    k0 = np.linalg.norm(q, axis=-1)
    k1 = np.linalg.norm(q / np.asarray(radii), axis=-1)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)


def capsule_chain(P, pts, radii):
    """Union of tapered capsules along a polyline (round cone segments)."""
    d = np.full(P.shape[:-1], 1e9)
    for (a, b, ra, rb) in zip(pts[:-1], pts[1:], radii[:-1], radii[1:]):
        a = np.asarray(a); b = np.asarray(b)
        ba = b - a
        t = np.clip(((P - a) @ ba) / (ba @ ba), 0, 1)
        r = ra + (rb - ra) * t
        q = P - (a + t[..., None] * ba)
        d = np.minimum(d, np.linalg.norm(q, axis=-1) - r)
    return d


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


# ------------------------------------------------------------------ beaver volume
def beaver_occupancy(pos, tris, lo, shape):
    """Inside/outside by ray parity along +Z for each (x, y) column of the grid."""
    nx, ny, nz = shape
    xs = lo[0] + (np.arange(nx) + 0.5) * VOXEL
    ys = lo[1] + (np.arange(ny) + 0.5) * VOXEL
    zs = lo[2] + (np.arange(nz) + 0.5) * VOXEL
    occ = np.zeros(shape, dtype=bool)
    A, B, C = pos[tris[:, 0]], pos[tris[:, 1]], pos[tris[:, 2]]
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    px, py = X.ravel(), Y.ravel()
    hits = [[] for _ in range(px.size)]
    for a, b, c in zip(A, B, C):
        minx, maxx = min(a[0], b[0], c[0]), max(a[0], b[0], c[0])
        miny, maxy = min(a[1], b[1], c[1]), max(a[1], b[1], c[1])
        i0, i1 = np.searchsorted(xs, [minx, maxx])
        j0, j1 = np.searchsorted(ys, [miny, maxy])
        if i0 >= i1 or j0 >= j1:
            continue
        ii, jj = np.meshgrid(np.arange(i0, i1), np.arange(j0, j1), indexing="ij")
        qx, qy = xs[ii.ravel()], ys[jj.ravel()]
        det = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(det) < 1e-12:
            continue
        l1 = ((b[1] - c[1]) * (qx - c[0]) + (c[0] - b[0]) * (qy - c[1])) / det
        l2 = ((c[1] - a[1]) * (qx - c[0]) + (a[0] - c[0]) * (qy - c[1])) / det
        l3 = 1 - l1 - l2
        ok = (l1 >= 0) & (l2 >= 0) & (l3 >= 0)
        zhit = l1 * a[2] + l2 * b[2] + l3 * c[2]
        flat = (ii.ravel() * ny + jj.ravel())
        for f, z in zip(flat[ok], zhit[ok]):
            hits[f].append(z)
    for f, hz in enumerate(hits):
        if len(hz) < 2:
            continue
        hz = np.sort(hz)
        i, j = divmod(f, ny)
        for k in range(0, len(hz) - 1, 2):
            k0, k1 = np.searchsorted(zs, [hz[k], hz[k + 1]])
            occ[i, j, k0:k1] = True
    return occ


def occupancy_to_sdf(occ):
    inside = ndimage.distance_transform_edt(occ)
    outside = ndimage.distance_transform_edt(~occ)
    sdf = (outside - inside) * VOXEL
    return ndimage.gaussian_filter(sdf, 1.0)


def sample_grid(grid, lo, P):
    idx = (P - lo) / VOXEL - 0.5
    return ndimage.map_coordinates(grid, [idx[..., 0], idx[..., 1], idx[..., 2]], order=1, mode="nearest")


# ------------------------------------------------------------------ otter
def otter_sdf(P, beaver_grid, lo, params):
    x, y, z = P[..., 0], P[..., 1], P[..., 2]
    ax = np.abs(x)

    # --- warp: narrow torso (x) and flatten belly/chest (front z) without moving the arms
    torso_band = smoothstep(0.03, 0.10, y) * (1 - smoothstep(0.34, 0.42, y))
    core = 1 - smoothstep(0.09, 0.155, ax)
    sx = 1 + params["slim"] * torso_band * core
    belly = torso_band * core * smoothstep(-0.02, 0.06, z)
    sz = 1 + params["belly"] * belly
    # head: a touch wider, a touch lower/flatter
    head_band = smoothstep(0.37, 0.43, y)
    sx = sx * (1 - params["head_widen"] * head_band)
    Q = np.stack([x * sx, y, z * sz], axis=-1)
    d = sample_grid(beaver_grid, lo, Q) + params["erode"]

    F = params["features"]
    # --- remove beaver paddle tail (everything behind the rump, low down)
    rz, ry = F["rump_z"], F["rump_y"]
    rump_cut = -(z - rz) - 0.015 * smoothstep(0.0, ry, y)
    tail_zone = 1 - smoothstep(ry, ry + 0.06, y)
    cut = np.where(tail_zone > 0, rump_cut, -1.0)
    d = smax(d, cut, 0.02)

    # --- flatter otter skull
    if F.get("skull_cap"):
        d = smax(d, y - F["skull_cap"], 0.03)

    # --- thick otter neck blending head into shoulders
    if F.get("neck"):
        c, r = F["neck"]
        d = smin(d, ellipsoid(P, c, r), 0.03)

    # --- otter tail: thick at the base, tapering, resting on the ground, tip lifting a little
    d = smin(d, capsule_chain(P, F["tail_pts"], F["tail_r"]), 0.03)

    # --- face: whisker pads, nose, fuller chin
    c, r = F["whisker"]
    for sgn in (-1, 1):
        d = smin(d, ellipsoid(P, (sgn * c[0], c[1], c[2]), r), 0.012)
    c, r = F["nose"]
    d = smin(d, ellipsoid(P, c, r), 0.008)
    c, r = F["chin"]
    d = smin(d, ellipsoid(P, c, r), 0.015)

    # --- small round ears set low on the sides of the head
    c, r = F["ear"]
    for sgn in (-1, 1):
        d = smin(d, ellipsoid(P, (sgn * c[0], c[1], c[2]), r), 0.01)

    # --- broader, flatter webbed hind feet
    c, r = F["foot"]
    for sgn in (-1, 1):
        d = smin(d, ellipsoid(P, (sgn * c[0], c[1], c[2]), r), 0.012)
    return d


ADULT_FEATURES = dict(
    rump_z=-0.185, rump_y=0.24,
    skull_cap=0.517,
    neck=((0, 0.365, 0.045), (0.088, 0.055, 0.085)),
    tail_pts=[(0, 0.085, -0.15), (0, 0.06, -0.24), (0, 0.035, -0.33), (0, 0.025, -0.42), (0, 0.03, -0.49), (0, 0.045, -0.535)],
    tail_r=[0.064, 0.052, 0.04, 0.029, 0.019, 0.011],
    whisker=((0.033, 0.418, 0.183), (0.036, 0.03, 0.03)),
    nose=((0, 0.441, 0.214), (0.019, 0.014, 0.016)),
    chin=((0, 0.395, 0.16), (0.04, 0.022, 0.035)),
    ear=((0.083, 0.495, 0.035), (0.016, 0.02, 0.012)),
    foot=((0.118, 0.012, -0.03), (0.05, 0.012, 0.07)),
)

ADULT_PARAMS = dict(slim=0.09, belly=0.10, head_widen=0.05, erode=0.0015, features=ADULT_FEATURES)


def build(pos, tris, params=ADULT_PARAMS):
    """pos/tris: beaver main body. Returns (verts, faces) of the otter (Unity space, Unity winding)."""
    pad = 0.04
    lo = pos.min(0) - pad
    hi = pos.max(0) + pad
    shape = tuple(np.ceil((hi - lo) / VOXEL).astype(int))
    occ = beaver_occupancy(pos, tris, lo, shape)
    bgrid = occupancy_to_sdf(occ)

    xs = lo[0] + (np.arange(shape[0]) + 0.5) * VOXEL
    ys = lo[1] + (np.arange(shape[1]) + 0.5) * VOXEL
    zs = lo[2] + (np.arange(shape[2]) + 0.5) * VOXEL
    P = np.stack(np.meshgrid(xs, ys, zs, indexing="ij"), axis=-1)
    d = otter_sdf(P, bgrid, lo, params)
    # flat floor: nothing below y = 0
    d = np.maximum(d, -(P[..., 1] - 0.0005))
    verts, faces, _, _ = measure.marching_cubes(d, 0.0, spacing=(VOXEL,) * 3)
    verts = verts + lo + 0.5 * VOXEL
    m = trimesh.Trimesh(verts, faces, process=True)
    m = max(m.split(only_watertight=False), key=lambda b: len(b.vertices))
    # marching_cubes winding is outward for (x,y,z) right-handed; flip to keep outward normals in our use
    return np.asarray(m.vertices), np.asarray(m.faces)




# ------------------------------------------------------------------ child: map the adult features onto the kit's proportions
def _affine(lo_a, hi_a, lo_c, hi_c):
    lo_a, hi_a, lo_c, hi_c = map(np.asarray, (lo_a, hi_a, lo_c, hi_c))
    s = (hi_c - lo_c) / (hi_a - lo_a)
    return (lambda p: tuple(lo_c + (np.asarray(p) - lo_a) * s)), s


# head boxes and body boxes measured from BeaverAdult / BeaverChild meshes
_head, _hs = _affine((-0.113, 0.38, -0.081), (0.108, 0.53, 0.226), (-0.074, 0.225, -0.051), (0.074, 0.32, 0.127))
_body, _bs = _affine((-0.241, 0.0, -0.557), (0.241, 0.53, 0.226), (-0.134, 0.0, -0.268), (0.134, 0.32, 0.127))


def _hfeat(f, centred=False):
    c, r = f
    c = list(map(float, _head(c)))
    if centred:
        c[0] = 0.0
    return (tuple(c), tuple(float(x) for x in np.asarray(r) * _hs))


def _bfeat(f):
    c, r = f
    return (_body(c), tuple(np.asarray(r) * _bs))


A = ADULT_FEATURES
CHILD_FEATURES = dict(
    rump_z=-0.118, rump_y=0.125,
    skull_cap=0.312,
    neck=_hfeat(A["neck"], True),
    tail_pts=[(0, 0.05, -0.095), (0, 0.037, -0.145), (0, 0.024, -0.19), (0, 0.018, -0.228), (0, 0.021, -0.252), (0, 0.03, -0.264)],
    tail_r=[0.04, 0.032, 0.025, 0.018, 0.012, 0.007],
    whisker=_hfeat(A["whisker"]),
    nose=_hfeat(A["nose"], True),
    chin=_hfeat(A["chin"], True),
    ear=((0.048, 0.305, 0.03), (0.011, 0.013, 0.008)),
    foot=((0.066, 0.008, -0.025), (0.03, 0.008, 0.042)),
)
CHILD_PARAMS = dict(slim=0.07, belly=0.08, head_widen=0.04, erode=0.001, features=CHILD_FEATURES)
