"""Bastion-class destroyer DD-12: clean hard-surface hull, rebuilt from measurements of the fal /
Tripo H3.1 blueprint (see README.md and README-destroyer.md in this folder for the method).

    <blender-python> tools/blender/hulls/destroyer.py <workdir> [--stage all|model|paint]
                     [--tex 4096] [--paint-tex 8192] [--ao 2048] [--threads 4] [--no-cull]

Stages: model -> <workdir>/destroyer-hull.blend (volumes, booleans, cull, bevel, join, UVs) and
<workdir>/maps.npz (baked position / normal / zone / AO / curvature at --tex); paint ->
<workdir>/base.png, orm.png, normal.png (destroyer_paint.py, painted at --paint-tex from the
baked maps) and <workdir>/destroyer-hull.glb (node 'hull', ship frame, not re-centred).

Ship frame, metres: bow +Z, dorsal +Y, port +X, at the RENDERED size: the blueprint was measured
with length 202.68 m (the installed module's 204.21 m x its class correction 0.9925), so the
envelope 56.1 x 73.9 x 202.7 m is already the 12-slot 840,000 m^3 and the class correction
stays ~1.0. Dimensions are blueprint measurements (measure.py: sections every 2 m, ortho depth
maps) unless noted as a design choice.

Main volumes (all chamfered prisms of mirrored half-profiles; tapers are UNIFORM SCALES of the
profile about a point on the centre line, so every tapered facet stays planar):
  engine block  z -85.0 .. -25.5  hexagonal section 55.3 x 31.5 m, stern frame, tapered front
                                  (the louvred intake bays sit on its forward flank facets)
  mid hull      z -26 .. 43.5     35 x 23 m, forward taper, framed front face (the gun gap, 11 m)
  bow block     z 54.3 .. 101.34  34.2 x 24 m, rear and nose tapers, the muzzle shroud
  tower         z -31.5 .. -62.5  forward block 21 x 18 m to y 26 and aft block 14.6 x 16 m,
                                  eight glazed deck rows, balconies, dome and mast
  railgun       spine, capacitor banks, the exposed barrel in the gap (z 43.5 .. 54.3: rails,
                clamp rings, copper coil packs, walkways with doors and ladders), muzzle boss
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

COPPER = Z['foil']   # zone 10 is painted as copper on this ship (destroyer_paint.py names it 'copper')

# ------------------------------------------------------------------------------------------
# key dimensions (blueprint, ship frame, rendered size)
# ------------------------------------------------------------------------------------------
BOW_Z = 101.34            # muzzle lip (bbox front)
BORE_Y = -18.55           # railgun axis (x 0)
# engine block half profile (deck centre -> port side -> keel centre)
E_HALF = [(0.0, -4.3), (15.0, -4.3), (27.67, -15.0), (27.67, -25.4), (14.9, -35.8), (0.0, -35.8)]
E_FRONT = (0.635, -19.5, -25.5)       # front taper: scale k about (0, yc) at z
E_STERN = -85.0                         # stern plate (bell bosses stand on it)
E_Z0, E_Z1 = -83.0, -35.0               # full-section run
M_HALF = [(0.0, -8.3), (12.5, -8.3), (17.5, -15.3), (17.5, -24.6), (11.5, -31.5), (0.0, -31.5)]
M_Z0, M_Z1, M_FRONT = -26.0, 21.0, 43.5
M_TAPER = (0.758, -21.5)
B_HALF = [(0.0, -6.4), (11.2, -6.4), (17.1, -13.6), (17.1, -22.7), (11.2, -30.4), (0.0, -30.4)]
B_REAR = (0.72, -18.4, 54.3)
B_Z0, B_Z1 = 58.4, 84.0
B_NOSE = (0.626, -18.7, 100.6)
SHROUD = (18.4, 11.8, 2.6)              # muzzle shroud: width, height, corner chamfer
SHROUD_BACK = 87.5
BOSS_FACE = 96.0                        # barrel boss face (the bore opening, muzzle anchor)
DECK_PITCH = 3.0


def scaled(half, k, yc):
    return [(x * k, yc + (y - yc) * k) for x, y in half]


def ring(half, z, d=0.0):
    pts = K.mirror_half(half)
    if d:
        pts = K.offset_poly(pts, d)
    return [V((x, y, z)) for x, y in pts]


def zone_rings(grid, seg_zones, rows=None):
    """Paint zones per profile segment (half profile of n points -> 2(n-1) ring segments)."""
    segs = len(seg_zones)
    zl = [seg_zones[j] if j < segs else seg_zones[2 * segs - 1 - j] for j in range(2 * segs)]
    for k, row in enumerate(grid):
        if rows is not None and k not in rows:
            continue
        for j, f in enumerate(row):
            if f is not None:
                f.material_index = Z[zl[j]]


def ring_solid(bm, outer, inner, plane, v0, v1, zone=0):
    """Closed ring solid between two nested closed 2D outlines (same point count) from v0 to v1."""
    O0, O1 = K.ring3(outer, plane, v0), K.ring3(outer, plane, v1)
    I0, I1 = K.ring3(inner, plane, v0), K.ring3(inner, plane, v1)
    n = len(outer)
    vs = {}
    for key, pts in (('o0', O0), ('o1', O1), ('i0', I0), ('i1', I1)):
        vs[key] = [bm.verts.new(p) for p in pts]
    for j in range(n):
        j2 = (j + 1) % n
        for a, b in (('o0', 'o1'), ('o1', 'i1'), ('i1', 'i0'), ('i0', 'o0')):
            f = bm.faces.new([vs[a][j], vs[a][j2], vs[b][j2], vs[b][j]])
            f.material_index = zone


def face_frame(pts):
    """Centroid, outward normal (right-hand winding) and in-plane up of a planar polygon."""
    P = [V(p) for p in pts]
    c = sum(P, V((0, 0, 0))) / len(P)
    n = (P[1] - P[0]).cross(P[2] - P[0]).normalized()
    return c, n


def rect_cutter(bm, c, n, up, w, h, depth, ch=0.15, zone_side=Z['recess'], zone_back=Z['recess'], out=1.0):
    grid, caps = K.oriented_prism(bm, K.chamfer_rect(0, 0, w, h, ch), c, n, up, -depth, out, zone=zone_side)
    caps[0].material_index = zone_back
    return grid, caps


def port(bm, c, n, up=(0, 1, 0), size=0.8, depth=0.2):
    """Recessed square port: 0.8 m glass at the back of a 0.2 m recess (glass zone)."""
    rect_cutter(bm, c, n, up, size, size, depth, ch=0.14, zone_back=Z['glass'])


def port_row(bm, a, b, pitch, n, up=(0, 1, 0), skip=(), size=0.8):
    a, b = V(a), V(b)
    L = (b - a).length
    k = max(1, int(math.floor(L / pitch + 1e-6)) + 1)
    off = (L - (k - 1) * pitch) / 2
    d = (b - a).normalized()
    cnt = 0
    for i in range(k):
        p = a + d * (off + i * pitch)
        if any(z0 <= p.z <= z1 for z0, z1 in skip):
            continue
        port(bm, p, n, up, size)
        cnt += 1
    return cnt


def mirrored_x(fn):
    """Call fn(side) for side +1 (port) and -1 (starboard)."""
    for s in (1, -1):
        fn(s)


# ------------------------------------------------------------------------------------------
# engine block
# ------------------------------------------------------------------------------------------
def engine_block():
    vol = Volume('engine', bevel=0.14)
    bm = vol.bm
    k, yc, zf = E_FRONT
    front = scaled(E_HALF, k, yc)
    rings = [ring(E_HALF, E_STERN, -2.6), ring(E_HALF, -84.2, -2.6), ring(E_HALF, -84.2, -1.5), ring(E_HALF, E_Z0),
             ring(E_HALF, E_Z1), ring(front, zf)]
    grid, caps = K.loft(bm, rings, zone=Z['paint'])
    zone_rings(grid, ['deck', 'paint', 'paint', 'paint', 'belly'], rows=[3, 4])
    zone_rings(grid, ['trim', 'trim', 'trim', 'trim', 'belly'], rows=[0, 1, 2])
    for f in caps:
        f.material_index = Z['recess'] if f.calc_center_median().z < -80 else Z['paint']
    K.solid(bm)
    cut = vol.cutters
    # flank port rows (three decks) on the flat flank, fore and aft of the mid band
    for s in (1, -1):
        n = (s, 0, 0)
        for y in (-17.2, -20.2, -23.2):
            port_row(cut, (s * 27.67, y, -37.8), (s * 27.67, y, -56.2), 2.5, n, skip=[(-51.4, -48.6)] if y == -20.2 else [])
            port_row(cut, (s * 27.67, y, -59.2), (s * 27.67, y, -81.2), 2.5, n)
        # upper row on the shoulder facet, lower two rows on the lower chamfer facet (normals from
        # the profile segments)
        sh = V((27.67 - 15.0, -15.0 + 4.3))
        nsh = V((s * 10.7, 12.67, 0)).normalized()
        for t, zr in ((0.72, [(-60.0, -81.0)]),):
            p = V((s * (15.0 + 12.67 * t), -4.3 - 10.7 * t, 0))
            for z0, z1 in zr:
                port_row(cut, (p.x, p.y, z0), (p.x, p.y, z1), 2.5, nsh, up=(-s * 0.764, 0.645, 0))
        nlo = V((s * 10.4, -12.77, 0)).normalized()
        for t in (0.28, 0.52):
            p = V((s * (27.67 - 12.77 * t), -25.4 - 10.4 * t, 0))
            for z0, z1 in ((-38.5, -56.0), (-59.5, -81.0)):
                port_row(cut, (p.x, p.y, z0), (p.x, p.y, z1), 2.5, nlo, up=(s * 0.775, 0.631, 0))
    # louvred vent bays on the shoulder facets (blueprint: square insets at x 16-24, z -40..-50)
    fins = []
    for s in (1, -1):
        nsh = V((s * 10.7, 12.67, 0)).normalized()
        upv = V((-s * 12.67, 10.7, 0)).normalized()   # up the slope, toward the deck
        for zc in (-45.0, -70.0):
            t = 0.42
            c = V((s * (15.0 + 12.67 * t), -4.3 - 10.7 * t, zc))
            rect_cutter(cut, c, nsh, upv, 9.0, 6.4, 0.5, ch=0.4, zone_back=Z['dark'])
            r_, u_, n_ = K.basis(nsh, upv)
            for dz in np.arange(-4.0, 4.01, 0.55):
                fins.append((c + r_ * dz - n_ * 0.28, Matrix((r_, u_, n_)).transposed()))
    vol.adds.append(('louvres', lambda bm2, fins=fins: [K.box(bm2, cc, (0.09, 6.2, 0.44), R=R, zone=Z['fin']) for cc, R in fins]))
    # intake bays on the forward flank facets of the taper (the concept's black grilles)
    for s in (1, -1):
        A = V((s * 27.67, -15.0, E_Z1)); B = V((s * 27.67, -25.4, E_Z1))
        fz = [(x * k, yc + (y - yc) * k) for x, y in ((27.67, -15.0), (27.67, -25.4))]
        Cc = V((s * fz[0][0], fz[0][1], zf)); D = V((s * fz[1][0], fz[1][1], zf))
        c = (A + B + Cc + D) / 4
        n = (Cc - A).cross(B - A).normalized()
        if n.x * s < 0:
            n = -n
        upv = (A - B).normalized()
        w = ((A + B) / 2 - (Cc + D) / 2).length
        rect_cutter(cut, c, n, upv, w - 1.6, 6.0, 1.1, ch=0.5, zone_back=Z['dark'])
        r_, u_, n_ = K.basis(n, upv)
        R = Matrix((r_, u_, n_)).transposed()
        pts = [c + r_ * dd - n_ * 0.6 for dd in np.arange(-(w - 2.6) / 2, (w - 2.6) / 2 + 0.01, 0.5)]
        vol.adds.append((f'grille{s}', lambda bm2, pts=pts, R=R: [K.box(bm2, pp, (0.08, 5.8, 0.95), R=R, zone=Z['fin']) for pp in pts]))
    K.solid(cut)
    return vol


def engine_details():
    vols = []
    # armour bands (0.22 m proud) at the segment joints
    b = Volume('engine_bands', bevel=0.06)
    ob_ = K.offset_poly(K.mirror_half(E_HALF), 0.22)
    ib_ = K.offset_poly(K.mirror_half(E_HALF), -0.4)
    for z0, z1 in ((-58.2, -56.8), (-36.4, -35.2), (-82.6, -81.6)):
        ring_solid(b.bm, ob_, ib_, 'xy', z0, z1, zone=Z['trim'])
    K.solid(b.bm)
    vols.append(b)
    # keel fin under the tower (blueprint: y -35.8 .. -36.9, z -44 .. -56)
    kf = Volume('keel_fin', bevel=0.06)
    prof = [(-57.0, -35.5), (-55.6, -36.9), (-44.4, -36.9), (-43.0, -35.5)]
    K.prism(kf.bm, prof, 'zy', -2.6, 2.6, zone=Z['belly'])
    K.solid(kf.bm)
    vols.append(kf)
    # dorsal: raised cable trunks either side of the aft turret, hatch plates, turret barbette
    d = Volume('engine_dorsal', bevel=0.05)
    for s in (1, -1):
        K.stack(d.bm, [(K.chamfer_rect(s * 7.2, -72.0, 1.4, 19.0, 0.3), -4.6), (K.chamfer_rect(s * 7.2, -72.0, 1.4, 19.0, 0.3), -3.9),
                       (K.chamfer_rect(s * 7.2, -72.0, 1.0, 18.6, 0.2), -3.7)], 'xz', zone=Z['metal'])
        # machinery cabinets and hatch plates aft of the turret (the VLS blocks are kit parts)
        K.stack(d.bm, [(K.chamfer_rect(s * 4.6, -80.6, 3.0, 3.4, 0.3), -4.6), (K.chamfer_rect(s * 4.6, -80.6, 3.0, 3.4, 0.3), -3.1),
                       (K.chamfer_rect(s * 4.6, -80.6, 2.6, 3.0, 0.2), -2.8)], 'xz', zone=Z['metal'])
        K.plate(d.bm, (s * 13.6, -4.3, -71.5), (0, 1, 0), (0, 0, 1), 2.2, 3.0, 0.12, ch=0.05, back=0.2, zone=Z['deck'])
        K.plate(d.bm, (s * 4.2, -4.3, -64.8), (0, 1, 0), (0, 0, 1), 2.4, 1.6, 0.1, ch=0.04, back=0.2, zone=Z['deck'])
    K.cyl(d.bm, (0, -4.8, -72.5), (0, -3.95, -72.5), 5.1, n=40, zone=Z['trim'])
    K.solid(d.bm)
    vols.append(d)
    # stern: bell bosses (corner) with ribs, the centre bell collar
    st = Volume('stern_bosses', bevel=0.05)
    for s in (1, -1):
        for y in (-13.71, -25.45):
            K.lathe(st.bm, (s * 13.45, y, E_STERN + 0.4), (0, 0, -1), [(5.35, 0.0), (5.35, 3.8), (4.95, 4.3), (4.95, 7.2)], n=32, zone=Z['metal'])
            for t in (1.0, 2.4):
                K.cyl(st.bm, (s * 13.45, y, E_STERN - t), (s * 13.45, y, E_STERN - t - 0.45), 5.6, n=32, zone=Z['trim'])
    K.lathe(st.bm, (0, -19.94, E_STERN + 0.4), (0, 0, -1), [(9.1, 0.0), (9.1, 1.2), (8.75, 1.6), (8.75, 3.2)], n=48, zone=Z['metal'])
    K.solid(st.bm)
    vols.append(st)
    return vols


# ------------------------------------------------------------------------------------------
# mid hull
# ------------------------------------------------------------------------------------------
BOAT = dict(z=-19.0, y=-19.9, w=7.2, h=8.2)      # framed boat hatch on the mid flank (blueprint frame z -14..-24)


def mid_hull():
    vol = Volume('mid', bevel=0.14)
    bm = vol.bm
    k, yc = M_TAPER
    fwd = scaled(M_HALF, k, yc)
    rings = [ring(M_HALF, M_Z0), ring(M_HALF, M_Z1), ring(fwd, M_FRONT), ring(fwd, M_FRONT, -0.6), ring(fwd, M_FRONT - 0.6, -0.6)]
    grid, caps = K.loft(bm, rings, cap0=True, cap1=True, zone=Z['paint'])
    zone_rings(grid, ['deck', 'paint', 'paint', 'paint', 'belly'], rows=[0, 1])
    zone_rings(grid, ['trim', 'trim', 'trim', 'trim', 'trim'], rows=[2, 3])
    for f in caps:
        f.material_index = Z['trim']
    K.solid(bm)
    cut = vol.cutters
    for s in (1, -1):
        n = (s, 0, 0)
        for y in (-17.2, -20.2, -23.2):
            port_row(cut, (s * 17.5, y, -12.0), (s * 17.5, y, 7.8), 2.5, n)
        port_row(cut, (s * 17.5, -23.2, -25.0), (s * 17.5, -23.2, -13.8), 2.5, n, skip=[(-24.2, -13.0)])
        # shoulder row
        nsh = V((s * 7.0, 5.0, 0)).normalized()
        p = V((s * (12.5 + 5.0 * 0.55), -8.3 - 7.0 * 0.55, 0))
        port_row(cut, (p.x, p.y, -24.5), (p.x, p.y, 19.5), 2.5, nsh, up=(-s * 0.581, 0.814, 0), skip=[(-4.0, -1.0)])
        # forward taper flank: one low row under the hull number
        ntp = V((s * 1.0, 0, (17.5 - 13.26) / (M_FRONT - M_Z1))).normalized()
        za, zb = 22.5, 41.0
        xa = 17.5 - (17.5 - 13.26) * (za - M_Z1) / (M_FRONT - M_Z1)
        xb = 17.5 - (17.5 - 13.26) * (zb - M_Z1) / (M_FRONT - M_Z1)
        ya = yc + (-23.4 - yc) * (1 - (1 - k) * (za - M_Z1) / (M_FRONT - M_Z1))
        yb = yc + (-23.4 - yc) * (1 - (1 - k) * (zb - M_Z1) / (M_FRONT - M_Z1))
        port_row(cut, (s * xa, ya, za), (s * xb, yb, zb), 2.3, ntp)
        # boat hatch bay: 0.6 m recess inside the frame
        c = V((s * 17.5, BOAT['y'], BOAT['z']))
        rect_cutter(cut, c, (s, 0, 0), (0, 1, 0), BOAT['w'] - 1.2, BOAT['h'] - 1.2, 0.6, ch=0.5, zone_back=Z['recess'])
    K.solid(cut)
    return vol


def mid_details():
    vols = []
    # boat hatch: raised frame (0.35 m proud) and two leaves split vertically, 0.25 m proud of the bay
    bh = Volume('boat_hatch', bevel=0.05)
    for s in (1, -1):
        c = V((s * 17.5, BOAT['y'], BOAT['z']))
        outer = K.chamfer_rect(BOAT['z'], BOAT['y'], BOAT['w'], BOAT['h'], 0.8)
        inner = K.chamfer_rect(BOAT['z'], BOAT['y'], BOAT['w'] - 1.2, BOAT['h'] - 1.2, 0.5)
        x0, x1 = (17.3, 17.85) if s > 0 else (-17.85, -17.3)
        ring_solid(bh.bm, outer, inner, 'zy', x0, x1, zone=Z['trim'])
        lw = (BOAT['w'] - 1.2) / 2 - 0.06
        for dz in (-1, 1):
            zc = BOAT['z'] + dz * (lw / 2 + 0.03)
            leaf = K.chamfer_rect(zc, BOAT['y'], lw, BOAT['h'] - 1.32, 0.12)
            xa, xb = (17.5 - 0.62, 17.5 - 0.36) if s > 0 else (-17.5 + 0.36, -17.5 + 0.62)
            K.prism(bh.bm, leaf, 'zy', xa, xb, zone=Z['paint'])
            # stiffener ribs on each leaf
            for dy in (-2.2, 0.0, 2.2):
                rib = K.chamfer_rect(zc, BOAT['y'] + dy + (1.3 if dz < 0 and dy == -2.2 else 0), lw - 0.5, 0.22, 0.05)
                if dz < 0 and dy == -2.2:
                    continue   # the personnel door sits there
                xr0, xr1 = (xb - 0.02, xb + 0.1) if s > 0 else (xa - 0.1, xa + 0.02)
                K.prism(bh.bm, rib, 'zy', xr0, xr1, zone=Z['trim'])
    K.solid(bh.bm)
    vols.append(bh)
    # ventral keel box
    kb = Volume('keel_mid', bevel=0.06)
    prof = [(-24.5, -31.2), (-23.3, -33.4), (17.8, -33.4), (19.0, -31.2)]
    K.prism(kb.bm, prof, 'zy', -5.0, 5.0, zone=Z['belly'])
    K.solid(kb.bm)
    for zc in (-16.0, -6.0, 4.0, 12.0):
        rect_cutter(kb.cutters, (0, -33.4, zc), (0, -1, 0), (0, 0, 1), 7.0, 3.2, 0.35, ch=0.3, zone_back=Z['dark'])
    K.solid(kb.cutters)
    kb.adds.append(('slats', lambda bm2: [K.box(bm2, (x, -33.25, zc), (0.1, 0.3, 3.0), zone=Z['fin'])
                                           for zc in (-16.0, -6.0, 4.0, 12.0) for x in np.arange(-3.0, 3.01, 0.5)]))
    vols.append(kb)
    # sponsons for the flank guns (blueprint: z 10..18.5, out to x +-21, y -18..-23)
    sp = Volume('sponsons', bevel=0.08)
    for s in (1, -1):
        prof = K.chamfer_rect(14.2, -20.2, 9.0, 6.6, 1.2)
        K.stack(sp.bm, [(prof, s * 16.8), (prof, s * 19.2), (K.chamfer_rect(14.2, -20.2, 8.0, 5.6, 0.9), s * 19.7)], 'zy', zone=Z['paint'])
    K.solid(sp.bm)
    vols.append(sp)
    # pre-tower deckhouse (blueprint z -31..-13, x +-9.5, top y 2.2) and the drum ahead of it
    dh = Volume('deckhouse', bevel=0.1)
    base = K.chamfer_rect(0, -22.0, 19.0, 18.0, 2.0)
    K.stack(dh.bm, [(base, -8.6), (base, 0.9), (K.chamfer_rect(0, -22.2, 16.6, 16.0, 1.6), 2.2)], 'xz', zone=Z['paint'])
    K.solid(dh.bm)
    for s in (1, -1):
        for y in (-5.2, -2.2):
            port_row(dh.cutters, (s * 9.5, y, -28.8), (s * 9.5, y, -15.2), 2.3, (s, 0, 0))
    for x in np.arange(-6.0, 6.01, 2.3):
        port(dh.cutters, (x, -2.2, -13.0), (0, 0, 1))
    K.solid(dh.cutters)
    vols.append(dh)
    dr = Volume('drum', bevel=0.06)
    K.stack(dr.bm, [(K.chamfer_rect(0, -9.6, 12.0, 7.2, 1.6), -8.6), (K.chamfer_rect(0, -9.6, 12.0, 7.2, 1.6), -2.2),
                    (K.chamfer_rect(0, -9.6, 10.8, 6.0, 1.2), -1.4)], 'xz', zone=Z['paint'])
    for zc in (-12.3, -9.6, -6.9):
        K.stack(dr.bm, [(K.chamfer_rect(0, zc, 12.5, 0.5, 0.2), -8.6), (K.chamfer_rect(0, zc, 12.5, 0.5, 0.2), -2.0)], 'xz', zone=Z['trim'])
    K.solid(dr.bm)
    vols.append(dr)
    return vols


# ------------------------------------------------------------------------------------------
# bow block
# ------------------------------------------------------------------------------------------
def bow_block():
    vol = Volume('bow', bevel=0.14)
    bm = vol.bm
    kr, ycr, zr = B_REAR
    kn, ycn, zn = B_NOSE
    rear = scaled(B_HALF, kr, ycr)
    nose = scaled(B_HALF, kn, ycn)
    rings = [ring(rear, zr + 0.6, -0.6), ring(rear, zr, -0.6), ring(rear, zr), ring(B_HALF, B_Z0), ring(B_HALF, B_Z1), ring(nose, zn)]
    grid, caps = K.loft(bm, rings, zone=Z['paint'])
    zone_rings(grid, ['deck', 'paint', 'paint', 'paint', 'belly'], rows=[2, 3, 4])
    zone_rings(grid, ['trim'] * 5, rows=[0, 1])
    for f in caps:
        f.material_index = Z['trim']
    K.solid(bm)
    cut = vol.cutters
    # muzzle shroud: octagonal recess 14 m deep
    w, h, ch = SHROUD
    K.prism(cut, K.chamfer_rect(0, BORE_Y, w, h, ch), 'xy', SHROUD_BACK, BOW_Z + 2.0, zone=Z['recess'])
    for s in (1, -1):
        for y in (-15.6, -20.8):
            port_row(cut, (s * 17.1, y, 61.0), (s * 17.1, y, 82.5), 2.5, (s, 0, 0), skip=[(69.0, 71.5)] if y == -20.8 else [])
        nsh = V((s * 7.2, 5.9, 0)).normalized()
        p = V((s * (11.2 + 5.9 * 0.5), -6.4 - 7.2 * 0.5, 0))
        port_row(cut, (p.x, p.y, 61.0), (p.x, p.y, 82.5), 2.5, nsh, up=(-s * 0.634, 0.773, 0))
    K.solid(cut)
    return vol


def bow_details():
    vols = []
    # muzzle lip: a frame ring round the shroud mouth, proud of the nose face to the bbox front
    lip = Volume('muzzle_lip', bevel=0.06)
    kn, ycn, zn = B_NOSE
    nh = scaled(B_HALF, kn, ycn)        # (0,top) (x1,top) (x2,y2) (x2,y3) (x1,bot) (0,bot)
    nose8 = [nh[1], nh[2], nh[3], nh[4], (-nh[4][0], nh[4][1]), (-nh[3][0], nh[3][1]), (-nh[2][0], nh[2][1]), (-nh[1][0], nh[1][1])]
    outer = K.offset_poly(nose8, -0.35)
    w, h, ch = SHROUD
    yt, yb, xh = BORE_Y + h / 2, BORE_Y - h / 2, w / 2
    inner = [(xh - ch, yt), (xh, yt - ch), (xh, yb + ch), (xh - ch, yb), (-xh + ch, yb), (-xh, yb + ch), (-xh, yt - ch), (-xh + ch, yt)]
    ring_solid(lip.bm, outer, inner, 'xy', zn - 0.3, BOW_Z, zone=Z['trim'])
    K.solid(lip.bm)
    vols.append(lip)
    # barrel boss in the shroud, hexagonal bore, field-coil rings on the shroud walls
    bo = Volume('muzzle_boss', bevel=0.06)
    K.stack(bo.bm, [(K.chamfer_rect(0, BORE_Y, 13.4, 9.4, 2.2), SHROUD_BACK - 0.5), (K.chamfer_rect(0, BORE_Y, 13.4, 9.4, 2.2), BOSS_FACE - 0.5),
                    (K.chamfer_rect(0, BORE_Y, 12.4, 8.4, 1.8), BOSS_FACE)], 'xy', zone=Z['metal'])
    K.solid(bo.bm)
    K.lathe(bo.cutters, (0, BORE_Y, BOSS_FACE + 1.0), (0, 0, -1), [(3.9, 0.0), (3.9, 1.0), (3.05, 1.85), (3.05, 8.5)], n=6, zone=Z['nozzle'])
    K.solid(bo.cutters)
    vols.append(bo)
    co = Volume('muzzle_coils', bevel=0.03, cull=False)
    for zc in (90.0, 92.2, 94.4):
        ring_solid(co.bm, K.chamfer_rect(0, BORE_Y, w + 0.2, h + 0.2, ch), K.chamfer_rect(0, BORE_Y, w - 0.7, h - 0.7, ch - 0.25), 'xy', zc, zc + 0.8, zone=COPPER)
    K.solid(co.bm)
    vols.append(co)
    # dorsal turret barbette, ventral turret barbette, hatch plates, blue band plinth
    d = Volume('bow_dorsal', bevel=0.05)
    K.cyl(d.bm, (0, -6.7, 69.0), (0, -5.9, 69.0), 5.3, n=40, zone=Z['trim'])
    K.cyl(d.bm, (0, -30.1, 72.0), (0, -30.9, 72.0), 5.0, n=40, zone=Z['trim'])
    for s in (1, -1):
        K.plate(d.bm, (s * 8.6, -6.4, 59.5), (0, 1, 0), (0, 0, 1), 3.0, 3.0, 0.12, ch=0.05, back=0.2, zone=Z['deck'])
        K.plate(d.bm, (s * 3.0, -6.4, 81.8), (0, 1, 0), (0, 0, 1), 2.4, 1.8, 0.1, ch=0.04, back=0.2, zone=Z['deck'])
    K.solid(d.bm)
    vols.append(d)
    b = Volume('bow_bands', bevel=0.05)
    ob_ = K.offset_poly(K.mirror_half(B_HALF), 0.2)
    ib_ = K.offset_poly(K.mirror_half(B_HALF), -0.4)
    ring_solid(b.bm, ob_, ib_, 'xy', 83.0, 84.2, zone=Z['trim'])
    ring_solid(b.bm, ob_, ib_, 'xy', 59.0, 60.0, zone=Z['trim'])
    K.solid(b.bm)
    vols.append(b)
    return vols


# ------------------------------------------------------------------------------------------
# railgun: spine, capacitor banks, the exposed barrel in the gap
# ------------------------------------------------------------------------------------------
GAP = (M_FRONT - 0.6, B_REAR[2] + 0.6)        # faces of the gap (mid front face, bow rear face)
WALK_Y = -26.3                            # walkway deck top in the gap


def railgun():
    vols = []
    sp = Volume('spine', bevel=0.08)
    prof = K.chamfer_rect(0, -8.75, 8.8, 6.5, 1.0)
    K.prism(sp.bm, prof, 'xy', -2.5, 61.0, zone=Z['paint'])
    K.solid(sp.bm)
    vols.append(sp)
    rl = Volume('spine_rails', bevel=0.03)
    for s in (1, -1):
        K.cyl(rl.bm, (s * 2.2, -5.1, -2.0), (s * 2.2, -5.1, 60.6), 0.36, n=12, zone=Z['metal'])
        # outer rails on saddles (blueprint: x +-10.35, y -6, z 20..62)
        K.cyl(rl.bm, (s * 10.35, -5.95, 20.5), (s * 10.35, -5.95, 62.5), 0.45, n=12, zone=Z['metal'])
        for z in (23.5, 30.0, 36.5, 42.0):
            yb = -8.3 - (z - M_Z1) / (M_FRONT - M_Z1) * 3.4
            K.box(rl.bm, (s * 10.35, (yb - 5.95) / 2 - 0.25, z), (0.9, -5.95 - yb + 0.5, 1.0), zone=Z['trim'])
            K.box(rl.bm, (s * 10.35, -5.95, z), (1.3, 1.1, 1.4), zone=Z['trim'])
        for z in (58.0, 61.5):
            K.box(rl.bm, (s * 10.35, -6.2, z), (0.6, 0.6, 0.6), zone=Z['trim'])
        # spine rail clamps
        for z in np.arange(0.0, 60.1, 6.0):
            K.box(rl.bm, (s * 2.2, -5.15, z), (1.1, 0.5, 0.4), zone=Z['trim'])
    K.solid(rl.bm)
    vols.append(rl)
    # capacitor banks either side of the spine (three per side, z -0.5 .. 20.4)
    cb = Volume('cap_banks', bevel=0.06)
    for s in (1, -1):
        for z0, z1 in ((-0.5, 5.8), (6.8, 13.1), (14.1, 20.4)):
            zc, L = (z0 + z1) / 2, z1 - z0
            xc = s * 8.1
            K.stack(cb.bm, [(K.chamfer_rect(xc, zc, 6.4, L, 0.3), -8.6), (K.chamfer_rect(xc, zc, 6.4, L, 0.3), -4.7),
                            (K.chamfer_rect(xc, zc, 5.6, L - 0.8, 0.2), -4.3)], 'xz', zone=Z['paint'])
            for dz in (-L / 4, L / 4):
                K.plate(cb.bm, (xc, -4.3, zc + dz), (0, 1, 0), (0, 0, 1), 4.6, L / 2 - 0.6, 0.12, ch=0.04, back=0.15, zone=Z['trim'])
    # equipment on the mid hull's forward deck, outboard of the spine: cabinets and hatch plates
    for s in (1, -1):
        for zc, L in ((26.0, 3.2), (33.5, 2.4)):
            yb = -8.3 - (zc - M_Z1) / (M_FRONT - M_Z1) * 3.2
            K.stack(cb.bm, [(K.chamfer_rect(s * 7.2, zc, 2.2, L, 0.25), yb - 0.6), (K.chamfer_rect(s * 7.2, zc, 2.2, L, 0.25), yb + 1.2),
                            (K.chamfer_rect(s * 7.2, zc, 1.9, L - 0.3, 0.15), yb + 1.4)], 'xz', zone=Z['metal'])
    K.solid(cb.bm)
    vols.append(cb)
    # copper bus bars between the banks and into the spine
    bus = Volume('bus', bevel=0.02, cull=False)
    for s in (1, -1):
        for z in (6.3, 13.6):
            for y in (-5.5, -6.3):
                K.cyl(bus.bm, (s * 4.2, y, z), (s * 11.0, y, z), 0.18, n=8, zone=COPPER)
    K.solid(bus.bm)
    vols.append(bus)
    # --- the exposed barrel in the gap -------------------------------------------------------
    g0, g1 = GAP[0] - 0.5, GAP[1] + 0.5
    br = Volume('barrel', bevel=0.05)
    K.cyl(br.bm, (0, BORE_Y, g0), (0, BORE_Y, g1), 3.3, n=16, zone=Z['metal'])
    for dy in (4.2, -4.2):   # the rails: two massive bars above and below the bore
        K.stack(br.bm, [(K.chamfer_rect(0, BORE_Y + dy, 3.2, 1.8, 0.3), g0), (K.chamfer_rect(0, BORE_Y + dy, 3.2, 1.8, 0.3), g1)], 'xy', zone=Z['metal'])
    # rail web plates tying the rails to the liner
    for dy in (2.6, -2.6):
        K.box(br.bm, (0, BORE_Y + dy, (g0 + g1) / 2), (1.2, 1.6, g1 - g0), zone=Z['dark'])
    # neck from the spine down to the upper rail
    K.box(br.bm, (0, -11.3, (g0 + g1) / 2), (3.0, 3.6, g1 - g0), zone=Z['paint'])
    K.solid(br.bm)
    vols.append(br)
    cl = Volume('clamps', bevel=0.05, cull=False)
    for zc in np.linspace(GAP[0] + 1.3, GAP[1] - 1.3, 4):
        ring_solid(cl.bm, K.chamfer_rect(0, BORE_Y, 11.0, 12.4, 2.0), K.chamfer_rect(0, BORE_Y, 6.8, 10.2, 1.6), 'xy', zc - 0.35, zc + 0.35, zone=Z['trim'])
    K.solid(cl.bm)
    vols.append(cl)
    # coil packs either side: two cylinders per side wound with copper coils
    cp = Volume('coil_packs', bevel=0.0, cull=False)
    for s in (1, -1):
        for y in (-16.2, -21.0):
            K.cyl(cp.bm, (s * 7.6, y, g0), (s * 7.6, y, g1), 1.45, n=16, zone=Z['metal'])
            # copper windings: thin turns on a 0.36 m pitch, 16-sided so they shade round (22.5 deg < the
            # 30 deg sharp limit), grouped in three coils with steel spacer collars between them
            L = GAP[1] - GAP[0] - 1.0
            for k in range(3):
                c0 = GAP[0] + 0.5 + k * L / 3
                for zc in np.arange(c0 + 0.35, c0 + L / 3 - 0.35, 0.36):
                    K.cyl(cp.bm, (s * 7.6, y, zc), (s * 7.6, y, zc + 0.2), 1.62, n=16, zone=COPPER)
                K.cyl(cp.bm, (s * 7.6, y, c0 - 0.1), (s * 7.6, y, c0 + 0.2), 1.78, n=16, zone=Z['trim'])
        # cable conduits along the outer side
        for y in (-14.0, -23.0):
            K.cyl(cp.bm, (s * 10.9, y, g0), (s * 10.9, y, g1), 0.34, n=10, zone=Z['dark'])
    K.solid(cp.bm)
    vols.append(cp)
    # walkways in the gap: deck plates on brackets, from the barrel housing to the outboard edge
    wk = Volume('walkways', bevel=0.03, cull=False)
    for s in (1, -1):
        K.box(wk.bm, (s * 8.3, WALK_Y - 0.15, (GAP[0] + GAP[1]) / 2), (5.6, 0.3, GAP[1] - GAP[0] + 0.6), zone=Z['deck'])
        for zc in np.linspace(GAP[0] + 1.0, GAP[1] - 1.0, 4):
            K.box(wk.bm, (s * 8.3, WALK_Y - 0.75, zc), (5.2, 0.9, 0.25), zone=Z['dark'])
    K.solid(wk.bm)
    vols.append(wk)
    return vols


# ------------------------------------------------------------------------------------------
# tower
# ------------------------------------------------------------------------------------------
T1 = dict(zc=-40.5, w=21.0, l=18.0, c=2.2, y0=0.6, y1=24.6, roof=26.0)
T2 = dict(zc=-54.5, w=14.6, l=16.0, c=1.4, y0=0.6, y1=25.0, roof=25.6)
BANDS = [2.8 + DECK_PITCH * i for i in range(8)]     # glazed deck rows (y centres), 0.9 m tall
BAND_H, BAND_D = 0.9, 0.35
BALCONY_Y = (10.6, 16.6)


def outline(t, d=0.0):
    o = K.chamfer_rect(0, t['zc'], t['w'], t['l'], t['c'])
    return K.offset_poly(o, d) if d else o


def band_cutter(bm, t, y):
    ring_solid(bm, outline(t, 3.0), outline(t, -BAND_D), 'xz', y - BAND_H / 2, y + BAND_H / 2, zone=Z['recess'])


def mullions(t, y, hidden):
    """Mullion boxes along the band's back wall, every 1.12 m, skipping corners and hidden runs."""
    o = outline(t, -BAND_D + 0.16)
    out = []
    n = len(o)
    for i in range(n):
        a, b = V(o[i]), V(o[(i + 1) % n])
        L = (b - a).length
        d = (b - a).normalized()
        k = int(L / 1.12)
        if k < 1:
            continue
        off = (L - k * 1.12) / 2
        for j in range(k + 1):
            p = a + d * (off + j * 1.12)
            if hidden(p.x, p.y):
                continue
            Rm = Matrix(((d.x, 0, d.y), (0, 1, 0), (d.y, 0, -d.x))).transposed()   # columns: along, up, out
            out.append((V((p.x, y, p.y)), Rm))
    return out


def tower():
    vols = []
    t0 = Volume('tower_base', bevel=0.1)
    base = K.chamfer_rect(0, -46.5, 24.0, 30.0, 3.0)
    K.stack(t0.bm, [(base, -8.0), (base, 0.6), (K.chamfer_rect(0, -46.5, 22.8, 28.8, 2.4), 1.2)], 'xz', zone=Z['paint'])
    K.solid(t0.bm)
    vols.append(t0)
    for name, t, hid in (('tower_fwd', T1, lambda x, z: z < -49.2 and abs(x) < 7.8),
                         ('tower_aft', T2, lambda x, z: z > -49.8)):
        v = Volume(name, bevel=0.1)
        top = outline(t, -1.4 if t is T1 else -0.8)
        K.stack(v.bm, [(outline(t), t['y0']), (outline(t), t['y1']), (top, t['roof'])], 'xz', zone=Z['paint'])
        K.solid(v.bm)
        mm = []
        for y in BANDS:
            if y + BAND_H / 2 > t['y1'] - 0.2:
                continue
            band_cutter(v.cutters, t, y)
            mm += mullions(t, y, hid)
        K.solid(v.cutters)
        v.adds.append(('mullions', lambda bm2, mm=mm: [K.box(bm2, c, (0.12, BAND_H + 0.02, 0.34), R=R, zone=Z['trim']) for c, R in mm]))
        vols.append(v)
    # deck ledges round the forward block (every second row) and balconies on the aft block
    le = Volume('tower_ledges', bevel=0.04)
    for y in BANDS[1::2]:
        yl = y - BAND_H / 2 - 0.35
        ring_solid(le.bm, outline(T1, 0.45), outline(T1, -0.2), 'xz', yl - 0.3, yl, zone=Z['trim'])
    for yb in BALCONY_Y:
        for s in (1, -1):
            x0, x1 = (T2['w'] / 2 - 0.3, 11.2) if s > 0 else (-11.2, -T2['w'] / 2 + 0.3)
            K.box(le.bm, ((x0 + x1) / 2, yb - 0.25, -56.0), (x1 - x0, 0.5, 12.6), zone=Z['deck'])
            for zc in (-50.4, -55.9, -61.4):
                K.box(le.bm, ((x0 + x1) / 2, yb - 0.9, zc), (x1 - x0 - 0.4, 0.8, 0.3), zone=Z['trim'])
    K.solid(le.bm)
    vols.append(le)
    # roof: dome plinth and mast pylon on the aft block, equipment on the forward roof
    rf = Volume('tower_roof', bevel=0.05)
    K.cyl(rf.bm, (0, T2['roof'] - 0.3, -54.0), (0, 29.6, -54.0), 2.9, n=32, zone=Z['paint'])
    K.stack(rf.bm, [(K.chamfer_rect(0, -60.3, 1.4, 1.4, 0.2), T2['roof'] - 0.3), (K.chamfer_rect(0, -60.3, 1.0, 1.0, 0.15), 30.0)], 'xz', zone=Z['metal'])
    K.plate(rf.bm, (5.0, T1['roof'], -37.0), (0, 1, 0), (0, 0, 1), 3.0, 4.0, 1.2, ch=0.08, back=0.2, zone=Z['metal'])
    K.plate(rf.bm, (-5.0, T1['roof'], -37.0), (0, 1, 0), (0, 0, 1), 3.0, 4.0, 0.9, ch=0.08, back=0.2, zone=Z['paint'])
    K.plate(rf.bm, (0.0, T1['roof'], -43.5), (0, 1, 0), (0, 0, 1), 5.0, 3.0, 0.14, ch=0.05, back=0.2, zone=Z['deck'])
    K.solid(rf.bm)
    vols.append(rf)
    return vols


# ------------------------------------------------------------------------------------------
# build
# ------------------------------------------------------------------------------------------
# volumes unwrapped at reduced texel density: small repeated parts in one flat zone colour
# (not the copper coil turns: at a reduced density their 0.2 m faces fall between texel centres, miss the
# bake and show the empty-texel fill)
DETAIL = {'clamps', 'walkways', 'tower_ledges'}


def build(args):
    t0 = time.time()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    K.zone_materials()
    vols = [engine_block(), *engine_details(), mid_hull(), *mid_details(), bow_block(), *bow_details(), *railgun(), *tower()]
    obs = []
    for v in vols:
        ob = v.to_object()
        ob['bevel'] = v.bevel
        ob['angle'] = v.angle
        ob['cull'] = v.cull
        if len(v.cutters.faces):
            t1 = time.time()
            cut = v.to_object(v.cutters, v.name + '_cut')
            n0 = len(ob.data.polygons)
            K.boolean(ob, cut)
            bpy.data.objects.remove(cut)
            if len(ob.data.polygons) < n0:
                raise RuntimeError(f'boolean on {v.name} lost the solid ({n0} -> {len(ob.data.polygons)} faces): coincident cutters?')
            K.log(f'boolean {v.name}: {time.time() - t1:.1f}s')
        obs.append(ob)
        for nm, fn in v.adds:
            bm = bmesh.new()
            fn(bm)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            vv = Volume(f'{v.name}_{nm}')
            ob2 = vv.to_object(bm, f'{v.name}_{nm}')
            ob2['bevel'] = 0.0 if nm in ('louvres', 'mullions', 'slats') or nm.startswith('grille') else 0.03   # thin repeated fins: flat, 12 tris each
            ob2['angle'] = 30.0
            ob2['cull'] = False
            ob2['closed'] = False
            obs.append(ob2)
    K.log(f'volumes: {len(obs)} objects, {sum(K.count_tris(o) for o in obs)} tris before bevel ({time.time() - t0:.1f}s)')
    if not args.get('no_cull'):
        K.cull_hidden(obs)
    import destroyer_uv
    for ob in obs:
        # thin single-zone fins (mullions, louvres, slats) and DETAIL volumes at a reduced density: their
        # tiny islands sit among islands of the same zone, so a face that misses every texel centre still
        # samples its own colour
        detail = (not ob.get('closed', True)) or ob.name in DETAIL
        destroyer_uv.pre_unwrap(ob, density=0.3 if detail else 1.0)
        K.finish(ob, ob['bevel'], ob['angle'])
    K.log('tris per object: ' + ', '.join(f'{o.name} {K.count_tris(o)}' for o in sorted(obs, key=lambda o: -K.count_tris(o))[:18]))
    hullob = K.join(obs, 'hull')
    K.log(f'joined: {K.count_tris(hullob)} tris ({time.time() - t0:.1f}s)')
    return hullob


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    work = os.path.abspath(argv[0])
    opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d
    stage = opt('--stage', 'all')
    os.makedirs(work, exist_ok=True)
    blend = os.path.join(work, 'destroyer-hull.blend')
    maps = os.path.join(work, 'maps.npz')
    tex = int(opt('--tex', 4096))
    ptex = int(opt('--paint-tex', tex))
    if stage in ('all', 'model'):
        ob = build({'no_cull': '--no-cull' in argv})
        import destroyer_uv
        info = destroyer_uv.pack(ob)
        K.log('uv', info)
        bpy.ops.wm.save_as_mainfile(filepath=blend)
        json.dump({'tris': K.count_tris(ob), **info}, open(os.path.join(work, 'model.json'), 'w'), indent=1)
        if stage == 'model' and '--bake' not in argv:
            return
        m = K.bake_maps(ob, size=tex, ao_size=int(opt('--ao', 2048)), threads=int(opt('--threads', 4)))
        np.savez_compressed(maps, **m)
    if stage in ('all', 'paint'):
        import destroyer_paint as DP
        bpy.ops.wm.open_mainfile(filepath=blend)
        ob = bpy.data.objects['hull']
        m = dict(np.load(maps))
        spec = DP.spec()
        spec['px_per_m'] = json.load(open(os.path.join(work, 'model.json')))['px_per_m_at_4096'] * ptex / 4096
        base, orm, nrm = DP.paint(m, spec, work, size=ptex, normal_size=int(opt('--normal-tex', min(ptex, 4096))))
        K.set_final_material(ob, base, orm, normal_png=nrm)
        glb = os.path.join(work, 'destroyer-hull.glb')
        K.export_glb(ob, glb)
        K.log('wrote', glb, os.path.getsize(glb))


if __name__ == '__main__':
    main()


# ------------------------------------------------------------------------------------------
# ship-module draft (module.py, then destroyer_module.py): fixed asset fields, light roles,
# surfaces to measure
# ------------------------------------------------------------------------------------------
MODULE = {
    'header': """// Destroyer DD-12 — v3 REMODEL: clean hard-surface hull (tools/blender/hulls/destroyer.py) rebuilt from
// measurements of the fal / Tripo H3.1 blueprint (the v5 true-scale-details hull), painted in texture space
// (tools/blender/hulls/destroyer_paint.py: light paint, plating seams and tone, varied access panels, PATINA
// plate tone, AO grime, edge wear, decals incl. the DD-12 stencils) at 8192 px, and assembled with the Blender
// parts kit (tools/blender/specs/destroyer-v3.json via tools/blender/assemble.py).
// The GLB is in the ship frame at the RENDERED size (metres, bow +Z, dorsal +Y, port +X): rotate [0, 0, 0],
// length = the assembled bbox length, so the 12-slot class correction stays ~1.0. Node 'hull' is the hull,
// 'parts_*' the kit parts (hullNodes).
// The spinal railgun is modelled parametrically (the kit's railgun-segment would have to be scaled x2.3 to
// the blueprint's 6 m bore, blowing its hatches and walkways up to giant size): the octagonal muzzle shroud
// (18.4 x 11.8 m, 13.8 m deep) with a barrel boss and a hexagonal bore, the barrel exposed in the gap between
// the mid hull and the bow block (liner, two rail bars, clamp rings, copper-wound coil packs, cable
// conduits, walkways with 1 x 2 m doors, ladders and hand rails at true scale), the dorsal spine with its
// rails and the capacitor banks.
// Engines: kit bells (bell-L x1.237 corner bells: CORNER_BELL, bell-XL x1.106 centre dish) with the kit's
// documented engine entry (depth to the throat plate, throat, inner wall) times that scale.
// Lights: at the lenses of the kit nav-light housings.""",
    'meta': {
        'name': 'Bastion-class destroyer', 'designation': 'DD-12', 'crew': 'about 2,000',
        'blurb': 'Heavy line destroyer built around a massive spinal railgun: an armoured bow block with the recessed muzzle, the barrel exposed in the gun gap between the bow block and the mid hull, a rail spine with capacitor banks along the back, a many-deck bridge tower, naval turrets fore, aft and in flank sponsons, louvred intakes on the engine section and five fusion bells in the stern.',
    },
    'asset': {
        'glb': './assets/ships/destroyer.glb', 'generator': 'tools/blender/hulls/destroyer.py (remodel of the tripo3d/h3.1/multiview-to-3d hull) + tools/blender/assemble.py',
        'concept': './assets/concepts/destroyer.webp', 'beauty': './assets/concepts/destroyer-beauty.webp',
        'rotate': [0, 0, 0], 'hullNodes': ['hull'],
        # remodel paint is lighter than the generated textures: gain 0.05 matches the fleet grey; kit and
        # hull glass get a dim warm interior light (livery.js glassGlow, opt-in)
        'livery': {'gain': 0.05, 'glassGlow': [0.06, 0.055, 0.046], 'glassLit': 0.35},
        # runtime PATINA micro detail, turned down: the hull carries its own plating seams and panel breaks
        'detail': {'set': 'hull', 'tile': 6, 'normalStrength': 0.6, 'roughAmount': 0.5, 'cavity': 0.2},
    },
    # in navlight placement order: sidelight port, starboard, tower strobe, keel strobe, stern
    'lights': [
        {'color': 'red', 'note': 'steady sidelights on the flat flank of the engine section (the beam extremity): red port, green starboard'},
        {'color': 'green'},
        {'color': 'white', 'blink': {'period': 1.3, 'duty': 0.1}, 'note': 'anti-collision strobes, alternating: tower roof ahead of the dome and the keel fin under the tower'},
        {'color': 'white', 'blink': {'period': 1.3, 'duty': 0.1, 'phase': 0.5}},
        {'color': 'white', 'note': 'steady stern light on the stern plate above the centre dish'},
    ],
    'surfaces': {
        'engine-flank-port': {'centre': [27.67, -20.2, -47.0], 'normal': [1, 0, 0], 'u': [0, 0, 1], 'width': 18.0, 'height': 9.0, 'note': 'flat flank of the engine section ahead of the mid band (three port rows)'},
        'engine-flank-stbd': {'centre': [-27.67, -20.2, -47.0], 'normal': [-1, 0, 0], 'u': [0, 0, -1], 'width': 18.0, 'height': 9.0},
        'engine-flank-aft-port': {'centre': [27.67, -20.2, -70.0], 'normal': [1, 0, 0], 'u': [0, 0, 1], 'width': 22.0, 'height': 9.0},
        'engine-flank-aft-stbd': {'centre': [-27.67, -20.2, -70.0], 'normal': [-1, 0, 0], 'u': [0, 0, -1], 'width': 22.0, 'height': 9.0},
        'mid-flank-port': {'centre': [17.5, -20.0, -2.0], 'normal': [1, 0, 0], 'u': [0, 0, 1], 'width': 18.0, 'height': 8.6, 'note': 'mid-hull flank between the boat hatch and the sponson (three port rows, cobalt band)'},
        'mid-flank-stbd': {'centre': [-17.5, -20.0, -2.0], 'normal': [-1, 0, 0], 'u': [0, 0, -1], 'width': 18.0, 'height': 8.6},
        'boat-hatch-port': {'centre': [17.14, -19.9, -19.0], 'normal': [1, 0, 0], 'u': [0, 0, 1], 'width': 5.8, 'height': 6.8, 'note': 'boat hatch leaves (6 x 7 m opening, 1 x 2 m personnel door in the aft leaf)'},
        'boat-hatch-stbd': {'centre': [-17.14, -19.9, -19.0], 'normal': [-1, 0, 0], 'u': [0, 0, -1], 'width': 5.8, 'height': 6.8},
        'bow-flank-port': {'centre': [17.1, -18.2, 70.5], 'normal': [1, 0, 0], 'u': [0, 0, 1], 'width': 24.0, 'height': 8.6, 'note': 'bow block flank (two port rows)'},
        'bow-flank-stbd': {'centre': [-17.1, -18.2, 70.5], 'normal': [-1, 0, 0], 'u': [0, 0, -1], 'width': 24.0, 'height': 8.6},
        'engine-deck': {'centre': [0.0, -4.3, -80.5], 'normal': [0, 1, 0], 'u': [0, 0, 1], 'width': 5.0, 'height': 3.0, 'note': 'engine-section deck aft of the aft turret'},
        'spine-top': {'centre': [0.0, -5.5, 32.0], 'normal': [0, 1, 0], 'u': [1, 0, 0], 'width': 3.0, 'height': 20.0, 'note': 'rail spine catwalk between the spine rails'},
        'gap-face-mid': {'centre': [0.0, -18.0, 42.9], 'normal': [0, 0, 1], 'u': [-1, 0, 0], 'width': 4.0, 'height': 3.0, 'note': 'gun-gap face of the mid hull (above the barrel)'},
        'tower-front': {'centre': [0.0, 13.0, -31.5], 'normal': [0, 0, 1], 'u': [1, 0, 0], 'width': 14.0, 'height': 1.6, 'note': 'bridge tower front between two glazed rows'},
        'tower-side-port': {'centre': [10.5, 13.3, -40.5], 'normal': [1, 0, 0], 'u': [0, 0, 1], 'width': 12.0, 'height': 1.6},
        'tower-side-stbd': {'centre': [-10.5, 13.3, -40.5], 'normal': [-1, 0, 0], 'u': [0, 0, -1], 'width': 12.0, 'height': 1.6},
        'stern-plate': {'centre': [0.0, -8.0, -85.0], 'normal': [0, 0, -1], 'u': [-1, 0, 0], 'width': 8.0, 'height': 1.0, 'note': 'stern plate above the centre dish'},
    },
}
