# Human-scale reference parts: door, airlock, port, pane, cargoHatch, rail, ladder, rcs,
# antenna, dome, floodlight, container. Part frame: X width, Y up, Z out of the hull (metres),
# origin at the centre of the mounting face (see lib.py).
import math
from lib import rrect, circle, chamfer_rect


def _bolt_ring(pts, pitch):
    """Points spaced ~pitch along a closed outline."""
    out = []
    n = len(pts)
    segs = [(pts[i], pts[(i + 1) % n]) for i in range(n)]
    L = sum(math.dist(a, b) for a, b in segs)
    k = max(4, int(L / pitch))
    step = L / k
    d = 0.0
    acc = 0.0
    it = iter(segs)
    a, b = next(it)
    sl = math.dist(a, b)
    for i in range(k):
        t = i * step
        while t > acc + sl:
            acc += sl
            a, b = next(it)
            sl = math.dist(a, b)
        u = (t - acc) / sl if sl else 0
        out.append((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u))
    return out


# --------------------------------------------------------------------------------------------
def door(P, leaf=(1.0, 2.0), frame=(1.4, 2.4), depth=0.3):
    lw, lh = leaf
    fw, fh = frame
    iw, ih = lw + 0.08, lh + 0.08          # clear opening round the leaf (seal gap)
    N = 3
    # armoured frame: sloped outer face, flat top band, straight inner wall down to the leaf
    P.loft([(rrect(fw, fh, 0.16, N), 0.0), (rrect(fw - 0.12, fh - 0.12, 0.12, N), depth),
            (rrect(iw, ih, 0.07, N), depth), (rrect(iw, ih, 0.07, N), 0.0)], bevel=0.012)
    # rubber seal and the leaf
    P.frame(rrect(iw, ih, 0.07, N), rrect(lw - 0.02, lh - 0.02, 0.05, N), 0.0, 0.07, mat='rubber', bevel=0.004)
    P.prism(rrect(lw, lh, 0.05, N), 0.0, 0.1, bevel=0.01)
    # leaf: lower pressure panel, upper panel round the viewport, rib between
    P.prism(rrect(lw - 0.16, 1.02, 0.04, N), 0.1, 0.13, at=(0, -0.41, 0), mat='paint2', bevel=0.008)
    vp_y = 0.5
    P.frame(rrect(lw - 0.16, 0.72, 0.04, N), rrect(0.24, 0.34, 0.07, N, cy=vp_y - 0.52), 0.1, 0.13, at=(0, 0.52, 0), mat='paint2', bevel=0.008)
    P.frame(rrect(0.34, 0.44, 0.1, N), rrect(0.24, 0.34, 0.07, N), 0.13, 0.155, at=(0, vp_y, 0), mat='dark', bevel=0.006)
    P.prism(rrect(0.25, 0.35, 0.07, N), 0.1, 0.118, at=(0, vp_y, 0), mat='glass', bevel=0.0)
    P.bolts([(x, vp_y + y, 0.155) for x in (-0.135, 0.135) for y in (-0.185, 0.185)], r=0.011, h=0.008, mat='steel')
    # lever handle (steel D-handle on a dark back plate), opening side +X
    hx = lw / 2 - 0.13
    P.box((0.08, 0.34, 0.02), at=(hx, 0.0, 0.14), mat='dark', bevel=0.006)
    P.tube([(hx, 0.12, 0.15), (hx, 0.12, 0.21), (hx, -0.12, 0.21), (hx, -0.12, 0.15)], 0.017, n=10, fillet=0.035, mat='steel')
    # hinges on -X: three knuckles on the leaf edge with straps on the leaf
    for y in (-0.7, 0.0, 0.7):
        P.cyl(0.035, 0.18, at=(-lw / 2 - 0.005, y, 0.12), rot=(90, 0, 0), n=12, mat='dark', bevel=0.006)
        P.box((0.26, 0.09, 0.016), at=(-lw / 2 + 0.12, y, 0.108), mat='dark', bevel=0.004)
        P.bolts([(-lw / 2 + 0.08, y, 0.116), (-lw / 2 + 0.2, y, 0.116)], r=0.012, h=0.008, mat='steel')
    # frame hardware: bolts on the top band, a keypad and an indicator lens, a label plate
    band = rrect(fw - 0.12 - (fw - 0.12 - iw) / 2, fh - 0.12 - (fh - 0.12 - ih) / 2, 0.1, 3)
    P.bolts([(x, y, depth) for x, y in _bolt_ring(band, 0.34)], r=0.014, h=0.01, mat='steel')
    kx = (fw - 0.12 + iw) / 4
    P.box((0.07, 0.14, 0.03), at=(kx, 0.05, depth + 0.012), mat='dark', bevel=0.005)
    P.cyl(0.012, 0.012, at=(kx, 0.15, depth + 0.004), n=10, mat='lens', bevel=0.0)
    P.box((0.36, 0.05, 0.008), at=(0, (fh - 0.12 + ih) / 4, depth + 0.002), mat='dark', bevel=0.002)
    return {'leaf': list(leaf), 'frame': [fw, fh, depth], 'about': 'crew door, hinges on -X, handle on +X'}



def airlock(P, hatch=(1.8, 2.6), collar=0.8):
    hw, hh = hatch
    N = 3
    ow, oh = hw + 0.5, hh + 0.5
    # collar: flared foot on the hull, straight tunnel, face band, recessed opening wall
    P.loft([(rrect(ow + 0.3, oh + 0.3, 0.45, N), 0.0), (rrect(ow + 0.04, oh + 0.04, 0.34, N), 0.14),
            (rrect(ow, oh, 0.32, N), collar), (rrect(hw + 0.1, hh + 0.1, 0.2, N), collar),
            (rrect(hw + 0.1, hh + 0.1, 0.2, N), collar - 0.14), (rrect(hw + 0.1, hh + 0.1, 0.2, N), 0.0)], bevel=0.02)
    # stiffener rings round the tunnel
    for z in (0.34, 0.56):
        P.frame(rrect(ow + 0.08, oh + 0.08, 0.36, N), rrect(ow - 0.02, oh - 0.02, 0.31, N), z - 0.035, z + 0.035, mat='paint2', bevel=0.01)
    # hazard band on the face and the hatch leaf
    P.frame(rrect(ow - 0.05, oh - 0.05, 0.3, N), rrect(hw + 0.22, hh + 0.22, 0.24, N), collar, collar + 0.006, mat='hazard', bevel=0.0)
    lz = collar - 0.14
    P.prism(rrect(hw, hh, 0.18, N), lz, lz + 0.1, bevel=0.015)
    P.prism(rrect(hw - 0.3, hh - 0.3, 0.12, N), lz + 0.1, lz + 0.13, mat='paint2', bevel=0.01)
    # locking dogs on the face band, over the leaf edge
    for x, y, r in [(0, hh / 2 + 0.02, 0), (0, -hh / 2 - 0.02, 0), (hw / 2 + 0.02, 0.6, 90), (hw / 2 + 0.02, -0.6, 90),
                    (-hw / 2 - 0.02, 0.6, 90), (-hw / 2 - 0.02, -0.6, 90), (hw / 2 - 0.25, hh / 2 + 0.02, 0), (-hw / 2 + 0.25, -hh / 2 - 0.02, 0)]:
        P.box((0.22, 0.12, 0.06), at=(x, y, lz + 0.13), rot=(0, 0, r), mat='dark', bevel=0.012)
    # hand wheel + viewport
    P.lathe([(0.2, 0.0), (0.24, 0.02), (0.26, 0.0), (0.24, -0.02)], 16, at=(0, -0.25, lz + 0.23), closed=True, mat='steel', sharp=80)
    for a in (0, 120, 240):
        P.box((0.2, 0.03, 0.02), at=(0.11 * math.cos(math.radians(a)), -0.25 + 0.11 * math.sin(math.radians(a)), lz + 0.2), rot=(0, 0, a), mat='steel', bevel=0.004)
    P.cyl(0.05, 0.1, at=(0, -0.25, lz + 0.17), n=12, mat='dark')
    P.frame(circle(0.2, 16), circle(0.13, 16), lz + 0.13, lz + 0.16, at=(0, 0.55, 0), mat='dark', bevel=0.006)
    P.cyl(0.135, 0.02, at=(0, 0.55, lz + 0.12), n=16, mat='glass', bevel=0.0)
    # grab handles on the tunnel sides, two lamps on the face, a bolt ring on the foot
    for sx in (-1, 1):
        x = sx * (ow / 2 + 0.01)
        P.tube([(x, 0.5, 0.25), (x + sx * 0.1, 0.5, 0.3), (x + sx * 0.1, -0.5, 0.3), (x, -0.5, 0.25)], 0.02, n=8, fillet=0.06, mat='steel')
        P.box((0.14, 0.1, 0.08), at=(sx * (hw / 2 + 0.25), hh / 2 + 0.2, collar + 0.04), mat='dark', bevel=0.01)
        P.box((0.1, 0.06, 0.012), at=(sx * (hw / 2 + 0.25), hh / 2 + 0.2, collar + 0.086), mat='lens', bevel=0.0)
    P.bolts([(x, y, 0.07) for x, y in _bolt_ring(rrect(ow + 0.17, oh + 0.17, 0.4, 3), 0.45)], r=0.018, h=0.014, normal=(0, 0, 1), mat='steel')
    return {'hatch': list(hatch), 'collar': collar, 'about': 'airlock hatch on a 0.8 m collar'}


def port(P, glass=1.0, frame=1.4, depth=0.2):
    N = 4
    g = glass
    P.loft([(rrect(frame, frame, 0.34, N), 0.0), (rrect(frame - 0.1, frame - 0.1, 0.3, N), depth),
            (rrect(g + 0.08, g + 0.08, 0.2, N), depth), (rrect(g + 0.02, g + 0.02, 0.17, N), 0.04),
            (rrect(g + 0.02, g + 0.02, 0.17, N), 0.0)], bevel=0.012)
    P.prism(rrect(g + 0.04, g + 0.04, 0.18, N), 0.0, 0.05, mat='glass', bevel=0.0)
    # inner clamp ring (dark) and sun brow over the top
    P.frame(rrect(g + 0.1, g + 0.1, 0.21, N), rrect(g + 0.0, g + 0.0, 0.16, N), 0.05, 0.075, mat='dark', bevel=0.005)
    P.loft([([(0.62, 0.0), (-0.62, 0.0), (-0.55, 0.12), (0.55, 0.12)], depth), ([(0.62, 0.0), (-0.62, 0.0), (-0.55, 0.08), (0.55, 0.08)], depth + 0.16)],
           closed=False, at=(0, frame / 2 - 0.12, 0), bevel=0.01)
    P.bolts([(x, y, depth) for x, y in _bolt_ring(rrect(frame - 0.28, frame - 0.28, 0.25, 3), 0.22)], r=0.015, h=0.01, mat='steel')
    return {'glass': [g, g], 'frame': [frame, frame, depth], 'about': 'window port, 1.0 m glass, round corners'}


def pane(P, glass=(1.0, 1.2), mull=0.12, depth=0.16):
    gw, gh = glass
    W, H = gw + mull, gh + mull
    # back plate, glass, mullion grid (half mullions on every edge so modules tile edge to edge)
    P.box((W, H, 0.04), at=(0, 0, 0.02), mat='dark', bevel=0.0)
    P.box((gw + 0.02, gh + 0.02, 0.03), at=(0, 0, 0.055), mat='glass', bevel=0.0)
    m = mull / 2
    for sx in (-1, 1):
        P.prism([(m / 2, H / 2), (-m / 2, H / 2), (-m / 2, -H / 2), (m / 2, -H / 2)], 0.0, depth, at=(sx * (W / 2 - m / 2), 0, 0), bevel=0.008)
        P.prism([(W / 2 - m, m / 2), (-W / 2 + m, m / 2), (-W / 2 + m, -m / 2), (W / 2 - m, -m / 2)], 0.0, depth, at=(0, sx * (H / 2 - m / 2), 0), bevel=0.008)
        # cap strips with bolts on the vertical mullions
        P.box((0.03, H - 0.02, 0.012), at=(sx * (W / 2 - m / 2), 0, depth + 0.006), mat='paint2', bevel=0.003)
        P.bolts([(sx * (W / 2 - m / 2), y, depth + 0.012) for y in (-0.45, -0.15, 0.15, 0.45)], r=0.011, h=0.007, mat='steel')
    # a horizontal glazing bar at 60 % height and the glass clamp strips
    P.box((gw, 0.05, depth * 0.6), at=(0, gh * 0.1, depth * 0.3), mat='paint', bevel=0.006)
    P.frame(rrect(gw + 0.02, gh + 0.02, 0), rrect(gw - 0.05, gh - 0.05, 0), 0.07, 0.085, mat='dark', bevel=0.0)
    return {'glass': list(glass), 'pitch': [W, H], 'depth': depth, 'about': 'bridge glazing module; tiles edge to edge at pitch (x, y)'}


def cargo_hatch(P, opening=(6.0, 4.0), depth=0.35):
    w, h = opening
    N = 3
    fw, fh = w + 0.7, h + 0.7
    P.loft([(rrect(fw + 0.2, fh + 0.2, 0.4, N), 0.0), (rrect(fw, fh, 0.3, N), depth),
            (rrect(w + 0.1, h + 0.1, 0.12, N), depth), (rrect(w + 0.1, h + 0.1, 0.12, N), 0.0)], bevel=0.025)
    P.frame(rrect(fw - 0.12, fh - 0.12, 0.26, N), rrect(w + 0.26, h + 0.26, 0.14, N), depth, depth + 0.008, mat='hazard', bevel=0.0)
    # two leaves meeting on x = 0, each with ribs
    for sx in (-1, 1):
        cx = sx * (w / 4 + 0.01)
        P.box((w / 2 - 0.04, h, 0.14), at=(cx, 0, 0.1), bevel=0.02)
        for y in (-1.3, 0.0, 1.3):
            P.box((w / 2 - 0.4, 0.18, 0.1), at=(cx, y, 0.22), mat='paint2', bevel=0.02)
        P.box((0.16, h - 0.3, 0.1), at=(sx * (w / 2 - 0.2), 0, 0.22), mat='paint2', bevel=0.02)
        # hinge line on the outer edge, actuator on the frame
        for y in (-1.4, 0, 1.4):
            P.cyl(0.08, 0.5, at=(sx * (w / 2 + 0.02), y, 0.2), rot=(90, 0, 0), n=10, mat='dark')
        P.cyl(0.07, 1.4, at=(sx * (w / 2 + 0.2), h / 2 + 0.22, depth + 0.08), rot=(0, 90, 0), n=10, mat='dark')
        P.cyl(0.04, 0.9, at=(sx * (w / 2 - 0.7), h / 2 + 0.22, depth + 0.08), rot=(0, 90, 0), n=10, mat='steel')
        # floodlights at the top corners of the frame
        P.box((0.3, 0.2, 0.18), at=(sx * (w / 2 + 0.05), h / 2 + 0.2, depth + 0.09), mat='dark', bevel=0.02)
        P.box((0.24, 0.14, 0.01), at=(sx * (w / 2 + 0.05), h / 2 + 0.2, depth + 0.185), mat='lens', bevel=0.0)
    # centre seam: interlocking strip and a crew door in the port leaf (1 x 2 m)
    P.box((0.06, h, 0.02), at=(0, 0, 0.18), mat='rubber', bevel=0.0)
    P.frame(rrect(1.12, 2.12, 0.06, N), rrect(1.0, 2.0, 0.04, N), 0.17, 0.2, at=(-w / 4 - 0.6, -h / 2 + 1.1, 0), mat='dark', bevel=0.006)
    P.box((0.05, 0.25, 0.04), at=(-w / 4 - 0.6 + 0.38, -h / 2 + 1.1, 0.19), mat='steel', bevel=0.006)
    P.bolts([(x, y, depth) for x, y in _bolt_ring(rrect(fw - 0.35, fh - 0.35, 0.2, 2), 0.75)], r=0.03, h=0.02, mat='steel')
    return {'opening': list(opening), 'frame': [fw, fh, depth], 'about': 'bi-parting cargo hatch with a 1 x 2 m crew door'}


def rail(P, length=1.0, height=1.1, r=0.025):
    L = length
    # one stanchion per metre at x = 0; top and mid rails run the full segment so segments tile at pitch 1 m
    P.cyl(r, L, at=(0, 0, height), rot=(0, 90, 0), n=10, caps=True, mat='paint', bevel=0.0)
    P.cyl(r * 0.8, L, at=(0, 0, height * 0.52), rot=(0, 90, 0), n=8, mat='paint', bevel=0.0)
    P.cyl(r * 1.1, height, at=(0, 0, height / 2), n=10, mat='paint', bevel=0.0)
    P.cyl(r * 1.4, 0.06, at=(0, 0, height), rot=(0, 90, 0), n=10, mat='paint', bevel=0.0)  # fitting
    P.cyl(r * 1.3, 0.05, at=(0, 0, height * 0.52), rot=(0, 90, 0), n=10, mat='paint', bevel=0.0)
    P.box((0.16, 0.12, 0.012), at=(0, 0, 0.006), mat='dark', bevel=0.003)
    P.box((0.06, 0.05, 0.1), at=(0, 0, 0.06), mat='paint', bevel=0.006)
    P.bolts([(sx * 0.055, sy * 0.04, 0.012) for sx in (-1, 1) for sy in (-1, 1)], r=0.01, h=0.008, mat='steel')
    return {'pitch': length, 'height': height, 'about': 'handrail segment along X, stanchion at x = 0; tiles at 1 m pitch'}


def ladder(P, width=0.5, length=3.0, pitch=0.3, standoff=0.18):
    for sx in (-1, 1):
        P.box((0.014, length, 0.07), at=(sx * width / 2, 0, standoff), mat='paint', bevel=0.004)
    n = int(round(length / pitch))
    for i in range(n):
        y = -length / 2 + pitch / 2 + i * pitch
        P.cyl(0.016, width, at=(0, y, standoff + 0.01), rot=(0, 90, 0), n=8, mat='steel', bevel=0.0)
    for y in (-length / 2 + 0.25, length / 2 - 0.25):
        for sx in (-1, 1):
            P.box((0.05, 0.08, standoff - 0.035), at=(sx * width / 2, y, (standoff - 0.035) / 2), mat='paint2', bevel=0.006)
            P.box((0.12, 0.12, 0.01), at=(sx * width / 2, y, 0.005), mat='dark', bevel=0.002)
    return {'rungs': n, 'pitch': pitch, 'about': 'ladder along Y, rungs every 0.3 m'}


def rcs(P, span=1.0):
    # quad block: armoured base, four nozzles (+-X, +-Y) and a fifth facing out (+Z)
    b = 0.46
    P.loft([(chamfer_rect(b + 0.14, b + 0.14, 0.1), 0.0), (chamfer_rect(b, b, 0.08), 0.12), (chamfer_rect(b, b, 0.08), 0.3), (chamfer_rect(b - 0.1, b - 0.1, 0.06), 0.36)], closed=False, bevel=0.012)
    prof = [(0.03, 0.0), (0.05, 0.02), (0.09, 0.14), (0.1, 0.16), (0.092, 0.16), (0.083, 0.14), (0.045, 0.03), (0.022, 0.0)]
    for rot, at in (((0, 90, 0), (b / 2 - 0.01, 0, 0.2)), ((0, -90, 0), (-b / 2 + 0.01, 0, 0.2)), ((-90, 0, 0), (0, b / 2 - 0.01, 0.2)), ((90, 0, 0), (0, -b / 2 + 0.01, 0.2))):
        P.lathe(prof, 16, at=at, rot=rot, closed=True, mat='nozzle', sharp=50)
        P.cyl(0.06, 0.04, at=tuple(a * 0.96 for a in at[:2]) + (0.2,), rot=rot, n=12, mat='dark', bevel=0.004)
    P.lathe(prof, 16, at=(0, 0, 0.35), closed=True, mat='nozzle', sharp=50)
    # valve boxes, feed lines (copper) and a bolt ring
    P.box((0.14, 0.1, 0.06), at=(0.1, 0.1, 0.39), mat='dark', bevel=0.008)
    P.tube([(0.1, 0.1, 0.39), (0.1, -0.12, 0.39), (0.03, -0.14, 0.37)], 0.012, n=6, fillet=0.03, mat='copper')
    P.bolts([(x, y, 0.06) for x, y in _bolt_ring(chamfer_rect(b + 0.04, b + 0.04, 0.09), 0.12)], r=0.012, h=0.01, normal=(0, 0, 1), mat='steel')
    return {'nozzles': ['+X', '-X', '+Y', '-Y', '+Z'], 'about': 'RCS quad block with an outboard nozzle'}


def antenna(P, height=6.0):
    P.cyl(0.32, 0.06, at=(0, 0, 0.03), n=16, mat='dark', bevel=0.01)
    P.bolts([(0.25 * math.cos(a), 0.25 * math.sin(a), 0.06) for a in [i * math.pi / 4 for i in range(8)]], r=0.018, h=0.014, mat='steel')
    P.cyl(0.14, 0.5, at=(0, 0, 0.3), n=12, r2=0.1, mat='paint')
    segs = [(0.55, 2.4, 0.09, 0.075), (2.95, 1.9, 0.07, 0.055), (4.85, 1.15, 0.05, 0.035)]
    for z, L, r0, r1 in segs:
        P.cyl(r0, L, at=(0, 0, z + L / 2), n=10, r2=r1, mat='paint', bevel=0.0)
        P.cyl(r0 + 0.025, 0.1, at=(0, 0, z + 0.05), n=10, mat='paint2', bevel=0.008)
    # yard arms with dipole elements, a small whip and a tip beacon housing
    for z, L in ((4.2, 1.2), (5.3, 0.8)):
        P.box((L, 0.05, 0.05), at=(0, 0, z), mat='paint2', bevel=0.008)
        for sx in (-1, 1):
            P.cyl(0.012, 0.5, at=(sx * L / 2, 0, z + 0.2), n=6, mat='steel', bevel=0.0)
            P.cyl(0.025, 0.06, at=(sx * L / 2, 0, z + 0.03), n=8, mat='dark', bevel=0.0)
    P.cyl(0.05, 0.12, at=(0, 0, 6.0 - 0.06), n=10, mat='lens', bevel=0.01)
    P.cyl(0.035, 0.03, at=(0, 0, 6.0 - 0.015 + 0.015), n=10, mat='dark', bevel=0.0)
    P.box((0.12, 0.1, 0.22), at=(0.12, 0, 1.0), mat='dark', bevel=0.01)
    P.tube([(0.02, -0.09, 0.62), (0.02, -0.08, 4.2)], 0.012, n=6, mat='copper')
    return {'height': height, 'about': 'mast along +Z, dipole yards at 4.2 m and 5.3 m'}


def dome(P, diameter=2.5):
    R = diameter / 2
    # plinth ring, flange, radome (faceted panels), maintenance hatch in the plinth
    P.cyl(R + 0.12, 0.08, at=(0, 0, 0.04), n=24, mat='dark', bevel=0.015)
    P.cyl(R + 0.02, 0.36, at=(0, 0, 0.26), n=24, mat='paint', bevel=0.015)
    P.cyl(R + 0.07, 0.07, at=(0, 0, 0.44), n=24, mat='paint2', bevel=0.012)
    prof = [(R, 0.0)] + [(R * math.cos(t), R * 0.82 * math.sin(t)) for t in [math.pi / 2 * k / 9 for k in range(1, 9)]] + [(0.0, R * 0.82)]
    P.lathe(prof, 40, at=(0, 0, 0.47), mat='paint', sharp=60, bevel=0.0)
    t = math.pi / 2 * 3.5 / 9
    P.lathe([(R * math.cos(t) - 0.005, -0.02), (R * math.cos(t) + 0.012, -0.02), (R * math.cos(t) + 0.012, 0.02), (R * math.cos(t) - 0.005, 0.02)], 40,
            at=(0, 0, 0.47 + R * 0.82 * math.sin(t)), closed=True, mat='paint2', sharp=50)
    P.bolts([((R + 0.04) * math.cos(a), (R + 0.04) * math.sin(a), 0.475) for a in [i * 2 * math.pi / 24 for i in range(24)]], r=0.02, h=0.014, mat='steel')
    P.box((0.5, 0.26, 0.04), at=(0, -R - 0.02, 0.26), rot=(90, 0, 0), mat='paint2', bevel=0.008)
    P.box((0.07, 0.04, 0.03), at=(0.18, -R - 0.05, 0.26), mat='steel', bevel=0.005)
    return {'diameter': diameter, 'about': 'sensor radome on a plinth'}


def floodlight(P, size=0.6):
    s = size
    P.box((0.22, 0.16, 0.04), at=(0, 0, 0.02), mat='dark', bevel=0.008)
    for sx in (-1, 1):
        P.box((0.03, 0.08, 0.3), at=(sx * 0.26, 0, 0.19), mat='paint', bevel=0.008)
        P.cyl(0.045, 0.02, at=(sx * 0.24, 0, 0.3), rot=(0, 90, 0), n=12, mat='dark', bevel=0.004)
    P.box((0.56, 0.06, 0.04), at=(0, 0, 0.06), mat='paint', bevel=0.01)
    # lamp head: pitched 25 degrees up about X, lens and cooling fins
    with P.at(at=(0, 0, 0.3), rot=(-25, 0, 180)):
        P.loft([(rrect(0.46, 0.3, 0.05, 2), -0.12), (rrect(0.46, 0.3, 0.05, 2), 0.1), (rrect(0.44, 0.28, 0.04, 2), 0.12)], closed=False, rot=(90, 0, 0), bevel=0.01)
        P.box((0.4, 0.012, 0.24), at=(0, -0.122, 0), mat='glass', bevel=0.0)
        for i in range(6):
            P.box((0.42, 0.06, 0.012), at=(0, 0.13, -0.1 + i * 0.04), mat='paint2', bevel=0.0)
        P.box((0.44, 0.02, 0.02), at=(0, -0.13, 0.13), mat='dark', bevel=0.004)
    return {'aim': 'lamp faces +Y, pitched 25 degrees toward +Z', 'about': 'floodlight on a yoke'}


def container(P, L=6.058, W=2.438, H=2.591):
    post = 0.16
    # corner posts, top / bottom rails, corner castings
    for sx in (-1, 1):
        for sy in (-1, 1):
            P.box((post, post, H), at=(sx * (L / 2 - post / 2), sy * (W / 2 - post / 2), H / 2), bevel=0.01)
            for z in (0.059, H - 0.059):
                P.box((0.178, 0.162, 0.118), at=(sx * (L / 2 - 0.089), sy * (W / 2 - 0.081), z), mat='dark', bevel=0.0)
        for z, hh in ((0.08, 0.16), (H - 0.06, 0.12)):
            P.box((L - 0.3, 0.14, hh), at=(0, sx * (W / 2 - 0.07), z), bevel=0.01)
            P.box((0.14, W - 0.3, hh), at=(sx * (L / 2 - 0.07), 0, z), bevel=0.01)
    # corrugated side walls (trapezoid ribs, pitch 0.278 m)
    pitch, dep = 0.278, 0.036
    for sy in (-1, 1):
        pts = []
        x = -L / 2 + post
        k = 0
        while x < L / 2 - post - 1e-6:
            x2 = min(x + pitch, L / 2 - post)
            y0 = sy * (W / 2 - 0.04)
            y1 = sy * (W / 2 - 0.04 + dep)
            pts += [(x, y0), (x + 0.03, y1), (x + pitch / 2 - 0.03, y1), (x + pitch / 2, y0)]
            x = x2
        pts.append((L / 2 - post, sy * (W / 2 - 0.04)))
        back = [(p[0], sy * (W / 2 - 0.07)) for p in reversed([pts[0], pts[-1]])]
        P.prism(pts + back if sy < 0 else list(reversed(pts + back)), 0.16, H - 0.12, bevel=0.0, sharp=40)
    # roof panel (shallow ribs) and the front end wall (horizontal corrugation)
    P.box((L - 0.3, W - 0.3, 0.04), at=(0, 0, H - 0.08), mat='paint', bevel=0.005)
    for i in range(10):
        P.box((0.1, W - 0.34, 0.012), at=(-L / 2 + 0.5 + i * (L - 1.0) / 9, 0, H - 0.054), mat='paint', bevel=0.0)
    P.box((0.04, W - 0.3, H - 0.3), at=(-L / 2 + 0.06, 0, H / 2), mat='paint', bevel=0.005)
    for i in range(7):
        P.box((0.03, W - 0.34, 0.12), at=(-L / 2 + 0.035, 0, 0.35 + i * 0.3), mat='paint', bevel=0.008)
    # door end (+X): two leaves, four locking bars with cam keepers and handles
    P.box((0.05, W - 0.3, H - 0.3), at=(L / 2 - 0.06, 0, H / 2), mat='paint', bevel=0.008)
    P.box((0.03, 0.02, H - 0.35), at=(L / 2 - 0.03, 0, H / 2), mat='rubber', bevel=0.0)
    for y in (-0.85, -0.35, 0.35, 0.85):
        P.cyl(0.024, H - 0.4, at=(L / 2 - 0.0, y, H / 2), n=8, mat='steel', bevel=0.0)
        for z in (0.2, H - 0.2):
            P.box((0.06, 0.08, 0.1), at=(L / 2 - 0.01, y, z), mat='dark', bevel=0.0)
        P.box((0.05, 0.035, 0.36), at=(L / 2 + 0.03, y + 0.07, 1.1), mat='steel', bevel=0.006)
    for y in (-0.6, 0.6):
        for z in (0.5, H / 2, H - 0.5):
            P.box((0.03, 0.12, 0.14), at=(L / 2 - 0.02, y * 1.55, z), mat='dark', bevel=0.0)
    # data plate
    P.box((0.02, 0.4, 0.3), at=(L / 2 - 0.02, -0.55 + 0.0, 1.8), mat='paint2', bevel=0.004)
    return {'iso': '20ft', 'dims': [L, W, H], 'about': '20-ft ISO container: length along X, height along +Z (deck normal), doors on +X'}


PARTS = {
    'door': {'build': door, 'tex': 512, 'bake': {'ao': 0.12, 'curv': 0.012, 'panel': (0.7, 0.9, 0.7)}},
    'airlock': {'build': airlock, 'tex': 1024, 'bake': {'ao': 0.2, 'curv': 0.015, 'panel': (1.0, 1.2, 1.0)}},
    'port': {'build': port, 'tex': 512, 'bake': {'ao': 0.12, 'curv': 0.012, 'panel': (0.8, 0.8, 0.8)}},
    'pane': {'build': pane, 'tex': 512, 'bake': {'ao': 0.1, 'curv': 0.01, 'panel': (0.8, 0.8, 0.8)}},
    'cargoHatch': {'build': cargo_hatch, 'tex': 1024, 'bake': {'ao': 0.35, 'curv': 0.025, 'panel': (1.5, 1.0, 1.5)}},
    'rail': {'build': rail, 'tex': 256, 'bake': {'ao': 0.08, 'curv': 0.008}},
    'ladder': {'build': ladder, 'tex': 256, 'bake': {'ao': 0.08, 'curv': 0.008}},
    'rcs': {'build': rcs, 'tex': 512, 'bake': {'ao': 0.1, 'curv': 0.01, 'panel': (0.5, 0.5, 0.5)}},
    'antenna': {'build': antenna, 'tex': 512, 'bake': {'ao': 0.1, 'curv': 0.01}},
    'dome': {'build': dome, 'tex': 512, 'bake': {'ao': 0.2, 'curv': 0.015, 'panel': (0.9, 0.9, 0.6)}},
    'floodlight': {'build': floodlight, 'tex': 256, 'bake': {'ao': 0.08, 'curv': 0.008}},
    'container': {'build': container, 'tex': 1024, 'bake': {'ao': 0.25, 'curv': 0.015, 'panel': (2.0, 1.2, 1.3)}},
}
