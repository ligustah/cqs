"""STEEL_MILL: blast furnace tower with skip hoist, glowing pour bay, stacks, long shed
(concept style-library/styles/cqs-fleet/images/buildings/steel_mill-concept.jpg).

v2: model() composes fal components (assets/parts-colony: blastFurnace, skipGallery, bandedStack x2, shedSegment x2,
pourBay) with the shared kit; furnace() / shed() / stacks() / gas_cleaner() are the v1 parametric versions, kept as
kit examples (unused). v4 (2026-10-07, corrections 40-42): the five components are remodelled parametric parts
(ckit.furnace / banded_stack / gable_shed / pour_bay / incline_gallery via remodel.py) at the same names and anchors,
so model() is unchanged; their lamps, glow and kit doors come with them (bkit.component). Built by colony_build.py:
    $PY tools/blender/buildings/colony_build.py steel_mill <work> [--tex 4096]

Frame: metres, plinth top y = 0, +Z front, +X left. The concept camera looks from the front-left (az ~40, el ~27):
the furnace stands at the front-left of the slab, the long shed runs back along the +X side with the open pour bay on
its +X face near the front, two banded stacks rise behind the furnace on the -X side.
Sizes (real-world, the concept's proportions against its doors and the shed): slab 72 x 96 m; furnace tower 62 m
(shaft 17 m across), steel frame 22 m square; shed 28 x 72 m, eaves 18 m, ridges 21.5 m; stacks 54 m and 46 m;
pour bay 22 m wide, 15 m clear, with an amber overhead crane.
"""
import math

import bkit as K

SPEC = {
    'title': 'Steel Mill', 'gameId': 'STEEL_MILL', 'group': 'production',
    'footprint': [80, 92], 'height': 61.0,
    'camera': {'az': 40, 'el': 27},
    'about': 'blast furnace in a steel tower frame with a skip-hoist gallery, glowing pour bay with an overhead crane, two banded stacks, long clad shed',
}

FX, FZ = -18.0, 24.0         # furnace axis (front-left of the slab; v5: 2 m back for the broader furnace)
SH_X, SH_SEGMENTS = 10.0, (-27.0, 9.0)   # shed: two 36 m fal segments along Z, x -4..24
PB_X, PB_Z = 28.0, 13.0       # pour bay centre (against the shed's +X face)
SH = (-4.0, 24.0, -44.0, 28.0)  # shed x0, x1, z0, z1
EAVE = 18.0


def furnace(B):
    x, z = FX, FZ
    # heavy square base (casthouse plinth) in gunmetal with light panels between dark posts
    K.block(B, (x, 0.0, z), (20.0, 7.0, 20.0),
            sides={'+z': {'bay': 5.0, 'doors': [16.5], 'windows': [], 'louvres': [(11.0, 3.5, 2.4, 1.6)]},
                   '+x': {'bay': 5.0, 'doors': [5.0], 'rollers': [(13.0, 5.0, 5.0)]},
                   '-x': {'bay': 5.5}, '-z': {'bay': 5.5}},
            roof={'parapet': 0.6, 'deck': True})
    yb = 7.0
    # hearth (dark, banded), the hot tuyere band, bustle main, bosh, shaft (light panels, dark bands), top cone, throat
    B.lathe([(8.0, 0), (8.0, 6.0), (7.6, 6.0), (7.6, 7.4), (8.2, 7.4), (8.2, 8.6), (0, 8.6)], (x, yb, z), mat='panel', n=36)
    for y0 in (0.0, 2.8, 5.4):
        B.ring(8.15, 7.9, y0, y0 + 0.5, (x, yb, z), mat='frame', n=36)
    K.glow_ring(B, (x, z), 7.65, yb + 6.7, h=1.0, n=22, color='#ff7a1e', radiance=3.0)
    B.ring(7.7, 7.55, 6.1, 6.25, (x, yb, z), mat='frame', n=36)
    # bustle pipe (torus as a closed tube) and tuyere downlegs
    pts = [(x + 10.0 * math.sin(2 * math.pi * k / 24), yb + 10.5, z + 10.0 * math.cos(2 * math.pi * k / 24)) for k in range(25)]
    B.tube(pts, 0.9, mat='pipeDark', n=12, fillet=0.0)
    for k in range(12):
        a = 2 * math.pi * (k + 0.5) / 12
        B.tube([(x + 10.0 * math.sin(a), yb + 10.0, z + 10.0 * math.cos(a)), (x + 9.0 * math.sin(a), yb + 7.8, z + 9.0 * math.cos(a)),
                (x + 8.2 * math.sin(a), yb + 7.0, z + 8.2 * math.cos(a))], 0.25, mat='pipeDark', n=6, fillet=0.4)
    B.lathe([(8.2, 0), (9.2, 5.0), (0, 5.0)], (x, yb + 8.6, z), mat='panel2', n=36)              # bosh
    B.lathe([(9.2, 0), (8.6, 7.5), (8.0, 15.0), (7.4, 20.0)], (x, yb + 13.6, z), mat='panel', n=36)  # shaft
    for y0 in (0.0, 5.0, 10.0, 15.0, 19.4):
        r = 9.2 - 0.09 * y0
        B.ring(r + 0.2, r - 0.1, yb + 13.6 + y0, yb + 13.6 + y0 + 0.7, (x, 0, z), mat='frame', n=36)
    for k in range(18):   # vertical cooling staves / seams
        a = 2 * math.pi * k / 18
        B.bar((x + 9.25 * math.sin(a), yb + 13.7, z + 9.25 * math.cos(a)), (x + 7.45 * math.sin(a), yb + 33.4, z + 7.45 * math.cos(a)), 0.12, 0.08, mat='panel2', bevel=0.0)
    ys = yb + 33.6
    B.lathe([(7.4, 0), (7.6, 0.8), (5.0, 6.0), (4.2, 6.0), (4.2, 13.0), (3.6, 13.5), (0, 13.5)], (x, ys, z), mat='frame2', n=32)  # top cone + throat
    B.ring(5.4, 3.9, 6.0, 7.2, (x, ys, z), mat='panel', n=32)
    B.ring(4.6, 4.1, 9.0, 12.0, (x, ys, z), mat='panel', n=32)
    # four uptakes from the throat rising and joining into the downcomer that drops to the gas cleaner (-X)
    yt = ys + 13.5
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        p0 = (x + 3.4 * math.sin(a), ys + 9.0, z + 3.4 * math.cos(a))
        K.pipe(B, [p0, (x + 4.4 * math.sin(a), yt + 1.0, z + 4.4 * math.cos(a)), (x + 1.8 * math.sin(a), yt + 3.5, z + 1.8 * math.cos(a)), (x, yt + 4.0, z)],
               r=0.75, mat='pipeDark', rings=False, flanges=False)
    B.vcyl(1.8, 2.0, (x, yt + 3.0, z), mat='frame2', n=16)
    K.pipe(B, [(x, yt + 4.2, z), (x - 6.0, yt + 4.2, z), (x - 10.5, yt - 2.0, z + 2.0), (x - 12.0, 31.0, z + 4.0)], r=1.3, mat='pipeDark', rings=False)
    B.R.beacon((x, yt + 6.0, z))
    # steel tower frame round the furnace: four built-up columns, ring girders and platforms at four levels
    s = 10.0
    cols = [(x - s, z - s), (x + s, z - s), (x + s, z + s), (x - s, z + s)]
    for (cx, cz) in cols:
        B.strut((cx, yb, cz), (cx * 0.85 + x * 0.15, yb + 44.0, cz * 0.85 + z * 0.15), (1.6, 1.6), (1.1, 1.1), 0.2, mat='frame')
    levels = [(yb + 12.0, 9.8), (yb + 24.0, 9.3), (yb + 34.0, 8.8), (yb + 44.0, 8.5)]
    for (ly, ss) in levels:
        pts = [(x - ss, ly, z - ss), (x + ss, ly, z - ss), (x + ss, ly, z + ss), (x - ss, ly, z + ss)]
        for i in range(4):
            B.bar(pts[i], pts[(i + 1) % 4], 0.6, 0.9, mat='frame', bevel=0.03)
        # grating deck between the frame and the shell on the front and left sides, with rails
        B.box((2 * ss, 0.15, 2.6), at=(x, ly + 0.45, z + ss - 1.3), mat='grate', bevel=0.0)
        B.box((2.6, 0.15, 2 * ss), at=(x + ss - 1.3, ly + 0.45, z), mat='grate', bevel=0.0)
        K.railing(B, [(x - ss, ly + 0.5, z + ss), (x + ss, ly + 0.5, z + ss), (x + ss, ly + 0.5, z - ss)], post=1.6)
        for (px, py, pz) in pts:
            B.R.pin((px + (0.7 if px > x else -0.7), py + 0.2, pz + (0.7 if pz > z else -0.7)))
    # diagonal bracing in the lower two storeys
    for i in range(4):
        a, b = cols[i], cols[(i + 1) % 4]
        B.rod((a[0], yb + 0.5, a[1]), (b[0], yb + 12.0, b[1]), 0.18, mat='frame', n=6)
        B.rod((b[0], yb + 0.5, b[1]), (a[0], yb + 12.0, a[1]), 0.18, mat='frame', n=6)
        B.rod((a[0], yb + 12.0, a[1]), (b[0], yb + 24.0, b[1]), 0.16, mat='frame', n=6)
    # access stair along the casthouse front up to its roof, and a second flight to the first platform
    K.stair(B, (x + 9.0, 0.0, z + 11.6), (-1, 0, 0), yb, w=1.2)
    K.stair(B, (x - 8.0, yb, z + 8.6), (1, 0, 0), 12.0, w=1.1)


def gas_cleaner(B):
    # tall clad block on the -X side of the furnace (gas cleaning / stoves), dark base, small annex
    x, z = -30.5, 25.0
    K.block(B, (x, 0.0, z), (8.0, 26.0, 16.0),
            sides={'+z': {'bay': 5.5, 'storey': 6.5, 'windows': [], 'doors': [2.5], 'louvres': [(7.5, 12.0, 2.0, 2.0)]},
                   '+x': {'bay': 5.5, 'storey': 6.5, 'windows': [1, 2], 'win': (1.2, 1.2)},
                   '-x': {'bay': 5.5, 'storey': 6.5}, '-z': {'bay': 5.5, 'storey': 6.5}},
            roof={'parapet': 0.6, 'units': [('hvac', 0.0, -3.0, {'w': 3.2, 'd': 2.2}), ('vent', 2.5, 4.0, {}), ('antenna', -3.5, 5.5, {'h': 5.0})]})
    K.ladder(B, (x - 4.0, 0.4, z - 4.0), (-1, 0, 0), 25.0)
    K.block(B, (-31.5, 0.0, 39.5), (6.0, 7.0, 8.0),
            sides={'+z': {'bay': 3.0, 'doors': [3.0], 'windows': []}, '+x': {'bay': 4.0, 'windows': [0], 'win': (1.2, 1.0)}},
            roof={'parapet': 0.4, 'units': [('hvac', 0.0, 0.0, {'w': 2.6, 'd': 1.8, 'fans': 1})]})
    # cyclone dust catcher between them and the furnace
    K.vtank(B, (-29.0, 10.0), 3.0, 10.0, y0=0.0, top='cone', mat='frame2', skirt=6.0, ladder_side=90.0,
            bands=[(1.0, 1.4, 'frame'), (8.4, 8.8, 'frame')], platforms=(10.5,))


def shed(B):
    x0, x1, z0, z1 = SH
    W = x1 - x0
    xc = (x0 + x1) / 2
    zb0, zb1 = 6.0, 28.0          # pour bay along the +X face
    # main shed body behind the pour bay
    K.block(B, (xc, 0.0, (z0 + zb0) / 2), (W, EAVE, zb0 - z0),
            sides={'+x': {'bay': 8.3, 'storey': 6.0, 'windows': [2], 'win': (2.4, 1.4), 'win_per_bay': 2, 'seams': False, 'bands': False,
                          'doors': [8.0, 26.0], 'rollers': [(41.0, 6.0, 7.0)]},
                   '-z': {'bay': 7.0, 'storey': 6.0, 'rollers': [(14.0, 7.0, 8.0)], 'doors': [4.0], 'seams': False},
                   '-x': {'bay': 8.3, 'storey': 6.0, 'windows': [2], 'win': (2.4, 1.4), 'seams': False, 'bands': False},
                   '+z': {'skip_face': True}},
            roof={'deck': False})
    # pour bay: the shed continues with its +X face open over the bay (dark interior wall 7 m in)
    bx1 = x1 - 7.0
    K.block(B, ((x0 + bx1) / 2, 0.0, (zb0 + zb1) / 2), (bx1 - x0, EAVE, zb1 - zb0),
            sides={'+z': {'bay': 6.0, 'storey': 6.0, 'windows': [2], 'win': (2.0, 1.4), 'doors': [5.0], 'seams': False},
                   '-x': {'bay': 7.0, 'storey': 6.0}, '+x': {'skip_face': True}, '-z': {'skip_face': True}},
            roof={'deck': False}, corner_lamps=False)
    B.box((0.3, EAVE - 1.0, zb1 - zb0 - 0.4), at=(bx1 + 0.1, (EAVE - 1.0) / 2, (zb0 + zb1) / 2), mat='interior', bevel=0.0)
    B.box((7.0, 0.3, zb1 - zb0), at=(bx1 + 3.5, 0.15, (zb0 + zb1) / 2), mat='soot', bevel=0.0)
    # bay structure: portal columns on the +X line, a deep truss girder at the eaves, the amber overhead crane
    for zc in (zb0 + 0.4, (zb0 + zb1) / 2, zb1 - 0.4):
        B.box((1.0, EAVE, 1.0), at=(x1 - 0.5, EAVE / 2, zc), mat='frame', bevel=0.04)
    K.truss(B, (x1 - 0.5, EAVE - 1.2, zb0), (x1 - 0.5, EAVE - 1.2, zb1), 2.2, bay=2.2, chord=0.3, web=0.14)
    B.box((7.4, 1.0, zb1 - zb0), at=(x1 - 3.7, EAVE - 0.2, (zb0 + zb1) / 2), mat='frame', bevel=0.03)
    # crane: two amber box girders across the bay on runway beams, a trolley with a hoist block over the ladle
    for xr in (bx1 + 0.6, x1 - 1.4):
        B.box((0.7, 0.9, zb1 - zb0), at=(xr, 13.6, (zb0 + zb1) / 2), mat='frame', bevel=0.02)
    zc = 16.5
    for dz in (-1.1, 1.1):
        B.box((x1 - bx1 - 0.4, 1.4, 0.7), at=((bx1 + x1) / 2 - 0.4, 14.8, zc + dz), mat='amber', bevel=0.04)
    B.box((2.6, 1.6, 3.2), at=((bx1 + x1) / 2, 16.2, zc), mat='frame2', bevel=0.05)
    B.rod(((bx1 + x1) / 2, 15.4, zc - 0.4), ((bx1 + x1) / 2, 8.6, zc - 0.4), 0.05, n=4)
    B.rod(((bx1 + x1) / 2, 15.4, zc + 0.4), ((bx1 + x1) / 2, 8.6, zc + 0.4), 0.05, n=4)
    B.box((1.8, 0.9, 1.4), at=((bx1 + x1) / 2, 8.2, zc), mat='amber', bevel=0.04)
    B.R.pin((x1 + 0.2, 14.9, zc - 1.1))
    # roof: three gable sections across the shed (ridges along X), the two forward ones carry roof monitors
    for (za, zz) in ((z0, -20.0), (-20.0, 4.0), (4.0, z1)):
        K.gable_roof(B, x0, x1, za, zz, EAVE, 3.5, ridge='x')
    for (xm, zm) in ((xc, -32.0), (xc, -8.0)):
        B.box((W * 0.5, 1.6, 3.0), at=(xm, EAVE + 4.0, zm), mat='frame2', bevel=0.05)
        B.box((W * 0.5 + 0.6, 0.25, 3.6), at=(xm, EAVE + 4.9, zm), mat='frame', bevel=0.02)
    # the pour: a glowing runner trough out of the bay onto the apron, a torpedo ladle car, the tapping platform
    tr_z = 18.0
    B.box((14.0, 1.2, 3.0), at=(x1 + 1.0, 0.6, tr_z), mat='frame2', bevel=0.04)
    B.box((13.6, 0.3, 1.6), at=(x1 + 1.0, 1.1, tr_z), mat='refractory', bevel=0.0)
    B.R.glowbox((x1 + 1.0, 1.28, tr_z), (13.2, 0.08, 1.3), color='#ff6a10', radiance=4.0)
    B.R.glowbox((bx1 + 0.4, 1.4, (zb0 + zb1) / 2), (0.06, 2.4, zb1 - zb0 - 4.0), color='#ff8a30', radiance=0.5)
    B.R.glowbox(((bx1 + x1) / 2, 0.35, tr_z), (6.0, 0.05, 5.0), color='#ff7a20', radiance=0.7)
    # hot ladle under the crane hook inside the bay
    B.vcyl(1.5, 2.4, ((bx1 + x1) / 2, 0.3, 12.0), mat='refractory', n=16)
    B.R.glowbox(((bx1 + x1) / 2, 2.75, 12.0), (2.2, 0.05, 2.2), color='#ff6a10', radiance=3.0)
    K.railing(B, [(x1 - 5.5, 1.2, tr_z - 1.6), (x1 + 7.6, 1.2, tr_z - 1.6)], post=1.6)
    K.railing(B, [(x1 - 5.5, 1.2, tr_z + 1.6), (x1 + 7.6, 1.2, tr_z + 1.6)], post=1.6)
    # ladle car on rails beside the runner
    for dz in (-0.9, 0.9):
        B.box((16.0, 0.15, 0.2), at=(x1 + 3.0, 0.08, 23.5 + dz), mat='pipe', bevel=0.0)
    B.box((6.0, 1.0, 2.6), at=(x1 + 5.0, 0.8, 23.5), mat='frame', bevel=0.04)
    B.cyl(1.6, 5.0, at=(x1 + 5.0, 3.0, 23.5), rot=(0, 90, 0), mat='refractory', n=16)
    B.vcyl(0.7, 0.8, (x1 + 5.0, 4.3, 23.5), mat='soot', n=12)
    # small switch room and control box on the apron, stairs, crates
    K.block(B, (x1 + 4.5, 0.0, 0.5), (6.0, 4.5, 7.0),
            sides={'+x': {'bay': 3.5, 'doors': [2.0], 'windows': [0], 'win': (1.2, 1.0)}, '+z': {'bay': 3.0, 'windows': [0], 'win': (1.2, 1.0)}},
            roof={'parapet': 0.4, 'units': [('hvac', 0.0, 0.0, {'w': 2.4, 'd': 1.6, 'fans': 1})]})
    K.block(B, (x1 + 3.0, 0.0, 33.0), (4.0, 3.6, 5.0),
            sides={'+x': {'bay': 2.5, 'doors': [2.5]}, '+z': {'bay': 2.0, 'windows': [0], 'win': (1.2, 1.0)}},
            roof={'parapet': 0.3})
    K.stair(B, (x1 + 0.8, 0.0, -36.0), (1, 0, 0), 2.4, w=1.2)
    B.box((3.0, 2.4, 4.0), at=(x1 + 2.3, 1.2, -38.0), mat='frame2', bevel=0.04)
    for (cx, cz) in ((x1 + 9.0, 8.0), (x1 + 9.5, 10.0), (x1 + 2.0, 40.0), (x1 + 4.0, 42.0)):
        K.crate(B, (cx, 0.0, cz), (1.6, 1.2, 1.6))


def stacks(B):
    # two banded stacks behind the furnace on the -X side, on flared bases with platform rings
    for (x, z, h, r) in ((-14.0, -10.0, 48.0, 3.4), (-13.0, -32.0, 41.0, 3.2)):
        B.box((9.0, 4.0, 9.0), at=(x, 2.0, z), mat='frame2', bevel=0.06)
        bands = []
        y = 6.0
        k = 0
        while y < h - 4:
            bands.append((y, y + 5.0, 'panel' if k % 2 == 0 else 'frame'))
            y += 7.0
            k += 1
        K.stack(B, (x, z), r * 1.15, h, r1=r * 0.95, y0=4.0, bands=bands, platforms=(h * 0.45, h - 6.0), base_h=7.0, base_r=r * 1.8,
                mat='frame2', ladder_side=90.0)
        # flue duct from the shed roof into the stack base
        K.pipe(B, [(-2.0, 12.0, z), (x + r * 1.8, 12.0, z), (x + r * 1.2, 9.0, z)], r=1.4, mat='pipeDark', rings=False)


def model(B):
    """v2: composed from fal components (assets/parts-colony: blastFurnace, skipGallery, bandedStack x2, shedSegment x2,
    pourBay; README-colony.md catalogue) on the shared kit's plinth, with parametric annexes, pipes, dressing, lights."""
    W, D = SPEC['footprint']
    K.plinth(B, W, D, h=2.0, kerb_h=1.1, chamfer=2.4, slab=4.6, lamp_pitch=4.6,   # r8: the concept's dense lamp line   # r7: a thick light slab edge centre=(0.0, -4.0),   # v6: lamps every 9 m (concept)
             markings=[([(37.5, 40.0), (37.5, -48.0)], 0.2, 'frame2'), ([(-38.0, 39.5), (38.0, 39.5)], 0.2, 'frame2'),
                       ([(30.0, 30.0), (39.0, 30.0)], 0.35, 'hazard'), ([(30.0, -2.0), (39.0, -2.0)], 0.35, 'hazard')],
             grates=[(37.0, -16.0, 0.8, 3.0), (37.0, 32.0, 0.8, 3.0), (-2.0, 34.0, 3.0, 0.8)],
             steps=[(12.0, 42.0, '+z')])
    # the furnace tower at the front-left (60 m: shaft, glowing tuyere band, top cone and uptakes, gunmetal frame)
    K.component(B, 'blastFurnace', (FX, 0.0, FZ), heading=0.0)
    B.R.beacon((FX, 63.0, FZ))
    B.R.obstruction((FX + 2.0, 60.0, FZ + 2.0))
    # v5: the skip bridge (an open truss with the gas main over it) from a tall clad tower between the stacks and the
    # shed up to the furnace's frame at 47 m (part frame: head at -Z, tower at +Z; heading 161.6 points it at the tower)
    K.component(B, 'skipGallery', (-11.8, 0.0, 5.2), heading=161.6)
    # two banded stacks behind the furnace, the second shorter (v5: moved back for the bridge tower)
    K.component(B, 'bandedStack', (-16.0, 0.0, -14.0), heading=90.0)
    K.component(B, 'bandedStack', (-14.0, 0.0, -34.0), heading=90.0, scale=0.87)
    for z in (-14.0, -34.0):
        K.pipe(B, [(-3.0, 12.0, z), (-9.0, 12.0, z), (-11.0, 8.0, z)], r=1.3, mat='pipeDark', rings=False)
    # the long shed along +X: two fal shed segments end to end, windowed long face to +X
    for zc in SH_SEGMENTS:
        K.component(B, 'shedSegment', (SH_X, 0.0, zc), heading=0.0)
    # the open pour bay against the shed's +X face, its glowing runner out onto the apron
    K.component(B, 'pourBay', (PB_X, 0.0, PB_Z), heading=0.0)
    for (x, z) in ((PB_X + 7.3, PB_Z - 13.0), (PB_X + 7.3, PB_Z + 13.0)):   # v6: the shallower portal's front columns
        B.R.pin((x, 14.0, z))
    # gas-cleaning annex on the furnace's -X side, under the downcomer's elbow (v5: narrow and low beside the broader
    # furnace plinth; the concept's light block with the big elbow pipe on its roof), the dust catcher behind
    # r7: the concept's tall light annex under the big elbow pipe (15 m)
    # r8 (coordinator: plain tall blocks, dark frames, light panels, one window row at most)
    K.block(B, (-37.0, 0.0, 30.0), (6.0, 15.0, 15.0),
            sides={'+z': {'bay': 3.0, 'storey': 7.5, 'windows': [], 'doors': [3.0]},
                   '+x': {'bay': 5.0, 'storey': 7.5, 'windows': [1], 'win': (1.2, 0.9)},
                   '-x': {'bay': 5.0, 'storey': 7.5, 'doors': [7.5], 'louvres': [(11.0, 7.5, 2.0, 2.0)]},
                   '-z': {'bay': 3.0, 'storey': 7.5}},
            roof={'parapet': 0.6, 'units': [('vent', 1.0, -5.0, {}), ('antenna', -1.5, 6.0, {'h': 5.0})]})
    K.ladder(B, (-40.4, 0.0, 26.0), (-1, 0, 0), 15.0)
    K.block(B, (-35.5, 0.0, -2.0), (7.0, 7.0, 8.0),
            sides={'+z': {'bay': 3.5, 'doors': [3.5], 'windows': []}, '+x': {'bay': 4.0, 'windows': [0], 'win': (1.2, 1.0)}},
            roof={'parapet': 0.4, 'units': [('hvac', 0.0, 0.0, {'w': 2.6, 'd': 1.8, 'fans': 1})]}, frame='frameL')
    K.vtank(B, (-34.0, 7.5), 2.6, 9.0, y0=0.0, top='cone', mat='frame2', skirt=5.0, ladder_side=90.0,
            bands=[(1.0, 1.4, 'frame'), (7.4, 7.8, 'frame')], platforms=(9.5,))
    K.pipe(B, [(-36.6, 12.0, 7.5), (-37.0, 12.0, 22.5)], r=0.6, mat='pipe', supports=False)
    # v5: furnace base dressing: cooling-water mains round the plinth on stools, valve skids, a stair to the
    # plinth top, crates (the concept's busy foot)
    K.pipe(B, [(FX - 17.2, 0.9, FZ + 6.0), (FX - 17.2, 0.9, FZ + 17.0), (FX + 6.0, 0.9, FZ + 17.0)], r=0.45, mat='pipe', supports=True, ground=0.0)
    K.pipe(B, [(FX - 17.2, 2.0, FZ - 8.0), (FX - 17.2, 2.0, FZ + 4.0), (FX - 16.4, 3.4, FZ + 4.0)], r=0.3, mat='pipe', supports=True, ground=0.0)
    K.cable_tray(B, (FX + 16.4, 2.6, FZ - 14.0), (FX + 16.4, 2.6, FZ + 10.0), w=0.5)
    K.stair(B, (FX + 6.0, 0.0, FZ + 17.6), (-1, 0, 0), 3.0, w=1.2)
    for (cx, cz) in ((FX + 9.0, FZ + 17.8), (FX + 10.8, FZ + 18.0)):
        K.crate(B, (cx, 0.0, cz), (1.4, 1.1, 1.4))
    K.valve(B, (FX - 17.2, 0.9, FZ + 11.0), (0, 0, 1), r=0.45)
    # v4 r3: the casthouse front block between the furnace and the pour bay (the concept's foreground: light panels in
    # dark frames, crew doors with lamps, a roller door, roof units), so the shed's front gable stands behind layered
    # volumes instead of over an empty apron
    # r4 (judges: "the boxy office in front of the furnace"): a LOW casthouse block (7 m, the concept's low light block
    # between the furnace and the pour bay): doors, a roller door and louvres, two small windows, no office strip
    K.block(B, (8.0, 0.0, 34.0), (21.0, 7.0, 9.0), frame='frameL',   # r9: dark frames read as a busy half-timber grid
            sides={'+z': {'bay': 5.25, 'storey': 7.0, 'windows': [], 'doors': [2.6, 18.4], 'rollers': [(10.5, 5.0, 5.6)],
                          'louvres': [(6.0, 4.4, 2.0, 1.4), (15.0, 4.4, 2.0, 1.4)]},
                   '+x': {'bay': 4.5, 'storey': 7.0, 'windows': [0], 'win': (1.2, 1.0), 'doors': [4.5]},
                   '-x': {'bay': 4.5, 'storey': 7.0}, '-z': {'bay': 5.25, 'storey': 7.0}},
            roof={'parapet': 0.5, 'units': [('hvac', -6.0, -1.0, {'w': 3.0, 'd': 2.0}), ('vent', 0.5, 1.5, {}), ('hvac', 6.0, -1.2, {'w': 2.4, 'd': 1.8, 'fans': 1})]})
    K.pipe(B, [(-3.6, 7.0, 31.0), (-2.0, 7.0, 31.0), (-2.0, 8.4, 31.0), (8.0, 8.4, 31.0)], r=0.45, mat='pipeDark', supports=False)
    # v5: more of the concept's secondary layer: a pipe run and cable tray along the casthouse front, door canopies,
    # a stair to its roof, crates and a skid on the apron, extra roof units
    K.pipe(B, [(-2.0, 3.6, 38.9), (18.0, 3.6, 38.9)], r=0.3, mat='pipe', supports=False)
    K.cable_tray(B, (-2.0, 5.9, 38.8), (18.0, 5.9, 38.8), w=0.45)
    K.ladder(B, (18.6, 0.0, 36.0), (1, 0, 0), 7.0)
    for (cx, cz, sz) in ((21.0, 39.5, (1.6, 1.2, 1.6)), (22.6, 39.8, (1.2, 1.0, 1.2)), (21.6, 39.5, (1.0, 0.8, 1.0))):
        K.crate(B, (cx, 0.0 if sz[1] > 0.9 else 1.2, cz), sz)
    K.hvac(B, (12.0, 7.0, 32.0), w=2.6, d=1.8, fans=2)
    # switch room, control box, stairs, crates on the +X apron
    # r4: the switch-room hut went (judges: scattered huts); stacked plate and coils by the shed wall instead
    for (x, z) in ((33.0, -8.0), (34.4, -8.0), (33.0, -9.4), (34.4, -9.4), (33.7, -11.2)):
        K.pallet(B, (x, 0.0, z), load='plate')
    for (x, z) in ((32.6, -13.5), (34.6, -13.5)):
        B.cyl(0.8, 1.2, at=(x, 0.8, z), rot=(0, 90, 0), mat='pipe', n=16)        # steel coils on the ground
    # the pour bay's control house (the concept: a light concrete block with a railed roof beside the runner)
    for (cx, cz) in ((37.5, -6.0), (37.5, 28.0), (27.0, 37.0), (29.0, 37.5)):
        K.crate(B, (cx, 0.0, cz), (1.6, 1.2, 1.6))
    # yard dressing: lamp posts, cabinets, workers, a truck at the shed's back end, a forklift by the switch room
    for (x, z, rot) in ((38.5, 40.0, -135), (38.5, -48.0, -45), (-38.5, 40.0, 135)):
        K.lamp_post(B, (x, 0.0, z), h=8.0, arm=1.2, rot=rot)
    for (x, z, r) in ((-39.0, 10.0, 90.0), (-39.0, 12.0, 90.0), (38.5, -24.0, -90.0)):
        K.cabinet(B, (x, 0.0, z), rot=r)
    # r4: the truck went (judges: the trailer read as scattered clutter, not the concept's plant)
    K.forklift(B, (37.0, 0.0, -16.0), heading=200)
    for (x, z, hd) in ((36.5, 22.0, 90), (37.0, 6.0, 260), (10.0, 40.5, 10), (24.0, 34.0, 200)):
        K.worker(B, (x, 0.0, z), heading=hd)
    K.flood_on_wall(B, (SH_X + 14.05, 16.0, -12.0), (1, 0, 0), (36.0, 0.0, -14.0))
    K.flood_on_wall(B, (SH_X + 14.05, 16.0, -36.0), (1, 0, 0), (36.0, 0.0, -34.0))
    clutter(B)
    # r10 (judge A: "the shed roof is large plain surfaces"; "base pipework on the stacks"): exhaust ducts on saddles along
    # both roof slopes, small pipe runs with valves round the stack bases
    for (dx, zs_) in ((7.5, (-43.0, -2.0)), (-7.5, (-40.0, 0.0)), (7.5, (2.0, 25.0))):
        x_ = SH_X + dx
        y_ = 14.4 + (17.8 - 14.4) * (1 - abs(dx) / 14.0) + 1.1
        K.pipe(B, [(x_, y_, zs_[0]), (x_, y_, zs_[1])], r=0.55, mat='pipeDark', flanges=True, rings=False)
        for z_ in [zs_[0] + 2 + 5 * k for k in range(int((zs_[1] - zs_[0] - 2) / 5) + 1)]:
            B.box((0.3, 0.7, 0.4), at=(x_, y_ - 0.75, z_), mat='frame', bevel=0.02)
    for (sx_, sz_) in ((-16.0, -14.0), (-14.0, -34.0)):
        K.pipe(B, [(sx_ + 6.5, 0.9, sz_ - 3.0), (sx_ + 6.5, 0.9, sz_ + 3.0), (sx_ + 10.0, 0.9, sz_ + 3.0)], r=0.3, mat='pipe', supports=True, ground=0.0)
        K.valve(B, (sx_ + 6.5, 0.9, sz_), (0, 0, 1), r=0.3)
        K.cabinet(B, (sx_ + 7.2, 0.0, sz_ - 5.0), w=1.0, rot=90)
    # r4 (coordinator / judge A: the concept stacks light boxy blocks round the furnace foot): two low light blocks on the
    # furnace plinth between the front legs (y 3, in front of the hearth drum) and a lower annex on the -X side
    # r7 (judges: merge the small cabins into fewer, larger attached blocks): one light casthouse block across the furnace
    # front between the hugging legs (on the furnace plinth), a 10 m annex block on the -X side, and an annex attached to
    # the shed's front end beside the pour bay (it replaces the free-standing control house)
    # r9: 3.6 m (5.5 hid half of the light hearth drum, the concept's lower light band)
    K.block(B, (FX, 3.0, FZ + 13.3), (12.0, 3.6, 4.6), frame='frameL',
            sides={'+z': {'bay': 4.0, 'storey': 3.6, 'doors': [2.0, 10.0], 'windows': []},
                   '+x': {'bay': 2.3, 'storey': 3.6}, '-x': {'bay': 2.3, 'storey': 3.6}},
            roof={'parapet': 0.4, 'units': [('vent', -3.0, 0.0, {}), ('hvac', 2.5, 0.0, {'w': 2.4, 'd': 1.6, 'fans': 1})]})
    K.block(B, (-37.0, 0.0, 17.8), (6.0, 11.0, 8.4),
            sides={'+z': {'bay': 3.0, 'storey': 5.5, 'doors': [3.0]}, '+x': {'bay': 4.2, 'storey': 5.5},
                   '-x': {'bay': 4.2, 'storey': 5.0, 'louvres': [(4.2, 6.5, 2.0, 1.6)]}},
            roof={'parapet': 0.4, 'units': [('hvac', 0.0, 0.0, {'w': 2.2, 'd': 1.6, 'fans': 1})]})
    K.block(B, (26.0, 0.0, 30.8), (13.0, 8.0, 6.4), frame='frameL',
            sides={'+z': {'bay': 4.33, 'storey': 4.0, 'doors': [2.2, 10.8], 'windows': [1], 'win': (1.6, 1.0), 'louvres': [(6.5, 1.6, 2.0, 1.4)]},
                   '+x': {'bay': 3.2, 'storey': 4.0, 'windows': [1], 'win': (1.4, 1.0)}},
            roof={'parapet': 0.4, 'units': [('hvac', -3.0, 0.0, {'w': 2.6, 'd': 1.8}), ('vent', 3.0, 0.0, {})]})



def clutter(B):
    """v6 (vibes, correction 43): the concept's density: small machinery, pallets, drums, crates, pipe clusters on
    stools, valves, gas bottles, small sheds, lamp posts and figures packed round the furnace foot, along the plinth
    edges and in front of the pour bay (BUILDING-GUIDE.md 5a: no bare run of apron over 15 m at the concept camera),
    plus the process-glow spill lights (hearth band, runner)."""
    # --- glow spill: the hearth band lights the furnace foot and casthouse roof; the runner lights the portal floor
    # r2: 900 cd / 34 m washed the whole furnace foot and the shed gable orange: a local spill only
    # r5: lower and weaker: at 13 m it painted the light hearth drum peach; the concept lights the ground and the legs
    B.R.spill((FX + 11.0, 4.5, FZ + 11.0), color='#ffa048', intensity=220.0, distance=18.0)   # r6/r8: yellow-orange, on the ground
    B.R.spill((FX + 9.0, 19.5, FZ + 9.0), color='#ffa048', intensity=90.0, distance=10.0)     # r8: lights the steel under the bustle
    # r8 (judge A: "the concept's many small warm wall lamps are mostly missing"): pins up the furnace legs' outer corners
    for (sx, sz) in ((1, 1), (-1, 1), (1, -1)):
        for y in (8.0, 14.0, 20.0):
            f = (y - 3.0) / 23.6
            b = 8.8 + 0.6 * f + (3.6 - 0.8 * f) / 2 + 0.12
            B.R.pin((FX + sx * b, y, FZ + sz * b))
    B.R.spill((PB_X + 11.0, 4.5, PB_Z + 4.0), color='#ffa048', intensity=220.0, distance=18.0)   # r7/r9: the pour lights the apron (2.6 m over the runner burnt its core pink-white)
    # --- +X apron along the shed (x 33-40, z -48..0): a pipe cluster on stools at the edge, sheds, pallets, skids
    K.pipe_bundle(B, [(38.6, 0.0, -45.5), (38.6, 0.0, -26.0)], n=3, r=0.22)
    K.pipe_bundle(B, [(39.2, 0.0, -8.0), (39.2, 0.0, -1.0), (35.0, 0.0, -1.0)], n=2, r=0.3)
    K.valve(B, (38.6, 0.72, -30.0), (0, 0, 1), r=0.22)
    K.valve(B, (38.6, 0.72, -38.0), (0, 0, 1), r=0.22)
    for (x, z, r, ld) in ((26.2, -3.0, 0, 'sacks'), (26.2, -4.4, 0, 'boxes'), (27.6, -3.2, 15, 'plate'), (34.5, -20.0, 0, 'boxes'),
                          (34.5, -21.3, 0, 'sacks'), (35.9, -20.2, 0, None), (26.0, -24.0, 90, 'plate'), (26.0, -25.4, 90, 'plate')):
        K.pallet(B, (x, 0.0, z), rot=r, load=ld)
    K.drums(B, (36.5, 0.0, -26.5), n=4)
    K.drums(B, (26.4, 0.0, -42.5), n=3, rot=20)
    K.pump_skid(B, (36.0, 0.0, -3.6), rot=90)
    K.gas_bottles(B, (25.4, 0.0, -14.0), n=6, rot=90)
    K.cabinet(B, (25.2, 0.0, -18.0), rot=90)
    K.cabinet(B, (25.2, 0.0, -19.6), w=0.9, rot=90)
    K.lamp_post(B, (38.5, 0.0, -12.0), h=8.0, arm=1.2, rot=-90)
    K.lamp_post(B, (38.5, 0.0, -36.0), h=8.0, arm=1.2, rot=-90)
    K.bollards(B, [(33.0, -1.0), (33.0, -6.0)])
    # --- the pour bay apron (x 31-40, z 0-28): the runner's foot, a pump skid, plate pallets, a ladle stand, drums
    # (r2: the runner now runs on the apron in front of the portal, world x 35-38, z 4-28: clutter beside it)
    for (x, z, r, ld) in ((36.2, 1.6, 0, 'plate'), (37.6, 1.6, 0, 'plate'), (39.0, 1.6, 0, 'boxes'), (39.2, 21.0, 90, 'sacks'),
                          (39.2, 22.4, 90, 'boxes')):
        K.pallet(B, (x, 0.0, z), rot=r, load=ld)
    K.drums(B, (39.45, 0.0, 15.5), n=2)
    K.gas_bottles(B, (39.3, 0.0, 9.5), n=5, rot=-90)
    K.lamp_post(B, (39.3, 0.0, 6.5), h=7.0, arm=1.0, rot=-90)
    K.lamp_post(B, (39.3, 0.0, 25.5), h=7.0, arm=1.0, rot=-90)
    for (x, z, hd) in ((34.0, 12.0, 90), (39.0, 18.5, 270)):
        K.worker(B, (x, 0.0, z), heading=hd)
    # --- the front-right corner (x 20-40, z 27-42): a small shed, skids, a pipe cluster to the control house
    for (x, z, ld) in ((30.6, 40.4, 'plate'), (32.0, 40.4, 'plate'), (33.4, 40.4, 'boxes')):
        K.pallet(B, (x, 0.0, z), load=ld)
    K.pipe_bundle(B, [(38.8, 0.0, 37.0), (38.8, 0.0, 28.0)], n=2, r=0.25)
    K.pump_skid(B, (36.6, 0.0, 33.5), rot=90)
    K.pallet(B, (25.5, 0.0, 40.6), load='boxes')
    K.pallet(B, (26.9, 0.0, 40.6), load='sacks')
    K.drums(B, (34.2, 0.0, 31.0), n=4, rot=10)
    K.gas_bottles(B, (34.0, 0.0, 35.6), n=4)
    # --- along the casthouse front (z 39-42): pallets, drums, a skid, bottles
    for (x, ld) in ((1.0, 'sacks'), (2.4, 'boxes'), (13.6, 'plate'), (15.0, 'boxes')):
        K.pallet(B, (x, 0.0, 40.6), load=ld)
    K.drums(B, (6.6, 0.0, 40.8), n=3)
    K.pump_skid(B, (9.6, 0.0, 40.6), rot=0, scale=0.9)
    K.cabinet(B, (18.0, 0.0, 41.0), w=1.0)
    # --- the furnace foot (front z 40-42, the -X side x -40..-34): drums, crates, bottles, a skid, a pipe cluster
    # (the v5 cooling main already runs along z 41 from x -35 to -12)
    K.drums(B, (-5.0, 0.0, 41.0), n=4)
    K.drums(B, (-38.6, 0.0, 40.6), n=2)
    K.lamp_post(B, (-36.5, 0.0, 41.5), h=7.0, arm=1.0, rot=0)
    K.lamp_post(B, (-3.0, 0.0, 41.6), h=7.0, arm=1.0, rot=0)
    for (x, z, hd) in ((-2.0, 40.6, 160), (3.5, 40.5, 200)):
        K.worker(B, (x, 0.0, z), heading=hd)
