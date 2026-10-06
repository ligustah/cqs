"""PROCESSING_PLANT: three tall banded process vessels, a low round tank, pipe manifolds, an armoured plant block
(concept style-library/styles/cqs-fleet/images/buildings/processing_plant-concept.jpg).

v2: composed from fal components (assets/parts-colony: processVessel x3, bandedLowTank, plantBlock, bottleSkid,
manifoldSkid, filterBank; README-colony.md catalogue) with the shared parametric kit (plinth, pipe gallery, the big
elbowed transfer lines, dressing, lights). Built by colony_build.py:
    $PY tools/blender/buildings/colony_build.py processing_plant <work> [--tex 4096]

Frame: metres, plinth top y = 0, +Z front, +X left. The concept camera looks from the front-left (az ~52, el ~28):
the three vessels stand on the -X half (one at the back-left, one at the front-left, one forward of centre), the low
round tank sits at the back of the +X half, the armoured plant block in front of it with its cargo door on the +X
face, a steel pipe gallery runs along the -X edge.
Sizes (real-world, the concept's proportions against its doors and the 12 m vessels): slab 72 x 76 m; vessels
12.5 m across, 32 m to the antennas; low tank 28 m across, 13 m tall; plant block 26 x 16 m, 10 m tall.
"""
import math

import bkit as K

SPEC = {
    'title': 'Processing Plant', 'gameId': 'PROCESSING_PLANT', 'group': 'production',
    'footprint': [72, 76], 'height': 33.0,
    'camera': {'az': 52, 'el': 28},
    'about': 'three banded process vessels with cobalt bands, a low round storage tank, an armoured plant block, a steel pipe gallery and elbowed transfer lines',
}

W, D = SPEC['footprint']
X0, X1, Z0, Z1 = -W / 2, W / 2, -D / 2, D / 2
VES = {'A': (-23.0, 21.0), 'B': (-4.0, 9.0), 'C': (-18.0, -13.0)}
TANK = (15.0, -22.0)
BLK = (22.0, 15.0)


def gallery(B):
    """Steel pipe gallery along the -X edge (the concept's dark frame at the front-left): portal bents, two pipe
    levels, diagonal bracing, the big lines turning into the vessels."""
    x0, x1 = X0 + 2.0, X0 + 7.0
    zs = [34.0 - k * 7.0 for k in range(10)]
    for z in zs:
        for x in (x0, x1):
            B.box((0.55, 9.6, 0.55), at=(x, 4.8, z), mat='frame', bevel=0.03)
            B.box((1.0, 0.35, 1.0), at=(x, 0.17, z), mat='concrete2', bevel=0.03)
        for y in (4.8, 9.2):
            B.box((x1 - x0 + 0.8, 0.5, 0.45), at=((x0 + x1) / 2, y, z), mat='frame', bevel=0.02)
    for (a, b) in zip(zs[:-1], zs[1:]):
        B.rod((x0, 0.6, a), (x0, 4.6, b), 0.13, mat='frame', n=6)
        B.rod((x0, 5.0, b), (x0, 9.0, a), 0.13, mat='frame', n=6)
    for x in (x0, x1):
        for y in (4.8, 9.2):
            B.box((0.35, 0.5, zs[0] - zs[-1]), at=(x, y, (zs[0] + zs[-1]) / 2), mat='frame', bevel=0.02)
    for k, (x, r, m) in enumerate(((x0 + 0.9, 0.55, 'pipe'), (x0 + 2.2, 0.55, 'pipe'), (x0 + 3.5, 0.4, 'pipeDark'), (x0 + 4.4, 0.35, 'pipe'))):
        K.pipe(B, [(x, 5.3 + r, zs[0] + 1.5), (x, 5.3 + r, zs[-1] - 1.0)], r=r, mat=m)
    for k, (x, r) in enumerate(((x0 + 1.2, 0.45), (x0 + 2.6, 0.35), (x0 + 3.8, 0.35))):
        K.pipe(B, [(x, 9.7 + r, zs[0] + 1.0), (x, 9.7 + r, zs[-1] - 1.0)], r=r, mat='pipe' if k != 1 else 'pipeDark')
    K.ladder(B, (x1 + 0.3, 0.3, 30.5), (1, 0, 0), 9.4)
    for z in (zs[0], zs[-1]):
        for x in (x0, x1):
            B.R.pin((x - 0.4, 9.8, z))


def big_line(B, pts, r=1.1):
    """A big elbowed transfer line (the concept's fat light pipes) with flanges, amber rings and pipe shoes."""
    K.pipe(B, pts, r=r, mat='pipe', supports=True, support_pitch=7.0)


def model(B):
    K.plinth(B, W, D, h=1.5, chamfer=2.4, slab=7.0, lamp_pitch=16.0,
             markings=[([(X1 - 2.0, Z1 - 1.6), (X1 - 2.0, Z0 + 1.6)], 0.16, 'amber'), ([(X0 + 1.6, Z1 - 2.0), (X1 - 1.6, Z1 - 2.0)], 0.16, 'amber'),
                       ([(4.0, Z1 - 2.0), (4.0, 26.0), (12.0, 26.0)], 0.14, 'amber')],
             grates=[(-4.0, Z1 - 4.0, 3.0, 0.9), (X1 - 4.0, -2.0, 0.9, 3.0), (-14.0, 30.0, 1.2, 1.2)],
             steps=[(10.0, Z1, '+z'), (X1, 4.0, '+x')])

    # --- the three process vessels (fal component processVessel: off-white shell, cobalt band, stepped gunmetal head,
    # riser pipes), each on a dark ring pedestal
    for k, (x, z) in VES.items():
        K.component(B, 'processVessel', (x, 0.0, z), heading={'A': 20.0, 'B': -20.0, 'C': 40.0}[k])
        B.ring(8.2, 0.0, 0.0, 0.35, (x, 0, z), mat='concrete2', n=40)
        for a in range(6):
            t = math.radians(30 + 60 * a)
            B.R.pin((x + 7.9 * math.cos(t), 0.9, z + 7.9 * math.sin(t)))
    # platforms between the vessel heads and walkways linking them (the concept's high bridges)
    for (a, b) in (('A', 'B'), ('B', 'C')):
        (xa, za), (xb, zb) = VES[a], VES[b]
        dx, dz = xb - xa, zb - za
        L = math.hypot(dx, dz)
        ux, uz = dx / L, dz / L
        p0 = (xa + ux * 6.6, 24.5, za + uz * 6.6)
        p1 = (xb - ux * 6.6, 24.5, zb - uz * 6.6)
        K.catwalk(B, p0, p1, w=1.4)
        K.pipe(B, [(p0[0], 23.6, p0[2]), (p1[0], 23.6, p1[2])], r=0.45, mat='pipe', rings=True)

    # --- big transfer lines: from each vessel down and across to the plant block and the low tank
    big_line(B, [(VES['B'][0] + 6.8, 14.0, VES['B'][1] + 1.5), (VES['B'][0] + 9.0, 14.0, VES['B'][1] + 1.5), (VES['B'][0] + 9.0, 4.0, VES['B'][1] + 1.5),
                 (BLK[0] - 13.0, 4.0, VES['B'][1] + 1.5), (BLK[0] - 13.0, 4.0, BLK[1])], r=1.0)
    big_line(B, [(VES['C'][0] + 6.8, 16.0, VES['C'][1]), (VES['C'][0] + 10.0, 16.0, VES['C'][1]), (VES['C'][0] + 10.0, 5.0, VES['C'][1]),
                 (TANK[0] - 14.6, 5.0, VES['C'][1]), (TANK[0] - 14.6, 5.0, TANK[1] + 2.0), (TANK[0] - 14.6, 9.0, TANK[1] + 2.0)], r=1.1)
    big_line(B, [(VES['A'][0] + 4.0, 3.0, VES['A'][1] - 6.5), (VES['A'][0] + 4.0, 3.0, VES['B'][1] - 1.0), (VES['B'][0] - 6.8, 3.0, VES['B'][1] - 1.0)], r=0.9)
    big_line(B, [(VES['A'][0] - 6.7, 18.0, VES['A'][1]), (X0 + 4.5, 18.0, VES['A'][1]), (X0 + 4.5, 10.6, VES['A'][1])], r=0.8)
    big_line(B, [(VES['C'][0] - 6.7, 12.0, VES['C'][1]), (X0 + 4.5, 12.0, VES['C'][1]), (X0 + 4.5, 10.4, VES['C'][1])], r=0.8)
    big_line(B, [(TANK[0] + 14.4, 3.0, TANK[1] + 4.0), (X1 - 3.0, 3.0, TANK[1] + 4.0), (X1 - 3.0, 3.0, BLK[1] - 9.0), (BLK[0] + 4.0, 3.0, BLK[1] - 9.0)], r=0.7)
    gallery(B)
    # low fat lines at the vessels' feet, visible from the front (the concept's elbowed lines round the bases)
    big_line(B, [(VES['A'][0] + 6.0, 2.2, VES['A'][1] + 5.0), (VES['B'][0] - 2.0, 2.2, VES['A'][1] + 5.0), (VES['B'][0] - 2.0, 2.2, VES['B'][1] + 6.5)], r=0.8)
    big_line(B, [(VES['B'][0] + 4.5, 8.0, VES['B'][1] + 5.0), (VES['B'][0] + 4.5, 8.0, VES['B'][1] + 10.0), (BLK[0] - 12.0, 8.0, VES['B'][1] + 10.0), (BLK[0] - 12.0, 8.0, BLK[1] + 8.0), (BLK[0] - 8.2, 8.0, BLK[1] + 8.0)], r=0.75)
    big_line(B, [(VES['C'][0] + 5.0, 2.0, VES['C'][1] + 5.0), (VES['C'][0] + 5.0, 2.0, VES['B'][1] - 4.0), (VES['B'][0] - 5.5, 2.0, VES['B'][1] - 4.0)], r=0.7)
    K.component(B, 'filterBank', (-2.0, 0.0, Z1 - 4.0), heading=90.0)
    for (x, z) in ((-9.0, Z1 - 4.0), (-13.0, Z1 - 4.0)):
        K.hvac(B, (x, 0.0, z), w=3.0, d=2.2, h=1.8, fans=2, rot=0)
    # a manifold of smaller lines between vessel B and the block, at 2.2 m on shoes
    for k in range(4):
        K.pipe(B, [(VES['B'][0] + 7.0, 1.0 + 0.8 * k, VES['B'][1] + 6.0 + 1.0 * k), (BLK[0] - 14.5, 1.0 + 0.8 * k, VES['B'][1] + 6.0 + 1.0 * k),
                   (BLK[0] - 14.5, 1.0 + 0.8 * k, BLK[1] + 6.5)], r=0.3, mat='pipe' if k % 2 == 0 else 'pipeDark', rings=(k == 0))

    # --- low round tank (fal component bandedLowTank) at the back of the +X half
    K.component(B, 'bandedLowTank', (TANK[0], 0.0, TANK[1]), heading=30.0)
    B.ring(15.2, 14.6, 0.0, 0.3, (TANK[0], 0, TANK[1]), mat='concrete2', n=48)
    for a in range(8):
        t = math.radians(22.5 + 45 * a)
        B.R.pin((TANK[0] + 14.8 * math.cos(t), 13.6, TANK[1] + 14.8 * math.sin(t)))

    # --- armoured plant block (fal component plantBlock: cargo door on its long front, which faces +X here)
    K.component(B, 'plantBlock', (BLK[0], 0.0, BLK[1]), heading=0.0)
    for sx in (-1, 1):
        for sz in (-1, 1):
            B.R.pin((BLK[0] + sx * 8.2, 10.4, BLK[1] + sz * 13.2))
    B.R.beacon((BLK[0], 12.4, BLK[1] - 6.0))

    # --- skids: the bottle skid and an HVAC / chiller bank by the tank, filter and manifold skids, cabinets
    K.component(B, 'bottleSkid', (X1 - 7.0, 0.0, -3.0), heading=90.0)
    K.component(B, 'manifoldSkid', (5.0, 0.0, 26.0), heading=90.0)
    K.component(B, 'filterBank', (X1 - 5.0, 0.0, Z0 + 6.0), heading=-90.0)
    for k in range(3):
        K.hvac(B, (X1 - 4.0, 0.0, Z0 + 16.0 + k * 3.6), w=3.0, d=2.2, h=2.2, fans=2, rot=90)
    for (x, z, r) in ((X0 + 9.5, Z1 - 2.0, 0), (X0 + 12.0, Z1 - 2.0, 0), (X0 + 14.5, Z1 - 2.0, 0), (X1 - 1.8, 30.0, -90)):
        K.cabinet(B, (x, 0.0, z), w=1.6, h=2.0, d=0.8, rot=r)
    B.box((3.4, 2.8, 2.6), at=(X0 + 11.0, 1.4, 31.8), mat='frame2', bevel=0.06)          # transformer
    for k in range(6):
        B.box((0.1, 2.2, 2.2), at=(X0 + 9.25, 1.5, 30.8 + k * 0.4), mat='frame', bevel=0.0)
    K.bollards(B, [(X1 - 2.5, 26.0), (X1 - 2.5, 20.0), (X1 - 2.5, 10.0), (X1 - 2.5, 4.0), (13.0, Z1 - 2.5), (20.0, Z1 - 2.5),
                   (28.0, Z1 - 2.5), (-1.0, 12.0), (X0 + 8.0, 2.0), (X0 + 8.0, -12.0)])
    for (x, z, rot) in ((X1 - 1.0, Z0 + 1.5, -45), (X0 + 1.0, Z1 - 1.5, 135), (X1 - 1.0, Z1 - 1.5, -135)):
        K.lamp_post(B, (x, 0.0, z), h=7.5, arm=1.0, rot=rot)
    for (x, z, m) in ((X1 - 4.0, 32.0, 'frame2'), (X1 - 4.0, 34.0, 'cobalt'), (-2.0, -36.0, 'frame2')):
        K.crate(B, (x, 0.0, z), (1.4, 1.1, 1.3), mat=m)
    K.forklift(B, (X1 - 5.5, 0.0, 22.0), heading=250)
    for (x, z, hd) in ((X1 - 4.0, 12.0, 270), (8.0, Z1 - 4.0, 20), (-2.0, 20.0, 160), (X0 + 9.0, 0.0, 90)):
        K.worker(B, (x, 0.0, z), heading=hd)
    K.flood_on_wall(B, (X0 + 7.3, 8.5, 0.0), (1, 0, 0), (-8.0, 0.0, 16.0))
