"""Writes tools/blender/specs/vehicle-v3.json: the kit placements on the V-31 body (vehicle.py).

    python3 tools/blender/hulls/vehicle_spec.py

Mounting points come from vehicle_dims.py (axles, wheelhouse wall, flank, roof, tail face, collar), so re-run
this after changing those. Every part is the kit's at true size (scale 1): the ground parts (wheel, suspension,
rws, roofHatch, vehicleDoor, markerLamp, foilBox, parts_ground.py) and the fleet's louvred vent.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import vehicle_dims as D  # noqa: E402

r = lambda v, k=3: [round(float(c), k) for c in v]
NOSEAT = {"check": False}
P = []
W = D.WHEEL
# ---- running gear: four wheels (kit wheel, origin = inner face) and four double-wishbone corners
for i, za in enumerate(D.AXLES):
    P.append({"id": "road wheels (kit wheel 1.15 m, inner face at x +-0.88)" if i == 0 else None, "part": "wheel",
              "p": r([W['x_in'], W['y'], za]), "n": [1, 0, 0], "up": [0, 1, 0], "snap": False, "mirrorX": True, "seat": NOSEAT})
    P.append({"id": "suspension corners on the wheelhouse wall" if i == 0 else None, "part": "suspension",
              "p": r([D.WELL_X, W['y'], za]), "n": [1, 0, 0], "up": [0, 1, 0], "snap": False, "mirrorX": True, "seat": NOSEAT})
# ---- doors: cab door and rear-flank door on each flank, tail door
for i, z in enumerate(D.DOORS):
    P.append({"id": "flank doors (kit vehicleDoor 0.9 x 1.3 m), cab and rear-flank" if i == 0 else None, "part": "vehicleDoor",
              "p": r([D.ST[2][1]['W'], D.DOOR_Y, z]), "n": [1, 0, 0], "up": [0, 1, 0], "snap": False, "mirrorX": True, "seat": NOSEAT})
P.append({"id": "tail door", "part": "vehicleDoor", "p": r([0, D.TAIL_DOOR['y'] + 0.05, D.Z_TAIL]), "n": [0, 0, -1], "up": [0, 1, 0], "snap": False, "seat": NOSEAT})
# ---- roof: two round hatches, the remote weapon station behind them, the engine-deck vent, the foil box
for i, (x, z) in enumerate(D.HATCHES):
    P.append({"id": "roof hatches (kit roofHatch 0.8 m)" if i == 0 else None, "part": "roofHatch", "p": [x, D.ROOF, z], "n": [0, 1, 0], "up": [0, 0, 1], "snap": False, "seat": NOSEAT})
P.append({"id": "remote weapon station (kit rws), gun forward", "part": "rws", "p": [D.RWS[0], D.ROOF, D.RWS[1]], "n": [0, 1, 0], "up": [0, 0, 1], "snap": False, "seat": NOSEAT})
P.append({"id": "engine-deck grille (kit vent, long axis across)", "part": "vent", "p": [D.ROOF_VENT[0], D.ROOF, D.ROOF_VENT[1]], "n": [0, 1, 0], "up": [0, 0, 1], "snap": False, "seat": NOSEAT})
P.append({"id": "foil-wrapped sensor box (kit foilBox)", "part": "foilBox", "p": [D.FOIL_BOX[0], D.ROOF, D.FOIL_BOX[1]], "n": [0, 1, 0], "up": [0, 0, 1], "snap": False, "seat": NOSEAT})
# ---- covered lamps (kit markerLamp): upright on the collar cheeks, amber side markers, red tail lamps, convoy lamp
C = D.COLLAR
P.append({"id": "front covered lamps, upright on the collar cheeks", "part": "markerLamp", "p": [round((C['w'] + C['wi']) / 4, 3), C['y'], C['z1']], "n": [0, 0, 1], "up": [0, 1, 0], "rot": 90, "snap": False, "mirrorX": True, "seat": NOSEAT})
P.append({"id": "amber side markers on the bonnet flank", "part": "markerLamp", "p": list(D.MARKERS['side'][0]), "n": [1, 0, 0], "up": [0, 1, 0], "snap": True, "normal": "hit", "mirrorX": True})
P.append({"id": "tail lamps beside the tail door", "part": "markerLamp", "p": [0.77, 2.02, D.Z_TAIL], "n": [0, 0, -1], "up": [0, 1, 0], "snap": True, "mirrorX": True})
P.append({"id": "covered convoy lamp over the tail door", "part": "markerLamp", "p": [0, 2.34, D.Z_TAIL], "n": [0, 0, -1], "up": [0, 1, 0], "snap": True})
P = [{k: v for k, v in q.items() if v is not None} for q in P]
spec = {
    "about": "V-31 wheeled 4x4 (ground unit), v3 REMODEL: the body is clean hard-surface geometry built by tools/blender/hulls/vehicle.py to the brief's true size (vehicle frame = ship frame, metres, front +Z, up +Y, left +X; ground at y = 0, not re-centred), textured by vehicle_paint.py over paint.py; this spec places the procedural kit (assets/parts-blender, +Z mounts) on it at scale 1.",
    "hull": {"glb": "HULL_GLB_FROM_COMMAND_LINE", "rotate": [0, 0, 0], "scale": 1.0, "centre": False},
    "partsDir": "../../../assets/parts-blender",
    "kits": {"fal": "../../../assets/parts"},
    "partDefaults": {"vehicleDoor": {"sink": 0.0}, "roofHatch": {"sink": 0.01}, "rws": {"sink": 0.0}, "vent": {"sink": 0.02},
                     "foilBox": {"sink": 0.0}, "markerLamp": {"sink": 0.0}, "wheel": {"sink": 0.0}, "suspension": {"sink": 0.0}},
    "fixes": {"wheel": {"decimate": 0.6}, "suspension": {"decimate": 0.7}, "rws": {"decimate": 0.7}, "roofHatch": {"decimate": 0.6},
              "vehicleDoor": {"decimate": 0.6}, "markerLamp": {"decimate": 0.8}, "foilBox": {"decimate": 0.8}, "vent": {"decimate": 0.7}},
    "seat": {"maxGap": 0.08, "maxBury": 0.2, "drop": True},
    "bake": {"ao": True, "res": 2048, "distance": 0.15, "samples": 16, "aa": 4, "strength": 0.6},
    "placements": P,
}
json.dump(spec, open(os.path.join(HERE, '..', 'specs', 'vehicle-v3.json'), 'w'), indent=1)
print(len(P))
