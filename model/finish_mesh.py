"""Blender pass: raw marching-cubes otter -> low-poly game mesh with UVs; saves .blend + npz (Unity space).

usage: python3 finish_mesh.py raw.npz out_prefix target_tris
"""
import sys
sys.path.insert(0, ".")
import bpy
import bmesh
import numpy as np
import blend_util as bu

raw, out, target = sys.argv[1], sys.argv[2], int(sys.argv[3])
bu.reset_scene()
r = np.load(raw)
ob = bu.mesh_from_unity("Otter", r["v"], r["f"], smooth=False)
bpy.context.view_layer.objects.active = ob
ob.select_set(True)

# light smoothing first so decimation follows the form, not voxel steps
m = ob.modifiers.new("smooth", "SMOOTH")
m.factor, m.iterations = 0.5, 4
bpy.ops.object.modifier_apply(modifier="smooth")

dec = ob.modifiers.new("dec", "DECIMATE")
dec.ratio = target / len(ob.data.polygons)
dec.use_symmetry = True
dec.symmetry_axis = "X"
bpy.ops.object.modifier_apply(modifier="dec")

# triangulate, clean
bm = bmesh.new()
bm.from_mesh(ob.data)
bmesh.ops.triangulate(bm, faces=bm.faces[:])
bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
bm.to_mesh(ob.data)
bm.free()
ob.data.shade_smooth()

# UVs: smart project, one island set, small margin
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.012, area_weight=0.0, scale_to_bounds=True)
bpy.ops.object.mode_set(mode="OBJECT")

bpy.ops.wm.save_as_mainfile(filepath=out + ".blend")

# export per-corner data -> split vertices by (position, uv) so each game vertex has one UV
me = ob.data
me.calc_loop_triangles()
nl = len(me.loops)
loop_v = np.zeros(nl, dtype=np.int64); me.loops.foreach_get("vertex_index", loop_v)
uv = np.zeros(nl * 2, dtype=np.float32); me.uv_layers.active.data.foreach_get("uv", uv); uv = uv.reshape(-1, 2)
co = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
tris = np.array([lt.loops[:] for lt in me.loop_triangles], dtype=np.int64)
key = np.round(np.concatenate([loop_v[:, None].astype(np.float64), uv * 65536.0], 1)).astype(np.int64)
_, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
inv = inv.ravel()
pos_b = co[loop_v[first]]
uv_out = uv[first]
faces = inv[tris]
pos_u = bu.b2u(pos_b)
faces_u = faces[:, [0, 2, 1]]
np.savez(out + ".npz", pos=pos_u, uv0=uv_out, tris=faces_u, src_vertex=loop_v[first])
print("verts", len(pos_u), "tris", len(faces_u))
