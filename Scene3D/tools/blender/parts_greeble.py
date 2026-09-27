# Structure and greebles: pipe run and conduit segments (tile along X at 4 m), hull vent, docking
# clamp, nav light housing. Part frame: X width, Y up, Z out of the hull (metres).
import math
from lib import rrect, circle, chamfer_rect


def pipes(P, length=4.0):
    L = length
    runs = [(-0.28, 0.12, 0.18, 'paint'), (0.0, 0.08, 0.18, 'steel'), (0.22, 0.08, 0.18, 'copper')]
    for y, r, z, mat in runs:
        P.cyl(r, L, at=(0, y, z + r), rot=(0, 90, 0), n=12, mat=mat, bevel=0.0, caps=False)
        # flange joint mid-run and half flanges at the tile ends
        P.cyl(r * 1.45, 0.06, at=(0, y, z + r), rot=(0, 90, 0), n=12, mat='dark', bevel=0.006)
        P.bolts([(0.03, y + r * 1.25 * math.cos(a), z + r + r * 1.25 * math.sin(a)) for a in [k * math.pi / 3 for k in range(6)]], r=0.012, h=0.01, normal=(1, 0, 0), mat='steel')
        for sx in (-1, 1):
            P.cyl(r * 1.45, 0.03, at=(sx * (L / 2 - 0.015), y, z + r), rot=(0, 90, 0), n=12, mat='dark', bevel=0.0)
    # pipe clamps (saddles) at 1 m and 3 m from the tile start
    for x in (-L / 4, L / 4):
        P.box((0.1, 0.8, 0.14), at=(x, -0.03, 0.07), mat='paint2', bevel=0.012)
        for y, r, z, mat in runs:
            P.lathe([(r + 0.005, -0.03), (r + 0.03, -0.03), (r + 0.03, 0.03), (r + 0.005, 0.03)], 12, at=(x, y, z + r), rot=(0, 90, 0), closed=True, mat='dark', sharp=50)
        P.box((0.2, 0.12, 0.012), at=(x, -0.43, 0.006), mat='dark', bevel=0.0)
    return {'pitch': length, 'about': 'three-pipe run along X (0.24 / 0.16 / 0.16 m), tiles at 4 m pitch'}


def conduit(P, length=4.0, width=0.6):
    L, W = length, width
    P.box((L, W, 0.03), at=(0, 0, 0.14), mat='dark', bevel=0.0)
    for sy in (-1, 1):
        P.box((L, 0.03, 0.14), at=(0, sy * (W / 2 - 0.015), 0.2), mat='paint', bevel=0.004)
    for k in range(5):
        P.cyl(0.03 + 0.005 * (k % 2), L, at=(0, -0.2 + k * 0.1, 0.19), rot=(0, 90, 0), n=8, mat='copper' if k % 2 else 'rubber', bevel=0.0, caps=False)
    # cover plates on half the tile, brackets every metre
    P.box((L / 2 - 0.05, W + 0.02, 0.02), at=(L / 4, 0, 0.28), mat='paint', bevel=0.006)
    P.bolts([(L / 4 + dx, sy * (W / 2 - 0.01), 0.29) for dx in (-0.8, -0.3, 0.3, 0.8) for sy in (-1, 1)], r=0.012, h=0.008, mat='steel')
    for x in (-1.5, -0.5, 0.5, 1.5):
        P.box((0.06, W + 0.1, 0.13), at=(x, 0, 0.065), mat='paint2', bevel=0.008)
    return {'pitch': length, 'about': 'covered cable conduit along X, tiles at 4 m pitch'}


def vent(P, w=1.2, h=0.8, depth=0.18):
    P.loft([(rrect(w + 0.2, h + 0.2, 0.1, 2), 0.0), (rrect(w + 0.1, h + 0.1, 0.07, 2), depth), (rrect(w - 0.02, h - 0.02, 0.04, 2), depth), (rrect(w - 0.02, h - 0.02, 0.04, 2), 0.02)], bevel=0.01)
    P.box((w, h, 0.02), at=(0, 0, 0.02), mat='rubber', bevel=0.0)
    n = int(h / 0.08)
    for k in range(n):
        P.box((w - 0.04, 0.07, 0.012), at=(0, -h / 2 + 0.05 + k * 0.08, 0.1), rot=(-40, 0, 0), mat='paint2', bevel=0.0)
    P.box((0.03, h - 0.02, 0.1), at=(0, 0, 0.1), mat='paint', bevel=0.004)
    P.bolts([(x, y, depth) for x, y in [(sx * (w / 2 + 0.02), sy * (h / 2 + 0.02)) for sx in (-1, 1) for sy in (-1, 1)]], r=0.014, h=0.01, mat='steel')
    return {'about': 'louvred hull vent 1.2 x 0.8 m'}


def clamp(P):
    # docking / mooring clamp: base, pivoting arm with a claw, hydraulic ram, contact pads
    P.loft([(chamfer_rect(1.6, 1.2, 0.2), 0.0), (chamfer_rect(1.4, 1.0, 0.15), 0.4)], closed=False, bevel=0.02)
    P.bolts([(sx * 0.7, sy * 0.5, 0.05) for sx in (-1, 1) for sy in (-1, 0, 1)], r=0.025, h=0.02, mat='steel')
    for sx in (-1, 1):
        P.box((0.1, 0.5, 0.45), at=(sx * 0.3, 0.2, 0.62), bevel=0.015)
    P.cyl(0.1, 0.7, at=(0, 0.25, 0.75), rot=(0, 90, 0), n=14, mat='dark', bevel=0.01)
    with P.at(at=(0, 0.25, 0.75), rot=(35, 0, 0)):
        P.box((0.44, 0.24, 1.2), at=(0, 0, 0.55), bevel=0.02)
        P.box((0.44, 0.7, 0.2), at=(0, -0.28, 1.1), bevel=0.02)
        P.box((0.4, 0.1, 0.35), at=(0, -0.6, 0.95), bevel=0.015)
        P.box((0.36, 0.04, 0.26), at=(0, -0.66, 0.92), mat='rubber', bevel=0.0)
    # ram from the base to the arm
    P.cyl(0.08, 0.7, at=(0, -0.35, 0.72), rot=(-28, 0, 0), n=12, mat='paint2', bevel=0.01)
    P.cyl(0.04, 0.5, at=(0, -0.2, 1.05), rot=(-28, 0, 0), n=10, mat='steel', bevel=0.0)
    P.box((0.3, 0.3, 0.06), at=(0, -0.2, 0.43), mat='hazard', bevel=0.0)
    return {'about': 'docking clamp; arm swings about X at (0, 0.25, 0.75), claw faces -Y'}


def navlight(P, size=0.4):
    P.cyl(0.2, 0.05, at=(0, 0, 0.025), n=20, mat='dark', bevel=0.008)
    P.bolts([(0.16 * math.cos(a), 0.16 * math.sin(a), 0.05) for a in [k * math.pi / 2 + math.pi / 4 for k in range(4)]], r=0.012, h=0.008, mat='steel')
    P.cyl(0.11, 0.08, at=(0, 0, 0.09), n=20, mat='paint', bevel=0.008)
    P.lathe([(0.09, 0.0), (0.09, 0.06)] + [(0.09 * math.cos(t), 0.06 + 0.07 * math.sin(t)) for t in [k * math.pi / 8 for k in range(1, 4)]] + [(0.0, 0.13)], 20, at=(0, 0, 0.13), mat='lens', sharp=40)
    for a in (0, 90):
        P.tube([(-0.12, 0, 0.13), (-0.12, 0, 0.26), (0.12, 0, 0.26), (0.12, 0, 0.13)], 0.008, n=6, fillet=0.08, rot=(0, 0, a), mat='paint')
    P.cyl(0.13, 0.015, at=(0, 0, 0.135), n=20, mat='paint', bevel=0.0)
    return {'lens': [0, 0, 0.23], 'about': 'nav light housing, 0.4 m; the runtime light sprite goes at `lens`'}


PARTS = {
    'pipes': {'build': pipes, 'tex': 512, 'bake': {'ao': 0.12, 'curv': 0.01}},
    'conduit': {'build': conduit, 'tex': 512, 'bake': {'ao': 0.1, 'curv': 0.01}},
    'vent': {'build': vent, 'tex': 256, 'bake': {'ao': 0.08, 'curv': 0.008}},
    'clamp': {'build': clamp, 'tex': 512, 'bake': {'ao': 0.15, 'curv': 0.012}},
    'navlight': {'build': navlight, 'tex': 256, 'bake': {'ao': 0.05, 'curv': 0.006}},
}
