# env.sh: sourced by the review scripts. Override any of these in the environment.
#   REVIEW_DIR  scratch for renders, logs and work dirs (default ${TMPDIR:-/tmp}/cqs-review)
#   BPY         a Python with the bpy module (BUILDING-GUIDE.md section 0b: python3.11 -m venv ...; pip install bpy==5.0.*)
#   SCENE3D     the Scene3D folder (default: found from this script)
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCENE3D="${SCENE3D:-$(cd "$HERE/../.." && pwd)}"
REPO="$(cd "$SCENE3D/.." && pwd)"
REVIEW_DIR="${REVIEW_DIR:-${TMPDIR:-/tmp}/cqs-review}"
BPY="${BPY:-python3}"
IMAGES="$REPO/style-library/styles/cqs-fleet/images/buildings"
mkdir -p "$REVIEW_DIR"
