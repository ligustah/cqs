"""Paint scheme of the Petrel-class fighter F-402 (tools/blender/hulls/fighter.py), over paint.py.

    import fighter_paint; base, orm = fighter_paint.paint(maps, fighter_paint.spec(), out)

paint.py is shared (do not edit): this module wraps it.
  - stencil(): the fleet stencil (hulltex.stencil_alpha) only has the glyphs K - 1 2 4, so the
    F and 0 glyphs are drawn here in the same style (strokes 0.185 h, butt ends, mitred corners),
    and the alpha is prefiltered to the hull texel size so a point sample per texel gives a crisp,
    anti-aliased edge instead of a stair-stepped one.
  - seams: the plating frames are ship-specific (a 72 m hull, ~2.4-3.6 m plates); the access
    panel share is lower and their sizes vary more (the corvette's repeated visibly).
The base colour is LIGHT PAINT: the runtime livery ('dark', gain 0.05 in the module) maps it to
the fleet's dark matte grey and keeps a hint of the orange bands and cobalt IDs.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import paint as P  # noqa: E402

_PX = {'m': 30.0}   # hull texel density (px per metre), set by paint()


def stencil_alpha(text, h, px_per_m=200):
    """Fleet stencil (as hulltex.stencil_alpha) with F and 0 added. Returns (PIL L, width m, height m)."""
    H = int(round(h * px_per_m)); s = 0.185 * H; g = 0.11 * H
    widths = {'F': 0.56, '-': 0.40, '0': 0.64, '1': 0.46, '2': 0.66, '4': 0.66, ' ': 0.4}
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
        top, bot, mid = y0, y0 + H, y0 + 0.52 * H
        if ch == 'F':
            bar(x, top, x + s, bot)
            bar(x, top, x + w, top + s)
            bar(x, mid - s / 2, x + w * 0.82, mid + s / 2)
        elif ch == '0':
            # stencil zero: a rectangular ring (bars, small outer corner chamfers) broken by narrow
            # bridges at the top and bottom
            bar(x, top, x + s, bot); bar(x + w - s, top, x + w, bot)
            bar(x, top, x + w, top + s); bar(x, bot - s, x + w, bot)
            c = 0.35 * s
            for (cx, cy, dx, dy) in ((x, top, 1, 1), (x + w, top, -1, 1), (x, bot, 1, -1), (x + w, bot, -1, -1)):
                d.polygon([(cx - dx, cy - dy), (cx + dx * c, cy - dy), (cx - dx, cy + dy * c)], fill=0)
            gap = 0.05 * H
            d.rectangle([x + w / 2 - gap / 2, top - 2, x + w / 2 + gap / 2, top + s + 1], fill=0)
            d.rectangle([x + w / 2 - gap / 2, bot - s - 1, x + w / 2 + gap / 2, bot + 2], fill=0)
        elif ch == '-':
            bar(x, y0 + 0.53 * H - s * 0.525, x + w, y0 + 0.53 * H + s * 0.525)
        elif ch == '2':
            stroke([(x, top + i), (x + w - i, top + i), (x + w - i, mid), (x + i, mid), (x + i, bot - i), (x + w, bot - i)])
        elif ch == '4':
            stroke([(x + i, top), (x + i, top + 0.64 * H), (x + w, top + 0.64 * H)])
            bar(x + w - s * 1.1 - 0.12 * H, top + 0.22 * H, x + w - 0.12 * H, bot)
        x += w + g
    return im, Wt / px_per_m, (H + 4) / px_per_m


def stencil(text, h, px_per_m=200):
    """paint.stencil replacement: alpha prefiltered to the texel footprint (box of 1 texel)."""
    from scipy.ndimage import uniform_filter
    im, wm, hm = stencil_alpha(text, h, px_per_m)
    a = np.asarray(im, np.float32) / 255
    k = max(1, int(round(px_per_m / _PX['m'])))
    a = uniform_filter(a, k)
    return a, wm, hm


P.stencil = stencil

ORANGE = [0.93, 0.45, 0.10]
COBALT = [0.24, 0.40, 0.82]
STENCIL = [0.96, 0.88, 0.52]      # pale stencil: saturated enough that the livery keeps it as a light low-vis marking
HAZ_DARK = [0.16, 0.16, 0.17]


def spec():
    # frames along z: irregular plate lengths, 2.4-3.6 m
    frames, z = [], -26.0
    steps = [2.8, 3.2, 2.6, 3.4, 3.0, 2.4, 3.6, 2.9, 3.1, 2.6, 3.3, 2.8, 3.5, 2.7, 3.0, 3.2, 2.5, 3.4, 2.9, 3.1, 2.8, 3.3, 3.0, 2.6, 3.2, 2.9]
    for s_ in steps:
        frames.append(z); z += s_
    frames.append(z)
    chn = [0.8, 0.6, 0.0]
    decals = [
        # hull number on the upper chamfer above each pylon (both flanks, reads from outside)
        {'kind': 'text', 'text': 'F-402', 'height': 2.7, 'p': [10.72, 3.15, -9.3], 'n': chn, 'size': [13, 3.6, 1.6], 'mirrorX': True, 'color': STENCIL, 'wear': 0.12, 'facing': 0.8},
        # orange bands: round the bow (top, chamfers, flanks) and behind the bridge block
        {'kind': 'fill', 'p': [0, -0.9, 27.6], 'n': [0, 0, 1], 'up': [0, 1, 0], 'size': [24, 7.6, 1.5], 'color': ORANGE, 'facing': -1.1, 'wear': 0.3},
        {'kind': 'fill', 'p': [0, 3.2, 3.6], 'n': [0, 0, 1], 'up': [0, 1, 0], 'size': [30, 5.8, 1.2], 'color': ORANGE, 'facing': -1.1, 'wear': 0.3},
        # thin orange bars on the sponson noses and the stern collar
        {'kind': 'fill', 'p': [20.05, -3.35, -0.1], 'n': [0, 0, 1], 'up': [0, 1, 0], 'size': [7.4, 6.8, 0.5], 'mirrorX': True, 'color': ORANGE, 'facing': -1.1, 'wear': 0.35},
        # cobalt ID squares on the flank (concept: blue marker forward of the pylon)
        {'kind': 'fill', 'p': [12.35, -1.3, 12.2], 'n': [0.99, 0, 0.145], 'size': [1.3, 1.0, 1.0], 'mirrorX': True, 'color': COBALT},
        {'kind': 'fill', 'p': [21.0, -0.55, -9.0], 'n': [0, 1, 0], 'up': [0, 0, 1], 'size': [1.0, 1.0, 0.6], 'mirrorX': True, 'color': COBALT},
        # hazard frames round the crew-door bays and the stern RCS cluster
        {'kind': 'hazard', 'p': [12.35, -3.7, 8.6], 'n': [0.99, 0, 0.145], 'size': [2.8, 3.8, 1.2], 'border': 0.3, 'pitch': 0.4, 'mirrorX': True, 'color': ORANGE, 'alt': HAZ_DARK},
        {'kind': 'hazard', 'p': [12.95, -2.6, -16.3], 'n': [1, 0, 0], 'size': [2.8, 3.8, 1.2], 'border': 0.3, 'pitch': 0.4, 'mirrorX': True, 'color': ORANGE, 'alt': HAZ_DARK},
        # hazard edge round the radiator bays on the dorsal deck
        {'kind': 'hazard', 'p': [5.8, 6.84, -11.3], 'n': [0, 1, 0], 'up': [0, 0, 1], 'size': [4.2, 13.1, 0.6], 'border': 0.3, 'pitch': 0.45, 'mirrorX': True, 'color': ORANGE, 'alt': HAZ_DARK, 'wear': 0.45},
        # walkway line along the spine edges
        {'kind': 'fill', 'p': [3.1, 6.98, -4.0], 'n': [0, 1, 0], 'up': [0, 0, 1], 'size': [0.14, 28.0, 0.4], 'mirrorX': True, 'color': [0.85, 0.62, 0.15], 'wear': 0.4},
    ]
    return {
        'zone_names': ['paint', 'belly', 'dark', 'deck', 'recess', 'metal', 'fin', 'glass', 'nozzle', 'trim', 'foil'],
        'zones': {
            'paint': {'color': [0.80, 0.795, 0.77], 'rough': 0.62},
            'trim': {'color': [0.60, 0.60, 0.59], 'rough': 0.6},
            'belly': {'color': [0.44, 0.44, 0.445], 'rough': 0.72},
            'deck': {'color': [0.66, 0.66, 0.65], 'rough': 0.78},
            'dark': {'color': [0.22, 0.22, 0.23], 'rough': 0.7},
            'recess': {'color': [0.48, 0.48, 0.48], 'rough': 0.7},
            'metal': {'color': [0.52, 0.52, 0.51], 'rough': 0.45, 'metal': 0.5},
            'fin': {'color': [0.40, 0.40, 0.41], 'rough': 0.5, 'metal': 0.4},
            'glass': {'color': [0.13, 0.16, 0.2], 'rough': 0.1},
            'nozzle': {'color': [0.30, 0.30, 0.30], 'rough': 0.45, 'metal': 0.6},
            # MLI foil: pale gold, crinkled; livery.js keeps part of the copper / gold hue
            'foil': {'color': [0.78, 0.62, 0.30], 'rough': 0.3, 'metal': 0.85},
        },
        'plated': ['paint', 'deck', 'trim', 'belly'],
        'seams': {'frames': frames, 'bands': [-10.07, -8.3, -6.4, -4.5, -2.4, 0.2, 2.3, 4.5, 6.84],
                  'strakes': [0.0, 1.9, 3.85, 5.9, 7.95, 10.0, 12.0], 'width': 0.07, 'stagger': 1.4, 'tone': 0.1, 'dark': 0.5,
                  'access': 0.22, 'access_dark': 0.45},
        'normal': {'seam_depth': 0.012, 'access_depth': 0.007, 'seam_w': 1.2, 'strength': 1.0},
        'patina': {'tile': 6.0, 'tone': 0.35},
        'grime': {'ao': 0.38, 'crease': 0.4, 'edge': 0.55, 'blotch': 0.13, 'streak': 0.12},
        'decals': decals,
    }


def paint(maps, spec, out):
    _PX['m'] = float(spec.get('px_per_m', 30.0))
    return P.paint(maps, spec=spec, out=out)
