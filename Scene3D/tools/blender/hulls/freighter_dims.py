"""Drover-class civil transport (CT-4 cargo / CT-7 troops): shared dimensions for the remodel.

Pure Python (no bpy), imported by freighter.py (hull), freighter_spec.py (kit placements) and
freighter_extras.py (containers, port lites). Ship frame, metres: bow +Z, dorsal +Y, port +X.
Everything is measured on the fal / Tripo H3.1 blueprints (measure.py sections every 2 m, ortho
views) unless noted as a design choice.

Both variants share one layout (common spine, engine section and crew module), and differ in
the mid-body: the cargo ship carries 20-ft ISO containers on a box girder, the troop ship four
pressurised habitat cylinders round a spine tube between two side girders.

Envelope (bbox, symmetric by construction; the carrier bay's binding load, keep it):
    cargo   54.68 x 38.15 x 134.12 m (x +-27.34, y +-19.08, z +-67.06)
    troops  57.74 x 37.65 x 128.84 m (x +-28.87, y +-18.83, z +-64.42)
x: radiator fin tips; y: mast antenna tip (top) and landing-leg pads (bottom); z: crew-module
bow face (front) and the bell exit lips (aft).
"""
import math

ISO = (6.058, 2.591, 2.438)   # 20-ft container: length, height, width (kit container.glb)
TIER = 2.591
PITCH_W = 2.438 + 0.03        # container width + a 3 cm gap in a stack row

VARIANTS = {
    'cargo': {
        'name': 'freighter', 'number': 'CT-4',
        'BOW': 67.06, 'HX': 27.34, 'HY': 19.08,
        # crew module: aft bulkhead z, length to the bow face
        'CM0': 34.0,
        # collar (docking block) aft face; payload span to the reactor block front
        'COL1': 25.5, 'R0': -22.5, 'R1': -34.0,
        # reactor block octagon: half-width, bottom, top, chamfer
        'RX': 13.4, 'RYB': -12.6, 'RYT': 12.0, 'RCH': 3.4,
        # bells (kit bell-L at the measured exit radius), exit plane centre
        'BELL': {'x': 7.74, 'y': 0.1, 'r': 4.75},
        # engine housings (cylinders ending in a bell-mount ring), tanks, keel
        'HOUS_R': 5.2, 'HOUS_RING': 5.95,
        'UTANK': {'x': 14.0, 'y': 4.5, 'r': 2.2},
        'LTANK': {'x': 11.6, 'y': -9.2, 'r': 3.5},
        # radiators: inner / outer x (fin tips at HX), y range, z range (two panels)
        'RAD': {'x0': 21.7, 'y0': -11.0, 'y1': 3.1, 'z0': -60.8, 'z1': -29.5},
        # landing legs: fore (centre line) and aft pair
        'LEG_F': {'x': 0.0, 'z': 39.5}, 'LEG_A': {'x': 7.2, 'z': -37.0},
        'MAST_Z': -25.8,
    },
    'troops': {
        'name': 'freighter-troops', 'number': 'CT-7',
        'BOW': 64.42, 'HX': 28.87, 'HY': 18.83,
        'CM0': 31.4,
        'COL1': 24.0, 'R0': -20.5, 'R1': -30.5,
        'RX': 15.5, 'RYB': -12.4, 'RYT': 10.1, 'RCH': 3.2,
        'BELL': {'x': 8.54, 'y': -0.05, 'r': 5.65},
        'HOUS_R': 6.0, 'HOUS_RING': 7.0,
        'UTANK': {'x': 15.4, 'y': 4.6, 'r': 2.2},
        'LTANK': {'x': 12.4, 'y': -9.0, 'r': 3.4},
        'RAD': {'x0': 22.7, 'y0': -10.5, 'y1': 3.2, 'z0': -55.5, 'z1': -27.5},
        'LEG_F': {'x': 0.0, 'z': 36.7}, 'LEG_A': {'x': 9.8, 'z': -34.5},
        'MAST_Z': -24.3,
    },
}

# kit bell-L: r 3.5 at the exit, body 8.12 deep, bbox 0.042 behind the exit plane
BELL_L = {'r': 3.5, 'back': 8.12, 'lip': 0.042, 'flange': 4.22}

# crew module section (local u = z - CM0 from the aft bulkhead; both variants, measured on both
# blueprints: 10.3 m half-beam, roof 9.8, keel -13.0; the bow taper starts 21.5 m forward)
CM = {
    'top': 9.8, 'roof_x': 7.4, 'sh_y': 7.8, 'ins': 0.9, 'ledge': 4.6, 'fx': 10.3, 'fy0': -10.6, 'bx': 7.8, 'bot': -13.0,
    'taper': 21.5,
    # bow face (u = length): blunt, 12.6 x 14.4 m; the upper-tier step (a walkway ledge on the
    # 4.6 m deck line, design) runs out on the taper
    'nose': {'top': 4.6, 'roof_x': 3.8, 'sh_y': 3.3, 'ins': 0.12, 'ledge': 3.0, 'fx': 6.3, 'fy0': -7.6, 'bx': 4.4, 'bot': -10.0},
}
# decks: 3 m pitch floors; ports sit 1.5 m above each floor
DECKS = [-10.4, -7.4, -4.4, -1.4, 1.6, 4.6]


def V(name):
    v = dict(VARIANTS[name])
    v['variant'] = name
    b = v['BELL']
    s = b['r'] / BELL_L['r']
    b['scale'] = s
    b['z'] = -v['BOW'] + BELL_L['lip'] * s          # exit plane (its lip lands on -BOW)
    b['back'] = b['z'] + BELL_L['back'] * s          # bell mounting flange = housing aft face
    b['flange'] = BELL_L['flange'] * s
    v['CM_LEN'] = v['BOW'] - v['CM0']
    v['PAY0'], v['PAY1'] = v['R0'], v['COL1']         # payload span (aft, fore)
    return v


def cm_half(u, L):
    """Crew-module half section at local u (0 = aft bulkhead, L = bow face): (x, y) from the
    roof centre down the port side to the keel centre: roof, shoulder chamfer, upper-tier wall,
    ledge, flank, lower chamfer, keel."""
    c, n = CM, CM['nose']
    t = 0.0 if u <= c['taper'] else min(1.0, (u - c['taper']) / (L - c['taper']))
    # the roof drops faster than the flank narrows (a sloped brow over the bridge band)
    tr = t ** 0.85
    g = lambda k: c[k] + (n[k] - c[k]) * (tr if k in ('top', 'roof_x', 'sh_y', 'ledge') else t)
    fx = g('fx')
    return [(0.0, g('top')), (g('roof_x'), g('top')), (fx - g('ins'), g('sh_y')), (fx - g('ins'), g('ledge')), (fx, g('ledge')),
            (fx, g('fy0')), (g('bx'), g('bot')), (0.0, g('bot'))]


# ------------------------------------------------------------------------------------------
# cargo: container stacks on the payload girder
# ------------------------------------------------------------------------------------------
GIRDER = {'x': 7.45, 'top': 1.9, 'bot': -6.3, 'chord': 0.7, 'deck': 0.3}
BAYS = 8
BAY_POST = 0.5
# weathered cargo colours (sRGB base-colour factors, designed to read through the civil livery:
# saturated enough to keep their hue, 'white' a warm cream and 'grey' a blue grey so both stay
# a little lighter than the hull)
CARGO_COLOURS = {
    'rust': [0.56, 0.19, 0.12],
    'ochre': [0.74, 0.52, 0.17],
    'blue': [0.19, 0.34, 0.60],
    'green': [0.24, 0.44, 0.30],
    'grey': [0.52, 0.56, 0.62],
    'white': [0.86, 0.82, 0.70],
}


def _hash(*a):
    h = 2166136261
    for v in a:
        h = ((h ^ (int(v) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    h ^= h >> 13
    h = (h * 1274126177) & 0xFFFFFFFF
    return (h & 0xFFFFFF) / 0xFFFFFF


def bays(v):
    """Container bays along z: [(z_fore_edge, z_aft_edge)], two columns each, cell-guide posts
    between bays."""
    span0, span1 = v['PAY0'] + 1.6, v['PAY1'] - 1.4
    width = 2 * PITCH_W
    pitch = width + BAY_POST
    total = BAYS * pitch - BAY_POST
    z0 = (span0 + span1) / 2 + total / 2
    out = []
    for i in range(BAYS):
        a = z0 - i * pitch
        out.append((a, a - width))
    return out


def containers(v):
    """Container boxes: list of dicts {c: centre (ship frame), colour, var (weathering variant),
    flip (doors to port or starboard)}. Long axis along X (two boxes end to end across the deck),
    three tiers above the girder's top deck and three hanging under its bottom deck; a few
    columns are one tier short (a stepped, loaded-in-service look, as the concept)."""
    L, H, Wd = ISO
    names = list(CARGO_COLOURS)
    # colour weights: rust, ochre, blue, green, grey, white
    wts = [0.22, 0.16, 0.17, 0.14, 0.13, 0.18]
    cum = [sum(wts[:i + 1]) for i in range(len(wts))]
    out = []
    gx = L / 2 + 0.03
    for bi, (za, zb) in enumerate(bays(v)):
        for col in range(2):
            zc = za - PITCH_W / 2 - col * PITCH_W
            for side in (1, -1):
                for deck in ('top', 'bot'):
                    h = _hash(bi, col, side, deck == 'top', 7)
                    tiers = 3 if h > 0.22 else 2
                    if deck == 'bot' and h < 0.08:
                        tiers = 1
                    for t in range(tiers):
                        if deck == 'top':
                            yb = GIRDER['top'] + t * TIER
                        else:
                            yb = GIRDER['bot'] - (t + 1) * TIER
                        r = _hash(bi, col, side, t, deck == 'top', 11)
                        ci = next(i for i, c in enumerate(cum) if r <= c + 1e-9)
                        out.append({'c': (side * gx, yb + H / 2, zc), 'colour': names[ci],
                                    'var': int(_hash(bi, col, side, t, 3) * 4) % 4,
                                    'flip': side < 0})
    return out


# ------------------------------------------------------------------------------------------
# troops: habitat cylinders
# ------------------------------------------------------------------------------------------
HAB = {'r': 4.6, 'x': 4.6, 'yu': 5.5, 'yl': -9.8, 'dome': 2.4, 'ring_pitch': 9.2}
TGIRDER = {'x0': 7.7, 'x1': 11.6, 'top': 2.0, 'bot': -5.1}
SPINE = {'r': 3.0, 'y': -2.1}


def hab_span(v):
    """Habitat z range (dome tips): clear of the collar and the reactor block."""
    return v['R0'] + 1.3, v['COL1'] - 0.7
