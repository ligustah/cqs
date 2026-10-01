"""SP-3 spaceport: kit placements for tools/blender/assemble.py (procedural kit, +Z mounts, true size).

    python3 spaceport_spec.py            # -> tools/blender/specs/spaceport-v1.json

Every ruler part is at kit size (scale 1; rails stretched to their 3 m pitch like the carrier's):
  - 1 m ports in runs of six on the lit decks of every habitat block (3 m decks, 2.5 m pitch);
  - one crew door per block (the human ruler), on its +Z end;
  - handrails along the near-rim walkway and round the control block;
  - 20-ft ISO containers stacked two high on the near-rim walkway (cargo staging);
  - floodlights on the rim corners and the block roofs, aimed into the bay;
  - nav-light housings (red obstruction lights) at the extremities; antennas and a radome on the control block.
Positions come from spaceport_dims (the same frames spaceport.py builds on), so nothing is snapped.
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import spaceport_dims as D  # noqa: E402
from spaceport_kit import habBlock_ports  # noqa: E402

R = lambda v: [round(float(x), 3) for x in v]


def xf(M, p):
    return (M @ np.r_[p, 1.0])[:3]


def xd(M, d):
    return M[:3, :3] @ np.asarray(d, float)


def main():
    P = []
    nports = 0
    for b in D.HAB_BLOCKS:
        M = D.block_frame(b)
        lit = {4: [2], 5: [1, 3], 6: [2, 4]}[b['decks']]
        for x, y, z, sx in habBlock_ports(b['L'], b['W'], b['decks'], lit_decks=lit, run=5):
            P.append(dict(part='port', p=R(xf(M, (x, y, z))), n=R(xd(M, (sx, 0, 0))), up=R(xd(M, (0, 1, 0))), snap=False, seat={'check': False}))
            nports += 1
        # the crew door on the +Z end, in its bay frame
        P.append(dict(id=f"door {b['rim']} z {b['z']}", part='door', p=R(xf(M, (0, 3.3, b['L'] / 2 + 0.5))), n=R(xd(M, (0, 0, 1))), up=R(xd(M, (0, 1, 0))), snap=False, seat={'check': False}))
        # floodlight on the roof's forward edge, aimed along the block
        H = 2.0 + b['decks'] * 3.0 + 1.5
        P.append(dict(part='floodlight', p=R(xf(M, (b['W'] * 0.3, H, b['L'] * 0.45))), n=R(xd(M, (0, 1, 0))), up=R(xd(M, (0, 0, 1))), rot=0, snap=False, seat={'check': False}))
    # walkway rails: outboard edge of the near trough rim, and the far rim's inboard edge (forward of the hood)
    xo = D.TROUGH['a'] + D.SHELL_T / 2 + D.RIM['r_out'] - 0.4
    for z0, z1 in ((515.0, 445.0), (300.0, 210.0), (-100.0, -160.0)):
        P.append(dict(id='near rim walkway rail', part='rail', row={'from': [xo, 4.0, z0], 'to': [xo, 4.0, z1], 'pitch': 3.0}, n=[0, 1, 0], snap=False, seat={'check': False}))
    xf_ = -(D.TROUGH['a'] - D.RIM['r_in'] + D.SHELL_T / 2 + 0.4)
    for z0, z1 in ((470.0, 420.0),):
        P.append(dict(id='far rim walkway rail', part='rail', row={'from': [xf_, D.RIM_TOP['trough_far'][0][1], z0], 'to': [xf_, D.RIM_TOP['trough_far'][0][1], z1], 'pitch': 3.0}, n=[0, 1, 0], snap=False, seat={'check': False}))
    # containers: two rows, two high, on the near rim walkway between the blocks
    for z0, z1 in ((292.0, 248.0), (188.0, 150.0), (-176.0, -230.0)):
        for x in (173.0, 175.6):
            P.append(dict(id='container staging', part='container', row={'from': [x, 4.0, z0], 'to': [x, 4.0, z1], 'pitch': 6.4},
                          rows={'count': 2, 'step': [0, 2.62, 0]}, n=[0, 1, 0], up=[1, 0, 0], snap=False, seat={'check': False}))
    # floodlights at the rim / arch corners, aimed into the bay
    for z in (D.TROUGH['z1'] - 10, D.TROUGH['z0'] + 10, 0.0):
        P.append(dict(part='floodlight', p=[D.TROUGH['a'] - 2, 4.0, z], n=[0, 1, 0], up=[-1, 0, 0], snap=False, seat={'check': False}))
        P.append(dict(part='floodlight', p=[-(D.TROUGH['a'] - 2), D.RIM_TOP['trough_far'][0][1], z], n=[0, 1, 0], up=[1, 0, 0], snap=False, seat={'check': False}))
    # control block roof: antennas and a radome
    cb = next(b for b in D.HAB_BLOCKS if b['rim'] == 'hood_top')
    M = D.block_frame(cb)
    H = 2.0 + cb['decks'] * 3.0 + 1.5
    for dx in (-6.0, 6.0):
        P.append(dict(part='antenna', p=R(xf(M, (dx, H, -cb['L'] * 0.35))), n=[0, 1, 0], up=[0, 0, 1], scale=2.0, snap=False, seat={'check': False}))
    P.append(dict(part='dome', p=R(xf(M, (0, H, cb['L'] * 0.3))), n=[0, 1, 0], up=[0, 0, 1], scale=3.0, snap=False, seat={'check': False}))
    P.append(dict(id='control block roof rail', part='rail', row={'from': R(xf(M, (-cb['W'] / 2 + 0.6, H, -cb['L'] / 2 + 1))), 'to': R(xf(M, (-cb['W'] / 2 + 0.6, H, cb['L'] / 2 - 1))), 'pitch': 3.0},
                  n=[0, 1, 0], snap=False, seat={'check': False}, mirrorX=True))
    # nav-light housings (red obstruction lights) at the extremities: rim ends and the mast tops
    navs = [[D.TROUGH['a'] + D.SHELL_T / 2, 4.0, D.TROUGH['z1'] + 4], [D.TROUGH['a'] + D.SHELL_T / 2, 4.0, D.TROUGH['z0'] - 4],
            [-(D.TROUGH['a'] + D.SHELL_T / 2), D.RIM_TOP['trough_far'][0][1], D.TROUGH['z1'] + 4],
            [0.0, D.HOOD['a'] + D.SHELL_T + 4.0, D.HOOD['z0'] - 2], [0.0, D.HOOD['a'] + D.SHELL_T + 4.0, D.HOOD['z1'] + 2]]
    for p in navs:
        P.append(dict(part='navlight', p=R(p), n=[0, 1, 0], up=[0, 0, 1], snap=False, seat={'check': False}))
    spec = {
        'about': 'SP-3 orbital spaceport (cqs-fleet installation): station geometry from tools/blender/buildings/spaceport.py '
                 '(station frame, metres, forward +Z, up +Y, left +X, not re-centred); kit parts from assets/parts-blender at true size.',
        'hull': {'glb': 'HULL_GLB_FROM_COMMAND_LINE', 'rotate': [0, 0, 0], 'scale': 1.0, 'centre': False},
        'partsDir': '../../../assets/parts-blender',
        'partDefaults': {'door': {'sink': 0.0}, 'port': {'sink': 0.03}, 'floodlight': {'sink': 0.02}, 'navlight': {'sink': 0.0},
                         'rail': {'sink': 0.0, 'xAlong': True, 'scale': [3, 1, 1]}, 'antenna': {'sink': 0.05}, 'dome': {'sink': 0.05}, 'container': {'sink': 0.0}},
        'fixes': {'door': {'decimate': 0.3}, 'port': {'decimate': 0.2}, 'rail': {'decimate': 1.0}, 'floodlight': {'decimate': 0.3},
                  'navlight': {'decimate': 0.35}, 'antenna': {'decimate': 0.45}, 'dome': {'decimate': 0.6}, 'container': {'decimate': 0.25}},
        'seat': {'maxGap': 0.3, 'maxBury': 0.6, 'drop': False},
        'bake': {'ao': False},
        'placements': P,
    }
    out = os.path.normpath(os.path.join(HERE, '..', 'specs', 'spaceport-v1.json'))
    json.dump(spec, open(out, 'w'), indent=1)
    print(out, len(P), 'placements,', nports, 'ports')


if __name__ == '__main__':
    main()
