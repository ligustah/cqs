#!/bin/bash
# prev.sh <part> [angles]: flat-colour geometry preview of a remodel part (stage R) -> $REVIEW_DIR/p-<part>-<az>_<el>.png
. "$(dirname "$0")/env.sh"
cd $SCENE3D
$BPY tools/blender/buildings/remodel.py $1 --preview $REVIEW_DIR/p-$1.glb 2>&1 | grep -E "remodel\]|Error|Trace|line "
timeout 600 node tools/render-glb.mjs $REVIEW_DIR/p-$1.glb $REVIEW_DIR/p-$1 --angles "${2:-35:15}" > /dev/null 2>&1
ls $REVIEW_DIR/p-$1*.png
