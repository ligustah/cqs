#!/bin/bash
# round.sh <building> <tag> [parts...]: one review round (BUILDING-GUIDE stage E): remodel the given parts at
# ${TEX:-2048}, build the building at ${BTEX:-2048} x ${SAMP:-6} samples, shoot (shots.sh), measure (check.sh) and make
# the blind sheet (concept | previous | current) and the close sheet. PREV=<tag> names the previous round (default: none).
# Logs and images in $REVIEW_DIR/<building>/. Heavy: run one at a time, in the background.
. "$(dirname "$0")/env.sh"; B=$1; T=$2; shift 2; O=$REVIEW_DIR/$B; mkdir -p $O
cd $SCENE3D
set -e
if [ $# -gt 0 ]; then
  echo "[round] remodel $@ $(date +%T)"
  $BPY tools/blender/buildings/remodel.py "$@" --tex ${TEX:-2048} --work $O/w > $O/$T-remodel.log 2>&1
fi
echo "[round] build $(date +%T)"
$BPY tools/blender/buildings/colony_build.py $B $O/b --tex ${BTEX:-2048} --samples ${SAMP:-6} > $O/$T-build.log 2>&1
echo "[round] shots $(date +%T)"
$HERE/shots.sh $B $T > $O/$T-shots.log 2>&1
$HERE/check.sh $B $O/$T-main.png $O/$T-grit-crops.png > $O/$T-check.txt 2>&1 || true
C=$IMAGES/$B-concept.jpg
P=${PREV:+$O/$PREV-main.png}
python3 $HERE/sheet.py $O/$T-blind.jpg "$T" "concept=$C${P:+|$PREV=$P}|$T=$O/$T-main.png" --cw 800 --ch 500 > /dev/null
VIEWS=$(python3 -c "import json; print('|'.join(f'{k}=$O/$T-{k}.png' for k in json.load(open('$HERE/cams/$B.json'))['views']))")
python3 $HERE/sheet.py $O/$T-closesheet.jpg "$T close" "$VIEWS" --cw 800 --ch 500 > /dev/null
echo "[round] done $(date +%T)"
cat $O/$T-check.txt
