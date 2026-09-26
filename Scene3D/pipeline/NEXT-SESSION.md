You're continuing work on the **CQS Orbital Fleet** 3D scene in the repo `ligustah/cqs`. Start from branch `claude/3d-orbital-ships-scene-u95ehb`: fetch it and base your work on it. The previous session may still push commits to it under `Scene3D/src/env/` (planet/sky), so fetch and merge it again before you finish.

## Goal

Replace the five placeholder ships with **fal.ai-generated assets** and finish a photoreal real-time scene:

1. concept art made with an image model,
2. 3D meshes made from that concept art with an image-to-3D model,
3. tiling PBR textures made with fal PATINA,

with three.js doing what Blender does in the usual pipeline: import, clean-up, materials, lighting, rendering. Follow the "Stefan_3D_AI" pipeline: image model → Tripo/Hunyuan3D mesh → optimise → PATINA materials → assemble, light and render, checking your own screenshots at every step.

**Every asset must be created with fal.** Don't model the ships procedurally.

## Hard rules

- **Original IP.** This is a reboot of the old browser game Conquer-Space. Never use, open or reference the old art: `Artwork/**`, `Html/Design/pack/units/*`, `*.blend`. Don't imitate franchise ships from Star Wars, Star Trek, The Expanse, Halo, BSG, Homeworld or EVE. Only the class roster and the stats come from the old game.
- **Realism.** It can be futuristic (fusion torch drives are welcome), but it must feel real and photographic, never like a cheap video game:
  - physically based, weathered materials;
  - real engineering proportions and human-scale details;
  - no neon trim;
  - one hard sun and deep shadows;
  - bloom only from genuinely bright sources.
- **Scale.** Scale comes from game data and is already implemented in `Scene3D/src/lib/scale.js`.
  - `UnitEnum.getSize()` gives each ship a number of hangar slots: fighter 1, civil ship 4, corvette 5, destroyer 12. The carrier carries 50.
  - 1 slot = 800 m³ of parking envelope (the axis-aligned bounding box).
  - Each ship is uniformly normalised to `size × 800 m³`. That puts the fighter at about 16 m, corvette ~31, freighter ~50 and destroyer ~67 m.
  - The carrier is 240–280 m. Size it so that a hangar box able to hold every legal full load physically fits inside its hull: 50 fighters, or 10 corvettes, or 4 destroyers, or 12 freighters, all with 2 m clearance.
  - `node tools/scale-check.mjs` must pass.

## fal access

Use whichever works in this session, in this order:

1. **fal MCP tools** (fal's own MCP server).
2. **Composio `fal_ai` tools.** Submit with `FAL_AI_SUBMIT_ASYNC_JOB` (or `FAL_AI_RUN_MODEL_SYNC`), poll with `FAL_AI_QUEUE_GET_STATUS`, and fetch with `FAL_AI_GET_QUEUE_REQUEST_RESULT`. In the previous session the submit tools were restricted by the Composio tool list. If they still are, say so and try option 1 or 3.
3. **A `FAL_KEY` env var** with fal's queue REST API (`https://queue.fal.run/<model>`).

fal's CDN (`*.fal.media`) is reachable from the container, so download results directly. The user has pre-approved fal usage for this task. The expected total is roughly $5–15. Check prices with the pricing tool, and ask before going far beyond that.

## What already exists (read these first)

- **`Scene3D/pipeline/fal-pipeline.json`**: every prompt and parameter, including the photoreal style, the art-bible prompt, per-ship descriptions, 3D settings and the PATINA material prompts. Use it as the source of truth, and improve the prompts if the results need it.
- **`Scene3D/tools/ingest-fal.mjs`**: downloads fal outputs into `assets/`: concepts become WebP, meshes are optimised, PATINA maps are written with a `manifest.json`. Input is a `results.json` of URLs; the format is documented in the file header.
- **`Scene3D/tools/optimize-glb.mjs`**: weld, simplify to a triangle budget, WebP textures, meshopt compression.
- **`Scene3D/src/lib/glbship.js`**: turns a GLB into a scene ship: orientation, design length, envelope, engines, lights, anchors, and material upgrades including the PATINA detail layer.
- **`Scene3D/src/lib/patina.js`**: loads `assets/materials/manifest.json` sets, builds full materials, and adds the tri-planar detail layer on generated meshes.
- **`Scene3D/src/ships/index.js`**: if a ship module exports `asset`, the GLB is preloaded and built through `glbship.js`. Placeholders are in `src/ships/*.js`.
- **`Scene3D/src/lib/effects.js`**: fusion-torch plumes (volumetric) and nav lights, driven by the `engines` and `lights` in the ship config.
- **`Scene3D/src/main.js`, `fleet.js`, `ui.js`, `index.html`**: the views.
  - Views are fleet in orbit, scale lineup (a stern-aligned chart with a ruler, a 1-slot cube and a hangar-load ghost) and a ship studio.
  - URL params: `?mode=ship&ship=X&az=&el=&dist=&variant=`, `?mode=lineup`, `?mode=fleet&shot=hero|high|stern`, `?mode=check`.
- **Tools**: `node tools/shoot.mjs "<query>" out.png [...]` renders stills in headless Chromium (software WebGL, ~10 s each); look at them with the Read tool. `node tools/scale-check.mjs` prints the scale table and the hangar fits. Run `npm install` in `Scene3D/` first.

Ship module format for generated ships (replace each placeholder file):

```js
export const meta = { name: 'Kestrel-class fighter', designation: 'FS-9', blurb: 'one sentence' };
export const asset = {
  glb: './assets/ships/fighter.glb', generator: 'tripo3d/p2/image-to-3d', concept: './assets/concepts/fighter.webp',
  rotate: [0, 0, 0],   // degrees, so the bow faces +Z and dorsal +Y (port = +X)
  length: 16,          // design length in metres (bounding-box Z); scale.js applies the small slot correction
  detail: { set: 'hull', tile: 3, normalStrength: 0.8, roughAmount: 0.5, cavity: 0.35 },
  materials: { '*': { envMapIntensity: 1.0 } },
  engines: [{ p: [x, y, z], radius: r, mirrorX: true }],   // nozzle exit centres, metres, ship frame
  lights: [{ p: [x, y, z], color: 'red', mirrorX: true, mirrorColor: 'green', blink: { period: 1.4, duty: 0.12 } }],
  anchors: {},  // carrier: hangar { p, size: [X, Y, Z] } and hangarMouth { p, dir: [0, 0, 1] }
};
export const variants = { troops: { glb: './assets/ships/freighter-troops.glb' } }; // optional
```

The fleet uses variants `fighter:lead|wing` and `freighter:cargo|troops`. A missing variant falls back to the base asset.

## Steps

1. **Concept art** (`fal-ai/nano-banana-pro`, then `/edit` with the bible as reference).
   - Generate the fleet art bible first and pick the best of two.
   - Then generate each ship isolated in a three-quarter studio view on plain light grey: no floor, shadows, text or exhaust, and the whole ship in frame. These are the image-to-3D inputs.
   - Also generate one photoreal in-orbit "beauty" shot per ship (`beautyTemplate`) as concept art for the UI.
   - Review every image yourself for originality, realism and design consistency; regenerate weak ones.
2. **Meshes.**
   - Run the fighter through both `tripo3d/p2/image-to-3d` (PBR, `texture_quality: detailed`, `delight: true`, face limit from the spec) and `fal-ai/hunyuan-3d/v3.1/pro/image-to-3d` (`enable_pbr: true`).
   - Import both, render them from several angles, and pick the model that reconstructs hard-surface detail better. Use that model for all ships: fighter, corvette, freighter (cargo, plus a troop-transport variant), destroyer and carrier.
   - Write down which model you chose and why.
3. **Optimise and ingest.** Use `tools/ingest-fal.mjs`: keep the raw GLBs out of git (add `assets/ships/raw/` to `.gitignore`) and commit the optimised ones. Stay inside the triangle budgets in the spec, and keep each file under ~12 MB.
4. **PATINA materials** (`fal-ai/patina/material`, all 5 maps, `upscale_factor` 2). Generate the 7 sets from the spec: hull, orange, armor, ceramic, foil, deck, radiator. Ingest them to `assets/materials/` with the manifest. Use hull, orange and armor as detail layers on the ships, and the full materials for scene-built parts.
5. **Assemble each ship module.**
   - Find the orientation from renders.
   - Place the engine anchors exactly on the nozzle exits, and the nav lights: red on port (+X), green on starboard (−X), white strobes.
   - For the carrier: place the hangar box and hangar mouth on the bow opening. Add a raycast inside-test to check mode (sample points in the hangar box, count ray crossings with the hull), and choose the carrier length so at least 95% of the box is inside the hull while all four loads fit.
   - Tune materials so they read as real. The generated textures carry the livery; PATINA adds close-up plating.
6. **Realism pass on the scene.**
   - Tune the fusion plumes (`effects.js`) on the real models; the view from astern is still slightly hot.
   - Remove or reduce the cool rim light in `src/env/lighting.js`, and keep the fill physically motivated: planet-shine plus an env map matching the sky and planet.
   - Keep the sky near-black with faint stars; tone down the magenta nebula if it looks game-like.
   - Tune the exposure and bloom threshold so only drives, the sun and lights bloom.
   - Show each ship's concept and beauty images in the spec sheet (`ui.js`).
7. **Verify.**
   - `node tools/scale-check.mjs` passes.
   - Render the ship studio for each class from four angles, the lineup, and the three fleet shots; look at every image and fix problems.
   - No console errors.
8. **Deliver.**
   - Update `Scene3D/README.md` with the pipeline (models used, prompts file, costs) and the scale table from scale-check.
   - Commit, and push to your designated branch.
   - Publish the scene as an Artifact: `node tools/build-artifact.mjs` produces the page plus `dist/files.json`. The GLBs, concepts and material maps must be included as supporting files (≤15 MB each).
   - Report what was generated, with which models, the cost, the renders, and any remaining issues.
