"""Writes tools/blender/specs/carrier-v3.json: the kit placements on the remodelled carrier hull.

    python3 tools/blender/hulls/carrier_spec.py

Mounting points come from carrier_dims.py (the same numbers carrier.py builds with). Ship frame,
centred, metres. Human-scale kit (doors 1 x 2 m, airlocks, ladders, rails, nav lights) stays at
scale 1 on the 900 m hull; only the machinery scales: bells (bell-XL x2.61 / x2.70 to the
blueprint radii), the main guns (turret-L x2.6: 41 m base, 63 m twin barrels, well over the
destroyer's turret-M x1.15), the secondaries (turret-M x1.4), RCS quads x4, domes, arrays.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import carrier_dims as D  # noqa: E402

r = lambda v: [round(c, 3) for c in v]
S2 = math.sqrt(0.5)
NS = {'check': False}
P = []

# ---- drive: six bell-XL at the blueprint radii; the lip (kit z -0.084 x scale) on z -450
for i, ((x, y), rad) in enumerate(D.BELLS):
    s = round(rad / D.BELL_XL_R, 4)
    P.append({"id": f"bells {['upper', 'outboard', 'lower'][i]} pair: bell-XL x{s} (exit r {rad})", "part": "bell-XL",
              "p": [x, y, round(D.Z_EXIT + 0.084 * s, 3)], "n": [0, 0, 1], "up": [0, 1, 0], "scale": s, "snap": False, "mirrorX": True, "seat": NS})

# ---- main guns: turret-L x2.6 on the spine barbettes and the sponsons
for z, g in D.SPINE_TURRETS:
    y = (24.0 if (z < D.Z_SF or z > D.Z_BA) else D.Y_DECK) + 3.5
    P.append({"id": f"spine turret z {z}: turret-L x{D.TURRET_L} ({'guns forward' if g > 0 else 'guns aft'})", "part": "turret-L",
              "p": [0, y, z], "n": [0, 1, 0], "up": [0, 0, g], "scale": D.TURRET_L, "snap": False, "seat": NS})
S = D.SPONSON
P.append({"id": "sponson turrets: turret-L x2.6 (guns forward)", "part": "turret-L", "p": [168.0, S['yc'] + S['h'] / 2 + 2.0, S['zc']], "n": [0, 1, 0], "up": [0, 0, 1],
          "scale": D.TURRET_L, "snap": False, "mirrorX": True, "seat": NS})
for z, g in D.EDGE_TURRETS:
    y = (24.0 if (z < D.Z_SF or z > D.Z_BA) else D.Y_DECK) + 1.2
    P.append({"id": f"deck-edge secondaries z {z}: turret-M x{D.TURRET_M}", "part": "turret-M", "p": [D.X_EDGE_T, y, z], "n": [0, 1, 0], "up": [0, 0, g],
              "scale": D.TURRET_M, "snap": False, "mirrorX": True, "seat": NS})

# ---- point defence: deck edges (on the chamfer tops), island terraces, stern and bow blocks
pdc = []
for z in (-340.0, -230.0, 50.0, 150.0, 250.0, 370.0):
    y = 24.0 if (z < D.Z_SF or z > D.Z_BA) else D.Y_DECK
    pdc.append({"part": "pdc", "p": [60.0, y, z], "n": [0, 1, 0], "up": [0, 0, 1], "mirrorX": True, "scale": 1.6})
for nm, zc, w, l, c, y0, y1 in D.TIERS[:3]:
    pdc.append({"part": "pdc", "p": [w / 2 - c - 1.5, y1 + 0.4, zc - l / 2 + c + 2.0], "n": [0, 1, 0], "up": [0, 0, -1], "mirrorX": True, "scale": 1.6})
pdc[0]["id"] = "point-defence mounts x1.6: deck, island terraces"
P += pdc

# ---- VLS blocks on the bow deck and the stern deck
P += [
    {"id": "VLS blocks, bow deck", "part": "missilePod", "p": [40.0, 24.0, 300.0], "n": [0, 1, 0], "up": [0, 0, 1], "mirrorX": True, "rows": {"count": 2, "step": [0, 0, 7.0]}},
    {"id": "VLS blocks, stern deck", "part": "missilePod", "p": [40.0, 24.0, -345.0], "n": [0, 1, 0], "up": [0, 0, 1], "mirrorX": True, "rows": {"count": 2, "step": [0, 0, 7.0]}},
]

# ---- airlocks (with docking clamps) and crew doors on the flanks of the stern block and bow section
X = D.X_END
P += [
    {"id": "stern block airlocks (between the upper port rows)", "part": "airlock", "p": [X, -21.5, -348.0], "n": [1, 0, 0], "mirrorX": True},
    {"id": "bow section airlocks", "part": "airlock", "p": [X, -24.5, 297.0], "n": [1, 0, 0], "mirrorX": True},
    {"part": "airlock", "p": [X, -24.5, 399.0], "n": [1, 0, 0], "mirrorX": True},
    {"id": "docking clamps flanking the airlocks", "part": "clamp", "p": [X, -21.5, -351.0], "n": [1, 0, 0], "up": [0, 1, 0], "mirrorX": True, "scale": 1.2},
    {"part": "clamp", "p": [X, -21.5, -345.0], "n": [1, 0, 0], "up": [0, 1, 0], "mirrorX": True, "scale": 1.2},
    {"part": "clamp", "p": [X, -24.5, 294.0], "n": [1, 0, 0], "up": [0, 1, 0], "mirrorX": True, "scale": 1.2},
    {"part": "clamp", "p": [X, -24.5, 402.0], "n": [1, 0, 0], "up": [0, 1, 0], "mirrorX": True, "scale": 1.2},
    {"id": "crew doors under the airlocks (lower port-row gaps)", "part": "door", "p": [X, -84.0, -348.0], "n": [1, 0, 0], "mirrorX": True},
    {"part": "door", "p": [X, -84.0, -296.0], "n": [1, 0, 0], "mirrorX": True},
    {"part": "door", "p": [X, -80.0, 297.0], "n": [1, 0, 0], "mirrorX": True},
    {"part": "door", "p": [X, -80.0, 399.0], "n": [1, 0, 0], "mirrorX": True},
]
# ---- hangar crew doors at deck level: back wall, bow section inner walls, forward faces of the frames
P += [
    {"id": "hangar back wall crew doors", "part": "door", "p": [42.0, D.Y_AFT + 1.2, D.Z_BACK], "n": [0, 0, 1], "mirrorX": True},
    {"part": "door", "p": [72.0, D.Y_AFT + 1.2, D.Z_BACK], "n": [0, 0, 1], "mirrorX": True},
    {"id": "bow section inner-wall crew doors", "part": "door", "p": [D.W_IN, -58.8, 297.5], "n": [-1, 0, 0], "mirrorX": True},
    {"part": "door", "p": [D.W_IN, -58.8, 347.5], "n": [-1, 0, 0], "mirrorX": True},
    {"part": "door", "p": [D.W_IN, -58.8, 397.5], "n": [-1, 0, 0], "mirrorX": True},
]
for i, (z0, z1) in enumerate(D.FRAMES):
    deck_fwd = D.Y_LONG if i < 4 else D.Y_BAY1
    y = (D.SILL[i] if D.SILL[i] > deck_fwd else deck_fwd) + 1.2
    P.append({"part": "door", "p": [101.0, y, z1], "n": [0, 0, 1], "mirrorX": True, **({"id": "frame-post crew doors (forward faces)"} if i == 0 else {})})
# island: plinth doors onto the deck
P += [{"id": "island plinth doors onto the deck", "part": "door", "p": [D.PLINTH['w'] / 2, D.Y_DECK + 1.2, z], "n": [1, 0, 0], "mirrorX": True} for z in (-190.0, -40.0)]

# ---- ladders: bow section deck to the wall walkways (y -60), frame posts
P += [
    {"id": "ladders on the hangar back wall", "part": "ladder", "p": [35.0, D.Y_AFT + 1.5, D.Z_BACK], "n": [0, 0, 1], "rows": {"count": 8, "step": [0, 3.0, 0]}, "mirrorX": True},
]

# ---- rails on the bridge roof edge (kit rails, 3 m segments)
B = D.BRIDGE
P += [
    {"id": "bridge roof rails, forward edge", "part": "rail", "row": {"from": [-B['w'] / 2 + B['c'] + 1.0, B['y1'] + 0.4, B['zc'] + B['l'] / 2 - 1.2], "to": [B['w'] / 2 - B['c'] - 1.0, B['y1'] + 0.4, B['zc'] + B['l'] / 2 - 1.2], "pitch": 3.0},
     "n": [0, 1, 0], "snap": False, "seat": NS},
]

# ---- RCS quads x4 on the chamfers at the four corners of the bow section and the stern block
for z in (-364.0, 410.0):
    P.append({"part": "rcs", "p": [115.0, 8.0, z], "n": [S2, S2, 0], "mirrorX": True, "normal": "hit", "scale": 4.0})
    P.append({"part": "rcs", "p": [118.0, -107.0, z], "n": [S2, -S2, 0], "mirrorX": True, "normal": "hit", "scale": 4.0})
P[-4]["id"] = "rcs quads x4, bow and stern corners"

# ---- nav lights (module lights at the lens): sidelights, strobes, stern light
P += [
    {"id": "nav lights: sponson sidelights (red port, green starboard)", "part": "navlight", "p": [S['x1'], -55.0, S['zc']], "n": [1, 0, 0], "mirrorX": True},
    {"part": "navlight", "p": [4.0, D.TIERS[-1][6] + 0.4, D.TIERS[-1][1] + 6.0], "n": [0, 1, 0]},
    {"part": "navlight", "p": [8.0, -152.0, 182.0], "n": [0, -1, 0]},
    {"part": "navlight", "p": [0.0, 18.5, D.Z_STERN], "n": [0, 0, -1]},
]

# ---- floodlights: over the mouth (aimed in), on the island terraces (aimed at the deck)
P += [
    {"id": "floodlights over the mouth and on the island", "part": "floodlight", "p": [-60.0 + 30.0 * i, 3.0, D.Z_LIP], "n": [0, 0, 1], "rot": 180, "scale": 2.0} for i in range(5)
]
P += [{"part": "floodlight", "p": [D.PLINTH['w'] / 2 - 4.0, D.PLINTH['y1'], z], "n": [0, 1, 0], "up": [1, 0, 0], "mirrorX": True, "scale": 2.0} for z in (-200.0, -100.0, -20.0)]

# ---- antennas, domes, sensor arrays
t = {n: (zc, w, l, c, y0, y1) for n, zc, w, l, c, y0, y1 in D.TIERS}
P += [
    {"id": "island whips x2", "part": "antenna", "p": [4.5, t['t6'][5] + 0.4, t['t6'][0] - 5.0], "n": [0, 1, 0], "up": [0, 0, 1], "scale": 2.0, "mirrorX": True},
    {"part": "antenna", "p": [9.0, t['t5'][5] + 0.4, t['t5'][0] - 18.0], "n": [0, 1, 0], "up": [0, 0, 1], "scale": 2.0, "mirrorX": True},
    {"part": "antenna", "p": [14.0, t['t4'][5] + 0.4, t['t4'][0] - 34.0], "n": [0, 1, 0], "up": [0, 0, 1], "scale": 2.0, "mirrorX": True},
    {"id": "bow deck whips", "part": "antenna", "p": [80.0, 24.0, 405.0], "n": [0, 1, 0], "up": [0, 0, 1], "scale": 2.0, "mirrorX": True},
    {"id": "radomes (10-12.5 m) on the island and the stern block", "part": "dome", "p": [12.0, t['t4'][5] + 0.4, t['t4'][0] + 30.0], "n": [0, 1, 0], "up": [0, 0, 1], "scale": 4.0, "mirrorX": True},
    {"part": "dome", "p": [70.0, 24.0, -335.0], "n": [0, 1, 0], "up": [0, 0, 1], "scale": 5.0, "mirrorX": True},
    {"id": "sensor arrays x4 (16 m): bow deck, island T3 roof", "part": "fal:sensorArray", "p": [20.0, 24.0, 330.0], "n": [0, 1, 0], "up": [0, 0, 1], "scale": 4.0, "mirrorX": True},
    {"part": "fal:sensorArray", "p": [15.0, t['t3'][5] + 0.4, t['t3'][0] - 45.0], "n": [0, 1, 0], "up": [0, 0, -1], "scale": 3.0, "mirrorX": True},
]
P = [{k: v for k, v in q.items() if v is not None} for q in P]
spec = {
    "about": "Keystone-class fleet carrier CV-50, v3 REMODEL: the hull is clean hard-surface geometry built by tools/blender/hulls/carrier.py from measurements of the fal/Tripo H3.1 blueprint (ship frame, centred, metres, bow +Z, dorsal +Y, port +X; not re-centred), painted by tools/blender/hulls/carrier_paint.py; this spec places the Blender parts kit (assets/parts-blender, +Z mounts) and the fal kit's sensor array on it.",
    "hull": {"glb": "HULL_GLB_FROM_COMMAND_LINE", "rotate": [0, 0, 0], "scale": 1.0, "centre": False},
    "partsDir": "../../../assets/parts-blender",
    "kits": {"fal": "../../../assets/parts"},
    "partDefaults": {
        "door": {"sink": 0.0}, "airlock": {"sink": 0.0}, "rcs": {"sink": 0.1}, "floodlight": {"sink": 0.02}, "navlight": {"sink": 0.0}, "pdc": {"sink": 0.05},
        "clamp": {"sink": 0.02}, "missilePod": {"sink": 0.05},
        "rail": {"sink": 0.0, "xAlong": True, "scale": [3, 1, 1]}, "ladder": {"sink": 0.0, "lift": 0.03}, "antenna": {"sink": 0.05}, "dome": {"sink": 0.05},
        "fal:sensorArray": {"sink": 0.05}},
    "fixes": {"door": {"decimate": 0.2}, "airlock": {"decimate": 0.3}, "missilePod": {"decimate": 0.3}, "rail": {"decimate": 1.0}, "rcs": {"decimate": 0.3},
              "navlight": {"decimate": 0.35}, "floodlight": {"decimate": 0.3}, "ladder": {"decimate": 0.45}, "turret-L": {"decimate": 0.4},
              "turret-M": {"decimate": 0.25}, "bell-XL": {"decimate": 0.35}, "antenna": {"decimate": 0.45}, "dome": {"decimate": 0.6}, "pdc": {"decimate": 0.25},
              "clamp": {"decimate": 0.5}, "fal:sensorArray": {"decimate": 0.5}},
    "seat": {"maxGap": 0.2, "maxBury": 0.5, "drop": True},
    "bake": {"ao": True, "res": 2048, "distance": 2.0, "samples": 16, "aa": 4, "strength": 0.6},
    "placements": P,
}
json.dump(spec, open(os.path.join(HERE, '..', 'specs', 'carrier-v3.json'), 'w'), indent=1)
print(len(P))
