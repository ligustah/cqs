"""Writes tools/blender/specs/destroyer-v3.json: the kit placements on the remodelled destroyer hull.

    python3 tools/blender/hulls/destroyer_spec.py

The mounting points repeat the hull dimensions of destroyer.py (profiles, facets, bays, gun gap,
command block, barbettes, VLS coamings), so re-run this after changing those. Frame: ship frame at the rendered size.
"""
import json
import math
import os

r = lambda v: [round(c, 3) for c in v]


def unit(v):
    L = math.sqrt(sum(c * c for c in v))
    return [round(c / L, 4) for c in v]


# hull facets (destroyer.py E_HALF / M_HALF / B_HALF)
def e_shoulder(t):  # engine shoulder (15, -4.3) -> (27.67, -15)
    return (15.0 + 12.67 * t, -4.3 - 10.7 * t), unit((10.7, 12.67, 0)), unit((-12.67, 10.7, 0))


def e_lower(t):     # engine lower chamfer (27.67, -25.4) -> (14.9, -35.8)
    return (27.67 - 12.77 * t, -25.4 - 10.4 * t), unit((10.4, -12.77, 0)), unit((12.77, 10.4, 0))


def m_shoulder(t):  # mid shoulder (12.5, -8.3) -> (17.5, -15.3)
    return (12.5 + 5.0 * t, -8.3 - 7.0 * t), unit((7.0, 5.0, 0)), unit((-5.0, 7.0, 0))


def b_shoulder(t):  # bow shoulder (11.2, -6.4) -> (17.1, -13.6)
    return (11.2 + 5.9 * t, -6.4 - 7.2 * t), unit((7.2, 5.9, 0)), unit((-5.9, 7.2, 0))


def b_lower(t):     # bow lower chamfer (17.1, -22.7) -> (11.2, -30.4)
    return (17.1 - 5.9 * t, -22.7 - 7.7 * t), unit((7.7, -5.9, 0)), unit((5.9, 7.7, 0))


# v8 weapon stations (destroyer.py TUR_*, SHOULDER_TUR, VLS, CB_*, MAST)
TUR_A, TUR_B, TUR_X, TUR_Y = 79.2, 66.5, -66.3, -78.8
BARBETTE_H = 3.0
DECK_E, DECK_B, BELLY_E, BELLY_B = -4.3, -6.4, -35.8, -30.4
SHOULDER_TUR = (21.5, -5.0, -57.5)
VLS_PITCH = (3.3, 5.7)
M_DECK_N = unit((0.0, 22.5, 3.19))
M_DECK_U = unit((0.0, -3.19, 22.5))
VLS = [
    ('bow', (8.0, DECK_B, 70.8), [0, 1, 0], [0, 0, 1], 1, 4),
    ('mid', (7.4, -9.718, 31.0), M_DECK_N, M_DECK_U, 1, 3),
    ('aft', (10.4, DECK_E, -72.5), [0, 1, 0], [0, 0, 1], 2, 3),
]
CB_Z, CASE_TOP = -45.0, 5.6
MAST_Z, DIR_W, DIR_H, POLE_TOP = -51.5, 5.2, 3.0, 23.5
SPINE_BANDS = [-1.2, 6.3, 13.6, 21.2, 29.9, 38.6, 47.3, 56.0]


BORE_Y = -18.55
GAP = (42.9, 54.9)
WALK_Y = -26.3
BOAT = dict(z=-19.0, y=-19.9, w=7.2, h=8.2)
P = []
# ---- drive: corner bells (bell-L x1.237 = r 4.33, the blueprint's inner-wall fit) and the centre
# dish (bell-XL x1.106 = r 7.74), exit-plane centres; corner exits at the envelope (z -101.32)
P += [
    {"id": "corner bells, upper pair: bell-L x1.237 (r 4.33)", "part": "bell-L", "p": [13.45, -13.71, -101.32], "n": [0, 0, 1], "up": [0, 1, 0], "scale": 1.237, "snap": False, "mirrorX": True, "seat": {"check": False}},
    {"id": "corner bells, lower pair: bell-L x1.237 (r 4.33)", "part": "bell-L", "p": [13.45, -25.45, -101.32], "n": [0, 0, 1], "up": [0, 1, 0], "scale": 1.237, "snap": False, "mirrorX": True, "seat": {"check": False}},
    {"id": "centre dish: bell-XL x1.106 (r 7.74), lip 10.7 m forward of the corner lips", "part": "bell-XL", "p": [0, -19.94, -90.6], "n": [0, 0, 1], "up": [0, 1, 0], "scale": 1.106, "snap": False, "seat": {"check": False}},
]
# ---- turrets (kit turret-M; guns along +Y = `up`): 12 in naval batteries
TM = 1.15   # main batteries (the carrier's turret-L x2.6 stay far bigger)
tur = lambda id_, p, n, up, sc, **kw: {"id": id_, "part": "turret-M", "p": r(p), "n": n, "up": up, "scale": sc, "snap": False, "seat": {"check": False}, **kw}
P += [
    tur(f"bow battery A: turret-M x{TM} on its ring (guns forward)", [0, DECK_B + 0.35, TUR_A], [0, 1, 0], [0, 0, 1], TM),
    tur(f"bow battery B: turret-M x{TM} superfiring on a 3 m barbette (guns forward)", [0, DECK_B + BARBETTE_H, TUR_B], [0, 1, 0], [0, 0, 1], TM),
    tur(f"bow ventral A': turret-M x{TM} (guns forward)", [0, BELLY_B - 0.35, TUR_A], [0, -1, 0], [0, 0, 1], TM),
    tur(f"bow ventral B': turret-M x{TM} superfiring on a 3 m barbette", [0, BELLY_B - BARBETTE_H, TUR_B], [0, -1, 0], [0, 0, 1], TM),
    tur(f"aft battery X: turret-M x{TM} superfiring on a 3 m barbette (guns aft)", [0, DECK_E + BARBETTE_H, TUR_X], [0, 1, 0], [0, 0, -1], TM),
    tur(f"aft battery Y: turret-M x{TM} on its ring (guns aft)", [0, DECK_E + 0.35, TUR_Y], [0, 1, 0], [0, 0, -1], TM),
    tur(f"aft ventral X': turret-M x{TM} superfiring on a 3 m barbette (guns aft)", [0, BELLY_E - BARBETTE_H, TUR_X], [0, -1, 0], [0, 0, -1], TM),
    tur(f"aft ventral Y': turret-M x{TM} (guns aft)", [0, BELLY_E - 0.35, TUR_Y], [0, -1, 0], [0, 0, -1], TM),
    tur("shoulder drums: turret-M x1.0 (guns forward)", list(SHOULDER_TUR), [0, 1, 0], [0, 0, 1], 1.0, mirrorX=True),
    tur("flank sponson guns: turret-M x1.0 on the sponson faces (guns forward)", [20.3, -20.2, 14.2], [1, 0, 0], [0, 0, 1], 1.0, mirrorX=True),
]
# ---- VLS (kit missilePod, 2 x 4 cells, 3.19 x 5.59 m) set flush in the armoured coamings: 26 blocks, 208 cells
for name, c, n, up, cols, rows in VLS:
    rr, uu = [1, 0, 0], up
    for k in range(cols):
        dx = (k - (cols - 1) / 2) * VLS_PITCH[0]
        p0 = [c[0] + dx - uu[0] * 0, c[1], c[2]]
        # first row centre: back along up by (rows - 1) / 2 pitches
        off = (rows - 1) / 2 * VLS_PITCH[1]
        p0 = [p0[0] - uu[0] * off, p0[1] - uu[1] * off, p0[2] - uu[2] * off]
        P.append({"id": f"VLS {name} deck, column {k + 1}" if k == 0 else None, "part": "missilePod", "p": r(p0), "n": n, "up": uu,
                  "rows": {"count": rows, "step": r([uu[0] * VLS_PITCH[1], uu[1] * VLS_PITCH[1], uu[2] * VLS_PITCH[1]])}, "mirrorX": True})
# ---- point defence (kit pdc, barrels toward `up`): clusters at bow, shoulders, stern, command block
pdc = []
def pd(fn, t, zs, up, **kw):
    (x, y), n, _ = fn(t)
    for z in zs:
        pdc.append({"part": "pdc", "p": r([x, y, z]), "n": n, "up": up, "mirrorX": True, **kw})
pd(b_shoulder, 0.55, (75.8, 80.6), [0, 0, 1])             # bow shoulders
pd(b_lower, 0.45, (76.0,), [0, 0, 1])                     # bow lower chamfer
pd(m_shoulder, 0.3, (-9.3, -13.7), [0, 0, 1])             # mid shoulders
pd(e_shoulder, 0.15, (-36.6, -39.6), [0, 0, 1])           # engine shoulders, forward
pd(e_shoulder, 0.2, (-77.2, -79.8), [0, 0, -1])           # engine shoulders, stern
pd(e_lower, 0.62, (-40.2,), [0, 0, 1])                    # engine lower chamfer, forward
pd(e_lower, 0.40, (-80.2,), [0, 0, -1])                   # engine lower chamfer, stern
pdc.append({"part": "pdc", "p": [7.0, BELLY_B, 60.0], "n": [0, -1, 0], "up": [0, 0, 1], "mirrorX": True})
for z, up in ((CB_Z + 3.5, [0, 0, 1]), (CB_Z - 3.0, [0, 0, -1])):   # command block roof, either side of radome and director
    pdc.append({"part": "pdc", "p": [5.2, CASE_TOP, z], "n": [0, 1, 0], "up": up, "mirrorX": True})
pdc[0]["id"] = "point-defence clusters: bow shoulders and chamfers, mid and engine shoulders, stern corners, keel, command block roof"
P += pdc
# ---- fire-control arrays (fal kit sensorArray x0.7: 2.8 x 2.26 m) on the four faces of the director
fy = CASE_TOP + DIR_H / 2 - 0.15
P += [
    {"id": "fire-control arrays x0.7 on the director faces", "part": "fal:sensorArray", "p": [DIR_W / 2, fy, MAST_Z], "n": [1, 0, 0], "up": [0, 1, 0], "scale": 0.7, "mirrorX": True},
    {"part": "fal:sensorArray", "p": [0, fy, MAST_Z + DIR_W / 2], "n": [0, 0, 1], "up": [0, 1, 0], "scale": 0.7},
    {"part": "fal:sensorArray", "p": [0, fy, MAST_Z - DIR_W / 2], "n": [0, 0, -1], "up": [0, 1, 0], "scale": 0.7},
]
# ---- doors: personnel door in the boat hatch's aft leaf, gun-gap faces, deckhouse, tower base
lw = (BOAT['w'] - 1.2) / 2 - 0.06
P += [
    {"id": "boat hatch personnel door (1 x 2 m) in the aft leaf", "part": "door", "p": [17.14, round(BOAT['y'] - (BOAT['h'] - 1.32) / 2 + 1.35, 3), round(BOAT['z'] - (lw / 2 + 0.03), 3)], "n": [1, 0, 0], "snap": False, "mirrorX": True, "seat": {"check": False}},
    {"id": "gun-gap doors, mid-hull front face", "part": "door", "p": [7.0, WALK_Y + 1.22, GAP[0]], "n": [0, 0, 1], "mirrorX": True},
    {"id": "gun-gap doors, bow block rear face", "part": "door", "p": [7.0, WALK_Y + 1.22, GAP[1]], "n": [0, 0, -1], "mirrorX": True},
    {"id": "deckhouse side doors", "part": "door", "p": [9.5, -7.08, -21.95], "n": [1, 0, 0], "mirrorX": True},
    {"id": "command block aft doors (not snapped: the X barbette stands behind them)", "part": "door", "p": [4.0, -3.08, round(CB_Z - 14.2, 3)], "n": [0, 0, -1], "mirrorX": True, "snap": False, "seat": {"check": False}},
    {"id": "command block side doors", "part": "door", "p": [11.5, -3.08, -35.6], "n": [1, 0, 0], "mirrorX": True},
]
# ---- ladders
P += [
    {"id": "gun-gap ladders, walkway to the upper rail level", "part": "ladder", "p": [9.95, WALK_Y + 1.5, GAP[0]], "n": [0, 0, 1], "rows": {"count": 4, "step": [0, 3.0, 0]}, "mirrorX": True},
    {"id": "spine ladders", "part": "ladder", "p": [4.4, -7.75, 25.0], "n": [1, 0, 0], "mirrorX": True, "seat": {"check": False}},
    {"id": "command block ladders, deck to the base roof walk", "part": "ladder", "p": [11.5, -2.75, -54.0], "n": [1, 0, 0], "mirrorX": True},
]
# ---- rails (3 m kit segments)
P += [
    {"id": "gun-gap walkway rails", "part": "rail", "row": {"from": [11.0, WALK_Y, 44.9], "to": [11.0, WALK_Y, 53.0], "pitch": 3.0}, "n": [0, 1, 0], "mirrorX": True, "snap": False, "seat": {"check": False}},
    {"id": "command block roof-walk rails (base roof, outboard edge)", "part": "rail", "row": {"from": [10.85, -0.4, -54.5], "to": [10.85, -0.4, -36.5], "pitch": 3.0}, "n": [0, 1, 0], "mirrorX": True, "snap": False, "seat": {"check": False}},
]
for z0, z1 in zip(SPINE_BANDS[3:-1], SPINE_BANDS[4:]):   # spine catwalk rails between the clamp bands
    P.append({"id": "spine catwalk rails (between the clamp bands)" if z0 == SPINE_BANDS[3] else None, "part": "rail", "row": {"from": [4.1, -5.5, z0 + 2.3], "to": [4.1, -5.5, z1 - 2.3], "pitch": 3.0}, "n": [0, 1, 0], "mirrorX": True, "snap": False, "seat": {"check": False}})
# ---- RCS quads: bow flanks and engine-block shoulders / lower chamfers
ntap = unit((1, 0, (17.1 - 10.7) / (100.6 - 84.0)))
for y in (-15.6, -21.0):
    P.append({"part": "rcs", "p": [round(17.1 - 6.4 * 4.0 / 16.6, 3), y, 88.0], "n": ntap, "mirrorX": True, "normal": "hit", "id": "rcs, bow nose flank" if y == -15.6 else None})
for fn in (e_shoulder, e_lower):
    (x, y), n, _ = fn(0.86)
    P.append({"part": "rcs", "p": r([x, y, -81.0]), "n": n, "mirrorX": True, "normal": "hit"})
# ---- nav lights (module lights at the lens): sidelights, strobes, stern light
P += [
    {"id": "nav lights: engine-block flank sidelights (red port, green starboard)", "part": "navlight", "p": [27.67, -19.7, -50.0], "n": [1, 0, 0], "mirrorX": True},
    {"part": "navlight", "p": [0, round(CASE_TOP + DIR_H, 3), round(MAST_Z + 1.6, 3)], "n": [0, 1, 0]},
    {"part": "navlight", "p": [0, -36.9, -50.0], "n": [0, -1, 0], "sink": 0.1},
    {"part": "navlight", "p": [0, -7.8, -85.0], "n": [0, 0, -1]},
]
# ---- floodlights over the boat hatch and the gap doors
P += [
    {"id": "floodlights", "part": "floodlight", "p": [17.5, -15.45, -19.0], "n": [1, 0, 0], "rot": 180, "mirrorX": True},
    {"part": "floodlight", "p": [7.0, -23.35, GAP[0]], "n": [0, 0, 1], "rot": 180, "mirrorX": True},
    {"part": "floodlight", "p": [7.0, -23.35, GAP[1]], "n": [0, 0, -1], "rot": 180, "mirrorX": True},
]
# ---- antennas, mast, dome
P += [
    {"id": "deckhouse whip", "part": "antenna", "p": [6.0, 2.2, -16.5], "n": [0, 1, 0], "up": [0, 0, 1]},
    {"id": "masthead: antenna x1.0 on the sensor pole (the envelope top, ~y 29.5)", "part": "antenna", "p": [0, POLE_TOP, MAST_Z], "n": [0, 1, 0], "up": [0, 0, 1], "scale": 1.0, "snap": False, "seat": {"check": False}},
    {"id": "radome x1.8 on its drum (command block roof, forward)", "part": "dome", "p": [0, CASE_TOP + 1.2, CB_Z + 5.5], "n": [0, 1, 0], "up": [0, 0, 1], "scale": 1.8, "snap": False, "seat": {"check": False}},
]
P = [{k: v for k, v in q.items() if v is not None} for q in P]
spec = {
    "about": "Bastion-class destroyer DD-12, v3 REMODEL: the hull is clean hard-surface geometry built by tools/blender/hulls/destroyer.py from measurements of the fal/Tripo H3.1 blueprint (ship frame at the rendered size, metres, bow +Z, dorsal +Y, port +X; not re-centred), painted by tools/blender/hulls/destroyer_paint.py; this spec places the Blender parts kit (assets/parts-blender, +Z mounts) on it. Bells are kit bells scaled to the blueprint radii; the module's engines use the kit's documented depth / throat / wall times the same scale.",
    "hull": {"glb": "HULL_GLB_FROM_COMMAND_LINE", "rotate": [0, 0, 0], "scale": 1.0, "centre": False},
    "partsDir": "../../../assets/parts-blender",
    "kits": {"fal": "../../../assets/parts"},
    "partDefaults": {
        "door": {"sink": 0.0}, "rcs": {"sink": 0.04}, "floodlight": {"sink": 0.02}, "navlight": {"sink": 0.0}, "pdc": {"sink": 0.05},
        "rail": {"sink": 0.0, "xAlong": True, "scale": [3, 1, 1]}, "ladder": {"sink": 0.0, "lift": 0.03}, "antenna": {"sink": 0.05}, "dome": {"sink": 0.05}, "missilePod": {"sink": 0.0}, "fal:sensorArray": {"sink": 0.05}},
    "fixes": {"door": {"decimate": 0.3}, "missilePod": {"decimate": 0.18}, "rail": {"decimate": 0.5}, "fal:sensorArray": {"decimate": 0.3}, "rcs": {"decimate": 0.3}, "navlight": {"decimate": 0.35}, "floodlight": {"decimate": 0.3},
              "ladder": {"decimate": 0.45}, "turret-M": {"decimate": 0.26}, "bell-L": {"decimate": 0.22}, "bell-XL": {"decimate": 0.3}, "antenna": {"decimate": 0.45},
              "dome": {"decimate": 0.6}, "pdc": {"decimate": 0.25}},
    "seat": {"maxGap": 0.15, "maxBury": 0.4, "drop": True},
    "bake": {"ao": True, "res": 2048, "distance": 0.5, "samples": 16, "aa": 4, "strength": 0.6},
    "placements": P,
}
json.dump(spec, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'specs', 'destroyer-v3.json'), 'w'), indent=1)
print(len(P))
