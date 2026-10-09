import sys; sys.path.insert(0,'.')
import numpy as np, paint, meshutil, landmarks, time
o=dict(np.load('/tmp/claude-0/otter_adult.npz'))
o['nrm']=meshutil.vertex_normals(o['pos'],o['tris'],o['src_vertex'])
t=time.time()
paint.make_textures(o, landmarks.ADULT, paint.ADULT_VARIANTS[:1], 2048, ['/tmp/claude-0/otter_adult_tex1.png'])
print('painted',time.time()-t)
