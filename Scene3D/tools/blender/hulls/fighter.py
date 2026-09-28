"""Petrel-class heavy fighter F-402: clean hard-surface hull, rebuilt from measurements of the fal /
Tripo H3.1 blueprint (assets/ships/raw/fighter.glb; see README.md and README-fighter.md).

    <blender-python> tools/blender/hulls/fighter.py <workdir> [--stage all|model|paint]
                     [--tex 4096] [--ao 2048] [--threads 4] [--no-cull] [--preview] [--bake]

Stages: model -> <workdir>/fighter-hull.blend (+ maps.npz with --bake); paint -> base / orm /
normal PNGs (fighter_paint.py over paint.py) and <workdir>/fighter-hull.glb (node 'hull', ship
frame, not re-centred). assemble.py adds the kit parts (specs/fighter-v3.json, fighter_spec.py).
The dimension tables live in fighter_dims.py (pure Python, shared with fighter_spec.py).

Ship frame, metres: bow +Z, dorsal +Y, port +X. Blueprint = raw GLB rotated [0, -90, 0] and scaled
to the module length 71.712 (bbox 46.92 x 20.96 x 71.71), measured with measure.py: sections every
1 m along z, top / bottom height maps. Dimensions below are those measurements unless noted.

Layout (blueprint): an armoured faceted pod. Octagonal section (flat top, big upper chamfers,
vertical flank, lower chamfers, flat belly) at full size from the stern block (z -26) to z 4, then
tapering in plan and height to a framed bow face (z 35.86) with a sensor ball under the chin. A
raised dorsal deck (y 6.84) with two louvred radiator bays and a spine that runs forward into a
low bridge block glazed in a band of small panes (front face z 15-17). Two armoured flank
sponsons on tapered pylons, each with a twin railgun forward and a small drive bell aft. Twin
fusion bells (r 3.55) on thrust hubs in two sockets of the stern face.
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

from fighter_dims import *  # noqa: E402,F401,F403  (dimension tables, shared with fighter_spec.py)
from fighter_dims import BELL, SBELL, BR, SIDE_GLAZE, SP, DOORS, ST, COLS  # noqa: E402


def prof(z):
    return K.interp_table(ST, z, COLS)


def half_profile(z):
    p = prof(z)
    return [(0.0, p['T']), (p['TX'], p['T']), (p['W'], p['FT']), (p['W'], p['FB']), (p['BX'], p['B']), (0.0, p['B'])]


SEG_ZONE = ['paint', 'paint', 'paint', 'belly', 'belly']


def ring_zones():
    segs = len(SEG_ZONE)
    return [SEG_ZONE[j] if j < segs else SEG_ZONE[2 * segs - 1 - j] for j in range(2 * segs)]


def fX(z):
    return prof(z)['W']


def flank_n(z, side=1):
    """Outward normal of the vertical flank at z (plan taper)."""
    d = 0.2
    dw = (fX(z + d) - fX(z - d)) / (2 * d)
    n = V((1, 0, -dw)).normalized()
    return V((side * n.x, 0, n.z))


def top_y(z):
    return prof(z)['T']


def chamfer_n(z, side=1):
    p = prof(z)
    e = V((p['W'] - p['TX'], p['FT'] - p['T'])).normalized()   # down the chamfer (x, y)
    n = V((-e.y, e.x)) if -e.y > 0 else V((e.y, -e.x))
    return V((side * n.x, n.y, 0)).normalized()


# ------------------------------------------------------------------------------------------
# volumes
# ------------------------------------------------------------------------------------------
def hull_body():
    vol = Volume('hull_body', bevel=0.09)
    bm = vol.bm
    stations = [z for z, _ in ST]
    rings = [[V((x, y, z)) for x, y in K.mirror_half(half_profile(z))] for z in stations]
    pb = K.mirror_half(half_profile(ST[-1][0]))
    lip = K.offset_poly(pb, -0.14)
    inner = K.offset_poly(pb, -0.75)
    rings_bow = [[V((x, y, BOW_Z)) for x, y in lip], [V((x, y, BOW_Z)) for x, y in inner], [V((x, y, BOW_PLATE)) for x, y in inner]]
    ps = K.mirror_half(half_profile(STERN_Z))
    s_lip = K.offset_poly(ps, -0.12)
    s_in = K.offset_poly(ps, -0.75)
    rings_st = [[V((x, y, STERN_PLATE)) for x, y in s_in], [V((x, y, STERN_LIP)) for x, y in s_in], [V((x, y, STERN_LIP)) for x, y in s_lip]]
    grid, caps = K.loft(bm, rings_st + rings + rings_bow, zone=Z['paint'])
    zones = ring_zones()
    off = len(rings_st)
    for k, row in enumerate(grid):
        for j, f in enumerate(row):
            if f is None:
                continue
            if off <= k < off + len(rings) - 1:
                f.material_index = Z[zones[j]]
            else:
                f.material_index = Z['trim'] if zones[j] != 'belly' else Z['belly']
    for f in caps:
        f.material_index = Z['recess']
    K.solid(bm)
    # bell sockets in the stern plate
    for sx in (1, -1):
        K.cyl(vol.cutters, (sx * BELL['x'], BELL['y'], STERN_PLATE - 1.0), (sx * BELL['x'], BELL['y'], STERN_PLATE + 0.85), 4.3, n=48, zone=Z['recess'])
    return vol


def stern_collar():
    """Armoured stern frame band (concept: a darker frame round the stern block)."""
    v = Volume('stern_collar', bevel=0.05)
    # a closed annular band (no end caps: a cap would cover the recessed stern plate)
    z0, z1, d = STERN_Z - 0.35, -23.4, 0.14
    o0 = K.offset_poly(K.mirror_half(half_profile(z0 + 0.35)), d)
    o1 = K.offset_poly(K.mirror_half(half_profile(z1)), d)
    i0 = K.offset_poly(K.mirror_half(half_profile(z0 + 0.35)), -0.3)
    i1 = K.offset_poly(K.mirror_half(half_profile(z1)), -0.3)
    K.loft(v.bm, [K.ring3(o0, 'xy', z0), K.ring3(o1, 'xy', z1), K.ring3(i1, 'xy', z1), K.ring3(i0, 'xy', z0), K.ring3(o0, 'xy', z0)],
           cap0=False, cap1=False, zone=Z['trim'])
    K.solid(v.bm)
    return v


# spine + bridge block: side profile (z, y), extruded between slanted walls (x 3.85 at the foot,
# 3.3 at the roof). The roof runs at SPINE_Y from the aft deck step to z 11.3, rakes to z 15.1,
# then the glazed front face drops to the forward deck at z 17.


def bridge():
    vol = Volume('bridge', bevel=0.07)
    zf, yf = BR['face']
    zr, yr = BR['rake']
    side = [(BR['aft'], 6.0), (BR['aft'], SPINE_Y), (BR['roof_end'], SPINE_Y), (zr, yr), (zf, yf), (BR['foot'][0], BR['foot'][1]),
            (4.2, 5.2), (-1.0, 5.2), (-3.4, 6.0)]
    # walls: x at the roof 3.3, at the foot 3.85 (slant scales with height above y 2.4)
    def wx(y):
        return 3.85 - 0.55 * (y - 2.4) / (SPINE_Y - 2.4)
    rings = []
    for sx in (1, -1):
        rings.append([V((sx * wx(y), y, z)) for z, y in side])
    grid, caps = K.loft(vol.bm, [rings[0], rings[1]], zone=Z['paint'])
    K.solid(vol.bm)
    # glazing recess on the front face (a band 0.32 m deep, 6.2 wide, 2.1 m along the face)
    fn = V((0, zf - zr, -(yf - yr))).normalized()   # outward normal of the front face (+z, +y)
    fn = V((0, abs(fn.y), abs(fn.z)))
    c = V((0, (yr + yf) / 2, (zr + zf) / 2))
    up = V((0, yr - yf, zr - zf)).normalized()
    K.oriented_prism(vol.cutters, K.chamfer_rect(0, 0, 5.75, 1.97, 0.1), c, fn, up, -0.32, 1.5, zone=Z['recess'])
    # side glazing: one row each side, forward end of the bridge (z 9.8-13.4, y 5.2-6.0; the roof
    # rakes down from z 11.3, so the band stays 0.12 m under it)
    for sx in (1, -1):
        yc = SIDE_GLAZE['y']
        c = V((sx * wx(yc), yc, SIDE_GLAZE['z']))
        wn = V((sx * 1.0, 0.55 / (SPINE_Y - 2.4), 0)).normalized()
        K.oriented_prism(vol.cutters, K.chamfer_rect(0, 0, SIDE_GLAZE['w'], SIDE_GLAZE['h'], 0.08), c, wn, (0, 1, 0), -0.25, 1.5, zone=Z['recess'])
    return vol


def glazing_frame():
    """Geometry of the glazing recess back walls (for the spec): centre, normal, up of the face."""
    zf, yf = BR['face']
    zr, yr = BR['rake']
    fn = V((0, abs(zf - zr), abs(yf - yr))).normalized()
    up = V((0, yr - yf, zr - zf)).normalized()
    c = V((0, (yr + yf) / 2, (zr + zf) / 2)) - fn * 0.32
    return c, fn, up


def grille_bays(hull):
    """Two louvred radiator bays on the raised deck (blueprint: grille panels x 3.9-7.6,
    z -17.6..-5), 0.3 m deep, transverse louvre fins tilted 30 degrees."""
    for sx in (1, -1):
        x0, x1, z0, z1 = 4.15, 7.45, -17.4, -5.2
        c = V((sx * (x0 + x1) / 2, DECK_HI, (z0 + z1) / 2))
        K.oriented_prism(hull.cutters, K.chamfer_rect(0, 0, x1 - x0, z1 - z0, 0.35), c, (0, 1, 0), (0, 0, 1), -0.3, 1.0, zone=Z['recess'])
        fins = [z for z in np.arange(z0 + 0.35, z1 - 0.2, 0.34)]
        a = 30 * K.DEG
        R = Matrix(((1, 0, 0), (0, math.cos(a), -math.sin(a)), (0, math.sin(a), math.cos(a))))
        hull.adds.append(('louvres', lambda bm, fins=fins, cx=c.x, R=R, w=x1 - x0: [K.box(bm, (cx, DECK_HI - 0.16, z), (w - 0.1, 0.07, 0.36), R=R, zone=Z['fin']) for z in fins]))
        # centre stringer across the bay
        hull.adds.append(('stringer', lambda bm, cx=c.x, zz=(z0 + z1) / 2, L=z1 - z0: K.box(bm, (cx, DECK_HI - 0.12, zz), (0.16, 0.24, L - 0.1), zone=Z['metal'])))


# crew doors 2 x 1 m (kit door, frame 1.4 x 2.4) in 1.95 x 2.95 bays on the flanks


def door_bays(hull):
    for sx in (1, -1):
        for z, y in DOORS:
            c = V((sx * fX(z), y, z))
            K.oriented_prism(hull.cutters, K.chamfer_rect(0, 0, 1.95, 2.95, 0.12), c, flank_n(z, sx), (0, 1, 0), -0.32, 1.5, zone=Z['recess'])


def rcs_cluster(hull):
    """Aft flank thruster cluster (blueprint: four round nozzle cups, 2 x 2, z -19..-22.3,
    y -1.3..-4.4): cups recessed into a raised square plate."""
    for sx in (1, -1):
        x = sx * 12.95
        hull.adds.append(('rcsplate', lambda bm, x=x, sx=sx: K.plate(bm, (x, -2.85, -20.65), (sx, 0, 0), (0, 1, 0), 3.9, 3.9, 0.22, ch=0.08, back=0.3, zone=Z['trim'])))
        for y in (-1.95, -3.75):
            for z in (-19.75, -21.55):
                # raised thruster disc with a chamfered rim and a small nozzle throat (shallow, so the
                # AO does not turn the cluster into dark blobs)
                hull.adds.append(('cup', lambda bm, x=x, y=y, z=z, sx=sx: K.lathe(bm, (x + sx * 0.1, y, z), (sx, 0, 0), [(0.74, 0.0), (0.74, 0.24), (0.64, 0.33), (0.3, 0.33), (0.24, 0.27), (0.14, 0.27), (0.02, 0.27)], n=24, zone=Z['metal'])))


def face_frame(face, z, t, side=1):
    """Point, outward normal, across-direction and along-direction on a hull face at (z, t):
    t runs 0..1 across the face (upper chamfer: deck edge -> flank top; flank: top -> bottom;
    lower chamfer: flank bottom -> belly edge; top: centre -> deck edge; belly: centre -> edge)."""
    def pt(zz, tt):
        p = prof(zz)
        a, b = {'upper': ((p['TX'], p['T']), (p['W'], p['FT'])), 'flank': ((p['W'], p['FT']), (p['W'], p['FB'])),
                'lower': ((p['W'], p['FB']), (p['BX'], p['B'])), 'top': ((0.0, p['T']), (p['TX'], p['T'])),
                'belly': ((0.0, p['B']), (p['BX'], p['B']))}[face]
        return V((side * (a[0] + (b[0] - a[0]) * tt), a[1] + (b[1] - a[1]) * tt, zz))
    c = pt(z, t)
    across = (pt(z, min(t + 0.05, 1)) - pt(z, max(t - 0.05, 0))).normalized()
    along = (pt(z + 0.25, t) - pt(z - 0.25, t)).normalized()
    n = along.cross(across).normalized()
    if n.dot(V((c.x, c.y, 0)).normalized() if face not in ('top', 'belly') else V((0, 1 if face == 'top' else -1, 0))) < 0:
        n = -n
    return c, n, across, along


# applique armour plates on the broad faces (design: breaks up the large flat facets; each a raised
# 6-8 cm plate with a chamfered edge that catches a highlight): (face, z0, z1, t0, t1, zone)
APPLIQUE = [
    ('upper', 6.2, 9.8, 0.18, 0.55, 'paint'), ('upper', 17.9, 21.6, 0.22, 0.7, 'trim'), ('upper', 23.1, 26.4, 0.25, 0.72, 'paint'),
    ('upper', -17.6, -16.4, 0.12, 0.42, 'trim'),
    ('flank', 15.9, 19.5, 0.6, 0.94, 'trim'), ('flank', 22.3, 26.1, 0.6, 0.94, 'paint'),
    ('lower', -9.1, -4.7, 0.14, 0.78, 'trim'), ('lower', -4.1, 0.6, 0.14, 0.78, 'paint'), ('lower', 5.7, 10.1, 0.18, 0.8, 'paint'),
    ('lower', 10.9, 14.3, 0.18, 0.8, 'trim'), ('lower', 16.3, 20.7, 0.2, 0.8, 'paint'), ('lower', -17.3, -12.7, 0.2, 0.8, 'paint'),
    ('top', 29.3, 32.9, 0.25, 0.78, 'deck'), ('top', 11.0, 13.6, 0.52, 0.85, 'deck'),
    ('belly', 9.8, 14.8, 0.22, 0.68, 'belly'), ('belly', -3.4, 0.4, 0.14, 0.42, 'belly'), ('belly', 18.5, 23.5, 0.1, 0.5, 'belly'),
]


def applique():
    v = Volume('applique', bevel=0.025)
    for face, z0, z1, t0, t1, zone in APPLIQUE:
        for sx in (1, -1):
            zc, tc = (z0 + z1) / 2, (t0 + t1) / 2
            c, n, across, along = face_frame(face, zc, tc, sx)
            a0, _, _, _ = face_frame(face, zc, t0, sx)
            a1, _, _, _ = face_frame(face, zc, t1, sx)
            h = (a1 - a0).length
            up = across
            r = up.cross(n)
            w = (z1 - z0) / max(abs(r.z), 0.3)
            K.plate(v.bm, c, n, up, w, h, 0.07, ch=0.03, back=0.18, zone=Z[zone])
    K.solid(v.bm)
    return v


def rcs_quad(bm, c, n, up):
    """RCS quad modelled on the hull (the kit block reads as a dark blob at hero distance): a
    chamfered 0.8 m housing in hull paint with four side nozzles and one outboard nozzle."""
    r, u, nn = K.basis(n, up)
    c = V(c)
    K.plate(bm, c, nn, u, 0.8, 0.8, 0.34, ch=0.07, back=0.2, zone=Z['trim'])
    bell = [(0.085, 0.0), (0.085, 0.05), (0.14, 0.2), (0.115, 0.2), (0.03, 0.1)]
    mid = c + nn * 0.19
    for d in (r, -r, u, -u):
        K.lathe(bm, mid + d * 0.38, d, bell, n=8, zone=Z['nozzle'], cap1=False)
    K.lathe(bm, c + nn * 0.32, nn, bell, n=8, zone=Z['nozzle'], cap1=False)


RCS = [  # (point on the surface, normal, up), mirrored to starboard
    ((None, -3.35, 31.8), 'flank', (0, 1, 0)),
    ((SP['x'] + 1.3, SP['y'] + SP['h'] / 2, -1.6), (0, 1, 0), (0, 0, 1)),
    ((SP['x'] + 1.3, SP['y'] - SP['h'] / 2, -1.6), (0, -1, 0), (0, 0, 1)),
    ((8.2, DECK_AFT + 0.14, -25.0), (0, 1, 0), (0, 0, 1)),
]


def rcs_quads():
    v = Volume('rcs_quads', bevel=0.02, cull=False)
    for p, n, up in RCS:
        for sx in (1, -1):
            if n == 'flank':
                z = p[2]
                pp, nn = V((sx * fX(z), p[1], z)), flank_n(z, sx)
            else:
                pp, nn = V((sx * p[0], p[1], p[2])), V((sx * n[0], n[1], n[2]))
            rcs_quad(v.bm, pp, nn, up)
    return v


def pylons():
    vols = []
    for sx in (1, -1):
        v = Volume(f'pylon_{"p" if sx > 0 else "s"}', bevel=0.08)
        root = [(2.5, -3.35), (1.4, -0.2), (-12.4, -0.2), (-13.5, -3.35), (-12.4, -6.5), (1.4, -6.5)]
        tip = [(0.6, -3.3), (-0.4, -1.15), (-10.4, -1.15), (-11.4, -3.3), (-10.4, -5.4), (-0.4, -5.4)]
        K.loft(v.bm, [K.ring3(root, 'zy', sx * 12.6), K.ring3(tip, 'zy', sx * 17.6)], zone=Z['paint'])
        K.solid(v.bm)
        vols.append(v)
    return vols




def sp_ring(z, d=0.0, side=1, w=None, h=None, c=None):
    p = K.offset_poly(K.chamfer_rect(side * SP['x'], SP['y'], w or SP['w'], h or SP['h'], c or SP['c']), d)
    return [V((x, y, z)) for x, y in p]


def sponsons():
    vols = []
    for sx in (1, -1):
        v = Volume(f'sponson_{"p" if sx > 0 else "s"}', bevel=0.08)
        rings = [sp_ring(SP['z0'] - 0.3, -0.9, sx), sp_ring(SP['z0'], 0, sx), sp_ring(SP['z1'], 0, sx),
                 sp_ring(SP['nose'], 0, sx, w=2.9, h=3.3, c=0.7)]
        K.loft(v.bm, rings, zone=Z['paint'])
        K.solid(v.bm)
        cx, cy = sx * SP['x'], SP['y']
        # outboard vent bay (louvred) aft on the outboard face
        xo = sx * (SP['x'] + SP['w'] / 2)
        K.box(v.cutters, (xo, cy, -9.9), (0.6, 2.6, 4.6), zone=Z['recess'])
        v.adds.append(('fins', lambda bm, xo=xo, sx=sx, cy=cy: [K.box(bm, (xo - sx * 0.16, cy, z), (0.3, 2.5, 0.06), zone=Z['fin']) for z in np.arange(-12.0, -7.7, 0.27)]))
        vols.append(v)
        col = Volume(f'sponson_trim_{"p" if sx > 0 else "s"}', bevel=0.04)
        for z0, z1 in ((-13.1, -12.3), (-1.0, -0.4)):
            K.loft(col.bm, [sp_ring(z0, 0.1, sx), sp_ring(z1, 0.1, sx)], zone=Z['trim'])
        # equipment box on the outboard face (sets the beam, x 23.45) and hatch plates on top / bottom
        K.plate(col.bm, (xo, cy + 0.2, -3.6), (sx, 0, 0), (0, 1, 0), 3.2, 2.2, 0.3, ch=0.07, back=0.3, zone=Z['trim'])
        for zc, w in ((-9.0, 3.2), (-3.4, 2.4)):
            K.plate(col.bm, (cx, cy + SP['h'] / 2, zc), (0, 1, 0), (0, 0, 1), 2.4, w, 0.1, ch=0.04, back=0.2, zone=Z['trim'])
            K.plate(col.bm, (cx, cy - SP['h'] / 2, zc), (0, -1, 0), (0, 0, 1), 2.4, w, 0.1, ch=0.04, back=0.2, zone=Z['trim'])
        # bell collar round the kit bell-S (exit z -16.64, back -13.46)
        K.cyl(col.bm, (cx, SBELL['y'], -13.5), (cx, SBELL['y'], -14.35), 1.72, r1=1.66, n=32, zone=Z['metal'])
        K.solid(col.bm)
        vols.append(col)
    return vols


def guns():
    """Twin railgun on each sponson nose (blueprint: mantlet z 1.9-5.4, twin barrels r 0.42 at
    y -2.95 / -3.9 to z 14.4, slotted muzzle block to z 17.86)."""
    vols = []
    for sx in (1, -1):
        v = Volume(f'gun_{"p" if sx > 0 else "s"}', bevel=0.04)
        cx, cy = sx * SP['x'], SP['y']
        K.stack(v.bm, [(K.chamfer_rect(cx, cy, 2.3, 2.8, 0.45), 1.6), (K.chamfer_rect(cx, cy, 2.3, 2.8, 0.45), 4.6),
                       (K.chamfer_rect(cx, cy, 1.9, 2.4, 0.4), 5.4)], 'xy', zone=Z['trim'])
        K.cyl(v.bm, (cx, cy, 5.2), (cx, cy, 7.2), 0.95, r1=0.9, n=24, zone=Z['trim'])
        K.cyl(v.bm, (cx, cy, 7.0), (cx, cy, 7.5), 1.02, n=24, zone=Z['metal'])
        for by in (cy + 0.475, cy - 0.475):
            K.cyl(v.bm, (cx, by, 7.2), (cx, by, 14.6), 0.42, r1=0.38, n=20, zone=Z['nozzle'])
        # barrel clamps
        for zc in (9.8, 12.4):
            K.stack(v.bm, [(K.chamfer_rect(cx, cy, 1.05, 2.0, 0.3), zc - 0.2), (K.chamfer_rect(cx, cy, 1.05, 2.0, 0.3), zc + 0.2)], 'xy', zone=Z['trim'])
        K.solid(v.bm)
        vols.append(v)
        m = Volume(f'muzzle_{"p" if sx > 0 else "s"}', bevel=0.04)
        K.stack(m.bm, [(K.chamfer_rect(cx, cy, 1.25, 2.1, 0.35), 14.3), (K.chamfer_rect(cx, cy, 1.45, 2.3, 0.4), 14.7),
                       (K.chamfer_rect(cx, cy, 1.45, 2.3, 0.4), 17.5), (K.chamfer_rect(cx, cy, 1.3, 2.15, 0.35), 17.86)], 'xy', zone=Z['trim'])
        K.solid(m.bm)
        for by in (cy + 0.5, cy - 0.5):
            K.cyl(m.cutters, (cx, by, 16.2), (cx, by, 18.5), 0.3, n=16, zone=Z['dark'])
        # side slots of the brake
        for zc in (15.3, 16.2):
            K.box(m.cutters, (cx, cy, zc), (2.0, 1.5, 0.3), zone=Z['dark'])
        vols.append(m)
    return vols


def ventral_keel():
    v = Volume('ventral', bevel=0.07)
    side = [(-22.6, -6.0), (-22.6, -6.9), (-19.8, -8.55), (-13.4, -9.2), (-12.2, -9.2), (-11.6, -8.6), (-11.6, -6.0)]
    # (z, y) side profile extruded x -3.4..3.4
    K.loft(v.bm, [[V((3.4, y, z)) for z, y in side], [V((-3.4, y, z)) for z, y in side]], zone=Z['belly'])
    K.solid(v.bm)
    return v


def chin_ball():
    v = Volume('chin', bevel=0.03)
    c = (0, -6.35, 30.6)
    prof = [(math.sin(t) * 2.95, -math.cos(t) * 2.95) for t in np.linspace(0.02, math.pi * 0.62, 11)]
    K.lathe(v.bm, (c[0], c[1], c[2]), (0, 1, 0), [(r, t) for r, t in prof], n=32, zone=Z['metal'])
    K.cyl(v.bm, (0, -6.9, 30.6), (0, -5.6, 30.6), 3.2, n=32, zone=Z['trim'])
    K.solid(v.bm)
    return v


def bow_sensors():
    v = Volume('bow_sensors', bevel=0.03)
    for sx in (1, -1):
        K.lathe(v.bm, (sx * 3.15, -2.55, BOW_PLATE - 0.1), (0, 0, 1), [(1.05, 0.0), (1.05, 0.35), (0.92, 0.45), (0.75, 0.45), (0.72, 0.3), (0.02, 0.3)], n=28, zone=Z['metal'])
    K.stack(v.bm, [(K.chamfer_rect(0, -2.4, 2.9, 1.9, 0.25), BOW_PLATE - 0.1), (K.chamfer_rect(0, -2.4, 2.9, 1.9, 0.25), BOW_PLATE + 0.3)], 'xy', zone=Z['metal'])
    K.solid(v.bm)
    for sx in (1, -1):
        K.cyl(v.cutters, (sx * 3.15, -2.55, BOW_PLATE + 0.15), (sx * 3.15, -2.55, BOW_PLATE + 1.0), 0.66, n=28, zone=Z['glass'])
    K.box(v.cutters, (0, -2.4, BOW_PLATE + 0.35), (2.3, 1.3, 0.3), zone=Z['glass'])
    return v


def thrust_hubs():
    """Bell mounts: a hub from the socket floor into the kit bell's back, a flange and eight struts
    (blueprint: a ring of rods round each bell neck)."""
    v = Volume('hubs', bevel=0.04, cull=False)
    back = BELL['exit'] + 8.12 * BELL['scale']        # kit bell back plane
    floor = STERN_PLATE + 0.85
    for sx in (1, -1):
        cx, cy = sx * BELL['x'], BELL['y']
        K.cyl(v.bm, (cx, cy, floor + 0.1), (cx, cy, back - 0.45), 2.35, r1=2.2, n=32, zone=Z['metal'])
        K.cyl(v.bm, (cx, cy, STERN_PLATE - 0.15), (cx, cy, STERN_PLATE - 0.55), 3.25, n=40, zone=Z['trim'])
        # clamp band round the bell neck and eight struts from the back flange to it
        neck = BELL['exit'] + 4.45 * BELL['scale']
        K.cyl(v.bm, (cx, cy, neck - 0.4), (cx, cy, neck + 0.4), 2.62, n=40, zone=Z['trim'])
        for i in range(8):
            a = 2 * math.pi * (i + 0.5) / 8
            p0 = V((cx + 3.95 * math.cos(a), cy + 3.95 * math.sin(a), back - 0.3))
            p1 = V((cx + 2.7 * math.cos(a), cy + 2.7 * math.sin(a), neck + 0.1))
            K.cyl(v.bm, p0, p1, 0.17, n=8, zone=Z['metal'])
            K.cyl(v.bm, p1 - (p1 - p0).normalized() * 0.6, p1 + (p1 - p0).normalized() * 0.1, 0.26, n=8, zone=Z['metal'])
    K.solid(v.bm)
    return v


def grab(bm, a, b, n, h=0.16, r=0.035):
    """Grab rail from a to b standing h off a surface with normal n (two posts and a bar)."""
    a, b, n = V(a), V(b), V(n).normalized()
    K.cyl(bm, a - n * 0.05, a + n * h, r, n=6, zone=Z['metal'])
    K.cyl(bm, b - n * 0.05, b + n * h, r, n=6, zone=Z['metal'])
    K.cyl(bm, a + n * h - (b - a).normalized() * r, b + n * h + (b - a).normalized() * r, r, n=6, zone=Z['metal'])


def deck_details():
    vols = []
    v = Volume('deck_plates', bevel=0.035)
    # spine hatches (blueprint: six oval hatches in two rows, z -15..-5)
    for sx in (1, -1):
        for zc in (-14.2, -10.2, -6.2):
            K.stack(v.bm, [(K.chamfer_rect(sx * 1.6, zc, 1.5, 1.05, 0.34), SPINE_Y - 0.1), (K.chamfer_rect(sx * 1.6, zc, 1.5, 1.05, 0.34), SPINE_Y + 0.1),
                           (K.chamfer_rect(sx * 1.6, zc, 1.36, 0.91, 0.28), SPINE_Y + 0.13)], 'xz', zone=Z['deck'])
    # aft deck: two equipment boxes forward of the domes, a transverse hatch
    for sx in (1, -1):
        K.stack(v.bm, [(K.chamfer_rect(sx * 3.9, -20.1, 2.4, 1.6, 0.2), DECK_AFT - 0.1), (K.chamfer_rect(sx * 3.9, -20.1, 2.4, 1.6, 0.2), DECK_AFT + 0.62)], 'xz', zone=Z['metal'])
    K.plate(v.bm, (0, DECK_AFT, -22.2), (0, 1, 0), (0, 0, 1), 4.4, 1.7, 0.1, ch=0.04, back=0.2, zone=Z['deck'])
    # forward deck: hatch plates beside the bridge, bow deck hatch
    for sx in (1, -1):
        for zc in (7.0, 20.8):
            y = top_y(zc)
            nn = V((0, 1, (top_y(zc - 0.5) - top_y(zc + 0.5)))).normalized()
            K.plate(v.bm, (sx * 5.9, y, zc), nn, (0, 0, 1), 2.1, 2.6 if zc < 10 else 2.0, 0.1, ch=0.04, back=0.25, zone=Z['deck'])
    # belly plates (blueprint: four 2 x 2 m access plates, 0.33 proud) and the keel strip
    for sx in (1, -1):
        for zc in (-8.0, 3.5):
            K.plate(v.bm, (sx * 5.3, -10.07, zc), (0, -1, 0), (0, 0, 1), 2.0, 2.0, 0.3, ch=0.07, back=0.2, zone=Z['belly'])
    K.solid(v.bm)
    vols.append(v)
    # gold MLI foil patches (concept: one forward of the port grille, one aft on the starboard deck)
    f = Volume('foil', bevel=0.02)
    K.plate(f.bm, (5.4, 5.8, 1.1), (0, 1, 0), (0, 0, 1), 2.3, 1.7, 0.07, ch=0.02, back=0.15, zone=Z['foil'])
    K.plate(f.bm, (-5.2, DECK_AFT, -22.3), (0, 1, 0), (0, 0, 1), 2.2, 1.6, 0.07, ch=0.02, back=0.15, zone=Z['foil'])
    K.solid(f.bm)
    vols.append(f)
    # grab rails
    g = Volume('grabs', bevel=0.0, cull=False)
    for sx in (1, -1):
        for z, y in DOORS:           # beside each crew door (hinge side and handle side)
            n = flank_n(z, sx)
            t = V((-n.z, 0, n.x)) * sx
            for s in (-1, 1):
                c = V((sx * fX(z), y, z)) + t * s * 1.3
                grab(g.bm, c + V((0, -0.7, 0)), c + V((0, 0.7, 0)), n)
        for zc in (-12.2, -8.2):     # along the spine, between the hatches
            grab(g.bm, (sx * 3.0, SPINE_Y, zc - 0.65), (sx * 3.0, SPINE_Y, zc + 0.65), (0, 1, 0))
        grab(g.bm, (sx * 2.3, SPINE_Y, 9.2), (sx * 2.3, SPINE_Y, 10.5), (0, 1, 0))      # bridge roof
        for zc in (-6.0, -2.0):       # sponson top walkway
            grab(g.bm, (sx * (SP['x'] - 1.6), SP['y'] + SP['h'] / 2, zc - 0.65), (sx * (SP['x'] - 1.6), SP['y'] + SP['h'] / 2, zc + 0.65), (0, 1, 0))
        grab(g.bm, (sx * 8.4, DECK_AFT, -22.9), (sx * 8.4, DECK_AFT, -21.6), (0, 1, 0))  # aft deck corners
    vols.append(g)
    return vols


# ------------------------------------------------------------------------------------------
# build
# ------------------------------------------------------------------------------------------
def build(args):
    t0 = time.time()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    K.zone_materials()
    hull = hull_body()
    door_bays(hull)
    grille_bays(hull)
    rcs_cluster(hull)
    vols = [hull, stern_collar(), bridge(), *pylons(), *sponsons(), *guns(), ventral_keel(), chin_ball(), bow_sensors(), thrust_hubs(), applique(), rcs_quads(), *deck_details()]
    obs = []
    for v in vols:
        ob = v.to_object()
        ob['bevel'] = v.bevel
        ob['angle'] = v.angle
        ob['cull'] = v.cull
        ob['small'] = v.name in SMALL
        if len(v.cutters.faces):
            cut = v.to_object(v.cutters, v.name + '_cut')
            K.boolean(ob, cut)
            bpy.data.objects.remove(cut)
        obs.append(ob)
        for nm, fn in v.adds:
            bm = bmesh.new()
            fn(bm)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            vv = Volume(f'{v.name}_{nm}')
            ob2 = vv.to_object(bm, f'{v.name}_{nm}')
            ob2['bevel'] = 0.012 if nm in ('fins', 'louvres') else 0.025
            ob2['angle'] = 30.0
            ob2['cull'] = False
            ob2['small'] = True
            obs.append(ob2)
    K.log(f'volumes: {len(obs)} objects, {sum(K.count_tris(o) for o in obs)} tris before bevel ({time.time() - t0:.1f}s)')
    if not args.get('no_cull'):
        K.cull_hidden(obs)
    for ob in obs:
        K.finish(ob, ob['bevel'], ob['angle'])
        a = ob.data.attributes.new('small', 'INT', 'FACE')
        a.data.foreach_set('value', [1 if ob.get('small') else 0] * len(ob.data.polygons))
    hullob = K.join(obs, 'hull')
    K.log(f'joined: {K.count_tris(hullob)} tris ({time.time() - t0:.1f}s)')
    return hullob


SMALL = {'grabs', 'hubs', 'chin', 'bow_sensors', 'rcs_quads'}   # fine parts: UV islands at SMALL_UV of the hull density
SMALL_UV = 0.4


def unwrap(ob, angle=50.0, margin=0.001):
    """common.unwrap with the fine parts (louvres, fins, grab rails, struts, sensor lenses: small,
    uniform, mostly in shadow) packed at SMALL_UV of the hull's texel density, so the big plated
    faces get the texels. Returns the plated-hull density (px per metre at 4096)."""
    import math as _m
    vl = bpy.context.view_layer
    for o in vl.objects:
        o.select_set(False)
    ob.select_set(True)
    vl.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=angle * K.DEG, island_margin=margin, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    me = ob.data
    small = np.zeros(len(me.polygons), np.int32)
    me.attributes['small'].data.foreach_get('value', small)
    uv = me.uv_layers.active.data
    co = np.zeros(len(uv) * 2, np.float32)
    uv.foreach_get('uv', co)
    co = co.reshape(-1, 2)
    for p in me.polygons:
        if small[p.index]:
            li = list(p.loop_indices)
            co[li] *= SMALL_UV
    uv.foreach_set('uv', co.ravel())
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(rotate=True, margin=margin, shape_method='CONCAVE')
    bpy.ops.object.mode_set(mode='OBJECT')
    uv = me.uv_layers.active.data
    a3 = {0: 0.0, 1: 0.0}; a2 = {0: 0.0, 1: 0.0}
    for p in me.polygons:
        k = int(small[p.index])
        a3[k] += p.area
        pts = [uv[i].uv for i in p.loop_indices]
        a2[k] += abs(sum(pts[i].x * pts[(i + 1) % len(pts)].y - pts[(i + 1) % len(pts)].x * pts[i].y for i in range(len(pts)))) / 2
    return {'surface_m2': round(a3[0] + a3[1], 1), 'small_m2': round(a3[1], 1), 'uv_fill': round(a2[0] + a2[1], 3),
            'px_per_m_at_4096': round(4096 * _m.sqrt(a2[0] / a3[0]), 1), 'small_px_per_m_at_4096': round(4096 * _m.sqrt(a2[1] / max(a3[1], 1e-6)), 1)}


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    work = os.path.abspath(argv[0])
    opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d
    stage = opt('--stage', 'all')
    os.makedirs(work, exist_ok=True)
    blend = os.path.join(work, 'fighter-hull.blend')
    maps = os.path.join(work, 'maps.npz')
    tex = int(opt('--tex', 4096))
    if stage in ('all', 'model'):
        ob = build({'no_cull': '--no-cull' in argv})
        info = unwrap(ob, margin=float(opt('--margin', 0.001)))
        K.log('uv', info)
        bpy.ops.wm.save_as_mainfile(filepath=blend)
        if '--preview' in argv:
            import preview
            preview.shots(ob, os.path.join(work, 'preview'), views=(opt('--views').split(',') if opt('--views') else None))
        json.dump({'tris': K.count_tris(ob), **info}, open(os.path.join(work, 'model.json'), 'w'), indent=1)
        if stage == 'model' and '--bake' not in argv:
            return
        m = K.bake_maps(ob, size=tex, ao_size=int(opt('--ao', 2048)), threads=int(opt('--threads', 4)))
        np.savez_compressed(maps, **m)
    if stage in ('all', 'paint'):
        import fighter_paint
        bpy.ops.wm.open_mainfile(filepath=blend)
        ob = bpy.data.objects['hull']
        m = dict(np.load(maps))
        spec = fighter_paint.spec()
        spec['px_per_m'] = json.load(open(os.path.join(work, 'model.json')))['px_per_m_at_4096'] * tex / 4096
        base, orm = fighter_paint.paint(m, spec=spec, out=work)
        K.set_final_material(ob, base, orm, normal_png=spec.get('_normal_png'))
        glb = os.path.join(work, 'fighter-hull.glb')
        K.export_glb(ob, glb)
        K.log('wrote', glb, os.path.getsize(glb))


if __name__ == '__main__':
    main()


# ------------------------------------------------------------------------------------------
# ship-module draft (module.py): fixed asset fields, light roles, surfaces to measure
# ------------------------------------------------------------------------------------------
MODULE = {
    'header': """// Fighter F-402 — v3 REMODEL: clean hard-surface hull (tools/blender/hulls/fighter.py) rebuilt from
// measurements of the fal / Tripo H3.1 blueprint (the v5 true-size re-detail), textured in texture space
// (tools/blender/hulls/fighter_paint.py over paint.py: light paint, plating seams and tone, PATINA plate
// tone, AO grime, edge wear, orange bands, the F-402 stencil) and assembled with the Blender parts kit
// (tools/blender/specs/fighter-v3.json via tools/blender/assemble.py).
// The GLB is already in the ship frame (metres, bow +Z, dorsal +Y, port +X): rotate [0, 0, 0], length =
// the assembled bbox length. Node 'hull' is the hull, 'parts_*' the kit parts (hullNodes).
// Beam = the equipment boxes on the sponsons' outboard faces (x +-23.45), height = the dorsal whip
// antenna (y +10.48) and the belly access plates (y -10.40), length = bow lip to the bell exits.
// Engines: kit bells (bell-L x1.014 main pair, r 3.55, exit z -35.856; bell-S x0.979 at the aft end
// of each sponson, r 1.37, exit z -16.64) with the kit's documented engine entry times that scale.
// Lights: at the lenses of the kit nav-light housings.""",
    'meta': {
        'name': 'Petrel-class fighter', 'designation': 'F-402', 'crew': 'about 40',
        'blurb': 'Heavy space-superiority fighter: a faceted armoured pod with a low bridge block glazed in a band of small panes, twin fusion bells in an armoured stern block and a twin railgun on each flank sponson, each sponson ending in a small secondary drive bell.',
    },
    'asset': {
        'glb': './assets/ships/fighter.glb', 'generator': 'tools/blender/hulls/fighter.py (remodel of the tripo3d/h3.1/multiview-to-3d hull) + tools/blender/assemble.py',
        'concept': './assets/concepts/fighter.webp', 'beauty': './assets/concepts/fighter-beauty.webp',
        'rotate': [0, 0, 0], 'hullNodes': ['hull'],
        # remodel paint is lighter than the generated textures: gain 0.05 matches the fleet grey;
        # kit glass gets a dim warm interior light (livery.js glassGlow, opt-in)
        'livery': {'gain': 0.05, 'glassGlow': [0.06, 0.055, 0.046], 'glassLit': 0.3},
        'detail': {'set': 'hull', 'tile': 6, 'normalStrength': 0.6, 'roughAmount': 0.5, 'cavity': 0.2},
    },
    # in navlight placement order
    'lights': [
        {'color': 'red', 'note': 'steady sidelights on the outboard face of each sponson (beam extremity): red port, green starboard'},
        {'color': 'green'},
        {'color': 'white', 'blink': {'period': 1.3, 'duty': 0.1}, 'note': 'anti-collision strobes, alternating: dorsal spine aft and keel'},
        {'color': 'white', 'blink': {'period': 1.3, 'duty': 0.1, 'phase': 0.5}},
        {'color': 'white', 'note': 'steady stern light on the stern plate between the bell sockets'},
    ],
    'surfaces': {
        'flank-fore-port': {'centre': [12.2, -3.2, 10.5], 'normal': [0.99, 0, 0.145], 'u': [-0.145, 0, 0.99], 'width': 7.0, 'height': 3.0, 'note': 'vertical flank forward of the pylon (crew door at z 8.6)'},
        'flank-fore-stbd': {'centre': [-12.2, -3.2, 10.5], 'normal': [-0.99, 0, 0.145], 'u': [-0.145, 0, -0.99], 'width': 7.0, 'height': 3.0},
        'chamfer-port': {'centre': [10.7, 3.2, -8.5], 'normal': [0.8, 0.6, 0], 'u': [0, 0, 1], 'width': 16.0, 'height': 5.0, 'note': 'upper chamfer above the pylon: F-402 stencil, port row'},
        'chamfer-stbd': {'centre': [-10.7, 3.2, -8.5], 'normal': [-0.8, 0.6, 0], 'u': [0, 0, -1], 'width': 16.0, 'height': 5.0},
        'dorsal-deck': {'centre': [0, 6.98, -10.0], 'normal': [0, 1, 0], 'u': [0, 0, 1], 'width': 5.0, 'height': 14.0, 'note': 'dorsal spine between the radiator bays (six hatches)'},
        'bow-deck': {'centre': [0, 1.5, 25.0], 'normal': [0, 0.985, 0.17], 'u': [0, -0.17, 0.985], 'width': 9.0, 'height': 12.0, 'note': 'sloping forward deck ahead of the bridge'},
        'bridge-glazing': {'centre': [0, 4.0, 15.9], 'normal': [0, 0.8, 0.6], 'u': [1, 0, 0], 'width': 5.5, 'height': 1.6, 'note': 'bridge glazing recess on the raked front face, kit panes x0.7'},
        'belly': {'centre': [0, -10.07, -2.0], 'normal': [0, -1, 0], 'u': [0, 0, 1], 'width': 16.0, 'height': 10.0, 'note': 'flat belly'},
        'stern-plate': {'centre': [0, 4.0, -26.05], 'normal': [0, 0, -1], 'u': [-1, 0, 0], 'width': 5.0, 'height': 1.2, 'note': 'recessed stern plate above the bell sockets'},
        'sponson-outboard-port': {'centre': [23.15, -3.35, -6.8], 'normal': [1, 0, 0], 'u': [0, 0, 1], 'width': 1.6, 'height': 2.8, 'note': 'sponson outboard face between the vent bay and the equipment box'},
        'sponson-outboard-stbd': {'centre': [-23.15, -3.35, -6.8], 'normal': [-1, 0, 0], 'u': [0, 0, -1], 'width': 1.6, 'height': 2.8},
    },
}
