"""Measure the real DD-12 (assets/ships/destroyer.glb) for its part-built state in the shipyard.

    $PY tools/blender/buildings/shipyard_measure.py [--out tools/blender/specs/shipyard-dd12.json]

Everything is in the destroyer GLB's own MODEL frame (metres, bow +Z, dorsal +Y, port +X, not
centred; src/lib/glbship.js centres it on its bbox at runtime). Writes:
  bbox            the whole GLB (hull + kit parts), and its centre (glbship's centring offset)
  frames          ring-frame outlines at the frame stations of shipyard_dims.FRAMES: the hull's
                  section at z (hull node only), cut to y <= top, as a simplified convex outline
                  (x, y) CCW; the procedural frames in shipyard.py follow them, so they match the
                  octagonal section of the real hull
  bottom          hull bottom y on a grid (x, z) for the keel and bilge blocks (ray cast upward;
                  forward of the plated cut through every node, aft of it the hull node only)
  keptMin         lowest y of what the runtime build state keeps (shipyard.js clip regions)
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import bpy  # noqa: E402
import bmesh  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402

import assemble_frame as F  # noqa: E402
import shipyard_dims as D  # noqa: E402


def hull2d(pts):
    """Convex hull (monotone chain), CCW."""
    P = sorted(set((round(x, 3), round(y, 3)) for x, y in pts))
    if len(P) < 3:
        return P
    cross = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in P:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(P):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def simplify(poly, min_turn=10.0, min_edge=1.2):
    """Drop vertices that turn less than min_turn degrees or sit closer than min_edge to the next."""
    P = list(poly)
    changed = True
    while changed and len(P) > 4:
        changed = False
        for i in range(len(P)):
            a, b, c = Vector(P[i - 1]), Vector(P[i]), Vector(P[(i + 1) % len(P)])
            u, v = b - a, c - b
            if u.length < 1e-6 or v.length < 1e-6:
                P.pop(i); changed = True; break
            turn = math.degrees(u.angle(v))
            if turn < min_turn or v.length < min_edge * 0.5:
                P.pop(i); changed = True; break
    # symmetric about x = 0: average mirrored pairs (the hull is symmetric by construction)
    return [[round(x, 3), round(y, 3)] for x, y in P]


def main():
    out = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else os.path.join(HERE, '..', 'specs', 'shipyard-dd12.json')
    tmp = os.path.join(os.environ.get('YARD_SCRATCH', '/tmp/cqs-yard'), 'measure')
    F.reset()
    src = F.decode([(os.path.join(F.SCENE3D, 'assets', 'ships', 'destroyer.glb'), 'dd12')], tmp)['dd12']
    meshes, _ = F.import_glb(src)
    dg = bpy.context.evaluated_depsgraph_get()
    hull = next(o for o in meshes if o.name.startswith('hull'))
    # model-frame vertex arrays
    def verts(o):
        co = np.array([(o.matrix_world @ v.co)[:] for v in o.data.vertices])
        return np.stack([co[:, 0], co[:, 2], -co[:, 1]], 1)
    allv = np.concatenate([verts(o) for o in meshes])
    lo, hi = allv.min(0), allv.max(0)
    res = {'source': 'assets/ships/destroyer.glb', 'frame': 'destroyer GLB model frame (metres, bow +Z, dorsal +Y, port +X; glbship centres it on bbox.centre)',
           'bbox': {'min': lo.round(3).tolist(), 'max': hi.round(3).tolist(), 'centre': ((lo + hi) / 2).round(4).tolist()}}
    # bake the import transforms into the meshes, so BVH trees are in Blender world space
    for o in meshes:
        o.data.transform(o.matrix_world)
        o.matrix_world = o.matrix_world.Identity(4)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    bvh_all = [BVHTree.FromObject(o, dg) for o in meshes]
    bvh_hull = BVHTree.FromObject(hull, dg)
    hv = verts(hull)
    # ring-frame outlines: the hull's section envelope at z from rays cast inward in the section
    # plane (a bisect of the boolean-built hull drops points in recesses), cut to y <= top
    frames = []
    for st in D.FRAMES:
        z, top = st.get('src', st['z']), st['top']
        pts = []
        c = Vector((0.0, -18.0))
        for k in range(180):
            a = 2 * math.pi * k / 180
            d = Vector((math.cos(a), math.sin(a)))
            o2 = c + d * 80.0
            p, n, i, dist = bvh_hull.ray_cast(F.b_vec((o2.x, o2.y, z)), F.b_vec((-d.x, -d.y, 0)), 200)
            if p is not None:
                q = F.s_vec(p)
                pts.append((q.x, min(q.y, top)))
        pts += [(-x, y) for x, y in pts]          # symmetric by construction
        poly = simplify(hull2d(pts))
        frames.append({**st, 'outline': poly, 'ymin': round(min(p[1] for p in poly), 3), 'halfBeam': round(max(abs(p[0]) for p in poly), 3)})
        print('[measure] frame z %.1f: %d pts, beam %.1f, y %.1f..%.1f' % (z, len(poly), 2 * frames[-1]['halfBeam'], frames[-1]['ymin'], max(p[1] for p in poly)), flush=True)
    res['frames'] = frames
    # bottom: ray cast up from below
    def bottom(x, z):
        trees = bvh_all if z >= D.CUT['forward'] else [bvh_hull]
        best = None
        for t in trees:
            p, n, i, d = t.ray_cast(F.b_vec((x, -80, z)), F.b_vec((0, 1, 0)), 200)
            if p is not None:
                y = F.s_vec(p).y
                best = y if best is None else min(best, y)
        return best
    res['bottom'] = {}
    for key, xs in (('keel', [0.0]), ('bilge', [-D.BILGE_X, D.BILGE_X])):
        rows = []
        for z in D.BLOCK_Z[key]:
            ys = [bottom(x, z) for x in xs]
            rows.append([z, None if any(y is None for y in ys) else round(min(ys), 3)])
        res['bottom'][key] = rows
    # lowest kept geometry: forward of the cut every node; midships the hull below the plating cut
    fwd = allv[allv[:, 2] >= D.CUT['forward']]
    mid = hv[(hv[:, 2] >= D.CUT['aft']) & (hv[:, 2] < D.CUT['forward'])]
    res['keptMin'] = {'forward': round(float(fwd[:, 1].min()), 3), 'midships': round(float(mid[:, 1].min()), 3)}
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    json.dump(res, open(out, 'w'), indent=1)
    print('[measure] bbox', res['bbox'], 'keptMin', res['keptMin'])
    print('[measure] keel bottom', res['bottom']['keel'])
    print('[measure] bilge bottom', res['bottom']['bilge'])


if __name__ == '__main__':
    main()
