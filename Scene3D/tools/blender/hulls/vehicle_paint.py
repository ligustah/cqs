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
         'mirrorX': True, 'color': STENCIL, 'wear': 0.12, 'facing': 0.8},
        # one vertical amber band per flank between the doors, fender line to the shoulder
        {'kind': 'fill', 'p': [1.10, 1.50, D.BAND['z']], 'n': [1, 0, 0], 'size': [D.BAND['w'], 1.44, 0.3], 'mirrorX': True, 'color': AMBER, 'wear': 0.25, 'facing': 0.8},
        # cobalt square above each front arch
        {'kind': 'fill', 'p': [1.10, D.COBALT['y'], D.COBALT['z']], 'n': [1, 0, 0], 'size': [D.COBALT['s'], D.COBALT['s'], 0.3], 'mirrorX': True, 'color': COBALT, 'wear': 0.1, 'facing': 0.8},
        # diagonal amber hatching at the two front corners: bonnet chamfer + nose flank
        {'kind': 'hazard', 'p': [0.80, 1.62, 2.80], 'n': [0.75, 0.3, 0.6], 'size': [0.62, 0.62, 0.5], 'pitch': 0.16, 'mirrorX': True, 'color': AMBER, 'wear': 0.3, 'facing': 0.15},
        # walkway line on the roof edges
        {'kind': 'fill', 'p': [0.80, D.ROOF, -0.9], 'n': [0, 1, 0], 'up': [0, 0, 1], 'size': [0.05, 4.4, 0.2], 'mirrorX': True, 'color': [0.85, 0.62, 0.15], 'wear': 0.4},
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
    }


def paint(maps, spec, out):
    FP._PX['m'] = float(spec.get('px_per_m', 300.0))
    return P.paint(maps, spec=spec, out=out)
