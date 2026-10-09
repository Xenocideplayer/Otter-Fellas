"""Flat-colour preview of a building timbermesh. usage: building_preview.py model.timbermesh out.png"""
import sys; sys.path.insert(0,'.')
import bpy, numpy as np, blend_util as bu, timbermesh as tm, tempfile
from mathutils import Quaternion, Vector, Matrix
from PIL import Image
m=tm.read(sys.argv[1]); out=sys.argv[2]
COL={'Cattail':(0.35,0.5,0.2),'ThatchedRoof':(0.75,0.62,0.3),'Windows':(0.3,0.45,0.6),'BaseWood_White':(0.85,0.82,0.75),'BaseWood_LightBrown':(0.62,0.45,0.28),'BaseWood_Brown':(0.42,0.28,0.17),'IrregularPlanks':(0.5,0.36,0.22)}
def col(name):
    for k,v in COL.items():
        if name.startswith(k): return v
    return (0.6,0.6,0.6)
bu.reset_scene()
mats={}
world={}
for i,n in enumerate(m.nodes):
    # Unity TRS -> matrix in Unity space
    q=n.rotation; T=Matrix.Translation(n.position); R=Quaternion((q[3],q[0],q[1],q[2])).to_matrix().to_4x4(); S=Matrix.Diagonal((*n.scale,1))
    local=T@R@S
    world[i]=(world[n.parent]@local) if n.parent>=0 else local
    if not n.vertex_count: continue
    P=n.prop('position').array().astype(float)
    W=np.array(world[i]); Ph=np.c_[P,np.ones(len(P))]@W.T
    tris=np.concatenate([x.indices for x in n.meshes]).reshape(-1,3)
    ob=bu.mesh_from_unity(n.name,Ph[:,:3],tris,smooth=False)
    me=ob.data; off=0
    for mp in n.meshes:
        if mp.material not in mats: mats[mp.material]=bu.color_material(mp.material,col(mp.material))
        me.materials.append(mats[mp.material])
    idx=0; fi=0
    for k,mp in enumerate(n.meshes):
        cnt=len(mp.indices)//3
        for f in range(fi,fi+cnt): me.polygons[f].material_index=k
        fi+=cnt
sc=bpy.context.scene; sc.render.engine='BLENDER_WORKBENCH'; sc.display.shading.light='STUDIO'; sc.display.shading.color_type='MATERIAL'; sc.display.shading.show_cavity=True
sc.render.resolution_x=sc.render.resolution_y=600; sc.display.render_aa='8'
bpy.ops.mesh.primitive_plane_add(size=1,location=(1,1.5,-0.001)); pl=bpy.context.active_object; pl.scale=(2,3,1); pl.data.materials.append(bu.color_material('g',(0.45,0.55,0.35)))
paths=[]
for i,loc in enumerate([(4.5,5.5,3.5),(-2.5,-2,3.0)]):
    cam=bu.camera(f'c{i}',loc,(1,1.5,0.7),lens=40); p=f'{tempfile.gettempdir()}/_bp{i}.png'; bu.render(cam,p); paths.append(p)
Wd=Image.new('RGB',(1200,600))
for i,p in enumerate(paths): Wd.paste(Image.open(p).convert('RGB'),(i*600,0))
Wd.save(out)
