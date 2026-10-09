"""Faction art from the 3D otters, finished to sit next to the game's painted art.

usage: art3d.py <model_out dir> <out dir>
Writes OttersAdult.png, OttersChild.png, OttersContaminatedAdult.png, OttersContaminatedChild.png (512x512 painted
portraits on a dark brushed frame, like the vanilla ones) and OttersFullNewGame.png (420x560 full figure, transparent).
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import numpy as np
from mathutils import Vector
from PIL import Image, ImageFilter
from scipy import ndimage

import blend_util as bu
import timbermesh as tm

M, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
TMP = tempfile.gettempdir()


def posed(which, anim, frame):
    o = np.load(f"{M}/otter_{which}.npz")
    name = "OtterAdult" if which == "adult" else "OtterChild"
    model = tm.read(f"{M}/{name}.Model.timbermesh")
    node = [n for n in model.nodes if n.vertex_count][0]
    a = [x for x in node.vertex_animations if x.name == anim][0]
    fr = {p.name: p for p in a.frames[frame]}
    return o, o["pos"] + fr["offset"].array(), name


def scene(o, P, tex, name, res, key=3.4):
    bu.reset_scene()
    ob = bu.mesh_from_unity("Otter", P, o["tris"], uvs={"uv0": o["uv0"]})
    t = f"{M}/textures/{name}"
    ob.data.materials.append(bu.full_material("m", tex, "uv0", ao=t + "AO.png", gloss=t + "Gloss.png",
                                              normal_ts=t + "NormalTS_blender_preview.png"))

    bu.setup_render(res, transparent=True)
    sc = bpy.context.scene
    sc.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.55, 0.62, 0.66, 1)
    sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.55
    sun = [x for x in bpy.data.lights if x.type == "SUN"][0]
    sun.energy, sun.color = key * 1.15, (1.0, 0.88, 0.72)
    so = [x for x in bpy.data.objects if x.type == "LIGHT"][0]
    so.rotation_euler = (0.6, 0.25, 0.35)
    rim = bpy.data.lights.new("rim", "AREA")
    rim.energy, rim.size, rim.color = 30, 0.8, (0.75, 0.9, 1.0)
    ro = bpy.data.objects.new("rim", rim)
    ro.location = (-0.7, -0.8, 0.9)
    ro.rotation_euler = (Vector((0, 0, 0.3)) - ro.location).to_track_quat("-Z", "Y").to_euler()
    sc.collection.objects.link(ro)
    return sc


def kuwahara(img, r):
    """Simple Kuwahara filter: an oil-paint look that keeps edges."""
    a = img.astype(np.float32)
    lum = a[..., :3].mean(-1)
    k = r + 1
    mc = np.stack([ndimage.uniform_filter(a[..., c], k) for c in range(a.shape[2])], -1)
    l1 = ndimage.uniform_filter(lum, k)
    l2 = ndimage.uniform_filter(lum * lum, k)
    var = l2 - l1 * l1
    h = r // 2 + 1
    means, varis = [], []
    for sy in (h, -h):
        for sx in (h, -h):
            means.append(np.roll(mc, (sy, sx), (0, 1)))
            varis.append(np.roll(var, (sy, sx), (0, 1)))
    idx = np.argmin(np.stack(varis), 0)
    out = np.zeros_like(a)
    for i, m in enumerate(means):
        out[idx == i] = m[idx == i]
    return out


def paint_finish(path, size, r=3):
    im = Image.open(path).convert("RGBA")
    a = np.asarray(im).astype(np.float32)
    rgb = kuwahara(a[..., :3], r)
    # painted brush texture: short directional strokes modulating the value a little
    rng = np.random.default_rng(11)
    strokes = ndimage.gaussian_filter(rng.random(rgb.shape[:2]), (1.0, 3.5)) - 0.5
    strokes += ndimage.gaussian_filter(rng.random(rgb.shape[:2]), (3.5, 1.0)) - 0.5
    rgb = rgb * (1 + 0.3 * strokes[..., None])
    # gentle colour grade towards the game's warm painted palette, a touch more contrast
    rgb = np.clip((rgb - 128) * 1.08 + 128 + np.array([6, 2, -6]), 0, 255)
    out = np.dstack([rgb, a[..., 3]]).astype(np.uint8)
    img = Image.fromarray(out, "RGBA").resize(size, Image.LANCZOS)
    return img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=60, threshold=2))


def brushed_frame(size, seed=3):
    """Dark teal painted background with a rough black border, like the vanilla portraits."""
    rng = np.random.default_rng(seed)
    w, h = size
    y, x = np.mgrid[0:h, 0:w] / max(w, h)
    base = np.array([0.10, 0.20, 0.21]) * (1.15 - 0.6 * np.hypot(x - 0.45, y - 0.4))[..., None]
    noise = ndimage.gaussian_filter(rng.random((h, w)), (1.2, 9)) - 0.5      # horizontal brush strokes
    noise2 = ndimage.gaussian_filter(rng.random((h, w)), (7, 1.5)) - 0.5
    col = base * (1 + 1.6 * noise[..., None] + 0.8 * noise2[..., None])
    edge = np.minimum.reduce([x, y, 1 - x, 1 - y]) * max(w, h)
    rough = (ndimage.gaussian_filter(rng.random((h, w)), (2, 12)) + ndimage.gaussian_filter(rng.random((h, w)), (12, 2))) * 45
    border = np.clip((edge + rough - 52) / 6, 0, 1)
    col = col * border[..., None] + np.array([0.02, 0.025, 0.025]) * (1 - border[..., None])
    return Image.fromarray((np.clip(col, 0, 1) * 255).astype(np.uint8), "RGB").convert("RGBA"), border


def portrait(which, tex_name, out_name):
    o, P, name = posed(which, "BeaverAdult_idle" if which == "adult" else "BeaverChild_idle", 20)
    s = 1.0 if which == "adult" else 0.62
    sc = scene(o, P, f"{M}/textures/{tex_name}.png", name, (1024, 1024))
    head = P[:, 1].max()
    nose = P[np.argmax(P[:, 2] + (P[:, 1] > head - 0.12 * s) * 10)]
    target = (float(nose[0]) * 0.6, float(nose[2]) - 0.05 * s, float(head) - 0.07 * s)
    cam = bu.camera("c", (target[0] + 0.03 * s, target[1] + 0.30 * s, target[2] + 0.015 * s), target, lens=52)
    p = f"{TMP}/_art_{out_name}.png"
    bu.render(cam, p)
    fig = paint_finish(p, (512, 512), r=4)
    bg, border = brushed_frame((512, 512), seed=hash(out_name) % 1000)
    bg.alpha_composite(fig)
    # the ragged dark border goes over the figure too
    arr = np.asarray(bg).astype(np.float32)
    arr[..., :3] = arr[..., :3] * border[..., None] + np.array([5, 6, 6]) * (1 - border[..., None])
    Image.fromarray(arr.astype(np.uint8), "RGBA").save(f"{OUT}/{out_name}.png")


def full_figure():
    o, P, name = posed("adult", "BeaverAdult_idle", 20)
    sc = scene(o, P, f"{M}/textures/OtterAdult1.png", name, (840, 1120), key=3.6)
    cam = bu.camera("c", (0.55, 0.95, 0.30), (-0.03, -0.12, 0.25), lens=50)
    p = f"{TMP}/_art_full.png"
    bu.render(cam, p)
    img = paint_finish(p, (420, 560), r=3)
    a = np.asarray(img).astype(np.float32)
    rng = np.random.default_rng(7)
    fuzz = ndimage.gaussian_filter(rng.random(a.shape[:2]), (2.5, 0.7))
    alpha = a[..., 3] / 255
    soft = ndimage.gaussian_filter(alpha, 1.2)
    edge = (soft > 0.05) & (soft < 0.95)
    alpha[edge] = np.clip(soft[edge] + (fuzz[edge] - 0.5) * 0.9, 0, 1)
    a[..., 3] = alpha * 255
    Image.fromarray(a.astype(np.uint8), "RGBA").save(f"{OUT}/OttersFullNewGame.png")


portrait("adult", "OtterAdult1", "OttersAdult")
portrait("adult", "OtterAdultSick", "OttersContaminatedAdult")
portrait("child", "OtterChild1", "OttersChild")
portrait("child", "OtterChildSick", "OttersContaminatedChild")
full_figure()
print("art done")
