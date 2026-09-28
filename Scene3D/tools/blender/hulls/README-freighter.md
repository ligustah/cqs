# Drover-class civil transport (CT-4 cargo / CT-7 troops)

The corvette's method (README.md), applied to the pair of civil ships with one parametric script.

```sh
PY=<python with bpy 5.x, scipy, pillow>
cd Scene3D
$PY tools/blender/hulls/measure.py assets/ships/raw/freighter.glb <work>/measure-c --rotate 0,-90,0 --length 134.12
$PY tools/blender/hulls/measure.py assets/ships/raw/freighter-troops.glb <work>/measure-t --rotate 0,-90,0 --length 128.84
PY=$PY tools/blender/hulls/freighter_build.sh cargo  <work>/c     # -> <work>/c/freighter-v3.glb
PY=$PY tools/blender/hulls/freighter_build.sh troops <work>/t     # -> <work>/t/freighter-troops-v3.glb
$PY tools/blender/hulls/freighter_module.py <work>/c/freighter-v3.glb <work>/t/freighter-troops-v3.glb src/ships/freighter.js
```

## Files

| File | Role |
| --- | --- |
| `freighter_dims.py` | Every dimension, both variants (pure Python): envelopes, crew-module section and taper, collar, reactor block, bells, housings, tanks, radiators, legs, container stacks (`containers()`), habitats. |
| `freighter.py` | The hull, `--variant cargo|troops`. Common: crew module (loft of measured sections with an upper-tier walkway ledge, bridge glazing band, recessed bow plate, grille, door and service bays), collar (airlock bays, docking tubes, cargo-control cab), reactor block, engine section (housings with bell-mount rings, tanks, keel and dorsal blocks, plumbing), radiators on truss pylons (finned bays), landing legs. Mid-body: cargo girder, decks, spine tube and container cell guides; or four habitat cylinders, spine tube, side girders and saddles. |
| `freighter_paint.py` | Paint scheme (civil light paint, irregular frames, hull-number stencils with C / T / 7 glyphs, teal stripe, hazard frames) and `paint_chunked`, paint.py's layers run in chunks so a 6144 atlas paints in ~2 GB. |
| `freighter_spec.py` | Kit placements -> `specs/freighter-v3.json`, `specs/freighter-troops-v3.json`. |
| `freighter_extras.py` | After assembly: container stacks and port lites, export, optimise. |
| `freighter_module.py` | Both variants into one `src/ships/freighter.js` (asset + `variants.troops`). |
| `freighter_build.sh` | model + raster/bake -> paint -> spec + assemble (`--no-optimize --blend`) -> extras. |

## What differs from the corvette pipeline, and why

- **Atlas 6144, two UV groups.** The ships carry ~30,000 m2 of surface (trusses, fins, radiator
  boxes). Thin members (girder webs, cell guides, pylon struts, fins, louvres, the cargo decks and
  spine tube, which the stacks hide) were thousands of islands whose pack margins ate the atlas
  (fill 0.17). They now get one 8 px cell each, dropped into space the main pack leaves free;
  the main surfaces pack alone (fill ~0.4). Main hull density 30.8 px/m (cargo) / 23.6 px/m
  (troops: the four habitat cylinders add ~6,800 m2 of main surface).
- **Position / normal / zone rasterised in numpy**, not baked with Cycles: three 6144 float bakes
  were OOM-killed next to the other agents' jobs. The raster reproduces the EMIT bakes (face
  normal, zone id, position) with an 8 px margin. AO and curvature are still Cycles bakes at
  2048; the AO sees the container stacks (proxies added for the bake only).
- **Ring bands never occlude.** Proud bands (housing collars, tank and habitat rings, frames)
  are ring-shaped closed solids without big buried caps, and are not used as occluders by
  `cull_hidden` (their parity test swallowed the habitat cylinders' long faces).
- **Containers** are the kit container baked (selected-to-active: colour, tangent normal,
  roughness) onto a 12-triangle box, two weathering variants in a 2048 atlas; each box's cargo
  colour is its material's base-colour factor, so it multiplies the texture *before* the livery
  (vertex colours would multiply after it and turn dark). Six weathered colours designed in
  livery space: rust, ochre, blue, green, a blue grey and a warm cream (so grey and white stay a
  little lighter than the hull).
- **Port lites**: hundreds of ~1 m ports (386 on the troop ship) at 38 triangles instead of the
  kit port's 1160 (348 decimated); glass passes livery.js's glass test, `glassGlow` lights it.

## Lessons

- An open mesh must not go through `recalc_face_normals`: the port lites came out inside-out
  (double-sided in glTF, so they rendered, but black).
- The hull numbers need glyphs hulltex's stencil lacks (C, T, 7): `freighter_paint.stencil`
  replaces `paint.stencil` for these ships.
- PATINA plate tone (tri-planar) is faded on sloped facets, where two projections blend into
  crossing diagonals.

## Result (installed)

| | cargo CT-4 | troops CT-7 |
| --- | --- | --- |
| envelope (L x B x H) | 134.12 x 54.68 x 38.16 m | 128.84 x 57.74 x 37.66 m |
| triangles (hull / total) | 33.7k / 95.9k | 45.2k / 126.8k |
| GLB | 5.1 MB | 6.0 MB |
| ports | 130 lites | 386 lites |
| containers | 169 boxes | - |
