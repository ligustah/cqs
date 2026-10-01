"""Paint scheme of the V-31 wheeled 4x4 (tools/blender/hulls/vehicle.py), over paint.py (shared, not edited).

    import vehicle_paint; base, orm = vehicle_paint.paint(maps, vehicle_paint.spec(), out)

Reuses fighter_paint's fleet stencil (strokes 0.185 h, butt ends, texel-prefiltered alpha) and adds the V and
3 glyphs in the same style. Markings follow the approved concept A: diagonal amber hatching at the two front
corners, one vertical amber band on each flank (between the doors), a cobalt square above each front arch and
V-31 above each rear arch. Plating frames are vehicle-sized (0.8-1.4 m plates), seams narrower than a ship's.
The base colour is LIGHT PAINT: the runtime livery maps it to the fleet's dark operational grey.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import paint as P  # noqa: E402
import fighter_paint as FP  # noqa: E402
import vehicle_dims as D  # noqa: E402

_base_alpha = FP.stencil_alpha


def stencil_alpha(text, h, px_per_m=200):
    """Fleet stencil with V and 3 (drawn here); other glyphs from fighter_paint / hulltex style."""
    if not any(ch in text for ch in 'V3'):
        return _base_alpha(text, h, px_per_m)
    H = int(round(h * px_per_m)); s = 0.185 * H; g = 0.11 * H
    widths = {'V': 0.62, '3': 0.6, '-': 0.40, '1': 0.46, ' ': 0.4}
    Wt = int(sum(widths.get(ch, 0.62) * H for ch in text) + g * (len(text) - 1)) + 4
    im = Image.new('L', (Wt, H + 4), 0)
    d = ImageDraw.Draw(im)
    x = 2; y0 = 2; i = s / 2

    def poly(pts):
        d.polygon([(float(a), float(b)) for a, b in pts], fill=255)

    def bar(x0, y0_, x1, y1):
        d.rectangle([x0, y0_, x1, y1], fill=255)

    def stroke(pts):
        for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
            dx, dy = bx - ax, by - ay; L = (dx * dx + dy * dy) ** 0.5
            nx, ny = -dy / L * s / 2, dx / L * s / 2
            poly([(ax + nx, ay + ny), (bx + nx, by + ny), (bx - nx, by - ny), (ax - nx, ay - ny)])
        for (cx, cy) in pts[1:-1]:
            bar(cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2)
    for ch in text:
        w = widths.get(ch, 0.62) * H
        top, bot, mid = y0, y0 + H, y0 + 0.5 * H
        if ch == 'V':
            # two straight strokes meeting in a flat foot (stencil: a hairline bridge-free gap at the foot)
            poly([(x, top), (x + s * 1.05, top), (x + w / 2 + s * 0.12, bot - s * 0.9), (x + w / 2 + s * 0.12, bot), (x + w / 2 - s * 0.55, bot)])
            poly([(x + w, top), (x + w - s * 1.05, top), (x + w / 2 + s * 0.28, bot - s * 0.9), (x + w / 2 + s * 0.28, bot), (x + w / 2 + s * 0.95, bot)])
        elif ch == '3':
            stroke([(x, top + i), (x + w - i, top + i), (x + w - i, bot - i), (x, bot - i)])
            bar(x + w * 0.3, mid - s / 2, x + w - s * 0.2, mid + s / 2)
            # stencil bridge: break the spine above and below the middle bar
            d.rectangle([x + w - s - 2, mid - s / 2 - 0.06 * H, x + w + 2, mid - s / 2 - 0.02 * H], fill=0)
            d.rectangle([x + w - s - 2, mid + s / 2 + 0.02 * H, x + w + 2, mid + s / 2 + 0.06 * H], fill=0)
        elif ch == '-':
            bar(x, y0 + 0.53 * H - s * 0.525, x + w, y0 + 0.53 * H + s * 0.525)
        elif ch == '1':
            bar(x + w - s, top, x + w, bot)
            poly([(x + w - s, top), (x + w - s, top + s * 1.2), (x, top + s * 1.9), (x, top + s * 0.8)])
        x += w + g
    return im, Wt / px_per_m, (H + 4) / px_per_m


FP.stencil_alpha = stencil_alpha        # FP.stencil (prefiltered, P.stencil) calls this

AMBER = [0.93, 0.58, 0.12]              # STYLE.md hazard amber (orange reads salmon through the livery)
COBALT = [0.24, 0.40, 0.82]
STENCIL = [0.96, 0.88, 0.52]            # pale saturated stencil (as the fighter's): the dark livery keeps it as a light low-vis
                                        # marking; a dark stencil (the concept's) vanishes on the dark operational grey (lessons)


def spec():
    frames, z = [], -3.25
    for s_ in [0.95, 1.2, 0.85, 1.3, 1.05, 0.9, 1.25, 1.1, 0.95, 1.2, 0.8]:
        frames.append(z); z += s_
    frames.append(3.3)
    decals = [
        # V-31 above each rear arch (reads correctly on both flanks: right = up x n)
        {'kind': 'text', 'text': 'V-31', 'height': D.STENCIL['h'], 'p': [1.10, D.STENCIL['y'], D.STENCIL['z']], 'n': [1, 0, 0], 'size': [1.4, 0.6, 0.3],
         'mirrorX': True, 'color': STENCIL, 'wear': 0.3, 'facing': 0.8},
        # one vertical amber band per flank between the doors, fender line to the shoulder
        {'kind': 'fill', 'p': [1.10, 1.50, D.BAND['z']], 'n': [1, 0, 0], 'size': [D.BAND['w'], 1.44, 0.3], 'mirrorX': True, 'color': AMBER, 'wear': 0.8, 'facing': 0.8},
        # cobalt square above each front arch
        {'kind': 'fill', 'p': [1.10, D.COBALT['y'], D.COBALT['z']], 'n': [1, 0, 0], 'size': [D.COBALT['s'], D.COBALT['s'], 0.3], 'mirrorX': True, 'color': COBALT, 'wear': 0.7, 'facing': 0.8},
        # diagonal amber hatching at the two front corners: bonnet chamfer + nose flank
        {'kind': 'hazard', 'p': [0.80, 1.62, 2.80], 'n': [0.75, 0.3, 0.6], 'size': [0.62, 0.62, 0.5], 'pitch': 0.16, 'mirrorX': True, 'color': AMBER, 'wear': 0.85, 'facing': 0.15},
        # walkway line on the roof edges
        {'kind': 'fill', 'p': [0.80, D.ROOF, -0.9], 'n': [0, 1, 0], 'up': [0, 0, 1], 'size': [0.05, 4.4, 0.2], 'mirrorX': True, 'color': [0.85, 0.62, 0.15], 'wear': 0.6},
    ]
    return {
        'zone_names': ['paint', 'belly', 'dark', 'deck', 'recess', 'metal', 'fin', 'glass', 'nozzle', 'trim', 'foil'],
        'zones': {
            'paint': {'color': [0.80, 0.795, 0.77], 'rough': 0.64},
            'trim': {'color': [0.70, 0.70, 0.68], 'rough': 0.62},
            'belly': {'color': [0.46, 0.46, 0.45], 'rough': 0.75},
            'deck': {'color': [0.72, 0.72, 0.70], 'rough': 0.8},
            'dark': {'color': [0.20, 0.205, 0.215], 'rough': 0.55, 'metal': 0.3},      # gunmetal collar, belly band, end frame
            'recess': {'color': [0.40, 0.40, 0.40], 'rough': 0.7},
            'metal': {'color': [0.50, 0.50, 0.49], 'rough': 0.45, 'metal': 0.5},
            'fin': {'color': [0.30, 0.30, 0.31], 'rough': 0.5, 'metal': 0.4},
            'glass': {'color': [0.10, 0.13, 0.17], 'rough': 0.08},
            'nozzle': {'color': [0.30, 0.30, 0.30], 'rough': 0.45, 'metal': 0.6},
            'foil': {'color': [0.78, 0.62, 0.30], 'rough': 0.3, 'metal': 0.85},
        },
        'plated': ['paint', 'deck', 'trim', 'belly'],
        'seams': {'frames': frames, 'bands': [0.55, 0.78, 0.98, 1.45, 2.22, 2.5],
                  # roof / bonnet: one strake per side (v1 had 0.42 m strakes too: with the ~1 m frames the bonnet read
                  # as a fine tile grid under the dark livery, not the concept's few large plates)
                  'strakes': [0.0, 0.84], 'width': 0.022, 'stagger': 0.45, 'tone': 0.07, 'dark': 0.32,
                  'access': 0.1, 'access_dark': 0.35},
        'normal': {'seam_depth': 0.004, 'access_depth': 0.0025, 'seam_w': 1.2, 'strength': 1.0},
        'patina': {'tile': 6.0, 'tone': 0.3},
        'grime': {'ao': 0.35, 'crease': 0.4, 'edge': 0.5, 'blotch': 0.12, 'streak': 0.14, 'color': [0.45, 0.41, 0.36]},
        'decals': decals,
        # v2 used look (correction 34): see weather()
        'weather': {
            'roof_fade': 0.2, 'recess': 0.28, 'streak': 0.4, 'chips': 1.0, 'stone': 1.0, 'mud': 1.0,
            'primer': [0.36, 0.25, 0.20],       # sRGB, red-oxide primer (muted)
            'metal': [0.56, 0.56, 0.55],        # sRGB, bare steel
            'mud_c': [0.36, 0.31, 0.26],        # sRGB, dried mud (linear ~0.105 / 0.08 / 0.056: finish.js ground mud)
            'crust_c': [0.44, 0.39, 0.33],      # sRGB, lighter dried crust at the splash edges
            'grime_c': [0.17, 0.15, 0.13],      # sRGB, recess grime
            'runoff_c': [0.33, 0.30, 0.27],     # sRGB, dusty run-off streaks
        },
    }


def weather(maps, spec, out):
    """v2 used look (correction 34: "way too smooth and clean. Too shiny"), over paint.py's base.png / orm.png.

    Luminance layers (the dark livery keeps them as grey tone): sun-faded roof, recess grime, grime streaks running down
    the walls from the roof edge, the side vents and the side panes. TRUE-COLOUR layers, written with base-colour alpha
    < 1 (livery.js keep: 1 leaves those texels unrepainted; 1 - alpha = how much): chipped convex edges with red-oxide
    primer round bare steel, stone chips low on the body and the nose, dried mud round the wheel arches, in the
    wheelhouses and on the belly. Graded dust over everything low down is runtime (finish.js ground preset), so it runs
    continuously across the kit parts (doors, wheels)."""
    w = spec['weather']
    zone = maps['zone'].astype(np.int32)
    S = zone.shape[0]
    idx = np.where((zone >= 0).ravel())[0]
    Pp = maps['pos'].reshape(-1, 3)[idx].astype(np.float32)
    N = maps['nrm'].reshape(-1, 3)[idx].astype(np.float32)
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-6)
    Zn = zone.ravel()[idx]
    ao = np.clip(P.upsample(maps['ao'], S).ravel()[idx], 0, 1)
    cv = P.upsample(maps['curv'], S).ravel()[idx]
    names = spec['zone_names']
    zin = lambda *ns: np.isin(Zn, [names.index(n) for n in ns])
    paintable = zin('paint', 'trim', 'belly', 'deck', 'dark', 'recess')
    plated = zin('paint', 'trim', 'belly', 'deck')
    bp, op = os.path.join(out, 'base.png'), os.path.join(out, 'orm.png')
    base8 = np.asarray(Image.open(bp).convert('RGB')).reshape(-1, 3)
    orm8 = np.asarray(Image.open(op).convert('RGB')).reshape(-1, 3).copy()
    col = P.srgb2lin(base8[idx].astype(np.float32) / 255)
    rough = orm8[idx, 1].astype(np.float32) / 255
    metal = orm8[idx, 2].astype(np.float32) / 255
    keep = np.zeros(len(idx), np.float32)
    x, y, z = Pp[:, 0], Pp[:, 1], Pp[:, 2]
    ax = np.abs(x)

    # 1. sun-faded roof: up-facing paint high on the body is lighter and chalkier, in soft patches
    up = P.smooth(0.6, 0.92, N[:, 1]) * P.smooth(1.6, 2.1, y) * plated
    fade = up * w['roof_fade'] * (0.55 + 0.45 * P.fbm(Pp, 0.9, 3, seed=61))
    col *= (1 + fade)[:, None]
    rough = np.where(up > 0, rough + 0.08 * up, rough)
    # 2. recess grime: deeper than paint.py's AO grime, in the creases and round fittings
    g = P.smooth(0.88, 0.45, ao) * paintable
    col *= (1 - w['recess'] * g)[:, None]
    rough += 0.06 * g
    # ... and in true colour (dark brown), so it reads on any livery
    gk = 0.55 * g * P.smooth(0.35, 0.6, P.fbm(Pp, 5.0, 3, seed=62))
    col = col * (1 - gk[:, None]) + P.srgb2lin(w['grime_c'])[None] * gk[:, None]
    keep = np.maximum(keep, gk)
    # 3. grime streaks down the walls from the roof edge, below the side vents and the side panes
    wall = (np.abs(N[:, 1]) < 0.35) & paintable
    sc = np.where(np.abs(N[:, 0]) > 0.6, z, np.where(np.abs(N[:, 2]) > 0.6, x, z + x)).astype(np.float32)
    zero = np.zeros_like(sc)
    colA = P.vnoise(np.stack([sc * 18.0, zero, zero + 3.7], 1), seed=71)
    colB = P.vnoise(np.stack([sc * 5.0, zero, zero + 1.3], 1), seed=72)
    L = 0.25 + 0.75 * colB                                   # streak length per column (m)
    src = np.full(len(idx), 2.24, np.float32)                # under the roof-edge chamfer
    src = np.where(np.abs(N[:, 2]) > 0.6, 2.36, src)         # tail and nose faces
    for (zc, yc, hw, hh) in ((D.SIDE_VENT['z'], D.SIDE_VENT['y'], D.SIDE_VENT['w'] / 2, D.SIDE_VENT['h'] / 2),
                             (D.SIDE_PANE['z'], D.SIDE_PANE['y'], D.SIDE_PANE['w'] / 2, D.SIDE_PANE['h'] / 2)):
        under = (np.abs(z - zc) < hw) & (y < yc - hh) & (ax > 0.9)
        src = np.where(under, yc - hh, src)
    d = src - y
    streak = wall * (d > 0) * np.exp(-np.maximum(d, 0) / L) * P.smooth(0.45, 0.8, colA) * (0.6 + 0.4 * colB)
    col *= (1 - w['streak'] * streak)[:, None]
    # dusty run-off in true colour: lighter than the dark paint, as rain streaks dust down a dark vehicle
    rk = 0.4 * streak * P.smooth(0.4, 0.7, colB)
    col = col * (1 - rk[:, None]) + P.srgb2lin(w['runoff_c'])[None] * rk[:, None]
    keep = np.maximum(keep, rk)
    # 3b. scuffed markings: fine abrasion takes saturated paint (bands, hatching, cobalt, V-31) back toward the grey
    #     paint in streaky patches (the livery then shows the hull grey there)
    mx, mn = col.max(1), col.min(1)
    sat = (mx - mn) / np.maximum(mx, 1e-4)
    lum = col @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    scuff = P.smooth(0.3, 0.5, sat) * P.smooth(0.55, 0.68, P.fbm(Pp * np.array([1.0, 2.5, 1.0], np.float32), 10.0, 3, seed=51)) * paintable   # never the glass (blue, saturated)
    col = col * (1 - 0.65 * scuff[:, None]) + (lum * 1.1)[:, None] * 0.65 * scuff[:, None]
    # 4. chipped edges: convex edges (curvature, not in a crease), more low down and at the nose; bare steel in the
    #    middle of a chip, red-oxide primer round it
    edge = P.smooth(0.06, 0.3, cv) * P.smooth(0.6, 0.9, ao)
    # the curvature edge is a few texels wide (2.5 cm bake radius); chips reach a few cm into the faces either side
    from scipy import ndimage
    E = np.zeros(S * S, np.float32); E[idx] = edge
    E = ndimage.gaussian_filter(ndimage.maximum_filter(E.reshape(S, S), size=w.get('chip_px', 9)), 1.5).ravel()
    edge = np.clip(E[idx] * 1.3, 0, 1) * paintable
    bias = 0.55 + 0.55 * P.smooth(1.3, 0.6, y) + 0.35 * P.smooth(2.6, 3.1, z) + 0.25 * P.smooth(-2.9, -3.2, z)
    n1 = P.fbm(Pp, 9.0, 3, seed=41) + 0.18 * (bias - 0.8)
    rim = edge * P.smooth(0.52, 0.57, n1) * w['chips']
    core = edge * P.smooth(0.6, 0.65, n1) * w['chips']
    # stone chips: small flecks on the lower body and the nose face (flat paint too)
    low = paintable & ((y < 1.15) | ((z > 2.95) & (N[:, 2] > 0.5)))
    n2 = P.fbm(Pp, 22.0, 2, seed=43)
    flecks = low * P.smooth(0.73, 0.77, n2) * w['stone']
    rim = np.maximum(rim, flecks)
    core = np.maximum(core, low * P.smooth(0.78, 0.8, n2) * w['stone'])
    prim = P.srgb2lin(w['primer']) * (0.85 + 0.3 * P.fbm(Pp, 30.0, 2, seed=44))[:, None]
    stl = P.srgb2lin(w['metal'])
    col = col * (1 - rim[:, None]) + prim * rim[:, None]
    col = col * (1 - core[:, None]) + stl[None] * core[:, None]
    rough = rough * (1 - rim) + 0.85 * rim
    rough = rough * (1 - core) + 0.45 * core
    metal = np.maximum(metal * (1 - rim), 0.85 * core)
    keep = np.maximum(keep, np.maximum(rim, core))
    # 5. dried mud: wheelhouses and arch rims (thrown back and up by the tyres), the belly
    mud = np.zeros(len(idx), np.float32)
    for az in D.AXLES:
        dz = z - az
        r = np.hypot(dz * 0.95, y - D.WHEEL['y'])
        near = (np.abs(dz) < 1.15) & (y < 1.6)
        inside = near & (ax < 1.02) & (r < 1.0)                         # wheelhouse walls and the arch ceiling
        rimz = near & (ax >= 0.95) & (N[:, 0] * np.sign(x) > 0.4)      # outer flank round the arch
        throw = 1 + 0.7 * (dz < 0)                                       # more behind each wheel
        spl = P.fbm(Pp, 6.0, 3, seed=81) + 0.15 * P.fbm(Pp, 25.0, 2, seed=82)
        m_in = inside * P.smooth(0.3, 0.55, spl + 0.25)
        m_rim = rimz * P.smooth(1.05 + 0.12 * throw, 0.82, r) * P.smooth(0.52, 0.6, spl + 0.05 * throw)
        mud = np.maximum(mud, np.maximum(m_in * 0.95, m_rim * 0.9))
    belly = (N[:, 1] < -0.5) & (y < 0.7)
    mud = np.maximum(mud, belly * 0.8 * P.smooth(0.35, 0.55, P.fbm(Pp, 4.0, 3, seed=83)))
    mud *= w['mud'] * (Zn != names.index('glass'))
    edge_m = P.smooth(0.2, 0.5, mud) * (1 - P.smooth(0.6, 0.9, mud))   # lighter crust at the splash edges
    mc = P.srgb2lin(w['mud_c'])[None] * (1 - edge_m[:, None]) + P.srgb2lin(w['crust_c'])[None] * edge_m[:, None]
    mc = mc * (0.85 + 0.3 * P.fbm(Pp, 14.0, 2, seed=84))[:, None]
    col = col * (1 - mud[:, None]) + mc * mud[:, None]
    rough = rough * (1 - mud) + 0.97 * mud
    metal *= 1 - mud
    keep = np.maximum(keep, mud)
    # 6. glass: paint.py's warm crease grime shifts the recessed panes off blue, and the livery then misses them (they
    #    took the matte push and read as a pale sheen). Restore the zone's blue-dark glass colour (AO kept) and gloss
    gl = Zn == names.index('glass')
    gcol = P.srgb2lin(spec['zones']['glass']['color'])
    col[gl] = gcol[None] * (0.75 + 0.25 * ao[gl])[:, None]
    rough[gl] = spec['zones']['glass'].get('rough', 0.08)
    metal[gl] = 0
    # write: base colour RGBA (alpha = 1 - keep), ORM
    out8 = np.concatenate([base8, np.full((S * S, 1), 255, np.uint8)], 1)
    out8[idx, :3] = (P.lin2srgb(col) * 255 + 0.5).astype(np.uint8)
    out8[idx, 3] = ((1 - np.clip(keep, 0, 1)) * 255 + 0.5).astype(np.uint8)
    Image.fromarray(out8.reshape(S, S, 4), 'RGBA').save(bp)
    orm8[idx, 1] = (np.clip(rough, 0.05, 1) * 255 + 0.5).astype(np.uint8)
    orm8[idx, 2] = (np.clip(metal, 0, 1) * 255 + 0.5).astype(np.uint8)
    Image.fromarray(orm8.reshape(S, S, 3)).save(op)
    Image.fromarray(out8.reshape(S, S, 4)[:, :, :3]).resize((2048, 2048)).save(os.path.join(out, 'base-2k.jpg'), quality=90)
    Image.fromarray(out8.reshape(S, S, 4)[:, :, 3]).save(os.path.join(out, 'keep.png'))
    return {'keep_texels': int((keep > 0.05).sum()), 'chips': int((core > 0.5).sum()), 'mud': int((mud > 0.5).sum())}


def paint(maps, spec, out):
    FP._PX['m'] = float(spec.get('px_per_m', 300.0))
    bp, op = P.paint(maps, spec=spec, out=out)
    if spec.get('weather'):
        print('[vehicle_paint] weather', weather(maps, spec, out))
    return bp, op
