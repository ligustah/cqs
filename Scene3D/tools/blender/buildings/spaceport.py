"""SP-3 orbital spaceport: parametric station geometry (headless Blender, bpy 5.x).

    python spaceport.py <workdir>          # -> <workdir>/spaceport-hull.glb (+ .json stats)
    then spaceport_spec.py + assemble.py (see spaceport_build.sh)

Station frame (spaceport_dims): metres, forward +Z, up +Y, left +X (the open slot side), origin on the
shells' axis at the carrier's mid-length. Built here (all new geometry, corrections 25, 31, 32):
  - two offset half-shells of octagonal section: a lower trough under the carrier, an upper hood
    shifted aft; thin (6 m) dark plating in panels with seam grooves, inner frame ribs every 40 m,
    white work-light strips on the inner walls;
  - pale chamfered rims on every free edge, in 60 m segments with dark joints, and end arches;
  - kit parts from spaceport_kit (habitat blocks, gantry cranes, manipulator arms, clamp arms,
    radiator / solar arrays, tugs);
  - the part-built carrier's bare structure aft of the cut: heavy rings at the real frame stations,
    light ribs between, keel, stringers, the first plates, keel cradles from the trough floor. The
    plated bow is NOT modelled: the runtime instances the real CV-50 GLB, clipped at CV_CUT_Z;
  - the station code SP-3 on a dark ID field on the hood.
No UVs: plating tone is in the vertex colour; the runtime adds PATINA tri-planar detail and the worn finish.
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402

import spaceport_dims as D  # noqa: E402
import spaceport_kit as K  # noqa: E402
from spaceport_kit import Acc, C, T, Ry, Rx, Rz, box, beam, rod, cyl, truss, prism, crect  # noqa: E402


# ------------------------------------------------------------------------------------------------
# shells
# ------------------------------------------------------------------------------------------------
def arc_sweep(acc, a, th0, th1, sec, mat, col, j=0.0, caps=True):
    """sweep a closed section [(dr, z), ...] (CCW in (dr, z)) along the octagon arc of apothem a"""
    angs = D.arc_angles(th0, th1)
    n = len(sec)
    rings = []
    for th in angs:
        pts = []
        for dr, z in sec:
            x, y = D.oct_pt(th, a + dr)
            pts.append((x, y, z))
        rings.append(acc.verts(pts))
    for i in range(len(angs) - 1):
        b0, b1 = rings[i], rings[i + 1]
        c = acc.tone(col, j) if j else col
        for k in range(n):
            m = (k + 1) % n
            acc.face([b0 + k, b0 + m, b1 + m, b1 + k], mat, c)
    if caps:
        acc.face([rings[0] + k for k in range(n)], mat, col)
        acc.face([rings[-1] + k for k in reversed(range(n))], mat, col)


def face_segments(th0, th1):
    angs = D.arc_angles(th0, th1)
    return list(zip(angs[:-1], angs[1:]))


def shell(acc, S, inner_light=True):
    a, t = S['a'], D.SHELL_T
    z0, z1 = S['z0'], S['z1']
    P = D.PANEL
    nz = int(round((z1 - z0) / P['dz']))
    zs = np.linspace(z0, z1, nz + 1)
    for tha, thb in face_segments(S['th0'], S['th1']):
        for side, rad, sgn in (('out', a + t, 1), ('in', a, -1)):
            pa = np.array(D.oct_pt(tha, rad))
            pb = np.array(D.oct_pt(thb, rad))
            n2 = np.array(D.oct_normal((tha + thb) / 2)) * sgn
            width = np.linalg.norm(pb - pa)
            nb = max(1, int(round(width / P['band'])))
            # seam backing (dark), a little below the panel faces
            back = (pa - n2 * P['depth'], pb - n2 * P['depth'])
            q = [(*back[0], z0), (*back[1], z0), (*back[1], z1), (*back[0], z1)]
            acc.poly(q if sgn > 0 else q[::-1], 'shell', C['seam'])
            zstep = P['dz'] if side == 'out' else D.RIB_PITCH
            zz = np.arange(z0, z1 + 1e-6, zstep) if side == 'in' else zs
            if zz[-1] < z1 - 1e-6:
                zz = np.r_[zz, z1]
            g = P['seam'] / 2
            for bi in range(nb):
                u0, u1 = bi / nb, (bi + 1) / nb
                e0 = pa + (pb - pa) * u0
                e1 = pa + (pb - pa) * u1
                d = (pb - pa) / width
                e0 = e0 + d * (g if bi > 0 else 0)
                e1 = e1 - d * (g if bi < nb - 1 else 0)
                for k in range(len(zz) - 1):
                    za, zb = zz[k] + (g if k > 0 else 0), zz[k + 1] - (g if k < len(zz) - 2 else 0)
                    base = C['shell'] if acc.rnd() > 0.22 else C['shell2']
                    q = [(*e0, za), (*e1, za), (*e1, zb), (*e0, zb)]
                    acc.poly(q if sgn > 0 else q[::-1], 'shell', acc.tone(base, 0.08))
    # inner frame ribs
    zr = np.arange(z0 + D.RIB_PITCH, z1 - 1, D.RIB_PITCH)
    for z in zr:
        arc_sweep(acc, a, S['th0'], S['th1'], [(-D.RIB['d'], z - D.RIB['w'] / 2), (0.2, z - D.RIB['w'] / 2), (0.2, z + D.RIB['w'] / 2), (-D.RIB['d'], z + D.RIB['w'] / 2)][::-1],
                  'steel', C['steel'], caps=True)
    # pale chamfered corner bands on the outside at the octagon vertices (the concept's pale chamfers; they split the
    # dark shell into narrower bands, so no face reads as one continuous slab: correction 31), segmented like the rims
    for th in D.arc_angles(S['th0'], S['th1'])[1:-1]:
        dth = math.degrees(6.0 / (a + t))
        nseg = max(1, int(round((z1 - z0) / D.RIM['seg'])))
        for i in range(nseg):
            za = z0 + (z1 - z0) * i / nseg + (0.6 if i else 0)
            zb = z0 + (z1 - z0) * (i + 1) / nseg - (0.6 if i < nseg - 1 else 0)
            arc_sweep(acc, a, th - dth, th + dth, [(t - 0.2, za), (t + 2.2, za + 1.0), (t + 2.2, zb - 1.0), (t - 0.2, zb)][::-1], 'rim', acc.tone(C['rim2'], 0.05), caps=True)
    return zr


def light_strips(acc, S, zr, which):
    """work-light strips on the inner walls between the ribs (white), as in the concept"""
    a = S['a'] - 0.15
    for tha, thb in face_segments(S['th0'], S['th1']):
        mid = (tha + thb) / 2
        fa = D.face_angle(mid)
        if fa not in which:
            continue
        pa, pb = np.array(D.oct_pt(tha, a)), np.array(D.oct_pt(thb, a))
        width = np.linalg.norm(pb - pa)
        d = (pb - pa) / width
        n2 = -np.array(D.oct_normal(mid))
        lo, hi = which[fa]
        for z in (zr[:-1] + zr[1:]) / 2:
            e0, e1 = pa + d * width * lo, pa + d * width * hi
            for dz in (-6.0, 6.0):
                q = [(*e0, z + dz - 0.7), (*e1, z + dz - 0.7), (*e1, z + dz + 0.7), (*e0, z + dz + 0.7)]
                acc.poly(q, 'strip', C['white'])


def rim_long(acc, name, S):
    """pale rim along a free longitudinal edge, in segments with dark joints"""
    R = D.RIM
    a, t = S['a'], D.SHELL_T
    th = {'trough_near': S['th1'], 'trough_far': S['th0'], 'hood_near': S['th0'], 'hood_far': S['th1']}[name]
    # face that holds the edge, its normal n and the free direction f (away from the shell)
    if name in ('trough_near', 'hood_far'):
        fa = D.face_angle(th - 1e-3)
        f_sign = 1.0
    else:
        fa = D.face_angle(th + 1e-3)
        f_sign = -1.0
    n = np.array([math.cos(math.radians(fa)), math.sin(math.radians(fa))])
    tang = np.array([-n[1], n[0]])                   # +theta direction along the face
    f = tang * f_sign
    e = np.array(D.oct_pt(th, a + t / 2))
    if name in D.RIM_TOP:                            # trough rims: tops at the walkway height
        top = D.RIM_TOP[name][0][1]
        over = top - e[1]
    else:
        over = 4.0
    fl = [over - R['w'], over]                       # along f
    nl = [-(t / 2 + R['r_in']), t / 2 + R['r_out']]  # along n
    ch = R['ch']
    sec2 = [(nl[0], fl[0]), (nl[1], fl[0]), (nl[1], fl[1] - ch), (nl[1] - ch, fl[1]), (nl[0] + ch, fl[1]), (nl[0], fl[1] - ch)]
    pts = [tuple(e + n * u + f * v) for u, v in sec2]
    # orientation: CCW in the (x, y) plane
    area = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))
    if area < 0:
        pts = pts[::-1]
    z0, z1 = S['z0'], S['z1']
    nseg = max(1, int(round((z1 - z0) / R['seg'])))
    for i in range(nseg):
        za = z0 + (z1 - z0) * i / nseg + (R['joint'] / 2 if i else 0)
        zb = z0 + (z1 - z0) * (i + 1) / nseg - (R['joint'] / 2 if i < nseg - 1 else 0)
        prism(acc, pts, za, zb, 'rim', acc.tone(C['rim'], 0.05))
        if i < nseg - 1:   # dark joint, slightly smaller
            zj = z0 + (z1 - z0) * (i + 1) / nseg
            ptsj = [tuple(e + n * u * 0.92 + f * (v * 0.92 + (fl[0] + fl[1]) * 0.04)) for u, v in sec2]
            if area < 0:
                ptsj = ptsj[::-1]
            prism(acc, ptsj, zj - R['joint'], zj + R['joint'], 'steel', C['joint'])
    return e, n, f, fl, nl


def arches(acc, S):
    A = D.ARCH
    a, t = S['a'], D.SHELL_T
    for zc, s in ((S['z0'], 1), (S['z1'], -1)):
        z0, z1 = zc - A['w'] / 2, zc + A['w'] / 2
        ch = A['ch']
        r0, r1 = -A['r_in'], t + A['r_out']
        sec = [(r0, z0 + ch), (r0 + ch, z0), (r1 - ch, z0), (r1, z0 + ch), (r1, z1 - ch), (r1 - ch, z1), (r0 + ch, z1), (r0, z1 - ch)]
        arc_sweep(acc, a, S['th0'], S['th1'], sec[::-1], 'rim', C['rim'], j=0.04)
        # white strip on the arch's inner face, amber at the end faces (marks the shell mouth)
        arc_sweep(acc, a, S['th0'] + 2, S['th1'] - 2, [(r0 - 0.15, zc - 1.0), (r0 - 0.05, zc - 1.0), (r0 - 0.05, zc + 1.0), (r0 - 0.15, zc + 1.0)][::-1], 'strip', C['white'])
        # dark joints across the arch at every octagon vertex (segments)
        for th in D.arc_angles(S['th0'], S['th1'])[1:-1]:
            arc_sweep(acc, a, th - 0.35, th + 0.35, [(r0 - 0.1, z0 - 0.1), (r1 + 0.1, z0 - 0.1), (r1 + 0.1, z1 + 0.1), (r0 - 0.1, z1 + 0.1)][::-1], 'steel', C['joint'])


# ------------------------------------------------------------------------------------------------
# carrier structure aft of the cut (carrier frame -> station: + (0, CY, 0))
# ------------------------------------------------------------------------------------------------
def full_outline(half):
    """mirror a half outline (x >= 0, top centre -> bottom centre) to a CCW closed polygon"""
    right = [p for p in half if p[0] > 1e-6]
    left = [(-x, y) for x, y in reversed(right)]
    poly = right + left
    area = sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))
    return poly if area > 0 else poly[::-1]


def offset_convex(poly, d):
    """inward offset of a convex CCW polygon by d"""
    n = len(poly)
    lines = []
    for i in range(n):
        p, q = np.array(poly[i]), np.array(poly[(i + 1) % n])
        t = (q - p) / np.linalg.norm(q - p)
        nn = np.array([-t[1], t[0]])   # inward for CCW
        lines.append((p + nn * d, t))
    out = []
    for i in range(n):
        p1, t1 = lines[i - 1]
        p2, t2 = lines[i]
        A = np.array([t1, -t2]).T
        s = np.linalg.solve(A, p2 - p1)
        out.append(tuple(p1 + t1 * s[0]))
    return out


def ring(acc, outer, inner, z0, z1, mat, col, tone=0.0):
    """prism ring between two CCW polygons with the same vertex count"""
    n = len(outer)
    bo = acc.verts([(x, y, z0) for x, y in outer] + [(x, y, z1) for x, y in outer])
    bi = acc.verts([(x, y, z0) for x, y in inner] + [(x, y, z1) for x, y in inner])
    for i in range(n):
        k = (i + 1) % n
        c = acc.tone(col, tone) if tone else col
        acc.face([bo + i, bo + k, bo + n + k, bo + n + i], mat, c)            # outer sides
        acc.face([bi + k, bi + i, bi + n + i, bi + n + k], mat, c)            # inner sides (facing the hole)
        acc.face([bo + k, bo + i, bi + i, bi + k], mat, c)                    # back face (z0)
        acc.face([bo + n + i, bo + n + k, bi + n + k, bi + n + i], mat, c)    # front face (z1)


def carrier_structure(acc):
    acc.push(T(0, D.CY, 0))
    outer = full_outline(D.P_END)
    inner_ring = full_outline(D.RING_IN)
    # heavy rings at the real frame stations (the plated hull's own frame section)
    for z0, z1 in D.HEAVY_RINGS:
        zc = (z0 + z1) / 2   # the real frame stations, built as 10 m deep bare rings (12 m thick)
        ring(acc, outer, offset_convex(outer, 10.0), zc - 6.0, zc + 6.0, 'primer', C['primer'], tone=0.05)
        # amber frame-number band on the outboard posts
        for sx in (-1, 1):
            q = [(sx * 131.05, -40.0, zc - 4), (sx * 131.05, -40.0, zc + 4), (sx * 131.05, -34.0, zc + 4), (sx * 131.05, -34.0, zc - 4)]
            acc.poly(q if sx > 0 else q[::-1], 'primer', C['amber'])
    ring(acc, outer, offset_convex(outer, 12.0), *D.STERN_RING, 'primer', C['primer'], tone=0.05)
    # light ribs between: bare octagonal frames
    for z in D.light_ribs():
        ring(acc, outer, offset_convex(outer, D.LIGHT_RIB_W), z - D.LIGHT_RIB_T / 2, z + D.LIGHT_RIB_T / 2, 'steel', C['primer2'], tone=0.06)
    # keel spine (box with chamfered bottom) and its 45-degree wedge chords
    k = D.KEEL
    sec = [(-k['x'], k['top']), (-k['x'], k['bot'] + 8), (-k['x'] + 8, k['bot']), (k['x'] - 8, k['bot']), (k['x'], k['bot'] + 8), (k['x'], k['top'])]
    prism(acc, sec[::-1] if False else sec, k['z0'], k['z1'], 'primer', C['primer2'])
    # stringers (some partial: plating and longitudinals grow aft from the finished bow)
    for x, y, s in D.STRINGERS:
        zstart = D.CV_CUT_Z
        zend = D.STERN_RING[0] if y < 0 else -110.0
        for sx in ((-1, 1) if x > 0 else (1,)):
            box(acc, (sx * x, y, (zstart + zend) / 2), (s, s, zstart - zend), 'steel', C['steel'])
    # the first plates aft of the cut: belly and lower flank, ragged edge
    rng = np.random.default_rng(7)
    for x0 in np.arange(-104, 104, 26.0):
        L = 30 + rng.random() * 50
        box(acc, (x0 + 13, -121.5, D.CV_CUT_Z - L / 2), (25.4, 1.0, L), 'primer', acc.tone(C['primer'], 0.06))
    for sx in (-1, 1):
        for y0 in (-94.0, -73.0):
            L = 20 + rng.random() * 40
            box(acc, (sx * 131.5, y0 + 10.5, D.CV_CUT_Z - L / 2), (1.0, 20.4, L), 'primer', acc.tone(C['primer'], 0.06))
        # deck-level plates (upper slab), shorter
        L = 18 + rng.random() * 25
        box(acc, (sx * 50, 23.5, D.CV_CUT_Z - L / 2), (96, 1.0, L), 'primer', acc.tone(C['primer'], 0.05))
    # scaffold towers beside the rings (access), thin trusses
    for z in (D.HEAVY_RINGS[0][0] - 8, D.HEAVY_RINGS[1][0] - 8, D.HEAVY_RINGS[2][0] - 8):
        for sx in (-1, 1):
            truss(acc, (sx * 140, -121, z), (sx * 140, 23, z), 4.0, up=(0, 0, 1))
    acc.pop()
    # keel cradles from the trough floor (station frame): A-frame trusses with a saddle under the keel
    floor = -D.TROUGH['a']
    keel_y = D.CY + D.KEEL['bot']
    for z in D.CRADLES:
        if z > D.CV_CUT_Z + 20:   # under the plated bow: cradle saddle under the keel wedge
            saddle_hw = 60.0
        else:
            saddle_hw = 40.0
        box(acc, (0, keel_y - 2.5, z), (saddle_hw * 2, 5.0, 12.0), 'rim', C['rim2'], ch=1.5)
        box(acc, (0, keel_y - 0.4, z), (saddle_hw * 1.6, 0.8, 8.0), 'steel', C['black'])
        for sx in (-1, 1):
            truss(acc, (sx * 70, floor, z), (sx * 40, keel_y - 5, z), 7.0, up=(0, 0, 1))
            box(acc, (sx * 70, floor + 1.5, z), (14.0, 3.0, 14.0), 'steel', C['steel2'], ch=1.0)


# ------------------------------------------------------------------------------------------------
# kit parts placed on the station
# ------------------------------------------------------------------------------------------------
def at(acc, M, fn, *a, **kw):
    acc.push(M)
    r = fn(acc, *a, **kw)
    acc.pop()
    return r


def frame_world(o, x, y):
    return K.frame(np.asarray(o, float), x, y)


def place_kit(acc, info):
    # habitat blocks
    for b in D.HAB_BLOCKS:
        M = D.block_frame(b)
        H = at(acc, M, K.habBlock, b['L'], b['W'], b['decks'])
        info['blocks'].append(dict(b, M=M.tolist(), H=H))
    # gantry cranes over the forward open bay
    yb = 125.0
    xl, xr = D.RIM_TOP['trough_far'][0][0], D.RIM_TOP['trough_near'][0][0]
    yl, yr = D.RIM_TOP['trough_far'][0][1], D.RIM_TOP['trough_near'][0][1]
    for i, z in enumerate(D.GANTRIES):
        span = xr - xl
        M = T((xl + xr) / 2, yb, z) @ Rx(0)
        # legs: from bridge underside (yb - 4) to rim tops (+3 bogie)
        legL = yb - 4 - yl - 3.0
        legR = yb - 4 - yr - 3.0
        # gantryCrane builds legs at x0 = -span/2 (legL) and x1 = +span/2 (legR)
        at(acc, M, K.gantryCrane, span, legL, legR, 8.0, trolley_x=-30.0 if i == 0 else 50.0, hoist=18.0 if i == 0 else 10.0)
        info['gantries'].append(dict(z=z, y=yb, span=span))
    # manipulator arms
    for m in D.MANIPULATORS:
        if m['mount'] == 'hood_ceiling':
            M = D.mount_frame('hood_ceiling', m['z'], m['x'])
            tip = at(acc, M, K.manipulator, 90.0 if m['x'] < 0 else -90.0, 35.0, 45.0, 46.0, 40.0)
        elif m['mount'] == 'trough_near':
            M = D.mount_frame('trough_near', m['z'])
            tip = at(acc, M, K.manipulator, -90.0, 40.0, -55.0, 36.0, 30.0)
        else:
            M = D.mount_frame('trough_far', m['z'])
            tip = at(acc, M, K.manipulator, 90.0, 35.0, -60.0, 36.0, 30.0)
        info['manipulators'].append(dict(m, tip=(M @ np.r_[tip, 1])[:3].tolist()))
    # clamp arms for the docked freighters
    for f in D.FREIGHTERS:
        for root, n, reach in D.freighter_clamps(f):
            along = (0, 0, 1)
            M = frame_world(root, np.cross(n, along) if abs(n[2]) < 0.9 else (1, 0, 0), n)
            # frame(): x then y; we want y = n (mount normal), z along the station
            M = D._frame(root, n, along)
            at(acc, M, K.clampArm, reach)
            info['clamps'].append(dict(freighter=f['name'], root=list(root), n=list(n), reach=reach))
    # radiator / solar arrays off the lower chamfers
    for i, r in enumerate(D.RADIATORS):
        a = D.TROUGH['a'] + D.SHELL_T
        x, y = D.oct_pt(r['th'], a)
        n = np.array(D.oct_normal(r['th']))
        M = D._frame((x, y, r['z']), (n[0], n[1], 0.0), (0, 0, 1))
        # panels spread along the station (local X must be station z): turn the part 90 deg about its mast
        at(acc, M @ Ry(90), K.radiatorArray, 2, 14.0, 34.0, None, None, i % 2 == 1)
        info['radiators'].append(dict(r, p=[x, y, r['z']]))
    # tugs
    for tg in D.TUGS:
        at(acc, T(*tg['p']) @ Ry(tg['yaw']), K.tug)
    # comm masts on the far rim (forward) and the hood top
    for M in (D.mount_frame('trough_far', 505.0), D.mount_frame('hood_top', -500.0, -40.0)):
        acc.push(M)
        truss(acc, (0, 0, 0), (0, 55, 0), 4.0, up=(0, 0, 1))
        box(acc, (0, 40, 0), (1.0, 18, 12), 'steel', C['steel2'])   # panel antenna
        acc.pop()
        info['masts'].append((M @ np.r_[0, 55, 0, 1])[:3].tolist())


def rim_dressing(acc):
    """busy rims (correction 31): pipe runs along the rim faces, plant boxes and tank clusters in the gaps
    between the blocks, containers, crane bogies and arm bases on the two trough rims"""
    rng = np.random.default_rng(31)
    t = D.TROUGH
    xo = t['a'] + D.SHELL_T / 2 + D.RIM['r_out']          # near rim outer face
    xi = -(t['a'] - D.RIM['r_in'] + D.SHELL_T / 2)         # far rim inner face (faces the bay)
    yfar = D.RIM_TOP['trough_far'][0][1]
    for x, ys in ((xo + 0.9, (-3.0, -7.0)), (xi + 0.9, (yfar - 6.0, yfar - 10.0))):
        for k, y in enumerate(ys):
            cyl(acc, (x, y, t['z0'] + 8), (x, y, t['z1'] - 8), 0.9 if k else 1.2, 'steel', C['steel2'] if k else C['rim2'], n=8, caps=False)
            for z in np.arange(t['z0'] + 30, t['z1'] - 20, 30.0):   # pipe brackets
                box(acc, (x - 0.4, y, z), (1.6, 2.8, 0.8), 'steel', C['steel'])
    # occupied stretches of the rim tops
    busy = {'trough_near': [], 'trough_far': []}
    for b in D.HAB_BLOCKS:
        if b['rim'] in busy:
            busy[b['rim']].append((b['z'] - b['L'] / 2 - 6, b['z'] + b['L'] / 2 + 6))
    for z in D.GANTRIES:
        for r in busy:
            busy[r].append((z - 12, z + 12))
    for m in D.MANIPULATORS:
        if m['mount'] == 'trough_near':
            busy['trough_near'].append((m['z'] - 8, m['z'] + 8))
        elif m['mount'] == 'far_wall':
            busy['trough_far'].append((m['z'] - 8, m['z'] + 8))
    for z0, z1 in ((292.0, 248.0), (188.0, 150.0), (-176.0, -230.0)):
        busy['trough_near'].append((z1 - 4, z0 + 4))
    busy['trough_far'].append((480.0, 530.0))   # comm mast
    busy['trough_far'].append((D.HOOD['z0'], D.HOOD['z1'] + 10))   # under the hood
    for rim, occ in busy.items():
        M = D.mount_frame(rim, 0.0)
        acc.push(M)
        z = t['z0'] + 14
        while z < t['z1'] - 14:
            L = float(rng.uniform(8, 18))
            if any(a - 2 < z + L / 2 and z - L / 2 < b + 2 for a, b in occ):
                z += 9.0
                continue
            kind = rng.random()
            if kind < 0.45:      # plant box (pale or gunmetal), with a smaller unit on top
                W = float(rng.uniform(6, 10))
                Hh = float(rng.uniform(3, 6))
                box(acc, (rng.uniform(-3, 3), Hh / 2, z), (W, Hh, L), 'hab', acc.tone(C['hab2'] if rng.random() < 0.5 else C['hab'], 0.08), ch=0.6)
                box(acc, (0, Hh + 0.8, z + L * 0.15), (W * 0.5, 1.6, L * 0.4), 'steel', C['steel2'], ch=0.3)
            elif kind < 0.75:    # tank cluster
                for k in range(3):
                    r = float(rng.uniform(1.6, 2.6))
                    cyl(acc, (-4 + k * 4.0, 0, z), (-4 + k * 4.0, 4 + 2 * r, z), r, 'rim', acc.tone(C['rim2'], 0.06), n=10)
                L = 10.0
            else:                # cargo pallet with a hazard frame
                box(acc, (0, 0.4, z), (10, 0.8, L), 'steel', C['steel'])
                box(acc, (0, 0.9, z), (9.4, 0.2, L - 0.6), 'steel', C['amber'])
                for k in range(int(L // 3.2)):
                    box(acc, (rng.uniform(-2, 2), 2.0, z - L / 2 + 1.8 + k * 3.2), (2.4, 2.2, 2.4), 'hab', acc.tone(C['hab'], 0.1), ch=0.2)
            z += L + float(rng.uniform(6, 22))
        acc.pop()


def station_code(acc, text='SP-3'):
    """the station code in white on a dark ID field, on the hood's upper-near chamfer"""
    curve = bpy.data.curves.new('code', 'FONT')
    curve.body = text
    curve.size = 1.0
    curve.align_x = 'CENTER'
    curve.align_y = 'CENTER'
    curve.extrude = 0.0
    ob = bpy.data.objects.new('code', curve)
    bpy.context.collection.objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    me = ob.evaluated_get(dg).to_mesh()
    V = np.array([v.co[:] for v in me.vertices])
    F = [list(p.vertices) for p in me.polygons]
    ob.evaluated_get(dg).to_mesh_clear()
    bpy.data.objects.remove(ob)
    h = 26.0   # letter height, metres (the CV-50's are 15 m on a 900 m hull)
    sc = h / max(1e-6, V[:, 1].max() - V[:, 1].min())
    a = D.HOOD['a'] + D.SHELL_T
    for z in (-250.0,):
        x, y = D.oct_pt(57.0, a)
        n = np.array([math.sqrt(0.5), math.sqrt(0.5), 0])
        up = np.array([-math.sqrt(0.5), math.sqrt(0.5), 0])
        # text reads along -z when seen from +x+z?  The camera sees this face from +x: text x -> -z
        M = np.eye(4)
        M[:3, 0] = (0, 0, -1)   # right-handed with up x n: reads left to right from the near side
        M[:3, 1] = up
        M[:3, 2] = n
        M[:3, 3] = (x, y, z)
        acc.push(M)
        w = (V[:, 0].max() - V[:, 0].min()) * sc
        acc.poly([(-w / 2 - 8, -h / 2 - 6, 0.25), (w / 2 + 8, -h / 2 - 6, 0.25), (w / 2 + 8, h / 2 + 6, 0.25), (-w / 2 - 8, h / 2 + 6, 0.25)], 'shell', C['black'])
        b = acc.verts([(vx * sc, vy * sc, 0.45) for vx, vy, _ in V])
        for f in F:
            acc.face([b + i for i in f], 'hab', C['white'])
        acc.pop()


def main():
    work = sys.argv[1] if len(sys.argv) > 1 else '/tmp/spaceport'
    os.makedirs(work, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    info = dict(blocks=[], gantries=[], manipulators=[], clamps=[], radiators=[], masts=[])
    groups = {}

    a = Acc()
    zr_t = shell(a, D.TROUGH)
    zr_h = shell(a, D.HOOD)
    for name in ('trough_near', 'trough_far'):
        rim_long(a, name, D.TROUGH)
    for name in ('hood_near', 'hood_far'):
        rim_long(a, name, D.HOOD)
    arches(a, D.TROUGH)
    arches(a, D.HOOD)
    station_code(a)
    groups['shells'] = a

    s = Acc()
    # strips: trough far wall (face 180) upper part, near wall (face 0) lower part, trough bottom chamfers,
    # hood ceiling (face 90) centre
    light_strips(s, D.TROUGH, np.r_[D.TROUGH['z0'], np.arange(D.TROUGH['z0'] + D.RIB_PITCH, D.TROUGH['z1'] - 1, D.RIB_PITCH), D.TROUGH['z1']],
                 {180: (0.15, 0.55), 0: (0.2, 0.75), 225: (0.35, 0.65), 315: (0.35, 0.65)})
    light_strips(s, D.HOOD, np.r_[D.HOOD['z0'], np.arange(D.HOOD['z0'] + D.RIB_PITCH, D.HOOD['z1'] - 1, D.RIB_PITCH), D.HOOD['z1']],
                 {90: (0.42, 0.58), 135: (0.4, 0.6)})
    groups['strips'] = s

    k = Acc()
    place_kit(k, info)
    rim_dressing(k)
    groups['kit'] = k

    c = Acc()
    carrier_structure(c)
    groups['cvframes'] = c

    objs = []
    stats = {}
    for name, acc in groups.items():
        ob = K.to_object(acc, name)
        objs.append(ob)
        stats[name] = acc.tris()
    # one hull mesh (assemble_frame.load_hull expects a single mesh object)
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    hull = bpy.context.view_layer.objects.active
    hull.name = 'hull'
    out = os.path.join(work, 'spaceport-hull.glb')
    K.export_glb([hull], out)
    allV = np.concatenate([np.asarray(g.V) for g in groups.values()])
    lo, hi = allV.min(0), allV.max(0)
    stats['total'] = sum(stats.values())
    rep = dict(tris=stats, bbox=[lo.round(2).tolist(), hi.round(2).tolist()], size=(hi - lo).round(2).tolist(), info=info)
    json.dump(rep, open(os.path.join(work, 'spaceport-hull.json'), 'w'), indent=1)
    print(json.dumps(dict(tris=stats, bbox=rep['bbox'], size=rep['size'])))


if __name__ == '__main__':
    main()
