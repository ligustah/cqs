# Headless Blender remodel pipeline

In this project the tooling lives in `Scene3D/tools/blender/`. The method is in
`Scene3D/tools/blender/hulls/README.md`, and the per-asset notes and lessons are in
`Scene3D/tools/blender/hulls/README-<asset>.md`. Read
those for a new asset in the same repo. This file is the portable summary.

## Setup

- Install the `bpy` 5.0.1 pip wheel (Blender as a Python module) into a Python 3.11 venv with scipy and
  pillow: `.claude/skills/model-forge/scripts/setup_blender_venv.sh <dir>`. There is no Blender app, no GPU and no display.
  - Cycles renders and bakes work on the CPU.
  - Workbench and EEVEE need a GPU and do not work.
- Everything is authored in the **asset frame** the runtime uses: metres, forward (front) +Z, up +Y,
  left +X. The glTF export must land in that frame with no rotate and no scale in the module.
- On 4 CPUs:
  - a full model + bake of a large asset takes about 9 min;
  - paint takes a few minutes;
  - assembly takes a minute.

  Run long steps with `nohup` and poll a log, because foreground shell calls are capped at about 10
  min.

## Stages (one `build.sh <asset> <workdir>` runs them all)

1. **measure.py:** rotate, then scale to the asset's key dimension (length for vehicles; footprint or
   height for buildings), then centre, exactly as the runtime does. Ray-cast
   ortho views (top, bottom, sides, front, back) with a 1/5/10 m grid, depth maps, and bmesh sections
   every 2 m in Z and Y plus key X stations. Output: JSON and sheets.
2. **`<asset>.py --stage model --bake`:** the parametric model. Dimension tables (`<asset>_dims.py`) are
   shared with the spec generator.
   - The main body is a loft of mirrored half-profiles at stations, each profile segment in its own paint
     zone.
   - Superstructure: stacks of plan outlines at heights.
   - Pods: chamfered-octagon lofts. Pylons: hexagon lofts.
   - Bosses and tubes: cylinders and lathes.
   - Volumes interpenetrate freely.
   - The kit in `common.py` was built for hulls (lofts, plan stacks, prisms, lathes). Other domains add
     their primitives to it: extruded footprints, gable and hip roofs, arrays for planks, shingles and
     courses, timber frames. Symmetry is a choice, not a rule: buildings and props are often
     asymmetric.
   - True recesses (glazing bands, door bays, vents, radiator bays, intakes, hangars) are **EXACT
     boolean cutters**. Fins and louvres are added after the cut. Faces buried inside another volume
     are culled.
   - Bevel: angle-limited, 4-10 cm, one segment, harden normals, then face-area weighted normals.
     Symmetric by construction.
   - UV: smart projection per face group at one texel density, then packed (about 20-32 px/m at
     4096). Small islands (rails, fins, lenses) are packed at 0.4x density.
   - Cycles EMIT bakes: position, true normal, paint zone, AO and curvature (bevel-node difference)
     into `maps.npz`.
3. **`--stage paint` (paint.py + `<asset>_paint.py`), texture space:**
   - base: light base paint per zone;
   - plating seams in each face's own frame (horizontal bands in y, frames along the face's horizontal
     direction, staggered);
   - panel tone and access-panel outlines;
   - PATINA plate tone at the runtime tile;
   - weathering: AO grime, curvature edge wear, blotches and streaks;
   - decals: whatever the style uses (numbers in the style's stencil font, bands, hazard frames in
     `cqs-fleet`; signs, wear patterns, moss and stains elsewhere).

   The normal map carries the seams and panel outlines. Output: base, ORM, normal, and
   `<asset>-hull.glb`.
4. **Spec:** `<asset>_spec.py` writes `specs/<asset>-v3.json` from the dimension tables (see
   `parts-kits.md`).
5. **assemble.py:** loads the main body and the kit parts, places, snaps, seat-checks, decimates per part,
   runs a contact AO bake, and exports one GLB with the main-body node (named `hull` in this repo) plus
   `parts_*` nodes. It writes a
   report (tris per node, dropped placements, bbox growth).
6. **module.py:** drafts the runtime module (for vehicles in this repo):
   - engines from the bell placements (kit engine data times scale);
   - nav lights from the nav-light lenses;
   - `anchors.surfaces` (named flat faces for authored details and lights), re-measured by ray casts;
   - coordinates shifted by minus the assembled bbox centre.
7. **compare.py:** remodel over blueprint. Silhouette difference per view, IoU (aim for about 0.9+), a
   95th-percentile outline deviation, and section overlays.

For a glass or parts-only change, re-run **only** the spec and assembly on the existing
`<asset>-hull.glb`. In `cqs-fleet`, the fighter's glass fix took one minute this way. Keep the work directory of the
accepted build, and check it with md5 against the shipped GLB.

## Acceptance checks

- The envelope stays within 0.5 % of the previous build: slot volumes, hangar fits and parking depend
  on it. Run the scene's scale check after every install.
- The `dropped` list in the assembly report is empty, or every entry is deliberate.
- HD renders at hero, close and range show no floating parts, no buried glass, no seams crossing
  facets, and no mushy detail.

## Lessons (collected across five assets)

- Patching generated meshes (straightening, texture repair, pressed features) moves problems around.
  Remodel instead.
- A plan offset's "left" side depends on the walking direction. Check recess depth in a section before
  trusting it.
- A closed end cap on a band volume hides a recessed plate behind it. Build bands as annuli (outer and
  inner rings, no caps).
- A mixed-zone volume (thin trim + metal bands) must keep full UV density, or thin bands sample their
  neighbours (white banding).
- Decimation eats thin round pieces first. Split parts into connected pieces (on welded positions,
  because glTF import splits vertices at UV seams) and keep, drop or decimate each piece by its bounding
  box. Never decimate rails.
- Deep cup-shaped details go black under AO. Model shallow discs, or put the detail in paint (the
  RCS quads in `cqs-fleet`).
- World-axis tri-planar detail draws crossing lines on 30-60 degree facets. When the paint carries its
  own seams, turn the runtime detail down (normalStrength about 0.6, cavity about 0.2).
- The side view is usually lit from behind, so flanks sit in shadow. What reads from the side is
  silhouette above the main body line and lit horizontal surfaces. Design for it (raised sponsons, tiered
  superstructure).
- Training turrets or other movables outboard can grow the envelope (+4.7 % width once). Re-check the
  envelope after any "small" change.
- Numbers and markings: pale saturated stencils survive a dark runtime paint as low-visibility grey. Stand white
  numbers on a dark ID field, or they vanish. Keep numbers clear of shadows cast by turrets.
- Runtime paint colour shifts (`cqs-fleet`): orange hazard paint read salmon-pink through desaturation, so amber was used
  instead. Calibrate marking colours on renders, not swatches.
