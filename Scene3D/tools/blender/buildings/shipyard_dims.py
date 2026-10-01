"""Shipyard dimension tables (shared by shipyard_measure.py, shipyard.py and shipyard_spec.py).

Two frames:
  YARD frame  = the shipyard GLB / module frame: metres, ground top at y = 0, +Y up, +Z front (the
                ship's bow end of the berth), +X left; origin at the centre of the berth floor.
  MODEL frame = the destroyer GLB's own frame (assets/ships/destroyer.glb, not centred).
The DD-12 sits in the berth with yard = model + SHIP_T (no rotation, bow +Z): SHIP_T[1] is set so
the lowest keel block is BLOCK_MIN tall (shipyard_spec.py checks it against the measurement).

Build state of the DD-12 (correction 26: the real unit, part-built), MODEL frame z:
  z >= CUT['forward']                 plated (complete, as in the fleet)
  CUT['aft'] <= z < CUT['forward']    midships cut open to its frames: only the lower plating stays,
                                      y <= CUT['plateAft'] for z < CUT['step'], y <= CUT['plateFwd'] forward of it
  z < CUT['aft']                      no plating: bare keel and octagonal ring frames (shipyard.py)
"""

# ---- the ship in the berth --------------------------------------------------------------------
SHIP_Z = 10.0                    # yard z of model z = 0 (bow at yard ~ +111, stern ~ -91)
GROUND_MODEL_Y = -38.8           # model y of the yard ground (yard y = 0)
SHIP_T = (0.0, -GROUND_MODEL_Y, SHIP_Z)
CUT = {'forward': 20.0, 'aft': -34.0, 'step': -6.0, 'plateAft': -24.0, 'plateFwd': -17.0}

# ring frames (MODEL z; `src` = the station whose hull section the frame follows: the main hull without
# the broadside sponsons midships, the engine block aft; top of the frame in model y: midships frames rise to the deck, aft frames top of the frame in model y: midships frames rise to the deck, aft frames
# to the engine block deck; the last aft frames are only the lower U: the build front)
FRAMES = (
    [{'z': z, 'src': -13.0, 'top': -3.6, 'kind': 'full'} for z in (17.0, 11.0, 5.0, -1.0, -7.0, -13.0, -19.0, -25.0, -31.0)]
    + [{'z': z, 'src': -49.0, 'top': 0.5, 'kind': 'full'} for z in (-37.0, -43.0, -49.0, -55.0, -61.0, -67.0, -73.0)]
    + [{'z': -79.0, 'top': -12.0, 'kind': 'lower'}, {'z': -85.0, 'top': -20.0, 'kind': 'lower'}, {'z': -91.0, 'top': -27.0, 'kind': 'lower'}]
)
FRAME_WEB = 1.5                  # ring frame web depth (inward), m
FRAME_T = 0.8                    # frame flange thickness along z, m
KEEL = {'z0': -96.0, 'z1': -30.0, 'w': 3.2, 'h': 1.4}   # bare keel box girder under the aft frames (model z), its top at their bottoms
STRINGER_N = 5                   # longitudinal stringers per side on the aft frames (lower chine points)

# keel and bilge blocks (MODEL z stations); bilge blocks at x = +-BILGE_X
BILGE_X = 13.0
BLOCK_Z = {'keel': [-93.0, -82.0, -70.0, -58.0, -46.0, -34.0, -22.0, -10.0, 2.0, 14.0, 34.0, 62.0, 74.0, 86.0, 96.0],
           'bilge': [-70.0, -46.0, -22.0, 2.0, 62.0, 86.0]}
BLOCK_MIN = 1.6                  # the lowest block is at least this tall

# ---- yard layout (YARD frame) ------------------------------------------------------------------
SLAB = {'x': (-129.0, 129.0), 'z': (-141.0, 141.0), 'depth': 1.6}   # ground apron (diorama plinth)
BERTH = {'x': 40.0, 'z': (-126.0, 124.0)}                           # berth floor 80 x 250 m
GANTRY = {'z': 0.0, 'span': 96.0, 'clear': 95.0}                    # rails at x = +-48
GANTRY_RAIL_Z = (-140.0, 140.0)
CRANE_X = 68.0                    # crane runway centre (rails at 62 / 74), cranes on the +X side
CRANE_RAIL_Z = (-140.0, 26.0)
CRANES = [  # yard z, part name (each a baked slew / luff variant of the yard kit crane)
    {'z': -45.0, 'part': 'crane-A'},
    {'z': -104.0, 'part': 'crane-B'},
]
HALLS = [  # centre (x, z), along (part +X direction in the yard); 80 x 36 m segments
    {'c': (-106.0, -95.0), 'along': (-1, 0, 0)},   # back-left pair (concept), end doors facing out
    {'c': (-106.0, -9.0), 'along': (1, 0, 0)},
    {'c': (106.0, 9.0), 'along': (-1, 0, 0)},      # right pair
    {'c': (106.0, 95.0), 'along': (1, 0, 0)},
]
MASTS = [(-56.0, -80.0), (-56.0, 20.0), (-56.0, 100.0), (56.0, -70.0), (56.0, 30.0), (56.0, 104.0)]
BELL = {'p': (30.0, -112.0), 'scale': 1.106}       # kit bell-XL x the destroyer's centre-bell scale, lying on a cradle
MODULE = {'size': (22.0, 11.0, 16.0), 'bottom': 44.0}  # yard: the module the gantry lowers into midships (x, y, z)
