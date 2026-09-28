"""Measure a blueprint mesh (a fal / Tripo hull) in the SHIP FRAME for a hard-surface remodel.

    <blender-python> tools/blender/hulls/measure.py <blueprint.glb> <outdir>
        [--rotate 0,-90,0] [--length 108.1] [--res 0.1] [--stations 2] [--extra z1,z2,...]
        [--compare model.glb]   (overlay a remodel's sections / silhouettes on the blueprint)

The blueprint is brought into the ship frame exactly as src/lib/glbship.js does (rotate ->
length -> centre; metres, bow +Z, dorsal +Y, port +X). Outputs in <outdir>:

  ortho-<view>.png   ray-cast orthographic renders (top, bottom, port, stbd, bow, stern) at --res
                     metres per pixel, shaded by the surface normal, with a 1 m / 5 m / 10 m grid
                     and ship-frame labels, so volumes can be read off in metres
  depth-<view>.npy   the matching depth maps (ship-frame coordinate of the first hit along the ray,
                     NaN where the ray misses) plus ortho.json (the pixel -> metre mapping)
  sections.json      bmesh-bisect cross-sections every --stations metres along Z (+ --extra), as
                     ship-frame polylines [[x, y], ...]
  sections.png       those sections drawn on a metre grid (one panel per station)
  zsec-*.json/png    the same for horizontal (Y) and longitudinal (X) cuts
With --compare, the model's sections are drawn in red over the blueprint's (grey), and
ortho-<view>-cmp.png shows the silhouette difference (blueprint only: blue, model only: red).
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import bpy  # noqa: E402
import bmesh  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import assemble_frame as F  # noqa: E402


def arg(flag, default=None, cast=str):
    if flag in sys.argv:
        i = sys.argv.index(flag)
        v = sys.argv[i + 1]
        del sys.argv[i:i + 2]
        return cast(v)
    return default


# view: (ray direction in ship frame, image-right axis, image-up axis)
VIEWS = {
    'top': ((0, -1, 0), (0, 0, 1), (1, 0, 0)),      # looking down, bow to the right, port up
    'bottom': ((0, 1, 0), (0, 0, 1), (-1, 0, 0)),   # looking up, bow right, starboard up
    'port': ((-1, 0, 0), (0, 0, -1), (0, 1, 0)),    # from port (+X): bow to the LEFT
    'stbd': ((1, 0, 0), (0, 0, 1), (0, 1, 0)),      # from starboard: bow to the right
    'bow': ((0, 0, -1), (-1, 0, 0), (0, 1, 0)),     # from ahead: port on the right? no: -X right = starboard right
    'stern': ((0, 0, 1), (1, 0, 0), (0, 1, 0)),     # from astern: port on the right
}


def font(sz):
    for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',):
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def bvh_of(obj):
    me = obj.data
    mw = obj.matrix_world
    verts = [F.s_vec(mw @ v.co) for v in me.vertices]
    polys = [tuple(p.vertices) for p in me.polygons]
    return BVHTree.FromPolygons(verts, polys, all_triangles=False), verts, polys


def ortho(bvh, lo, hi, view, res, pad=1.0):
    d, r, u = (np.array(a, float) for a in VIEWS[view])
    # extent along r and u
    corners = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
    rr = corners @ r; uu = corners @ u; dd = corners @ d
    r0, r1 = rr.min() - pad, rr.max() + pad
    u0, u1 = uu.min() - pad, uu.max() + pad
    start = dd.min() - 5
    W, H = int((r1 - r0) / res), int((u1 - u0) / res)
    depth = np.full((H, W), np.nan, np.float32)
    nrm = np.zeros((H, W, 3), np.float32)
    D = Vector(d)
    far = dd.max() - dd.min() + 10
    for j in range(H):
        uv = u1 - (j + 0.5) * res
        for i in range(W):
            rv = r0 + (i + 0.5) * res
            o = Vector(r * rv + u * uv + d * start)
            p, n, _i, dist = bvh.ray_cast(o, D, far)
            if p is not None:
                depth[j, i] = start + dist
                if n.dot(D) > 0:
                    n = -n
                nrm[j, i] = n
    return depth, nrm, dict(view=view, d=d.tolist(), r=r.tolist(), u=u.tolist(), r0=r0, u1=u1, res=res, W=W, H=H)


def shade(nrm, depth, view):
    d = np.array(VIEWS[view][0], float)
    # key light from over the viewer's left shoulder, plus a depth cue
    L = -d + np.array(VIEWS[view][2]) * 0.8 - np.array(VIEWS[view][1]) * 0.5
    L /= np.linalg.norm(L)
    lam = np.clip(nrm @ L, 0, 1)
    img = 0.18 + 0.72 * lam
    ok = ~np.isnan(depth)
    if ok.any():
        dn = (depth - np.nanmin(depth)) / max(1e-6, np.nanmax(depth) - np.nanmin(depth))
        img = img * (1 - 0.35 * np.nan_to_num(dn))
    img[~ok] = 0.97
    return img


def grid_image(gray, meta, title, overlay=None):
    H, W = gray.shape
    rgb = np.stack([gray] * 3, -1)
    if overlay is not None:
        rgb = overlay
    im = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8))
    dr = ImageDraw.Draw(im, 'RGBA')
    res, r0, u1 = meta['res'], meta['r0'], meta['u1']
    f = font(max(10, int(0.9 / res)))
    rs = np.array(meta['r']); us = np.array(meta['u'])
    rn = 'xyz'[int(np.argmax(np.abs(rs)))]; un = 'xyz'[int(np.argmax(np.abs(us)))]
    for k in range(int(math.floor(r0)), int(math.ceil(r0 + W * res)) + 1):
        x = (k - r0) / res
        a = 150 if k % 10 == 0 else (70 if k % 5 == 0 else 22)
        dr.line([(x, 0), (x, H)], fill=(0, 90, 200, a), width=1)
        if k % 5 == 0:
            dr.text((x + 2, 2), f'{rn}={k * (1 if rs.sum() > 0 else -1)}', fill=(0, 60, 160, 255), font=f)
    for k in range(int(math.floor(u1 - H * res)), int(math.ceil(u1)) + 1):
        y = (u1 - k) / res
        a = 150 if k % 10 == 0 else (70 if k % 5 == 0 else 22)
        dr.line([(0, y), (W, y)], fill=(200, 60, 0, a), width=1)
        if k % 5 == 0:
            dr.text((2, y + 1), f'{un}={k * (1 if us.sum() > 0 else -1)}', fill=(160, 40, 0, 255), font=f)
    dr.text((W - 12 * len(title), H - 30), title, fill=(0, 0, 0, 255), font=font(20))
    return im


def sections(obj, axis, values):
    """bmesh bisect cuts of obj (ship frame) at axis = value; returns {value: [[p, q], ...] segments}."""
    me = obj.data
    bm0 = bmesh.new()
    bm0.from_mesh(me)
    bm0.transform(obj.matrix_world)
    # to ship frame
    for v in bm0.verts:
        v.co = F.s_vec(v.co)
    out = {}
    ax = 'xyz'.index(axis)
    no = [0, 0, 0]; no[ax] = 1
    for val in values:
        bm = bm0.copy()
        co = [0, 0, 0]; co[ax] = val
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        res = bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-5, plane_co=co, plane_no=no)
        cut = [e for e in res['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
        segs = [[list(e.verts[0].co), list(e.verts[1].co)] for e in cut]
        out[val] = segs
        bm.free()
    bm0.free()
    return out


def draw_sections(secs, axis, path, cmp=None, cols=6, cell=520, span=None):
    """Panels of section segments on a metre grid (1 m faint, 5 m strong)."""
    keys = sorted(secs.keys(), reverse=(axis == 'z'))
    other = [a for a in 'xyz' if a != axis]
    ia, ib = 'xyz'.index(other[0]), 'xyz'.index(other[1])
    # z-cuts: x right (port on the right, seen from astern? keep x right), y up
    allp = [p for k in keys for s in secs[k] for p in s]
    if cmp:
        allp += [p for k in keys for s in cmp.get(k, []) for p in s]
    if not allp:
        return
    A = np.array(allp)
    amin, amax = A[:, ia].min() - 1, A[:, ia].max() + 1
    bmin, bmax = A[:, ib].min() - 1, A[:, ib].max() + 1
    if span:
        amin, amax, bmin, bmax = span
    sc = (cell - 20) / max(amax - amin, bmax - bmin)
    rows = int(math.ceil(len(keys) / cols))
    im = Image.new('RGB', (cols * cell, rows * cell), (250, 250, 250))
    dr = ImageDraw.Draw(im, 'RGBA')
    f = font(16)
    for n, k in enumerate(keys):
        ox, oy = (n % cols) * cell + 10, (n // cols) * cell + 10
        P = lambda p: (ox + (p[ia] - amin) * sc, oy + (bmax - p[ib]) * sc)
        for g in range(int(math.floor(amin)), int(math.ceil(amax)) + 1):
            x = ox + (g - amin) * sc
            dr.line([(x, oy), (x, oy + (bmax - bmin) * sc)], fill=(0, 80, 200, 90 if g % 5 == 0 else 22))
        for g in range(int(math.floor(bmin)), int(math.ceil(bmax)) + 1):
            y = oy + (bmax - g) * sc
            dr.line([(ox, y), (ox + (amax - amin) * sc, y)], fill=(200, 60, 0, 90 if g % 5 == 0 else 22))
        for s in secs[k]:
            dr.line([P(s[0]), P(s[1])], fill=(40, 40, 40, 255), width=2)
        if cmp:
            for s in cmp.get(k, []):
                dr.line([P(s[0]), P(s[1])], fill=(230, 20, 20, 220), width=2)
        dr.text((ox + 4, oy + 2), f'{axis} = {k:+.1f}   ({other[0]} right, {other[1]} up; grid 1 m)', fill=(0, 0, 0), font=f)
    im.save(path)


def load(path, rotate, length):
    tmp = os.path.join(OUT, '.tmp')
    hull, info = F.load_hull(path, rotate=rotate, length=length, tmpdir=tmp)
    return hull, info


if __name__ == '__main__':
    rotate = [float(v) for v in arg('--rotate', '0,-90,0').split(',')]
    length = arg('--length', 108.1, float)
    res = arg('--res', 0.1, float)
    step = arg('--stations', 2.0, float)
    extra = [float(v) for v in arg('--extra', '').split(',') if v]
    cmp_path = arg('--compare')
    views = arg('--views', 'top,bottom,port,stbd,bow,stern').split(',')
    skip_ortho = '--no-ortho' in sys.argv
    for fl in ('--no-ortho', '--no-sections'):
        if fl in sys.argv:
            sys.argv.remove(fl)
            if fl == '--no-sections':
                sys.argv.append(fl)
    src, OUT = sys.argv[1], sys.argv[2]
    os.makedirs(OUT, exist_ok=True)
    F.reset()
    hull, info = load(src, rotate, length)
    print('[measure] blueprint', json.dumps(info))
    model = None
    if cmp_path:
        # the model is already in the ship frame (rotate 0, its own length)
        mh, minfo = F.load_hull(cmp_path, rotate=[0, 0, 0], length=None, scale=1.0, tmpdir=os.path.join(OUT, '.tmp'))
        # load_hull re-centres on the bbox: a remodel in the ship frame is centred already
        model = mh
        print('[measure] model', json.dumps(minfo))
    lo, hi = F.vert_box(hull)
    bvh, _v, _p = bvh_of(hull)
    mbvh = bvh_of(model)[0] if model else None
    meta_all = {}
    if not skip_ortho:
        for v in views:
            depth, nrm, meta = ortho(bvh, lo, hi, v, res)
            np.save(os.path.join(OUT, f'depth-{v}.npy'), depth)
            meta_all[v] = meta
            g = shade(nrm, depth, v)
            grid_image(g, meta, f'blueprint {v} (ship frame, m)').save(os.path.join(OUT, f'ortho-{v}.png'))
            if mbvh:
                d2, n2, _m = ortho(mbvh, lo, hi, v, res)
                g2 = shade(n2, d2, v)
                a, b = ~np.isnan(depth), ~np.isnan(d2)
                ov = np.stack([g2] * 3, -1)
                ov[a & ~b] = [0.2, 0.45, 1.0]
                ov[b & ~a] = [1.0, 0.25, 0.2]
                grid_image(g2, meta, f'remodel {v}: blue = blueprint only, red = remodel only', overlay=ov).save(os.path.join(OUT, f'ortho-{v}-cmp.png'))
                # depth difference where both hit (m, + = remodel further along the ray)
                dd = np.where(a & b, d2 - depth, np.nan)
                np.save(os.path.join(OUT, f'ddiff-{v}.npy'), dd)
        json.dump(meta_all, open(os.path.join(OUT, 'ortho.json'), 'w'), indent=1)
    if '--no-sections' in sys.argv:
        sys.exit(0)
    zs = sorted(set([round(z, 2) for z in np.arange(math.floor(lo[2]) + 0.5, hi[2], step)] + extra))
    sz = sections(hull, 'z', zs)
    json.dump({str(k): v for k, v in sz.items()}, open(os.path.join(OUT, 'sections-z.json'), 'w'))
    cz = sections(model, 'z', zs) if model else None
    draw_sections(sz, 'z', os.path.join(OUT, 'sections-z.png'), cz)
    ys = [round(y, 2) for y in np.arange(math.floor(lo[1]) + 0.5, hi[1], 2.0)]
    sy = sections(hull, 'y', ys)
    json.dump({str(k): v for k, v in sy.items()}, open(os.path.join(OUT, 'sections-y.json'), 'w'))
    draw_sections(sy, 'y', os.path.join(OUT, 'sections-y.png'), sections(model, 'y', ys) if model else None, cols=4, cell=700)
    xs = [0.0, 3.0, 6.0, 9.0, 12.0, 14.5, 16.0, 22.0, 28.5, 33.0]
    sx = sections(hull, 'x', xs)
    json.dump({str(k): v for k, v in sx.items()}, open(os.path.join(OUT, 'sections-x.json'), 'w'))
    draw_sections(sx, 'x', os.path.join(OUT, 'sections-x.png'), sections(model, 'x', xs) if model else None, cols=2, cell=1100)
    print('[measure] done', OUT)
