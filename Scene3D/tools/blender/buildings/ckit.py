"""ckit: parametric hard-surface remodels of the colony components (README-colony.md, "Component remodel").

The fal components (component.py: Tripo image-to-3D of an isolated component image, cleaned and sized) are BLUEPRINTS:
their soft, averaged geometry and low-res de-lit texture read "mushy" at close range (correction 40) and "low res"
(correction 41). Each large component is rebuilt here as clean geometry on the shared building kit (bkit.Build: the
batched primitives, the kit's calibrated paint materials, the Rec of lights and kit placements), measured off its
blueprint (cmeasure.py: ortho views on a metre grid, radial profile and its stations, ledge heights), at the SAME
name, size and anchor (part frame: metres, +Y up, footprint centre at the origin on y = 0, front +Z), so every
building script that places it keeps working. remodel.py bakes and paints it in texture space and installs it.

Generic builders (reuse them for the other buildings; the five steel-mill parts are parameter sets of them):
  furnace(B, P)          a vertical vessel from stations: plinth, hearth with staves, a recessed glowing tuyere band,
                         bustle main and downlegs, a lathe shaft from a radius table, hoops, flange, top cone, throat,
                         uptakes / downcomer, top platform; optional four-column laced steel tower with square
                         grating decks, ring girders, X bracing, caged ladder, lamps
  banded_stack(B, P)     chimney: base block, gusseted flared foot, banded shell (paint per band), hoops, platforms,
                         caged ladders, sooted open top, lamps, obstruction light
  gable_shed(B, P)       clad portal-frame shed segment: corrugated walls between I-section pilasters, recessed window
                         strips, dark dado, gable ends with outward verges (segments abut along Z without overlap),
                         corrugated roof, gutters, ridge, louvred roof monitor, downpipes, kit door
  pour_bay(B, P)         open crane bay: heavy columns, lattice side, plate eaves girder and roof truss, runways, an amber
                         double-girder bridge crane with trolley and hook, a plated back wall, the glowing runner and
                         tundish, rails and a ladle car, tapping platforms with stairs
  incline_gallery(B, P)  inclined enclosed conveyor gallery on two Warren trusses between a drive house and a head house,
                         with a lattice trestle
Shared details: laced_column, ibeam, plate_girder, warren, square_deck, lamp, louvre_bank, window_strip, clad_panel.

Every builder returns the PAINT spec for remodel.py / cpaint.py: per material zone, the plating seams (courses in y,
joints along the face or round an axis), corrugation pitch, grating pitch, rust and wear strengths.
"""
import math

import bkit as K
import lib
from mathutils import Vector

V = Vector
DEG = math.pi / 180

# extra paint zones for the remodels (linear base colour, bake kind, roughness, metal), on the kit's calibrated scale
# (panel 0.60 = the concepts' light paint sRGB ~200; frame 0.04 = the gunmetal sRGB ~55)
lib.MATS.update({
    'clad':   ((0.56, 0.555, 0.535), 'paint', 0.62, 0.0),   # corrugated light cladding (walls), a touch warmer than panel
    'clad2':  ((0.50, 0.49, 0.465), 'paint', 0.66, 0.0),   # corrugated roof sheeting (warm light grey)
    'shell':  ((0.58, 0.575, 0.555), 'paint', 0.6, 0.0),   # light plated vessel shell (furnace shaft, stack bands)
    'hot':    ((1.0, 0.36, 0.05), 'paint', 0.45, 0.0),      # molten / glowing (emissive in the paint)
    'lamp':   ((1.0, 0.60, 0.22), 'paint', 0.3, 0.0),       # amber lamp lenses (emissive)
    'louvre': ((0.05, 0.052, 0.056), 'paint', 0.6, 0.0),    # louvre blades, dark grilles
    'rust':   ((0.20, 0.085, 0.035), 'paint', 0.85, 0.0),   # rusted steel accents (ladle shell, rails)
})


# heavy-industry paint (the steel mill's concept, measured with tools/buildings/paint-check.py: its light paint is a warm,
# weathered grey, sat ~0.16 at hue ~23 deg, a step darker than the kit's clean 'panel'; frames are rust-warm gunmetal).
# Merged under every builder's paint spec; a building family with a cleaner look passes its own.
WORKS = {
    # v5 (second review): light paint a step less yellow (v4 hue 35 deg vs the concept's 25-28), seams and run-off
    # stronger (worn, not dirty), and the dark steel a neutral gunmetal: v4's frames rendered at saturation 0.2-0.3
    # (brown) from warm grime, dirt and rusty edges on a neutral base; the concept's are ~0.09
    'shell': {'color': [0.76, 0.735, 0.705], 'rust': 0.6, 'streak': 0.22, 'streak_f': 3.2, 'dark': 0.5, 'seam_w': 0.045},
    'clad': {'color': [0.78, 0.755, 0.725], 'rust': 0.5, 'streak': 0.22, 'streak_f': 3.2},
    'clad2': {'color': [0.71, 0.69, 0.66], 'rust': 0.45, 'blot': 0.035, 'patina': 0.03},   # roofs: big planes, blotches read as camouflage
    'panel': {'color': [0.79, 0.765, 0.735], 'rust': 0.45, 'streak': 0.2, 'streak_f': 3.2},
    'frame': {'color': [0.33, 0.336, 0.35], 'rust': 0.1, 'edge': 0.9},     # concept gunmetal ~sRGB 70-80, neutral
    'frame2': {'color': [0.37, 0.375, 0.388], 'rust': 0.12},
    'pipeDark': {'color': [0.42, 0.425, 0.435], 'rust': 0.15, 'metal': 0.3},           # mid-grey mains: dark pipes vanished on the dusk backdrop
}


def works(spec):
    out = {k: dict(v) for k, v in WORKS.items()}
    for k, v in spec.items():
        out.setdefault(k, {}).update(v)
    return out


# ------------------------------------------------------------------------------------------------------------------
# small structural details (true size)
# ------------------------------------------------------------------------------------------------------------------
def ibeam(B, p0, p1, h=0.6, b=0.3, tw=0.03, tf=0.04, mat='frame', up=(0, 1, 0)):
    """Rolled I-section from p0 to p1 (depth h toward `up`, flange width b): two flanges and a web."""
    p0, p1 = V(p0), V(p1)
    L = (p1 - p0).length
    if L < 1e-3:
        return
    d = (p1 - p0).normalized()
    u = V(up)
    if abs(d.dot(u.normalized())) > 0.99:
        u = V((1, 0, 0)) if abs(d.x) < 0.9 else V((0, 0, 1))
    with B.at(M=K.frame_along(p0, p1, u)):
        B.box((b, tf, L), at=(0, h / 2 - tf / 2, L / 2), mat=mat, bevel=0.012)
        B.box((b, tf, L), at=(0, -h / 2 + tf / 2, L / 2), mat=mat, bevel=0.012)
        B.box((tw, h - 2 * tf, L), at=(0, 0, L / 2), mat=mat, bevel=0.0)


def plate_girder(B, p0, p1, h=1.4, b=0.6, mat='frame', stiff=1.6, up=(0, 1, 0), side=1):
    """Heavy welded plate girder (flanges, web, stiffener plates every `stiff` m on the visible side(s))."""
    ibeam(B, p0, p1, h, b, 0.05, 0.07, mat, up)
    p0, p1 = V(p0), V(p1)
    L = (p1 - p0).length
    n = max(1, int(L / stiff))
    d = (p1 - p0).normalized()
    u = V(up)
    with B.at(M=K.frame_along(p0, p1, u)):
        for i in range(n + 1):
            z = L * i / n
            for s in (-1, 1):
                B.box((b / 2 - 0.03, h - 0.14, 0.03), at=(s * (b / 4 + 0.012), 0, min(max(z, 0.02), L - 0.02)), mat=mat, bevel=0.0)


def laced_column(B, x, z, y0, y1, w=1.3, d=None, bay=2.6, chord=0.26, lace=0.09, mat='frame', battens=4, cap=True):
    """Built-up laced column (the furnace tower's legs): four angle chords at the corners of a w x d section, X lacing
    on all four faces every `bay` m, batten plates every `battens` bays, base and cap plates."""
    d = d or w
    H = y1 - y0
    nb = max(1, int(round(H / bay)))
    hw, hd = w / 2 - chord / 2, d / 2 - chord / 2
    corners = [(-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd)]
    for cx, cz in corners:
        # an angle: two legs of a chord x chord L (crisp re-entrant corner)
        sx, sz = (1 if cx > 0 else -1), (1 if cz > 0 else -1)
        B.box((chord, H, 0.05), at=(x + cx, y0 + H / 2, z + cz + sz * (chord / 2 - 0.025)), mat=mat, bevel=0.01)
        B.box((0.05, H, chord), at=(x + cx + sx * (chord / 2 - 0.025), y0 + H / 2, z + cz), mat=mat, bevel=0.01)
    faces = [((-hw, hd), (hw, hd)), ((hw, hd), (hw, -hd)), ((hw, -hd), (-hw, -hd)), ((-hw, -hd), (-hw, hd))]
    for i in range(nb):
        ya, yb = y0 + H * i / nb, y0 + H * (i + 1) / nb
        for (a, b) in faces:
            # lacing in the face plane, just inside the chord's outer face
            nx, nz = (a[1] + b[1]) / 2, (a[0] + b[0]) / 2
            out = V(((a[0] + b[0]) / 2, 0, (a[1] + b[1]) / 2)).normalized() * 0.1
            pa = V((x + a[0], ya, z + a[1])) + out
            pb = V((x + b[0], yb, z + b[1])) + out
            pc = V((x + b[0], ya, z + b[1])) + out
            pd = V((x + a[0], yb, z + a[1])) + out
            B.bar(pa, pb, 0.03, lace, mat=mat, bevel=0.0)
            B.bar(pc, pd, 0.03, lace, mat=mat, bevel=0.0)
        if battens and i % battens == 0:
            B.box((w - 0.02, 0.32, d - 0.02), at=(x, ya + 0.16, z), mat=mat, bevel=0.02)
    B.box((w + 0.5, 0.08, d + 0.5), at=(x, y0 + 0.04, z), mat=mat, bevel=0.02)
    B.box((w + 0.12, 0.35, d + 0.12), at=(x, y0 + 0.25, z), mat=mat, bevel=0.03)
    if cap:
        B.box((w + 0.2, 0.3, d + 0.2), at=(x, y1 - 0.15, z), mat=mat, bevel=0.03)


def warren(B, p0, p1, depth, up=(0, 1, 0), bay=None, chord=0.3, web=0.14, mat='frame', verticals=True):
    """Planar Warren truss: bottom chord p0 -> p1, top chord `depth` m along `up`, diagonals (and verticals)."""
    p0, p1 = V(p0), V(p1)
    u = V(up).normalized() * depth
    L = (p1 - p0).length
    bay = bay or depth * 1.2
    n = max(1, int(round(L / bay)))
    B.bar(p0, p1, chord, chord, mat=mat, up=up, bevel=0.02)
    B.bar(p0 + u, p1 + u, chord, chord, mat=mat, up=up, bevel=0.02)
    for i in range(n + 1):
        a = p0 + (p1 - p0) * (i / n)
        if verticals:
            B.bar(a, a + u, web, web, mat=mat, bevel=0.0)
        if i < n:
            b = p0 + (p1 - p0) * ((i + 1) / n)
            if i % 2 == 0:
                B.bar(a, b + u, web, web, mat=mat, bevel=0.0)
            else:
                B.bar(a + u, b, web, web, mat=mat, bevel=0.0)


def square_deck(B, c, y, half, r_in, t=0.14, n=32, mat='grate', toe=True):
    """Square grating deck (half-width `half`) round a round shell (hole radius r_in): one solid with a hole, a toe
    plate on the outer edge."""
    cx, cz = c
    outer, inner = [], []
    for k in range(n):
        a = 2 * math.pi * k / n
        ca, sa = math.cos(a), math.sin(a)
        s = half / max(abs(ca), abs(sa))
        outer.append((cx + s * ca, -(cz + s * sa)))
        inner.append((cx + r_in * ca, -(cz + r_in * sa)))
    B.add(lib.bm_frame(outer, inner, y - t, y), rot=(-90, 0, 0), mat=mat, bevel=0.0)
    if toe:
        for (a, b) in (((-half, -half), (half, -half)), ((half, -half), (half, half)), ((half, half), (-half, half)), ((-half, half), (-half, -half))):
            B.bar((cx + a[0], y + 0.07, cz + a[1]), (cx + b[0], y + 0.07, cz + b[1]), 0.02, 0.15, mat='frame', bevel=0.0)


def lamp(B, p, n, size=0.32, light=True):
    """Amber wall lamp: a dark housing and a lit lens facing n; a lightscape pin in front of it."""
    p, n = V(p), V(n).normalized()
    u = V((0, 1, 0)).cross(n)
    if u.length < 1e-3:
        u = V((1, 0, 0))
    with B.at(M=lib.basis(p, u.normalized(), n.cross(u.normalized()), n)):
        B.box((size, size, 0.18), at=(0, 0, 0.09), mat='frame', bevel=0.02)
        B.box((size * 0.7, size * 0.5, 0.06), at=(0, 0, 0.2), mat='lamp', bevel=0.01)
    if light:
        B.R.pin(tuple(p + n * 0.3))


def louvre_bank(B, o, u, w, h, pitch=0.32, depth=0.25, frame=0.12):
    """Louvre bank on a face (o = bottom-left on the face plane, u = face right): a dark frame, a recessed back and
    angled blades every `pitch` m."""
    M = K.face_basis(o, u)
    with B.at(M=M):
        B.box((w, h, 0.05), at=(w / 2, h / 2, -depth), mat='interior', bevel=0.0)
        n = max(1, int(h / pitch))
        for k in range(n):
            y = (k + 0.5) * h / n
            B.box((w - 0.04, 0.035, depth * 0.9), at=(w / 2, y, -depth / 2), rot=(35, 0, 0), mat='louvre', bevel=0.0)
        for (bw, bh, bx, by) in ((w + 2 * frame, frame, w / 2, 0), (w + 2 * frame, frame, w / 2, h), (frame, h, 0, h / 2), (frame, h, w, h / 2)):
            B.box((bw, bh, depth + 0.08), at=(bx, by, -depth / 2 + 0.04), mat='frame', bevel=0.015)


def window_strip(B, o, u, w, h, panes=4, depth=0.18, frame=0.1, lit=False):
    """Recessed glazing in an opening (o bottom-left on the wall face, u face right): reveals, glass set `depth` back,
    mullions and a sill."""
    M = K.face_basis(o, u)
    with B.at(M=M):
        B.box((w, h, 0.04), at=(w / 2, h / 2, -depth), mat='glassW', bevel=0.0)
        for k in range(1, panes):
            B.box((0.07, h, 0.1), at=(w * k / panes, h / 2, -depth + 0.06), mat='frame', bevel=0.0)
        B.box((w, 0.06, 0.1), at=(w / 2, h * 0.55, -depth + 0.06), mat='frame', bevel=0.0)
        for (bw, bh, bx, by, bz) in ((w + 2 * frame, frame, w / 2, -frame / 2, depth), (w + 2 * frame, frame, w / 2, h + frame / 2, depth),
                                     (frame, h, -frame / 2, h / 2, depth), (frame, h, w + frame / 2, h / 2, depth)):
            B.box((bw, bh, bz + 0.06), at=(bx, by, -bz / 2 + 0.03), mat='frame', bevel=0.015)
        B.box((w + 0.3, 0.08, 0.22), at=(w / 2, -frame - 0.03, 0.06), mat='frame', bevel=0.02)
    if lit:
        n = M.to_3x3() @ V((0, 0, 1))
        B.R.window(tuple(M @ V((w / 2, h / 2, -depth - 0.1))), tuple(n), w, h)


def plate(B, size, at=(0, 0, 0), rot=(0, 0, 0), mat='clad', bevel=0.02):
    """A box without its back (-z) face: cladding seen from one side only (no texels spent on the hidden inside)."""
    import bmesh
    bm = lib.bm_box(*size)
    back = [f for f in bm.faces if f.calc_center_median().z < -size[2] / 2 + 1e-5]
    bmesh.ops.delete(bm, geom=back, context='FACES_ONLY')
    B.add(bm, at, rot, mat, bevel)


def clad_panel(B, o, u, w, h, t=0.2, mat='clad', holes=()):
    """A flat cladding sheet on a face (o bottom-left, u right, outward normal u x up), thickness t inward; holes
    [(x0, y0, x1, y1)] in face coordinates are left open (the sheet is split round them: exact openings)."""
    M = K.face_basis(o, u)
    rects = [(0.0, 0.0, w, h)]
    for (hx0, hy0, hx1, hy1) in holes:
        nxt = []
        for (x0, y0, x1, y1) in rects:
            if hx1 <= x0 or hx0 >= x1 or hy1 <= y0 or hy0 >= y1:
                nxt.append((x0, y0, x1, y1)); continue
            if hy0 > y0: nxt.append((x0, y0, x1, hy0))
            if hy1 < y1: nxt.append((x0, hy1, x1, y1))
            if hx0 > x0: nxt.append((x0, max(y0, hy0), hx0, min(y1, hy1)))
            if hx1 < x1: nxt.append((hx1, max(y0, hy0), x1, min(y1, hy1)))
        rects = nxt
    with B.at(M=M):
        for (x0, y0, x1, y1) in rects:
            if x1 - x0 > 1e-3 and y1 - y0 > 1e-3:
                plate(B, (x1 - x0, y1 - y0, t), at=((x0 + x1) / 2, (y0 + y1) / 2, -t / 2), mat=mat, bevel=0.02)


def hoop(B, c, r, y, h=0.6, out=0.2, mat='frame', n=48, base_y=0.0):
    """A raised band round a round shell: crisp chamfered edges."""
    x, z = c
    B.lathe([(r - 0.05, y), (r + out, y), (r + out, y + h), (r - 0.05, y + h)], (x, base_y, z), mat=mat, n=n, closed=True, bevel=0.03, sharp=30)


def lap_rings(B, rfun, y0, y1, pitch, mat='shell', skip=(), n=48, out=0.035, h=0.14, c=(0.0, 0.0)):
    """Modelled plate courses on a round shell (v4 r2): a thin lap ring at every course seam y = k * pitch in (y0, y1)
    (the paint's course seams sit on the same multiples), its lower edge chamfered so each seam catches the key light
    as a crisp line at any distance (a painted seam alone fades into the plate tone beyond ~40 m). rfun(y) is the shell
    radius; seams within 0.7 m of a `skip` height (hoops, bands) are left out."""
    x, z = c
    for k in range(int(math.ceil(y0 / pitch)), int(y1 / pitch) + 1):
        y = k * pitch
        if y < y0 + 0.3 or y > y1 - 0.3 or any(abs(y - s) < 0.7 for s in skip):
            continue
        r = rfun(y)
        B.lathe([(r - 0.04, y - h / 2), (r + out * 0.4, y - h / 2), (r + out, y - h / 2 + 0.03), (r + out, y + h / 2), (r - 0.04, y + h / 2)],
                (x, 0.0, z), mat=mat, n=n, closed=True, bevel=0.0, sharp=25)


def ribbed_slope(B, a, b, z0, z1, pitch=0.9, w=0.09, h=0.07, mat='clad2', margin=0.25, stop=None):
    """Standing-seam ribs on a sloped sheet (v4 r2): the sheet's top surface runs from a = (x, y) (eaves) to b = (x, y)
    (ridge) and is extruded along Z from z0 to z1; a rib every `pitch` m runs down the slope. stop(z) -> x (optional)
    ends a rib early (under a roof monitor). Ribs are real geometry so the roof reads as profiled sheeting from the
    building camera, not as a flat painted plane."""
    a3, b3 = V((a[0], a[1], 0.0)), V((b[0], b[1], 0.0))
    t = (b3 - a3).normalized()
    nrm = V((-t.y, t.x, 0.0))
    if nrm.y < 0:
        nrm = -nrm
    n = max(1, int(round((z1 - z0 - 2 * margin) / pitch)))
    for i in range(n + 1):
        z = z0 + margin + (z1 - z0 - 2 * margin) * i / n
        e = b3
        if stop is not None:
            xs = stop(z)
            if xs is not None:
                f = (xs - a3.x) / (b3.x - a3.x) if abs(b3.x - a3.x) > 1e-6 else 1.0
                e = a3 + (b3 - a3) * max(0.0, min(1.0, f))
        B.bar(a3 + nrm * (h / 2) + V((0, 0, z)), e + nrm * (h / 2) + V((0, 0, z)), w, h, mat=mat, up=tuple(nrm), bevel=0.0)


def ribbed_flat(B, x0, x1, z0, z1, y, pitch=0.9, w=0.09, h=0.07, mat='clad2', along='x'):
    """Standing-seam ribs on a flat roof deck at top height y (ribs along X or Z)."""
    if along == 'x':
        n = max(1, int(round((z1 - z0) / pitch)))
        for i in range(1, n):
            z = z0 + (z1 - z0) * i / n
            B.box((x1 - x0, h, w), at=((x0 + x1) / 2, y + h / 2, z), mat=mat, bevel=0.0)
    else:
        n = max(1, int(round((x1 - x0) / pitch)))
        for i in range(1, n):
            x = x0 + (x1 - x0) * i / n
            B.box((w, h, z1 - z0), at=(x, y + h / 2, (z0 + z1) / 2), mat=mat, bevel=0.0)


# ------------------------------------------------------------------------------------------------------------------
# furnace: vertical vessel from stations, with the optional four-column tower
# ------------------------------------------------------------------------------------------------------------------
FURNACE = {   # blastFurnace, measured off its blueprint (cmeasure.py; README-colony.md "Component remodel")
    'base': (27.4, 3.0, 29.2),                 # concrete plinth w, h, d (bbox 27.46 x 29.34)
    'hearth': (9.7, 3.0, 8.2),                 # r, y0, y1 (dark, staves)
    'tuyere': (9.45, 8.2, 10.2, 36),           # recessed band r, y0, y1, windows
    'collar': (10.0, 10.2, 10.9),              # dark collar under the deck
    'bustle': (9.95, 11.9, 0.5, 16),           # bustle main radius, y, tube r, downlegs
    'shaft': [(9.45, 10.9), (9.3, 12.5), (9.1, 15.0), (8.75, 19.0), (8.3, 23.0), (7.9, 27.0), (7.45, 31.5),
              (7.0, 36.0), (6.7, 40.0), (6.5, 44.0), (6.45, 46.8)],
    'hoops': [(12.2, 1.0), (16.6, 0.8), (23.4, 0.9), (35.8, 0.8), (42.0, 0.8)],
    'flange': (7.2, 46.8, 47.6),
    'cone': [(6.6, 47.6), (5.2, 49.0), (2.5, 51.2)],
    'throat': (2.3, 51.2, 58.0),
    'cap': (1.95, 58.0, 60.0),
    'top_deck': (53.6, 5.0),
    'uptakes': (4, 0.7, [(4.1, 49.6), (4.3, 54.6), (3.4, 56.4), (2.2, 56.9)]),
    'downcomer': (1.05, [(0.0, 55.4, -2.2), (0.0, 55.4, -6.4), (0.0, 53.6, -8.6), (0.0, 31.0, -9.15)]),
    'tower': {'half': 10.6, 'y0': 3.0, 'y1': 46.4, 'w': 1.3, 'levels': [17.0, 30.0, 44.0], 'ring': 2.0, 'walk': 1.6,
              'xbrace': [(17.0, 30.0), (30.0, 44.0)], 'ladder': (1, 1)},
}


# v4 r3: the blueprint (FURNACE) refitted to the CONCEPT's stations, read off steel_mill-concept.jpg at 15.5 px/m (ground
# to the top at 60 m): a light plated hearth drum to 17.4 m between raking dark legs, the glowing tuyere band at
# 17.6-19.8, a stepped dark bosh to 29 m with the first deck, a light conical shaft to 42 m, a dark stepped hood to 46.5,
# the narrow upper drum to 55 with the wide top deck at 52.6, the cap to 60. Radii keep the blueprint's 9.5 m footprint
# scaled to the concept's slimmer ratio (cone foot 8.4 m).
FURNACE_V4 = dict(FURNACE)
FURNACE_V4.update({
    'hearth': (7.6, 3.0, 17.4), 'hearth_mat': 'shell', 'staves': 0, 'hearth_hoops': (4.6, 10.4, 16.6),
    'tuyere': (7.35, 17.6, 19.8, 30),
    'collar': (8.1, 19.8, 20.4),
    'bustle': (9.4, 21.4, 0.5, 14),
    'bosh': [(20.4, 22.9, 7.9), (22.9, 25.4, 8.15), (25.4, 27.9, 8.4), (27.9, 29.0, 8.55)],
    'shaft': [(8.4, 29.0), (8.15, 31.0), (7.75, 34.0), (7.3, 37.0), (6.8, 40.0), (6.5, 42.0)],
    'hoops': [(32.4, 0.7), (38.4, 0.7)],
    'flange': (6.9, 42.0, 42.7),
    'cone': [(6.4, 42.7), (5.7, 44.2), (4.4, 46.5)],
    'throat': (3.9, 46.5, 55.0),
    'cap': (3.1, 55.0, 60.0),
    'top_deck': None,
    'uptakes': (4, 0.6, [(3.9, 48.0), (4.9, 55.2), (3.6, 58.6), (2.2, 59.2)]),
    'downcomer': (1.05, [(0.0, 57.6, -2.4), (0.0, 57.6, -6.4), (0.0, 55.0, -8.6), (0.0, 31.0, -9.6)]),
    'tower': {'half': 9.6, 'y0': 29.0, 'y1': 53.2, 'w': 1.3, 'levels': [29.0, 42.4, 52.6], 'ring': 1.5, 'walk': 1.2,
              'xbrace': [(29.0, 42.4), (42.4, 52.6)], 'ladder': (1, 1), 'ladder_y0': 3.0, 'legs': ((11.4, 3.0), (9.6, 29.0)), 'leg_section': (2.8, 2.0), 'leg_tie': (17.6, 9.4),
              'ring_in': {52.6: 3.95, 42.4: 6.95}},
})


# v5 (second review, 2026-10-07): the concept's furnace is the hero: a BROAD light bell (the light cone flares to r 11.4
# at its foot over a dark stepped bosh, tapering to r 8 at 42 m), a light hearth drum r 9.2, heavy plated raking legs to
# the cone-foot deck, and only a light, open frame above: four slim tapered posts from the leg tops to a wide top deck,
# X bracing in the top bay alone (v4's four laced columns and three square decks read as a black scaffold hiding a thin
# cylinder). A big bustle main round the bosh, the uptakes over the cap, and a 3 m downcomer dropping to -X into the
# gas-cleaning annex (the concept's elbow pipe on the left).
FURNACE_V5 = dict(FURNACE)
FURNACE_V5.update({
    'base': (32.0, 3.0, 32.0),
    'hearth': (9.2, 3.0, 15.0), 'hearth_mat': 'shell', 'staves': 0, 'hearth_hoops': (4.4, 9.4, 13.9),
    'tuyere': (8.95, 15.2, 17.6, 32),
    'collar': (9.85, 17.6, 18.3),
    'bustle': (12.6, 21.2, 0.85, 16),
    'bosh': [(18.3, 20.6, 9.6), (20.6, 22.9, 9.95), (22.9, 25.2, 10.3), (25.2, 26.6, 10.65)],
    'shaft': [(11.4, 26.6), (11.25, 27.6), (10.5, 31.0), (9.6, 35.0), (8.75, 39.0), (8.1, 42.4)],
    'hoops': [(34.4, 0.45)],
    'flange': (8.5, 42.4, 43.1), 'throat_mat': 'frame2',
    'cone': [(8.3, 43.1), (7.5, 44.6), (5.4, 47.2)],
    'throat': (5.0, 47.2, 54.0),
    'cap': (3.7, 54.0, 59.6),
    'top_deck': None,
    'uptakes': (4, 0.62, [(5.25, 48.4), (6.3, 55.6), (4.6, 59.9), (1.9, 60.9)]),
    'header': (1.75, 59.4, 62.4),
    'downcomer': (1.45, [(0.0, 61.2, 0.0), (-5.5, 61.2, 0.0), (-15.6, 41.0, 4.0), (-15.6, 25.0, 7.0), (-19.0, 21.6, 7.0), (-19.0, 14.0, 7.0)]),
    'decks': [(26.6, 11.45, 13.4), (43.1, 8.55, 10.4)],
    'tower': {'style': 'posts', 'legs': ((13.9, 3.0), (12.2, 26.6)), 'leg_section': (4.0, 2.8), 'leg_tie': (15.2, 10.6),
              'post': (0.95, 0.75), 'top': (8.9, 54.0), 'levels': [43.1], 'xbrace': (43.1, 54.0), 'top_deck': (54.0, 5.05, 9.6),
              'ladder': (-1, 0), 'ladder_y0': 26.6},
})


def _raking_legs(B, T):
    """Heavy raking legs: plated tapered box sections from the plinth corners to the first deck, stiffener bands, a
    base shoe, a cap, anchor nuts, a plate-girder tie to the tuyere platform ring."""
    (b0, ly0), (b1, ly1) = T['legs']
    s0, s1 = T.get('leg_section', (2.2, 1.6))
    for (sx, sz) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        pa, pb = V((sx * b0, ly0, sz * b0)), V((sx * b1, ly1, sz * b1))
        B.strut(pa, pb, (s0, s0), (s1, s1), 0.22, mat='frame2', bevel=0.04)
        d = (pb - pa)
        for t in [0.12 + 0.76 * i / 5 for i in range(6)]:
            sz_ = s0 + (s1 - s0) * t
            with B.at(M=K.frame_along(pa, pb)):
                B.box((sz_ + 0.12, sz_ + 0.12, 0.22), at=(0, 0, d.length * t), mat='frame', bevel=0.02)
        # flange plates down the two outer faces (a built-up section: crisp vertical shadow lines)
        with B.at(M=K.frame_along(pa, pb)):
            for (fx, fy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                B.box((0.08 if fx else s1 * 0.9, 0.08 if fy else s1 * 0.9, d.length * 0.9), at=(fx * (s0 + s1) / 4 + fx * 0.05, fy * (s0 + s1) / 4 + fy * 0.05, d.length * 0.5), mat='frame', bevel=0.0)
        B.box((s0 + 0.8, 0.5, s0 + 0.8), at=(sx * b0, ly0 + 0.25, sz * b0), mat='frame', bevel=0.04)
        B.box((s1 + 0.6, 0.4, s1 + 0.6), at=(sx * b1, ly1 - 0.2, sz * b1), mat='frame', bevel=0.03)
        if T.get('leg_tie'):
            yt, rt_ = T['leg_tie']
            tt = (yt - ly0) / (ly1 - ly0)
            bt = b0 + (b1 - b0) * tt
            a_ = math.atan2(sx, sz)
            plate_girder(B, (sx * bt, yt - 0.5, sz * bt), (rt_ * math.sin(a_), yt - 0.5, rt_ * math.cos(a_)), h=1.0)
        for (ex, ez) in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            B.cyl(0.07, 0.16, at=(sx * b0 + ex * (s0 / 2 + 0.2), ly0 + 0.58, sz * b0 + ez * (s0 / 2 + 0.2)), mat='frame', n=6)
        lamp(B, (sx * (b0 + s0 / 2 + 0.1), ly0 + 3.2, sz * b0), (sx, 0, 0), size=0.28)


def _posts_tower(B, P, T, prof, c):
    """v5: the concept's light, open frame: raking legs to the cone-foot deck, then four slim tapered posts to a wide
    square top deck round the upper drum, ring beams at the hood deck, X bracing in the top bay only, caged ladder."""
    _raking_legs(B, T)
    (b1, ly1) = T['legs'][1]
    ht, yt = T['top']
    pw, pd = T.get('post', (0.9, 0.7))

    def half_at(y):
        return b1 + (ht - b1) * (y - ly1) / (yt - ly1)
    corners = ((-1, -1), (1, -1), (1, 1), (-1, 1))
    for (sx, sz) in corners:
        B.strut((sx * b1, ly1, sz * b1), (sx * ht, yt, sz * ht), (pw, pw), (pd, pd), 0.08, mat='frame', bevel=0.02)
    for ly in T['levels'] + [yt - 0.5]:
        h_ = half_at(ly)
        for i in range(4):
            a, b = corners[i], corners[(i + 1) % 4]
            ibeam(B, (a[0] * h_, ly - 0.45, a[1] * h_), (b[0] * h_, ly - 0.45, b[1] * h_), h=0.7, b=0.32, mat='frame')
        # radial ties from the ring beams to the decks round the shell
        for (sx, sz) in corners:
            r_ = _shaft_r(prof, ly) if ly < prof[-1][1] else P['throat'][0]
            B.bar((sx * h_ * 0.98, ly - 0.45, sz * h_ * 0.98), (sx * r_ * 0.75, ly - 0.45, sz * r_ * 0.75), 0.22, 0.45, mat='frame', bevel=0.0)
    ya, yb = T['xbrace']
    for i in range(4):
        a, b = corners[i], corners[(i + 1) % 4]
        ha, hb = half_at(ya + 0.6), half_at(yb - 1.0)
        B.bar((a[0] * ha, ya + 0.6, a[1] * ha), (b[0] * hb, yb - 1.0, b[1] * hb), 0.2, 0.2, mat='frame', bevel=0.0)
        B.bar((b[0] * ha, ya + 0.6, b[1] * ha), (a[0] * hb, yb - 1.0, a[1] * hb), 0.2, 0.2, mat='frame', bevel=0.0)
    # knee braces from the leg tops to the cone-foot ring beam level (the concept's portal look between the legs)
    for i in range(4):
        a, b = corners[i], corners[(i + 1) % 4]
        for (p, q) in ((a, b), (b, a)):
            B.bar((p[0] * b1, ly1 - 0.5, p[1] * b1), (p[0] * b1 * 0.55 + q[0] * b1 * 0.45, ly1 - 0.5, p[1] * b1 * 0.55 + q[1] * b1 * 0.45), 0.5, 0.9, mat='frame2', bevel=0.02)
    # the wide top deck: a square grating deck round the upper drum with toe plates, rails, lamps
    ty, rin, hw = T['top_deck']
    pts = [(-hw, -hw), (hw, -hw), (hw, hw), (-hw, hw)]
    # a grating ring round the drum, then four strips out to the square edge (the ring sits 2 cm lower: no coplanar overlap)
    B.ring(rin + 2.6, rin, ty - 0.18, ty - 0.02, base=(0, 0, 0), mat='grate', n=48)
    inner = rin + 1.6
    for (sx, sz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        if sx:
            B.box((hw - inner, 0.16, 2 * hw), at=(sx * (hw + inner) / 2, ty - 0.08, 0), mat='grate', bevel=0.0)
        else:
            B.box((2 * inner, 0.16, hw - inner), at=(0, ty - 0.08, sz * (hw + inner) / 2), mat='grate', bevel=0.0)
    for i in range(4):
        a, b = pts[i], pts[(i + 1) % 4]
        B.box((abs(b[0] - a[0]) + 0.1 if a[1] == b[1] else 0.08, 0.2, abs(b[1] - a[1]) + 0.1 if a[0] == b[0] else 0.08),
              at=((a[0] + b[0]) / 2, ty + 0.06, (a[1] + b[1]) / 2), mat='frame', bevel=0.0)
    K.railing(B, [(x, ty, z) for (x, z) in pts], post=1.8, closed=True)
    for (x, z) in pts:
        lamp(B, (x * 1.02, ty + 1.5, z * 1.02), (1 if x > 0 else -1, 0, 1 if z > 0 else -1), size=0.3)
    lx, lz = T['ladder']
    ly0_ = T.get('ladder_y0', ly1)
    hx = half_at(ly0_)
    K.ladder(B, (lx * (_shaft_r(prof, 30.0) + 0.5), ly0_, 2.2), (lx, 0, 0), T['levels'][0] - ly0_)
    # the tuyere platform ring at the band's foot
    K.platform_ring(B, c, P['tuyere'][1], P['hearth'][0] + 0.05, P['hearth'][0] + 1.9, n=48, brackets=12)


def _shaft_r(prof, y):
    for (ra, ya), (rb, yb) in zip(prof[:-1], prof[1:]):
        if ya <= y <= yb:
            return ra + (rb - ra) * (y - ya) / max(yb - ya, 1e-6)
    return prof[0][0] if y < prof[0][1] else prof[-1][0]


def furnace(B, P=FURNACE):
    n = P.get('segments', 72)       # 72 round a 19 m shell: facets ~0.8 m, a smooth silhouette at the 1:1 close-up
    c = (0.0, 0.0)
    # plinth: a chamfered concrete block with a kerb and anchor plinths under the tower legs
    bw, bh, bd = P['base']
    B.prism(lib.chamfer_rect(bw, bd, 0.5), 0.0, bh - 0.3, mat='concrete2', bevel=0.05)
    B.prism(lib.chamfer_rect(bw - 0.3, bd - 0.3, 0.4), bh - 0.32, bh, mat='concrete', bevel=0.04)
    # hearth: dark plated drum, vertical staves, two hoops, tap-hole bays with sooted openings
    r, y0, y1 = P['hearth']
    B.lathe([(0, y0), (r, y0), (r, y1), (0, y1)], (0, 0, 0), mat=P.get('hearth_mat', 'frame2'), n=n, bevel=0.04)
    if P.get('hearth_mat', 'frame2') != 'frame2':
        lap_rings(B, lambda y: r, y0 + 2.4, y1 - 2.0, P.get('course', 2.25), mat=P['hearth_mat'], n=n)
    for k in range(P.get('staves', 24)):
        a = 2 * math.pi * (k + 0.5) / P.get('staves', 24)
        B.bar((r * math.sin(a), y0 + 0.2, r * math.cos(a)), (r * math.sin(a), y1 - 0.1, r * math.cos(a)), 0.14, 0.24, mat='frame', bevel=0.02,
              up=(math.sin(a), 0, math.cos(a)))
    for yy in P.get('hearth_hoops', (y0 + 1.6, y1 - 1.6)):
        hoop(B, c, r, yy, 0.45, 0.16, mat='frame', n=n)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        u = V((math.cos(a), 0, -math.sin(a)))
        o = V((r * math.sin(a), y0, r * math.cos(a)))
        nrm = V((math.sin(a), 0, math.cos(a)))
        with B.at(M=lib.basis(o, u, (0, 1, 0), nrm)):
            B.box((2.6, 2.8, 1.2), at=(0, 1.4, 0.4), mat='frame', bevel=0.05)
            B.box((1.2, 1.1, 0.3), at=(0, 1.1, 1.0), mat='soot', bevel=0.02)
            B.box((0.5, 0.6, 3.0), at=(0, 0.3, 2.0), mat='refractory', bevel=0.03)
        B.tube([o + nrm * 1.0 + V((0, 4.8, 0)), o + nrm * 1.8 + V((0, 3.5, 0)), o + nrm * 1.8 + V((0, 0.0, 0))], 0.22, mat='pipeDark', n=10)
    # tuyere band: a recessed hot drum seen through a ring of window frames (exact openings, the glow is real)
    rt, t0, t1, nw = P['tuyere']
    B.lathe([(0, t0), (rt - 0.25, t0), (rt - 0.25, t1), (0, t1)], (0, 0, 0), mat='hot', n=n, bevel=0.0)
    B.lathe([(rt - 0.3, t0), (r + 0.05, t0), (r + 0.05, t0 + 0.35), (rt - 0.3, t0 + 0.35)], (0, 0, 0), mat='frame', n=n, closed=True, bevel=0.03)
    B.lathe([(rt - 0.3, t1 - 0.35), (r + 0.05, t1 - 0.35), (r + 0.05, t1), (rt - 0.3, t1)], (0, 0, 0), mat='frame', n=n, closed=True, bevel=0.03)
    for k in range(nw):
        a = 2 * math.pi * k / nw
        with B.at(at=(rt * math.sin(a), (t0 + t1) / 2, rt * math.cos(a)), rot=(0, math.degrees(a), 0)):
            B.box((0.42, t1 - t0 - 0.6, 0.55), at=(0, 0, 0), mat='frame', bevel=0.03)
            B.cyl(0.14, 0.9, at=(0, -0.15, 0.55), mat='pipeDark', n=10)        # tuyere stock nose
    K.glow_ring(B, c, rt - 0.2, (t0 + t1) / 2, h=(t1 - t0) - 0.7, n=nw, color='#ff8a28', radiance=0.7)
    # collar and bosh shoulder
    rc, c0, c1 = P['collar']
    B.lathe([(0, c0), (rc, c0), (rc, c1), (0, c1)], (0, 0, 0), mat='frame', n=n, bevel=0.04)
    # v4 r3 (the concept): a stepped dark bosh between the tuyere band and the light shaft, each course a plated band
    # with a proud lip at its top (one crisp shadow line per step) and modelled course seams
    for (ya, yb_, rr) in P.get('bosh', []):
        B.lathe([(0, ya), (rr, ya), (rr, yb_), (0, yb_)], (0, 0, 0), mat='frame2', n=n, bevel=0.04)
        hoop(B, c, rr, yb_ - 0.32, 0.32, 0.26, mat='frame', n=n)
        lap_rings(B, lambda y, rr=rr: rr, ya + 0.4, yb_ - 0.5, 1.2, mat='frame2', n=n, out=0.03, h=0.1)
    # shaft: one lathe solid, the light plated shell (seams and courses are paint + normal)
    prof = P['shaft']
    B.lathe([(0, prof[0][1])] + prof + [(0, prof[-1][1])], (0, 0, 0), mat='shell', n=n, bevel=0.0, sharp=50)
    for (yy, hh) in P['hoops']:
        hoop(B, c, _shaft_r(prof, yy + hh / 2), yy, hh, 0.22, mat='frame', n=n)
    lap_rings(B, lambda y: _shaft_r(prof, y), prof[0][1], prof[-1][1], P.get('course', 2.25), mat='shell',
              skip=[yy + hh / 2 for (yy, hh) in P['hoops']], n=n)
    # bustle main (a torus) and the tuyere downlegs with their goosenecks
    rb, yb, tb, nl = P['bustle']
    pts = [(rb * math.sin(2 * math.pi * k / 40), yb, rb * math.cos(2 * math.pi * k / 40)) for k in range(41)]
    B.tube(pts, tb, mat='pipeDark', n=14, fillet=0.0)
    for k in range(nl):
        a = 2 * math.pi * (k + 0.5) / nl
        s, cc = math.sin(a), math.cos(a)
        B.tube([(rb * s, yb - 0.3, rb * cc), (rb * s, yb - 0.9, rb * cc), ((rt + 0.35) * s, t1 - 0.2, (rt + 0.35) * cc), ((rt + 0.35) * s, (t0 + t1) / 2 + 0.2, (rt + 0.35) * cc)],
               0.16, mat='pipeDark', n=8, fillet=0.35)
    # top: flange ring, cone, throat, cap, top platform
    rf, f0, f1 = P['flange']
    B.lathe([(0, f0), (rf, f0), (rf, f1), (0, f1)], (0, 0, 0), mat='frame', n=n, bevel=0.05)
    cone = P['cone']
    B.lathe([(0, cone[0][1])] + cone + [(0, cone[-1][1])], (0, 0, 0), mat='frame2', n=n, bevel=0.0, sharp=30)
    hoop(B, c, cone[1][0] - 0.1, cone[1][1] - 0.2, 0.4, 0.15, mat='frame', n=n)
    rth, h0, h1 = P['throat']
    B.lathe([(0, h0), (rth, h0), (rth, h1), (0, h1)], (0, 0, 0), mat=P.get('throat_mat', 'shell'), n=40, bevel=0.03)
    for yy in (h0 + 1.0, h1 - 0.9):
        hoop(B, c, rth, yy, 0.35, 0.12, mat='frame', n=40)
    rcap, k0, k1 = P['cap']
    B.lathe([(0, k0), (rcap + 0.15, k0), (rcap + 0.15, k0 + 0.3), (rcap, k0 + 0.3), (rcap, k1 - 0.3), (rcap + 0.15, k1 - 0.3),
             (rcap + 0.15, k1), (rcap - 0.3, k1), (rcap - 0.3, k1 - 0.6), (0, k1 - 0.6)], (0, 0, 0), mat='shell', n=40, bevel=0.03, sharp=30)
    if P.get('top_deck'):
        ty, tr = P['top_deck']
        K.platform_ring(B, c, ty, rth + 0.05, tr, n=32, brackets=8)
    # uptakes (inverted goosenecks into the throat) and the downcomer
    nu, ru, path = P['uptakes']
    for k in range(nu):
        a = math.pi / 4 + k * 2 * math.pi / nu
        s, cc = math.sin(a), math.cos(a)
        B.tube([(rr * s, yy, rr * cc) for rr, yy in path], ru, mat='pipeDark', n=16, fillet=1.2)
        B.lathe([(ru + 0.12, 0), (ru + 0.12, 0.25), (ru, 0.25), (ru, 0)], (path[0][0] * s, path[0][1], path[0][0] * cc), mat='frame', n=16, closed=True, bevel=0.02)
        B.lathe([(ru + 0.12, 0), (ru + 0.12, 0.25), (ru, 0.25), (ru, 0)], (path[1][0] * s, path[1][1] - 1.0, path[1][0] * cc), mat='frame', n=16, closed=True, bevel=0.02)
    if P.get('header'):
        rh, y0h, y1h = P['header']
        B.lathe([(0, y0h), (rh, y0h), (rh, y1h - 0.4), (rh - 0.5, y1h), (0, y1h)], (0, 0, 0), mat='frame2', n=24, bevel=0.03, sharp=30)
        hoop(B, c, rh, y0h + 0.8, 0.3, 0.12, mat='frame', n=24)
    rd, dpath = P['downcomer']
    B.tube(dpath, rd, mat='pipeDark', n=24 if rd > 1.2 else 18, fillet=min(2.4, 1.6 * rd))
    if len(dpath) > 4:
        # v5: flanged joints along the big downcomer and a flanged end where the building's main continues
        for (pa_, pb_) in zip(dpath[1:-1], dpath[2:]):
            a_, b_ = V(pa_), V(pb_)
            L_ = (b_ - a_).length
            with B.at(M=K.frame_along(a_, b_)):
                for t_ in (0.25, 0.75):
                    B.cyl(rd + 0.16, 0.32, at=(0, 0, L_ * t_), mat='frame', n=24, bevel=0.02)
        a_, b_ = V(dpath[-2]), V(dpath[-1])
        with B.at(M=K.frame_along(a_, b_)):
            B.cyl(rd + 0.22, 0.4, at=(0, 0, (b_ - a_).length - 0.2), mat='frame', n=24, bevel=0.02)
    for t in ((0.35, 0.6, 0.85) if len(dpath) <= 4 else ()):
        a, b = V(dpath[-2]), V(dpath[-1])
        q = a + (b - a) * t
        with B.at(M=K.frame_along(a, b)):
            L = (b - a).length * t
            B.cyl(rd + 0.14, 0.3, at=(0, 0, L), mat='frame', n=18, bevel=0.02)
    # v5: the extras the concept hangs on the body (bustle hangers, the cone-foot and hood decks, the wide top deck)
    for (ya, ra, rb) in P.get('decks', []):
        K.platform_ring(B, c, ya, ra, rb, n=48, brackets=12)
        for k in range(12):
            a = 2 * math.pi * (k + 0.5) / 12
            if k % 3 == 0:
                lamp(B, ((rb + 0.1) * math.sin(a), ya + 1.3, (rb + 0.1) * math.cos(a)), (math.sin(a), 0, math.cos(a)), size=0.26)
    # the tower
    T = P.get('tower')
    if T and T.get('style') == 'posts':
        _posts_tower(B, P, T, prof, c)
        T = None
    if T:
        hf = T['half']
        cols = [(-hf, -hf), (hf, -hf), (hf, hf), (-hf, hf)]
        legs = T.get('legs')
        if legs:
            # v4 r3 (the concept): heavy raking legs, plated box sections from the plinth corners to the first deck,
            # with stiffener bands, a base shoe and a cap where the laced column stands on them
            (b0, ly0), (b1, ly1) = legs
            for (sx, sz) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                pa, pb = V((sx * b0, ly0, sz * b0)), V((sx * b1, ly1, sz * b1))
                s0, s1 = T.get('leg_section', (2.2, 1.6))
                B.strut(pa, pb, (s0, s0), (s1, s1), 0.22, mat='frame2', bevel=0.04)
                d = (pb - pa)
                for t in [0.12 + 0.76 * i / 5 for i in range(6)]:
                    q = pa + d * t
                    sz_ = s0 + (s1 - s0) * t
                    with B.at(M=K.frame_along(pa, pb)):
                        B.box((sz_ + 0.12, sz_ + 0.12, 0.22), at=(0, 0, d.length * t), mat='frame', bevel=0.02)
                B.box((s0 + 0.8, 0.5, s0 + 0.8), at=(sx * b0, ly0 + 0.25, sz * b0), mat='frame', bevel=0.04)
                B.box((s1 + 0.6, 0.4, s1 + 0.6), at=(sx * b1, ly1 - 0.2, sz * b1), mat='frame', bevel=0.03)
                # a plate-girder tie from the leg to the tuyere platform ring (the legs carry the hearth deck)
                if T.get('leg_tie'):
                    yt, rt_ = T['leg_tie']
                    tt = (yt - ly0) / (ly1 - ly0)
                    bt = b0 + (b1 - b0) * tt
                    a_ = math.atan2(sx, sz)
                    plate_girder(B, (sx * bt, yt - 0.5, sz * bt), (rt_ * math.sin(a_), yt - 0.5, rt_ * math.cos(a_)), h=1.0)
                for (ex, ez) in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                    B.cyl(0.07, 0.16, at=(sx * b0 + ex * (s0 / 2 + 0.2), ly0 + 0.58, sz * b0 + ez * (s0 / 2 + 0.2)), mat='frame', n=6)
        for (x, z) in cols:
            laced_column(B, x, z, T['y0'], T['y1'], w=T['w'])
            lamp(B, (x + (0.75 if x > 0 else -0.75), T['y1'] - 0.6, z + (0.75 if z > 0 else -0.75)), (1 if x > 0 else -1, 0, 1 if z > 0 else -1))
        for ly in T['levels']:
            r_in = T.get('ring_in', {}).get(ly, _shaft_r(prof, ly) + 0.35)
            # ring girders between the legs; a round grating ring round the shell and walkways along the frame sides
            # (open corners: the shell reads through, as in the concept), radial joists, toe plates, rails, deck lamps
            for i in range(4):
                a, b = cols[i], cols[(i + 1) % 4]
                ibeam(B, (a[0], ly - 0.6, a[1]), (b[0], ly - 0.6, b[1]), h=0.9, b=0.4, mat='frame')
            ro = min(r_in + T.get('ring', 2.0), hf - 0.2)
            B.lathe([(r_in, ly - 0.14), (ro, ly - 0.14), (ro, ly), (r_in, ly)], (0, 0, 0), mat='grate', n=48, closed=True, bevel=0.0)
            B.lathe([(ro, ly - 0.1), (ro + 0.03, ly - 0.1), (ro + 0.03, ly + 0.1), (ro, ly + 0.1)], (0, 0, 0), mat='frame', n=48, closed=True, bevel=0.0)
            ww = T.get('walk', 1.6)
            for i in range(4):
                a, b = cols[i], cols[(i + 1) % 4]
                mx, mz = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
                nx, nz = (1 if mx > 0.1 else -1 if mx < -0.1 else 0), (1 if mz > 0.1 else -1 if mz < -0.1 else 0)
                L = 2 * hf - T['w']
                if nx:
                    B.box((ww, 0.14, L), at=(mx - nx * (ww / 2 - 0.3), ly - 0.07, 0), mat='grate', bevel=0.0)
                    K.railing(B, [(mx + nx * 0.3, ly, -L / 2), (mx + nx * 0.3, ly, L / 2)], post=1.8)
                else:
                    B.box((L, 0.14, ww), at=(0, ly - 0.07, mz - nz * (ww / 2 - 0.3)), mat='grate', bevel=0.0)
                    K.railing(B, [(-L / 2, ly, mz + nz * 0.3), (L / 2, ly, mz + nz * 0.3)], post=1.8)
                # connector from the ring to the walkway at mid-side
                rin_w = hf - ww + 0.3
                if ro < rin_w:
                    if nx:
                        B.box((rin_w - ro + 0.2, 0.14, 1.4), at=(nx * (ro + rin_w) / 2, ly - 0.07, 0), mat='grate', bevel=0.0)
                    else:
                        B.box((1.4, 0.14, rin_w - ro + 0.2), at=(0, ly - 0.07, nz * (ro + rin_w) / 2), mat='grate', bevel=0.0)
            if ro < hf - ww + 0.1:
                pts = []
                for k in range(40):
                    a = 2 * math.pi * k / 40
                    if min(abs(math.sin(a)), abs(math.cos(a))) < 0.12:   # leave the connector openings
                        if pts:
                            K.railing(B, pts, post=1.8)
                        pts = []
                        continue
                    pts.append((ro * math.sin(a), ly, ro * math.cos(a)))
                if pts:
                    K.railing(B, pts, post=1.8)
            for k in range(8):
                a = 2 * math.pi * (k + 0.5) / 8
                s_, cc = math.sin(a), math.cos(a)
                q = hf / max(abs(s_), abs(cc))
                B.bar((r_in * s_, ly - 0.4, r_in * cc), (q * s_, ly - 0.4, q * cc), 0.18, 0.5, mat='frame', bevel=0.0)
            lamp(B, (hf + 0.35, ly + 1.4, 0.0), (1, 0, 0))
            lamp(B, (0.0, ly + 1.4, hf + 0.35), (0, 0, 1))
        # the tuyere platform: a round railed ring at the band's foot (the glow reads above it, as in the concept)
        ty0 = P['tuyere'][1]
        K.platform_ring(B, c, ty0, P['hearth'][0] + 0.05, P['hearth'][0] + 1.9, n=48, brackets=12)
        for (ya, yb_) in T['xbrace']:
            for i in range(4):
                a, b = cols[i], cols[(i + 1) % 4]
                for (p, q) in (((a, ya), (b, yb_)), ((b, ya), (a, yb_))):
                    B.bar((p[0][0], p[1] + 0.6, p[0][1]), (q[0][0], q[1] - 1.2, q[0][1]), 0.2, 0.2, mat='frame', bevel=0.0)
        lx, lz = T['ladder']
        ly0_ = T.get('ladder_y0', T['y0'])
        K.ladder(B, (lx * (hf + 0.66), ly0_, lz * (hf - 1.6)), (lx, 0, 0), T['levels'][-1] - ly0_)
    return works({
        'shell': {'axis': (0, 0), 'course': 2.25, 'joint': 2.0, 'bolts': 0.32, 'rust': 0.5, 'tone': 0.1, 'drip': 0.3},
        'frame2': {'axis': (0, 0), 'course': 1.6, 'joint': 1.6, 'rust': 0.15, 'tone': 0.08},
        'concrete2': {'course': 1.5, 'joint': 3.0, 'rust': 0.0, 'dark': 0.25},
        'concrete': {'course': 3.0, 'joint': 3.0, 'rust': 0.0, 'dark': 0.3},
        'hot': {'crust': 0.0},
    })


# ------------------------------------------------------------------------------------------------------------------
# banded stack
# ------------------------------------------------------------------------------------------------------------------
STACK = {   # bandedStack, measured: base block 10.2 x 3.1, flare r 5.3 -> 3.78 (3.1 -> 9.6), shaft r 3.75 to 42.6,
            # platforms 19.4 and 42.8, top lip r 4.05 at 46; bands from the component image (dark / light)
    'base': (11.0, 3.1), 'flare': [(5.0, 3.1), (5.0, 4.3), (3.78, 9.6)], 'r': 3.75, 'top': 46.0,
    'bands': [(9.6, 18.6, 'frame2'), (18.6, 25.0, 'shell'), (25.0, 33.8, 'frame2'), (33.8, 42.6, 'shell')],
    'platforms': [(19.4, 6.2), (42.8, 6.0)], 'ladder': 90.0,
}
# the image reads, top down: dark top, light band, dark band (lower platform), light band, dark flare. Shell bands:
STACK['bands'] = [(9.6, 18.6, 'shell'), (18.6, 25.0, 'frame2'), (25.0, 33.8, 'shell'), (33.8, 42.6, 'frame2')]


def banded_stack(B, P=STACK):
    n = P.get('segments', 56)
    c = (0.0, 0.0)
    bw, bh = P['base']
    B.prism(lib.chamfer_rect(bw, bw, 0.35), 0.0, bh, mat='frame2', bevel=0.05)
    B.prism(lib.chamfer_rect(bw + 0.3, bw + 0.3, 0.4), 0.0, 0.5, mat='concrete2', bevel=0.04)
    fl = P['flare']
    B.lathe([(0, fl[0][1])] + fl + [(0, fl[-1][1])], (0, 0, 0), mat='frame2', n=n, bevel=0.03, sharp=30)
    # gussets round the foot and anchor bolt chairs
    for k in range(16):
        a = 2 * math.pi * (k + 0.5) / 16
        s, cc = math.sin(a), math.cos(a)
        with B.at(M=lib.basis((fl[0][0] * s, bh, fl[0][0] * cc), (cc, 0, -s), (0, 1, 0), (s, 0, cc))):
            B.add(lib.bm_prism([(0.0, 0.0), (0.45, 0.0), (0.0, 1.1)], -0.04, 0.04), rot=(0, -90, 0), mat='frame', bevel=0.0)
            B.box((0.4, 0.25, 0.4), at=(0, 0.125, 0.3), mat='frame', bevel=0.02)
    r = P['r']
    for (y0, y1, m) in P['bands']:
        B.lathe([(r, y0), (r, y1)], (0, 0, 0), mat=m, n=n, bevel=0.0)
        hoop(B, c, r, y0 - 0.18, 0.36, 0.12, mat='frame', n=n)
        lap_rings(B, lambda y: r, y0, y1, P.get('course', 2.2), mat=m, skip=[py for (py, _) in P['platforms']], n=n, out=0.03, h=0.12)
    top0 = P['bands'][-1][1]
    T = P['top']
    B.lathe([(r, top0), (r, T - 1.4), (r + 0.3, T - 0.6), (r + 0.3, T), (r - 0.3, T), (r - 0.3, T - 3.0), (0, T - 3.0)], (0, 0, 0), mat='frame2', n=n, bevel=0.03, sharp=25)
    hoop(B, c, r, top0 - 0.18, 0.36, 0.12, mat='frame', n=n)
    hoop(B, c, r + 0.3, T - 0.35, 0.35, 0.08, mat='soot', n=n)
    for (py, ro) in P['platforms']:
        K.platform_ring(B, c, py, r + 0.06, ro, n=32, brackets=8)
        for k in range(4):
            a = math.pi / 4 + k * math.pi / 2
            lamp(B, ((r + 0.02) * math.sin(a), py + 1.0, (r + 0.02) * math.cos(a)), (math.sin(a), 0, math.cos(a)), size=0.3)
    a = P['ladder'] * DEG
    nn = V((math.sin(a), 0, math.cos(a)))
    p0, p1 = P['platforms'][0][0], P['platforms'][1][0]
    K.ladder(B, V((0, bh, 0)) + nn * (fl[0][0] + 0.3), nn, p0 - bh)
    K.ladder(B, V((0, p0, 0)) + nn * (r + 0.05), nn, p1 - p0)
    B.R.obstruction((0.7 * (r + 0.3), T + 0.45, 0.7 * (r + 0.3)))
    return works({
        'shell': {'axis': (0, 0), 'course': 2.2, 'joint': 2.4, 'bolts': 0.3, 'rust': 0.6, 'tone': 0.07},
        'frame2': {'axis': (0, 0), 'course': 2.2, 'joint': 2.4, 'rust': 0.15, 'tone': 0.09},
    })


# ------------------------------------------------------------------------------------------------------------------
# gable shed segment
# ------------------------------------------------------------------------------------------------------------------
SHED = {   # shedSegment, measured: 28 x 36, eaves 14.4, ridge 21.2, monitor 5.6 x 27 to 24; long face +X with 5 bays
    'W': 27.2, 'L': 36.0, 'eave': 14.4, 'ridge': 21.2, 'overhang': 0.4, 'bays': 5, 'dado': 1.6,
    'windows': (8.9, 10.5, 4.6), 'monitor': (5.6, 27.0, 3.3, 0.7), 'door': (1, 14.8), 'pilaster': (0.7, 0.45),
}


def _spans(a, b, cuts):
    """[a, b] minus the (unordered) intervals in cuts, as a list of (lo, hi)."""
    out = [(a, b)]
    for (c0, c1) in cuts:
        c0, c1 = min(c0, c1), max(c0, c1)
        nxt = []
        for (lo, hi) in out:
            if c1 <= lo or c0 >= hi:
                nxt.append((lo, hi)); continue
            if c0 > lo: nxt.append((lo, c0))
            if c1 < hi: nxt.append((c1, hi))
        out = nxt
    return [(lo, hi) for (lo, hi) in out if hi - lo > 0.05]


# v4 r3: the concept's shed wall: flat light panels in a grid (no corrugation, no high windows), heavy dark pilasters,
# crew doors with lamps at the foot of the bays and a roller door at the back bay
SHED_V4 = dict(SHED)
SHED_V4.update({
    'windows': None, 'pilaster': (1.0, 0.75), 'roller': (0, 5.6, 7.0), 'doors': [-7.2, 7.2], 'door': None,
    'wall_joints': [4.4, 7.2, 10.0, 12.8],
    'paint': {
        'clad': {'course': 2.8, 'joint': 2.4, 'corr': 0.0, 'bolts': 0.6, 'rust': 0.45, 'tone': 0.09, 'dark': 0.3, 'stagger': False},
        'clad2': {'course': 3.2, 'joint': 12.0, 'corr': 0.3, 'rust': 0.35, 'tone': 0.05, 'dark': 0.2},
        'frame2': {'rust': 0.15},
    },
})


SHED_V5 = dict(SHED_V4)
SHED_V5.update({
    'canopies': True, 'wall_pipes': [(1, 3.3, 0.32), (-1, 3.3, 0.32), (1, 11.8, 0.22)], 'tray': (1, 13.0),
    'roof_units': [(1, -11.0), (1, 9.0), (-1, -4.0), (-1, 13.0)], 'ridge_vents': 3, 'dock': (0, 9.0, 3.2, 1.2),
    'pilaster_lamps': (4.2, 10.4),
    'paint': {
        'clad': {'course': 2.8, 'joint': 2.4, 'corr': 0.0, 'bolts': 0.6, 'rust': 0.5, 'tone': 0.13, 'dark': 0.6, 'stagger': False,
                 'seam_w': 0.05, 'streak': 0.2, 'streak_f': 3.2, 'drip': 0.3},
        'clad2': {'course': 3.2, 'joint': 12.0, 'corr': 0.3, 'rust': 0.4, 'tone': 0.07, 'dark': 0.35, 'streak': 0.2},
        'frame2': {'rust': 0.15},
    },
})


def _shed_dressing(B, P, hx, hz, E, Rg, ov, bay, nb, pd):
    """v5: door canopies, wall pipe runs with flanges and amber rings on brackets, a cable tray under the eaves, extra
    pilaster lamps, roof curb units on the slopes, ridge ventilators, a loading dock with a stair at the roller door."""
    if P.get('canopies'):
        for dz in P.get('doors', []):
            x = hx + 0.02
            B.box((1.3, 0.14, 2.4), at=(x + 0.65, 2.95, dz), mat='frame2', bevel=0.02)
            B.box((0.1, 0.24, 2.5), at=(x + 1.3, 2.92, dz), mat='frame', bevel=0.0)
            for s_ in (-1, 1):
                B.bar((x, 3.9, dz + s_ * 1.1), (x + 1.25, 3.0, dz + s_ * 1.1), 0.06, 0.06, mat='frame', bevel=0.0)
            # a step and kick plate under the door
            B.box((1.0, 0.18, 1.9), at=(x + 0.5, 0.09, dz), mat='concrete', bevel=0.02)
    for (sx, y, r) in P.get('wall_pipes', []):
        x = sx * (hx + pd + 0.15 + r)
        # skip the roller door bay (and keep 1.5 m clear of the gable corners)
        cuts = []
        rd = P.get('roller')
        if rd and sx > 0 and y < rd[2] + 0.6:
            zc = -hz + bay * (rd[0] + 0.5)
            cuts.append((zc - rd[1] / 2 - 1.0, zc + rd[1] / 2 + 1.0))
        if sx > 0 and y < 3.8:
            cuts += [(dz - 1.2, dz + 1.2) for dz in P.get('doors', [])]
        for (za, zb) in _spans(-hz + 1.5, hz - 1.5, cuts):
            if zb - za < 3.0:
                continue
            K.pipe(B, [(x, y, za), (x, y, zb)], r=r, mat='pipeDark', flanges=True, rings=True, ring_mat='amber')
            for zz in [za + 0.8 + k * 3.6 for k in range(int((zb - za - 1.0) / 3.6) + 1)]:
                B.bar((sx * (hx + 0.05), y - r - 0.12, zz), (x + sx * r, y - r - 0.12, zz), 0.12, 0.12, mat='frame', bevel=0.0)
                B.box((0.08, 0.5, 0.3), at=(sx * (hx + 0.06), y - r - 0.1, zz), mat='frame', bevel=0.0)
            # a drop at the far end into a valve on the dado
            K.pipe(B, [(x, y, zb), (x, 0.9, zb)] if y < 6 else [(x, y, zb), (x, y - 2.2, zb)], r=r * 0.8, mat='pipeDark', flanges=True, rings=False)
    if P.get('tray'):
        sx, y = P['tray']
        x = sx * (hx + pd + 0.45)
        K.cable_tray(B, (x, y, -hz + 1.0), (x, y, hz - 1.0), w=0.5)
        for zz in [-hz + 1.5 + k * 4.8 for k in range(int((2 * hz - 2.0) / 4.8) + 1)]:
            B.bar((sx * (hx + 0.05), y - 0.1, zz), (x + sx * 0.25, y - 0.1, zz), 0.1, 0.1, mat='frame', bevel=0.0)
    for y in P.get('pilaster_lamps', ())[1:]:
        for sx in (1, -1):
            for i in range(1, nb):
                lamp(B, (sx * (hx + pd + 0.02), y, -hz + bay * i), (sx, 0, 0), size=0.28)
    ang = math.atan2(Rg - E, hx + ov)
    for (sx, zc) in P.get('roof_units', []):
        xf = sx * (hx + ov) * 0.45
        yf = E + (Rg - E) * 0.55
        with B.at(at=(xf, yf, zc), rot=(0, 0, math.degrees(ang) * sx)):
            B.box((2.6, 0.5, 3.0), at=(0, 0.25, 0), mat='frame2', bevel=0.04)        # curb
        # the unit itself stands level on the curb
        B.box((2.2, 1.3, 2.6), at=(xf, yf + 0.9, zc), mat='panel', bevel=0.05)
        B.box((2.3, 0.14, 2.7), at=(xf, yf + 1.6, zc), mat='frame', bevel=0.02)
        for dz in (-0.6, 0.6):
            B.cyl(0.42, 0.18, at=(xf, yf + 1.68, zc + dz), rot=(90, 0, 0), mat='louvre', n=16, bevel=0.0)
        louvre_bank(B, (xf + sx * 1.11, yf + 0.5, zc + (0.9 if sx > 0 else -0.9)), (0, 0, -1) if sx > 0 else (0, 0, 1), 1.8, 0.6, pitch=0.15, depth=0.1)
    nv = P.get('ridge_vents', 0)
    mw, ml, mh, mr = P['monitor']
    for k in range(nv):
        for sz in (-1, 1):
            zc = sz * (ml / 2 + 0.9 + 1.4 * k)
            if abs(zc) > hz - 0.8:
                continue
            B.vcyl(0.45, 0.9, (0.0, Rg - 0.1, zc), mat='frame2', n=16)
            B.lathe([(0.0, 0.0), (0.62, 0.0), (0.55, 0.3), (0.0, 0.45)], (0.0, Rg + 0.8, zc), mat='frame', n=16, bevel=0.0)
    if P.get('dock'):
        bi, dw, dd, dh = P['dock']
        zc = -hz + bay * (bi + 0.5)
        rd = P.get('roller')
        x0 = hx + pd
        B.box((dd, dh, dw), at=(x0 + dd / 2, dh / 2, zc), mat='concrete2', bevel=0.04)
        B.box((0.2, 0.25, dw), at=(x0 + dd - 0.1, dh - 0.12, zc), mat='hazard', bevel=0.0)
        for dz in (-dw / 2 + 0.6, dw / 2 - 0.6):
            B.box((0.25, 0.6, 0.35), at=(x0 + dd + 0.12, dh - 0.45, zc + dz), mat='frame', bevel=0.02)   # bumpers
        K.stair(B, (x0 + 0.6, 0.0, zc + dw / 2 + 2.0), (0, 0, -1), dh, w=1.0)
        K.railing(B, [(x0 + 0.1, dh, zc - dw / 2 + 0.1), (x0 + dd - 0.2, dh, zc - dw / 2 + 0.1)], post=1.4)


def gable_shed(B, P=SHED):
    W, L, E, Rg, ov = P['W'], P['L'], P['eave'], P['ridge'], P['overhang']
    hx, hz = W / 2, L / 2
    nb = P['bays']
    bay = L / nb
    pw, pd = P['pilaster']
    wy0, wy1, ww = P['windows'] or (0, 0, 0)
    dado = P['dado']
    # long walls (+X and -X): dado, corrugated sheets with window openings, pilasters, window strips
    for sx in (1, -1):
        x = sx * hx
        u = (0, 0, -1) if sx > 0 else (0, 0, 1)
        z0 = hz if sx > 0 else -hz
        o = (x, 0.0, z0)
        holes = []
        fxo = lambda zc: (hz - zc) if sx > 0 else (zc + hz)    # face coordinate of a z
        if P.get('windows'):
            for i in range(nb):
                zc = -hz + bay * (i + 0.5)
                fx = fxo(zc)
                holes.append((fx - ww / 2, wy0, fx + ww / 2, wy1))
                window_strip(B, (x, wy0, zc + (ww / 2 if sx > 0 else -ww / 2)), u, ww, wy1 - wy0, panes=4)
        # v4 r3 (the concept): a roller door in one bay of the +X face: an exact opening, a recessed ribbed shutter,
        # a dark portal frame with a hood, jamb lamps
        rd = P.get('roller')
        if rd and sx > 0:
            ri, rw_, rh_ = rd
            zc = -hz + bay * (ri + 0.5)
            fx = fxo(zc)
            holes.append((fx - rw_ / 2, 0.0, fx + rw_ / 2, rh_))
            B.box((0.12, rh_, rw_), at=(x - 0.45, rh_ / 2, zc), mat='frame2', bevel=0.0)
            for k in range(int(rh_ / 0.3)):
                B.box((0.06, 0.06, rw_ - 0.1), at=(x - 0.36, 0.2 + 0.3 * k, zc), mat='frame2', bevel=0.0)
            for dz in (-1, 1):
                B.box((0.7, rh_ + 0.5, 0.45), at=(x + 0.12, (rh_ + 0.5) / 2, zc + dz * (rw_ / 2 + 0.22)), mat='frame', bevel=0.04)
                lamp(B, (x + 0.6, rh_ + 1.0, zc + dz * (rw_ / 2 - 0.4)), (1, 0, 0), size=0.26)
            B.box((0.9, 0.55, rw_ + 1.6), at=(x + 0.2, rh_ + 0.3, zc), mat='frame', bevel=0.04)
            B.box((0.5, 0.9, rw_ + 0.4), at=(x - 0.1, rh_ - 0.4, zc), mat='frame2', bevel=0.02)    # coil box
        clad_panel(B, (x, dado, z0), u, L, E - dado, holes=[(a, max(b_, dado) - dado, c_, d_ - dado) for (a, b_, c_, d_) in holes])
        if P.get('wall_joints'):
            # modelled horizontal panel joints: a thin cover strip every course, a crisp shadow line at any distance
            for yj in P['wall_joints']:
                for (za, zb) in _spans(-hz, hz, [((z0 - sx * a) if sx > 0 else (a + z0), (z0 - sx * c_) if sx > 0 else (c_ + z0)) for (a, b_, c_, d_) in holes if b_ <= yj <= d_]):
                    B.box((0.05, 0.07, zb - za), at=(x + sx * 0.02, yj, (za + zb) / 2), mat='clad', bevel=0.0)
        for (dz_, ) in [(d,) for d in (P.get('doors', []) if sx > 0 else [])]:
            B.R.door((x + 0.02, 0.0, dz_), (1, 0, 0))
        cuts = [((z0 - a) if sx > 0 else (a + z0), (z0 - c_) if sx > 0 else (c_ + z0)) for (a, b_, c_, d_) in holes if b_ < dado]
        for (za, zb) in _spans(-hz, hz, cuts):
            B.box((0.3, dado, zb - za), at=(x - sx * 0.07, dado / 2, (za + zb) / 2), mat='frame2', bevel=0.03)
            B.box((0.34, 0.12, zb - za + 0.1), at=(x + sx * 0.02, dado + 0.02, (za + zb) / 2), mat='frame', bevel=0.02)
        for i in range(nb + 1):
            zc = -hz + bay * i
            zc = max(-hz + pw / 2, min(hz - pw / 2, zc))
            ibeam(B, (x + sx * pd / 2, 0.0, zc), (x + sx * pd / 2, E - 0.1, zc), h=pd, b=pw, tw=0.05, tf=0.06, mat='frame', up=(sx, 0, 0))
        # eaves: gutter and fascia
        B.box((0.5, 0.45, L + 0.3), at=(x + sx * (ov - 0.05), E - 0.05, 0), mat='frame', bevel=0.04)
        # downpipes at the corners
        for zc in (-hz + 0.6, hz - 0.6):
            B.vcyl(0.1, E - 0.3, (x + sx * 0.75, 0.15, zc), mat='frame', n=10)
            for yy in (2.5, 6.5, 10.5):
                B.box((0.6, 0.08, 0.08), at=(x + sx * 0.45, yy, zc), mat='frame', bevel=0.0)
        # lamps on the pilasters
        for i in range(1, nb):
            zc = -hz + bay * i
            lamp(B, (x + sx * (pd + 0.02), 4.2, zc), (sx, 0, 0), size=0.28)
    # gable ends: corrugated wall to the eaves plus the triangle, corner trims, girts, verge trims (outward only)
    for sz in (1, -1):
        z = sz * hz
        u = (1, 0, 0) if sz > 0 else (-1, 0, 0)
        o = (-hx if sz > 0 else hx, dado, z)
        clad_panel(B, o, u, W, E - dado)
        B.box((W, dado, 0.3), at=(0, dado / 2, z - sz * 0.07), mat='frame2', bevel=0.03)
        tri = [(-hx, E), (hx, E), (0.0, Rg - 0.25)]
        B.add(lib.bm_prism([(x_, y_) for x_, y_ in tri], -0.2, 0.0), at=(0, 0, z), rot=(0, 0 if sz > 0 else 180, 0), mat='clad', bevel=0.02)
        for sx in (1, -1):
            B.box((0.55, E + 0.2, 0.55), at=(sx * (hx + 0.12), (E + 0.2) / 2, z + sz * 0.12), mat='frame', bevel=0.04)
            # verge: along the rake, outside the gable plane
            a = V((sx * (hx + ov), E - 0.05, z + sz * 0.15))
            b = V((0.0, Rg + 0.05, z + sz * 0.15))
            B.bar(a, b, 0.3, 0.5, mat='frame', up=(0, 1, 0), bevel=0.03)
        for gy in (5.6, 10.0):
            B.box((W - 0.4, 0.1, 0.06), at=(0, gy, z + sz * 0.03), mat='frame2', bevel=0.0)
    # roof sheets (corrugation in the paint), ridge cap
    for sx in (1, -1):
        a0 = V((sx * (hx + ov), E - 0.02, 0))
        a1 = V((0.0, Rg, 0))
        prof = [(sx * (hx + ov), E), (0.0, Rg), (0.0, Rg - 0.22), (sx * (hx + ov), E - 0.22)]
        if sx < 0:
            prof = list(reversed(prof))
        B.add(lib.bm_prism(prof, -hz, hz), mat='clad2', bevel=0.02)
    B.box((0.7, 0.35, L), at=(0, Rg + 0.08, 0), mat='frame', bevel=0.04)
    mw, ml, mh, mr = P['monitor']
    # standing-seam ribs down both slopes (stopping at the monitor's cheeks) and a lap flashing every sheet length
    rp = P.get('rib', 0.9)
    for sx in (1, -1):
        ribbed_slope(B, (sx * (hx + ov - 0.05), E), (sx * 0.4, Rg - 0.4 * (Rg - E) / (hx + ov)), -hz, hz, pitch=rp,
                     stop=lambda z, sx=sx: (sx * (mw / 2 + 0.25)) if abs(z) < ml / 2 + 0.3 else None)
        ang = math.atan2(Rg - E, hx + ov)
        for f in (0.36, 0.7):      # sheet end laps: a low step across the slope
            xa = sx * (hx + ov) * (1 - f)
            ya = E + (Rg - E) * f
            B.bar((xa, ya + 0.02, -hz + 0.1), (xa, ya + 0.02, hz - 0.1), 0.18, 0.05, mat='clad2', up=(sx * math.sin(ang), math.cos(ang), 0), bevel=0.0)
    # dark eaves band under the gutter on the long faces (the concept's fascia line)
    for sx in (1, -1):
        B.box((0.12, 0.7, L - 0.2), at=(sx * (hx + 0.06), E - 0.62, 0), mat='frame2', bevel=0.02)
    # roof monitor: louvred sides, light cheeks, a shallow roof with dark trims
    ang = math.atan2(Rg - E, hx + ov)
    ybase = Rg - (mw / 2) * math.tan(ang)
    for sx in (1, -1):
        louvre_bank(B, (sx * mw / 2, ybase + 0.15, ml / 2 if sx > 0 else -ml / 2), (0, 0, -1) if sx > 0 else (0, 0, 1), ml, mh - 0.3, pitch=0.3)
        B.box((0.2, 0.6, ml + 0.2), at=(sx * mw / 2, ybase - 0.1, 0), mat='frame', bevel=0.02)
        for k in range(9):
            B.box((0.18, mh, 0.18), at=(sx * (mw / 2 + 0.05), ybase + mh / 2, -ml / 2 + ml * k / 8), mat='frame', bevel=0.02)
    for sz in (1, -1):
        B.box((mw, mh, 0.2), at=(0, ybase + mh / 2, sz * (ml / 2 - 0.1)), mat='clad', bevel=0.03)
        B.add(lib.bm_prism([(-mw / 2 - 0.3, ybase + mh), (mw / 2 + 0.3, ybase + mh), (0.0, ybase + mh + mr)], -0.15, 0.15), at=(0, 0, sz * (ml / 2 + 0.05)), mat='frame', bevel=0.02)
    for sx in (1, -1):
        prof = [(sx * (mw / 2 + 0.3), ybase + mh), (0.0, ybase + mh + mr), (0.0, ybase + mh + mr - 0.18), (sx * (mw / 2 + 0.3), ybase + mh - 0.18)]
        if sx < 0:
            prof = list(reversed(prof))
        B.add(lib.bm_prism(prof, -ml / 2 - 0.2, ml / 2 + 0.2), mat='clad2', bevel=0.02)
        ribbed_slope(B, (sx * (mw / 2 + 0.3), ybase + mh), (sx * 0.3, ybase + mh + mr * (1 - 0.3 / (mw / 2 + 0.3))), -ml / 2 - 0.2, ml / 2 + 0.2, pitch=rp, w=0.08, h=0.06)
    B.box((0.5, 0.25, ml + 0.4), at=(0, ybase + mh + mr + 0.06, 0), mat='frame', bevel=0.03)
    # v5 (second review): the concept's secondary layer on the walls and roof
    _shed_dressing(B, P, hx, hz, E, Rg, ov, bay, nb, pd)
    # crew door (fleet kit) on the +X face
    if P.get('door'):
        side, dz = P['door']
        B.R.door((side * (hx + 0.02), 0.0, dz), (side, 0, 0))
    if P.get('paint'):
        return works(P['paint'])
    return works({
        'clad': {'course': 4.2, 'joint': 1e3, 'corr': 0.22, 'rust': 0.45, 'tone': 0.05, 'dark': 0.25},
        'clad2': {'course': 3.2, 'joint': 12.0, 'corr': 0.3, 'rust': 0.35, 'tone': 0.05, 'dark': 0.2},
        'frame2': {'rust': 0.15},
    })


# ------------------------------------------------------------------------------------------------------------------
# pour bay
# ------------------------------------------------------------------------------------------------------------------
# v5 (second review): an open portal like the concept: no slab roof over the crane (a dark deck over the back third
# only), a bigger amber bridge girder, the runner along +Z out of the bay toward the casthouse (22 m, brighter), the
# ladle track along X at the front, a railed control house inside the portal
POUR_V5 = None   # set below (needs POUR)
POUR = {   # pourBay, measured: x -9.5..9.5 (open to +X), z -13..13, h 15.5; crane girder 10.8-12.3, truss 13.6-15.3
    'xf': 8.4, 'xb': -8.4, 'zs': 12.0, 'H': 15.4, 'eave': 13.6, 'runway': 8.6, 'crane_x': 5.4,
    'runner': (-3.4, 8.9, -2.6, 2.4), 'rails': (3.4, -6.4, 9.4), 'ladle_x': 1.6,
}


POUR_V5 = dict(POUR)
POUR_V5.update({
    'roof': 0.32, 'girder': (1.0, 2.0),
    'runner': (0.0, 22.0, 0.0, 2.8), 'runner_at': (0.6, -7.6, -90.0), 'runner_glow': 2.6,
    'rails': (7.2, 2.8, 9.6), 'ladle_x': 6.4,
    'control': (3.4, 7.9, -6.4, -2.2, 3.8), 'trolley_z': 4.2,
})


def pour_bay(B, P=POUR):
    xf, xb, zs, H, E = P['xf'], P['xb'], P['zs'], P['H'], P['eave']
    # floor pad and the casting pit outline
    B.box((xf - xb + 1.6, 0.16, 2 * zs + 1.4), at=((xf + xb) / 2 + 0.4, 0.08, 0), mat='concrete2', bevel=0.03)
    # columns: heavy built-up box columns on plinths
    for x in (xf, xb):
        for sz in (-1, 1):
            z = sz * zs
            B.box((2.2, 0.8, 2.4), at=(x, 0.4, z), mat='concrete', bevel=0.06)
            B.box((1.3, E + 0.2, 1.5), at=(x, 0.8 + (E - 0.6) / 2, z), mat='frame', bevel=0.05)
            for dx in (-0.66, 0.66):   # flange edges proud of the web plates (a built-up section)
                B.box((0.06, E - 0.6, 1.7), at=(x + dx, 0.8 + (E - 0.6) / 2, z), mat='frame', bevel=0.0)
            B.box((1.6, 0.3, 1.8), at=(x, E + 0.35, z), mat='frame', bevel=0.03)
            for yy in [1.6 + 2.4 * k for k in range(int((E - 2.0) / 2.4))]:   # diaphragm / batten plates
                B.box((1.36, 0.1, 1.56), at=(x, yy, z), mat='frame', bevel=0.01)
            B.box((1.9, 0.06, 2.1), at=(x, 0.83, z), mat='frame', bevel=0.01)                  # base plate
            for dx in (-0.8, 0.8):
                for dz in (-0.9, 0.9):
                    B.cyl(0.05, 0.12, at=(x + dx, 0.9, z + dz), rot=(90, 0, 0), mat='frame', n=6)  # anchor nuts
            # runway corbel
            B.box((1.2, 1.0, 0.9), at=(x - (0.9 if x > 0 else -0.9), P['runway'] - 0.95, z - sz * 0.9), mat='frame', bevel=0.03)
            lamp(B, (x + (0.68 if x > 0 else -0.68), 8.2, z), (1 if x > 0 else -1, 0, 0), size=0.3)
    # -Z side: lattice infill between the columns (struts and X braces); +Z side: struts and knee braces
    for sz in (-1, 1):
        z = sz * zs
        levels = (4.6, 9.0, E - 0.4)
        for ly in levels:
            ibeam(B, (xb + 0.7, ly, z), (xf - 0.7, ly, z), h=0.45, b=0.25, mat='frame')
        if sz < 0:
            for (ya, yb) in ((0.9, 4.6), (4.6, 9.0), (9.0, E - 0.4)):
                for k in range(4):
                    xa = xb + 0.7 + (xf - xb - 1.4) * k / 4
                    xb2 = xb + 0.7 + (xf - xb - 1.4) * (k + 1) / 4
                    B.bar((xa, ya, z), (xb2, yb, z), 0.16, 0.16, mat='frame', bevel=0.0)
                    B.bar((xb2, ya, z), (xa, yb, z), 0.16, 0.16, mat='frame', bevel=0.0)
        else:
            for x, sgn in ((xf, -1), (xb, 1)):
                B.bar((x + sgn * 0.7, 6.5, z), (x + sgn * 4.0, 9.0, z), 0.3, 0.3, mat='frame', bevel=0.02)
    # front eaves plate girder, front and back roof trusses, roof deck and fascia
    plate_girder(B, (xf, E - 0.7, -zs - 0.8), (xf, E - 0.7, zs + 0.8), h=1.4, b=0.7, up=(0, 1, 0))
    plate_girder(B, (xb, E - 0.7, -zs - 0.8), (xb, E - 0.7, zs + 0.8), h=1.4, b=0.7, up=(0, 1, 0))
    for x in (xf, xb):
        warren(B, (x, E, -zs - 0.8), (x, E, zs + 0.8), H - E - 0.15, bay=2.1, chord=0.32, web=0.16)
    for k in range(7):
        z = -zs + 2 * zs * k / 6
        ibeam(B, (xb, H - 0.3, z), (xf, H - 0.3, z), h=0.5, b=0.25, mat='frame')
    # open roof: the crane and the pour read from above (concept); X bracing in the roof plane between the purlins
    for k in range(6):
        za, zb = -zs + 2 * zs * k / 6, -zs + 2 * zs * (k + 1) / 6
        B.rod((xb, H - 0.1, za), (xf, H - 0.1, zb), 0.06, mat='frame', n=6)
        B.rod((xb, H - 0.1, zb), (xf, H - 0.1, za), 0.06, mat='frame', n=6)
    for x in (xb, xf):
        B.box((0.5, 0.35, 2 * zs + 2.0), at=(x, H + 0.05, 0), mat='frame', bevel=0.03)
    # v4 r2: a profiled roof deck on the purlins (the open roof read as loose rafters poking over the shed from the
    # building camera); the crane still shows through the open +X face under the eaves girder, as in the concept
    if P.get('roof', True):
        rm_ = P.get('roof_mat', 'frame2')     # v4 r3: dark steel deck (the concept); a light deck read as a slab from above
        # v5: 'roof' may be a fraction: a partial deck over the back of the bay only, the front open over the crane
        fr = 1.0 if P.get('roof') is True or 'roof' not in P else float(P['roof'])
        xr1 = xb + (xf - xb) * fr
        B.box((xr1 - xb + 0.6, 0.16, 2 * zs + 1.6), at=((xr1 + xb) / 2, H - 0.05 + 0.08, 0), mat=rm_, bevel=0.03)
        ribbed_flat(B, xb - 0.3, xr1 + 0.3, -zs - 0.8, zs + 0.8, H + 0.11, pitch=P.get('rib', 0.9), along='x', mat=rm_)
        B.box((0.3, 0.55, 2 * zs + 1.9), at=(xr1 + 0.42, H - 0.02, 0), mat='frame2', bevel=0.03)     # front fascia
    # back wall: dark plates with stiffeners and girts, a doorway with the warm interior beyond
    xw = xb - 0.4
    B.box((0.25, E, 2 * zs - 1.5), at=(xw, E / 2, 0), mat='frame2', bevel=0.03)
    for k in range(17):
        z = -zs + 0.9 + (2 * zs - 1.8) * k / 16
        B.box((0.35, E - 0.4, 0.12), at=(xw + 0.2, E / 2, z), mat='frame', bevel=0.0)
    for gy in (3.8, 7.6, 11.4):
        B.box((0.4, 0.3, 2 * zs - 1.5), at=(xw + 0.22, gy, 0), mat='frame', bevel=0.02)
    B.box((0.3, 3.2, 3.0), at=(xw + 0.05, 1.6, 7.0), mat='interior', bevel=0.0)
    B.R.glowbox((xw + 0.3, 1.6, 7.0), (0.05, 3.0, 2.8), color='#ffb060', radiance=0.5)
    # crane runways (I-beams along X on the corbels) and rails
    ry = P['runway']
    for sz in (-1, 1):
        z = sz * (zs - 0.9)
        ibeam(B, (xb + 0.4, ry, z), (xf - 0.4, ry, z), h=0.9, b=0.45, mat='frame')
        B.box((xf - xb - 0.8, 0.12, 0.12), at=((xf + xb) / 2, ry + 0.51, z), mat='pipe', bevel=0.0)
    # the amber double-girder bridge crane
    cx = P['crane_x']
    zr = zs - 0.9
    gw, gh = P.get('girder', (0.75, 1.5))
    for dx in (-1.05, 1.05):
        B.box((gw, gh, 2 * zr - 1.2), at=(cx + dx * (1 + (gw - 0.75)), ry + 0.7 + gh / 2, 0), mat='amber', bevel=0.05)
        for k in range(12):
            B.box((gw + 0.03, gh - 0.2, 0.05), at=(cx + dx * (1 + (gw - 0.75)), ry + 0.7 + gh / 2, -zr + 0.6 + (2 * zr - 1.2) * (k + 0.5) / 12), mat='amber', bevel=0.0)
    for sz in (-1, 1):
        B.box((3.4, 1.1, 1.3), at=(cx, ry + 1.1, sz * zr), mat='amber', bevel=0.05)
        for dx in (-1.2, 1.2):
            B.cyl(0.32, 0.25, at=(cx + dx, ry + 0.85, sz * zr), rot=(0, 0, 0), mat='frame', n=14)
        B.box((3.6, 0.3, 0.2), at=(cx, ry + 2.3, sz * (zr - 0.7)), mat='frame', bevel=0.0)
    for dx in (-1.05, 1.05):     # crab rails on the girders, buffers at the ends
        B.box((0.14, 0.14, 2 * zr - 1.4), at=(cx + dx, ry + 2.27, 0), mat='pipe', bevel=0.0)
    for sz in (-1, 1):
        for dx in (-1.05, 1.05):
            B.cyl(0.18, 0.4, at=(cx + dx, ry + 2.45, sz * (zr - 1.0)), mat='frame', n=10)
        B.box((3.5, 0.32, 0.6), at=(cx, ry + 0.55, sz * zr), mat='hazard', bevel=0.02)
    B.box((0.9, 0.12, 2 * zr - 1.2), at=(cx + 1.9, ry + 2.2, 0), mat='grate', bevel=0.0)
    K.railing(B, [(cx + 2.3, ry + 2.25, -zr + 0.6), (cx + 2.3, ry + 2.25, zr - 0.6)], post=1.8)
    # trolley with hoist drum and motor, ropes, hook block
    tz = P.get('trolley_z', -1.2)
    B.box((3.0, 1.2, 3.2), at=(cx, ry + 2.85, tz), mat='frame2', bevel=0.05)
    B.cyl(0.55, 2.2, at=(cx, ry + 2.75, tz), rot=(0, 90, 0), mat='pipeDark', n=18)
    B.box((1.0, 0.9, 1.0), at=(cx - 0.9, ry + 3.9, tz + 1.0), mat='frame', bevel=0.04)
    hy = 3.9
    for dz in (-0.35, 0.35):
        B.rod((cx - 0.35, ry + 2.2, tz + dz), (cx - 0.35, hy + 1.2, tz + dz), 0.035, mat='pipe', n=6)
        B.rod((cx + 0.35, ry + 2.2, tz + dz), (cx + 0.35, hy + 1.2, tz + dz), 0.035, mat='pipe', n=6)
    B.box((1.2, 1.3, 1.0), at=(cx, hy + 0.65, tz), mat='amber', bevel=0.05)
    B.tube([(cx, hy, tz), (cx, hy - 0.6, tz), (cx + 0.25, hy - 1.05, tz), (cx + 0.55, hy - 0.8, tz)], 0.11, mat='frame', n=8, fillet=0.25)
    # crane cab under the bridge end
    B.box((1.8, 2.0, 1.8), at=(cx + 1.6, ry + 0.2, zr - 2.4), mat='frame2', bevel=0.05)
    B.box((1.82, 0.9, 1.5), at=(cx + 1.6, ry + 0.4, zr - 2.4), mat='glassW', bevel=0.0)
    B.R.window((cx + 2.52, ry + 0.4, zr - 2.4), (1, 0, 0), 1.4, 0.8, lit=True)
    # the runner: trough on stools, refractory lining, molten metal; the tundish at its back end
    # v5: the runner may run in its own frame (P['runner_at'] = (x, z, rotY)): along +Z out of the bay toward the
    # casthouse, as in the concept, longer and brighter (core glow radiance P['runner_glow'])
    rax, raz, rar = P.get('runner_at', (0.0, 0.0, 0.0))
    rgl = P.get('runner_glow', 1.6)
    with B.at(at=(rax, 0.0, raz), rot=(0, rar, 0)):
        rx0, rx1, rz, rw = P['runner']
        for x in [rx0 + 0.8 + k * 2.4 for k in range(int((rx1 - rx0 - 1.6) / 2.4) + 1)]:
            B.box((0.6, 0.5, rw + 0.6), at=(x, 0.41, rz), mat='frame', bevel=0.03)
        B.box((rx1 - rx0, 0.75, rw), at=((rx0 + rx1) / 2, 1.03, rz), mat='frame2', bevel=0.05)
        B.box((rx1 - rx0 + 0.02, 0.2, rw - 0.6), at=((rx0 + rx1) / 2, 1.33, rz), mat='refractory', bevel=0.02)
        B.box((rx1 - rx0 - 0.1, 0.08, rw - 1.1), at=((rx0 + rx1) / 2, 1.40, rz), mat='hot', bevel=0.0)
        for x in (rx0 + 2.0, rx1 - 2.0):
            for s in (-1, 1):
                B.box((0.25, 0.9, 0.12), at=(x, 1.0, rz + s * (rw / 2 + 0.06)), mat='frame', bevel=0.0)
        B.R.glowbox(B.world(((rx0 + rx1) / 2, 1.45, rz)), (rx1 - rx0 - 1.2, 0.03, 0.32), color='#ffb050', radiance=rgl, roty=math.radians(rar))   # the hot core of the stream only: the crust shows round it
        B.box((3.0, 1.9, 3.2), at=(rx0 - 1.2, 1.12, rz), mat='frame2', bevel=0.06)
        B.box((2.6, 0.12, 2.8), at=(rx0 - 1.2, 2.1, rz), mat='hot', bevel=0.0)
        B.box((3.2, 0.3, 3.4), at=(rx0 - 1.2, 2.2, rz), mat='frame', bevel=0.03)
        B.R.glowbox(B.world((rx0 - 1.2, 2.17, rz)), (1.0, 0.03, 1.0), color='#ffb050', radiance=1.4)
        K.railing(B, [(rx0 + 0.5, 1.4, rz - rw / 2 - 0.4), (rx1 - 0.2, 1.4, rz - rw / 2 - 0.4)], post=1.8)
    # rails and sleepers; the ladle car with its pot
    zr0, x0, x1 = P['rails']
    for k in range(int((x1 - x0) / 0.9)):
        B.box((0.25, 0.12, 2.3), at=(x0 + 0.45 + k * 0.9, 0.22, zr0), mat='frame2', bevel=0.0)
    for s in (-1, 1):
        B.box((x1 - x0, 0.16, 0.12), at=((x0 + x1) / 2, 0.36, zr0 + s * 0.72), mat='pipe', bevel=0.0)
    lx = P['ladle_x']
    B.box((4.4, 0.6, 2.4), at=(lx, 1.1, zr0), mat='frame', bevel=0.04)
    for dx in (-1.5, 1.5):
        for s in (-1, 1):
            B.cyl(0.42, 0.2, at=(lx + dx, 0.85, zr0 + s * 0.72), mat='frame2', n=16)
    pot = [(0, 1.4), (1.25, 1.4), (1.35, 1.6), (1.6, 3.5), (1.75, 3.6), (1.75, 3.85), (1.45, 3.85), (1.45, 3.6), (0, 3.6)]
    B.lathe(pot, (lx, 0, zr0), mat='rust', n=32, bevel=0.03, sharp=30)
    hoop(B, (lx, zr0), 1.45, 2.3, 0.3, 0.1, mat='frame', n=32)
    B.lathe([(0, 3.62), (1.42, 3.62), (1.42, 3.66), (0, 3.66)], (lx, 0, zr0), mat='hot', n=32, bevel=0.0)
    for s in (-1, 1):
        B.cyl(0.25, 0.5, at=(lx, 2.9, zr0 + s * 1.75), mat='frame', n=12)
    if not P.get('runner_at'):     # v5: the pot's hot top is emissive paint; a square glow box read as a sticker
        B.R.glowbox((lx, 3.68, zr0), (1.0, 0.03, 1.0), color='#ffb050', radiance=1.4)
    K.railing(B, [(lx - 2.2, 1.4, zr0 + 1.25), (lx + 2.2, 1.4, zr0 + 1.25)], post=1.4)
    # v5: the concept's small railed control house inside the portal beside the runner: light concrete block on a dark
    # plinth, a lit window toward the runner, a kit crew door with its lamp, a railed roof with a unit
    if P.get('control'):
        cx0, cx1, cz0, cz1, ch = P['control']
        ccx, ccz = (cx0 + cx1) / 2, (cz0 + cz1) / 2
        B.box((cx1 - cx0, 0.5, cz1 - cz0), at=(ccx, 0.25, ccz), mat='frame2', bevel=0.04)
        B.box((cx1 - cx0 - 0.2, ch - 0.5, cz1 - cz0 - 0.2), at=(ccx, 0.5 + (ch - 0.5) / 2, ccz), mat='panel', bevel=0.05)
        for (px, pz) in ((cx0, cz0), (cx1, cz0), (cx1, cz1), (cx0, cz1)):
            B.box((0.3, ch + 0.1, 0.3), at=(px, (ch + 0.1) / 2, pz), mat='frame', bevel=0.02)
        B.box((cx1 - cx0 + 0.3, 0.3, cz1 - cz0 + 0.3), at=(ccx, ch + 0.1, ccz), mat='frame', bevel=0.03)
        # window strip on the +Z face (toward the runner) and on the +X face (toward the apron)
        for (o, n_, w_) in (((ccx, 2.4, cz1 - 0.08), (0, 0, 1), cx1 - cx0 - 1.6), ((cx1 - 0.08, 2.4, ccz - 0.6), (1, 0, 0), 1.6)):
            sz_ = (w_, 1.1, 0.12) if n_[2] else (0.12, 1.1, w_)
            B.box(sz_, at=o, mat='glassW', bevel=0.0)
            B.box((sz_[0] + 0.2, 0.14, sz_[2] + 0.2), at=(o[0], 1.78, o[2]), mat='frame', bevel=0.0)
            B.R.window((o[0] + n_[0] * 0.07, o[1], o[2] + n_[2] * 0.07), n_, w_, 1.0, lit=True)
        B.R.door((cx1 + 0.02, 0.5, cz1 - 1.1), (1, 0, 0))
        K.railing(B, [(cx0 + 0.1, ch + 0.25, cz0 + 0.1), (cx1 - 0.1, ch + 0.25, cz0 + 0.1), (cx1 - 0.1, ch + 0.25, cz1 - 0.1), (cx0 + 0.1, ch + 0.25, cz1 - 0.1)], post=1.4, closed=True)
        B.box((1.6, 0.9, 1.2), at=(ccx - 0.5, ch + 0.7, ccz), mat='frame2', bevel=0.04)
        K.ladder(B, (cx0 - 0.35, 0.0, ccz), (-1, 0, 0), ch + 0.25)
        lamp(B, (cx1 + 0.02, ch - 0.6, cz0 + 0.6), (1, 0, 0), size=0.26)
    # tapping platforms (two levels) with stairs on the -Z side
    def deck(x0_, x1_, z0_, z1_, y):
        B.box((x1_ - x0_, 0.14, z1_ - z0_), at=((x0_ + x1_) / 2, y - 0.07, (z0_ + z1_) / 2), mat='grate', bevel=0.0)
        ibeam(B, (x0_, y - 0.4, z0_), (x1_, y - 0.4, z0_), h=0.5, b=0.2)
        ibeam(B, (x0_, y - 0.4, z1_), (x1_, y - 0.4, z1_), h=0.5, b=0.2)
        for (xx, zz) in ((x0_ + 0.2, z0_ + 0.2), (x1_ - 0.2, z0_ + 0.2), (x0_ + 0.2, z1_ - 0.2), (x1_ - 0.2, z1_ - 0.2)):
            B.box((0.25, y - 0.6, 0.25), at=(xx, (y - 0.6) / 2 + 0.16, zz), mat='frame', bevel=0.02)
    deck(-7.4, -1.4, -11.2, -7.6, 4.2)
    K.railing(B, [(-1.4, 4.2, -11.2), (-1.4, 4.2, -10.0)], post=1.6)
    K.railing(B, [(-1.4, 4.2, -7.6), (-7.4, 4.2, -7.6)], post=1.6)
    K.stair(B, (-1.4 + 0.28 * round(4.04 / 0.18), 0.16, -8.8), (-1, 0, 0), 4.04, w=1.1)
    deck(-7.4, -4.4, -11.2, -9.0, 7.6)
    K.railing(B, [(-4.4, 7.6, -11.2), (-4.4, 7.6, -9.0), (-7.4, 7.6, -9.0)], post=1.6)
    K.ladder(B, (-4.2, 4.2, -10.1), (1, 0, 0), 3.4)
    for (x, z) in ((-1.6, -7.7), (-4.5, -9.1)):
        lamp(B, (x, 5.6 if z > -8 else 9.0, z), (1, 0, 0), size=0.26)
    return works({
        'frame2': {'course': 1.5, 'joint': 1.2, 'rust': 0.15, 'tone': 0.1},
        'concrete2': {'course': 3.0, 'joint': 3.0, 'rust': 0.0, 'dark': 0.3},
        'amber': {'color': [0.80, 0.52, 0.16], 'rust': 0.4, 'edge': 0.9, 'tone': 0.08},
        'rust': {'rust': 0.0},
        'hot': {'crust': 0.45},
    })


# ------------------------------------------------------------------------------------------------------------------
# inclined gallery
# ------------------------------------------------------------------------------------------------------------------
GALLERY = {   # skipGallery, measured (part bbox 6 x 46 x 28): drive house z 9.6..14 at the foot, head house z -14..-9.6
              # y 36..46, gallery from (y 8, z 10) to (y 40, z -11), trestle at z -4.5
    'A': (0.0, 9.5, 9.6), 'B': (0.0, 39.8, -9.6), 'w': 3.6, 'h': 3.0, 'truss': 2.2,
    'foot': (6.0, 12.6, (9.6, 14.0)), 'head': (6.0, (36.0, 46.0), (-14.0, -9.6)), 'trestle': (-4.5, 2.6, 2.2),
}


# v5 (second review): the concept's skip bridge is an OPEN dark box truss climbing steeply from a tall clad tower to the
# furnace top, a big gas main riding on saddles over it and dropping down the tower's far face. Part frame: the head
# (high, -Z) lands on the furnace's frame at 47 m, the foot on the tower top at 28.5 m.
GALLERY_V5 = {
    'A': (0.0, 28.5, 7.6), 'B': (0.0, 47.0, -9.6), 'w': 4.4, 'h': 3.4, 'truss': 0.0, 'open': True,
    'foot': (6.0, 30.0, (7.6, 13.6)), 'head': None, 'trestle': None,
    'pipe': (1.15, [(0.0, 52.6, -9.6), (0.0, 34.1, 7.6), (0.0, 34.1, 15.2), (0.0, 3.0, 15.2)]),
}


def _open_bridge(B, P, L):
    """An open box truss in the gallery frame (x across, y up from the slope, z along): two Warren side trusses the
    full height, top and bottom lateral X bracing, a grating floor with the skip track, a walkway rail."""
    w, h = P['w'], P['h']
    nb = max(2, int(L / 2.8))
    for s in (-1, 1):
        warren(B, (s * (w / 2), 0.15, 0.2), (s * (w / 2), 0.15, L - 0.2), h, up=(0, 1, 0), bay=L / nb, chord=0.34, web=0.18)
    for k in range(nb + 1):
        z = 0.2 + (L - 0.4) * k / nb
        B.box((w + 0.3, 0.3, 0.3), at=(0, 0.15, z), mat='frame', bevel=0.02)
        B.box((w + 0.3, 0.26, 0.26), at=(0, h + 0.15, z), mat='frame', bevel=0.02)
        if k < nb:
            z2 = 0.2 + (L - 0.4) * (k + 1) / nb
            for yy in (0.15, h + 0.15):
                B.bar((-w / 2, yy, z), (w / 2, yy, z2), 0.12, 0.12, mat='frame', bevel=0.0)
                B.bar((w / 2, yy, z), (-w / 2, yy, z2), 0.12, 0.12, mat='frame', bevel=0.0)
    B.box((w - 0.3, 0.12, L - 0.4), at=(0, 0.36, L / 2), mat='grate', bevel=0.0)
    for dx in (-0.8, 0.8):        # the skip track: two rails on sleepers
        B.box((0.16, 0.18, L - 0.4), at=(dx, 0.5, L / 2), mat='pipe', bevel=0.0)
    for k in range(int(L / 1.2)):
        B.box((2.2, 0.1, 0.22), at=(0, 0.42, 0.4 + 1.2 * k), mat='frame2', bevel=0.0)
    # the skip car part way up
    B.box((2.0, 1.4, 2.6), at=(0, 1.3, L * 0.62), mat='frame2', bevel=0.05)
    B.box((2.1, 0.2, 2.7), at=(0, 2.05, L * 0.62), mat='frame', bevel=0.02)
    K.railing(B, [(-w / 2 + 0.35, 0.42, 0.4), (-w / 2 + 0.35, 0.42, L - 0.4)], post=1.8)


def incline_gallery(B, P=GALLERY):
    A, Bp = V(P['A']), V(P['B'])
    w, h, td = P['w'], P['h'], P['truss']
    d = (Bp - A)
    L = d.length
    up = V((0, 1, 0))
    t = d.normalized()
    n_up = (up - t * up.dot(t)).normalized()          # the gallery's own "up" (perpendicular to the slope)
    if P.get('open'):
        with B.at(M=K.frame_along(A, Bp, n_up)):
            _open_bridge(B, P, L)
        # saddles and the gas main over the bridge, dropping down the tower's far face
        pr, path = P['pipe']
        B.tube(path, pr, mat='pipeDark', n=20, fillet=1.6)
        a_, b_ = V(path[0]), V(path[1])
        for k in range(1, 6):
            q = a_ + (b_ - a_) * (k / 6)
            lo = Bp + (A - Bp) * (k / 6) + n_up * (h + 0.3)
            B.bar(lo, q - V((0, pr * 0.8, 0)), 0.35, 0.6, mat='frame', bevel=0.02)
        for (pa_, pb_) in zip(path[:-1], path[1:]):
            a_, b_ = V(pa_), V(pb_)
            L_ = (b_ - a_).length
            with B.at(M=K.frame_along(a_, b_)):
                for t_ in ((0.5,) if L_ < 12 else (0.2, 0.5, 0.8)):
                    B.cyl(pr + 0.14, 0.3, at=(0, 0, L_ * t_), mat='frame', n=20, bevel=0.02)
        fw, fh, (fz0, fz1) = P['foot']
        _house(B, (0.0, 0.0, (fz0 + fz1) / 2), (fw, fh, fz1 - fz0), door=True)
        # a stair tower's worth of landings on the tower's open side: a caged ladder to the top
        K.ladder(B, (fw / 2 + 0.6, 0.0, fz0 + 1.2), (1, 0, 0), fh)
        for yy in (10.0, 20.0):
            lamp(B, (fw / 2 + 0.05, yy, (fz0 + fz1) / 2), (1, 0, 0), size=0.28)
        return works({
            'clad': {'course': 1e3, 'joint': 2.4, 'rust': 0.35, 'tone': 0.06, 'corr': 0.22},
            'panel': {'course': 2.4, 'joint': 1.6, 'rust': 0.45, 'tone': 0.08, 'dark': 0.5},
        })
    with B.at(M=K.frame_along(A, Bp, n_up)):
        # enclosed body: floor, clad walls, a pitched roof; dark portal ribs every 2.4 m (frames along the gallery)
        B.box((w, 0.25, L), at=(0, 0.125, L / 2), mat='frame2', bevel=0.03)
        for s in (-1, 1):
            B.box((0.18, h, L), at=(s * (w / 2 - 0.09), h / 2 + 0.25, L / 2), mat='clad', bevel=0.02)
        B.add(lib.bm_prism([(-w / 2 - 0.15, h + 0.2), (w / 2 + 0.15, h + 0.2), (w / 2 + 0.15, h + 0.38), (0.0, h + 0.75), (-w / 2 - 0.15, h + 0.38)], 0.0, L),
              mat='clad2', bevel=0.02)
        nr = int(L / 2.4)
        for k in range(nr + 1):
            z = 0.15 + (L - 0.3) * k / nr
            for s in (-1, 1):
                B.box((0.14, h + 0.25, 0.2), at=(s * (w / 2 + 0.02), (h + 0.25) / 2 + 0.1, z), mat='frame', bevel=0.02)
            B.box((w + 0.3, 0.14, 0.2), at=(0, h + 0.3, z), mat='frame', bevel=0.0)
        # small windows every second bay on both sides
        for k in range(1, nr, 2):
            z = 0.15 + (L - 0.3) * (k + 0.5) / nr
            for s in (-1, 1):
                B.box((0.06, 0.6, 1.2), at=(s * (w / 2 + 0.01), h * 0.62, z), mat='glassW', bevel=0.0)
                B.box((0.08, 0.8, 1.4), at=(s * (w / 2 - 0.01), h * 0.62, z), mat='frame', bevel=0.0)
        # two Warren trusses under it and cross bracing
        for s in (-1, 1):
            warren(B, (s * (w / 2 - 0.15), -td, 0.3), (s * (w / 2 - 0.15), -td, L - 0.3), td - 0.05, up=(0, 1, 0), bay=2.4, chord=0.28, web=0.14)
        for k in range(int(L / 2.4) + 1):
            z = 0.3 + (L - 0.6) * k / int(L / 2.4)
            B.box((w - 0.3, 0.16, 0.16), at=(0, -td, z), mat='frame', bevel=0.0)
    # drive house at the foot (+Z), head house at the top (-Z): clad boxes with dark posts, louvres, doors
    fw, fh, (fz0, fz1) = P['foot']
    _house(B, (0.0, 0.0, (fz0 + fz1) / 2), (fw, fh, fz1 - fz0), door=True)
    hw, (hy0, hy1), (hz0, hz1) = P['head']
    _house(B, (0.0, hy0, (hz0 + hz1) / 2), (hw, hy1 - hy0, hz1 - hz0), door=False)
    # trestle under the gallery
    tz, tw, tdp = P['trestle']
    lo = A - n_up * td                                # the trusses' bottom chord line
    lam = (lo.z - tz) / max(-t.z, 1e-6)
    yb = lo.y + t.y * lam - 0.45
    _trestle(B, (0.0, 0.0, tz), tw, tdp, yb)
    return works({
        'clad': {'course': 1e3, 'joint': 2.4, 'rust': 0.35, 'tone': 0.06, 'corr': 0.22},
        'clad2': {'course': 1e3, 'joint': 2.4, 'rust': 0.3, 'corr': 0.3},
        'panel': {'course': 2.4, 'joint': 1.6, 'rust': 0.4, 'tone': 0.06},
    })


def _house(B, c, size, door=True):
    x, y0, z = c
    w, hh, d = size
    B.box((w - 0.3, hh, d - 0.3), at=(x, y0 + hh / 2, z), mat='panel', bevel=0.05)
    for sx in (-1, 1):
        for sz in (-1, 1):
            B.box((0.35, hh + 0.2, 0.35), at=(x + sx * (w / 2 - 0.1), y0 + (hh + 0.2) / 2, z + sz * (d / 2 - 0.1)), mat='frame', bevel=0.03)
    B.box((w + 0.1, 0.3, d + 0.1), at=(x, y0 + hh + 0.05, z), mat='frame', bevel=0.03)
    B.box((w - 0.6, 0.1, d - 0.6), at=(x, y0 + hh + 0.18, z), mat='roof', bevel=0.0)
    for yy in [y0 + 4.0 * k for k in range(1, int(hh / 4.0) + 1) if 4.0 * k < hh - 0.5]:
        B.box((w - 0.1, 0.12, d - 0.1), at=(x, yy, z), mat='frame2', bevel=0.0)
    B.box((w - 0.1, 0.9, d - 0.1), at=(x, y0 + 0.45, z), mat='frame2', bevel=0.03)
    louvre_bank(B, (x + w / 2 - 0.14, y0 + hh - 2.2, z + 0.9), (0, 0, -1), 1.8, 1.2)
    louvre_bank(B, (x - w / 2 + 0.14, y0 + hh - 2.2, z - 0.9), (0, 0, 1), 1.8, 1.2)
    lamp(B, (x + w / 2 - 0.12, y0 + hh - 0.6, z - d / 2 + 0.5), (1, 0, 0), size=0.28)
    if door:
        zf = z + d / 2 - 0.12
        # roller door (recessed dark slats in a frame) and the fleet-kit crew door beside it
        with B.at(M=K.face_basis((x - 1.4, y0, zf), (1, 0, 0))):
            B.box((2.6, 3.4, 0.05), at=(1.3, 1.7, -0.12), mat='frame2', bevel=0.0)
            for k in range(14):
                B.box((2.58, 0.04, 0.04), at=(1.3, 0.15 + k * 0.23, -0.08), mat='frame', bevel=0.0)
            for (bw, bh, bx, by) in ((0.2, 3.6, -0.1, 1.8), (0.2, 3.6, 2.7, 1.8), (3.0, 0.25, 1.3, 3.5)):
                B.box((bw, bh, 0.3), at=(bx, by, 0.0), mat='frame', bevel=0.02)
        B.R.door((x + 2.0, y0, zf + 0.12), (0, 0, 1))


def _trestle(B, c, w, d, h):
    x, y0, z = c
    nb = max(1, int(round(h / 3.0)))
    pts = [(x - w / 2, z - d / 2), (x + w / 2, z - d / 2), (x + w / 2, z + d / 2), (x - w / 2, z + d / 2)]
    for (px, pz) in pts:
        B.box((0.9, 0.5, 0.9), at=(px, 0.25, pz), mat='concrete', bevel=0.04)
        ibeam(B, (px, 0.5, pz), (px, h, pz), h=0.35, b=0.3, mat='frame', up=(1, 0, 0))
    for i in range(nb + 1):
        y = 0.5 + (h - 0.5) * i / nb
        for k in range(4):
            a, b = pts[k], pts[(k + 1) % 4]
            B.bar((a[0], y, a[1]), (b[0], y, b[1]), 0.16, 0.16, mat='frame', bevel=0.0)
        if i < nb:
            y2 = 0.5 + (h - 0.5) * (i + 1) / nb
            for k in range(4):
                a, b = pts[k], pts[(k + 1) % 4]
                B.bar((a[0], y, a[1]), (b[0], y2, b[1]), 0.12, 0.12, mat='frame', bevel=0.0)
                B.bar((b[0], y, b[1]), (a[0], y2, a[1]), 0.12, 0.12, mat='frame', bevel=0.0)
    B.box((w + 0.8, 0.4, d + 0.8), at=(x, h + 0.2, z), mat='frame', bevel=0.03)


# ------------------------------------------------------------------------------------------------------------------
# registry: part name -> (builder, params, texture size, about)
# ------------------------------------------------------------------------------------------------------------------
# v5: parts whose light shell gets its own texture set (remodel.py: zones -> a second atlas and material colony_<name>_2)
SPLIT = {'blastFurnace': ({'shell'}, 4096)}

REMODELS = {
    'blastFurnace': (furnace, FURNACE_V5, 4096, '60 m blast furnace remodel: concrete plinth, dark staved hearth, recessed glowing tuyere band with 24 window frames, bustle main and downlegs, light plated shaft with five hoops, flange, cone, throat, uptakes and downcomer; four laced columns, four square grating decks on ring girders, X bracing, caged ladder, lamps'),
    'bandedStack': (banded_stack, STACK, 2048, '46 m banded stack remodel: base block, gusseted flared foot, light / dark plated bands with hoops, two railed platforms, caged ladders, sooted lip, lamps, obstruction light'),
    'shedSegment': (gable_shed, SHED_V5, 4096, '28 x 36 m clad shed segment remodel: corrugated walls between I-section pilasters, recessed window strips, dark dado, gables with outward verges, corrugated roof, gutters, ridge, louvred monitor, downpipes, kit crew door'),
    'pourBay': (pour_bay, POUR_V5, 4096, '19 x 26 m pour bay remodel: built-up columns, lattice side, plate girders and Warren roof trusses, runways and an amber double-girder bridge crane with trolley and hook, plated back wall, glowing runner and tundish, rails and ladle car, two tapping platforms with stairs'),
    'skipGallery': (incline_gallery, GALLERY_V5, 2048, 'inclined skip gallery remodel: clad enclosed gallery with portal ribs and windows on two Warren trusses, lattice trestle, drive house with roller and crew doors, head house'),
}
