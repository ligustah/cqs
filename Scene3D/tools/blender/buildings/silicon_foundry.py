"""SILICON_FOUNDRY: long fab hall under a sawtooth of roof monitors, a glazed bay showing a violet-lit crystal reactor
(concept style-library/styles/cqs-fleet/images/buildings/silicon_foundry-concept.jpg).

v2: composed from fal components (assets/parts-colony: roofMonitor x6, crystalReactor; README-colony.md catalogue)
with the shared parametric kit (plinth, the hall's facades with their dark lower course, the loading portal with its
roller door, the glazed reactor bay, pipe risers, ground plant, dressing, lights). Built by colony_build.py:
    $PY tools/blender/buildings/colony_build.py silicon_foundry <work> [--tex 4096]

Frame: metres, plinth top y = 0, +Z front, +X left. The concept camera looks from the front-left (az ~30, el ~33):
the long +Z facade carries the loading portal and, near the (+X, +Z) corner, the tall glazed bay with the reactor;
pipe risers come down the short +X face; six roof monitors run front to back over the hall.
Sizes (real-world, against the concept's doors and roller door): slab 80 x 56 m; hall 68 x 42 m, eaves 17 m, the
monitors 10 x 5.5 x 40 m on top; glazed bay 19 m wide, 15 m tall, 15 m deep; reactor 11 m.
"""
import math

import bkit as K

SPEC = {
    'title': 'Silicon Foundry', 'gameId': 'SILICON_FOUNDRY', 'group': 'production',
    'footprint': [80, 56], 'height': 23.0,
    'camera': {'az': 30, 'el': 33},
    'about': 'long clad fab hall under six roof monitors, a loading portal with a roller door, a tall glazed bay showing a violet-lit crystal reactor, pipe risers and ground plant',
}

W, D = SPEC['footprint']
X0, X1, Z0, Z1 = -W / 2, W / 2, -D / 2, D / 2
HX0, HX1, HZ0, HZ1 = -34.0, 34.0, -22.0, 20.0     # hall
EAVE = 17.0
GB = (9.0, 28.0, 5.0, 15.5)                        # glazed bay: x0, x1, depth (z from HZ1 - depth), height


def slab_tone(B):
    B.box((W - 1.2, 0.004, D - 1.2), at=(0.0, 0.002, 0.0), mat='concrete2', bevel=0.0)


def hall(B):
    gx0, gx1, gz0, gh = GB[0], GB[1], HZ1 - 15.0, GB[3]
    # core: the hall box minus the glazed bay pocket at the front (+Z) near the +X end
    B.boxp((HX0 + 0.2, 0.0, HZ0 + 0.2), (HX1 - 0.2, EAVE, gz0), mat='panel', bevel=0.06)
    B.boxp((HX0 + 0.2, 0.0, gz0), (gx0, EAVE, HZ1 - 0.2), mat='panel', bevel=0.06)
    B.boxp((gx1, 0.0, gz0), (HX1 - 0.2, EAVE, HZ1 - 0.2), mat='panel', bevel=0.06)
    B.boxp((gx0, gh, gz0), (gx1, EAVE, HZ1 - 0.2), mat='panel', bevel=0.06)
    # the long front facade, in two pieces either side of the glazed bay: dark 5 m lower course, big light panels
    fz = HZ1 - 0.1
    K.facade(B, (HX0 + 0.1, 0.0, fz), (1, 0, 0), gx0 - HX0 - 0.1, EAVE, bay=14.4, storey=5.0, base=5.0, bands=False, frame='frameL', base_mat='frame2',
             windows=[], rollers=[(25.5, 6.5, 7.0)], doors=[33.5, 6.0],
             louvres=[(6.5, 8.0, 5.5, 1.8), (16.0, 8.0, 5.5, 1.8), (9.0, 1.4, 6.0, 2.0), (39.0, 9.5, 2.4, 3.0)])
    K.facade(B, (gx1, 0.0, fz), (1, 0, 0), HX1 - gx1 - 0.1, EAVE, bay=6.0, pilasters=False, storey=5.0, base=5.0, bands=False, windows=[], frame='frameL', base_mat='frame2')
    # the loading portal: a deep dark surround projecting from the wall round the roller door, with a lit sign band
    px = HX0 + 0.1 + 25.5
    B.box((10.8, 1.4, 2.4), at=(px, 10.6, fz + 1.2), mat='frame2', bevel=0.08)
    for sx in (-1, 1):
        B.box((1.6, 10.0, 2.4), at=(px + sx * 4.6, 5.0, fz + 1.2), mat='frame2', bevel=0.08)
        B.box((0.5, 9.0, 0.3), at=(px + sx * 3.6, 4.5, fz + 2.3), mat='frame', bevel=0.02)
    B.box((8.0, 0.5, 0.6), at=(px, 9.6, fz + 2.3), mat='frame', bevel=0.02)
    B.R.glowbox((px, 8.4, fz + 0.6), (3.6, 0.18, 0.05), color='#ffc27a', radiance=1.4)
    # the +X short face: dark lower course, louvres, a crew door, the risers come down it
    K.facade(B, (HX1 - 0.1, 0.0, HZ1 - 0.1), (0, 0, -1), HZ1 - HZ0 - 0.2, EAVE, bay=14.0, storey=5.0, base=5.0, bands=False, frame='frameL', base_mat='frame2',
             windows=[], doors=[30.0], louvres=[(8.0, 9.0, 4.0, 1.8), (24.0, 1.4, 4.0, 2.0)])
    # back and -X faces: plainer
    K.facade(B, (HX0 + 0.1, 0.0, HZ0 + 0.1), (0, 0, 1), HZ1 - HZ0 - 0.2, EAVE, bay=7.0, storey=5.0, base=5.0, bands=False, frame='frameL', base_mat='frame2',
             windows=[], rollers=[(21.0, 5.5, 6.0)], doors=[12.0])
    K.facade(B, (HX1 - 0.1, 0.0, HZ0 + 0.1), (-1, 0, 0), HX1 - HX0 - 0.2, EAVE, bay=8.6, storey=5.0, base=5.0, bands=False, frame='frameL', base_mat='frame2',
             windows=[], rollers=[(14.0, 6.0, 7.0)], doors=[30.0, 50.0])
    # heavy corner posts and a dark pilaster dividing the long front into two volumes (the concept's break)
    for (x, z) in ((HX0, HZ0), (HX0, HZ1), (HX1, HZ0), (HX1, HZ1)):
        B.box((1.0, EAVE + 0.8, 1.0), at=(x, (EAVE + 0.8) / 2, z), mat='frame', bevel=0.06)
        B.R.pin((x + (0.6 if x > 0 else -0.6), EAVE + 0.4, z + (0.6 if z > 0 else -0.6)))
    B.box((1.4, EAVE + 1.2, 1.2), at=(-12.0, (EAVE + 1.2) / 2, HZ1 + 0.3), mat='frame', bevel=0.06)
    # roof: deck, a raised rim (parapet), six monitors front to back (louvres on their +X sides), roof plant
    K.roof_deck(B, (0.0, EAVE, (HZ0 + HZ1) / 2), (HX1 - HX0, HZ1 - HZ0), parapet=0.9)
    for k in range(6):
        x = HX0 + 5.7 + k * 11.3
        K.component(B, 'roofMonitor', (x, EAVE + 0.1, (HZ0 + HZ1) / 2), heading=0.0, scale=[0.9, 0.45, 1.0])   # part axes (x, y up, z): low monitors (v3)
    for (x, z) in ((HX1 - 2.0, HZ0 + 3.0), (HX0 + 2.5, HZ0 + 3.0), (HX1 - 2.0, HZ1 - 3.0)):
        K.hvac(B, (x, EAVE + 0.1, z), w=3.0, d=2.2, h=1.6, fans=2, rot=90)
    # the glazed bay: dark interior walls and floor, the reactor, an open mullion grid in a heavy frame (no glass
    # pane: the reactor must read through it), violet core light and a cool interior wash
    B.boxp((gx0, 0.0, gz0), (gx1, 0.15, HZ1), mat='frame2', bevel=0.0)
    B.boxp((gx0, 0.0, gz0), (gx1, gh, gz0 + 0.2), mat='interior', bevel=0.0)
    B.boxp((gx0, 0.0, gz0), (gx0 + 0.2, gh, HZ1), mat='panel2', bevel=0.0)
    B.boxp((gx1 - 0.2, 0.0, gz0), (gx1, gh, HZ1), mat='panel2', bevel=0.0)
    B.boxp((gx0, gh - 0.2, gz0), (gx1, gh, HZ1), mat='frame2', bevel=0.0)
    rx, rz = (gx0 + gx1) / 2, gz0 + 7.0
    K.component(B, 'crystalReactor', (rx, 0.15, rz), heading=0.0, scale=0.9)
    B.R.glowbox((rx, 6.4, rz), (2.4, 6.0, 2.4), color='#c2adff', radiance=4.5)
    B.R.glowbox((rx, gh / 2, gz0 + 0.3), (gx1 - gx0 - 1.0, gh - 1.0, 0.05), color='#ddd6ff', radiance=1.5)
    B.R.glowbox((rx, gh - 0.4, rz), (gx1 - gx0 - 2.0, 0.05, 10.0), color='#eeeaff', radiance=1.6)
    B.R.glowbox((rx, 0.2, rz + 3.0), (gx1 - gx0 - 2.0, 0.05, 8.0), color='#d6ccff', radiance=0.6)
    for (sx, h) in ((-1, 0), (1, 0)):
        B.R.glowbox((rx + sx * (w0 := (gx1 - gx0) / 2 - 0.3), gh / 2, rz), (0.05, gh - 2.0, 12.0), color='#e2dcff', radiance=0.7)
    for (x, z) in ((gx0 + 2.0, gz0 + 2.0), (gx1 - 2.0, gz0 + 2.0), (gx0 + 2.0, gz0 + 5.0)):
        K.cabinet(B, (x, 0.15, z), w=1.4, h=2.2, d=0.8)
    w = gx1 - gx0
    B.box((w + 1.6, 1.0, 1.4), at=(rx, gh + 0.5, HZ1 + 0.4), mat='frame', bevel=0.05)
    B.box((w + 1.6, 0.8, 1.4), at=(rx, 0.4, HZ1 + 0.4), mat='frame', bevel=0.05)
    for sx in (-1, 1):
        B.box((1.0, gh + 1.0, 1.4), at=(rx + sx * (w / 2 + 0.3), (gh + 1.0) / 2, HZ1 + 0.4), mat='frame', bevel=0.05)
    for k in range(1, 5):
        B.box((0.22, gh - 0.8, 0.3), at=(gx0 + w * k / 5, gh / 2, HZ1 + 0.3), mat='frame', bevel=0.0)
    for y in (5.0, 10.0):
        B.box((w, 0.2, 0.3), at=(rx, y, HZ1 + 0.3), mat='frame', bevel=0.0)
    for x in (gx0 - 0.6, gx1 + 0.6):
        B.R.slit((x, 4.0, HZ1 + 1.15), (0, 1, 0), (0, 0, 1), 1.2, 0.16)


def risers(B):
    """Three big pipe risers down the +X face from the roof into ground plant, two smaller ones, cabinets, chillers."""
    x = HX1 + 0.9
    for k, (z, r) in enumerate(((10.0, 0.7), (8.4, 0.7), (6.8, 0.55))):
        K.pipe(B, [(HX1 - 3.0, EAVE + 1.6, z), (x + 0.4 * k, EAVE + 1.6, z), (x + 0.4 * k, 2.2, z), (x + 3.0 + 0.4 * k, 2.2, z)], r=r, mat='pipe', rings=True)
        for y in (5.0, 11.0):
            B.box((1.2, 0.3, 0.3), at=(HX1 + 0.5, y, z), mat='frame', bevel=0.0)
    K.pipe(B, [(HX1 - 2.0, EAVE + 1.0, -4.0), (x, EAVE + 1.0, -4.0), (x, 1.2, -4.0), (x + 2.5, 1.2, -4.0)], r=0.35, mat='pipeDark', rings=False)
    for (z, w) in ((13.5, 2.6), (2.0, 2.6), (-1.5, 2.6), (-10.0, 3.0)):
        B.box((2.0, 2.4, w), at=(x + 3.8, 1.2, z), mat='panel2', bevel=0.05)
        B.box((2.2, 0.15, w + 0.2), at=(x + 3.8, 2.45, z), mat='frame', bevel=0.0)
        B.box((0.04, 2.0, 0.04), at=(x + 4.82, 1.2, z), mat='seam', bevel=0.0)
    for k in range(3):
        K.hvac(B, (x + 3.8, 0.0, -16.0 + k * 3.4), w=2.8, d=2.0, h=1.8, fans=1, rot=90)


def model(B):
    K.plinth(B, W, D, h=1.4, chamfer=2.0, slab=8.0, lamp_pitch=14.0,
             markings=[([(X0 + 1.5, Z1 - 1.6), (X1 - 1.5, Z1 - 1.6)], 0.16, 'amber'), ([(X1 - 1.6, Z1 - 1.5), (X1 - 1.6, Z0 + 1.5)], 0.16, 'amber'),
                       ([(-11.5, HZ1 + 0.6), (-11.5, Z1 - 2.0)], 0.3, 'hazard'), ([(-3.0, HZ1 + 0.6), (-3.0, Z1 - 2.0)], 0.3, 'hazard')],
             grates=[(-7.5, Z1 - 3.0, 4.0, 0.9), (X1 - 3.0, 2.0, 0.9, 2.4), (20.0, Z1 - 2.6, 2.4, 0.8)],
             steps=[(-26.0, Z1, '+z'), (X1, -14.0, '+x')])
    slab_tone(B)
    hall(B)
    risers(B)
    # wall lamps along the dark lower course (the concept's amber row) and the base of the +X face
    for x in range(-31, 34, 6):
        if not (GB[0] - 0.5 < x < GB[1] + 0.5):
            B.R.pin((x, 5.3, HZ1 + 0.3))
    for z in range(-19, 19, 6):
        B.R.pin((HX1 + 0.3, 5.3, z))
    # ground plant along the front: a row of cabinets and transformer boxes, bollards, lamp posts, workers, a truck
    for k in range(4):
        B.box((1.6, 2.0, 1.2), at=(HX0 + 3.0 + k * 1.8, 1.0, HZ1 + 1.4), mat='panel2', bevel=0.04)
        B.box((1.7, 0.12, 1.3), at=(HX0 + 3.0 + k * 1.8, 2.06, HZ1 + 1.4), mat='frame', bevel=0.0)
    for (x, z) in ((HX0 + 13.0, HZ1 + 1.4), (GB[1] + 2.5, HZ1 + 1.4), (GB[1] + 4.5, HZ1 + 1.4)):
        K.cabinet(B, (x, 0.0, z), w=1.4, h=1.9, d=0.8)
    K.bollards(B, [(-12.0, Z1 - 2.0), (-2.5, Z1 - 2.0), (-14.0, Z1 - 2.0), (GB[0] - 1.0, HZ1 + 2.0), (GB[1] + 1.0, HZ1 + 2.0), (X1 - 2.0, 18.0), (X1 - 2.0, 10.0)])
    for (x, z, rot) in ((X1 - 1.0, Z1 - 1.0, -135), (X0 + 1.0, Z1 - 1.0, 135), (X1 - 1.0, Z0 + 1.0, -45)):
        K.lamp_post(B, (x, 0.0, z), h=7.0, arm=1.0, rot=rot)
    K.forklift(B, (-6.0, 0.0, HZ1 + 4.0), heading=170)
    for (x, z, hd) in ((-9.0, Z1 - 3.0, 20), (14.0, Z1 - 2.5, 200), (X1 - 3.0, 4.0, 270), (GB[1] + 3.5, HZ1 + 3.5, 160)):
        K.worker(B, (x, 0.0, z), heading=hd)
    for (x, z, m) in ((X1 - 3.0, -24.0, 'frame2'), (X1 - 4.8, -24.0, 'violet'), (X0 + 3.0, -24.0, 'frame2')):
        K.crate(B, (x, 0.0, z), (1.4, 1.1, 1.3), mat=m)
    B.R.beacon((HX1 - 2.0, EAVE + 3.2, HZ1 - 3.0))
    B.R.beacon((HX0 + 2.5, EAVE + 3.2, HZ0 + 3.0))
