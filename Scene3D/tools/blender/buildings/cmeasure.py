"""Measure a colony component blueprint (an ingested fal / Tripo part in assets/parts-colony, already true size in the
part frame: metres, +Y up, footprint centre at the origin, front +Z) for its hard-surface remodel (README-colony.md,
"Component remodel").

    $PY tools/blender/buildings/cmeasure.py <part.glb | name> <outdir> [--axis x,z] [--step 0.5] [--res 0.1]
        [--compare remodel.glb]

Writes to <outdir>:
  ortho-front.png / ortho-left.png / ortho-top.png   ray-cast orthographic views (normal-shaded) on a 1 / 5 / 10 m
                                                     grid with part-frame labels: read volumes, bays, stations off them
  profile.json / profile.png    the radial profile r(y) about a vertical axis (default the bbox centre, or --axis x,z),
                                cast from the axis outward at 24 azimuths every --step m: median (the shell) and
                                min / max (frames, lugs) per station, plus the detected stations (steps in the median
                                radius > 0.25 m: flanges, bands, the bosh / shaft break)
  ledges.json                   horizontal-face area per 0.25 m of height (up-facing area peaks = platforms, decks,
                                eaves, roof breaks), the strongest peaks listed
With --compare, the remodel's silhouettes are drawn in red over the blueprint's (grey) and its profile over the
blueprint's: the check of the remodel against its blueprint.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import assemble_frame as F  # noqa: E402

SCENE3D = os.path.abspath(os.path.join(HERE, '..', '..', '..'))


def arg(flag, default=None, cast=str):
    if flag in sys.argv:
        i = sys.argv.index(flag)
        v = sys.argv[i + 1]
        del sys.argv[i:i + 2]
        return cast(v)
    return default


def font(sz):
    try:
        return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', sz)
    except OSError:
        return ImageFont.load_default()


def load(path, tmp):
    """-> (verts (n, 3) part frame, polys) of every mesh in the GLB."""
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    dec = F.decode([(path, 'm')], tmp)['m']
    ms, _ = F.import_glb(dec)
    V, P = [], []
    for o in ms:
        base = len(V)
        for v in o.data.vertices:
            V.append(tuple(F.s_vec(o.matrix_world @ v.co)))
        for p in o.data.polygons:
            P.append([base + i for i in p.vertices])
    return np.asarray(V, np.float64), P


def ortho(bvh, lo, hi, view, res):
    """(normal-shade image, hit mask, extents). view: front (from +Z), left (from +X), top (from +Y)."""
    if view == 'front':
        d, ax_u, ax_v = (0, 0, -1), 0, 1
    elif view == 'left':
        d, ax_u, ax_v = (-1, 0, 0), 2, 1
    else:
        d, ax_u, ax_v = (0, -1, 0), 0, 2
    u0, u1 = lo[ax_u] - 1, hi[ax_u] + 1
    v0, v1 = lo[ax_v] - 1, hi[ax_v] + 1
    W, H = int((u1 - u0) / res), int((v1 - v0) / res)
    img = np.full((H, W), 235, np.uint8)
    mask = np.zeros((H, W), bool)
    D = Vector(d)
    far = max(hi - lo) + 10
    for j in range(H):
        vv = v1 - (j + 0.5) * res if view != 'top' else v0 + (j + 0.5) * res
        for i in range(W):
            uu = u0 + (i + 0.5) * res
            if view == 'front':
                o = Vector((uu, vv, hi[2] + 5))
            elif view == 'left':
                o = Vector((hi[0] + 5, vv, uu))
            else:
                o = Vector((uu, hi[1] + 5, vv))
            hit, n, _, _ = bvh.ray_cast(o, D, far)
            if hit is not None:
                mask[j, i] = True
                s = abs(n.dot(-D)) * 0.75 + 0.15 * max(0, n.y)
                img[j, i] = int(40 + 180 * min(1, s))
    return img, mask, (u0, u1, v0, v1)


def grid(img, ext, res, title, labels, overlay=None):
    u0, u1, v0, v1 = ext
    im = Image.fromarray(img).convert('RGB')
    if overlay is not None:
        a = np.asarray(im).copy()
        bp, rm = overlay
        a[bp & ~rm] = (90, 140, 230)
        a[rm & ~bp] = (230, 70, 60)
        im = Image.fromarray(a)
    dr = ImageDraw.Draw(im)
    W, H = im.size
    f = font(12)
    for k in range(int(math.floor(u0)), int(math.ceil(u1)) + 1):
        x = (k - u0) / res
        c = (200, 60, 60) if k % 10 == 0 else ((150, 150, 210) if k % 5 == 0 else (215, 215, 222))
        if k % 5 == 0 or res <= 0.06:
            dr.line([(x, 0), (x, H)], fill=c, width=1)
        if k % 5 == 0:
            dr.text((x + 2, H - 14), str(k), fill=(30, 30, 30), font=f)
    for k in range(int(math.floor(v0)), int(math.ceil(v1)) + 1):
        y = (v1 - k) / res if 'top' not in title else (k - v0) / res
        c = (200, 60, 60) if k % 10 == 0 else ((150, 150, 210) if k % 5 == 0 else (215, 215, 222))
        if k % 5 == 0 or res <= 0.06:
            dr.line([(0, y), (W, y)], fill=c, width=1)
        if k % 5 == 0:
            dr.text((2, y - 14), str(k), fill=(30, 30, 30), font=f)
    dr.text((6, 4), f'{title}   {labels}   grid 1 / 5 / 10 m', fill=(0, 0, 0), font=font(15))
    return im


def profile(bvh, axis, lo, hi, step, n=24):
    """r(y): rays from the axis outward (the first shell hit from inside)."""
    ax, az = axis
    out = []
    y = lo[1] + step / 2
    while y < hi[1]:
        rs = []
        for k in range(n):
            a = 2 * math.pi * k / n
            d = Vector((math.sin(a), 0, math.cos(a)))
            hit, _, _, dist = bvh.ray_cast(Vector((ax, y, az)), d, 60.0)
            if hit is not None:
                rs.append(dist)
        if rs:
            r = np.asarray(rs)
            out.append({'y': round(y, 2), 'med': round(float(np.median(r)), 3), 'min': round(float(r.min()), 3),
                        'max': round(float(r.max()), 3), 'hits': len(rs)})
        y += step
    st = []
    for a, b in zip(out[:-1], out[1:]):
        if abs(b['med'] - a['med']) > 0.25:
            st.append({'y': round((a['y'] + b['y']) / 2, 2), 'from': a['med'], 'to': b['med']})
    return out, st


def draw_profile(prof, path, cmp=None):
    if not prof:
        return
    H = max(p['y'] for p in prof) + 2
    R = max(p['max'] for p in prof) + 2
    s = 900 / H
    im = Image.new('RGB', (int(R * s) + 80, 940), (245, 245, 245))
    dr = ImageDraw.Draw(im)
    for k in range(0, int(H) + 1):
        y = 920 - k * s
        dr.line([(40, y), (im.size[0], y)], fill=(225, 225, 230) if k % 5 else (180, 180, 210))
        if k % 5 == 0:
            dr.text((4, y - 7), str(k), fill=(0, 0, 0), font=font(11))
    for k in range(0, int(R) + 1):
        x = 40 + k * s
        dr.line([(x, 0), (x, 920)], fill=(225, 225, 230) if k % 5 else (180, 180, 210))
    for key, col in (('min', (170, 170, 170)), ('max', (170, 170, 170)), ('med', (30, 30, 30))):
        dr.line([(40 + p[key] * s, 920 - p['y'] * s) for p in prof], fill=col, width=2 if key == 'med' else 1)
    if cmp:
        dr.line([(40 + p['med'] * s, 920 - p['y'] * s) for p in cmp], fill=(220, 50, 40), width=2)
    im.save(path)


def ledges(V, P, lo, hi, step=0.25):
    nb = int((hi[1] - lo[1]) / step) + 1
    up = np.zeros(nb)
    for p in P:
        if len(p) < 3:
            continue
        a, b, c = V[p[0]], V[p[1]], V[p[2]]
        n = np.cross(b - a, c - a)
        area = 0.5 * np.linalg.norm(n)
        if area < 1e-9:
            continue
        if n[1] / (2 * area) > 0.85:
            y = (a[1] + b[1] + c[1]) / 3
            up[int((y - lo[1]) / step)] += area
    order = np.argsort(-up)[:20]
    return [{'y': round(lo[1] + (i + 0.5) * step, 2), 'm2': round(float(up[i]), 1)} for i in sorted(order) if up[i] > 0.5]


def main():
    axis = arg('--axis')
    step = arg('--step', 0.5, float)
    res = arg('--res', 0.1, float)
    cmp_path = arg('--compare')
    src, out = sys.argv[1], sys.argv[2]
    if not src.endswith('.glb'):
        src = os.path.join(SCENE3D, 'assets', 'parts-colony', f'{src}.glb')
    os.makedirs(out, exist_ok=True)
    tmp = os.path.join(out, '_tmp')
    V, P = load(src, tmp)
    lo, hi = Vector(V.min(0)), Vector(V.max(0))
    bvh = BVHTree.FromPolygons([Vector(v) for v in V], P)
    ax = [float(v) for v in axis.split(',')] if axis else [(lo.x + hi.x) / 2, (lo.z + hi.z) / 2]
    cmpd = None
    if cmp_path:
        V2, P2 = load(cmp_path, tmp)
        bvh2 = BVHTree.FromPolygons([Vector(v) for v in V2], P2)
        lo = Vector(np.minimum(V.min(0), V2.min(0))); hi = Vector(np.maximum(V.max(0), V2.max(0)))
        cmpd = bvh2
    rep = {'file': src, 'bbox': [list(lo), list(hi)], 'size': list(hi - lo), 'axis': ax}
    for view in ('front', 'left', 'top'):
        img, mask, ext = ortho(bvh, lo, hi, view, res)
        ov = None
        if cmpd:
            _, m2, _ = ortho(cmpd, lo, hi, view, res)
            ov = (mask, m2)
            inter, uni = (mask & m2).sum(), (mask | m2).sum()
            rep[f'iou_{view}'] = round(float(inter / max(uni, 1)), 3)
        lab = {'front': 'from +Z: x right? (-x left of image is -x), y up', 'left': 'from +X: z across, y up', 'top': 'from +Y: x across, z down'}[view]
        grid(img, ext, res, f'ortho-{view}', lab, ov).save(os.path.join(out, f'ortho-{view}.png'))
    prof, st = profile(bvh, ax, lo, hi, step)
    rep['stations'] = st
    cp = None
    if cmpd:
        cp, _ = profile(cmpd, ax, lo, hi, step)
    json.dump({'profile': prof, 'stations': st, 'compare': cp}, open(os.path.join(out, 'profile.json'), 'w'), indent=0)
    draw_profile(prof, os.path.join(out, 'profile.png'), cp)
    lg = ledges(V, P, lo, hi)
    json.dump(lg, open(os.path.join(out, 'ledges.json'), 'w'), indent=0)
    rep['ledges'] = lg
    json.dump(rep, open(os.path.join(out, 'measure.json'), 'w'), indent=1)
    print(json.dumps({k: v for k, v in rep.items() if k != 'ledges'}, indent=0))
    print('ledges', lg)


if __name__ == '__main__':
    main()
