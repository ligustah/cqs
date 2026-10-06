"""TRADE_CENTER: two office towers joined by a glazed sky bridge, a covered market arcade between them, a dark
loading annex (concept style-library/styles/cqs-fleet/images/buildings/trade_center-concept.jpg).

Composed from fal components (assets/parts-colony: officeTower x2, skyBridge, marketArcade, loadingHall; README-colony.md
catalogue) on the shared parametric kit (plinth, podium and plaza blocks, planters, stairs, dressing, lights). Built by
colony_build.py:
    $PY tools/blender/buildings/colony_build.py trade_center <work> [--tex 4096]

Frame: metres, plinth top y = 0, +Z front, +X left (the concept camera looks from the front-left, az ~27, el ~27: the
long +Z plaza front and the short +X loading side are the visible faces).
Sizes (the concept's proportions measured against its doors, the truck and the slab): slab 120 x 58 m; towers 20 x 18 m
footprint, 50 m; bridge 9 m wide at 27-37 m spanning the 38 m between the towers; arcade 26 x 18 m, 9 m; loading annex
28 x 22 m, 10 m.
"""
import math

import bkit as K

SPEC = {
    'title': 'Trade Center', 'gameId': 'TRADE_CENTER', 'group': 'civic',
    'footprint': [112, 54], 'height': 52.0,
    'camera': {'az': 24, 'el': 26},
    'about': 'two 50 m office towers joined by a glazed sky bridge, a covered market arcade on the plaza between them, a dark loading annex with a truck',
}

TL = (-36.0, 1.0)       # left tower (screen left, -X) centre
TR = (20.0, 4.0)        # right tower centre
TW, TD = 21.0, 21.6     # tower footprint (x, z): the officeTower component
CX, CZ = 0.0, 0.0       # slab centre


def model(B):
    W, D = SPEC['footprint']
    FZ = CZ + D / 2
    X0, X1 = CX - W / 2, CX + W / 2
    K.plinth(B, W, D, h=1.5, chamfer=2.2, slab=6.0, lamp_pitch=14.0, centre=(CX, CZ),
             markings=[([(X0 + 1.4, FZ - 1.2), (X1 - 1.4, FZ - 1.2)], 0.16, 'frame2'),
                       ([(32.0, 21.0), (54.0, 21.0)], 0.3, 'hazard'), ([(32.0, 26.0), (54.0, 26.0)], 0.3, 'hazard')],
             grates=[(-10.0, FZ - 2.4, 2.4, 0.8), (6.0, FZ - 2.4, 2.4, 0.8), (-46.0, FZ - 2.4, 2.4, 0.8), (54.0, -12.0, 0.8, 2.4)],
             steps=[(-20.0, FZ, '+z'), (-50.0, -6.0, '-x')])

    # --- the two towers (fal officeTower: 50 m, dark glazed base, recessed lit window strips on two faces) on dark
    # podium plinths that tie them into the plaza
    for (x, z) in (TL, TR):
        K.component(B, 'officeTower', (x, 0.0, z), heading=0.0)
        B.box((TW + 3.0, 0.6, TD + 3.0), at=(x, 0.3, z), mat='frame2', bevel=0.05)
        for sx in (-1, 1):
            for sz in (-1, 1):
                B.R.pin((x + sx * (TW / 2 + 1.6), 0.8, z + sz * (TD / 2 + 1.6)))
        B.R.obstruction((x + 3.0, 50.6, z - 2.0))
        B.R.beacon((x - 4.0, 50.2, z + 3.0))
    # --- the sky bridge (fal skyBridge: glazed, dark girder) between the towers' inner faces at 27-38 m
    zb = (TL[1] + TR[1]) / 2
    xa, xb = TL[0] + TW / 2 - 1.5, TR[0] - TW / 2 + 1.5
    K.component(B, 'skyBridge', ((xa + xb) / 2, 27.0, zb), heading=90.0)
    B.R.glowbox(((xa + xb) / 2, 32.0, zb), (xb - xa - 2.0, 4.0, 8.6), color='#ffc27a', radiance=0.3)   # lit concourse
    for x in (xa + 2.0, xb - 2.0):          # dark collar plates where the bridge meets the towers
        B.box((1.2, 11.6, 11.6), at=(x, 32.8, zb), mat='frame', bevel=0.05)

    # --- the covered market arcade (fal marketArcade) on the plaza between the towers, a low glazed concourse behind it
    K.component(B, 'marketArcade', (-8.0, 0.0, 6.0), heading=0.0)
    # v3: warm pools under the canopy bays and over the stalls instead of one flat 22 x 16 m orange floor plane
    for (dx, dz) in ((-7.0, -4.0), (0.0, -4.5), (7.0, -4.0), (-7.0, 4.0), (0.0, 4.5), (7.0, 4.0)):
        B.R.glowbox((-8.0 + dx, 0.06, 6.0 + dz), (4.2, 0.03, 3.4), color='#ffc890', radiance=0.7)
        B.R.glowbox((-8.0 + dx, 8.2, 6.0 + dz), (1.8, 0.05, 0.5), color='#ffe2b8', radiance=2.2)
    K.block(B, (-8.0, 0.0, -13.0), (26.0, 7.0, 10.0),
            sides={'+z': {'bay': 4.3, 'storey': 3.5, 'windows': [0, 1], 'win': (2.6, 1.6), 'doors': [6.5, 19.5], 'seams': False},
                   '-z': {'bay': 4.3, 'storey': 3.5}, '+x': {'bay': 5.0}, '-x': {'bay': 5.0}},
            roof={'parapet': 0.5, 'units': [('hvac', -6.0, 0.0, {'w': 3.2, 'd': 2.2}), ('hvac', 5.0, 0.0, {'w': 3.2, 'd': 2.2}), ('vent', 10.0, 2.5, {})]})

    # --- the loading annex (fal loadingHall: dark ribbed hall, roller doors on its +X long face) against the right
    # tower, a low dispatch office in front of it, a truck at the front dock
    K.component(B, 'loadingHall', (42.0, 0.0, -6.0), heading=0.0, scale=1.25)
    K.block(B, (43.0, 0.0, 13.0), (14.0, 5.5, 9.0),
            sides={'+z': {'bay': 3.5, 'rollers': [(4.5, 3.6, 3.8)], 'doors': [10.5], 'windows': [], 'base': 0.6},
                   '+x': {'bay': 4.5, 'windows': [0], 'win': (1.6, 1.2), 'doors': [6.5]}},
            roof={'parapet': 0.4, 'units': [('hvac', -3.0, 0.0, {'w': 2.6, 'd': 1.8, 'fans': 1}), ('vent', 3.5, 1.5, {})]},
            frame='frame', panel='frame2')
    K.truck(B, (43.0, 0.0, 23.5), heading=90.0)
    K.forklift(B, (53.0, 0.0, 6.0), heading=200.0)
    for (cx, cz) in ((54.0, -18.0), (54.0, -16.2), (52.2, -17.1), (54.0, 13.0), (52.2, 13.0), (34.0, 18.5)):
        K.crate(B, (cx, 0.0, cz), (1.4, 1.1, 1.4))
    K.container(B, (52.5, 0.0, -24.0), heading=90.0)

    # --- plaza: planters with trees, benches, lit kiosks, steps, bollards, lamp posts, people
    for (x, z, w, d, t) in ((-48.0, 20.0, 5.0, 2.2, 1), (-38.0, 20.5, 4.0, 2.0, 1), (-26.0, 21.0, 4.0, 2.0, 1),
                            (-18.0, 21.5, 3.0, 2.0, 0), (2.0, 21.5, 4.0, 2.0, 1), (12.0, 21.5, 3.0, 2.0, 0), (24.0, 21.0, 4.0, 2.0, 1),
                            (-52.0, 6.0, 2.0, 5.0, 0), (-52.0, -10.0, 2.0, 5.0, 1), (-20.0, -20.0, 4.0, 2.0, 1), (4.0, -20.0, 4.0, 2.0, 1)):
        K.planter(B, (x, z), w, d, h=0.8, trees=t)
    for (x, z) in ((-44.0, 23.5), (-32.0, 24.0), (-10.0, 24.0), (8.0, 24.0), (18.0, 24.0)):
        B.box((3.0, 0.45, 0.7), at=(x, 0.45, z), mat='frame2', bevel=0.04)
        B.box((3.0, 0.1, 0.8), at=(x, 0.95, z), mat='panel2', bevel=0.02)
    for (x, z) in ((-2.0, 18.0), (-14.0, 18.0)):          # lit kiosks at the arcade front
        B.box((2.4, 2.4, 2.0), at=(x, 1.2, z), mat='frame2', bevel=0.04)
        B.box((2.8, 0.15, 2.4), at=(x, 2.5, z), mat='amber', bevel=0.02)
        B.R.glowbox((x, 1.4, z + 1.02), (1.8, 1.0, 0.04), color='#ffc27a', radiance=1.0)
    # a low seat wall along the front of the plaza and a stepped terrace before the arcade
    B.box((22.0, 0.9, 0.8), at=(-40.0, 0.45, 25.6), mat='concrete2', bevel=0.05)
    B.box((14.0, 0.9, 0.8), at=(15.0, 0.45, 25.6), mat='concrete2', bevel=0.05)
    for k in range(3):
        B.box((26.0 - 2 * k, 0.18, 1.2), at=(-8.0, 0.09 + 0.18 * k, 16.2 - 0.6 * k), mat='concrete', bevel=0.02)
    pts = [(x, 26.4) for x in (-50.0, -44.0, -36.0, -29.0, -24.0, -12.0, -4.0, 4.0, 10.0, 22.0, 28.0)]
    K.bollards(B, pts)
    for (x, z) in pts:
        B.R.pin((x, 1.05, z))
    for (x, z, rot) in ((-54.0, 25.0, 135), (-54.0, -25.0, 45), (54.0, -25.0, -45), (-22.0, 25.4, 180), (6.0, 25.4, 180), (30.0, 18.0, 180)):
        K.lamp_post(B, (x, 0.0, z), h=6.5, arm=0.9, rot=rot)
    for (x, z, r) in ((-55.0, -2.0, 90.0), (-55.0, 0.0, 90.0), (54.0, -10.0, -90.0)):
        K.cabinet(B, (x, 0.0, z), w=1.1, h=1.7, d=0.6, rot=r)
    for (x, z, hd) in ((-22.0, 22.5, 20), (-20.5, 23.0, 200), (-4.0, 20.5, 90), (6.0, 22.5, 250), (12.0, 24.0, 160),
                       (-38.0, 23.0, 0), (28.0, 22.0, 300), (52.0, 18.0, 270), (-12.0, 10.0, 120), (0.0, 8.0, 300), (-16.0, 4.0, 40)):
        K.worker(B, (x, 0.0, z), heading=hd)
    B.R.beacon((42.0, 10.4, -6.0))
