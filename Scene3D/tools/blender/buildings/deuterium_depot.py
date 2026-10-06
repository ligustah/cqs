"""DEUTERIUM_DEPOT: three spherical tanks on legs with cobalt bands, pipe manifold, pump houses
(concept style-library/styles/cqs-fleet/images/buildings/deuterium_depot-concept.jpg).

Built only from the shared kit (bkit.py) by colony_build.py:
    $PY tools/blender/buildings/colony_build.py deuterium_depot <work> [--tex 4096]

Frame: metres, plinth top y = 0, +Z front, +X left (the concept camera looks from the front-left, az ~30, el ~27).
Sizes (real-world, the concept's proportions measured against its doors and spheres):
  plinth 66 x 48 m, 1.4 m deep; spheres 19 m diameter, centre 16 m up (bottom 6.5 m clear), tops ~26 m (+ valve
  housing 28 m); pump houses 12 x 8 x 6.5 m and 14 x 9 x 7 m with 1 x 2 m kit crew doors.
"""
import math

import bkit as K

SPEC = {
    'title': 'Deuterium Depot', 'gameId': 'DEUTERIUM_DEPOT', 'group': 'storage',
    'footprint': [70, 52], 'height': 30.0,
    'camera': {'az': 30, 'el': 27},
    'about': 'three 19 m deuterium spheres on braced legs, cobalt equator bands, ground manifold, two pump houses',
}

R_S = 10.5         # sphere radius (21 m: the concept's spheres crowd the slab, ~3 diameters across it)
YC = 16.5          # sphere centre height (bottom 6 m clear)
SPHERES = {'L': (-21.5, -9.5), 'M': (1.0, -2.5), 'R': (22.0, -13.5)}


def model(B):
    W, D = SPEC['footprint']
    K.plinth(B, W, D, h=1.4, chamfer=2.0, slab=6.0, lamp_pitch=16.0,
             markings=[
                 ([(-31.5, 21.0), (31.5, 21.0)], 0.18, 'frame2'),         # front walkway edge line (dark paint)
                 ([(29.5, 21.0), (29.5, -21.0)], 0.18, 'frame2'),         # left walkway edge line
                 ([(-26, 16.5), (-2, 16.5)], 0.12, 'white'),              # lane in front of the left pump house
                 ([(6, 21.0), (6, 17.0), (26, 17.0)], 0.12, 'white'),
             ],
             grates=[(12.0, 20.0, 2.2, 0.8), (-6.0, 20.0, 2.2, 0.8), (27.0, -4.0, 0.8, 2.2), (-28.0, 18.0, 1.2, 1.2)],
             steps=[(26.0, 24.0, '+z')])

    # --- the three spheres -------------------------------------------------------------------------------------
    tops = {}
    for k, (x, z) in SPHERES.items():
        tops[k] = K.sphere_tank(B, (x, z), r=R_S, yc=YC, legs=8, band='cobalt', ladder_angle=160.0 if k != 'R' else 130.0)
        # bund kerb ring round each tank's legs (a low dark curb on the slab)
        B.ring(R_S * 1.25, R_S * 1.25 - 0.3, 0.0, 0.25, (x, 0, z), mat='concrete2', n=40)

    # --- top-to-ground transfer pipes: a big pipe from each top platform arcs over the shoulder and down the side
    for k, (x, z) in SPHERES.items():
        a = {'L': 40.0, 'M': 25.0, 'R': 55.0}[k] * math.pi / 180      # angle of the downcomer (toward front-left)
        cx, cz = math.sin(a), math.cos(a)
        top = (x + 1.2 * cx, YC + R_S + 1.0, z + 1.2 * cz)
        over = (x + (R_S * 0.62) * cx, YC + R_S + 1.0, z + (R_S * 0.62) * cz)
        side = (x + (R_S + 1.5) * cx, YC + R_S * 0.62, z + (R_S + 1.5) * cz)
        low = (x + (R_S + 1.5) * cx, 3.2, z + (R_S + 1.5) * cz)
        K.pipe(B, [top, over, side, low], r=0.55, rings=True)
        # clamp brackets tying the downcomer to the shell
        for yy in (YC + 3.0, YC - 2.0):
            B.bar((x + (R_S * 0.95) * cx, yy, z + (R_S * 0.95) * cz), (x + (R_S + 1.5) * cx, yy, z + (R_S + 1.5) * cz), 0.18, mat='frame')
        tops[k] = low

    # --- ground manifold: a main header along the front of the spheres, branches to each sphere, risers
    hy = 2.6
    header = [(-28.0, hy, 9.5), (8.0, hy, 9.5), (8.0, hy, 12.0), (10.0, hy, 12.0)]
    K.pipe(B, header, r=0.75, supports=True, support_pitch=6.0)
    K.pipe(B, [(-28.0, hy + 1.8, 8.0), (14.0, hy + 1.8, 8.0)], r=0.45, supports=False)
    for k, (x, z) in SPHERES.items():
        lx, _, lz = tops[k]
        run = [(lx, 3.2, lz), (lx, hy, lz), (lx, hy, 9.5)] if k != 'R' else [(lx, 3.2, lz), (lx, hy, lz), (lx, hy, -1.0), (8.0, hy, -1.0), (8.0, hy, 9.5)]
        K.pipe(B, run, r=0.5)
        # bottom outlet to the header
        K.pipe(B, [(x, 1.6, z), (x, 1.2, z), (x, 1.2, 9.5 if z < 9 else z)], r=0.35, flanges=True, rings=False)
    # the concept's big transfer lines between the spheres (5 m up, through the leg rings), one rising into R's belly
    K.pipe(B, [(-31.0, 5.0, 2.5), (12.5, 5.0, 2.5), (12.5, 5.0, -7.0), (15.5, 6.5, -9.5)], r=0.85, supports=True, support_pitch=8.0)
    K.pipe(B, [(-21.5, 4.6, -9.5), (-21.5, 3.6, 1.0), (-21.5, 3.6, 2.5)], r=0.55, rings=False)
    K.pipe(B, [(1.0, 4.6, -2.5), (6.0, 3.8, -2.5), (6.0, 3.8, 2.5)], r=0.55, rings=False)
    K.valve(B, (-10.0, hy, 9.5), (1, 0, 0), r=0.75)
    K.valve(B, (4.0, hy, 9.5), (1, 0, 0), r=0.75)
    # racks of smaller lines between the spheres (the concept's pipe bundle behind the middle tank)
    K.pipe_rack(B, (-8.0, 0, -19.0), (10.0, 0, -19.0), w=3.0, levels=(4.5,), pitch=6.0,
                pipes=[(0, -0.8, 0.35, 'pipe'), (0, 0.2, 0.3, 'pipe'), (0, 1.0, 0.25, 'pipeDark')])

    # --- pump house A (left, front) ----------------------------------------------------------------------------
    K.block(B, (-14.0, 0.0, 15.5), (12.0, 6.5, 8.0),
            sides={'+z': {'bay': 6.0, 'doors': [8.0], 'rollers': [(3.6, 3.6, 4.0)], 'windows': [], 'louvres': [(10.6, 3.8, 1.4, 1.0)]},
                   '+x': {'bay': 4.0, 'doors': [], 'windows': [0], 'win': (1.2, 1.0), 'louvres': [(2.2, 3.6, 1.2, 1.2)]},
                   '-x': {'bay': 4.0}, '-z': {'bay': 4.0}},
            roof={'parapet': 0.45, 'units': [('hvac', -2.6, 0.5, {'w': 3.2, 'd': 2.2}), ('hvac', 1.6, 0.5, {'w': 3.2, 'd': 2.2}),
                                            ('vent', 4.4, -2.2, {}), ('box', -4.6, -2.4, {'w': 1.6, 'd': 1.4, 'h': 1.0})]})
    # pumps on skids in front of its left side, with their pipework into the header
    for i, x in enumerate((-6.0, -4.0)):
        B.box((1.4, 0.4, 2.6), at=(x, 0.2, 13.2), mat='frame', bevel=0.03)
        B.cyl(0.55, 1.6, at=(x, 1.0, 13.0), rot=(0, 0, 0), mat='pipeDark', n=12)
        B.vcyl(0.4, 1.0, (x, 0.4, 14.2), mat='cobalt', n=12)
        K.pipe(B, [(x, 1.0, 12.2), (x, 1.0, 10.6), (x, hy, 10.6), (x, hy, 9.5)], r=0.25, rings=False)

    # --- pump house B (right of the middle sphere, front) with the filter / dryer columns beside it ----------
    K.block(B, (17.0, 0.0, 15.0), (14.0, 7.0, 9.0),
            sides={'+z': {'bay': 7.0, 'doors': [10.5], 'rollers': [(4.0, 3.6, 4.2)], 'windows': [0], 'win': (1.2, 1.0), 'skip': [0, 2]},
                   '+x': {'bay': 4.5, 'windows': [0], 'win': (1.2, 1.0), 'doors': [6.5]},
                   '-x': {'bay': 4.5}, '-z': {'bay': 4.6}},
            roof={'parapet': 0.45, 'units': [('hvac', -3.8, -0.8, {'w': 3.4, 'd': 2.4}), ('hvac', 0.4, -0.8, {'w': 3.4, 'd': 2.4}),
                                            ('hvac', 4.4, -0.8, {'w': 2.6, 'd': 2.0, 'fans': 1}), ('vent', -4.4, 2.6, {}), ('fan', 3.6, 2.6, {})]})
    # five dryer / filter columns on a skid between the header and pump house B
    B.box((6.4, 0.35, 3.4), at=(6.8, 0.175, 15.6), mat='frame', bevel=0.03)
    for i in range(5):
        x = 4.4 + i * 1.25
        K.vtank(B, (x, 15.6 + (0.5 if i % 2 else -0.5)), 0.45, 4.2 + 0.4 * (i % 2), y0=0.35, top='dome', mat='pipe',
                bands=[(0.6, 0.85, 'pipeDark'), (3.4, 3.6, 'pipeDark')], seams=False, n=14, top_unit=False)
    K.pipe(B, [(4.4, 4.0, 14.6), (4.4, 5.6, 14.6), (9.4, 5.6, 14.6), (9.4, 4.0, 14.6)], r=0.15, rings=False)
    K.pipe(B, [(8.0, hy, 12.0), (8.0, hy, 14.2), (10.0, 1.2, 14.2)], r=0.3, rings=False)
    B.R.pin((3.6, 0.6, 17.4))

    # --- dressing: cabinets, bollards, lamp posts, crates, a worker, a truck at the gate, edge stairs ---------
    for (x, z, r) in ((-29.0, 4.0, 90.0), (-29.0, 6.0, 90.0), (-29.0, 13.0, 90.0), (28.5, 2.0, -90.0), (24.0, 21.5, 0.0)):
        K.cabinet(B, (x, 0.0, z), w=1.1, h=1.7, d=0.6, rot=r)
    K.bollards(B, [(-21.0, 20.0), (-7.0, 20.0), (9.0, 20.5), (11.5, 20.5), (24.5, 20.0), (27.0, 11.0), (27.0, 7.0), (-2.0, 20.0)])
    for (x, z, rot) in ((-30.0, -20.0, 45), (30.0, -20.0, -45), (-30.0, 20.0, 135)):
        K.lamp_post(B, (x, 0.0, z), h=7.0, arm=1.0, rot=rot)
    K.crate(B, (-24.0, 0.0, 17.5), (1.4, 1.1, 1.2))
    K.crate(B, (-22.5, 0.0, 17.8), (1.2, 0.9, 1.2), mat='cobalt')
    K.crate(B, (26.5, 0.0, -18.0), (1.6, 1.2, 1.2))
    K.worker(B, (3.0, 0.0, 19.0), heading=200)
    K.worker(B, (-8.6, 0.0, 20.0), heading=10)
    B.R.beacon((-14.0, 7.8, 11.8))
    B.R.beacon((19.0, 8.3, 11.0))
