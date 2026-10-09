import numpy as np
def vertex_normals(pos, tris, group=None):
    fn = np.cross(pos[tris[:,1]]-pos[tris[:,0]], pos[tris[:,2]]-pos[tris[:,0]])
    n = np.zeros_like(pos)
    for k in range(3): np.add.at(n, tris[:,k], fn)
    if group is not None:  # share normals between vertices split only by UV seams
        g = np.zeros((group.max()+1,3)); np.add.at(g, group, n); n = g[group]
    return n/np.linalg.norm(n,axis=1,keepdims=True)
def tangents(pos, uv, tris, nrm, group=None):
    p0,p1,p2 = pos[tris[:,0]],pos[tris[:,1]],pos[tris[:,2]]
    u0,u1,u2 = uv[tris[:,0]],uv[tris[:,1]],uv[tris[:,2]]
    e1,e2 = p1-p0,p2-p0; d1,d2 = u1-u0,u2-u0
    r = d1[:,0]*d2[:,1]-d2[:,0]*d1[:,1]; r = np.where(np.abs(r)<1e-12,1e-12,r)
    t = (e1*d2[:,1:2]-e2*d1[:,1:2])/r[:,None]
    T = np.zeros_like(pos)
    for k in range(3): np.add.at(T, tris[:,k], t)
    T = T - nrm*np.sum(T*nrm,1,keepdims=True)
    bad = np.linalg.norm(T,axis=1)<1e-9
    T[bad] = np.cross(nrm[bad],[0,1,0.001])
    return T/np.linalg.norm(T,axis=1,keepdims=True)
