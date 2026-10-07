#!/bin/bash
# audit.sh <building> <tag>: the pipe-logic / layout audit views of cams/<building>.json (top, rear, ...) (checklist P1)
. "$(dirname "$0")/env.sh"; B=$1; T=$2; O=$REVIEW_DIR/$B; mkdir -p $O
cd $SCENE3D
Q="mode=building&building=$B&t=20"
ARGS=()
while read -r name q; do ARGS+=("$Q&$q" "$O/$T-audit-$name.png"); done < <(python3 -c "
import json; c=json.load(open('$HERE/cams/$B.json'))
for k,v in c.get('audit',{}).items(): print(k, v)")
timeout 2400 node tools/shoot.mjs "${ARGS[@]}" --w 1600 --h 1000 --timeout 900000
