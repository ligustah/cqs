"""RESIDENCE: curved terraced apartment blocks with balconies and roof gardens round a courtyard
(concept style-library/styles/cqs-fleet/images/buildings/residence-concept.jpg).

Composed from fal components (assets/parts-colony: curvedTerrace x3, podiumSegment x2; README-colony.md catalogue) on
the shared parametric kit (plinth, courtyard garden deck, planters, trees, paths, service blocks, dressing, lights).
Built by colony_build.py:
    $PY tools/blender/buildings/colony_build.py residence <work> [--tex 4096]

Frame: metres, plinth top y = 0, +Z front, +X left (the concept camera looks from the front-left, az ~31, el ~33).
The three curved blocks (balcony face on the component's +X side, rounded end tower at its +Z end) wrap the courtyard:
two on the diagonal from the front-left corner to the back, one down the +X side; the two-storey podium runs along the
street in front of the courtyard garden.
Sizes (the concept's proportions against its doors and storeys): slab 100 x 72 m; blocks 17 m deep, ~52 m long,
32 m (9-10 storeys at 3.2 m); podium 8 m (two storeys).
"""
import math

import bkit as K

SPEC = {
    'title': 'Residence', 'gameId': 'RESIDENCE', 'group': 'civic',
    'footprint': [100, 72], 'height': 33.0,
    'camera': {'az': 31, 'el': 33},
    'about': 'three curved 10-storey apartment blocks with balconies and roof gardens round a courtyard garden, a two-storey podium with entrances along the front',
}


def model(B):
    W, D = SPEC['footprint']
    FZ = D / 2
    K.plinth(B, W, D, h=1.4, chamfer=2.0, slab=6.0, lamp_pitch=14.0, centre=(0.0, 0.0),
             markings=[([(-W / 2 + 1.4, FZ - 1.2), (W / 2 - 1.4, FZ - 1.2)], 0.14, 'frame2')],
             grates=[(-36.0, FZ - 2.0, 2.0, 0.7), (0.0, FZ - 2.0, 2.0, 0.7), (W / 2 - 2.0, -10.0, 0.7, 2.0)],
             steps=[(-14.0, FZ, '+z'), (W / 2, 14.0, '+x')])

    # --- the three curved apartment blocks (fal curvedTerrace: balconies on its +X face, rounded tower at its +Z end),
    # wrapped round the courtyard like the concept: the tallest on the diagonal from the front-left corner to the back,
    # a lower one nested inside it, the third down the +X side with its rounded tower on the street; every balcony
    # face turned to the courtyard and the camera
    BL = ((-22.0, 0.0, -14.0, 315.0, 1.0), (1.0, 0.0, -9.0, 300.0, 0.82), (32.0, 0.0, 6.0, 0.0, 0.92))
    for (x, y, z, hd, sc) in BL:
        K.component(B, 'curvedTerrace', (x, y, z), heading=hd, scale=sc)
        B.R.beacon((x, 32.4 * sc, z))
    # --- the podium along the street in front of the courtyard (fal podiumSegment, entrance face turned to +Z)
    K.component(B, 'podiumSegment', (-20.0, 0.0, 29.0), heading=270.0)
    K.component(B, 'podiumSegment', (11.0, 0.0, 30.5), heading=270.0, scale=0.55)
    # --- the courtyard garden behind the podium: a raised deck, dense planters and trees, paths, benches
    B.box((50.0, 1.2, 22.0), at=(-11.0, 0.6, 12.0), mat='concrete2', bevel=0.05)
    B.box((50.3, 0.25, 22.3), at=(-11.0, 1.25, 12.0), mat='kerb', bevel=0.03)
    B.box((49.0, 0.06, 21.0), at=(-11.0, 1.38, 12.0), mat='concrete', bevel=0.0)
    B.prism([(-36.0, 1.0), (-8.0, -26.0), (8.0, -26.0), (8.0, 1.0)], 0.0, 1.2, mat='concrete2', bevel=0.05)
    for (x, z, w, d) in ((-11.0, 13.0, 46.0, 2.0), (-2.0, 0.0, 2.0, 20.0)):
        B.box((w, 0.04, d), at=(x, 1.39, z), mat='kerb', bevel=0.0)
    for (x, z, w, d, t) in ((-30.0, 8.0, 7.0, 4.0, 2), (-20.0, 6.0, 6.0, 4.0, 1), (-9.0, 4.0, 6.0, 4.0, 2), (4.0, 6.0, 5.0, 5.0, 2),
                            (-28.0, 18.0, 7.0, 4.0, 1), (-16.0, 18.5, 6.0, 4.0, 2), (-4.0, 18.5, 6.0, 4.0, 1), (8.0, 18.0, 5.0, 4.0, 2),
                            (-6.0, -8.0, 5.0, 5.0, 2), (2.0, -16.0, 4.0, 4.0, 1), (-14.0, -4.0, 4.0, 3.0, 1)):
        K.planter(B, (x, z), w, d, h=1.9, trees=t)
        B.R.pin((x + w / 2 + 0.2, 2.0, z + d / 2 + 0.2))
    for (x, z) in ((-24.0, 13.0), (-10.0, 13.0), (2.0, 11.0)):
        B.box((2.2, 0.45, 0.6), at=(x, 1.6, z), mat='frame2', bevel=0.03)
    K.stair(B, (16.0, 0.0, 12.0), (-1, 0, 0), 1.2, w=2.0)
    # lawns and free-standing trees between the planters (the concept's courtyard reads green and dense)
    for (x, z, w, d) in ((-24.0, 13.0, 8.0, 3.5), (-6.0, 12.0, 6.0, 3.0), (-2.0, -14.0, 6.0, 8.0), (-18.0, -2.0, 6.0, 4.0)):
        B.box((w, 0.08, d), at=(x, 1.42, z), mat='foliage', bevel=0.0)
    for k, (x, z) in enumerate(((-34.0, 13.0), (-20.0, 11.0), (-12.0, 9.0), (-1.0, 4.0), (10.0, 10.0), (-30.0, 3.0),
                                 (-10.0, -12.0), (4.0, -22.0), (-22.0, 22.0), (0.0, 22.0), (12.0, 22.0),
                                 (-32.0, 20.0), (-26.0, 4.0), (-16.0, 15.0), (-8.0, 20.0), (6.0, 2.0), (-4.0, -2.0),
                                 (2.0, -8.0), (-14.0, -9.0), (8.0, -14.0), (-6.0, 15.0))):
        K.tree(B, (x, 1.25, z), h=6.5 + (k % 3), r=2.2 + 0.4 * (k % 2), seed=k * 2.3)
    # street corner at the +X front: benches, planters, a kiosk
    for (x, z) in ((44.0, 33.0), (44.0, 27.0)):
        K.planter(B, (x, z), 3.0, 2.0, h=0.7, trees=1)
    B.box((3.0, 0.45, 0.7), at=(38.0, 0.45, 33.5), mat='frame2', bevel=0.04)
    # --- service blocks at the +X front corner and the back corners (utility, bins, plant)
    K.block(B, (46.0, 0.0, -28.0), (6.0, 7.0, 10.0),
            sides={'+x': {'bay': 3.3, 'rollers': [(5.0, 3.2, 3.4)]}},
            roof={'parapet': 0.4, 'units': [('fan', 0.0, -2.0, {}), ('fan', 0.0, 2.0, {})]})
    K.block(B, (-46.0, 0.0, 28.0), (5.0, 4.0, 8.0),
            sides={'+z': {'bay': 2.5, 'doors': [2.5]}, '-x': {'bay': 4.0, 'louvres': [(4.0, 1.2, 2.0, 1.8)]}},
            roof={'parapet': 0.3})
    # --- street dressing along the front and the +X side: planters, lamps, bollards, bins, figures, a van
    for (x, z) in ((-40.0, 34.0), (-12.0, 34.0), (16.0, 34.0), (30.0, 34.0)):
        K.planter(B, (x, z), 4.0, 1.2, h=0.6, trees=0)
    for (x, z) in ((47.0, 2.0), (47.0, -10.0)):
        K.planter(B, (x, z), 1.2, 4.0, h=0.6, trees=0)
    for (x, z, rot) in ((-49.0, 35.0, 135), (49.0, 35.0, -135), (49.0, -35.0, -45), (24.0, 34.6, 180), (-28.0, 34.6, 180)):
        K.lamp_post(B, (x, 0.0, z), h=5.5, arm=0.8, rot=rot)
    K.bollards(B, [(x, 35.0) for x in (-34.0, -20.0, -4.0, 10.0, 40.0)])
    for (x, z, r) in ((48.5, 30.0, -90.0), (48.5, 31.6, -90.0)):
        K.cabinet(B, (x, 0.0, z), w=1.2, h=1.4, d=0.8, rot=r, mat='frame2')
    for (x, z, hd) in ((-22.0, 35.0, 90), (-6.0, 34.5, 270), (38.0, 34.0, 180), (47.0, 20.0, 0), (-14.0, 11.0, 30), (6.0, 13.0, 200), (-25.0, 12.0, 120)):
        K.worker(B, (x, 1.38 if -36.0 < x < 14.0 and 1.0 < z < 23.0 else 0.0, z), heading=hd)
