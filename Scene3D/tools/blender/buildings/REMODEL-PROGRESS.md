# Steel mill remodel pilot: progress (resumable)

PY=/tmp/claude-0/-home-user-cqs/e592383b-a9f6-5dde-82a6-4494b59b11a7/scratchpad/blender-venv/bin/python
W=/tmp/claude-0/-home-user-cqs/e592383b-a9f6-5dde-82a6-4494b59b11a7/scratchpad/rm   (scratch work dir)

## Done
- Kit: cmeasure.py, ckit.py (furnace, banded_stack, gable_shed, pour_bay, incline_gallery), cpaint.py, remodel.py.
- R1 measure + R2-R5 r1 for all five parts (installed 2026-10-06 23:3x, commit 8703e98).
- r2 kit changes (lap rings, ribbed roofs, pour bay roof deck, molten paint, glTF occlusion) committed 1d6d679, NOT yet run.

- r3 (2026-10-07): remodel.unwrap stacks tiny / narrow islands into one swatch per zone (merge_overlap pack):
  furnace shell 27.6 -> 38.4 px/m at 4096, shed clad 47 -> 52, pour bay 64 -> 76, stack 42 -> 39 (2048), gallery 45 (2048).

## In progress
- r7: bake all five parts with r2 kit + r3 unwrap ($W/r7.log), then rebuild the building (colony_build.py --tex 2048).

## Next command
  cd /home/user/cqs/Scene3D && $PY tools/blender/buildings/remodel.py <part> --work $W/work > $W/r6-<part>.log 2>&1
