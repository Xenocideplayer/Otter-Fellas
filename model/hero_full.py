"""Rest-pose renders with all maps. usage: hero_full.py mesh.npz tex.png prefix out.png [scale]"""
import sys; sys.path.insert(0,'.')
import bpy, numpy as np, blend_util as bu, tempfile
from mathutils import Vector
from PIL import Image
npz, tex, prefix, out = sys.argv[1:5]; s=float(sys.argv[5]) if len(sys.argv)>5 else 1.0
o=np.load(npz); bu.reset_scene()
ob=bu.mesh_from_unity('O',o['pos'],o['tris'],uvs={'uv0':o['uv0']})
ob.data.materials.append(bu.full_material('m',tex,'uv0',ao=prefix+'AO.png',gloss=prefix+'Gloss.png',normal_ts=prefix+'NormalTS_blender_preview.png'))
bpy.ops.mesh.primitive_plane_add(size=6); bpy.context.active_object.data.materials.append(bu.color_material('g',(0.30,0.36,0.26),0.95))
bu.setup_render((640,640))
sun=[x for x in bpy.data.lights if x.type=='SUN'][0]; sun.energy=3.8; sun.color=(1.0,0.9,0.76)
views=[((0.7*s,1.1*s,0.5*s),(0,0,0.27*s),45),((0.16*s,0.5*s,0.47*s),(0,0.12*s,0.44*s),70),((-0.75*s,-0.95*s,0.6*s),(0,-0.05*s,0.25*s),45),((1.25*s,0.05,0.35*s),(0,-0.1*s,0.26*s),45)]
paths=[]
for i,(loc,tgt,lens) in enumerate(views):
    cam=bu.camera(f'c{i}',loc,tgt,lens=lens); p=f'{tempfile.gettempdir()}/_hf{i}.png'; bu.render(cam,p); paths.append(p)
W=Image.new('RGB',(1280,1280))
for i,p in enumerate(paths): W.paste(Image.open(p).convert('RGB'),((i%2)*640,(i//2)*640))
W.save(out)
