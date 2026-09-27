# Orbital Fleet — 3D scene for the Conquer-Space reboot

A real-time three.js scene of the reboot's orbital ships: fighter, corvette,
civil ship (freighter / troop transport), destroyer and the fleet carrier, in
orbit above a planet. Every hull, texture and tiling material was generated
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
| Fleet in orbit | `#fleet` (default), `?mode=fleet&shot=hero\|high\|stern` | Carrier group above the planet: parked ships in the carrier's open bays (21 fighters, 2 corvettes, a destroyer and a cargo ship; with the 3 fighters of the launch cycle that is exactly its 50-slot legal load), a launch and recovery cycle through the bow mouth, escorts, fighter patrols, the logistics convoy |
| Scale lineup | `#lineup`, close-up `?lineup=small#lineup` | Scale chart: sterns aligned on a metre ruler (ticks every 10 m to 100 m, then every 100 m), one row per class labelled by callouts on the stern side, a 1-slot reference cube, a 1.8 m crew member, a neutral 10 m / 100 m grid, and an optional 50-fighter hangar load (`hangar=1`). The default view frames the whole 900 m chart, with a detail box in the empty grid that shows the `lineup=small` framing (a second render of the same scene); `lineup=small` frames only the small ships, the cube and the crew member, like the enlarged inset of a technical drawing (also linked from the toggles bar and the detail box) |
| Ship studio | `?mode=ship&ship=carrier&az=35&el=18&dist=1` | One ship, framed for inspection (`fighter`, `corvette`, `freighter`, `destroyer`, `carrier`; `variant=troops`; the carrier's hangar is parked by default (`parked=0` empties it, `parked=1` aims the camera at it); `debug=1` shows axes, a metre grid, engine/light anchors and the hangar box). The camera fits the hull's own silhouette (sampled mesh vertices), not its bounding box. Stills are shot over the planet (`planet=0` for black; the interactive studio adds it with `planet`), and the studio key is placed relative to the camera, 85 degrees round from its azimuth and 30 degrees up, so every view splits into a lit and a shadowed plane (`sunaz=`/`sunel=` override, in degrees) |
| Check | `?mode=check` | Builds every ship and reports envelopes, slots and hangar fits (used by `tools/scale-check.mjs`) |

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
repair (v6) about $0.70: about **$55** in total.

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
| Corvette | 107 m | about 350 |
| Civil ship (cargo / troops) | 134 m / 129 m | about 80 (troops: ground-unit capacity 750) |
| Destroyer | 204 m | about 2,000 |
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
lies inside the hull:

<!-- scale-table -->
```
slot volume: 70000 m^3

class             size  L x B x H (m)             volume    slots   design scale  tris     draws
fighter           1     71.54 x 46.8 x 20.91      70000     1       0.9975        73479    1
corvette          5     107.11 x 68.81 x 47.49    350000    5       1.0001        91060    1
freighter         4     134.15 x 54.7 x 38.16     280000    4       1.0002        110779   1
destroyer         12    202.68 x 56.1 x 73.88     840000    12      0.9925        145130   1
carrier           -     900 x 405.55 x 319.3      116541493 -       1             231273   1
freighter:troops  4     128.82 x 57.73 x 37.65    280000    4       0.9998        109004   1

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
  assets/ships/         optimised fal meshes (GLB); raw/ is gitignored
  assets/materials/     PATINA tiling PBR sets + manifest.json
  src/main.js           renderer, views, camera, post-processing
  src/fleet.js          fleet composition and choreography
  src/ui.js             ship registry and spec sheet
  src/ships/*.js        one module per class: meta + asset config (GLB, orientation, length, anchors)
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
  tools/                server, stills, GLB inspection, scale check, fal ingest/optimise, artifact packaging
```

## Tools

```sh
npm install                     # three, playwright-core, gltf-transform, sharp (tools only)
node tools/scale-check.mjs      # envelope vs. game size for every ship + hangar loads
node tools/shoot.mjs "mode=ship&ship=destroyer&az=35&el=18" shots/destroyer.png
node tools/render-glb.mjs any/where/ship.glb shots/ship --rot 0,-90,0   # GLB inspection stills + contact sheet + mesh info
node tools/ingest-fal.mjs results.json   # download fal outputs: concepts, meshes (optimised), PATINA maps
node tools/build-artifact.mjs   # single-page package for sharing
```

`shoot.mjs` renders with headless Chromium and software WebGL, and serves
three.js from `node_modules`, so it works offline.
