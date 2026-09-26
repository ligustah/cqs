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
| Fleet in orbit | `#fleet` (default), `?mode=fleet&shot=hero\|high\|stern` | Carrier group above the planet: parked ships in the carrier's open bays, launches from the hangar mouth, escorts, fighter patrols, the logistics convoy |
| Scale lineup | `#lineup` | Scale chart: sterns aligned on a metre ruler, one row per class, a 1-slot reference cube, a 1.8 m crew member, and an optional 50-fighter hangar load |
| Ship studio | `?mode=ship&ship=carrier&az=35&el=18&dist=1` | One ship, framed for inspection (`fighter`, `corvette`, `freighter`, `destroyer`, `carrier`; `variant=troops`; `parked=1` fills the carrier's hangar; `debug=1` shows axes, a metre grid, engine/light anchors and the hangar box) |
| Check | `?mode=check` | Builds every ship and reports envelopes, slots and hangar fits (used by `tools/scale-check.mjs`) |

Controls: drag to orbit, scroll to zoom, double-click a ship to fly to it and
follow it. The spec sheet shows each ship's dimensions, crew, hangar loads and
its fal concept art (in-orbit concept and the image-to-3D input).

Look-dev overrides: `?livery=none|dark|civil`, `?exposure=`, `?fov=`, `&t=` (freeze time).

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
     re-projected onto its texture.
3. **Optimise** — `tools/ingest-fal.mjs` downloads results; meshes go through
   `tools/optimize-glb.mjs` (weld, simplify to the class budget, WebP textures,
   meshopt). Raw GLBs stay in `assets/ships/raw/` (gitignored).
4. **Materials** — `fal-ai/patina/material` (all five maps, 2× upscale):
   hull, orange, armor, ceramic, foil, deck, radiator in `assets/materials/`
   with `manifest.json`. On the generated hulls PATINA is a tri-planar detail
   layer (normal, roughness, cavity) at one absolute plating size (6 m per
   repeat) on every ship; the full sets texture scene-built parts.
5. **Assemble, light, render** — `src/lib/glbship.js` orients and sizes each
   GLB, repaints it in the dark matte operational livery (`src/lib/livery.js`;
   the generation images stay light because light paint reconstructs better),
   adds the PATINA layer, nozzle glows, nav lights and anchors. One hard sun,
   an environment map of black space plus the planet, bloom only on the sun,
   drive bells and lights; drives are a glowing bell with a short soft plume.

Costs (fal list prices): about 58 nano-banana-pro images (13 of them 4K
turnaround sheets) ≈ $10.70, 6 Tripo P2 models $7.20 (superseded), 11 Tripo
H3.1 models $6.60, 3 Hunyuan3D 3.1 Pro models ≈ $1.90, 11 PATINA sets ≈ $1.20 —
about **$27.50** in total.

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
12× a fighter's **volume**, not 12× its length. One slot is 3,200 m³, set from
the smallest class: a fighter with a crew of three is about 25 m long.
`src/lib/scale.js` scales every ship uniformly so that its envelope volume is
exactly `size × 3,200 m³`; each module is authored at real size, so this
correction is under 2 %. Both civil variants take 4 slots, so the bulkier troop
transport comes out shorter than the cargo ship.

The carrier is a 900 m, ~9,000-crew design (warp-capable, so never carried
itself). Its hangar box is measured inside the generated hull's bay and must
hold every legal full load — 50 fighters, 10 corvettes, 4 destroyers or 12
civil ships, with 2 m clearance. `node tools/scale-check.mjs` verifies all of
this against the geometry that is actually rendered, including a ray-cast test
that the hangar box lies inside the hull:

<!-- scale-table -->

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
