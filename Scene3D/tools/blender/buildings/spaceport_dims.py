"""SP-3 orbital spaceport: shared dimensions (pure Python, no bpy).

Used by spaceport.py (the station geometry), spaceport_spec.py (kit placements) and the runtime
module notes (src/buildings/spaceport.js). Approved concept: style-library/styles/cqs-fleet/images/
spaceport-r6.jpg (r5 C, offset half-shells, made busier; corrections 25, 29-32).

Station frame = the scene's asset frame, metres: forward +Z, up +Y, left (port) +X. The open slot is
on the +X side ("near" side: the studio camera at az 35 sits at +X +Z). Origin: the shells' common
axis (y = 0) at the carrier's mid-length (z = 0). Not re-centred in Blender; the runtime centres the
envelope like every other GLB asset.

The carrier inside is the real CV-50 (assets/ships/carrier.glb, 900 m, carrier frame = its bbox
centre) instanced at CARRIER_AT; its hull section (carrier_dims.P_END: x +-131, y 23..-121, keel
flat -145.6) is centred on the station axis. Docked freighters are the real CT-4
(assets/ships/freighter.glb, 134.1 m = 0.149 of the carrier) at FREIGHTERS.
"""
import math

# ------------------------------------------------------------------------------------------------
# the instanced ships
# ------------------------------------------------------------------------------------------------
CARRIER_LEN = 900.0
CY = 61.0                      # carrier frame origin in the station frame: (0, CY, 0)
CARRIER_AT = (0.0, CY, 0.0)
# part-built: the carrier GLB is clipped at the aft face of its frame ring F4 (carrier z 87.42):
# the bow section, bay 1, frame F5, bay 2 and F4 stay plated (z 87.4..450 = 362 m, 40 %), aft of it
# the hull is bare frames on the keel (CV_FRAMES below)
CV_CUT_Z = 87.42
FREIGHTER_LEN = 134.12
FREIGHTER_BOX = (54.68, 38.16, 134.12)   # B x H x L of the CT-4 envelope (fin tips, mast, bells)

# ------------------------------------------------------------------------------------------------
# the two offset half-shells: octagonal section (flats at 0, 45, 90 ... degrees; theta measured
# from +X (near side) toward +Y (up)), apothem = inner face distance from the axis
# ------------------------------------------------------------------------------------------------
SHELL_T = 6.0                  # plate thickness (thin: correction 31, "busy, not bulky")
TROUGH = dict(a=175.0, th0=157.5, th1=360.0, z0=-480.0, z1=520.0)   # far wall top -> bottom -> near wall mid
HOOD = dict(a=196.0, th0=40.0, th1=200.0, z0=-560.0, z1=40.0)       # near upper chamfer -> top -> far wall
RIB_PITCH = 40.0               # inner frame ribs
RIB = dict(w=3.0, d=5.0)       # rib width along z, depth inward
PANEL = dict(dz=24.0, band=29.0, seam=0.45, depth=0.35)   # outer plating panels, seam groove
RIM = dict(w=16.0, r_in=6.0, r_out=6.0, ch=3.0, seg=60.0, joint=1.2)  # pale rims: tangential width, radial overhang in / out, chamfer
ARCH = dict(w=14.0, r_in=8.0, r_out=6.0, ch=3.0)                       # pale end arches (z ends of each shell)

STATION_Z = (min(TROUGH['z0'], HOOD['z0']), max(TROUGH['z1'], HOOD['z1']))   # -560 .. 520 = 1080 m


def face_angle(th):
    """centre angle (deg) of the octagon flat that contains polar angle th"""
    return 45.0 * round(th / 45.0)


def oct_pt(th, a):
    """point (x, y) on the octagon of apothem a at polar angle th (deg)"""
    f = math.radians(face_angle(th))
    t = math.radians(th)
    r = a / math.cos(t - f)
    return (r * math.cos(t), r * math.sin(t))


def arc_angles(th0, th1):
    """th0, every octagon vertex angle strictly between, th1 (th0 < th1)"""
    out = [th0]
    k = math.floor((th0 - 22.5) / 45.0) + 1
    while 22.5 + 45.0 * k < th1 - 1e-6:
        v = 22.5 + 45.0 * k
        if v > th0 + 1e-6:
            out.append(v)
        k += 1
    out.append(th1)
    return out


def oct_normal(th):
    f = math.radians(face_angle(th))
    return (math.cos(f), math.sin(f))


# rim lines (free longitudinal edges) and the shell each belongs to
def rim_edges():
    return [
        dict(name='trough_near', shell='TROUGH', th=TROUGH['th1'], side=+1),
        dict(name='trough_far', shell='TROUGH', th=TROUGH['th0'], side=-1),
        dict(name='hood_near', shell='HOOD', th=HOOD['th0'], side=-1),
        dict(name='hood_far', shell='HOOD', th=HOOD['th1'], side=+1),
    ]


# ------------------------------------------------------------------------------------------------
# carrier part-built: frames (carrier frame z, metres; P_END section from carrier_dims)
# ------------------------------------------------------------------------------------------------
P_END = [(0.0, 23.0), (98.0, 23.0), (131.0, -10.0), (131.0, -94.0), (104.0, -121.0), (0.0, -121.0)]
# hangar opening of a frame ring (carrier_dims.c_ring for the long zone): x +-95, y -5.7 .. -96.35
RING_IN = [(0.0, -5.7), (79.0, -5.7), (95.0, -26.0), (95.0, -88.35), (87.0, -96.35), (0.0, -96.35)]
HEAVY_RINGS = [(-5.25, 19.2), (-98.0, -73.5), (-188.1, -164.3)]     # the real F3, F2, F1 stations
STERN_RING = (-371.0, -361.0)                                       # stern plate frame
LIGHT_RIB_T = 4.0
LIGHT_RIB_W = 7.0              # radial depth of the bare ribs between the rings
KEEL = dict(x=34.0, top=-117.0, bot=-145.6, z0=-371.0, z1=CV_CUT_Z)
STRINGERS = [(40.0, -117.0, 5.0), (95.0, -105.0, 4.0), (131.0, -52.0, 4.0), (98.0, 23.0, 4.0), (0.0, 23.0, 4.0)]   # (x, y, size)
CRADLES = [-300.0, -140.0, 20.0, 180.0, 340.0]   # keel cradles (station z) from the trough floor


def light_ribs():
    """z of the bare ribs between the heavy rings, aft of the cut (pitch about 23 m)"""
    stations = sorted([CV_CUT_Z] + [z for r in HEAVY_RINGS for z in r] + list(STERN_RING))
    out = []
    spans = [(HEAVY_RINGS[0][1], CV_CUT_Z), (HEAVY_RINGS[1][1], HEAVY_RINGS[0][0]), (HEAVY_RINGS[2][1], HEAVY_RINGS[1][0]),
             (STERN_RING[1], HEAVY_RINGS[2][0])]
    for z0, z1 in spans:
        n = max(1, round((z1 - z0) / 23.0))
        for i in range(1, n):
            out.append(z0 + (z1 - z0) * i / n)
    return out


# ------------------------------------------------------------------------------------------------
# what sits on the shells
# ------------------------------------------------------------------------------------------------
# habitat / cargo blocks (kit habBlock): rim, z centre, length, width, decks (3 m each + 2 m plinth)
HAB_BLOCKS = [
    dict(rim='trough_near', z=468.0, L=44.0, W=16.0, decks=5),
    dict(rim='trough_near', z=330.0, L=36.0, W=14.0, decks=4),
    dict(rim='trough_near', z=-130.0, L=44.0, W=16.0, decks=5),
    dict(rim='trough_near', z=-330.0, L=36.0, W=14.0, decks=4),
    dict(rim='trough_far', z=440.0, L=44.0, W=16.0, decks=5),
    dict(rim='trough_far', z=150.0, L=36.0, W=14.0, decks=4),
    dict(rim='hood_near', z=-70.0, L=44.0, W=16.0, decks=4),
    dict(rim='hood_near', z=-330.0, L=40.0, W=16.0, decks=5),
    dict(rim='hood_near', z=-520.0, L=36.0, W=14.0, decks=4),
    dict(rim='hood_top', z=-200.0, L=60.0, W=24.0, decks=6),      # yard control block on the hood
]
DECK_PITCH = 3.0
PORT_PITCH = 2.5
# container stacks on the near rim walkway (z ranges)
CONTAINER_RUNS = [(380.0, 300.0), (230.0, 120.0), (-200.0, -260.0)]
# gantry cranes over the open forward bay (z), riding the two trough rims
GANTRIES = [205.0, 385.0]
# manipulator arms: (mount, z, reach target in carrier-relative station coords)
MANIPULATORS = [
    dict(mount='hood_ceiling', z=-120.0, x=60.0),
    dict(mount='hood_ceiling', z=-260.0, x=-50.0),
    dict(mount='hood_ceiling', z=-420.0, x=40.0),
    dict(mount='trough_near', z=60.0),
    dict(mount='trough_near', z=-40.0),
    dict(mount='far_wall', z=300.0),
    dict(mount='far_wall', z=20.0),
]
# docked CT-4s on clamp arms (station frame): position of the freighter's envelope centre, yaw (deg about
# +Y, 0 = bow +Z), roll (deg about its own z), the clamp root on the shell and arm length
# The side berths clamp the freighter's collar airlock (CT-4 frame (+-11.5, -2.2, 29.75), freighter_dims / the
# freighter module's autoClear boxes); the hood berth holds it belly-down by two cradles under the reactor
# block and the crew module (CT-4 y -12.6).
FREIGHTERS = [
    dict(name='near_fwd', p=(218.0, -45.0, 250.0), yaw=0.0),
    dict(name='near_aft', p=(218.0, -45.0, -230.0), yaw=180.0),
    dict(name='far_mid', p=(-218.0, -40.0, 165.0), yaw=0.0),
    dict(name='hood_top', p=(0.0, 233.0, -400.0), yaw=180.0, top=True),
]
CT4_LOCK = (11.5, -2.2, 29.75)
CT4_BELLY = -12.6


def freighter_clamps(f):
    """clamp arms for a docked freighter: [(root (station), normal, reach)]"""
    px, py, pz = f['p']
    a = math.radians(f['yaw'])
    rot = lambda x, z: (x * math.cos(a) + z * math.sin(a), -x * math.sin(a) + z * math.cos(a))
    if f.get('top'):
        top = HOOD['a'] + SHELL_T
        out = []
        for lz in (-28.0, 40.0):
            dx, dz = rot(0.0, lz)
            out.append(((px + dx, top, pz + dz), (0.0, 1.0, 0.0), py + CT4_BELLY - top))
        return out
    side = 1.0 if px > 0 else -1.0
    wall = TROUGH['a'] + SHELL_T
    # the airlock on the side facing the station
    for sx in (1.0, -1.0):
        dx, dz = rot(sx * CT4_LOCK[0], CT4_LOCK[2])
        if (px + dx) * side < px * side:
            return [((side * wall, py + CT4_LOCK[1], pz + dz), (side, 0.0, 0.0), abs(px + dx) - wall)]
    raise ValueError(f)
# radiator / solar arrays (kit radiatorArray), hung off the lower chamfers
RADIATORS = [
    dict(th=315.0, z=-430.0, side=+1), dict(th=315.0, z=-300.0, side=+1), dict(th=315.0, z=-90.0, side=+1),
    dict(th=315.0, z=40.0, side=+1), dict(th=315.0, z=360.0, side=+1), dict(th=315.0, z=470.0, side=+1),
    dict(th=225.0, z=-330.0, side=-1), dict(th=225.0, z=-200.0, side=-1), dict(th=225.0, z=300.0, side=-1), dict(th=225.0, z=420.0, side=-1),
]
# tugs (kit tug): position, yaw
TUGS = [
    dict(p=(120.0, -60.0, 548.0), yaw=200.0),
    dict(p=(40.0, 30.0, 552.0), yaw=170.0),
    dict(p=(262.0, -10.0, 110.0), yaw=95.0),
]


# ------------------------------------------------------------------------------------------------
# mount frames (numpy 4x4: columns x, y (up / mount normal), z (along), origin) for what stands on
# the rims and shells; shared by spaceport.py (geometry) and spaceport_spec.py (kit placements)
# ------------------------------------------------------------------------------------------------
import numpy as np  # noqa: E402

RIM_TOP = {   # top face of each longitudinal rim: point (x, y) and outward "up" for things standing on it
    'trough_near': ((TROUGH['a'] + SHELL_T / 2, 4.0), (0.0, 1.0)),
    'trough_far': ((-(TROUGH['a'] + SHELL_T / 2), 75.5 + 4.0), (0.0, 1.0)),
}


def _frame(o, up, along=(0.0, 0.0, 1.0)):
    y = np.asarray(up, float); y /= np.linalg.norm(y)
    z = np.asarray(along, float); z = z - y * np.dot(y, z); z /= np.linalg.norm(z)
    x = np.cross(y, z)
    M = np.eye(4)
    M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = x, y, z, o
    return M


def mount_frame(where, z, x=0.0):
    """frame of something standing at station z on a named mount"""
    if where in RIM_TOP:
        (px, py), (ux, uy) = RIM_TOP[where]
        return _frame((px, py, z), (ux, uy, 0.0))
    if where == 'hood_near':   # on the hood's outer upper-near chamfer (face 45), 30 m in from its rim
        a = HOOD['a'] + SHELL_T
        n = (math.sqrt(0.5), math.sqrt(0.5))
        px, py = oct_pt(56.0, a)
        return _frame((px, py, z), (n[0], n[1], 0.0))
    if where == 'hood_top':
        return _frame((x, HOOD['a'] + SHELL_T, z), (0.0, 1.0, 0.0))
    if where == 'hood_ceiling':  # hanging from the hood's inner top face (below the ribs)
        return _frame((x, HOOD['a'] - RIB['d'], z), (0.0, -1.0, 0.0))
    raise KeyError(where)


def block_frame(b):
    return mount_frame(b['rim'], b['z'], b.get('x', 0.0))
