"""Paint scheme of the Drover-class civil transport (CT-4 / CT-7) for paint.py.

    spec = scheme(v)          # v = freighter_dims.V('cargo' | 'troops')

Light civil paint (the runtime 'civil' livery repaints neutral texels to the fleet grey and keeps
markings as muted colour), plating seams on irregular frames, PATINA plate tone, AO grime, edge
wear, and decals from the concepts: the hull number (dark stencil, large on the reactor block
flanks and roof, small on the bow flanks), the teal stripe along the crew module, orange tags,
hazard frames round the airlocks and doors, yellow walkway edge lines.
"""
import freighter_dims as D

ORANGE = [0.90, 0.42, 0.10]
TEAL = [0.16, 0.60, 0.58]
STENCIL = [0.09, 0.09, 0.10]
YELLOW = [0.86, 0.66, 0.16]
HAZ_ALT = [0.16, 0.16, 0.17]


def frames(z0, z1, seed=5):
    """Irregular plating frames (2.3-3.4 m) over the whole length."""
    out, z, k = [], z0, 0
    while z < z1:
        out.append(round(z, 2))
        z += 2.3 + 1.1 * D._hash(k, seed)
        k += 1
    out.append(z1)
    return out


def scheme(v):
    num = v['number']
    cm0, bow = v['CM0'], v['BOW']
    X, YB, YT = v['RX'], v['RYB'], v['RYT']
    zr = (v['R0'] + v['R1']) / 2
    fx = D.CM['fx']
    decals = [
        # hull number: large, dark stencil on the reactor block flanks (concept) and on its roof
        {'kind': 'text', 'text': num, 'height': 3.4, 'p': [X, 2.6, zr + 0.4], 'n': [1, 0, 0], 'size': [10.5, 4.4, 1.6], 'mirrorX': True, 'color': STENCIL, 'wear': 0.12},
        {'kind': 'text', 'text': num, 'height': 3.0, 'p': [0, YT, zr + 1.6], 'n': [0, 1, 0], 'up': [0, 0, 1], 'size': [9.0, 4.0, 1.2], 'color': STENCIL, 'wear': 0.15},
        # small hull number on the crew module flank, forward, above the teal stripe
        {'kind': 'text', 'text': num, 'height': 1.5, 'p': [fx, 2.9, cm0 + 18.2], 'n': [1, 0, 0], 'size': [5.0, 1.9, 1.2], 'mirrorX': True, 'color': STENCIL, 'wear': 0.1},
        # teal stripe along the crew module flank (concept), and a diagonal tail at its aft end
        {'kind': 'fill', 'p': [fx, 0.35, cm0 + 11.0], 'n': [1, 0, 0], 'size': [20.6, 0.55, 1.2], 'mirrorX': True, 'color': TEAL, 'wear': 0.08},
        {'kind': 'fill', 'p': [fx, -0.35, cm0 + 11.0], 'n': [1, 0, 0], 'size': [20.6, 0.16, 1.2], 'mirrorX': True, 'color': TEAL, 'wear': 0.08},
        # orange tags: crew module bow flank (beside the number), collar corner, reactor front frame
        {'kind': 'fill', 'p': [fx, 2.9, cm0 + 21.3], 'n': [1, 0, 0], 'size': [0.9, 1.4, 1.2], 'mirrorX': True, 'color': ORANGE},
        {'kind': 'fill', 'p': [X, YT - v['RCH'] - 0.9, v['R0'] - 1.4], 'n': [1, 0, 0], 'size': [1.6, 0.9, 1.2], 'mirrorX': True, 'color': ORANGE},
        {'kind': 'fill', 'p': [X, YB + v['RCH'] + 0.8, v['R1'] + 1.6], 'n': [1, 0, 0], 'size': [1.4, 1.4, 1.2], 'mirrorX': True, 'color': ORANGE},
        # yellow edge line along the upper-tier walkway ledge
        {'kind': 'fill', 'p': [fx - 0.2, D.CM['ledge'], cm0 + 10.8], 'n': [0, 1, 0], 'up': [0, 0, 1], 'size': [0.16, 20.8, 0.5], 'mirrorX': True, 'color': YELLOW, 'wear': 0.4},
        # hazard frames: collar airlock bays, crew-door bays, reactor door
        {'kind': 'hazard', 'p': [11.0, -2.2, (v['COL1'] + cm0) / 2], 'n': [1, 0, 0], 'size': [4.0, 4.8, 1.2], 'border': 0.4, 'pitch': 0.5, 'mirrorX': True, 'color': ORANGE, 'alt': HAZ_ALT},
        {'kind': 'hazard', 'p': [X, YB + 3.4 + 1.2, v['R0'] - 2.2], 'n': [1, 0, 0], 'size': [2.8, 3.8, 1.2], 'border': 0.35, 'pitch': 0.45, 'mirrorX': True, 'color': ORANGE, 'alt': HAZ_ALT},
    ]
    for u in (4.6, 17.2):
        decals.append({'kind': 'hazard', 'p': [fx, D.DECKS[0] + 1.6, cm0 + u], 'n': [1, 0, 0], 'size': [2.8, 3.8, 1.2], 'border': 0.35, 'pitch': 0.45, 'mirrorX': True, 'color': ORANGE, 'alt': HAZ_ALT})
    # radiator marks: a thin orange edge bar at the outboard top corner of each panel
    R = v['RAD']
    for zc in (R['z1'] - 1.0, (R['z0'] + R['z1']) / 2 - 1.3):
        decals.append({'kind': 'fill', 'p': [v['HX'], R['y1'] - 0.35, zc], 'n': [1, 0, 0], 'size': [1.4, 0.5, 1.0], 'mirrorX': True, 'color': ORANGE})
    bands = sorted({-14.3, D.CM['bot'], D.CM['fy0'], *D.DECKS, D.CM['ledge'], D.CM['sh_y'], D.CM['top'], YB, YT, -2.2, 3.1, 7.0, 10.5})
    return {
        'zone_names': ['paint', 'belly', 'dark', 'deck', 'recess', 'metal', 'fin', 'glass', 'nozzle', 'trim', 'foil'],
        'zones': {
            'paint': {'color': [0.80, 0.795, 0.775], 'rough': 0.62},
            'trim': {'color': [0.72, 0.72, 0.71], 'rough': 0.6},
            'belly': {'color': [0.58, 0.58, 0.575], 'rough': 0.7},
            'deck': {'color': [0.62, 0.62, 0.61], 'rough': 0.8},
            'dark': {'color': [0.26, 0.26, 0.27], 'rough': 0.72},
            'recess': {'color': [0.50, 0.50, 0.50], 'rough': 0.7},
            'metal': {'color': [0.50, 0.50, 0.50], 'rough': 0.5, 'metal': 0.4},
            'fin': {'color': [0.68, 0.68, 0.66], 'rough': 0.55, 'metal': 0.2},
            'glass': {'color': [0.13, 0.16, 0.2], 'rough': 0.1},
            'nozzle': {'color': [0.2, 0.2, 0.2], 'rough': 0.5, 'metal': 0.6},
            'foil': {'color': [0.6, 0.48, 0.27], 'rough': 0.35, 'metal': 0.8},
        },
        'plated': ['paint', 'deck', 'trim', 'belly'],
        'seams': {'frames': frames(-v['BOW'], v['BOW']), 'bands': bands,
                  'strakes': [0.0, 2.4, 4.6, 7.4, 9.6, 12.2, 14.6, 17.5, 20.5, 23.5, 26.5], 'width': 0.07, 'stagger': 2.9, 'tone': 0.07, 'dark': 0.45,
                  'access': 0.12, 'access_dark': 0.3},
        'normal': {'seam_depth': 0.014, 'access_depth': 0.007, 'seam_w': 1.2, 'strength': 1.0},
        'patina': {'tile': 6.0, 'tone': 0.35},
        'grime': {'ao': 0.35, 'crease': 0.35, 'edge': 0.5, 'blotch': 0.08, 'streak': 0.08},
        'decals': decals,
    }


def stencil(text, h, px_per_m=200):
    """Fleet stencil (hulltex.stencil_alpha's style: strokes 0.185 h, butt ends, mitred corners)
    with the glyphs the civil hull numbers need: C, T, 4, 7 and '-'. Returns (alpha 0..1 array,
    width m, height m) as paint.stencil does."""
    import numpy as np
    from PIL import Image, ImageDraw
    H = int(round(h * px_per_m)); s = 0.185 * H; g = 0.13 * H
    widths = {'C': 0.6, 'T': 0.64, '-': 0.40, '4': 0.66, '7': 0.6, ' ': 0.4}
    Wt = int(sum(widths.get(ch, 0.62) * H for ch in text) + g * (len(text) - 1)) + 4
    im = Image.new('L', (Wt, H + 4), 0)
    d = ImageDraw.Draw(im)
    x = 2; y0 = 2; i = s / 2

    def poly(pts):
        d.polygon([(float(a), float(b)) for a, b in pts], fill=255)

    def bar(a, b, c, e):
        d.rectangle([a, b, c, e], fill=255)

    def stroke(pts):
        for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
            dx, dy = bx - ax, by - ay; L = (dx * dx + dy * dy) ** 0.5
            nx, ny = -dy / L * s / 2, dx / L * s / 2
            poly([(ax + nx, ay + ny), (bx + nx, by + ny), (bx - nx, by - ny), (ax - nx, ay - ny)])
        for (cx, cy) in pts[1:-1]:
            bar(cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2)
    for ch in text:
        w = widths.get(ch, 0.62) * H
        top, bot, mid = y0, y0 + H, y0 + 0.52 * H
        if ch == 'C':
            stroke([(x + w, top + i), (x + i, top + i), (x + i, bot - i), (x + w, bot - i)])
            # stencil bridges: small breaks in the top and bottom bars
            d.rectangle([x + 0.55 * w, top, x + 0.55 * w + 0.05 * H, top + s], fill=0)
            d.rectangle([x + 0.55 * w, bot - s, x + 0.55 * w + 0.05 * H, bot], fill=0)
        elif ch == 'T':
            bar(x, top, x + w, top + s)
            bar(x + w / 2 - s / 2, top + s + 0.05 * H, x + w / 2 + s / 2, bot)
        elif ch == '-':
            bar(x, y0 + 0.53 * H - s * 0.525, x + w, y0 + 0.53 * H + s * 0.525)
        elif ch == '4':
            stroke([(x + i, top), (x + i, top + 0.64 * H), (x + w, top + 0.64 * H)])
            bar(x + w - s * 1.1 - 0.12 * H, top + 0.22 * H, x + w - 0.12 * H, bot)
        elif ch == '7':
            bar(x, top, x + w, top + s)
            poly([(x + w - s * 1.05, top + s + 0.04 * H), (x + w, top + s + 0.04 * H), (x + 0.36 * w + s * 0.55, bot), (x + 0.36 * w - s * 0.55, bot)])
        x += w + g
    return np.asarray(im, np.float32) / 255, Wt / px_per_m, (H + 4) / px_per_m


def paint_chunked(maps, spec, out, chunk=2_000_000):
    """paint.paint (same layers, same spec), run over the covered texels in chunks so a 6144
    atlas paints in ~2 GB: every layer except the normal map is per texel. Writes base.png,
    orm.png, normal.png and base-2k.jpg into `out`."""
    import os
    import numpy as np
    from PIL import Image
    import paint as PT
    zone = np.asarray(maps['zone'])
    S = zone.shape[0]
    idx_all = np.flatnonzero(zone.ravel() >= 0)
    posm = maps['pos'].reshape(-1, 3)
    nrmm = maps['nrm'].reshape(-1, 3)
    ao_full = PT.upsample(np.asarray(maps['ao'], np.float32), S).ravel()
    cv_full = PT.upsample(np.asarray(maps['curv'], np.float32), S).ravel()
    zones, names = spec['zones'], spec['zone_names']
    fill = PT.srgb2lin(zones['paint']['color'])
    col8 = np.empty((S * S, 3), np.uint8)
    col8[:] = (PT.lin2srgb(fill) * 255 + 0.5).astype(np.uint8)
    orm8 = np.zeros((S * S, 3), np.uint8)
    orm8[:, 0] = 255
    orm8[:, 1] = int(zones['paint'].get('rough', 0.6) * 255 + 0.5)
    hh = np.zeros(S * S, np.float32)
    nm = spec.get('normal')
    hm_img = np.asarray(Image.open(os.path.join(PT.SCENE, 'assets/materials/hull/height.webp')).convert('L'), np.float32) / 255 if spec.get('patina') else None
    rng = np.random.default_rng(3)
    plated_ids = [names.index(n) for n in spec.get('plated', ['paint', 'deck', 'trim', 'belly'])]
    g = spec['grime']
    for c0 in range(0, len(idx_all), chunk):
        idx = idx_all[c0:c0 + chunk]
        P = np.asarray(posm[idx], np.float32)
        N = np.asarray(nrmm[idx], np.float32)
        N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-6)
        Zn = zone.ravel()[idx].astype(np.int32)
        ao, cv = ao_full[idx], cv_full[idx]
        base = np.zeros((len(idx), 3), np.float32)
        rough = np.zeros(len(idx), np.float32)
        metal = np.zeros(len(idx), np.float32)
        for i, n in enumerate(names):
            z = zones.get(n, zones['paint'])
            m = Zn == i
            base[m] = PT.srgb2lin(z['color'])
            rough[m] = z.get('rough', 0.6)
            metal[m] = z.get('metal', 0.0)
        painted = np.isin(Zn, plated_ids)
        sm, pid, d_seam, d_acc = PT.seams(P, N, spec['seams'])
        ptone = 1 + spec['seams'].get('tone', 0.06) * (PT.hash3(pid, pid // 7, pid // 13, 11) * 2 - 1)
        base *= np.where(painted, ptone, 1.0)[:, None]
        base *= (1 - spec['seams'].get('dark', 0.45) * sm * painted)[:, None]
        rough = np.where(painted, rough + 0.08 * sm, rough)
        pt = spec.get('patina')
        if pt:
            h = PT.triplanar(hm_img, P, N, pt['tile'])
            # full tone on walls and decks; faded on sloped facets, where the tri-planar blend of
            # two projections draws crossing diagonals
            ax = np.abs(N).max(1)
            k = 1 + pt['tone'] * PT.smooth(0.8, 0.95, ax) * (h / hm_img.mean() - 1)
            base *= np.where(painted, k, 1.0)[:, None]
        aof = np.clip(ao, 0, 1)
        base *= (1 - g['ao'] * (1 - aof))[:, None]
        grime_c = PT.srgb2lin(g.get('color', [0.42, 0.40, 0.37]))
        gm = g['crease'] * PT.smooth(0.9, 0.55, aof)
        base = base * (1 - gm[:, None]) + (base * grime_c / 0.6) * gm[:, None]
        rough += 0.1 * gm
        edge = PT.smooth(0.08, 0.35, cv) * PT.smooth(0.8, 0.97, aof)
        chip = PT.fbm(P, 2.2, 3, seed=5)
        wear = edge * PT.smooth(0.35, 0.6, chip) * g['edge']
        base = base * (1 - wear[:, None]) + PT.srgb2lin(g.get('edge_color', [0.9, 0.9, 0.88]))[None] * wear[:, None]
        metal = np.maximum(metal, wear * 0.5)
        rough -= 0.15 * wear
        blot = PT.fbm(P, 0.09, 3, seed=1)
        base *= (1 + g.get('blotch', 0.08) * (blot - 0.5) * 2)[:, None]
        walls = np.abs(N[:, 1]) < 0.5
        st = PT.fbm(P * np.array([1.0, 0.08, 1.0], np.float32), 1.6, 2, seed=9)
        base *= (1 - walls * PT.smooth(0.55, 0.8, st) * g.get('streak', 0.08))[:, None]
        if 'foil' in names:
            fm = Zn == names.index('foil')
            if fm.any():
                cr = PT.fbm(P[fm], 2.5, 3, seed=31)
                base[fm] *= (0.7 + 0.6 * cr)[:, None]
                rough[fm] = 0.25 + 0.3 * cr
        PT.apply_decals(base, rough, P, N, spec.get('decals', []), rng)
        col8[idx] = (PT.lin2srgb(base) * 255 + 0.5).astype(np.uint8)
        orm8[idx, 1] = (np.clip(rough, 0.05, 1) * 255 + 0.5).astype(np.uint8)
        orm8[idx, 2] = (np.clip(metal, 0, 1) * 255 + 0.5).astype(np.uint8)
        if nm:
            sw = spec['seams'].get('width', 0.08)
            gro = nm['seam_depth'] * (1 - PT.smooth(0.0, sw * nm.get('seam_w', 1.0), d_seam))
            gro = np.maximum(gro, nm['access_depth'] * (1 - PT.smooth(0.0, sw * 0.7, d_acc)))
            hh[idx] = -gro * painted
            if 'foil' in names:
                fm = Zn == names.index('foil')
                hh[idx[fm]] = 0.02 * PT.fbm(P[fm], 4.0, 3, seed=33)
        del P, N, base, rough, metal, sm, pid, d_seam, d_acc
    bp, op = os.path.join(out, 'base.png'), os.path.join(out, 'orm.png')
    Image.fromarray(col8.reshape(S, S, 3)).save(bp)
    Image.fromarray(orm8.reshape(S, S, 3)).save(op)
    Image.fromarray(col8.reshape(S, S, 3)).resize((2048, 2048)).save(os.path.join(out, 'base-2k.jpg'), quality=90)
    del col8, orm8
    np_ = None
    if nm:
        cov = (zone >= 0)
        nimg = PT.height_to_normal(hh.reshape(S, S), cov, spec['px_per_m'], nm.get('strength', 1.0))
        np_ = os.path.join(out, 'normal.png')
        Image.fromarray(nimg).save(np_)
    spec['_normal_png'] = np_
    return bp, op
