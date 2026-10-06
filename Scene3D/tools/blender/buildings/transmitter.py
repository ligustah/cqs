"""TRANSMITTER: orbital hexagonal ring (megaproject): six corner nodes, six girder segments with a glowing blue inner
edge, solar wings and a docking hub (concept style-library/styles/cqs-fleet/images/buildings/transmitter-concept.jpg).

Orbital: no plinth, space backdrop (SPEC orbital, colony.js SPACE_BACKDROP), the ring centre at the origin.
Composed from fal components (assets/parts-colony: ringModule x6, ringSegment x12, solarWing x5, dockingHub; README-colony.md
catalogue) with the shared kit's lattice trusses, pipe runs and lights (blue inner-field glow boxes, amber marker pins,
beacons). Built by colony_build.py:
    $PY tools/blender/buildings/colony_build.py transmitter <work> [--tex 4096]

Frame: metres, +Y up (the ring lies in the XZ plane, its top face up), +Z front, +X left. The concept looks down on the
ring's top face, nearly square on (az ~10, el ~62), corners pointing left and right.
Sizes: a thick band like the concept's (about a fifth of the diameter): an inner row of 104 m girder segments (20 x 14 m,
blue edge inward) and an outer row at 1.2 scale, corner nodes at 2.2 scale (88 m radial) 128 m from the centre; the
inner opening ~180 m across the flats; solar wings at 2.5x (85 m); overall ~400 m with the wings.
"""
import math

import bkit as K

SPEC = {
    'title': 'Transmitter', 'gameId': 'TRANSMITTER', 'group': 'megaproject', 'orbital': True,
    'footprint': [400, 360], 'height': 54.0,
    'camera': {'az': 10, 'el': 70},
    'about': 'orbital hexagonal ring: six thruster-clustered corner nodes, six girder segments with a glowing blue inner edge, six solar wings and a docking hub',
}

A1 = 100.0                    # inner segment row: centre distance from the ring centre (apothem)
A2 = 123.0                    # outer segment row (scale 1.2: 124.8 m long, 24 m wide)
RC = 128.0                    # corner node centre radius
SEG_HEADING = -90.0           # ringSegment: long axis Z, blue edge on its +X face (part check): -90 turns +X inward
NODE_HEADING = 180.0          # ringModule: long axis Z, its thruster quad reads at -Z in the ring (r2 check): turned so the nozzles point outward
WING_ROLL = 45.0              # solarWing: boom at -Z (part check), panels rolled ~45 deg about Z: roll them flat


def P(r, deg, y=0.0):
    a = math.radians(deg)
    return (r * math.cos(a), y, r * math.sin(a))


def model(B):
    BLUE = '#5fb2ff'
    corners = [i * 60.0 for i in range(6)]
    # --- corner nodes: the heavy fal module at 2.2 (88 m radial, 58 m wide), turned radially (thrusters outward), spanning both segment rows
    for t in corners:
        K.component(B, 'ringModule', P(RC, t, -26.0), heading=90.0 - t + NODE_HEADING, scale=2.2)
        for k in (-1, 1):                                    # amber markers at the node's outer corners
            B.R.pin(P(RC + 40.0, t + k * 11.0, 26.0))
    # --- girder segments: two rows between the nodes, the inner row's blue edge inward
    for t in corners:
        tm = t + 30.0
        K.component(B, 'ringSegment', P(A1, tm, -8.0), heading=270.0 - tm + SEG_HEADING)
        K.component(B, 'ringSegment', P(A2, tm, -9.5), heading=270.0 - tm + SEG_HEADING, scale=1.2)   # blue edge into the gap
        a = math.radians(tm)
        u = (-math.sin(a), 0.0, math.cos(a))
        # the inner field edge: a run of blue glow boxes along the inner face of the inner row
        for s in range(-5, 6):
            c = P(A1 - 10.4, tm, -4.5)
            p = (c[0] + u[0] * s * 9.6, c[1], c[2] + u[2] * s * 9.6)
            B.R.glowbox(p, (8.4, 2.6, 0.3), color=BLUE, radiance=2.2, roty=math.radians(-90.0 - tm))
            q = P(A1 - 8.6, tm, 6.15)                        # and along the top inner edge (the concept's lit rim)
            B.R.glowbox((q[0] + u[0] * s * 9.6, q[1], q[2] + u[2] * s * 9.6), (8.4, 0.12, 1.6), color=BLUE, radiance=2.2,
                        roty=math.radians(-90.0 - tm))
        # amber markers along the outer edge, pipe runs in the gap between the rows
        for s in (-48.0, -24.0, 0.0, 24.0, 48.0):
            c = P(A2 + 12.6, tm, 7.0)
            B.R.pin((c[0] + u[0] * s, c[1], c[2] + u[2] * s))
        for (dr, y, r) in ((-1.0, 2.0, 1.1), (0.4, 0.0, 0.8), (-0.2, -3.0, 1.3)):
            c = P(A1 + 11.0 + dr, tm, y)
            L = 2 * (A1 + 11.0) * math.tan(math.radians(30)) * 0.5 - 14.0
            K.pipe(B, [(c[0] - u[0] * L, c[1], c[2] - u[2] * L), (c[0] + u[0] * L, c[1], c[2] + u[2] * L)], r=r,
                   mat='pipe' if r < 1.2 else 'pipeDark', rings=True)
    # --- the inner field: a faint blue hexagon (three overlapping rectangles), the transmission plane
    ai = A1 - 10.6
    side = 2 * ai * math.tan(math.radians(30))
    # v3: a blue haze, brightest at the rim and deepening toward the centre (the concept's luminous field; v2 was a
    # dark navy plane): eight nested hexagons, each a little nearer the camera, from a light sky blue to a deep blue
    N = 16
    for i in range(N):
        u = i / (N - 1)                                         # 0 at the rim, 1 at the centre
        f = 1.0 - 0.78 * u
        c0, c1 = (0xa9, 0xcd, 0xf5), (0x50, 0x66, 0x89)
        col = '#%02x%02x%02x' % tuple(round(a + (b - a) * u ** 0.7) for a, b in zip(c0, c1))
        for k in range(3):
            B.R.glowbox((0.0, -6.0 + 0.08 * i, 0.0), (side * f, 0.04, 2 * ai * f), color=col, radiance=0.30 - 0.17 * u ** 0.6,
                        roty=math.radians(60.0 * k))
    # --- solar wings at 2x: one off each node but the hub's, boom toward the node, panels outboard
    for i, t in enumerate(corners):
        if t == 180.0:
            continue                                         # the docking hub's node
        dt = 9.0 if i % 2 else -9.0
        # placed directly so the wing can also roll about its boom: the fal part's panels are tilted ~45 deg about its
        # long axis; WING_ROLL lays them flat to the camera like the concept's
        a = math.radians(t + dt)
        up = (math.cos(a), 0.0, math.sin(a))                  # part +Z (boom inward at -Z): radially outward
        tan = (-math.sin(a), 0.0, math.cos(a))
        r = math.radians(WING_ROLL)
        n = (tan[0] * math.sin(r), math.cos(r), tan[2] * math.sin(r))   # part +Y
        along = (n[1] * up[2] - n[2] * up[1], n[2] * up[0] - n[0] * up[2], n[0] * up[1] - n[1] * up[0])  # n x up = part +X
        B.R.place('colony:solarWing', P(RC + 92.0, t + dt, -10.0), n=n, up=up, along=along, scale=2.5, id='solarWing')
    # --- the docking hub on the -X node (the concept's round port with its blue core), port facing outward
    # dockingHub: port on its +X face (part check): heading 180 turns it to -X
    K.component(B, 'dockingHub', P(RC + 56.0, 180.0, -12.7), heading=180.0, scale=1.4)
    B.R.glowbox(P(RC + 74.0, 180.0, 5.0), (0.3, 4.0, 4.0), color=BLUE, radiance=2.0)
    # beacons on three nodes
    for t in (60.0, 180.0, 300.0):
        B.R.beacon(P(RC, t, 30.0))
