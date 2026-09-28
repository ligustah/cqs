"""Warden-class corvette K-214: clean hard-surface hull, rebuilt from measurements of the fal /
Tripo v7 blueprint (see README.md in this folder for the method).

    <blender-python> tools/blender/hulls/corvette.py <workdir> [--stage all|model|paint]
                     [--tex 4096] [--ao 2048] [--threads 4] [--no-cull] [--preview]

Stages: model -> <workdir>/corvette-hull.blend (volumes built, booleans, culled, bevelled,
joined, UV-unwrapped) and <workdir>/maps.npz (baked position / normal / zone / AO / curvature);
paint -> <workdir>/base.png, orm.png (paint.py) and <workdir>/corvette-hull.glb (node 'hull',
ship frame, not re-centred; assemble.py adds the kit parts: specs/corvette-v3.json).

Ship frame, metres: bow +Z, dorsal +Y, port +X. All dimensions below are measured on the
blueprint (measure.py: sections every 2 m, ortho views) unless noted as a design choice.
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

# ------------------------------------------------------------------------------------------
# key dimensions (blueprint, ship frame)
# ------------------------------------------------------------------------------------------
BOW_Z = 54.05            # bow frame lip (bbox front)
STERN_Z = -49.0          # hull loft end; stern frame lip at STERN_LIP
STERN_LIP = -49.55
STERN_PLATE = -49.25     # recessed stern plate (bell bosses stand on it)
DECK_Y = -1.46           # main deck / walkway
ROOF_Y = 3.45            # deckhouse roof
BELT_TOP = -11.6         # armour belt top edge (design: continuous belt from the stern to the bow taper)
BELT = 0.22              # belt proud of the flank
TAPER0 = 19.0            # bow taper starts (plan kink)
TAPER = 0.2265           # flank half-width loss per metre forward of TAPER0


def fX(z):
    if z >= TAPER0:
        return 16.15 - TAPER * (z - TAPER0)
    if z >= 0:
        return 16.15
    if z >= -30:
        return 16.15 - 0.3 * (-z / 30)
    return 15.85 - 0.35 * ((-30 - z) / 19)


def pw(pts, z):
    """piecewise linear through [(z, v), ...]"""
    if z <= pts[0][0]:
        return pts[0][1]
    for (z0, a), (z1, b) in zip(pts[:-1], pts[1:]):
        if z <= z1:
            return a + (b - a) * (z - z0) / (z1 - z0)
    return pts[-1][1]


def kY(z):   # keel line: stern undercut, flat belly, rising forefoot
    return pw([(-49.0, -17.3), (-45.0, -17.45), (-42.5, -19.3), (-38.5, -21.1), (-33.0, -23.05), (18.0, -23.05), (53.0, -18.9)], z)


def dY(z):   # deck line
    return pw([(27.5, DECK_Y), (41.5, -3.75), (53.0, -4.9)], z)


def sY(z):   # flank top (shoulder chamfer lower edge)
    return pw([(-49.0, -4.0), (-40.0, -4.5), (TAPER0, -4.5), (53.0, -8.3)], z)


def dX(z):   # deck edge (shoulder chamfer upper edge)
    if z >= TAPER0:
        return fX(z) - 2.35
    return pw([(-49.0, 13.1), (-29.0, 13.1), (TAPER0, 13.55)], z)


def fB(z):   # flank bottom (lower chamfer upper edge)
    if z >= TAPER0:
        return pw([(TAPER0, -17.0), (53.0, -15.2)], z)
    return max(-17.0, kY(z) + 1.7, pw([(-49.0, -15.6), (-44.0, -17.0)], z))


def belt(z):
    return pw([(18.5, BELT), (21.0, 0.01)], z)


def kX(z):
    return fX(z) + belt(z) - max(pw([(-49.0, 3.3), (-43.0, 2.6)], z), 0.64 * (fB(z) - kY(z)))


def half_profile(z):
    """Half cross-section from the deck centre down the port side to the keel centre."""
    f, b = fX(z), belt(z)
    return [(0.0, dY(z)), (dX(z), dY(z)), (f, sY(z)), (f, BELT_TOP + b), (f + b, BELT_TOP), (f + b, fB(z)),
            (kX(z), kY(z)), (0.0, kY(z))]


SEG_ZONE = ['deck', 'paint', 'paint', 'paint', 'paint', 'belly', 'belly']  # per half-profile segment


def ring_zones(n_half=8):
    segs = n_half - 1
    out = []
    for j in range(2 * segs):
        out.append(SEG_ZONE[j] if j < segs else SEG_ZONE[2 * segs - 1 - j])
    return out


# ------------------------------------------------------------------------------------------
# volumes
# ------------------------------------------------------------------------------------------
def hull_body():
    vol = Volume('hull_body', bevel=0.10)
    bm = vol.bm
    stations = [STERN_Z, -46.5, -44.5, -42.5, -40.0, -37.0, -33.0, -30.0, 0.0, 18.0, 18.5, TAPER0, 21.0, 27.5, 33.0, 40.0, 46.5, 53.0]
    rings = [[V((x, y, z)) for x, y in K.mirror_half(half_profile(z))] for z in stations]
    # bow frame: lip ring, inner lip, recessed torpedo plate
    p53 = K.mirror_half(half_profile(53.0))
    lip = K.offset_poly(p53, -0.15)
    inner = K.offset_poly(p53, -0.85)
    rings_bow = [[V((x, y, BOW_Z)) for x, y in lip], [V((x, y, BOW_Z)) for x, y in inner], [V((x, y, 52.75)) for x, y in inner]]
    # stern frame
    ps = K.mirror_half(half_profile(STERN_Z))
    s_lip = K.offset_poly(ps, -0.12)
    s_in = K.offset_poly(ps, -0.8)
    rings_st = [[V((x, y, STERN_PLATE)) for x, y in s_in], [V((x, y, STERN_LIP)) for x, y in s_in], [V((x, y, STERN_LIP)) for x, y in s_lip]]
    allr = rings_st + rings + rings_bow
    grid, caps = K.loft(bm, allr, zone=Z['paint'])
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
    return vol


def keel_strip():
    vol = Volume('keel', bevel=0.06)
    prof = [(-33.8, -22.7), (-31.8, -23.25), (15.5, -23.25), (17.5, -22.7)]  # (z, y) side profile
    K.prism(vol.bm, prof, 'zy', -1.6, 1.6, zone=Z['belly'])
    K.solid(vol.bm)
    return vol


# deckhouse plan outlines (x, z), half from the aft centre forward (A at the deck, D at the roof)
DH_A = [(0, -38.8), (5.1, -38.8), (10.35, -31.6), (10.4, 15.8), (9.3, 21.2), (5.3, 26.6), (0, 28.0)]
DH_D = [(0, -35.3), (3.7, -35.3), (7.9, -30.4), (7.9, 15.8), (6.95, 19.6), (3.9, 22.6), (0, 23.6)]
GLAZE = (0.65, 2.05, 0.9, 11.0)   # bridge glazing band: y0, y1, recess depth, aft end z


def dh_outline(y):
    t = (y - DECK_Y) / (ROOF_Y - DECK_Y)
    return [(a[0] + (d[0] - a[0]) * t, a[1] + (d[1] - a[1]) * t) for a, d in zip(DH_A, DH_D)]


def deckhouse():
    vol = Volume('deckhouse', bevel=0.09)
    A = K.mirror_half(DH_A)
    D = K.mirror_half(DH_D)
    K.stack(vol.bm, [(A, DECK_Y - 0.6), (A, DECK_Y), (D, ROOF_Y)], 'xz', zone=Z['paint'])
    K.solid(vol.bm)
    # glazing recess: a C-shaped band from the port side (z = 11) round the nose to starboard,
    # its inner edge the back wall (vertical), 0.5 m in from the sloped face at the band top
    y0, y1, depth, zend = GLAZE
    o = dh_outline(y1)
    side_x = o[3][0]
    half = [(side_x, zend)] + [p for p in o[3:]]
    line = half + [(-x, z) for x, z in reversed(half[:-1])]
    # walking from port aft -> nose -> stbd aft in the (x, z) plan, offset_open's left side is
    # the inside of the deckhouse
    inner = K.offset_open(line, depth, left=True)
    outer = K.offset_open(line, 3.0, left=False)
    poly = outer + list(reversed(inner))
    K.prism(vol.cutters, poly, 'xz', y0, y1, zone=Z['recess'])
    K.solid(vol.cutters)
    return vol


def bridge_director():
    vol = Volume('director', bevel=0.06)
    K.stack(vol.bm, [(K.chamfer_rect(0, 21.2, 2.8, 2.6, 0.5), ROOF_Y - 0.3), (K.chamfer_rect(0, 21.2, 2.8, 2.6, 0.5), ROOF_Y + 1.3),
                     (K.chamfer_rect(0, 21.2, 2.4, 2.2, 0.4), ROOF_Y + 1.6)], 'xz', zone=Z['paint'])
    K.solid(vol.bm)
    return vol


def roof_details():
    """Raised hatch plates on the deckhouse roof (between the turrets and the tower) and aft."""
    vol = Volume('roof_plates', bevel=0.04)
    for (x, z, w, h) in ((5.6, 12.0, 1.6, 2.4), (-5.6, 12.0, 1.6, 2.4), (0.0, 14.2, 2.4, 1.8)):
        K.plate(vol.bm, (x, ROOF_Y, z), (0, 1, 0), (0, 0, 1), w, h, 0.12, ch=0.05, back=0.2, zone=Z['paint'])
    # equipment boxes aft of the aft turret (concept: a foil-wrapped box and a grey cabinet)
    K.plate(vol.bm, (-1.7, ROOF_Y, -32.7), (0, 1, 0), (0, 0, 1), 2.2, 1.8, 1.5, ch=0.06, back=0.2, zone=Z['foil'])
    K.plate(vol.bm, (1.6, ROOF_Y, -32.5), (0, 1, 0), (0, 0, 1), 1.8, 1.4, 1.1, ch=0.08, back=0.2, zone=Z['metal'])
    K.solid(vol.bm)
    return vol


# tower (bridge tower): plan rectangles (x width, z length) with chamfered corners
def rect(zc, w, h, c):
    return K.chamfer_rect(0.0, zc, w, h, c)


def tower():
    vols = []
    t1 = Volume('tower_base', bevel=0.08)
    base = rect(-10.9, 15.8, 15.4, 1.6)
    top = rect(-11.015, 11.9, 10.57, 0.9)
    K.stack(t1.bm, [(base, ROOF_Y - 0.4), (base, ROOF_Y), (top, 6.9), (top, 9.4)], 'xz', zone=Z['paint'])
    K.solid(t1.bm)
    vols.append(t1)
    # bridge tier: glazing band leaning out (faces forward and down), recessed 0.3 m, all round
    t3 = Volume('tower_bridge', bevel=0.06)
    lean = 1.33 / 1.76
    y1, y2, y3, y4 = 10.64, 10.84, 12.2, 12.4
    AFT = -16.35

    def tier(d, inset=0.0):
        """bridge-tier plan at lean offset d (front and sides lean out, the aft face stays put)"""
        zf, hw = -5.72 + d - inset, 6.05 + d - inset
        za = AFT + inset
        return K.chamfer_rect(0.0, (zf + za) / 2, 2 * hw, zf - za, 1.0 + 0.4 * d)
    O1 = tier(0)
    O2, O3, O4 = tier((y2 - y1) * lean), tier((y3 - y1) * lean), tier((y4 - y1) * lean)
    O5 = tier((y4 - y1) * lean + 0.25)
    levels = [(rect(-11.015, 11.9, 10.57, 0.9), 9.3), (O1, y1), (O2, y2), (tier((y2 - y1) * lean, 0.3), y2), (tier((y3 - y1) * lean, 0.3), y3),
              (O3, y3), (O4, y4), (O5, y4), (O5, 12.85)]
    grid, caps = K.stack(t3.bm, levels, 'xz', zone=Z['paint'])
    for f in grid[3]:
        if f:
            f.material_index = Z['recess']
    K.solid(t3.bm)
    vols.append(t3)
    # mast block, neck, sensor block
    m = Volume('mast', bevel=0.06)
    K.stack(m.bm, [(rect(-12.4, 5.8, 6.2, 0.6), 12.7), (rect(-12.6, 4.8, 4.6, 0.5), 20.0)], 'xz', zone=Z['paint'])
    K.solid(m.bm)
    vols.append(m)
    n = Volume('mast_top', bevel=0.05)
    K.stack(n.bm, [(rect(-11.4, 3.2, 2.4, 0.3), 19.8), (rect(-11.4, 3.2, 2.4, 0.3), 21.5)], 'xz', zone=Z['paint'])
    # sensor block: MLI foil wrapped (concept: gold / silver foil on the mast top)
    K.stack(n.bm, [(rect(-11.5, 6.4, 3.0, 0.3), 21.4), (rect(-11.5, 6.4, 3.0, 0.3), 22.75), (rect(-11.5, 6.0, 2.6, 0.2), 23.05)], 'xz', zone=Z['foil'])
    K.solid(n.bm)
    vols.append(n)
    # yardarm (hexagonal section, tapered tips) and the swept aft sensor boom
    y = Volume('yardarm', bevel=0.04)
    sec = lambda zc, ch, yc, th: [(zc + ch / 2, yc), (zc + ch / 2 - 0.3, yc + th / 2), (zc - ch / 2 + 0.3, yc + th / 2), (zc - ch / 2, yc), (zc - ch / 2 + 0.3, yc - th / 2), (zc + ch / 2 - 0.3, yc - th / 2)]
    K.loft(y.bm, [K.ring3(sec(-13.0, 1.1, 14.9, 0.5), 'zy', -8.1), K.ring3(sec(-13.15, 2.6, 15.7, 1.2), 'zy', -2.0),
                  K.ring3(sec(-13.15, 2.6, 15.7, 1.2), 'zy', 2.0), K.ring3(sec(-13.0, 1.1, 14.9, 0.5), 'zy', 8.1)], zone=Z['paint'])
    # forward sensor housing on the mast front (blueprint: y 17.3-19.6, z -9.3..-8.4)
    K.stack(y.bm, [(K.chamfer_rect(0, -9.2, 2.6, 1.8, 0.25), 17.2), (K.chamfer_rect(0, -9.2, 2.6, 1.8, 0.25), 19.6)], 'xz', zone=Z['paint'])
    K.loft(y.bm, [K.ring3(K.chamfer_rect(0, 19.8, 1.1, 1.0, 0.2), 'xy', -13.8), K.ring3(K.chamfer_rect(0, 19.75, 0.7, 0.6, 0.12), 'xy', -19.6)], zone=Z['paint'])
    K.solid(y.bm)
    vols.append(y)
    # radome plinth on the platform (kit dome on top)
    d = Volume('dome_plinth', bevel=0.04)
    K.cyl(d.bm, (0, 12.7, -7.3), (0, 14.4, -7.3), 1.35, n=24, zone=Z['paint'])
    K.solid(d.bm)
    vols.append(d)
    return vols


# drive pods and pylons
POD = dict(x=29.55, y=-14.95, w=9.8, h=10.5, c=1.6, z0=-26.8, z1=-1.95, nose=-0.75)


def pod_ring(z, d=0.0, side=1):
    p = K.offset_poly(K.chamfer_rect(side * POD['x'], POD['y'], POD['w'], POD['h'], POD['c']), d)
    return [V((x, y, z)) for x, y in p]


def pods():
    vols = []
    for side in (1, -1):
        v = Volume(f'pod_{"p" if side > 0 else "s"}', bevel=0.09)
        rings = [pod_ring(-28.6, -1.4, side), pod_ring(POD['z0'], 0, side), pod_ring(POD['z1'], 0, side), pod_ring(POD['nose'], -1.5, side)]
        K.loft(v.bm, rings, zone=Z['paint'])
        K.solid(v.bm)
        cx, cy = side * POD['x'], POD['y']
        # intake: a round recess in the nose, 3.4 m deep
        K.cyl(v.cutters, (cx, cy, POD['nose'] + 3.0), (cx, cy, POD['nose'] - 3.4), 2.45, n=40, zone=Z['dark'])
        # radiator bay on the outboard face (fins added after the boolean)
        xo = side * (POD['x'] + POD['w'] / 2)
        K.box(v.cutters, (xo, POD['y'], -16.0), (0.9, 4.2, 13.2), zone=Z['recess'])
        K.solid(v.cutters)
        # intake centre body, radiator fins, collars, bell collar
        v.adds.append(('spike', lambda bm, cx=cx, cy=cy: K.lathe(bm, (cx, cy, POD['nose'] - 3.5), (0, 0, 1), [(1.55, -0.2), (1.55, 0.5), (0.9, 2.0), (0.25, 3.0), (0.02, 3.05)], n=24, zone=Z['metal'])))
        v.adds.append(('fins', lambda bm, xo=xo, side=side: [K.box(bm, (xo - side * 0.22, POD['y'], z), (0.44, 4.1, 0.07), zone=Z['fin']) for z in np.arange(-22.35, -9.6, 0.3)]))
        vols.append(v)
        col = Volume(f'pod_collars_{"p" if side > 0 else "s"}', bevel=0.04)
        for z0, z1 in ((-4.4, -5.2), (-23.2, -24.0)):
            K.loft(col.bm, [pod_ring(z0, 0.12, side), pod_ring(z1, 0.12, side)], zone=Z['trim'])
        # hatch plates on the pod top and bottom (blueprint: two panels on each face)
        for zc in (-8.5, -18.5):
            K.plate(col.bm, (cx, POD['y'] + POD['h'] / 2, zc), (0, 1, 0), (0, 0, 1), POD['w'] - 2 * POD['c'] - 1.2, 5.2, 0.1, ch=0.04, back=0.2, zone=Z['trim'])
            K.plate(col.bm, (cx, POD['y'] - POD['h'] / 2, zc), (0, -1, 0), (0, 0, 1), POD['w'] - 2 * POD['c'] - 1.2, 5.2, 0.1, ch=0.04, back=0.2, zone=Z['trim'])
        # bell collar round the kit bell (bell-L exit at z -34.6, body reaches z -26.5)
        K.cyl(col.bm, (cx, cy, -27.6), (cx, cy, -30.9), 4.2, r1=4.25, n=40, zone=Z['metal'])
        K.solid(col.bm)
        vols.append(col)
        # pylon: hexagonal section lofted from inside the hull flank to inside the pod
        py = Volume(f'pylon_{"p" if side > 0 else "s"}', bevel=0.09)
        root = [(-4.4, -8.6), (-5.8, -5.3), (-17.2, -5.3), (-18.6, -8.6), (-17.2, -12.2), (-5.8, -12.2)]
        tip = [(-5.8, -13.2), (-7.2, -9.4), (-15.8, -9.4), (-17.2, -13.2), (-15.8, -17.0), (-7.2, -17.0)]
        K.loft(py.bm, [K.ring3(root, 'zy', side * 15.4), K.ring3(tip, 'zy', side * 26.2)], zone=Z['paint'])
        K.solid(py.bm)
        vols.append(py)
    return vols


def stern_bosses():
    v = Volume('stern_bosses', bevel=0.06)
    K.cyl(v.bm, (0, -10.0, STERN_PLATE + 0.3), (0, -10.0, -50.3), 6.05, n=48, zone=Z['metal'])
    for sx in (1, -1):
        K.cyl(v.bm, (sx * 9.85, -5.44, STERN_PLATE + 0.3), (sx * 9.85, -5.44, -50.1), 2.95, n=32, zone=Z['metal'])
        K.cyl(v.bm, (sx * 9.8, -14.08, STERN_PLATE + 0.3), (sx * 9.8, -14.08, -50.1), 2.85, n=32, zone=Z['metal'])
    K.solid(v.bm)
    return v


def shoulder_tubes():
    """Two ribbed launcher tubes on the aft shoulders (blueprint: z -29.6..-37.4, r ~1.25)."""
    v = Volume('shoulder_tubes', bevel=0.04)
    for sx in (1, -1):
        c = (sx * 15.25, -2.95)
        K.lathe(v.bm, (c[0], c[1], -28.6), (0, 0, -1), [(1.0, 0.0), (1.2, 0.2), (1.2, 7.8), (1.0, 8.0)], n=24, zone=Z['paint'])
        for t0 in (1.2, 3.7, 6.2):
            K.cyl(v.bm, (c[0], c[1], -28.6 - t0), (c[0], c[1], -28.6 - t0 - 0.45), 1.36, n=24, zone=Z['trim'])
    K.solid(v.bm)
    return v


def bow_deck():
    v = Volume('bow_deck', bevel=0.05)
    nrm = V((0, 1, 0.158)).normalized()
    y_at = lambda z: dY(z)
    # large hatch plate
    K.plate(v.bm, (0, y_at(34.0), 34.0), nrm, (0, 0, 1), 7.4, 6.2, 0.14, ch=0.07, back=0.3, zone=Z['deck'])
    # round hatches beside the bridge nose (blueprint: circles at x +-9.3, z 27.5) and two small
    # flush hatches forward on the bow deck
    for sx in (1, -1):
        K.cyl(v.bm, (sx * 9.3, DECK_Y - 0.25, 27.3), (sx * 9.3, DECK_Y + 0.12, 27.3), 1.55, n=28, zone=Z['deck'])
        K.plate(v.bm, (sx * 4.6, y_at(41.0), 41.0), nrm, (0, 0, 1), 1.5, 2.0, 0.1, ch=0.04, back=0.3, zone=Z['deck'])
    # two vent ramps (wedges) with a dark louvre face aft
    for sx in (1, -1):
        x = sx * 3.5
        z0, z1 = 47.4, 53.0
        r0 = [V((x - 0.7, y_at(z0) - 0.3, z0)), V((x + 0.7, y_at(z0) - 0.3, z0)), V((x + 0.7, y_at(z0) + 0.9, z0)), V((x - 0.7, y_at(z0) + 0.9, z0))]
        r1 = [V((x - 0.7, y_at(z1) - 0.3, z1)), V((x + 0.7, y_at(z1) - 0.3, z1)), V((x + 0.7, y_at(z1) + 0.04, z1)), V((x - 0.7, y_at(z1) + 0.04, z1))]
        grid, caps = K.loft(v.bm, [r0, r1], zone=Z['paint'])
        caps[0].material_index = Z['dark']
    K.solid(v.bm)
    return v


def shoulder_bays(hull):
    """Vent bays on the shoulder chamfers (blueprint: slanted slots at z 6-17 and -40..-46):
    real 0.3 m recesses with slanted louvre fins."""
    for sx in (1, -1):
        for (z0, z1, zc_step) in ((6.2, 16.8, 1.15), (-46.4, -40.4, 1.15)):
            zc = (z0 + z1) / 2
            f, dx = fX(zc), dX(zc)
            p0, p1 = V((dx, DECK_Y)), V((f, sY(zc)))
            mid = (p0 + p1) / 2
            e = (p1 - p0).normalized()                      # down the slope, port side
            n = V((sx * abs(e.y), abs(e.x), 0)).normalized()  # outward
            up = V((-sx * abs(e.x), abs(e.y), 0))              # up the slope, toward the deck edge
            c = V((sx * mid.x, mid.y, zc))
            K.oriented_prism(hull.cutters, [(a, b) for a, b in ((-(z1 - z0) / 2, -1.2), ((z1 - z0) / 2, -1.2), ((z1 - z0) / 2, 1.2), (-(z1 - z0) / 2, 1.2))],
                             c, n, up, -0.3, 1.2, zone=Z['recess'])
            r, u, nn = K.basis(n, up)
            fins = []
            for zf in np.arange(z0 + 0.6, z1 - 0.4, zc_step):
                cc = V((sx * mid.x, mid.y, zf)) - n * 0.14
                # right (r) runs along z for the port side; tilt the fin 28 degrees in the plane
                a = 28 * K.DEG
                R = Matrix((r * math.cos(a) + u * math.sin(a), -r * math.sin(a) + u * math.cos(a), nn)).transposed()
                fins.append((cc, R))
            hull.adds.append(('louvres', lambda bm, fins=fins: [K.box(bm, cc, (0.10, 2.3, 0.28), R=R, zone=Z['fin']) for cc, R in fins]))


# door / airlock bays on the belt (design: 0.25 m margin round the kit frame)
DOORS = [(1.5,), (9.9,), (-39.5,)]
DOOR_Y = -13.6
AIRLOCK = (24.65, -13.45)


def flank_x(z):
    return fX(z) + belt(z)


def flank_n(z, side=1):
    if z >= TAPER0:
        n = V((1, 0, TAPER)).normalized()
    elif z < -30:
        n = V((1, 0, -0.35 / 19)).normalized()
    else:
        n = V((1, 0, 0))
    return V((side * n.x, 0, n.z))


def door_bays(hull):
    for sx in (1, -1):
        for (z,) in DOORS:
            c = V((sx * flank_x(z), DOOR_Y, z))
            K.oriented_prism(hull.cutters, K.chamfer_rect(0, 0, 1.95, 2.95, 0.12), c, flank_n(z, sx), (0, 1, 0), -0.32, 1.5, zone=Z['recess'])
        z, y = AIRLOCK
        c = V((sx * flank_x(z), y, z))
        K.oriented_prism(hull.cutters, K.chamfer_rect(0, 0, 3.05, 3.85, 0.2), c, flank_n(z, sx), (0, 1, 0), -0.4, 1.5, zone=Z['recess'])


# ------------------------------------------------------------------------------------------
# build
# ------------------------------------------------------------------------------------------
def build(args):
    t0 = time.time()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    K.zone_materials()
    hull = hull_body()
    door_bays(hull)
    shoulder_bays(hull)
    vols = [hull, keel_strip(), deckhouse(), bridge_director(), roof_details(), *tower(), *pods(), stern_bosses(), shoulder_tubes(), bow_deck()]
    obs = []
    for v in vols:
        ob = v.to_object()
        ob['bevel'] = v.bevel
        ob['angle'] = v.angle
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
            ob2['bevel'] = 0.015 if nm in ('fins', 'louvres') else 0.03
            ob2['angle'] = 30.0
            ob2['cull'] = False
            obs.append(ob2)
    K.log(f'volumes: {len(obs)} objects, {sum(K.count_tris(o) for o in obs)} tris before bevel ({time.time() - t0:.1f}s)')
    if not args.get('no_cull'):
        K.cull_hidden(obs)
    for ob in obs:
        K.finish(ob, ob['bevel'], ob['angle'])
    hullob = K.join(obs, 'hull')
    K.log(f'joined: {K.count_tris(hullob)} tris ({time.time() - t0:.1f}s)')
    return hullob


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    work = os.path.abspath(argv[0])
    opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d
    stage = opt('--stage', 'all')
    os.makedirs(work, exist_ok=True)
    blend = os.path.join(work, 'corvette-hull.blend')
    maps = os.path.join(work, 'maps.npz')
    tex = int(opt('--tex', 4096))
    if stage in ('all', 'model'):
        ob = build({'no_cull': '--no-cull' in argv})
        info = K.unwrap(ob)
        K.log('uv', info)
        bpy.ops.wm.save_as_mainfile(filepath=blend)
        if '--preview' in argv:
            import preview
            preview.shots(ob, os.path.join(work, 'preview'))
        if stage == 'model' and '--bake' not in argv:
            return
        m = K.bake_maps(ob, size=tex, ao_size=int(opt('--ao', 2048)), threads=int(opt('--threads', 4)))
        np.savez_compressed(maps, **m)
        json.dump({'tris': K.count_tris(ob), **info}, open(os.path.join(work, 'model.json'), 'w'), indent=1)
    if stage in ('all', 'paint'):
        import paint
        bpy.ops.wm.open_mainfile(filepath=blend)
        ob = bpy.data.objects['hull']
        m = dict(np.load(maps))
        spec = dict(paint.CORVETTE)
        spec['px_per_m'] = json.load(open(os.path.join(work, 'model.json')))['px_per_m_at_4096'] * tex / 4096
        base, orm = paint.paint(m, spec=spec, out=work)
        K.set_final_material(ob, base, orm, normal_png=spec.get('_normal_png'))
        glb = os.path.join(work, 'corvette-hull.glb')
        K.export_glb(ob, glb)
        K.log('wrote', glb, os.path.getsize(glb))


if __name__ == '__main__':
    main()


# ------------------------------------------------------------------------------------------
# ship-module draft (module.py): fixed asset fields, light roles, surfaces to measure
# ------------------------------------------------------------------------------------------
MODULE = {
    'header': """// Corvette K-214 — v3 REMODEL: clean hard-surface hull (tools/blender/hulls/corvette.py) rebuilt from
// measurements of the v7 fal / Tripo blueprint, textured in texture space (tools/blender/hulls/paint.py:
// light paint, plating seams and tone, PATINA plate tone, AO grime, edge wear, decals) and assembled with
// the Blender parts kit (tools/blender/specs/corvette-v3.json via tools/blender/assemble.py).
// The GLB is already in the ship frame (metres, bow +Z, dorsal +Y, port +X): rotate [0, 0, 0], length =
// the assembled bbox length. Node 'hull' is the hull, 'parts_*' the kit parts (hullNodes).
// Engines: kit bells (bell-L x1.463 centre, bell-M x1.114 / x1.064 upper / lower pairs, bell-L on each pod)
// with the kit's documented engine entry (depth to the throat plate, throat, inner wall) times that scale.
// Lights: at the lenses of the kit nav-light housings.""",
    'meta': {
        'name': 'Warden-class corvette', 'designation': 'K-214', 'crew': 'about 350',
        'blurb': 'Armoured escort corvette: a chamfered bow with four torpedo doors, a bridge house and a two-tier bridge tower, two twin-barrel dorsal gun mounts and a sensor mast, five fusion bells in the stern frame and two outrigger drive pods on pylons.',
    },
    'asset': {
        'glb': './assets/ships/corvette.glb', 'generator': 'tools/blender/hulls/corvette.py (remodel of the tripo3d/h3.1/multiview-to-3d v7 hull) + tools/blender/assemble.py',
        'concept': './assets/concepts/corvette.webp', 'beauty': './assets/concepts/corvette-beauty.webp',
        'rotate': [0, 0, 0], 'hullNodes': ['hull'],
        # dark operational livery; kit glass gets a dim warm interior light (livery.js glassGlow, opt-in)
        'livery': {'glassGlow': [0.046, 0.04, 0.033], 'glassLit': 0.5},
        # runtime PATINA micro detail, turned down: the hull carries its own plating seams and panel
        # breaks, and the world-axis tri-planar layer draws crossing lines on 30-60 degree facets
        'detail': {'set': 'hull', 'tile': 6, 'normalStrength': 0.6, 'roughAmount': 0.5, 'cavity': 0.2},
    },
    # in navlight placement order: pod port, pod stbd, keel, masthead, stern
    'lights': [
        {'color': 'red', 'note': 'steady sidelights on the flat outboard face of each pod (the beam extremity): red port, green starboard'},
        {'color': 'green'},
        {'color': 'white', 'blink': {'period': 1.3, 'duty': 0.1, 'phase': 0.5}, 'note': 'anti-collision strobes, alternating: keel and masthead (top of the sensor block)'},
        {'color': 'white', 'blink': {'period': 1.3, 'duty': 0.1}},
        {'color': 'white', 'note': 'steady stern light on the stern plate above the centre bell'},
    ],
    'surfaces': {
        'flank-fore-port': {'centre': [16.15, -8.05, 9.5], 'normal': [1, 0, 0], 'u': [0, 0, 1], 'width': 18.0, 'height': 6.6, 'note': 'upper flank between the pylon and the bow taper (two port rows)'},
        'flank-fore-stbd': {'centre': [-16.15, -8.05, 9.5], 'normal': [-1, 0, 0], 'u': [0, 0, -1], 'width': 18.0, 'height': 6.6},
        'flank-aft-port': {'centre': [15.8, -8.05, -36.0], 'normal': [1, 0, -0.018], 'u': [0.018, 0, 1], 'width': 17.0, 'height': 6.6, 'note': 'upper flank aft of the pod'},
        'flank-aft-stbd': {'centre': [-15.8, -8.05, -36.0], 'normal': [-1, 0, -0.018], 'u': [0.018, 0, -1], 'width': 17.0, 'height': 6.6},
        'belt-port': {'centre': [16.37, -14.3, -12.0], 'normal': [1, 0, 0], 'u': [0, 0, 1], 'width': 56.0, 'height': 5.0, 'note': 'armour belt (0.22 m proud), crew-door bays at z 1.5 / 9.9 / -39.5'},
        'belt-stbd': {'centre': [-16.37, -14.3, -12.0], 'normal': [-1, 0, 0], 'u': [0, 0, -1], 'width': 56.0, 'height': 5.0},
        'flank-bow-port': {'centre': [12.4, -10.0, 36.0], 'normal': [0.975, 0, 0.221], 'u': [-0.221, 0, 0.975], 'width': 26.0, 'height': 9.0, 'note': 'tapered bow flank; K-214 at z 28-43'},
        'flank-bow-stbd': {'centre': [-12.4, -10.0, 36.0], 'normal': [-0.975, 0, 0.221], 'u': [-0.221, 0, -0.975], 'width': 26.0, 'height': 9.0},
        'shoulder-port': {'centre': [14.83, -2.98, -12.0], 'normal': [0.754, 0.657, 0], 'u': [0, 0, 1], 'width': 30.0, 'height': 3.0, 'note': 'shoulder chamfer from the flank to the walkway, clear stretch z -27..3 (vent bays at z 6-17 and -46..-40, launcher tubes at z -29..-37)'},
        'shoulder-stbd': {'centre': [-14.83, -2.98, -12.0], 'normal': [-0.754, 0.657, 0], 'u': [0, 0, -1], 'width': 30.0, 'height': 3.0},
        'deck-walk-port': {'centre': [11.7, -1.46, -6.0], 'normal': [0, 1, 0], 'u': [0, 0, 1], 'width': 44.0, 'height': 2.0, 'note': 'walkway outboard of the deckhouse (deck-edge rails)'},
        'deck-walk-stbd': {'centre': [-11.7, -1.46, -6.0], 'normal': [0, 1, 0], 'u': [0, 0, 1], 'width': 44.0, 'height': 2.0},
        'deckhouse-side-port': {'centre': [9.15, 1.0, -12.0], 'normal': [0.891, 0.455, 0], 'u': [0, 0, 1], 'width': 36.0, 'height': 4.4, 'note': 'sloped deckhouse side (ports, ladders)'},
        'deckhouse-side-stbd': {'centre': [-9.15, 1.0, -12.0], 'normal': [-0.891, 0.455, 0], 'u': [0, 0, -1], 'width': 36.0, 'height': 4.4},
        'dorsal-deck': {'centre': [0, 3.45, 13.0], 'normal': [0, 1, 0], 'u': [0, 0, 1], 'width': 6.0, 'height': 10.0, 'note': 'deckhouse roof between the forward turret and the bridge'},
        'stern-deck': {'centre': [0, -1.46, -44.0], 'normal': [0, 1, 0], 'u': [0, 0, 1], 'width': 9.0, 'height': 20.0, 'note': 'main deck aft of the deckhouse'},
        'bow-deck': {'centre': [0, -3.2, 40.0], 'normal': [0, 0.988, 0.156], 'u': [0, -0.156, 0.988], 'width': 12.0, 'height': 8.0, 'note': 'sloping bow deck (hatch plate, vent ramps)'},
        'bridge-glazing': {'centre': [0, 1.35, 24.35], 'normal': [0, 0, 1], 'u': [1, 0, 0], 'width': 5.0, 'height': 1.2, 'note': 'bridge glazing recess back wall (vertical, 0.9 m in from the glacis at the band top), kit panes'},
        'tower-front': {'centre': [0, 8.15, -5.73], 'normal': [0, 0, 1], 'u': [1, 0, 0], 'width': 9.0, 'height': 2.2, 'note': 'vertical tier of the tower front'},
        'tower-side-port': {'centre': [5.95, 8.15, -11.0], 'normal': [1, 0, 0], 'u': [0, 0, 1], 'width': 8.0, 'height': 2.2},
        'tower-side-stbd': {'centre': [-5.95, 8.15, -11.0], 'normal': [-1, 0, 0], 'u': [0, 0, -1], 'width': 8.0, 'height': 2.2},
        'tower-glazing': {'centre': [0, 11.52, -5.35], 'normal': [0, -0.603, 0.798], 'u': [1, 0, 0], 'width': 9.0, 'height': 1.5, 'note': 'leaning tower glazing (faces forward and down), recessed 0.3 m'},
        'stern-plate': {'centre': [0, -2.9, -49.25], 'normal': [0, 0, -1], 'u': [-1, 0, 0], 'width': 8.0, 'height': 0.8, 'note': 'recessed stern plate strip above the centre bell boss'},
        'pod-outboard-port': {'centre': [34.45, -14.95, -5.0], 'normal': [1, 0, 0], 'u': [0, 0, 1], 'width': 6.0, 'height': 5.0, 'note': 'pod outboard face forward of the radiator bay'},
        'pod-outboard-stbd': {'centre': [-34.45, -14.95, -5.0], 'normal': [-1, 0, 0], 'u': [0, 0, -1], 'width': 6.0, 'height': 5.0},
    },
}
