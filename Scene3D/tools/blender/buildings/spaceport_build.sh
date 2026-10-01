#!/usr/bin/env bash
# SP-3 spaceport, end to end (run from Scene3D/):
#   PY=<python with bpy 5.x> tools/blender/buildings/spaceport_build.sh <workdir> [--install]
#   1. station geometry:  buildings/spaceport.py <work>            -> <work>/spaceport-hull.glb (+ .json)
#   2. kit placements:    buildings/spaceport_spec.py              -> specs/spaceport-v1.json
#   3. assemble:          assemble.py (no contact bake: no hull UVs) -> <work>/spaceport.glb (+ .json report)
#   4. lite tier:         tools/lite-glb.mjs                       -> <work>/spaceport.lite.glb
#   --install copies both to assets/buildings/ (temp file + rename)
set -euo pipefail
WORK="$(realpath -m "$1")"; shift
: "${PY:?set PY to a python with bpy}"
HERE="$(cd "$(dirname "$0")" && pwd)"
SCENE="$(cd "$HERE/../../.." && pwd)"
mkdir -p "$WORK"
"$PY" "$HERE/spaceport.py" "$WORK" 2>&1 | grep -E '^\{|Error|Traceback' || true
python3 "$HERE/spaceport_spec.py"
"$PY" "$HERE/../assemble.py" "$HERE/../specs/spaceport-v1.json" "$WORK/spaceport.glb" --hull "$WORK/spaceport-hull.glb" --no-bake --threads 4 > "$WORK/assemble.log" 2>&1
python3 - "$WORK/spaceport.json" <<'PYEOF'
import json, sys
r = json.load(open(sys.argv[1]))
print('[build] tris', r['tris']['total'], {k: v for k, v in r['tris'].items() if k != 'total'})
print('[build] bytes', r['bytes'], 'length', r['length'], 'dropped', r['dropped'])
PYEOF
(cd "$SCENE" && node tools/lite-glb.mjs "$WORK/spaceport.glb" "$WORK/spaceport.lite.glb" --tex 512)
if [[ " $* " == *" --install "* ]]; then
  mkdir -p "$SCENE/assets/buildings"
  for f in spaceport.glb spaceport.lite.glb; do cp "$WORK/$f" "$SCENE/assets/buildings/.$f.tmp" && mv "$SCENE/assets/buildings/.$f.tmp" "$SCENE/assets/buildings/$f"; done
  echo "[build] installed assets/buildings/spaceport.glb (+ lite)"
fi
