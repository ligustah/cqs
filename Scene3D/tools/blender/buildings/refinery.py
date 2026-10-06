"""REFINERY: three tall distillation columns in a lattice of pipe racks, a control block, horizontal tanks
(concept style-library/styles/cqs-fleet/images/buildings/refinery-concept.jpg).

v2: composed from fal components (assets/parts-colony: distColumn x3 at three heights, htankSkid x2, manifoldSkid,
filterBank; README-colony.md catalogue) with the shared parametric kit (plinth, control block and its dark annex, the
two-level pipe rack with amber railed decks, column risers, pipe runs, dressing, lights). Built by colony_build.py:
    $PY tools/blender/buildings/colony_build.py refinery <work> [--tex 4096]

Frame: metres, plinth top y = 0, +Z front, +X left. The concept camera looks mostly at the long +X side (az ~58,
el ~24): the control block stands at the near (+X, +Z) corner with a dark annex behind it, the three columns rise
behind it in a line along Z (tallest at the front), threaded by a two-level pipe rack, and two capsule tanks lie
along the +X edge at the back.
Sizes (real-world, the concept's proportions against its doors and the ~4 m columns): slab 42 x 74 m; columns 50,
39 and 28 m; control block 16 x 24 m, 11 m tall, annex 14 x 9 m, 9 m tall; capsule tanks 13 m.
"""
import math

import bkit as K

SPEC = {
    'title': 'Refinery', 'gameId': 'REFINERY', 'group': 'production',
    'footprint': [42, 74], 'height': 51.0,
    'camera': {'az': 58, 'el': 24},
    'about': 'three distillation columns (50 / 39 / 28 m) in a two-level pipe rack with amber railed decks, a control block with a dark annex, two capsule tanks, pumps and skids',
}

W, D = SPEC['footprint']
X0, X1, Z0, Z1 = -W / 2, W / 2, -D / 2, D / 2
COLS = ((-6.0, 17.0, 1.25), (-5.5, -3.0, 0.98), (-5.0, -21.5, 0.7))     # (x, z, scale of the 40 m column)
BLK = (12.5, 0.0, 24.5)                                                # control block centre (x, y, z)
BLK_SIZE = (16.0, 11.0, 23.0)
ANX = (13.0, 0.0, 7.0)
ANX_SIZE = (14.0, 9.0, 10.0)
LV = (7.0, 11.5)                                                       # rack levels


def slab_tone(B):
    """A thin darker wash over the slab top (the concept's mid-grey concrete; the kit's top is a step lighter):
    joints, markings and grates stay proud of it."""
    B.box((W - 1.2, 0.004, D - 1.2), at=(0.0, 0.002, 0.0), mat='concrete2', bevel=0.0)


def rack(B):
    """The two-level pipe rack along Z through the column line: portal bents, grating decks with amber rails on both
    levels, pipes, cross-runs to each column and to the tanks."""
    x0, x1 = -12.5, 0.5
    za, zb = 30.0, -34.0
    xs = (x0, x1)
    for z in [za - k * 8.0 for k in range(9)]:
        for x in xs:
            B.box((0.5, LV[1] + 0.4, 0.5), at=(x, (LV[1] + 0.4) / 2, z), mat='frame2', bevel=0.03)
            B.box((1.0, 0.35, 1.0), at=(x, 0.17, z), mat='concrete2', bevel=0.03)
        for y in LV:
            B.box((x1 - x0 + 0.8, 0.45, 0.4), at=((x0 + x1) / 2, y, z), mat='frame2', bevel=0.02)
        B.rod((x0, 0.6, z), (x0 + 3.0, LV[0] - 0.4, z), 0.12, mat='frame', n=6)
        B.rod((x1, 0.6, z), (x1 - 3.0, LV[0] - 0.4, z), 0.12, mat='frame', n=6)
    for y in LV:
        for x in xs:
            B.box((0.35, 0.45, za - zb), at=(x, y, (za + zb) / 2), mat='frame2', bevel=0.02)
    # grating walks with amber rails on both levels (+X side)
    for y in LV:
        B.box((2.6, 0.12, za - zb), at=(x1 - 1.4, y + 0.3, (za + zb) / 2), mat='grate', bevel=0.0)
        for x in (x1 - 2.7, x1 + 0.1):
            K.railing(B, [(x, y + 0.36, zb), (x, y + 0.36, za)], post=2.0, mat='amber')
    lower = [(-11.6, 0.6, 'pipe'), (-10.2, 0.5, 'pipe'), (-8.9, 0.5, 'pipeDark'), (-7.6, 0.4, 'pipe'), (-6.5, 0.4, 'pipe'), (-5.4, 0.35, 'pipeDark'), (-4.4, 0.35, 'pipe'), (-3.4, 0.3, 'pipe')]
    for (x, r, m) in lower:
        K.pipe(B, [(x, LV[0] + 0.25 + r, za + 1.5), (x, LV[0] + 0.25 + r, zb - 1.0)], r=r, mat=m, rings=True)
    upper = [(-11.6, 0.45, 'pipe'), (-10.4, 0.4, 'pipe'), (-9.3, 0.35, 'pipeDark'), (-8.3, 0.35, 'pipe'), (-7.3, 0.3, 'pipe'), (-6.4, 0.3, 'pipeDark')]
    for (x, r, m) in upper:
        K.pipe(B, [(x, LV[1] + 0.25 + r, za + 1.0), (x, LV[1] + 0.25 + r, zb - 1.0)], r=r, mat=m, rings=True)
    # risers: vertical lines hugging each column from the ground into its upper platforms, with elbows off the rack
    for (cx, cz, s) in COLS:
        top = 40.0 * s
        for k, (ang, r, h) in enumerate(((200.0, 0.45, 0.82), (240.0, 0.35, 0.62), (160.0, 0.3, 0.45))):
            a = math.radians(ang)
            px, pz = cx + (2.6 * s + 0.9) * math.sin(a), cz + (2.6 * s + 0.9) * math.cos(a)
            K.pipe(B, [(px, 0.5, pz), (px, top * h, pz), (cx + (2.0 * s) * math.sin(a), top * h + 1.6, cz + (2.0 * s) * math.cos(a))],
                   r=r, mat='pipe' if k != 1 else 'pipeDark', rings=(k == 0))
        K.pipe(B, [(-10.2, LV[0] + 0.8, cz + 3.0), (cx + 3.2, LV[0] + 0.8, cz + 3.0), (cx + 3.2, LV[1] + 3.5, cz + 3.0), (cx + 2.2 * s, LV[1] + 3.5, cz + 1.0)], r=0.4, mat='pipe', rings=False)
        K.pipe(B, [(-4.4, LV[0] + 0.6, cz - 3.0), (-4.4, 1.2, cz - 3.0), (6.0, 1.2, cz - 3.0)], r=0.3, mat='pipeDark', rings=False)
    # a cross rack at the back carrying lines from column 3 to the capsule tanks
    for z in (-26.0, -30.0):
        for x in (3.0, 8.0):
            B.box((0.4, 6.0, 0.4), at=(x, 3.0, z), mat='frame2', bevel=0.02)
        B.box((6.0, 0.4, 0.4), at=(5.5, 6.0, z), mat='frame2', bevel=0.02)
    for k, (dz, r) in enumerate(((-26.8, 0.45), (-28.0, 0.4), (-29.2, 0.35))):
        K.pipe(B, [(-4.0, LV[0] + 0.7 + 0.1 * k, dz), (10.5, 6.6 + 0.1 * k, dz), (10.5, 3.5, dz), (11.4, 3.5, dz)], r=r, mat='pipe', rings=(k == 0))
    # stairs up to the decks at the front end, ladders on the bents
    K.stair(B, (2.2, 0.0, 30.0), (0, 0, -1), LV[0] + 0.3, w=1.1)
    K.ladder(B, (x0 - 0.3, 0.3, -18.0), (-1, 0, 0), LV[1])
    K.ladder(B, (x1 + 0.3, LV[0] + 0.3, 6.0), (1, 0, 0), LV[1] - LV[0])
    for y in LV:
        for z in range(int(zb) + 4, int(za), 8):
            B.R.pin((x1 + 0.15, y + 1.5, z))
    for z in (za, za - 32.0, zb):
        for x in xs:
            B.R.pin((x + (0.4 if x > -5 else -0.4), LV[1] + 0.6, z))
            B.R.pin((x + (0.4 if x > -5 else -0.4), LV[0] + 0.6, z))


def model(B):
    K.plinth(B, W, D, h=1.5, chamfer=2.2, slab=7.0, lamp_pitch=14.0,
             markings=[([(X1 - 2.0, Z1 - 1.5), (X1 - 2.0, Z0 + 1.5)], 0.18, 'amber'),
                       ([(X0 + 1.5, Z1 - 2.0), (X1 - 1.5, Z1 - 2.0)], 0.18, 'amber'),
                       ([(10.0, -6.0), (19.0, -6.0)], 0.3, 'hazard'), ([(10.0, -37.0), (19.0, -37.0)], 0.3, 'hazard')],
             grates=[(X1 - 3.0, 0.0, 0.8, 2.4), (X1 - 3.0, -16.0, 0.8, 2.4), (-15.0, Z1 - 3.2, 2.4, 0.8), (14.0, -22.0, 3.0, 0.8)],
             steps=[(-15.0, Z1, '+z'), (X1, -2.0, '+x')])
    slab_tone(B)

    # --- the three distillation columns (fal component distColumn: platforms, caged amber ladders, domed head),
    # tallest at the front; pedestals; the tallest carries the beacon
    for i, (x, z, s) in enumerate(COLS):
        K.component(B, 'distColumn', (x, 0.0, z), heading=(150.0, 120.0, 160.0)[i], scale=s)
        B.box((6.0 * s + 1.5, 0.6, 6.0 * s + 1.5), at=(x, 0.3, z), mat='concrete2', bevel=0.08)
        B.R.pin((x, 40.4 * s + 0.4, z))
    B.R.beacon((COLS[0][0], 40.0 * COLS[0][2] + 1.0, COLS[0][1]))
    rack(B)

    # --- control block at the near corner: light cladding over a gunmetal ground storey, windows on +Z and +X, crew
    # doors, roof plant with two exhaust stacks; the darker annex behind it with the big roller door (the concept's
    # two-tone block)
    bx, _, bz = BLK
    bw, bh, bd = BLK_SIZE
    K.block(B, BLK, BLK_SIZE, frame='frame2',
            sides={'+x': {'bay': 4.6, 'storey': 4.0, 'base': 1.4, 'windows': [1], 'win': (1.5, 1.2), 'doors': [7.0, 16.0], 'seams': True, 'bands': False},
                   '+z': {'bay': 4.0, 'storey': 4.0, 'base': 1.4, 'windows': [1], 'win': (1.2, 1.2), 'doors': [8.0], 'bands': False},
                   '-x': {'bay': 4.6, 'storey': 4.0, 'base': 1.4, 'windows': [1], 'win': (1.2, 1.0), 'bands': False},
                   '-z': {'bay': 4.0, 'storey': 4.0, 'base': 1.4, 'bands': False}},
            roof={'parapet': 0.7, 'mat': 'panel2', 'units': [('hvac', -3.0, 6.5, {'w': 3.6, 'd': 2.4, 'fans': 2}), ('hvac', 3.0, 6.5, {'w': 3.6, 'd': 2.4, 'fans': 2}),
                                            ('hvac', -3.0, -6.5, {'w': 3.2, 'd': 2.2}), ('box', 3.5, -1.0, {'w': 3.0, 'd': 4.0, 'h': 2.0}),
                                            ('vent', 0.0, 1.0, {}), ('vent', -4.5, 0.5, {}), ('antenna', 5.5, -9.0, {'h': 5.0})]})
    for (sx, sz, h) in ((-5.0, -2.5, 6.5), (-5.0, -5.5, 5.5)):
        K.stack(B, (bx + sx, bz + sz), 0.6, h, y0=bh, bands=[(h - 1.2, h - 0.8, 'frame')], lamps=False)
    ax_, _, az_ = ANX
    K.block(B, ANX, ANX_SIZE, panel='frame2',
            sides={'+x': {'bay': 5.0, 'storey': 4.5, 'base': 0.8, 'rollers': [(4.0, 4.4, 5.0)], 'doors': [8.0], 'panel': 'frame2', 'bands': False},
                   '+z': {'skip_face': True},
                   '-x': {'bay': 5.0, 'storey': 4.5, 'panel': 'frame2', 'bands': False},
                   '-z': {'bay': 4.5, 'storey': 4.5, 'panel': 'frame2', 'louvres': [(5.0, 3.0, 3.0, 2.4)], 'bands': False}},
            roof={'parapet': 0.5, 'mat': 'panel2', 'units': [('hvac', 0.0, -1.5, {'w': 3.4, 'd': 2.2, 'fans': 2}), ('vent', 4.0, 2.5, {})]})
    K.ladder(B, (bx + bw / 2 + 0.05, 0.2, bz - 9.5), (1, 0, 0), bh + 0.5)
    # pipe riser up the block's -X side and over its roof into the rack; transformer and cabinets by the block
    K.pipe(B, [(bx - bw / 2 - 1.2, 0.0, bz + 4.0), (bx - bw / 2 - 1.2, bh + 1.6, bz + 4.0), (bx - 2.0, bh + 1.6, bz + 4.0)], r=0.5, mat='pipe')
    K.pipe(B, [(bx - bw / 2 - 2.4, 0.0, bz + 1.0), (bx - bw / 2 - 2.4, LV[0] + 0.8, bz + 1.0), (-1.0, LV[0] + 0.8, bz + 1.0)], r=0.4, mat='pipeDark')
    K.pipe(B, [(bx - bw / 2 - 1.2, 1.0, bz - 6.0), (-0.5, 1.0, bz - 6.0)], r=0.35, mat='pipe', supports=False)
    for (x, z) in ((bx + 3.0, Z1 - 2.6), (bx - 1.0, Z1 - 2.6), (bx - 5.0, Z1 - 2.6)):
        K.cabinet(B, (x, 0.0, z), w=1.6, h=1.9, d=0.8)
    B.box((3.0, 2.6, 2.4), at=(bx - bw / 2 - 3.2, 1.3, bz + 9.0), mat='frame2', bevel=0.06)      # transformer
    for k in range(5):
        B.box((0.1, 2.0, 2.0), at=(bx - bw / 2 - 4.75, 1.4, bz + 8.2 + k * 0.4), mat='frame', bevel=0.0)

    # --- capsule tanks along the +X edge at the back (fal component htankSkid), axis along Z, platform end forward
    for z in (-13.5, -29.5):
        K.component(B, 'htankSkid', (14.5, 0.0, z), heading=0.0)
        K.bollards(B, [(19.8, z - 6.0), (19.8, z + 6.0), (19.8, z)])
        B.R.pin((14.5, 6.0, z + 6.8))
    # pumps and skids between the rack and the tanks (reused fal skids), small vertical drums, a small htank
    K.component(B, 'manifoldSkid', (12.5, 0.0, -3.4), heading=90.0)
    K.component(B, 'filterBank', (5.0, 0.0, -11.0), heading=0.0)
    K.component(B, 'filterBank', (-17.0, 0.0, 7.0), heading=-90.0)
    for (x, z, r, h) in ((-17.0, -11.0, 1.6, 7.0), (-17.0, -16.5, 1.6, 7.0), (-17.0, 25.0, 1.2, 5.0), (4.5, -33.5, 1.3, 5.5), (5.5, -18.0, 1.1, 4.5)):
        K.vtank(B, (x, z), r, h, y0=0.4, top='dome', mat='panel', bands=[(0.6, 1.0, 'frame'), (h - 1.0, h - 0.6, 'frame')], skirt=0.6, ladder_side=90.0)
    K.htank(B, (-17.0, -29.0), 1.4, 8.0, axis=(0, 0, 1), band='amber')
    for (x, z) in ((-14.5, 22.0), (-14.5, 11.0), (-14.5, -6.0), (-14.5, -24.0), (3.0, 12.0), (3.0, 1.5)):
        B.box((2.2, 1.2, 1.4), at=(x, 0.6, z), mat='frame2', bevel=0.05)                       # pump bodies
        B.vcyl(0.45, 1.0, (x + 0.6, 1.2, z), mat='pipe', n=10)
        K.pipe(B, [(x + 0.6, 2.2, z), (x + 0.6, 3.5, z), (x + (2.0 if x < 0 else -2.0), LV[0] - 0.2, z)], r=0.22, mat='pipe', rings=False)
    # a pipe bank at the foot of the rack along the -X edge
    for k, y in enumerate((1.2, 2.0, 2.8)):
        K.pipe(B, [(-15.5 - 0.9 * k, y, 30.0), (-15.5 - 0.9 * k, y, -35.0)], r=0.28, mat='pipe' if k != 1 else 'pipeDark', supports=(k == 0), support_pitch=8.0, rings=True)
    # bollards, lamp posts, cabinets, crates, workers
    K.bollards(B, [(X1 - 1.5, 15.0), (X1 - 1.5, 10.0), (X1 - 1.5, 4.0), (6.0, Z1 - 1.5), (10.0, Z1 - 1.5), (17.0, Z1 - 1.5), (3.5, 20.0), (3.5, 26.0), (6.5, -6.5), (6.5, 0.5)])
    for (x, z, rot) in ((X1 - 1.0, Z0 + 1.5, -45), (X0 + 1.0, Z1 - 1.5, 135), (X1 - 1.0, -4.0, -90), (X0 + 1.0, Z0 + 1.5, 45)):
        K.lamp_post(B, (x, 0.0, z), h=7.0, arm=1.0, rot=rot)
    for (x, z) in ((X1 - 1.6, -21.0), (X1 - 1.6, -22.6), (-19.6, 14.0), (-19.6, 15.6)):
        K.cabinet(B, (x, 0.0, z), rot=-90 if x > 0 else 90)
    for (x, z, m) in ((18.5, -35.0, 'frame2'), (16.7, -35.0, 'cobalt'), (-19.0, -34.5, 'frame2'), (9.0, -1.0, 'amber')):
        K.crate(B, (x, 0.0, z), (1.4, 1.1, 1.3), mat=m)
    K.forklift(B, (X1 - 3.0, 0.0, -6.0), heading=200)
    for (x, z, hd) in ((X1 - 3.5, 13.0, 250), (5.0, Z1 - 3.0, 10), (9.0, -7.5, 100), (-1.0, -35.0, 300), (2.0, 30.5, 180)):
        K.worker(B, (x, 0.0, z), heading=hd)
    B.R.beacon((ax_ + 4.5, ANX_SIZE[1] + 0.8, az_ - 3.0))
