# Orbital Fleet — 3D scene for the Conquer-Space reboot

A real-time three.js scene of the reboot's orbital ships: fighter, corvette,
civil ship (freighter / troop transport), destroyer and the fleet carrier, in
orbit above a planet, plus the first ground unit (the V-31 vehicle) and two buildings (the planetside
shipyard and the SP-3 orbital spaceport, which also orbits near the fleet). Every hull, texture and tiling material was generated
with fal.ai; three.js plays Blender's role (import, clean-up, materials,
lighting, rendering). All ships share one scale derived from the game's own
unit data.

All designs are new work for the reboot. None of the original game's artwork
or models (`Artwork/`, `Html/Design/pack/units/`, `*.blend`) was used, opened
or referenced. Only the class roster and the gameplay stats come from the
original code.

## Running it

No build step. The page loads three.js from the jsDelivr CDN through an import map.

```sh
cd Scene3D
node tools/serve.mjs 8080      # any static server works
# open http://127.0.0.1:8080/
```

| View | URL | What it shows |
| --- | --- | --- |
| Fleet in orbit | `#fleet` (default), `?mode=fleet&shot=hero\|high\|stern\|spaceport` | Carrier group above the planet: parked ships in the carrier's open bays (21 fighters, 2 corvettes, a destroyer and a cargo ship; with the 3 fighters of the launch cycle that is exactly its 50-slot legal load), a launch and recovery cycle through the bow mouth, escorts, fighter patrols, the logistics convoy, and the SP-3 spaceport 3 km off the starboard bow (yawed 30 degrees so its open berth faces the group; `shot=spaceport` frames it from 2 km). Ground units never appear here |
| Scale lineup | `#lineup`, close-up `?lineup=small#lineup` | Scale chart: sterns aligned on a metre ruler (ticks every 10 m to 100 m, then every 100 m), one row per class (the 7 m V-31 vehicle in the front row, beside the slot cube and the crew member: "ground unit, true size") labelled by callouts on the stern side, a 1-slot reference cube, a 1.8 m crew member, a neutral 10 m / 100 m grid, and an optional 50-fighter hangar load (`hangar=1`). The default view frames the whole 900 m chart, with a detail box in the empty grid that shows the `lineup=small` framing (a second render of the same scene); `lineup=small` frames only the small ships, the cube and the crew member, like the enlarged inset of a technical drawing (also linked from the toggles bar and the detail box) |
| Ship studio | `?mode=ship&ship=carrier&az=35&el=18&dist=1`, `#vehicle` | One ship or ground unit, framed for inspection (`fighter`, `corvette`, `freighter`, `destroyer`, `carrier`, `vehicle`; `variant=troops`; the carrier's hangar is parked by default (`parked=0` empties it, `parked=1` aims the camera at it); `debug=1` shows axes, a metre grid, engine/light anchors and the hangar box). The camera fits the hull's own silhouette (sampled mesh vertices), not its bounding box. Stills are shot over the planet (`planet=0` for black; the interactive studio adds it with `planet`), and the studio key is placed relative to the camera, 85 degrees round from its azimuth and 30 degrees up, so every view splits into a lit and a shadowed plane (`sunaz=`/`sunel=` override, in degrees) |
| Building view | `?mode=building&building=<id>`, `#<id>` (shipyard, spaceport, and the colony buildings as they are built: deuterium_depot, steel_mill; `?mode=ship&ship=spaceport` is an alias) | One building at true size in the studio rig, dimmed by the building's own `studio` hint (the shipyard's dusk: exposure 1.25, a lower key, lamps x1.3); camera from 35 / 30 degrees (`az=`, `el=`), fitted to the silhouette (`dist=` scales it), or `focus=x,y,z&dist=m` for a close-up on a point of the building (metres, its own frame). The shipyard shows the real DD-12 cut back to its build state in the berth; the spaceport the real CV-50 under construction and four docked CT-4s (drives cold) |
| Check | `?mode=check` | Builds every ship and the vehicle and reports envelopes, slots and hangar fits (used by `tools/scale-check.mjs`) |

The view switch in the page header (Fleet in orbit, Scale lineup, Vehicle, and a Buildings menu listing all 18 buildings in the brief's groups: production, storage, civic, science, military, megaproject; `src/buildings/catalog.js`) uses the `#` routes. Buildings not built yet are listed as planned.

Colony buildings (`briefs/buildings.md`, 16 of them) share one runtime pattern: `src/buildings/colony.js` (`colonyBuilding({ id, DATA, meta, studio })`) gives each its GLB, light concept paint, the `building` finish preset, the fleet light language from its generated light block (amber pins, door lamps, jamb slits, lit windows, hot glow, floods, red obstruction lights) and a dusk studio with a front-left key (`studio.sunaz` / `sunel`) and the concepts' slate backdrop; orbital ones get a space backdrop. They are built by `tools/blender/buildings/colony_build.py` on the shared kit `bkit.py` and compared with their concepts by `tools/buildings/compare.mjs` (recipe: `tools/blender/buildings/README-colony.md`).

Registries (`src/ships/index.js`): `ORDER` (the five fleet classes: fleet scene, hangar loads, scale check), `GROUND`
(ground units: ship studio and lineup only, never in the orbital fleet) and `BUILDINGS` (id -> module path and
`fleet: true` when the fleet scene places it). A building module exports `meta`, a `load()` or `preload()` hook (its GLB
and the real ship GLBs it reuses), `build(palette, { library })` and an optional `studio` hint; `buildBuilding()` builds
it at true size (never slot-normalised). `src/lib/scale.js` `CLASSES` has an entry for each (size null).

Controls: drag to orbit, scroll to zoom, double-click a ship to fly to it and
follow it. The spec sheet shows each ship's dimensions, crew, hangar loads and
its fal concept art (in-orbit concept and the image-to-3D input). In the interactive
fleet view the lens is shifted (an off-axis projection, the camera pose is unchanged) so
the named shot's composition sits centred in the area left clear by the title, the class
list, the spec sheet and the toggles; stills use the plain lens.

Look-dev overrides: `?livery=none|dark|civil`, `?exposure=`, `?fov=`, `&t=` (freeze time),
`?cam=x,y,z&target=x,y,z` (fleet: a free camera in the carrier's frame, metres), `?level=deg`
(fleet: the most horizon tilt a shot keeps; each named shot sets its own lens and tilt),
`?planetss=1..3` (planet supersampling; stills default to 2), `?envhide=surface,clouds,atmosphere`.

Ship lights (`src/lib/lightscape.js`, drawn by `src/lib/effects.js`): each module's `lightscape`
field generates the small lights that make a dark hull read as crewed. The hierarchy follows
the concept art: short, hard-edged amber slits at block corners and in real recesses carry the
look (a crisp bar with a faint warm spill, not a bloomed tube); sparse amber pins mark corners;
authored runs, rings, chasers and beacons mark doors, drives and docking ports; grilles and
louvres stay dark. Far off, pins thin out first and the corner slits are the last lights left.

The launch cycle (`src/lib/launch.js`) is one closed track flown by three fighters, a
third of its 105 s period apart: a deck lift in the enclosed bow section raises the
fighter onto the starboard half of the centreline lane, the deck's linear catapult
throws it out of the bow mouth with its drive cold, it lights the drive ~140 m clear of
the bow, climbs away to starboard, flies a 700 m-radius teardrop (about 3 g) and glides
back in, unpowered, along the port half of the lane to the recovery lift. Fighters are
only ever hidden while they are below the deck, so nothing appears or vanishes in view.

## Asset pipeline (fal.ai)

Source of truth for every prompt and parameter: `pipeline/fal-pipeline.json`.
The pipeline follows the usual "image model → image-to-3D → optimise → PBR
materials → assemble, light and render" flow, checking renders at every step.
Each stage ran as a small multi-agent workflow: generators, independent judges
(originality, realism, scale, reconstruction suitability) and a fix loop.

1. **Concept art** — `fal-ai/nano-banana-pro` (art bible) and
   `fal-ai/nano-banana-pro/edit` (every ship, with the bible and approved
   sister ships as references). Per ship: an isolated three-quarter studio
   image on light grey (the image-to-3D input), an in-orbit beauty shot in the
   dark operational livery (spec-sheet art), and a 4K six-view orthographic
   turnaround sheet cropped into front / port / stern / starboard / top /
   bottom views.
   - The first fighter read like a franchise fighter and was redesigned
     (a faceted pod with flank railguns, no wings).
   - The destroyer was redesigned around a massive spinal railgun, and the
     carrier around an open-flank through-deck hangar so its bay (and ships
     parked in it) can be seen from ordinary three-quarter angles.
   - A scale judge measured doors, windows, containers and weapons in every
     concept against the ship's final length (2 m doors, ~1 m windows, 20-ft
     containers on every hull), so the shared details read as a scale reference.
2. **Meshes** — `tripo3d/h3.1/multiview-to-3d` (front, port, stern,
   starboard views; detailed geometry and textures, PBR). Chosen in two
   bake-offs, each judged by three independent reviewers (geometry,
   texture/PBR, production):
   - fighter: `tripo3d/p2/image-to-3d` beat `fal-ai/hunyuan-3d/v3.1/pro` 2-1
     (clean hull numbers, CAD-like topology);
   - fighter + destroyer pilot: H3.1 multiview ranked first on both
     (Borda 10 and 12) ahead of H3.1 single-view, Hunyuan3D multiview and the
     P2 meshes — crisper facets, legible non-mirrored hull numbers, a real
     stern and belly instead of hallucinated ones.
   - The carrier's bays were made see-through in its turnaround views so the
     reconstruction keeps them open; the destroyer's hull number was
     re-projected onto its texture, and so was the carrier's: both flanks now
     carry the same stencil "CV-50" (the reconstruction had put a different,
     rounded number on the starboard flank and an offset relief of one under
     the port paint; the relief was flattened, since paint has none).
3. **Optimise** — `tools/ingest-fal.mjs` downloads results; meshes go through
   `tools/optimize-glb.mjs` (weld, simplify to the class budget, WebP textures,
   meshopt). Raw GLBs stay in `assets/ships/raw/` (gitignored).
4. **Materials** — `fal-ai/patina/material` (all five maps, 2× upscale):
   hull, orange, armor, ceramic, foil, deck, radiator in `assets/materials/`
   with `manifest.json`. On the generated hulls PATINA is a tri-planar detail
   layer (normal, roughness, cavity) at one absolute plating size (6 m per
   repeat) on every ship; inside the carrier's hangar the `deck` set takes over
   (tread plates, deep seams, plate-to-plate tone, and the same set 7.3x larger for
   deck-panel tone that still reads from a kilometre away); the full sets texture
   scene-built parts.
5. **Assemble, light, render** — `src/lib/glbship.js` orients and sizes each
   GLB, repaints it in the dark matte operational livery (`src/lib/livery.js`;
   the generation images stay light because light paint reconstructs better),
   adds the PATINA layer, nozzle glows, nav lights and anchors. One hard sun,
   an environment map of black space plus the planet, bloom only on the sun,
   drive bells and lights; drives are a glowing bell with a short soft plume: a small
   white-hot throat, a bell wall that stays dark except for a graded glow near the throat
   (the lining is drawn on its inner face only), and a narrow tapered column 1.5-2.5 bell
   radii long in profile that fades to a hint when seen end-on, so no view shows a lit disc
   or a beam. The star
   field is capped for an exposure set on sunlit hulls (about 21 sRGB at most), so only a
   sparse scatter of faint points shows, as in a real photograph.
   The planet (`src/env/planet.js`, `atmosphere.js`) is procedural and at true scale: an
   Earth-sized globe with the fleet 400 km up, so the ground reads hundreds of km below
   and a camera move of a kilometre changes nothing on it. Terrain (with a 3-10 km drainage
   network and coastal shelves of varying width), ocean glint (Cox-Munk roughness: calm water
   and surfactant slicks glint silver-bright) and a cloud deck (weather systems, mottled decks
   with soft closed cells, fair-weather cumulus fields casting their shadows on the ground)
   are one ray-cast shader whose noise octaves fade out below the pixel; a
   single-scattering atmosphere with Earth's scale heights draws the thin bright limb.
   The fleet shots are lit by the sun 50-62 degrees off the lens axis (never from behind the
   camera), so it rakes the hulls and leaves deep shadows.
   The carrier's hangar floodlights (neutral white, ~5,800 K) cast no shadow maps, so they are light-linked
   to the hangar volume on its own hull (`interiorLightGate`): they light the deck
   and the parked ships, never the hull outside or under the deck. Each lamp throws a pool
   that falls off toward the bay backs; emissive light strips on the bay ceilings and the
   frame posts show where the light comes from. The deck carries non-slot equipment at
   human scale (`src/lib/park.js`): painted parking boxes round every parked ship and the
   launch-lane edges, stacks of 20-ft containers and deck tractors with cart trains. Outside,
   rows of 1 m lit ports every 6 m along the upper flank band and the island tiers, and
   0.4 m amber running lights every 25 m along the deck edge and the sponsons, carry the
   900 m scale into full-ship framings.

Costs (fal list prices): about 58 nano-banana-pro images (13 of them 4K
turnaround sheets) ≈ $10.70, 6 Tripo P2 models $7.20 (superseded), 11 Tripo
H3.1 models $6.60, 3 Hunyuan3D 3.1 Pro models ≈ $1.90, 11 PATINA sets ≈ $1.20 —
about $27.50 for the first build. The fleet-scale re-draw (v4) added about $10.50 and
the true-scale detail round (v5: targeted detail edits, new turnarounds, 5 Tripo H3.1
meshes, 3 PATINA detail tiles for the carrier) about $15.70, and the door and container
repair (v6) about $0.70: about $55. The remodel (v7, below) added two fal parts kits
(24 parts, about $19.50), a clean corvette blueprint (about $3) and three worn-finish
PATINA sets (about $0.35): about **$78** in total.

## Remodel (v7): hard-surface hulls in Blender

Image-to-3D reconstructions average fine detail into soft lumps, so every hull was
rebuilt as clean hard-surface geometry in headless Blender (the `bpy` 5.0 module), with
the fal mesh, concept and turnaround used only as the blueprint:

1. `tools/blender/hulls/measure.py` puts the Tripo mesh in the ship frame and slices it
   (sections, height maps, silhouettes); `compare.py` scores the model against it (IoU).
2. `<ship>.py` builds the hull parametrically: lofted stations, planar facets, exact
   boolean recesses (glazing, door bays, the carrier's hangar), 4-10 cm bevels with
   weighted normals. `<ship>_paint.py` paints it in texture space: light base paint for the
   runtime livery, plating seams, panel tone, AO grime, edge wear, crisp hull-number stencils.
3. Parts come from two kits, designed once and reused at the same metric size on every
   ship: `assets/parts-blender/` (procedural, `tools/blender/kit.py`: doors 1 x 2 m, 1 m
   ports and panes, rails, ladders, RCS, S/M/L turrets, drive bells S-XL with exact throat
   depths, railgun segments, containers) and `assets/parts/` (fal: nano-banana-pro concept,
   Tripo H3.1 image-to-3D; antennas, domes, PDC, missile pods, clamps).
   `tools/blender/assemble.py` snaps them onto the hull from a placement spec
   (`tools/blender/specs/<ship>-v3.json`) and exports one GLB with a `hull` node and
   `parts_*` nodes (`hullNodes` in the module, so the hangar test ignores the parts).
4. `<ship>_module.py` re-measures engines, lights and anchors on the result.

One command per ship: `tools/blender/hulls/build.sh <ship> <workdir>` (see
`tools/blender/hulls/README*.md`). Every envelope stayed within 0.5 % of the previous
one, so the scale model and the hangar loads are unchanged. Shading: a worn finish
(`src/lib/finish.js`, fal PATINA `hullWear`/`hullGrit`/`sootStreak`: two-scale plate tone,
roughness breakup, micro grit, drive soot) and screen-space AO contact shadows are on by
default (`?finish=off`, `?ao=0`).

Phones: the full scene holds ~2 GB of GPU textures, which mobile browsers kill. A lite
tier (`src/lib/device.js`, automatic on touch / low-memory devices, `?lite=1|0` to force)
loads phone copies of every GLB (see Phone budget), a lower pixel ratio and shadow map,
no AO, and widens the lens on portrait screens.

### Phone budget

Every view must load on a mid-range phone. Budget per view on the lite tier: retained JS
heap + GPU estimate (textures with mips + geometry buffers + render targets) **under
300 MB**, about 25 MB fetched, ready in seconds. Check before every publish:

```bash
node tools/build-artifact.mjs && node tools/phone-check.mjs   # every view, 390x844 DPR 3 touch, served through dist/files.json
```

How the phone tier stays inside it:

- **Load per view.** The default fleet view on a phone places the ships only; a building's
  assets load only when its own view (`#shipyard`, `#spaceport`) opens. Desktop keeps the
  spaceport in the fleet scene.
- **Two phone copies per ship** (`tools/build-artifact.mjs` via `tools/split-glb.mjs`):
  `.lite` (1024 px textures) for the subject of a ship studio, `.mini` (256 px, carrier
  512 px) for ships in a crowd: the fleet, the lineup, the carrier's parked load and the
  ships inside a building scene. `loadShips(ids, tier)` / `loadGLB(url, tier)` pick one;
  desktop always loads the full GLB.
- **Buildings**: one `.lite` copy, 512 px textures and the small dressing parts left out
  (`LITE_BUILDINGS`: shipyard ladders, rails, vents, workers 244k -> 180k tris; spaceport
  rails 266k -> 220k). The build fails if a drop moves the bbox the runtime frames on.
- **One GLB cache.** `loadGLB` caches per (url, tier); the spaceport's carrier and
  freighters and the shipyard's destroyer are the registry's own parsed GLBs. The
  spaceport's four docked freighters are one prototype instanced four times.
- **Decode once, keep nothing twice.** Base64 is decoded straight into bytes (no `atob`
  binary string), the parser and its GLB buffer are dropped after parse, and on phones each
  texture's decoded ImageBitmap is closed once it is on the GPU.
- **Clip in place.** The build-state cuts (shipyard DD-12, spaceport CV-50,
  `src/lib/clip.js`) keep meshes wholly in front of the cut as they are and grow the split
  ones in typed arrays.
- **Fail visibly.** A load error or a lost WebGL context shows a message with Reload and a
  lighter view (index.html `__fail`), never a white page.
- Not shipped: the parts kits (`assets/parts*`): nothing loads them at runtime; nor the PATINA
  maps the runtime does not fetch (only each set's `runtimeMaps` / `maps` from the manifest).

### Package size

One artifact version holds at most 256 MiB, 511 files, 15 MB per binary and 16 MB per text
file; the build fails past the first two. Artifact hosting does not serve `model/gltf-binary`,
so models travel as base64 text, but split (`tools/split-glb.mjs`) so the base64 carries as
little as possible and nothing twice:

- `<name>.glb.shared.b64.txt`: the geometry (meshopt buffers, bit-identical to the GLB) and the
  textures every tier uses unchanged, once for all tiers.
- `<name>.glb.b64.txt` (desktop), `.lite.b64.txt`, `.mini.b64.txt`: a small GLB per tier, its
  JSON (offsets already past the shared bytes; a building's lite JSON leaves the dressing nodes
  out of the scene graph) and its own textures (the phone tiers' downscaled copies).
- `assets/tex/<hash>.webp`: every texture of 2048 px or more as a plain WebP file, shared by
  content hash, referenced by URI from the tier JSON.

`loadGLB` (glbship.js) fetches tier + shared, decodes the shared base64 straight into one GLB
buffer behind the tier's JSON and parses it. Desktop gets the authored textures, except the
colony buildings' own 4096 px metallic-roughness map, which goes out at 2048 px (base colour
and normals stay at 4096). 358 MB in 246 files before, ~208 MB in ~387 files after.

Embedded textures decode with `createImageBitmap(Blob)` (glbship.js `EmbeddedImageBitmaps`), never by URL:
three's GLTFLoader wraps them in a `blob:` URL and `fetch()`es it, and the artifact host's CSP
(`connect-src`) refuses that, so on the published page every texture inside a GLB failed to load
(white colony components, plain parts) while the `assets/tex/*.webp` URI textures loaded.

**Texture-unit budget.** Most real GPUs give a fragment shader 16 texture units (ANGLE on D3D11 and
Metal, iOS, most Android); SwiftShader, which every local still uses, gives 32. A material over 16
samplers fails to link there and its meshes are not drawn. The carrier hull (glTF map, normal,
roughness, metalness + PATINA detail and hangar interior sets + worn finish + SAO + env, DFG LUT,
shadow) needed 18, `bell-XL` 17: once 851093d moved the hull's 4096 px maps to URI files that the
CSP lets through, the hull and the engine bells vanished on the published page (lights, turrets,
parked ships and the hangar outline stayed; the bells' glowing throats floated alone as blue
spheres; parked fighters and freighters lost their textured materials and read brown). Before
851093d every texture was embedded, blocked by the CSP, and the untextured hull had 14 samplers.
Now: the detail and interior sets' roughness and height go in one packed texture (patina.js
`packRoughHeight`, R/G) and glTF materials read metalness from the shared metal-roughness texel
(glbship.js `shareMetalRough`): hull 15, colony components 13.

`tools/pkg-diff.mjs` renders every view through the package and through the dev path and diffs
the stills; by default the package page gets a host-like CSP and both pages an emulated 16-unit
GPU (`--csp 0` / `--units 0` to turn either off), the conditions that hid this locally.

**Package check** (`tools/check-package.mjs`, run at the end of `build-artifact.mjs`; `--no-check`
skips it): every model tier is decoded the way the published page does it (glbship.js `loadGLB`,
files through `dist/files.json`, the host's CSP) and compared with its source GLB in three's own
loader: nodes, meshes, triangles, materials, textures per material slot, every texture decoded,
within its tier's cap and looking like the source's (16 px thumbnails); and before any loader, the
reassembled glTF itself: scene nodes, meshes, primitives, accessors, materials, textures, images,
geometry bit-identical to the source, every image a packaged URI or an embedded range that
decodes, the shared file the length its tier was split against. The build fails on any
difference. `node tools/check-package.mjs [--only <name>]` runs it alone;
`CHECK_VARIANT=nob64` / `noibm` exercise the loader's fallbacks (no `Uint8Array` base64, no
`createImageBitmap`).

Measured with `tools/phone-check.mjs` (headless Chromium, SwiftShader, so times are
relative). Before = commit 73c9ec2 (vehicle, shipyard, spaceport added); after = this fix.
GPU = textures + geometry + render targets; heap = retained after GC / transient peak.

| view (phone) | fetched MB | textures MB | GPU MB | triangles | heap MB after | heap + GPU MB after | ready s |
|---|---|---|---|---|---|---|---|
| fleet (default) | 36.8 → 24.0 | 608 → 98 | 737 → 204 | 3824k → 3067k | 15 / 113 | 219 | 44 → 20 |
| lineup | 33.1 → 25.4 | 625 → 105 | 732 → 212 | 1404k | 16 / 79 | 229 | 43 → 24 |
| fighter studio | 4.0 | 61 | 132 | 72k | 7 / 22 | 139 | 6 |
| corvette studio | 6.4 | 94 | 169 | 145k | 7 / 17 | 176 | 7 → 6 |
| freighter studio | 8.6 | 80 | 153 | 100k | 7 / 31 | 160 | 9 → 7 |
| destroyer studio | 7.0 | 85 | 160 | 191k | 7 / 22 | 167 | 7 → 6 |
| carrier studio (+ parked) | 31.2 → 24.9 | 496 → 153 | 596 → 253 | 748k | 12 / 111 | 264 | 30 → 17 |
| vehicle studio | 3.3 | 48 | 118 | 40k | 6 / 10 | 124 | 6 |
| deuterium_depot (colony, v2) | 5.0 | 27 | 101 | 120k | 6 / 11 | 112 | 3.8 |
| steel_mill (colony, v2) | 6.3 | 43 | 117 | 127k | 6 / 11 | 129 | 4.1 |
| shipyard | 15.0 → 10.8 | 210 → 59 | 292 → 141 | 355k → 291k | 8 / 28 | 149 | 11 → 10 |
| spaceport | 19.9 → 15.9 | 282 → 67 | 377 → 160 | 757k → 712k | 10 / 104 | 170 | 22 → 12 |

Renderer + GPU process memory (RSS) for the default fleet view: 1.71 GB before the new
assets (b0d3f39), 1.84 GB at 73c9ec2, 1.05 GB after. The transient heap peaks (80-110 MB in
the big views) are the crease weld and lightscape passes at build time; they are garbage
collected before the first frame.

## Scale model

The game gives each space unit a hangar **size** in
`Engine/net/cqs/engine/units/UnitEnum.java` (`getSize()`), and the carrier
has `spaceTransport = 50`; `Fleet.mayLeaveSystem()` requires that capacity to
cover the summed sizes of all non-warp ships:

| Class | Game id | Size (hangar slots) |
| --- | --- | --- |
| Fighter | `FIGHTER*` | 1 |
| Civil ship | `FREIGHTER*`, `TRANSPORTER*` | 4 |
| Corvette | `CORVETTE*` | 5 |
| Destroyer | `DESTROYER*` | 12 |
| Carrier | `CARRIER` | carries 50 |

The scene reads *size* as a ship's parking envelope in a hangar: the
axis-aligned bounding box, length × beam × height. A destroyer therefore takes
12× a fighter's **volume**, not 12× its length. The slot volume is set by the
carrier: its 900 m hull and the hangar bay measured inside it are fixed, and a slot
is the largest volume at which every legal full load (50 fighters, 10 corvettes,
4 destroyers or 12 civil ships, 2 m clearance) still fits that bay. That is
70,000 m³: twelve civil ships exactly fill it, so the carrier's 50-slot
capacity is what sizes its hangar (scale-check: the carrier could not be more than
2.4 % shorter). `src/lib/scale.js` scales every ship uniformly so that its envelope
volume is exactly `size × 70,000 m³`; each module is authored at real size, so
this correction is under 2 %. Both civil variants take 4 slots, so the bulkier
two variants are sized independently.

| Class | Length | Crew |
| --- | --- | --- |
| Fighter | 72 m | about 40 |
| Corvette | 108 m | about 350 |
| Civil ship (cargo / troops) | 134 m / 129 m | about 80 (troops: ground-unit capacity 750) |
| Destroyer | 203 m | about 2,000 |
| Carrier | 900 m | about 20,000 |

Crews are design estimates from each hull's volume; the game's chassis population
cost (`crew`) is an abstract unit and is not used. The troop transport's 750 is the
game's `groundTransport`, counted in ground-unit sizes (infantry 1, vehicles 3,
aircraft 4), not people. Shared details stay at human scale on every hull: after
the rescale, the fighter, corvette, civil ships and destroyer were re-drawn at their
new sizes (nano-banana-pro/edit, then new Tripo H3.1 multiview meshes) so their
windows (~1 m), hatches, handrails and containers (20-ft ISO) read at true size
instead of being blown up 2.8x; the 0.4 m nav lights, the 6 m plating repeat and
the 1.8 m crew member in the lineup are fixed in metres.

A second detail round (v5) then tightened the small details so they read crisply:
nano-banana-pro/edit passes aimed at the named elements (bridge glazing, ports, hatches,
rails; crop-and-blend edits where a whole-image edit would not change them), new 4K
turnarounds and Tripo H3.1 meshes, with fighter and corvette textures raised to 4096.
Measured on the meshes: bridge panes 0.5-0.8 m, ports 0.65-0.95 m in rows one deck
apart, rails about 1-1.8 m, hull numbers 2.2-2.3 m (carrier 15 m). The image model
would not draw the carrier's ports small enough at 900 m, so its hull carries fal
PATINA tiles (flank ports, island ribbon panes, 2.7 m plating) sized from measured
pixels and baked into an 8K base-colour and normal texture by a texel-to-world lookup
(the hangar cavity and the drive bells are left as generated). A texture-repair pass
(v6) then fixed what the image model would not shrink: every oversized crew door is
repainted as plating plus a 1.0 x 2.0 m door cut from a fal door image (the destroyer's
5.6 x 10.4 m flank opening became a framed boat hatch with a personnel door in its leaf),
the civil ships' container stacks carry fal PATINA container faces at true ISO size
(2.59 m rows, 2.44 m door ends, 6.06 m long sides), and an opt-in livery band removes
the lilac cast of their generated paint. Where the old door shapes are modelled into
the mesh (a recess on the fighter, raised panels on the corvette) their relief still
shows at close range.

The carrier is warp-capable, so never carried itself. In the fleet its bay holds a
legal load (two destroyers and two civil ships nose to tail across the frames, two
fighters in the bow section, three fighters on the launch and recovery cycle: 37
of 50 slots). `node tools/scale-check.mjs` verifies all of this against the
geometry that is actually rendered, including a ray-cast test that the hangar box
lies inside the hull (the V-31 vehicle is listed at its true size: a ground unit, no hangar slots):

<!-- scale-table -->
```
slot volume: 70000 m^3

class             size  L x B x H (m)             volume    slots   design scale  tris     draws
fighter           1     71.71 x 46.87 x 20.83     70000     1       0.9994        63379    10
corvette          5     108.04 x 69.41 x 46.67    350000    5       0.9992        129852   17
freighter         4     134.14 x 54.69 x 38.17    280000    4       1.0001        95927    22
destroyer         12    203.13 x 56.02 x 73.82    840000    12      1.002         179620   14
carrier           -     900 x 406.04 x 319.33     116695859 -       1             314854   17
freighter:troops  4     128.82 x 57.73 x 37.65    280000    4       0.9998        126827   16
vehicle           -     6.95 x 2.63 x 2.99        55        -       1             40387    9

carrier hangar (clear, L x B x H): 670 x 155.8 x 84.4 m
  fighter           need 50  fits 81   OK
  corvette          need 10  fits 12   OK
  destroyer         need 4   fits 6    OK
  freighter         need 12  fits 22   OK
  freighter:troops  need 12  fits 22   OK
  hangar box inside hull: 100.0% of 384 samples OK
  capacity 50 slots (UnitEnum.CARRIER spaceTransport); loads: 50 fighter x 1, 10 corvette x 5, 4 destroyer x 12, 12 freighter x 4, 12 freighter:troops x 4
  smallest carrier whose hangar would still fit every load: 878.4 m (97.6 % of the design; binding load: freighter, 11 of 12 fit 0.1 % smaller); built: 900 m (design length)

SCALE CHECK PASSED
```

## Layout

```
Scene3D/
  index.html            page shell, UI overlay, import map
  pipeline/             fal-pipeline.json: every prompt and parameter
  assets/concepts/      fal concept art (WebP)
  assets/ships/         optimised fal meshes and remodelled hulls (GLB, incl. the vehicle); raw/ is gitignored
  assets/buildings/     shipyard.glb, spaceport.glb, colony buildings <id>.glb (Blender builds, tools/blender/buildings/); raw/ is gitignored
  assets/materials/     PATINA tiling PBR sets + manifest.json
  src/main.js           renderer, views, camera, post-processing
  src/fleet.js          fleet composition and choreography
  src/ui.js             ship registry and spec sheet
  src/ships/*.js        one module per class: meta + asset config (GLB, orientation, length, anchors); index.js = registries
  src/buildings/*.js    shipyard.js, spaceport.js; colony.js (shared colony factory), catalog.js (Buildings menu), one small module per colony building
  src/lib/glbship.js    GLB -> scene ship (orientation, size, livery, detail, nozzle glow, anchors)
  src/lib/livery.js     dark matte operational repaint of the generated textures
  src/lib/patina.js     PATINA library, full materials and the tri-planar detail layer
  src/lib/park.js       parks real ships on the carrier's hangar deck
  src/lib/launch.js     launch and recovery cycle through the bow mouth (deck lifts, catapult, teardrop)
  src/lib/chart.js      scale-chart annotation: callouts with leader lines, ruler, camera framing
  src/lib/hangar.js     ray-cast hangar containment test
  src/lib/effects.js    drive glow / short plumes and navigation lights
  src/lib/scale.js      game-derived scale model and hangar-fit check
  src/env/*.js          lighting rig, sky, sun, planet
  src/lib/finish.js     worn hull finish and screen-space AO
  src/lib/device.js     phone (lite) tier
  src/lib/clip.js       build-state clipping (shipyard, spaceport)
  assets/parts*/        parts kits (fal and procedural Blender, incl. the ground-unit parts; parts-yard/ and
                        parts-spaceport/: the building kits)
  tools/blender/        Blender pipeline: kit.py, parts_ground.py, hulls/ (remodel per ship and the vehicle),
                        buildings/ (shipyard, spaceport, their kits), assemble.py, straighten.py
  tools/                server, stills, GLB inspection, scale check, fal ingest/optimise, artifact packaging
```

## Tools

```sh
npm install                     # three, playwright-core, gltf-transform, sharp (tools only)
node tools/scale-check.mjs      # envelope vs. game size for every ship + hangar loads
node tools/shoot.mjs "mode=ship&ship=destroyer&az=35&el=18" shots/destroyer.png
node tools/render-glb.mjs any/where/ship.glb shots/ship --rot 0,-90,0   # GLB inspection stills + contact sheet + mesh info
node tools/thumbs/thumbs.mjs shots/thumbs.png "Fighter=a.png" "Vehicle=b.png"   # icon readability test: 80 / 40 px squares on the game UI panel
node tools/ingest-fal.mjs results.json   # download fal outputs: concepts, meshes (optimised), PATINA maps
node tools/build-artifact.mjs   # single-page package for sharing (+ phone copies: ships .lite/.mini, buildings .lite)
node tools/phone-check.mjs      # phone budget per view (needs a fresh dist/); --desktop, --still --shots <dir>
node tools/shoot.mjs "mode=building&building=shipyard" shots/shipyard.png
node tools/buildings/compare.mjs steel_mill --version v1   # concept | old render | new render + 80/40 px icons -> style-library/.../images/buildings/<id>-v1.jpg
PY=<venv>/bin/python tools/blender/buildings/colony_build.py steel_mill /tmp/work --tex 4096   # build a colony building (bkit)
PY=<venv>/bin/python tools/blender/hulls/build.sh corvette /tmp/work   # rebuild a hull (bpy 5.0)
```

`shoot.mjs` renders with headless Chromium and software WebGL, and serves
three.js from `node_modules`, so it works offline.
