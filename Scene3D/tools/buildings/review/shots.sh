#!/bin/bash
# shots.sh <building> <tag>: the main shot at the module's studio hint (the concept camera) + the close-ups of
# cams/<building>.json, 1600 x 1000 -> $REVIEW_DIR/<building>/<tag>-{main,<view>...}.png
. "$(dirname "$0")/env.sh"; B=$1; T=$2; O=$REVIEW_DIR/$B; mkdir -p $O
cd $SCENE3D
Q="mode=building&building=$B&t=20"
ARGS=("$Q" "$O/$T-main.png")
while read -r name q; do ARGS+=("$Q&$q" "$O/$T-$name.png"); done < <(python3 -c "
import json,sys; c=json.load(open('$HERE/cams/$B.json')); cl=c['close']
for k,v in c['views'].items(): print(k, f\"az={cl['az']}&el={cl['el']}&fov={cl['fov']}&focus={v['focus']}&dist={v['dist']}\")")
timeout 2400 node tools/shoot.mjs "${ARGS[@]}" --w 1600 --h 1000 --timeout 900000
