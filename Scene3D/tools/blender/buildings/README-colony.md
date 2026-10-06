# Colony buildings: the recipe (one building in about 1-2 h)

The 16 colony buildings of `style-library/styles/cqs-fleet/briefs/buildings.md` are built one way: the approved concept
(correction 35) is the target; a 4K turnaround fixes proportions and layout; the building's distinctive pieces become
**fal-made components** (an isolated component image, then image-to-3D of that component alone, cleaned and sized in
Blender into a reusable kit part); everything generic comes from the shared parametric kit (`bkit.py`, see
`README-bkit.md`); the building script composes both; one generic runtime pattern shows it. Never generate a
whole-building mesh (the user, 2026-10-06: "use the fal 3d model to create small individual components, and then
simplify and compose them in blender as opposed to generating the full 3d model"); a whole-building mesh, if one
exists, is only a measuring reference.

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
| C | components: image, mesh, ingest (reuse the catalogue first) | nano-banana-pro/edit, `tripo3d/h3.1/image-to-3d`, `component.py` | 15-40 min |
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
   - The runtime lifts every `colony_*` material's albedo by 1.25 (`colony.js`): Tripo's paint reads a step darker
     than the concept's off-white once the detail layer and worn finish are on.
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

## Phone budget (measured, phone tier, `tools/phone-check.mjs`)

| view | fetched MB | tris | textures MB | heap + GPU MB | ready s |
|---|---|---|---|---|---|
| deuterium_depot (v2: 4 components) | 5.0 | 120k | 27 | 112 | 3.8 |
| steel_mill (v2: 6 components) | 6.3 | 127k | 43 | 129 | 4.1 |
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

Orientation notes (part frame): plantHouse's door is on its +X long face, pipe stubs at +Z; pourBay opens to +X with
its runner running out along +X; shedSegment's windowed long face is +X, gables at +-Z, segments abut along Z;
skipGallery climbs from its drive house at +Z (low) to -Z (high); blastFurnace's square base is axis-aligned.
Hot texels (`--hot`): pourBay (runner), blastFurnace (tuyere band, frame lamps), bandedStack and plantHouse (lamps).

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
