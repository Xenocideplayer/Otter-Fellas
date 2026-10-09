import sys; sys.path.insert(0,'.')
import numpy as np, timbermesh as tm
path, uvnpz, out, specs = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4].split(',')
m=tm.read(path); n=[x for x in m.nodes if x.vertex_count][0]
pos=n.prop('position').array(); tris=np.concatenate([x.indices for x in n.meshes]).reshape(-1,3); uv0=n.prop('uv0').array()
A={a.name:a for a in n.vertex_animations}
res={}
for s in specs:
    nm,fi=s.split(':'); a=A[nm]; fr={p.name:p for p in a.frames[int(fi)]}
    res['o_'+nm]=pos+fr['offset'].array()
np.savez(out,**res)
np.savez(out.replace('.npz','_mesh.npz'),pos=pos,tris=tris,uv0=uv0)
print('anims',len(A))
