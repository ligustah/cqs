"""OIL_TANKS: three large floating-roof tanks in a bunded yard, pump house, pipe manifold
(concept style-library/styles/cqs-fleet/images/buildings/oil_tanks-concept.jpg).

v2: composed from fal components (assets/parts-colony: floatTank x3, plantHouse as the pump house, manifoldSkid;
README-colony.md catalogue) with the shared parametric kit (plinth, the bund wall with coping, buttresses, corner
pylons and stairs, the pipe manifold, dressing, lights). Built by colony_build.py:
    $PY tools/blender/buildings/colony_build.py oil_tanks <work> [--tex 4096]

Frame: metres, plinth top y = 0, +Z front, +X left. The concept camera looks at the (+X, +Z) corner on the diagonal
(az ~45, el ~29): two tanks at the left and right corners, the third at the back, the pump house in front of the
centre, the pipe manifold between them, a 3.2 m bund wall all round on the slab edge.
Sizes (real-world, against the concept's doors and 1.1 m rails): slab 72 x 72 m; tanks 30 m across, 15.5 m tall
(floatTank); bund wall 3.2 m; pump house 17 x 8.5 m, 7.8 m tall (plantHouse).
"""
import math

import bkit as K

SPEC = {
    'title': 'Oil Tanks', 'gameId': 'OIL_TANKS', 'group': 'storage',
    'footprint': [72, 72], 'height': 16.0,
    'camera': {'az': 45, 'el': 29},
    'about': 'three 30 m floating-roof oil tanks in a bunded concrete yard, a pump house, a ground pipe manifold, wall stairs and corner lamp pylons',
}

W, D = SPEC['footprint']
X0, X1, Z0, Z1 = -W / 2, W / 2, -D / 2, D / 2
TANKS = {'L': (-18.5, 16.5), 'R': (16.5, -18.5), 'B': (-17.5, -17.5)}
PH = (13.0, 13.0)          # pump house centre
MAN = (-1.0, -1.0)         # manifold junction
WALL_H = 3.2


def bund_wall(B):
    """3.2 m bund wall on the slab edge: light concrete panels with a gunmetal coping and a thin amber line, a dark
    toe, buttresses every 6.5 m on the inner face, square pylons with lamp posts at the corners, an access gap with
    stairs over the wall at the front."""
    t = 0.8
    inset = 1.6
    xa, xb, za, zb = X0 + inset, X1 - inset, Z0 + inset, Z1 - inset
    runs = [((xa, zb), (xb, zb)), ((xb, zb), (xb, za)), ((xb, za), (xa, za)), ((xa, za), (xa, zb))]
    for (p, q) in runs:
        L = math.hypot(q[0] - p[0], q[1] - p[1])
        ux, uz = (q[0] - p[0]) / L, (q[1] - p[1]) / L
        nx, nz = -uz, ux            # outward normal
        B.bar((p[0], WALL_H / 2, p[1]), (q[0], WALL_H / 2, q[1]), t, WALL_H, mat='kerb', bevel=0.05)
        B.bar((p[0] + nx * 0.05, 0.25, p[1] + nz * 0.05), (q[0] + nx * 0.05, 0.25, q[1] + nz * 0.05), t + 0.2, 0.5, mat='concrete2', bevel=0.0)
        B.bar((p[0], WALL_H + 0.12, p[1]), (q[0], WALL_H + 0.12, q[1]), t + 0.3, 0.24, mat='frame', bevel=0.03)
        for s in (1, -1):
            B.bar((p[0] + s * nx * (t / 2 + 0.01), WALL_H - 0.45, p[1] + s * nz * (t / 2 + 0.01)), (q[0] + s * nx * (t / 2 + 0.01), WALL_H - 0.45, q[1] + s * nz * (t / 2 + 0.01)), 0.03, 0.12, mat='amber', bevel=0.0)
        n = int(L / 6.5)
        for k in range(1, n):
            f = k / n
            cx, cz = p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f
            # panel joints on the outer face and buttresses inside
            B.box((0.08, WALL_H - 0.6, 0.08), at=(cx + nx * (t / 2 + 0.02), (WALL_H - 0.6) / 2 + 0.5, cz + nz * (t / 2 + 0.02)), mat='seam', bevel=0.0)
            with B.at(at=(cx - nx * (t / 2 + 0.5), 0.0, cz - nz * (t / 2 + 0.5)), rot=(0, math.degrees(math.atan2(ux, uz)), 0)):
                B.prism([(-0.3, -0.5), (0.3, -0.5), (0.3, 0.5), (-0.3, 0.5)], 0.0, WALL_H - 0.6, mat='concrete2', bevel=0.03)
    for (x, z) in ((xa, za), (xa, zb), (xb, za), (xb, zb)):
        B.box((2.6, WALL_H + 1.6, 2.6), at=(x, (WALL_H + 1.6) / 2, z), mat='kerb', bevel=0.08)
        B.box((2.9, 0.3, 2.9), at=(x, WALL_H + 1.75, z), mat='frame', bevel=0.03)
        B.box((2.7, 0.12, 2.7), at=(x, WALL_H + 0.6, z), mat='amber', bevel=0.0)
        K.lamp_post(B, (x, WALL_H + 1.9, z), h=4.5, arm=0.8, rot=math.degrees(math.atan2(-x, -z)))
    # access stairs over the wall at the front-left and the left side, with platforms on top
    for (x, z, d) in ((-14.0, zb, (0, 0, -1)), (xb, -2.0, (-1, 0, 0))):
        if d[2]:
            K.stair(B, (x, 0.0, z + 5.6), (0, 0, -1), WALL_H + 0.24, w=1.4)
            B.box((1.8, 0.15, 2.6), at=(x, WALL_H + 0.3, z), mat='grate', bevel=0.0)
            K.ladder(B, (x, 0.2, z - 0.7), (0, 0, -1), WALL_H + 0.2, cage=False)
        else:
            K.stair(B, (x + 5.6, 0.0, z), (-1, 0, 0), WALL_H + 0.24, w=1.4)
            B.box((2.6, 0.15, 1.8), at=(x, WALL_H + 0.3, z), mat='grate', bevel=0.0)
    # amber pins along the coping (the concept's wall lamps) and on the pylons
    for (p, q) in runs:
        for k in range(1, 6):
            f = k / 6
            B.R.pin((p[0] + (q[0] - p[0]) * f, WALL_H + 0.35, p[1] + (q[1] - p[1]) * f))


def manifold(B):
    """Ground pipe manifold: a cross-yard header from the pump house to the junction, branches to each tank's pipe
    pair, elbows rising onto the tank shells, valves, shoes."""
    y = 1.4
    for k, dz in enumerate((-1.2, 0.0, 1.2)):
        r = 0.55 if k == 1 else 0.42
        K.pipe(B, [(PH[0] - 9.5, y + 0.2 * k, PH[1] + dz - 4.0), (MAN[0] + dz, y + 0.2 * k, PH[1] + dz - 4.0), (MAN[0] + dz, y + 0.2 * k, MAN[1])],
               r=r, mat='pipe' if k != 2 else 'pipeDark', supports=True, support_pitch=6.0)
    # branches: to tank L (-X, +Z), tank R (+X, -Z), tank B (back)
    for key, (tx, tz) in TANKS.items():
        dx, dz = tx - MAN[0], tz - MAN[1]
        L = math.hypot(dx, dz)
        ux, uz = dx / L, dz / L
        e = (tx - ux * 16.0, tz - uz * 16.0)          # just outside the shell
        for s, r in ((-1.0, 0.5), (1.0, 0.42)):
            ox, oz = -uz * s * 1.3, ux * s * 1.3
            if key == 'B':
                pts = [(MAN[0] + ox, y + 0.6, MAN[1] + oz), (e[0] + ox, y + 0.6, e[1] + oz), (e[0] + ox, 2.6, e[1] + oz)]
            elif key == 'L':
                pts = [(MAN[0] + ox, y + 0.6, MAN[1] + oz), (MAN[0] + ox, y + 0.6, e[1] + oz), (e[0] + ox, y + 0.6, e[1] + oz), (e[0] + ox, 2.6, e[1] + oz)]
            else:
                pts = [(MAN[0] + ox, y + 0.6, MAN[1] + oz), (e[0] + ox, y + 0.6, MAN[1] + oz), (e[0] + ox, y + 0.6, e[1] + oz), (e[0] + ox, 2.6, e[1] + oz)]
            K.pipe(B, pts, r=r, mat='pipe', supports=True, support_pitch=6.0)
            K.valve(B, (e[0] + ox - ux * 2.0, y + 0.6, e[1] + oz - uz * 2.0), (ux, 0, uz), r=r)
    # the junction: a header box with risers and valves (the concept's tee cluster in the yard centre)
    B.box((4.4, 1.2, 4.4), at=(MAN[0], 0.6, MAN[1]), mat='concrete2', bevel=0.05)
    for (dx, dz) in ((-1.0, -1.0), (1.0, -1.0), (-1.0, 1.0), (1.0, 1.0)):
        B.vcyl(0.45, 3.4, (MAN[0] + dx, 1.2, MAN[1] + dz), mat='pipe', n=12)
        B.vcyl(0.6, 0.15, (MAN[0] + dx, 3.2, MAN[1] + dz), mat='pipeDark', n=12)
    K.pipe(B, [(MAN[0] - 1.0, 4.6, MAN[1] - 1.0), (MAN[0] - 1.0, 4.6, MAN[1] + 1.0), (MAN[0] + 1.0, 4.6, MAN[1] + 1.0), (MAN[0] + 1.0, 4.6, MAN[1] - 1.0)], r=0.45, mat='pipe', rings=False)
    K.valve(B, (MAN[0] + 1.0, 4.6, MAN[1]), (0, 0, 1), r=0.45)
    # a long high run from the junction over the yard to the back tank (the concept's raised T at the back)
    K.pipe(B, [(MAN[0], 4.6, MAN[1] - 1.0), (MAN[0], 4.6, -24.0), (MAN[0] - 2.0, 4.6, -26.0), (-1.0, 4.6, Z0 + 4.0)], r=0.5, mat='pipe', supports=True, support_pitch=5.5)


def model(B):
    K.plinth(B, W, D, h=1.5, chamfer=2.4, slab=8.0, lamp_pitch=16.0,
             markings=[([(PH[0] - 9.0, PH[1] + 7.5), (PH[0] + 9.0, PH[1] + 7.5)], 0.16, 'amber'),
                       ([(4.0, 24.0), (4.0, 30.0)], 0.3, 'hazard')],
             grates=[(PH[0] - 4.0, PH[1] + 9.5, 2.4, 0.9), (-2.0, 8.0, 1.2, 1.2), (8.0, -6.0, 1.2, 1.2), (24.0, 2.0, 0.9, 2.4)],
             steps=[(-14.0, Z1, '+z'), (X1, -2.0, '+x')])
    # bund floor inside the wall: a darker, drained concrete apron with sump grates
    B.box((W - 6.0, 0.02, D - 6.0), at=(0.0, 0.01, 0.0), mat='concrete2', bevel=0.0)
    for (x, z) in ((-4.0, 20.0), (20.0, -4.0), (-30.0, 0.0), (0.0, -30.0)):
        B.box((1.6, 0.04, 1.6), at=(x, 0.03, z), mat='frame', bevel=0.0)
    bund_wall(B)

    # --- the three tanks (fal component floatTank: 28 m, gauge-hut stair tower, shell pipes), each on a ring footing,
    # turned so the stair towers face the camera side as in the concept
    for k, (x, z) in TANKS.items():
        K.component(B, 'floatTank', (x, 0.0, z), heading={'L': -26.0, 'R': 45.0, 'B': -11.0}[k], scale=1.06)
        B.ring(15.6, 14.8, 0.0, 0.45, (x, 0, z), mat='concrete2', n=56)
        B.R.pin((x, 16.4, z))
    # --- the pump house (fal plantHouse: door on its long face, turned to face +Z), roof units added
    K.component(B, 'plantHouse', (PH[0], 0.0, PH[1]), heading=-90.0)
    for sx in (-1, 1):
        for sz in (-1, 1):
            B.R.pin((PH[0] + sx * 8.6, 7.9, PH[1] + sz * 4.4))
    B.R.beacon((PH[0], 9.0, PH[1]))
    K.component(B, 'manifoldSkid', (PH[0] - 12.0, 0.0, PH[1] - 1.0), heading=0.0)
    manifold(B)
    # stair-and-platform skid at the junction (the concept's amber railed steps), cabinets, bollards, workers
    B.box((3.0, 1.2, 2.4), at=(MAN[0] + 4.5, 0.6, MAN[1] + 4.5), mat='frame2', bevel=0.04)
    K.stair(B, (MAN[0] + 4.5, 0.0, MAN[1] + 8.5), (0, 0, -1), 1.2, w=1.2)
    K.railing(B, [(MAN[0] + 3.0, 1.2, MAN[1] + 3.3), (MAN[0] + 6.0, 1.2, MAN[1] + 3.3), (MAN[0] + 6.0, 1.2, MAN[1] + 5.7)], post=1.2, mat='amber')
    for (x, z, r) in ((PH[0] + 6.0, PH[1] + 6.0, 0), (PH[0] + 7.5, PH[1] + 6.0, 0), (PH[0] - 10.0, PH[1] + 4.5, 0), (27.0, -6.0, -90)):
        K.cabinet(B, (x, 0.0, z), w=1.2, h=1.8, d=0.6, rot=r)
    K.bollards(B, [(PH[0] - 4.0, PH[1] + 7.0), (PH[0] + 4.0, PH[1] + 7.0), (PH[0] + 9.6, PH[1] + 2.0), (MAN[0] + 3.0, MAN[1] - 3.0), (MAN[0] - 3.0, MAN[1] + 3.0)])
    for (x, z, m) in ((26.0, 26.0, 'frame2'), (27.8, 26.0, 'amber'), (-27.0, 28.0, 'frame2')):
        K.crate(B, (x, 0.0, z), (1.4, 1.1, 1.3), mat=m)
    for (x, z, hd) in ((PH[0] - 2.0, PH[1] + 8.0, 20), (MAN[0] + 6.0, MAN[1] + 9.0, 200), (-14.0, Z1 - 7.0, 160)):
        K.worker(B, (x, 0.0, z), heading=hd)
    K.lamp_post(B, (PH[0] - 9.0, 0.0, PH[1] + 7.0), h=6.0, arm=1.0, rot=180)
