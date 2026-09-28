"""Keystone-class fleet carrier CV-50: clean hard-surface hull, rebuilt from measurements of the
fal / Tripo H3.1 blueprint (the v5 installed GLB; see README.md and README-carrier.md).

    <blender-python> tools/blender/hulls/carrier.py <workdir> [--stage all|model|paint]
                     [--tex 4096] [--paint-tex 8192] [--ao 2048] [--threads 4] [--no-cull]

Stages: model -> <workdir>/carrier-hull.blend (volumes, booleans, cull, bevel, join, UVs) and
<workdir>/maps.npz (baked position / normal / zone / AO / curvature at --tex); paint ->
<workdir>/base.png, orm.png, normal.png (carrier_paint.py at --paint-tex) and
<workdir>/carrier-hull.glb (node 'hull', ship frame, not re-centred).

The 900 m hull (dimensions in carrier_dims.py):
  stern block   z -371 .. -261   octagon 262 x 145 m, the hangar's back recess, stern plate with
                                 six bell housings and louvred grilles, two gun sponsons
  box           z -261 .. 276    upper slab (deck y 21, bay ceiling -0.6) and lower slab (the
                                 hangar decks), cut through by the hangar and the six flank bays
                                 per side; radiator fields above and grilles below every bay
  frame rings   5 x 24 m         bold octagonal ribs between the bays (the bays' frames)
  bow section   z 276 .. 418     enclosed hangar section, the bow mouth and its lip
  keel wedge    y -115 .. -145.6 45-degree wedge under the box, ventral sensor pod
  island        z -249 .. 21     chamfered plinth, six stepped tiers of ~1 m pane rows on the 3 m
                                 deck pitch, the hammerhead bridge, mast
Ports are 1 m glass at the back of a 0.3 m band recess, between 1.5 m piers (2.5 m pitch), in
rows on the 3 m deck pitch; piers, mullions and fins are open 3-face meshes (no hidden faces).
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
import carrier_dims as D  # noqa: E402

S2 = math.sqrt(0.5)


# ------------------------------------------------------------------------------------------
# helpers
# ------------------------------------------------------------------------------------------
def ring(half, z, d=0.0):
    pts = K.mirror_half(half)
    if d:
        pts = K.offset_poly(pts, d)
    return [V((x, y, z)) for x, y in pts]


def zone_rings(grid, seg_zones, rows=None):
    segs = len(seg_zones)
    zl = [seg_zones[j] if j < segs else seg_zones[2 * segs - 1 - j] for j in range(2 * segs)]
    for k, row in enumerate(grid):
        if rows is not None and k not in rows:
            continue
        for j, f in enumerate(row):
            if f is not None:
                f.material_index = Z[zl[j]]


def ring_solid(bm, outer, inner, plane, v0, v1, zone=0, inner_zone=None):
    """Closed ring solid between two nested closed 2D outlines (same point count)."""
    O0, O1 = K.ring3(outer, plane, v0), K.ring3(outer, plane, v1)
    I0, I1 = K.ring3(inner, plane, v0), K.ring3(inner, plane, v1)
    n = len(outer)
    vs = {k: [bm.verts.new(p) for p in pts] for k, pts in (('o0', O0), ('o1', O1), ('i0', I0), ('i1', I1))}
    for j in range(n):
        j2 = (j + 1) % n
        for a, b in (('o0', 'o1'), ('o1', 'i1'), ('i1', 'i0'), ('i0', 'o0')):
            f = bm.faces.new([vs[a][j], vs[a][j2], vs[b][j2], vs[b][j]])
            f.material_index = inner_zone if (inner_zone is not None and (a, b) == ('i1', 'i0')) else zone


def rect_cutter(bm, c, n, up, w, h, depth, ch=0.15, zone_side=Z['recess'], zone_back=Z['recess'], out=1.0):
    grid, caps = K.oriented_prism(bm, K.chamfer_rect(0, 0, w, h, ch), c, n, up, -depth, out, zone=zone_side)
    caps[0].material_index = zone_back
    return grid, caps


def quad(bm, pts, zone):
    f = bm.faces.new([bm.verts.new(V(p)) for p in pts])
    f.material_index = zone
    return f


def fin(bm, c, along, n, w, h, depth, zone, front=True):
    """Open 3-face block (front + two sides) standing in a recess: front face centred at c (on
    the facade plane), `along` the row direction, n outward, width w, height h (along n x along
    ... i.e. the in-plane up), reaching `depth` back into the recess. No top / bottom / back
    faces: they lie against the recess walls and the glass."""
    a = V(along).normalized(); nn = V(n).normalized(); u = nn.cross(a).normalized()
    if u.y < 0:
        u = -u
    c = V(c)
    hw, hh = w / 2, h / 2
    f0 = [c - a * hw - u * hh, c + a * hw - u * hh, c + a * hw + u * hh, c - a * hw + u * hh]
    b = [p - nn * depth for p in f0]
    out = []
    if front:
        out.append(quad(bm, f0, zone))
    out.append(quad(bm, [b[0], f0[0], f0[3], b[3]], zone))
    out.append(quad(bm, [f0[1], b[1], b[2], f0[2]], zone))
    return out


class Rows:
    """Port rows on a planar facade: one band cutter per row (1 m tall, 0.3 m deep, glass back)
    and open piers between the 1 m panes (2.5 m pitch)."""

    def __init__(self, vol, pitch=2.5, pane=1.0, h=1.0, depth=0.3, pier_zone=Z['paint']):
        self.vol, self.pitch, self.pane, self.h, self.depth, self.zone = vol, pitch, pane, h, depth, pier_zone
        self.piers = []
        self.count = 0

    def row(self, a, b, n, skip=()):
        """Row from a to b (points on the facade, same height), n outward. skip: [(t0, t1)]
        ranges of the along-coordinate (metres from a) left without ports."""
        a, b, n = V(a), V(b), V(n).normalized()
        L = (b - a).length
        d = (b - a).normalized()
        # split into runs around the skips
        cuts = sorted(skip)
        runs, t = [], 0.0
        for s0, s1 in cuts:
            if s0 > t:
                runs.append((t, min(s0, L)))
            t = max(t, s1)
        if t < L:
            runs.append((t, L))
        for t0, t1 in runs:
            k = int(math.floor((t1 - t0 - (self.pitch - self.pane)) / self.pitch + 1e-6))
            if k < 1:
                continue
            Lb = k * self.pitch + (self.pitch - self.pane)
            m = a + d * ((t0 + t1) / 2)
            u = n.cross(d).normalized()
            if u.y < 0 or (abs(u.y) < 1e-6 and u.z < 0):
                u = -u
            rect_cutter(self.vol.cutters, m, n, u, Lb, self.h, self.depth, ch=0.0, zone_back=Z['glass'], out=1.5)
            pw = self.pitch - self.pane
            for j in range(k + 1):
                p = m + d * (-Lb / 2 + pw / 2 + j * self.pitch)
                self.piers.append((p, d, n, pw))
            self.count += k

    def add(self, name='piers'):
        piers, h, dep, zone = self.piers, self.h, self.depth, self.zone
        if piers:
            self.vol.adds.append((name, lambda bm2: [fin(bm2, p, d, n, w, h + 0.02, dep + 0.02, zone) for p, d, n, w in piers]))


# ------------------------------------------------------------------------------------------
# stern block
# ------------------------------------------------------------------------------------------
def stern_block():
    v = Volume('stern', bevel=0.3)
    bm = v.bm
    rings = [ring(D.P_END, D.Z_STERN, -4.0), ring(D.P_END, D.Z_STERN + 4.0), ring(D.P_END, D.Z_SF - 2.0), ring(D.P_END, D.Z_SF, -2.0)]
    grid, caps = K.loft(bm, rings, zone=Z['paint'])
    zone_rings(grid, ['deck', 'paint', 'paint', 'paint', 'belly'])
    for f in caps:
        f.material_index = Z['paint']
    K.solid(bm)
    cut = v.cutters
    # the hangar's back recess (back wall z -276): ceiling 1 m under the slab's (no coplanar faces)
    back = K.mirror_half(D.c_oct(D.Y_CEIL - 1.0, D.Y_AFT, tc=(16.0, 19.0), bc=(12.0, 12.0)))
    K.prism(cut, back, 'xy', D.Z_BACK, D.Z_SF + 3.0, zone=Z['trim'])
    # port rows on the flanks: 6 decks above the sponson, 6 below it
    rows = Rows(v)
    for s in (1, -1):
        for y in [-14.0 - 3 * i for i in range(6)] + [-76.0 - 3 * i for i in range(6)]:
            rows.row((s * D.X_END, y, D.Z_SF - 3.0), (s * D.X_END, y, D.Z_STERN + 5.0), (s, 0, 0), skip=[(28.0, 36.0), (80.0, 88.0)])
        # three rows on the upper chamfer
        for t in (0.35, 0.55, 0.75):
            x, y = 131.0 - 32.0 * t, -8.0 + 32.0 * t
            rows.row((s * x, y, D.Z_SF - 4.0), (s * x, y, D.Z_STERN + 6.0), (s * S2, S2, 0))
    # bay-facing gallery ports on the stern block's front face (two rows of four)
    gallery_ports(cut, D.Z_SF, 1)
    # stern plate: centre grille between the bells, upper and lower grille panels
    fins = []
    for (xc, yc, w, h) in ((0.0, -50.0, 52.0, 34.0), (0.0, 8.0, 40.0, 16.0), (0.0, -104.0, 40.0, 12.0)):
        c = V((xc, yc, D.Z_STERN))
        rect_cutter(cut, c, (0, 0, -1), (0, 1, 0), w, h, 2.0, ch=1.2, zone_back=Z['dark'])
        for dx in np.arange(-w / 2 + 1.2, w / 2 - 1.1, 1.4):
            fins.append((V((xc + dx, yc, D.Z_STERN + 1.2)), (0.14, h - 0.6, 1.8)))
    v.adds.append(('grille', lambda bm2: [K.box(bm2, cc, sz, zone=Z['fin']) for cc, sz in fins]))
    K.solid(cut)
    rows.add()
    return v


def gallery_ports(cut, z, s_face):
    """Two rows of four 1 m ports on a bay-facing face (z = const, facing s_face * z) of a frame
    post, both sides: x 105, 111, 117, 123, y -32 / -64 (the module's GALLERY lights)."""
    for sx in (1, -1):
        for x in (105.0, 111.0, 117.0, 123.0):
            for y in (-32.0, -64.0):
                rect_cutter(cut, (sx * x, y, z), (0, 0, s_face), (0, 1, 0), 1.0, 1.0, 0.25, ch=0.12, zone_back=Z['glass'])


def stern_details():
    vols = []
    # bell housings: collars from the stern plate aft to the bells, two trim rings each
    h = Volume('bell_housings', bevel=0.12)
    for (x, y), r in D.BELLS:
        for s in (1, -1):
            K.lathe(h.bm, (s * x, y, D.Z_STERN + 1.0), (0, 0, -1), [(r + 4.4, 0.0), (r + 4.4, 26.0), (r + 3.4, 27.6), (r + 3.4, 37.6)], n=32, zone=Z['metal'])
            for t in (6.0, 18.0):
                K.cyl(h.bm, (s * x, y, D.Z_STERN - t), (s * x, y, D.Z_STERN - t - 1.4), r + 5.0, n=32, zone=Z['trim'])
    K.solid(h.bm)
    vols.append(h)
    # sponsons: chamfered box from the flank out to the beam extremity, a chamfered outer end
    sp = Volume('sponsons', bevel=0.2)
    S = D.SPONSON
    for s in (1, -1):
        prof = K.chamfer_rect(S['zc'], S['yc'], S['l'], S['h'], S['c'])
        prof2 = K.offset_poly(prof, -4.0)
        K.stack(sp.bm, [(prof, s * S['x0']), (prof, s * (S['x1'] - 4.0)), (prof2, s * S['x1'])], 'zy', zone=Z['paint'])
    K.solid(sp.bm)
    for s in (1, -1):
        # a service bay on the sponson's forward face and a vent bay on its aft face
        rect_cutter(sp.cutters, (s * 165.0, S['yc'], S['zc'] + S['l'] / 2), (0, 0, 1), (0, 1, 0), 18.0, 10.0, 1.2, ch=1.0, zone_back=Z['dark'])
        rect_cutter(sp.cutters, (s * 165.0, S['yc'], S['zc'] - S['l'] / 2), (0, 0, -1), (0, 1, 0), 24.0, 12.0, 1.2, ch=1.0, zone_back=Z['dark'])
        for t in (0.0,):
            pass
    K.solid(sp.cutters)
    vols.append(sp)
    # belts: armour rings round the stern block
    b = Volume('stern_belts', bevel=0.1)
    ob = K.offset_poly(K.mirror_half(D.P_END), 0.8)
    ib = K.offset_poly(K.mirror_half(D.P_END), -1.0)
    for z0, z1 in ((-366.0, -362.0), (-270.0, -266.0)):
        ring_solid(b.bm, ob, ib, 'xy', z0, z1, zone=Z['trim'])
    K.solid(b.bm)
    vols.append(b)
    return vols


# ------------------------------------------------------------------------------------------
# box: upper and lower slab, the hangar bays
# ------------------------------------------------------------------------------------------
def box():
    v = Volume('box', bevel=0.3)
    bm = v.bm
    grid, caps = K.loft(bm, [ring(D.P_BOX, D.Z_SF), ring(D.P_BOX, D.Z_BA)], zone=Z['paint'])
    zone_rings(grid, ['deck', 'paint', 'paint', 'paint', 'belly'])
    K.solid(bm)
    cut = v.cutters
    # the hangar and the flank bays: one closed (z, y) outline through both flanks, stepped decks;
    # the steps sit 0.5 m inside the frame rings F1 / F5 (never coplanar with a ring face)
    zA, zB = D.FRAMES[0][1] - 0.5, D.FRAMES[4][0] + 0.5
    outline = [(D.Z_SF - 4.0, D.Y_AFT), (zA, D.Y_AFT), (zA, D.Y_LONG), (zB, D.Y_LONG), (zB, D.Y_BAY1), (D.Z_BA + 4.0, D.Y_BAY1),
               (D.Z_BA + 4.0, D.Y_CEIL), (D.Z_SF - 4.0, D.Y_CEIL)]
    K.prism(cut, outline, 'zy', -150.0, 150.0, zone=Z['trim'])
    # floor and ceiling zones are set after the boolean (see finish_box_zones)
    # radiator fields on the upper chamfer above every bay, grille bays on the lower chamfer below
    fins = []
    for z0, z1 in D.BAYS:
        z0c, z1c = max(z0, D.Z_SF) + 4.0, min(z1, D.Z_BA) - 4.0
        zc, L = (z0c + z1c) / 2, z1c - z0c
        for s in (1, -1):
            nu = V((s * S2, S2, 0)); up = V((-s * S2, S2, 0))
            c = V((s * 110.5, 10.5, zc)) + up * 2.0
            rect_cutter(cut, c, nu, up, L, 19.0, 1.0, ch=0.8, zone_back=Z['dark'])
            r_, u_, n_ = K.basis(nu, up)
            R = Matrix((r_, u_, n_)).transposed()
            for dz in np.arange(-L / 2 + 0.9, L / 2 - 0.8, 1.8):
                fins.append((c + r_ * dz - n_ * 0.55, R, (0.1, 18.4, 0.9)))
            nd = V((s * S2, -S2, 0)); dn = V((s * S2, S2, 0))
            c2 = V((s * 110.5, -106.5, zc)) + dn * 0.5
            rect_cutter(cut, c2, nd, dn, L, 11.0, 0.9, ch=0.6, zone_back=Z['dark'])
            r2, u2, n2 = K.basis(nd, dn)
            R2 = Matrix((r2, u2, n2)).transposed()
            for dz in np.arange(-L / 2 + 0.8, L / 2 - 0.7, 1.5):
                fins.append((c2 + r2 * dz - n2 * 0.5, R2, (0.09, 10.4, 0.8)))
    v.adds.append(('louvres', lambda bm2: [K.box(bm2, cc, sz, R=R, zone=Z['fin']) for cc, R, sz in fins]))
    K.solid(cut)
    return v


def frame_rings():
    vols = []
    for i, (z0, z1) in enumerate(D.FRAMES):
        v = Volume(f'frame{i + 1}', bevel=0.3)
        sill = D.SILL[i]
        # long-zone rings: inner floor 0.1 m under the continuous deck (hidden in the lower slab)
        inner = K.mirror_half(D.c_ring(sill - (0.1 if sill < -95 else 0.0)))
        outer = K.mirror_half(D.P_END)
        ring_solid(v.bm, outer, inner, 'xy', z0, z1, zone=Z['paint'], inner_zone=Z['trim'])
        # zones of the outer ring faces: deck on top, belly under
        for f in v.bm.faces:
            c = f.calc_center_median()
            f.normal_update()
            if f.normal.y > 0.9 and c.y > 20:
                f.material_index = Z['deck']
            elif f.normal.y < -0.9 and c.y < -110:
                f.material_index = Z['belly']
        K.solid(v.bm)
        cut = v.cutters
        zc = (z0 + z1) / 2
        for s in (1, -1):
            # two inset panels on the post's outer face, a full-height band between them at y -44 .. -56
            for yc, h in ((-31.5, 25.0), (-69.5, 27.0)):
                rect_cutter(cut, (s * D.X_END, yc, zc), (s, 0, 0), (0, 1, 0), 16.0, h, 1.0, ch=1.2, zone_back=Z['trim'])
            # a recessed band across the rib on the deck (the rib's cap)
        gallery_ports(cut, z0, -1)
        gallery_ports(cut, z1, 1)
        K.solid(cut)
        vols.append(v)
    return vols


# ------------------------------------------------------------------------------------------
# bow section
# ------------------------------------------------------------------------------------------
def bow_block():
    v = Volume('bow', bevel=0.3)
    bm = v.bm
    rings = [ring(D.P_END, D.Z_BA, -2.0), ring(D.P_END, D.Z_BA + 2.0), ring(D.P_END, D.Z_BF - 6.0), ring(D.P_END, D.Z_BF, -6.0)]
    grid, caps = K.loft(bm, rings, zone=Z['paint'])
    zone_rings(grid, ['deck', 'paint', 'paint', 'paint', 'belly'])
    for f in caps:
        f.material_index = Z['paint']
    K.solid(bm)
    cut = v.cutters
    K.prism(cut, K.mirror_half(D.C_BOW), 'xy', D.Z_BA - 3.0, D.Z_BF + 4.0, zone=Z['trim'])
    rows = Rows(v)
    for s in (1, -1):
        for y in [-14.0 - 3 * i for i in range(8)] + [-70.0 - 3 * i for i in range(8)]:
            rows.row((s * D.X_END, y, D.Z_BA + 3.0), (s * D.X_END, y, D.Z_BF - 7.0), (s, 0, 0), skip=[(14.0, 22.0), (116.0, 124.0)])
        for t in (0.35, 0.55, 0.75):
            x, y = 131.0 - 32.0 * t, -8.0 + 32.0 * t
            rows.row((s * x, y, D.Z_BA + 4.0), (s * x, y, D.Z_BF - 8.0), (s * S2, S2, 0))
    gallery_ports(cut, D.Z_BA, -1)
    # bow face round the mouth lip (it read as one flat plate): recessed service panels in the upper and
    # lower bands, louvred vent bays in the side bands (the face is P_END inset 6 m: top y 17, sides x 125)
    fins = []
    for s in (1, -1):
        for x in (20.0, 50.0, 80.0):
            for yc in (9.0, -106.5):
                rect_cutter(cut, (s * x, yc, D.Z_BF), (0, 0, 1), (0, 1, 0), 24.0, 8.0, 0.6, ch=0.8, zone_back=Z['trim'])
        for yc in (-32.0, -68.0):
            rect_cutter(cut, (s * 113.5, yc, D.Z_BF), (0, 0, 1), (0, 1, 0), 13.0, 28.0, 1.4, ch=1.0, zone_back=Z['dark'])
            for dy in np.arange(-13.0, 13.01, 1.3):
                fins.append((V((s * 113.5, yc + dy, D.Z_BF - 0.7)), (12.4, 0.12, 1.2)))
    v.adds.append(('bow_vents', lambda bm2: [K.box(bm2, cc, sz, zone=Z['fin']) for cc, sz in fins]))
    K.solid(cut)
    rows.add()
    return v


def bow_details():
    vols = []
    # mouth lip: a proud frame round the mouth, flush with the opening
    lip = Volume('mouth_lip', bevel=0.15)
    inner = K.mirror_half(D.C_BOW)
    outer = K.offset_poly(inner, 7.0)
    ring_solid(lip.bm, outer, inner, 'xy', D.Z_BF - 2.0, D.Z_LIP, zone=Z['trim'])
    K.solid(lip.bm)
    vols.append(lip)
    # belts round the bow section
    b = Volume('bow_belts', bevel=0.1)
    ob = K.offset_poly(K.mirror_half(D.P_END), 0.8)
    ib = K.offset_poly(K.mirror_half(D.P_END), -1.0)
    for z0, z1 in ((282.0, 286.0), (404.0, 408.0)):
        ring_solid(b.bm, ob, ib, 'xy', z0, z1, zone=Z['trim'])
    K.solid(b.bm)
    vols.append(b)
    # bow sensor probes (the envelope's bow extremity, z +450)
    pr = Volume('probes', bevel=0.04)
    for x in (15.0, -15.0):
        K.lathe(pr.bm, (x, -108.0, D.Z_BF - 1.0), (0, 0, 1), [(1.6, 0.0), (1.6, 4.0), (0.8, 5.0), (0.8, 26.0), (0.45, 27.0), (0.45, 31.0), (0.05, D.Z_TIP - D.Z_BF + 1.0)], n=12, zone=Z['metal'])
    K.solid(pr.bm)
    vols.append(pr)
    # hangar interior of the bow section: wall walkways (y -60) along both inner walls
    wk = Volume('bow_walkways', bevel=0.05, cull=False)
    for s in (1, -1):
        K.box(wk.bm, (s * (D.W_IN - 1.5), -60.25, 346.0), (3.0, 0.5, 136.0), zone=Z['deck'])
        for z in np.arange(282.0, 412.0, 6.5):
            K.box(wk.bm, (s * (D.W_IN - 0.9), -61.2, z), (1.8, 1.4, 0.4), zone=Z['dark'])
    K.solid(wk.bm)
    vols.append(wk)
    return vols


# ------------------------------------------------------------------------------------------
# keel wedge, ventral pod
# ------------------------------------------------------------------------------------------
def keel():
    v = Volume('keel', bevel=0.3)
    kt = D.KEEL
    top, ht = kt['top'], kt['half_top']
    dh = top - D.Y_KEEL
    hb = ht - dh
    z0, z1 = kt['z0'], kt['z1']
    # a planar 45-degree ramp at each end: loft of (x, y) sections along z would twist; build the
    # wedge as two (x, y) trapezoids joined by ramps: top face z0..z1, bottom z0+dh..z1-dh
    T = lambda z: [V((ht, top, z)), V((-ht, top, z))]
    Bt = lambda z: [V((-hb, D.Y_KEEL, z)), V((hb, D.Y_KEEL, z))]
    rings = [T(z0) + Bt(z0 + dh), T(z1) + Bt(z1 - dh)]
    grid, caps = K.loft(bm := v.bm, rings, zone=Z['belly'])
    K.solid(bm)
    rows = Rows(v, pier_zone=Z['belly'])
    for s in (1, -1):
        n = (s * S2, -S2, 0)
        for y in D.KEEL_ROWS:
            x = ht - (top - y)
            za, zb = z0 + (top - y) + 6.0, z1 - (top - y) - 6.0
            rows.row((s * x, y, za), (s * x, y, zb), n)
    K.solid(v.cutters)
    rows.add()
    vols = [v]
    pod = Volume('keel_pod', bevel=0.12)
    K.stack(pod.bm, [(K.chamfer_rect(0, 160.0, 28.0, 60.0, 5.0), D.Y_KEEL + 1.0), (K.chamfer_rect(0, 160.0, 28.0, 60.0, 5.0), -150.0),
                     (K.chamfer_rect(0, 160.0, 24.0, 56.0, 3.5), -152.0)], 'xz', zone=Z['belly'])
    prof = [(8.4, 0.0), (8.4, 0.6)]
    R = D.Y_KEEL - 6.4 - 0.6 - D.Y_BOTTOM - 0.0   # dome radius so the tip lands on the envelope bottom
    R = (-151.4 - 0.6) - D.Y_BOTTOM
    for k in range(0, 9):
        a = k / 8 * math.pi / 2
        prof.append((max(R * math.cos(a), 0.02), 0.6 + R * math.sin(a)))
    K.lathe(pod.bm, (0, -151.4, 160.0), (0, -1, 0), prof, n=32, zone=Z['metal'])
    K.solid(pod.bm)
    vols.append(pod)
    return vols


# ------------------------------------------------------------------------------------------
# hangar interior dressing that belongs to the hull: ceiling girders and gantries in the bays,
# the back wall (control gallery, cargo door, ports) and the bow section's inner walls
# ------------------------------------------------------------------------------------------
def hangar_cutters2(stern, bow):
    """Cutters applied AFTER the hangar cavity (they cut its walls): the back wall and the bow
    section's inner walls."""
    c2 = bmesh.new()
    zb = D.Z_BACK
    # control gallery: a 3 m glazed band across the back wall, mullions every 2 m
    rect_cutter(c2, (0.0, -15.0, zb), (0, 0, 1), (0, 1, 0), 120.0, 3.0, 1.2, ch=0.0, zone_back=Z['glass'])
    mul = [(V((x, -15.0, zb)), 0.22) for x in np.arange(-59.0, 59.01, 2.0)]
    stern.adds.append(('gallery_mullions', lambda bm2: [fin(bm2, p, (1, 0, 0), (0, 0, 1), w, 3.02, 1.22, Z['trim']) for p, w in mul]))
    # cargo door recess (bi-parting leaves are paint) at deck level
    rect_cutter(c2, (0.0, D.Y_AFT + 19.0, zb), (0, 0, 1), (0, 1, 0), 64.0, 36.0, 0.8, ch=1.5, zone_back=Z['trim'])
    # two rows of ports either side of the door
    piers = []
    for y in (-30.0, -38.0):
        for s in (1, -1):
            k = 16
            x0 = s * 38.0
            for j in range(k):
                x = x0 + s * (1.25 + j * 2.5)
                rect_cutter(c2, (x, y, zb), (0, 0, 1), (0, 1, 0), 1.0, 1.0, 0.25, ch=0.12, zone_back=Z['glass'])
    stern.cutters2 = c2
    b2 = bmesh.new()
    zl = D.Z_BA + 0.38 * (415.0 - 276.8) + 0.8
    for s in (1, -1):
        for i in range(11):
            z = 285.0 + 12.5 * i
            rect_cutter(b2, (s * D.W_IN, -48.0, z), (s, 0, 0), (0, 1, 0), 1.0, 1.0, 0.25, ch=0.12, zone_back=Z['glass'])
        # gallery windows over the walkway (y -56), 2.5 m pitch between the wall ports
        for i in range(10):
            z = 291.25 + 12.5 * i
            for dz in (-2.5, 0.0, 2.5):
                rect_cutter(b2, (s * D.W_IN, -56.5, z + dz), (s, 0, 0), (0, 1, 0), 1.0, 1.0, 0.25, ch=0.12, zone_back=Z['glass'])
    lift = K.chamfer_rect(0.0, zl, 54.0, 44.0, 3.0)
    ring_solid(b2, lift, K.offset_poly(lift, -0.35), 'xz', D.Y_BOW - 0.4, D.Y_BOW + 1.0, zone=Z['dark'])
    for x in (-3.0, 3.0):
        K.prism(b2, K.chamfer_rect(x, (zl + 22.0 + 415.0) / 2, 0.6, 415.0 - zl - 24.0, 0.2), 'xz', D.Y_BOW - 0.3, D.Y_BOW + 1.0, zone=Z['dark'])
    bow.cutters2 = b2


def hangar_dressing():
    vols = []
    g = Volume('ceiling_girders', bevel=0.04, cull=False)
    for z0, z1 in D.BAYS:
        L = z1 - z0
        yc = D.Y_CEIL - (1.0 if z0 > D.Z_SF else 1.5)
        for f in (0.08, 1 / 3, 2 / 3, 0.92):
            K.box(g.bm, (0.0, D.Y_CEIL - 1.1, z0 + L * f), (238.0, 2.6, 1.6), zone=Z['trim'])
        for s in (1, -1):
            # crane gantry rails along the bay (safety yellow) and their hangers
            K.box(g.bm, (s * 46.0, D.Y_CEIL - 3.2, (z0 + z1) / 2), (1.6, 1.8, L - 0.5), zone=Z['foil'])
            for f in (0.08, 1 / 3, 2 / 3, 0.92):
                K.box(g.bm, (s * 46.0, D.Y_CEIL - 2.4, z0 + L * f), (0.8, 1.2, 0.8), zone=Z['dark'])
    K.solid(g.bm)
    vols.append(g)
    return vols


# ------------------------------------------------------------------------------------------
# island
# ------------------------------------------------------------------------------------------
def outline(zc, w, l, c, d=0.0):
    o = K.chamfer_rect(0.0, zc, w, l, c)
    return K.offset_poly(o, d) if d else o


def _inside2(pts, x, z):
    ins = False
    n = len(pts)
    for i in range(n):
        (x1, z1), (x2, z2) = pts[i], pts[(i + 1) % n]
        if (z1 > z) != (z2 > z) and x < x1 + (z - z1) * (x2 - x1) / (z2 - z1):
            ins = not ins
    return ins


ISLAND = None


def island_blocks():
    blocks = [('plinth', D.PLINTH['zc'], D.PLINTH['w'], D.PLINTH['l'], D.PLINTH['c'], D.PLINTH['y0'], D.PLINTH['y1'])]
    blocks += list(D.TIERS)
    B = D.BRIDGE
    blocks.append(('bridge', B['zc'], B['w'], B['l'], B['c'], B['y0'], B['y1']))
    return blocks


def hidden_in_island(name, x, y, z):
    for nm, zc, w, l, c, y0, y1 in island_blocks():
        if nm == name or not (y0 < y < y1):
            continue
        if _inside2(outline(zc, w, l, c, 0.2), x, z):
            return True
    return False


def edges(o):
    n = len(o)
    for i in range(n):
        a, b = V(o[i]), V(o[(i + 1) % n])
        e = (b - a)
        if e.length < 1e-6:
            continue
        d = e.normalized()
        yield a, b, d, V((d.y, 0.0, -d.x))      # 2D (x, z) -> outward normal (x, 0, z) for CCW


def island():
    vols = []
    P = D.PLINTH
    pl = Volume('plinth', bevel=0.25)
    o = outline(P['zc'], P['w'], P['l'], P['c'])
    K.stack(pl.bm, [(o, P['y0']), (o, P['y1'] - 2.0), (outline(P['zc'], P['w'], P['l'], P['c'], -2.0), P['y1'])], 'xz', zone=Z['paint'])
    K.solid(pl.bm)
    rows = Rows(pl)
    for a, b, d, n in edges(o):
        for y in (24.5, 27.5, 30.5, 33.5):
            A, Bp = V((a.x, y, a.y)), V((b.x, y, b.y))
            L = (Bp - A).length
            if L < 8:
                continue
            rows.row(A + (Bp - A).normalized() * 2.0, Bp - (Bp - A).normalized() * 2.0, (n.x, 0, n.z))
    K.solid(pl.cutters)
    rows.add()
    vols.append(pl)
    B = D.BRIDGE
    for nm, zc, w, l, c, y0, y1 in list(D.TIERS) + [('bridge', B['zc'], B['w'], B['l'], B['c'], B['y0'], B['y1'])]:
        v = Volume(nm, bevel=0.15)
        o = outline(zc, w, l, c)
        top = outline(zc, w, l, c, -0.6)
        K.stack(v.bm, [(o, y0 - 0.5), (o, y1), (top, y1 + 0.4)], 'xz', zone=Z['paint'])
        K.solid(v.bm)
        if nm == 'bridge':
            bands, bh, pitch = [B['y0'] + 3.5, B['y0'] + 7.5], 1.6, 1.4
        else:
            bands, bh, pitch = [y for y in np.arange(y0 + 1.5, y1 - 1.9, D.DECK_PITCH)], 1.0, 2.4
        mm = []
        for y in bands:
            ring_solid(v.cutters, outline(zc, w, l, c, 3.0), outline(zc, w, l, c, -0.35), 'xz', y - bh / 2, y + bh / 2, zone=Z['recess'], inner_zone=Z['glass'])
            for a, b, d, n in edges(o):
                L = (b - a).length
                k = int(L / pitch)
                if k < 1:
                    continue
                off = (L - k * pitch) / 2
                for j in range(k + 1):
                    t = off + j * pitch
                    if t < 0.3 or t > L - 0.3:
                        continue
                    p2 = a + d * t
                    if hidden_in_island(nm, p2.x, y, p2.y):
                        continue
                    mm.append((V((p2.x, y, p2.y)), V((d.x, 0, d.y)), V((n.x, 0, n.z))))
        K.solid(v.cutters)
        v.adds.append(('mullions', lambda bm2, mm=mm, bh=bh: [fin(bm2, p, d, n, 0.2, bh + 0.02, 0.37, Z['trim']) for p, d, n in mm]))
        vols.append(v)
    # parapets round every roof (1.2 m) and the plinth's deck
    pa = Volume('parapets', bevel=0.04)
    for nm, zc, w, l, c, y0, y1 in island_blocks():
        yt = y1 + (0.4 if nm != 'plinth' else 0.0)
        oo = outline(zc, w, l, c, -0.2 if nm != 'plinth' else -2.2)
        ring_solid(pa.bm, K.offset_poly(oo, 0.0), K.offset_poly(oo, -0.45), 'xz', yt - 0.3, yt + 1.2, zone=Z['trim'])
    K.solid(pa.bm)
    vols.append(pa)
    # roof equipment: machinery houses, stair towers, dish plinths
    rf = Volume('island_roofs', bevel=0.08)
    rng = np.random.default_rng(50)
    for nm, zc, w, l, c, y0, y1 in island_blocks():
        yt = y1 + (0.4 if nm != 'plinth' else 0.0)
        # roof area not covered by the next block up
        for _ in range(3 if nm not in ('t6', 'bridge') else 1):
            for tries in range(20):
                ww, ll = rng.uniform(3, 7), rng.uniform(4, 10)
                lx, lz = w / 2 - c - ww, l / 2 - c - ll
                if lx < 1.0 or lz < 1.0:
                    continue
                x = rng.uniform(-lx, lx)
                z = zc + rng.uniform(-lz, lz)
                if any(_inside2(outline(z2, w2 + 8, l2 + 8, c2), x, z) for n2, z2, w2, l2, c2, a2, b2 in island_blocks() if a2 >= y1 - 0.5 and n2 != nm):
                    continue
                if nm == 'plinth' and abs(x) < 36:
                    continue
                hh = rng.uniform(2.2, 4.0)
                K.stack(rf.bm, [(K.chamfer_rect(x, z, ww, ll, 0.4), yt - 0.3), (K.chamfer_rect(x, z, ww, ll, 0.4), yt + hh),
                                (K.chamfer_rect(x, z, ww - 0.6, ll - 0.6, 0.3), yt + hh + 0.3)], 'xz', zone=Z['metal'])
                break
    K.solid(rf.bm)
    vols.append(rf)
    # mast on T6: a tapered lattice stand-in (tube, yards) up to the envelope top
    ms = Volume('mast', bevel=0.02)
    zm = D.MAST['z']
    K.cyl(ms.bm, (0, D.MAST['y0'] - 0.5, zm), (0, 156.0, zm), 1.3, 0.8, n=12, zone=Z['metal'])
    K.cyl(ms.bm, (0, 155.5, zm), (0, D.Y_TOP, zm), 0.35, 0.12, n=8, zone=Z['metal'])
    for y, L in ((149.0, 16.0), (153.0, 10.0)):
        K.box(ms.bm, (0, y, zm), (L, 0.35, 0.35), zone=Z['metal'])
        K.box(ms.bm, (0, y, zm), (0.35, 0.35, L * 0.5), zone=Z['metal'])
    K.solid(ms.bm)
    vols.append(ms)
    return vols


# ------------------------------------------------------------------------------------------
# deck: barbettes, armour plates, conduits, hatches, sensor wells
# ------------------------------------------------------------------------------------------
def deck_y(z):
    return 24.0 if (z < D.Z_SF or z > D.Z_BA) else D.Y_DECK


def deck():
    vols = []
    ba = Volume('barbettes', bevel=0.12)
    rL = 7.84 * D.TURRET_L
    for z, _g in D.SPINE_TURRETS:
        y = deck_y(z)
        K.cyl(ba.bm, (0, y - 0.5, z), (0, y + 3.0, z), rL + 1.2, n=64, zone=Z['trim'])
        K.cyl(ba.bm, (0, y + 2.9, z), (0, y + 3.5, z), rL - 0.4, n=64, zone=Z['metal'])
    rM = 4.48 * D.TURRET_M
    for z, _g in D.EDGE_TURRETS:
        y = deck_y(z)
        for s in (1, -1):
            K.cyl(ba.bm, (s * D.X_EDGE_T, y - 0.5, z), (s * D.X_EDGE_T, y + 1.2, z), rM + 0.8, n=40, zone=Z['trim'])
    S = D.SPONSON
    for s in (1, -1):
        K.cyl(ba.bm, (s * 168.0, S['yc'] + S['h'] / 2 - 0.5, S['zc']), (s * 168.0, S['yc'] + S['h'] / 2 + 2.0, S['zc']), rL + 1.0, n=64, zone=Z['trim'])
    K.solid(ba.bm)
    vols.append(ba)
    # raised armour plates on the deck between the ribs, conduit runs along the deck edges
    ap = Volume('deck_plates', bevel=0.06)
    runs = [(D.Z_SF, D.FRAMES[0][0])] + [(D.FRAMES[i][1], D.FRAMES[i + 1][0]) for i in range(4)] + [(D.FRAMES[4][1], D.Z_BA)]
    rng = np.random.default_rng(7)
    for z0, z1 in runs:
        for s in (1, -1):
            zz = z0 + 3.0
            while zz < z1 - 8.0:
                L = min(rng.uniform(14.0, 26.0), z1 - 3.0 - zz)
                for xc, w in ((s * 69.0, 30.0), (s * 88.5, 6.0)):
                    if abs(xc) < 50 and D.PLINTH['zc'] - D.PLINTH['l'] / 2 - 4 < zz + L / 2 < 25:
                        continue
                    K.plate(ap.bm, (xc, D.Y_DECK, zz + L / 2), (0, 1, 0), (0, 0, 1), w - 1.0, L - 1.0, 0.35, ch=0.12, back=0.3, zone=Z['deck'])
                zz += L
        # centre-line plates forward of the island
        if z0 > 20:
            for s in (1, -1):
                K.plate(ap.bm, (s * 26.0, D.Y_DECK, (z0 + z1) / 2), (0, 1, 0), (0, 0, 1), 30.0, z1 - z0 - 10.0, 0.3, ch=0.1, back=0.3, zone=Z['deck'])
    for s in (1, -1):
        K.box(ap.bm, (s * 95.5, D.Y_DECK + 0.45, 7.5), (1.6, 1.3, 537.0), zone=Z['dark'])
        K.box(ap.bm, (s * 93.2, D.Y_DECK + 0.35, 7.5), (1.0, 1.1, 537.0), zone=Z['metal'])
    K.solid(ap.bm)
    vols.append(ap)
    # sensor well on the bow section's deck (blueprint: a recessed rectangle, z 330 .. 380)
    return vols


# ------------------------------------------------------------------------------------------
# build
# ------------------------------------------------------------------------------------------
DETAIL = {'bow_walkways', 'ceiling_girders', 'parapets', 'island_roofs', 'mast', 'probes', 'deck_plates'}


def cull_hidden(obs, eps=0.03):
    """common.cull_hidden with a bounding-box prefilter (the carrier has thousands of faces per
    volume and ~40 volumes)."""
    from mathutils.bvhtree import BVHTree
    solid_obs = [o for o in obs if o.get('closed', True)]
    trees = []
    for ob in solid_obs:
        me = ob.data
        vs = [ob.matrix_world @ v.co for v in me.vertices]
        if not vs:
            continue
        lo = V((min(p.x for p in vs), min(p.y for p in vs), min(p.z for p in vs)))
        hi = V((max(p.x for p in vs), max(p.y for p in vs), max(p.z for p in vs)))
        trees.append((ob.name, lo, hi, BVHTree.FromPolygons(vs, [tuple(p.vertices) for p in me.polygons], all_triangles=False)))
    dirs = [V((0.577, 0.5774, 0.5773)).normalized(), V((-0.61, 0.33, -0.72)).normalized()]

    def inside(p, skip):
        for name, lo, hi, t in trees:
            if name == skip or not (lo.x < p.x < hi.x and lo.y < p.y < hi.y and lo.z < p.z < hi.z):
                continue
            votes = 0
            for d in dirs:
                o = V(p); k = 0
                for _ in range(64):
                    hit, _n, _i, _d = t.ray_cast(o, d, 1e4)
                    if hit is None:
                        break
                    k += 1; o = hit + d * 1e-4
                votes += k % 2
            if votes == 2:
                return True
        return False
    total = 0
    for ob in obs:
        if not ob.get('cull', True):
            continue
        me = ob.data
        bm = bmesh.new(); bm.from_mesh(me)
        dead = []
        for f in bm.faces:
            c = f.calc_center_median()
            if not inside(c - f.normal * eps, ob.name):
                continue
            if all(inside(v.co + (c - v.co).normalized() * min(eps * 3, (c - v.co).length * 0.5) - f.normal * eps, ob.name) for v in f.verts):
                dead.append(f)
        bmesh.ops.delete(bm, geom=dead, context='FACES')
        bm.to_mesh(me); bm.free(); me.update()
        total += len(dead)
    K.log(f'cull: {total} buried faces removed')


def dice(ob, step=24.0):
    """Split the big faces of a volume on a grid of planes (step metres, all three axes), so the
    cull can drop the buried parts of faces that are only partly covered (the box's slabs inside
    the frame rings, the box bottom over the keel wedge, the island's footprint on the deck)."""
    me = ob.data
    bm = bmesh.new(); bm.from_mesh(me)
    lo = np.min([v.co[:] for v in bm.verts], 0); hi = np.max([v.co[:] for v in bm.verts], 0)
    for ax in range(3):
        nrm = [0.0, 0.0, 0.0]; nrm[ax] = 1.0
        for c in np.arange(math.floor(lo[ax] / step) * step + step / 2, hi[ax], step):
            co = [0.0, 0.0, 0.0]; co[ax] = float(c)
            geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
            bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-4, plane_co=co, plane_no=nrm)
    n0 = len(me.polygons)
    bm.to_mesh(me); bm.free(); me.update()
    K.log(f'dice {ob.name}: {n0} -> {len(me.polygons)} faces')


DICE = {'box': 40.0, 'stern': 40.0, 'bow': 40.0, 'keel': 40.0, 'plinth': 18.0, 't1': 18.0, 't2': 18.0, 'frame1': 12.0, 'frame2': 12.0,
        'frame3': 12.0, 'frame4': 12.0, 'frame5': 12.0, 'sponsons': 12.0}


def do_boolean(ob, bm_cut, name):
    if not len(bm_cut.faces):
        return
    t1 = time.time()
    tmp = Volume(name)
    cut = tmp.to_object(bm_cut, name)
    n0 = len(ob.data.polygons)
    K.boolean(ob, cut)
    bpy.data.objects.remove(cut)
    if len(ob.data.polygons) < n0 * 0.5:
        raise RuntimeError(f'boolean {name} lost the solid ({n0} -> {len(ob.data.polygons)} faces): coincident cutters?')
    K.log(f'boolean {name}: {time.time() - t1:.1f}s ({n0} -> {len(ob.data.polygons)} faces)')


def build(args):
    t0 = time.time()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    K.zone_materials()
    st = stern_block()
    bw = bow_block()
    hangar_cutters2(st, bw)
    vols = [st, *stern_details(), box(), *frame_rings(), bw, *bow_details(), *keel(), *hangar_dressing(), *island(), *deck()]
    obs = []
    for v in vols:
        ob = v.to_object()
        ob['bevel'] = v.bevel
        ob['angle'] = v.angle
        ob['cull'] = v.cull
        do_boolean(ob, v.cutters, v.name + '_cut')
        if getattr(v, 'cutters2', None) is not None:
            do_boolean(ob, v.cutters2, v.name + '_cut2')
        if v.name in DICE:
            dice(ob, DICE[v.name])
        obs.append(ob)
        for nm, fn in v.adds:
            bm = bmesh.new()
            fn(bm)
            vv = Volume(f'{v.name}_{nm}')
            ob2 = vv.to_object(bm, f'{v.name}_{nm}')
            ob2['bevel'] = 0.0
            ob2['angle'] = 30.0
            ob2['cull'] = False
            ob2['closed'] = False
            obs.append(ob2)
    K.log(f'volumes: {len(obs)} objects, {sum(K.count_tris(o) for o in obs)} tris before bevel ({time.time() - t0:.1f}s)')
    if not args.get('no_cull'):
        cull_hidden(obs)
    import carrier_uv as UV
    for ob in obs:
        detail = (not ob.get('closed', True)) or ob.name in DETAIL
        UV.pre_unwrap(ob, density=0.3 if detail else 1.0)
        K.finish(ob, ob['bevel'], ob['angle'])
        if not detail:
            UV.tile_and_scale(ob)
    K.log('tris per object: ' + ', '.join(f'{o.name} {K.count_tris(o)}' for o in sorted(obs, key=lambda o: -K.count_tris(o))[:24]))
    hullob = K.join(obs, 'hull')
    K.log(f'joined: {K.count_tris(hullob)} tris ({time.time() - t0:.1f}s)')
    return hullob


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    work = os.path.abspath(argv[0])
    opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d
    stage = opt('--stage', 'all')
    os.makedirs(work, exist_ok=True)
    blend = os.path.join(work, 'carrier-hull.blend')
    maps = os.path.join(work, 'maps.npz')
    tex = int(opt('--tex', 4096))
    ptex = int(opt('--paint-tex', tex))
    if stage in ('all', 'model'):
        ob = build({'no_cull': '--no-cull' in argv})
        import carrier_uv as UV
        info = UV.pack(ob)
        K.log('uv', info)
        bpy.ops.wm.save_as_mainfile(filepath=blend)
        json.dump({'tris': K.count_tris(ob), **info}, open(os.path.join(work, 'model.json'), 'w'), indent=1)
        if stage == 'model' and '--bake' not in argv:
            return
        m = K.bake_maps(ob, size=tex, ao_size=int(opt('--ao', 2048)), ao_dist=3.0, threads=int(opt('--threads', 4)))
        np.savez_compressed(maps, **m)
    if stage in ('all', 'paint'):
        import carrier_paint as CP
        bpy.ops.wm.open_mainfile(filepath=blend)
        ob = bpy.data.objects['hull']
        m = dict(np.load(maps))
        spec = CP.spec()
        spec['px_per_m'] = json.load(open(os.path.join(work, 'model.json')))['px_per_m_at_4096'] * ptex / 4096
        base, orm, nrm = CP.paint(m, spec, work, size=ptex, normal_size=int(opt('--normal-tex', min(ptex, 4096))))
        K.set_final_material(ob, base, orm, normal_png=nrm)
        glb = os.path.join(work, 'carrier-hull.glb')
        K.export_glb(ob, glb)
        K.log('wrote', glb, os.path.getsize(glb))


if __name__ == '__main__':
    main()


# ------------------------------------------------------------------------------------------
# ship-module draft (module.py, then carrier_module.py): fixed asset fields, light roles,
# surfaces to measure
# ------------------------------------------------------------------------------------------
MODULE = {
    'header': """// Fleet carrier CV-50 — v3 REMODEL: clean hard-surface hull (tools/blender/hulls/carrier.py, dimensions in
// carrier_dims.py) rebuilt from measurements of the fal / Tripo H3.1 blueprint (the v5 hull), painted in
// texture space at 8192 px (tools/blender/hulls/carrier_paint.py: light paint, plating seams and tone, varied
// access panels, PATINA plate tone, AO grime, edge wear, decals incl. the CV-50 stencils, 15 m letters) and
// assembled with the Blender parts kit (tools/blender/specs/carrier-v3.json via tools/blender/assemble.py).
// A 900 m design (never carried itself, so no hangar-slot normalisation: the class scale correction is 1).
// The GLB is in the ship frame (metres, bow +Z, dorsal +Y, port +X), built symmetric about x = 0 (the
// blueprint sat 0.9 m to port, so every old centre-line coordinate x ~ +0.9 is x = 0 here) with its bbox
// centre at the origin: rotate [0, 0, 0], length = the bbox length. Node 'hull' is the hull, 'parts_*' the kit.""",
    'meta': {
        'name': 'Keystone-class fleet carrier', 'designation': 'CV-50', 'crew': 'about 20,000',
        'blurb': 'Warp-capable fleet carrier: a 900 m armoured box hull around one through-deck hangar that opens at the bow mouth and through six framed bays along each flank, with a stepped island, twin-gun turrets along the spine and on two stern sponsons, and six fusion bells in the stern block.',
    },
    'asset': {
        'glb': './assets/ships/carrier.glb', 'generator': 'tools/blender/hulls/carrier.py (remodel of the tripo3d/h3.1/multiview-to-3d hull) + tools/blender/assemble.py',
        'concept': './assets/concepts/carrier.webp', 'beauty': './assets/concepts/carrier-beauty.webp',
        'rotate': [0, 0, 0], 'hullNodes': ['hull'],
        'livery': {'gain': 0.05, 'glassGlow': [0.06, 0.055, 0.046], 'glassLit': 0.35},
    },
    # in navlight placement order: sidelight port, starboard, island strobe, keel strobe, stern
    'lights': [
        {'color': 'red', 'note': 'steady sidelights on the outboard face of each stern gun sponson (the beam extremity): red port, green starboard'},
        {'color': 'green'},
        {'color': 'white', 'blink': {'period': 1.3, 'duty': 0.1}, 'note': 'anti-collision strobes, alternating: island crown roof and the keel pod'},
        {'color': 'white', 'blink': {'period': 1.3, 'duty': 0.1, 'phase': 0.5}},
        {'color': 'white', 'note': 'steady stern light on the stern plate above the upper grille'},
    ],
    'surfaces': {
        'bow-flank-port': {'centre': [131.0, -52.0, 346.0], 'normal': [1, 0, 0], 'u': [0, 0, -1], 'width': 60.0, 'height': 30.0, 'note': 'bow section flank round the CV-50 stencil (between the port rows)'},
        'bow-flank-stbd': {'centre': [-131.0, -52.0, 346.0], 'normal': [-1, 0, 0], 'u': [0, 0, 1], 'width': 60.0, 'height': 30.0},
        'stern-flank-port': {'centre': [131.0, -80.0, -318.0], 'normal': [1, 0, 0], 'u': [0, 0, -1], 'width': 40.0, 'height': 6.0, 'note': 'stern block flank under the sponson'},
        'stern-flank-stbd': {'centre': [-131.0, -80.0, -318.0], 'normal': [-1, 0, 0], 'u': [0, 0, 1], 'width': 40.0, 'height': 6.0},
        'deck-bay3': {'centre': [60.0, -96.35, 53.0], 'normal': [0, 1, 0], 'u': [0, 0, 1], 'width': 40.0, 'height': 50.0, 'note': 'hangar deck, bay 3 (long zone)'},
        'deck-bow': {'centre': [50.0, -90.97, 380.0], 'normal': [0, 1, 0], 'u': [0, 0, 1], 'width': 30.0, 'height': 40.0, 'note': 'hangar deck, bow section'},
        'dorsal-deck': {'centre': [30.0, 21.0, 150.0], 'normal': [0, 1, 0], 'u': [0, 0, 1], 'width': 10.0, 'height': 50.0, 'note': 'dorsal deck forward of the island'},
        'back-wall': {'centre': [0.0, -50.0, -276.0], 'normal': [0, 0, 1], 'u': [-1, 0, 0], 'width': 60.0, 'height': 8.0, 'note': 'hangar back wall between the port rows and the cargo door'},
        'stern-plate': {'centre': [0.0, -50.0, -371.0], 'normal': [0, 0, -1], 'u': [-1, 0, 0], 'width': 20.0, 'height': 10.0, 'note': 'stern plate, centre grille'},
    },
}
