"""DEUTERIUM_DEPOT: three spherical tanks on legs with cobalt bands, pipe manifold, pump houses
(concept style-library/styles/cqs-fleet/images/buildings/deuterium_depot-concept.jpg).

v2: the signature pieces are fal components (assets/parts-colony: sphereTank, plantHouse, manifoldSkid, filterBank;
README-colony.md catalogue), composed with the shared parametric kit (plinth, pipe runs, racks, dressing, lights).
Built by colony_build.py:
    $PY tools/blender/buildings/colony_build.py deuterium_depot <work> [--tex 4096]

Frame: metres, plinth top y = 0, +Z front, +X left (the concept camera looks from the front-left, az ~30, el ~27).
Sizes (real-world, the concept's proportions measured against its doors and spheres):
  plinth 72 x 48 m, 1.4 m deep; spheres 21 m (component sphereTank: 26.5 m across the footings, 25.8 m tall); pump
  houses 12 x 8 x 6.5 m (component plantHouse).
"""
import math

import bkit as K

SPEC = {
    'title': 'Deuterium Depot', 'gameId': 'DEUTERIUM_DEPOT', 'group': 'storage',
    'footprint': [72, 48], 'height': 27.0,
    'camera': {'az': 30, 'el': 27},
    'about': 'three 19 m deuterium spheres on braced legs, cobalt equator bands, ground manifold, two pump houses',
}

R_S = 10.5         # sphere radius (21 m: the concept's spheres crowd the slab, ~3 diameters across it)
YC = 16.5          # sphere centre height (bottom 6 m clear)
SPHERES = {'L': (-21.5, -9.5), 'M': (1.0, -2.5), 'R': (22.0, -13.5)}


def model(B):
    W, D = SPEC['footprint']
    CZ = -3.5                     # slab centre (z): the spheres sit back, the pump houses tuck in front of them
    FZ = CZ + D / 2               # front edge z
    K.plinth(B, W, D, h=1.4, chamfer=2.0, slab=6.0, lamp_pitch=16.0, centre=(0.0, CZ),
             markings=[
                 ([(-W / 2 + 1.5, FZ - 1.6), (W / 2 - 1.5, FZ - 1.6)], 0.18, 'frame2'),   # front walkway edge line (dark paint)
                 ([(W / 2 - 3.0, FZ - 1.6), (W / 2 - 3.0, CZ - D / 2 + 2.0)], 0.18, 'frame2'),
                 ([(-1.0, FZ - 1.6), (-1.0, 9.5), (8.0, 9.5)], 0.12, 'white'),
             ],
             grates=[(1.0, FZ - 2.6, 2.2, 0.8), (-12.0, FZ - 2.6, 2.2, 0.8), (W / 2 - 4.5, -6.0, 0.8, 2.2), (-W / 2 + 3.0, 10.0, 1.2, 1.2)],
             steps=[(28.0, FZ, '+z')])

    # --- the three spheres: the fal component (assets/parts-colony/sphereTank: 21 m shell on 8 legs, 26.5 m across the
    # footings, 25.8 m to the platform), turned so each transfer pipe runs down the side the concept shows
    for k, (x, z) in SPHERES.items():
        K.component(B, 'sphereTank', (x, 0.0, z), heading={'L': 200.0, 'M': 160.0, 'R': 130.0}[k])
        B.ring(13.6, 13.3, 0.0, 0.25, (x, 0, z), mat='concrete2', n=40)          # bund kerb round the footings
        for a in range(8):                                                         # amber pins at the footings
            t = math.radians(22.5 + 45 * a)
            B.R.pin((x + 13.0 * math.cos(t), 1.2, z + 13.0 * math.sin(t)))
        B.R.pin((x, 26.6, z))

    # --- ground manifold: the fal manifold skid between the pump houses, a header and the big transfer line through
    # the leg rings (parametric: the kit's flanges, amber rings, supports)
    hy = 2.6
    K.component(B, 'manifoldSkid', (-3.0, 0.0, 12.8), heading=90.0)
    K.pipe(B, [(-W / 2 + 2.0, 4.8, 3.0), (13.0, 4.8, 3.0), (13.0, 4.8, -6.0), (15.5, 6.0, -8.0)], r=0.85, supports=True, support_pitch=8.0)
    K.pipe(B, [(-W / 2 + 2.0, hy, 7.2), (16.0, hy, 7.2)], r=0.55, supports=True, support_pitch=6.0)
    K.pipe(B, [(-3.0, 1.6, 9.9), (-3.0, 1.6, 7.6)], r=0.5, rings=False)
    K.pipe_rack(B, (-8.0, 0, -19.0), (10.0, 0, -19.0), w=3.0, levels=(4.5,), pitch=6.0,
                pipes=[(0, -0.8, 0.35, 'pipe'), (0, 0.2, 0.3, 'pipe'), (0, 1.0, 0.25, 'pipeDark')])

    # --- pump houses: the fal plant house (12 x 8 x 6.5 m body, roof HVAC, pipe stubs on one end), door face to +Z,
    # tucked in front of the left and right spheres as in the concept
    houses = ((-19.5, 12.5), (18.5, 11.0))
    for (x, z) in houses:
        K.component(B, 'plantHouse', (x, 0.0, z), heading=-90.0)
        for sx in (-1, 1):
            for sz in (-1, 1):
                B.R.pin((x + sx * 8.6, 6.6, z + sz * 4.3))
    # the fal filter / dryer skid beside pump house B
    K.component(B, 'filterBank', (6.0, 0.0, 16.6), heading=90.0)
    B.R.pin((2.4, 0.6, 18.4))

    # --- dressing: cabinets, bollards, lamp posts, crates, workers, edge lamps
    for (x, z, r) in ((-33.5, 2.0, 90.0), (-33.5, 4.0, 90.0), (33.0, 0.0, -90.0), (33.0, 14.0, -90.0)):
        K.cabinet(B, (x, 0.0, z), w=1.1, h=1.7, d=0.6, rot=r)
    K.bollards(B, [(-24.0, FZ - 2.2), (-14.0, FZ - 2.2), (4.0, FZ - 2.2), (9.0, FZ - 2.2), (24.0, FZ - 2.2), (31.5, 8.0), (31.5, 4.0), (-1.0, FZ - 2.2)])
    for (x, z, rot) in ((-33.0, -26.0, 45), (33.0, -26.0, -45), (-33.0, FZ - 2.0, 135)):
        K.lamp_post(B, (x, 0.0, z), h=7.0, arm=1.0, rot=rot)
    K.crate(B, (-31.5, 0.0, 15.5), (1.4, 1.1, 1.2))
    K.crate(B, (-31.5, 0.0, 17.4), (1.2, 0.9, 1.2), mat='cobalt')
    K.crate(B, (30.0, 0.0, -22.0), (1.6, 1.2, 1.2))
    K.worker(B, (2.0, 0.0, FZ - 2.5), heading=200)
    K.worker(B, (-8.0, 0.0, FZ - 2.8), heading=10)
    B.R.beacon((-19.5, 8.2, 9.0))
    B.R.beacon((18.5, 8.2, 7.5))
