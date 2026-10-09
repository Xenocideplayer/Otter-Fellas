"""Full otter model pipeline. usage: python3 build_models.py <beaver_extract_dir> <out_dir>

Produces in out_dir:
  OtterAdult.Model.timbermesh, OtterChild.Model.timbermesh
  textures/OtterAdult1..4.png, textures/OtterChild1..3.png (+ contaminated preview textures for portraits)
  portraits/*.png, otter_adult.blend, otter_child.blend, otter_*.npz
"""
import tempfile
TMP = tempfile.gettempdir()
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import landmarks
import meshutil
import paint

src, out = sys.argv[1], sys.argv[2]
here = os.path.dirname(os.path.abspath(__file__))
os.makedirs(f"{out}/textures", exist_ok=True)
os.makedirs(f"{out}/portraits", exist_ok=True)
SICK = [((0.30, 0.31, 0.2), (0.45, 0.46, 0.32))]


def run(*args):
    subprocess.run([sys.executable, *args], cwd=here, check=True)


for which, beaver, tris, size, sigma in [("adult", "BeaverAdult", 2300, 2048, 0.03),
                                         ("child", "BeaverChild", 1900, 1024, 0.02)]:
    raw = f"{TMP}/otter_{which}_raw.npz"
    run("make_shape.py", which, os.path.abspath(src))
    run("finish_mesh.py", raw, f"{out}/otter_{which}", str(tris))
    o = dict(np.load(f"{out}/otter_{which}.npz"))
    o["nrm"] = meshutil.vertex_normals(o["pos"], o["tris"], o["src_vertex"])
    L = getattr(landmarks, which.upper())
    variants = paint.ADULT_VARIANTS if which == "adult" else paint.CHILD_VARIANTS
    name = "OtterAdult" if which == "adult" else "OtterChild"
    paint.make_textures(o, L, variants + SICK, size,
                        [f"{out}/textures/{name}{i + 1}.png" for i in range(len(variants))] + [f"{out}/textures/{name}Sick.png"])
    run("export_otter.py", f"{src}/{beaver}.timbermesh", f"{out}/otter_{which}.npz", f"{out}/{name}.Model.timbermesh", str(sigma))

run("portraits.py", f"{out}/otter_adult.npz", f"{out}/textures/OtterAdult1.png", f"{out}/textures/OtterAdultSick.png",
    f"{out}/otter_child.npz", f"{out}/textures/OtterChild1.png", f"{out}/textures/OtterChildSick.png", f"{out}/portraits")
print("done")
