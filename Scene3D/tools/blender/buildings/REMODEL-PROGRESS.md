# Steel mill remodel pilot: progress (resumable)

PY=/tmp/claude-0/-home-user-cqs/e592383b-a9f6-5dde-82a6-4494b59b11a7/scratchpad/blender-venv/bin/python
W=/tmp/claude-0/-home-user-cqs/e592383b-a9f6-5dde-82a6-4494b59b11a7/scratchpad/rm   (scratch work dir)

## Done
- Kit: cmeasure.py, ckit.py (furnace, banded_stack, gable_shed, pour_bay, incline_gallery), cpaint.py, remodel.py.
- R1 measure + R2-R5 r1 for all five parts (installed 2026-10-06 23:3x, commit 8703e98).
- r2 kit changes (lap rings, ribbed roofs, pour bay roof deck, molten paint, glTF occlusion) committed 1d6d679, NOT yet run.

- r3 (2026-10-07): remodel.unwrap stacks tiny / narrow islands into one swatch per zone (merge_overlap pack):
  furnace shell 27.6 -> 38.4 px/m at 4096, shed clad 47 -> 52, pour bay 64 -> 76, stack 42 -> 39 (2048), gallery 45 (2048).

- r3 geometry: ckit.FURNACE_V4 (concept stations: light hearth drum, stepped dark bosh, light cone, dark hood, upper
  drum, raking plated legs with ties) and SHED_V4 (panel walls, heavy pilasters, roller + crew doors, no windows).
- r7 bake (r2 kit + r3 unwrap): bandedStack, pourBay, skipGallery installed (furnace/shed from r7 are superseded).
- Preview a part's geometry fast: $W/../uvx/prev.sh <part> "az:el" -> $W/../uvx/<part>-az_el.png

- Fix rounds on the building (2048 review builds r1-r3): dark pour bay deck, lighter gunmetal, low light annex, light
  casthouse front block (steel_mill.py), slimmer tower walkways. README-colony + lessons 56-59 written; remodel --preview.
- v3 evidence shots at fixed cameras: scratchpad/ev/v3-{main,furnace,pour,shed}.png (shots.sh swaps the v3 GLB+js in
  from $W/steel_mill-v3.*, shoots, restores).

## In progress
- r10: paint pass (neutral gunmetal, rust 0.2-0.3) -> rebake all five ($W/r10.log) -> final 4096 build ($W/b10.log).

## Next
- scratchpad/ev/shots.sh v4; sheet-v4.mjs -> images/buildings/steel_mill-v4.jpg (+ close-up sheet), thumbs.mjs 80/40,
  build-artifact.mjs, phone-check.mjs steel_mill, pkg-diff.mjs --csp 1 --units 16 b_steel_mill; commit all.
