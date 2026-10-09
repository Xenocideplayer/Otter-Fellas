"""Full otter model pipeline. usage: python3 build_models.py <beaver_extract_dir> <out_dir>

Produces in out_dir:
  OtterAdult.Model.timbermesh, OtterChild.Model.timbermesh
  textures/OtterAdult1..4.png, textures/OtterChild1..3.png (+ contaminated preview textures for portraits)
  portraits/*.png, otter_adult.blend, otter_child.blend, otter_*.npz
"""
import os
import tempfile
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import landmarks
import meshutil
import paint

TMP = tempfile.gettempdir()
src, out = sys.argv[1], sys.argv[2]
textures_only = "--textures-only" in sys.argv
here = os.path.dirname(os.path.abspath(__file__))
os.makedirs(f"{out}/textures", exist_ok=True)
os.makedirs(f"{out}/portraits", exist_ok=True)


def find(name):
    for d in (src, os.path.join(src, "ref")):
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    raise FileNotFoundError(name)


def run(*args):
    subprocess.run([sys.executable, *args], cwd=here, check=True)


import trimesh
import beaver_data as bd
import bake_detail as bk

CONFIG = [  # which, beaver, target tris, texture size, binding sigma, beaver normal, beaver AO, beaver albedo
    ("adult", "BeaverAdult", 2300, 2048, 0.03, "Adult_Normal_2K.png", "Adult_AO_2K.png", "BeaverAdult1.Folktails.png"),
    ("child", "BeaverChild", 1900, 1024, 0.02, "Chilkd_Normal_1K.png", "Child_AO_1K.png", "BeaverChild1.Folktails.png"),
]
for which, beaver, tris, size, sigma, bn, bao, balb in CONFIG:
    raw = f"{TMP}/otter_{which}_raw.npz"
    name = "OtterAdult" if which == "adult" else "OtterChild"
    if not textures_only or not os.path.exists(raw):
        run("make_shape.py", which, os.path.abspath(src))
    if not textures_only:
        run("finish_mesh.py", raw, f"{out}/otter_{which}", str(tris))
    o = dict(np.load(f"{out}/otter_{which}.npz"))
    o["nrm"] = meshutil.vertex_normals(o["pos"], o["tris"], o["src_vertex"])
    r = np.load(raw)
    hm = trimesh.Trimesh(r["v"], r["f"], process=True)
    trimesh.smoothing.filter_laplacian(hm, lamb=0.5, iterations=8)
    L = getattr(landmarks, which.upper())
    variants = paint.ADULT_VARIANTS if which == "adult" else paint.CHILD_VARIANTS
    paint.make_textures(o, L, variants + [paint.SICK_VARIANT], size,
                        [f"{out}/textures/{name}{i + 1}.png" for i in range(len(variants))] + [f"{out}/textures/{name}Sick.png"],
                        beaver=bd.load(find(f"{beaver}.timbermesh")),
                        beaver_maps=bk.load_maps(find(bn), find(bao), find(balb)),
                        maps_prefix=f"{out}/textures/{name}",
                        hires=(np.asarray(hm.vertices), np.asarray(hm.vertex_normals)))
    if not textures_only:
        run("export_otter.py", find(f"{beaver}.timbermesh"), f"{out}/otter_{which}.npz", f"{out}/{name}.Model.timbermesh", str(sigma))
print("models done")
