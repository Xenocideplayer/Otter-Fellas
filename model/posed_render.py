"""Render the otter in an animation pose with all maps. usage: posed_render.py otter.npz model.timbermesh anim:frame prefix tex out.png [scale] [sash_on]"""
import sys; sys.path.insert(0,'.')
import bpy, numpy as np, blend_util as bu, timbermesh as tm, tempfile
from mathutils import Vector
from PIL import Image
npz, tmesh, spec, prefix, tex, out = sys.argv[1:7]
s=float(sys.argv[7]) if len(sys.argv)>7 else 1.0
o=np.load(npz); m=tm.read(tmesh); n=[x for x in m.nodes if x.vertex_count][0]
name,fi=spec.split(':'); a=[x for x in n.vertex_animations if x.name==name][0]
fr={p.name:p for p in a.frames[int(fi)]}
P=o['pos']+fr['offset'].array()
bu.reset_scene()
ob=bu.mesh_from_unity('Otter',P,o['tris'],uvs={'uv0':o['uv0']})
ob.data.materials.append(bu.full_material('m',tex,'uv0',ao=prefix+'AO.png',gloss=prefix+'Gloss.png',normal_ts=prefix+'NormalTS_blender_preview.png'))
bpy.ops.mesh.primitive_plane_add(size=6); bpy.context.active_object.data.materials.append(bu.color_material('g',(0.30,0.36,0.26),0.95))
bu.setup_render((700,700))
sc=bpy.context.scene
sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=0.6
sun=[x for x in bpy.data.lights if x.type=='SUN'][0]; sun.energy=3.6; sun.color=(1.0,0.92,0.8)
rim=bpy.data.lights.new('rim','AREA'); rim.energy=12*s*s; rim.size=0.6*s; rim.color=(0.8,0.9,1.0)
ro=bpy.data.objects.new('rim',rim); ro.location=(-0.4*s,-0.9*s,0.8*s); sc.collection.objects.link(ro)
ro.rotation_euler=(Vector((0,-0.1*s,0.3*s))-ro.location).to_track_quat('-Z','Y').to_euler()
TMP=tempfile.gettempdir(); paths=[]
views=[((0.62*s,1.05*s,0.5*s),(0,0,0.26*s),45),((0.22*s,0.62*s,0.47*s),(0,0.12*s,0.42*s),70),((-0.75*s,-0.95*s,0.6*s),(0,-0.05*s,0.25*s),45),((1.2*s,0.0,0.35*s),(0,-0.1*s,0.25*s),45)]
for i,(loc,tgt,lens) in enumerate(views):
    cam=bu.camera(f'c{i}',loc,tgt,lens=lens); p=f'{TMP}/_pr{i}.png'; bu.render(cam,p); paths.append(p)
W=Image.new('RGB',(1400,1400))
for i,p in enumerate(paths): W.paste(Image.open(p).convert('RGB'),((i%2)*700,(i//2)*700))
W.save(out)
