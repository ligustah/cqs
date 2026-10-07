# Colony buildings: the recipe (one building in about 1-2 h)

The 16 colony buildings of `style-library/styles/cqs-fleet/briefs/buildings.md` are built one way: the approved concept
(correction 35) is the target; a 4K turnaround fixes proportions and layout; the building's distinctive pieces become
**fal-made components** (an isolated component image, then image-to-3D of that component alone, cleaned and sized in
Blender into a reusable kit part); everything generic comes from the shared parametric kit (`bkit.py`, see
`README-bkit.md`); the building script composes both; one generic runtime pattern shows it. Never generate a
whole-building mesh (the user, 2026-10-06: "use the fal 3d model to create small individual components, and then
simplify and compose them in blender as opposed to generating the full 3d model"); a whole-building mesh, if one
exists, is only a measuring reference.

**Every large component is rebuilt in Blender** (corrections 40-42, 2026-10-07: "one-shot creations from the fal
model ... very mushy", "extremely low res", "like from a 20 year old video game"). A fal / Tripo component mesh is a
BLUEPRINT only: it is measured, then the part is remodelled as clean parametric hard-surface geometry with its own
texture-space paint (section "Component remodel" below), under the same name and anchor. fal meshes may survive only
as small kit parts (about 3 m and under: valves, lamps, small machinery), and those too are cleaned and flattened
(planar faces, straight edges). No raw fal geometry, and no Tripo texture, stays on anything large or is scaled up.
The steel mill (v4) is the remodel pilot; the other 15 buildings follow it.

Pilots: `deuterium_depot`, `steel_mill`, v2: each composed from four to six fal components plus the parametric kit.
The v1 pilots (kit only, built while fal was blocked) are kept as the compare sheets `<id>-v1.jpg`; v2 sheets are
`<id>-v2.jpg`.

## Inputs (read first)

- The brief row and the fidelity checklist: `briefs/buildings.md` (plinth, light / dark contrast, dense secondary
  detail, lights, wear, depth).
- `images/buildings/<id>-concept.jpg` (the target) and `<id>-old-render.jpg` (what fell short: flat grey, no plinth
  kerb, no lights, thin detail).
- STYLE.md: Installations, Thumbnail readability, Reuse first, Phone first, Lights; corrections 22-35; kits.md.
- This kit: `README-bkit.md`, the component catalogue below, the pilots `deuterium_depot.py` and `steel_mill.py`.

## Stages

| # | Stage | Tool | Time |
|---|---|---|---|
| A | sizes and camera from the concept | by eye + the rulers | 10 min |
| B | 4K turnaround (layout, proportions; not meshed) | `fal-ai/nano-banana-pro/edit` | 5 min |
| C | components: image, mesh, ingest as a blueprint (reuse the catalogue first) | nano-banana-pro/edit, `tripo3d/h3.1/image-to-3d`, `component.py` | 15-40 min |
| R | remodel every large component: measure, parametric model, bake, paint, install | `cmeasure.py`, `ckit.py`, `remodel.py` | 20-60 min a part |
| D | the building script `<id>.py` on bkit + components | Blender (bpy) | 30-40 min |
| E | build, register, compare, fix (2-3 rounds), final 4096 bake | `colony_build.py`, `tools/buildings/compare.mjs` | 30 min |
| F | phone check, docs | `tools/build-artifact.mjs`, `tools/phone-check.mjs` | 10 min |

Record every fal job (endpoint, request id, inputs, status, what it was used for) in `Scene3D/pipeline/fal-pipeline.json`
under `v24_buildings`. Never re-submit a job: poll `check_job`, then `get_job_result`. If fal reports the account is
out of credit, stop paid jobs and say so.

### A. Sizes and camera

Real-world, plausible sizes, measured on the concept against its rulers (crew doors 1 x 2 m leaf in a 1.4 x 2.4 m
frame, rails 1.1 m, 1.8 m figures, 20-ft containers) and against each other. Record footprint and height in `SPEC`.
Concept camera: estimate azimuth and elevation from the plinth edges (two edges from the near corner: for azimuth a
and elevation e the +X edge runs `(cos a, sin e sin a)` on screen, the -Z edge `(sin a, sin e cos a)`), then tune by
eye in the compare loop. The pilots: depot az 30 / el 25, mill az 55 / el 20. Typical sizes: slab 60-100 m a side,
1.4-1.6 m deep; small plant houses 12 x 8 x 6.5 m; sheds eaves 18 m; tanks and towers to the concept's ratios.

### B. Turnaround (layout and proportions)

`fal-ai/nano-banana-pro/edit`, `image_urls` = [the concept uploaded to fal (`upload_file` with `prepare_upload`, then
PUT the bytes)], `resolution` 4K:

> Technical orthographic turnaround sheet of EXACTLY this building (same design, proportions, plinth, paint, markings,
> weathering, lights). Five views in a clean grid of equal cells on a plain seamless light-grey background: FRONT
> view (straight at the front, camera level), LEFT SIDE view, BACK view, RIGHT SIDE view, TOP view (straight down).
> Orthographic, no perspective, no shadows on the background, every view at the same scale, no labels.

Crop the cells (PIL). If the views disagree (a tank moves, a stack doubles), regenerate once, then stop. Both pilot
sheets ghosted a faded copy of the perspective concept across the grid and the depot's TOP view drew four spheres
(lesson 39): use the elevations for heights and the left-to-right order, take the plan from the concept by eye, and
never mesh the sheet. Save the usable sheet as `images/buildings/<id>-turnaround.jpg`.

### C. Components

1. **Decompose** the concept into its signature components (the shapes that carry the icon read and the dense
   pieces that are tedious to model: a sphere on legs, a furnace, a pump skid, a dome, a hangar) and generic pieces
   (plinth, framed walls, pipes, rails, stairs, lamps, roof units: bkit). Check the catalogue: reuse a component
   (scaled within reason, or as-is) before making one.
2. **Component image**: `fal-ai/nano-banana-pro/edit`, `image_urls` = [the concept] (the style reference), 2K, 4:3:

   > Isolated component for an original near-future colony building kit, in exactly the style, paint, frames,
   > markings and wear of the reference image: <component, with true dimensions, e.g. "a 21 m spherical pressure tank
   > on eight splayed gunmetal legs with shoulder gussets and concrete footings, a cobalt equator band, a top platform
   > with railing and valve housing, a meridian ladder; 1.1 m railings">. Three-quarter view from the front-left,
   > slightly above, on a plain light-grey studio background, soft even light, no shadows on the background, nothing
   > else in frame, no plinth, no text.

   Light paint and even light reconstruct best. Anything that must stay open (a bay, a lattice) must be drawn open.
3. **Mesh**: `tripo3d/h3.1/image-to-3d` with `image_url`, `texture: true`, `pbr: true`, `texture_quality: "detailed"`,
   `geometry_quality: "detailed"`, `face_limit` to suit (3k for a skid, 10-30k for a furnace or a dish). Download the
   GLB into `Scene3D/assets/buildings/raw/` (gitignored).
4. **Ingest**: `$PY tools/blender/buildings/component.py <raw.glb> <name> (--height | --width | --length | --long |
   --size W,H,D) [--rot x,y,z] [--tris N] [--tex 1024|2048] [--hot 0.8] --source images/buildings/components/<name>.jpg
   --fal <image job>,<mesh job> --used-by <id> --about "..."`. It welds, drops Tripo floaters, dissolves flat regions
   (UV-delimited), decimates, stands the part on y = 0 at true size, flattens the foot, keeps the texture (WebP),
   names the material `colony_<name>` and records the part in `assets/parts-colony/parts.json` (re-run all with
   `--rebuild`). Tripo H3.1 output is Y-up with the long axis on Z, so `--rot` was never needed on the pilots.
   - Size: uniform from one key dimension (`--width 26.5` for the sphere's footing span, `--height 60` for the furnace,
     `--long` for skids); per axis (`--size`) only where the building fixes all three (shed segment 28 x 24 x 36,
     skip gallery stretched to 46 m rise over 28 m).
   - `--hot 0.8`: bright saturated orange texels (molten runner, tuyere band, the image's small amber lamps) become an
     emissive map, so the concept's glow is real at runtime; amber paint (darker) stays unlit.
   - Texture: 2048 px for hero components (sphere, furnace, pour bay), 1024 for the rest; the phone copy caps all at 512.
   - Paint is normalised at ingest, never lifted at runtime (see "Paint calibration" below): `component.py` matches
     the part's albedo to its own source image (`--source`, or the recorded one) and caps its metalness; `--no-norm`
     skips it (only for a part with no source image). `--hot-sat 0.35` lowers the hot texels' saturation floor (the
     residence's dim amber windows: `--hot 0.5 --hot-sat 0.35`); `--glass` turns warm-baked glazing cool with a dim
     warm emissive interior (not needed so far: check the texture's hue first).
5. **Check** it: `node tools/render-glb.mjs assets/parts-colony/<name>.glb <out> --angles "35:20,0:89"` (three-quarter
   and top: confirm which face is front), and `--bg dark` for `--hot` parts. Reject glass-as-hole, mushy faces, a
   mirrored marking, missing open bays. Then add a row to the catalogue below. All nine pilot components passed first
   time: isolated, light-background component images reconstruct far better than whole buildings.

### D. The building script

`tools/blender/buildings/<id>.py`:

```python
import math
import bkit as K

SPEC = {'title': 'Oil Tanks', 'gameId': 'OIL_TANKS', 'group': 'storage', 'footprint': [80, 64], 'height': 18,
        'camera': {'az': 35, 'el': 27}, 'about': '...'}

def model(B):                                     # building frame: plinth top y = 0, +Z front, +X left
    W, D = SPEC['footprint']
    K.plinth(B, W, D, h=1.4, markings=[...], grates=[...], steps=[...])
    for (x, z) in ((-20, -8), (14, -12), (-4, 14)):
        K.component(B, 'floatTank', (x, 0, z), heading=0)        # fal component (catalogue)
    K.block(B, (18, 0, 18), (12, 6.5, 8), sides={'+z': {'doors': [8.0], 'rollers': [(3.6, 3.6, 4.0)]},
            '+x': {'windows': [0], 'win': (1.2, 1.0)}}, roof={'parapet': 0.45, 'units': [('hvac', 0, 0, {})]})
    K.pipe(B, [(..), (..), (..)], r=0.6, supports=True)
    K.bollards(B, [...]); K.lamp_post(B, (x, 0, z)); K.worker(B, (x, 0, z), heading=200)
    B.R.beacon((x, y, z))
```

Rules from the pilots:
- Signature shapes first (the icon read), at the concept's ratios; then the secondary layer: pipes with flanges,
  rails, ladders, roof units, cabinets, bollards, vehicles, figures. Keep it compact (icon aspect <= 1.5).
- Light / dark split: off-white `panel` walls in gunmetal `frame` (thin: posts 0.6 m, parapet cap 0.42 m, pilasters
  0.4 m); big plain facades (sheds) with `seams: False, bands: False`; roofs light (`panel2`).
- Lights: amber pins at block corners, plinth edges, legs; door lamps come with every `facade(doors=...)`; ~55 % lit
  windows; 2-3 beacons; red obstruction lights on stacks only; hot glow (pour, furnace) as `glowbox` / `glow_ring`.
  Floods only aimed away from the camera (a lens facing the camera blooms).
- Placements that mount +Y (yard parts, components) take `heading`; never pass only `up`.

### E. Build, register, compare

```sh
PY=<venv with bpy 5.x>/bin/python
$PY tools/blender/buildings/colony_build.py <id> <scratch>/w-<id> --tex 2048 --samples 6     # review rounds (~45 s)
$PY tools/blender/buildings/colony_build.py <id> <scratch>/w-<id> --tex 4096 --samples 10    # final (~3.5 min)
```

It bakes the hull, writes `specs/<id>-v1.json`, assembles with the fleet / yard / colony kits, installs
`assets/buildings/<id>.glb` (+ a local `.lite.glb`) and writes the GENERATED block of `src/buildings/<id>.js`
(created from the template the first time: fill in `meta` and the `studio` hint `{ az, el, sunaz, sunel, dist }`).
Register it once: `src/ships/index.js` `BUILDINGS` (`<id>: { module: '../buildings/<id>.js', fleet: false }`) and
`tools/phone-check.mjs` `COLONY_VIEWS`; the Buildings menu (`src/buildings/catalog.js`) then enables it and
`src/lib/scale.js` already has its `CLASSES` row. The scratch work dir is deleted after the build (disk is tight).

Compare (every round):

```sh
node tools/buildings/compare.mjs <id> --version r1 --out <scratch>/<id>-r1.jpg       # review rounds
node tools/buildings/compare.mjs <id> --version v1 --extra "close=focus=x,y,z&dist=m" # final sheet
```

The sheet is concept | old render | new render at the concept's 3:2 frame, plus 80 / 40 px icons on #222d35 (1:1 and
3x) and the icon aspect; the final one goes to `style-library/styles/cqs-fleet/images/buildings/<id>-v1.jpg`. Look at
it yourself, then fix the largest difference first: massing and placement, then light / dark contrast (the key side:
`sunaz`), then detail density, then lights. Two or three rounds. Typical round-1 faults seen on the pilots: walls
greyed by grime (fixed in bkit), the key lighting the wrong face, flood glare, seam grids too busy, too-thin legs,
a +Y part turned 90 degrees.

### F. Phone check and docs

```sh
node tools/build-artifact.mjs && node tools/phone-check.mjs <id>     # budget: heap + GPU well under 300 MB
node tools/scale-check.mjs                                           # must print SCALE CHECK PASSED
```

Building phone copies are 512 px with workers and vents dropped (`build-artifact.mjs` `LITE_COLONY`). Add the row to
the README "Phone budget" table, the catalogue rows, and a line in `style-library/styles/cqs-fleet/assets.md`.

## Component remodel (v4, 2026-10-07: corrections 40-42; pilot: the steel mill)

Why: the v2 / v3 components were the Tripo meshes themselves, cleaned and sized (`component.py`). Image-to-3D averages
detail into soft lumps and de-lights its texture at a fraction of the source image's resolution, so at the building
camera they read "mushy" (soft chamfers, wavy facets, melted rails and ladders, smeared bands; correction 40) and up
close "extremely low res" (correction 41). The ships met the bar by rebuilding every hull as parametric hard-surface
geometry with the generated mesh as a blueprint (lessons 4-5, `../hulls/README.md`); the components now do the same.

Rule: **a fal component mesh is a blueprint, never the part.** Every large component (anything over about 3 m, every
signature shape) is remodelled. A small fal part may stay (valves, lamps, small machinery), cleaned and flattened.
Nothing from Tripo is scaled up, and no Tripo texture is kept on a remodelled part: colour comes from the kit's calibrated
paint and procedural texture-space layers, with the component image and the concept as the colour and wear reference.

Tools (all in this folder):

| file | role |
|---|---|
| `cmeasure.py` | measure a blueprint in the part frame: ray-cast ortho views (front from +Z, left from +X, top) on a 1 / 5 / 10 m grid, the radial profile r(y) about a vertical axis with its stations (steps > 0.25 m: flanges, bands, the bosh / shaft break), the ledge heights (up-facing area per 0.25 m: decks, platforms, eaves); `--compare remodel.glb` overlays the remodel's silhouettes (red) and profile on the blueprint's and reports the silhouette IoU |
| `ckit.py` | the parametric remodel kit on `bkit.Build`: generic builders `furnace`, `banded_stack`, `gable_shed`, `pour_bay`, `incline_gallery`; details `laced_column`, `ibeam`, `plate_girder`, `warren`, `square_deck`, `hoop`, `plate`, `clad_panel` (sheets split round exact openings), `window_strip` (recessed glazing), `louvre_bank`, `lamp`; the extra paint zones (`shell`, `clad`, `clad2`, `hot`, `lamp`, `louvre`, `rust`); the `WORKS` heavy-industry paint; `REMODELS` (part name -> builder, measured parameters, texture size, about) |
| `cpaint.py` | texture-space paint from the baked maps (part frame): zone colours from `lib.MATS` (the calibrated kit scale) with per-zone overrides; plating seams (courses in y, staggered joints along the face or round an axis), per-plate tone, bolt rows, corrugation, grating; PATINA 'hull' plate tone at the runtime 6 m tile; AO grime, ground dirt, run-off and rust streaks, rust bleeding from seams, curvature edge wear (primer on light paint, bare steel and rust on dark); emissive for `hot` and `lamp`; a tangent-space normal map from the seam / bolt / corrugation / grating height |
| `remodel.py` | the chain for one part: model -> bevel + weighted normals -> UV (per-zone texel weights) -> Cycles bakes (position, normal, zone, AO 1.2 m, curvature) -> paint -> one material `colony_<name>` (base, ORM, normal, emissive) -> `assets/parts-colony/<name>.glb` (WebP) -> `parts.json` (the remodel record, the part's lights and kit placements; the blueprint's ingest record kept under `blueprint`) |

```sh
PY=<python with bpy 5.x, numpy, pillow>
$PY tools/blender/buildings/cmeasure.py <name> <work>/m-<name> --res 0.07              # R1 measure the blueprint
$PY tools/blender/buildings/remodel.py <name> --dry                                   # R2 model: tris, bbox, zones
$PY tools/blender/buildings/remodel.py <name> --preview <work>/<name>.glb             # R2 geometry check, flat colours
node tools/render-glb.mjs <work>/<name>.glb <work>/p-<name> --angles "35:15"           #   (40 s; before any bake)
node tools/render-glb.mjs assets/parts-colony/<name>.glb <work>/<name> --angles "35:20,215:25"   # (after R3-R5)
$PY tools/blender/buildings/remodel.py <name> [<name> ...] [--tex 2048] --work <work>  # R3-R5 bake, paint, install
$PY tools/blender/buildings/cmeasure.py <name> <work>/c-<name> --compare assets/parts-colony/<name>.glb  # vs blueprint
```

(For `--compare` keep a copy of the blueprint GLB first: `remodel.py` replaces `assets/parts-colony/<name>.glb`; the raw
Tripo mesh stays in `assets/buildings/raw/`.)

### The recipe, per component

1. **Decide.** Over about 3 m, or a signature shape: remodel. Pick the generic builder that fits (a vessel or tower
   from stations: `furnace`; any chimney / column / silo: `banded_stack`; any clad portal shed: `gable_shed`; an open
   crane bay: `pour_bay`; an inclined conveyor or bridge: `incline_gallery`), or write a new generic one in `ckit.py`
   from the shared details. A new builder takes a parameter dict, so a sister part is a new dict, not new code.
2. **Measure** (`cmeasure.py`, 10 min), then **fit the concept** (below): blueprint for the envelope, concept for the
   stations and the light / dark rhythm. Read off the ortho sheets and `profile.json`: the envelope (keep the
   ingested bbox: the building scripts place the part by it), radii and heights of every station (plinth, hearth,
   bands, flanges, cone, throat), deck and platform heights (`ledges.json`), bay and panel counts, column positions
   (top view), openings. Correct what is a reconstruction error, not a design (the skip gallery's stretched drive
   house; the stack's off-centre radial profile) by the component image and the concept.
3. **Model** (`ckit.py`, 15-45 min). Rules that made the edges crisp:
   - every volume a closed solid (lathes from pole to pole, prisms, boxes); profile points in increasing y so
     normals face out; 40-48 segments on round shells (smooth shading, sharp angle 30-50 degrees);
   - bevels 2-6 cm on every box and band (`lib.Part` angle-limited bevel with harden normals: each edge one chamfer
     that catches the light), none on thin bars, rails and lacing (they would only add triangles);
   - true size from the fleet rulers: rails 1.1 m (posts 1.5-1.8 m), caged ladders 0.62 m, stair treads 0.18 / 0.28 m,
     crew doors as the fleet kit door (a Rec placement), grating decks 0.14 m, I-beams with real flanges and webs,
     laced columns with angle chords and X lacing, plate girders with stiffeners;
   - exact openings, not boolean cutters: `clad_panel` splits the sheet round each hole and `window_strip` /
     `louvre_bank` put recessed glass, mullions, reveals and blades in it; one-sided `plate` for cladding whose inside is
     never seen (no texels spent on it);
   - lights live in the part: `lamp()` housings with a lit lens and a pin, `B.R.glowbox` / `K.glow_ring` for hot
     zones, `B.R.obstruction` on stack tops, `B.R.door` kit doors; `remodel.py` stores them in `parts.json` and
     `bkit.component()` adds them to every building that places the part, through its heading and scale.
4. **Paint spec** (returned by the builder, merged over `ckit.WORKS`): per zone `course` / `joint` (m), `axis` (x, z)
   for round shells (joints as arc length), `bolts` (pitch), `corr` (corrugation pitch), `rust`, `edge`, `tone`,
   `dark`, `color` (sRGB override). Calibrate light paint with `tools/buildings/paint-check.py` on the building render:
   the steel mill's light paint is a warm weathered grey (`WORKS`: shell sRGB (191, 182, 168), cladding (196, 189, 176)),
   which brought its light band from 1.31x the concept (v3) to 1.23x with the building hull unchanged and the hue from
   15 to 29 degrees (concept 23).
5. **Bake and paint** (`remodel.py`, 1-6 min a part at 2048-4096). UVs: smart projection at one scale, then islands of
   dark structure, grating, glass and interiors scaled down (`UV_WEIGHT`, 0.25-0.85) before packing, so the light
   shells and cladding get the texels: the furnace's shell 31 px/m and the shed's cladding 47 px/m at 4096 (v3: one
   2048 texture over the whole Tripo furnace). Hero parts at 4096 (furnace, shed, pour bay), the rest 2048; the phone
   copy caps all at 512 (`lite-glb.mjs`).
6. **Check** each part alone: geometry first with the flat-colour preview (`ckit` builder -> zone colours ->
   `remodel.py <name> --preview <out.glb>`, then `render-glb.mjs`: 40 s), then the baked part (`render-glb.mjs`, two angles), then the building (`colony_build.py`, `compare.mjs`,
   `paint-check.py`) and a 1:1 close-up next to the old one at the same camera (`shoot.mjs` with `focus=` / `dist=`).
   Fix the largest difference first: occluding decks (the furnace's first full square decks hid the shaft: rings and
   side walkways instead), the glow placement (the tuyere band above its platform, not under a deck), the crane under
   the eaves girder (lowered runway), opaque glow volumes (a 1.8 m haze glow box over the runner drew as a solid orange
   slab: keep glow boxes thin), camouflage blotches (blotch tone +-7 %, not +-16 %).

### Steel mill parts (v4)

| part | builder (params) | measured / fitted stations | tris (v3 Tripo -> v4) | texture | px/m (light zones) | chain at final size |
|---|---|---|---|---|---|---|
| blastFurnace | `furnace` (`FURNACE_V4`) | blueprint plinth 27.4 x 3 x 29.2 and envelope; stations refitted to the CONCEPT (15.5 px/m on the concept, ground to 60 m): light plated hearth drum r 7.6 to 17.4 m with hoops and modelled course laps, glowing tuyere band 17.6-19.8 (30 windows), stepped dark bosh in four lipped courses to 29, light cone r 8.4 -> 6.5 to 42, dark stepped hood to 46.5, upper drum r 3.9 to 55, cap to 60; four raking plated legs (2.8 -> 2.0 m box, stiffener bands, base shoes, plate-girder ties to the tuyere deck) to the first deck at 29, laced columns to the top deck at 52.6 | 29,137 -> 70,680 | 4096 | 33.9 (shell) | 3.6 min |
| bandedStack | `banded_stack` (`STACK`) | base 11 x 3.1; flare r 5.0 -> 3.78 (3.1-9.6 m); shaft r 3.75 to 42.6; platforms 19.4 / 42.8; lip r 4.05 at 46; lap rings every 2.2 m | 8,959 -> 23,912 | 2048 | 39.9 (shell) | 0.8 min |
| shedSegment | `gable_shed` (`SHED_V4`) | 28 x 36 (wall 27.2); eaves 14.4, ridge 21.2; 5 bays of 7.2 m; monitor 5.6 x 27 to 24 m; concept wall: flat panel grid (2.8 x 2.4 m, aligned), modelled course joints, 1.0 x 0.75 m pilasters, roller door in the back bay, two kit crew doors, no high windows; standing-seam ribs on the roof | 7,534 -> 8,042 | 4096 | 50.9 (cladding) | 3.8 min |
| pourBay | `pour_bay` (`POUR`) | x -9.5..9.5 open to +X, z -13..13, 15.5 m; columns at x +-8.4, z +-12; eaves girder 12.2-13.6; truss to 15.4; dark ribbed steel deck | 25,842 -> 15,426 | 4096 | 66.5 (frame2), 54 (apron) | 4.6 min |
| skipGallery | `incline_gallery` (`GALLERY`) | 6 x 46 x 28: gallery (0, 9.5, 9.6) -> (0, 39.8, -9.6), drive house z 9.6-14, head house y 36-46, trestle at z -4.5 | 12,915 -> 7,168 | 2048 | 45.3 (cladding) | 1.1 min |

Measured times (4 CPU threads, 2026-10-07): the chain above per part (bake 23-142 s, paint 21-126 s); all five parts
in one `remodel.py` run 14 min; the building review build (`colony_build.py --tex 2048 --samples 6`) 68 s; the final
(`--tex 4096 --samples 10`) ~10 min; one `compare.mjs` render 50 s; a geometry-only preview of a part (model, flat zone
colours, `render-glb.mjs`) 40 s. Authoring per part, first time (builder from the measures): furnace ~45 min + 30 min
concept refit, stack ~15 min, shed ~25 min + 15 min refit, pour bay ~35 min, gallery ~20 min; a sister part is a new
parameter dict (~10 min + the chain).

**Fit the CONCEPT, not only the blueprint.** The first v4 furnace followed its Tripo blueprint (dark staved hearth, one
tall light shaft, a square laced tower with four decks) and was crisp but did not read as the concept's furnace. The
concept's stations, read off the image against its height, are what make the icon: a light drum, the glow, a dark
stepped bosh, a light cone, a dark hood, the narrow top, heavy raking legs. Use the blueprint for the envelope and the
anchor, the concept for the stations and the light / dark rhythm. The same for the shed: the concept's wall is a flat
panel grid with heavy pilasters, not corrugation with high window strips.

**Texel density: stack the thin structure** (`remodel.unwrap`, v4 r3). A lattice-heavy part is thousands of islands a
few texels wide (the furnace: 10,900 islands, 86 % of them rails, lacing, rods and rungs holding 9 % of the surface),
and each paid a 1.5 px margin: the atlas filled 37 %. Islands under 2 m2 in the structural zones (`STACK_ZONES`), and
any island narrower than 0.25 m or under 0.15 m2 in any zone but `hot`, `lamp` and glass, are now normalised into one
shared square swatch per zone and packed as one island (`merge_overlap`); a 10 cm bar shows one painted tone with its
edge wear at any distance, which the swatch still carries. Fill rose to 0.55-0.88 and the light zones gained 20-90 %
(furnace shell 27.6 -> 38.4 px/m on the blueprint-shaped furnace; shed cladding 47 -> 51; pour bay 64 -> 77; stack
and gallery ~40-45 at 2048). Concrete weight 0.7 (it was 1.0: the furnace plinth took as many texels as the shell).

Checks on the final v4 (2026-10-07): `build-artifact.mjs` package check 57 model tiers OK; `pkg-diff.mjs --csp 1
--units 16 b_steel_mill` desktop 0.00 % (no program over 16 samplers with the parts' occlusion maps), phone 0.44 %;
`phone-check.mjs steel_mill` heap + GPU 133 MB. Evidence: `images/buildings/steel_mill-v4.jpg` (concept | v3 | v4),
`steel_mill-v4-close.jpg` (furnace, pour bay, shed wall at 1:1, v3 beside v4 at the same cameras),
`steel_mill-v4-thumbs.png` (80 / 40 px).

### v5: second fidelity round (2026-10-07, the user's review of v4)

The review against the concept found five problems; what fixed each (parameter sets in `ckit.py`, all generic):

| # | v4 problem | v5 fix |
|---|---|---|
| 1 | furnace: a thin cylinder inside a tall black square lattice tower (read as a scaffold) | `FURNACE_V5`: a broad light bell (cone foot r 11.4 over a dark stepped bosh r 9.6-10.65, tapering to r 8.1 at 42 m; hearth drum r 9.2), heavy plated raking legs (4.0 -> 2.8 m box, corner angles, bands, base shoes) to the cone-foot deck, then a light open frame: four slim tapered posts (`_posts_tower`) to a wide square top deck, X bracing in the top bay only, decks round the cone foot and the hood; a 0.85 m bustle main at r 12.6; four uptakes over the cap into a header drum; a 2.9 m downcomer from the header down the -X side into the gas-cleaning annex. `GALLERY_V5`: the skip bridge as an open box truss with a skip car and track, the gas main on saddles over it, landing on a 30 m clad tower between the stacks and the shed |
| 2 | pour bay: a solid dark slab roof hid the crane | `POUR_V5`: `roof` 0.32 (a dark deck over the back third only; purlins and X rods over the crane), bridge girders 1.0 x 2.0 m, the runner along +Z out of the bay toward the casthouse (22 m, core glow 2.6) via `runner_at`, the ladle track at the front, a railed control house inside the portal (`control`: lit windows, kit door, roof unit, ladder) |
| 3 | clean CG, large plain panels | `SHED_V5` / `_shed_dressing`: door canopies and steps, wall pipe runs with flanges, amber rings and brackets (both long faces), a cable tray under the eaves, a second row of pilaster lamps, roof curb units, ridge ventilators, a loading dock with a stair at the roller door; `steel_mill.py`: cooling-water mains on stools, a valve, a cable tray and stair at the furnace plinth, pipe run, tray, stair, crates and a roof unit at the casthouse. Paint (`cpaint.py`): `seam_w`, `streak` / `streak_f` (thin run-off), `drip` (grime held in each course seam running down the panel below); clad seams `dark` 0.6, tone 0.13. The yard truck's trailer (`yard_kit.truck`): external posts, rails, corner posts, rear doors with lock rods, guards, marker lamps |
| 4 | furnace shell 34 px/m, soft at 1:1 | a second texture set (`ckit.SPLIT`: the `shell` zone -> its own 4096 atlas and material `colony_blastFurnace_2`, same 4 maps, so no material exceeds the colony sampler count) whose revolved faces are unrolled (`remodel.CYL`: 24 sectors x 6 m bands, u = arc length, v = height); hollow islands (annuli of hoops and lap rings: area < 12 % of their box) are stacked like thin structure; buried faces culled before unwrapping (`remodel.cull_buried`). Shell 34 -> ~70 px/m at 4096 (fill 0.79) |
| 5 | dark steel warm brown (saturation 0.2-0.3; the concept's ~0.09) | the base was neutral: the brown came from the weathering. Dark zones now take a neutral soot (`GRIME_D`), neutral ground dirt (`DIRT_D`), neutral bare-steel edges (`EDGE_DARK`), rusty edges scaled by the zone's `rust`; `WORKS` frame / frame2 / mains lighter neutral gunmetal (sRGB 0.33 / 0.37 / 0.42), rust 0.1-0.15; the light paint a step less yellow |

`remodel.cull_buried` (all parts, `REMODEL_FLAGS="--no-cull"` to skip): a face is buried when every sample (centre,
corners and edge midpoints pulled 5 % in, fan-triangle centroids, 4 mm off the face) has a positive winding number
(solids containing it, counted along five rays: back faces +1, front faces -1, coincident faces at one hit all counted)
or when it lies on the ground facing down. The furnace lost 7,636 of 33,046 faces (lathe caps inside the next station,
stacked bands, footing undersides); first versions with five samples and a first-hit test wrongly culled the furnace
plinth top (its samples sat under the leg shoes) and kept coincident caps. Check every part's preview after a change.

Process: three 2048 review rounds (bake all five parts ~4 min, building ~70 s, four evidence shots ~3 min), then the
final 4096 build. Evidence: `images/buildings/steel_mill-v5.jpg` (concept | v4 | v5 at the concept camera),
`steel_mill-v5-close.jpg` (the v4 close-up cameras), `steel_mill-v5-thumbs.png` (80 / 40 px).

### Gotchas

- `hulls/common.bake_maps` returns the SHIP frame (x, z, -y of Blender); the kit authors the part frame directly in
  Blender with +Y up, so `remodel.py` converts pos / nrm back (x, -z, y) before painting.
- Smart UV margins of 3 px on a part with thousands of small islands (lacing, rails) left 16 % of the atlas used
  (6.5 px/m on the furnace); 1.5 px margins and the per-zone weights gave 46-76 %.
- `component.py` refuses to re-ingest a remodelled part (`--force-ingest` to replace it with the raw mesh again) and
  `--rebuild` skips them.
- v5: the concave packer drops tiny islands into gaps inside a stacked swatch; any small emissive island there makes
  every bar using that swatch glow (the furnace rails at 4096). Lamp lenses are stacked; only `hot` and glass are not.
- The glow (`hot`) zone is emissive in the texture and gets a runtime glow box too; keep glow boxes thin (< 0.1 m)
  or they read as solid slabs in the dusk studio.

## Paint calibration (v3, 2026-10-06)

v2 compensated dark, brown components with runtime lifts of different sizes (the factory's 1.25 on every `colony_*`,
then 1.2-1.6 per module, the radio dish 2.5 with a cool tint). Measured (`component.py` stats in `parts.json` `albedo`,
and a GrabCut-masked light-paint band, p70-97 of the building's pixels, of render vs concept), two causes:

1. **Tripo's albedo is darker and warmer than its own source image.** Over all 50 components the surface-weighted
   (triangle area x barycentric texel samples) linear albedo was 0.84-4.2x (median 1.6x) below the component image's
   foreground, with about twice its saturation on the neutral paint (the brown cast), and its tonal range was flattened
   (the dish face baked near white, the yoke under it near black). The ingest preserved it exactly (0.099 -> 0.101 on
   the dish): it is Tripo's de-lighting, not the colour space, the WebP export or the finish.
2. **The dusk studio's key at 0.5 rendered even the kit's calibrated panel paint (linear 0.60) at 0.55-0.8x the
   concepts' light-paint luminance.** Key 1.0 alone brought four test buildings to 0.96-1.09x but over-lit the big
   light roofs and slabs and flattened the shadows; over all 16, key 0.85 with fill 0.4 and env 0.45 gives a median
   0.95x.

The fix, once in the shared pipeline:
- `component.py` normalises every part at ingest against its source image (`NORM`): a white balance from the neutral
  texels (sat < 0.15, +-15 %), a chroma pull on near-neutral paint toward the image's (never more saturated; sat > 0.45
  amber, cobalt and lamps kept), one linear gain (0.85-3.2x, bisected so the p30-p97 trimmed mean equals the image's,
  soft knee at 0.72 -> 0.94), a tonal match (the toned texture's p5-p98 luminance quantiles onto the image's, 60 %
  strength, per texel 0.6-2.2x), and a metal cap (mean metallic <= 0.15 through the map). It runs after `--hot` (which
  reads the raw paint) and records gain, wb, chroma, before / after / image luminance and saturation in `parts.json`.
  `--rebuild` re-ingests every part from its raw mesh with the same params.
- `colony.js`: no runtime lift (`materials` stays for looks that are not paint); `DUSK` key 0.85, fill 0.4, env 0.45.
  Per-building lighting trims (studio hint `key`, never a paint lift): steel mill 0.6, infrastructure 0.62, residence
  0.6, steel depot 0.6, military base 0.6, transmitter 0.5 (big light roofs / slabs / ring read over-lit), refinery and
  radio telescope 1.15, trade center 1.05. `?key= / ?fill= / ?env= / ?rim= / ?kick=` override them for a test shot.
- Every per-module lift and metalness override was removed (infrastructure, library, military base, radio telescope,
  residence, silicon depot, trade center, university); the transmitter keeps its ring-segment tint (a look: the
  concept's ring is mid grey, darker than its image's).
- Verify every building after a rebuild: `python3 tools/buildings/paint-check.py <concept> shots/buildings/<id>-<v>.png`
  (light-band luminance ratio about 0.9-1.1, hue within ~10 degrees of the concept's). Fix a building's remaining
  difference in its geometry and kit materials (lighter trim `frameL`, `stone`), not with a runtime lift.

## Phone budget (measured, phone tier, `tools/phone-check.mjs`; v3 rows after the paint pass)

| view | fetched MB | tris | textures MB | heap + GPU MB | ready s |
|---|---|---|---|---|---|
| deuterium_depot (v3: 4 components) | 5.1 | 120k | 27 | 110 | 4.9 |
| steel_mill (v3: 6 components) | 6.4 | 127k | 43 | 127 | 4.7 |
| steel_mill (v4: 5 remodelled parts, 7 placed) | 6.2 | 196k | 46 | 133 | 4.0 |
| silicon_depot (v3: 5 components) | 3.9 | 71k | 32 | 115 | 6.9 |
| military_base (v3: 23 components + 1 V-31) | 6.7 | 146k | 49 | 138 | 6.2 |
| radio_telescope (v3: 2 components) | 3.3 | 58k | 21 | 102 | 6.0 |
| transmitter (v3: 24 components, orbital) | 7.1 | 138k | 31 | 119 | 5.9 |
| refinery (v3: 4 components, 7 placed) | 6.5 | 165k | 34 | 120 | 4.6 |
| processing_plant (v3: 6 components, 9 placed) | 5.9 | 133k | 42 | 127 | 5.4 |
| oil_tanks (v3: 3 components, 5 placed) | 3.5 | 68k | 24 | 106 | 4.0 |
| silicon_foundry (v3: 2 components, 7 placed) | 3.4 | 59k | 23 | 104 | 4.4 |
| steel_depot (v3: 4 components, 30 placed) | 7.0 | 135k | 38 | 123 | 6.2 |
| trade_center (v3: 4 components, 5 placed) | 4.2 | 61k | 41 | 122 | 8.1 |
| infrastructure (v3: 4 components, 10 placed) | 4.5 | 78k | 38 | 120 | 5.4 |
| residence (v3: 2 components, 5 placed) | 4.0 | 65k | 23 | 107 | 4.5 |
| university (v3: 3 components, 6 placed) | 3.4 | 51k | 27 | 108 | 5.8 |
| library (v3: 2 components, 8 placed; parametric stepped wings) | 3.8 | 87k | 26 | 110 | 6.8 |
| (v1, kit only: depot / mill) | 2.7 / 3.5 | 55k / 82k | 12 / 18 | 94 / 103 | 3.4 / 3.1 |
| (shipyard, for scale) | 10.9 | 291k | 59 | 169 | 5.9 |

Budget per colony building: about 150k triangles and 7 MB fetched on the phone tier (components dominate: keep their
`--tris` near the pilots' and their textures at 1024 unless the part is the hero); the hull at 4096 px desktop.

## Component catalogue (`assets/parts-colony/`, placed as `colony:<name>`)

Made (pilots, 2026-10-06). Sizes are the ingested bbox (w x h x d, part frame: +Y up, front +Z); tris after cleaning.

| part | size (m) | tris | source image | fal jobs | used by |
|---|---|---|---|---|---|
| sphereTank | 26.5 x 25.837 x 26.546 | 22,895 | `images/buildings/components/sphereTank.jpg` | 01a110ea-6b9f-79b1-baee-bab0dcc60d7d (image), 01a110eb-e9f8-7a33-be46-049e2c749aa8 (mesh) | deuterium_depot |
| plantHouse | 8.504 x 7.8 x 16.88 | 7,383 | `images/buildings/components/plantHouse.jpg` | 01a110ea-6cb6-7453-b1bf-a33d888b0954 (image), 01a110eb-eb05-7230-865d-24d8639b900c (mesh) | deuterium_depot |
| manifoldSkid | 5.826 x 4.474 x 13 | 16,813 | `images/buildings/components/manifoldSkid.jpg` | 01a110ea-6d8b-7e23-8a51-34348e554249 (image), 01a110eb-ec06-7b52-a3de-54b818c03716 (mesh) | deuterium_depot |
| filterBank | 2.922 x 4.299 x 6.5 | 11,923 | `images/buildings/components/filterBank.jpg` | 01a110ea-6e5d-7ed3-b121-8b644e0a4cb5 (image), 01a110eb-ece7-7563-91c2-46b532dabd55 (mesh) | deuterium_depot |
| blastFurnace | 27.456 x 60 x 29.342 | 29,137 | `images/buildings/components/blastFurnace.jpg` | 01a110ea-6f2f-78b2-ba37-48609d9e64d4 (image), 01a110eb-ee16-7f12-ab38-0addcf0f67fb (mesh) | steel_mill |
| bandedStack | 12.666 x 46 x 13.2 | 8,959 | `images/buildings/components/bandedStack.jpg` | 01a110ea-7011-7942-9813-46e1fcb46b82 (image), 01a110eb-eee5-7f93-9e32-3b89a6d7f2a9 (mesh) | steel_mill |
| pourBay | 18.98 x 15.542 x 26 | 25,842 | `images/buildings/components/pourBay.jpg` | 01a110ea-70fa-7621-b809-e7a52fa8a855 (image), 01a110eb-efcf-7903-b342-56b00d4154c3 (mesh) | steel_mill |
| skipGallery | 6 x 46 x 28 | 12,915 | `images/buildings/components/skipGallery.jpg` | 01a110ea-71ea-7212-b86a-5cc9123f8168 (image), 01a110eb-f0e4-71e3-a9c4-f713360bc9b5 (mesh) | steel_mill |
| shedSegment | 28 x 24 x 36 | 7,534 | `images/buildings/components/shedSegment.jpg` | 01a110ea-72c4-7de3-b15f-4df2db490330 (image), 01a110eb-f1ca-7292-ae3e-72318ec0b68c (mesh) | steel_mill |
| officeTower | 20.856 x 50 x 21.566 | 8,997 | `images/buildings/components/officeTower.jpg` | 01a11116-f7e4-7461-b783-172e835fa7cb (image), 01a11118-4c90-7262-97e2-a7578983f3d9 (mesh) | trade_center |
| skyBridge | 11.074 x 11.349 x 42 | 5,997 | `images/buildings/components/skyBridge.jpg` | 01a11116-f8b8-7921-b06e-771343dd232b (image), 01a11118-4d6f-71f0-b841-2a52b77df730 (mesh) | trade_center |
| marketArcade | 28 x 10.088 x 23.236 | 8,994 | `images/buildings/components/marketArcade.jpg` | 01a11118-30b7-7f60-bdd7-d2b815c57420 (image), 01a1111d-e0d9-76f1-8db4-10a0c07f3d8d (mesh) | trade_center |
| loadingHall | 17.794 x 9.635 x 28 | 5,991 | `images/buildings/components/loadingHall.jpg` | 01a11116-fa88-71f3-9cf6-609880351ed2 (image), 01a11118-4e4e-72c1-aad3-93794c4f24de (mesh) | trade_center |
| adminWing | 17.68 x 14.533 x 36 | 5,997 | `images/buildings/components/adminWing.jpg` | 01a11117-3aba-7f63-b887-44e5e564ad53 (image), 01a11118-94d7-7c33-9178-7e71f80e6261 (mesh) | infrastructure |
| hubDrum | 26 x 26.586 x 27.576 | 8,000 | `images/buildings/components/hubDrum.jpg` | 01a11117-3b85-7011-9fdf-da7093340eb9 (image), 01a11118-95bd-7ae1-b944-31f8dd80326b (mesh) | infrastructure |
| waterTower | 9.362 x 24 x 10.27 | 5,996 | `images/buildings/components/waterTower.jpg` | 01a11118-93f8-7880-b679-33e3a5ecbdbc (image), 01a1111d-e1ba-7662-a168-885cc9ce8a41 (mesh) | infrastructure |
| vesselSkid | 4.432 x 6.107 x 13 | 5,997 | `images/buildings/components/vesselSkid.jpg` | 01a11117-3d36-7022-a35b-9e1ae0613d41 (image), 01a11118-967a-71d3-9238-928487c5fe98 (mesh) | infrastructure |
| curvedTerrace | 20.026 x 32 x 55.09 | 11,989 | `images/buildings/components/curvedTerrace2.jpg` (v3; v2: `curvedTerrace.jpg`) | 01a11221-9240-7340-a4fb-8c80cd077621 (image, v3), 01a11222-44ae-7032-a204-5115716563b5 (mesh, v3) | residence |
| podiumSegment | 14.866 x 12.454 x 40 | 5,997 | `images/buildings/components/podiumSegment.jpg` | 01a11117-66e0-7873-876f-def937b9d399 (image), 01a1111a-753f-7842-923c-58e3b0a19417 (mesh) | residence |
| facetedWing | 40 x 15.689 x 16.944 | 6,999 | `images/buildings/components/facetedWing.jpg` | 01a11117-c648-7f32-b6af-b0821cba9c79 (image), 01a1111a-ccd8-7571-ad7c-3a652a641508 (mesh) | university |
| atriumHall | 34 x 17.754 x 34.024 | 9,997 | `images/buildings/components/atriumHall.jpg` | 01a11117-c71c-7e72-9ea1-dae058e2ad48 (image), 01a1111a-7618-79c1-9a7a-911822c58e3b (mesh) | university |
| obsDome | 10 x 9.195 x 9.908 | 4,406 | `images/buildings/components/obsDome.jpg` | 01a11117-c7fc-7240-bef1-f5557f083dec (image), 01a1111a-f27d-76b3-96df-8f45c4affc75 (mesh) | university |
| portalTower | 24 x 46 x 28 | 9,994 | `images/buildings/components/portalTower.jpg` | 01a11117-c90d-7301-9057-1eefb4e34372 (image), 01a1111a-f36f-7522-b9b4-439a0670bf5e (mesh) | library |
| steppedWing | 40 x 31.79 x 39.958 | 6,998 | `images/buildings/components/steppedWing.jpg` | 01a11117-c9ec-7361-8300-2212cdef8d62 (image), 01a1111a-f443-74c1-a70a-504b1c3452f9 (mesh) | library (v2; v3 builds the wings parametric: crisper terraces) |
| monumentPylon | 3.934 x 10 x 3.924 | 1,499 | `images/buildings/components/monumentPylon.jpg` | 01a11117-cae4-7941-95c3-d2db4439d2b0 (image), 01a1111a-f557-7911-9a04-2db398907478 (mesh) | library |
| distColumn | 6.8 x 40 x 5.8 | 11,787 | `images/buildings/components/distColumn.jpg` | 01a11117-5a2f-7b93-8e7c-5315b36c54fb (image), 01a11118-543c-7311-a42a-7a573d6ec09d (mesh) | refinery |
| htankSkid | 5.512 x 6.679 x 13 | 8,000 | `images/buildings/components/htankSkid.jpg` | 01a11117-5b08-7a33-904d-5291f6538c88 (image), 01a11118-7267-7601-bb84-49400e1aefa2 (mesh) | refinery |
| processVessel | 17.45 x 32 x 17.72 | 13,907 | `images/buildings/components/processVessel.jpg` | 01a11117-5bf7-75d0-85fc-d761500f3d9b (image), 01a11119-222e-7bc3-8073-8c07e3a3d6df (mesh) | processing_plant |
| bandedLowTank | 28 x 16.083 x 27.566 | 10,971 | `images/buildings/components/bandedLowTank.jpg` | 01a11117-5ccb-70c2-97a7-f78304b0e452 (image), 01a11119-2307-7a53-be29-1912ac5abf49 (mesh) | processing_plant |
| plantBlock | 15.806 x 13.971 x 26 | 9,999 | `images/buildings/components/plantBlock.jpg` | 01a11117-5da0-7c73-9d92-c4e78843d6d1 (image), 01a11119-23cc-7993-8c12-6686126ea63e (mesh) | processing_plant |
| bottleSkid | 2.988 x 4.601 x 7 | 6,000 | `images/buildings/components/bottleSkid.jpg` | 01a11117-5e67-7581-b0ad-02a13ff009ba (image), 01a11119-24b4-7ba0-b71c-5096e898e4d7 (mesh) | processing_plant |
| floatTank | 28.956 x 17.255 x 29 | 8,495 | `images/buildings/components/floatTank.jpg` | 01a11117-5f32-7593-8386-1f6bee77f9c7 (image), 01a11119-4bec-79d3-b952-8a0c1818311c (mesh) | oil_tanks |
| roofMonitor | 10 x 5.5 x 40 | 4,521 | `images/buildings/components/roofMonitor.jpg` | 01a11117-5ff2-7cd2-8778-e15677a13471 (image), 01a11119-4cb1-7ee0-bf1f-87ee25c798a0 (mesh) | silicon_foundry |
| crystalReactor | 15.066 x 12 x 14.53 | 10,737 | `images/buildings/components/crystalReactor.jpg` | 01a11117-60b6-7212-9213-1301a79db914 (image), 01a11119-8d9e-7f51-b315-09b07c14f65a (mesh) | silicon_foundry |
| overheadCrane | 13.364 x 8.948 x 32 | 9,695 | `images/buildings/components/overheadCrane.jpg` | 01a11119-8f2d-79b3-9a21-a05e89b91633 (image), 01a1111d-32d8-7b12-8093-7ebca85b3329 (mesh) | steel_depot |
| beamStack | 3.6 x 2.6 x 12 | 2,996 | `images/buildings/components/beamStack.jpg` | 01a11119-8ffd-7132-9bbd-531284b4b26e (image), 01a1111d-33c9-7c81-94cc-58f977665cc5 (mesh) | steel_depot |
| portalColumn | 6.304 x 22 x 7.198 | 6,000 | `images/buildings/components/portalColumn.jpg` | 01a11117-6354-7aa0-9fbf-d4b3e9f9508d (image), 01a11119-8e65-79e1-bf02-2ac79d627fa5 (mesh) | steel_depot |
| vaultBay | 9 x 30 x 12.5 | 8,998 | `images/buildings/components/vaultBay.jpg` | 01a11117-ca3e-7df0-9b61-3ecabe52943f (image), 01a1111a-d2d9-7b61-b4b9-60f2216dff23 (mesh) | silicon_depot |
| rackBay | 9 x 30 x 12.5 | 13,995 | `images/buildings/components/rackBay.jpg` | 01a11117-cb25-7f73-a725-e75545f565c3 (image), 01a1111a-d3d7-7183-b35b-6f9c1bca22f0 (mesh) | silicon_depot |
| entrancePorch | 8 x 5.186 x 8.932 | 5,997 | `images/buildings/components/entrancePorch.jpg` | 01a11117-cc19-7e43-a3e7-73463c294731 (image), 01a1111a-d4a2-7312-a925-ca9c06899f81 (mesh) | silicon_depot |
| armouredHangar | 34 x 11 x 30 | 11,998 | `images/buildings/components/armouredHangar.jpg` | 01a11117-cce0-79d3-9c2a-4b2b9bad5851 (image), 01a1111a-d581-7070-aa6e-25208b30f5f3 (mesh) | military_base |
| guardTower | 8.722 x 17 x 8.154 | 3,999 | `images/buildings/components/guardTower.jpg` | 01a11117-cda8-7321-9a74-1a49db54a3c4 (image), 01a1111b-7305-7930-b1bb-1322a8794ce1 (mesh) | military_base |
| wallSegment | 6.652 x 6.647 x 24 | 1,998 | `images/buildings/components/wallSegment.jpg` | 01a1111b-75bc-79c2-9cc9-3b01e5063f2e (image), 01a1111c-c924-7b61-9f31-10e2443e25b2 (mesh) | military_base |
| gateHouse | 9.076 x 8.999 x 32 | 8,995 | `images/buildings/components/gateHouse.jpg` | 01a11117-d02d-7240-af01-a2eb8acefe1b (image), 01a1111b-74d1-7451-ab7d-ee8b7c6b226a (mesh) | military_base |
| commandBunker | 29.902 x 19.099 x 30 | 13,703 | `images/buildings/components/commandBunker.jpg` | 01a11117-cf52-7d13-bdbf-95cb831fccf8 (image), 01a1111b-73eb-7ba2-8397-30181c06171b (mesh) | military_base |
| dishMount | 26.902 x 32.941 x 33 | 25,601 | `images/buildings/components/dishMount.jpg` | 01a11117-d1e0-7360-b292-6d7fc8dad8f6 (image), 01a1111b-c062-7fe2-9894-955c96fc4b76 (mesh) | radio_telescope |
| ringModule | 26.192 x 24.587 x 40 | 7,998 | `images/buildings/components/ringModule.jpg` | 01a11117-d2a0-7df0-aef0-3732b56ffae1 (image), 01a1111b-c16b-7160-8827-fdfd7f074abd (mesh) | transmitter |
| ringSegment | 20 x 14 x 104 | 4,500 | `images/buildings/components/ringSegment.jpg` | 01a11117-d375-7160-9ef7-59ec4081f121 (image), 01a1111b-c25d-7b43-9124-44bc2c286954 (mesh) | transmitter |
| solarWing | 15.948 x 17.749 x 34 | 3,996 | `images/buildings/components/solarWing.jpg` | 01a11117-d458-7500-bd18-e92d36b110e2 (image), 01a1111b-c341-7ac2-bbad-dae3479c85a6 (mesh) | transmitter |
| dockingHub | 25.49 x 25.485 x 26 | 7,999 | `images/buildings/components/dockingHub.jpg` | 01a11117-d51a-7873-adf4-ed2dd6513e33 (image), 01a1111b-c419-7202-b00f-48ce7e46b590 (mesh) | transmitter |

Orientation notes (part frame): plantHouse's door is on its +X long face, pipe stubs at +Z; pourBay opens to +X with
its runner running out along +X; shedSegment's windowed long face is +X, gables at +-Z, segments abut along Z;
skipGallery climbs from its drive house at +Z (low) to -Z (high); blastFurnace's square base is axis-aligned.
Hot texels (`--hot`): pourBay (runner), blastFurnace (tuyere band, frame lamps), bandedStack and plantHouse (lamps).

Production / storage batch (refinery, processing_plant, oil_tanks, silicon_foundry, steel_depot; 2026-10-06),
orientation notes (part frame): distColumn's vapour line is on -X, ingested at 0.65 in plan (`--size 6.8,40,5.8`: the
concept's columns are slimmer than the image's); htankSkid's axis is Z with its railed platform at +Z; plantBlock's
cargo door is on its +X long face (heading 0 faces +X); floatTank's stair tower and gauge hut sit about 56 degrees from
+Z toward +X; roofMonitor came out long along X and was turned (`--rot 0,90,0`) so it runs along Z with its louvres on
+X, abut or stretch it along Z; crystalReactor's glass reconstructed opaque, so the building lights it with violet glow
boxes inside its open-mullion bay; overheadCrane spans along Z (scale its span with `scale=[1, 1, k]`, part axes x, y up, z; v2 wrote [1, k, 1], which made it taller: the steel depot
uses 1.5 for a 48 m bay); beamStack runs along Z, stack it at 2.62 m; portalColumn's lattice bay is on +X.

Civic / science batch (trade_center, infrastructure, residence, university, library; 2026-10-06), orientation notes
(part frame): the image's main face came out on the part's +X for officeTower (lit strips on +X and +Z), loadingHall
(roller doors on its +X long face), curvedTerrace (balconies on +X, rounded end tower at +Z; plan is a gentle S),
podiumSegment (entrances on +X), atriumHall (canopy on +X) and portalTower (slot face on +X): turn them with heading 270
to face +Z. facetedWing, steppedWing and marketArcade came out long along X with their front on +Z (heading 0).
Hot texels (`--hot` 0.6-0.8): every one of these, for the lit windows, slots and lamps. `component()` takes a per-axis
`scale=[x, y, z]` in the part frame (x, y = UP, z; assemble_place.py `Matrix.Diagonal` after the +Y basis) as well as a
number: the university stretches facetedWing to [0.8, 1.3, 1.35] (taller and deeper). v2's notes called the axes
"length, depth, height": wrong, the second is the height (the silicon foundry's [1, 1, 0.75] shortened its monitors
instead of lowering them, the steel depot's crane [1, 1.5, 1] grew 1.5x taller instead of spanning wider).


Storage / military / science / orbital batch (silicon_depot, military_base, radio_telescope, transmitter; 2026-10-06),
orientation notes (part frame): the image's front came out on +X for every one of these (vaultBay / rackBay doors,
entrancePorch ramp, armouredHangar opening, commandBunker entrance, gateHouse gate, wallSegment door face, dishMount's
dish, dockingHub's port, ringSegment's blue edge): heading -90 turns it to +Z. vaultBay / rackBay were ingested at
`--size 9,30,12.5` (12.5 m bay pitch; Tripo gave them 17.5 m faces) and armouredHangar at `--size 34,11,30`;
wallSegment and ringSegment run along Z and abut along Z (ringSegment `--size 20,14,104`: the image's section came out
square); ringModule runs along Z with its thruster quad at +Z; solarWing runs along Z with its boom at -Z and its panels
rolled ~45 degrees about Z (transmitter.py places it with `B.R.place` and a roll); dishMount's azimuth drum is centred at
part x = -3.45 (the dish overhangs +X; radio_telescope.py offsets it). The dish and the bays baked a mid grey-tan that read
dark and warm in the dusk studio (v2 lifted them per material, the dish by 2.5x; v3 normalises every part at ingest,
"Paint calibration"). Hot texels: all at 0.8 except armouredHangar (0.93: at 0.8 its amber-lit interior wall glowed as a flat
orange panel) and dockingHub (0.75). Not meshed: an armoured car image (the yard instances the fleet's V-31 instead).

Planned (decomposition of the other concepts; make each once, reuse across the buildings listed). Made parts to reuse
first: plantHouse (oil_tanks, refinery, processing_plant), manifoldSkid / filterBank (every storage and production
building), bandedStack (silicon_foundry, refinery), shedSegment (steel_depot, silicon_foundry with a new roof),
skipGallery (steel_depot), pourBay's crane (steel_depot: or a new overheadCrane).

| component | what | buildings |
|---|---|---|
| processVessel | 6 x 22 m banded process vessel with head and pipe collar | processing_plant (x3), refinery |
| distColumn | 3-4 m x 30-45 m column with platforms and caged ladder | refinery (x3) |
| floatTank | 28 x 14 m floating-roof tank with wind girder and stair | oil_tanks (x3), processing_plant (low tank, scaled) |
| htankSkid | 3.5 x 14 m capsule tank on saddles with valves | refinery, processing_plant, deuterium_depot |
| pumpSkid / valveSkid | pump and valve skids 3-6 m | every storage and production building |
| overheadCrane | amber bridge crane, 20-30 m span | steel_mill, steel_depot |
| beamStack | stacked steel sections on dunnage | steel_depot, steel_mill |
| crystalReactor | violet-lit reactor vessel behind glazing | silicon_foundry, silicon_depot |
| rackBay | dark rack bay with containers | silicon_depot |
| waterTower | elevated tank on a frame | infrastructure |
| obsDome | 8-10 m observatory dome on a drum | university (x2) |
| dishMount | large dish on an alt-az mount; small dish variants | radio_telescope, military_base, transmitter |
| armouredHangar | 30 x 20 m armoured vehicle hangar | military_base (x2) |
| guardTower | corner tower with lamps | military_base (x4) |
| wallSegment | blast wall segment with buttress | military_base, oil_tanks (bund) |
| balconyBay | apartment bay with balcony and planter | residence, trade_center |
| skyBridge | glazed sky bridge segment | trade_center |
| atriumRoof | glazed pyramid / barrel atrium | university, infrastructure, trade_center |
| monumentPylon | stepped monumental pylon with lit slot | library, university |
| solarWing | orbital solar array wing | transmitter (x6), spaceport |
| ringModule | hexagon ring corner module | transmitter (x6) |

## Gotchas (pilots)

- `lib.BAKE` grime tuned for ships darkens building walls framed by proud gunmetal: bkit sets `grime` (0.45, 0.88,
  0.6). Keep it.
- The ship studio's key comes from 85 degrees round the camera; buildings set `sunaz` / `sunel` so the face the
  concept shows lit is lit (mill: the long +X face, key at 42 degrees).
- `bkit` must import `bpy` before `bmesh`; a building script imports only `bkit` (and `math`).
- `colony_build.py` installs into `assets/buildings/` and `src/buildings/`: a throwaway test building leaves files
  there; delete them.
- Bake times on 4 CPUs: 2048 px x 6 samples ~20 s, 4096 x 10 ~2.5 min; the full chain ~45 s / ~3.5 min.
