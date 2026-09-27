# Propulsion: drive bells (parametric exit radius; S/M/L/XL), a 2 x 2 engine housing, a
# tileable radiator panel. Bell frame: origin at the centre of the exit plane, exhaust toward
# -Z, the nozzle body and its mounting back at +Z (they mount with their back on the hull).
import math
from lib import rrect, circle, chamfer_rect, BAKE

K_DEPTH, K_THROAT, K_POW = 1.35, 0.5, 1.8   # throat plate depth / exit radius, throat / exit radius, bell contour exponent


def bell_profile(r, k=8):
    """Inner wall [(depth, radius), ...] from the lip (d = 0) to the throat (d = depth)."""
    depth, rt = K_DEPTH * r, K_THROAT * r
    return [(depth * i / k, r - (r - rt) * (i / k) ** K_POW) for i in range(k + 1)]


def _bell(P, r, n=96, detail=True):
    depth, rt = K_DEPTH * r, K_THROAT * r
    inner = bell_profile(r, 12)
    t0, t1 = 0.035 * r, 0.09 * r                   # wall thickness at the lip and at the throat
    # closed profile (radius, z): inner wall lip -> throat, throat face, outer wall throat -> lip, lip roll
    prof, amp = [], []
    for i, (d, rr) in enumerate(inner):
        prof.append((rr, d)); amp.append(0.004 * r if 0 < i < len(inner) - 1 else 0.0)
    outer = []
    for i, (d, rr) in enumerate(reversed(inner)):
        u = d / depth
        outer.append((rr + t0 + (t1 - t0) * u, d))
    for i, (rr, d) in enumerate(outer):
        prof.append((rr, d)); amp.append(0.012 * r if 0 < i < len(outer) - 1 else 0.0)
    prof.append((r + t0 * 0.6, -0.01 * r)); amp.append(0.0)
    prof.append((r + t0 * 0.1, -0.012 * r)); amp.append(0.0)
    P.lathe(prof, n, closed=True, amp=amp, mat='nozzle', sharp=45)
    # exit manifold ring (the coolant header round the lip) and two mid-bell stiffening bands
    ring = [(r + t0 + 0.05 * r, 0.02 * r), (r + t0 + 0.07 * r, 0.06 * r), (r + t0 + 0.05 * r, 0.1 * r), (r + t0 - 0.004 * r, 0.1 * r), (r + t0 - 0.004 * r, 0.02 * r)]
    P.lathe(ring, n // 2, closed=True, mat='gunmetal', sharp=50)
    for fz in (0.35, 0.7):
        d = fz * depth
        rr = r - (r - rt) * fz ** K_POW + t0 + (t1 - t0) * fz
        P.lathe([(rr + 0.01 * r, d - 0.03 * r), (rr + 0.035 * r, d - 0.02 * r), (rr + 0.035 * r, d + 0.02 * r), (rr + 0.01 * r, d + 0.03 * r)], n // 2, closed=True, mat='gunmetal', sharp=50)
    # throat plate: refractory disc closing the bell just behind the documented glow depth
    P.cyl(rt + 0.02 * r, 0.02 * r, at=(0, 0, depth + 0.02 * r), n=max(24, n // 3), mat='ceramic', bevel=0.0)
    if not detail:
        return depth, rt
    # chamber / reactor can behind the throat, injector head, gimbal ring and four actuators
    zc = depth + 0.02 * r
    P.lathe([(rt + t1, zc), (0.62 * r, zc + 0.12 * r), (0.62 * r, zc + 0.55 * r), (0.5 * r, zc + 0.68 * r), (0.0, zc + 0.7 * r)], max(24, n // 3), mat='gunmetal', sharp=35)
    zg = zc + 0.36 * r
    P.lathe([(0.66 * r, zg - 0.06 * r), (0.8 * r, zg - 0.06 * r), (0.8 * r, zg + 0.06 * r), (0.66 * r, zg + 0.06 * r)], max(24, n // 3), closed=True, mat='paint', sharp=40)
    zb = zc + 0.95 * r                              # mounting back (thrust frame plate)
    P.prism(chamfer_rect(2.1 * r, 2.1 * r, 0.45 * r), zb - 0.08 * r, zb, bevel=0.01 * r)
    P.cyl(0.35 * r, zb - zc - 0.68 * r, at=(0, 0, (zc + 0.68 * r + zb) / 2), n=16, mat='dark', bevel=0.01 * r)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        p0 = (0.8 * r * math.cos(a), 0.8 * r * math.sin(a), zg)
        p1 = (0.95 * r * math.cos(a), 0.95 * r * math.sin(a), zb - 0.08 * r)
        L = math.dist(p0, p1)
        mid = [(p0[i] + p1[i]) / 2 for i in range(3)]
        # cylinder (paint) + rod (steel) + clevis blocks; along the p0 -> p1 direction
        dx, dy, dz = (p1[i] - p0[i] for i in range(3))
        ry = math.degrees(math.atan2(math.hypot(dx, dy), dz))
        rz = math.degrees(math.atan2(dy, dx))
        with P.at(at=mid, rot=(0, 0, rz)):
            with P.at(rot=(0, ry, 0)):
                P.cyl(0.07 * r, 0.55 * L, at=(0, 0, 0.18 * L), n=12, mat='paint2', bevel=0.008 * r)
                P.cyl(0.035 * r, 0.5 * L, at=(0, 0, -0.2 * L), n=10, mat='steel', bevel=0.0)
        P.box((0.14 * r, 0.14 * r, 0.1 * r), at=p0, rot=(0, 0, math.degrees(a)), mat='dark', bevel=0.01 * r)
        P.box((0.16 * r, 0.16 * r, 0.1 * r), at=(p1[0], p1[1], p1[2] - 0.02 * r), rot=(0, 0, math.degrees(a)), mat='dark', bevel=0.01 * r)
    # coolant feed lines from the back plate to the exit manifold (regenerative circuit), two turbopumps
    for k in range(2):
        a = k * math.pi
        x, y = math.cos(a), math.sin(a)
        P.tube([(0.5 * r * x, 0.5 * r * y, zb - 0.08 * r), (0.72 * r * x, 0.72 * r * y, zg + 0.2 * r), (0.72 * r * x, 0.72 * r * y, zc + 0.05 * r),
                ((rt + t1 + 0.1 * r) * x, (rt + t1 + 0.1 * r) * y, depth * 0.85)], 0.04 * r, n=8, fillet=0.15 * r, mat='copper')
        P.cyl(0.14 * r, 0.3 * r, at=(0.5 * r * math.cos(a + 1.2), 0.5 * r * math.sin(a + 1.2), zb - 0.25 * r), n=14, mat='gunmetal', bevel=0.01 * r)
    return depth, rt


def _bell_meta(r, n):
    depth, rt = K_DEPTH * r, K_THROAT * r
    wall = [[round(d, 3), round(rr, 3)] for d, rr in bell_profile(r, 7)[1:-1]]
    return {'engine': {'p': [0, 0, 0], 'dir': [0, 0, -1], 'radius': r, 'depth': round(depth, 3), 'throat': round(rt, 3), 'wall': wall},
            'plateDepth': round(depth + 0.02 * r, 3), 'back': round(depth + 0.02 * r + 0.95 * r, 3), 'segments': n}


def bell(P, r=2.2, n=96):
    _bell(P, r, n)
    m = _bell_meta(r, n)
    m['about'] = ('drive bell: exit plane at z = 0 (origin), exhaust toward -Z, mounting back at z = back; '
                  'engine = the ship-module engine entry (radius, depth of the glow in front of the throat plate, throat, wall)')
    return m


def engine_housing(P, r=2.2, pitch=5.9, n=48):
    """Block holding 2 x 2 bells. Exit planes at z = 0; the housing's aft face at z = 0.9 r."""
    zf = 0.9 * r
    W = 2 * pitch + 1.4
    depth = K_DEPTH * r + 0.02 * r + 0.95 * r + 0.6
    zb = zf + depth
    P.loft([(chamfer_rect(W - 0.6, W - 0.6, 1.2), zf), (chamfer_rect(W, W, 1.4), zf + 0.5), (chamfer_rect(W, W, 1.4), zb - 0.5), (chamfer_rect(W + 0.4, W + 0.4, 1.5), zb)], closed=False, bevel=0.05)
    engines = []
    for i in (-1, 1):
        for j in (-1, 1):
            x, y = i * pitch / 2, j * pitch / 2
            with P.at(at=(x, y, 0)):
                _bell(P, r, n, detail=False)
                # bell well: a recessed collar in the aft face with a bolt ring
                P.frame(circle(r * 1.28, 32), circle(r * 1.1, 32), zf - 0.25, zf + 0.02, mat='dark', bevel=0.03)
                P.bolts([(x2, y2, zf - 0.25) for x2, y2 in circle(r * 1.19, 24)], r=0.05, h=0.04, normal=(0, 0, -1), mat='steel')
            e = {'p': [x, y, 0], 'dir': [0, 0, -1], 'radius': r, 'depth': round(K_DEPTH * r, 3), 'throat': round(K_THROAT * r, 3),
                 'wall': [[round(d, 3), round(rr, 3)] for d, rr in bell_profile(r, 7)[1:-1]]}
            engines.append(e)
    # side access panels, louvres, lifting lugs, cable runs
    for sx in (-1, 1):
        for k, zz in enumerate((zf + 1.6, zf + 3.6)):
            P.box((0.1, 3.2, 1.4), at=(sx * (W / 2 + 0.02), 0, zz), mat='paint2', bevel=0.03)
        P.box((0.12, 1.2, 2.0), at=(sx * (W / 2 + 0.03), -pitch / 2 - 1.0, zb - 1.8), mat='dark', bevel=0.02)
        for k in range(6):
            P.box((0.14, 1.1, 0.08), at=(sx * (W / 2 + 0.06), -pitch / 2 - 1.0, zb - 2.6 + k * 0.32), rot=(0, 0, 0), mat='paint2', bevel=0.0)
        P.tube([(sx * (W / 2 + 0.15), W / 2 - 1.0, zf + 0.8), (sx * (W / 2 + 0.15), W / 2 - 1.0, zb - 0.5)], 0.12, n=8, mat='copper')
        P.tube([(sx * (W / 2 + 0.15), W / 2 - 1.4, zf + 0.8), (sx * (W / 2 + 0.15), W / 2 - 1.4, zb - 0.5)], 0.12, n=8, mat='copper')
    for sy in (-1, 1):
        P.box((W - 3.0, 0.1, 1.2), at=(0, sy * (W / 2 + 0.02), zf + 2.5), mat='paint2', bevel=0.03)
    return {'engines': engines, 'aftFace': round(zf, 3), 'back': round(zb, 3),
            'about': 'engine housing with 2 x 2 M bells; exit planes at z = 0, exhaust toward -Z, mounting back at z = back'}


def radiator(P, length=10.0, width=4.0, standoff=0.35):
    L, W = length, width
    z = standoff
    P.box((L, W, 0.06), at=(0, 0, z), mat='paint', bevel=0.01)
    # fins across the panel (pitch 0.25 m, tile-aligned), headers top and bottom, standoff brackets
    n = int(round(L / 0.25))
    for k in range(n):
        x = -L / 2 + 0.125 + k * 0.25
        P.box((0.025, W - 0.5, 0.12), at=(x, 0, z + 0.09), mat='paint2', bevel=0.0)
    for sy in (-1, 1):
        P.cyl(0.11, L, at=(0, sy * (W / 2 - 0.12), z + 0.1), rot=(0, 90, 0), n=10, mat='steel', bevel=0.0, caps=False)
        P.box((L, 0.06, 0.2), at=(0, sy * (W / 2 - 0.02), z + 0.02), mat='dark', bevel=0.0)
    for x in (-L / 2 + 1.25, -L / 2 + 3.75, -L / 2 + 6.25, -L / 2 + 8.75):
        for sy in (-1, 1):
            P.box((0.3, 0.3, z - 0.03), at=(x, sy * 1.2, (z - 0.03) / 2), mat='dark', bevel=0.02)
        P.box((0.4, W - 0.2, 0.05), at=(x, 0, z - 0.055), mat='paint2', bevel=0.01)
    # manifold joints at the tile edges (half flanges, so neighbouring segments make a full flange)
    for sx in (-1, 1):
        for sy in (-1, 1):
            P.cyl(0.16, 0.05, at=(sx * (L / 2 - 0.025), sy * (W / 2 - 0.12), z + 0.1), rot=(0, 90, 0), n=12, mat='dark', bevel=0.0)
    return {'pitch': length, 'about': 'radiator panel 10 x 4 m on standoffs, tiles along X at 10 m pitch; fins across X'}


PARTS = {
    'bell': {'build': bell, 'tex': 1024, 'sizes': {k: {'r': r, 'n': n, 'tex': t, 'bake': {'ao': 0.4 * r, 'heat0': 0.6 * K_DEPTH * r, 'heat1': K_DEPTH * r}}
                                          for k, r, n, t in (('S', 1.4, 64, 1024), ('M', 2.2, 96, 1024), ('L', 3.5, 120, 2048), ('XL', 7.0, 144, 2048))},
             'bake': {'ao': 1.0, 'curv': 0.03, 'panel': (2.0, 2.0, 2.0), 'heat0': 1.2, 'heat1': 3.2}},
    'engineHousing': {'build': engine_housing, 'tex': 2048, 'bake': {'ao': 1.2, 'curv': 0.04, 'panel': (2.5, 2.5, 2.5), 'heat0': 1.5, 'heat1': 3.0}},
    'radiator': {'build': radiator, 'tex': 1024, 'bake': {'ao': 0.25, 'curv': 0.012, 'panel': (2.5, 2.0, 2.0)}},
}
