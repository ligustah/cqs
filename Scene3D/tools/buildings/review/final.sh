#!/bin/bash
# final.sh <building> <tag> <parts...>: the final (stage F): the parts at their registry size (4096 heroes), the
# building at 4096 x 10 samples, the shots and the measures (then evidence.sh, thumbs, the release checks)
. "$(dirname "$0")/env.sh"; B=$1; T=$2; shift 2; O=$REVIEW_DIR/$B; mkdir -p $O
cd $SCENE3D
set -e
echo "[final] remodel $(date +%T)"
[ $# -gt 0 ] && $BPY tools/blender/buildings/remodel.py "$@" --work $O/w > $O/$T-remodel.log 2>&1
echo "[final] build $(date +%T)"
$BPY tools/blender/buildings/colony_build.py $B $O/b --tex 4096 --samples 10 > $O/$T-build.log 2>&1
echo "[final] shots $(date +%T)"
$HERE/shots.sh $B $T > $O/$T-shots.log 2>&1
$HERE/check.sh $B $O/$T-main.png $O/$T-grit-crops.png > $O/$T-check.txt 2>&1 || true
echo "[final] done $(date +%T)"
cat $O/$T-check.txt
