#!/bin/bash
# evidence.sh <building> <final tag> <previous tag> <version>: the evidence sheets into style-library/.../images/buildings:
# <building>-<version>.jpg (concept | previous | final at the concept camera) and <building>-<version>-close.jpg (concept
# crop | previous | final per close-up view)
. "$(dirname "$0")/env.sh"; B=$1; T=$2; V=$3; VER=$4; O=$REVIEW_DIR/$B
C=$IMAGES/$B-concept.jpg
ROWS=$(python3 - "$HERE/cams/$B.json" "$C" "$O" "$T" "$V" <<'PY'
import json, sys
from PIL import Image
cams, C, O, T, V = sys.argv[1:6]
c = Image.open(C); rows = []
for k, box in json.load(open(cams))['concept_crops'].items():
    c.crop(tuple(box)).save(f'{O}/cc-{k}.png')
    rows.append(f'{k}: concept={O}/cc-{k}.png|{k}: previous={O}/{V}-{k}.png|{k}: {T}={O}/{T}-{k}.png')
print('\n'.join(rows))
PY
)
python3 $HERE/sheet.py $IMAGES/$B-$VER.jpg "$B $VER at the concept camera (1600 x 1000): concept | previous | $VER" "concept=$C|previous=$O/$V-main.png|$VER=$O/$T-main.png" --cw 1100 --ch 733
mapfile -t R <<< "$ROWS"
python3 $HERE/sheet.py $IMAGES/$B-$VER-close.jpg "$B close-ups (az 52, el 22, fov 38, <= 34 m): concept crop | previous | $VER" "${R[@]}" --cw 1100 --ch 688
