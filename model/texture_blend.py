"""Give the saved otter .blend its fur texture (packed into the file) so it opens ready to look at."""
import sys
sys.path.insert(0, ".")
import bpy
import blend_util as bu
blend, tex, out = sys.argv[1:4]
bpy.ops.wm.open_mainfile(filepath=blend)
ob = bpy.data.objects["Otter"]
ob.data.materials.clear()
mat = bu.image_material("OtterFur", tex, ob.data.uv_layers[0].name)
ob.data.materials.append(mat)
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
