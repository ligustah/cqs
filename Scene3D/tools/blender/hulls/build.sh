#!/usr/bin/env bash
# One remodelled ship, end to end:
#   tools/blender/hulls/build.sh <ship> <workdir> [--skip-model] [--skip-paint]
# needs PY=<python with bpy (Blender 5 as a module), scipy, pillow>; run from Scene3D/.
#   1. model + bake:  hulls/<ship>.py <work> --stage model --bake  -> corvette-hull.blend, maps.npz
#   2. paint:          hulls/<ship>.py <work> --stage paint         -> base/orm/normal.png, <ship>-hull.glb
#   3. spec + assemble: hulls/<ship>_spec.py -> specs/<ship>-v3.json;       assemble.py specs/<ship>-v3.json <work>/<ship>-v3.glb --hull <work>/<ship>-hull.glb
#   4. module draft:   hulls/module.py <ship> <work>/<ship>-v3.glb specs/<ship>-v3.json <work>/<ship>.js
set -euo pipefail
SHIP="$1"; WORK="$(realpath -m "$2")"; shift 2
: "${PY:?set PY to a python with bpy}"
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$WORK"
ARGS=" $* "
if [[ "$ARGS" != *" --skip-model "* ]]; then
  "$PY" "$HERE/$SHIP.py" "$WORK" --stage model --bake 2>&1 | grep -E '^\[hull\]|Error|Traceback' || true
fi
if [[ "$ARGS" != *" --skip-paint "* ]]; then
  "$PY" "$HERE/$SHIP.py" "$WORK" --stage paint 2>&1 | grep -E '^\[hull\]|Error|Traceback' || true
fi
[ -f "$HERE/${SHIP}_spec.py" ] && python3 "$HERE/${SHIP}_spec.py" > /dev/null   # regenerate the placement spec
"$PY" "$HERE/../assemble.py" "$HERE/../specs/$SHIP-v3.json" "$WORK/$SHIP-v3.glb" --hull "$WORK/$SHIP-hull.glb" --tex 4096 --threads 4 > "$WORK/assemble.log" 2>&1
python3 - "$WORK/$SHIP-v3.json" <<'EOF'
import json, sys
r = json.load(open(sys.argv[1]))
print('[build] tris', r['tris']['total'], {k: v for k, v in r['tris'].items() if k != 'total'})
print('[build] bytes', r['bytes'], 'dropped', r['dropped'], 'bbox', r['bbox_assembled'])
EOF
"$PY" "$HERE/module.py" "$SHIP" "$WORK/$SHIP-v3.glb" "$HERE/../specs/$SHIP-v3.json" "$WORK/$SHIP.js" 2>&1 | grep -E '^\[module\]|Error|Traceback'
