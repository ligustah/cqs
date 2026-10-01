"""The shipyard end to end (run from Scene3D/):

    PY=<python with bpy 5.x, scipy, pillow> python3 tools/blender/buildings/shipyard_build.py <workdir>
        [--kit] [--measure] [--tex 2048] [--threads 4]

  0. (--kit)      yard_kit.py            -> assets/parts-yard/*.glb + parts.json   (~40 min on 4 CPUs: gantry 4096 bake)
  1. (--measure)  shipyard_measure.py    -> tools/blender/specs/shipyard-dd12.json (the DD-12's sections and bottom)
  2. shipyard.py <work>                  -> <work>/shipyard-hull.glb (ground, rails, frames, keel, module rig)
  3. shipyard_spec.py                    -> tools/blender/specs/shipyard-v1.json + the GENERATED block of src/buildings/shipyard.js
  4. assemble.py (no contact bake)       -> assets/buildings/shipyard.glb (node 'hull' + parts_*), report <work>/shipyard.json
  5. tools/lite-glb.mjs                  -> assets/buildings/shipyard.lite.glb (textures <= 1024, phone tier)
"""
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCENE3D = os.path.abspath(os.path.join(HERE, '..', '..', '..'))


def run(cmd, env=None, log=None):
    print('>', ' '.join(os.path.basename(c) if i < 2 else c for i, c in enumerate(cmd[:4])), '...', flush=True)
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=SCENE3D, env={**os.environ, **(env or {})})
    txt = p.stdout + p.stderr
    if log:
        open(log, 'w').write(txt)
    for line in txt.split('\n'):
        if line.startswith(('[yard]', '[measure]', '[spec]', 'ok ', 'Traceback')) or 'Error' in line:
            print(line, flush=True)
    if p.returncode:
        print(txt[-3000:])
        sys.exit(p.returncode)
    return txt


def main():
    argv = sys.argv[1:]
    work = os.path.abspath(argv[0])
    py = os.environ['PY']
    tex = argv[argv.index('--tex') + 1] if '--tex' in argv else '2048'
    threads = argv[argv.index('--threads') + 1] if '--threads' in argv else '4'
    os.makedirs(work, exist_ok=True)
    env = {'YARD_SCRATCH': os.path.join(work, 'scratch')}
    if '--kit' in argv:
        run([py, os.path.join(HERE, 'yard_kit.py'), '--threads', threads], env)
    if '--measure' in argv or not os.path.exists(os.path.join(HERE, '..', 'specs', 'shipyard-dd12.json')):
        run([py, os.path.join(HERE, 'shipyard_measure.py')], env)
    run([py, os.path.join(HERE, 'shipyard.py'), work, '--tex', tex, '--threads', threads], env)
    run(['python3', os.path.join(HERE, 'shipyard_spec.py')], {'SHIPYARD_HULL_JSON': os.path.join(work, 'shipyard-hull.json')})
    out_dir = os.path.join(SCENE3D, 'assets', 'buildings')
    os.makedirs(out_dir, exist_ok=True)
    glb = os.path.join(work, 'shipyard.glb')
    run([py, os.path.join(HERE, '..', 'assemble.py'), os.path.join(HERE, '..', 'specs', 'shipyard-v1.json'), glb,
         '--hull', os.path.join(work, 'shipyard-hull.glb'), '--no-bake', '--tex', '4096', '--threads', threads], env, log=os.path.join(work, 'assemble.log'))
    r = json.load(open(glb.replace('.glb', '.json')))
    print('[build] tris', r['tris']['total'], {k: v for k, v in r['tris'].items() if k != 'total'})
    print('[build] bytes', r['bytes'], 'dropped', r['dropped'], 'bbox', r['bbox_assembled'])
    shutil.copy(glb, os.path.join(out_dir, 'shipyard.glb'))
    run(['node', 'tools/lite-glb.mjs', os.path.join(out_dir, 'shipyard.glb'), os.path.join(out_dir, 'shipyard.lite.glb'), '--tex', '1024'])
    print('[build] wrote', os.path.join(out_dir, 'shipyard.glb'), 'and shipyard.lite.glb')


if __name__ == '__main__':
    main()
