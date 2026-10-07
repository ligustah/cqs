#!/bin/bash
# shoot-rev.sh <building> <git-rev> <tag>: shoot an earlier version (its GLB, lite GLB and the module's DATA from
# <git-rev>) with the CURRENT studio hint and cameras, then restore the working tree. For the evidence's "previous"
# column (e.g. the v5 commit) without keeping copies in scratch.
. "$(dirname "$0")/env.sh"; B=$1; REV=$2; T=$3; O=$REVIEW_DIR/$B; mkdir -p $O/cur
A=$SCENE3D/assets/buildings; J=$SCENE3D/src/buildings/$B.js
cp $A/$B.glb $A/$B.lite.glb $J $O/cur/
trap 'cp $O/cur/$B.glb $O/cur/$B.lite.glb $A/; cp $O/cur/$B.js $J' EXIT
cd $REPO
git show $REV:Scene3D/assets/buildings/$B.glb > $A/$B.glb
git show $REV:Scene3D/assets/buildings/$B.lite.glb > $A/$B.lite.glb
git show $REV:Scene3D/src/buildings/$B.js > $O/rev.js
python3 - $J $O/rev.js <<'PY'
import re, sys
cur = open(sys.argv[1]).read(); old = open(sys.argv[2]).read()
d_old = re.search(r'const DATA = .*?;\n', old, re.S).group(0)
open(sys.argv[1], 'w').write(re.sub(r'const DATA = .*?;\n', lambda m: d_old, cur, count=1, flags=re.S))
PY
$HERE/shots.sh $B $T
