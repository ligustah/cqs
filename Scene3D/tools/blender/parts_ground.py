# Ground-vehicle parts (first used by the V-31 wheeled 4x4, tools/blender/hulls/vehicle.py): road wheel
# with tyre, double-wishbone corner with coil-over, remote weapon station, round roof hatch, armoured
# vehicle door, covered convoy / marker lamp, foil-wrapped sensor box. Every part is at TRUE SIZE, so later
# ground units (the tank chassis, module variants) reuse them unchanged: a heavier unit gets more wheels,
# never bigger hatches or doors.
# Part frame (as every procedural kit part, see lib.py): metres, X width, Y up, Z out of the mounting surface,
# origin at the centre of the mounting face.
#   wheel:      axle along +Z; origin = centre of the INNER (hub) face, the tyre runs z 0 .. width outboard.
#               Mount on a vehicle flank with n = the outboard axle direction (+-X).
#   suspension: mounts on the hull side (tub wall) at the axle height; +Z = outboard, the hub carrier at z = reach;
#               +Y up. Upper / lower wishbones, upright, coil-over to a top mount 0.62 m above the axle, drive shaft.
#   rws:        mounts on the roof (n = +Y of the vehicle, up = forward): gun along +Y of the part frame.
#   roofHatch, vehicleDoor, markerLamp, foilBox: flush wall / roof parts, +Z out.
import math
from lib import rrect, circle, chamfer_rect


def _helix(r, z0, z1, turns, n_per=10):
    pts = []
    N = int(turns * n_per)
    for i in range(N + 1):
        t = i / N
        a = 2 * math.pi * turns * t
        pts.append((r * math.cos(a), r * math.sin(a), z0 + (z1 - z0) * t))
    return pts


# --------------------------------------------------------------------------------------------
def wheel(P, d=1.15, width=0.42, rim_d=0.66, lugs=26):
    R = d / 2
    w = width
    rr = rim_d / 2
    # tyre carcass: a closed lathe ring (bead, sidewall bulge, shoulder, crown) about +Z
    C = R - 0.055          # carcass crown; the lugs stand 0.055 proud of it, so the tread tops are at R
    prof = [(rr - 0.01, 0.03), (rr + 0.04, 0.0), (C - 0.06, 0.0), (C + 0.005, 0.02), (C, 0.06),
            (C, w - 0.06), (C + 0.005, w - 0.02), (C - 0.06, w), (rr + 0.04, w), (rr - 0.01, w - 0.03)]
    P.lathe(prof, 56, closed=True, mat='rubber', sharp=40)
    # deep off-road tread: two staggered rows of chevron lugs plus shoulder blocks on both sidewalls
    for i in range(lugs):
        a = 360.0 * i / lugs
        for row, (zc, off) in enumerate(((w * 0.29, 0.0), (w * 0.71, 0.5))):
            aa = a + off * 360.0 / lugs
            with P.at(rot=(0, 0, aa)):
                P.box((0.07, 0.09, w * 0.36), at=(R - 0.035, 0, zc), rot=(14 if row else -14, 0, 0), mat='rubber', bevel=0.01)
        for zc in (0.035, w - 0.035):
            with P.at(rot=(0, 0, a + 180.0 / lugs)):
                P.box((0.07, 0.075, 0.05), at=(C - 0.03, 0, zc), mat='rubber', bevel=0.008)
    # steel rim: well, dished face set 0.27 m out, bead-lock ring with bolts
    zf = 0.27
    P.lathe([(rr - 0.005, 0.02), (rr - 0.005, w - 0.02), (rr - 0.04, w - 0.03), (rr - 0.04, zf + 0.04), (0.2, zf), (0.2, zf + 0.025),
             (rr - 0.02, zf + 0.065), (rr - 0.02, w - 0.04), (rr - 0.02, 0.04), (rr - 0.03, 0.03)], 40, closed=True, mat='paint2', sharp=35)
    P.lathe([(rr + 0.01, w - 0.035), (rr + 0.05, w - 0.035), (rr + 0.05, w - 0.005), (rr + 0.01, w - 0.005)], 40, closed=True, mat='paint', sharp=40)
    P.bolts([((rr + 0.03) * math.cos(a), (rr + 0.03) * math.sin(a), w - 0.005) for a in [k * 2 * math.pi / 16 for k in range(16)]], r=0.014, h=0.012, mat='steel')
    # hub: flange, eight wheel nuts, centre cap; the drive flange inside
    P.cyl(0.2, 0.03, at=(0, 0, zf + 0.04), n=24, mat='paint2', bevel=0.006)
    P.cyl(0.15, 0.07, at=(0, 0, zf + 0.085), n=24, mat='dark', bevel=0.01)
    P.bolts([(0.12 * math.cos(a), 0.12 * math.sin(a), zf + 0.055) for a in [k * 2 * math.pi / 8 for k in range(8)]], r=0.018, h=0.025, mat='steel')
    P.cyl(0.07, 0.05, at=(0, 0, zf + 0.14), n=16, r2=0.05, mat='steel', bevel=0.006)
    P.cyl(0.13, 0.06, at=(0, 0, 0.03), n=20, mat='dark', bevel=0.008)
    # tyre-pressure line from the hub to the valve (central tyre inflation)
    P.tube([(0.05, 0.03, zf + 0.15), (0.16, 0.12, zf + 0.12), (rr - 0.06, 0.18, zf + 0.07)], 0.009, n=6, fillet=0.03, mat='steel')
    return {'diameter': d, 'width': width, 'axle': [0, 0, 0], 'outer': [0, 0, width],
            'about': f'road wheel: {d:.2f} m deep-tread tyre, {width:.2f} m wide, bead-lock steel rim; axle along +Z, origin = centre of the inner face'}


def suspension(P, reach=0.24, top=0.62):
    """Double-wishbone corner. z = 0 is the hull wall, the upright (hub carrier) at z = reach."""
    # hull brackets for the four wishbone pivots and the damper top mount
    for y in (0.24, -0.2):
        P.box((0.72, 0.12, 0.06), at=(0, y, 0.03), mat='gunmetal', bevel=0.01)
        P.bolts([(sx * 0.3, y, 0.06) for sx in (-1, 1)], r=0.016, h=0.012, mat='steel')
    P.box((0.24, 0.16, 0.1), at=(0, top + 0.05, 0.05), mat='gunmetal', bevel=0.012)
    # wishbones: two tubes from the hull pivots (x +-0.3) to the outer ball joint at the upright
    for (yi, yo) in ((0.24, 0.17), (-0.2, -0.15)):
        for sx in (-1, 1):
            P.tube([(sx * 0.3, yi, 0.07), (0.0, yo, reach - 0.02)], 0.03, n=8, mat='gunmetal')
            P.cyl(0.04, 0.08, at=(sx * 0.3, yi, 0.07), rot=(0, 90, 0), n=10, mat='rubber', bevel=0.0)
        P.cyl(0.045, 0.06, at=(0, yo, reach - 0.02), n=12, mat='dark', bevel=0.008)
    # upright and the hub bearing housing
    P.box((0.14, 0.42, 0.08), at=(0, 0.01, reach + 0.02), mat='gunmetal', bevel=0.015)
    P.cyl(0.11, 0.07, at=(0, 0, reach + 0.04), n=20, mat='dark', bevel=0.01)
    # drive shaft with a CV boot at each end
    P.cyl(0.035, reach, at=(0, 0, reach / 2), n=10, mat='steel', bevel=0.0)
    for zc in (0.05, reach - 0.04):
        P.cyl(0.06, 0.06, at=(0, 0, zc), n=12, r2=0.04, mat='rubber', bevel=0.0)
    # coil-over: lower eye on the lower wishbone, upper eye at the top mount; spring as a helix
    a = (0.0, -0.12, reach * 0.62)
    b = (0.0, top, 0.08)
    import mathutils
    A, B = mathutils.Vector(a), mathutils.Vector(b)
    ax = (B - A)
    L = ax.length
    q = mathutils.Vector((0, 0, 1)).rotation_difference(ax.normalized()).to_matrix().to_4x4()
    M = mathutils.Matrix.Translation(A) @ q
    with P.at(M=M):
        P.cyl(0.035, L * 0.55, at=(0, 0, L * 0.3), n=12, mat='steel', bevel=0.0)          # rod
        P.cyl(0.05, L * 0.5, at=(0, 0, L * 0.72), n=14, mat='dark', bevel=0.006)          # body
        P.cyl(0.075, 0.02, at=(0, 0, L * 0.18), n=16, mat='gunmetal', bevel=0.0)          # lower seat
        P.cyl(0.075, 0.02, at=(0, 0, L * 0.92), n=16, mat='gunmetal', bevel=0.0)          # upper seat
        P.tube(_helix(0.065, L * 0.19, L * 0.91, 6.5, 10), 0.013, n=6, mat='hazard', caps=True)
        P.cyl(0.03, 0.06, at=(0, 0, 0.0), rot=(0, 90, 0), n=10, mat='rubber', bevel=0.0)
    return {'reach': reach, 'top': top, 'hub': [0, 0, reach + 0.075],
            'about': f'double-wishbone corner with a coil-over; hull wall at z = 0, hub at z = {reach + 0.075:.3f}, damper top {top} m above the axle'}


def rws(P, ring=0.72):
    """Small remote weapon station: low turntable, cradle with a short heavy-MG barrel, sensor head, ammo box."""
    R = ring / 2
    P.cyl(R + 0.05, 0.04, at=(0, 0, 0.02), n=32, mat='dark', bevel=0.008)
    P.bolts([((R + 0.02) * math.cos(a), (R + 0.02) * math.sin(a), 0.04) for a in [k * 2 * math.pi / 16 for k in range(16)]], r=0.014, h=0.01, mat='steel')
    P.cyl(R, 0.07, at=(0, 0, 0.075), n=32, mat='paint', bevel=0.012)
    P.cyl(R - 0.03, 0.015, at=(0, 0, 0.115), n=32, mat='rubber', bevel=0.0)
    # turntable housing: chamfered low box
    plan = chamfer_rect(0.56, 0.5, 0.1)
    P.loft([(plan, 0.12), (plan, 0.24), (chamfer_rect(0.5, 0.42, 0.08), 0.29)], closed=False, mat='paint', bevel=0.012)
    # cradle cheeks and the receiver on the trunnion (z 0.34)
    zt = 0.37
    for sx in (-1, 1):
        P.box((0.04, 0.26, 0.18), at=(sx * 0.11, 0.02, zt - 0.03), mat='paint2', bevel=0.01)
    P.box((0.14, 0.46, 0.13), at=(0, 0.03, zt), mat='gunmetal', bevel=0.012)
    P.box((0.1, 0.12, 0.06), at=(0, -0.12, zt + 0.09), mat='gunmetal', bevel=0.008)
    # barrel along +Y with a jacket and a muzzle brake
    y0 = 0.26
    P.cyl(0.032, 0.22, at=(0, y0 + 0.11, zt), rot=(-90, 0, 0), n=12, mat='gunmetal', bevel=0.004)
    P.cyl(0.02, 0.72, at=(0, y0 + 0.22 + 0.36, zt), rot=(-90, 0, 0), n=12, mat='gunmetal', bevel=0.0)
    P.cyl(0.03, 0.08, at=(0, y0 + 0.94 + 0.04, zt), rot=(-90, 0, 0), n=12, mat='gunmetal', bevel=0.004)
    muzzle = y0 + 1.02
    # sensor head on the left (+X) arm: day / thermal sights behind a glass face
    P.box((0.04, 0.12, 0.2), at=(0.17, 0.0, zt - 0.02), mat='paint2', bevel=0.008)
    P.box((0.16, 0.2, 0.15), at=(0.27, 0.04, zt + 0.02), mat='paint', bevel=0.015)
    P.box((0.12, 0.012, 0.06), at=(0.27, 0.145, zt + 0.05), mat='glass', bevel=0.0)
    P.cyl(0.03, 0.012, at=(0.24, 0.145, zt - 0.015), rot=(-90, 0, 0), n=12, mat='glass', bevel=0.0)
    P.box((0.18, 0.04, 0.02), at=(0.27, 0.15, zt + 0.1), mat='dark', bevel=0.004)      # sun hood
    # ammunition box on the right (-X) with its feed chute
    P.box((0.16, 0.26, 0.17), at=(-0.21, -0.02, zt - 0.01), mat='paint2', bevel=0.012)
    P.box((0.15, 0.24, 0.02), at=(-0.21, -0.02, zt + 0.085), mat='dark', bevel=0.004)
    P.tube([(-0.14, -0.02, zt + 0.05), (-0.07, -0.02, zt + 0.07)], 0.025, n=6, mat='dark')
    # smoke dischargers: two small tubes each side at the back
    for sx in (-1, 1):
        for k in range(2):
            P.cyl(0.035, 0.12, at=(sx * (0.2 + 0.075 * k), -0.2, 0.3), rot=(-60, 0, 0), n=10, mat='dark', bevel=0.004)
    return {'ring': ring, 'trunnion': [0, 0.03, zt], 'muzzle': [0, round(muzzle, 3), zt], 'height': round(zt + 0.12, 3),
            'about': 'remote weapon station: 0.72 m ring, heavy-MG barrel along +Y, sensor head (+X), ammo box (-X); mount on the roof with up = forward'}


def roof_hatch(P, d=0.8):
    R = d / 2
    P.cyl(R + 0.1, 0.03, at=(0, 0, 0.015), n=32, mat='paint2', bevel=0.006)
    P.bolts([((R + 0.06) * math.cos(a), (R + 0.06) * math.sin(a), 0.03) for a in [k * 2 * math.pi / 16 for k in range(16)]], r=0.013, h=0.01, mat='steel')
    P.lathe([(R + 0.04, 0.0), (R + 0.04, 0.09), (R + 0.01, 0.11), (R - 0.03, 0.11), (R - 0.03, 0.0)], 32, closed=True, mat='paint', sharp=40)
    # lid: slightly domed plate, a stiffening cross, the hinge block at -Y, a grab handle
    P.lathe([(R - 0.035, 0.09), (R - 0.035, 0.13), (R * 0.6, 0.15), (0.0, 0.16), (0.0, 0.09)], 32, closed=True, mat='paint', sharp=30)
    P.box((d * 0.7, 0.05, 0.02), at=(0, 0, 0.16), mat='paint2', bevel=0.005)
    P.box((0.05, d * 0.7, 0.02), at=(0, 0, 0.16), mat='paint2', bevel=0.005)
    P.box((0.32, 0.1, 0.1), at=(0, -R - 0.02, 0.1), mat='dark', bevel=0.012)
    P.cyl(0.035, 0.36, at=(0, -R - 0.02, 0.13), rot=(0, 90, 0), n=10, mat='steel', bevel=0.0)
    P.tube([(-0.12, R * 0.45, 0.16), (-0.12, R * 0.45, 0.21), (0.12, R * 0.45, 0.21), (0.12, R * 0.45, 0.16)], 0.014, n=8, fillet=0.03, mat='steel')
    # periscope block on the lid
    P.box((0.16, 0.1, 0.07), at=(0, R * 0.05, 0.19), mat='dark', bevel=0.008)
    P.box((0.12, 0.01, 0.035), at=(0, R * 0.05 + 0.052, 0.195), mat='glass', bevel=0.0)
    return {'diameter': d, 'about': f'round armoured roof hatch {d} m with a periscope, hinge at -Y'}


def vehicle_door(P, leaf=(0.9, 1.3), frame=0.05, depth=0.07):
    """Surface-mounted armoured vehicle door: proud frame, leaf with two pressed panels, a small vision
    block, three heavy external hinges on -X, a lever handle on +X. Vehicle scale (not the 1 x 2 m ship door)."""
    lw, lh = leaf
    fw, fh = lw + 2 * frame, lh + 2 * frame
    N = 2
    P.frame(rrect(fw, fh, 0.06, N), rrect(lw + 0.02, lh + 0.02, 0.04, N), 0.0, depth, mat='paint2', bevel=0.01)
    P.prism(rrect(lw, lh, 0.04, N), 0.0, depth - 0.02, bevel=0.01)
    # pressed panels (raised) and the vision block in the upper panel
    P.prism(rrect(lw - 0.16, lh * 0.42, 0.03, N), depth - 0.02, depth, at=(0, -lh * 0.24, 0), mat='paint2', bevel=0.006)
    vy = lh * 0.27
    P.frame(rrect(0.34, 0.24, 0.03, N), rrect(0.24, 0.15, 0.02, N), depth - 0.02, depth + 0.03, at=(0, vy, 0), mat='dark', bevel=0.006)
    P.prism(rrect(0.25, 0.16, 0.02, N), depth - 0.03, depth - 0.005, at=(0, vy, 0), mat='glass', bevel=0.0)
    P.bolts([(x, vy + y, depth + 0.03) for x in (-0.14, 0.14) for y in (-0.09, 0.09)], r=0.01, h=0.008, mat='steel')
    # hinges on -X: knuckle on the frame, strap across the leaf
    for y in (-lh * 0.36, 0.0, lh * 0.36):
        P.cyl(0.035, 0.14, at=(-lw / 2 - frame * 0.4, y, depth + 0.02), rot=(90, 0, 0), n=12, mat='dark', bevel=0.006)
        P.box((0.3, 0.08, 0.02), at=(-lw / 2 + 0.1, y, depth + 0.0), mat='dark', bevel=0.004)
        P.bolts([(-lw / 2 + 0.04, y, depth + 0.01), (-lw / 2 + 0.18, y, depth + 0.01)], r=0.011, h=0.008, mat='steel')
    # lever handle and lock on +X
    hx = lw / 2 - 0.1
    P.box((0.07, 0.24, 0.02), at=(hx, -0.02, depth), mat='dark', bevel=0.005)
    P.tube([(hx, 0.07, depth + 0.01), (hx, 0.07, depth + 0.06), (hx, -0.11, depth + 0.06), (hx, -0.11, depth + 0.01)], 0.014, n=8, fillet=0.025, mat='steel')
    return {'leaf': list(leaf), 'frame': [round(fw, 3), round(fh, 3), depth], 'visionBlock': [0, round(vy, 3), depth],
            'about': f'armoured vehicle door, {lw} x {lh} m leaf, surface-mounted frame; hinges -X, handle +X'}


def marker_lamp(P, w=0.22, h=0.12):
    """Covered convoy / marker lamp: armoured box housing with a hood and side cheeks over a slit lens.
    The runtime light sprite goes at `lens`."""
    P.box((w + 0.04, h + 0.04, 0.02), at=(0, 0, 0.01), mat='dark', bevel=0.004)
    P.box((w, h, 0.06), at=(0, 0, 0.05), mat='dark', bevel=0.008)
    P.box((w - 0.06, h * 0.4, 0.012), at=(0, -0.01, 0.083), mat='lens', bevel=0.0)
    # hood and cheeks (the "cover")
    P.box((w + 0.03, 0.02, 0.08), at=(0, h / 2 + 0.005, 0.09), rot=(12, 0, 0), mat='paint2', bevel=0.005)
    for sx in (-1, 1):
        P.box((0.016, h, 0.05), at=(sx * (w / 2 + 0.004), 0, 0.095), mat='paint2', bevel=0.004)
    P.bolts([(sx * (w / 2 - 0.018), sy * (h / 2 - 0.018), 0.08) for sx in (-1, 1) for sy in (-1, 1)], r=0.007, h=0.005, mat='steel')
    return {'lens': [0, -0.01, 0.09], 'lensSize': [round(w - 0.06, 3), round(h * 0.4, 3)],
            'about': f'covered convoy / marker lamp {w} x {h} m: hooded slit lens; the runtime light goes at `lens`'}


def foil_box(P, s=0.32):
    """Sensor box wrapped in gold MLI foil on a gunmetal plinth (the fleet's foil boxes at vehicle size)."""
    P.box((s + 0.08, s + 0.08, 0.04), at=(0, 0, 0.02), mat='gunmetal', bevel=0.008)
    P.bolts([(sx * (s / 2 + 0.02), sy * (s / 2 + 0.02), 0.04) for sx in (-1, 1) for sy in (-1, 1)], r=0.012, h=0.008, mat='steel')
    P.box((s, s, s), at=(0, 0, 0.04 + s / 2), mat='foil', bevel=0.03, seg=2)
    # tape seams and a small dark sensor window on the front (+Y) face
    P.box((s + 0.006, 0.03, s + 0.006), at=(0, 0, 0.04 + s / 2), mat='foil2', bevel=0.0)
    P.box((0.03, s + 0.006, s + 0.006), at=(0, 0, 0.04 + s / 2), mat='foil2', bevel=0.0)
    P.box((s * 0.4, 0.01, s * 0.25), at=(0, s / 2 + 0.004, 0.04 + s * 0.62), mat='glass', bevel=0.0)
    return {'size': s, 'about': f'{s} m sensor box wrapped in gold MLI foil on a gunmetal plinth'}


PARTS = {
    'wheel': {'build': wheel, 'tex': 1024, 'bake': {'ao': 0.12, 'curv': 0.01, 'panel': (0.5, 0.5, 0.5)},
              'about': 'road wheel 1.15 m with a deep-tread tyre; axle along +Z, origin = centre of the inner face'},
    'suspension': {'build': suspension, 'tex': 512, 'bake': {'ao': 0.1, 'curv': 0.01}},
    'rws': {'build': rws, 'tex': 512, 'bake': {'ao': 0.1, 'curv': 0.008, 'panel': (0.3, 0.3, 0.3)}},
    'roofHatch': {'build': roof_hatch, 'tex': 512, 'bake': {'ao': 0.08, 'curv': 0.008, 'panel': (0.5, 0.5, 0.5)}},
    'vehicleDoor': {'build': vehicle_door, 'tex': 512, 'bake': {'ao': 0.08, 'curv': 0.008, 'panel': (0.6, 0.6, 0.6)}},
    'markerLamp': {'build': marker_lamp, 'tex': 256, 'bake': {'ao': 0.04, 'curv': 0.005}},
    'foilBox': {'build': foil_box, 'tex': 256, 'bake': {'ao': 0.05, 'curv': 0.006}},
}
