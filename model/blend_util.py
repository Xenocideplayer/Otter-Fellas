"""Helpers for moving meshes between Timberborn (Unity, left-handed, Y up, +Z forward) and Blender (right-handed, Z up).

Unity (x, y, z) <-> Blender (x, z, y). Swapping two axes flips handedness, so triangle winding is reversed too.
"""
import bpy
import numpy as np
from mathutils import Vector


def u2b(arr):
    arr = np.asarray(arr, dtype=np.float64)
    return arr[..., [0, 2, 1]]


b2u = u2b  # the swap is its own inverse


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def mesh_from_unity(name, positions, tris, uvs=None, colors=None, smooth=True):
    """positions: (N,3) unity; tris: (M,3) unity winding."""
    verts = u2b(positions)
    faces = np.asarray(tris)[:, [0, 2, 1]]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts.tolist(), [], faces.tolist())
    me.update()
    if uvs is not None:
        for key, uv in uvs.items():
            layer = me.uv_layers.new(name=key)
            loop_v = np.zeros(len(me.loops), dtype=np.int64)
            me.loops.foreach_get("vertex_index", loop_v)
            data = np.asarray(uv, dtype=np.float32)[loop_v]
            layer.data.foreach_set("uv", data.ravel())
    if colors is not None:
        attr = me.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
        attr.data.foreach_set("color", np.asarray(colors, dtype=np.float32).ravel())
    if smooth:
        me.shade_smooth()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def image_material(name, image_path, uv_name=None):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.85
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(image_path)
    if uv_name:
        uvn = nt.nodes.new("ShaderNodeUVMap")
        uvn.uv_map = uv_name
        nt.links.new(uvn.outputs["UV"], tex.inputs["Vector"])
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def full_material(name, image_path, uv_name, normal_os=None, ao=None, gloss=None, normal_ts=None):
    """Diffuse (x AO) + object-space normal + roughness from gloss, for previews close to the game look."""
    mat = image_material(name, image_path, uv_name)
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    uvn = [n for n in nt.nodes if n.type == "UVMAP"][0]
    tex = [n for n in nt.nodes if n.type == "TEX_IMAGE"][0]
    if ao:
        ai = nt.nodes.new("ShaderNodeTexImage"); ai.image = bpy.data.images.load(ao); ai.image.colorspace_settings.name = "Non-Color"
        nt.links.new(uvn.outputs["UV"], ai.inputs["Vector"])
        mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        nt.links.new(tex.outputs["Color"], mix.inputs[6]); nt.links.new(ai.outputs["Color"], mix.inputs[7])
        nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    if normal_os:
        ni = nt.nodes.new("ShaderNodeTexImage"); ni.image = bpy.data.images.load(normal_os); ni.image.colorspace_settings.name = "Non-Color"
        nt.links.new(uvn.outputs["UV"], ni.inputs["Vector"])
        nm = nt.nodes.new("ShaderNodeNormalMap"); nm.space = "OBJECT"
        nt.links.new(ni.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    if normal_ts:
        ni = nt.nodes.new("ShaderNodeTexImage"); ni.image = bpy.data.images.load(normal_ts); ni.image.colorspace_settings.name = "Non-Color"
        nt.links.new(uvn.outputs["UV"], ni.inputs["Vector"])
        nm = nt.nodes.new("ShaderNodeNormalMap"); nm.space = "TANGENT"; nm.uv_map = uv_name
        nt.links.new(ni.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    if gloss:
        gi = nt.nodes.new("ShaderNodeTexImage"); gi.image = bpy.data.images.load(gloss); gi.image.colorspace_settings.name = "Non-Color"
        nt.links.new(uvn.outputs["UV"], gi.inputs["Vector"])
        inv = nt.nodes.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0
        nt.links.new(gi.outputs["Alpha"], inv.inputs[1]); nt.links.new(inv.outputs[0], bsdf.inputs["Roughness"])
    return mat


def color_material(name, rgb, roughness=0.8):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    mat.diffuse_color = (*rgb, 1.0)
    return mat


def setup_render(res=(900, 900), engine="BLENDER_EEVEE_NEXT", transparent=False):
    sc = bpy.context.scene
    try:
        sc.render.engine = engine
    except TypeError:
        sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.film_transparent = transparent
    if sc.world is None:
        sc.world = bpy.data.worlds.new("World")
    sc.world.use_nodes = True
    bg = sc.world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.78, 0.84, 0.88, 1)
    bg.inputs["Strength"].default_value = 0.9
    sun = bpy.data.lights.new("Sun", "SUN")
    sun.energy = 3.2
    so = bpy.data.objects.new("Sun", sun)
    so.rotation_euler = (0.75, 0.15, 0.6)
    sc.collection.objects.link(so)
    try:
        sc.view_settings.view_transform = "Standard"
    except Exception:
        pass


def camera(name, location, target, ortho_scale=None, lens=60):
    cam = bpy.data.cameras.new(name)
    if ortho_scale:
        cam.type = "ORTHO"
        cam.ortho_scale = ortho_scale
    else:
        cam.lens = lens
    ob = bpy.data.objects.new(name, cam)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = location
    d = Vector(target) - Vector(location)
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return ob


def render(cam, path):
    sc = bpy.context.scene
    sc.camera = cam
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
