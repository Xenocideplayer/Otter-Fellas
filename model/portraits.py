"""Render faction portraits from the otter models (EEVEE, transparent background).

usage: portraits.py adult.npz adult_tex.png adult_sick_tex.png child.npz child_tex.png child_sick_tex.png outdir
Writes OttersAdult.png, OttersChild.png, OttersContaminatedAdult.png, OttersContaminatedChild.png (128x128)
and OttersFullNewGame.png (420x560).
"""
import sys
sys.path.insert(0, ".")
import bpy
import numpy as np
from mathutils import Vector
from PIL import Image
import blend_util as bu
import tempfile
TMP = tempfile.gettempdir()

a_npz, a_tex, a_sick, c_npz, c_tex, c_sick, outdir = sys.argv[1:8]


def scene_with(npz, tex):
    bu.reset_scene()
    o = np.load(npz)
    ob = bu.mesh_from_unity("Otter", o["pos"], o["tris"], uvs={"uv0": o["uv0"]})
    ob.data.materials.append(bu.image_material("ot", tex, "uv0"))
    bu.setup_render((512, 512), transparent=True)
    sc = bpy.context.scene
    sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.7
    fill = bpy.data.lights.new("Fill", "AREA")
    fill.energy = 4
    fo = bpy.data.objects.new("Fill", fill)
    fo.location = (0.0, 1.2, 0.6)
    fo.rotation_euler = (Vector((0, -1.2, -0.3))).to_track_quat("-Z", "Y").to_euler()
    sc.collection.objects.link(fo)
    return o


def portrait(npz, tex, out, head_y, s):
    scene_with(npz, tex)
    target = (0.0, 0.09 * s, head_y - 0.02 * s)
    cam = bu.camera("c", (0.24 * s, 0.95 * s, head_y + 0.05 * s), target, lens=85)
    p = f"{TMP}/_portrait.png"
    bu.render(cam, p)
    Image.open(p).convert("RGBA").resize((128, 128), Image.LANCZOS).save(out)


def full(npz, tex, out):
    scene_with(npz, tex)
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = 840, 1120
    cam = bu.camera("c", (0.55, 1.15, 0.42), (0.0, -0.08, 0.27), lens=55)
    p = f"{TMP}/_full.png"
    bu.render(cam, p)
    Image.open(p).convert("RGBA").resize((420, 560), Image.LANCZOS).save(out)


portrait(a_npz, a_tex, f"{outdir}/OttersAdult.png", 0.44, 1.0)
portrait(a_npz, a_sick, f"{outdir}/OttersContaminatedAdult.png", 0.44, 1.0)
portrait(c_npz, c_tex, f"{outdir}/OttersChild.png", 0.262, 0.62)
portrait(c_npz, c_sick, f"{outdir}/OttersContaminatedChild.png", 0.262, 0.62)
full(a_npz, a_tex, f"{outdir}/OttersFullNewGame.png")
