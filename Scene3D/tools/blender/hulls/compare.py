"""Overlay a remodel on the measured blueprint (measure.py output), in the ship frame.

    <blender-python> tools/blender/hulls/compare.py <model.blend|model.glb> <measure-dir> <outdir>
        [--views port,top,stern,bow] [--z 53,40,20,0,-20,-40] [--object hull]

Writes <outdir>/cmp-<view>.png (silhouette difference: blue = blueprint only, red = remodel
only, grey = both, shaded by the remodel's normal), cmp-sections.png (blueprint sections grey,
remodel red, on a 1 m grid) and cmp.json (silhouette IoU and the 95th-percentile outline
deviation per view, metres).
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402

import measure as M  # noqa: E402
import assemble_frame as F  # noqa: E402


def load_model(path, name='hull'):
    if path.endswith('.blend'):
        bpy.ops.wm.open_mainfile(filepath=path)
        ob = bpy.data.objects.get(name) or next(o for o in bpy.data.objects if o.type == 'MESH')
        return [ob]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.data.objects if o.type == 'MESH']


def bvh_many(obs):
    vs, ps = [], []
    for ob in obs:
        me = ob.data
        mw = ob.matrix_world
        b = len(vs)
        vs += [F.s_vec(mw @ v.co) for v in me.vertices]
        ps += [tuple(b + i for i in p.vertices) for p in me.polygons]
    return BVHTree.FromPolygons(vs, ps, all_triangles=False)


def edge_dist(a, b):
    """95th percentile distance (px) from each silhouette's boundary to the other's."""
    from scipy.ndimage import distance_transform_edt, binary_erosion
    ea = a & ~binary_erosion(a); eb = b & ~binary_erosion(b)
    da = distance_transform_edt(~ea); db = distance_transform_edt(~eb)
    d = np.concatenate([db[ea], da[eb]])
    return float(np.percentile(d, 95)) if d.size else 0.0


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d
    model, mdir, out = argv[0], argv[1], argv[2]
    os.makedirs(out, exist_ok=True)
    obs = load_model(model, opt('--object', 'hull'))
    bvh = bvh_many(obs)
    meta = json.load(open(os.path.join(mdir, 'ortho.json')))
    rep = {}
    for v in opt('--views', 'port,top,stern,bow').split(','):
        m = meta[v]
        dep = np.load(os.path.join(mdir, f'depth-{v}.npy'))
        W, H, res = m['W'], m['H'], m['res']
        d, r, u = (np.array(m[k]) for k in ('d', 'r', 'u'))
        start = -80.0
        from mathutils import Vector
        D = Vector(d)
        d2 = np.full((H, W), np.nan, np.float32)
        nrm = np.zeros((H, W, 3), np.float32)
        for j in range(H):
            uv = m['u1'] - (j + 0.5) * res
            for i in range(W):
                rv = m['r0'] + (i + 0.5) * res
                o = Vector(r * rv + u * uv + d * start)
                p, n, _i, dist = bvh.ray_cast(o, D, 200)
                if p is not None:
                    d2[j, i] = start + dist
                    nrm[j, i] = n if n.dot(D) < 0 else -n
        a, b = ~np.isnan(dep), ~np.isnan(d2)
        g = M.shade(nrm, d2, v)
        ov = np.stack([g] * 3, -1)
        ov[~a & ~b] = 0.97
        ov[a & ~b] = [0.2, 0.45, 1.0]
        ov[b & ~a] = [1.0, 0.25, 0.2]
        M.grid_image(g, m, f'remodel {v}: blue = blueprint only, red = remodel only', overlay=ov).save(os.path.join(out, f'cmp-{v}.png'))
        iou = float((a & b).sum() / max(1, (a | b).sum()))
        rep[v] = {'iou': round(iou, 4), 'edge_p95_m': round(edge_dist(a, b) * res, 3)}
        print('[compare]', v, rep[v], flush=True)
    # sections
    zs = [float(z) for z in opt('--z', '53.5,47.5,41.5,35.5,29.5,23.5,19.5,13.5,5.5,-2.5,-8.5,-12.5,-18.5,-24.5,-30.5,-36.5,-42.5,-48.5').split(',')]
    bz = json.load(open(os.path.join(mdir, 'sections-z.json')))
    keys = {z: min(bz.keys(), key=lambda k: abs(float(k) - z)) for z in zs}
    blue = {z: bz[keys[z]] for z in zs}
    import bmesh
    red = {}
    for z in zs:
        segs = []
        for ob in obs:
            s = M.sections(ob, 'z', [float(keys[z])])
            segs += s[float(keys[z])]
        red[z] = segs
    M.draw_sections(blue, 'z', os.path.join(out, 'cmp-sections.png'), red, cols=6, cell=520, span=(-36, 36, -24, 24))
    json.dump(rep, open(os.path.join(out, 'cmp.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
