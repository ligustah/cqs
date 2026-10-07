"""glbppm.py <glb> <texsize> [box x0 x1 y0 y1 z0 z1] : per-mesh tris, and px/m of triangles whose centroid is in the box."""
import json, struct, sys
import numpy as np
d = open(sys.argv[1], 'rb').read()
L = struct.unpack('<I', d[12:16])[0]; j = json.loads(d[20:20 + L]); b0 = 20 + L + 8
CT = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8, 5122: np.int16, 5120: np.int8}
NORM = {5122: 32767.0, 5120: 127.0, 5123: 65535.0, 5121: 255.0}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}
def acc(i):
    a = j['accessors'][i]; bv = j['bufferViews'][a['bufferView']]
    o = b0 + bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    t = np.dtype(CT[a['componentType']]); k = NC[a['type']]
    st = bv.get('byteStride', t.itemsize * k)
    raw = np.frombuffer(d, np.uint8, st * (a['count'] - 1) + t.itemsize * k, o)
    out = np.lib.stride_tricks.as_strided(raw, (a['count'], k * t.itemsize), (st, 1)).copy().view(t).reshape(a['count'], k)
    if a.get('normalized'):
        out = out.astype(float) / NORM[a['componentType']]
    return out
tex = int(sys.argv[2]); box = [float(x) for x in sys.argv[3:9]] if len(sys.argv) > 8 else None
# node transforms (translation/rotation/scale only, flat)
def mat(n):
    import math
    M = np.eye(4)
    if 'matrix' in n: return np.array(n['matrix']).reshape(4, 4).T
    t = n.get('translation', [0, 0, 0]); r = n.get('rotation', [0, 0, 0, 1]); s = n.get('scale', [1, 1, 1])
    x, y, z, w = r
    R = np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)], [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)], [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])
    M[:3, :3] = R * np.array(s); M[:3, 3] = t
    return M
def walk(ni, P):
    n = j['nodes'][ni]; M = P @ mat(n)
    if 'mesh' in n:
        for pr in j['meshes'][n['mesh']]['primitives']:
            if 'TEXCOORD_0' not in pr['attributes']: continue
            p = acc(pr['attributes']['POSITION']).astype(float); uv = acc(pr['attributes']['TEXCOORD_0']).astype(float)
            idx = acc(pr['indices']).reshape(-1, 3) if 'indices' in pr else np.arange(len(p)).reshape(-1, 3)
            p = (np.c_[p, np.ones(len(p))] @ M.T)[:, :3]
            A = p[idx]; U = uv[idx]
            wa = 0.5 * np.linalg.norm(np.cross(A[:, 1] - A[:, 0], A[:, 2] - A[:, 0]), axis=1)
            ua = 0.5 * np.abs(np.cross(U[:, 1] - U[:, 0], U[:, 2] - U[:, 0])) * tex * tex
            c = A.mean(1)
            m = np.ones(len(c), bool)
            if box:
                m = (c[:, 0] > box[0]) & (c[:, 0] < box[1]) & (c[:, 1] > box[2]) & (c[:, 1] < box[3]) & (c[:, 2] > box[4]) & (c[:, 2] < box[5])
            m &= wa > 1e-4
            name = n.get('name', '?')
            if m.sum():
                ppm = np.sqrt(ua[m] / wa[m])
                print(f'{name:40s} tris {len(idx):6d} in-box {m.sum():5d}  px/m median {np.median(ppm):.1f}  area-weighted {np.sqrt(ua[m].sum() / wa[m].sum()):.1f}')
            elif not box:
                print(f'{name:40s} tris {len(idx):6d}')
    for c in n.get('children', []): walk(c, M)
for r in j['scenes'][j.get('scene', 0)]['nodes']: walk(r, np.eye(4))
