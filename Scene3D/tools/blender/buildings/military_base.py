"""MILITARY_BASE: walled compound, two armoured vehicle hangars, command block, corner towers
(concept style-library/styles/cqs-fleet/images/buildings/military_base-concept.jpg).

Composed from fal components (assets/parts-colony: armouredHangar x2, commandBunker, guardTower x4, wallSegment,
gateHouse; README-colony.md catalogue) on the shared parametric kit (plinth, apron markings, barrier blocks, sheds,
fuel tank, masts, dressing, lights). The fleet's own V-31 ground vehicles are instanced at runtime by the module
(src/buildings/military_base.js, correction 26: show the actual unit), not baked here.
Built by colony_build.py:
    $PY tools/blender/buildings/colony_build.py military_base <work> [--tex 4096]

Frame: metres, plinth top y = 0, +Z front, +X left. The concept camera looks almost straight at the front wall from a
little to the front-left (az ~14, el ~27): the gate in the front wall a little left of centre, the two hangars at the
back corners opening onto the yard, the command block between them, a tower at every corner.
Sizes (real-world: 7 m walls, 2.4 m crew doors, a 6.5 m V-31 in the yard): compound 104 x 76 m on the wall line (the
concept's dense yard: the hangars and the bunker fill the back half), hangars 30 x 11 x 34 m, command bunker 30 x 19 x
30 m, walls 6.6 m, towers 17 m; slab 118 x 94 m.
"""
import bkit as K

SPEC = {
    'title': 'Military Base', 'gameId': 'MILITARY_BASE', 'group': 'military',
    'footprint': [118, 94], 'height': 22.0,
    'camera': {'az': 14, 'el': 28},
    'about': 'walled compound: blast walls with buttresses, a fortified gate, four corner towers, two armoured vehicle hangars and a stepped command bunker round a marked yard',
}

WX, WZ = 52.0, 38.0          # wall line half extents
GATE_X = -8.0                # gate centre on the front wall
SEG = 24.0                   # wallSegment length
HZ = -15.6                   # hangar centre (z): 40.8 m deep at scale 1.2, opening at z = 4.8
HX = 33.5                    # hangar centre (|x|): 36 m wide at scale 1.2, the outer flank set into the side wall
HS = 1.2                     # hangar scale: the concept's hangars stand about twice the wall height


def wall_run(B, a, b, fixed, axis, heading):
    """wallSegment components along one wall line from a to b (axis 'x' or 'z'); segments overlap to fit exactly."""
    L = b - a
    n = max(1, int(-(-L // SEG)))
    step = (L - SEG) / (n - 1) if n > 1 else 0.0
    for i in range(n):
        c = a + SEG / 2 + i * step if n > 1 else (a + b) / 2
        p = (c, 0.0, fixed) if axis == 'x' else (fixed, 0.0, c)
        K.component(B, 'wallSegment', p, heading=heading)


def model(B):
    W, D = SPEC['footprint']
    CZ = 1.5
    FZ = CZ + D / 2
    K.plinth(B, W, D, h=1.6, chamfer=3.0, slab=8.0, lamp_pitch=18.0, centre=(0.0, CZ),
             markings=[([(GATE_X - 6.0, FZ - 1.5), (GATE_X - 6.0, WZ + 4.0)], 0.25, 'amber'),
                       ([(GATE_X + 6.0, FZ - 1.5), (GATE_X + 6.0, WZ + 4.0)], 0.25, 'amber')],
             grates=[(GATE_X, WZ + 5.0, 10.0, 0.8), (30.0, WZ + 4.5, 2.2, 0.8), (-38.0, WZ + 4.5, 2.2, 0.8)],
             steps=[(30.0, FZ, '+z'), (-40.0, FZ, '+z')])
    # the yard and the outer apron read dark (the concept's grey-brown concrete), the slab kerb stays light
    B.box((2 * WX - 1.0, 0.03, 2 * WZ - 1.0), at=(0.0, 0.015, 0.0), mat='roof', bevel=0.0)
    for x in range(-48, 52, 8):
        B.box((0.08, 0.04, 2 * WZ - 2.0), at=(x, 0.03, 0.0), mat='seam', bevel=0.0)
    for z in range(-32, 36, 8):
        B.box((2 * WX - 2.0, 0.04, 0.08), at=(0.0, 0.03, z), mat='seam', bevel=0.0)

    # --- the wall: fal blast-wall segments round the compound, the fal gate in the front wall, a tower at each corner
    g0, g1 = GATE_X - 16.0, GATE_X + 16.0
    # the fal parts' front is their +X (Tripo H3.1 frame, catalogue note): heading = outward direction - 90
    wall_run(B, -WX + 3.0, g0, WZ, 'x', -90.0)
    wall_run(B, g1, WX - 3.0, WZ, 'x', -90.0)
    wall_run(B, -WX + 3.0, WX - 3.0, -WZ, 'x', 90.0)
    wall_run(B, -WZ + 3.0, WZ - 3.0, WX, 'z', 0.0)
    wall_run(B, -WZ + 3.0, WZ - 3.0, -WX, 'z', 180.0)
    K.component(B, 'gateHouse', (GATE_X, 0.0, WZ), heading=-90.0)
    for sx in (-1, 1):
        for sz in (-1, 1):
            K.component(B, 'guardTower', (sx * WX, 0.0, sz * WZ), heading=45.0 * sx * (1 if sz > 0 else 3), scale=0.85)
            B.R.pin((sx * (WX + 4.2), 1.2, sz * (WZ + 4.2)))
    # wall-top walkway lamps (pins on the coping along the front and the +X side)
    for x in (-40.0, -28.0, 14.0, 26.0, 38.0):
        B.R.pin((x, 6.9, WZ + 2.2))
    for z in (-24.0, -8.0, 8.0, 24.0):
        B.R.pin((WX + 2.2, 6.9, z))

    # --- inside: two armoured hangars at the back corners, the command bunker between them (fal components)
    for x in (-HX, HX):
        K.component(B, 'armouredHangar', (x, 0.0, HZ), heading=-90.0, scale=HS)
        for sx in (-1, 1):
            B.R.pin((x + sx * 12.5, 1.0, 5.4))
            B.R.pin((x + sx * 10.5, 7.0, 3.0))
    K.component(B, 'commandBunker', (0.0, 0.0, -21.5), heading=-90.0, scale=1.15)
    B.R.beacon((0.0, 22.4, -21.5))
    B.R.obstruction((1.0, 27.4, -22.5))

    # --- the yard: a raised inspection pad with angled barrier blocks, hangar bay lines, parking stripes
    PX, PZ = GATE_X + 6.0, 16.0
    B.box((20.0, 0.35, 11.0), at=(PX, 0.175, PZ), mat='concrete2', bevel=0.08)
    B.box((19.0, 0.05, 10.0), at=(PX, 0.36, PZ), mat='concrete', bevel=0.0)
    for (x, z, r) in ((-7.0, -2.5, 20), (-2.0, 1.5, -15), (3.0, -2.0, 10), (6.5, 2.0, 30), (-6.0, 2.8, -25)):
        with B.at(at=(PX + x, 0.35, PZ + z), rot=(0, r, 0)):
            B.prism([(-1.2, -0.6), (1.2, -0.6), (0.9, 0.6), (-0.9, 0.6)], 0.0, 2.0, mat='panel2', bevel=0.06)
    for x in (-HX, HX):
        for sx in (-1, 1):
            B.bar((x + sx * 9.5, 0.05, 0.5), (x + sx * 9.5, 0.05, 24.0), 0.25, 0.012, mat='amber', bevel=0.0)
        B.bar((x - 9.5, 0.05, 24.0), (x + 9.5, 0.05, 24.0), 0.25, 0.012, mat='amber', bevel=0.0)
    B.bar((-46.0, 0.05, 29.0), (46.0, 0.05, 29.0), 0.2, 0.012, mat='white', bevel=0.0)
    B.bar((-12.0, 0.05, -4.0), (12.0, 0.05, -4.0), 0.2, 0.012, mat='white', bevel=0.0)
    # guard hut inside the gate, a store shed against the +X wall, a fuel tank on saddles and its pump cabinet
    K.block(B, (GATE_X - 21.0, 0.0, 30.0), (7.0, 4.0, 6.0),
            sides={'+z': {'bay': 3.5, 'doors': [2.0], 'windows': [0], 'win': (1.4, 1.0)},
                   '+x': {'bay': 3.0, 'windows': [0], 'win': (1.4, 1.0)}},
            roof={'parapet': 0.3, 'units': [('antenna', 1.5, 1.0, {'h': 5.0})]})
    for (x, z, h) in ((44.0, 14.0, 1.3), (44.0, 16.0, 1.3), (45.8, 15.0, 1.1), (44.0, 18.5, 1.3)):
        K.crate(B, (x, 0.0, z), (1.7, h, 1.7))
    K.container(B, (44.0, 0.0, 24.0), heading=0.0)
    K.htank(B, (-44.0, 18.0), 1.6, 10.0, axis=(0, 0, 1))
    K.pipe(B, [(-44.0, 1.4, 12.5), (-44.0, 1.4, 9.0), (-40.0, 1.4, 9.0), (-40.0, 1.4, 6.0)], r=0.25, rings=True, supports=True)
    K.valve(B, (-42.0, 1.4, 9.0), (1, 0, 0), r=0.25)
    K.cabinet(B, (-40.0, 0.0, 5.0), w=1.6, h=1.6, d=0.8)
    # dressing: crates and containers at the hangar mouths, cabinets, bollards, lamp posts, workers, a truck outside
    for (x, z) in ((-23.0, 2.0), (-22.0, 4.0), (23.5, 2.5), (24.5, 4.5), (46.0, 2.0), (-46.0, 3.0), (-15.0, -3.0), (15.5, -2.5)):
        K.crate(B, (x, 0.0, z), (1.6, 1.3, 1.6))
    K.crate(B, (-20.5, 0.0, 2.5), (1.4, 1.0, 1.4), mat='amber')
    K.container(B, (-45.0, 0.0, 28.0), heading=90.0)
    for (x, z, r) in ((-48.0, 32.0, 90.0), (-48.0, 30.0, 90.0), (48.0, 30.0, -90.0)):
        K.cabinet(B, (x, 0.0, z), rot=r)
    K.bollards(B, [(GATE_X - 7.5, WZ - 4.5), (GATE_X + 7.5, WZ - 4.5), (GATE_X - 7.5, WZ + 6.5), (GATE_X + 7.5, WZ + 6.5)])
    for (x, z, rot) in ((-20.0, 6.0, 180), (20.0, 6.0, 180), (-36.0, 28.0, 135), (34.0, 28.0, -135)):
        K.lamp_post(B, (x, 0.0, z), h=9.0, arm=1.2, rot=rot)
    for (x, z, hd) in ((GATE_X - 3.0, WZ - 4.0, 180), (GATE_X + 3.5, WZ - 3.5, 160), (-27.0, 3.0, 20),
                       (28.0, 3.5, 200), (5.0, -3.0, 0), (18.0, 20.0, 90)):
        K.worker(B, (x, 0.0, z), heading=hd)
    B.R.beacon((-HX, 13.8, HZ))
    B.R.beacon((HX, 13.8, HZ))
