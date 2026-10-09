import sys; sys.path.insert(0,'.')
import bpy, numpy as np, blend_util as bu, beaver_data as bd
from PIL import Image
frames=np.load(sys.argv[1]); o=np.load(sys.argv[2]); tex=sys.argv[3]; beaver=sys.argv[4]; out=sys.argv[5]
d=bd.load(beaver)
keys=[k[2:] for k in frames.files if k.startswith('o_')]
ims=[]
for k in keys:
    bu.reset_scene()
    ob=bu.mesh_from_unity('O',frames['o_'+k],o['tris'],uvs={'uv0':o['uv0']}); ob.data.materials.append(bu.image_material('m',tex,'uv0'))
    bv=bu.mesh_from_unity('B',frames['b_'+k],d['tris']); bv.data.materials.append(bu.color_material('g',(0.6,0.6,0.6))); bv.location.x=0.7
    sc=bpy.context.scene; sc.render.engine='BLENDER_WORKBENCH'; sc.display.shading.light='STUDIO'; sc.display.shading.color_type='TEXTURE'
    sc.render.resolution_x=sc.render.resolution_y=500; sc.display.render_aa='8'
    cam=bu.camera('c',(1.9,1.9,0.9),(0.35,-0.1,0.2),ortho_scale=1.5)
    p=f'/tmp/claude-0/r/_a_{k}.png'; bu.render(cam,p)
    im=Image.open(p).convert('RGB'); 
    from PIL import ImageDraw; ImageDraw.Draw(im).text((10,10),k,fill=(255,255,0)); ims.append(im)
cols=3; rows=(len(ims)+cols-1)//cols
W=Image.new('RGB',(500*cols,500*rows))
for i,im in enumerate(ims): W.paste(im,((i%cols)*500,(i//cols)*500))
W.save(out)
