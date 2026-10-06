"""RADIO_TELESCOPE: large dish on an alt-az mount over an armoured base building
(concept style-library/styles/cqs-fleet/images/buildings/radio_telescope-concept.jpg).

Composed from the fal component dishMount (assets/parts-colony: the 32 m dish, feed tripod, yoke and azimuth drum in
one part; README-colony.md catalogue) on the shared parametric kit: the chamfered armoured base building with its
crew door, roller door and roof railing, the stair tower and utility annexes, plinth, pipes, dressing, lights; the
catalogue's filterBank reused as the cryo plant beside it.
Built by colony_build.py:
    $PY tools/blender/buildings/colony_build.py radio_telescope <work> [--tex 4096]

Frame: metres, plinth top y = 0, +Z front, +X left. The concept camera sits well round to the +X side (az ~62,
el ~14): the long +X face of the base with the crew door and the roller door faces the camera, the stair tower and
annex on the +Z end show on the left of the screen, the dish faces the front-left.
Sizes (real-world, against the concept's crew door and roller door): base 26 x 10 x 30 m, dish ~42 m (dishMount at 1.3),
top of the dish rim ~52 m; slab 48 x 58 m.
"""
import math

import bkit as K

SPEC = {
    'title': 'Radio Telescope', 'gameId': 'RADIO_TELESCOPE', 'group': 'science',
    'footprint': [48, 58], 'height': 54.0,
    'camera': {'az': 62, 'el': 8},
    'about': '32 m dish on an alt-az yoke and azimuth drum, on a chamfered armoured base building with crew and roller doors, stair tower and cryo plant',
}

BX, BZ, BW, BD, BH = 0.0, 0.0, 26.0, 30.0, 10.0     # base building centre, size (x, z), height
DISH_HEADING = -70.0          # dishMount faces its +X (part check): the dish turned to face the front-left (az ~20)
DISH_SCALE = 1.3              # the concept's dish spans more than the base: ~42 m
DISH_FOOT_X = -3.45 * 1.3     # the azimuth drum's centre in the part frame (x; the dish overhangs +X)


def model(B):
    W, D = SPEC['footprint']
    CX, CZ = 3.0, 0.0
    K.plinth(B, W, D, h=1.4, chamfer=2.0, slab=6.0, lamp_pitch=12.0, centre=(CX, CZ),
             markings=[([(CX + W / 2 - 2.0, CZ - D / 2 + 2.0), (CX + W / 2 - 2.0, CZ + D / 2 - 2.0)], 0.18, 'frame2'),
                       ([(BW / 2 + 0.5, -2.0), (BW / 2 + 7.0, -2.0)], 0.3, 'hazard'),
                       ([(BW / 2 + 0.5, -8.0), (BW / 2 + 7.0, -8.0)], 0.3, 'hazard')],
             grates=[(BW / 2 + 4.0, 6.0, 0.8, 2.2), (BW / 2 + 4.0, -14.0, 0.8, 2.2)],
             steps=[(CX + W / 2, -18.0, '+x')])

    # --- the armoured base (parametric): chamfered block, light panels in dark frames, doors on the +X face
    K.block(B, (BX, 0.0, BZ), (BW, BH, BD), chamfer=3.0,
            sides={'+x': {'bay': 5.0, 'pilasters': False, 'bands': False, 'storey': 4.0, 'base': 1.2, 'frame': 'frameL', 'base_mat': 'frame2', 'doors': [21.0], 'rollers': [(7.5, 6.0, 5.2)],
                          'louvres': [(11.5, 4.2, 3.0, 1.6), (16.0, 1.6, 1.2, 1.2)]},
                   '+z': {'bay': 5.0, 'pilasters': False, 'bands': False, 'storey': 4.0, 'base': 1.2, 'frame': 'frameL', 'base_mat': 'frame2', 'louvres': [(5.0, 4.4, 3.6, 2.0)]},
                   '-z': {'bay': 5.0, 'pilasters': False, 'bands': False, 'storey': 4.0, 'base': 1.2, 'frame': 'frameL', 'base_mat': 'frame2', 'doors': [8.0]},
                   '-x': {'bay': 5.0, 'pilasters': False, 'bands': False, 'storey': 4.0, 'base': 1.2}},
            roof={'parapet': 0.0, 'mat': 'panel2'}, post=0.5, frame='frameL')   # v3: light trim (was gunmetal frame2 posts and frames)
    # roof: a raised ring plinth for the azimuth drum, the deck railing, roof boxes at the corners
    B.vcyl(13.0, 0.8, (BX, BH, BZ), mat='frame2', n=48)
    B.vcyl(13.6, 0.25, (BX, BH, BZ), mat='frame', n=48)
    K.railing(B, [(BX + BW / 2 - 0.6, BH + 0.1, BZ - BD / 2 + 3.2), (BX + BW / 2 - 0.6, BH + 0.1, BZ + BD / 2 - 3.2),
                  (BX + BW / 2 - 3.2, BH + 0.1, BZ + BD / 2 - 0.6), (BX - BW / 2 + 3.2, BH + 0.1, BZ + BD / 2 - 0.6),
                  (BX - BW / 2 + 0.6, BH + 0.1, BZ + BD / 2 - 3.2), (BX - BW / 2 + 0.6, BH + 0.1, BZ - BD / 2 + 3.2),
                  (BX - BW / 2 + 3.2, BH + 0.1, BZ - BD / 2 + 0.6), (BX + BW / 2 - 3.2, BH + 0.1, BZ - BD / 2 + 0.6)],
              closed=True)
    for (x, z) in ((9.0, 11.5), (-9.0, -11.5), (9.0, -11.5)):
        K.roof_box(B, (x, BH + 0.1, z), w=2.2, d=1.8, h=1.2)
    # the dish on its alt-az mount (fal component), standing on the ring plinth
    a = math.radians(DISH_HEADING)
    K.component(B, 'dishMount', (BX - DISH_FOOT_X * math.cos(a), BH + 0.8, BZ + DISH_FOOT_X * math.sin(a)), heading=DISH_HEADING, scale=DISH_SCALE)

    # --- stair tower and annex on the +Z end (the concept's left), utility box on the -Z end
    K.block(B, (-2.0, 0.0, BD / 2 + 3.5), (12.0, 6.0, 7.0),
            sides={'+z': {'bay': 4.0, 'pilasters': False, 'doors': [8.5], 'louvres': [(3.0, 2.2, 2.4, 1.6)]},
                   '+x': {'bay': 3.5, 'pilasters': False, 'windows': [0], 'win': (1.2, 1.0)}},
            roof={'parapet': 0.35, 'units': [('hvac', -2.0, 0.0, {'w': 3.0, 'd': 2.0})]}, frame='frame2')
    K.block(B, (7.0, 0.0, BD / 2 + 2.5), (5.0, 11.5, 5.0),
            sides={'+x': {'bay': 2.5, 'storey': 3.8, 'pilasters': False, 'louvres': [(2.5, 1.5, 2.6, 3.0), (2.5, 6.0, 2.6, 3.0)]},
                   '+z': {'bay': 2.5, 'storey': 3.8, 'pilasters': False, 'windows': [1, 2], 'win': (1.0, 1.0)}},
            roof={'parapet': 0.3, 'units': [('antenna', 0.5, 0.5, {'h': 4.0})]}, frame='frame2')
    K.stair(B, (BW / 2 - 1.0, 0.0, BD / 2 - 2.0), (0, 0, -1), 4.0, w=1.2)
    K.vtank(B, (11.5, BD / 2 + 2.0), 1.3, 5.5, top='dome', mat='panel2', bands=[(1.0, 1.3, 'frame')])
    K.block(B, (3.0, 0.0, -BD / 2 - 2.5), (6.0, 5.0, 5.0),
            sides={'+x': {'bay': 3.0, 'pilasters': False, 'doors': [2.8]}, '-z': {'bay': 3.0, 'pilasters': False, 'louvres': [(3.0, 1.5, 2.4, 1.6)]}},
            roof={'parapet': 0.3}, frame='frame2')
    # cryo plant beside the base (catalogue components) and its line up the wall
    K.component(B, 'filterBank', (BW / 2 + 4.0, 0.0, -18.5), heading=0.0)
    K.htank(B, (-BW / 2 - 4.0, 2.0), 1.4, 8.0, axis=(0, 0, 1), band='cobalt')
    K.pipe(B, [(BW / 2 + 2.6, 1.2, -15.6), (BW / 2 + 2.6, 1.2, -13.0), (BW / 2 + 0.6, 1.2, -13.0), (BW / 2 + 0.6, 9.0, -13.0)], r=0.25, rings=True)
    K.pipe(B, [(-BW / 2 - 1.5, 1.4, 2.0), (-BW / 2 - 0.4, 1.4, 2.0), (-BW / 2 - 0.4, 9.0, 2.0)], r=0.3, rings=True)
    K.cable_tray(B, (BW / 2 + 0.4, 8.5, -12.0), (BW / 2 + 0.4, 8.5, 6.0))

    # --- dressing and lights
    for (x, z, r) in ((BW / 2 + 1.0, -16.5, -90.0), (BW / 2 + 1.0, -18.5, -90.0), (-BW / 2 - 1.0, -10.0, 90.0)):
        K.cabinet(B, (x, 0.0, z), rot=r)
    K.hvac(B, (BW / 2 + 2.5, 0.0, 2.0), w=2.4, d=1.6, h=1.6, fans=1, rot=90.0)
    K.bollards(B, [(BW / 2 + 1.5, -1.5), (BW / 2 + 1.5, -8.5), (BW / 2 + 6.0, 16.0), (BW / 2 + 6.0, -24.0)])
    K.crate(B, (BW / 2 + 6.5, 0.0, 14.0), (1.4, 1.1, 1.4))
    K.crate(B, (BW / 2 + 6.7, 0.0, 12.2), (1.2, 0.9, 1.2), mat='cobalt')
    for (x, z, rot) in ((CX + W / 2 - 1.5, CZ + D / 2 - 1.5, 45), (CX + W / 2 - 1.5, CZ - D / 2 + 1.5, -45)):
        K.lamp_post(B, (x, 0.0, z), h=7.0, arm=1.0, rot=rot)
    for (x, z, hd) in ((BW / 2 + 3.5, -4.0, 80), (BW / 2 + 5.0, 18.0, 250)):
        K.worker(B, (x, 0.0, z), heading=hd)
    for (x, z) in ((BX + BW / 2 - 1.0, BZ + BD / 2 - 1.0), (BX + BW / 2 - 1.0, BZ - BD / 2 + 1.0)):
        B.R.pin((x + 0.6, 1.0, z))
    B.R.beacon((7.0, 11.5 + 4.6, BD / 2 + 3.0))
    K.flood_on_wall(B, (BX - BW / 2 - 0.05, 8.5, -6.0), (-1, 0, 0), (-24.0, 0.0, -10.0))
