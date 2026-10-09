"""Pull the animated body node out of a beaver timbermesh as numpy arrays (Unity space)."""
import numpy as np

import timbermesh as tm


def body_node(model):
    for n in model.nodes:
        if n.vertex_count > 0:
            return n
    raise ValueError("no mesh node")


def load(path):
    model = tm.read(path)
    node = body_node(model)
    d = {
        "model": model,
        "node": node,
        "pos": node.prop("position").array().astype(np.float64),
        "nrm": node.prop("normal").array().astype(np.float64),
        "tan": node.prop("tangent").array().astype(np.float64),
        "col": node.prop("color").array().astype(np.float64),
        "uv0": node.prop("uv0").array().astype(np.float64),
        "uv1": node.prop("uv1").array().astype(np.float64),
        "tris": np.concatenate([m.indices for m in node.meshes]).reshape(-1, 3),
        "material": node.meshes[0].material,
    }
    return d


def frames(anim):
    """Returns offsets (F,N,3) and rotations (F,N,4) for one vertex animation."""
    offs, rots = [], []
    for fr in anim.frames:
        props = {p.name: p for p in fr}
        offs.append(props["offset"].array())
        rots.append(props["rotation"].array())
    return np.asarray(offs, dtype=np.float64), np.asarray(rots, dtype=np.float64)
