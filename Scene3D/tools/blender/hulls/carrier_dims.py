"""Keystone-class fleet carrier CV-50: shared dimensions of the hard-surface remodel.

Used by carrier.py (the hull), carrier_spec.py (kit placements) and carrier_module.py (the ship
module). Ship frame of the scene, metres: bow +Z, dorsal +Y, port +X, centred on the envelope
like glbship.js does. The blueprint (the v5 fal / Tripo H3.1 hull, measure.py at length 900) sat
0.9 m to port of its envelope centre; the remodel is built symmetric about x = 0, so every old
coordinate x ~ +0.9 on the centre line is x = 0 here. Heights (y) and stations (z) keep the old
values, in particular every hangar deck height of anchors.hangarDeck.

Envelope 405.5 x 319.3 x 900 m (the old module): the extremes are set by named features so the
bbox centre stays at the origin (then the deck heights need no shift):
  x +-202.75  outboard faces of the two stern gun sponsons
  y +159.65   masthead of the island;   y -159.65  ventral sensor dome under the keel pod
  z -450.0    exit planes of the six fusion bells;   z +450.0  tips of the two bow sensor probes
"""

# ---------------------------------------------------------------------------------------------
# stations (z) of the main blocks, from the blueprint (old module comments + sections every 10 m)
# ---------------------------------------------------------------------------------------------
Z_STERN = -371.0          # stern plate (bell housings stand on it)
Z_BACK = -276.0           # hangar back wall
Z_SF = -261.0             # stern block front face (flank), faces the aft bay
Z_BA = 276.0              # bow section aft face (flank), faces bay 1
Z_BF = 418.0              # bow face (the mouth frame stands proud of it)
Z_LIP = 421.4             # front of the mouth lip
Z_TIP = 450.0             # bow probes
Z_EXIT = -450.0           # bell exit planes

# frame rings between the six flank bays (z of the two faces), blueprint FRAME_FACES
FRAMES = [(-188.1, -164.3), (-98.0, -73.5), (-5.25, 19.2), (87.42, 111.6), (178.1, 202.1)]
# open flank bays (between the stern block, the frames and the bow section)
BAYS = [(Z_SF, -188.1), (-164.3, -98.0), (-73.5, -5.25), (19.2, 87.42), (111.6, 178.1), (202.1, Z_BA)]

# ---------------------------------------------------------------------------------------------
# hangar: deck heights (kept EXACTLY from the installed module), ceilings, walls
# ---------------------------------------------------------------------------------------------
Y_AFT = -92.45            # aft bay deck (zone 'aft')
Y_LONG = -96.35           # bays 5-2, continuous under frames F2-F4 (zones long, bay5..bay2)
Y_SILL = -91.9            # sills of the frame rings F1 and F5 (between decks of different height)
Y_BAY1 = -93.61           # bay 1 (zone 'bay1')
Y_BOW = -90.97            # enclosed bow section (zone 'bow', the launch lane and lifts)
Y_CEIL = -0.6             # ceiling of the open bays (underside of the upper slab)
Y_RING = -5.7             # ceiling under the frame rings
Y_BOWC = -6.4             # ceiling of the bow section
W_IN = 95.0               # inner walls (frame rings, stern recess, bow section): x = +-95
# deck height per z (the lower slab's top) and the frame sill per frame
DECK_RUNS = [(-262.0, FRAMES[0][0], Y_AFT), (FRAMES[0][0], FRAMES[0][1], Y_SILL), (FRAMES[0][1], FRAMES[4][0], Y_LONG),
             (FRAMES[4][0], FRAMES[4][1], Y_SILL), (FRAMES[4][1], Z_BA + 1.0, Y_BAY1)]
SILL = [Y_SILL, Y_LONG, Y_LONG, Y_LONG, Y_SILL]


def c_oct(ceil, floor, tc=(16.0, 20.0), bc=(14.0, 14.0), w=W_IN):
    """Half outline (x >= 0, top centre -> bottom centre) of a hangar cross-section: ceiling,
    45-ish top chamfer (tc = dx, dy), wall at x = w, bottom chamfer (bc), floor."""
    return [(0.0, ceil), (w - tc[0], ceil), (w, ceil - tc[1]), (w, floor + bc[1]), (w - bc[0], floor), (0.0, floor)]


# bow section / mouth: the blueprint's bow chamfers (80.5, -9) -> (94.4, -29) and (94.2, -73) -> (80.8, -89)
C_BOW = c_oct(Y_BOWC, Y_BOW, tc=(15.0, 20.0), bc=(14.0, 16.0))
C_STERN = c_oct(Y_CEIL, Y_AFT, tc=(16.0, 20.0), bc=(12.0, 12.0))


def c_ring(sill):
    # frame rings: long-zone rings keep a small bottom chamfer so the deck stays continuous
    return c_oct(Y_RING, sill, tc=(16.0, 20.3), bc=(8.0, 8.0) if sill < -95 else (14.0, 14.0))


# ---------------------------------------------------------------------------------------------
# outer hull: half profiles (x >= 0, top centre -> bottom centre), all corners 45 degrees
# ---------------------------------------------------------------------------------------------
P_BOX = [(0.0, 21.0), (100.0, 21.0), (121.0, 0.0), (121.0, -96.0), (100.0, -117.0), (0.0, -117.0)]   # bays region
P_END = [(0.0, 23.0), (98.0, 23.0), (131.0, -10.0), (131.0, -94.0), (104.0, -121.0), (0.0, -121.0)]  # stern, bow, frames
X_FLANK = 121.0           # flank plating at the bays (the opening plane)
X_END = 131.0             # flank of the stern block, the bow section and the frame posts
Y_DECK = 21.0             # dorsal deck (upper slab top)
Y_KEEL = -145.6           # keel flat (the wedge under the box)
KEEL = dict(top=-115.0, half_top=100.0, z0=-330.0, z1=232.0)   # 45-degree wedge, ramped ends
KEEL_ROWS = (-125.0, -133.0)   # port rows on the wedge's 45-degree sides

# stern gun sponsons (blueprint: x 133 .. 203, y -30 .. -72, z -279 .. -339)
SPONSON = dict(x0=125.0, x1=202.75, zc=-310.0, l=62.0, yc=-52.0, h=40.0, c=10.0)

# drive: six bells (blueprint circle fits, centred), kit bell-XL (engine radius 7.0) scaled to
# the blueprint radii 18.3 (upper / lower) and 18.9 (outboard)
BELLS = [((57.4, -3.2), 18.3), ((92.3, -50.1), 18.9), ((57.4, -95.9), 18.3)]
BELL_XL_R = 7.0
BELL_XL_LEN = 16.24

# island (stepped building on a chamfered plinth): (name, zc, width, length, chamfer, y0, y1)
PLINTH = dict(zc=-114.0, w=90.0, l=270.0, c=22.0, y0=Y_DECK - 1.0, y1=40.0)
TIERS = [
    ('t1', -118.0, 66.0, 200.0, 15.0, 40.0, 58.0),
    ('t2', -121.0, 50.0, 150.0, 12.0, 58.0, 79.0),
    ('t3', -124.0, 44.0, 118.0, 10.0, 79.0, 100.0),
    ('t4', -128.0, 36.0, 86.0, 8.0, 100.0, 121.0),
    ('t5', -131.0, 24.0, 50.0, 6.0, 121.0, 136.0),
    ('t6', -133.0, 13.0, 18.0, 3.0, 136.0, 145.0),
]
BRIDGE = dict(zc=-74.0, w=64.0, l=34.0, c=8.0, y0=100.0, y1=112.0)   # hammerhead bridge on T3, overhangs its front
Y_TOP = 159.65
Y_BOTTOM = -159.65
MAST = dict(z=-133.0, y0=145.0)
DECK_PITCH = 3.0

# spine turrets (kit turret-L x2.6: 41 m base, 63 m barrels) and deck-edge secondaries (turret-M x1.4)
TURRET_L = 2.6
SPINE_TURRETS = [(-306.0, -1), (60.0, 1), (235.0, 1)]      # (z, guns +1 forward / -1 aft)
TURRET_M = 1.4
EDGE_TURRETS = [(-296.0, -1), (140.0, 1), (330.0, 1)]      # x = +-78 on the deck, both sides
X_EDGE_T = 78.0
