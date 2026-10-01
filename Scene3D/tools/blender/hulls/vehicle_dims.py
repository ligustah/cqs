"""Dimension tables of the V-31 wheeled 4x4 (tools/blender/hulls/vehicle.py), shared with vehicle_spec.py.

Pure Python (no bpy). Vehicle frame = the ship frame of the scene: metres, front +Z, up +Y, left +X.
Authored with the GROUND at y = 0 (glbship.js re-centres the GLB on its bbox at runtime; module.py shifts
every runtime coordinate by minus the assembled bbox centre).

Sources:
  - the brief (style-library/styles/cqs-fleet/briefs/vehicle.md, correction 19): body 6.5 x 2.6 x 2.5 m,
    weapon station to about 2.9 m, tyres 1.1-1.2 m, doors about 0.9 x 1.3-1.4 m, hatches 0.7-0.8 m;
  - the blueprint (assets/ships/raw/vehicle.glb, Tripo H3.1 multiview of the 4K turnaround, measured with
    measure.py at length 6.5): axles at z +1.6 / -1.9, roof 2.72 (scaled to the brief's 2.5), body
    half-width 1.13 with the tyres out to 1.48 (scaled so the tyres and fenders end at the brief's
    1.30), upper chamfer from 2.2 to the roof (half-width 0.94), belly 0.64, nose 0.87 half-width;
  - the brief's hardware rule moved the axles apart (wheelbase 3.5 -> 3.8) so two vehicle-size doors and
    the amber band fit between the arches.
"""
LENGTH = 6.5
Z_NOSE, Z_TAIL = 3.25, -3.25
ROOF = 2.5
WIDTH = 2.6

# body stations (z, profile). Half-profile from the roof centre down the +X side:
#   (0, T) roof -> (TX, T) roof edge -> (W, FT) upper chamfer -> (W, FM) flank (paint) -> (W, FB) belly band
#   (dark) -> (BX, B) lower chamfer (dark) -> (0, B) belly
COLS = ['T', 'TX', 'W', 'FT', 'FM', 'FB', 'BX', 'B']
ST = [
    (-3.25, dict(T=2.44, TX=0.80, W=1.04, FT=2.18, FM=1.00, FB=0.86, BX=0.56, B=0.86)),
    (-3.17, dict(T=2.50, TX=0.84, W=1.10, FT=2.22, FM=0.98, FB=0.80, BX=0.60, B=0.80)),
    (-2.55, dict(T=2.50, TX=0.84, W=1.10, FT=2.22, FM=0.98, FB=0.78, BX=0.62, B=0.55)),
    (1.40, dict(T=2.50, TX=0.84, W=1.10, FT=2.22, FM=0.98, FB=0.78, BX=0.62, B=0.55)),     # cab roof front edge (brow)
    (1.95, dict(T=2.00, TX=0.80, W=1.10, FT=1.90, FM=0.98, FB=0.78, BX=0.62, B=0.55)),     # windscreen base / bonnet rear
    (2.55, dict(T=1.86, TX=0.76, W=1.04, FT=1.66, FM=1.02, FB=0.84, BX=0.60, B=0.58)),
    (3.10, dict(T=1.74, TX=0.64, W=0.90, FT=1.50, FM=1.14, FB=1.02, BX=0.56, B=0.95)),
    (3.25, dict(T=1.70, TX=0.60, W=0.86, FT=1.46, FM=1.14, FB=1.04, BX=0.54, B=0.99)),
]

# wheels and arches
AXLES = [1.80, -2.00]
WHEEL = dict(d=1.15, w=0.42, x_out=1.30)            # tyre outer face at x +-1.30 (the 2.6 m width)
WHEEL['r'] = WHEEL['d'] / 2
WHEEL['y'] = WHEEL['r']                              # axle height (tyre on the ground)
WHEEL['x_in'] = WHEEL['x_out'] - WHEEL['w']          # kit wheel origin (inner face) at x +-0.88
WELL_X = 0.84                                        # wheelhouse inner wall (suspension mount face)
# arch outline in (dz from the axle, y): faceted half-octagon, open at the bottom
ARCH = [(-0.70, 0.20), (-0.68, 1.18), (-0.44, 1.45), (0.44, 1.45), (0.68, 1.18), (0.70, 0.20)]
FLARE = dict(w=0.07, x0=1.04, x1=1.25)               # fender flare over the arch top (from the shoulders up), x extent

# doors (kit vehicleDoor: 0.9 x 1.3 m leaf, 1.0 x 1.4 m frame, surface-mounted on the flank)
DOOR_Y = 1.50
BAND = dict(z=-0.11, w=0.22)                         # amber flank band between the two doors
COBALT = dict(z=1.95, y=1.68, s=0.28)               # cobalt square above the front arch
STENCIL = dict(z=-2.00, y=1.84, h=0.40)              # V-31 above the rear arch
DOORS = [0.53, -0.75]                                # cab door, rear-flank door (z centres), both flanks
TAIL_DOOR = dict(x=0.0, y=1.50)
# glazing (armoured panes, true recesses with dark glass)
WINDSCREEN = dict(xs=[0.42, -0.42], w=0.72, h=0.46, depth=0.06)
SIDE_PANE = dict(z=1.36, y=1.86, w=0.56, h=0.36, depth=0.05)
# louvred side vent at the tail, above the rear arch
SIDE_VENT = dict(z=-2.86, y=1.86, w=0.50, h=0.50, depth=0.12)
# nose collar (gunmetal chamfered octagonal frame round the nose face)
COLLAR = dict(y=1.33, w=1.92, h=0.86, c=0.24, wi=1.42, hi=0.50, ci=0.14, z0=3.08, z1=3.34)
# rear end frame (gunmetal) round the tail face
TAILFRAME = dict(z0=-3.31, z1=-3.12, t=0.075)
# roof fittings (kit)
HATCHES = [(0.0, 0.75), (0.0, -0.15)]                # (x, z) roofHatch 0.8 m
RWS = (0.0, -1.22)
ROOF_VENT = (0.0, -2.42)                             # kit vent (engine-deck / AC grille), long axis across
FOIL_BOX = (0.52, -1.72)
MARKERS = {
    'front': [(0.78, 1.33, 3.34)],                   # on the collar's outer cheeks, mirrored
    'side': [(1.0, 1.34, 2.86)],                    # amber side marker on the bonnet flank ahead of the arch, mirrored
    'rear': [(0.78, 1.62, -3.33)],                   # red tail lamps on the end frame, mirrored
    'convoy': [(0.0, 2.36, -3.25)],                  # covered convoy lamp over the tail door
}
