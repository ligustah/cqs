"""The carrier end to end (build.sh's chain with the carrier's texture sizes and module finish):

    PY=<python with bpy 5.x, scipy, pillow> python3 tools/blender/hulls/carrier_build.py <workdir>
        [--skip-model] [--skip-paint] [--paint-tex 8192]

  1. model + bake (4096 maps):  carrier.py <work> --stage model --bake
  2. paint at 8192:             carrier.py <work> --stage paint --paint-tex 8192
  3. spec + assemble:           carrier_spec.py; assemble.py specs/carrier-v3.json --tex 8192
                                (the hull's base colour stays 8192; ORM / normal are 4096)
  4. module:                    module.py -> draft; carrier_module.py -> <work>/carrier.js
  then: node tools/blender/hulls/carrier_squeeze.mjs <work>/carrier-v3.glb <work>/carrier.glb --base-q 82
        (the GLB budget pass, 12.7 -> 10.4 MB) before installing <work>/carrier.glb and <work>/carrier.js.
Run from Scene3D/.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def run(cmd, log=None, filt=('[hull]', '[paint]', '[module]', '[cmodule]', 'Error', 'Traceback')):
    print('>', ' '.join(cmd[:4]), '...', flush=True)
    p = subprocess.run(cmd, capture_output=True, text=True)
    txt = p.stdout + p.stderr
    if log:
        open(log, 'w').write(txt)
    for L in txt.split('\n'):
        if any(L.startswith(f) or f in L for f in filt):
            print(L, flush=True)
    if p.returncode:
        print(txt[-3000:])
        sys.exit(p.returncode)


def main():
    argv = sys.argv[1:]
    work = os.path.abspath(argv[0])
    py = os.environ['PY']
    ptex = argv[argv.index('--paint-tex') + 1] if '--paint-tex' in argv else '8192'
    os.makedirs(work, exist_ok=True)
    if '--skip-model' not in argv:
        run([py, os.path.join(HERE, 'carrier.py'), work, '--stage', 'model', '--bake'])
    if '--skip-paint' not in argv:
        run([py, os.path.join(HERE, 'carrier.py'), work, '--stage', 'paint', '--paint-tex', ptex])
    run(['python3', os.path.join(HERE, 'carrier_spec.py')])
    spec = os.path.join(HERE, '..', 'specs', 'carrier-v3.json')
    glb = os.path.join(work, 'carrier-v3.glb')
    run([py, os.path.join(HERE, '..', 'assemble.py'), spec, glb, '--hull', os.path.join(work, 'carrier-hull.glb'), '--tex', ptex, '--threads', '4'],
        log=os.path.join(work, 'assemble.log'))
    r = json.load(open(os.path.join(work, 'carrier-v3.json')))
    print('[build] tris', r['tris']['total'], {k: v for k, v in r['tris'].items() if k != 'total'})
    print('[build] bytes', r['bytes'], 'dropped', r['dropped'], 'bbox', r['bbox_assembled'])
    draft = os.path.join(work, 'carrier-draft.js')
    run([py, os.path.join(HERE, 'module.py'), 'carrier', glb, spec, draft])
    run([py, os.path.join(HERE, 'carrier_module.py'), draft, glb, os.path.join(work, 'carrier.js')])


if __name__ == '__main__':
    main()
