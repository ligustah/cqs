import sys
import numpy as np
from PIL import Image, ImageDraw
exec(open(__file__.replace('uvdraw.py', 'glbppm.py')).read().split('for r in j')[0])
out = sys.argv[3]
k = 0
for n in j['nodes']:
    if 'mesh' not in n: continue
    for pi, pr in enumerate(j['meshes'][n['mesh']]['primitives']):
        p = acc(pr['attributes']['POSITION']).astype(float); uv = acc(pr['attributes']['TEXCOORD_0']).astype(float)
        idx = acc(pr['indices']).reshape(-1, 3)
        A = p[idx]; U = uv[idx]
        wa = 0.5 * np.linalg.norm(np.cross(A[:, 1] - A[:, 0], A[:, 2] - A[:, 0]), axis=1)
        mat = j['materials'][pr.get('material', 0)].get('name')
        im = Image.new('RGB', (1024, 1024), 'black'); d = ImageDraw.Draw(im)
        big = np.argsort(-wa)
        for t in range(len(U)):
            q = [(float(u[0]) * 1024, float(u[1]) * 1024) for u in U[t]]
            c = A[t].mean(0)
            col = (int(min(255, 40 + wa[t] * 4)), 120, 200)
            d.polygon(q, fill=col)
        im.save(out.replace('.png', f'-{k}.png')); print(k, mat, len(idx), 'uv bbox', U.reshape(-1, 2).min(0).round(3), U.reshape(-1, 2).max(0).round(3)); k += 1
