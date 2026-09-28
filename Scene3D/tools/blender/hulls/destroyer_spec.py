"""Writes tools/blender/specs/destroyer-v3.json: the kit placements on the remodelled destroyer hull.

    python3 tools/blender/hulls/destroyer_spec.py

The mounting points repeat the hull dimensions of destroyer.py (profiles, facets, bays, gun gap,
tower blocks), so re-run this after changing those. Frame: ship frame at the rendered size.
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
# ---- turrets (kit turret-M; guns along +Y = `up`)
P += [
    {"id": "bow dorsal turret: turret-M x1.15 on its barbette (guns forward)", "part": "turret-M", "p": [0, -5.9, 69.0], "n": [0, 1, 0], "up": [0, 0, 1], "scale": 1.15, "snap": False, "seat": {"check": False}},
    {"id": "bow ventral turret: turret-M x1.1 (guns forward)", "part": "turret-M", "p": [0, -30.9, 72.0], "n": [0, -1, 0], "up": [0, 0, 1], "scale": 1.1, "snap": False, "seat": {"check": False}},
    {"id": "aft dorsal turret: turret-M x1.15 (guns aft)", "part": "turret-M", "p": [0, -3.95, -72.5], "n": [0, 1, 0], "up": [0, 0, -1], "scale": 1.15, "snap": False, "seat": {"check": False}},
    {"id": "flank sponson guns: turret-M x0.8 on the sponson faces (guns forward)", "part": "turret-M", "p": [19.7, -20.2, 14.2], "n": [1, 0, 0], "up": [0, 0, 1], "scale": 0.8, "snap": False, "mirrorX": True, "seat": {"check": False}},
]
# ---- point defence (kit pdc, barrels toward `up`)
pdc = []
for t, z, up in ((0.2, -38.6, [0, 0, 1]), (0.2, -80.4, [0, 0, -1])):
    (x, y), n, _ = e_shoulder(t)
    pdc.append({"part": "pdc", "p": r([x, y, z]), "n": n, "up": up, "mirrorX": True})
(x, y), n, _ = m_shoulder(0.3)
pdc.append({"part": "pdc", "p": r([x, y, -11.5]), "n": n, "up": [0, 0, 1], "mirrorX": True})
(x, y), n, _ = b_shoulder(0.55)
pdc.append({"part": "pdc", "p": r([x, y, 79.0]), "n": n, "up": [0, 0, 1], "mirrorX": True})
(x, y), n, _ = e_lower(0.62)
pdc.append({"part": "pdc", "p": r([x, y, -40.2]), "n": n, "up": [0, 0, 1], "mirrorX": True})
pdc.append({"part": "pdc", "p": [7.0, -30.4, 60.0], "n": [0, -1, 0], "up": [0, 0, 1], "mirrorX": True})
pdc.append({"part": "pdc", "p": [7.4, 26.0, -35.6], "n": [0, 1, 0], "up": [0, 0, 1], "mirrorX": True})
pdc[0]["id"] = "point-defence mounts: engine shoulders, mid and bow shoulders, keel, tower roof"
P += pdc
# ---- VLS blocks (kit missilePod, 2 x 4 cells) on the engine deck and the bow deck
P += [
    {"id": "VLS blocks, engine deck", "part": "missilePod", "p": [10.6, -4.3, -65.8], "n": [0, 1, 0], "up": [0, 0, 1], "mirrorX": True},
    {"part": "missilePod", "p": [10.6, -4.3, -79.0], "n": [0, 1, 0], "up": [0, 0, 1], "mirrorX": True},
    {"id": "VLS blocks, bow deck", "part": "missilePod", "p": [7.6, -6.4, 78.5], "n": [0, 1, 0], "up": [0, 0, 1], "mirrorX": True},
]
# ---- doors: personnel door in the boat hatch's aft leaf, gun-gap faces, deckhouse, tower base
lw = (BOAT['w'] - 1.2) / 2 - 0.06
P += [
    {"id": "boat hatch personnel door (1 x 2 m) in the aft leaf", "part": "door", "p": [17.14, round(BOAT['y'] - (BOAT['h'] - 1.32) / 2 + 1.35, 3), round(BOAT['z'] - (lw / 2 + 0.03), 3)], "n": [1, 0, 0], "snap": False, "mirrorX": True, "seat": {"check": False}},
    {"id": "gun-gap doors, mid-hull front face", "part": "door", "p": [7.0, WALK_Y + 1.22, GAP[0]], "n": [0, 0, 1], "mirrorX": True},
    {"id": "gun-gap doors, bow block rear face", "part": "door", "p": [7.0, WALK_Y + 1.22, GAP[1]], "n": [0, 0, -1], "mirrorX": True},
    {"id": "deckhouse side doors", "part": "door", "p": [9.5, -7.08, -21.95], "n": [1, 0, 0], "mirrorX": True},
    {"id": "tower base aft doors", "part": "door", "p": [4.0, -3.08, -61.5], "n": [0, 0, -1], "mirrorX": True},
]
# ---- ladders
P += [
    {"id": "gun-gap ladders, walkway to the upper rail level", "part": "ladder", "p": [9.95, WALK_Y + 1.5, GAP[0]], "n": [0, 0, 1], "rows": {"count": 4, "step": [0, 3.0, 0]}, "mirrorX": True},
    {"id": "spine ladders", "part": "ladder", "p": [4.4, -7.75, 25.0], "n": [1, 0, 0], "mirrorX": True, "seat": {"check": False}},
    {"id": "tower base ladders", "part": "ladder", "p": [12.0, -2.75, -56.0], "n": [1, 0, 0], "mirrorX": True},
]
# ---- rails (3 m kit segments)
P += [
    {"id": "gun-gap walkway rails", "part": "rail", "row": {"from": [11.0, WALK_Y, 44.9], "to": [11.0, WALK_Y, 53.0], "pitch": 3.0}, "n": [0, 1, 0], "mirrorX": True, "snap": False, "seat": {"check": False}},
    {"id": "spine catwalk rails", "part": "rail", "row": {"from": [4.1, -5.5, 21.5], "to": [4.1, -5.5, 59.0], "pitch": 3.0}, "n": [0, 1, 0], "mirrorX": True, "snap": False, "seat": {"check": False}},
]
for yb in (10.6, 16.6):
    P.append({"id": f"balcony rails y {yb}, outer edge", "part": "rail", "row": {"from": [11.0, yb, -50.6], "to": [11.0, yb, -61.4], "pitch": 3.0}, "n": [0, 1, 0], "mirrorX": True, "snap": False, "seat": {"check": False}})
    P.append({"part": "rail", "p": [9.3, yb, -62.1], "n": [0, 1, 0], "along": [1, 0, 0], "mirrorX": True, "snap": False, "seat": {"check": False}})
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
    {"part": "navlight", "p": [0, 26.0, -34.3], "n": [0, 1, 0]},
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
    {"id": "bow block whip", "part": "antenna", "p": [6.2, -6.4, 59.5], "n": [0, 1, 0], "up": [0, 0, 1]},
    {"id": "deckhouse whip", "part": "antenna", "p": [6.0, 2.2, -16.5], "n": [0, 1, 0], "up": [0, 0, 1]},
    {"id": "masthead: antenna x1.15 on the mast pylon (envelope top y 36.9)", "part": "antenna", "p": [0, 30.0, -60.3], "n": [0, 1, 0], "up": [0, 0, 1], "scale": 1.15, "snap": False, "seat": {"check": False}},
    {"id": "radome x2.3 on its plinth", "part": "dome", "p": [0, 29.6, -54.0], "n": [0, 1, 0], "up": [0, 0, 1], "scale": 2.3, "snap": False, "seat": {"check": False}},
]
P = [{k: v for k, v in q.items() if v is not None} for q in P]
spec = {
    "about": "Bastion-class destroyer DD-12, v3 REMODEL: the hull is clean hard-surface geometry built by tools/blender/hulls/destroyer.py from measurements of the fal/Tripo H3.1 blueprint (ship frame at the rendered size, metres, bow +Z, dorsal +Y, port +X; not re-centred), painted by tools/blender/hulls/destroyer_paint.py; this spec places the Blender parts kit (assets/parts-blender, +Z mounts) on it. Bells are kit bells scaled to the blueprint radii; the module's engines use the kit's documented depth / throat / wall times the same scale.",
    "hull": {"glb": "HULL_GLB_FROM_COMMAND_LINE", "rotate": [0, 0, 0], "scale": 1.0, "centre": False},
    "partsDir": "../../../assets/parts-blender",
    "partDefaults": {
        "door": {"sink": 0.0}, "rcs": {"sink": 0.04}, "floodlight": {"sink": 0.02}, "navlight": {"sink": 0.0}, "pdc": {"sink": 0.05},
        "rail": {"sink": 0.0, "xAlong": True, "scale": [3, 1, 1]}, "ladder": {"sink": 0.0, "lift": 0.03}, "antenna": {"sink": 0.05}, "dome": {"sink": 0.05}},
    "fixes": {"door": {"decimate": 0.3}, "missilePod": {"decimate": 0.3}, "rail": {"decimate": 1.0}, "rcs": {"decimate": 0.3}, "navlight": {"decimate": 0.35}, "floodlight": {"decimate": 0.3},
              "ladder": {"decimate": 0.45}, "turret-M": {"decimate": 0.35}, "bell-L": {"decimate": 0.22}, "bell-XL": {"decimate": 0.3}, "antenna": {"decimate": 0.45},
              "dome": {"decimate": 0.6}, "pdc": {"decimate": 0.35}},
    "seat": {"maxGap": 0.15, "maxBury": 0.4, "drop": True},
    "bake": {"ao": True, "res": 2048, "distance": 0.5, "samples": 16, "aa": 4, "strength": 0.6},
    "placements": P,
}
json.dump(spec, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'specs', 'destroyer-v3.json'), 'w'), indent=1)
print(len(P))
