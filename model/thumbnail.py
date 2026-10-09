"""Workshop thumbnail from the 3D otters. usage: thumbnail.py adult.npz adult_tex child.npz child_tex out.png"""
import sys
sys.path.insert(0, ".")
import bpy
import numpy as np
from mathutils import Vector
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import blend_util as bu
import tempfile
TMP = tempfile.gettempdir()

a_npz, a_tex, c_npz, c_tex, out = sys.argv[1:6]
bu.reset_scene()


def add(npz, tex, loc, rot_z):
    o = np.load(npz)
    ob = bu.mesh_from_unity("O", o["pos"], o["tris"], uvs={"uv0": o["uv0"]})
    pre = tex.rsplit("/", 1)[0] + "/" + ("OtterAdult" if "Adult" in tex else "OtterChild")
    ob.data.materials.append(bu.full_material("m" + tex[-6:], tex, "uv0", ao=pre + "AO.png", gloss=pre + "Gloss.png",
                                              normal_ts=pre + "NormalTS_blender_preview.png"))
    ob.location = loc
    ob.rotation_euler = (0, 0, rot_z)
    return ob


add(a_npz, a_tex, (0.0, 0.0, 0.0), 0.35)
add(c_npz, c_tex, (0.36, 0.12, 0.0), -0.1)
# grassy bank and a strip of river
bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, 0))
bpy.context.active_object.data.materials.append(bu.color_material("grass", (0.38, 0.52, 0.24), 0.95))
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -2.2, 0.004))
w = bpy.context.active_object
w.scale = (8, 3.2, 1)
w.data.materials.append(bu.color_material("water", (0.16, 0.42, 0.55), 0.15))
bu.setup_render((1920, 1080))
cam = bu.camera("c", (1.15, 1.5, 0.55), (0.05, 0.0, 0.24), lens=42)
p = f"{TMP}/_thumb.png"
bu.render(cam, p)

im = Image.open(p).convert("RGB").resize((960, 540), Image.LANCZOS)
d = ImageDraw.Draw(im)
font_paths = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"]
font = sub = None
for fp in font_paths:
    try:
        font = ImageFont.truetype(fp, 92)
        sub = ImageFont.truetype(fp, 30)
        break
    except OSError:
        pass
font = font or ImageFont.load_default()
sub = sub or ImageFont.load_default()
d.text((48, 40), "OTTERS", font=font, fill=(255, 246, 227), stroke_width=6, stroke_fill=(43, 28, 18))
d.text((52, 145), "A water faction for Timberborn", font=sub, fill=(255, 246, 227), stroke_width=3, stroke_fill=(43, 28, 18))
im.save(out, optimize=True)
