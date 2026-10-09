import sys, time; sys.path.insert(0,'.')
import numpy as np, paint, meshutil, landmarks, beaver_data as bd, bake_detail as bk
which=sys.argv[1]; out=sys.argv[2]
X='/mnt/user-data/uploads/Timberborn/_otter_extract'
cfg={'adult':('BeaverAdult',2048,'Adult_Normal_2K','Adult_AO_2K','BeaverAdult1.Folktails',paint.ADULT_VARIANTS),
     'child':('BeaverChild',1024,'Chilkd_Normal_1K','Child_AO_1K','BeaverChild1.Folktails',paint.CHILD_VARIANTS)}[which]
import os
o=dict(np.load(os.environ.get('MESH', f'/home/claude/otters/model_out/otter_{which}.npz')))
o['nrm']=meshutil.vertex_normals(o['pos'],o['tris'],o['src_vertex'])
d=bd.load(f'{X}/{cfg[0]}.timbermesh')
maps=bk.load_maps(f'{X}/ref/{cfg[2]}.png',f'{X}/ref/{cfg[3]}.png',f'{X}/{cfg[4]}.png')
import trimesh
raw=np.load(os.environ.get('RAW', f'/tmp/otter_{which}_raw.npz'))
hm=trimesh.Trimesh(raw['v'],raw['f'],process=True); trimesh.smoothing.filter_laplacian(hm,lamb=0.5,iterations=8)
hires=(np.asarray(hm.vertices),np.asarray(hm.vertex_normals))
t=time.time()
paint.make_textures(o, getattr(landmarks,which.upper()), cfg[5][:1], cfg[1], [f'{out}/{which}_tex1.png'], beaver=d, beaver_maps=maps, maps_prefix=f'{out}/{which}_', hires=hires)
print('done',time.time()-t)
