#!/usr/bin/env bash
# Drover-class CT-4 / CT-7 end to end (the corvette's build.sh chain, plus the extras step and a
# texture atlas of 6144 for ~30 px/m on the main hull):
#   tools/blender/hulls/freighter_build.sh <cargo|troops> <workdir> [--skip-model] [--skip-paint] [--skip-asm]
# needs PY=<python with bpy (Blender 5 as a module), scipy, pillow>; run from Scene3D/.
#   1. model + bake: freighter.py --stage model --bake -> <name>-hull.blend, maps.npz
#   2. paint:        freighter.py --stage paint        -> base/orm/normal.png, <name>-hull.glb
#   3. spec + assemble (kit parts, contact AO; not optimised yet) -> <name>-asm.blend
#   4. extras: containers + port lites, export, optimise   -> <name>-v3.glb
# The module (both variants in one src/ships/freighter.js) is freighter_module.py.
set -euo pipefail
VAR="$1"; WORK="$(realpath -m "$2")"; shift 2
: "${PY:?set PY to a python with bpy}"
HERE="$(cd "$(dirname "$0")" && pwd)"
NAME=$([ "$VAR" = troops ] && echo freighter-troops || echo freighter)
mkdir -p "$WORK"
ARGS=" $* "
if [[ "$ARGS" != *" --skip-model "* ]]; then
  "$PY" "$HERE/freighter.py" "$WORK" --variant "$VAR" --stage model --bake 2>&1 | grep -E '^\[hull\] (uv|joined|cull|bake|saved|raster)|Error|Traceback|Killed' || true
fi
if [[ "$ARGS" != *" --skip-paint "* ]]; then
  "$PY" "$HERE/freighter.py" "$WORK" --variant "$VAR" --stage paint 2>&1 | grep -E '^\[hull\]|Error|Traceback' || true
fi
python3 "$HERE/freighter_spec.py" "$VAR" > /dev/null
if [[ "$ARGS" != *" --skip-asm "* ]]; then
  "$PY" "$HERE/../assemble.py" "$HERE/../specs/$NAME-v3.json" "$WORK/$NAME-asm.glb" --hull "$WORK/$NAME-hull.glb" --tex 6144 --threads 4 \
    --no-optimize --blend "$WORK/$NAME-asm.blend" > "$WORK/assemble.log" 2>&1
  python3 - "$WORK/$NAME-asm.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
print('[build] kit tris', r['tris']['total'], {k: v for k, v in r['tris'].items() if k != 'total'})
print('[build] placed', r['placed'], 'dropped', r['dropped'], 'seat', len(r['seat']))
PY
fi
"$PY" "$HERE/freighter_extras.py" "$WORK/$NAME-asm.blend" "$WORK/$NAME-v3.glb" --variant "$VAR" --work "$(dirname "$WORK")/extras" 2>&1 | grep -E '^\[extras\]|Error|Traceback|tris,'
