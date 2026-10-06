"""STEEL_MILL: blast furnace tower with skip hoist, glowing pour bay, stacks, long shed
(concept style-library/styles/cqs-fleet/images/buildings/steel_mill-concept.jpg).

Built only from the shared kit (bkit.py) by colony_build.py:
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
    'footprint': [72, 96], 'height': 62.0,
    'camera': {'az': 40, 'el': 27},
    'about': 'blast furnace in a steel tower frame with a skip-hoist gallery, glowing pour bay with an overhead crane, two banded stacks, long clad shed',
}

FX, FZ = -16.0, 24.0         # furnace axis
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
    W, D = SPEC['footprint']
    K.plinth(B, W, D, h=1.6, chamfer=2.4, slab=8.0, lamp_pitch=18.0,
             markings=[([(30.0, 46.0), (30.0, -46.0)], 0.2, 'frame2'), ([(-34.0, 45.0), (34.0, 45.0)], 0.2, 'frame2'),
                       ([(26.0, 12.0), (35.5, 12.0)], 0.35, 'hazard'), ([(26.0, 24.0), (35.5, 24.0)], 0.35, 'hazard')],
             grates=[(31.0, -12.0, 0.8, 3.0), (31.0, 30.0, 0.8, 3.0), (-6.0, 44.0, 3.0, 0.8)],
             steps=[(10.0, 48.0, '+z')])
    furnace(B)
    gas_cleaner(B)
    shed(B)
    stacks(B)
    # skip-hoist gallery: an inclined covered conveyor from the stockhouse on the shed roof up to the furnace top
    p0, p1 = (2.0, EAVE + 6.0, 8.0), (FX + 3.0, 47.0, FZ - 2.0)
    K.truss(B, p0, p1, 3.0, bay=3.0, chord=0.35, web=0.16)
    from mathutils import Vector
    a, b = Vector(p0), Vector(p1)
    with B.at(M=K.frame_along(a, b)):
        L = (b - a).length
        B.box((3.6, 2.6, L), at=(0, 2.7, L / 2), mat='panel', bevel=0.05)
        B.box((3.9, 0.3, L + 0.3), at=(0, 4.1, L / 2), mat='frame', bevel=0.02)
    K.block(B, (2.0, EAVE + 0.0, 8.0), (7.0, 9.0, 7.0),
            sides={'+x': {'bay': 3.5, 'windows': [1], 'win': (1.2, 1.0)}, '+z': {'bay': 3.5}}, roof={'parapet': 0.4})
    K.lattice_tower(B, (FX + 9.0, 7.5, FZ - 6.0), 3.0, 33.0, bay=3.3, chord=0.3, web=0.14)
    # yard dressing: lamp posts, cabinets, workers, a truck at the shed's back door, a forklift by the pour bay
    for (x, z, rot) in ((33.0, 44.0, -135), (33.0, -44.0, -45), (-34.0, 44.0, 135)):
        K.lamp_post(B, (x, 0.0, z), h=8.0, arm=1.2, rot=rot)
    for (x, z, r) in ((-35.0, 10.0, 90.0), (-35.0, 12.0, 90.0), (31.5, -20.0, -90.0)):
        K.cabinet(B, (x, 0.0, z), rot=r)
    K.truck(B, (31.0, 0.0, -24.0), heading=180)
    K.forklift(B, (31.0, 0.0, 4.0), heading=200)
    for (x, z, hd) in ((28.5, 14.0, 90), (29.5, 21.5, 260), (12.0, 43.0, 10), (30.0, 34.0, 200)):
        K.worker(B, (x, 0.0, z), heading=hd)
    K.flood_on_wall(B, (SH[1] + 0.05, EAVE - 3.0, 4.5), (1, 0, 0), (32.0, 0.0, 18.0))
    K.flood_on_wall(B, (SH[1] + 0.05, EAVE - 3.0, -26.0), (1, 0, 0), (32.0, 0.0, -24.0))
