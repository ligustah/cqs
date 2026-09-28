"""Dimensions of the Petrel-class fighter remodel (pure Python, no bpy): shared by fighter.py (the
hull model) and fighter_spec.py (the kit placements). Ship frame, metres, bow +Z, dorsal +Y,
port +X; values measured on the blueprint (see fighter.py) unless noted.
"""
import math


def interp_table(table, z, cols):
    zs = [r[0] for r in table]
    if z <= zs[0]:
        return {c: table[0][1][c] for c in cols}
    if z >= zs[-1]:
        return {c: table[-1][1][c] for c in cols}
    for (z0, a), (z1, b) in zip(table[:-1], table[1:]):
        if z0 <= z <= z1:
            t = (z - z0) / (z1 - z0) if z1 > z0 else 0
            return {c: a[c] + (b[c] - a[c]) * t for c in cols}


BOW_Z = 35.856           # bow frame lip (bbox front = -bell exit)
BOW_PLATE = 35.2         # recessed sensor plate
STERN_Z = -26.0          # hull loft start (stern face)
STERN_LIP = -26.4        # stern frame lip
STERN_PLATE = -26.05     # recessed stern plate (bell sockets cut into it)
BELL = dict(x=5.9, y=0.0, r=3.55, exit=-35.856, scale=3.55 / 3.5)   # kit bell-L x1.0143
SBELL = dict(x=20.05, y=-3.3, r=1.37, exit=-16.64, scale=1.37 / 1.4)  # kit bell-S x0.979
DECK_HI = 6.84           # raised dorsal deck
DECK_AFT = 5.28          # aft deck (stern block)
SPINE_Y = 6.98           # spine / bridge block roof
DECK_STEP = -18.5        # step from the aft deck up to the raised deck

# ------------------------------------------------------------------------------------------
# hull stations: z -> top y, top-flat half-width, flank half-width, flank top, flank bottom,
# belly-flat half-width, belly y (port half; mirrored)
# ------------------------------------------------------------------------------------------
COLS = ['T', 'TX', 'W', 'FT', 'FB', 'BX', 'B']
ST = [
    (STERN_Z, dict(T=5.28, TX=9.1, W=12.9, FT=0.25, FB=-4.45, BX=10.5, B=-6.13)),
    (-22.0, dict(T=5.28, TX=9.1, W=12.95, FT=0.22, FB=-4.95, BX=10.7, B=-6.95)),
    (DECK_STEP - 0.06, dict(T=5.28, TX=9.1, W=12.95, FT=0.2, FB=-5.5, BX=10.8, B=-7.85)),
    (DECK_STEP + 0.06, dict(T=DECK_HI, TX=7.95, W=12.95, FT=0.2, FB=-5.52, BX=10.8, B=-7.88)),
    (-10.0, dict(T=DECK_HI, TX=7.95, W=13.0, FT=0.2, FB=-6.4, BX=10.65, B=-10.0)),
    (-9.0, dict(T=DECK_HI, TX=7.95, W=13.0, FT=0.2, FB=-6.4, BX=10.65, B=-10.07)),
    (-3.3, dict(T=DECK_HI, TX=7.95, W=13.0, FT=0.2, FB=-6.4, BX=10.65, B=-10.07)),
    (-1.9, dict(T=5.8, TX=8.73, W=13.0, FT=0.2, FB=-6.4, BX=10.65, B=-10.07)),
    (4.2, dict(T=5.8, TX=8.73, W=13.0, FT=0.2, FB=-6.4, BX=10.65, B=-10.07)),
    (5.4, dict(T=5.49, TX=8.75, W=12.83, FT=-0.1, FB=-6.2, BX=10.5, B=-10.07)),
    (14.9, dict(T=3.0, TX=8.2, W=11.45, FT=-1.9, FB=-5.05, BX=9.35, B=-8.2)),
    (15.5, dict(T=2.92, TX=8.05, W=10.75, FT=-1.85, FB=-5.0, BX=9.0, B=-8.08)),
    (18.0, dict(T=2.82, TX=7.9, W=10.2, FT=-1.8, FB=-4.9, BX=8.6, B=-8.02)),
    (20.5, dict(T=2.4, TX=7.6, W=9.66, FT=-1.8, FB=-4.8, BX=8.1, B=-7.7)),
    (30.5, dict(T=0.55, TX=6.0, W=7.69, FT=-2.7, FB=-4.0, BX=6.3, B=-6.25)),
    (35.3, dict(T=-0.32, TX=5.3, W=6.75, FT=-2.85, FB=-3.9, BX=5.5, B=-5.42)),
]
SIDE_GLAZE = dict(y=5.6, z=11.55, w=3.5, h=0.8)
BR = dict(roof_end=11.3, rake=(15.1, 5.45), face=(17.0, 2.98), foot=(17.35, 2.4), aft=-18.3)
SP = dict(x=20.05, y=-3.35, w=6.2, h=5.6, c=1.25, z0=-13.4, z1=0.2, nose=1.9)
DOORS = [(8.6, -3.7), (-16.3, -2.6)]
GLAZE_DEPTH = 0.32
SIDE_DEPTH = 0.25


def prof(z):
    return interp_table(ST, z, COLS)


def fX(z):
    return prof(z)['W']


def top_y(z):
    return prof(z)['T']


def flank_n(z, side=1):
    """Outward normal (x, y, z) of the vertical flank at z (plan taper)."""
    d = 0.2
    dw = (fX(z + d) - fX(z - d)) / (2 * d)
    L = math.sqrt(1 + dw * dw)
    return (side / L, 0.0, -dw / L)


def _norm(v):
    L = math.sqrt(sum(c * c for c in v))
    return tuple(c / L for c in v)


def glazing_frame():
    """Bridge front glazing recess: back-wall centre, outward normal, up (along the face)."""
    zf, yf = BR['face']
    zr, yr = BR['rake']
    fn = _norm((0, abs(zf - zr), abs(yf - yr)))
    up = _norm((0, yr - yf, zr - zf))
    c = (0, (yr + yf) / 2 - fn[1] * GLAZE_DEPTH, (zr + zf) / 2 - fn[2] * GLAZE_DEPTH)
    return c, fn, up


def side_wall_x(y):
    """Bridge block wall (x at height y): 3.85 at the foot (y 2.4), 3.3 at the roof."""
    return 3.85 - 0.55 * (y - 2.4) / (SPINE_Y - 2.4)


def side_wall_n(side=1):
    return _norm((side, 0.55 / (SPINE_Y - 2.4), 0))
