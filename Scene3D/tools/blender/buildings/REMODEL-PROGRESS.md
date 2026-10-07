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

- r10 paint pass, final 4096 build (197k tris, 11.6 MB), evidence sheets, thumbnails, build-artifact + package check,
  pkg-diff desktop/phone (--csp 1 --units 16), phone-check: all done 2026-10-07.

## Status
DONE (steel mill pilot). Next building: follow README-colony.md "Component remodel".

## v5: second fidelity round (2026-10-07, user review of v4; scratch $S/v5, logs there)
Review points: 1 furnace silhouette (broad light bell, open light frame, downcomer / uptakes / skip bridge), 2 pour bay
(open portal, amber crane visible, longer brighter runner, control house), 3 density + wear (kit detail on walls,
plinth, furnace base; seam / grime contrast; trailer texture), 4 furnace shell texel density (second texture set),
5 neutral gunmetal.
- S1 geometry (done): ckit FURNACE_V5 (+ _posts_tower, _raking_legs, decks, header, 6-point downcomer), GALLERY_V5
  (open truss + gas main + tall tower), POUR_V5 (partial roof 0.32, bigger crane girder, runner along +Z 22 m, glow
  2.6, control house), SHED_V5 (_shed_dressing: canopies, wall pipes, tray, roof units, ridge vents, dock);
  steel_mill.py layout (furnace z 24, annex / dust catcher / stacks moved, bridge at heading 161.6, base dressing).
- S1 paint/kit (done, not yet baked): cpaint seam_w / streak / drip, neutral GRIME_D / DIRT_D / EDGE_DARK; WORKS
  lighter neutral gunmetal, less yellow light paint; remodel.py cull_buried (REMODEL_FLAGS="--no-cull" to skip) and
  ckit.SPLIT (blastFurnace shell -> colony_blastFurnace_2, own atlas).
- Next: S2 review bake (2048) of the 5 parts + building 2048, compare rounds; truck trailer (yard_kit); final 4096.
