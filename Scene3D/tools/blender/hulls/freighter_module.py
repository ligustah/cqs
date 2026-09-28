"""Write src/ships/freighter.js for the remodelled Drover-class ships: the cargo ship CT-4 as the
module's `asset` and the troop ship CT-7 as `variants.troops` (own GLB), both measured on their
assembled GLBs as module.py does (engines from the bell placements times the kit's engine entry,
lights at the nav-light lenses, anchor surfaces re-measured by ray casts, every coordinate
shifted by minus the assembled bbox centre).

    <blender-python> tools/blender/hulls/freighter_module.py <cargo-v3.glb> <troops-v3.glb> <out.js>
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import bpy  # noqa: E402,F401
from mathutils import Vector  # noqa: E402

import module as M  # noqa: E402
import assemble_place as PL  # noqa: E402
import freighter_dims as D  # noqa: E402

SPECS = os.path.join(HERE, '..', 'specs')
KIT = os.path.join(HERE, '..', '..', '..', 'assets', 'parts-blender', 'parts.json')

LIGHTS = [
    {'color': 'red', 'note': 'steady sidelights on the top of each radiator, outboard forward corner (the beam extremity): red port, green starboard'},
    {'color': 'green'},
    {'color': 'white', 'blink': {'period': 1.3, 'duty': 0.1}, 'note': 'anti-collision strobes, alternating: mast housing and keel block'},
    {'color': 'white', 'blink': {'period': 1.3, 'duty': 0.1, 'phase': 0.5}},
    {'color': 'white', 'note': 'steady stern light on the aft face of the dorsal block, between the bells'},
]


def surfaces(v):
    cm0 = v['CM0']
    fx = D.CM['fx']
    X, YB, YT = v['RX'], v['RYB'], v['RYT']
    zr = (v['R0'] + v['R1']) / 2
    R = v['RAD']
    s = {
        'cm-flank-port': {'centre': [fx, -4.4, cm0 + 11.0], 'normal': [1, 0, 0], 'u': [0, 0, 1], 'width': 18.0, 'height': 8.0, 'note': 'crew-module flank, decks 2-4 (port rows every 1.6 m, teal stripe at y 0)'},
        'cm-flank-stbd': {'centre': [-fx, -4.4, cm0 + 11.0], 'normal': [-1, 0, 0], 'u': [0, 0, -1], 'width': 18.0, 'height': 8.0},
        'cm-ledge-port': {'centre': [fx - 0.45, D.CM['ledge'], cm0 + 11.0], 'normal': [0, 1, 0], 'u': [0, 0, 1], 'width': 18.0, 'height': 0.8, 'note': 'upper-tier walkway ledge (rails)'},
        'cm-ledge-stbd': {'centre': [-(fx - 0.45), D.CM['ledge'], cm0 + 11.0], 'normal': [0, 1, 0], 'u': [0, 0, 1], 'width': 18.0, 'height': 0.8},
        'cm-roof': {'centre': [0, D.CM['top'] + 0.7, cm0 + 12.0], 'normal': [0, 1, 0], 'u': [0, 0, 1], 'width': 7.0, 'height': 10.0, 'note': 'raised roof deck (hatches)'},
        'reactor-flank-port': {'centre': [X, 2.0, zr], 'normal': [1, 0, 0], 'u': [0, 0, 1], 'width': 9.0, 'height': 6.0, 'note': f"reactor block flank ({v['number']} stencil)"},
        'reactor-flank-stbd': {'centre': [-X, 2.0, zr], 'normal': [-1, 0, 0], 'u': [0, 0, -1], 'width': 9.0, 'height': 6.0},
        'reactor-roof': {'centre': [0, YT, zr + 1.6], 'normal': [0, 1, 0], 'u': [0, 0, 1], 'width': 8.0, 'height': 4.0},
        'radiator-top-port': {'centre': [(R['x0'] + v['HX']) / 2, R['y1'], (R['z0'] + R['z1']) / 2 + 7.0], 'normal': [0, 1, 0], 'u': [0, 0, 1], 'width': 10.0, 'height': 4.0, 'note': 'radiator panel top edge'},
        'radiator-top-stbd': {'centre': [-(R['x0'] + v['HX']) / 2, R['y1'], (R['z0'] + R['z1']) / 2 + 7.0], 'normal': [0, 1, 0], 'u': [0, 0, 1], 'width': 10.0, 'height': 4.0},
    }
    return s


def measure(v, glb):
    spec = json.load(open(os.path.join(SPECS, f"{v['name']}-v3.json")))
    kit = json.load(open(KIT))['parts']
    bvh, lo, hi = M.load(glb)
    ctr = (lo + hi) / 2
    size = hi - lo
    P = lambda p: M.rnd(Vector(p) - ctr, 3)
    engines, lights = [], []
    for q in PL.expand(spec['placements']):
        if q['part'].startswith('bell-'):
            if q.get('mirrored'):
                continue
            e = kit[q['part']]['engine']
            s = q.get('scale', 1) or 1
            engines.append({'p': P(q['p']), 'radius': round(e['radius'] * s, 3), 'mirrorX': True, 'depth': round(e['depth'] * s, 3), 'throat': round(e['throat'] * s, 3),
                            'wall': [[round(a * s, 3), round(b * s, 3)] for a, b in e['wall']], 'id': q.get('id')})
        if q['part'] == 'navlight':
            lens = kit['navlight'].get('lens', [0, 0, 0.23])[2]
            lights.append(P(Vector(q['p']) + q['n'] * (lens - q.get('sink', 0.0))))
    surf = {}
    for name, s in surfaces(v).items():
        r = M.measure_surface(bvh, s)
        if r is None:
            print('[fmodule] surface missed:', name, flush=True)
            continue
        r['centre'] = [round(x, 2) for x in P(r['centre'])]
        surf[name] = (r, s.get('note', ''))
    return {'size': size, 'ctr': ctr, 'engines': engines, 'lights': lights, 'surfaces': surf}


def js_asset(v, m, indent, fixed):
    I = ' ' * indent
    out = []
    for k, val in fixed.items():
        val, _, note = val.partition(' // ')
        out.append(f'{I}{k}: {val},' + (f' // {note}' if note else ''))
    out.append(f"{I}length: {round(m['size'].z, 3)}, // {m['size'].z:.2f} x {m['size'].x:.2f} x {m['size'].y:.2f} m assembled (L x B x H), 4 slots")
    out.append(f'{I}engines: [')
    for e in m['engines']:
        e = dict(e)
        out.append(f"{I}  // {e.pop('id')}")
        out.append(f'{I}  ' + json.dumps(e, separators=(', ', ': ')).replace('"', '') + ',')
    out.append(f'{I}],')
    out.append(f'{I}lights: [')
    for p, d in zip(m['lights'], LIGHTS):
        if d.get('note'):
            out.append(f"{I}  // {d['note']}")
        b = f", blink: {{ ...STROBE{', phase: ' + str(d['blink']['phase']) if 'phase' in d['blink'] else ''} }}" if d.get('blink') else ''
        out.append(f"{I}  {{ p: {p}, color: '{d['color']}', size: 0.4{b} }},")
    out.append(f'{I}],')
    out.append(f'{I}anchors: {{')
    out.append(f'{I}  // flat hull faces, measured on the remodelled hull by ray casts (0.5 m grid along -normal, plane refit;')
    out.append(f'{I}  // flat = share of samples within 0.15 m of the plane)')
    out.append(f'{I}  surfaces: {{')
    for name, (r, note) in m['surfaces'].items():
        out.append(f"{I}    '{name}': {{ centre: {r['centre']}, normal: {r['normal']}, u: {r['u']}, width: {r['width']}, height: {r['height']}, flat: {r['flat']} }},{(' // ' + note) if note else ''}")
    out.append(f'{I}  }},')
    out.append(f'{I}}},')
    return out


HEADER = """// Civil ship CT-4 / CT-7 (Drover class) — v3 REMODEL: clean hard-surface hulls (tools/blender/hulls/freighter.py,
// one parametric script, --variant cargo|troops: common crew module, collar, reactor block and engine section,
// variant mid-body) rebuilt from measurements of the fal / Tripo H3.1 multiview blueprints, painted in texture
// space (paint.py with freighter_paint.py: light civil paint, irregular plating seams, PATINA plate tone, AO grime,
// edge wear, dark hull-number stencils, teal stripe, hazard frames) and assembled with the Blender parts kit
// (tools/blender/specs/freighter-v3.json, freighter-troops-v3.json via tools/blender/assemble.py), then
// tools/blender/hulls/freighter_extras.py: the container stacks (kit 20-ft ISO container baked onto 12-triangle
// boxes, six weathered cargo colours as material tints, so they survive the civil livery) and ~1 m port lites on
// the 3 m decks (the troop habitats' 750 berths).
// The GLBs are in the ship frame (metres, bow +Z, dorsal +Y, port +X): rotate [0, 0, 0], length = the assembled
// bbox length. Node 'hull' is the hull, 'parts_*' the kit parts, containers and port lites (hullNodes).
// Scale: the game's civil ship is 4 hangar slots (UnitEnum getSize() = 4), so EACH variant's envelope is
// 4 x 70,000 = 280,000 m^3; the pair is the carrier bay's binding load (12 of each), so both envelopes are kept
// to the blueprints' (cargo 134.1 x 54.7 x 38.2 m, troops 128.8 x 57.7 x 37.7 m): radiator fin tips set the beam,
// the mast whip and the landing-leg pads the height, the bow face and the bell lips the length.
// Engines: kit bell-L scaled to the blueprint exit radius, with the kit's engine entry (depth to the throat plate,
// throat, inner wall) times that scale. Lights: at the lenses of the kit nav-light housings.
// Troop capacity from game data: UnitEnum TRANSPORTER groundTransport = 750, counted in the game's ground-unit
// size units (UnitMap.getGroundUnitSize: infantry 1, vehicles 3, aircraft 4), not people."""


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    cg, tg, out = argv[:3]
    vc, vt = D.V('cargo'), D.V('troops')
    mc, mt = measure(vc, cg), measure(vt, tg)
    livery = "{ ...LIVERIES.civil, gain: 0.05, glassGlow: [0.06, 0.055, 0.046], glassLit: 0.45 }"
    js = HEADER.split('\n')
    js.append(f"// Assembled envelopes: cargo {mc['size'].z:.2f} x {mc['size'].x:.2f} x {mc['size'].y:.2f} m (bbox centre {M.rnd(mc['ctr'], 3)}), troops "
              f"{mt['size'].z:.2f} x {mt['size'].x:.2f} x {mt['size'].y:.2f} m (centre {M.rnd(mt['ctr'], 3)}); coordinates below are shifted by minus the centre.")
    js.append("import { LIVERIES } from '../lib/livery.js';")
    js.append('')
    meta = {'name': 'Drover-class civil transport', 'designation': 'CT-4 / CT-7', 'crew': 'about 80 (troop variant: ground-unit capacity 750; infantry 1, vehicles 3, aircraft 4)',
            'blurb': "Civil workhorse: a forward crew module and an aft reactor block with two fusion bells, tanks and radiator panels, joined by a truss keel that carries twenty-foot containers (CT-4) or four pressurised habitat cylinders (CT-7 troop transport: ground-unit capacity 750, the game's groundTransport)."}
    js.append(f'export const meta = {json.dumps(meta, indent=2)};')
    js.append('')
    js.append('const STROBE = { period: 1.3, duty: 0.1 };')
    js.append('')
    js.append('export const asset = {')
    fixed = {
        'glb': "'./assets/ships/freighter.glb'", 'generator': "'tools/blender/hulls/freighter.py --variant cargo (remodel of the tripo3d/h3.1/multiview-to-3d hull) + tools/blender/assemble.py + freighter_extras.py'",
        'concept': "'./assets/concepts/freighter.webp'", 'beauty': "'./assets/concepts/freighter-beauty.webp'",
        'rotate': '[0, 0, 0]', 'hullNodes': "['hull']",
        'livery': livery + ' // civil grey; the remodel paint is lighter than the generated textures (gain 0.05); lit cabins behind the ports',
        'detail': "{ set: 'hull', tile: 6, normalStrength: 0.6, roughAmount: 0.5, cavity: 0.2 } // the hull carries its own seams: runtime PATINA turned down",
    }
    js += js_asset(vc, mc, 2, fixed)
    js.append('};')
    js.append('')
    js.append('export const variants = {')
    js.append('  cargo: {},')
    js.append('  troops: {')
    fixed_t = {
        'gameId': "'TRANSPORTER' // UnitEnum TRANSPORTER (the cargo ship is FREIGHTER)",
        'glb': "'./assets/ships/freighter-troops.glb'", 'generator': "'tools/blender/hulls/freighter.py --variant troops + tools/blender/assemble.py + freighter_extras.py'",
        'concept': "'./assets/concepts/freighter-troops.webp'", 'beauty': "'./assets/concepts/freighter-troops-beauty.webp'",
        'rotate': '[0, 0, 0]',
    }
    js += js_asset(vt, mt, 4, fixed_t)
    js.append('  },')
    js.append('};')
    open(out, 'w').write('\n'.join(js) + '\n')
    print('[fmodule] wrote', out, 'cargo', M.rnd(mc['size'], 3), 'troops', M.rnd(mt['size'], 3), flush=True)


if __name__ == '__main__':
    main()
