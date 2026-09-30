#!/usr/bin/env bash
# Headless Blender for the remodel pipeline: bpy 5.0.1 (Blender as a Python module) + scipy + pillow
# in a Python 3.11 venv. No Blender app, GPU or display needed (Cycles CPU bakes and renders work;
# Workbench / EEVEE do not).
#   scripts/setup_blender_venv.sh <venv-dir>      then: PY=<venv-dir>/bin/python
set -euo pipefail
DIR="${1:?usage: setup_blender_venv.sh <venv-dir>}"
PYTHON="${PYTHON:-python3.11}"
command -v "$PYTHON" >/dev/null || { echo "need $PYTHON (bpy 5.0 wheels are built for CPython 3.11)"; exit 1; }
"$PYTHON" -m venv "$DIR"
"$DIR/bin/pip" install --quiet --upgrade pip
"$DIR/bin/pip" install --quiet bpy==5.0.1 "numpy<2" scipy pillow
"$DIR/bin/python" -c "import bpy, scipy, PIL; print('bpy', bpy.app.version_string, 'ok')"
