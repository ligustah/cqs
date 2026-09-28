"""Drover-class civil transport CT-4 (cargo) / CT-7 (troops): clean hard-surface hull, rebuilt
from measurements of the fal / Tripo H3.1 blueprints (README.md in this folder: the method;
freighter_dims.py: every dimension). One parametric script for both ships: a common crew
module, collar, reactor block and engine section, and a variant mid-body.

    <blender-python> tools/blender/hulls/freighter.py <workdir> --variant cargo|troops
                     [--stage all|model|paint] [--bake] [--tex 4096] [--ao 2048] [--threads 4]

Stages: model -> <workdir>/<name>-hull.blend and maps.npz (baked position / normal / zone / AO /
curvature; the AO sees the container stacks too); paint -> base / orm / normal.png
(freighter_paint.py over paint.py) and <workdir>/<name>-hull.glb (node 'hull', ship frame).
Kit parts: freighter_spec.py -> specs/<name>-v3.json (assemble.py); containers and the
low-poly port lites: freighter_extras.py.
"""
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402
import bmesh  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import common as K  # noqa: E402
from common import V, Z, Volume  # noqa: E402
import freighter_dims as D  # noqa: E402

SEC_ZONES = ['paint', 'paint', 'paint', 'deck', 'paint', 'belly', 'belly']  # cm_half segments (roof, shoulder, upper tier, ledge, flank, lower chamfer, keel)


def ring_zones(seg):
    n = len(seg)
    return [seg[j] if j < n else seg[2 * n - 1 - j] for j in range(2 * n)]


def oct_xy(hx, yb, yt, ch, z, d=0.0):
    p = K.chamfer_rect(0.0, (yb + yt) / 2, 2 * hx, yt - yb, ch)
    if d:
        p = K.offset_poly(p, d)
    return [V((x, y, z)) for x, y in p]


def box(vol, lo, hi, zone='paint', R=None):
    c = [(a + b) / 2 for a, b in zip(lo, hi)]
    s = [abs(b - a) for a, b in zip(lo, hi)]
    return K.box(vol.bm, c, s, R=R, zone=Z[zone])


def beam(bm, p0, p1, w, h=None, zone='metal', up=(0, 1, 0)):
    """Square / rectangular member from p0 to p1 (w across, h in the `up` direction)."""
    h = h or w
    p0, p1 = V(p0), V(p1)
    ax = (p1 - p0)
    L = ax.length
    ax.normalize()
    u = V(up) - ax * V(up).dot(ax)
    if u.length < 1e-4:
        u = V((1, 0, 0)) - ax * ax.x
    u.normalize()
    r = u.cross(ax)
    R = Matrix((r, u, ax)).transposed()
    return K.box(bm, (p0 + p1) / 2, (w, h, L), R=R, zone=Z[zone])


def band_loft(bm, ring_fn, a, b, d_out, d_in=-0.4, zone='trim'):
    """A proud band as a closed ring-shaped solid (no big caps buried in the hull): ring_fn(t, d)
    gives the outline at station t offset by d."""
    rings = [ring_fn(a, d_in), ring_fn(a, d_out), ring_fn(b, d_out), ring_fn(b, d_in), ring_fn(a, d_in)]
    return K.loft(bm, rings, cap0=False, cap1=False, zone=Z[zone])


def band_cyl(bm, c, axis, r_in, r_out, t0, t1, n=48, zone='trim'):
    prof = [(r_in, t0), (r_out, t0), (r_out, t1), (r_in, t1), (r_in, t0)]
    return K.lathe(bm, c, axis, prof, n=n, zone=Z[zone], cap0=False, cap1=False)


# ------------------------------------------------------------------------------------------
# crew module (bow): loft of the measured half sections, recessed bow plate, glazing band
# ------------------------------------------------------------------------------------------
def cm_ring(v, u, d=0.0):
    pts = K.mirror_half(D.cm_half(u, v['CM_LEN']))
    if d:
        pts = K.offset_poly(pts, d)
    return [V((x, y, v['CM0'] + u)) for x, y in pts]


def crew_module(v):
    vol = Volume('crew_module', bevel=0.10)
    L = v['CM_LEN']
    us = [0.0, 0.5, D.CM['taper'], D.CM['taper'] + 2.0, D.CM['taper'] + 4.0, D.CM['taper'] + 6.0, D.CM['taper'] + 8.0, D.CM['taper'] + 10.0, L - 0.3, L]
    us = sorted(set(u for u in us if u <= L))
    rings = [cm_ring(v, u) for u in us]
    # bow plate: lip, inset, recessed 0.35
    face = K.mirror_half(D.cm_half(L, L))
    inner = K.offset_poly(face, -0.5)
    rings += [[V((x, y, v['BOW'])) for x, y in inner], [V((x, y, v['BOW'] - 0.35)) for x, y in inner]]
    # aft bulkhead: inset ring, recessed plate
    aft_in = K.offset_poly(K.mirror_half(D.cm_half(0, L)), -0.45)
    rings = [[V((x, y, v['CM0'] - 0.0)) for x, y in aft_in]] + rings
    grid, caps = K.loft(vol.bm, rings, zone=Z['paint'])
    zones = ring_zones(SEC_ZONES)
    for k, row in enumerate(grid):
        for j, f in enumerate(row):
            if f is None:
                continue
            if 1 <= k < len(rings) - 3:
                f.material_index = Z[zones[j]]
            else:
                f.material_index = Z['trim']
    for f in caps:
        f.material_index = Z['trim']
    K.solid(vol.bm)
    # bridge glazing band round the tapered bow and the bow face (0.6 m deep recess)
    y0, y1, depth = 0.9, 2.5, 0.6
    half = []
    for u in (D.CM['taper'] + 1.0, D.CM['taper'] + 4.0, D.CM['taper'] + 7.0, L - 0.6):
        half.append((D.cm_half(u, L)[4][0], v['CM0'] + u))
    half.append((D.cm_half(L, L)[4][0] - 0.6, v['BOW']))
    half.append((0.0, v['BOW']))
    line = half + [(-x, z) for x, z in reversed(half[:-1])]
    inner_l = K.offset_open(line, depth, left=True)
    outer_l = K.offset_open(line, 3.0, left=False)
    K.prism(vol.cutters, outer_l + list(reversed(inner_l)), 'xz', y0, y1, zone=Z['recess'])
    # second, lower window band on the bow face (observation deck under the bridge)
    K.box(vol.cutters, (0, -1.6, v['BOW']), (6.4, 1.6, 1.4), zone=Z['recess'])
    # grille recess low on the bow plate, louvres after the cut
    zb = v['BOW'] - 0.35
    K.box(vol.cutters, (0, -5.6, zb), (8.2, 2.4, 0.9), zone=Z['dark'])
    vol.adds.append(('louvres', lambda bm: [K.box(bm, (0, y, zb - 0.28), (8.1, 0.09, 0.5), R=Matrix.Rotation(math.radians(35), 3, 'X'), zone=Z['fin'])
                                           for y in np.arange(-6.55, -4.5, 0.32)]))
    # crew door bays on the flank, lowest deck (kit door in each; design: 0.25 m margin)
    for sx in (1, -1):
        for u in door_us(v):
            c = V((sx * D.CM['fx'], door_y(), v['CM0'] + u))
            K.oriented_prism(vol.cutters, K.chamfer_rect(0, 0, 1.95, 2.95, 0.12), c, (sx, 0, 0), (0, 1, 0), -0.32, 1.5, zone=Z['recess'])
        # service bay (louvred) on the lower flank aft
        c = V((sx * D.CM['fx'], -4.4 + 0.2, v['CM0'] + 10.5))
        K.oriented_prism(vol.cutters, K.chamfer_rect(0, 0, 4.2, 1.6, 0.15), c, (sx, 0, 0), (0, 1, 0), -0.3, 1.5, zone=Z['recess'])
        xs = sx * (D.CM['fx'] - 0.16)
        vol.adds.append(('louvres', lambda bm, xs=xs: [K.box(bm, (xs, -4.2, v['CM0'] + 10.5 + dz), (0.24, 1.45, 0.08), R=Matrix.Rotation(math.radians(30 * (1 if xs > 0 else -1)), 3, 'Y'), zone=Z['fin'])
                                                     for dz in np.arange(-1.85, 1.9, 0.3)]))
    K.solid(vol.cutters)
    return vol


def door_us(v):
    return (4.6, 17.2)


def door_y():
    return D.DECKS[0] + 1.6


def cm_details(v):
    """Frame bands, rub strakes, roof deck and equipment, bow bumpers."""
    vols = []
    L = v['CM_LEN']
    fb = Volume('cm_frames', bevel=0.05)
    fb.occluder = False
    for u0, u1 in ((0.6, 1.3), (D.CM['taper'] - 0.35, D.CM['taper'] + 0.35)):
        band_loft(fb.bm, lambda u, d: cm_ring(v, u, d), u0, u1, 0.14)
    # rub strakes along the constant section: at the lower flank (fender) and the deck line
    for sx in (1, -1):
        for y, hh in ((-10.45, 0.25), (1.45, 0.32)):
            # the deck-line strake breaks for the flank ladder (u 6.4)
            spans = [(1.4, 20.6)] if y < 0 else [(1.4, 5.7), (7.1, 20.6)]
            for u0, u1 in spans:
                K.box(fb.bm, (sx * (D.CM['fx'] + 0.1), y, v['CM0'] + (u0 + u1) / 2), (0.28, hh, u1 - u0), zone=Z['trim'])
    K.solid(fb.bm)
    vols.append(fb)
    # roof deck: raised plate with chamfers, hatches, equipment boxes (concept: roof clutter)
    rd = Volume('cm_roof', bevel=0.06)
    top = D.CM['top']
    K.stack(rd.bm, [(K.chamfer_rect(0, v['CM0'] + 12.0, 9.0, 13.0, 0.9), top - 0.3), (K.chamfer_rect(0, v['CM0'] + 12.0, 9.0, 13.0, 0.9), top + 0.45),
                    (K.chamfer_rect(0, v['CM0'] + 12.0, 8.4, 12.4, 0.7), top + 0.7)], 'xz', zone=Z['deck'])
    # hatches (raised plates) and equipment
    for x, u, w, h in ((2.3, 8.2, 2.2, 2.2), (-2.3, 8.2, 2.2, 2.2), (0.0, 15.8, 3.0, 2.0)):
        K.plate(rd.bm, (x, top + 0.7, v['CM0'] + u), (0, 1, 0), (0, 0, 1), w, h, 0.14, ch=0.05, back=0.2, zone=Z['deck'])
    K.plate(rd.bm, (-5.6, top, v['CM0'] + 3.5), (0, 1, 0), (0, 0, 1), 1.8, 2.6, 1.3, ch=0.07, back=0.2, zone=Z['metal'])
    K.plate(rd.bm, (5.4, top, v['CM0'] + 3.2), (0, 1, 0), (0, 0, 1), 1.4, 1.6, 0.9, ch=0.06, back=0.2, zone=Z['foil'])
    K.plate(rd.bm, (4.2, top, v['CM0'] + 21.0), (0, 1, 0), (0, 0, 1), 2.0, 1.2, 0.8, ch=0.06, back=0.2, zone=Z['metal'])
    # antenna / dome plinths
    K.cyl(rd.bm, (-3.0, top - 0.2, v['CM0'] + 20.4), (-3.0, top + 0.9, v['CM0'] + 20.4), 1.2, n=24, zone=Z['paint'])
    K.solid(rd.bm)
    vols.append(rd)
    # equipment on the sloped bow roof (the brow over the bridge): hatch, vent housings, sensor box
    L = v['CM_LEN']
    br = Volume('cm_bow_roof', bevel=0.05)
    def roof_at(u):
        t0, t1 = D.cm_half(u - 0.5, L)[0][1], D.cm_half(u + 0.5, L)[0][1]
        return (t0 + t1) / 2, V((0, 1, -(t1 - t0))).normalized()
    for x, u, w, h, t, zone in ((0.0, D.CM['taper'] + 2.6, 2.6, 2.2, 0.14, 'deck'), (2.1, D.CM['taper'] + 6.2, 1.1, 2.4, 0.35, 'dark'), (-2.1, D.CM['taper'] + 6.2, 1.1, 2.4, 0.35, 'dark'),
                                (0.0, D.CM['taper'] + 8.4, 1.8, 1.3, 0.7, 'metal')):
        y, n = roof_at(u)
        K.plate(br.bm, (x, y, v['CM0'] + u), n, (0, 0, 1), w, h, t, ch=0.04, back=0.3, zone=Z[zone])
    K.solid(br.bm)
    vols.append(br)
    # bow bumpers at the lower bow corners and a chin plate
    bb = Volume('cm_bumpers', bevel=0.08)
    zf = v['BOW'] - 0.02
    for sx in (1, -1):
        K.stack(bb.bm, [(K.chamfer_rect(sx * 4.3, zf - 1.6, 2.6, 3.2, 0.5), -9.9), (K.chamfer_rect(sx * 4.3, zf - 1.6, 2.6, 3.2, 0.5), -7.4),
                        (K.chamfer_rect(sx * 4.3, zf - 1.9, 2.3, 2.6, 0.4), -7.0)], 'xz', zone=Z['trim'])
    K.solid(bb.bm)
    vols.append(bb)
    return vols


# ------------------------------------------------------------------------------------------
# collar: docking block between the crew module and the payload (airlocks, docking tubes, cab)
# ------------------------------------------------------------------------------------------
COL = {'x': 11.0, 'yb': -11.5, 'yt': 7.6, 'ch': 2.2}


def collar(v):
    vols = []
    z0, z1 = v['COL1'], v['CM0']
    c = Volume('collar', bevel=0.09)
    rings = [oct_xy(COL['x'], COL['yb'], COL['yt'], COL['ch'], z0, -0.5), oct_xy(COL['x'], COL['yb'], COL['yt'], COL['ch'], z0 + 0.0),
             oct_xy(COL['x'], COL['yb'], COL['yt'], COL['ch'], z1 + 0.3)]
    grid, caps = K.loft(c.bm, rings, zone=Z['paint'])
    for f in grid[0]:
        if f:
            f.material_index = Z['trim']
    for f in caps:
        f.material_index = Z['trim']
    K.solid(c.bm)
    zm = (z0 + z1) / 2
    for sx in (1, -1):
        cc = V((sx * COL['x'], -2.2, zm))
        K.oriented_prism(c.cutters, K.chamfer_rect(0, 0, 3.05, 3.85, 0.2), cc, (sx, 0, 0), (0, 1, 0), -0.4, 1.5, zone=Z['recess'])
    K.solid(c.cutters)
    vols.append(c)
    # docking tubes at the lower corners (blueprint: r 1.9 rings at x +-12.4, y -8.4)
    t = Volume('dock_tubes', bevel=0.05)
    for sx in (1, -1):
        cx, cy = sx * 12.3, -8.4
        K.lathe(t.bm, (cx, cy, z0 - 0.6), (0, 0, 1), [(1.5, 0.0), (2.15, 0.0), (2.15, 0.55), (1.85, 0.7), (1.85, z1 - z0 + 0.3)], n=32, zone=Z['paint'], cap0=False)
        K.cyl(t.cutters, (cx, cy, z0 - 1.0), (cx, cy, z0 + 0.2), 1.5, n=32, zone=Z['dark'])
    K.solid(t.bm)
    K.solid(t.cutters)
    vols.append(t)
    # cargo-control cab on the collar roof: glazing leans aft over the payload
    cab = Volume('collar_cab', bevel=0.07)
    zc = z1 - 0.1
    lv = [(K.chamfer_rect(0, (z0 + 0.6 + zc) / 2, 9.2, zc - z0 - 0.6, 0.5), COL['yt'] - 0.4), (K.chamfer_rect(0, (z0 + 0.6 + zc) / 2, 9.2, zc - z0 - 0.6, 0.5), COL['yt'] + 0.6),
          (K.chamfer_rect(0, (z0 + 2.0 + zc) / 2, 8.2, zc - z0 - 2.0, 0.4), COL['yt'] + 2.6), (K.chamfer_rect(0, (z0 + 2.2 + zc) / 2, 7.6, zc - z0 - 2.2, 0.35), COL['yt'] + 2.85)]
    K.stack(cab.bm, lv, 'xz', zone=Z['paint'])
    K.solid(cab.bm)
    vols.append(cab)
    return vols


def cab_glazing(v):
    """(centre, normal, up) of the cab's sloped aft face, for the kit panes."""
    z0 = v['COL1']
    a, b = V((0, COL['yt'] + 0.6, z0 + 0.6)), V((0, COL['yt'] + 2.6, z0 + 2.0))
    up = (b - a).normalized()
    n = V((0, -up.z, up.y))  # faces aft and up
    if n.z > 0:
        n = -n
    return (a + b) / 2, n, up


# ------------------------------------------------------------------------------------------
# reactor block
# ------------------------------------------------------------------------------------------
def reactor(v):
    vols = []
    r = Volume('reactor', bevel=0.10)
    X, YB, YT, CH = v['RX'], v['RYB'], v['RYT'], v['RCH']
    z0, z1 = v['R1'], v['R0']
    rings = [oct_xy(X, YB, YT, CH, z0, -0.6), oct_xy(X, YB, YT, CH, z0 + 0.0), oct_xy(X, YB, YT, CH, z1), oct_xy(X, YB, YT, CH, z1, -0.6)]
    grid, caps = K.loft(r.bm, rings, zone=Z['paint'])
    for k in (0, 2):
        for f in grid[k]:
            if f:
                f.material_index = Z['trim']
    for f in caps:
        f.material_index = Z['trim']
    K.solid(r.bm)
    zm = (z0 + z1) / 2
    for sx in (1, -1):
        # crew door bay (flank, lower) and two louvred maintenance bays
        c = V((sx * X, YB + 3.4 + 1.2, z1 - 2.2))
        K.oriented_prism(r.cutters, K.chamfer_rect(0, 0, 1.95, 2.95, 0.12), c, (sx, 0, 0), (0, 1, 0), -0.32, 1.5, zone=Z['recess'])
        for zb in (zm - 1.6,):
            c = V((sx * X, YB + CH + 1.4, zb))
            K.oriented_prism(r.cutters, K.chamfer_rect(0, 0, 4.6, 1.8, 0.15), c, (sx, 0, 0), (0, 1, 0), -0.3, 1.5, zone=Z['recess'])
            xs = sx * (X - 0.16)
            r.adds.append(('louvres', lambda bm, xs=xs, zb=zb: [K.box(bm, (xs, YB + CH + 1.4, zb + dz), (0.24, 1.6, 0.08), R=Matrix.Rotation(math.radians(30 * (1 if xs > 0 else -1)), 3, 'Y'), zone=Z['fin'])
                                                                for dz in np.arange(-2.05, 2.1, 0.3)]))
    K.solid(r.cutters)
    vols.append(r)
    # frame bands proud of the block, a raised hatch, the mast housing
    fb = Volume('reactor_frames', bevel=0.05)
    fb.occluder = False
    for za in (z0 + 0.6, z1 - 0.6):
        band_loft(fb.bm, lambda z, d: oct_xy(X, YB, YT, CH, z, d), za - 0.3, za + 0.3, 0.14)
    K.solid(fb.bm)
    vols.append(fb)
    m = Volume('mast', bevel=0.06)
    mz = v['MAST_Z']
    K.stack(m.bm, [(K.chamfer_rect(0, mz, 4.2, 3.6, 0.5), YT - 0.3), (K.chamfer_rect(0, mz, 4.2, 3.6, 0.5), YT + 1.0), (K.chamfer_rect(0, mz, 3.4, 2.8, 0.4), YT + 1.35)], 'xz', zone=Z['paint'])
    K.plate(m.bm, (0, YT, zm - 3.4 if v['variant'] == 'cargo' else zm + 2.6), (0, 1, 0), (0, 0, 1), 5.0, 2.4, 0.16, ch=0.06, back=0.2, zone=Z['deck'])
    K.plate(m.bm, (-4.6, YT, mz + 0.4), (0, 1, 0), (0, 0, 1), 1.6, 2.2, 1.1, ch=0.06, back=0.2, zone=Z['foil'])
    K.plate(m.bm, (4.8, YT, mz - 0.6), (0, 1, 0), (0, 0, 1), 1.8, 1.4, 0.8, ch=0.06, back=0.2, zone=Z['metal'])
    K.solid(m.bm)
    vols.append(m)
    return vols


# ------------------------------------------------------------------------------------------
# engine section: housings with bell-mount rings, tanks, keel and dorsal blocks, plumbing
# ------------------------------------------------------------------------------------------
def engines(v):
    vols = []
    b = v['BELL']
    z0 = v['R1'] + 0.3
    zb = b['back']
    Rh, Rr = v['HOUS_R'], v['HOUS_RING']
    h = Volume('housings', bevel=0.07)
    for sx in (1, -1):
        c = (sx * b['x'], b['y'], z0)
        Lh = z0 - zb
        prof = [(Rh, 0.0), (Rh, Lh - 2.4), (Rr, Lh - 0.9), (Rr, Lh - 0.35), (Rr - 0.25, Lh)]
        K.lathe(h.bm, c, (0, 0, -1), prof, n=48, zone=Z['paint'])
    K.solid(h.bm)
    vols.append(h)
    # collars round each housing (proud bands) and the bell-mount flange ring
    hc = Volume('housing_collars', bevel=0.04)
    hc.occluder = False
    for sx in (1, -1):
        for zc in np.arange(z0 - 3.0, zb + 3.0, -4.5):
            band_cyl(hc.bm, (sx * b['x'], b['y'], zc), (0, 0, -1), Rh - 0.4, Rh + 0.14, 0.0, 0.5, n=40)
    K.solid(hc.bm)
    vols.append(hc)
    # tanks: upper outboard pair and lower pair, domed ends
    tk = Volume('tanks', bevel=0.05)
    for key, zz in (('UTANK', (z0 - 1.2, zb - 1.6)), ('LTANK', (z0 - 0.4, zb - 3.2))):
        t = v[key]
        L = zz[0] - zz[1]
        r = t['r']
        prof = [(r * 0.35, 0.0), (r * 0.75, 0.25 * r), (r * 0.95, 0.6 * r), (r, 0.95 * r), (r, L - 0.95 * r), (r * 0.95, L - 0.6 * r), (r * 0.75, L - 0.25 * r), (r * 0.35, L)]
        for sx in (1, -1):
            K.lathe(tk.bm, (sx * t['x'], t['y'], zz[0]), (0, 0, -1), prof, n=36, zone=Z['paint'])
    K.solid(tk.bm)
    vols.append(tk)
    tb = Volume('tank_bands', bevel=0.03)
    tb.occluder = False
    for key, zz in (('UTANK', (z0 - 1.2, zb - 1.6)), ('LTANK', (z0 - 0.4, zb - 3.2))):
        t = v[key]
        L = zz[0] - zz[1]
        for sx in (1, -1):
            for f in (0.34, 0.66):
                zc = zz[0] - L * f
                band_cyl(tb.bm, (sx * t['x'], t['y'], zc + 0.2), (0, 0, -1), t['r'] - 0.3, t['r'] + 0.1, 0.0, 0.4, n=28)
    K.solid(tb.bm)
    vols.append(tb)
    # keel block between the lower tanks and the dorsal block between the housings
    kb = Volume('keel_block', bevel=0.08)
    kx = 5.2 if v['variant'] == 'cargo' else 5.8
    K.stack(kb.bm, [(K.chamfer_rect(0, -8.8, 2 * kx, 8.0, 1.2), z0), (K.chamfer_rect(0, -8.8, 2 * kx, 8.0, 1.2), zb - 1.5), (K.chamfer_rect(0, -8.3, 2 * kx - 2.0, 6.0, 0.8), zb - 3.2)], 'xy', zone=Z['paint'])
    K.solid(kb.bm)
    vols.append(kb)
    db = Volume('dorsal_block', bevel=0.07)
    top = v['RYT'] - 4.6
    K.stack(db.bm, [(K.chamfer_rect(0, (top + b['y']) / 2, 5.6, top - b['y'], 0.8), z0), (K.chamfer_rect(0, (top + b['y']) / 2, 5.6, top - b['y'], 0.8), zb + 1.2),
                    (K.chamfer_rect(0, (top + b['y']) / 2 - 0.6, 4.4, top - b['y'] - 1.2, 0.6), zb + 0.2)], 'xy', zone=Z['paint'])
    K.solid(db.bm)
    vols.append(db)
    # plumbing: feed pipes from the tanks into the housings, a pipe bundle on the dorsal block
    pp = Volume('pipes', bevel=0.02)
    for sx in (1, -1):
        ut, lt = v['UTANK'], v['LTANK']
        for zz in (z0 - 6.0, zb + 5.0):
            K.cyl(pp.bm, (sx * ut['x'], ut['y'], zz), (sx * (b['x'] + Rh * 0.6), b['y'] + Rh * 0.6, zz), 0.32, n=12, zone=Z['metal'])
            K.cyl(pp.bm, (sx * lt['x'], lt['y'], zz - 1.5), (sx * (b['x'] + Rh * 0.3), b['y'] - Rh * 0.85, zz - 1.5), 0.36, n=12, zone=Z['metal'])
        for k, (dx, dy, rr) in enumerate(((1.6, top + 0.3, 0.28), (2.3, top + 0.25, 0.2))):
            K.cyl(pp.bm, (sx * dx, dy, z0), (sx * dx, dy, zb + 1.0), rr, n=12, zone=Z['metal'])
    K.solid(pp.bm)
    vols.append(pp)
    return vols


# ------------------------------------------------------------------------------------------
# radiators on pylons
# ------------------------------------------------------------------------------------------
def radiators(v):
    vols = []
    R = v['RAD']
    x0, x1 = R['x0'], v['HX']
    y0, y1 = R['y0'], R['y1']
    zs = (R['z1'], (R['z0'] + R['z1']) / 2 + 0.3), ((R['z0'] + R['z1']) / 2 - 0.3, R['z0'])
    for sx in (1, -1):
        for pi, (za, zb) in enumerate(zs):
            p = Volume(f'radiator_{"p" if sx > 0 else "s"}{pi}', bevel=0.06)
            xa, xb = min(sx * x0, sx * x1), max(sx * x0, sx * x1)
            K.box(p.bm, ((xa + xb) / 2, (y0 + y1) / 2, (za + zb) / 2), (xb - xa, y1 - y0, za - zb), zone=Z['paint'])
            K.solid(p.bm)
            # fin bays on both big faces (outer and inner), 0.9 m deep; fins added after the cut
            zc = (R['z0'] + R['z1']) / 2
            for face, dirn, bz0, bz1 in ((x1, 1, zb + 0.6, za - 0.6), (x0, -1, (zb + 2.6) if pi == 0 else (zb + 0.6), za - 0.6 if pi == 0 else za - 2.6)):
                fx = sx * face
                n = (sx * dirn, 0, 0)
                c = V((fx, (y0 + y1) / 2, (bz0 + bz1) / 2))
                K.oriented_prism(p.cutters, K.chamfer_rect(0, 0, bz1 - bz0, (y1 - y0) - 1.2, 0.2), c, n, (0, 1, 0), -0.7 if dirn < 0 else -0.9, 1.0, zone=Z['dark'])
                d = 0.7 if dirn < 0 else 0.9
                xf = fx - sx * dirn * (d / 2 + 0.02)
                p.adds.append(('fins', lambda bm, xf=xf, bz0=bz0, bz1=bz1, d=d: [K.box(bm, (xf, (y0 + y1) / 2, z), (d, (y1 - y0) - 1.3, 0.07), zone=Z['fin'])
                                                                                 for z in np.arange(bz0 + 0.15, bz1 - 0.05, 0.34)]))
            K.solid(p.cutters)
            vols.append(p)
    # pylons: a box truss from the engine section out to each radiator's inner face (between the
    # two panels), and two slim struts
    py = Volume('pylons', bevel=0.05)
    zc = (R['z0'] + R['z1']) / 2
    ut = v['UTANK']
    xin = ut['x'] - 0.5
    for sx in (1, -1):
        for y in (-4.6, 0.4):
            for z in (zc + 1.6, zc - 1.6):
                beam(py.bm, (sx * (xin - 1.0), y, z), (sx * (x0 + 0.3), y, z), 0.8, zone='paint')
        for z in (zc + 1.6, zc - 1.6):
            for k in range(3):
                xa = xin + (x0 - xin) * k / 3
                xb2 = xin + (x0 - xin) * (k + 1) / 3
                ya, yb = (-4.6, 0.4) if k % 2 == 0 else (0.4, -4.6)
                beam(py.bm, (sx * xa, ya, z), (sx * xb2, yb, z), 0.35, zone='metal')
        beam(py.bm, (sx * (xin - 1.0), -2.1, zc + 1.6), (sx * (xin - 1.0), -2.1, zc - 1.6), 1.2, 5.8, zone='paint')
        # radiator root plates on the inner face (hinge blocks)
        K.box(py.bm, (sx * (x0 + 0.2), -2.1, zc), (0.8, 6.4, 4.4), zone=Z['trim'])
        for z in (R['z1'] - 3.0, R['z0'] + 3.0):
            beam(py.bm, (sx * (ut['x'] + 1.2), ut['y'] - 1.4, z if abs(z) < abs(v['BELL']['back']) - 0.5 else z), (sx * (x0 + 0.2), y1 - 1.2, z), 0.35, zone='metal')
    K.solid(py.bm)
    py.cull = False
    py.uvb = True
    vols.append(py)
    return vols


# ------------------------------------------------------------------------------------------
# landing legs (pads set the envelope bottom)
# ------------------------------------------------------------------------------------------
def legs(v):
    vol = Volume('legs', bevel=0.05)
    bm = vol.bm
    yb = -v['HY']
    specs = [(v['LEG_F']['x'], v['LEG_F']['z'], D.CM['bot'] + 0.4, 2.8)]
    for sx in (1, -1):
        specs.append((sx * v['LEG_A']['x'], v['LEG_A']['z'], v['LTANK']['y'] - v['LTANK']['r'] * 0.6, 4.2))
    for x, z, ytop, hw in specs:
        # hip housing, upper strut, lower stage, two knee actuators, foot pad on a pivot block
        K.box(bm, (x, ytop - 0.8, z), (hw, 1.6, 3.2), zone=Z['trim'])
        a, b = yb + 2.6, ytop - 1.5
        K.box(bm, (x, (a + b) / 2, z), (1.3, b - a, 1.5), zone=Z['metal'])
        K.box(bm, (x, yb + 1.85, z), (1.0, 2.1, 1.15), zone=Z['metal'])
        K.box(bm, (x, yb + 1.05, z), (1.6, 0.6, 1.6), zone=Z['dark'])
        beam(bm, (x, ytop - 1.2, z + 1.35), (x, yb + 2.5, z + 0.35), 0.4, zone='metal', up=(1, 0, 0))
        beam(bm, (x, ytop - 1.2, z - 1.35), (x, yb + 2.5, z - 0.35), 0.4, zone='metal', up=(1, 0, 0))
        K.stack(bm, [(K.chamfer_rect(x, z, 3.6, 4.2, 0.5), yb), (K.chamfer_rect(x, z, 3.6, 4.2, 0.5), yb + 0.45), (K.chamfer_rect(x, z, 2.8, 3.2, 0.4), yb + 0.8)], 'xz', zone=Z['dark'])
    K.solid(bm)
    vol.cull = False
    return vol


# ------------------------------------------------------------------------------------------
# mid-body: cargo girder + container cell guides / troop habitats, girders, spine tube
# ------------------------------------------------------------------------------------------
def web_stations(v):
    """Girder web verticals: bay boundaries (cargo) or ring stations (troops)."""
    if v['variant'] == 'cargo':
        bs = D.bays(v)
        zs = [bs[0][0] + D.BAY_POST / 2] + [(bs[i][1] + bs[i + 1][0]) / 2 for i in range(len(bs) - 1)] + [bs[-1][1] - D.BAY_POST / 2]
        return zs
    z0, z1 = v['PAY0'] + 0.5, v['PAY1'] - 0.5
    n = int(round((z1 - z0) / 4.6))
    return [z1 - i * (z1 - z0) / n for i in range(n + 1)]


def girder(v, x_in, x_out, ytop, ybot, chord_h, name, deck=None):
    """A pair of side girders: flat chord boxes (x_in..x_out) top and bottom, Warren webs in the
    outer and inner planes, verticals at the web stations."""
    ch = Volume(name + '_chords', bevel=0.05)
    vol = Volume(name, bevel=0.0)
    bm = vol.bm
    za, zb = v['PAY1'] + 0.2, v['PAY0'] - 0.2
    zs = web_stations(v)
    for sx in (1, -1):
        xa, xb = sx * x_in, sx * x_out
        cx = (xa + xb) / 2
        wx = abs(xb - xa)
        for yc in (ytop - chord_h / 2, ybot + chord_h / 2):
            K.box(ch.bm, (cx, yc, (za + zb) / 2), (wx, chord_h, za - zb), zone=Z['paint'])
        planes = [xb - sx * 0.2] if wx < 1.2 else [xb - sx * 0.25, xa + sx * 0.25]
        y0, y1 = ybot + chord_h, ytop - chord_h
        for px in planes:
            for i, z in enumerate(zs):
                beam(bm, (px, y0 - 0.05, z), (px, y1 + 0.05, z), 0.42, zone='metal', up=(1, 0, 0))
                if i + 1 < len(zs):
                    zn = zs[i + 1]
                    zm = (z + zn) / 2
                    beam(bm, (px, y0, z - 0.2), (px, y1, zm), 0.3, zone='metal', up=(1, 0, 0))
                    beam(bm, (px, y1, zm), (px, y0, zn + 0.2), 0.3, zone='metal', up=(1, 0, 0))
        # gusset plates at the web nodes (outer plane)
        for z in zs:
            for yy in (y0 + 0.35, y1 - 0.35):
                K.box(bm, (planes[0] + sx * 0.08, yy, z), (0.06, 0.9, 1.1), zone=Z['trim'])
    K.solid(bm)
    K.solid(ch.bm)
    vol.cull = False
    vol.uvb = True
    ch.cull = False
    return [ch, vol]


def cargo_mid(v):
    vols = []
    G = D.GIRDER
    za, zb = v['PAY1'] + 0.2, v['PAY0'] - 0.2
    # box girder: flat chords at x +-(6.9..7.8), top and bottom deck plates across
    vols += girder(v, G['x'] - 0.55, G['x'] + 0.35, G['top'], G['bot'], G['chord'], 'girder')
    dk = Volume('decks', bevel=0.04)
    for y0, y1 in ((G['top'] - G['deck'], G['top']), (G['bot'], G['bot'] + G['deck'])):
        K.box(dk.bm, (0, (y0 + y1) / 2, (za + zb) / 2), (2 * (G['x'] - 0.5), y1 - y0, za - zb), zone=Z['dark'])
    K.solid(dk.bm)
    dk.uvb = True
    vols.append(dk)
    # spine tube inside the girder (pressurised corridor), ring frames at the web stations
    sp = Volume('spine', bevel=0.04)
    K.cyl(sp.bm, (0, -2.2, v['PAY1'] + 0.4), (0, -2.2, v['PAY0'] - 0.4), 2.2, n=32, zone=Z['paint'])
    for z in web_stations(v):
        band_cyl(sp.bm, (0, -2.2, z + 0.25), (0, 0, -1), 1.9, 2.38, 0.0, 0.5, n=32)
        # cross frame: floor beams from the spine to the chords
        beam(sp.bm, (-G['x'] + 0.5, -2.2, z), (G['x'] - 0.5, -2.2, z), 0.4, zone='metal')
    K.solid(sp.bm)
    sp.cull = False
    sp.uvb = True
    vols.append(sp)
    # container cell guides: posts at the bay boundaries, a lashing bridge across the top
    cg = Volume('cell_guides', bevel=0.025)
    zs = web_stations(v)
    htop = G['top'] + 3 * D.TIER + 0.25
    hbot = G['bot'] - 3 * D.TIER - 0.25
    for z in zs:
        for x in (-6.25, 0.0, 6.25):
            beam(cg.bm, (x, G['top'], z), (x, htop, z), 0.26, zone='metal', up=(1, 0, 0))
            beam(cg.bm, (x, G['bot'], z), (x, hbot, z), 0.26, zone='metal', up=(1, 0, 0))
        beam(cg.bm, (-6.4, htop - 0.2, z), (6.4, htop - 0.2, z), 0.3, 0.4, zone='trim')
        beam(cg.bm, (-6.4, hbot + 0.2, z), (6.4, hbot + 0.2, z), 0.3, 0.4, zone='trim')
    K.solid(cg.bm)
    cg.cull = False
    cg.uvb = True
    vols.append(cg)
    return vols


def hab_rings(v):
    z0, z1 = D.hab_span(v)
    H = D.HAB
    zc0, zc1 = z0 + H['dome'], z1 - H['dome']
    n = max(2, int(round((zc1 - zc0) / H['ring_pitch'])))
    return [zc1 - i * (zc1 - zc0) / n for i in range(n + 1)], (z0, z1, zc0, zc1)


def troops_mid(v):
    vols = []
    H, TG, SP = D.HAB, D.TGIRDER, D.SPINE
    rings, (z0, z1, zc0, zc1) = hab_rings(v)
    hb = Volume('habitats', bevel=0.05)
    r, dm = H['r'], H['dome']
    prof = [(r * 0.62, 0.0), (r * 0.84, dm * 0.3), (r * 0.95, dm * 0.62), (r, dm), (r, dm + (zc1 - zc0)), (r * 0.95, 2 * dm + (zc1 - zc0) - dm * 0.62),
            (r * 0.84, 2 * dm + (zc1 - zc0) - dm * 0.3), (r * 0.62, 2 * dm + (zc1 - zc0))]
    for sx in (1, -1):
        for yc in (H['yu'], H['yl']):
            K.lathe(hb.bm, (sx * H['x'], yc, z1), (0, 0, -1), prof, n=48, zone=Z['paint'])
    K.solid(hb.bm)
    vols.append(hb)
    # ring frames and end hatches
    hr = Volume('hab_rings', bevel=0.025)
    hr.occluder = False
    for sx in (1, -1):
        for yc in (H['yu'], H['yl']):
            for z in rings:
                band_cyl(hr.bm, (sx * H['x'], yc, z + 0.2), (0, 0, -1), r - 0.3, r + 0.12, 0.0, 0.4, n=40)
            for ze, d in ((z1, 1), (z0, -1)):
                K.cyl(hr.bm, (sx * H['x'], yc, ze - d * 0.2), (sx * H['x'], yc, ze + d * 0.15), r * 0.45, n=32, zone=Z['trim'])
    K.solid(hr.bm)
    vols.append(hr)
    # spine tube between the four habitats
    sp = Volume('spine', bevel=0.04)
    K.cyl(sp.bm, (0, SP['y'], v['PAY1'] + 0.4), (0, SP['y'], v['PAY0'] - 0.4), SP['r'], n=36, zone=Z['paint'])
    for z in web_stations(v):
        band_cyl(sp.bm, (0, SP['y'], z + 0.25), (0, 0, -1), SP['r'] - 0.3, SP['r'] + 0.16, 0.0, 0.5, n=24)
    K.solid(sp.bm)
    sp.cull = False
    sp.uvb = True
    vols.append(sp)
    vols += girder(v, TG['x0'], TG['x1'], TG['top'], TG['bot'], 0.85, 'girder')
    # cross struts spine -> girders, saddles spine -> habitats at the ring frames
    cs = Volume('struts', bevel=0.03)
    for z in web_stations(v):
        for sx in (1, -1):
            beam(cs.bm, (sx * (SP['r'] - 0.2), SP['y'], z), (sx * (TG['x0'] + 0.1), SP['y'], z), 0.5, zone='metal')
    for z in rings:
        for sx in (1, -1):
            for yc in (H['yu'], H['yl']):
                d = V((sx * H['x'], yc - SP['y'], 0))
                a = V((0, SP['y'], z)) + d.normalized() * (SP['r'] - 0.1)
                bpt = V((sx * H['x'], yc, z)) - d.normalized() * (r - 0.1)
                beam(cs.bm, a, bpt, 0.7, 0.45, zone='trim', up=(0, 0, 1))
    K.solid(cs.bm)
    cs.cull = False
    cs.uvb = True
    vols.append(cs)
    return vols


# ------------------------------------------------------------------------------------------
# build
# ------------------------------------------------------------------------------------------
def all_volumes(v):
    cm = crew_module(v)
    vols = [cm, *cm_details(v), *collar(v), *reactor(v), *engines(v), *radiators(v), legs(v)]
    vols += cargo_mid(v) if v['variant'] == 'cargo' else troops_mid(v)
    return vols


def build(v, args):
    t0 = time.time()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    K.zone_materials()
    obs = []
    for vol in all_volumes(v):
        ob = vol.to_object()
        ob['bevel'] = vol.bevel
        ob['angle'] = vol.angle
        ob['cull'] = vol.cull
        ob['closed'] = getattr(vol, 'occluder', vol.cull)
        ob['uvb'] = getattr(vol, 'uvb', False)
        if len(vol.cutters.faces):
            cut = vol.to_object(vol.cutters, vol.name + '_cut')
            K.boolean(ob, cut)
            bpy.data.objects.remove(cut)
        obs.append(ob)
        for nm, fn in vol.adds:
            bm = bmesh.new()
            fn(bm)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            vv = Volume(f'{vol.name}_{nm}')
            ob2 = vv.to_object(bm, f'{vol.name}_{nm}')
            ob2['bevel'] = 0.0 if nm in ('fins', 'louvres') else 0.03
            ob2['angle'] = 30.0
            ob2['cull'] = False
            ob2['closed'] = False
            ob2['uvb'] = True
            obs.append(ob2)
    K.log(f'volumes: {len(obs)} objects, {sum(K.count_tris(o) for o in obs)} tris before bevel ({time.time() - t0:.1f}s)')
    if not args.get('no_cull'):
        K.cull_hidden(obs)
    for ob in obs:
        K.finish(ob, ob['bevel'], ob['angle'])
        a = ob.data.attributes.new('uvb', 'INT', 'FACE')
        a.data.foreach_set('value', [int(ob['uvb'])] * len(ob.data.polygons))
    areas = sorted(((round(sum(p.area for p in o.data.polygons)), o.name, int(o['uvb'])) for o in obs), reverse=True)
    K.log('areas', areas[:24])
    K.log('tris', sorted(((K.count_tris(o), o.name) for o in obs), reverse=True)[:20])
    hullob = K.join(obs, 'hull')
    K.log(f'joined: {K.count_tris(hullob)} tris ({time.time() - t0:.1f}s)')
    return hullob


def _uv_area(pts):
    return abs(sum(pts[i].x * pts[(i + 1) % len(pts)].y - pts[(i + 1) % len(pts)].x * pts[i].y for i in range(len(pts)))) / 2


def unwrap(ob, angle=50.0, margin=0.0006, tex=6144, cell_px=8):
    """Two groups. Main surfaces (hull plating, blocks, tanks, habitats): smart projection at one
    scale, packed (margin as a fraction of the atlas). Thin members (girder webs, cell guides,
    pylon struts, radiator fins, louvres; face attribute 'uvb'): thousands of small islands whose
    margins would eat the atlas, so each connected member gets one small cell (cell_px square,
    a planar map over its two longest extents) dropped into atlas space the main pack left
    free. They take their colour from the zone paint, the baked AO and the runtime PATINA."""
    from PIL import Image, ImageDraw
    vl = bpy.context.view_layer
    for o in vl.objects:
        o.select_set(False)
    ob.select_set(True)
    vl.objects.active = ob
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    me = ob.data
    grp = np.zeros(len(me.polygons), np.int32)
    me.attributes['uvb'].data.foreach_get('value', grp)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=angle * K.DEG, island_margin=0.0, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
    ebm = bmesh.from_edit_mesh(me)
    ebm.faces.ensure_lookup_table()
    for f in ebm.faces:
        f.select_set(not grp[f.index])
    bmesh.update_edit_mesh(me)
    for _ in range(2):
        bpy.ops.uv.pack_islands(rotate=True, margin=margin, margin_method='FRACTION', shape_method='CONCAVE', scale=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    uv = me.uv_layers.active.data
    # coverage of the main pack in cells
    ncell = tex // cell_px
    im = Image.new('L', (tex, tex), 0)
    dr = ImageDraw.Draw(im)
    for p in me.polygons:
        if grp[p.index]:
            continue
        dr.polygon([(uv[i].uv.x * tex, (1 - uv[i].uv.y) * tex) for i in p.loop_indices], fill=255)
    cov = np.asarray(im, np.uint8).reshape(ncell, cell_px, ncell, cell_px).max(axis=(1, 3)) > 0
    # dilate one cell (margin)
    d = cov.copy()
    d[1:] |= cov[:-1]; d[:-1] |= cov[1:]; d[:, 1:] |= cov[:, :-1]; d[:, :-1] |= cov[:, 1:]
    free = [(r, c) for r in range(ncell) for c in range(ncell) if not d[r, c]]
    # members: connected pieces of the uvb faces
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    uvl = bm.loops.layers.uv.active
    seen = np.zeros(len(bm.faces), bool)
    pieces = []
    for f in bm.faces:
        if not grp[f.index] or seen[f.index]:
            continue
        seen[f.index] = True
        st, piece = [f], []
        while st:
            g = st.pop()
            piece.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if grp[h.index] and not seen[h.index]:
                        seen[h.index] = True
                        st.append(h)
        pieces.append(piece)
    if len(pieces) > len(free):
        raise RuntimeError(f'uv: {len(pieces)} members, only {len(free)} free cells')
    inset = 1.0 / tex  # one texel inside the cell edge
    for piece, (r, c) in zip(pieces, free):
        co = np.array([l.vert.co[:] for g in piece for l in g.loops])
        lo, hi = co.min(0), co.max(0)
        ax = np.argsort(hi - lo)[::-1][:2]
        u0, v0 = c * cell_px / tex + inset, 1 - (r + 1) * cell_px / tex + inset
        sz = cell_px / tex - 2 * inset
        for g in piece:
            for l in g.loops:
                p = l.vert.co
                l[uvl].uv = (u0 + (p[ax[0]] - lo[ax[0]]) / max(hi[ax[0]] - lo[ax[0]], 1e-6) * sz, v0 + (p[ax[1]] - lo[ax[1]]) / max(hi[ax[1]] - lo[ax[1]], 1e-6) * sz)
    bm.to_mesh(me)
    bm.free()
    a3 = a2 = 0.0
    uv = me.uv_layers.active.data
    for p in me.polygons:
        if grp[p.index]:
            continue
        a3 += p.area
        a2 += _uv_area([uv[i].uv for i in p.loop_indices])
    return {'surface_m2': round(sum(p.area for p in me.polygons), 1), 'main_m2': round(a3, 1), 'uv_fill': round(a2, 3),
            'px_per_m_at_4096': round(4096 * math.sqrt(a2 / a3), 1), 'px_per_m': round(tex * math.sqrt(a2 / a3), 1), 'tex': tex, 'members': len(pieces), 'free_cells': len(free)}


def container_proxies(v):
    """Container boxes (and nothing else) as a plain object, so the hull's AO bake sees the
    stacks. Not exported: freighter_extras.py adds the real containers after assembly."""
    if v['variant'] != 'cargo':
        return None
    bm = bmesh.new()
    L, Hh, Wd = D.ISO
    for c in D.containers(v):
        K.box(bm, c['c'], (L, Hh, Wd))
    me = bpy.data.meshes.new('container_proxies')
    bm.to_mesh(me)
    bm.free()
    me.transform(K.C)
    ob = bpy.data.objects.new('container_proxies', me)
    bpy.context.collection.objects.link(ob)
    return ob


def bake_maps(ob, work, size=6144, ao_size=2048, ao_samples=24, ao_dist=1.2, curv_r=0.06, threads=4):
    """common.bake_maps with a small memory footprint at 6144: each map is baked, reduced to its
    storage type and written to <work>/map-<name>.npy before the next one (position float32,
    normal float16, zone int8, AO / curvature float16)."""
    import gc
    K.setup_cycles(threads)

    def save(name, a):
        np.save(os.path.join(work, f'map-{name}.npy'), a)
        K.log('saved', name, a.shape, a.dtype)
    zone, pos, nrm = raster_maps(ob, size)
    save('zone', zone)
    del zone
    save('pos', pos)
    del pos
    save('nrm', nrm)
    del nrm
    gc.collect()

    def ao_b(nt, em):
        ao = nt.nodes.new('ShaderNodeAmbientOcclusion')
        ao.samples = 16
        ao.inputs['Distance'].default_value = ao_dist
        nt.links.new(ao.outputs['AO'], em.inputs['Color'])
    save('ao', K.bake_emit(ob, ao_size, ao_b, samples=ao_samples, name='ao')[..., 0].astype(np.float16))

    def cv_b(nt, em):
        bv = nt.nodes.new('ShaderNodeBevel')
        bv.samples = 8
        bv.inputs['Radius'].default_value = curv_r
        g = nt.nodes.new('ShaderNodeNewGeometry')
        d = nt.nodes.new('ShaderNodeVectorMath'); d.operation = 'DOT_PRODUCT'
        nt.links.new(bv.outputs['Normal'], d.inputs[0])
        nt.links.new(g.outputs['True Normal'], d.inputs[1])
        sb = nt.nodes.new('ShaderNodeMath'); sb.operation = 'SUBTRACT'; sb.inputs[0].default_value = 1.0
        nt.links.new(d.outputs['Value'], sb.inputs[1])
        nt.links.new(sb.outputs[0], em.inputs['Color'])
    save('curv', K.bake_emit(ob, ao_size, cv_b, samples=8, name='curv')[..., 0].astype(np.float16))


def raster_maps(ob, S, margin=8):
    """Zone id, ship-frame position and true (face) normal per texel, rasterised from the UV
    triangles in numpy (what the Cycles EMIT bakes give, at a fraction of their memory at 6144),
    then extended `margin` texels past every island edge (nearest filled neighbour), as the
    bake margin does. Rows top-down."""
    me = ob.data
    me.calc_loop_triangles()
    nt = len(me.loop_triangles)
    tl = np.empty(nt * 3, np.int32); me.loop_triangles.foreach_get('loops', tl); tl = tl.reshape(-1, 3)
    tp = np.empty(nt, np.int32); me.loop_triangles.foreach_get('polygon_index', tp)
    lv = np.empty(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', lv)
    co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    co = np.stack([co[:, 0], co[:, 2], -co[:, 1]], 1)   # Blender -> ship frame
    uv = np.empty(len(me.loops) * 2, np.float32); me.uv_layers.active.data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
    pn = np.empty(len(me.polygons) * 3, np.float32); me.polygons.foreach_get('normal', pn); pn = pn.reshape(-1, 3)
    pn = np.stack([pn[:, 0], pn[:, 2], -pn[:, 1]], 1)
    pm = np.empty(len(me.polygons), np.int32); me.polygons.foreach_get('material_index', pm)
    zone = np.full((S, S), -1, np.int8)
    pos = np.zeros((S, S, 3), np.float32)
    nrm = np.zeros((S, S, 3), np.float16)
    P = uv[tl] * S                                        # (nt, 3, 2) pixel coords, x right, y up
    P[..., 1] = S - P[..., 1]                             # rows top-down
    X = co[lv[tl]]
    for t in range(nt):
        a, b, c = P[t]
        x0 = max(int(math.floor(min(a[0], b[0], c[0]) - 0.5)), 0); x1 = min(int(math.ceil(max(a[0], b[0], c[0]) + 0.5)), S)
        y0 = max(int(math.floor(min(a[1], b[1], c[1]) - 0.5)), 0); y1 = min(int(math.ceil(max(a[1], b[1], c[1]) + 0.5)), S)
        if x1 <= x0 or y1 <= y0:
            continue
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        gy, gx = np.mgrid[y0:y1, x0:x1]
        px, py = gx + 0.5, gy + 0.5
        w0 = ((b[1] - c[1]) * (px - c[0]) + (c[0] - b[0]) * (py - c[1])) / den
        w1 = ((c[1] - a[1]) * (px - c[0]) + (a[0] - c[0]) * (py - c[1])) / den
        w2 = 1 - w0 - w1
        e = -0.02
        m = (w0 >= e) & (w1 >= e) & (w2 >= e)
        if not m.any():
            continue
        yy, xx = gy[m], gx[m]
        W = np.stack([w0[m], w1[m], w2[m]], 1)
        pos[yy, xx] = W @ X[t]
        nrm[yy, xx] = pn[tp[t]]
        zone[yy, xx] = pm[tp[t]]
    # margin: grow every island by nearest-neighbour copies
    for _ in range(margin):
        empty = zone < 0
        if not empty.any():
            break
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            src = np.roll(np.roll(zone, dy, 0), dx, 1)
            take = empty & (src >= 0)
            if not take.any():
                continue
            yy, xx = np.nonzero(take)
            sy, sx = (yy - dy) % S, (xx - dx) % S
            zone[yy, xx] = zone[sy, sx]
            pos[yy, xx] = pos[sy, sx]
            nrm[yy, xx] = nrm[sy, sx]
            empty = zone < 0
    K.log('raster', nt, 'triangles, covered', round(float((zone >= 0).mean()), 3))
    return zone, pos, nrm


def load_maps(work):
    m = {k: np.load(os.path.join(work, f'map-{k}.npy'), mmap_mode='r') for k in ('zone', 'pos', 'nrm', 'ao', 'curv')}
    m['ao'] = np.asarray(m['ao'], np.float32)
    m['curv'] = np.asarray(m['curv'], np.float32)
    m['zone'] = np.asarray(m['zone'], np.int16)
    return m


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    work = os.path.abspath(argv[0])
    opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d
    stage = opt('--stage', 'all')
    v = D.V(opt('--variant', 'cargo'))
    os.makedirs(work, exist_ok=True)
    name = v['name']
    blend = os.path.join(work, f'{name}-hull.blend')
    maps = os.path.join(work, 'maps.npz')
    tex = int(opt('--tex', 6144))
    if stage in ('all', 'model'):
        ob = build(v, {'no_cull': '--no-cull' in argv})
        info = unwrap(ob)
        K.log('uv', info)
        bpy.ops.wm.save_as_mainfile(filepath=blend)
        if stage == 'model' and '--bake' not in argv:
            json.dump({'tris': K.count_tris(ob), **info}, open(os.path.join(work, 'model.json'), 'w'), indent=1)
            return
        container_proxies(v)
        bake_maps(ob, work, size=tex, ao_size=int(opt('--ao', 2048)), threads=int(opt('--threads', 4)))
        json.dump({'tris': K.count_tris(ob), **info}, open(os.path.join(work, 'model.json'), 'w'), indent=1)
    if stage in ('all', 'paint'):
        import paint
        import freighter_paint as FP
        bpy.ops.wm.open_mainfile(filepath=blend)
        ob = bpy.data.objects['hull']
        m = load_maps(work)
        paint.stencil = FP.stencil   # C, T and 7 glyphs for the civil hull numbers
        spec = FP.scheme(v)
        spec['px_per_m'] = json.load(open(os.path.join(work, 'model.json')))['px_per_m_at_4096'] * tex / 4096
        base, orm = FP.paint_chunked(m, spec=spec, out=work)
        K.set_final_material(ob, base, orm, normal_png=spec.get('_normal_png'))
        glb = os.path.join(work, f'{name}-hull.glb')
        K.export_glb(ob, glb)
        K.log('wrote', glb, os.path.getsize(glb))


if __name__ == '__main__':
    main()
