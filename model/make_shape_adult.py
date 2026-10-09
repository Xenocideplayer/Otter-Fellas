import sys, time, numpy as np, trimesh
sys.path.insert(0,'.')
import beaver_data as bd, otter_shape as osh
d=bd.load('/mnt/user-data/uploads/Timberborn/_otter_extract/BeaverAdult.timbermesh')
m=trimesh.Trimesh(d['pos'],d['tris'],process=True)
body=max(m.split(only_watertight=False),key=lambda b:len(b.vertices))
t=time.time()
v,f=osh.build(np.asarray(body.vertices),np.asarray(body.faces))
print('mc',len(v),len(f),time.time()-t)
np.savez('/tmp/claude-0/otter_adult_raw.npz',v=v,f=f)
