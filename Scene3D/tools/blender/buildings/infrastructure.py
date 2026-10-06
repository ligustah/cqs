"""INFRASTRUCTURE: cross-plan administration block round a domed command hub, a courtyard garden, a water tower and
utility skids (concept style-library/styles/cqs-fleet/images/buildings/infrastructure-concept.jpg).

Composed from fal components (assets/parts-colony: hubDrum, adminWing x4, waterTower, vesselSkid x3; README-colony.md
catalogue) on the shared parametric kit (plinth, entrance portico, garden planters, pipe runs, dressing, lights). Built
by colony_build.py:
    $PY tools/blender/buildings/colony_build.py infrastructure <work> [--tex 4096]

Frame: metres, plinth top y = 0, +Z front, +X left. The concept camera looks along the diagonal from the front-left
(az ~40, el ~30): the +Z and +X wings run towards the viewer either side of the courtyard garden in the +X/+Z quadrant,
whose entrance portico faces the camera; the water tower stands behind the +X wing at the back.
Sizes (the concept's proportions against its doors): slab 104 m square; wings 36 x 16 m, 9 m (two storeys); hub 26 m
across, drum to 17 m, masts to ~30 m; water tower 24 m; skids 13 x 5 m.
"""
import math

import bkit as K

SPEC = {
    'title': 'Infrastructure', 'gameId': 'INFRASTRUCTURE', 'group': 'civic',
    'footprint': [104, 104], 'height': 30.0,
    'camera': {'az': 40, 'el': 33},
    'about': 'cross-plan two-storey administration wings round a domed command hub with an antenna cluster, a courtyard garden and entrance portico, a water tower, utility vessel skids',
}

ARM = 30.0          # wing centre distance from the hub


def portico(B, c, rot, w=16.0, d=9.0, h=6.5):
    """Entrance portico turned `rot` degrees about +Y at c: dark flat-roofed porch on piers, glazed lit doors, steps."""
    x, z = c
    a = math.radians(rot)
    fwd = (math.sin(a), math.cos(a))
    with B.at(at=(x, 0.0, z), rot=(0, rot, 0)):
        B.box((w, 0.9, d + 1.0), at=(0, h - 0.45, 0.5), mat='frame', bevel=0.06)          # roof slab
        B.box((w + 0.4, 0.3, d + 1.4), at=(0, h + 0.1, 0.5), mat='panel2', bevel=0.04)
        B.box((w + 0.5, 0.5, 0.4), at=(0, h - 0.1, d / 2 + 1.1), mat='panel', bevel=0.04)
        B.box((w - 1.0, h - 0.9, 0.6), at=(0, (h - 0.9) / 2, -d / 2 + 0.3), mat='panel2', bevel=0.04)   # back wall
        B.box((w - 6.0, h - 2.2, 0.08), at=(0, (h - 2.2) / 2 + 0.2, -d / 2 + 0.65), mat='glassW', bevel=0.0)
        for k in range(1, 5):
            B.box((0.12, h - 2.2, 0.16), at=(-(w - 6.0) / 2 + (w - 6.0) * k / 5, (h - 2.2) / 2 + 0.2, -d / 2 + 0.7), mat='frame', bevel=0.0)
        for sx in (-1, 1):
            B.box((1.4, h - 0.9, 1.4), at=(sx * (w / 2 - 0.9), (h - 0.9) / 2, d / 2), mat='panel', bevel=0.05)    # front piers
            B.box((1.6, h - 0.9, d), at=(sx * (w / 2 - 0.8), (h - 0.9) / 2, 0.0), mat='panel', bevel=0.05)        # side walls
        for k in range(4):                                                                                          # steps
            B.box((w - 4.0 - k * 0.0, 0.18 * (4 - k), 0.32), at=(0, 0.09 * (4 - k), d / 2 + 1.2 + 0.32 * k), mat='concrete', bevel=0.0)
        for sx in (-1, 1):
            K.railing(B, [(sx * 2.5, 0.75, d / 2 + 1.0), (sx * 2.5, 0.05, d / 2 + 2.4)], h=0.95, post=2.0, mid=False)
    ca, sa = math.cos(a), math.sin(a)
    to = lambda lx, ly, lz: (x + lx * ca + lz * sa, ly, z - lx * sa + lz * ca)
    B.R.glowbox(to(0.0, (h - 2.2) / 2 + 0.2, -d / 2 + 0.3), (w - 6.0, h - 2.2, 0.05), color='#ffc27a', radiance=0.9, roty=rot)
    B.R.glowbox(to(0.0, h - 0.95, 0.5), (w - 3.0, 0.04, d - 1.0), color='#ffd29a', radiance=0.6, roty=rot)
    for sx in (-1, 1):
        B.R.pin(to(sx * (w / 2 - 0.9), h - 1.2, d / 2 + 0.75))
        B.R.pin(to(sx * (w / 2 - 0.3), h + 0.3, d / 2 + 1.2))


NOTCH = 14.0


def model(B):
    W, D = SPEC['footprint']
    # the concept's notched cross: a 14 m square cut from each corner, the arms run out under the wings
    K.plinth(B, W, D, h=1.5, chamfer=3.0, slab=8.0, lamp_pitch=16.0, centre=(0.0, 0.0), notch=(NOTCH, NOTCH),
             markings=[([(-W / 2 + NOTCH + 1.5, D / 2 - 1.5), (W / 2 - NOTCH - 1.5, D / 2 - 1.5)], 0.16, 'frame2'),
                       ([(W / 2 - 1.5, W / 2 - NOTCH - 1.5), (W / 2 - 1.5, -D / 2 + NOTCH + 1.5)], 0.16, 'frame2'),
                       ([(10.0, 49.0), (10.0, 33.0)], 0.14, 'white'), ([(49.0, 10.0), (33.0, 10.0)], 0.14, 'white')],
             grates=[(26.0, 45.0, 2.4, 0.8), (45.0, 26.0, 0.8, 2.4), (-20.0, 46.0, 2.4, 0.8), (46.0, -24.0, 0.8, 2.4)],
             steps=[(-30.0, D / 2, '+z'), (W / 2, -30.0, '+x')])

    # --- the command hub (fal hubDrum: dark octagonal base, ringed drum, antenna cluster) and the four wings (fal
    # adminWing: two storeys, rounded free end, ribbon windows, solar roof), long axis along their arm
    K.component(B, 'hubDrum', (0.0, 0.0, 0.0), heading=0.0)
    B.R.beacon((0.0, 31.0, 0.0))
    B.R.obstruction((1.5, 29.0, -1.0))
    for (x, z, hd, s) in ((0.0, ARM, 0.0, [1.0, 1.15, 1.0]), (ARM, 0.0, 90.0, [1.0, 1.15, 1.0]), (-ARM, 0.0, 270.0, [1.0, 1.15, 1.0]), (0.0, -ARM + 2.0, 180.0, 0.95)):
        K.component(B, 'adminWing', (x, 0.0, z), heading=hd, scale=s)
    # dark glazed link collars where the wings meet the hub
    for (x, z, w, d) in ((0.0, 12.5, 14.0, 3.0), (12.5, 0.0, 3.0, 14.0), (-12.5, 0.0, 3.0, 14.0), (0.0, -12.5, 14.0, 3.0)):
        B.box((w, 9.4, d), at=(x, 4.7, z), mat='frame', bevel=0.06)
        B.box((w + 0.4, 0.4, d + 0.4), at=(x, 9.6, z), mat='frame2', bevel=0.03)

    # --- the courtyard garden in the +X/+Z quadrant, the entrance portico facing the camera on its diagonal
    B.box((22.0, 0.25, 22.0), at=(21.0, 0.125, 21.0), mat='concrete2', bevel=0.02)
    for (x, z, w, d, t) in ((14.5, 22.0, 6.0, 9.0, 2), (24.0, 14.5, 9.0, 6.0, 2), (14.0, 14.0, 4.0, 4.0, 1)):
        K.planter(B, (x, z), w, d, h=0.9, trees=t)
    for (x, z) in ((19.0, 19.0), (22.0, 23.5)):
        B.box((2.4, 0.45, 0.6), at=(x, 0.45, z), mat='frame2', bevel=0.03)
    portico(B, (31.0, 31.0), 45.0, w=13.0, d=8.0, h=6.0)
    for k, (x, z) in enumerate(((12.0, 18.0), (18.0, 12.0), (20.0, 22.0), (22.0, 17.0), (13.0, 26.0), (26.0, 13.0))):
        K.tree(B, (x, 0.9, z), h=7.0 + (k % 2), r=2.4, seed=k * 1.9)
    for (x, z) in ((25.0, 37.5), (37.5, 25.0)):
        K.tree(B, (x, 0.0, z), h=6.0, r=1.8, seed=x)
        B.ring(1.6, 1.3, 0.0, 0.35, (x, 0, z), mat='concrete2', n=16)

    # --- utility skids (fal vesselSkid) on the front and left aprons, piped into the wings
    K.component(B, 'vesselSkid', (16.0, 0.0, 43.0), heading=90.0)
    K.component(B, 'vesselSkid', (43.0, 0.0, 16.0), heading=0.0)
    K.component(B, 'vesselSkid', (-22.0, 0.0, 40.0), heading=90.0, scale=0.9)
    K.pipe_rack(B, (16.0, 0, 48.5), (34.0, 0, 48.5), w=2.4, levels=(3.2,), pitch=6.0,
                pipes=[(0, -0.5, 0.3, 'pipe'), (0, 0.3, 0.25, 'pipeDark')])
    K.pipe_rack(B, (48.5, 0, 16.0), (48.5, 0, 34.0), w=2.4, levels=(3.2,), pitch=6.0,
                pipes=[(0, -0.5, 0.3, 'pipe'), (0, 0.3, 0.25, 'pipeDark')])
    K.pipe(B, [(9.5, 1.6, 43.0), (9.0, 1.6, 43.0), (9.0, 1.6, 40.0), (8.4, 3.0, 40.0)], r=0.45, supports=True, support_pitch=4.0)
    K.pipe(B, [(43.0, 1.6, 9.5), (43.0, 1.6, 9.0), (40.0, 1.6, 9.0), (40.0, 3.0, 8.4)], r=0.45, supports=True, support_pitch=4.0)
    K.pipe(B, [(-14.0, 2.4, 44.0), (-9.0, 2.4, 44.0), (-9.0, 2.4, 36.0), (-8.4, 4.5, 36.0)], r=0.55, supports=True, support_pitch=4.0)
    K.pipe(B, [(-8.4, 3.2, 20.0), (-12.0, 3.2, 20.0), (-12.0, 3.2, 8.4)], r=0.4, supports=True, support_pitch=4.0)
    for (x, z) in ((10.5, 37.0), (37.0, 10.5), (-15.0, 36.0)):
        K.cabinet(B, (x, 0.0, z), w=1.1, h=1.7, d=0.6, rot=0.0)

    # --- the water tower behind the +X wing (fal waterTower), its feed main to the hub
    K.component(B, 'waterTower', (34.0, 0.0, -32.0), heading=0.0)
    K.pipe(B, [(34.0, 0.6, -27.0), (34.0, 0.6, -18.0), (16.0, 0.6, -18.0), (16.0, 0.6, -9.0), (14.0, 2.0, -8.4)], r=0.5, supports=True, support_pitch=5.0)
    B.R.beacon((34.0, 25.0, -32.0))
    # back quadrants: generator housings, a container stack, cable trays
    K.block(B, (-30.0, 0.0, -30.0), (14.0, 5.0, 9.0),
            sides={'+z': {'bay': 3.5, 'rollers': [(4.0, 3.2, 3.6)], 'doors': [10.5], 'louvres': [(7.5, 1.4, 2.2, 2.0)]},
                   '+x': {'bay': 3.0, 'louvres': [(4.5, 1.4, 2.0, 2.0)]}},
            roof={'parapet': 0.4, 'units': [('fan', -3.0, 0.0, {}), ('fan', 0.0, 0.0, {}), ('fan', 3.0, 0.0, {}), ('vent', 5.0, 2.0, {})]})
    for (x, z) in ((-44.0, -22.0), (-44.0, -16.0)):
        K.container(B, (x, 0.0, z), heading=90.0)
    K.cable_tray(B, (-16.0, 6.0, -12.0), (-23.0, 6.0, -25.0))
    # --- dressing: bollards round the skids and the portico, lamp posts, cabinets, workers, a vehicle at the gate
    K.bollards(B, [(x, 49.0) for x in (6.0, 26.0, -30.0, -14.0)] + [(49.0, z) for z in (6.0, 26.0, -14.0)])
    for (x, z, rot) in ((-36.0, 50.0, 135), (50.0, 36.0, -135), (50.0, -36.0, -45), (-36.0, -50.0, 45)):
        K.lamp_post(B, (x, 0.0, z), h=7.0, arm=1.0, rot=rot)
    K.truck(B, (-36.0, 0.0, 22.0), heading=0.0)
    for (x, z, hd) in ((33.0, 38.0, 225), (36.5, 34.5, 45), (20.0, 26.0, 0), (24.0, 18.5, 120), (14.0, 47.0, 180), (46.0, 22.0, 270)):
        K.worker(B, (x, 0.0, z), heading=hd)
    K.flood_on_wall(B, (8.2, 7.0, 40.0), (1, 0, 0), (20.0, 0.0, 47.0))
