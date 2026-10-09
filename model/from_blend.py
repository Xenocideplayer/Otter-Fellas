"""Turn an edited otter .blend back into the npz the exporter uses.

usage: python3 from_blend.py otter_adult.blend otter_adult.npz
then:  python3 export_otter.py BeaverAdult.timbermesh otter_adult.npz OtterAdult.Model.timbermesh 0.03
       (0.02 for the kit). Keep the object named "Otter", triangulated, with one UV map, standing where it is now
       (the beaver's animations are matched by position).
"""
import sys
sys.path.insert(0, ".")
import bpy
import numpy as np
import blend_util as bu

blend, out_npz = sys.argv[1], sys.argv[2]
bpy.ops.wm.open_mainfile(filepath=blend)
ob = bpy.data.objects["Otter"]
out = out_npz[:-4] if out_npz.endswith(".npz") else out_npz
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
