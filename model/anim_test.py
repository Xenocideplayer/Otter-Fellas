import sys; sys.path.insert(0,'.')
import numpy as np, time, beaver_data as bd, transfer as tr, meshutil
d=bd.load(sys.argv[1]); o=dict(np.load(sys.argv[2])); out=sys.argv[3]; sigma=float(sys.argv[4]); names=sys.argv[5].split(',')
o['nrm']=meshutil.vertex_normals(o['pos'],o['tris'],o['src_vertex'])
o['tan']=meshutil.tangents(o['pos'],o['uv0'],o['tris'],o['nrm'])
t=time.time(); idx,w,dist=tr.bind(d,o['pos'],sigma); print('bind',time.time()-t,'K',idx.shape[1],'maxdist',dist.max())
qo=tr.otter_rest_quats(o); qb=tr.frame_quat(d['nrm'],d['tan'][:,:3])
anims={a.name:a for a in d['node'].vertex_animations}
res={}
for spec in names:
    nm,fi=spec.split(':'); fi=int(fi)
    a=anims[nm]; t=time.time()
    off,rot=tr.transfer_animation(a,d,o,idx,w,qo,qb)
    bo,_=bd.frames(a)
    res[nm]=(o['pos']+off[fi], d['pos']+bo[fi])
    print(nm,len(a.frames),'t',round(time.time()-t,2),'max off',np.abs(off).max())
np.savez(out, **{f'o_{k}':v[0] for k,v in res.items()}, **{f'b_{k}':v[1] for k,v in res.items()})
