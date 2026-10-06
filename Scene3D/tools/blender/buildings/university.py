"""UNIVERSITY: three faceted wings with observatory domes round a glazed faceted atrium and a front garden
(concept style-library/styles/cqs-fleet/images/buildings/university-concept.jpg).

Composed from fal components (assets/parts-colony: facetedWing x3, atriumHall, obsDome x2; README-colony.md catalogue) on
the shared parametric kit (plinth, glazed links, garden planters and pools, steps, radome, roof units, dressing, lights).
Built by colony_build.py:
    $PY tools/blender/buildings/colony_build.py university <work> [--tex 4096]

Frame: metres, plinth top y = 0, +Z front, +X left (the concept camera looks from the front-left, az ~31, el ~28): the
left wing stands at the front of the -X side, the right wing at the front of the +X side, the back wing behind the
atrium; the garden fills the front between the wings.
Sizes (the concept's proportions against its doors and figures): slab 120 x 74 m; wings 40 x 24 m, 17 m; atrium 34 m
across, 16 m; observatory domes 9 m on 10 m drums.
"""
import math

import bkit as K

SPEC = {
    'title': 'University', 'gameId': 'UNIVERSITY', 'group': 'science',
    'footprint': [112, 66], 'height': 30.0,
    'camera': {'az': 31, 'el': 28},
    'about': 'three faceted teaching wings with observatory domes and a radome round a glazed faceted atrium hall, glazed links, a terraced front garden',
}

WL = (-38.0, -6.0)      # left wing centre (long along X)
WR = (34.0, 12.0)       # right wing centre
WB = (6.0, -21.0)       # back wing centre
AT = (-3.0, -3.0)       # atrium centre
WH = 21.2               # wing roof height (the component's 15.7 m x 1.35)
WS = [0.8, 1.3, 1.35]   # wing scale (Blender part axes: length, depth, height): chunkier than the component, like the concept
WSB = [0.8, 1.2, 1.2]


def model(B):
    W, D = SPEC['footprint']
    FZ = D / 2
    K.plinth(B, W, D, h=1.5, chamfer=2.2, slab=7.0, lamp_pitch=15.0, centre=(0.0, 0.0),
             markings=[([(-W / 2 + 1.5, FZ - 1.5), (W / 2 - 1.5, FZ - 1.5)], 0.16, 'frame2')],
             grates=[(-24.0, FZ - 2.4, 2.4, 0.8), (16.0, FZ - 2.4, 2.4, 0.8), (W / 2 - 2.4, -20.0, 0.8, 2.4)],
             steps=[(-8.0, FZ, '+z'), (W / 2, -14.0, '+x')])

    # --- the three wings (fal facetedWing: battered stone walls, chamfered dark-finned corners, glazing bands), long axis
    # along X, the back one a little shorter
    K.component(B, 'facetedWing', (WL[0], 0.0, WL[1]), heading=0.0, scale=WS)
    K.component(B, 'facetedWing', (WR[0], 0.0, WR[1]), heading=0.0, scale=WS)
    K.component(B, 'facetedWing', (WB[0], 0.0, WB[1]), heading=0.0, scale=WSB)
    # --- the atrium (fal atriumHall: faceted glass roof, stone fins, glazed lit walls, entrance canopy) facing the garden
    K.component(B, 'atriumHall', (AT[0], 0.0, AT[1]), heading=270.0)     # canopy face (+X of the part) to the front
    # v3: the interior seen through the glazing reads blue-grey with warm lamps (v2: one flat 22 x 8 x 20 m amber box
    # showed through the glass as an amber-brown pane): a dim cool volume and a few small warm pendant lights
    B.R.glowbox((AT[0], 5.0, AT[1]), (22.0, 8.0, 20.0), color='#8fa6bf', radiance=0.07)
    for (dx, dz) in ((-6.0, -5.0), (6.0, -5.0), (-6.0, 5.0), (6.0, 5.0), (0.0, 0.0)):
        B.R.glowbox((AT[0] + dx, 8.5, AT[1] + dz), (1.2, 0.3, 1.2), color='#ffd29a', radiance=1.2)
    # glazed two-storey links between the atrium and the wings
    for (x0, x1, z) in ((WL[0] + 15.0, AT[0] - 15.0, -4.0), (AT[0] + 15.0, WR[0] - 15.0, 2.0)):
        xm, w = (x0 + x1) / 2, abs(x1 - x0) + 2.0
        B.box((w, 8.0, 10.0), at=(xm, 4.0, z), mat='frame2', bevel=0.05)
        B.box((w + 0.4, 0.5, 10.4), at=(xm, 8.2, z), mat='frame', bevel=0.03)
        K.glazing(B, (xm - w / 2 + 0.6, 0.8, z + 5.05), (1, 0, 0), w - 1.2, 6.4, mull=(1.6, 3.2))

    # --- roof furniture: the observatory domes (fal obsDome), a radome on the right wing, roof units, masts
    K.component(B, 'obsDome', (WL[0] - 6.0, WH, WL[1] - 2.0), heading=30.0)
    K.component(B, 'obsDome', (WB[0] + 2.0, 18.8, WB[1] - 2.0), heading=0.0, scale=0.6)
    rx, rz = WR[0] + 9.0, WR[1] - 3.0
    B.box((5.0, 2.4, 5.0), at=(rx, WH + 1.2, rz), mat='frame2', bevel=0.05)
    B.sphere(3.2, (rx, WH + 5.4, rz), mat='panel', n=20, rings=12)
    B.R.pin((rx + 2.6, WH + 2.6, rz + 2.6))
    for (x, z, kind, kw) in ((WR[0] - 8.0, WR[1] + 3.0, 'hvac', {'w': 3.4, 'd': 2.4}), (WR[0] - 2.0, WR[1] + 4.0, 'hvac', {'w': 3.4, 'd': 2.4}),
                             (WL[0] + 9.0, WL[1] + 3.0, 'hvac', {'w': 3.0, 'd': 2.2}), (WL[0] + 13.0, WL[1] - 4.0, 'vent', {}),
                             (WR[0] + 3.0, WR[1] - 6.0, 'antenna', {'h': 6.0}), (WB[0] - 8.0, WB[1], 'antenna', {'h': 7.0})):
        K.ROOF_UNITS[kind](B, (x, (18.9 if z < WB[1] + 3 else WH + 0.1), z), **kw)
    B.R.beacon((WR[0] + 3.0, WH + 6.2, WR[1] - 6.0))

    # --- the terraced front garden between the wings: paved court, planters with trees, two reflecting pools, steps,
    # benches, figures
    B.box((46.0, 0.3, 20.0), at=(-12.0, 0.15, 21.0), mat='concrete2', bevel=0.02)
    for k in range(3):
        B.box((14.0 - 2 * k, 0.18, 1.0), at=(-3.0, 0.3 + 0.09 + 0.18 * k, 13.2 - 0.5 * k), mat='concrete', bevel=0.0)
    for (x, z, w, d, t) in ((-28.0, 16.0, 8.0, 3.0, 2), (-20.0, 26.0, 7.0, 2.6, 2), (4.0, 24.0, 7.0, 3.0, 2),
                            (10.0, 15.5, 4.0, 3.0, 1), (-32.0, 27.0, 4.0, 2.4, 1), (-8.0, 29.0, 5.0, 2.4, 1), (-14.0, 15.5, 4.0, 2.4, 1)):
        K.planter(B, (x, z), w, d, h=0.9, trees=t)
    for (x, z, w, d) in ((-9.0, 21.0, 8.0, 4.0), (8.0, 29.5, 5.0, 2.6)):
        B.box((w + 0.6, 0.6, d + 0.6), at=(x, 0.6, z), mat='frame2', bevel=0.04)
        B.box((w, 0.05, d), at=(x, 0.88, z), mat='glassW', bevel=0.0)
        B.R.glowbox((x, 0.92, z), (w - 0.4, 0.02, d - 0.4), color='#7fb6c8', radiance=0.25)
    for (x, z) in ((-18.0, 21.0), (0.0, 18.0), (-30.0, 21.5)):
        B.box((2.6, 0.45, 0.6), at=(x, 0.75, z), mat='frame2', bevel=0.03)
    for (x, z) in ((-44.0, 14.0), (-50.0, 24.0), (-40.0, 27.0), (52.0, 28.0), (52.0, -10.0)):
        K.tree(B, (x, 0.0, z), h=6.5, r=2.0, seed=x)
    # --- dressing: utility boxes against the wings, bollards, lamp posts, workers (students), a van at the side door
    for (x, z) in ((-30.0, 6.2), (-27.5, 6.2), (24.0, 24.2), (44.0, 24.2)):
        B.box((2.2, 1.6, 1.4), at=(x, 0.8, z), mat='frame2', bevel=0.04)
        B.R.pin((x, 1.7, z + 0.75))
    K.bollards(B, [(x, FZ - 2.4) for x in (-40.0, -32.0, 14.0, 26.0, 40.0)])
    for (x, z, rot) in ((-54.0, 31.0, 135), (54.0, 31.0, -135), (54.0, -31.0, -45), (-54.0, -31.0, 45)):
        K.lamp_post(B, (x, 0.0, z), h=7.0, arm=1.0, rot=rot)
    K.truck(B, (52.0, 0.0, -16.0), heading=180.0)
    for (x, z, hd) in ((-10.0, 24.5, 30), (-8.5, 25.5, 210), (4.0, 22.0, 120), (-18.0, 16.5, 300), (10.0, 31.0, 180),
                       (-2.0, 12.0, 0), (24.0, 24.0, 250)):
        K.worker(B, (x, 0.3, z), heading=hd)
