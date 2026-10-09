import tempfile
TMP = tempfile.gettempdir()
import sys; sys.path.insert(0,'.')
import bpy, numpy as np, blend_util as bu
from PIL import Image, ImageDraw
frames=np.load(sys.argv[1]); o=np.load(sys.argv[2]); tex=sys.argv[3]; out=sys.argv[4]
keys=[k[2:] for k in frames.files if k.startswith('o_')]
ims=[]
for k in keys:
  for vi,view in enumerate([(1.0,1.2,0.6),(-1.1,0.6,0.5)]):
    bu.reset_scene()
    P=frames['o_'+k]
    ob=bu.mesh_from_unity('O',P,o['tris'],uvs={'uv0':o['uv0']}); ob.data.materials.append(bu.image_material('m',tex,'uv0'))
    sc=bpy.context.scene; sc.render.engine='BLENDER_WORKBENCH'; sc.display.shading.light='STUDIO'; sc.display.shading.color_type='TEXTURE'
    sc.render.resolution_x=sc.render.resolution_y=420; sc.display.render_aa='8'
    c=bu.u2b(P.mean(0)); 
    cam=bu.camera('c',tuple(c+np.array(view)),tuple(c),lens=50)
    p=f'{TMP}/_c.png'; bu.render(cam,p)
    im=Image.open(p).convert('RGB'); ImageDraw.Draw(im).text((8,8),k[12:],fill=(255,255,0)); ims.append(im)
cols=4; rows=(len(ims)+cols-1)//cols
W=Image.new('RGB',(420*cols,420*rows))
for i,im in enumerate(ims): W.paste(im,((i%cols)*420,(i//cols)*420))
W.save(out)
