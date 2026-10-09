"""Hero renders of the otter alone (EEVEE). usage: hero.py otter.npz texture.png out.png [scale]"""
import tempfile
TMP = tempfile.gettempdir()
import sys; sys.path.insert(0,'.')
import bpy, numpy as np, blend_util as bu
from PIL import Image
o=np.load(sys.argv[1]); tex=sys.argv[2]; out=sys.argv[3]; s=float(sys.argv[4]) if len(sys.argv)>4 else 1.0
bu.reset_scene()
ob=bu.mesh_from_unity('Otter',o['pos'],o['tris'],uvs={'uv0':o['uv0']})
ob.data.materials.append(bu.image_material('ot',tex,'uv0'))
bpy.ops.mesh.primitive_plane_add(size=6)
pl=bpy.context.active_object; pl.data.materials.append(bu.color_material('g',(0.42,0.5,0.3),0.95))
bu.setup_render((640,640))
c=(0,-0.08*s,0.28*s)
views=[(0.75*s,1.15*s,0.55*s),(1.35*s,-0.1*s,0.35*s),(-0.6*s,-1.2*s,0.6*s),(0.18*s,0.55*s,0.47*s)]
targets=[c,c,c,(0,0.15*s,0.45*s)]
paths=[]
for i,(v,t) in enumerate(zip(views,targets)):
    cam=bu.camera(f'c{i}',v,t,lens=50 if i<3 else 70)
    p=f'{TMP}/_hero{i}.png'; bu.render(cam,p); paths.append(p)
ims=[Image.open(p).convert('RGB') for p in paths]
W=Image.new('RGB',(640*2,640*2))
for i,im in enumerate(ims): W.paste(im,((i%2)*640,(i//2)*640))
W.save(out)
