"""Write the carrier's ship module (src/ships/carrier.js) from the assembled, remodelled GLB.

    <blender-python> tools/blender/hulls/carrier_module.py <draft.js> <assembled.glb> <out.js>

module.py's draft covers engines (bell placements x the kit's engine entry), the nav lights and
the measured surfaces; the carrier also needs everything that hangs on its hangar and its
900 m scale. All of it is RE-MEASURED here by ray casts on the assembled hull (node 'hull'),
then shifted by minus the assembled bbox centre (as glbship.js centres the GLB):
  - running lights: white DECK_EDGE (75 m) and amber EDGE_RUN (25 m) on the top of the deck-edge
    chamfer, amber FLANK lights on the frame posts' capital band and the end blocks (y -50),
    SPONSON_RUN on the sponsons' outer faces;
  - lit ports (1 m warm points) on real glass: found by rays along the port rows (glass lies
    0.3 m behind the facade), every third port on the upper and lower rows of the stern block and
    the bow section and on the keel wedge, and every 6 m on the island's pane bands;
  - hangar: GALLERY ports on the bay-facing faces of the frame posts, BOW_WALL ports, the MOUTH_RIM
    approach lights on the lip, ceiling heights of every bay (light strips), the frame-ring
    ceilings (floodlights), the deck heights of every zone (checked against carrier_dims), the
    clear z runs of the flank openings (rays from the centre line out through the bays);
  - anchors: hangar / hangarMouth / hangarDeck (zones, lane, openings), liveryKeep, detail,
    interiorLights, interiorLightGate, interiorBounce.
"""
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import bpy  # noqa: E402,F401
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402

import module as MOD  # noqa: E402
import assemble_place as PL  # noqa: E402
import carrier as CV  # noqa: E402
import carrier_dims as D  # noqa: E402

V = Vector
S2 = math.sqrt(0.5)


def cast(bvh, o, d, far=400.0):
    p, n, _i, dist = bvh.ray_cast(V(o), V(d).normalized(), far)
    return (p, n, dist) if p is not None else (None, None, None)


def f2(v, k=2):
    return [round(float(x), k) + 0.0 for x in v]


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    draft, glb, out = argv[:3]
    spec_path = os.path.join(HERE, '..', 'specs', 'carrier-v3.json')
    bvh, lo, hi = MOD.load(glb)
    ctr = (lo + hi) / 2
    size = hi - lo
    sh = lambda v, k=2: f2(V(v) - ctr, k)
    log = lambda *a: print('[cmodule]', *a, flush=True)
    log('bbox', f2(lo), f2(hi), 'size', f2(size), 'centre', f2(ctr, 3))

    def proud(p, n, d=0.08):
        return V(p) + V(n).normalized() * d

    # ---- engines and nav lights (module.py's rules)
    spec = json.load(open(spec_path))
    kit = json.load(open(os.path.join(os.path.dirname(spec_path), spec['partsDir'], 'parts.json')))['parts']
    places = PL.expand(spec['placements'])
    engines, navs = [], []
    for q in places:
        if q['part'].startswith('bell-'):
            e = kit[q['part']]['engine']; s = q.get('scale', 1)
            engines.append({'p': sh(q['p'], 3), 'radius': round(e['radius'] * s, 3), 'depth': round(e['depth'] * s, 3), 'throat': round(e['throat'] * s, 3),
                            'wall': [[round(a * s, 3), round(b * s, 3)] for a, b in e['wall']]})
        if q['part'] == 'navlight':
            lens = kit['navlight'].get('lens', [0, 0, 0.23])[2]
            navs.append(sh(V(q['p']) + q['n'] * (lens - q.get('sink', 0.0)), 2))

    # ---- deck-edge chamfer lights: rays down the chamfer's normal onto its upper part
    def deck_edge(z, side):
        n = V((side * S2, S2, 0))
        o = V((side * 140.0, 40.0, z)) - n * 0.0
        # aim at the chamfer 3 m below its top edge
        top = V((side * (99.0 if (z < D.Z_SF or z > D.Z_BA or any(a <= z <= b for a, b in D.FRAMES)) else 100.0), 24.0 if (z < D.Z_SF or z > D.Z_BA or any(a <= z <= b for a, b in D.FRAMES)) else 21.0, z))
        tgt = top + V((side * S2, -S2, 0)) * 3.0
        p, nn, _ = cast(bvh, tgt + n * 30.0, -n, 60)
        return None if p is None else sh(proud(p, nn, 0.08))
    DECK_EDGE = [q for z in np.arange(-255.0, 420.0, 75.0) for q in (deck_edge(z, 1), deck_edge(z, -1)) if q]
    EDGE_RUN = [q for z in np.arange(-355.0, 415.0, 25.0) if abs(((z + 255.0) / 75.0) - round((z + 255.0) / 75.0)) > 0.01
                for q in (deck_edge(z, 1), deck_edge(z, -1)) if q]
    # ---- flank lights at y -50: end blocks and the frame posts' capital band
    fz = [-300.0, -268.0] + [(a + b) / 2 for a, b in D.FRAMES] + [290.0, 350.0, 410.0]
    FLANK = []
    for z in fz:
        for s in (1, -1):
            p, nn, _ = cast(bvh, (s * 260.0, -50.0, z), (-s, 0, 0), 200)
            if p is not None and abs(p.x) > 125:
                FLANK.append(sh(proud(p, nn)))
    S = D.SPONSON
    SPONSON_RUN = []
    for z in (S['zc'] - 20.0, S['zc'] + 20.0):
        for s in (1, -1):
            p, nn, _ = cast(bvh, (s * 260.0, -46.0, z), (-s, 0, 0), 100)
            if p is not None:
                SPONSON_RUN.append(sh(proud(p, nn)))

    # ---- lit ports: scan along port rows for glass (hit 0.25..0.4 m behind the facade plane)
    def scan(a, b, n, plane_d, every=3, step=0.1):
        a, b, n = V(a), V(b), V(n).normalized()
        L = (b - a).length; d = (b - a).normalized()
        runs, cur = [], None
        for t in np.arange(0.0, L, step):
            p0 = a + d * t
            p, nn, dist = cast(bvh, p0 + n * 5.0, -n, 10.0)
            glass = p is not None and 0.2 < (dist - 5.0) < 0.45
            if glass and cur is None:
                cur = t
            if not glass and cur is not None:
                runs.append((cur, t)); cur = None
        cen = [(t0 + t1) / 2 for t0, t1 in runs if 0.6 < t1 - t0 < 1.4]
        return [sh(a + d * t + n * 0.3) for t in cen[::every]]
    OUTER = []
    for s in (1, -1):
        for y in (-14.0, -29.0, -76.0, -91.0):
            OUTER += scan((s * D.X_END, y, D.Z_SF - 2.0), (s * D.X_END, y, D.Z_STERN + 4.0), (s, 0, 0), D.X_END)
            OUTER += scan((s * D.X_END, y, D.Z_BA + 2.0), (s * D.X_END, y, D.Z_BF - 6.0), (s, 0, 0), D.X_END)
        top, ht = D.KEEL['top'], D.KEEL['half_top']
        for y in D.KEEL_ROWS:
            x = ht - (top - y)
            OUTER += scan((s * x, y, D.KEEL['z0'] + 20.0), (s * x, y, D.KEEL['z1'] - 20.0), (s * S2, -S2, 0), None, every=4)
    log('lit hull ports', len(OUTER))
    ISLAND = []
    for nm, zc, w, l, c, y0, y1 in list(D.TIERS[:5]):
        bands = [y for y in np.arange(y0 + 1.5, y1 - 1.9, D.DECK_PITCH)]
        for y in bands[::2]:
            for a, b, d, n in CV.edges(CV.outline(zc, w, l, c)):
                L = (b - a).length
                for t in np.arange(3.0, L - 2.0, 6.0):
                    p2 = a + d * t
                    o = V((p2.x, y, p2.y)); nn3 = V((n.x, 0, n.z))
                    p, hn, dist = cast(bvh, o + nn3 * 5.0, -nn3, 10.0)
                    if p is not None and 0.25 < dist - 5.0 < 0.5:
                        ISLAND.append(sh(p + nn3 * 0.35))
    log('lit island panes', len(ISLAND))

    # ---- hangar: frame faces, gallery ports, bow wall, mouth rim
    faces = [(D.Z_SF, 1)] + [(z, s) for a, b in D.FRAMES for z, s in ((a, -1), (b, 1))] + [(D.Z_BA, -1)]
    FRAME_FACES = []
    for z, s in faces:
        p, nn, _ = cast(bvh, (113.0, -48.0, z + s * 20.0), (0, 0, -s), 40)
        FRAME_FACES.append([round(p.z - ctr.z, 2), s])
    BOW_WALL_X = []
    for s in (1, -1):
        p, nn, _ = cast(bvh, (0.0, -45.0, 300.0), (s, 0, 0), 200)
        BOW_WALL_X.append(round(p.x - ctr.x - s * 0.08, 2))
    p, _, _ = cast(bvh, (0.0, -3.0, D.Z_LIP + 10.0), (0, 0, -1), 30)
    p2, _, _ = cast(bvh, (0.0, -94.5, D.Z_LIP + 10.0), (0, 0, -1), 30)
    mouth_rim = [round(p.z - ctr.z + 0.08, 2), round(p2.z - ctr.z + 0.08, 2)]
    # ceilings and decks
    bays = D.BAYS
    ceil = []
    for z0, z1 in bays:
        zc = (z0 + z1) / 2                   # mid-bay: between the girders (at 0.08, 1/3, 2/3, 0.92)
        p, _, _ = cast(bvh, (30.0, -50.0, zc), (0, 1, 0), 100)
        ceil.append([round(z0 + 0.5, 1), round(z1 - 0.5, 1), round(p.y - ctr.y, 2)])
    p, _, _ = cast(bvh, (30.0, -50.0, 350.0), (0, 1, 0), 100)
    ceil.append([round(D.Z_BA + 0.8, 1), round(D.Z_BF - 3.0, 1), round(p.y - ctr.y, 2)])
    ring_ceil = []
    for a, b in D.FRAMES:
        p, _, _ = cast(bvh, (0.0, -50.0, (a + b) / 2), (0, 1, 0), 100)
        ring_ceil.append(round(p.y - ctr.y, 2))
    decks = {}
    for name, (x, z) in {'aft': (60, -225), 'long': (60, 0), 'bay5': (60, -130), 'bay4': (60, -40), 'bay3': (60, 53), 'bay2': (60, 145), 'bay1': (60, 240), 'bow': (50, 380)}.items():
        p, _, _ = cast(bvh, (x, -50.0, z), (0, -1, 0), 100)
        decks[name] = round(p.y - ctr.y, 2)
    log('ceilings', ceil, 'ring ceilings', ring_ceil, 'decks (measured, meshopt-quantised)', decks)
    # the zone decks keep the design heights (carrier_dims, = the v5 module's): the measured planes agree to the
    # GLB's position quantisation (~0.015 m steps over the 900 m hull)
    design = {'aft': D.Y_AFT, 'long': D.Y_LONG, 'bay5': D.Y_LONG, 'bay4': D.Y_LONG, 'bay3': D.Y_LONG, 'bay2': D.Y_LONG, 'bay1': D.Y_BAY1, 'bow': D.Y_BOW}
    for k, y in design.items():
        assert abs(decks[k] - y) < 0.06, (k, decks[k], y)
    decks = design
    # flank openings: clear runs of rays from the centre line out through the bays (y -48)
    runs, cur = [], None
    for z in np.arange(D.Z_SF - 5.0, D.Z_BA + 5.0, 0.25):
        p, _, _ = cast(bvh, (0.0, -48.0, z), (1, 0, 0), 300)
        open_ = p is None or p.x > 140
        if open_ and cur is None:
            cur = z
        if not open_ and cur is not None:
            runs.append([round(cur - ctr.z + 0.25, 1), round(z - ctr.z - 0.25, 1)]); cur = None
    log('flank openings', runs)
    xs = []
    for s in (1, -1):
        p, _, _ = cast(bvh, (s * 140.0, -48.0, D.Z_SF - 20.0), (-s, 0, 0), 60)   # stern block flank
        xs.append(round(p.x - ctr.x, 1))

    # ---- write
    L = lambda v: '[' + ', '.join(f'{x:g}' for x in v) + ']'
    js = []
    header = CV.MODULE['header'].rstrip().split('\n')
    js += header
    js += [
        f"// Assembled envelope {size.x:.2f} x {size.y:.2f} x {size.z:.2f} m (bbox centre {f2(ctr, 3)}; every coordinate below is",
        "// shifted by minus that centre, as glbship.js centres the GLB). Everything below is measured on the assembled",
        "// remodel by tools/blender/hulls/carrier_module.py (ray casts), as the other remodels' modules are.",
        "// - Hangar: one through-deck bay from the back wall (z -276) to the bow mouth (lip z 421.4). Along the flanks it is",
        "//   open between the stern block, five 24 m frame rings and the bow section (six bays per side, flank plating at",
        "//   x = +-121, frame posts and end blocks at +-131). Decks (the lower slab's top, heights kept from the v5",
        "//   module): aft bay -92.45, bays 5-2 -96.35 (continuous under frames F2-F4), bay 1 -93.61, bow section -90.97;",
        "//   sills of F1 / F5 -91.9. Ceilings: bays -0.6 (with transverse girders to -3.2 and crane gantries to -4.7),",
        "//   frame rings -5.7, bow section -6.4. Walls of the rings, the back recess and the bow section at x = +-95 with",
        "//   45-degree chamfers. anchors.hangar (155.8 x 84.4 x 670 m) stands on the bow-section deck inside every chamfer,",
        "//   ring and ceiling, as before.",
        "// - Drive: six kit bell-XL (x2.614 upper / lower, r 18.3; x2.7 outboard, r 18.9) at the blueprint's circle fits,",
        "//   exit planes on z -450, in collars on the stern plate; depth / throat / wall = the kit's engine entry x scale.",
        "// - Lights sit 8 cm proud of the surface. Running lights: white on the deck-edge chamfer every 75 m, amber every",
        "//   25 m between them, amber at mid-height (y -50) on the frame posts' capital band and the end blocks, and on the",
        "//   sponsons' outer faces. Lit ports: 1 m warm points on real glass (ray-cast), every third port of the outer",
        "//   rows of the stern block and bow section, every fourth on the keel wedge, every 6 m on the island's pane bands.",
        "// - Hangar floodlights and strips as before (see the v5 notes): six spots under the frame rings and in the bow",
        "//   section, light-linked to the hangar by interiorLightGate, plus interiorBounce; emissive strips across every",
        "//   bay ceiling and down every bay-facing frame face.",
    ]
    js.append(f"export const meta = {json.dumps(CV.MODULE['meta'], indent=2)};")
    js.append('')
    js += [
        "const STROBE = { period: 1.3, duty: 0.1 };",
        "const RUN = 0.4; // running-light size (m): the same 0.4 m as every nav light on every hull",
        "const PORT = '#4a3a26'; // lit interior behind a 1 m port (x4 in the light shader: well under the bloom threshold)",
        "",
        "// dorsal deck edge: white every 75 m, amber every 25 m between them (top of the deck-edge chamfer)",
        f"const DECK_EDGE = {json.dumps(DECK_EDGE)};",
        f"const EDGE_RUN = {json.dumps(EDGE_RUN)};",
        "// flanks at mid-height (y -50): stern block, the five frame posts' capital band, bow section; sponson outer faces",
        f"const FLANK = {json.dumps(FLANK)};",
        f"const SPONSON_RUN = {json.dumps(SPONSON_RUN)};",
        "// lit ports on real glass: stern block and bow section outer rows, keel wedge; island pane bands",
        f"const HULL_PORTS = {json.dumps(OUTER)};",
        f"const ISLAND_PORTS = {json.dumps(ISLAND)};",
        "",
        "// hangar: 1 m gallery ports on every bay-facing face (frame posts, stern block, bow section): two rows (y -32 / -64)",
        "// of four per side; ports every 12.5 m along the bow section's inner walls; amber approach lights on the mouth lip",
        f"const FRAME_FACES = {json.dumps(FRAME_FACES)};",
        "const GALLERY = FRAME_FACES.flatMap(([z, s]) => [105, 111, 117, 123, -105, -111, -117, -123].flatMap((x) => [-32, -64].map((y) => ({ p: [x, y, z + s * 0.08], color: PORT, size: 1 }))));",
        f"const BOW_WALL = Array.from({{ length: 11 }}, (_, i) => 285 + i * 12.5).flatMap((z) => [{{ p: [{BOW_WALL_X[0]}, -48, z], color: PORT, size: 1 }}, {{ p: [{BOW_WALL_X[1]}, -48, z], color: PORT, size: 1 }}]);",
        f"const MOUTH_RIM = [-80, -40, 0, 40, 80].flatMap((x) => [{{ p: [x, -3, {mouth_rim[0]}], color: 'amber', size: 0.4 }}, {{ p: [x, -94.5, {mouth_rim[1]}], color: 'amber', size: 0.4 }}]);",
        "const OUTER = [",
        "  ...HULL_PORTS.map((p) => ({ p, color: PORT, size: 1 })), ...ISLAND_PORTS.map((p) => ({ p, color: PORT, size: 1 })),",
        "  ...EDGE_RUN.map((p) => ({ p, color: 'amber', size: RUN })), ...SPONSON_RUN.map((p) => ({ p, color: 'amber', size: RUN })),",
        "];",
        "",
        "// Hangar light strips (emissive fixtures, see glbship.js): three 150 m strips across each bay ceiling (ray-cast",
        "// ceilings, between the girders) and the bow section, and a 64 m vertical strip on every bay-facing frame face (x +-108.5,",
        "// between the gallery ports, 0.25 m off the face). Radiance ~1.8 (ceiling) / 0.9 (posts).",
        "const STRIP = { color: '#fff1e0', radiance: 1.8 };",
        "const POST_STRIP = { color: '#ffe9d2', radiance: 0.9 };",
        f"const BAY_CEILINGS = {json.dumps(ceil)};",
        "const STRIPS = [",
        "  ...BAY_CEILINGS.flatMap(([z0, z1, y]) => [1 / 6, 1 / 2, 5 / 6].map((f) => ({ ...STRIP, p: [0, y - 0.35, z0 + (z1 - z0) * f], size: [150, 0.3, 1.0] }))),",
        "  ...FRAME_FACES.flatMap(([z, s]) => [108.5, -108.5].map((x) => ({ ...POST_STRIP, p: [x, -47.5, z + s * 0.25], size: [0.45, 64, 0.1] }))),",
        "];",
        "",
        "// hangar floodlights: under the five frame rings (ray-cast ring ceilings) and in the bow section",
        "const FLOOD = { kind: 'spot', color: '#fff3e8', intensity: 52000, distance: 240, angle: 64, penumbra: 0.55, fixture: 1.5 };",
        f"const RING_CEIL = {json.dumps([[round((a + b) / 2 - ctr.z, 2), y] for (a, b), y in zip(D.FRAMES, ring_ceil)])};",
        "",
    ]
    ew = lambda e: '{ ' + f"p: {L(e['p'])}, radius: {e['radius']}, depth: {e['depth']}, throat: {e['throat']}, wall: {json.dumps(e['wall'])}" + ' }'
    names = ['red', 'green', 'white', 'white', 'white']
    nl = []
    for i, p in enumerate(navs):
        d = CV.MODULE['lights'][i]
        blink = ''
        if d.get('blink'):
            blink = ', blink: { ...STROBE' + (', phase: 0.5' if d['blink'].get('phase') else '') + ' }'
        nl.append(f"    {{ p: {L(p)}, color: '{d['color']}', size: 0.4{blink} }},")
    zones = {
        'aft': ([-93.5, 93.5], [-255.5, -189.0], decks['aft']),
        'long': ([-95.75, 95.75], [-164.3, 178.1], decks['long']),
        'bay5': ([-95.75, 95.75], [-164.3, -98.2], decks['bay5']),
        'bay4': ([-95.75, 95.75], [-73.4, -5.4], decks['bay4']),
        'bay3': ([-95.75, 95.75], [19.5, 87.1], decks['bay3']),
        'bay2': ([-95.75, 95.75], [111.8, 178.1], decks['bay2']),
        'bay1': ([-82.35, 82.35], [202.4, 275.8], decks['bay1']),
        'bow': ([-78.65, 78.65], [276.8, 415.0], decks['bow']),
    }
    js += [
        "export const asset = {",
        f"  glb: './assets/ships/carrier.glb', generator: '{CV.MODULE['asset']['generator']}',",
        "  concept: './assets/concepts/carrier.webp', beauty: './assets/concepts/carrier-beauty.webp',",
        "  rotate: [0, 0, 0], hullNodes: ['hull'],",
        f"  length: {round(size.z, 3)}, // {size.x:.1f} x {size.y:.1f} x {size.z:.1f} m design (no slot normalisation)",
        "  // remodel paint is lighter than the generated textures: gain 0.05 matches the fleet grey; kit and hull glass get a",
        "  // dim warm interior light (livery.js glassGlow, opt-in)",
        "  livery: { gain: 0.05, glassGlow: [0.06, 0.055, 0.046], glassLit: 0.35 },",
        "  // the operational repaint stops at the hangar: inside the cavity box the texture keeps its own plating (x 0.14, 8 %",
        "  // saturation), so the deck and walls read as lit grey steel instead of the near-black hull paint",
        "  liveryKeep: { box: [[-100.5, -97.5, -277], [100.5, -0.3, 414]], gain: 0.14, saturation: 0.08, feather: 1.5 },",
        "  // runtime PATINA micro detail, turned down (the hull carries its own plating seams); the hangar takes the 'deck' set",
        "  detail: {",
        "    set: 'hull', tile: 6, normalStrength: 0.6, roughAmount: 0.5, cavity: 0.2,",
        "    interior: { set: 'deck', tile: 6, normalStrength: 0.8, roughAmount: 0.6, cavity: 0.25, albedo: 0.9, seam: 0.5, grime: 1.6, feather: 1.5 },",
        "  },",
        "  engines: [",
        *[f"    {ew(e)}," for e in engines],
        "  ],",
        "  lights: [",
        f"    // {CV.MODULE['lights'][0]['note']}",
        *nl[:2],
        f"    // {CV.MODULE['lights'][2]['note']}",
        *nl[2:4],
        f"    // {CV.MODULE['lights'][4]['note']}",
        *nl[4:],
        "    ...DECK_EDGE.map((p) => ({ p, color: 'white', size: RUN })),",
        "    ...FLANK.map((p) => ({ p, color: 'amber', size: RUN })),",
        "    ...MOUTH_RIM, ...GALLERY, ...BOW_WALL, ...OUTER,",
        "  ],",
        "  fixtures: STRIPS,",
        "  interiorLights: RING_CEIL.map(([z, y]) => ({ ...FLOOD, p: [0, y - 1.3, z], target: [0, -96, z] }))",
        f"    .concat([{{ ...FLOOD, p: [0, {round(ceil[-1][2] - 1.2, 2)}, 350], target: [0, -91, 350] }}]),",
        "  // only the hangar's own surfaces receive the floodlights: back wall to just past the mouth lip, from 1.1 m below the",
        "  // lowest deck up, out to the flank plating (so the open bays' floors and frame sides still catch the light)",
        "  interiorLightGate: { box: [[-133, -97.5, -277], [133, 0, 425]], feather: 1 },",
        "  interiorBounce: { box: [[-100.5, -97.5, -277], [100.5, 4, 416]], color: '#e9e4dc', irradiance: 1.2, feather: 3 },",
        "  anchors: {",
        "    hangar: { p: [0, -48.7, 80], size: [155.8, 84.4, 670] },",
        "    hangarMouth: { p: [0, -48.7, 418], dir: [0, 0, 1] },",
        "    hangarDeck: {",
        "      lane: [-25, 25], // 50 m launch lane on the centreline, clear to the mouth (a fleet-scale fighter is 48 m wide)",
        "      zones: {",
        *[f"        {k}: {{ x: {L(x)}, z: {L(z)}, y: {y} }}," for k, (x, z, y) in zones.items()],
        "      },",
        "      // where the hangar can be seen from outside (lib/park.js draws parked ships only then): the six flank bays at the",
        "      // flank plating (clear z runs of a ray from the centre line, y range of the opening) and the bow mouth",
        "      openings: {",
        f"        flank: {{ x: [-121, 121], y: [{decks['long']}, {ceil[1][2]}], z: {json.dumps(runs)} }},",
        f"        mouth: {{ z: 418, x: [-95, 95], y: [{decks['bow']}, {ceil[-1][2]}] }},",
        "        inside: { min: [-95, -97, -276], max: [95, 0, 418] },",
        "      },",
        "    },",
        "  },",
        "};",
    ]
    open(out, 'w').write('\n'.join(js) + '\n')
    log('wrote', out, 'engines', len(engines), 'navs', len(navs), 'deck edge', len(DECK_EDGE), 'edge run', len(EDGE_RUN), 'flank', len(FLANK), 'stern x', xs)


if __name__ == '__main__':
    main()
