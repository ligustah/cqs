"""Writes tools/blender/specs/freighter-v3.json (CT-4 cargo) and freighter-troops-v3.json (CT-7
troops): the kit placements on the remodelled hulls (freighter.py).

    python3 tools/blender/hulls/freighter_spec.py [cargo|troops ...]

Mounting points repeat the hull dimensions of freighter_dims.py, so re-run this after changing
those. The low-poly port lites (hundreds of 1 m ports on 3 m decks) and the container stacks are
not kit placements: freighter_extras.py adds them after assembly.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import freighter_dims as D  # noqa: E402

r3 = lambda v: [round(c, 3) for c in v]


def norm(v):
    L = math.hypot(*v)
    return (v[0] / L, v[1] / L)


def offset_open(pts, d, left):
    out = []
    for i, p in enumerate(pts):
        ts = []
        if i > 0:
            ts.append(norm((pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])))
        if i < len(pts) - 1:
            ts.append(norm((pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])))
        ns = [(-t[1], t[0]) if left else (t[1], -t[0]) for t in ts]
        if len(ns) == 2:
            b = norm((ns[0][0] + ns[1][0], ns[0][1] + ns[1][1]))
            k = d / max(b[0] * ns[0][0] + b[1] * ns[0][1], 0.25)
            out.append((p[0] + b[0] * k, p[1] + b[1] * k))
        else:
            out.append((p[0] + ns[0][0] * d, p[1] + ns[0][1] * d))
    return out


def cm_x(v, u):
    return D.cm_half(u, v['CM_LEN'])[4][0]


def taper_n(v, u):
    """Outward normal of the tapered crew-module flank at local u (port side)."""
    L = v['CM_LEN']
    t0 = D.CM['taper']
    if u <= t0:
        return [1.0, 0.0, 0.0]
    dx = (D.CM['nose']['fx'] - D.CM['fx']) / (L - t0)
    n = (1.0, 0.0, -dx)
    k = math.sqrt(sum(c * c for c in n))
    return [round(c / k, 4) for c in n]


def placements(v):
    P = []
    cm0, bow, L = v['CM0'], v['BOW'], v['CM_LEN']
    fx = D.CM['fx']
    top = D.CM['top']
    X, YB, YT, CH = v['RX'], v['RYB'], v['RYT'], v['RCH']
    b = v['BELL']
    # ---- drive: kit bell-L at the blueprint exit radius (exit plane centre, body toward +Z)
    P.append({'id': f"main bells: bell-L x{b['scale']:.4f} (r {b['r']})", 'part': 'bell-L', 'p': r3([b['x'], b['y'], b['z']]), 'n': [0, 0, 1], 'up': [0, 1, 0],
              'scale': round(b['scale'], 4), 'snap': False, 'mirrorX': True, 'seat': {'check': False}})
    # ---- crew doors in the crew-module bays (lowest deck), reactor block doors, collar airlocks
    for u in (4.6, 17.2):
        z = cm0 + u
        P.append({'id': f'crew door bay u {u}', 'part': 'door', 'p': [fx, D.DECKS[0] + 1.6, round(z, 3)], 'n': [1, 0, 0], 'mirrorX': True})
        P.append({'part': 'floodlight', 'p': [fx, D.DECKS[0] + 3.35, round(z, 3)], 'n': [1, 0, 0], 'rot': 180, 'mirrorX': True})
    P.append({'id': 'reactor block doors', 'part': 'door', 'p': [X, YB + 4.6, v['R0'] - 2.2], 'n': [1, 0, 0], 'mirrorX': True})
    P.append({'part': 'floodlight', 'p': [X, YB + 6.35, v['R0'] - 2.2], 'n': [1, 0, 0], 'rot': 180, 'mirrorX': True})
    zc = (v['COL1'] + cm0) / 2
    P.append({'id': 'collar airlocks', 'part': 'airlock', 'p': [11.0, -2.2, round(zc, 3)], 'n': [1, 0, 0], 'mirrorX': True})
    P.append({'part': 'floodlight', 'p': [11.0, 0.55, round(zc, 3)], 'n': [1, 0, 0], 'rot': 180, 'mirrorX': True})
    # ---- bridge glazing: kit panes on the back wall of the band round the bow (y 0.9..2.5)
    half = [(cm_x(v, u), cm0 + u) for u in (D.CM['taper'] + 1.0, D.CM['taper'] + 4.0, D.CM['taper'] + 7.0, L - 0.6)]
    half.append((cm_x(v, L) - 0.6, bow))
    half.append((0.0, bow))
    line = half + [(-x, z) for x, z in reversed(half[:-1])]
    inner = offset_open(line, 0.6, True)
    PANE = 1.12
    for i in range(len(inner) // 2):
        a, c = inner[i], inner[i + 1]
        dx, dz = c[0] - a[0], c[1] - a[1]
        Ls = math.hypot(dx, dz)
        ux, uz = dx / Ls, dz / Ls
        n = [round(uz, 4), 0, round(-ux, 4)]
        m = PANE / 2 + 0.08
        if Ls - 2 * m < 0:
            continue
        fa = [a[0] + ux * m, 1.7, a[1] + uz * m]
        fb = [c[0] - ux * m, 1.7, c[1] - uz * m]
        P.append({'id': 'bridge glazing panes' if i == 0 else None, 'part': 'pane', 'row': {'from': r3(fa), 'to': r3(fb), 'pitch': PANE}, 'n': n,
                  'mirrorX': abs(fa[0] + fb[0]) > 0.5, 'seat': {'check': False}})
    # the centre segment (across the bow) is placed once, without its mirror
    P.append({'part': 'pane', 'row': {'from': [-2.6, -1.6, round(bow - 0.7, 3)], 'to': [2.6, -1.6, round(bow - 0.7, 3)], 'pitch': PANE}, 'n': [0, 0, 1], 'seat': {'check': False},
              'id': 'observation deck panes (bow face, lower band)'})
    # cargo-control cab: panes on the sloped aft glazing
    z0 = v['COL1']
    ya, za_, yb_, zb_ = COLYT + 0.6, z0 + 0.6, COLYT + 2.6, z0 + 2.0
    up = norm((yb_ - ya, zb_ - za_))                     # (dy, dz)
    nn = (up[1], -up[0])                                   # faces up and aft
    if nn[1] > 0:
        nn = (-nn[0], -nn[1])
    yc, zcab = (ya + yb_) / 2, (za_ + zb_) / 2
    P.append({'id': 'cab panes (sloped aft glazing)', 'part': 'pane', 'row': {'from': [-3.4, round(yc, 3), round(zcab, 3)], 'to': [3.4, round(yc, 3), round(zcab, 3)], 'pitch': PANE},
              'n': [0, round(nn[0], 4), round(nn[1], 4)], 'up': [0, round(up[0], 4), round(up[1], 4)], 'normal': 'hit'})
    # ---- rails: upper-tier walkway ledge edge, roof edge, collar cab roof
    P.append({'id': 'ledge walkway rails', 'part': 'rail', 'row': {'from': [fx - 0.15, D.CM['ledge'], cm0 + 1.8], 'to': [fx - 0.15, D.CM['ledge'], cm0 + 20.4], 'pitch': 3.0}, 'n': [0, 1, 0], 'mirrorX': True})
    P.append({'id': 'roof edge rails', 'part': 'rail', 'row': {'from': [D.CM['roof_x'] - 0.3, top, cm0 + 1.8], 'to': [D.CM['roof_x'] - 0.3, top, cm0 + 20.4], 'pitch': 3.0}, 'n': [0, 1, 0], 'mirrorX': True})
    # ---- ladders: flank, from the door deck up to the ledge; reactor block flank to its roof
    P.append({'id': 'crew-module flank ladders', 'part': 'ladder', 'p': [fx, -6.4, cm0 + 6.4], 'n': [1, 0, 0], 'rows': {'count': 4, 'step': [0, 3.0, 0]}, 'mirrorX': True})
    P.append({'id': 'reactor block ladders', 'part': 'ladder', 'p': [X, -4.6, v['R0'] - 4.2], 'n': [1, 0, 0], 'rows': {'count': 4, 'step': [0, 3.0, 0]}, 'mirrorX': True})
    # ---- RCS quads: bow corners, reactor block aft corners, radiator outboard tips
    for u, y in ((L - 2.4, -3.8), (L - 2.4, -7.0)):
        P.append({'id': 'rcs' if y > 0 else None, 'part': 'rcs', 'p': r3([cm_x(v, u), y, cm0 + u]), 'n': taper_n(v, u), 'normal': 'hit', 'mirrorX': True})
    for y in (YT - CH - 1.2, YB + CH + 1.2):
        P.append({'part': 'rcs', 'p': r3([X, y, v['R1'] + 1.3]), 'n': [1, 0, 0], 'normal': 'hit', 'mirrorX': True})
    R = v['RAD']
    P.append({'part': 'rcs', 'p': r3([v['HX'] - 0.7, R['y0'], R['z0'] + 0.7]), 'n': [0, -1, 0], 'up': [0, 0, 1], 'normal': 'hit', 'mirrorX': True})
    # ---- nav lights (module lights at the lenses): port red / stbd green on the radiator tops
    # (beam extremity, forward), strobes on the mast housing and the keel block, stern light
    P.append({'id': 'nav lights: radiator sidelights', 'part': 'navlight', 'p': r3([v['HX'] - 0.35, R['y1'], R['z1'] - 0.35]), 'n': [0, 1, 0], 'mirrorX': True})
    P.append({'part': 'navlight', 'p': r3([1.1, YT + 1.35, v['MAST_Z'] - 0.9]), 'n': [0, 1, 0], 'snap': False})
    P.append({'part': 'navlight', 'p': r3([0, -12.8, v['R1'] - 6.0]), 'n': [0, -1, 0]})
    P.append({'part': 'navlight', 'p': r3([0, YT - 4.6 - 1.4, b['back'] + 0.2]), 'n': [0, 0, -1]})
    # ---- antennas: mast whip (its tip sets the envelope top), mast yards, crew-module whips, dome
    base = YT + 1.35
    s = (v['HY'] - base + 0.05) / 6.015
    P.append({'id': f'mast whip x{s:.3f}: tip at y {v["HY"]}', 'part': 'antenna', 'p': r3([0, base, v['MAST_Z']]), 'n': [0, 1, 0], 'up': [0, 0, 1], 'scale': round(s, 4), 'snap': False, 'seat': {'check': False}})
    P.append({'part': 'antenna', 'p': r3([1.3, base, v['MAST_Z'] + 0.6]), 'n': [0, 1, 0], 'up': [0, 0, 1], 'scale': 0.55, 'mirrorX': True, 'snap': False, 'seat': {'check': False}})
    P.append({'id': 'crew-module whips', 'part': 'antenna', 'p': r3([3.6, top + 0.7, cm0 + 14.5]), 'n': [0, 1, 0], 'up': [0, 0, 1], 'scale': 0.8})
    P.append({'part': 'antenna', 'p': r3([-3.4, top + 0.7, cm0 + 10.0]), 'n': [0, 1, 0], 'up': [0, 0, 1], 'scale': 0.62})
    P.append({'id': 'radome', 'part': 'dome', 'p': r3([-3.0, top + 0.9, cm0 + 20.4]), 'n': [0, 1, 0], 'up': [0, 0, 1], 'scale': 0.85, 'snap': False, 'seat': {'check': False}})
    # ---- vents on the reactor block flanks (upper)
    zr = (v['R0'] + v['R1']) / 2
    P.append({'id': 'reactor vents', 'part': 'vent', 'row': {'from': [X, 6.2, zr + 3.0], 'to': [X, 6.2, zr - 3.0], 'pitch': 2.0}, 'n': [1, 0, 0], 'mirrorX': True})
    # ---- troops: habitat doors (outboard, mid length) and top rails
    if v['variant'] == 'troops':
        H = D.HAB
        z0h, z1h = D.hab_span(v)
        zm = (z0h + z1h) / 2
        for yc in (H['yu'], H['yl']):
            P.append({'id': 'habitat doors' if yc > 0 else None, 'part': 'door', 'p': r3([H['x'] + H['r'], yc, zm + 2.3]), 'n': [1, 0, 0], 'mirrorX': True})
        P.append({'id': 'habitat top rails', 'part': 'rail', 'row': {'from': [H['x'], H['yu'] + H['r'], z1h - 4.0], 'to': [H['x'], H['yu'] + H['r'], z0h + 4.0], 'pitch': 3.0}, 'n': [0, 1, 0], 'mirrorX': True})
    return [{k: q for k, q in p.items() if q is not None} for p in P]


COLYT = 7.6  # collar roof (freighter.COL['yt'])


def spec(v):
    return {
        'about': f"Drover-class {v['variant']} ship {v['number']}, v3 REMODEL: the hull is clean hard-surface geometry built by tools/blender/hulls/freighter.py "
                 f"(--variant {v['variant']}) from measurements of the fal/Tripo H3.1 blueprint (ship frame, metres, bow +Z, dorsal +Y, port +X; not re-centred), "
                 "textured by paint.py with freighter_paint.py; this spec places the Blender parts kit on it. Container stacks (cargo) and the port lites are "
                 "added after assembly by freighter_extras.py. Bells are kit bells scaled to the blueprint exit radius.",
        'hull': {'glb': 'HULL_GLB_FROM_COMMAND_LINE', 'rotate': [0, 0, 0], 'scale': 1.0, 'centre': False},
        'partsDir': '../../../assets/parts-blender',
        'partDefaults': {
            'door': {'sink': 0.0}, 'airlock': {'sink': 0.0}, 'pane': {'sink': 0.04}, 'rcs': {'sink': 0.04}, 'floodlight': {'sink': 0.02}, 'navlight': {'sink': 0.0},
            'rail': {'sink': 0.0, 'xAlong': True, 'scale': [3, 1, 1]}, 'ladder': {'sink': 0.0, 'lift': 0.03}, 'antenna': {'sink': 0.05}, 'dome': {'sink': 0.05}, 'vent': {'sink': 0.03}},
        'fixes': {'pane': {'decimate': 0.4}, 'door': {'decimate': 0.3}, 'airlock': {'decimate': 0.45}, 'rail': {'decimate': 1.0}, 'rcs': {'decimate': 0.35},
                  'navlight': {'decimate': 0.35}, 'floodlight': {'decimate': 0.3}, 'ladder': {'decimate': 0.45}, 'bell-L': {'decimate': 0.35},
                  'antenna': {'decimate': 0.45}, 'dome': {'decimate': 0.6}, 'vent': {'decimate': 0.5}},
        'seat': {'maxGap': 0.15, 'maxBury': 0.4, 'drop': True},
        'bake': {'ao': True, 'res': 2048, 'distance': 0.35, 'samples': 16, 'aa': 4, 'strength': 0.6},
        'placements': placements(v),
    }


def main():
    names = sys.argv[1:] or ['cargo', 'troops']
    for nm in names:
        v = D.V(nm)
        path = os.path.join(HERE, '..', 'specs', f"{v['name']}-v3.json")
        sp = spec(v)
        json.dump(sp, open(path, 'w'), indent=1)
        print(os.path.normpath(path), len(sp['placements']))


if __name__ == '__main__':
    main()
