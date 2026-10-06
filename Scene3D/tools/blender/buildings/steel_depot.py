"""STEEL_DEPOT: open-sided portal shed with an amber overhead crane over stacked beams
(concept style-library/styles/cqs-fleet/images/buildings/steel_depot-concept.jpg).

v2: composed from fal components (assets/parts-colony: portalColumn x4, overheadCrane, beamStack x14, roofMonitor x3
scaled as the roof lights; README-colony.md catalogue) with the shared parametric kit (plinth, runway columns and
beams, the roof and its deep front girder, the clad store at the back, dressing, lights). Built by colony_build.py:
    $PY tools/blender/buildings/colony_build.py steel_depot <work> [--tex 4096]

Frame: metres, plinth top y = 0, +Z front, +X left. The concept camera looks at the (+X, +Z) corner (az ~38, el
~26): a deep gunmetal girder spans the open front between two massive portal columns; the amber crane runs on runway
beams along Z over rows of beam stacks; the +X side is open under a truss at the front and closed by a clad store
with roller doors at the back.
Sizes (real-world, against the concept's crew doors and the stacks): slab 62 x 66 m; roof 20 m at the eaves over
56 x 54 m; crane 32 m span; stacks 12 m.
"""
import math

import bkit as K

SPEC = {
    'title': 'Steel Depot', 'gameId': 'STEEL_DEPOT', 'group': 'storage',
    'footprint': [62, 66], 'height': 24.0,
    'camera': {'az': 38, 'el': 26},
    'about': 'open-sided portal shed with a deep front girder on massive braced columns, an amber overhead crane over rows of stacked steel, a clad store with roller doors at the back',
}

W, D = SPEC['footprint']
X0, X1, Z0, Z1 = -W / 2, W / 2, -D / 2, D / 2
RX0, RX1, RZ0, RZ1 = -28.0, 28.0, -30.0, 22.0       # roof
EAVE = 20.0
RUN = (-25.0, 24.0)                                 # crane runway lines (x)
RUN_Y = 11.5
STORE = (8.5, 28.0, -30.0, -4.0)                    # clad store x0, x1, z0, z1


def slab_tone(B):
    B.box((W - 1.2, 0.004, D - 1.2), at=(0.0, 0.002, 0.0), mat='concrete2', bevel=0.0)


def frame(B):
    # the four massive portal columns at the roof corners (fal component portalColumn, 22 m with its clad cap)
    for (x, z, hd) in ((RX0 + 2.0, RZ1 - 1.5, 90.0), (RX1 - 2.0, RZ1 - 1.5, -90.0), (RX0 + 2.0, RZ0 + 2.0, 90.0)):
        K.component(B, 'portalColumn', (x, 0.0, z), heading=hd)
        for y in (6.0, 12.0):
            B.R.pin((x + (2.0 if x > 0 else -2.0), y, z + 1.8))
    # runway columns and beams along Z on both crane lines, knee braces
    zs = [RZ1 - 13.0, RZ1 - 25.0, RZ1 - 37.0, RZ0 + 3.0]
    for x in RUN:
        zr0 = RZ0 + 2.0 if x < 0 else STORE[3] + 0.5
        for z in [z for z in zs if z >= zr0 - 0.1] + ([zr0] if x > 0 else []):
            B.box((1.1, EAVE, 1.1), at=(x, EAVE / 2, z), mat='frame', bevel=0.05)
            B.box((1.8, 0.4, 1.8), at=(x, 0.2, z), mat='concrete2', bevel=0.03)
            B.box((1.6, 0.6, 1.2), at=(x + (0.9 if x < 0 else -0.9), RUN_Y - 0.6, z), mat='frame', bevel=0.03)
        B.box((0.9, 1.2, RZ1 - zr0), at=(x + (0.9 if x < 0 else -0.9), RUN_Y, (zr0 + RZ1) / 2), mat='frame2', bevel=0.03)
        B.box((0.2, 0.2, RZ1 - zr0), at=(x + (0.9 if x < 0 else -0.9), RUN_Y + 0.7, (zr0 + RZ1) / 2), mat='pipe', bevel=0.0)
    # X bracing in the -X side bays (the concept's crossed side frames) and between the front column and the first bent
    for (za, zb) in ((RZ1 - 1.5, RZ1 - 13.0), (RZ1 - 25.0, RZ1 - 37.0)):
        B.rod((RX0 + 2.0, 1.0, za), (RX0 + 2.0, RUN_Y - 1.0, zb), 0.2, mat='frame', n=6)
        B.rod((RX0 + 2.0, 1.0, zb), (RX0 + 2.0, RUN_Y - 1.0, za), 0.2, mat='frame', n=6)
    # the deep front girder (dark box beam, light clad top band) and the side girders
    B.box((RX1 - RX0, 2.4, 1.6), at=(0.0, EAVE - 0.6, RZ1), mat='frame', bevel=0.06)
    B.box((RX1 - RX0 + 0.4, 1.6, 1.8), at=(0.0, EAVE + 1.4, RZ1), mat='panel', bevel=0.05)
    B.box((RX1 - RX0 + 0.6, 0.3, 2.0), at=(0.0, EAVE + 2.3, RZ1), mat='frame', bevel=0.03)
    for x in (RX0, RX1):
        B.box((1.4, 2.6, RZ1 - RZ0), at=(x, EAVE - 0.7, (RZ0 + RZ1) / 2), mat='frame', bevel=0.05)
        B.box((1.6, 1.6, RZ1 - RZ0 + 0.4), at=(x, EAVE + 1.4, (RZ0 + RZ1) / 2), mat='panel', bevel=0.05)
    # open +X side at the front: a truss girder at the eaves between the corner column and the store
    K.truss(B, (RX1 - 0.5, EAVE - 3.6, RZ1 - 2.0), (RX1 - 0.5, EAVE - 3.6, STORE[3]), 2.4, bay=3.0, chord=0.3, web=0.14)
    B.box((1.0, EAVE, 1.0), at=(RX1 - 0.5, EAVE / 2, STORE[3] + 0.5), mat='frame', bevel=0.05)
    # roof: light deck with standing seams, three roof lights (the fal roof monitor, scaled), roof units at the back
    B.box((RX1 - RX0, 0.5, RZ1 - RZ0), at=(0.0, EAVE + 0.75, (RZ0 + RZ1) / 2), mat='panel2', bevel=0.04)
    for k in range(int((RX1 - RX0) / 1.6)):
        B.box((0.06, 0.08, RZ1 - RZ0 - 0.4), at=(RX0 + 0.8 + k * 1.6, EAVE + 1.04, (RZ0 + RZ1) / 2), mat='frame2', bevel=0.0)
    for x in (-17.0, -1.0, 15.0):
        K.component(B, 'roofMonitor', (x, EAVE + 1.0, (RZ0 + RZ1) / 2 - 2.0), heading=0.0, scale=0.7)
    for (x, z) in ((22.0, -24.0), (22.0, -18.5), (-22.0, -25.0), (4.0, -25.0)):
        K.hvac(B, (x, EAVE + 1.0, z), w=3.2, d=2.2, h=1.6, fans=2, rot=90)
    K.railing(B, [(RX1 - 0.6, EAVE + 1.0, RZ0 + 1.0), (RX1 - 0.6, EAVE + 1.0, STORE[3])], post=2.0)
    # under-roof lights: warm down-light boxes along the runway and the bay
    for z in range(int(RZ0) + 6, int(RZ1), 10):
        for x in (-18.0, -6.0, 14.0):
            B.R.glowbox((x, EAVE - 0.3, z), (1.6, 0.05, 0.5), color='#ffd9a8', radiance=2.0)
    for (x, z) in ((RX0, RZ1), (RX1, RZ1), (0.0, RZ1)):
        B.R.pin((x, EAVE - 2.8, z + 0.9))


def store(B):
    """The clad store at the back of the +X side: light panels on a dark lower course, two roller doors and a crew
    door facing +X, a roller door into the bay (+Z), windows high up on the +X face."""
    x0, x1, z0, z1 = STORE
    K.block(B, ((x0 + x1) / 2, 0.0, (z0 + z1) / 2), (x1 - x0, EAVE - 0.2, z1 - z0), frame='frame2',
            sides={'+x': {'bay': 6.5, 'storey': 5.0, 'base': 1.2, 'windows': [3], 'win': (2.6, 1.6), 'win_per_bay': 1, 'bands': False,
                          'rollers': [(7.0, 5.5, 6.5), (16.0, 5.5, 6.5)], 'doors': [22.5]},
                   '+z': {'bay': 6.5, 'storey': 5.0, 'base': 1.2, 'bands': False, 'rollers': [(10.0, 5.5, 6.5)], 'doors': [3.0], 'windows': [3], 'win': (2.4, 1.4)},
                   '-x': {'bay': 6.5, 'bands': False}, '-z': {'bay': 6.5, 'bands': False}},
            roof={'deck': False}, corner_lamps=True)
    for (x, z) in ((x1 + 1.2, -26.0), (x1 + 1.2, -24.4), (x1 + 1.2, -6.0)):
        K.cabinet(B, (x, 0.0, z), rot=-90)
    B.box((2.0, 2.0, 2.0), at=(x1 + 1.6, 1.0, -9.6), mat='amber', bevel=0.05)
    K.stair(B, (x1 + 3.4, 0.0, -2.0), (-1, 0, 0), 1.2, w=1.2)


def yard(B):
    # rows of beam stacks under the crane (fal component beamStack, 12 m along X), some double-stacked
    rows = [(-19.0, 19.0, 1), (-19.0, 14.0, 2), (-19.0, 9.0, 1), (-19.0, 4.0, 2), (-19.0, -1.0, 1), (-19.0, -8.0, 2), (-19.0, -14.0, 1),
            (-4.0, 19.0, 2), (-4.0, 14.0, 1), (-4.0, 9.0, 2), (-4.0, 4.0, 1), (-4.0, -8.0, 1), (-4.0, -14.0, 2),
            (15.5, 17.0, 1), (15.5, 12.0, 2), (15.5, 7.0, 1), (15.5, 2.0, 1)]
    for (x, z, n) in rows:
        for k in range(n):
            K.component(B, 'beamStack', (x + 0.3 * k, 2.62 * k, z), heading=90.0)
    # loose sections and a part-loaded flatbed spot on the apron, bollards round the columns
    for k in range(5):
        B.box((12.0, 0.6, 0.35), at=(-4.0, 0.3 + 0.62 * (k // 2), -24.0 + (k % 2) * 0.6 + 0.4 * k), mat='frame2', bevel=0.02)
    for (x, z) in ((-4.0, -24.0),):
        for dx in (-4.5, 0.0, 4.5):
            B.box((0.5, 0.3, 2.8), at=(x + dx, 0.15, z + 1.0), mat='bark', bevel=0.02)
    K.bollards(B, [(RX0 + 4.6, RZ1 + 1.2), (RX0 + 4.6, RZ1 - 4.2), (RX1 - 4.6, RZ1 + 1.2), (RX1 - 4.6, RZ1 - 4.2), (RUN[1] - 1.2, RZ1 - 12.0), (RUN[1] - 1.2, RZ1 - 14.0),
                   (RX1 + 1.2, 6.0), (RX1 + 1.2, 12.0), (RX1 + 1.2, 18.0)])
    for (x, z) in ((RX1 - 3.5, RZ1 + 2.5), (RX1 - 1.6, RZ1 + 2.5)):
        B.box((1.4, 1.4, 1.4), at=(x, 0.7, z), mat='amber', bevel=0.05)
    for (x, z, rot) in ((X1 - 1.0, Z1 - 1.0, -135), (X0 + 1.0, Z1 - 1.0, 135), (X1 - 1.0, Z0 + 1.0, -45)):
        K.lamp_post(B, (x, 0.0, z), h=7.0, arm=1.0, rot=rot)
    for (x, z, m) in ((RX0 + 4.0, -20.0, 'frame2'), (RX0 + 4.0, -22.0, 'amber'), (RX0 + 4.0, 20.0, 'frame2')):
        K.crate(B, (x, 0.0, z), (1.4, 1.2, 1.4), mat=m)
    K.container(B, (RX1 - 6.0, 0.0, -1.0), heading=0.0)
    K.forklift(B, (8.0, 0.0, 18.0), heading=230)
    K.truck(B, (X1 - 2.5, 0.0, 6.0), heading=180)
    for (x, z, hd) in ((2.0, 20.0, 200), (-12.0, 18.5, 30), (RX1 + 2.0, 0.0, 270), (-20.0, -8.0, 90)):
        K.worker(B, (x, 0.0, z), heading=hd)


def model(B):
    K.plinth(B, W, D, h=1.5, chamfer=2.2, slab=8.0, lamp_pitch=15.0,
             markings=[([(X0 + 1.5, Z1 - 2.0), (X1 - 1.5, Z1 - 2.0)], 0.18, 'amber'), ([(X1 - 1.8, Z1 - 1.5), (X1 - 1.8, Z0 + 1.5)], 0.18, 'amber'),
                       ([(RUN[1] - 2.0, RZ1), (RUN[1] - 2.0, STORE[3] + 1.0)], 0.14, 'amber'), ([(RX0 + 4.0, RZ1), (RX0 + 4.0, RZ0 + 2.0)], 0.14, 'amber'),
                       ([(RX1 - 6.0, Z1 - 2.5), (RX1 - 1.0, Z1 - 2.5)], 0.3, 'hazard')],
             grates=[(0.0, Z1 - 3.5, 3.0, 0.9), (X1 - 3.0, -14.0, 0.9, 3.0)],
             steps=[(-16.0, Z1, '+z')])
    slab_tone(B)
    frame(B)
    # the amber crane over the stacks: span along X between the runway lines, cab toward +X
    K.component(B, 'overheadCrane', ((RUN[0] + RUN[1]) / 2, RUN_Y + 0.6 - 6.4, 17.0), heading=90.0, scale=[1.0, 1.5, 1.0])
    B.R.pin((RUN[1] - 2.0, RUN_Y - 1.0, 17.0))
    B.R.beacon(((RUN[0] + RUN[1]) / 2, RUN_Y + 3.0, 17.0))
    store(B)
    yard(B)
