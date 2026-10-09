import sys; sys.path.insert(0,'.')
import numpy as np, paint, meshutil, landmarks
which=sys.argv[1]; size=int(sys.argv[2])
o=dict(np.load(f'/tmp/claude-0/otter_{which}.npz'))
o['nrm']=meshutil.vertex_normals(o['pos'],o['tris'],o['src_vertex'])
L=getattr(landmarks,which.upper()); V=paint.ADULT_VARIANTS if which=='adult' else paint.CHILD_VARIANTS
paint.make_textures(o, L, V[:1], size, [f'/tmp/claude-0/otter_{which}_tex1.png'])
