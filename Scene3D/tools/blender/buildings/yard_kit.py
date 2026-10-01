"""Yard kit: reusable, parametric parts for cqs-fleet installations (shipyard first).

Built with the fleet's procedural parts pipeline (tools/blender/lib.py: lib.Part primitives ->
bevel + weighted normals -> smart UV -> Cycles bake of a weathered base colour (panel tone, AO
grime, curvature edge wear) and ORM -> one glTF material -> tools/optimize-glb.mjs), so the yard
parts weather and shade exactly like the ship kit (assets/parts-blender).

    PY=<venv with bpy>/bin/python
    $PY tools/blender/buildings/yard_kit.py                # every part
    $PY tools/blender/buildings/yard_kit.py crane hall      # only these
    options: --threads 4  --samples 12  --tex-scale 1.0  --list

Output: assets/parts-yard/<part>.glb + assets/parts-yard/parts.json (bbox, tris, tex, mount and
each part's anchors: lamp, window, flood, door, ladder and hook points in the PART frame).

PART FRAME (all yard parts): metres, +Y up, the part stands on y = 0, origin at the centre of its
footprint, +Z its front / forward, +X its left. parts.json mount.normal is '+Y', so
tools/blender/assemble.py stands the part with +Y along the placement normal and +X along
`along` (rot turns it about +Y). This differs from the ship kit (+Z out of the hull) on purpose:
yard parts stand on the ground.

Parts (the parameters are the defaults the shipyard uses; other buildings pass their own):
  gantry        portal (goliath) gantry: span 96 m between rail centres, 95 m clear height, double
                box girder, A-frame legs on sill beams and bogies, crab with hoist house, machinery
                house, girder number in the fleet stencil (mark='01')
  crane         slim level-luffing portal crane: 12 m portal on rails along Z, slewing house and cab,
                light box jib with amber bands, beak and hook (jib 70 m, luff 60 deg)
  hall          workshop hall segment 80 x 36 x 18 m (21.5 m at the roof), light cladding with
                pilasters, chamfered roof shoulders, skylights, roof plant, a half-open end door and
                two side roller doors; anchors for kit crew doors, panes, vents, ladders, lamps
  floodMast     32 m flood mast, tapered octagonal pole, two-tier head frame for 6 kit floodlights
  scaffold      scaffold tower, 2.5 m bays x 1.3 m, 2 m lifts (sizes S / M / L: 4, 7, 11 lifts)
  truck         semi: cab-over tractor + 13.6 m box trailer, 16.5 m long
  forklift      3.4 m counterbalance forklift, amber
  worker        1.8 m crew figure, hard hat and amber vest
  keelBlock     keel / bilge block 2 m tall (scale y for other heights)
  bollard       1.1 m amber lamp bollard (the lamp itself is a lightscape pin at anchors.lamp)
Container stacks are not a part: shipyard_spec.py's container_stack() expands into kit
`container` placements (assets/parts-blender), so the ISO ruler stays one part.
"""
import argparse
import json
import math
import os
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(BLENDER, '..', '..'))
sys.path.insert(0, BLENDER)

import lib  # noqa: E402
from lib import chamfer_rect, rrect  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

OUT = os.path.join(ROOT, 'assets', 'parts-yard')
SCRATCH = os.environ.get('YARD_SCRATCH', os.path.join(tempfile.gettempdir(), 'cqs-yard-kit'))
DEG = math.pi / 180
V = Vector

# Yard materials (linear base colour, kind, roughness, metal), added to lib.MATS at import (lib.py
# itself is shared and not edited). Light paint on buildings (correction 27), dark steel on the gantry
# and the crane portals (concept), amber (0.93, 0.58, 0.12 sRGB) for hazard bands (STYLE.md Palette).
YARD_MATS = {
    'charcoal':  ((0.036, 0.038, 0.042), 'paint', 0.6, 0.0),   # dark painted steel (gantry, crane portals)
    'charcoal2': ((0.060, 0.062, 0.066), 'paint', 0.62, 0.0),  # its panels / houses
    'cladding':  ((0.50, 0.505, 0.50), 'paint', 0.72, 0.0),    # hall cladding, light concept paint
    'cladding2': ((0.40, 0.405, 0.405), 'paint', 0.72, 0.0),   # pilasters, door leaves
    'amber':     ((0.85, 0.30, 0.013), 'paint', 0.55, 0.0),    # hazard / marking amber
    'white':     ((0.72, 0.72, 0.70), 'paint', 0.55, 0.0),     # stencil white, jib paint
    'concrete':  ((0.15, 0.15, 0.145), 'paint', 0.9, 0.0),     # plinths, block bases
    'timber':    ((0.16, 0.10, 0.055), 'paint', 0.85, 0.0),    # keel-block caps, planks
    'galv':      ((0.36, 0.37, 0.37), 'metal', 0.5, 0.7),      # galvanised tube (scaffold, masts)
}
lib.MATS.update(YARD_MATS)


# --------------------------------------------------------------------------------------------
# helpers (part frame)
# --------------------------------------------------------------------------------------------
def frame_along(p0, p1, up=(0, 1, 0)):
    """4x4 with +Z along p0 -> p1, +Y toward `up`, origin at p0."""
    p0, p1 = V(p0), V(p1)
    z = (p1 - p0).normalized()
    u = V(up)
    y = u - z * u.dot(z)
    if y.length < 1e-6:
        y = V((1, 0, 0)) - z * z.x
    y.normalize()
    x = y.cross(z)
    return lib.basis(p0, x, y, z)


def beam(P, p0, p1, w, h, mat, up=(0, 1, 0), bevel=None, ext=0.0):
    """Box beam p0 -> p1 (extended by ext at both ends), section w (x) by h (toward up)."""
    L = (V(p1) - V(p0)).length + 2 * ext
    with P.at(M=frame_along(p0, p1, up)):
        kw = {} if bevel is None else {'bevel': bevel}
        P.box((w, h, L), at=(0, 0, L / 2 - ext), mat=mat, **kw)


def strut(P, p0, p1, s0, s1, ch, mat, up=(0, 1, 0), bevel=0.06):
    """Tapered chamfered-rectangle strut p0 -> p1, sections s0 = (w, h) at p0, s1 at p1."""
    L = (V(p1) - V(p0)).length
    with P.at(M=frame_along(p0, p1, up)):
        P.loft([(chamfer_rect(s0[0], s0[1], ch), 0.0), (chamfer_rect(s1[0], s1[1], ch), L)], closed=False, mat=mat, bevel=bevel)


def tube(P, pts, r, mat, n=6):
    P.tube([tuple(p) for p in pts], r, n=n, mat=mat, bevel=0.0)


def vcyl(P, r, h, at, mat, n=16, r2=None, bevel=None):
    """Vertical cylinder standing on at (base centre)."""
    kw = {} if bevel is None else {'bevel': bevel}
    P.cyl(r, h, at=(at[0], at[1] + h / 2, at[2]), rot=(90, 0, 0), n=n, r2=r2, mat=mat, **kw)


# fleet stencil glyphs (hulltex.stencil_alpha construction: strokes 0.185 h, butt ends, mitred
# corners, 0.11 h spacing) as 2D polygons in (u, v), v up, glyph box from (0, -h/2) to (w, h/2)
GLYPH_W = {'0': 0.62, '1': 0.46, '2': 0.66, '-': 0.40}


def glyph_polys(ch, h):
    s = 0.185 * h
    w = GLYPH_W.get(ch, 0.62) * h
    Y = h / 2
    if ch == '0':
        X = w / 2; c = 0.22 * h; g = 0.11 * h  # stencil bridges at top and bottom centre
        Xi, Yi = X - s, Y - s
        ci = max(c - s * 0.414, 0.04 * h)
        left = [(-g / 2, Y), (-X + c, Y), (-X, Y - c), (-X, -Y + c), (-X + c, -Y), (-g / 2, -Y),
                (-g / 2, -Yi), (-Xi + ci, -Yi), (-Xi, -Yi + ci), (-Xi, Yi - ci), (-Xi + ci, Yi), (-g / 2, Yi)]
        right = [(-x, y) for x, y in reversed(left)]
        return [[(x + X, y) for x, y in left], [(x + X, y) for x, y in right]]
    if ch == '1':
        sx = w - s * 1.1
        bar = [(sx, -Y), (w, -Y), (w, Y), (sx, Y)]
        flag = [(0, Y - 0.36 * h - s * 0.0), (sx, Y - s * 1.25), (sx, Y), (0, Y - 0.36 * h + s * 1.25)]
        return [bar, flag]
    if ch == '-':
        return [[(0, -s * 0.525), (w, -s * 0.525), (w, s * 0.525), (0, s * 0.525)]]
    raise ValueError(ch)


def stencil(P, text, h, centre, normal, up=(0, 1, 0), depth=0.12, mat='white'):
    """Raised stencil text centred on `centre` on a face with outward `normal` (reads from outside)."""
    total = sum(GLYPH_W.get(c, 0.62) * h for c in text) + 0.11 * h * (len(text) - 1)
    n = V(normal).normalized()
    u_up = V(up)
    y = (u_up - n * u_up.dot(n)).normalized()
    x = y.cross(n)  # reading direction seen from outside
    M = lib.basis(V(centre), x, y, n)
    u = -total / 2
    with P.at(M=M):
        for ch in text:
            for poly in glyph_polys(ch, h):
                P.prism([(px + u, py) for px, py in poly], -0.02, depth, mat=mat, bevel=0.0, sharp=40)
            u += GLYPH_W.get(ch, 0.62) * h + 0.11 * h


def boolean_cut(target, cutters):
    """EXACT boolean DIFFERENCE of closed box cutters [(centre, size)] from a part object."""
    import bpy
    import bmesh
    for k, (c, size) in enumerate(cutters):
        bm = lib.bm_box(*size)
        me = bpy.data.meshes.new(f'cut{k}')
        bm.to_mesh(me); bm.free()
        ob = bpy.data.objects.new(f'cut{k}', me)
        ob.location = c
        bpy.context.scene.collection.objects.link(ob)
        ob.hide_render = True
        m = target.modifiers.new(f'cut{k}', 'BOOLEAN')
        m.operation = 'DIFFERENCE'
        m.solver = 'EXACT'
        m.object = ob
        yield ob


# --------------------------------------------------------------------------------------------
# gantry
# --------------------------------------------------------------------------------------------
def gantry(P, span=96.0, clear=95.0, depth=10.0, gw=4.5, gap=7.0, over=8.0, mark='01', trolley_x=0.0):
    hx = span / 2
    g0, g1 = clear, clear + depth                 # girder underside / top
    meta = {'lampsAmber': [], 'beacons': [], 'obstruction': [], 'windows': [], 'ladders': [], 'rails': [], 'slits': []}
    zo = gap / 2 + gw                             # outer face of the girder pair
    L = span + 2 * over
    for sx in (-1, 1):
        x = sx * hx
        # bogies with wheels on the rail, sill beam, hazard end caps and rail buffers
        for z in (-20.5, -12.5, 12.5, 20.5):
            P.box((3.0, 2.4, 6.4), at=(x, 1.7, z), mat='charcoal', bevel=0.1)
            for dz in (-2.0, 2.0):
                P.cyl(0.6, 3.3, at=(x, 0.65, z + dz), rot=(0, 90, 0), n=14, mat='galv', bevel=0.03)
        P.box((4.2, 3.4, 50.0), at=(x, 4.6, 0), mat='charcoal', bevel=0.14)
        for sz in (-1, 1):
            P.box((4.3, 3.5, 1.4), at=(x, 4.6, sz * 24.4), mat='amber', bevel=0.06)
            P.box((1.6, 1.6, 1.4), at=(x, 2.2, sz * 24.9), mat='charcoal2', bevel=0.08)  # buffer
            meta['lampsAmber'].append([x + sx * 2.2, 6.4, sz * 24.9])
        # A-frame legs (tapered box legs, wider at the foot), a tie at a third of the height
        ytop = g0 + 1.0
        zf, zt = 20.0, 6.8
        for sz in (-1, 1):
            strut(P, (x, 6.0, sz * zf), (x, ytop, sz * zt), (4.8, 6.4), (4.0, 4.6), 0.55, 'charcoal', up=(0, 0, 1), bevel=0.12)
            # amber hazard band round the foot of each leg
            yb = 9.5
            zb = sz * (zf + (zt - zf) * (yb - 6.0) / (ytop - 6.0))
            strut(P, (x, yb - 1.2, sz * (zf + (zt - zf) * (yb - 7.2) / (ytop - 6.0))), (x, yb + 1.2, zb + sz * (zt - zf) * 1.2 / (ytop - 6.0)),
                  (5.0, 6.5), (4.95, 6.45), 0.55, 'amber', up=(0, 0, 1), bevel=0.04)
            # ladder cage platforms on the outer face (kit ladders run up the leg foot only)
            meta['ladders'].append({'p': [x + sx * 2.45, 7.0, sz * 18.6], 'n': [sx, 0, 0], 'count': 3})
        yt = 36.0
        zt_ = zf + (zt - zf) * (yt - 6.0) / (ytop - 6.0)
        P.box((3.4, 2.8, 2 * zt_), at=(x, yt, 0), mat='charcoal', bevel=0.1)
        # leg heads: a deep block under each girder end
        P.box((7.5, 7.0, 2 * zo + 2.0), at=(x, g0 + 0.5, 0), mat='charcoal', bevel=0.15)
    # double box girder with outboard stiffeners, end carriages over the legs
    for sz in (-1, 1):
        zc = sz * (gap / 2 + gw / 2)
        P.box((L, depth, gw), at=(0, g0 + depth / 2, zc), mat='charcoal', bevel=0.16)
        nst = int(L // 7.0)
        for i in range(nst + 1):
            xs = -L / 2 + 1.5 + i * (L - 3.0) / nst
            P.box((0.45, depth - 0.8, 0.32), at=(xs, g0 + depth / 2, sz * (zo + 0.16)), mat='charcoal2', bevel=0.03)
        # top flange lip and the crab rail
        P.box((L - 0.6, 0.5, gw + 0.6), at=(0, g1 + 0.25, zc), mat='charcoal2', bevel=0.06)
        P.box((L - 8.0, 0.35, 0.4), at=(0, g1 + 0.67, zc), mat='galv', bevel=0.02)
        # walkway rails along the outer top edge
        meta['rails'].append({'from': [-L / 2 + 1.0, g1 + 0.5, sz * (zo + 0.05)], 'to': [L / 2 - 1.0, g1 + 0.5, sz * (zo + 0.05)], 'n': [0, 1, 0]})
        # girder number in the fleet stencil, white on the dark girder, left end of both faces
        if mark:
            stencil(P, mark, 6.4, (-sz * (hx - 10.0), g0 + depth / 2, sz * (zo + 0.32)), (0, 0, sz))
    for sx in (-1, 1):
        P.box((6.5, depth + 0.6, 2 * zo + 0.6), at=(sx * (L / 2 - 3.25), g0 + depth / 2 + 0.1, 0), mat='charcoal', bevel=0.16)
    # cross diaphragms under the gap every 14 m
    for i in range(1, int(L // 14)):
        xs = -L / 2 + i * 14.0
        P.box((0.8, 1.2, gap), at=(xs, g0 + 0.6, 0), mat='charcoal2', bevel=0.04)
    # crab (trolley): frame on the girder tops, hoist house with windows, rope drums
    tx = trolley_x
    P.box((14.0, 2.0, 2 * zo + 0.8), at=(tx, g1 + 1.5, 0), mat='charcoal2', bevel=0.12)
    for sx in (-1, 1):
        P.cyl(1.3, 2 * zo - 1.0, at=(tx + sx * 3.6, g1 + 3.3, 0), rot=(0, 0, 0), n=20, mat='galv', bevel=0.04)
    P.box((8.5, 6.0, 11.0), at=(tx + 1.0, g1 + 2.5 + 3.0 + 1.0, 0), mat='charcoal2', bevel=0.12)
    P.box((8.9, 0.5, 11.4), at=(tx + 1.0, g1 + 9.75, 0), mat='charcoal', bevel=0.06)
    for k in range(3):
        meta['windows'].append({'p': [tx + 1.0 - 2.4 + k * 2.4, g1 + 7.8, 5.5 + 0.02], 'n': [0, 0, 1], 'size': [1.2, 1.0]})
    meta['hook'] = [tx, g0, 0]
    meta['beacons'] += [[tx + 1.0 + 3.8, g1 + 10.2, 5.2], [tx + 1.0 - 3.8, g1 + 10.2, -5.2]]
    # machinery house on the +X end carriage, an operator cab hung under the -X end
    P.box((10.0, 5.5, 2 * zo + 0.6), at=(hx + 3.0, g1 + 2.75 + 0.5, 0), mat='charcoal2', bevel=0.12)
    meta['obstruction'] += [[hx + 7.6, g1 + 6.6, 0], [-L / 2 + 0.6, g1 + 0.9, 0]]
    cab = (-hx + 9.0, g0 - 2.4, zo - 2.2)
    P.box((5.0, 3.6, 4.0), at=cab, mat='charcoal2', bevel=0.08)
    P.box((0.6, 3.2, 0.6), at=(cab[0], g0 - 0.3, cab[2]), mat='charcoal', bevel=0.04)
    for k in range(2):
        meta['windows'].append({'p': [cab[0] - 1.1 + k * 2.2, cab[1] + 0.2, cab[2] + 2.02], 'n': [0, 0, 1], 'size': [1.6, 1.3]})
    # amber corner lamps on the girder ends (top corners) and leg heads
    for sx in (-1, 1):
        for sz in (-1, 1):
            meta['lampsAmber'].append([sx * (L / 2 - 0.2), g1 + 0.7, sz * (zo + 0.1)])
            meta['slits'].append({'p': [sx * (hx + 3.76), g0 - 1.6, sz * (zo - 1.0)], 'u': [0, 1, 0], 'n': [sx, 0, 0], 'len': 1.6})
    meta['about'] = f'portal gantry: span {span} m between rail centres (rails along Z at x = +-{hx}), {clear} m clear under the girders, girder top {g1} m'
    meta['span'] = span
    meta['clear'] = clear
    return meta


# --------------------------------------------------------------------------------------------
# luffing crane
# --------------------------------------------------------------------------------------------
def crane(P, jib=70.0, luff=60.0, gauge=12.0, portal=14.0, slew=0.0, hook=30.0):
    meta = {'lampsAmber': [], 'beacons': [], 'obstruction': [], 'windows': []}
    gx, gz = gauge / 2, 5.0
    for sx in (-1, 1):
        for sz in (-1, 1):
            P.box((1.8, 1.6, 4.0), at=(sx * gx, 1.1, sz * gz), mat='charcoal', bevel=0.08)
            for dz in (-1.1, 1.1):
                P.cyl(0.45, 1.9, at=(sx * gx, 0.5, sz * gz + dz), rot=(0, 90, 0), n=12, mat='galv', bevel=0.02)
            strut(P, (sx * gx, 2.0, sz * gz), (sx * 3.0, portal, sz * 3.0), (1.6, 1.6), (1.2, 1.2), 0.25, 'charcoal', bevel=0.06)
            P.box((2.0, 0.9, 4.2), at=(sx * gx, 2.4, sz * gz), mat='amber', bevel=0.05)
        # portal braces
        beam(P, (sx * (gx - 0.6), 6.5, -gz + 0.4), (sx * (gx - 0.6), 6.5, gz - 0.4), 0.9, 1.2, 'charcoal', bevel=0.05)
    for sz in (-1, 1):
        beam(P, (-gx + 0.8, 7.5, sz * (gz - 0.5)), (gx - 0.8, 7.5, sz * (gz - 0.5)), 0.9, 1.2, 'charcoal', bevel=0.05)
    P.box((8.0, 1.6, 8.0), at=(0, portal + 0.3, 0), mat='charcoal', bevel=0.1)
    meta['lampsAmber'] += [[sx * (gx + 0.95), 2.8, sz * (gz + 2.1)] for sx in (-1, 1) for sz in (-1, 1)]
    y0 = portal + 1.1
    with P.at(rot=(0, slew, 0)):
        P.cyl(4.0, 1.2, at=(0, y0 + 0.6, 0), rot=(90, 0, 0), n=24, mat='charcoal2', bevel=0.05)
        # machinery house and counterweight
        P.box((7.0, 6.5, 10.5), at=(0, y0 + 1.2 + 3.25, -1.5), mat='charcoal2', bevel=0.12)
        P.box((7.4, 0.4, 10.9), at=(0, y0 + 7.9, -1.5), mat='charcoal', bevel=0.04)
        P.box((6.2, 4.0, 2.6), at=(0, y0 + 3.4, -8.1), mat='charcoal', bevel=0.1)
        # cab beside the jib foot with a front window band
        P.box((2.6, 3.0, 3.2), at=(3.6, y0 + 3.4, 5.0), mat='white', bevel=0.08)
        meta['windows'].append({'p': [3.6, y0 + 3.9, 6.62], 'n': [0, 0, 1], 'size': [2.0, 1.1]})
        meta['windows'].append({'p': [4.92, y0 + 3.9, 5.3], 'n': [1, 0, 0], 'size': [1.6, 1.0]})
        # A-frame
        apex = V((0, y0 + 24.0, -3.0))
        for sx in (-1, 1):
            strut(P, (sx * 3.0, y0 + 7.5, -5.5), tuple(apex + V((sx * 0.6, 0, 0))), (1.0, 1.0), (0.7, 0.7), 0.18, 'charcoal', bevel=0.05)
            strut(P, (sx * 3.0, y0 + 7.5, 1.5), tuple(apex + V((sx * 0.6, 0, 0))), (0.8, 0.8), (0.6, 0.6), 0.15, 'charcoal', bevel=0.05)
        P.box((2.0, 1.2, 1.2), at=tuple(apex + V((0, 0.4, 0))), mat='charcoal', bevel=0.05)
        meta['beacons'].append(list(apex + V((0, 1.15, 0))))
        # jib: tapered light box girder, amber bands
        piv = V((0, y0 + 5.0, 3.5))
        d = V((0, math.sin(luff * DEG), math.cos(luff * DEG)))
        tip = piv + d * jib
        P.box((3.0, 2.0, 2.4), at=tuple(piv), mat='charcoal', bevel=0.06)
        strut(P, tuple(piv), tuple(tip), (2.4, 2.6), (1.2, 1.3), 0.3, 'white', up=(0, 1, 0), bevel=0.06)
        nb = 6
        for i in range(nb):
            t = (i + 0.5) / nb * 0.9 + 0.04
            c = piv + d * (jib * t)
            w = 2.4 + (1.2 - 2.4) * t + 0.08
            hh = 2.6 + (1.3 - 2.6) * t + 0.08
            a = c - d * 1.6; b = c + d * 1.6
            strut(P, tuple(a), tuple(b), (w, hh), (w - 0.04, hh - 0.04), 0.3, 'amber', bevel=0.03)
        # beak (horizontal nose) with sheave and the hook
        beak_end = tip + V((0, -0.6, 7.0))
        beam(P, tuple(tip + V((0, 0, -1.0))), tuple(beak_end), 1.0, 1.4, 'white', bevel=0.05)
        P.box((1.2, 1.2, 1.2), at=tuple(beak_end), mat='charcoal', bevel=0.05)
        hook_top = beak_end + V((0, -0.6, 0))
        hook_bot = hook_top + V((0, -hook, 0))
        for dx in (-0.25, 0.25):
            tube(P, [hook_top + V((dx, 0, 0)), hook_bot + V((dx, 1.0, 0))], 0.05, 'galv', n=5)
        P.box((0.9, 1.4, 0.7), at=tuple(hook_bot + V((0, 0.3, 0))), mat='amber', bevel=0.05)
        # luffing ties from the A-frame apex to the jib
        mid = piv + d * (jib * 0.62)
        for dx in (-0.5, 0.5):
            tube(P, [apex + V((dx, 0, 0)), mid + V((dx, 0.8, 0))], 0.09, 'galv', n=6)
        meta['obstruction'].append(list(beak_end + V((0, 0.85, 0))))
        meta['lampsAmber'].append(list(piv + V((1.6, 1.2, 0.6))))
    Rs = Matrix.Rotation(slew * DEG, 4, 'Y')
    for k in ('lampsAmber', 'beacons', 'obstruction'):
        meta[k] = [list(Rs @ V(p)) if i >= 4 or k != 'lampsAmber' else p for i, p in enumerate(meta[k])]
    meta['windows'] = [{**w, 'p': list(Rs @ V(w['p'])), 'n': list(Rs.to_3x3() @ V(w['n']))} for w in meta['windows']]
    meta['hook'] = list(Rs @ hook_bot)
    meta['about'] = f'level-luffing portal crane: {gauge} m gauge (rails along Z at x = +-{gx}), jib {jib} m at {luff} deg, slew {slew} deg'
    return meta


# --------------------------------------------------------------------------------------------
# workshop hall segment
# --------------------------------------------------------------------------------------------
def hall(P, L=80.0, W=36.0, H=18.0, door='front', side_doors=((1, -20.0), (1, 16.0)), office=1):
    """door: 'front' (+Z end) | 'back' | 'both' | None. side_doors: [(side +-1 (x), z)].
    office: +-1 side with the office windows (near the door end), 0 none."""
    meta = {'lampsAmber': [], 'beacons': [], 'windows': [], 'panes': [], 'doors': [], 'vents': [], 'ladders': [], 'slits': [], 'glow': []}
    hw = W / 2
    sh, rise = 4.0, 3.5                           # roof shoulder chamfer (run, rise)
    prof = [(hw, 0.0), (hw, H), (hw - sh, H + rise), (-hw + sh, H + rise), (-hw, H), (-hw, 0.0)]
    with P.at(rot=(0, 0, 0)):
        body = P.prism(prof, -L / 2, L / 2, mat='cladding', bevel=0.08)
    ends = {'front': [1], 'back': [-1], 'both': [1, -1], None: []}[door]
    cut = []
    dw, dh = 20.0, 14.0
    for e in ends:
        cut.append(((0, dh / 2, e * (L / 2)), (dw, dh, 3.0)))          # door recess (1.5 m deep)
        cut.append(((0, 2.75, e * (L / 2 - 4.0)), (dw - 0.01, 5.5, 8.0)))  # open lower part: 5.5 m clear, 5.5 m deep
    for sd, z in side_doors:
        cut.append(((sd * hw, 4.5, z), (2.4, 9.0, 8.0)))
    cutters = list(boolean_cut(body, cut))
    # door leaves: roller shutter (upper part of the end door), side roller doors; dark interior back walls
    for e in ends:
        P.box((dw, dh - 5.5, 0.3), at=(0, 5.5 + (dh - 5.5) / 2, e * (L / 2 - 1.2)), mat='cladding2', bevel=0.03)
        for k in range(8):
            P.box((dw - 0.4, 0.06, 0.08), at=(0, 6.0 + k * 1.0, e * (L / 2 - 1.0)), mat='charcoal2', bevel=0.0)
        P.box((dw - 0.02, 5.4, 0.4), at=(0, 2.75, e * (L / 2 - 7.6)), mat='charcoal', bevel=0.0)
        P.box((dw + 2.4, 1.0, 0.8), at=(0, dh + 0.5, e * (L / 2 + 0.2)), mat='charcoal2', bevel=0.05)   # lintel
        for sx in (-1, 1):
            P.box((1.2, dh + 1.0, 0.8), at=(sx * (dw / 2 + 0.6), (dh + 1.0) / 2, e * (L / 2 + 0.2)), mat='amber', bevel=0.04)
            meta['slits'].append({'p': [sx * (dw / 2 + 0.6), dh - 1.0, e * (L / 2 + 0.62)], 'u': [0, 1, 0], 'n': [0, 0, e], 'len': 1.4})
        meta['glow'].append({'p': [0, 2.75, e * (L / 2 - 7.38)], 'size': [dw - 1.0, 4.4], 'n': [0, 0, e]})
    for sd, z in side_doors:
        P.box((0.3, 8.0, 7.6), at=(sd * (hw - 0.9), 4.0 + 1.0, z), mat='cladding2', bevel=0.03)
        P.box((0.8, 1.0, 9.0), at=(sd * (hw + 0.2), 9.5, z), mat='charcoal2', bevel=0.04)
        # crew door beside each roller door
        meta['doors'].append({'p': [sd * (hw + 0.01), 0.0, z + 7.0 * sd], 'n': [sd, 0, 0]})
        meta['slits'].append({'p': [sd * (hw + 0.12), 2.75, z + 7.0 * sd], 'u': [0, 0, 1], 'n': [sd, 0, 0], 'len': 0.6, 'width': 0.14, 'door': True})
    # plinth, eaves band, pilasters (one bay = 10 m), shoulder ribs, end-wall pilasters
    P.box((W + 0.2, 1.3, L + 0.2), at=(0, 0.65, 0), mat='concrete', bevel=0.04)
    for sx in (-1, 1):
        P.box((0.5, 0.6, L + 0.2), at=(sx * (hw + 0.2), H + 0.1, 0), mat='charcoal2', bevel=0.04)
        nb = int(round(L / 10.0))
        for i in range(nb + 1):
            z = -L / 2 + 0.6 + i * (L - 1.2) / nb
            if any(abs(z - zd) < 2.0 for sd, zd in side_doors if sd == sx):
                continue
            P.box((0.7, H - 1.0, 1.1), at=(sx * (hw + 0.3), 1.3 + (H - 1.3) / 2, z), mat='cladding2', bevel=0.06)
            with P.at(M=frame_along((sx * hw, H - 0.3, z), (sx * (hw - sh), H + rise, z))):
                P.box((1.1, 0.6, 5.6), at=(0, 0.2, 2.6), mat='cladding2', bevel=0.05)
    for e in (-1, 1):
        for xk in (-1, 1):
            for xo in ((hw - 0.6), (dw / 2 + 4.0)):
                P.box((1.1, H - 1.0, 0.7), at=(xk * xo, 1.3 + (H - 1.3) / 2, e * (L / 2 + 0.3)), mat='cladding2', bevel=0.06)
    # roof: skylight bands, plant boxes, a parapet stub at the ladder
    for xk in (-7.0, 0.0, 7.0):
        P.box((2.4, 0.5, L - 10.0), at=(xk, H + rise + 0.25, 0), mat='cladding2', bevel=0.05)
        P.box((1.9, 0.08, L - 10.6), at=(xk, H + rise + 0.52, 0), mat='glass', bevel=0.0)
    for (xk, z, s) in ((-3.5, -L / 2 + 12, (4.0, 2.4, 3.0)), (3.5, -L / 2 + 16, (3.0, 2.0, 3.0)), (-3.5, L / 2 - 14, (5.0, 2.6, 3.4)), (10.5, 2.0, (3.0, 1.6, 2.4))):
        P.box(s, at=(xk, H + rise + s[1] / 2, z), mat='charcoal2', bevel=0.06)
        meta['vents'].append({'p': [xk, H + rise + s[1] + 0.01, z], 'n': [0, 1, 0]})
    # office windows: two rows of kit panes near the door end, some lit (glow anchors)
    if office:
        sx = office
        z0 = L / 2 - 16.0
        for row, y in enumerate((4.2, 7.6)):
            for k in range(7):
                z = z0 + (k - 3) * 1.12
                meta['panes'].append({'p': [sx * (hw + 0.02), y, z], 'n': [sx, 0, 0]})
        meta['doors'].append({'p': [sx * (hw + 0.01), 0.0, z0 + 6.5], 'n': [sx, 0, 0]})
        meta['slits'].append({'p': [sx * (hw + 0.12), 2.75, z0 + 6.5], 'u': [0, 0, 1], 'n': [sx, 0, 0], 'len': 0.6, 'width': 0.14, 'door': True})
    # wall vents high on the long sides, a roof ladder on the -Z end
    for sx in (-1, 1):
        for z in (-L / 2 + 6.0, -5.0, L / 2 - 26.0):
            meta['vents'].append({'p': [sx * (hw + 0.01), H - 2.5, z], 'n': [sx, 0, 0]})
    meta['ladders'].append({'p': [hw - 2.0, 1.3, -L / 2 - 0.01], 'n': [0, 0, -1], 'count': 7})
    # amber pins at the roof shoulder corners (block corners)
    for sx in (-1, 1):
        for e in (-1, 1):
            meta['lampsAmber'].append([sx * (hw + 0.1), H + 0.2, e * (L / 2 + 0.1)])
    meta['about'] = f'workshop hall segment {L} x {W} m, eaves {H} m, roof {H + rise} m; end door {dw} x {dh} m ({door}), side roller doors {list(side_doors)}'
    meta['size'] = [W, H + rise, L]
    meta['_cutters'] = cutters
    return meta


# --------------------------------------------------------------------------------------------
# flood mast
# --------------------------------------------------------------------------------------------
def floodMast(P, h=32.0, lamps=(3, 2), pitch=0.72):
    meta = {'floods': [], 'lampsAmber': []}
    P.box((2.0, 1.2, 2.0), at=(0, 0.6, 0), mat='concrete', bevel=0.06)
    P.box((1.3, 0.3, 1.3), at=(0, 1.35, 0), mat='charcoal', bevel=0.03)
    P.cyl(0.42, h - 1.5, at=(0, 1.5 + (h - 1.5) / 2, 0), rot=(90, 0, 0), n=8, r2=0.22, mat='galv', bevel=0.02)
    P.box((1.0, 1.4, 0.8), at=(0, 2.8, 0.5), mat='charcoal2', bevel=0.04)           # control box
    nx, ny = lamps
    wf = nx * pitch + 0.4
    for j in range(ny):
        y = h - 0.2 - j * 0.85
        P.box((wf, 0.14, 0.16), at=(0, y - 0.32, 0.24), mat='charcoal', bevel=0.01)
        for i in range(nx):
            x = (i - (nx - 1) / 2) * pitch
            # kit floodlight mounted upside down on the bar's front: lamp faces down, pitched 25 deg out (+Z)
            meta['floods'].append({'p': [x, y - 0.32, 0.33], 'n': [0, 0, 1], 'up': [0, -1, 0]})
    P.box((0.3, 1.6, 0.3), at=(0, h - 0.6, 0.1), mat='charcoal', bevel=0.02)
    P.box((2.6, 0.1, 1.4), at=(0, h - 2.2, -0.2), mat='galv', bevel=0.0)                # service platform
    meta['light'] = {'p': [0, h - 0.9, 0.9], 'dir': [0, -math.sin(55 * DEG), math.cos(55 * DEG)]}
    meta['about'] = f'flood mast {h} m with {nx * ny} kit floodlights facing +Z (anchors.floods), spot anchor anchors.light'
    return meta


# --------------------------------------------------------------------------------------------
# scaffold tower
# --------------------------------------------------------------------------------------------
def scaffold(P, bx=2, bz=1, lifts=7, bay=2.5, wid=1.3, lift=2.0, r=0.035):
    W, D = bx * bay, bz * wid
    H = lifts * lift
    xs = [-W / 2 + i * bay for i in range(bx + 1)]
    zs = [-D / 2 + j * wid for j in range(bz + 1)]
    for x in xs:
        for z in zs:
            tube(P, [(x, 0.1, z), (x, H + 1.0, z)], r, 'galv', n=6)
            P.box((0.2, 0.06, 0.2), at=(x, 0.03, z), mat='charcoal', bevel=0.0)
    for k in range(1, lifts + 1):
        y = k * lift
        for z in zs:
            tube(P, [(xs[0], y, z), (xs[-1], y, z)], r, 'galv', n=6)
        for x in xs:
            tube(P, [(x, y, zs[0]), (x, y, zs[-1])], r, 'galv', n=6)
        if k % 2 == 0 or k == lifts:
            P.box((W, 0.06, D), at=(0, y + 0.04, 0), mat='timber', bevel=0.0)
            for z in zs:
                P.box((W, 0.18, 0.03), at=(0, y + 0.16, z), mat='amber', bevel=0.0)
            for z in zs:
                tube(P, [(xs[0], y + 1.0, z), (xs[-1], y + 1.0, z)], r, 'galv', n=6)
    # facade diagonals on the long faces
    for z in zs:
        for k in range(lifts):
            i = k % bx
            a = (xs[i], k * lift, z); b = (xs[i + 1], (k + 1) * lift, z)
            tube(P, [a, b], r * 0.9, 'galv', n=5)
    return {'about': f'scaffold tower {W} x {D} m, {lifts} lifts of {lift} m ({H} m), tubes {2 * r} m', 'height': H}


# --------------------------------------------------------------------------------------------
# vehicles and people
# --------------------------------------------------------------------------------------------
def wheel(P, x, y, z, r=0.5, w=0.35):
    P.cyl(r, w, at=(x, y, z), rot=(0, 90, 0), n=14, mat='rubber', bevel=0.02)
    P.cyl(r * 0.55, w + 0.02, at=(x, y, z), rot=(0, 90, 0), n=10, mat='galv', bevel=0.0)


def truck(P, trailer=13.6):
    meta = {'lampsAmber': []}
    # tractor: cab-over at +Z
    zc = trailer / 2 + 0.2
    P.box((2.5, 2.6, 2.3), at=(0, 1.15 + 1.3 + 0.1, zc + 1.25), mat='white', bevel=0.08)
    P.box((2.3, 1.0, 0.06), at=(0, 2.95, zc + 2.42), mat='glass', bevel=0.0)
    P.box((2.4, 0.9, 1.6), at=(0, 4.1, zc + 0.95), mat='white', bevel=0.08)         # roof fairing
    P.box((1.0, 1.0, 5.4), at=(0, 0.9, zc + 0.3), mat='charcoal', bevel=0.04)       # chassis
    P.box((2.5, 0.35, 0.2), at=(0, 0.75, zc + 2.4), mat='charcoal', bevel=0.03)
    for z in (zc + 1.4, zc - 1.6):
        for sx in (-1, 1):
            wheel(P, sx * 1.05, 0.52, z, 0.52)
    meta['lampsAmber'] += [[sx * 0.9, 4.58, zc + 1.6] for sx in (-1, 1)]
    # box trailer
    P.box((2.55, 2.75, trailer), at=(0, 1.35 + 1.375, -0.4), mat='cladding', bevel=0.06)
    P.box((2.0, 0.4, trailer - 1.0), at=(0, 1.15, -0.4), mat='charcoal', bevel=0.03)
    for z in (-trailer / 2 + 0.6, -trailer / 2 + 1.9, -trailer / 2 + 3.2):
        for sx in (-1, 1):
            wheel(P, sx * 1.0, 0.52, z, 0.52)
    for sx in (-1, 1):
        P.box((0.06, 0.2, trailer - 2.0), at=(sx * 1.29, 1.5, -0.4), mat='amber', bevel=0.0)
    return {**meta, 'about': f'semi: cab-over tractor + {trailer} m box trailer, front +Z, {trailer + 2.9:.1f} m long'}


def forklift(P):
    P.box((1.2, 1.0, 2.2), at=(0, 0.75, -0.2), mat='amber', bevel=0.06)
    P.box((1.2, 0.9, 0.6), at=(0, 0.75, -1.5), mat='charcoal', bevel=0.06)
    for sx in (-1, 1):
        for z in (-1.0, 0.6):
            wheel(P, sx * 0.55, 0.32, z, 0.32, 0.25)
        tube(P, [(sx * 0.55, 1.25, -1.0), (sx * 0.55, 2.2, -0.8), (sx * 0.55, 2.2, 0.5), (sx * 0.55, 1.25, 0.7)], 0.04, 'charcoal', n=5)
        P.box((0.1, 3.0, 0.14), at=(sx * 0.35, 1.6, 1.05), mat='charcoal', bevel=0.01)
        P.box((0.12, 0.06, 1.1), at=(sx * 0.3, 0.12, 1.65), mat='galv', bevel=0.0)
    P.box((1.2, 0.04, 1.4), at=(0, 2.22, -0.15), mat='charcoal', bevel=0.0)
    P.box((0.8, 0.5, 0.08), at=(0, 0.55, 1.12), mat='charcoal', bevel=0.0)
    return {'about': '3.4 m counterbalance forklift, forks +Z', 'lampsAmber': [[0, 2.32, -0.6]]}


def worker(P, hat='white'):
    for sx in (-1, 1):
        P.box((0.16, 0.86, 0.2), at=(sx * 0.1, 0.43, 0), mat='charcoal2', bevel=0.02)
        P.box((0.1, 0.6, 0.12), at=(sx * 0.27, 1.12, 0.02), mat='charcoal2', bevel=0.02)
    P.box((0.44, 0.62, 0.26), at=(0, 1.16, 0), mat='amber', bevel=0.04)
    P.cyl(0.1, 0.2, at=(0, 1.62, 0), rot=(90, 0, 0), n=8, mat='cladding2', bevel=0.02)
    P.cyl(0.14, 0.09, at=(0, 1.755, 0), rot=(90, 0, 0), n=10, r2=0.1, mat=hat, bevel=0.01)
    return {'about': '1.8 m crew figure (fleet ruler), amber vest, hard hat'}


def keelBlock(P, h=2.0):
    P.box((3.0, 0.8, 2.2), at=(0, 0.4, 0), mat='concrete', bevel=0.04)
    P.box((2.4, h - 1.2, 1.6), at=(0, 0.8 + (h - 1.2) / 2, 0), mat='charcoal', bevel=0.04)
    P.box((2.6, 0.4, 1.8), at=(0, h - 0.2, 0), mat='timber', bevel=0.03)
    return {'about': f'keel block {h} m (concrete base, steel crib, timber cap); scale y for other heights'}


def bollard(P):
    P.box((0.36, 0.2, 0.36), at=(0, 0.1, 0), mat='concrete', bevel=0.02)
    P.cyl(0.11, 0.85, at=(0, 0.62, 0), rot=(90, 0, 0), n=8, mat='charcoal', bevel=0.01)
    P.cyl(0.13, 0.14, at=(0, 1.1, 0), rot=(90, 0, 0), n=10, mat='lens', bevel=0.0)
    return {'about': '1.1 m lamp bollard: the amber lamp is a lightscape pin at anchors.lamp', 'lamp': [0, 1.12, 0]}


# --------------------------------------------------------------------------------------------
REGISTRY = {
    'gantry': {'build': gantry, 'tex': 4096, 'samples': 8, 'bake': {'ao': 3.0, 'curv': 0.08, 'panel': (6.0, 3.5, 6.0)}},
    # the shipyard's two cranes: crane-A slewed over the aft frames, crane-B over the drive bell (one bake per pose)
    'crane-A': {'build': crane, 'params': {'slew': -90.0, 'luff': 60.0, 'hook': 20.0}, 'tex': 2048, 'samples': 8, 'bake': {'ao': 1.5, 'curv': 0.05, 'panel': (3.0, 2.0, 3.0)}},
    'crane-B': {'build': crane, 'params': {'slew': -101.9, 'luff': 66.2, 'hook': 62.0}, 'tex': 2048, 'samples': 8, 'bake': {'ao': 1.5, 'curv': 0.05, 'panel': (3.0, 2.0, 3.0)}},
    'hall': {'build': hall, 'tex': 2048, 'samples': 10, 'bake': {'ao': 2.5, 'curv': 0.06, 'panel': (2.0, 6.0, 2.0)}},
    'floodMast': {'build': floodMast, 'tex': 512, 'bake': {'ao': 0.3, 'curv': 0.02, 'panel': (1.0, 2.0, 1.0)}},
    'scaffold-S': {'build': scaffold, 'params': {'lifts': 4}, 'tex': 512, 'bake': {'ao': 0.25, 'curv': 0.01}},
    'scaffold-M': {'build': scaffold, 'params': {'lifts': 7}, 'tex': 512, 'bake': {'ao': 0.25, 'curv': 0.01}},
    'scaffold-L': {'build': scaffold, 'params': {'lifts': 11}, 'tex': 1024, 'bake': {'ao': 0.25, 'curv': 0.01}},
    'truck': {'build': truck, 'tex': 1024, 'bake': {'ao': 0.35, 'curv': 0.02, 'panel': (1.2, 1.4, 1.2)}},
    'forklift': {'build': forklift, 'tex': 512, 'bake': {'ao': 0.2, 'curv': 0.015}},
    'worker': {'build': worker, 'tex': 256, 'bake': {'ao': 0.08, 'curv': 0.01}},
    'keelBlock': {'build': keelBlock, 'tex': 256, 'bake': {'ao': 0.25, 'curv': 0.02}},
    'bollard': {'build': bollard, 'tex': 256, 'bake': {'ao': 0.08, 'curv': 0.01}},
}


def build_one(name, spec, args):
    import bpy
    t0 = time.time()
    lib.reset_scene(args.threads)
    lib.BAKE.clear()
    lib.BAKE.update({'ao': 0.35, 'curv': 0.02, 'panel': (1.6, 1.1, 1.6)})
    lib.BAKE.update(spec.get('bake', {}))
    P = lib.Part(name)
    meta = spec['build'](P, **spec.get('params', {})) or {}
    cutters = meta.pop('_cutters', [])
    ob = P.finish()
    for c in cutters:
        bpy.data.objects.remove(c)
    bpy.context.view_layer.update()
    tris = lib.tris_of(ob)
    co = [ob.matrix_world @ v.co for v in ob.data.vertices]
    mn = [round(min(v[i] for v in co), 3) for i in range(3)]
    mx = [round(max(v[i] for v in co), 3) for i in range(3)]
    lib.unwrap(ob)
    tex = int(spec.get('tex', 512) * args.tex_scale)
    t_bake = lib.bake(ob, tex, spec.get('samples', args.samples))
    raw = os.path.join(SCRATCH, 'raw', f'{name}.glb')
    if args.blend:
        os.makedirs(args.blend, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(args.blend, f'{name}.blend'), check_existing=False)
    lib.export(ob, raw)
    out = os.path.join(OUT, f'{name}.glb')
    os.makedirs(OUT, exist_ok=True)
    r = subprocess.run(['node', os.path.join(ROOT, 'tools', 'optimize-glb.mjs'), raw, out, '--tris', '100000000', '--tex', str(tex)],
                       cwd=ROOT, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr or r.stdout)
    secs = time.time() - t0
    entry = {'file': f'{name}.glb', 'part': name.split('-')[0], 'size': name.split('-')[1] if '-' in name else None, 'tris': tris,
             'bbox': {'min': mn, 'max': mx, 'size': [round(b - a, 3) for a, b in zip(mn, mx)]},
             'mount': {'normal': '+Y', 'anchor': 'footprint centre at y = 0, front +Z'},
             'tex': tex, 'kb': round(os.path.getsize(out) / 1024), 'seconds': round(secs, 1), 'seconds_bake': round(t_bake, 1),
             'params': spec.get('params', {}), 'anchors': meta}
    print(f'ok {name:12s} tris {tris:7d}  bbox {entry["bbox"]["size"]}  tex {tex}  {secs:.1f}s (bake {t_bake:.1f}s)', flush=True)
    return entry


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('parts', nargs='*')
    ap.add_argument('--threads', type=int, default=4)
    ap.add_argument('--samples', type=int, default=12)
    ap.add_argument('--tex-scale', type=float, default=1.0)
    ap.add_argument('--blend', default=None)
    ap.add_argument('--list', action='store_true')
    args = ap.parse_args(sys.argv[1:])
    names = [n for n in REGISTRY if not args.parts or n in args.parts or n.split('-')[0] in args.parts]
    if args.list:
        for n in names:
            print(n, REGISTRY[n].get('params', {}))
        return
    man_path = os.path.join(OUT, 'parts.json')
    man = {'generator': 'tools/blender/buildings/yard_kit.py (Blender %s, procedural, lib.py bake)' % __import__('bpy').app.version_string,
           'frame': 'metres; +Y up, the part stands on y = 0, origin = footprint centre, front +Z, +X left. mount.normal +Y.',
           'parts': {}}
    if os.path.exists(man_path):
        man['parts'] = json.load(open(man_path)).get('parts', {})
    for n in names:
        man['parts'][n] = build_one(n, REGISTRY[n], args)
        man['parts'] = dict(sorted(man['parts'].items()))
        json.dump(man, open(man_path, 'w'), indent=1)


if __name__ == '__main__':
    main()
