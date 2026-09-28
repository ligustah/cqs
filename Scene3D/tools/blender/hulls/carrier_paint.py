"""Texture-space paint for the carrier (tools/blender/hulls/carrier.py).

The destroyer's painter (destroyer_paint.py: paint.py's layers in row chunks at 8192 on
upsampled 4096 bakes, varied access panels) with the carrier's scheme and scale:
  - zone 10 is SAFETY yellow (hangar gantry rails), not copper / foil;
  - plating at the 900 m hull's scale: frames ~11 m, bands 6 m on the deck pitch, strakes ~9 m,
    seams 0.22 m wide (a texel is ~0.1-0.2 m); the runtime PATINA hull tile (6 m) carries the
    finer plating;
  - a crisp stencil with the glyphs C V - 5 0 (CV-50, 15 m letters on both bow flanks).
The destroyer module's stencil lookup is swapped for this one (module attribute), nothing in
destroyer_paint.py changes.
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import destroyer_paint as DP  # noqa: E402
import carrier_dims as D  # noqa: E402

Image.MAX_IMAGE_PIXELS = None


# ------------------------------------------------------------------------------------------
# stencil: C V - 5 0 with stencil bridges
# ------------------------------------------------------------------------------------------
def stencil_alpha(text, h, px_per_m=40):
    H = int(round(h * px_per_m)); s = 0.19 * H; g = 0.13 * H; br = 0.06 * H   # stroke, letter gap, bridge
    widths = {'C': 0.6, 'V': 0.66, '-': 0.4, '5': 0.6, '0': 0.62, ' ': 0.4}
    Wt = int(sum(widths.get(ch, 0.62) * H for ch in text) + g * (len(text) - 1)) + 4
    im = Image.new('L', (Wt, H + 4), 0)
    d = ImageDraw.Draw(im)
    x = 2.0; top = 2.0; bot = top + H; c = 0.2 * H   # corner chamfer

    def poly(pts):
        d.polygon([(float(a), float(b)) for a, b in pts], fill=255)

    def bar(x0, y0, x1, y1):
        if x1 > x0 and y1 > y0:
            d.rectangle([x0, y0, x1, y1], fill=255)
    for ch in text:
        w = widths.get(ch, 0.62) * H
        mid = top + 0.5 * H
        if ch == 'C':
            # left post with chamfered corners; top and bottom arms split from it by a bridge
            poly([(x + c, top), (x + c + s * 0.4, top), (x + s, top + c), (x + s, bot - c), (x + c + s * 0.4, bot), (x + c, bot), (x, bot - c), (x, top + c)])
            bar(x + c + s * 0.4 + br, top, x + w, top + s)
            bar(x + c + s * 0.4 + br, bot - s, x + w, bot)
        elif ch == 'V':
            k = s * 1.15
            poly([(x, top), (x + k, top), (x + w / 2 + k * 0.1, bot - s * 0.2), (x + w / 2 - k * 0.55, bot)])
            poly([(x + w - k, top), (x + w, top), (x + w / 2 + k * 0.55, bot), (x + w / 2 + br * 0.5, bot - s * 0.9)])
        elif ch == '-':
            bar(x, mid - s * 0.5, x + w, mid + s * 0.5)
        elif ch == '5':
            bar(x, top, x + w, top + s)
            bar(x, top + s + br, x + s, mid + s * 0.5)
            bar(x + s + br, mid - s * 0.5, x + w - c * 0.6, mid + s * 0.5)
            poly([(x + w - c * 0.6, mid - s * 0.5), (x + w, mid - s * 0.5 + c * 0.6), (x + w, bot - c), (x + w - c, bot), (x + w - s, bot - s * 0.7), (x + w - s, mid + s * 0.5)])
            bar(x, bot - s, x + w - c - br, bot)
        elif ch == '0':
            # chamfered ring, split top and bottom by bridges
            poly([(x + c, top), (x + w / 2 - br / 2, top), (x + w / 2 - br / 2, top + s), (x + c + s * 0.4, top + s), (x + s, top + c + s * 0.4),
                  (x + s, bot - c - s * 0.4), (x + c + s * 0.4, bot - s), (x + w / 2 - br / 2, bot - s), (x + w / 2 - br / 2, bot), (x + c, bot), (x, bot - c), (x, top + c)])
            X = lambda px: 2 * x + w - px
            poly([(X(x + c), top), (X(x + w / 2 - br / 2), top), (X(x + w / 2 - br / 2), top + s), (X(x + c + s * 0.4), top + s), (X(x + s), top + c + s * 0.4),
                  (X(x + s), bot - c - s * 0.4), (X(x + c + s * 0.4), bot - s), (X(x + w / 2 - br / 2), bot - s), (X(x + w / 2 - br / 2), bot), (X(x + c), bot), (X(x), bot - c), (X(x), top + c)])
        x += w + g
    return im, Wt / px_per_m, (H + 4) / px_per_m


_ST = {}


def stencil(text, h):
    if (text, h) not in _ST:
        im, wm, hm = stencil_alpha(text, h)
        _ST[(text, h)] = (np.asarray(im, np.float32) / 255, wm, hm)
    return _ST[(text, h)]


DP.stencil = stencil          # destroyer_paint.apply_decals looks the stencil up at call time


def paint(maps, spec, out, size=8192, normal_size=4096):
    return DP.paint(maps, spec, out, size=size, normal_size=normal_size)


# ------------------------------------------------------------------------------------------
# CV-50's scheme (the approved concept: light naval grey, orange bands and hazard frames on
# the bow section, dark keel wedge and radiator eaves, yellow gantries in the hangar)
# ------------------------------------------------------------------------------------------
ORANGE = [0.93, 0.45, 0.10]
YELLOW = [0.85, 0.62, 0.15]
WHITE = [0.95, 0.94, 0.91]
HAZ = {'kind': 'hazard', 'pitch': 1.6, 'color': ORANGE, 'alt': [0.16, 0.16, 0.17]}


def _lines(a, b, steps):
    out, z, i = [], a, 0
    while z < b:
        out.append(round(z, 2)); z += steps[i % len(steps)]; i += 1
    out.append(round(z, 2))
    return out


def spec():
    frames = _lines(-462.0, 462.0, [10.8, 12.6, 9.4, 13.2, 11.0, 12.0, 10.2, 13.8, 11.6, 9.8, 12.4, 11.4])
    bands = _lines(-162.0, 164.0, [6.0, 6.0, 3.0, 6.0, 9.0, 6.0, 3.0, 6.0])
    strakes = _lines(0.0, 210.0, [8.6, 10.4, 9.2, 11.0, 8.2, 9.8])
    decals = [
        # hull number, 15 m stencil letters on both flanks of the bow section (reads from outside). The dark
        # livery maps neutral paint by luminance only (white 0.06 vs the paint's 0.046: the letters vanished),
        # so they stand on a dark ID field (0.017 after the livery): ~3.5x contrast, crisp at fleet distance
        {'kind': 'fill', 'p': [D.X_END, -52.0, 346.0], 'n': [1, 0, 0], 'size': [74.0, 23.0, 3.0], 'mirrorX': True, 'color': [0.2, 0.2, 0.21], 'facing': 0.3, 'wear': 0.1},
        {'kind': 'text', 'text': 'CV-50', 'height': 15.0, 'p': [D.X_END, -52.0, 346.0], 'n': [1, 0, 0], 'size': [66.0, 17.5, 3.0], 'mirrorX': True, 'color': WHITE, 'wear': 0.12},
        # orange bands round the bow section behind the mouth (flank, chamfers, deck) and a thin one aft
        {'kind': 'fill', 'p': [D.X_END, -50.0, 392.0], 'n': [1, 0, 0], 'size': [5.0, 90.0, 3.0], 'mirrorX': True, 'color': ORANGE, 'facing': 0.3},
        {'kind': 'fill', 'p': [115.0, 8.0, 392.0], 'n': [0.707, 0.707, 0], 'up': [-0.707, 0.707, 0], 'size': [5.0, 46.0, 4.0], 'mirrorX': True, 'color': ORANGE, 'facing': 0.3},
        {'kind': 'fill', 'p': [0.0, 24.0, 392.0], 'n': [0, 1, 0], 'up': [0, 0, 1], 'size': [200.0, 5.0, 3.0], 'color': ORANGE, 'facing': 0.5},
        {'kind': 'fill', 'p': [D.X_END, -50.0, 380.0], 'n': [1, 0, 0], 'size': [1.6, 90.0, 3.0], 'mirrorX': True, 'color': ORANGE, 'facing': 0.3},
        {'kind': 'fill', 'p': [D.X_END, -50.0, -300.0], 'n': [1, 0, 0], 'size': [3.0, 40.0, 3.0], 'mirrorX': True, 'color': ORANGE, 'facing': 0.3},
        # hazard frame round the mouth lip's face, and on the frame rings' bay-facing edges
        {**HAZ, 'p': [0.0, -48.7, D.Z_LIP], 'n': [0, 0, 1], 'size': [204.0, 99.0, 1.2], 'border': 3.2},
        # deck edges at the flank openings (the drop to the sill): hazard strips on the decks
        {**HAZ, 'p': [117.5, D.Y_LONG, (D.FRAMES[0][1] + D.FRAMES[4][0]) / 2], 'n': [0, 1, 0], 'up': [0, 0, 1], 'size': [3.0, D.FRAMES[4][0] - D.FRAMES[0][1], 0.6], 'mirrorX': True},
        {**HAZ, 'p': [117.5, D.Y_AFT, (D.Z_SF + D.FRAMES[0][0]) / 2], 'n': [0, 1, 0], 'up': [0, 0, 1], 'size': [3.0, D.FRAMES[0][0] - D.Z_SF, 0.6], 'mirrorX': True},
        {**HAZ, 'p': [117.5, D.Y_BAY1, (D.FRAMES[4][1] + D.Z_BA) / 2], 'n': [0, 1, 0], 'up': [0, 0, 1], 'size': [3.0, D.Z_BA - D.FRAMES[4][1], 0.6], 'mirrorX': True},
        # launch lane in the bow section: centre line and lift frame
        {'kind': 'fill', 'p': [0.0, D.Y_BOW, 372.0], 'n': [0, 1, 0], 'up': [0, 0, 1], 'size': [0.8, 84.0, 0.6], 'color': YELLOW, 'wear': 0.35},
        {**HAZ, 'p': [0.0, D.Y_BOW, D.Z_BA + 0.38 * (415.0 - 276.8) + 0.8], 'n': [0, 1, 0], 'up': [0, 0, 1], 'size': [58.0, 48.0, 0.6], 'border': 1.6},
        # stern plate: hazard frames round the grilles
        {**HAZ, 'p': [0.0, -50.0, D.Z_STERN], 'n': [0, 0, -1], 'size': [58.0, 40.0, 1.0], 'border': 2.0},
        # sponsons: an orange band round the outer end
        {'kind': 'fill', 'p': [196.0, D.SPONSON['yc'], D.SPONSON['zc']], 'n': [0, 1, 0], 'up': [1, 0, 0], 'size': [66.0, 3.0, 50.0], 'mirrorX': True, 'color': ORANGE, 'facing': -2.0},
        # deck: landing / walk lines along the deck-edge conduits (safety yellow)
        {'kind': 'fill', 'p': [91.8, D.Y_DECK, 7.5], 'n': [0, 1, 0], 'up': [0, 0, 1], 'size': [0.5, 536.0, 0.6], 'mirrorX': True, 'color': YELLOW, 'wear': 0.4},
    ]
    return {
        'zone_names': ['paint', 'belly', 'dark', 'deck', 'recess', 'metal', 'fin', 'glass', 'nozzle', 'trim', 'safety'],
        'zones': {
            'paint': {'color': [0.80, 0.795, 0.77], 'rough': 0.62},
            'trim': {'color': [0.72, 0.72, 0.70], 'rough': 0.6},
            'belly': {'color': [0.40, 0.40, 0.41], 'rough': 0.72},
            'deck': {'color': [0.60, 0.60, 0.59], 'rough': 0.8},
            'dark': {'color': [0.22, 0.22, 0.23], 'rough': 0.7},
            'recess': {'color': [0.50, 0.50, 0.50], 'rough': 0.7},
            'metal': {'color': [0.46, 0.46, 0.46], 'rough': 0.45, 'metal': 0.5},
            'fin': {'color': [0.34, 0.34, 0.35], 'rough': 0.5, 'metal': 0.4},
            'glass': {'color': [0.13, 0.16, 0.2], 'rough': 0.1},
            'nozzle': {'color': [0.2, 0.2, 0.2], 'rough': 0.5, 'metal': 0.6},
            'safety': {'color': [0.78, 0.58, 0.16], 'rough': 0.55},
        },
        'plated': ['paint', 'deck', 'trim', 'belly'],
        'seams': {'frames': frames, 'bands': bands, 'strakes': strakes,
                  'width': 0.24, 'stagger': 5.2, 'tone': 0.07, 'dark': 0.45, 'access': 0.28, 'access_dark': 0.4},
        'normal': {'seam_depth': 0.03, 'access_depth': 0.016, 'seam_w': 1.2, 'strength': 1.0},
        'patina': {'tile': 6.0, 'tone': 0.25},
        'grime': {'ao': 0.35, 'crease': 0.3, 'edge': 0.5, 'blotch': 0.08, 'blotch2': 0.08, 'streak': 0.08},
        'decals': decals,
    }
