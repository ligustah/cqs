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
  command block z -59 .. -31      (v8, replaces the v7 bridge tower) armoured base deck 23 x 28 m to
                                  y -0.4, sloped two-deck casemate to y 5.6 (10 m above the engine
                                  deck); v9: bridge slit under an armour visor and a CIC slit, applique
                                  armour, sensor fairings, docking collars, radome drum, fire-control
                                  director and the sensor mast (trunk with arrays, gallery, lattice,
                                  radar, topmast, strobe and whip: the envelope top)
  railgun       spine with a finned cooling ridge and heavy clamp bands, capacitor banks, the exposed
                barrel in the gap (z 43.5 .. 54.3: rails, three heavy clamp rings, copper coil packs,
                walkways with doors and ladders), muzzle boss, armoured muzzle collar and nose band
  weapons (v9)  seats for 12 turret-M (A/B bow, X/Y aft, X'/Y' ventral aft, two on the engine-shoulder
                bastions, four on the broadside sponsons of the mid-hull upper flank), VLS coamings for
                28 kit missile pods (bow deck, deckhouse roof, engine deck)
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
SPINE_BANDS = [-1.2, 6.3, 13.6, 21.2, 29.9, 38.6, 47.3, 56.0]   # heavy clamp bands round the railgun spine

# ------------------------------------------------------------------------------------------
# v8 redesign: weapon stations (destroyer_spec.py repeats these numbers). Turrets are kit turret-M
# (x1.15 main batteries, x1.0 shoulders and sponsons; the carrier's turret-L x2.6 stay far bigger).
# 'B' / 'X' stations superfire over 'A' / 'Y' on barbettes, dorsal and ventral alike (turret-M x1.15: roof 4.44 m,
# trunnion 2.6 m). v9: every turret is seated 0.98 x scale INTO its ring or barbette (destroyer_assemble.py drops the
# kit's base discs, which the decimation left faceted): the barbettes grew by that 1.13 m (4.13 m), so B / X and the
# envelope stay where they were, and A / Y sit 1.13 m lower on their rings (more clearance under B / X's guns).
# ------------------------------------------------------------------------------------------
TUR_A, TUR_B = 79.2, 66.5                 # bow block: A (low ring), B (superfiring barbette), guns forward
TUR_X, TUR_Y = -66.3, -78.8               # engine block: X (superfiring barbette), Y (low ring), guns aft
BARBETTE_H = 4.13
SHOULDER_TUR = (21.2, -4.98, -57.5)       # engine-shoulder turrets (turret origin), guns forward, on the shoulder bastions
DECK_E, DECK_M, DECK_B = -4.3, -8.3, -6.4 # dorsal deck heights: engine block, mid hull, bow block
BELLY_E, BELLY_B = -35.8, -30.4           # ventral flats: engine block, bow block
# v9: shoulder bastions: flat-topped armoured plinths squaring off the engine shoulder under the shoulder
# turrets (v8's drums rose out of the sloped facet with a base flare half way up their outboard side).
# Plan: x0 .. x1 (inboard edge buried under the shoulder), l long, plan chamfer c; walls battered `batter`
# inward from the buried foot to the top, a top chamfer; a 1.2 m seat ring on the flat top.
BASTION = dict(x0=14.2, x1=27.2, l=13.4, c=2.4, foot=-16.5, top=-6.2, batter=0.5, tch=0.4, ring_r=4.6, ring_h=2.2)
# v9: broadside sponsons on the mid-hull upper flank (the bow ventral pair of v8 moved here): turret-M x1.0,
# guns forward; the aft pair (S2) superfires over the forward pair (S1). (name, turret z, deck top y, turret x)
SPONSONS = [('S1', 14.5, -11.4, 21.0), ('S2', -4.0, -8.0, 21.0)]   # S2's deck 0.3 m above the mid deck: its turret breaks the hull line
SPON = dict(xi=11.5, xo=26.2, ch=1.2, face=3.4, under=28.0, xf=16.9, l=13.0, lc=1.0, ring_r=4.6, ring_h=2.0)
# VLS bays (kit missilePod 3.188 x 5.588 m, 8 cells): armoured coamings flush with the pod tops.
# (name, deck centre, normal, up, cols, rows); columns at +-x, mirrored
VLS_PITCH = (3.3, 5.7)
M_DECK_N = (0.0, 22.5, 3.19)              # mid hull forward-taper deck normal (unnormalised)
DH_TOP = 2.2                              # deckhouse roof (v9: carries the ex-mid-deck VLS, clear of the spine rails)
VLS = [
    ('bow', (8.0, DECK_B, 70.8), (0, 1, 0), (0, 0, 1), 1, 4),
    ('dh', (4.45, DH_TOP, -22.0), (0, 1, 0), (0, 0, 1), 2, 2),
    ('aft', (10.4, DECK_E, -72.5), (0, 1, 0), (0, 0, 1), 2, 3),
]
VLS_H, VLS_WALL = 0.62, 0.5
# command block (replaces the v7 bridge tower): armoured base deck, sloped two-deck casemate with a
# bridge slit (upper deck) and a CIC slit (lower deck, front only), applique armour, radome drum,
# fire-control director and the sensor mast
CB_Z = -45.0
CB_BASE = dict(w=23.0, l=28.4, c=3.2, top=-0.4)   # front at z -30.8: 0.2 m into the deckhouse
CB_CASE = dict(w0=19.6, l0=25.0, c0=3.0, w1=15.0, l1=19.0, c1=2.2, y0=-0.4, y1=5.6)
CB_SLIT = dict(y=4.25, h=0.85, d=0.5, zcut=-47.0, pitch=1.5)      # bridge (v8: 0.5 m tall)
CB_CIC = dict(y=1.35, h=0.55, d=0.45, zcut=-37.6, pitch=1.8)      # combat information centre, lower deck
# v9 sensor mast on the director: a 45-degree tapered trunk with four phased arrays, a railed gallery, a
# lattice section, the surveillance radar on the upper platform, a topmast with a yard, the masthead strobe
# and the whip (the envelope top ~y 29.47, as v8's pole + whip)
FAIR = (5.75, -37.25, 2.4, 1.8)   # v9 roof sensor fairings: |x|, z, width, height (faces 45 deg outboard-forward)
MAST = dict(z=-51.5, dir_w=5.2, dir_h=3.0, trunk=(3.4, 2.3), trunk_top=15.0, lat=(1.9, 1.15), lat_top=20.5,
            radar_y=21.75, pole_top=24.0)


def barbette(bm, top, axis, h, r=5.0, bury=0.9, zone=None):
    """Turret barbette: a drum from `bury` below the deck to `h` above it (top = the turret seat on
    the axis), with a base skirt and a top lip."""
    top, ax = V(top), V(axis).normalized()
    p0 = top - ax * (h + bury)
    L = h + bury
    prof = [(r + 0.45, 0.0), (r + 0.45, bury + 0.35), (r, bury + 0.75), (r, L - 0.35), (r + 0.3, L - 0.3), (r + 0.3, L)]
    K.lathe(bm, p0, ax, prof, n=40, zone=Z['trim'] if zone is None else zone)


def seat_ring(bm, top, h, r, bury=0.3, zone=None):
    """Low turret seat ring on a flat deck (v9): a base flange, the drum and a top lip; `top` = the turret seat."""
    top = V(top)
    L = h + bury
    prof = [(r + 0.4, 0.0), (r + 0.4, bury + 0.18), (r, bury + 0.32), (r, L - 0.28), (r + 0.25, L - 0.24), (r + 0.25, L)]
    K.lathe(bm, top - V((0, L, 0)), (0, 1, 0), prof, n=32, zone=Z['trim'] if zone is None else zone)


def sponson(bm, s, zc, yd):
    """Broadside sponson on the mid-hull upper flank (v9), side s (+1 port): a flat deck at yd from the
    shoulder facet out to SPON.xo, a vertical outer face, and a corbelled underside back into the flank;
    the inboard part is buried in the hull (culled). Chamfered ends (a loft of the section inset at the ends)."""
    p = SPON
    ye = yd - p['face'] - (p['xo'] - p['xf']) * math.tan(math.radians(p['under']))
    sec = [(p['xi'], yd), (p['xo'] - p['ch'], yd), (p['xo'], yd - p['ch']), (p['xo'], yd - p['face']), (p['xf'], ye), (p['xi'], ye)]
    if s < 0:
        sec = [(-x, y) for x, y in reversed(sec)]
    ins = K.offset_poly(sec, -p['lc'])
    z0, z1 = zc - p['l'] / 2, zc + p['l'] / 2
    K.stack(bm, [(ins, z0), (sec, z0 + p['lc']), (sec, z1 - p['lc']), (ins, z1)], 'xy', zone=Z['paint'])
    return ye


def bastion(bm, s):
    """Engine-shoulder bastion (v9): a flat-topped armoured plinth (plan chamfer_rect, battered walls, top
    chamfer) whose foot is buried in the engine block; the shoulder turret's seat ring stands on its top."""
    b = BASTION
    x0, x1 = (b['x0'], b['x1']) if s > 0 else (-b['x1'], -b['x0'])
    zc = SHOULDER_TUR[2]
    plan = K.chamfer_rect((x0 + x1) / 2, zc, x1 - x0, b['l'], b['c'])
    K.stack(bm, [(plan, b['foot']), (K.offset_poly(plan, -b['batter']), b['top'] - b['tch']),
                 (K.offset_poly(plan, -b['batter'] - b['tch']), b['top'])], 'xz', zone=Z['paint'])


def tube(bm, outers, inners, zone):
    """Closed tube between matching lists of outer and inner rings (3D, same point counts)."""
    O = [[bm.verts.new(V(p)) for p in r] for r in outers]
    I = [[bm.verts.new(V(p)) for p in r] for r in inners]
    n = len(O[0])
    def quads(A, B):
        for k in range(len(A) - 1):
            for j in range(n):
                j2 = (j + 1) % n
                f = bm.faces.new([A[k][j], A[k][j2], A[k + 1][j2], A[k + 1][j]]); f.material_index = zone
    quads(O, O); quads(I, I)
    for a, b in ((O[0], I[0]), (O[-1], I[-1])):
        for j in range(n):
            j2 = (j + 1) % n
            f = bm.faces.new([a[j], a[j2], b[j2], b[j]]); f.material_index = zone


def vls_bay(bm, c, n, up, cols, rows):
    """Armoured coaming round a cols x rows grid of kit VLS pods, VLS_H tall (flush with the pod
    tops), walls VLS_WALL thick, chamfered; returns nothing (the pods are kit parts)."""
    r_, u_, n_ = K.basis(V(n).normalized(), V(up))
    R = Matrix((r_, u_, n_)).transposed()
    c = V(c)
    iw, ih = cols * VLS_PITCH[0] + 0.1, rows * VLS_PITCH[1] + 0.1
    w = VLS_WALL
    for sx in (-1, 1):   # long walls (along up), full length
        K.box(bm, c + r_ * sx * (iw / 2 + w / 2) + n_ * (VLS_H / 2 - 0.3), (w, ih + 2 * w, VLS_H + 0.6), R=R, zone=Z['trim'])
    for sy in (-1, 1):   # end walls between them
        K.box(bm, c + u_ * sy * (ih / 2 + w / 2) + n_ * (VLS_H / 2 - 0.3), (iw, w, VLS_H + 0.6), R=R, zone=Z['trim'])
    if cols > 1:         # centre divider between the columns
        K.box(bm, c + n_ * (VLS_H / 2 - 0.3), (0.1, ih, VLS_H + 0.55), R=R, zone=Z['trim'])


def nose_outline(z, d=0.0):
    """Bow nose section at z (84 .. 100.6): B_HALF scaled uniformly toward B_NOSE, offset d."""
    kn, ycn, zn = B_NOSE
    k = 1.0 + (kn - 1.0) * (z - B_Z1) / (zn - B_Z1)
    pts = K.mirror_half(scaled(B_HALF, k, ycn))
    return K.offset_poly(pts, d) if d else pts


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


def port(bm, c, n, up=(0, 1, 0), size=1.0, depth=0.2):
    """Recessed square port: 1.0 m glass at the back of a 0.2 m recess (glass zone)."""
    rect_cutter(bm, c, n, up, size, size, depth, ch=0.14, zone_back=Z['glass'])


def port_row(bm, a, b, pitch, n, up=(0, 1, 0), skip=(), size=1.0):
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
        for t, zr in ((0.72, [(-65.8, -81.0)]),):   # v9: aft of the shoulder bastion
            p = V((s * (15.0 + 12.67 * t), -4.3 - 10.7 * t, 0))
            for z0, z1 in zr:
                port_row(cut, (p.x, p.y, z0), (p.x, p.y, z1), 2.5, nsh, up=(-s * 0.764, 0.645, 0))
        nlo = V((s * 10.4, -12.77, 0)).normalized()
        for t in (0.28,):   # v9: one lower-chamfer row (the second, seen only from below, went to the triangle budget)
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
    # dorsal: X (superfiring) and Y turret barbettes, the aft VLS bays, deck hatch plates
    d = Volume('engine_dorsal', bevel=0.05)
    barbette(d.bm, (0, DECK_E + BARBETTE_H, TUR_X), (0, 1, 0), BARBETTE_H)
    K.cyl(d.bm, (0, DECK_E - 0.5, TUR_Y), (0, DECK_E + 0.35, TUR_Y), 5.1, n=40, zone=Z['trim'])
    # ventral: X' / Y' under the engine block (guns aft)
    barbette(d.bm, (0, BELLY_E - BARBETTE_H, TUR_X), (0, -1, 0), BARBETTE_H)
    K.cyl(d.bm, (0, BELLY_E + 0.5, TUR_Y), (0, BELLY_E - 0.35, TUR_Y), 5.1, n=40, zone=Z['trim'])
    K.solid(d.bm)
    vols.append(d)
    # v9: engine-shoulder bastions (flat armoured plinths) with the shoulder turrets' seat rings, a trim band
    # round the top and applique plates on the outboard wall
    bs = Volume('bastions', bevel=0.1)
    b = BASTION
    for s_ in (1, -1):
        bastion(bs.bm, s_)
    K.solid(bs.bm)
    vols.append(bs)
    br = Volume('bastion_rings', bevel=0.05)
    for s_ in (1, -1):
        x, y, z = SHOULDER_TUR
        seat_ring(br.bm, (s_ * x, b['top'] + b['ring_h'], z), b['ring_h'], b['ring_r'], bury=0.5)
        # armour band round the bastion just under the top chamfer, and two applique plates per outboard wall
        yp, hw = b['top'] - 3.3, b['top'] - b['tch'] - b['foot']
        xo = b['x1'] - b['batter'] * (yp - b['foot']) / hw
        nb = V((s_ * hw, b['batter'], 0)).normalized()
        for dz in (-2.0, 2.0):
            K.plate(br.bm, (s_ * (xo - 0.02), yp, z + dz), nb, (0, 1, 0), 3.6, 3.4, 0.16, ch=0.05, back=0.1, zone=Z['trim'])
        # one plate on each of the fore and aft walls, outboard where the wall stands tallest above the shoulder
        yq = b['top'] - 2.0
        for sz in (1, -1):
            zw = z + sz * (b['l'] / 2 - b['batter'] * (yq - b['foot']) / hw)
            K.plate(br.bm, (s_ * 23.4, yq, zw - sz * 0.02), V((0, b['batter'], sz * hw)).normalized(), (0, 1, 0), 2.4, 2.0, 0.14, ch=0.04, back=0.1, zone=Z['trim'])
    K.solid(br.bm)
    vols.append(br)
    v = Volume('vls_aft', bevel=0.05)
    for s_ in (1, -1):
        nm, c, n, up, cols, rows = VLS[2]
        vls_bay(v.bm, (s_ * c[0], c[1], c[2]), n, up, cols, rows)
    K.solid(v.bm)
    vols.append(v)
    # stern: bell bosses (corner) with ribs, the centre bell collar
    st = Volume('stern_bosses', bevel=0.05)
    for s in (1, -1):
        for y in (-13.71, -25.45):
            K.lathe(st.bm, (s * 13.45, y, E_STERN + 0.4), (0, 0, -1), [(5.35, 0.0), (5.35, 3.8), (4.95, 4.3), (4.95, 7.2)], n=28, zone=Z['metal'])
            for t in (1.0, 2.4):
                K.cyl(st.bm, (s * 13.45, y, E_STERN - t), (s * 13.45, y, E_STERN - t - 0.45), 5.6, n=28, zone=Z['trim'])
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
        port_row(cut, (p.x, p.y, -24.5), (p.x, p.y, 19.5), 2.5, nsh, up=(-s * 0.581, 0.814, 0), skip=[(-11.6, 3.6), (7.4, 22.0)])   # v9: sponsons
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
    # v9: broadside sponsons on the upper flank (replace v8's flank sponsons, whose turret lay on its side
    # facing outboard): flat decks catching the sun, turret-M x1.0 on seat rings, S2 superfiring over S1
    sp = Volume('sponsons', bevel=0.1)
    for s in (1, -1):
        for nm, zc, yd, xt in SPONSONS:
            sponson(sp.bm, s, zc, yd)
    K.solid(sp.bm)
    for f in sp.bm.faces:
        if f.normal.y > 0.95:
            f.material_index = Z['deck']
    vols.append(sp)
    sr = Volume('sponson_rings', bevel=0.05)
    p = SPON
    for s in (1, -1):
        for nm, zc, yd, xt in SPONSONS:
            seat_ring(sr.bm, (s * xt, yd + p['ring_h'], zc), p['ring_h'], p['ring_r'])
            # applique plates on the outer face, a deck hatch forward-inboard of the ring
            for dz in (-2.9, 2.9):
                K.plate(sr.bm, (s * p['xo'], yd - p['ch'] - 1.05, zc + dz), (s, 0, 0), (0, 1, 0), 5.0, 1.7, 0.14, ch=0.04, back=0.1, zone=Z['trim'])
            K.plate(sr.bm, (s * 16.7, yd, zc + 4.7), (0, 1, 0), (0, 0, 1), 1.3, 1.3, 0.1, ch=0.03, back=0.1, zone=Z['trim'])
    K.solid(sr.bm)
    vols.append(sr)
    # pre-tower deckhouse (blueprint z -31..-13, x +-9.5, top y 2.2) and the drum ahead of it
    dh = Volume('deckhouse', bevel=0.1)
    base = K.chamfer_rect(0, -22.0, 19.0, 18.0, 2.0)
    # v9: a broader roof (18.2 x 17.2 m, was 16.6 x 16) for the VLS bays moved up from the mid-hull deck
    K.stack(dh.bm, [(base, -8.6), (base, DH_TOP - 0.7), (K.chamfer_rect(0, -22.0, 18.2, 17.2, 1.8), DH_TOP)], 'xz', zone=Z['paint'])
    K.solid(dh.bm)
    for f in dh.bm.faces:
        if f.normal.y > 0.95:
            f.material_index = Z['deck']
    for s in (1, -1):
        for y in (-5.2, -2.2):
            port_row(dh.cutters, (s * 9.5, y, -28.8), (s * 9.5, y, -15.2), 2.3, (s, 0, 0))
    for x in np.arange(-6.0, 6.01, 2.3):
        port(dh.cutters, (x, -2.2, -13.0), (0, 0, 1))
    K.solid(dh.cutters)
    vols.append(dh)
    v = Volume('vls_dh', bevel=0.05)
    for s_ in (1, -1):
        nm, c, n, up, cols, rows = VLS[1]
        vls_bay(v.bm, (s_ * c[0], c[1], c[2]), n, up, cols, rows)
    K.solid(v.bm)
    vols.append(v)
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
    # v8: heavy armoured muzzle collar in bare steel (1.3 m proud of the nose facets, 6 m deep, chamfered front)
    # replacing the flush lip, and a reinforcing band further aft on the nose taper
    lip = Volume('muzzle_lip', bevel=0.08)
    kn, ycn, zn = B_NOSE
    w, h, ch = SHROUD
    yt, yb, xh = BORE_Y + h / 2, BORE_Y - h / 2, w / 2
    inner = [(xh - ch, yt), (xh, yt - ch), (xh, yb + ch), (xh - ch, yb), (-xh + ch, yb), (-xh, yb + ch), (-xh, yt - ch), (-xh + ch, yt)]
    def nose8(z, d):
        o = nose_outline(z, d)       # mirror_half order: 10 points incl. the two centre-line points
        return [p for p in o if abs(p[0]) > 1e-6]
    def fit(pts, ref):
        # reorder an 8-point ring so point j is the one nearest ref[j] (same winding as the shroud)
        return [min(pts, key=lambda p: (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2) for q in ref]
    zs = [95.3, 96.1, zn - 0.05, zn + 0.05, 100.65, BOW_Z]
    od = [-0.05, 1.3, 1.3, 1.3, 1.3, 0.35]
    outers = [[(x, y, z) for x, y in fit(nose8(z, d), inner)] for z, d in zip(zs, od)]
    # the inner wall steps out to the shroud opening only in front of the bow's nose face (the step is
    # buried between the two solids); behind it the collar's inner wall sits 0.9 m inside the bow
    inners = [[(x, y, z) for x, y in (K.offset_poly(inner, 0.9) if z < zn else inner)] for z in zs]
    tube(lip.bm, outers, inners, Z['metal'])
    b0, b1 = 89.2, 91.4
    tube(lip.bm, [[(x, y, z) for x, y in fit(nose8(z, d), inner)] for z, d in ((b0, -0.05), (b0 + 0.5, 0.7), (b1 - 0.5, 0.7), (b1, -0.05))],
         [[(x, y, z) for x, y in fit(nose8(z, -1.2), inner)] for z in (b0, b0 + 0.4, b1 - 0.4, b1)], Z['trim'])
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
    # dorsal turret ring and barbette (v9: the ventral A' / B' pair moved up to the broadside sponsons)
    d = Volume('bow_dorsal', bevel=0.05)
    K.cyl(d.bm, (0, DECK_B - 0.5, TUR_A), (0, DECK_B + 0.35, TUR_A), 5.1, n=40, zone=Z['trim'])
    barbette(d.bm, (0, DECK_B + BARBETTE_H, TUR_B), (0, 1, 0), BARBETTE_H)
    K.solid(d.bm)
    vols.append(d)
    # v9: ventral sensor keel under the bow block where the ventral pair stood: a low fairing with two
    # louvred sensor windows
    kb = Volume('keel_bow', bevel=0.06)
    K.prism(kb.bm, [(62.4, BELLY_B + 0.3), (63.8, BELLY_B - 1.7), (80.2, BELLY_B - 1.7), (81.6, BELLY_B + 0.3)], 'zy', -4.6, 4.6, zone=Z['belly'])
    K.solid(kb.bm)
    for zc in (67.5, 76.5):
        rect_cutter(kb.cutters, (0, BELLY_B - 1.7, zc), (0, -1, 0), (0, 0, 1), 6.0, 5.6, 0.3, ch=0.3, zone_back=Z['dark'])
    K.solid(kb.cutters)
    kb.adds.append(('slats', lambda bm2: [K.box(bm2, (x, BELLY_B - 1.55, zc), (0.1, 0.26, 5.2), zone=Z['fin'])
                                           for zc in (67.5, 76.5) for x in np.arange(-2.5, 2.51, 0.5)]))
    vols.append(kb)
    v = Volume('vls_bow', bevel=0.05)
    for s in (1, -1):
        nm, c, n, up, cols, rows = VLS[0]
        vls_bay(v.bm, (s * c[0], c[1], c[2]), n, up, cols, rows)
    K.solid(v.bm)
    vols.append(v)
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
        K.cyl(rl.bm, (s * 10.35, -5.95, 20.5), (s * 10.35, -5.95, 56.0), 0.45, n=12, zone=Z['metal'])
        for z in (23.5, 30.0, 36.5, 42.0):
            yb = -8.3 - (z - M_Z1) / (M_FRONT - M_Z1) * 3.4
            K.box(rl.bm, (s * 10.35, (yb - 5.95) / 2 - 0.25, z), (0.9, -5.95 - yb + 0.5, 1.0), zone=Z['trim'])
            K.box(rl.bm, (s * 10.35, -5.95, z), (1.3, 1.1, 1.4), zone=Z['trim'])
        K.box(rl.bm, (s * 10.35, -6.2, 55.6), (0.9, 0.9, 0.9), zone=Z['trim'])
        # spine rail clamps
        for z in [(a + b) / 2 for a, b in zip(SPINE_BANDS[:-1], SPINE_BANDS[1:])]:
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
    K.solid(cb.bm)
    vols.append(cb)
    # v9: the mid-deck VLS bays (hidden under the spine rails from the hero view) moved to the deckhouse
    # roof; the forward deck keeps flush magazine hatches between the spine and the outer rails
    vm = Volume('mid_hatches', bevel=0.03)
    nn = V(M_DECK_N).normalized(); uu = V((0, -3.19, 22.5)).normalized()
    for s in (1, -1):
        for z in (25.6, 34.4):
            c = V((s * 7.4, -9.718, 31.0)) + uu * ((z - 31.0) / uu.z)
            K.plate(vm.bm, c, nn, uu, 3.0, 6.4, 0.1, ch=0.03, back=0.12, zone=Z['trim'])
    K.solid(vm.bm)
    vols.append(vm)
    # v8: cooling ridge along the spine crown (the railgun's heat path, a dark finned core between the
    # spine rails) and heavy clamp bands round spine and ridge every ~8.7 m
    cr = Volume('spine_ridge', bevel=0.04)
    BANDS_Z = SPINE_BANDS
    for z0, z1 in zip(BANDS_Z[:-1], BANDS_Z[1:]):
        K.stack(cr.bm, [(K.chamfer_rect(0, (z0 + z1) / 2, 1.8, z1 - z0 - 1.0, 0.2), -5.8), (K.chamfer_rect(0, (z0 + z1) / 2, 1.8, z1 - z0 - 1.0, 0.2), -4.9)], 'xz', zone=Z['dark'])
    K.solid(cr.bm)
    fins = [((0, -4.82, z), None) for z0, z1 in zip(BANDS_Z[:-1], BANDS_Z[1:]) for z in np.arange(z0 + 1.0, z1 - 0.99, 0.45)]
    cr.adds.append(('fins', lambda bm2, fins=fins: [K.box(bm2, c, (3.4, 1.46, 0.1), zone=Z['fin']) for c, _ in fins]))
    vols.append(cr)
    sb = Volume('spine_bands', bevel=0.06)
    for zc in BANDS_Z:
        K.prism(sb.bm, K.chamfer_rect(0, -8.1, 10.4, 8.6, 1.6), 'xy', zc - 0.6, zc + 0.6, zone=Z['trim'])
    K.solid(sb.bm)
    vols.append(sb)
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
    # v8: three heavy clamp rings (1.5 m thick, 13.6 m tall) with bolted lugs top and bottom
    for zc in np.linspace(GAP[0] + 1.6, GAP[1] - 1.6, 3):
        # zones metal / dark: the gap keeps a muted livery (liveryKeep gain 0.3), so light trim paint glared white
        ring_solid(cl.bm, K.chamfer_rect(0, BORE_Y, 11.2, 13.6, 2.4), K.chamfer_rect(0, BORE_Y, 6.8, 10.2, 1.6), 'xy', zc - 0.75, zc + 0.75, zone=Z['metal'])
        ring_solid(cl.bm, K.chamfer_rect(0, BORE_Y, 11.5, 13.9, 2.5), K.chamfer_rect(0, BORE_Y, 10.9, 13.3, 2.3), 'xy', zc - 0.25, zc + 0.25, zone=Z['dark'])
        for sy in (1, -1):
            K.box(cl.bm, (0, BORE_Y + sy * 7.15, zc), (4.2, 0.9, 2.3), zone=Z['dark'])
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
                for zc in np.arange(c0 + 0.35, c0 + L / 3 - 0.35, 0.48):   # v9: 0.48 m pitch (was 0.36; triangle budget)
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
# command block (v8: replaces the bridge tower)
# ------------------------------------------------------------------------------------------
def case_outline(y, d=0.0):
    """Casemate plan outline at height y (sloped armour: linear between the bottom and top outlines)."""
    c = CB_CASE
    t = (y - c['y0']) / (c['y1'] - c['y0'])
    o = K.chamfer_rect(0, CB_Z, c['w0'] + (c['w1'] - c['w0']) * t, c['l0'] + (c['l1'] - c['l0']) * t, c['c0'] + (c['c1'] - c['c0']) * t)
    return K.offset_poly(o, d) if d else o


def u_band(inner, outer, zcut):
    """Plan polygon of the forward part (z > zcut) of the band between two chamfer_rect outlines."""
    xi, xo = max(p[0] for p in inner), max(p[0] for p in outer)
    # chamfer_rect order: (x1, y0+c), (x1, y1-c), (x1-c, y1), (x0+c, y1), (x0, y1-c), ... -> forward run is [1..4]
    fi = [inner[1], inner[2], inner[3], inner[4]]
    fo = [outer[1], outer[2], outer[3], outer[4]]
    return [(xi, zcut)] + fi + [(-xi, zcut), (-xo, zcut)] + fo[::-1] + [(xo, zcut)]


def slit(cm, sl, zone_back=None):
    """Cut an armoured glazing slit round the casemate front (z > sl.zcut) at height sl.y (sl.h tall, sl.d deep,
    glass on the back wall) into cm.cutters; returns the armoured mullion frames (every sl.pitch)."""
    band = u_band(case_outline(sl['y'], -sl['d']), case_outline(sl['y'], 3.0), sl['zcut'])
    grid, _caps = K.prism(cm.cutters, band, 'xz', sl['y'] - sl['h'] / 2, sl['y'] + sl['h'] / 2, zone=Z['recess'])
    for j in range(5):       # the band's inner run (edges 0..4) is the slit's back wall: glass
        if grid[0][j] is not None:
            grid[0][j].material_index = Z['glass'] if zone_back is None else zone_back
    o = case_outline(sl['y'], -sl['d'] + 0.2)
    mm = []
    for i in range(1, 4):
        a_, b_ = V(o[i]), V(o[i + 1])
        L = (b_ - a_).length; d = (b_ - a_).normalized()
        k = max(1, int(L / sl['pitch']))
        for j in range(k + (1 if i == 3 else 0)):
            p = a_ + d * (L * j / k)
            if p.y < sl['zcut'] + 0.3:
                continue
            Rm = Matrix(((d.x, 0, d.y), (0, 1, 0), (d.y, 0, -d.x))).transposed()
            mm.append((V((p.x, sl['y'], p.y)), Rm))
    for s in (1, -1):   # the side runs forward of zcut
        a_ = V(o[0] if s > 0 else o[5]); b_ = V(o[1] if s > 0 else o[4])
        for zz in np.arange(sl['zcut'] + 1.0, max(a_.y, b_.y) - 0.3, sl['pitch']):
            Rm = Matrix(((0, 0, 1), (0, 1, 0), (1, 0, 0))).transposed()
            mm.append((V((a_.x, sl['y'], zz)), Rm))
    return [(c, R, sl['h']) for c, R in mm]


def rot_outline(pts, cx, cz, ang):
    ca, sa = math.cos(ang), math.sin(ang)
    return [(cx + x * ca - z * sa, cz + x * sa + z * ca) for x, z in pts]


def octa(bm, c, n, up, w, h, ch, d0, d1, lip=0.0, zone=0):
    """Octagonal plate (chamfer_rect w x h, corner cut ch) on a face: from d0 to d1 along n about c, front edge
    chamfered by `lip`."""
    r, u, nn = K.basis(n, up)
    c = V(c)
    at = lambda pts, d: [c + r * a + u * b + nn * d for a, b in pts]
    o = K.chamfer_rect(0, 0, w, h, ch)
    rings = [at(o, d0)] + ([at(o, d1 - lip), at(K.offset_poly(o, -lip), d1)] if lip > 0 else [at(o, d1)])
    return K.loft(bm, rings, zone=zone)


# v9: phased-array faces (were fal kit sensorArray meshes: crumpled facets at close range and 540 triangles
# each): an octagonal armoured backing (trim), a dark radiating face and a grid of raised tile modules
ARRAY_T = (0.2, 0.05, 0.035)   # backing proud of the host face, face proud of the backing, tiles proud of the face


def phased_array(vol, tiles, c, n, up, w, h, pitch=0.46):
    """Octagonal phased-array face w x h standing on a host face at c (outward normal n): backing and face into
    vol.bm (closed, bevelled); the tile grid (rows of tiles clipped to the octagon, columns aligned) is appended
    to `tiles` as K.plate arguments (the caller adds them unbevelled: 12 triangles a tile)."""
    tb, tf, tt = ARRAY_T
    ch = 0.24 * min(w, h)
    octa(vol.bm, c, n, up, w, h, ch, -0.15, tb, lip=0.05, zone=Z['trim'])
    fw, fh, fch = w - 0.28, h - 0.28, ch - 0.14 * 0.414
    octa(vol.bm, c, n, up, fw, fh, fch, tb - 0.1, tb + tf, lip=0.02, zone=Z['dark'])
    r, u, nn = K.basis(V(n), V(up))
    gw, gh, gch = fw - 0.16, fh - 0.16, fch - 0.08 * 0.414
    rows = max(2, int(round(gh / pitch)))
    th = gh / rows
    cols_full = max(2, int(round(gw / pitch)))
    tw = gw / cols_full
    gap = 0.05
    for i in range(rows):
        yc = -gh / 2 + th * (i + 0.5)
        worst = abs(yc) + th / 2 - gap / 2
        hw = gw / 2 - max(0.0, worst - (gh / 2 - gch))
        cols = cols_full
        while cols > 1 and cols * tw > 2 * hw + 1e-6:
            cols -= 2
        for j in range(cols):
            xc = (j - (cols - 1) / 2) * tw
            tiles.append((V(c) + r * xc + u * yc + nn * (tb + tf), V(n), V(up), tw - gap, th - gap, tt))


def case_frame(y, side):
    """Point on the casemate's sloped face at height y (centre of the face run) and its outward normal / up-slope
    direction. side: 'port', 'front', 'aft'."""
    c = CB_CASE
    kw = (c['w1'] - c['w0']) / 2 / (c['y1'] - c['y0'])    # x change per metre of height (negative)
    kl = (c['l1'] - c['l0']) / 2 / (c['y1'] - c['y0'])
    t = (y - c['y0'])
    if side == 'port':
        x = c['w0'] / 2 + kw * t
        n = V((1.0, -kw, 0)).normalized(); up = V((kw, 1.0, 0)).normalized()
        return V((x, y, CB_Z)), n, up
    zf = c['l0'] / 2 + kl * t
    sg = 1 if side == 'front' else -1
    n = V((0, -kl, sg)).normalized(); up = V((0, 1.0, sg * kl)).normalized()
    return V((0, y, CB_Z + sg * zf)), n, up


def command_block():
    vols = []
    b = CB_BASE
    base = K.chamfer_rect(0, CB_Z, b['w'], b['l'], b['c'])
    v = Volume('cmd_base', bevel=0.1)
    K.stack(v.bm, [(base, -8.0), (base, b['top'] - 0.55), (K.offset_poly(base, -0.5), b['top'])], 'xz', zone=Z['paint'])
    K.solid(v.bm)
    # crew deck ports along the base sides (1 m ports, deck -4.3); v9: the docking collar replaces one
    for s in (1, -1):
        port_row(v.cutters, (s * b['w'] / 2, -2.5, CB_Z - 10.5), (s * b['w'] / 2, -2.5, CB_Z + 6.0), 2.5, (s, 0, 0), skip=[(-48.4, -46.1)])
    K.solid(v.cutters)
    vols.append(v)
    # casemate: sloped armour faces, two decks; v9: a taller bridge slit on the upper deck (0.85 m) under an armour
    # visor, and a CIC slit on the lower deck (front only)
    c = CB_CASE
    cm = Volume('cmd_case', bevel=0.1)
    K.stack(cm.bm, [(case_outline(c['y0'] - 0.3), c['y0'] - 0.3), (case_outline(c['y1']), c['y1'])], 'xz', zone=Z['paint'])
    K.solid(cm.bm)
    mm = slit(cm, CB_SLIT) + slit(cm, CB_CIC)
    K.solid(cm.cutters)
    cm.adds.append(('mullions', lambda bm2, mm=mm: [K.box(bm2, cc, (0.3, h + 0.02, 0.7), R=R, zone=Z['trim']) for cc, R, h in mm]))
    vols.append(cm)
    # visor: an armour brow 0.55 m proud over the bridge slit (its shadow line makes the slit read)
    vz = Volume('cmd_visor', bevel=0.03)
    sl = CB_SLIT
    yv = sl['y'] + sl['h'] / 2 + 0.03
    K.prism(vz.bm, u_band(case_outline(yv + 0.12, -0.15), case_outline(yv + 0.12, 0.55), sl['zcut'] - 0.6), 'xz', yv, yv + 0.24, zone=Z['trim'])
    K.solid(vz.bm)
    vols.append(vz)
    # applique armour: bolted plates on the sloped faces (sides aft of the slits, front between the slits, aft face)
    ap = Volume('cmd_applique', bevel=0.04)
    for s in (1, -1):
        cc, n, up = case_frame(1.65, 'port')
        for zc in (-50.8, -45.6, -40.4):
            K.plate(ap.bm, V((s * cc.x, cc.y, zc)), V((s * n.x, n.y, 0)), up if s > 0 else V((-up.x, up.y, 0)), 4.6, 3.5, 0.16, ch=0.05, back=0.12, zone=Z['trim'])
    cc, n, up = case_frame(2.72, 'front')
    for x in (-2.8, 2.8):
        K.plate(ap.bm, cc + V((x, 0, 0)), n, up, 5.2, 1.95, 0.16, ch=0.05, back=0.12, zone=Z['trim'])
    cc, n, up = case_frame(1.9, 'aft')
    for x in (-2.9, 2.9):
        K.plate(ap.bm, cc + V((x, 0, 0)), n, up, 5.0, 3.6, 0.16, ch=0.05, back=0.12, zone=Z['trim'])
    K.solid(ap.bm)
    vols.append(ap)
    # docking collars on the base sides (a 2.2 m hatch in a flanged ring; crew and boat transfer at the deck)
    dk = Volume('cmd_collars', bevel=0.03)
    for s in (1, -1):
        K.lathe(dk.bm, (s * (b['w'] / 2 - 0.2), -2.55, -47.25), (s, 0, 0),
                [(1.42, 0.0), (1.42, 0.72), (1.66, 0.72), (1.66, 0.98), (1.14, 0.98), (1.14, 0.8), (0.001, 0.8)], n=18, zone=Z['trim'])
    K.solid(dk.bm)
    for f in dk.bm.faces:
        if abs(f.normal.x) > 0.95 and (f.calc_center_median() - V((f.calc_center_median().x, -2.55, -47.25))).length < 1.1:
            f.material_index = Z['dark']
    vols.append(dk)
    # roof: plates and hatches, radome drum (forward), sensor fairings on the forward corners, antenna bases on the
    # aft corners, the fire-control director (aft) and the sensor mast on it
    rf = Volume('cmd_roof', bevel=0.05)
    yt = c['y1']
    K.plate(rf.bm, (0.0, yt, CB_Z + 2.0), (0, 1, 0), (0, 0, 1), 6.0, 3.6, 0.14, ch=0.05, back=0.2, zone=Z['deck'])
    for s in (1, -1):
        K.plate(rf.bm, (s * 3.8, yt, -46.0), (0, 1, 0), (0, 0, 1), 1.2, 1.2, 0.1, ch=0.03, back=0.1, zone=Z['trim'])
    K.cyl(rf.bm, (0, yt - 0.3, CB_Z + 5.5), (0, yt + 1.2, CB_Z + 5.5), 2.5, n=32, zone=Z['paint'])
    for s in (1, -1):
        d = V((s * 0.7071, 0, 0.7071))
        fc = V((s * FAIR[0], yt + FAIR[3] / 2 - 0.2, FAIR[1]))
        R = Matrix((d.cross(V((0, 1, 0))) * -1, V((0, 1, 0)), d)).transposed()   # columns: right, up, out
        K.box(rf.bm, fc, (FAIR[2], FAIR[3] + 0.4, 1.3), R=R, zone=Z['paint'])
        K.cyl(rf.bm, (s * 5.6, yt - 0.2, -53.6), (s * 5.6, yt + 0.35, -53.6), 0.38, n=12, zone=Z['trim'])   # clear of the director arrays' footprint
    m = MAST
    dw, dh = m['dir_w'], m['dir_h']
    K.stack(rf.bm, [(K.chamfer_rect(0, m['z'], dw, dw, 0.6), yt - 0.3), (K.chamfer_rect(0, m['z'], dw, dw, 0.6), yt + dh - 0.3),
                    (K.chamfer_rect(0, m['z'], dw - 0.6, dw - 0.6, 0.4), yt + dh)], 'xz', zone=Z['paint'])
    # mast trunk: a square turned 45 degrees (its four array faces look fore/aft-quarter), tapered
    t0, t1 = m['trunk']
    K.stack(rf.bm, [(rot_outline(K.chamfer_rect(0, 0, t0, t0, 0.4), 0, m['z'], math.pi / 4), yt + dh - 0.2),
                    (rot_outline(K.chamfer_rect(0, 0, t1, t1, 0.3), 0, m['z'], math.pi / 4), m['trunk_top'])], 'xz', zone=Z['paint'])
    # gallery at the trunk top, the upper (radar) platform on the lattice, pedestal, pole and cap
    K.plate(rf.bm, (0, m['trunk_top'], m['z']), (0, 1, 0), (0, 0, 1), 4.4, 4.4, 0.22, ch=0.05, back=0.05, zone=Z['metal'])
    K.plate(rf.bm, (0, m['lat_top'], m['z']), (0, 1, 0), (0, 0, 1), 2.8, 2.8, 0.18, ch=0.04, back=0.05, zone=Z['metal'])
    K.cyl(rf.bm, (0, m['lat_top'] + 0.1, m['z']), (0, m['radar_y'] - 0.35, m['z']), 0.34, n=12, zone=Z['metal'])
    K.cyl(rf.bm, (0, m['radar_y'] + 0.3, m['z']), (0, m['pole_top'], m['z']), 0.14, 0.1, n=10, zone=Z['metal'])
    K.cyl(rf.bm, (0, m['pole_top'] - 0.06, m['z']), (0, m['pole_top'] + 0.05, m['z']), 0.46, n=12, zone=Z['metal'])
    # surveillance radar: a slotted planar antenna tilted back 12 degrees on a backing frame
    tl = math.radians(-12)   # face normal forward and up
    Rr = Matrix(((1, 0, 0), (0, math.cos(tl), -math.sin(tl)), (0, math.sin(tl), math.cos(tl))))
    K.box(rf.bm, (0, m['radar_y'], m['z'] + 0.12), (4.8, 1.0, 0.22), R=Rr, zone=Z['dark'])
    K.box(rf.bm, (0, m['radar_y'] - 0.05, m['z'] - 0.12), (4.4, 0.5, 0.3), R=Rr, zone=Z['metal'])
    K.solid(rf.bm)
    # thin unbevelled members: gallery railing, lattice legs and braces, yard and dipoles
    fins = []
    gy, g = m['trunk_top'] + 0.11, 2.1
    for s in (1, -1):
        fins.append(((0, gy + 1.0, m['z'] + s * g), (2 * g, 0.06, 0.06)))
        fins.append(((s * g, gy + 1.0, m['z']), (0.06, 0.06, 2 * g)))
        fins.append(((0, gy + 0.5, m['z'] + s * g), (2 * g, 0.05, 0.05)))
        fins.append(((s * g, gy + 0.5, m['z']), (0.05, 0.05, 2 * g)))
        for k in (-1, 0, 1):
            fins.append(((k * g, gy + 0.5, m['z'] + s * g), (0.06, 1.0, 0.06)))
            if k:
                fins.append(((s * g, gy + 0.5, m['z'] + k * g * 0.5), (0.06, 1.0, 0.06)))
    fins.append(((0, m['pole_top'] - 0.9, m['z']), (3.0, 0.09, 0.12)))                   # yard
    for s in (1, -1):
        fins.append(((s * 1.4, m['pole_top'] - 1.3, m['z']), (0.04, 0.8, 0.04)))        # dipoles
    lat = []
    a0, a1 = m['lat']
    y0, y1 = m['trunk_top'] + 0.1, m['lat_top']
    ym = (y0 + y1) / 2
    hw = lambda y: (a0 + (a1 - a0) * (y - y0) / (y1 - y0)) / 2
    for sx in (1, -1):
        for sz in (1, -1):
            lat.append(((sx * hw(y0), y0, m['z'] + sz * hw(y0)), (sx * hw(y1), y1, m['z'] + sz * hw(y1)), 0.08))
    for ya, yb in ((y0, ym), (ym, y1)):
        for s in (1, -1):   # X braces on the four faces
            lat.append(((s * hw(ya), ya, m['z'] - hw(ya)), (s * hw(yb), yb, m['z'] + hw(yb)), 0.045))
            lat.append(((s * hw(ya), ya, m['z'] + hw(ya)), (s * hw(yb), yb, m['z'] - hw(yb)), 0.045))
            lat.append(((-hw(ya), ya, m['z'] + s * hw(ya)), (hw(yb), yb, m['z'] + s * hw(yb)), 0.045))
            lat.append(((hw(ya), ya, m['z'] + s * hw(ya)), (-hw(yb), yb, m['z'] + s * hw(yb)), 0.045))
    for s in (1, -1):       # the ring half way up
        lat.append(((-hw(ym), ym, m['z'] + s * hw(ym)), (hw(ym), ym, m['z'] + s * hw(ym)), 0.05))
        lat.append(((s * hw(ym), ym, m['z'] - hw(ym)), (s * hw(ym), ym, m['z'] + hw(ym)), 0.05))
    def members(bm2, fins=fins, lat=lat):
        for cc, sz in fins:
            K.box(bm2, cc, sz, zone=Z['metal'])
        for pa, pb, r in lat:
            K.cyl(bm2, pa, pb, r, n=6, zone=Z['metal'])
    rf.adds.append(('fins', members))
    vols.append(rf)
    # phased-array faces (v9, parametric; were fal kit sensorArray meshes): four fire-control arrays on the
    # director faces, four surveillance arrays on the mast trunk faces, one on each roof fairing
    ar = Volume('cmd_arrays', bevel=0.02)
    tiles = []
    fy = yt + dh / 2 - 0.15
    for n_ in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1)):
        phased_array(ar, tiles, (n_[0] * dw / 2, fy, m['z'] + n_[2] * dw / 2), n_, (0, 1, 0), 2.8, 2.26, pitch=0.36)
    tb0, ty = yt + dh - 0.2, 11.7
    ta = math.atan2((t0 - t1) / 2, m['trunk_top'] - tb0)
    ap = t0 / 2 - (t0 - t1) / 2 * (ty - tb0) / (m['trunk_top'] - tb0)
    for sx in (1, -1):
        for sz in (1, -1):
            nrm = (sx * 0.7071 * math.cos(ta), math.sin(ta), sz * 0.7071 * math.cos(ta))
            phased_array(ar, tiles, (sx * ap * 0.7071, ty, m['z'] + sz * ap * 0.7071), nrm, (0, 1, 0), 1.8, 1.9, pitch=0.36)
    for s in (1, -1):
        d = V((s * 0.7071, 0, 0.7071))
        phased_array(ar, tiles, V((s * FAIR[0], yt + 0.9, FAIR[1])) + d * 0.65, d, (0, 1, 0), 2.0, 1.5, pitch=0.34)
    K.solid(ar.bm)
    ar.adds.append(('grille_tiles', lambda bm2, tiles=tiles: [K.plate(bm2, p, n_, up_, w_, h_, t_, back=0.01, zone=Z['metal'])
                                                              for p, n_, up_, w_, h_, t_ in tiles]))
    vols.append(ar)
    return vols


# ------------------------------------------------------------------------------------------
# build
# ------------------------------------------------------------------------------------------
# volumes unwrapped at reduced texel density: small repeated parts in one flat zone colour
# (not the copper coil turns: at a reduced density their 0.2 m faces fall between texel centres, miss the
# bake and show the empty-texel fill)
DETAIL = {'walkways', 'spine_bands'}   # v8: 'clamps' now mixes trim rings and metal bands -> full density


def build(args):
    t0 = time.time()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    K.zone_materials()
    vols = [engine_block(), *engine_details(), mid_hull(), *mid_details(), bow_block(), *bow_details(), *railgun(), *command_block()]
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
            ob2['bevel'] = 0.0 if nm in ('louvres', 'mullions', 'slats', 'fins') or nm.startswith('grille') else 0.03   # thin repeated fins: flat, 12 tris each
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
// rails, finned cooling ridge, heavy clamp bands and the capacitor banks.
// v8 redesign (user feedback: 'massive tower, relatively little weaponisation'): the bridge tower is gone;
// a low armoured command block sits on the spine, crew live inside the armoured hull (rows of 1 m ports on
// 3 m decks).
// v9 polish: the command block carries a bridge slit under an armour visor and a CIC slit, applique armour,
// sensor fairings, docking collars and a designed sensor mast (a tapered trunk with four phased arrays, a
// railed gallery, a lattice section, the surveillance radar, a topmast with the masthead strobe and whip:
// the envelope top). Weapons: 12 kit turret-M with full-resolution guns (tools/blender/hulls/
// destroyer_assemble.py): bow A/B and aft X/Y with superfiring barbettes, X'/Y' ventral aft, two on
// flat-topped shoulder bastions and four in the broadside (two sponsons a side on the upper flank, the aft
// one superfiring), 28 flush VLS blocks (224 cells) in armoured coamings on open deck (bow, deckhouse roof,
// engine deck), point-defence clusters at bow, shoulders, stern, sponsons and on the command block.
// The aft superfiring X turret cannot fire forward over the command block: its arc is aft and abeam, as a
// sea-going ship's after turrets (A/B cover the forward arc, the shoulder and broadside guns the beam).
// Engines: kit bells (bell-L x1.237 corner bells: CORNER_BELL, bell-XL x1.106 centre dish) with the kit's
// documented engine entry (depth to the throat plate, throat, inner wall) times that scale.
// Lights: at the lenses of the kit nav-light housings.""",
    'meta': {
        'name': 'Bastion-class destroyer', 'designation': 'DD-12', 'crew': 'about 2,000',
        'blurb': 'Heavy line destroyer built around a massive spinal railgun: an armoured bow block with the heavy-collared muzzle, the barrel exposed in the gun gap between the bow block and the mid hull, a finned cooling spine with capacitor banks and clamp bands along the back, a low armoured command block with bridge and combat-centre slits under a lattice sensor mast, twelve twin turrets (superfiring batteries fore and aft, a ventral pair, shoulder bastions and a four-gun broadside on flank sponsons), 224 vertical launch cells, point-defence clusters, and five fusion bells in the stern.',
    },
    'asset': {
        'glb': './assets/ships/destroyer.glb', 'generator': 'tools/blender/hulls/destroyer.py (remodel of the tripo3d/h3.1/multiview-to-3d hull) + tools/blender/assemble.py',
        'concept': './assets/concepts/destroyer.webp', 'beauty': './assets/concepts/destroyer-beauty.webp',
        'rotate': [0, 0, 0], 'hullNodes': ['hull'],
        # remodel paint is lighter than the generated textures: gain 0.05 matches the fleet grey; kit and
        # hull glass get a dim warm interior light (livery.js glassGlow, opt-in)
        # v9: markings keep part of their hue (mark 0.18, markSat 0.3; the fleet 'dark' default is 0.11 / 0.05):
        # the hazard frames, cobalt bands and walk lines read as muted naval paint instead of vanishing
        'livery': {'gain': 0.05, 'glassGlow': [0.06, 0.055, 0.046], 'glassLit': 0.35, 'mark': 0.18, 'markSat': 0.3},
        # runtime PATINA micro detail, turned down: the hull carries its own plating seams and panel breaks
        'detail': {'set': 'hull', 'tile': 6, 'normalStrength': 0.6, 'roughAmount': 0.5, 'cavity': 0.2},
    },
    # in navlight placement order: sidelight port, starboard, director strobe, keel strobe, stern
    'lights': [
        {'color': 'red', 'note': 'steady sidelights on the flat flank of the engine section (the beam extremity): red port, green starboard'},
        {'color': 'green'},
        {'color': 'white', 'blink': {'period': 1.3, 'duty': 0.1}, 'note': 'anti-collision strobes, alternating: the masthead (topmast cap) and the keel fin'},
        {'color': 'white', 'blink': {'period': 1.3, 'duty': 0.1, 'phase': 0.5}},
        {'color': 'white', 'note': 'steady stern light on the stern plate above the centre dish'},
    ],
    'surfaces': {
        'engine-flank-port': {'centre': [27.67, -20.2, -47.0], 'normal': [1, 0, 0], 'u': [0, 0, 1], 'width': 18.0, 'height': 9.0, 'note': 'flat flank of the engine section ahead of the mid band (three port rows)'},
        'engine-flank-stbd': {'centre': [-27.67, -20.2, -47.0], 'normal': [-1, 0, 0], 'u': [0, 0, -1], 'width': 18.0, 'height': 9.0},
        'engine-flank-aft-port': {'centre': [27.67, -20.2, -70.0], 'normal': [1, 0, 0], 'u': [0, 0, 1], 'width': 22.0, 'height': 9.0},
        'engine-flank-aft-stbd': {'centre': [-27.67, -20.2, -70.0], 'normal': [-1, 0, 0], 'u': [0, 0, -1], 'width': 22.0, 'height': 9.0},
        'mid-flank-port': {'centre': [17.5, -21.5, -2.0], 'normal': [1, 0, 0], 'u': [0, 0, 1], 'width': 18.0, 'height': 5.4, 'note': 'mid-hull flank under the S2 sponson (two port rows)'},
        'mid-flank-stbd': {'centre': [-17.5, -21.5, -2.0], 'normal': [-1, 0, 0], 'u': [0, 0, -1], 'width': 18.0, 'height': 5.4},
        'boat-hatch-port': {'centre': [17.14, -19.9, -19.0], 'normal': [1, 0, 0], 'u': [0, 0, 1], 'width': 5.8, 'height': 6.8, 'note': 'boat hatch leaves (6 x 7 m opening, 1 x 2 m personnel door in the aft leaf)'},
        'boat-hatch-stbd': {'centre': [-17.14, -19.9, -19.0], 'normal': [-1, 0, 0], 'u': [0, 0, -1], 'width': 5.8, 'height': 6.8},
        'bow-flank-port': {'centre': [17.1, -18.2, 70.5], 'normal': [1, 0, 0], 'u': [0, 0, 1], 'width': 24.0, 'height': 8.6, 'note': 'bow block flank (two port rows)'},
        'bow-flank-stbd': {'centre': [-17.1, -18.2, 70.5], 'normal': [-1, 0, 0], 'u': [0, 0, -1], 'width': 24.0, 'height': 8.6},
        'engine-deck': {'centre': [0.0, -4.3, -80.5], 'normal': [0, 1, 0], 'u': [0, 0, 1], 'width': 5.0, 'height': 3.0, 'note': 'engine-section deck aft of the aft turret'},
        'spine-top': {'centre': [0.0, -5.5, 32.0], 'normal': [0, 1, 0], 'u': [1, 0, 0], 'width': 3.0, 'height': 20.0, 'note': 'rail spine catwalk between the spine rails'},
        'gap-face-mid': {'centre': [0.0, -18.0, 42.9], 'normal': [0, 0, 1], 'u': [-1, 0, 0], 'width': 4.0, 'height': 3.0, 'note': 'gun-gap face of the mid hull (above the barrel)'},
        'command-front': {'centre': [2.8, 2.72, -33.9], 'normal': [0, 0.447, 0.894], 'u': [1, 0, 0], 'width': 4.6, 'height': 1.6, 'note': 'applique plate on the sloped casemate front between the CIC and bridge slits'},
        'command-aft': {'centre': [0.0, -2.3, -59.2], 'normal': [0, 0, -1], 'u': [-1, 0, 0], 'width': 5.0, 'height': 2.0, 'note': 'command block base, aft face between the two doors'},
        'command-roof': {'centre': [0.0, 5.6, -46.5], 'normal': [0, 1, 0], 'u': [1, 0, 0], 'width': 6.0, 'height': 3.0, 'note': 'casemate roof between the radome drum and the director'},
        'stern-plate': {'centre': [0.0, -8.0, -85.0], 'normal': [0, 0, -1], 'u': [-1, 0, 0], 'width': 8.0, 'height': 1.0, 'note': 'stern plate above the centre dish'},
    },
}
