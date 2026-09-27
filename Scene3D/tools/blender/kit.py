"""Procedural parts kit for the CQS Orbital Fleet scene (Blender 5 as a Python module).

README
  Generates the shared hard-surface parts (doors, ports, turrets, drive bells, ...) as GLBs in
  assets/parts-blender/ plus assets/parts-blender/parts.json, one GLB per part and size.

    PY=<venv with bpy>/bin/python
    $PY tools/blender/kit.py                 # every part, every size
    $PY tools/blender/kit.py door turret     # only these families (all sizes)
    $PY tools/blender/kit.py turret-M        # one size
    $PY tools/blender/kit.py --list          # families, sizes and parameters
    options: --threads 2 (Cycles bake threads)  --samples 16  --tex-scale 1.0
             --blend DIR (also save each part's .blend there; keep it out of the repo)

  Frame (all parts): metres; origin at the centre of the mounting face; +Z out of the hull
  (surface normal), +Y up, +X width, i.e. the placement frame of src/lib/compose.js. Drive bells
  and the engine housing: origin at the centre of the exit plane, exhaust toward -Z, the body
  (and the mounting back) at +Z. parts.json lists per file: part, size, tris, bbox, texture size,
  generation time, plus part-specific anchors (bells: depth / throat / wall in the ship-module
  engine format; turrets: trunnion and muzzle points; tiling parts: pitch).

  Pipeline per part: build primitives (lib.Part) -> bevel (harden normals) + weighted normals
  per primitive -> join -> smart-UV -> Cycles bake (CPU): weathered base colour (panel tone,
  AO grime, curvature edge wear) and an ORM map -> one glTF material -> GLB -> the repo's
  tools/optimize-glb.mjs (WebP textures, meshopt) -> assets/parts-blender/<file>.glb.
  Modules: lib.py (builders, materials, bake, export), parts_human.py (human-scale reference
  parts), parts_weapons.py, parts_drive.py (bells, housing, radiator), parts_greeble.py.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)

import lib  # noqa: E402
import parts_human  # noqa: E402
import parts_weapons  # noqa: E402
import parts_drive  # noqa: E402
import parts_greeble  # noqa: E402

REGISTRY = {}
for mod in (parts_human, parts_weapons, parts_drive, parts_greeble):
    REGISTRY.update(mod.PARTS)

OUT = os.path.join(ROOT, 'assets', 'parts-blender')
SCRATCH = os.environ.get('KIT_SCRATCH', os.path.join(tempfile.gettempdir(), 'cqs-parts-kit'))  # raw GLBs


def variants(sel):
    out = []
    for fam, spec in REGISTRY.items():
        sizes = spec.get('sizes') or {None: {}}
        for size, params in sizes.items():
            file = fam if size is None else f'{fam}-{size}'
            if not sel or fam in sel or file in sel:
                out.append((fam, size, file, spec, params))
    return out


def build_one(fam, size, file, spec, params, args):
    t0 = time.time()
    lib.reset_scene(args.threads)
    lib.BAKE.clear()
    lib.BAKE.update({'ao': 0.35, 'curv': 0.02, 'panel': (1.6, 1.1, 1.6)})
    lib.BAKE.update(spec.get('bake', {}))
    lib.BAKE.update(params.get('bake', {}))
    P = lib.Part(file)
    kw = {k: v for k, v in params.items() if k not in ('bake', 'tex')}
    meta = spec['build'](P, **kw) or {}
    ob = P.finish()
    t_build = time.time() - t0
    tris = lib.tris_of(ob)
    bb = [ob.matrix_world @ v.co for v in ob.data.vertices]
    mn = [round(min(v[i] for v in bb), 3) for i in range(3)]
    mx = [round(max(v[i] for v in bb), 3) for i in range(3)]
    lib.unwrap(ob)
    tex = int(params.get('tex', spec.get('tex', 512)) * args.tex_scale)
    t_bake = lib.bake(ob, tex, args.samples)
    raw = os.path.join(SCRATCH, 'raw', f'{file}.glb')
    if args.blend:
        import bpy
        os.makedirs(args.blend, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(args.blend, f'{file}.blend'), check_existing=False)
    lib.export(ob, raw)
    out = os.path.join(OUT, f'{file}.glb')
    os.makedirs(OUT, exist_ok=True)
    r = subprocess.run(['node', os.path.join(ROOT, 'tools', 'optimize-glb.mjs'), raw, out, '--tris', '100000000', '--tex', str(tex)],
                       cwd=ROOT, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr or r.stdout)
    secs = time.time() - t0
    entry = {'file': f'{file}.glb', 'part': fam, 'size': size, 'tris': tris,
             'bbox': {'min': mn, 'max': mx, 'size': [round(b - a, 3) for a, b in zip(mn, mx)]},
             'tex': tex, 'kb': round(os.path.getsize(out) / 1024), 'seconds': round(secs, 1),
             'seconds_build': round(t_build, 1), 'seconds_bake': round(t_bake, 1)}
    if spec.get('about'):
        entry['about'] = spec['about']
    entry.update(meta)
    print(f'ok {file:18s} tris {tris:6d}  bbox {entry["bbox"]["size"]}  tex {tex}  {secs:.1f}s (bake {t_bake:.1f}s)', flush=True)
    return entry


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('parts', nargs='*')
    ap.add_argument('--threads', type=int, default=2)
    ap.add_argument('--samples', type=int, default=16)
    ap.add_argument('--tex-scale', type=float, default=1.0)
    ap.add_argument('--blend', default=None)
    ap.add_argument('--list', action='store_true')
    args = ap.parse_args(sys.argv[1:] if '--' not in sys.argv else sys.argv[sys.argv.index('--') + 1:])
    if args.list:
        for fam, size, file, spec, params in variants(args.parts):
            print(file, params)
        return
    man_path = os.path.join(OUT, 'parts.json')
    man = {'generator': 'tools/blender/kit.py (Blender %s, procedural)' % __import__('bpy').app.version_string,
           'frame': 'metres; origin = centre of the mounting face; +Z out of the hull, +Y up, +X width (glTF axes). '
                    'Bells / engineHousing: origin = centre of the exit plane, exhaust toward -Z, body at +Z.',
           'parts': {}}
    if os.path.exists(man_path):
        old = json.load(open(man_path))
        man['parts'] = old.get('parts', {})
    for fam, size, file, spec, params in variants(args.parts):
        man['parts'][file] = build_one(fam, size, file, spec, params, args)
        man['parts'] = dict(sorted(man['parts'].items()))
        with open(man_path, 'w') as f:
            json.dump(man, f, indent=1)


if __name__ == '__main__':
    main()
