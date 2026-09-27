# Weapons: twin turret (S/M/L), point-defence mount, VLS missile pod, spinal railgun (tileable
# barrel segment + muzzle cap), bow torpedo door. Part frame: X width, Y up, Z out of the hull
# (metres); turrets and mounts stand on the hull (+Z) with their guns trained along +Y, so a
# placement with `up` toward the bow trains them forward.
import math
from lib import rrect, circle, chamfer_rect, basis
from parts_human import door, _bolt_ring


def _barrel(P, L, r0, at, n=20, mat='gunmetal'):
    """Gun barrel along +Y from `at` (breech face): sleeve, taper, bands, muzzle collar, bore."""
    f = [(0.0, 0.0), (1.30, 0.0), (1.30, 0.10), (1.02, 0.115), (0.98, 0.35), (1.07, 0.355), (1.07, 0.38), (0.93, 0.385),
         (0.82, 0.70), (0.9, 0.705), (0.9, 0.725), (0.8, 0.73), (0.74, 0.93), (0.9, 0.935), (0.9, 0.99), (0.86, 1.0),
         (0.46, 1.0), (0.46, 0.965), (0.0, 0.965)]
    prof = [(r * r0, z * L) for r, z in f]
    P.lathe(prof, n, at=at, rot=(-90, 0, 0), mat=mat, sharp=40)


def turret(P, D=8.0, Lb=14.0):
    hb = 0.12 * D                       # barbette height
    h = max(0.36 * D, 2.9)              # gun house height
    hv = max(0.6 * h, 2.55)             # vertical part of the house walls (the access door sits on it)
    w, f, b = 0.86 * D, 0.5 * D, -0.52 * D
    c = 0.18 * D
    z0 = hb
    # barbette ring, bolted flange, the dark training gap
    P.cyl(0.5 * D + 0.06 * D, 0.03 * D, at=(0, 0, 0.015 * D), n=48, mat='paint2', bevel=0.01 * D)
    P.cyl(0.5 * D, hb - 0.03 * D, at=(0, 0, 0.03 * D + (hb - 0.03 * D) / 2), n=48, bevel=0.008 * D)
    P.cyl(0.48 * D, 0.05, at=(0, 0, hb + 0.02), n=48, mat='rubber', bevel=0.0)
    nb = int(2 * math.pi * 0.53 * D / 0.45)
    P.bolts([(0.53 * D * math.cos(2 * math.pi * i / nb), 0.53 * D * math.sin(2 * math.pi * i / nb), 0.03 * D) for i in range(nb)], r=0.035, h=0.025, mat='steel')
    # gun house: armoured faceted box, vertical walls then a sloped roof band
    plan0 = [(w / 2, f - c), (w / 2 - c * 0.8, f), (-w / 2 + c * 0.8, f), (-w / 2, f - c), (-w / 2, b + c * 0.3), (-w / 2 + c * 0.3, b), (w / 2 - c * 0.3, b), (w / 2, b + c * 0.3)]
    si, fi, bi = 0.09 * D, 0.16 * D, 0.04 * D
    plan1 = [(x - math.copysign(si, x), y - (fi if y > 0 else -bi)) for x, y in plan0]
    P.loft([(plan0, z0 + 0.04), (plan0, z0 + hv), (plan1, z0 + h)], closed=False, bevel=0.012 * D, seg=2)
    # rear bustle, appliqué armour on the port side and the glacis
    P.box((0.6 * w, 0.14 * D, 0.55 * h), at=(0, b - 0.06 * D, z0 + 0.3 * h), bevel=0.01 * D)
    P.box((0.03 * D, 0.45 * D, 0.5 * hv), at=(-w / 2 - 0.012 * D, 0.02 * D, z0 + 0.45 * hv), mat='paint2', bevel=0.006 * D)
    # mantlet, blast boots and the barrels
    zt = z0 + 0.45 * h
    sb = 0.26 * D
    rb = 0.045 * D
    mw, mh = sb + 0.3 * D, 0.34 * D
    # gun shield: a half drum on the trunnion axis, with cheek plates
    P.lathe([(mh / 2, -mw / 2), (mh / 2, mw / 2)], 24, at=(0, f - 0.02 * D, zt), rot=(0, 90, 0), a0=0, a1=180, mat='paint', sharp=30)
    for sx in (-1, 1):
        P.cyl(mh / 2 + 0.01 * D, 0.03 * D, at=(sx * mw / 2, f - 0.02 * D, zt), rot=(0, 90, 0), n=24, mat='paint2', bevel=0.006 * D)
    P.box((mw, 0.04 * D, mh * 0.2), at=(0, f - 0.02 * D + mh * 0.35, zt + mh * 0.34), rot=(-35, 0, 0), mat='paint2', bevel=0.006 * D)
    for sx in (-1, 1):
        x = sx * sb / 2
        P.cyl(rb * 1.6, 0.08 * D, at=(x, f - 0.02 * D + mh / 2 + 0.03 * D, zt), rot=(-90, 0, 0), n=20, mat='rubber', bevel=0.004 * D)
        _barrel(P, Lb, rb, (x, f - 0.02 * D + mh / 2 - 0.02 * D, zt))
    # sighting blister (optical hood with a glass slit) and a second periscope head
    rs = 0.075 * D
    bx, by = -w / 2 + 0.2 * D, 0.02 * D
    P.cyl(rs, 0.05 * D, at=(bx, by, z0 + h + 0.02 * D), n=20, mat='paint2', bevel=0.004 * D)
    P.lathe([(rs, 0.0)] + [(rs * math.cos(t), rs * 0.8 * math.sin(t)) for t in [k * math.pi / 10 for k in range(1, 5)]] + [(0, rs * 0.8)], 20, at=(bx, by, z0 + h + 0.045 * D), mat='paint', sharp=30)
    P.box((rs * 1.3, 0.02 * D, rs * 0.35), at=(bx, by + rs * 0.93, z0 + h + 0.045 * D + rs * 0.25), mat='glass', bevel=0.0)
    P.box((0.05 * D, 0.06 * D, 0.05 * D), at=(w / 2 - 0.2 * D, 0.05 * D, z0 + h + 0.02 * D), mat='dark', bevel=0.005 * D)
    P.box((0.035 * D, 0.01 * D, 0.015 * D), at=(w / 2 - 0.2 * D, 0.081 * D, z0 + h + 0.03 * D), mat='glass', bevel=0.0)
    # roof: crew hatch (0.9 m, fixed size), vent louvres (fixed size) on the rear
    rx, ry = 0.12 * D, -0.22 * D
    P.cyl(0.52, 0.12, at=(rx, ry, z0 + h + 0.06), n=20, mat='paint2', bevel=0.02)
    P.cyl(0.45, 0.08, at=(rx, ry, z0 + h + 0.14), n=20, bevel=0.015)
    P.cyl(0.05, 0.3, at=(rx, ry - 0.5, z0 + h + 0.14), rot=(0, 90, 0), n=10, mat='dark', bevel=0.0)
    for i, x in enumerate((-0.6, 0.6)):
        P.box((0.9, 0.08, 0.55), at=(x * min(1.0, 0.15 * D), b - 0.13 * D - 0.04, z0 + 0.35 * h), mat='dark', bevel=0.01)
        for k in range(4):
            P.box((0.84, 0.05, 0.03), at=(x * min(1.0, 0.15 * D), b - 0.13 * D - 0.09, z0 + 0.35 * h - 0.2 + k * 0.13), rot=(30, 0, 0), mat='paint2', bevel=0.0)
    # access door (the shared 1 x 2 m crew door) on the starboard (+X) wall
    dy = b + 0.3 * D if D > 5 else (b + f) / 2
    with P.at(M=basis(origin=(w / 2, dy, z0 + 1.3), x=(0, 1, 0), y=(0, 0, 1), z=(1, 0, 0))):
        door(P)
    # grab rails up the starboard wall next to the door (rungs), fixed human size
    for k in range(int((hv - 0.4) / 0.3)):
        P.cyl(0.016, 0.45, at=(w / 2 + 0.12, dy - 1.1, z0 + 0.4 + k * 0.3), rot=(90, 0, 0), n=6, mat='steel', bevel=0.0)
    # roof plate seams (dark strips), lifting eyes, appliqué on the starboard wall forward of the door
    for y in (-0.3 * D, 0.05 * D):
        P.box((w - 2 * si - 0.1 * D, 0.012 * D + 0.02, 0.01), at=(0, y, z0 + h + 0.004), mat='dark', bevel=0.0)
    P.box((0.012 * D + 0.02, 0.36 * D, 0.01), at=(-0.05 * D, -0.12 * D, z0 + h + 0.004), mat='dark', bevel=0.0)
    for sx in (-1, 1):
        for sy in (-1, 1):
            P.box((0.03 * D, 0.06 * D, 0.03 * D), at=(sx * (w / 2 - si - 0.06 * D), sy * 0.25 * D - 0.1 * D, z0 + h + 0.015 * D), mat='dark', bevel=0.004 * D)
    if D > 5:
        P.box((0.03 * D, 0.28 * D, 0.5 * hv), at=(w / 2 + 0.012 * D, 0.2 * D, z0 + 0.45 * hv), mat='paint2', bevel=0.006 * D)
    return {'base': D, 'barrel': Lb, 'barrelSpacing': round(sb, 3), 'barrelRadius': round(rb, 3),
            'trunnion': [0, round(f - 0.02 * D, 3), round(zt, 3)], 'muzzle': [0, round(f - 0.04 * D + mh / 2 + Lb, 3), round(zt, 3)],
            'height': round(z0 + h, 3),
            'about': 'twin gun turret on a barbette, guns along +Y; 1 x 2 m access door on the +X wall'}


def pdc(P, size=2.0):
    P.cyl(0.62, 0.12, at=(0, 0, 0.06), n=24, mat='dark', bevel=0.02)
    P.bolts([(0.54 * math.cos(a), 0.54 * math.sin(a), 0.12) for a in [i * math.pi / 6 for i in range(12)]], r=0.02, h=0.015, mat='steel')
    P.cyl(0.5, 0.3, at=(0, 0, 0.27), n=24, bevel=0.02)
    P.cyl(0.46, 0.03, at=(0, 0, 0.435), n=24, mat='rubber', bevel=0.0)
    for sx in (-1, 1):
        P.prism(rrect(0.5, 0.9, 0.2, 3), -0.04, 0.04, at=(sx * 0.34, 0, 0.85), rot=(0, 90, 0), bevel=0.012)
        P.cyl(0.12, 0.06, at=(sx * 0.39, 0, 0.95), rot=(0, 90, 0), n=16, mat='dark', bevel=0.01)
    P.box((0.72, 0.5, 0.12), at=(0, 0, 0.5), bevel=0.02)
    with P.at(at=(0, 0, 0.95), rot=(22, 0, 0)):
        P.box((0.56, 0.9, 0.42), at=(0, 0.1, 0), bevel=0.025)
        P.box((0.4, 0.5, 0.06), at=(0, 0.05, 0.24), mat='paint2', bevel=0.012)
        P.cyl(0.16, 0.2, at=(0, 0.62, 0), rot=(-90, 0, 0), n=16, mat='dark', bevel=0.015)
        for k in range(6):
            a = k * math.pi / 3
            P.cyl(0.03, 1.15, at=(0.075 * math.cos(a), 0.62 + 0.575 + 0.1, 0.075 * math.sin(a)), rot=(-90, 0, 0), n=8, mat='gunmetal', bevel=0.0)
        for y in (0.95, 1.5):
            P.cyl(0.13, 0.05, at=(0, y, 0), rot=(-90, 0, 0), n=16, mat='gunmetal', bevel=0.008)
        P.cyl(0.04, 1.2, at=(0, 1.2, 0), rot=(-90, 0, 0), n=8, mat='gunmetal', bevel=0.0)
        # ammunition box (-X) with its feed chute, sensor pod (+X)
        P.box((0.26, 0.5, 0.36), at=(-0.53, -0.05, 0.0), bevel=0.02)
        P.tube([(-0.4, 0.1, 0.12), (-0.33, 0.2, 0.2), (-0.2, 0.3, 0.2)], 0.05, n=8, mat='dark')
        P.box((0.18, 0.3, 0.22), at=(0.5, 0.2, 0.05), mat='paint2', bevel=0.015)
        P.cyl(0.06, 0.02, at=(0.5, 0.355, 0.08), rot=(-90, 0, 0), n=14, mat='glass', bevel=0.0)
    return {'trunnion': [0, 0, 0.95], 'elevation': 22, 'about': 'rotary point-defence mount, barrels along +Y elevated 22 degrees'}


def missile_pod(P, cols=2, rows=4, pitch=1.2, height=0.5):
    W, L = cols * pitch + 0.5, rows * pitch + 0.5
    P.loft([(chamfer_rect(W + 0.3, L + 0.3, 0.2), 0.0), (chamfer_rect(W, L, 0.15), height - 0.05), (chamfer_rect(W - 0.06, L - 0.06, 0.12), height)], closed=False, bevel=0.02)
    P.frame(chamfer_rect(W - 0.08, L - 0.08, 0.12), chamfer_rect(W - 0.26, L - 0.26, 0.05), height, height + 0.006, mat='hazard', bevel=0.0)
    for i in range(cols):
        for j in range(rows):
            x = (i - (cols - 1) / 2) * pitch
            y = (j - (rows - 1) / 2) * pitch
            P.frame(rrect(1.02, 1.02, 0.1, 2), rrect(0.96, 0.96, 0.07, 2), height - 0.01, height + 0.01, at=(x, y, 0), mat='rubber', bevel=0.0)
            P.prism(rrect(0.94, 0.94, 0.07, 2), height, height + 0.05, at=(x, y, 0), bevel=0.01)
            for k in (-0.22, 0.22):
                P.box((0.7, 0.07, 0.04), at=(x, y + k, height + 0.07), mat='paint2', bevel=0.0)
            P.cyl(0.035, 0.7, at=(x, y - 0.5, height + 0.04), rot=(0, 90, 0), n=8, mat='dark', bevel=0.0)
            P.bolts([(x + sx * 0.4, y + sx * 0.4, height + 0.05) for sx in (-1, 1)], r=0.018, h=0.012, mat='steel')
    # exhaust uptake between the columns: a grated strip
    P.box((0.16, L - 0.6, 0.02), at=(0, 0, height + 0.01), mat='dark', bevel=0.0)
    for k in range(int((L - 0.7) / 0.12)):
        P.box((0.14, 0.03, 0.025), at=(0, -L / 2 + 0.4 + k * 0.12, height + 0.02), mat='steel', bevel=0.0)
    return {'cells': [cols, rows], 'pitch': pitch, 'about': 'VLS block, 2 x 4 cells at 1.2 m pitch (X by Y)'}


def _rail_section(P, y0, y1, zb, gap, rw, rh):
    """Continuous members of the railgun from y0 to y1 (rails, insulators, keel, cable trays, pipes)."""
    L, yc = y1 - y0, (y0 + y1) / 2
    for sx in (-1, 1):
        x = sx * (gap / 2 + rw / 2)
        P.box((rw, L, rh), at=(x, yc, zb), mat='gunmetal', bevel=0.03)
        P.box((0.1, L, rh * 0.8), at=(sx * (gap / 2 + 0.04), yc, zb), mat='copper', bevel=0.0)
        # cable tray with three copper cables
        tx = sx * (gap / 2 + rw + 0.95)
        P.box((0.42, L, 0.08), at=(tx, yc, zb - 0.55), mat='dark', bevel=0.0)
        P.box((0.04, L, 0.3), at=(tx + sx * 0.19, yc, zb - 0.4), mat='dark', bevel=0.0)
        for k in range(3):
            P.cyl(0.06, L, at=(tx - sx * 0.12 + sx * k * 0.12, yc, zb - 0.45), rot=(90, 0, 0), n=8, mat='copper', bevel=0.0, caps=False)
    for sz in (-1, 1):
        P.box((gap, L, 0.4), at=(0, yc, zb + sz * (rh / 2 - 0.2 + 0.2)), mat='ceramic', bevel=0.0)
    P.box((gap + 2 * rw - 0.4, L, 0.8), at=(0, yc, zb - rh / 2 - 0.4 - 0.3), mat='paint2', bevel=0.03)
    for sx in (-1, 1):
        P.cyl(0.14, L, at=(sx * 0.7, yc, zb + rh / 2 + 0.75), rot=(90, 0, 0), n=10, mat='steel', bevel=0.0, caps=False)


def _clamp(P, y, zb, outer, inner, t, mat='paint'):
    P.frame(outer, inner, -t / 2, t / 2, at=(0, y, zb), rot=(90, 0, 0), mat=mat, bevel=0.03)


def railgun(P, part='segment', length=10.0, gap=2.4, rw=0.7, rh=1.8, cap=4.0):
    zb = 3.0
    ow, oh = gap + 2 * rw + 0.9, rh + 1.6
    outer = chamfer_rect(ow, oh, 0.7)
    inner = chamfer_rect(gap + 2 * rw + 0.02, rh + 0.82, 0.12)
    if part == 'segment':
        y0, y1 = -length / 2, length / 2
        _rail_section(P, y0, y1, zb, gap, rw, rh)
        n = int(round(length / 1.25))
        for k in range(n):
            y = y0 + 0.625 + k * 1.25
            if abs(abs(y) - length / 4) < 0.7:
                continue
            _clamp(P, y, zb, outer, inner, 0.3)
        # capacitor bands every 5 m: heavy collar, capacitor banks and busbars on both flanks
        for yb in (-length / 4, length / 4):
            _clamp(P, yb, zb, chamfer_rect(ow + 0.6, oh + 0.6, 1.1), inner, 1.3, mat='paint2')
            for sx in (-1, 1):
                x = sx * (ow / 2 + 0.75)
                P.box((1.3, 1.5, 0.2), at=(x, yb, zb - 1.0), mat='paint2', bevel=0.03)
                for i in range(2):
                    for j in range(3):
                        P.cyl(0.24, 1.5, at=(x + (i - 0.5) * 0.56, yb + (j - 1) * 0.5, zb - 0.15), n=14, mat='dark', bevel=0.02)
                        P.cyl(0.1, 0.1, at=(x + (i - 0.5) * 0.56, yb + (j - 1) * 0.5, zb + 0.65), n=10, mat='copper', bevel=0.0)
                P.box((1.3, 0.3, 0.1), at=(sx * (ow / 2 + 0.3), yb, zb + 0.72), mat='copper', bevel=0.0)
            P.box((0.3, 1.0, 0.3), at=(0, yb, zb + oh / 2 + 0.45), mat='dark', bevel=0.02)
        # saddle on the hull mid-segment (with the bands every 5 m the saddles fall between them)
        P.prism([(2.4, 0.0), (1.6, zb - oh / 2 + 0.2), (-1.6, zb - oh / 2 + 0.2), (-2.4, 0.0)], -0.5, 0.5, at=(0, 0.0, 0), rot=(90, 0, 0), bevel=0.04)
        return {'pitch': length, 'axis': '+Y', 'bore': {'centre': [0, 0, zb], 'width': gap, 'height': rh},
                'about': 'spinal railgun barrel segment, y -5..+5, tiles end to end at 10 m pitch'}
    # muzzle cap: joint at y = 0, muzzle face at y = cap
    _rail_section(P, 0.0, cap - 0.3, zb, gap, rw, rh)
    for y in (0.625, 1.875):
        _clamp(P, y, zb, outer, inner, 0.3)
    P.loft([(chamfer_rect(ow + 0.3, oh + 0.3, 1.0), 0.0), (chamfer_rect(ow + 0.9, oh + 0.9, 1.2), 1.0),
            (chamfer_rect(ow + 0.9, oh + 0.9, 1.2), 1.5), (chamfer_rect(gap + 0.5, rh + 0.5, 0.25), 1.5),
            (chamfer_rect(gap, rh, 0.1), 1.2), (chamfer_rect(gap, rh, 0.1), 0.0)], closed=True, at=(0, cap - 1.5, zb), rot=(-90, 0, 0), bevel=0.04)
    for sx in (-1, 1):
        for k in range(3):
            P.box((0.08, 0.5, 0.7), at=(sx * (ow / 2 + 0.47), cap - 1.1, zb - 0.9 + k * 0.9), mat='dark', bevel=0.0)
    P.prism([(2.4, 0.0), (1.6, zb - oh / 2 + 0.2), (-1.6, zb - oh / 2 + 0.2), (-2.4, 0.0)], -0.5, 0.5, at=(0, 1.25, 0), rot=(90, 0, 0), bevel=0.04)
    return {'axis': '+Y', 'joint': [0, 0, 0], 'muzzle': [0, cap, zb], 'bore': {'centre': [0, 0, zb], 'width': gap, 'height': rh},
            'about': 'railgun muzzle cap; joint face at y = 0 (butts on a segment end), muzzle face at y = +4'}


def torpedo_door(P, d=3.0, depth=0.45):
    R = d / 2
    n = 32
    P.loft([(circle(R + 0.55, n), 0.0), (circle(R + 0.42, n), depth), (circle(R + 0.08, n), depth), (circle(R + 0.08, n), 0.0)], bevel=0.02)
    P.frame(circle(R + 0.4, n), circle(R + 0.22, n), depth, depth + 0.006, mat='hazard', bevel=0.0)
    for sx in (-1, 1):
        half = [(sx * 0.02 + sx * abs(R * math.cos(t)) * 1.0, R * math.sin(t)) for t in [math.pi / 2 - math.pi * k / 16 for k in range(17)]]
        pts = [(x, y) for x, y in half]
        if sx < 0:
            pts = list(reversed(pts))
        P.prism(pts, 0.05, 0.18, bevel=0.015)
        for y in (-0.7, 0.0, 0.7):
            wlen = math.sqrt(max(0.01, R * R - y * y)) - 0.25
            P.box((wlen, 0.12, 0.08), at=(sx * (0.12 + wlen / 2), y, 0.22), mat='paint2', bevel=0.012)
        for y in (-0.8, 0.8):
            P.cyl(0.1, 0.4, at=(sx * (R + 0.05), y, 0.28), rot=(90, 0, 0), n=12, mat='dark', bevel=0.01)
    for k in range(7):
        P.box((0.14, 0.2, 0.06), at=(0, -1.2 + k * 0.4, 0.2), mat='dark', bevel=0.01)
    P.bolts([(x, y, depth) for x, y in circle(R + 0.3, 36)], r=0.025, h=0.018, mat='steel')
    return {'diameter': d, 'about': 'bow launch door, two leaves split on x = 0'}


PARTS = {
    'turret': {'build': turret, 'tex': 1024, 'sizes': {'S': {'D': 4.0, 'Lb': 6.0}, 'M': {'D': 8.0, 'Lb': 14.0}, 'L': {'D': 14.0, 'Lb': 24.0, 'tex': 2048}},
               'bake': {'ao': 0.5, 'curv': 0.02, 'panel': (1.8, 1.2, 1.8)}},
    'pdc': {'build': pdc, 'tex': 512, 'bake': {'ao': 0.15, 'curv': 0.012}},
    'missilePod': {'build': missile_pod, 'tex': 1024, 'bake': {'ao': 0.15, 'curv': 0.012, 'panel': (1.2, 1.2, 1.2)}},
    'railgun': {'build': railgun, 'tex': 1024, 'sizes': {'segment': {'part': 'segment'}, 'muzzle': {'part': 'muzzle'}},
                'bake': {'ao': 0.6, 'curv': 0.03, 'panel': (2.5, 1.25, 2.0)}},
    'torpedoDoor': {'build': torpedo_door, 'tex': 512, 'bake': {'ao': 0.2, 'curv': 0.015}},
}
