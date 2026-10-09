import tempfile
TMP = tempfile.gettempdir()
import sys, numpy as np, trimesh
sys.path.insert(0,'.')
import beaver_data as bd, otter_shape as osh
which=sys.argv[1]
src_dir=sys.argv[2]  # folder holding BeaverAdult.timbermesh / BeaverChild.timbermesh extracted from your game
src={'adult':'BeaverAdult','child':'BeaverChild'}[which]
params={'adult':osh.ADULT_PARAMS,'child':osh.CHILD_PARAMS}[which]
d=bd.load(f'{src_dir}/{src}.timbermesh')
m=trimesh.Trimesh(d['pos'],d['tris'],process=True)
body=max(m.split(only_watertight=False),key=lambda b:len(b.vertices))
if which=='child': osh.VOXEL=0.0028
v,f=osh.build(np.asarray(body.vertices),np.asarray(body.faces),params)
print(which,'mc',len(v),len(f))
np.savez(f'{TMP}/otter_{which}_raw.npz',v=v,f=f)
