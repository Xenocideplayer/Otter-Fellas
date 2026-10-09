import sys; sys.path.insert(0,'.')
import bpy, numpy as np, beaver_data as bd, blend_util as bu
from mathutils import Vector
bu.reset_scene()
d=bd.load('/mnt/user-data/uploads/Timberborn/_otter_extract/BeaverAdult.timbermesh')
ob=bu.mesh_from_unity('Beaver',d['pos'],d['tris'],uvs={'uv0':d['uv0']})
ob.data.materials.append(bu.image_material('bv','/mnt/user-data/uploads/Timberborn/_otter_extract/BeaverAdult1.Folktails.png','uv0'))
bu.setup_render((700,700))
c=(0,-0.15,0.27)
views={'front':(0,1.6,0.3),'side':(1.6,-0.15,0.3),'back':(0,-1.9,0.4),'top':(0.001,-0.15,1.8),'persp':(1.0,0.9,0.7)}
for k,loc in views.items():
    cam=bu.camera(k,loc,c,ortho_scale=0.9 if k!='persp' else None, lens=50)
    bu.render(cam,f'/tmp/claude-0/r/beaver_{k}.png')
