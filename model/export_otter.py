"""Write an otter .timbermesh: otter body + every beaver animation transferred, beaver attachment nodes kept.

usage: python3 export_otter.py beaver.timbermesh otter.npz out.timbermesh sigma
"""
import sys
import time

import numpy as np
import trimesh

import beaver_data as bd
import meshutil
import timbermesh as tm
import transfer as tr


def half(a):
    # the game converts animation data to half floats on load; rounding here loses nothing and compresses far better
    return np.asarray(a, np.float32).astype(np.float16).astype(np.float32)


def transfer_uv1(beaver, otter_pos):
    """UV1 drives worker outfits / tail decals / contamination overlays: copy it from the closest beaver surface."""
    body = trimesh.Trimesh(beaver["pos"], beaver["tris"], process=False)
    closest, _, tri = trimesh.proximity.closest_point(body, otter_pos)
    t = beaver["tris"][tri]
    a, b, c = (beaver["pos"][t[:, k]] for k in range(3))
    v0, v1, v2 = b - a, c - a, closest - a
    d00 = np.sum(v0 * v0, 1); d01 = np.sum(v0 * v1, 1); d11 = np.sum(v1 * v1, 1)
    d20 = np.sum(v2 * v0, 1); d21 = np.sum(v2 * v1, 1)
    den = np.where(np.abs(d00 * d11 - d01 * d01) < 1e-18, 1e-18, d00 * d11 - d01 * d01)
    l1 = (d11 * d20 - d01 * d21) / den
    l2 = (d00 * d21 - d01 * d20) / den
    l0 = 1 - l1 - l2
    uv = beaver["uv1"]
    return l0[:, None] * uv[t[:, 0]] + l1[:, None] * uv[t[:, 1]] + l2[:, None] * uv[t[:, 2]]


def build(beaver_path, otter_npz, out_path, sigma):
    t0 = time.time()
    d = bd.load(beaver_path)
    o = dict(np.load(otter_npz))
    o["nrm"] = meshutil.vertex_normals(o["pos"], o["tris"], o["src_vertex"])
    o["tan"] = meshutil.tangents(o["pos"], o["uv0"], o["tris"], o["nrm"])
    n = len(o["pos"])
    idx, w, _ = tr.bind(d, o["pos"], sigma)
    q_otter = tr.otter_rest_quats(o)
    q_beaver = tr.frame_quat(d["nrm"], d["tan"][:, :3])
    uv1 = transfer_uv1(d, o["pos"])

    src = d["node"]
    node = tm.Node(src.parent, src.name, src.position, src.rotation, src.scale)
    node.vertex_count = n
    tan4 = np.concatenate([o["tan"], -np.ones((n, 1))], 1)  # beaver meshes use w = -1 throughout
    node.vertex_properties = [
        tm.VertexProperty.from_array("position", o["pos"]),
        tm.VertexProperty.from_array("normal", o["nrm"]),
        tm.VertexProperty.from_array("tangent", tan4),
        tm.VertexProperty.from_array("color", np.ones((n, 4))),
        tm.VertexProperty.from_array("uv0", o["uv0"]),
        tm.VertexProperty.from_array("uv1", uv1),
    ]
    node.meshes = [tm.MeshPart(o["tris"].reshape(-1), d["material"])]
    for anim in src.vertex_animations:
        off, rot = tr.transfer_animation(anim, d, o, idx, w, q_otter, q_beaver)
        frames = [[tm.VertexProperty.from_array("offset", half(off[f])),
                   tm.VertexProperty.from_array("rotation", half(rot[f]))] for f in range(off.shape[0])]
        node.vertex_animations.append(tm.VertexAnimation(anim.name, anim.framerate, n, frames))
    nodes = [node if nd is src else nd for nd in d["model"].nodes]
    model = tm.Model(d["model"].version, d["model"].name, nodes)
    tm.write(model, out_path)
    print(f"wrote {out_path}: {n} verts, {len(o['tris'])} tris, {len(node.vertex_animations)} animations, {time.time() - t0:.1f}s")
    return model


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]))
