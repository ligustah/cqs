#!/bin/bash
# check.sh <building> <render> [crops.png]: paint-check (light / mid / all bands vs the concept) and grit-check (bare
# surface std / high-pass and the shadow side vs the concept; regions tools/buildings/grit-regions/<building>.json)
. "$(dirname "$0")/env.sh"; B=$1; RIMG=$(cd "$(dirname "$2")" && pwd)/$(basename "$2"); CROPS=${3:+$(cd "$(dirname "$3")" && pwd)/$(basename "$3")}
cd $SCENE3D
C=$IMAGES/$B-concept.jpg; G=tools/buildings/grit-regions/$B.json
python3 tools/buildings/paint-check.py $C $RIMG | python3 -c "
import json,sys; d=json.load(sys.stdin)
for b in ('light','mid','all'):
    c,r=d['concept'][b],d['render'][b]
    print(f\"{b:5s} Y {r['Y']:.4f} ({r['Y']/c['Y']:.2f}x) hue {r['hue']:.1f} (c {c['hue']:.1f}) sat {r['sat']:.3f} (c {c['sat']:.3f})\")"
[ -f $G ] || exit 0
python3 tools/buildings/grit-check.py $C $RIMG $G | python3 -c "
import json,sys; d=json.load(sys.stdin)
for k,v in d['regions'].items(): print(f\"{k:6s} std {v['concept']['std']:.3f} -> {v['render']['std']:.3f} ({v['std_ratio']}x)  hp {v['hp_ratio']}x  mean {v['mean_ratio']}x\")
print('shadow', d['shadow'])"
if [ -n "$CROPS" ]; then python3 - "$RIMG" "$CROPS" "$C" "$G" <<'PY'
import json, sys
from PIL import Image
R = json.load(open(sys.argv[4]))
c = Image.open(sys.argv[3]).convert('RGB'); r = Image.open(sys.argv[1]).convert('RGB').resize((1152, 720))
keys = list(R['concept'])
s = Image.new('RGB', (610, 205 * len(keys)), 'black')
for i, k in enumerate(keys):
    for j, (im, key) in enumerate(((c, 'concept'), (r, 'render'))):
        w, h = im.size; x0, y0, x1, y1 = R[key][k]
        s.paste(im.crop((int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h))).resize((300, 200)), (j * 305, i * 205))
s.save(sys.argv[2])
PY
fi
