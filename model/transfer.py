"""Transfer the beaver's baked vertex animations onto the otter mesh.

Game convention (AnimateVAT.hlsl): per frame and vertex, `offset` is added to the rest position and `rotation`
is an absolute quaternion with normal = q*(-1,0,0) and tangent = q*(0,0,-1).

Each otter vertex is bound to beaver vertices around its closest point on the beaver surface (Gaussian weights
over a 2-ring neighbourhood). For every frame the otter vertex follows the weighted blend of those beaver
vertices' rigid motions (translation + rotation relative to rest), and its frame rotation is the blended
relative rotation applied to its own rest orientation.
"""
import numpy as np
import trimesh

import beaver_data as bd


# ---------------------------------------------------------------- quaternion helpers (x, y, z, w)
def qmul(a, b):
    ax, ay, az, aw = np.moveaxis(a, -1, 0)
    bx, by, bz, bw = np.moveaxis(b, -1, 0)
    return np.stack([aw * bx + ax * bw + ay * bz - az * by,
                     aw * by - ax * bz + ay * bw + az * bx,
                     aw * bz + ax * by - ay * bx + az * bw,
                     aw * bw - ax * bx - ay * by - az * bz], -1)


def qconj(q):
    return q * np.array([-1, -1, -1, 1.0])


def qrot(q, v):
    t = 2.0 * np.cross(q[..., :3], v)
    return v + q[..., 3:4] * t + np.cross(q[..., :3], t)


def mat_to_quat(M):
    """M: (...,3,3) rotation matrices (columns = images of the basis vectors)."""
    m00, m11, m22 = M[..., 0, 0], M[..., 1, 1], M[..., 2, 2]
    tr = m00 + m11 + m22
    q = np.zeros(M.shape[:-2] + (4,))
    w = np.sqrt(np.maximum(0, 1 + tr)) / 2
    x = np.sqrt(np.maximum(0, 1 + m00 - m11 - m22)) / 2
    y = np.sqrt(np.maximum(0, 1 - m00 + m11 - m22)) / 2
    z = np.sqrt(np.maximum(0, 1 - m00 - m11 + m22)) / 2
    x = np.copysign(x, M[..., 2, 1] - M[..., 1, 2])
    y = np.copysign(y, M[..., 0, 2] - M[..., 2, 0])
    z = np.copysign(z, M[..., 1, 0] - M[..., 0, 1])
    q[..., 0], q[..., 1], q[..., 2], q[..., 3] = x, y, z, w
    return q / np.linalg.norm(q, axis=-1, keepdims=True)


def frame_quat(n, t):
    """Quaternion q with q*(-1,0,0) = n and q*(0,0,-1) = t (t made orthogonal to n)."""
    n = n / np.linalg.norm(n, axis=-1, keepdims=True)
    t = t - n * np.sum(t * n, -1, keepdims=True)
    t = t / np.linalg.norm(t, axis=-1, keepdims=True)
    ex, ez = -n, -t
    ey = np.cross(ez, ex)
    M = np.stack([ex, ey, ez], -1)
    return mat_to_quat(M)


# ---------------------------------------------------------------- binding
def bind(beaver, otter_pos, sigma, rings=2):
    pos, tris = beaver["pos"], beaver["tris"]
    merged = trimesh.Trimesh(pos, tris, process=True)  # merges split vertices
    # map merged vertex -> one original index
    from scipy.spatial import cKDTree
    kd = cKDTree(pos)
    _, rep = kd.query(merged.vertices)
    body = max(merged.split(only_watertight=False), key=lambda b: len(b.vertices))
    body_mask = np.zeros(len(merged.vertices), bool)
    _, body_idx = cKDTree(merged.vertices).query(body.vertices)
    body_mask[body_idx] = True
    faces = merged.faces[body_mask[merged.faces].all(1)]
    surf = trimesh.Trimesh(merged.vertices, faces, process=False)
    closest, dist, tri_id = trimesh.proximity.closest_point(surf, otter_pos)

    nbr = [set() for _ in range(len(merged.vertices))]
    for a, b, c in faces:
        nbr[a].update((b, c)); nbr[b].update((a, c)); nbr[c].update((a, b))

    cand_lists = []
    for t in tri_id:
        s = set(faces[t])
        frontier = set(s)
        for _ in range(rings):
            nxt = set()
            for v in frontier:
                nxt |= nbr[v]
            frontier = nxt - s
            s |= nxt
        cand_lists.append(sorted(s))
    K = max(len(c) for c in cand_lists)
    idx = np.zeros((len(otter_pos), K), np.int64)
    w = np.zeros((len(otter_pos), K))
    mv = np.asarray(merged.vertices)
    for i, c in enumerate(cand_lists):
        c = np.array(c)
        dd = np.linalg.norm(mv[c] - closest[i], axis=1)
        ww = np.exp(-(dd / sigma) ** 2)
        ww /= ww.sum()
        idx[i, :len(c)] = rep[c]
        w[i, :len(c)] = ww
    return idx, w, dist


def otter_rest_quats(otter):
    return frame_quat(otter["nrm"], otter["tan"])


def transfer_animation(anim, beaver, otter, idx, w, q_rest_otter, q_rest_beaver, chunk=24):
    offs, rots = bd.frames(anim)  # (F,Nb,3), (F,Nb,4)
    outs = [_transfer_frames(offs[i:i + chunk], rots[i:i + chunk], beaver, otter, idx, w, q_rest_otter, q_rest_beaver)
            for i in range(0, offs.shape[0], chunk)]
    return np.concatenate([a for a, _ in outs]), np.concatenate([b for _, b in outs])


def _transfer_frames(offs, rots, beaver, otter, idx, w, q_rest_otter, q_rest_beaver):
    F = offs.shape[0]
    rest_b = beaver["pos"]
    Pf = rest_b[None] + offs                                  # (F,Nb,3)
    Rrel = qmul(rots, qconj(q_rest_beaver)[None])             # (F,Nb,4)
    vo = otter["pos"]
    local = vo[:, None, :] - rest_b[idx]                      # (No,K,3)
    Rk = Rrel[:, idx]                                         # (F,No,K,4)
    moved = Pf[:, idx] + qrot(Rk, np.broadcast_to(local, Rk.shape[:-1] + (3,)))  # (F,No,K,3)
    newpos = np.einsum("fnkc,nk->fnc", moved, w)
    # blend relative rotations (align hemispheres with the heaviest candidate)
    ref = Rk[:, np.arange(len(vo)), np.argmax(w, 1)]          # (F,No,4)
    sign = np.sign(np.sum(Rk * ref[:, :, None, :], -1))
    sign[sign == 0] = 1
    qb = np.einsum("fnkc,nk->fnc", Rk * sign[..., None], w)
    qb /= np.linalg.norm(qb, axis=-1, keepdims=True)
    qout = qmul(qb, q_rest_otter[None])
    return (newpos - vo[None]).astype(np.float32), qout.astype(np.float32)
