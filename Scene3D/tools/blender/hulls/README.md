# Hard-surface hull remodels

The fal / Tripo image-to-3D hulls are dense, noisy triangle soup: warped faces, soft chamfers,
melted details and light baked into the texture. Patching them (straighten.py, hulltex.py,
pressed features) only moves the problems around. This folder rebuilds a hull as clean,
parametric hard-surface geometry. The generated mesh serves only as the **blueprint**. The first
ship is the corvette (`corvette.py`); the other four follow the same method.

Everything is authored in the **ship frame** that `src/lib/glbship.js` produces and
`tools/blender/assemble.py` places parts in: metres, bow +Z, dorsal +Y, port +X.

```sh
PY=<python with bpy 5.x, scipy, pillow>       # e.g. the scratch blender-venv
cd Scene3D
$PY tools/blender/hulls/measure.py <tripo-raw.glb> <work>/measure --rotate 0,-90,0 --length 108.1
PY=$PY tools/blender/hulls/build.sh corvette <work>/m1          # model, bake, paint, assemble, module
$PY tools/blender/hulls/compare.py <work>/m1/corvette-hull.blend <work>/measure <work>/m1/cmp
```

## Files

| File | Role |
| --- | --- |
| `measure.py` | Blueprint in the ship frame (rotate, then length, then centre, exactly as glbship). Ray-cast ortho views (top, bottom, port, stbd, bow, stern) with a 1/5/10 m grid, plus depth maps. bmesh-bisect sections every 2 m along Z, every 2 m in Y, and at key X stations, as JSON and sheets. |
| `compare.py` | Remodel over blueprint. Silhouette difference per view (blue: blueprint only, red: remodel only), IoU, and 95th-percentile outline deviation. Sections overlaid (grey: blueprint, red: remodel). |
| `common.py` | Modelling kit: outlines (mirror a half-profile, offset polygon or polyline, chamfered rectangles), bmesh builders (loft, stack of plan outlines, prism, oriented prism, plate, cylinder, lathe, box), `Volume` (a closed solid with EXACT-boolean cutters and extra solids added after the cut), cull of buried faces, bevel and weighted normals, join, UV, Cycles EMIT bakes, the final glTF material, GLB export. |
| `<ship>.py` | Parametric hull: blueprint dimensions as functions of z, volumes, recess cutters, and the ship-module definition (`MODULE`). Stages are `model` (writes the `.blend`) and `--bake` (writes `maps.npz`), then `paint` (writes the textures and `<ship>-hull.glb`). |
| `paint.py` | Texture-space paint from the baked maps. Output: base colour, ORM and a tangent-space normal. Holds the ship's paint scheme (zones, seams, decals). |
| `module.py` | Ship-module draft from the assembly. Engines come from the bell placements (kit engine entry times scale), lights from the nav-light lenses, and `anchors.surfaces` are re-measured on the hull by ray casts. Coordinates are shifted by minus the assembled bbox centre. |
| `preview.py` | Quick Cycles clay renders of a `.blend` or `.glb` (Workbench and EEVEE need a GPU). |
| `build.sh` | The whole chain for one ship. |
| `<ship>_spec.py` → `../specs/<ship>-v3.json` | Kit placements for assemble.py, generated from the hull dimensions. `hull.centre: false` keeps the ship-frame origin. |

## Method

1. **Measure** (`measure.py`). Read the main volumes off the sections and ortho sheets: hull
   body stations (deck line, shoulder chamfer, flank, belt, lower chamfer, keel), deckhouse plan at
   deck and at roof, bridge, tower tiers, mast, pods, pylons, stern frame and bell layout,
   turrets, bow face. Keep the silhouette within about 0.3 m of the blueprint, except where
   the blueprint is visibly a reconstruction error. Keep the envelope the same, because the
   envelope sets the slot volume: the build uses symmetric extremes, bow lip at +54.05 and
   lowest bell exit at −54.05.
2. **Model** (`<ship>.py`). Each volume is a closed solid:
   - the hull is a loft of mirrored half-profiles at stations; each profile segment has its own paint zone;
   - the deckhouse and tower are stacks of plan outlines at heights;
   - pods are chamfered-octagon lofts, pylons are hexagon lofts;
   - bosses, tubes and intakes are cylinders and lathes.

   Volumes interpenetrate freely. **True recesses** (glazing band, door and airlock bays, vent
   bays, radiator bay, intakes) are EXACT boolean cutters. Fins and louvres are added after the
   cut. Faces buried inside another volume are culled. Each volume gets an angle-limited bevel
   of 4–10 cm (one segment gives an exact chamfer) with harden normals, then face-area weighted
   normals. Everything is symmetric by construction.
3. **UV and bake**. Smart projection per face group at one scale, then packed; the corvette
   gets about 20 px/m at 4096. Cycles EMIT bakes ship-frame position, true normal, paint zone,
   AO and curvature (bevel-node difference).
4. **Paint** (`paint.py`, texture space, ship frame). The base colour is light paint, because
   the runtime livery maps neutral luminance to the dark operational grey:
   - zone colours;
   - structural plating seams in each face's own frame: horizontal bands in y, frames along the
     face's horizontal direction (straight on every facet), staggered per band;
   - per-panel tone and access-panel outlines;
   - PATINA hull-set plate tone at the runtime tile (6 m);
   - AO grime, curvature edge wear, blotches and wall streaks;
   - decals: stencil hull number (hulltex's stencil), bands, hazard frames, marks.

   The normal map carries the seam grooves, access-panel outlines and foil crinkle.
5. **Assemble** (`assemble.py specs/<ship>-v3.json`). Place kit parts on the clean mounting
   faces: bells at the blueprint radii (kit bell times scale), turrets, torpedo doors, doors in
   their bays, ports in 3 m deck rows at 2.5 m pitch, panes on the recess back walls, rails,
   ladders, RCS, nav lights, floodlights, antennas, dome. Set per-part decimation in `fixes`.
   Do **not** decimate rails: collapse removes their tubes. Mount ports with `sink` of about
   0.03 m: their glass sits only 0.05 m above the mount face, so a deeper sink buries it under
   the skin.
6. **Module** (`module.py`), then `node tools/scale-check.mjs` in a scratch scene copy.

## Lessons (corvette)

- The seams lesson carries over to the runtime layer: world-axis tri-planar PATINA (patina.js)
  draws crossing lines on 30–60° facets. The remodel carries its own seams, so the module turns
  the runtime detail down (normalStrength 0.6, cavity 0.2).
- A plan offset's "left" side depends on the walking direction in the (x, z) plane. Check
  recess depth in a section (`compare.py`) before trusting it.
- Engine plumes (`effects.js`) are drawn from a BackSide proxy with depth test. In stern-quarter
  views the proxy's far faces lie behind the bell bodies, so the glow is clipped along straight
  lines across a bell: the "C-shaped rim". This is a runtime issue, not a mesh issue.
- Kit glass passes livery.js's glass test. The fix for "dark hole" ports is the sink depth above,
  plus the opt-in `glassGlow` livery option (a dim warm interior light, varying by compartment).
