"""bkit: the shared building kit for the cqs-fleet colony buildings (16 buildings, brief briefs/buildings.md).

One parametric, true-size component library that every colony building script (tools/blender/buildings/<id>.py)
composes, plus the record of everything that is not baked geometry (lights, kit-part placements). It merges the two
earlier building kits:
  - yard_kit.py (shipyard): the lib.Part bake pipeline (bevel, weighted normals, smart UV, Cycles bake of a weathered
    base colour + ORM), its materials and helpers (frame_along, beam, strut, stencil), its truck / forklift / worker /
    bollard parts (placed from assets/parts-yard as 'yard:<part>');
  - spaceport_kit.py (spaceport): the square lattice truss (ported to this builder), the light-paint / dark-accent
    palette;
  - the fleet procedural kit (assets/parts-blender): every human-scale ruler is placed, never re-modelled: crew door
    1.4 x 2.4 m (1 x 2 m leaf), floodlight, ISO container, vent, pane, antenna, dome.

FRAME (every colony building): metres, +Y up, the plinth top at y = 0 (planetside) or the ring centre at the origin
(orbital), +Z the building's front, +X its left (as the yard frame). The concept camera looks from the front-left
(azimuth ~35 deg, ~30-35 deg down), so the +Z and +X faces carry the most detail.

How a building script uses it (README-colony.md has the full recipe):

    import bkit as K
    SPEC = {...}                       # footprint, height, camera, notes
    def model(B):                      # B = K.Build(id)
        K.plinth(B, 110, 80)
        K.block(B, (-30, 0, 20), (14, 7, 9), sides={'+z': {'doors': [3.0]}, '+x': {'windows': [0]}})
        K.sphere_tank(B, (0, 0, 0), r=12, legs=8, band='cobalt')
        K.pipe(B, [(..), (..)], r=0.6)
    # tools/blender/buildings/colony_build.py <id> <work> bakes, places the kit parts, assembles, writes the GLB,
    # the lite copy and the generated light block of src/buildings/<id>.js

Builder: B.box / B.cyl / B.tube / B.lathe / B.prism / B.loft add primitives; primitives with the same (material,
bevel) are merged into one bmesh as they are added (a building has thousands of boxes; one Blender object per
primitive made finish() slow), then B.part() hands lib.Part one object per batch for bevel + weighted normals + join.
B.at(M=...) / B.at(at=, rot=) is the transform stack. B.R is the Rec: lights and kit placements, building frame.

Materials (linear base colour, bake kind, roughness, metal) are added to lib.MATS: the concept's off-white panels
('panel', 'panel2'), dark gunmetal frames, posts and bands ('frame', 'frame2'), concrete ('concrete', 'concrete2',
'kerb'), pipe metal ('pipe', 'pipeDark'), cobalt and violet accent bands, roof grey, grating, glass, refractory,
foliage. The bake (lib.material graphs) adds panel-to-panel tone, AO grime under edges, vertical run-off streaks and
convex edge wear: "worn, not dirty" (STYLE.md Materials). BAKE is retuned for building scale on import.
"""
import math
import os
import sys
from contextlib import contextmanager

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import lib  # noqa: E402
import yard_kit as YK  # noqa: E402  (adds the yard materials: charcoal, cladding, amber, concrete, galv, white)
from lib import chamfer_rect, circle  # noqa: E402

V = Vector
DEG = math.pi / 180
ROOT = YK.ROOT

# ------------------------------------------------------------------------------------------------------------------
# materials (linear RGB). Calibrated on the concepts: panels sRGB ~200-205 (linear ~0.6), frames sRGB ~50-60
# (linear ~0.035-0.045), plinth concrete sRGB ~150 (linear ~0.3), cobalt band sRGB (60, 112, 170).
# ------------------------------------------------------------------------------------------------------------------
BKIT_MATS = {
    'panel':     ((0.60, 0.60, 0.585), 'paint', 0.62, 0.0),   # off-white cladding panels (light concept paint, corr. 27)
    'panel2':    ((0.47, 0.47, 0.46), 'paint', 0.66, 0.0),    # recessed / secondary panels, a step darker
    'frame':     ((0.040, 0.042, 0.046), 'paint', 0.55, 0.0),  # dark gunmetal frames, posts, beams, bands
    'frame2':    ((0.075, 0.078, 0.082), 'paint', 0.6, 0.0),   # its lighter variant (housings, legs)
    'seam':      ((0.016, 0.017, 0.018), 'paint', 0.8, 0.0),   # panel seams, slab joints (near black)
    'concrete':  ((0.30, 0.295, 0.28), 'paint', 0.9, 0.0),     # plinth top: light concrete
    'concrete2': ((0.20, 0.197, 0.19), 'paint', 0.9, 0.0),     # plinth sides, footings
    'kerb':      ((0.40, 0.395, 0.38), 'paint', 0.88, 0.0),    # kerb and edge band (the light rim of the slab)
    'roof':      ((0.16, 0.162, 0.165), 'paint', 0.8, 0.0),    # roof membrane / deck
    'pipe':      ((0.36, 0.365, 0.37), 'metal', 0.42, 0.55),   # bare-ish pipe metal (light steel)
    'pipeDark':  ((0.10, 0.104, 0.11), 'metal', 0.45, 0.6),    # dark pipe / valve bodies
    'grate':     ((0.030, 0.031, 0.033), 'metal', 0.6, 0.5),   # grating, catwalk decks
    'cobalt':    ((0.045, 0.15, 0.40), 'paint', 0.55, 0.0),    # small cobalt bands (STYLE.md Palette)
    'violet':    ((0.16, 0.07, 0.40), 'paint', 0.55, 0.0),     # silicon accent strips
    'refractory': ((0.13, 0.06, 0.03), 'paint', 0.85, 0.0),    # brick-brown refractory, hot zones
    'soot':      ((0.022, 0.021, 0.02), 'paint', 0.9, 0.0),    # burnt stack tops, pour pit
    'foliage':   ((0.035, 0.07, 0.025), 'paint', 0.9, 0.0),
    'soil':      ((0.045, 0.034, 0.025), 'paint', 0.95, 0.0),
    'bark':      ((0.05, 0.035, 0.022), 'paint', 0.9, 0.0),
    'glassW':    ((0.020, 0.024, 0.030), 'glass', 0.08, 0.0),  # window glass (lit ones get a runtime glow box)
    'interior':  ((0.012, 0.012, 0.013), 'paint', 0.95, 0.0),  # dark interiors behind open bays
}
lib.MATS.update(BKIT_MATS)
# bake tuning for building scale (lib.BAKE is the ship kit's: 0.35 m AO, 1.6 m panels): AO grime reaches 1.2 m under
# ledges and into corners; panel tone cells 3 x 1.8 x 3 m (one cladding panel); curvature over 4 cm
# grime: full only in real corners (AO < 0.45), gone by AO 0.88, at 0.6 strength: proud frames round a panel must not
# grey the whole wall (r1 of the depot read black)
lib.BAKE.update({'ao': 1.2, 'curv': 0.04, 'panel': (3.0, 1.8, 3.0), 'grime': (0.45, 0.88, 0.6)})

AMBER = 'amber'


# ------------------------------------------------------------------------------------------------------------------
# small vector helpers
# ------------------------------------------------------------------------------------------------------------------
def vv(p):
    return V((float(p[0]), float(p[1]), float(p[2])))


def lst(p, nd=3):
    return [round(float(c), nd) for c in p]


def frame_along(p0, p1, up=(0, 1, 0)):
    return YK.frame_along(p0, p1, up)


def face_basis(o, u, up=(0, 1, 0)):
    """4x4 for a face: local x along u, y along up, z = u x up = outward normal; origin o."""
    u = vv(u).normalized()
    up = vv(up).normalized()
    n = u.cross(up).normalized()
    return lib.basis(o, u, up, n)


# ------------------------------------------------------------------------------------------------------------------
# Rec: everything that is not baked: lights (lightscape pins / slits / windows / glow / floods), red obstruction
# lights, kit-part placements (assemble.py spec format). Building frame.
# ------------------------------------------------------------------------------------------------------------------
class Rec:
    def __init__(self):
        self.pins, self.beacons, self.nav, self.slits = [], [], [], []
        self.windows, self.glow, self.floods, self.lenses, self.rings = [], [], [], [], []
        self.placements = []
        self.seed = 7
        self.notes = []

    def rnd(self):
        self.seed = (self.seed * 1103515245 + 12345) & 0x7fffffff
        return self.seed / 0x7fffffff

    # lights ---------------------------------------------------------------------------------------------------
    def pin(self, p):
        """0.3 m amber pin lamp (block corners, plinth edges, legs)."""
        self.pins.append(lst(p))

    def beacon(self, p):
        """0.3 m slow amber beacon (2-4 per building, clear of antennas)."""
        self.beacons.append(lst(p))

    def obstruction(self, p):
        """0.4 m red obstruction light on a stack or mast top (the only lights[] entries)."""
        self.nav.append(lst(p))

    def slit(self, p, u, n, length=1.2, width=0.18):
        """Amber corner / recess slit 0.6-1.8 x 0.14-0.2 m (STYLE.md Lights)."""
        self.slits.append({'p': lst(p), 'u': lst(u), 'n': lst(n), 'len': length, 'width': width, 'door': False})

    def door_lamp(self, p, u, n):
        """0.6 x 0.14 m amber door lamp over a crew door (the human ruler)."""
        self.slits.append({'p': lst(p), 'u': lst(u), 'n': lst(n), 'len': 0.6, 'width': 0.14, 'door': True})

    def window(self, p, n, w, h, lit=None, office=False):
        """A lit window: a warm glow box over real glass (centre p, face normal n). lit=None: ~55 % lit."""
        if lit is None:
            lit = self.rnd() < 0.55
        if lit:
            self.windows.append({'p': lst(p), 'n': lst(n), 'size': [round(w, 3), round(h, 3)], **({'office': True} if office else {})})

    def glowbox(self, p, size, color='#ffb766', radiance=0.42, roty=0.0):
        """Warm interior glow (open bays, atria, the pour) as an unlit box (glbship fixtures)."""
        self.glow.append({'p': lst(p), 'size': lst(size), 'color': color, 'radiance': radiance, **({'rotY': round(roty, 4)} if roty else {})})

    def flood(self, p, target, n=None, lamp=True):
        """A work flood: a fleet-kit floodlight (if lamp) at p aimed at target, its lit lens and one spot light."""
        self.floods.append({'p': lst(p), 'target': lst(target)})
        d = (vv(target) - vv(p)).normalized()
        self.lenses.append(lst(vv(p) + d * 0.25))
        if lamp:
            nn = vv(n) if n is not None else V((0, 1, 0))
            yaw = math.degrees(math.atan2(d.x, d.z))
            self.place('floodlight', p, n=nn, up=(0, 0, 1) if abs(nn.y) > 0.9 else (0, 1, 0), rot=yaw if abs(nn.y) > 0.9 else 0,
                       id='flood')

    # kit placements ---------------------------------------------------------------------------------------------
    def place(self, part, p, n=(0, 1, 0), up=(0, 0, 1), along=None, rot=0.0, scale=None, id=None, **kw):
        q = {'part': part, 'p': lst(p), 'n': lst(n), 'up': lst(up), 'snap': False, 'seat': {'check': False}}
        if along is not None:
            q['along'] = lst(along)
        if rot:
            q['rot'] = round(rot, 2)
        if scale is not None:
            q['scale'] = scale
        if id:
            q['id'] = id
        q.update(kw)
        self.placements.append(q)

    def door(self, p, n, u=None, lamp=True, canopy=None):
        """Fleet-kit crew door (1 x 2 m leaf in a 1.4 x 2.4 m frame) standing on p (base centre, on the wall face),
        facing n; its 0.6 x 0.14 m amber lamp above. Returns nothing; the frame is the kit part's."""
        p, n = vv(p), vv(n).normalized()
        self.place('door', p + V((0, 1.2, 0)) + n * 0.005, n=n, up=(0, 1, 0), id='crew door')
        if lamp:
            uu = vv(u) if u is not None else V((0, 1, 0)).cross(n)
            self.door_lamp(p + V((0, 2.72, 0)) + n * 0.1, uu, n)

    def light_data(self):
        return {'pins': self.pins, 'beacons': self.beacons, 'nav': self.nav, 'slits': self.slits, 'windows': self.windows,
                'glow': self.glow, 'floods': self.floods, 'lenses': self.lenses}


# ------------------------------------------------------------------------------------------------------------------
# Build: batched primitive accumulator over lib.Part
# ------------------------------------------------------------------------------------------------------------------
def _append(dst, src, M):
    src.verts.index_update()
    neg = M.determinant() < 0
    vm = [dst.verts.new(M @ v.co) for v in src.verts]
    for f in src.faces:
        vs = [vm[v.index] for v in f.verts]
        if neg:
            vs.reverse()
        try:
            dst.faces.new(vs)
        except ValueError:
            pass
    src.free()


class Build:
    def __init__(self, name):
        self.name = name
        self.R = Rec()
        self.stack = [Matrix.Identity(4)]
        self.batches = {}   # (mat, bevel, sharp) -> bmesh
        self.counts = {}

    @property
    def M(self):
        return self.stack[-1]

    @contextmanager
    def at(self, at=(0, 0, 0), rot=(0, 0, 0), scale=None, M=None):
        self.stack.append(self.M @ (M if M is not None else lib.mat_xf(at, rot, scale)))
        try:
            yield self
        finally:
            self.stack.pop()

    def world(self, p):
        """A local point in the building frame (for lights and placements made under a transform)."""
        return self.M @ vv(p)

    def wdir(self, d):
        return (self.M.to_3x3() @ vv(d)).normalized()

    def add(self, bm, at=(0, 0, 0), rot=(0, 0, 0), mat='panel', bevel=0.03, sharp=35, scale=None):
        key = (mat, round(bevel, 4), sharp)
        dst = self.batches.get(key)
        if dst is None:
            dst = self.batches[key] = bmesh.new()
        _append(dst, bm, self.M @ lib.mat_xf(at, rot, scale))
        self.counts[mat] = self.counts.get(mat, 0) + 1

    # primitives -----------------------------------------------------------------------------------------------
    def box(self, size, at=(0, 0, 0), rot=(0, 0, 0), mat='panel', bevel=None, **kw):
        if bevel is None:
            bevel = min(0.04, min(size) * 0.2)
        self.add(lib.bm_box(*size), at, rot, mat, bevel, **kw)

    def boxp(self, p0, p1, mat='panel', bevel=None, **kw):
        """Axis-aligned box between two corners."""
        c = [(a + b) / 2 for a, b in zip(p0, p1)]
        s = [max(1e-3, abs(b - a)) for a, b in zip(p0, p1)]
        self.box(s, at=c, mat=mat, bevel=bevel, **kw)

    def cyl(self, r, h, at=(0, 0, 0), rot=(0, 0, 0), mat='panel', n=16, r2=None, caps=True, bevel=None, **kw):
        """Cylinder along its local Z (rot=(90,0,0) stands it on Y), centred on at."""
        if bevel is None:
            bevel = min(0.03, r * 0.15, h * 0.15)
        self.add(lib.bm_cyl(r, h, n, r2, caps), at, rot, mat, bevel, **kw)

    def vcyl(self, r, h, base, mat='panel', n=16, r2=None, bevel=None, caps=True, **kw):
        """Vertical cylinder standing on base (x, y, z)."""
        self.cyl(r, h, at=(base[0], base[1] + h / 2, base[2]), rot=(-90, 0, 0), mat=mat, n=n, r2=r2, bevel=bevel, caps=caps, **kw)

    def rod(self, p0, p1, r, mat='frame', n=8, bevel=0.0, caps=True):
        """Round bar / pipe between two points."""
        p0, p1 = vv(p0), vv(p1)
        L = (p1 - p0).length
        if L < 1e-4:
            return
        with self.at(M=frame_along(p0, p1)):
            self.cyl(r, L, at=(0, 0, L / 2), mat=mat, n=n, bevel=bevel, caps=caps)

    def bar(self, p0, p1, w, h=None, mat='frame', up=(0, 1, 0), bevel=0.02, ext=0.0):
        """Box beam p0 -> p1, section w x h (h toward up)."""
        h = w if h is None else h
        p0, p1 = vv(p0), vv(p1)
        L = (p1 - p0).length + 2 * ext
        if L < 1e-4:
            return
        d = (p1 - p0).normalized()
        u = vv(up)
        if abs(d.dot(u.normalized())) > 0.99:
            u = V((1, 0, 0)) if abs(d.x) < 0.9 else V((0, 0, 1))
        with self.at(M=frame_along(p0, p1, u)):
            self.box((w, h, L), at=(0, 0, L / 2 - ext), mat=mat, bevel=min(bevel, w * 0.2, h * 0.2))

    def strut(self, p0, p1, s0, s1, ch, mat='frame2', up=(0, 1, 0), bevel=0.05):
        """Tapered chamfered-rectangle strut (yard_kit.strut)."""
        p0, p1 = vv(p0), vv(p1)
        L = (p1 - p0).length
        with self.at(M=frame_along(p0, p1, up)):
            self.add(lib.bm_loft([(chamfer_rect(s0[0], s0[1], ch), 0.0), (chamfer_rect(s1[0], s1[1], ch), L)], closed=False), mat=mat, bevel=bevel)

    def tube(self, path, r, mat='pipe', n=12, fillet=None, caps=True, bevel=0.0):
        p = lib.fillet_path([vv(q) for q in path], r * 2.2 if fillet is None else fillet, 4) if len(path) > 2 else [vv(q) for q in path]
        self.add(lib.bm_tube(p, r, n, caps), mat=mat, bevel=bevel, sharp=60)

    def lathe(self, prof, base=(0, 0, 0), mat='panel', n=32, closed=False, bevel=0.0, a0=0.0, a1=None, sharp=40):
        """Surface of revolution about the vertical axis through base: prof [(r, y)]."""
        self.add(lib.bm_lathe(prof, n, closed, a0=a0, a1=a1), at=base, rot=(-90, 0, 0), mat=mat, bevel=bevel, sharp=sharp)

    def ring(self, r_out, r_in, y0, y1, base=(0, 0, 0), mat='cobalt', n=32):
        """Annulus band (no caps: lesson 'a closed end cap hides a recessed plate')."""
        self.lathe([(r_in, y0), (r_out, y0), (r_out, y1), (r_in, y1)], base, mat, n, closed=True, sharp=30)

    def prism(self, pts, y0, y1, mat='panel', bevel=None):
        """Plan outline (x, z) [CCW seen from above] extruded from y0 to y1."""
        if bevel is None:
            bevel = min(0.05, abs(y1 - y0) * 0.2)
        # lib.bm_prism extrudes along Z: author (x, -z) in XY and rotate -90 about X (Z -> Y, Y -> -Z)
        self.add(lib.bm_prism([(x, -z) for x, z in pts], y0, y1), rot=(-90, 0, 0), mat=mat, bevel=bevel)

    def loft(self, rings, mat='panel', closed=False, bevel=0.02):
        """Vertical loft: rings [(plan pts [(x, z)], y)], same point count."""
        self.add(lib.bm_loft([([(x, -z) for x, z in pts], y) for pts, y in rings], closed), rot=(-90, 0, 0), mat=mat, bevel=bevel)

    def sphere(self, r, c, mat='panel', n=32, rings=16, y0=None, y1=None):
        """UV sphere (or a band of it between heights y0..y1 relative to c) as a lathe."""
        prof = []
        for k in range(rings + 1):
            a = -math.pi / 2 + math.pi * k / rings
            y = r * math.sin(a)
            if (y0 is not None and y < y0 - 1e-6) or (y1 is not None and y > y1 + 1e-6):
                continue
            prof.append((max(0.0, r * math.cos(a)), y))
        self.lathe(prof, c, mat, n, sharp=50)

    # ---------------------------------------------------------------------------------------------------------
    def part(self):
        """Hand the batches to a lib.Part (bevel + weighted normals per batch, join). Returns the joined object."""
        P = lib.Part(self.name)
        for (mat, bevel, sharp), bm in self.batches.items():
            P.mesh(bm, mat=mat, bevel=bevel, sharp=sharp)
        self.batches = {}
        return P


# ------------------------------------------------------------------------------------------------------------------
# lattice (spaceport_kit.truss, ported): square truss between two points, chords + rings + diagonals
# ------------------------------------------------------------------------------------------------------------------
def truss(B, p0, p1, w, bay=None, chord=0.25, web=0.12, mat='frame', up=(0, 1, 0), diag=True):
    p0, p1 = vv(p0), vv(p1)
    L = (p1 - p0).length
    bay = bay or w
    nb = max(1, int(round(L / bay)))
    with B.at(M=frame_along(p0, p1, up)):
        cs = [(-w / 2, -w / 2), (w / 2, -w / 2), (w / 2, w / 2), (-w / 2, w / 2)]
        for x, y in cs:
            B.box((chord, chord, L), at=(x, y, L / 2), mat=mat, bevel=0.02)
        for i in range(nb + 1):
            z = L * i / nb
            for k in range(4):
                a, b = cs[k], cs[(k + 1) % 4]
                B.bar((a[0], a[1], z), (b[0], b[1], z), web, mat=mat, bevel=0.0)
            if diag and i < nb:
                z2 = L * (i + 1) / nb
                for k in range(4):
                    a, b = cs[k], cs[(k + 1) % 4]
                    if i % 2:
                        a, b = b, a
                    B.bar((a[0], a[1], z), (b[0], b[1], z2), web, mat=mat, bevel=0.0)


def lattice_tower(B, c, w, h, bay=4.0, chord=0.35, web=0.15, mat='frame', taper=0.0):
    """Four-post lattice tower on a square plan (w), base c = (x, y, z), height h; taper shrinks the top."""
    x, y, z = c
    wt = w * (1 - taper)
    nb = max(1, int(round(h / bay)))
    corners = lambda s, yy: [(x - s / 2, yy, z - s / 2), (x + s / 2, yy, z - s / 2), (x + s / 2, yy, z + s / 2), (x - s / 2, yy, z + s / 2)]
    for k in range(4):
        B.bar(corners(w, y)[k], corners(wt, y + h)[k], chord, mat=mat, bevel=0.03)
    for i in range(nb + 1):
        t = i / nb
        s = w + (wt - w) * t
        ring_pts = corners(s, y + h * t)
        for k in range(4):
            B.bar(ring_pts[k], ring_pts[(k + 1) % 4], web, mat=mat, bevel=0.0)
        if i < nb:
            s2 = w + (wt - w) * (i + 1) / nb
            nxt = corners(s2, y + h * (i + 1) / nb)
            for k in range(4):
                a, b = (ring_pts[k], nxt[(k + 1) % 4]) if i % 2 == 0 else (ring_pts[(k + 1) % 4], nxt[k])
                B.bar(a, b, web, mat=mat, bevel=0.0)


# ------------------------------------------------------------------------------------------------------------------
# railings, catwalks, stairs, ladders (fleet rulers: rail 1.1 m, ladder 0.62 m wide with 0.3 m rungs, tread 0.18 rise)
# ------------------------------------------------------------------------------------------------------------------
def railing(B, pts, h=1.1, post=1.5, mat='frame', mid=True, closed=False):
    P = [vv(p) for p in pts] + ([vv(pts[0])] if closed else [])
    for a, b in zip(P[:-1], P[1:]):
        L = (b - a).length
        if L < 1e-3:
            continue
        n = max(1, int(math.ceil(L / post)))
        for i in range(n + (0 if closed else 1)):
            q = a + (b - a) * (i / n)
            B.box((0.06, h, 0.06), at=(q.x, q.y + h / 2, q.z), mat=mat, bevel=0.0)
        up = V((0, h, 0))
        B.bar(a + up, b + up, 0.06, mat=mat, bevel=0.0)
        if mid:
            B.bar(a + up * 0.5, b + up * 0.5, 0.04, mat=mat, bevel=0.0)


def catwalk(B, p0, p1, w=1.0, rails=(True, True), mat='grate', rail_mat='frame', t=0.12):
    """Grating walkway p0 -> p1 (centreline at deck level), side rails."""
    p0, p1 = vv(p0), vv(p1)
    d = (p1 - p0)
    d.y = 0
    L = d.length
    if L < 1e-3:
        return
    d.normalize()
    s = V((0, 1, 0)).cross(d).normalized()
    with B.at(M=frame_along(p0, p1)):
        B.box((w, t, (p1 - p0).length), at=(0, -t / 2, (p1 - p0).length / 2), mat=mat, bevel=0.0)
        B.box((0.08, 0.18, (p1 - p0).length), at=(w / 2, -0.09, (p1 - p0).length / 2), mat=rail_mat, bevel=0.0)
        B.box((0.08, 0.18, (p1 - p0).length), at=(-w / 2, -0.09, (p1 - p0).length / 2), mat=rail_mat, bevel=0.0)
    for side, on in zip((1, -1), rails):
        if on:
            railing(B, [p0 + s * side * w / 2, p1 + s * side * w / 2], mat=rail_mat)


def platform_ring(B, c, y, r_in, r_out, mat='grate', rail=True, n=24, brackets=6):
    """Circular grating platform round a vertical vessel (centre c = (x, z)), railing on the outer edge."""
    x, z = c
    B.ring(r_out, r_in, y - 0.1, y, base=(x, 0, z), mat=mat, n=n)
    if rail:
        pts = [(x + r_out * math.cos(2 * math.pi * k / n), y, z + r_out * math.sin(2 * math.pi * k / n)) for k in range(n)]
        railing(B, pts, post=2.0, closed=True, mid=True)
    for k in range(brackets):
        a = 2 * math.pi * (k + 0.5) / brackets
        B.bar((x + r_in * math.cos(a), y - 1.2, z + r_in * math.sin(a)), (x + r_out * math.cos(a), y - 0.12, z + r_out * math.sin(a)), 0.12, mat='frame', bevel=0.0)


def stair(B, base, d, rise, w=1.0, mat='frame', tread='grate', rails=True):
    """Straight stair from base (bottom of the first tread line) along horizontal d, rising `rise` m
    (0.18 m rise, 0.28 m going per step)."""
    base, d = vv(base), vv(d)
    d.y = 0
    d.normalize()
    s = V((0, 1, 0)).cross(d).normalized()
    n = max(1, int(round(rise / 0.18)))
    rs, go = rise / n, 0.28
    top = base + d * (go * n) + V((0, rise, 0))
    for side in (1, -1):
        B.bar(base + s * side * w / 2 + V((0, -0.15, 0)), top + s * side * w / 2 + V((0, -0.15, 0)), 0.08, 0.3, mat=mat, bevel=0.0)
    for i in range(n):
        q = base + d * (go * (i + 0.5)) + V((0, rs * (i + 1) - 0.03, 0))
        with B.at(M=lib.basis(q, s, (0, 1, 0), d)):
            B.box((w, 0.05, go), mat=tread, bevel=0.0)
    if rails:
        for side in (1, -1):
            railing(B, [base + s * side * w / 2, top + s * side * w / 2], post=1.2, mid=False)
    return top


def ladder(B, p, n, h, cage=True, w=0.62, mat='frame'):
    """Wall ladder: foot at p (on the face), face normal n, height h; rungs every 0.3 m, a safety cage above 2.5 m."""
    p, n = vv(p), vv(n).normalized()
    s = V((0, 1, 0)).cross(n).normalized()
    off = n * 0.2
    for side in (1, -1):
        B.bar(p + off + s * side * w / 2, p + off + s * side * w / 2 + V((0, h + 1.0, 0)), 0.06, mat=mat, bevel=0.0)
    k = int(h / 0.3)
    for i in range(1, k + 1):
        q = p + off + V((0, i * 0.3, 0))
        B.bar(q - s * w / 2, q + s * w / 2, 0.03, mat=mat, bevel=0.0)
    if cage and h > 3.0:
        y = 2.5
        while y <= h + 0.9:
            pts = []
            for j in range(7):
                a = math.pi * j / 6
                pts.append(p + off + n * (0.35 + 0.35 * math.sin(a)) + s * (0.4 * math.cos(a)) + V((0, y, 0)))
            for a, b in zip(pts[:-1], pts[1:]):
                B.bar(a, b, 0.04, mat=mat, bevel=0.0)
            y += 1.2
        for j in (1, 3, 5):
            a = math.pi * j / 6
            q = p + off + n * (0.35 + 0.35 * math.sin(a)) + s * (0.4 * math.cos(a))
            B.bar(q + V((0, 2.5, 0)), q + V((0, h + 0.9, 0)), 0.04, mat=mat, bevel=0.0)


# ------------------------------------------------------------------------------------------------------------------
# plinth: the chamfered concrete slab every planetside building stands on (brief checklist item 1)
# ------------------------------------------------------------------------------------------------------------------
def plinth(B, w, d, h=1.4, chamfer=2.0, kerb=0.5, slab=8.0, lamp_pitch=18.0, centre=(0, 0), markings=None,
           grates=(), lamps=True, steps=()):
    """Slab w (x) by d (z) with chamfered plan corners, top at y = 0, `h` deep: a light kerb band round the top edge,
    a darker skirt, slab joints every `slab` m, amber edge lamps (corners + every lamp_pitch m along the front and
    left edges, R.pin), optional markings [(polyline [(x, z)...], width, mat)] and drain grates [(x, z, w, d)].
    steps: [(x, z, side)] short access stairs down the slab edge (side '+z' / '-z' / '+x' / '-x')."""
    cx, cz = centre
    out = [(cx + x, cz + z) for x, z in chamfer_rect(w, d, chamfer)]
    # body (side faces) and a 0.3 m lighter kerb cap round the top edge, top surface
    B.prism(out, -h, -0.32, mat='concrete2', bevel=0.06)
    B.prism(out, -0.36, -0.02, mat='kerb', bevel=0.05)
    inner = [(cx + x, cz + z) for x, z in chamfer_rect(w - 2 * kerb, d - 2 * kerb, max(0.2, chamfer - kerb * 0.6))]
    B.prism(inner, -0.06, 0.0, mat='concrete', bevel=0.0)
    # skirt shadow line half-way down and a dark toe
    B.prism([(cx + x, cz + z) for x, z in chamfer_rect(w + 0.16, d + 0.16, chamfer + 0.06)], -h * 0.62, -h * 0.55, mat='seam', bevel=0.0)
    B.prism([(cx + x, cz + z) for x, z in chamfer_rect(w + 0.1, d + 0.1, chamfer + 0.04)], -h - 0.02, -h + 0.18, mat='frame2', bevel=0.0)
    # slab joints (dark grooves) across the top
    iw, idd = w - 2 * kerb, d - 2 * kerb
    nx, nz = max(1, int(round(iw / slab))), max(1, int(round(idd / slab)))
    for i in range(1, nx):
        x = cx - iw / 2 + iw * i / nx
        B.box((0.09, 0.012, idd - 0.4), at=(x, 0.002, cz), mat='seam', bevel=0.0)
    for j in range(1, nz):
        z = cz - idd / 2 + idd * j / nz
        B.box((iw - 0.4, 0.012, 0.09), at=(cx, 0.002, z), mat='seam', bevel=0.0)
    # kerb joint between kerb and top
    for (a, b) in zip(inner, inner[1:] + inner[:1]):
        B.bar((a[0], 0.0, a[1]), (b[0], 0.0, b[1]), 0.07, 0.012, mat='seam', bevel=0.0)
    for poly, wid, mat in (markings or []):
        for a, b in zip(poly[:-1], poly[1:]):
            B.bar((cx + a[0], 0.006, cz + a[1]), (cx + b[0], 0.006, cz + b[1]), wid, 0.012, mat=mat, bevel=0.0, ext=wid / 2)
    for (x, z, gw, gd) in grates:
        B.box((gw, 0.02, gd), at=(cx + x, 0.004, cz + z), mat='frame', bevel=0.0)
        for k in range(int(gw / 0.12)):
            B.box((0.04, 0.03, gd - 0.1), at=(cx + x - gw / 2 + 0.06 + k * 0.12, 0.01, cz + z), mat='grate', bevel=0.0)
    for (x, z, side) in steps:
        sgn = 1 if side[0] == '+' else -1
        ax = side[1]
        dvec = (0, 0, -sgn) if ax == 'z' else (-sgn, 0, 0)
        base = (cx + x + (sgn * 3.0 if ax == 'x' else 0), -h, cz + z + (sgn * 3.0 if ax == 'z' else 0))
        stair(B, base, dvec, h, w=1.6, rails=True)
    if lamps:
        # amber lamps set into the kerb face at the corners and along the edges (pins, 0.3 m), facing out
        y = -0.2
        pts = []
        hw, hd = w / 2 + 0.05, d / 2 + 0.05
        for sx in (-1, 1):
            for sz in (-1, 1):
                pts.append((cx + sx * (hw - chamfer * 0.5), y, cz + sz * (hd - 0.02)))
                pts.append((cx + sx * (hw - 0.02), y, cz + sz * (hd - chamfer * 0.5)))
        if lamp_pitch:
            for i in range(1, int(w / lamp_pitch)):
                x = cx - w / 2 + w * i / int(w / lamp_pitch)
                pts.append((x, y, cz + hd))
            for i in range(1, int(d / lamp_pitch)):
                z = cz - d / 2 + d * i / int(d / lamp_pitch)
                pts.append((cx + hw, y, z))
        for p in pts:
            B.box((0.34, 0.16, 0.34), at=p, mat='frame', bevel=0.02)
            B.R.pin((p[0], p[1] + 0.03, p[2]))


def bollards(B, pts, h=1.0, r=0.1, mat=AMBER):
    """Short amber traffic bollards (the small yellow posts round pump houses in the concept)."""
    for x, z in pts:
        B.vcyl(r, h, (x, 0, z), mat=mat, n=8, bevel=0.0)
        B.vcyl(r * 1.05, 0.12, (x, h * 0.72, z), mat='frame', n=8, bevel=0.0)


# ------------------------------------------------------------------------------------------------------------------
# facades and blocks: off-white panels in dark gunmetal frames, corner posts, bands, recessed warm windows, kit doors
# ------------------------------------------------------------------------------------------------------------------
def facade(B, o, u, w, h, bay=4.5, storey=3.6, base=1.0, windows=(), win=(1.6, 1.4), win_per_bay=1, sill=1.0,
           doors=(), rollers=(), skip=(), pilasters=True, seams=True, bands=True, lit=0.55, louvres=(), panel='panel',
           slots=(), lamps=True, frame='frame'):
    """One wall face. o: bottom-left corner on the wall surface (seen from outside), u: unit horizontal to the right;
    the outward normal is u x up. Local x in [0, w], y in [0, h], z outward.
      windows   storey indices that carry windows (0 = ground floor), one or `win_per_bay` per bay
      doors     local x of crew doors (fleet kit door + 0.6 m lamp; a small canopy over it)
      rollers   [(x, width, height)] roller doors: ribbed shutter in a dark portal frame, amber jamb slits
      skip      bay indices without windows
      louvres   [(x, y, w, h)] dark louvre panels
      slots     [(x, y, w, h)] tall glazed slots (glass, lit)
    Returns the list of bay x positions."""
    M = face_basis(o, u)
    n = (M.to_3x3() @ V((0, 0, 1))).normalized()
    uu = vv(u).normalized()
    nb = max(1, int(round(w / bay)))
    bw = w / nb
    xs = [bw * i for i in range(nb + 1)]

    def W(x, y, z=0.0):
        return M @ V((x, y, z))

    with B.at(M=M):
        # dark base band and parapet cap, storey bands
        if base:
            B.box((w + 0.2, base, 0.22), at=(w / 2, base / 2, 0.06), mat=frame, bevel=0.03)
        if bands:
            y = storey
            while y < h - 1.0:
                B.box((w, 0.28, 0.16), at=(w / 2, y, 0.06), mat=frame, bevel=0.02)
                y += storey
        B.box((w + 0.3, 0.42, 0.32), at=(w / 2, h - 0.2, 0.1), mat=frame, bevel=0.04)
        if pilasters:
            for i, x in enumerate(xs):
                ww = 0.5 if i in (0, nb) else 0.4
                B.box((ww, h - base, 0.32), at=(min(max(x, ww / 2), w - ww / 2), base + (h - base) / 2, 0.12), mat=frame, bevel=0.04)
        if seams:
            for i in range(nb):
                x = xs[i] + bw / 2
                B.box((0.07, h - base - 0.6, 0.03), at=(x, base + (h - base - 0.6) / 2, 0.0), mat='seam', bevel=0.0)
            y = base + storey / 2
            while y < h - 0.8:
                B.box((w - 0.4, 0.06, 0.03), at=(w / 2, y, 0.0), mat='seam', bevel=0.0)
                y += storey
        # windows: recessed look = dark glass flush + proud dark surround and sill
        ww, wh = win
        for s in windows:
            yc = base + s * storey + sill + wh / 2 - (base if s == 0 else 0) * 0.0
            if s == 0:
                yc = max(base + sill * 0.6 + wh / 2, 1.2 + wh / 2)
            if yc + wh / 2 > h - 0.7:
                continue
            for i in range(nb):
                if i in skip:
                    continue
                for k in range(win_per_bay):
                    x = xs[i] + bw * (k + 1) / (win_per_bay + 1)
                    if any(abs(x - dx) < 1.6 for dx in doors) or any(abs(x - rx) < rw / 2 + 1.0 for rx, rw, rh in rollers) and yc < max([rh for _, _, rh in rollers] + [0]) + 0.6:
                        continue
                    B.box((ww, wh, 0.06), at=(x, yc, -0.01), mat='glassW', bevel=0.0)
                    fw = 0.14
                    B.box((ww + 2 * fw, fw, 0.22), at=(x, yc + wh / 2 + fw / 2, 0.08), mat=frame, bevel=0.01)
                    B.box((ww + 2 * fw + 0.16, 0.12, 0.3), at=(x, yc - wh / 2 - 0.06, 0.12), mat=frame, bevel=0.01)
                    for sx in (-1, 1):
                        B.box((fw, wh, 0.22), at=(x + sx * (ww / 2 + fw / 2), yc, 0.08), mat=frame, bevel=0.01)
                    B.R.window(W(x, yc, 0.06), n, ww, wh, lit=None if lit is None else (B.R.rnd() < lit))
        for (x, y, sw, sh) in slots:
            B.box((sw, sh, 0.06), at=(x, y + sh / 2, -0.01), mat='glassW', bevel=0.0)
            for sx in (-1, 1):
                B.box((0.3, sh + 0.3, 0.34), at=(x + sx * (sw / 2 + 0.15), y + sh / 2, 0.12), mat=frame, bevel=0.02)
            B.box((sw + 0.6, 0.3, 0.34), at=(x, y + sh + 0.15, 0.12), mat=frame, bevel=0.02)
            nm = max(1, int(round(sw / 1.2)))
            for k in range(1, nm):
                B.box((0.08, sh, 0.1), at=(x - sw / 2 + sw * k / nm, y + sh / 2, 0.03), mat=frame, bevel=0.0)
            for yy in range(1, int(sh / 1.4)):
                B.box((sw, 0.06, 0.1), at=(x, y + yy * 1.4, 0.03), mat=frame, bevel=0.0)
            B.R.glowbox(W(x, y + sh / 2, -0.02), (sw if abs(n.z) > 0.5 else 0.05, sh, 0.05 if abs(n.z) > 0.5 else sw), color='#ffc27a', radiance=0.9)
        for (x, y, lw, lh) in louvres:
            B.box((lw, lh, 0.08), at=(x, y + lh / 2, 0.02), mat='frame2', bevel=0.0)
            for k in range(int(lh / 0.2)):
                B.box((lw - 0.1, 0.04, 0.12), at=(x, y + 0.1 + k * 0.2, 0.08), mat=frame, bevel=0.0)
        for (x, rw, rh) in rollers:
            B.box((rw, rh, 0.12), at=(x, rh / 2, -0.25), mat='frame2', bevel=0.0)
            for k in range(int(rh / 0.45)):
                B.box((rw - 0.1, 0.07, 0.1), at=(x, 0.25 + k * 0.45, -0.16), mat=frame, bevel=0.0)
            for sx in (-1, 1):
                B.box((0.7, rh + 0.6, 0.5), at=(x + sx * (rw / 2 + 0.35), (rh + 0.6) / 2, 0.15), mat=frame, bevel=0.04)
            B.box((rw + 1.4, 0.7, 0.55), at=(x, rh + 0.35, 0.15), mat=frame, bevel=0.04)
            if lamps:
                for sx in (-1, 1):
                    B.R.slit(W(x + sx * (rw / 2 + 0.35), rh - 0.6, 0.42), (0, 1, 0), n, 1.0, 0.16)
        for x in doors:
            # a shallow canopy; the door itself is the fleet kit's (placed, not modelled)
            B.box((1.9, 0.14, 0.9), at=(x, 2.95, 0.45), mat=frame, bevel=0.02)
    for x in doors:
        B.R.door(W(x, 0.0, 0.0), n, u=uu, lamp=lamps)
    for (x, y, sw, sh) in slots:
        pass
    return [M @ V((x, 0, 0)) for x in xs]


def block(B, c, size, sides=None, roof=None, post=0.6, frame='frame', panel='panel', y0=0.0, corner_lamps=True,
          chamfer=0.0, core=True):
    """Clad box building: c = (x, y0, z) centre of its footprint at its base, size = (w (x), h, d (z)).
    sides: {'+z': facade kwargs, '-z': ..., '+x': ..., '-x': ...}; missing sides get plain panels and bands.
    roof: kwargs for roof_deck (parapet, units). Corner posts in dark gunmetal, amber pins at the top corners."""
    x, y0, z = c
    w, h, d = size
    sides = sides or {}
    if core:
        if chamfer:
            B.prism([(x + a, z + b) for a, b in chamfer_rect(w - 0.2, d - 0.2, chamfer)], y0, y0 + h, mat=panel, bevel=0.06)
        else:
            B.box((w - 0.2, h, d - 0.2), at=(x, y0 + h / 2, z), mat=panel, bevel=0.06)
    hw, hd = w / 2 - 0.1, d / 2 - 0.1
    faces = {
        '+z': ((x - hw, y0, z + hd), (1, 0, 0), w - 0.2),
        '-z': ((x + hw, y0, z - hd), (-1, 0, 0), w - 0.2),
        '+x': ((x + hw, y0, z + hd), (0, 0, -1), d - 0.2),
        '-x': ((x - hw, y0, z - hd), (0, 0, 1), d - 0.2),
    }
    for k, (o, u, L) in faces.items():
        kw = dict(sides.get(k, {}))
        if kw.get('skip_face'):
            continue
        kw.setdefault('frame', frame)
        facade(B, o, u, L, h, **kw)
    # corner posts
    for sx in (-1, 1):
        for sz in (-1, 1):
            B.box((post, h + 0.4, post), at=(x + sx * (hw + 0.05), y0 + (h + 0.4) / 2, z + sz * (hd + 0.05)), mat=frame, bevel=0.05)
            if corner_lamps:
                B.R.pin((x + sx * (hw + 0.05 + post / 2 + 0.02), y0 + h + 0.1, z + sz * (hd + 0.05 + post / 2 + 0.02)))
    roof_deck(B, (x, y0 + h, z), (w, d), **(roof or {}))
    return (x, y0 + h, z)


def roof_deck(B, c, wd, parapet=0.0, units=(), deck=True, mat='roof'):
    """Roof membrane on top of a block (c = centre of the roof at roof level), optional parapet, roof units
    [(kind, x, z, kwargs)] in roof-local offsets (kind: 'hvac' | 'vent' | 'fan' | 'antenna' | 'solar' | 'tank' | 'box')."""
    x, y, z = c
    w, d = wd
    if deck:
        B.box((w - 0.6, 0.12, d - 0.6), at=(x, y + 0.06, z), mat=mat, bevel=0.0)
    if parapet:
        for sx in (-1, 1):
            B.box((0.35, parapet, d), at=(x + sx * (w / 2 - 0.18), y + parapet / 2, z), mat='frame', bevel=0.03)
        for sz in (-1, 1):
            B.box((w, parapet, 0.35), at=(x, y + parapet / 2, z + sz * (d / 2 - 0.18)), mat='frame', bevel=0.03)
    for kind, ux, uz, kw in units:
        p = (x + ux, y + 0.12, z + uz)
        ROOF_UNITS[kind](B, p, **kw)


def hvac(B, p, w=3.0, d=2.0, h=1.3, fans=2, rot=0.0):
    """Packaged roof unit: dark housing on a curb, fan discs on top (the concept's roof boxes)."""
    with B.at(at=p, rot=(0, rot, 0)):
        B.box((w + 0.3, 0.25, d + 0.3), at=(0, 0.125, 0), mat='frame', bevel=0.02)
        B.box((w, h, d), at=(0, 0.25 + h / 2, 0), mat='frame2', bevel=0.05)
        for k in range(fans):
            fx = -w / 2 + w * (k + 0.5) / fans
            B.cyl(min(d, w / fans) * 0.38, 0.12, at=(fx, 0.25 + h + 0.03, 0), rot=(-90, 0, 0), mat='seam', n=14)
            B.cyl(min(d, w / fans) * 0.42, 0.06, at=(fx, 0.25 + h + 0.06, 0), rot=(-90, 0, 0), mat='frame', n=14, caps=False)
        for k in range(int(w / 0.3)):
            B.box((0.04, h * 0.6, 0.05), at=(-w / 2 + 0.15 + k * 0.3, 0.25 + h * 0.5, d / 2 + 0.02), mat='seam', bevel=0.0)


def vent_box(B, p, w=1.2, d=1.2, h=0.9, rot=0.0):
    with B.at(at=p, rot=(0, rot, 0)):
        B.box((w, h, d), at=(0, h / 2, 0), mat='panel2', bevel=0.04)
        B.box((w + 0.25, 0.12, d + 0.25), at=(0, h + 0.06, 0), mat='frame', bevel=0.02)


def fan(B, p, r=0.8, h=0.7):
    B.vcyl(r, h, p, mat='frame2', n=16)
    B.vcyl(r * 0.85, 0.06, (p[0], p[1] + h, p[2]), mat='seam', n=16)


def antenna(B, p, h=6.0, r=0.06):
    """Whip / lattice mast with two dipole yards (no lamp on the tip: lesson 'a lamp on a whip reads as a lamp post')."""
    B.vcyl(0.25, 0.3, p, mat='frame', n=8)
    B.vcyl(r, h, (p[0], p[1] + 0.3, p[2]), mat='frame', n=6, bevel=0.0)
    for f in (0.62, 0.84):
        B.box((1.0, 0.05, 0.05), at=(p[0], p[1] + 0.3 + h * f, p[2]), mat='frame', bevel=0.0)


def solar(B, p, w=6.0, d=3.0, tilt=20.0, rot=0.0):
    with B.at(at=p, rot=(0, rot, 0)):
        for sx in (-1, 1):
            B.box((0.12, 0.8, 0.12), at=(sx * (w / 2 - 0.3), 0.4, 0), mat='frame', bevel=0.0)
        with B.at(at=(0, 0.9, 0), rot=(-tilt, 0, 0)):
            B.box((w, 0.08, d), mat='frame', bevel=0.01)
            B.box((w - 0.2, 0.04, d - 0.2), at=(0, 0.05, 0), mat='glassW', bevel=0.0)
            for k in range(1, int(w / 1.0)):
                B.box((0.03, 0.03, d - 0.2), at=(-w / 2 + k * 1.0, 0.08, 0), mat='frame2', bevel=0.0)


def roof_tank(B, p, r=1.0, h=2.0):
    B.vcyl(r, h, p, mat='panel2', n=16)
    B.vcyl(r * 1.04, 0.15, (p[0], p[1] + h * 0.7, p[2]), mat='frame', n=16)


def roof_box(B, p, w=2.0, d=2.0, h=1.5, mat='frame2'):
    B.box((w, h, d), at=(p[0], p[1] + h / 2, p[2]), mat=mat, bevel=0.04)


ROOF_UNITS = {'hvac': hvac, 'vent': vent_box, 'fan': fan, 'antenna': antenna, 'solar': solar, 'tank': roof_tank, 'box': roof_box}


# ------------------------------------------------------------------------------------------------------------------
# pipes: runs with flanges and amber rings, supports, racks
# ------------------------------------------------------------------------------------------------------------------
def pipe(B, pts, r=0.4, mat='pipe', flanges=True, rings=True, supports=False, ground=0.0, ring_mat=AMBER, n=None,
         fillet=None, support_pitch=7.0):
    """Pipe run along a polyline (filleted elbows of ~2.2 r), flanges (1.3 r, 0.12 r thick) at both ends and
    each straight's middle, amber identification rings beside the flanges, optional T supports on horizontal legs
    down to `ground`."""
    P = [vv(p) for p in pts]
    n = n or (16 if r > 0.5 else 12 if r > 0.2 else 8)
    B.tube(P, r, mat=mat, n=n, fillet=fillet)
    fl = []
    for a, b in zip(P[:-1], P[1:]):
        L = (b - a).length
        d = (b - a).normalized()
        if flanges:
            ends = [a + d * min(L * 0.5, r * 3.2), b - d * min(L * 0.5, r * 3.2)] if L > r * 8 else []
            if L > 14:
                ends.append(a + d * (L / 2))
            for q in ends:
                fl.append((q, d))
        if supports and abs(d.y) < 0.2 and a.y - ground > r * 2:
            k = max(1, int(L / support_pitch))
            for i in range(k):
                q = a + d * (L * (i + 0.5) / k)
                s = V((0, 1, 0)).cross(d).normalized()
                B.bar(V((q.x, ground, q.z)), V((q.x, q.y - r, q.z)), max(0.18, r * 0.5), mat='frame', bevel=0.0)
                B.bar(q - s * r * 1.4 + V((0, -r - 0.08, 0)), q + s * r * 1.4 + V((0, -r - 0.08, 0)), 0.16, mat='frame', bevel=0.0)
                B.box((max(0.5, r * 1.4), 0.25, max(0.5, r * 1.4)), at=(q.x, ground + 0.12, q.z), mat='concrete2', bevel=0.02)
    for i, (q, d) in enumerate(fl):
        with B.at(M=frame_along(q - d * r * 0.06, q + d * r * 0.06)):
            B.cyl(r * 1.3, r * 0.14 + 0.03, at=(0, 0, 0.06), mat='pipeDark', n=n, bevel=0.0)
        if rings and i in (0, len(fl) - 1):
            q2 = q + d * (r * 1.2 + 0.15)
            with B.at(M=frame_along(q2, q2 + d)):
                B.cyl(r * 1.04, min(0.35, r * 0.6), at=(0, 0, 0), mat=ring_mat, n=n, bevel=0.0, caps=False)


def valve(B, p, d, r=0.4):
    """Gate valve on a pipe at p along direction d: body, bonnet and handwheel."""
    p, d = vv(p), vv(d).normalized()
    with B.at(M=frame_along(p - d * r, p + d * r)):
        B.cyl(r * 1.25, r * 1.6, at=(0, 0, r), mat='pipeDark', n=10, bevel=0.0)
    B.vcyl(r * 0.35, r * 2.2, (p.x, p.y + r, p.z), mat='pipeDark', n=8)
    B.cyl(r * 0.9, 0.06, at=(p.x, p.y + r * 3.3, p.z), rot=(-90, 0, 0), mat=AMBER, n=12, caps=False)


def pipe_rack(B, p0, p1, w=4.0, h=5.0, levels=(5.0,), pitch=6.0, pipes=(), mat='frame'):
    """Pipe rack: portal bents every `pitch` m from p0 to p1 (ground points), longitudinal beams, and pipes
    [(level index, lateral offset, r, mat)] carried on it."""
    p0, p1 = vv(p0), vv(p1)
    d = (p1 - p0)
    d.y = 0
    L = d.length
    d.normalize()
    s = V((0, 1, 0)).cross(d).normalized()
    nb = max(1, int(round(L / pitch)))
    for i in range(nb + 1):
        q = p0 + d * (L * i / nb)
        for side in (1, -1):
            B.bar(q + s * side * w / 2, q + s * side * w / 2 + V((0, max(levels) + 0.3, 0)), 0.3, mat=mat, bevel=0.02)
            B.box((0.6, 0.3, 0.6), at=tuple(q + s * side * w / 2 + V((0, 0.15, 0))), mat='concrete2', bevel=0.02)
        for lv in levels:
            B.bar(q - s * (w / 2 + 0.2) + V((0, lv, 0)), q + s * (w / 2 + 0.2) + V((0, lv, 0)), 0.25, 0.3, mat=mat, bevel=0.02)
    for lv in levels:
        for side in (1, -1):
            B.bar(p0 + s * side * w / 2 + V((0, lv, 0)), p1 + s * side * w / 2 + V((0, lv, 0)), 0.2, 0.25, mat=mat, bevel=0.0)
    for li, off, r, m in pipes:
        y = levels[li] + 0.15 + r
        pipe(B, [p0 + s * off + V((0, y, 0)) - d * 1.0, p1 + s * off + V((0, y, 0)) + d * 1.0], r, mat=m, rings=True)


def cable_tray(B, p0, p1, w=0.6, mat='frame'):
    p0, p1 = vv(p0), vv(p1)
    B.bar(p0, p1, w, 0.08, mat=mat, bevel=0.0)
    d = (p1 - p0).normalized()
    s = V((0, 1, 0)).cross(d).normalized()
    for side in (1, -1):
        B.bar(p0 + s * side * w / 2 + V((0, 0.1, 0)), p1 + s * side * w / 2 + V((0, 0.1, 0)), 0.04, 0.2, mat=mat, bevel=0.0)


# ------------------------------------------------------------------------------------------------------------------
# vessels: vertical tanks / columns, spheres on legs, horizontal tanks, stacks
# ------------------------------------------------------------------------------------------------------------------
def vtank(B, c, r, h, y0=0.0, top='dome', bands=(), mat='panel', ladder_side=None, platforms=(), skirt=0.0,
          nozzles=(), seams=True, n=32, cap_mat='frame2', top_unit=True):
    """Vertical vessel at plan centre c = (x, z) from y0: shell r x h, head 'dome' | 'flat' | 'cone', bands
    [(y0, y1, mat)] relative to the base, ladder with cage on side angle `ladder_side` (deg, 0 = +Z), circular
    platforms at heights, a skirt of `skirt` m (dark) under it, nozzles [(y, angle deg, r, length)]."""
    x, z = c
    if skirt:
        B.vcyl(r * 0.98, skirt, (x, y0, z), mat='frame2', n=n)
        B.vcyl(r * 1.08, 0.4, (x, y0, z), mat='concrete2', n=n)
    yb = y0 + skirt
    B.vcyl(r, h, (x, yb, z), mat=mat, n=n, caps=False)
    if top == 'dome':
        prof = [(r * math.cos(a * DEG), r * 0.45 * math.sin(a * DEG)) for a in range(0, 91, 15)]
        B.lathe(prof, (x, yb + h, z), mat=mat, n=n)
        ytop = yb + h + r * 0.45
    elif top == 'cone':
        B.lathe([(r, 0), (r * 0.15, r * 0.35), (0, r * 0.36)], (x, yb + h, z), mat=mat, n=n)
        ytop = yb + h + r * 0.35
    else:
        B.lathe([(r, 0), (r + 0.1, 0), (r + 0.1, 0.3), (0, 0.3)], (x, yb + h, z), mat=cap_mat, n=n)
        ytop = yb + h + 0.3
    B.lathe([(r, 0), (0, 0)], (x, yb, z), mat=mat, n=n)
    for (a, b, m) in bands:
        B.ring(r + 0.06, r - 0.05, yb + a, yb + b, (x, 0, z), mat=m, n=n)
    if seams:
        k = int(h / 2.4)
        for i in range(1, k):
            B.ring(r + 0.025, r - 0.02, yb + i * h / k - 0.03, yb + i * h / k + 0.03, (x, 0, z), mat='seam', n=n)
    for py in platforms:
        platform_ring(B, (x, z), yb + py, r + 0.05, r + 1.3)
    if ladder_side is not None:
        a = ladder_side * DEG
        nn = V((math.sin(a), 0, math.cos(a)))
        ladder(B, V((x, yb, z)) + nn * r, nn, h + (0.0 if top == 'flat' else r * 0.2))
    for (ny, ang, nr, nl) in nozzles:
        a = ang * DEG
        nn = V((math.sin(a), 0, math.cos(a)))
        p0 = V((x, yb + ny, z)) + nn * (r - 0.1)
        B.rod(p0, p0 + nn * nl, nr, mat='pipe', n=10)
        q = p0 + nn * nl
        with B.at(M=frame_along(q - nn * 0.08, q + nn * 0.08)):
            B.cyl(nr * 1.4, 0.16, at=(0, 0, 0.08), mat='pipeDark', n=10, bevel=0.0)
    if top_unit and top != 'flat':
        B.vcyl(r * 0.18, 0.6, (x, ytop - 0.1, z), mat='pipeDark', n=10)
    return ytop


def sphere_tank(B, c, r=12.0, yc=None, legs=8, band='cobalt', band_h=1.4, mat='panel', leg_mat='frame2', seams=True,
                top=True, ladder_angle=200.0, n=40, footing=True):
    """Spherical pressure tank (Horton sphere) on `legs` columns: plan centre c = (x, z), centre height yc (default
    r * 1.6), equator band, latitude seams, legs with X bracing, concrete footings, a top platform with valve
    housing, railing and an amber pin, and a meridian ladder. Returns the top point."""
    x, z = c
    yc = r * 1.6 if yc is None else yc
    B.sphere(r, (x, yc, z), mat=mat, n=n, rings=20)
    if band:
        B.lathe([(r * math.cos(a * DEG) + 0.06, r * math.sin(a * DEG)) for a in (-3.4, -1.7, 0, 1.7, 3.4)], (x, yc, z), mat=band, n=n)
    if seams:
        # plate courses: thin latitude grooves and meridian seams a step darker than the paint (not black lines)
        for lat in (-50, -26, 24, 48, 68):
            a = lat * DEG
            rr, yy = r * math.cos(a), r * math.sin(a)
            B.ring(rr + 0.02, rr - 0.2, yy - 0.03, yy + 0.03, (x, yc, z), mat='panel2', n=n)
        for k in range(16):
            a = 2 * math.pi * (k + 0.25) / 16
            for t0, t1 in ((-48, -27), (25, 47), (49, 67)):
                pts = [V((x + r * 1.002 * math.cos(t * DEG) * math.cos(a), yc + r * 1.002 * math.sin(t * DEG), z + r * 1.002 * math.cos(t * DEG) * math.sin(a))) for t in range(t0, t1 + 1, 7)]
                B.tube(pts, 0.03, mat='panel2', n=4, fillet=0.0, caps=False)
    # legs: heavy tapered box columns from just under the equator, splayed out to concrete footings (the concept's
    # massive legs), a gusset bracket on the shell, a ring tie beam at a third of their height, one diagonal per bay
    feet = []
    for k in range(legs):
        a = 2 * math.pi * (k + 0.5) / legs
        cx_, cz_ = math.cos(a), math.sin(a)
        top_p = V((x + r * 0.9 * cx_, yc - r * 0.28, z + r * 0.9 * cz_))
        foot = V((x + r * 1.13 * cx_, 0.0, z + r * 1.13 * cz_))
        B.strut(foot + V((0, 1.0, 0)), top_p + V((0, 1.2, 0)), (1.7, 1.5), (1.15, 1.05), 0.22, mat=leg_mat, up=(cx_, 0, cz_))
        sh = top_p + V((cx_, 0, cz_)) * 0.35
        B.strut(sh + V((0, -1.8, 0)), sh + V((0, 2.6, 0)) - V((cx_, 0, cz_)) * 0.9, (0.7, 2.2), (0.7, 0.9), 0.12, mat=leg_mat, up=(cx_, 0, cz_))
        if footing:
            B.box((2.8, 1.4, 2.8), at=(foot.x, 0.7, foot.z), mat='concrete2', bevel=0.08)
            B.box((2.1, 0.14, 2.1), at=(foot.x, 1.45, foot.z), mat='frame', bevel=0.02)
        feet.append((foot, top_p))
        B.R.pin((foot.x + cx_ * 1.45, 1.1, foot.z + cz_ * 1.45))
    for k in range(legs):
        (f0, t0), (f1, t1) = feet[k], feet[(k + 1) % legs]
        lerp = lambda f, t, s: f + (t - f) * s
        a0, a1 = lerp(f0, t0, 0.33), lerp(f1, t1, 0.33)
        B.bar(a0, a1, 0.35, 0.45, mat='frame', bevel=0.02)
        B.rod(lerp(f0, t0, 0.36), lerp(f1, t1, 0.85), 0.11, mat='frame', n=6)
    # bottom outlet nozzle
    B.vcyl(r * 0.08, yc - r - 1.6, (x, 1.6, z), mat='pipe', n=10)
    ytop = yc + r
    if top:
        B.vcyl(r * 0.3, 0.5, (x, ytop - 0.35, z), mat='frame2', n=16)
        pr = r * 0.32
        B.ring(pr + 0.9, 0.0, ytop + 0.05, ytop + 0.18, (x, 0, z), mat='grate', n=16)
        railing(B, [(x + (pr + 0.9) * math.cos(2 * math.pi * k / 12), ytop + 0.18, z + (pr + 0.9) * math.sin(2 * math.pi * k / 12)) for k in range(12)], post=1.4, closed=True)
        B.vcyl(r * 0.12, 1.5, (x, ytop + 0.18, z), mat='frame2', n=12)                # valve housing
        B.vcyl(r * 0.07, 0.9, (x + r * 0.15, ytop + 0.18, z - r * 0.1), mat='pipeDark', n=8)
        B.vcyl(r * 0.05, 1.2, (x - r * 0.14, ytop + 0.18, z + r * 0.08), mat='pipeDark', n=8)
        B.R.pin((x, ytop + 1.8, z))
    if ladder_angle is not None:
        a = ladder_angle * DEG
        pts = []
        for t in range(-6, 88, 6):
            tt = t * DEG
            pts.append(V((x + (r + 0.35) * math.cos(tt) * math.cos(a), yc + (r + 0.35) * math.sin(tt), z + (r + 0.35) * math.cos(tt) * math.sin(a))))
        side = V((-math.sin(a), 0, math.cos(a)))
        for sd in (1, -1):
            B.tube([p + side * sd * 0.4 for p in pts], 0.05, mat='frame', n=5, fillet=0.0)
        for p in pts[::1]:
            B.rod(p - side * 0.4, p + side * 0.4, 0.04, mat='frame', n=4)
    return V((x, ytop, z))


def htank(B, c, r, L, axis=(1, 0, 0), saddles=2, mat='panel', band=None, y=None):
    """Horizontal capsule tank on concrete saddles: centre c = (x, z), axis horizontal, centre height y (default
    r + 0.8)."""
    x, z = c
    y = r + 0.8 if y is None else y
    ax = vv(axis).normalized()
    p0 = V((x, y, z)) - ax * (L / 2)
    p1 = V((x, y, z)) + ax * (L / 2)
    with B.at(M=frame_along(p0, p1)):
        B.cyl(r, L, at=(0, 0, L / 2), mat=mat, n=24, caps=False)
        prof = [(r * math.cos(a * DEG), r * 0.5 * math.sin(a * DEG)) for a in range(0, 91, 15)]
        for e, sgn in ((L, 1), (0.0, -1)):
            with B.at(at=(0, 0, e), rot=(0 if sgn > 0 else 180, 0, 0)):
                B.add(lib.bm_lathe(prof, 24), mat=mat, bevel=0.0, sharp=50)
        if band:
            B.add(lib.bm_lathe([(r - 0.05, L * 0.45), (r + 0.06, L * 0.45), (r + 0.06, L * 0.55), (r - 0.05, L * 0.55)], 24, closed=True), mat=band, bevel=0.0)
    s = V((0, 1, 0)).cross(ax).normalized()
    for k in range(saddles):
        t = (k + 0.5) / saddles - 0.5
        q = V((x, 0, z)) + ax * (t * L * 0.72)
        with B.at(M=lib.basis(q, s, (0, 1, 0), ax)):
            B.box((r * 1.6, y - r * 0.5, 0.8), at=(0, (y - r * 0.5) / 2, 0), mat='concrete2', bevel=0.05)
            B.box((r * 1.7, 0.25, 1.0), at=(0, y - r * 0.5, 0), mat='frame', bevel=0.02)
    B.vcyl(0.3, 0.8, (x, y + r - 0.1, z), mat='pipeDark', n=8)


def stack(B, c, r0, h, r1=None, y0=0.0, bands=(), platforms=(), base_h=0.0, base_r=None, mat='panel', n=24,
          cap=True, ladder_side=None, lamps=True):
    """Chimney / stack: plan centre c, radius r0 at the base tapering to r1, height h above y0; bands [(y0, y1, mat)]
    (the concept's dark / light banding), platform rings with railings, a flared base of base_h, a dark sooted
    lip; an amber pin under each platform and a red obstruction light at the top."""
    x, z = c
    r1 = r0 if r1 is None else r1
    if base_h:
        br = base_r or r0 * 1.5
        B.lathe([(br, 0), (br, base_h * 0.3), (r0 * 1.02, base_h), (0, base_h)], (x, y0, z), mat='frame2', n=n)
    B.lathe([(r0, 0), (r1, h)], (x, y0, z), mat=mat, n=n)
    for (a, b, m) in bands:
        ra = r0 + (r1 - r0) * a / h
        rb = r0 + (r1 - r0) * b / h
        B.lathe([(ra - 0.04, a), (ra + 0.05, a), (rb + 0.05, b), (rb - 0.04, b)], (x, y0, z), mat=m, n=n, closed=True)
    for py in platforms:
        rr = r0 + (r1 - r0) * py / h
        platform_ring(B, (x, z), y0 + py, rr + 0.05, rr + 1.4)
        if lamps:
            B.R.pin((x + rr + 1.45, y0 + py + 0.1, z))
    if cap:
        B.lathe([(r1 + 0.25, 0), (r1 + 0.25, 1.0), (r1 - 0.35, 1.0), (r1 - 0.35, -0.2)], (x, y0 + h - 0.6, z), mat='soot', n=n, closed=True)
        B.lathe([(r1 - 0.3, 0), (0, 0)], (x, y0 + h - 1.6, z), mat='soot', n=n)
    if ladder_side is not None:
        a = ladder_side * DEG
        nn = V((math.sin(a), 0, math.cos(a)))
        ladder(B, V((x, y0 + base_h, z)) + nn * (r0 + 0.05), nn, h - base_h - 0.5)
    B.R.obstruction((x + (r1 + 0.3) * 0.7, y0 + h + 0.55, z + (r1 + 0.3) * 0.7))
    return y0 + h


def gable_roof(B, x0, x1, z0, z1, y, rise, ridge='z', mat='panel2', cap='frame', eave=0.4, ribs=True, skylight=True):
    """Shallow gable roof over the rectangle [x0, x1] x [z0, z1] at eaves height y, ridge `rise` m up, ridge running
    along `ridge` ('z' or 'x'); dark ridge cap, gable-end fascias, standing-seam ribs and a ridge skylight strip."""
    if ridge == 'z':
        xm = (x0 + x1) / 2
        prof = [(x0 - eave, y), (xm, y + rise), (x1 + eave, y), (x1 + eave, y - 0.35), (xm, y + rise - 0.35), (x0 - eave, y - 0.35)]
        B.add(lib.bm_prism([(a, b) for a, b in prof], z0 - eave, z1 + eave), mat=mat, bevel=0.03)
        B.box((0.6, 0.35, z1 - z0 + 2 * eave + 0.2), at=(xm, y + rise + 0.05, (z0 + z1) / 2), mat=cap, bevel=0.03)
        if skylight:
            for sx in (-1, 1):
                ang = math.atan2(rise, (x1 - x0) / 2)
                with B.at(at=(xm + sx * 2.2, y + rise - 2.2 * math.tan(ang) + 0.06, (z0 + z1) / 2), rot=(0, 0, sx * -math.degrees(ang))):
                    B.box((2.4, 0.12, z1 - z0 - 6.0), mat='glassW', bevel=0.0)
        if ribs:
            n = int((z1 - z0) / 1.2)
            for sx in (-1, 1):
                ang = math.atan2(rise, (x1 - x0) / 2 + eave)
                L = math.hypot((x1 - x0) / 2 + eave, rise)
                with B.at(at=(xm + sx * ((x1 - x0) / 4 + eave / 2), y + rise / 2 + 0.03, 0), rot=(0, 0, sx * -math.degrees(ang))):
                    for k in range(n + 1):
                        B.box((L, 0.06, 0.06), at=(0, 0, z0 + k * (z1 - z0) / n), mat='frame2', bevel=0.0)
        for e in (z0 - eave, z1 + eave):
            B.bar((x0 - eave, y, e), (xm, y + rise, e), 0.35, 0.5, mat=cap, bevel=0.02)
            B.bar((xm, y + rise, e), (x1 + eave, y, e), 0.35, 0.5, mat=cap, bevel=0.02)
            B.add(lib.bm_prism([(x0, y), (xm, y + rise - 0.3), (x1, y)], -0.15, 0.15), at=(0, 0, e - (0.2 if e < z0 else -0.2)), mat='panel2', bevel=0.0)
    else:
        with B.at(at=((x0 + x1) / 2, 0, (z0 + z1) / 2), rot=(0, 90, 0)):
            hz, hx = (z1 - z0) / 2, (x1 - x0) / 2
            gable_roof(B, -hz, hz, -hx, hx, y, rise, 'z', mat, cap, eave, ribs, skylight)


def glow_ring(B, c, r, y, h=0.8, n=20, color='#ff8a2a', radiance=2.6, arc=(0, 360)):
    """A band of hot light round a vessel (tuyere ring, furnace glow): n tangent glow boxes at radius r."""
    x, z = c
    a0, a1 = arc
    for k in range(n):
        a = math.radians(a0 + (a1 - a0) * (k + 0.5) / n)
        seg = 2 * math.pi * r * ((a1 - a0) / 360.0) / n * 0.82
        B.R.glowbox((x + r * math.sin(a), y, z + r * math.cos(a)), (seg, h, 0.06), color=color, radiance=radiance, roty=a)


# ------------------------------------------------------------------------------------------------------------------
# glazing, landscape, small dressing
# ------------------------------------------------------------------------------------------------------------------
def glazing(B, o, u, w, h, mull=(1.5, 1.5), frame_w=0.25, lit=True, color='#ffc27a', radiance=0.8, depth=0.0):
    """Curtain wall: glass with a mullion grid in a heavy dark frame on a face (o bottom-left, u right)."""
    M = face_basis(o, u)
    n = (M.to_3x3() @ V((0, 0, 1))).normalized()
    with B.at(M=M):
        B.box((w, h, 0.06), at=(w / 2, h / 2, -depth - 0.02), mat='glassW', bevel=0.0)
        nx, ny = max(1, int(round(w / mull[0]))), max(1, int(round(h / mull[1])))
        for i in range(1, nx):
            B.box((0.08, h, 0.14), at=(w * i / nx, h / 2, -depth + 0.04), mat='frame', bevel=0.0)
        for j in range(1, ny):
            B.box((w, 0.08, 0.14), at=(w / 2, h * j / ny, -depth + 0.04), mat='frame', bevel=0.0)
        for (a, b) in (((0, 0), (w, 0)), ((0, h), (w, h))):
            B.box((w + 2 * frame_w, frame_w, 0.3 + depth), at=(w / 2, a[1], -depth / 2 + 0.1), mat='frame', bevel=0.02)
        for x in (0, w):
            B.box((frame_w, h, 0.3 + depth), at=(x, h / 2, -depth / 2 + 0.1), mat='frame', bevel=0.02)
    if lit:
        c = M @ V((w / 2, h / 2, -depth - 0.4))
        size = (w, h, 0.05) if abs(n.z) > 0.7 else (0.05, h, w)
        B.R.glowbox(c, size, color=color, radiance=radiance)


def tree(B, p, h=6.0, r=2.2, seed=0):
    """Low-poly tree: trunk and two or three stacked crowns."""
    x, y, z = p
    B.vcyl(0.18, h * 0.45, (x, y, z), mat='bark', n=6)
    rr = r
    yy = y + h * 0.35
    for k in range(3):
        B.add(_ico(rr * (1.0 - 0.18 * k)), at=(x + 0.3 * math.sin(seed + k), yy + rr * 0.7, z + 0.3 * math.cos(seed * 2 + k)), mat='foliage', bevel=0.0, sharp=20)
        yy += rr * 0.75


def _ico(r):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r)
    for v in bm.verts:
        v.co.y *= 0.8
    return bm


def planter(B, c, w, d, h=0.7, trees=1, shrubs=True):
    x, z = c
    B.box((w, h, d), at=(x, h / 2, z), mat='frame2', bevel=0.04)
    B.box((w - 0.3, 0.05, d - 0.3), at=(x, h + 0.01, z), mat='soil', bevel=0.0)
    for k in range(trees):
        tx = x - w / 2 + w * (k + 0.5) / trees
        tree(B, (tx, h, z), h=5.0, r=1.6, seed=k * 1.7 + x)
    if shrubs:
        for k in range(int(w / 1.2)):
            B.add(_ico(0.5), at=(x - w / 2 + 0.6 + k * 1.2, h + 0.35, z + (0.3 if k % 2 else -0.3)), mat='foliage', bevel=0.0, sharp=20)


def crate(B, p, size=(1.2, 1.0, 1.2), mat='frame2', rot=0.0):
    with B.at(at=p, rot=(0, rot, 0)):
        B.box(size, at=(0, size[1] / 2, 0), mat=mat, bevel=0.03)
        B.box((size[0] + 0.04, 0.1, size[2] + 0.04), at=(0, size[1] * 0.85, 0), mat='frame', bevel=0.0)
        B.box((size[0] + 0.04, 0.1, size[2] + 0.04), at=(0, size[1] * 0.15, 0), mat='frame', bevel=0.0)


def cabinet(B, p, w=1.2, h=1.8, d=0.6, rot=0.0, mat='panel2'):
    """Electrical cabinet / junction box on a plinth."""
    with B.at(at=p, rot=(0, rot, 0)):
        B.box((w + 0.2, 0.15, d + 0.2), at=(0, 0.075, 0), mat='concrete2', bevel=0.02)
        B.box((w, h, d), at=(0, 0.15 + h / 2, 0), mat=mat, bevel=0.03)
        B.box((0.03, h - 0.3, 0.04), at=(0, 0.15 + h / 2, d / 2 + 0.01), mat='seam', bevel=0.0)
        B.box((w + 0.1, 0.08, d + 0.15), at=(0, 0.15 + h + 0.04, 0), mat='frame', bevel=0.0)


def lamp_post(B, p, h=6.0, arm=1.2, rot=0.0):
    """Area lamp post with an amber head lamp (a pin at the head, never a chain)."""
    x, y, z = p
    B.vcyl(0.09, h, (x, y, z), mat='frame', n=6)
    B.box((0.5, 0.3, 0.5), at=(x, y + 0.15, z), mat='concrete2', bevel=0.02)
    a = rot * DEG
    hx, hz = x + arm * math.sin(a), z + arm * math.cos(a)
    B.bar((x, y + h, z), (hx, y + h, hz), 0.08, mat='frame', bevel=0.0)
    B.box((0.5, 0.15, 0.3), at=(hx, y + h - 0.05, hz), mat='frame2', bevel=0.02)
    B.R.pin((hx, y + h - 0.18, hz))


# yard-kit vehicles and figures (assets/parts-yard, placed by assemble.py; they stand on y = 0, front +Z)
def _yard(B, part, p, heading, tag):
    # +Y-mount parts: assemble.py lays the part's +X along `along`; heading turns its front (+Z) about +Y
    a = heading * DEG
    B.R.place(part, p, n=(0, 1, 0), up=(math.sin(a), 0, math.cos(a)), along=(math.cos(a), 0, -math.sin(a)), id=tag)


def truck(B, p, heading=0.0):
    """Yard-kit semi (16.5 m), heading in degrees (0 = front toward +Z)."""
    _yard(B, 'yard:truck', p, heading, 'truck')


def forklift(B, p, heading=0.0):
    _yard(B, 'yard:forklift', p, heading, 'forklift')


def worker(B, p, heading=0.0):
    """1.8 m crew figure (the fleet ruler)."""
    _yard(B, 'yard:worker', p, heading, 'worker')


def container(B, p, heading=0.0):
    """Fleet-kit 20-ft ISO container (mount +Z out of the deck: stands with +Z up)."""
    a = heading * DEG
    B.R.place('container', p, n=(0, 1, 0), up=(math.sin(a), 0, math.cos(a)), id='container')


def flood_on_wall(B, p, n, target):
    """A kit floodlight on a wall bracket at p (face normal n) aimed at a ground point."""
    p, n = vv(p), vv(n)
    B.box((0.2, 0.2, 0.5), at=tuple(p + n * 0.25), mat='frame', bevel=0.0)
    B.R.flood(tuple(p + n * 0.5), target, n=n)


def stencil(B, text, h, centre, normal, up=(0, 1, 0), mat='frame'):
    """Fleet stencil numbers (yard_kit glyphs) as thin plates on a face."""
    P = lib.Part('_stencil')
    YK.stencil(P, text, h, centre, normal, up=up, depth=0.06, mat=mat)
    for ob, m, bev, seg, sharp in P.items:
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bm.transform(ob.matrix_world)
        B.add(bm, mat=m, bevel=0.0)
        bpy.data.objects.remove(ob)


def hazard_band(B, p0, p1, w=0.3, h=0.03):
    """Amber / black diagonal-striped strip on the ground or a kerb (lib 'hazard' bake)."""
    B.bar(p0, p1, w, h, mat='hazard', bevel=0.0)


# ------------------------------------------------------------------------------------------------------------------
# kit inventory (README-bkit.md / kits.md are written from this)
# ------------------------------------------------------------------------------------------------------------------
INVENTORY = [
    ('plinth', 'chamfered concrete slab, light kerb, dark toe and shadow line, slab joints, markings, grates, access stairs, amber edge pins'),
    ('facade / block', 'off-white panels in gunmetal frames: corner posts, pilasters per bay, storey bands, parapet cap, base band, seams, recessed warm windows, tall glazed slots, louvres, roller doors with amber jamb slits, kit crew doors with lamps and canopies'),
    ('roof_deck + ROOF_UNITS', 'membrane, parapet; hvac, vent, fan, antenna, solar, tank, box'),
    ('pipe / valve / pipe_rack / cable_tray', 'filleted runs, flanges, amber rings, T supports with footings; gate valves; portal racks'),
    ('vtank / sphere_tank / htank / stack', 'vertical vessels (dome / cone / flat heads, bands, seams, platforms, caged ladders, nozzles), Horton spheres on braced legs, capsule tanks on saddles, banded stacks with platforms and obstruction lights'),
    ('railing / catwalk / platform_ring / stair / ladder', '1.1 m rails, grating walks, ring platforms, 0.18 / 0.28 m stairs, 0.62 m caged ladders'),
    ('truss / lattice_tower', 'square lattice between two points; four-post tapered towers'),
    ('glazing', 'curtain wall with mullions, heavy frame, warm glow'),
    ('gable_roof / glow_ring', 'shallow gable roof sections with ridge caps, ribs and skylights; hot light bands round vessels'),
    ('tree / planter', 'low-poly trees, planters with shrubs'),
    ('crate / cabinet / bollards / lamp_post / hazard_band / stencil', 'small dressing'),
    ('truck / forklift / worker / container / flood_on_wall', 'placements of yard-kit and fleet-kit parts (assemble.py)'),
]
