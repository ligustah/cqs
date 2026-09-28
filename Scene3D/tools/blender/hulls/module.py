"""Write a ship-module draft (src/ships/<ship>.js format) for a remodelled, assembled hull.

    <blender-python> tools/blender/hulls/module.py <ship> <assembled.glb> <spec.json> <out.js>

<ship> names a module in this folder (e.g. corvette) that exports MODULE = { meta, header,
asset: {...fixed fields...}, lights: [{placement id or index, colour, blink}], surfaces: {name:
{centre, normal, u, width, height, note}} }. From the assembly this script derives:
  - engines: every bell placement (part 'bell-*'): p = exit-plane centre, radius / depth / throat /
    wall = the kit's documented engine entry (assets/parts-blender/parts.json) times the
    placement scale;
  - lights: nav-light housings (part 'navlight'): the lens point = mount + n * lens.z (kit
    manifest), plus the colour / blink the ship module gives each;
  - anchors.surfaces: each named face re-measured on the assembled GLB's 'hull' node by ray
    casts on a 0.5 m grid along -normal (plane refit; flat = share of samples within 0.15 m of
    the plane), like the committed modules;
  - the runtime centring: glbship.js centres the GLB on its bbox, so every coordinate is shifted
    by minus the assembled bbox centre (a few cm at most when the hull is built symmetric).
"""
import importlib
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402

import assemble_frame as F  # noqa: E402
import assemble_place as PL  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))


def rnd(v, k=3):
    return [round(float(x), k) + 0.0 for x in v]


def load(glb):
    tmp = os.path.join(os.path.dirname(os.path.abspath(glb)), '.module-tmp')
    F.reset()
    src = F.decode([(glb, 'asm')], tmp)['asm']
    meshes, _new = F.import_glb(src)
    hull = [o for o in meshes if o.name.startswith('hull') or (o.parent and o.parent.name == 'hull')]
    lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
    for o in meshes:
        a, b = F.vert_box(o)
        lo = Vector(map(min, lo, a)); hi = Vector(map(max, hi, b))
    vs, ps = [], []
    for o in hull:
        me = o.data; mw = o.matrix_world
        b = len(vs)
        vs += [F.s_vec(mw @ v.co) for v in me.vertices]
        ps += [tuple(b + i for i in p.vertices) for p in me.polygons]
    return BVHTree.FromPolygons(vs, ps, all_triangles=False), lo, hi


def measure_surface(bvh, s):
    c, n, u = Vector(s['centre']), Vector(s['normal']).normalized(), Vector(s['u']).normalized()
    v = n.cross(u).normalized()
    pts = []
    W, H = s['width'], s['height']
    for a in np.arange(-W / 2 + 0.25, W / 2, 0.5):
        for b in np.arange(-H / 2 + 0.25, H / 2, 0.5):
            o = c + u * a + v * b + n * 3
            p, nn, _i, d = bvh.ray_cast(o, -n, 8)
            if p is not None:
                pts.append(p)
    if len(pts) < 6:
        return None
    P = np.array(pts)
    m = P.mean(0)
    _, _, vt = np.linalg.svd(P - m)
    nn = Vector(vt[2]).normalized()
    if nn.dot(n) < 0:
        nn = -nn
    dist = np.abs((P - m) @ np.array(nn))
    flat = float((dist < 0.15).mean())
    # centre on the fitted plane below the requested centre
    t = (Vector(m) - c).dot(nn)
    cc = c + nn * t
    uu = (u - nn * u.dot(nn)).normalized()
    return {'centre': rnd(cc, 2), 'normal': rnd(nn, 3), 'u': rnd(uu, 3), 'width': s['width'], 'height': s['height'], 'flat': round(flat, 2)}


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ship, glb, spec_path, out = argv[:4]
    mod = importlib.import_module(ship).MODULE
    spec = json.load(open(spec_path))
    base = os.path.dirname(os.path.abspath(spec_path))
    kit = json.load(open(os.path.join(os.path.normpath(os.path.join(base, spec['partsDir'])), 'parts.json')))['parts']
    bvh, lo, hi = load(glb)
    ctr = (lo + hi) / 2
    size = hi - lo
    shift = -ctr
    P = lambda v: rnd(Vector(v) + shift, 3)
    places = PL.expand(spec['placements'])
    engines, lights = [], []
    for q in places:
        name = q['part']
        if name.startswith('bell-'):
            e = kit[name]['engine']
            s = q.get('scale', 1) or 1
            engines.append({'p': P(q['p']), 'radius': round(e['radius'] * s, 3), 'depth': round(e['depth'] * s, 3), 'throat': round(e['throat'] * s, 3),
                            'wall': [[round(a * s, 3), round(b * s, 3)] for a, b in e['wall']], 'id': q.get('id', name)})
        if name == 'navlight':
            lens = kit['navlight'].get('lens', [0, 0, 0.23])[2]
            p = Vector(q['p']) + q['n'] * (lens - q.get('sink', 0.0))
            lights.append(P(p))
    ldefs = mod['lights']
    out_lights = []
    for i, p in enumerate(lights):
        d = ldefs[i] if i < len(ldefs) else {'color': 'white'}
        L = {'p': p, 'color': d['color'], 'size': d.get('size', 0.4)}
        if d.get('blink'):
            L['blink'] = d['blink']
        out_lights.append((L, d.get('note', '')))
    surfaces = {}
    for name, s in mod['surfaces'].items():
        r = measure_surface(bvh, s)
        if r is None:
            print('[module] surface missed:', name, flush=True)
            continue
        r['centre'] = P(r['centre'])
        r['centre'] = [round(x, 2) for x in r['centre']]
        surfaces[name] = (r, s.get('note', ''))
    # --- write
    js = []
    js += mod['header'].rstrip().split('\n')
    js.append(f"// Assembled envelope {size.x:.2f} x {size.y:.2f} x {size.z:.2f} m (bbox centre {rnd(ctr, 3)} in the model frame; every")
    js.append("// coordinate below is shifted by minus that centre, as glbship.js centres the GLB).")
    js.append(f"export const meta = {json.dumps(mod['meta'], indent=2)};")
    js.append('')
    js.append('export const asset = {')
    for k, v in mod['asset'].items():
        js.append(f'  {k}: {json.dumps(v)},')
    js.append(f'  length: {round(size.z, 3)},')
    js.append('  engines: [')
    for e in engines:
        idd = e.pop('id')
        js.append(f'    // {idd}')
        js.append('    ' + json.dumps(e, separators=(', ', ': ')).replace('"', '') + ',')
    js.append('  ],')
    js.append('  lights: [')
    for L, note in out_lights:
        if note:
            js.append(f'    // {note}')
        js.append('    ' + json.dumps(L, separators=(', ', ': ')).replace('"p"', 'p').replace('"color"', 'color').replace('"size"', 'size').replace('"blink"', 'blink').replace('"period"', 'period').replace('"duty"', 'duty').replace('"phase"', 'phase') + ',')
    js.append('  ],')
    js.append('  anchors: {')
    js.append('    // Flat hull faces for the composition step, measured on the remodelled hull by ray casts (0.5 m')
    js.append('    // grid along -normal, plane refit; flat = share of samples within 0.15 m of the plane).')
    js.append('    surfaces: {')
    for name, (r, note) in surfaces.items():
        js.append(f"      '{name}': {{ centre: {r['centre']}, normal: {r['normal']}, u: {r['u']}, width: {r['width']}, height: {r['height']}, flat: {r['flat']} }},{(' // ' + note) if note else ''}")
    js.append('    },')
    js.append('  },')
    js.append('};')
    open(out, 'w').write('\n'.join(js) + '\n')
    print('[module] wrote', out, 'envelope', rnd(size, 3), 'centre', rnd(ctr, 3), flush=True)


if __name__ == '__main__':
    main()
