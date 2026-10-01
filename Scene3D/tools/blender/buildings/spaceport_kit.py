"""Building kit for cqs-fleet installations (spaceport first): a light polygon accumulator plus
parametric parts that later buildings (shipyard, stations) reuse at true metric size.

    python spaceport_kit.py --export <dir>     # writes the kit parts as GLBs + parts-buildings.json

Kit parts (each a function that adds geometry to an Acc in the PART frame; see the mount notes):
  habBlock(L, W, decks)      habitat / cargo block: chamfered body on a plinth, 3 m decks, roof plant;
                             mount +Y (stands on y = 0, length along Z, width along X). Kit ports and
                             the crew door go on it from the spec (habBlock_ports() gives the positions).
  clampArm(reach)            docking clamp arm: base plate, two parallel truss arms, a cradle with two
                             padded jaws; mount +Y (base on y = 0, the cradle face at y = reach).
  manipulator(l1, l2, ...)   two-link manipulator arm on a turret: base y = 0, mount +Y; the boom
                             points along the given angles; a flood head at the wrist.
  gantryCrane(span, legL, legR, h)  bridge crane over a bay: truss bridge, trolley, hoist block;
                             legs down to two rails at x = -span/2 (height legL) and +span/2 (legR).
  radiatorArray(n, w, h)     lattice mast with n thin radiator / solar panels (w x h, 0.5 m thick)
                             on outriggers; mount +Y (root at y = 0, mast along +Y).
  tug(scale=1)               24 m yard tug: crew cab, four drive pods, push plate with fenders; bow +Z.
  truss(p0, p1, w)           square lattice truss between two points (chords + diagonals).

Colours are linear RGB and go into the vertex colour (COLOR_0); materials carry roughness, metalness
and emission (see MATERIALS). Every face is flat shaded (planar facets, chamfers modelled).
"""
import math
import os
import sys
import json

import numpy as np

# ------------------------------------------------------------------------------------------------
# palette (linear RGB): light building paint with dark accents (corrections 24, 27, 31)
# ------------------------------------------------------------------------------------------------
C = dict(
    shell=(0.034, 0.036, 0.039),      # dark plated shell
    shell2=(0.050, 0.051, 0.054),
    seam=(0.020, 0.021, 0.023),
    rim=(0.52, 0.50, 0.46),           # pale chamfered rims (concept off-white)
    rim2=(0.43, 0.42, 0.39),
    joint=(0.10, 0.10, 0.10),
    hab=(0.56, 0.55, 0.52),           # habitat blocks: light paint
    hab2=(0.36, 0.36, 0.35),
    steel=(0.13, 0.135, 0.14),        # gunmetal trusses and frames
    steel2=(0.22, 0.22, 0.22),
    primer=(0.30, 0.30, 0.29),        # carrier frames (part-built: primer grey)
    primer2=(0.20, 0.205, 0.21),
    amber=(0.80, 0.42, 0.06),         # hazard / marking amber (0.93, 0.58, 0.12 sRGB-ish)
    black=(0.012, 0.012, 0.013),
    radiator=(0.16, 0.165, 0.17),
    solar=(0.020, 0.024, 0.040),
    white=(0.80, 0.80, 0.78),
)

# name: (roughness, metallic, emission rgb or None, emission strength)
MATERIALS = {
    'shell': (0.72, 0.25, None, 0),
    'rim': (0.62, 0.05, None, 0),
    'hab': (0.6, 0.05, None, 0),
    'steel': (0.5, 0.55, None, 0),
    'primer': (0.68, 0.15, None, 0),
    'radiator': (0.38, 0.6, None, 0),
    'solar': (0.25, 0.3, None, 0),
    'strip': (0.5, 0.0, (1.0, 0.95, 0.86), 2.2),       # white work-light strips
    'stripAmber': (0.5, 0.0, (1.0, 0.55, 0.12), 5.0),  # amber interior strips
}


class Acc:
    """Polygon accumulator in a current transform (4x4). faces: lists of vertex indices."""

    def __init__(self):
        self.V = []
        self.F = []
        self.M = []
        self.C = []
        self.stack = [np.eye(4)]
        self.seed = 1

    # transform stack ----------------------------------------------------------------------------
    def push(self, M):
        self.stack.append(self.stack[-1] @ M)

    def pop(self):
        self.stack.pop()

    def X(self):
        return self.stack[-1]

    def rnd(self):
        self.seed = (self.seed * 1103515245 + 12345) & 0x7fffffff
        return self.seed / 0x7fffffff

    def tone(self, col, j=0.06):
        k = 1.0 + (self.rnd() * 2 - 1) * j
        return tuple(c * k for c in col)

    def verts(self, pts):
        P = np.asarray(pts, float)
        H = np.c_[P, np.ones(len(P))] @ self.X().T
        b = len(self.V)
        self.V.extend(H[:, :3].tolist())
        return b

    def face(self, idx, mat, col):
        self.F.append(list(idx))
        self.M.append(mat)
        self.C.append(col)

    def poly(self, pts, mat, col):
        b = self.verts(pts)
        self.face(range(b, b + len(pts)), mat, col)

    def merge(self, other):
        b = len(self.V)
        self.V.extend(other.V)
        self.F.extend([[i + b for i in f] for f in other.F])
        self.M.extend(other.M)
        self.C.extend(other.C)

    def tris(self):
        return sum(len(f) - 2 for f in self.F)


# ------------------------------------------------------------------------------------------------
# matrices
# ------------------------------------------------------------------------------------------------
def T(x, y, z):
    M = np.eye(4)
    M[:3, 3] = (x, y, z)
    return M


def S(sx, sy=None, sz=None):
    sy = sx if sy is None else sy
    sz = sx if sz is None else sz
    return np.diag([sx, sy, sz, 1.0])


def Ry(deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    M = np.eye(4)
    M[0, 0], M[0, 2], M[2, 0], M[2, 2] = c, s, -s, c
    return M


def Rx(deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    M = np.eye(4)
    M[1, 1], M[1, 2], M[2, 1], M[2, 2] = c, -s, s, c
    return M


def Rz(deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    M = np.eye(4)
    M[0, 0], M[0, 1], M[1, 0], M[1, 1] = c, -s, s, c
    return M


def frame(o, x, y):
    """columns: local x, y, z = x cross y, origin o"""
    x = np.asarray(x, float); x /= np.linalg.norm(x)
    y = np.asarray(y, float); y = y - x * np.dot(x, y); y /= np.linalg.norm(y)
    z = np.cross(x, y)
    M = np.eye(4)
    M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = x, y, z, o
    return M


def along(p0, p1, up=(0, 1, 0)):
    """frame with +Z from p0 to p1, +Y toward up; origin p0. Returns (M, length)."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    d = p1 - p0
    L = float(np.linalg.norm(d))
    z = d / L
    up = np.asarray(up, float)
    if abs(np.dot(up / np.linalg.norm(up), z)) > 0.98:
        up = np.array([1.0, 0, 0]) if abs(z[0]) < 0.9 else np.array([0, 0, 1.0])
    x = np.cross(up, z); x /= np.linalg.norm(x)
    y = np.cross(z, x)
    M = np.eye(4)
    M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = x, y, z, p0
    return M, L


# ------------------------------------------------------------------------------------------------
# primitives (local frame of the accumulator)
# ------------------------------------------------------------------------------------------------
def crect(w, h, c=0.0, cx=0.0, cy=0.0):
    """chamfered rectangle, CCW, centred"""
    x, y = w / 2, h / 2
    if c <= 0:
        return [(cx - x, cy - y), (cx + x, cy - y), (cx + x, cy + y), (cx - x, cy + y)]
    return [(cx - x + c, cy - y), (cx + x - c, cy - y), (cx + x, cy - y + c), (cx + x, cy + y - c),
            (cx + x - c, cy + y), (cx - x + c, cy + y), (cx - x, cy + y - c), (cx - x, cy - y + c)]


def prism(acc, pts2, z0, z1, mat, col, caps=True, capcol=None, j=0.0):
    """extrude a CCW 2D outline (x, y) from z0 to z1"""
    n = len(pts2)
    b = acc.verts([(x, y, z0) for x, y in pts2] + [(x, y, z1) for x, y in pts2])
    for i in range(n):
        k = (i + 1) % n
        acc.face([b + i, b + k, b + n + k, b + n + i], mat, acc.tone(col, j) if j else col)
    if caps:
        cc = capcol or col
        acc.face([b + i for i in reversed(range(n))], mat, cc)
        acc.face([b + n + i for i in range(n)], mat, cc)


def box(acc, c, size, mat, col, ch=0.0, caps=True, j=0.0):
    """axis box centred at c (local), size (sx, sy, sz); chamfer on the 4 edges parallel to z"""
    sx, sy, sz = size
    acc.push(T(*c))
    prism(acc, crect(sx, sy, ch), -sz / 2, sz / 2, mat, col, caps=caps, j=j)
    acc.pop()


def beam(acc, p0, p1, w, h, mat, col, up=(0, 1, 0), ch=0.0, caps=True):
    M, L = along(p0, p1, up)
    acc.push(M)
    prism(acc, crect(w, h, ch), 0, L, mat, col, caps=caps)
    acc.pop()


def rod(acc, p0, p1, s, mat, col, up=(0, 1, 0)):
    """thin square rod, 4 faces, no caps (lattice members)"""
    beam(acc, p0, p1, s, s, mat, col, up=up, caps=False)


def cyl(acc, p0, p1, r, mat, col, n=12, caps=True, up=(0, 1, 0)):
    M, L = along(p0, p1, up)
    acc.push(M)
    pts = [(r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n)) for i in range(n)]
    prism(acc, pts, 0, L, mat, col, caps=caps)
    acc.pop()


def truss(acc, p0, p1, w, mat='steel', col=None, chord=None, up=(0, 1, 0), bays=None, diag=True):
    """square lattice truss p0 -> p1: four chords, rings and diagonals at ~w pitch"""
    col = col or C['steel']
    M, L = along(p0, p1, up)
    s = chord or max(0.35, w * 0.09)
    nb = bays or max(1, int(round(L / w)))
    acc.push(M)
    h = w / 2
    corners = [(-h, -h), (h, -h), (h, h), (-h, h)]
    for x, y in corners:
        rod(acc, (x, y, 0), (x, y, L), s, mat, col)
    for i in range(nb + 1):
        z = L * i / nb
        for k in range(4):
            a, b = corners[k], corners[(k + 1) % 4]
            rod(acc, (a[0], a[1], z), (b[0], b[1], z), s * 0.7, mat, col, up=(0, 0, 1))
        if diag and i < nb:
            z2 = L * (i + 1) / nb
            for k in range(4):
                a, b = corners[k], corners[(k + 1) % 4]
                if i % 2:
                    a, b = b, a
                rod(acc, (a[0], a[1], z), (b[0], b[1], z2), s * 0.6, mat, col, up=(0, 0, 1))
    acc.pop()


# ------------------------------------------------------------------------------------------------
# kit parts
# ------------------------------------------------------------------------------------------------
def habBlock(acc, L=40.0, W=16.0, decks=5, rnd=0.5):
    """habitat / cargo block standing on y = 0, length along z, width along x. Plinth 2 m, decks of
    3 m, chamfered roof edge, roof plant, a darker window band per lit deck (kit ports go on it),
    a recessed door bay on the +z end (kit door). Returns the face list for port placement."""
    H = 2.0 + decks * DECK + 1.5
    # plinth (dark)
    box(acc, (0, 1.0, 0), (W - 1.0, 2.0, L - 1.0), 'steel', C['steel'], ch=0.4)
    # body: chamfered section, slight tone per block
    col = acc.tone(C['hab'], 0.07)
    acc.push(T(0, 0, 0))
    sec = [(-W / 2, 2.0), (W / 2, 2.0), (W / 2, H - 2.0), (W / 2 - 2.0, H), (-W / 2 + 2.0, H), (-W / 2, H - 2.0)]
    prism(acc, sec, -L / 2, L / 2, 'hab', col, j=0.03)
    acc.pop()
    # dark ID / service band at the plinth and a pale-dark stripe at the roof line
    for sx in (-1, 1):
        acc.poly([(sx * (W / 2 + 0.05), 2.0, -L / 2 + 0.5), (sx * (W / 2 + 0.05), 2.0, L / 2 - 0.5),
                  (sx * (W / 2 + 0.05), 3.2, L / 2 - 0.5), (sx * (W / 2 + 0.05), 3.2, -L / 2 + 0.5)][::sx], 'hab', C['hab2'])
    # amber hazard corner marks on the +z end
    for sx in (-1, 1):
        acc.poly([(sx * (W / 2 - 0.2), 2.4, L / 2 + 0.05), (sx * (W / 2 - 2.2), 2.4, L / 2 + 0.05),
                  (sx * (W / 2 - 2.2), 3.4, L / 2 + 0.05), (sx * (W / 2 - 0.2), 3.4, L / 2 + 0.05)][::-sx], 'hab', C['amber'])
    # door bay recess frame on +z end (the kit door sits at x = 0, y = 2)
    box(acc, (0, 2.0 + 1.6, L / 2 + 0.25), (3.2, 3.2, 0.5), 'steel', C['steel2'], ch=0.2)
    # roof plant: two boxes, a vent stack, a small mast
    box(acc, (W * 0.18, H + 1.2, -L * 0.22), (W * 0.36, 2.4, L * 0.28), 'hab', acc.tone(C['hab2'], 0.1), ch=0.4)
    box(acc, (-W * 0.2, H + 0.9, L * 0.18), (W * 0.3, 1.8, L * 0.2), 'steel', C['steel2'], ch=0.3)
    cyl(acc, (-W * 0.25, H, -L * 0.3), (-W * 0.25, H + 4.0, -L * 0.3), 0.8, 'steel', C['steel'], n=8)
    rod(acc, (W * 0.3, H, L * 0.35), (W * 0.3, H + 7.0, L * 0.35), 0.25, 'steel', C['steel2'])
    return H


DECK = 3.0


def habBlock_ports(L, W, decks, lit_decks=None, run=6, pitch=2.5, gap=6.0):
    """kit port positions on the two long faces of a habBlock (part frame): rows on the lit decks,
    runs of `run` ports at `pitch` separated by `gap` m; returns [(x, y, z, nx)]"""
    lit = lit_decks if lit_decks is not None else [d for d in range(decks) if d % 2 == (decks % 2)] or [0]
    out = []
    runL = (run - 1) * pitch
    nr = max(1, int((L - 8.0 + gap) // (runL + gap)))
    tot = nr * runL + (nr - 1) * gap
    for d in lit:
        y = 2.0 + d * DECK + 1.6
        for r in range(nr):
            z0 = -tot / 2 + r * (runL + gap)
            for i in range(run):
                z = z0 + i * pitch
                for sx in (-1, 1):
                    out.append((sx * W / 2, y, z, sx))
    return out


def clampArm(acc, reach=24.0, w=10.0):
    """docking clamp arm from a base plate (y = 0) to a cradle at y = reach"""
    box(acc, (0, 0.8, 0), (w + 4, 1.6, w + 6), 'steel', C['steel'], ch=0.5)
    box(acc, (0, 3.0, 0), (w * 0.7, 3.0, w * 0.7), 'rim', C['rim2'], ch=0.8)
    for sz in (-1, 1):
        truss(acc, (0, 4.0, sz * w * 0.35), (0, reach - 3.0, sz * w * 0.35), 2.6, up=(0, 0, 1))
    # hydraulic rams
    for sx in (-1, 1):
        cyl(acc, (sx * w * 0.32, 4.0, 0), (sx * w * 0.2, reach * 0.6, 0), 0.5, 'steel', C['steel2'], n=8)
    # cradle: saddle beam with two jaws and pads
    box(acc, (0, reach - 2.0, 0), (w * 1.6, 2.4, w * 0.9), 'rim', C['rim'], ch=0.6)
    for sx in (-1, 1):
        box(acc, (sx * w * 0.7, reach + 0.4, 0), (1.6, 3.6, w * 0.8), 'steel', C['steel2'], ch=0.3)
        box(acc, (sx * w * 0.55, reach - 0.4, 0), (1.0, 1.2, w * 0.6), 'steel', C['amber'], ch=0.2)
    box(acc, (0, reach - 0.6, 0), (w * 1.0, 0.6, w * 0.6), 'steel', C['black'])


def manipulator(acc, yaw=0.0, a1=55.0, a2=-70.0, l1=34.0, l2=30.0, w=3.0):
    """turret base (y = 0) + shoulder + boom l1 at elevation a1 + forearm l2 at a1 + a2 (deg) +
    wrist and flood head; yaw about +Y. Returns the effector point in the part frame."""
    box(acc, (0, 1.0, 0), (9.0, 2.0, 9.0), 'steel', C['steel'], ch=1.0)
    cyl(acc, (0, 2.0, 0), (0, 5.0, 0), 3.6, 'rim', C['rim'], n=12)
    acc.push(Ry(yaw))
    box(acc, (0, 7.0, 0), (5.0, 4.0, 6.0), 'rim', C['rim2'], ch=0.8)
    sh = np.array([0, 8.0, 0])
    e1 = sh + l1 * np.array([0, math.sin(math.radians(a1)), math.cos(math.radians(a1))])
    a = math.radians(a1 + a2)
    e2 = e1 + l2 * np.array([0, math.sin(a), math.cos(a)])
    beam(acc, sh, e1, w, w * 1.2, 'rim', C['rim'], up=(1, 0, 0), ch=0.5)
    # hazard band near the elbow
    M, L = along(sh, e1, (1, 0, 0))
    acc.push(M)
    prism(acc, crect(w + 0.1, w * 1.2 + 0.1, 0.5), L - 4.0, L - 2.5, 'rim', C['amber'], caps=False)
    acc.pop()
    cyl(acc, e1 + np.array([-2.2, 0, 0]), e1 + np.array([2.2, 0, 0]), w * 0.8, 'steel', C['steel2'], n=10)
    beam(acc, e1, e2, w * 0.8, w, 'steel', C['steel2'], up=(1, 0, 0), ch=0.4)
    # cable along the boom
    rod(acc, sh + np.array([w * 0.7, 0, 0]), e1 + np.array([w * 0.7, 0, 0]), 0.35, 'steel', C['black'])
    # wrist + effector + flood head
    box(acc, tuple(e2), (2.4, 2.4, 2.4), 'steel', C['steel'], ch=0.4)
    d = (e2 - e1) / np.linalg.norm(e2 - e1)
    tip = e2 + d * 3.0
    cyl(acc, e2, tip, 0.9, 'steel', C['steel2'], n=8)
    for k in (-1, 1):
        rod(acc, tip, tip + d * 2.0 + np.array([k * 1.2, 0, 0]), 0.35, 'steel', C['steel'])
    acc.pop()
    return (Ry(yaw) @ np.r_[tip, 1])[:3]


def gantryCrane(acc, span=360.0, legL=60.0, legR=60.0, h=8.0, trolley_x=0.0, hoist=40.0):
    """bridge at y = 0 from x = -span/2 to +span/2 (z = 0); legs reach down legL / legR to rail bogies"""
    x0, x1 = -span / 2, span / 2
    # twin box girders with a walkway between (pale, like the concept's bridges)
    for sz in (-1, 1):
        beam(acc, (x0, 0, sz * 4.0), (x1, 0, sz * 4.0), h * 0.45, h, 'rim', C['rim'], up=(0, 1, 0), ch=0.8)
    # cross ties
    n = int(span // 20)
    for i in range(n + 1):
        x = x0 + span * i / n
        rod(acc, (x, -h * 0.3, -4.0), (x, -h * 0.3, 4.0), 0.6, 'steel', C['steel'])
    # amber stripe on the girder faces (hazard)
    for sz in (-1, 1):
        acc.poly([(x0 + 4, h * 0.30, sz * (4.0 + h * 0.225 + 0.05)), (x1 - 4, h * 0.30, sz * (4.0 + h * 0.225 + 0.05)),
                  (x1 - 4, h * 0.40, sz * (4.0 + h * 0.225 + 0.05)), (x0 + 4, h * 0.40, sz * (4.0 + h * 0.225 + 0.05))][::sz], 'rim', C['amber'])
    # legs (trusses) and bogies
    for x, L in ((x0, legL), (x1, legR)):
        if L > 1:
            truss(acc, (x, -h / 2, 0), (x, -h / 2 - L, 0), 6.0, up=(0, 0, 1))
        box(acc, (x, -h / 2 - L - 1.5, 0), (8.0, 3.0, 16.0), 'steel', C['steel2'], ch=0.6)
        box(acc, (x, h * 0.5 + 1.5, 0), (10.0, 3.0, 12.0), 'rim', C['rim2'], ch=0.6)
    # trolley + hoist + hook block
    box(acc, (trolley_x, h * 0.5 + 2.0, 0), (14.0, 4.0, 13.0), 'hab', C['hab'], ch=0.8)
    box(acc, (trolley_x + 5.0, h * 0.5 + 3.0, 4.0), (3.6, 2.6, 3.0), 'steel', C['steel2'], ch=0.3)
    for sx in (-1, 1):
        rod(acc, (trolley_x + sx * 1.2, -h * 0.5, 0), (trolley_x + sx * 1.2, -h * 0.5 - hoist, 0), 0.3, 'steel', C['black'])
    box(acc, (trolley_x, -h * 0.5 - hoist - 1.5, 0), (5.0, 3.0, 3.0), 'steel', C['amber'], ch=0.4)
    box(acc, (trolley_x, -h * 0.5 - hoist - 4.0, 0), (9.0, 1.2, 9.0), 'steel', C['steel'], ch=0.3)


def radiatorArray(acc, n=4, w=12.0, h=34.0, pitch=None, mast=None, solar=False):
    """lattice mast from y = 0 up, with n thin panels (w wide along x either side, h tall along y)"""
    pitch = pitch or h + 4.0
    mast = mast or 8.0 + n * pitch
    box(acc, (0, 1.0, 0), (6.0, 2.0, 6.0), 'steel', C['steel'], ch=0.6)
    truss(acc, (0, 2.0, 0), (0, mast, 0), 3.2, up=(0, 0, 1))
    for i in range(n):
        y0 = 8.0 + i * pitch
        for sx in (-1, 1):
            # outrigger + panel (thin), a slightly darker frame
            rod(acc, (sx * 1.6, y0 + h * 0.5, 0), (sx * 3.5, y0 + h * 0.5, 0), 0.6, 'steel', C['steel2'])
            x0 = sx * 3.5
            x1 = sx * (3.5 + w)
            mat, col = ('solar', C['solar']) if solar else ('radiator', C['radiator'])
            box(acc, ((x0 + x1) / 2, y0 + h / 2, 0), (w, h, 0.4), mat, acc.tone(col, 0.05))
            box(acc, ((x0 + x1) / 2, y0 + 0.3, 0), (w, 0.6, 0.8), 'steel', C['steel'])
            box(acc, ((x0 + x1) / 2, y0 + h - 0.3, 0), (w, 0.6, 0.8), 'steel', C['steel'])
            # fin ribs (radiator) as shallow strips on both faces
            if not solar:
                for k in range(1, int(w // 2)):
                    xx = x0 + (x1 - x0) * k / int(w // 2)
                    for sz in (-1, 1):
                        acc.poly([(xx - 0.12, y0 + 0.6, sz * 0.21), (xx + 0.12, y0 + 0.6, sz * 0.21),
                                  (xx + 0.12, y0 + h - 0.6, sz * 0.21), (xx - 0.12, y0 + h - 0.6, sz * 0.21)][::sz], 'radiator', C['steel2'])
    return mast


def tug(acc):
    """24 m yard tug, bow +Z: cab block, four drive pods on outriggers, push plate with fenders"""
    box(acc, (0, 0, 0), (8.0, 6.0, 14.0), 'hab', C['hab'], ch=1.2)
    box(acc, (0, 3.6, 2.0), (5.6, 1.6, 6.0), 'hab', C['hab2'], ch=0.5)
    # cab glazing band (dark, small craft keep glass dark)
    acc.poly([(-2.6, 1.0, 7.02), (2.6, 1.0, 7.02), (2.6, 2.2, 7.02), (-2.6, 2.2, 7.02)], 'steel', C['black'])
    # push plate + fenders at the bow
    box(acc, (0, 0, 8.6), (10.0, 7.0, 1.6), 'steel', C['steel'], ch=0.6)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(acc, (sx * 3.4, sy * 2.2, 9.7), (2.2, 2.0, 0.8), 'steel', C['black'], ch=0.3)
    # amber hazard bands on the plate
    acc.poly([(-4.8, -3.3, 9.42), (4.8, -3.3, 9.42), (4.8, -2.6, 9.42), (-4.8, -2.6, 9.42)], 'steel', C['amber'])
    # four pods on outriggers
    for sx in (-1, 1):
        for sy in (-1, 1):
            rod(acc, (sx * 4.0, sy * 1.5, -4.0), (sx * 7.0, sy * 3.0, -5.0), 0.8, 'steel', C['steel'])
            cyl(acc, (sx * 7.0, sy * 3.0, -1.0), (sx * 7.0, sy * 3.0, -9.5), 1.4, 'steel', C['steel2'], n=10)
            cyl(acc, (sx * 7.0, sy * 3.0, -9.5), (sx * 7.0, sy * 3.0, -11.0), 1.0, 'steel', C['black'], n=10)
    rod(acc, (0, 3.0, -4.0), (0, 8.0, -4.0), 0.2, 'steel', C['steel2'])


# ------------------------------------------------------------------------------------------------
# Blender mesh out
# ------------------------------------------------------------------------------------------------
def to_object(acc, name):
    """Blender object from an Acc (station frame metres, +Y up) as glTF-ready mesh: the glTF exporter
    with export_yup maps Blender (x, -z, y)... so we store Blender coords = (x, -z, y)."""
    import bpy
    V = np.asarray(acc.V, float)
    Vb = np.stack([V[:, 0], -V[:, 2], V[:, 1]], 1)
    me = bpy.data.meshes.new(name)
    me.from_pydata(Vb.tolist(), [], acc.F)
    me.update()
    mats = sorted(set(acc.M))
    for m in mats:
        me.materials.append(material(m))
    mi = {m: i for i, m in enumerate(mats)}
    me.polygons.foreach_set('material_index', [mi[m] for m in acc.M])
    # per-corner vertex colour (linear)
    ca = me.color_attributes.new('Col', 'FLOAT_COLOR', 'CORNER')
    cols = np.zeros((len(me.loops), 4), np.float32)
    cols[:, 3] = 1
    starts = np.empty(len(me.polygons), int)
    me.polygons.foreach_get('loop_start', starts)
    tot = np.empty(len(me.polygons), int)
    me.polygons.foreach_get('loop_total', tot)
    C_ = np.asarray(acc.C, np.float32)
    idx = np.repeat(np.arange(len(starts)), tot)
    cols[:, :3] = C_[idx]
    ca.data.foreach_set('color', cols.ravel())
    me.color_attributes.active_color = ca
    me.validate(clean_customdata=False)
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return ob


def material(name):
    import bpy
    key = f'sp_{name}'
    if key in bpy.data.materials:
        return bpy.data.materials[key]
    rough, metal, emis, es = MATERIALS[name]
    mt = bpy.data.materials.new(key)
    mt.use_nodes = True
    nt = mt.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    va = nt.nodes.new('ShaderNodeVertexColor')
    va.layer_name = 'Col'
    nt.links.new(va.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if emis:
        b.inputs['Emission Color'].default_value = (*emis, 1)
        b.inputs['Emission Strength'].default_value = es
    return mt


def export_glb(objs, path):
    import bpy
    for o in bpy.context.scene.objects:
        if o is not None:
            o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_yup=True,
                              export_apply=True, export_normals=True, export_tangents=False, export_texcoords=False,
                              export_materials='EXPORT', export_vertex_color='MATERIAL', export_animations=False,
                              export_extras=False, export_cameras=False, export_lights=False)


KIT = {
    'habBlock': dict(fn=lambda a: habBlock(a, 40.0, 16.0, 5), mount='+Y', note='habitat / cargo block 40 x 16 m, 5 decks of 3 m on a 2 m plinth; length along Z; kit ports at habBlock_ports(), crew door on the +Z end at (0, 2, L/2 + 0.5)'),
    'clampArm': dict(fn=lambda a: clampArm(a, 24.0), mount='+Y', note='docking clamp arm: base plate at y = 0, cradle face at y = 24 (reach), jaws along X'),
    'manipulator': dict(fn=lambda a: manipulator(a), mount='+Y', note='two-link manipulator arm (34 + 30 m) on a turret, base at y = 0; boom in the YZ plane; flood head at the wrist'),
    'gantryCrane': dict(fn=lambda a: gantryCrane(a, 120.0, 30.0, 30.0, hoist=20.0), mount='bridge', note='bridge crane: bridge girders at y = 0 along X (span 120 here, parametric), legs down to rail bogies, trolley and hoist'),
    'radiatorArray': dict(fn=lambda a: radiatorArray(a, 3, 12.0, 34.0), mount='+Y', note='lattice mast (root y = 0) with 3 pairs of thin 12 x 34 m radiator panels; solar=True gives dark cells'),
    'tug': dict(fn=lambda a: tug(a), mount='centre', note='24 m yard tug, bow +Z: cab, push plate with fenders, four drive pods (exhaust -Z)'),
}


def main():
    if '--export' not in sys.argv:
        print(__doc__)
        return
    out = sys.argv[sys.argv.index('--export') + 1]
    import bpy
    bpy.ops.wm.read_factory_settings(use_empty=True)
    info = {}
    for name, k in KIT.items():
        for o in list(bpy.data.objects):
            bpy.data.objects.remove(o)
        a = Acc()
        k['fn'](a)
        ob = to_object(a, name)
        path = os.path.join(out, f'{name}.glb')
        export_glb([ob], path)
        V = np.asarray(a.V)
        lo, hi = V.min(0), V.max(0)
        info[name] = dict(file=f'{name}.glb', tris=a.tris(), bbox=[lo.round(2).tolist(), hi.round(2).tolist()],
                          size=(hi - lo).round(2).tolist(), mount=dict(normal=k['mount']), note=k['note'],
                          generator='tools/blender/buildings/spaceport_kit.py')
        print(name, a.tris(), (hi - lo).round(2).tolist())
    json.dump(dict(generator='tools/blender/buildings/spaceport_kit.py', frame='metres, +Y up, +Z forward, +X left', parts=info),
              open(os.path.join(out, 'parts-buildings.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
