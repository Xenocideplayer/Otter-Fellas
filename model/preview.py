"""Quick Workbench renders: otter (npz, Unity space) next to the beaver. usage: preview.py otter.npz beaver.timbermesh out.png [texture.png]"""
import sys
sys.path.insert(0, ".")
import bpy
import numpy as np
import blend_util as bu
import tempfile
TMP = tempfile.gettempdir()
import beaver_data as bd
from PIL import Image

otter, beaver, outpng = sys.argv[1:4]
tex = sys.argv[4] if len(sys.argv) > 4 else None
bu.reset_scene()
o = np.load(otter)
ob = bu.mesh_from_unity("Otter", o["pos"], o["tris"], uvs={"uv0": o["uv0"]})
if tex:
    ob.data.materials.append(bu.image_material("ot", tex, "uv0"))
else:
    ob.data.materials.append(bu.color_material("ot", (0.42, 0.29, 0.2)))
d = bd.load(beaver)
bv = bu.mesh_from_unity("Beaver", d["pos"], d["tris"])
bv.data.materials.append(bu.color_material("bv", (0.6, 0.6, 0.6)))
bv.location.x = 0.62

sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"
sc.display.shading.light = "STUDIO"
sc.display.shading.color_type = "TEXTURE" if tex else "MATERIAL"
sc.display.shading.show_cavity = True
sc.render.resolution_x = sc.render.resolution_y = 600
sc.display.render_aa = "8"
H = float(o["pos"][:, 1].max())
c = (0.31, -0.15, H * 0.5)
views = {"front": (0.31, 2.2, H * 0.55), "side": (2.6, -0.15, H * 0.55), "persp": (1.7, 1.5, 1.0), "back": (0.31, -2.6, H * 0.7)}
paths = []
for k, loc in views.items():
    cam = bu.camera(k, loc, c, ortho_scale=1.3)
    p = f"{TMP}/_pv_{k}.png"
    bu.render(cam, p)
    paths.append(p)
ims = [Image.open(p) for p in paths]
W = Image.new("RGB", (600 * len(ims), 600), "white")
for i, im in enumerate(ims):
    W.paste(im, (600 * i, 0))
W.save(outpng)
