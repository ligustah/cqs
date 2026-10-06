"""LIBRARY: stepped monumental archive block with a tall glazed central slot and a grand stair
(concept style-library/styles/cqs-fleet/images/buildings/library-concept.jpg).

Composed from fal components (assets/parts-colony: portalTower, monumentPylon x6; v3: the stepped wings are parametric, see stepped_wing; README-colony.md
catalogue) on the shared parametric kit (plinth, entrance podium, grand stair, cheek blocks, link blocks, dressing,
lights). Built by colony_build.py:
    $PY tools/blender/buildings/colony_build.py library <work> [--tex 4096]

Frame: metres, plinth top y = 0, +Z front, +X left (the concept camera looks from the front-left, az ~24, el ~27).
Sizes (the concept's proportions against its doors and the stair): slab 112 x 74 m; the two stepped wings 40 m square,
34 m; the portal tower 24 m wide, 46 m on a 3.6 m entrance podium (top ~50 m); grand stair 16 m wide, 20 risers of
0.18 m; pylons 10 m.
"""
import math

import bkit as K

SPEC = {
    'title': 'Library', 'gameId': 'LIBRARY', 'group': 'science',
    'footprint': [112, 70], 'height': 56.0,
    'camera': {'az': 22, 'el': 23},
    'about': 'stepped monumental archive: two battered stepped wings either side of a 46 m portal tower with a tall lit glazed slot, a grand stair up to the entrance podium, lit pylons',
}

CX, CZ = 0.0, -1.0
PODIUM_H = 3.6
WING_X = 24.0       # wing centres at +-WING_X: the 46 m wings meet behind the portal and read as one stepped mass
WING_Z = -6.0
PT_Z = 8.0          # portal tower centre z (its front stands 3 m proud of the wings)


def grand_stair(B, x, z0, w, rise, n):
    """Monumental stair: n risers from y = 0 at z0 (front) up to `rise` towards -Z, with dark cheek walls."""
    r, t = rise / n, 0.32
    for k in range(n):
        B.box((w, r * (k + 1), t), at=(x, r * (k + 1) / 2, z0 - t * (k + 0.5)), mat='concrete' if k % 2 else 'kerb', bevel=0.0)
    L = n * t
    for sx in (-1, 1):
        cx = x + sx * (w / 2 + 0.9)
        B.prism([(cx - 0.9, z0 + 0.3), (cx + 0.9, z0 + 0.3), (cx + 0.9, z0 - L), (cx - 0.9, z0 - L)], 0.0, rise + 0.9, mat='frame2', bevel=0.05)
        B.box((2.0, 0.2, L + 0.5), at=(cx, rise + 1.0, z0 - L / 2 + 0.1), mat='frame', bevel=0.03)
        B.R.pin((cx, rise + 1.25, z0 + 0.2))
        # handrail down the middle and at each side
    for xr in (x - w / 4, x + w / 4):
        K.railing(B, [(xr, 0.2, z0 - 0.2), (xr, rise + 0.1, z0 - L + 0.2)], h=0.95, post=3.0, mid=False)


def stepped_wing(B, sx):
    """v3: one stepped wing, parametric (crisp terraces; the fal steppedWing reconstructed its set-backs soft and its
    stone brown): a dark base course, a battered 15 m lower tier in pale stone, three set-back tiers with dark ribbon
    window bands, light terrace caps at every step; the tiers step back toward the portal (-sx) and the front."""
    x0, z0 = sx * WING_X, WING_Z
    B.box((46.8, 1.6, 46.8), at=(x0, 0.8, z0), mat='frame2', bevel=0.05)
    sq = lambda w, d, cx, cz: [(cx + w / 2, cz - d / 2), (cx + w / 2, cz + d / 2), (cx - w / 2, cz + d / 2), (cx - w / 2, cz - d / 2)]
    B.loft([(sq(46.0, 46.0, x0, z0), 1.6), (sq(42.0, 42.0, x0, z0), 16.6)], mat='stone', bevel=0.04)
    B.box((42.6, 0.5, 42.6), at=(x0, 16.85, z0), mat='kerb', bevel=0.04)          # crisp light terrace cap
    B.box((42.8, 0.18, 42.8), at=(x0, 16.55, z0), mat='frame', bevel=0.0)          # shadow line under it
    # tall dark slots in the battered front and outer faces (the concept's vertical recesses), lit at the foot
    for k in (-1, 1):
        for (u, f) in ((k * 9.0, 'z'), (k * 9.0, 'x')):
            if f == 'z':
                B.box((1.4, 12.5, 0.4), at=(x0 + u, 8.6, z0 + 22.1), mat='frame', bevel=0.02)
            else:
                B.box((0.4, 12.5, 1.4), at=(x0 + sx * 22.1, 8.6, z0 + u), mat='frame', bevel=0.02)
    y = 17.1
    for k, (w, h) in enumerate(((36.0, 5.6), (29.0, 5.2), (22.0, 5.0))):
        cx, cz = x0 - sx * 1.6 * (k + 1), z0 - 1.2 * (k + 1)
        K.block(B, (cx, y, cz), (w, h, w), y0=y, frame='frameL', panel='stone', corner_lamps=False,
                sides={f: {'bay': 3.0, 'storey': h, 'base': 0.0, 'windows': [0], 'win': (2.1, 1.5), 'win_per_bay': 1, 'sill': 1.6,
                           'pilasters': False, 'seams': False, 'bands': False, 'lit': 0.5, 'frame': 'frame'} for f in ('+z', '-z', '+x', '-x')},
                roof={'parapet': 0.0, 'mat': 'panel2'}, post=0.35)
        B.box((w + 0.8, 0.45, w + 0.8), at=(cx, y + h + 0.22, cz), mat='kerb', bevel=0.04)   # terrace cap
        y += h + 0.45


def model(B):
    W, D = SPEC['footprint']
    FZ = CZ + D / 2
    K.plinth(B, W, D, h=1.6, chamfer=2.4, slab=7.0, lamp_pitch=14.0, centre=(CX, CZ),
             markings=[([(-W / 2 + 1.5, FZ - 1.5), (W / 2 - 1.5, FZ - 1.5)], 0.16, 'frame2')],
             grates=[(-30.0, FZ - 7.0, 4.0, 0.8), (30.0, FZ - 7.0, 4.0, 0.8), (47.0, 12.0, 0.8, 4.0), (-47.0, 12.0, 0.8, 4.0)])

    # --- the two stepped wings (v3 parametric, stepped_wing(): battered lower tier on a dark base course, three set-back tiers with
    # lit window bands), and a dark link block filling the joint between them behind the portal
    for sx in (-1, 1):
        stepped_wing(B, sx)
        for (x, z) in ((sx * WING_X + sx * 23.4, WING_Z + 23.4), (sx * WING_X + sx * 23.4, WING_Z - 23.4)):
            B.R.pin((x, 0.6, z))
    K.block(B, (0.0, 0.0, -14.0), (26.0, 30.0, 26.0),
            sides={'-z': {'bay': 4.0, 'storey': 6.0, 'windows': [3, 4], 'win': (1.0, 2.2)}, '+x': {'bay': 4.0}, '-x': {'bay': 4.0}},
            roof={'parapet': 0.6, 'units': [('hvac', -5.0, -4.0, {'w': 3.2, 'd': 2.2}), ('hvac', 5.0, -4.0, {'w': 3.2, 'd': 2.2}), ('vent', 0.0, -8.0, {})]},
            corner_lamps=False)

    # --- the entrance podium and the portal tower on it (fal portalTower: 46 m, tall gold-lit glazed slot)
    B.box((30.0, PODIUM_H, 22.0), at=(0.0, PODIUM_H / 2, PT_Z + 4.0), mat='frame2', bevel=0.08)
    B.box((30.6, 0.35, 22.6), at=(0.0, PODIUM_H + 0.1, PT_Z + 4.0), mat='frame', bevel=0.04)
    for k in range(7):                      # dark ribs along the podium face
        B.box((0.5, PODIUM_H - 0.6, 0.3), at=(-13.5 + 4.5 * k, (PODIUM_H - 0.6) / 2 + 0.3, PT_Z + 15.1), mat='frame', bevel=0.02)
    K.component(B, 'portalTower', (0.0, PODIUM_H, PT_Z), heading=270.0)     # slot face (+X of the part) to the front
    B.R.beacon((0.0, PODIUM_H + 46.4, PT_Z - 4.0))
    B.R.glowbox((0.0, PODIUM_H + 0.2, PT_Z + 13.0), (8.0, 0.04, 3.0), color='#ffc27a', radiance=0.5)   # warm spill at the doors
    # paved forecourt on the podium: planters, lamps
    for sx in (-1, 1):
        B.box((3.2, 0.7, 1.4), at=(sx * 11.0, PODIUM_H + 0.35, PT_Z + 13.0), mat='frame2', bevel=0.04)
        B.R.pin((sx * 11.0, PODIUM_H + 0.85, PT_Z + 13.0))

    # --- the grand stair from the plaza up to the podium, flanked by cheek walls with lamps
    grand_stair(B, 0.0, PT_Z + 15.0 + 20 * 0.32, 16.0, PODIUM_H, 20)
    # low dark side terraces either side of the stair (the concept's stepped cheek blocks with lit doorways)
    for sx in (-1, 1):
        K.block(B, (sx * 14.5, 0.0, PT_Z + 18.0), (8.0, 2.6, 7.0),
                sides={'+z': {'bay': 4.0, 'doors': [4.0], 'windows': [], 'base': 0.5}, '+x' if sx > 0 else '-x': {'bay': 3.5}},
                roof={'parapet': 0.35}, frame='frame', panel='frame2', corner_lamps=True)

    # --- the lit pylons on the plaza (fal monumentPylon: dark stepped base, gold-lit slots)
    for (x, z) in ((-50.0, 28.0), (-26.0, 26.0), (11.5, 30.5), (-11.5, 30.5), (26.0, 26.0), (50.0, 30.0)):
        K.component(B, 'monumentPylon', (x, 0.0, z), heading=0.0)
    # --- dressing: low lamp bollards along the front, benches, crates of the archive's deliveries round the back
    for x in (-42.0, -34.0, -18.0, 18.0, 34.0, 42.0):
        B.vcyl(0.16, 0.9, (x, 0.0, FZ - 2.4), mat='frame', n=8)
        B.R.pin((x, 0.95, FZ - 2.4))
    for (x, z) in ((-40.0, 22.0), (40.0, 22.0)):
        B.box((3.0, 0.45, 0.7), at=(x, 0.45, z), mat='frame2', bevel=0.04)
    for (x, z, rot) in ((-54.0, -34.0, 45), (54.0, -34.0, -45)):
        K.lamp_post(B, (x, 0.0, z), h=7.0, arm=1.0, rot=rot)
    for (x, z, r) in ((53.0, -6.0, -90.0), (53.0, -4.0, -90.0), (-53.0, -10.0, 90.0)):
        K.cabinet(B, (x, 0.0, z), w=1.1, h=1.7, d=0.6, rot=r)
    K.truck(B, (46.0, 0.0, -32.5), heading=270.0)
    for (cx, cz) in ((36.0, -32.0), (34.0, -32.5)):
        K.crate(B, (cx, 0.0, cz), (1.4, 1.1, 1.4))
    for (x, z, hd) in ((-3.0, 31.0, 180), (2.5, 29.0, 10), (-1.0, 14.0, 160), (-20.0, 30.0, 90), (22.0, 31.0, 270), (5.0, 11.0, 200)):
        K.worker(B, (x, 0.0 if z > 24 else PODIUM_H, z), heading=hd)
