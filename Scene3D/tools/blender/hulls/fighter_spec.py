"""Writes tools/blender/specs/fighter-v3.json: the kit placements on the remodelled fighter hull.

    python3 tools/blender/hulls/fighter_spec.py

Mounting points come from fighter_dims.py (flank line, chamfer plane, bays, glazing recess back walls,
sponson faces), so re-run this after changing those.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fighter_dims as H  # noqa: E402


class V(tuple):
    """Tiny 3-vector (plain python3, no mathutils)."""
    def __new__(cls, v):
        return super().__new__(cls, [float(c) for c in v])

    def __add__(self, o): return V([a + b for a, b in zip(self, o)])
    def __sub__(self, o): return V([a - b for a, b in zip(self, o)])
    def __mul__(self, k): return V([a * k for a in self])

    def normalized(self):
        L = math.sqrt(sum(a * a for a in self)); return V([a / L for a in self])


r = lambda v, k=3: [round(float(c), k) for c in v]
fX = H.fX


def flank_n(z, side=1):
    return r(H.flank_n(z, side), 4)


P = []
B, SB = H.BELL, H.SBELL
# ---- drive: main bells in the stern sockets, small bells at the aft end of each sponson
P += [
    {"id": f"main bells: bell-L x{B['scale']:.4f} (r 3.55)", "part": "bell-L", "p": [B['x'], B['y'], B['exit']], "n": [0, 0, 1], "up": [0, 1, 0], "scale": round(B['scale'], 4), "snap": False, "mirrorX": True, "seat": {"check": False}},
    {"id": f"sponson bells: bell-S x{SB['scale']:.4f} (r 1.37)", "part": "bell-S", "p": [SB['x'], SB['y'], SB['exit']], "n": [0, 0, 1], "up": [0, 1, 0], "scale": round(SB['scale'], 4), "snap": False, "mirrorX": True, "seat": {"check": False}},
]
# ---- crew doors (2 x 1 m leaves) in their bays, a floodlight above each
for i, (z, y) in enumerate(H.DOORS):
    n = flank_n(z)
    # placed on the bay floor (0.32 m deep) without snapping: the ray from 8 m out would start inside
    # the sponson railgun barrels for the forward door
    P.append({"id": "crew doors in the flank bays (on the bay floor)" if i == 0 else None, "part": "door", "p": r([fX(z) - 0.32 * n[0], y, z - 0.32 * n[2]]), "n": n,
              "snap": False, "seat": {"check": False}, "mirrorX": True})
    P.append({"part": "floodlight", "p": r([fX(z), y + 2.05, z]), "n": n, "rot": 180, "mirrorX": True})
# ---- ports: a row along the forward flank just under the chamfer, a row on the aft chamfer
PS = 0.55
zs = [11.2 + 2.25 * k for k in range(9)]
for i, z in enumerate(zs):
    y = H.prof(z)['FT'] - 0.72
    P.append({"id": "flank ports (kit port x0.55), forward flank" if i == 0 else None, "part": "port", "p": r([fX(z), y, z]), "n": flank_n(z), "scale": PS, "mirrorX": True})
chn = [0.8, 0.6, 0.0]
P.append({"id": "flank ports, aft upper chamfer", "part": "port", "row": {"from": [12.33, 1.1, -17.4], "to": [12.33, 1.1, -1.4], "pitch": 2.0}, "n": chn, "scale": PS, "mirrorX": True})
# ---- bridge glazing: two rows of kit panes x0.7 on the front recess back wall, one row x0.58 on
# each side recess
c, fn, up = (V(t) for t in H.glazing_frame())
S1 = 0.7
pw, ph = 1.12 * S1, 1.32 * S1
for k, s in enumerate((-0.5, 0.5)):
    cc = c + up * (s * ph)
    a = cc + V((1, 0, 0)) * (-3 * pw); b = cc + V((1, 0, 0)) * (3 * pw)
    P.append({"id": "bridge glazing panes x0.7 (front recess, two rows)" if k == 0 else None, "part": "pane", "row": {"from": r(a), "to": r(b), "pitch": round(pw, 4)},
              "n": r(fn, 4), "up": r(up, 4), "scale": S1, "seat": {"check": False}})
S2 = 0.58
g = H.SIDE_GLAZE
wn = V(H.side_wall_n())
cc = V((H.side_wall_x(g['y']), g['y'], g['z'])) - wn * H.SIDE_DEPTH
pw2 = 1.12 * S2
P.append({"id": "bridge side panes x0.58", "part": "pane", "row": {"from": r(cc + V((0, 0, -2 * pw2))), "to": r(cc + V((0, 0, 2 * pw2))), "pitch": round(pw2, 4)},
          "n": r(wn, 4), "up": [0, 1, 0], "scale": S2, "mirrorX": True, "seat": {"check": False}})
# ---- RCS quads: modelled on the hull (fighter.py rcs_quads), not the kit block
# ---- nav light housings (module lights at the lens, 0.23 m out)
P += [
    {"id": "nav lights: sponson outboard sidelights", "part": "navlight", "p": [H.SP['x'] + H.SP['w'] / 2, H.SP['y'], -6.8], "n": [1, 0, 0], "mirrorX": True},
    {"part": "navlight", "p": [0, H.SPINE_Y, -16.7], "n": [0, 1, 0]},
    {"part": "navlight", "p": [0, -10.07, -1.0], "n": [0, -1, 0]},
    {"part": "navlight", "p": [0, 4.0, H.STERN_PLATE], "n": [0, 0, -1]},
]
# ---- antennas, domes
P += [
    {"id": "dorsal whip (sets the height, y 10.48)", "part": "antenna", "p": [0, H.SPINE_Y, -17.5], "n": [0, 1, 0], "up": [0, 0, 1], "scale": 0.585},
    {"id": "stern corner whips", "part": "antenna", "p": [7.1, H.DECK_AFT + 0.14, -24.1], "n": [0, 1, 0], "up": [0, 0, 1], "scale": 0.42, "mirrorX": True},
    {"id": "forward whips beside the bridge", "part": "antenna", "p": [5.2, 5.49, 5.5], "n": [0, 1, 0], "up": [0, 0, 1], "scale": 0.45, "mirrorX": True},
    {"id": "sensor domes on the aft deck", "part": "dome", "p": [6.8, H.DECK_AFT, -20.2], "n": [0, 1, 0], "up": [0, 0, 1], "scale": 0.72, "mirrorX": True},
]
P = [{k: v for k, v in q.items() if v is not None} for q in P]
spec = {
    "about": "Petrel-class fighter F-402, v3 REMODEL: the hull is clean hard-surface geometry built by tools/blender/hulls/fighter.py from measurements of the fal/Tripo H3.1 blueprint (ship frame, metres, bow +Z, dorsal +Y, port +X; not re-centred), textured by fighter_paint.py over paint.py; this spec places the Blender parts kit (assets/parts-blender, +Z mounts) on it. Bells are kit bells scaled to the blueprint radii; the module's engines use the kit's documented depth / throat / wall times the same scale.",
    "hull": {"glb": "HULL_GLB_FROM_COMMAND_LINE", "rotate": [0, 0, 0], "scale": 1.0, "centre": False},
    "partsDir": "../../../assets/parts-blender",
    "kits": {"fal": "../../../assets/parts"},
    "partDefaults": {
        "door": {"sink": 0.0}, "port": {"sink": 0.03, "normal": "hit"}, "pane": {"sink": 0.04},
        "rcs": {"sink": 0.04}, "floodlight": {"sink": 0.02}, "navlight": {"sink": 0.0},
        "antenna": {"sink": 0.05}, "dome": {"sink": 0.05}},
    "fixes": {"port": {"decimate": 0.3}, "pane": {"decimate": 0.4}, "door": {"decimate": 0.35},
              "rcs": {"decimate": 0.5}, "navlight": {"decimate": 0.35}, "floodlight": {"decimate": 0.3},
              "bell-L": {"decimate": 0.35}, "bell-S": {"decimate": 0.35}, "antenna": {"decimate": 0.45}, "dome": {"decimate": 0.6}},
    "seat": {"maxGap": 0.15, "maxBury": 0.4, "drop": True},
    "bake": {"ao": True, "res": 2048, "distance": 0.3, "samples": 16, "aa": 4, "strength": 0.6},
    "placements": P,
}
json.dump(spec, open(os.path.join(HERE, '..', 'specs', 'fighter-v3.json'), 'w'), indent=1)
print(len(P))
