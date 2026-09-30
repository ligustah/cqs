# Runtime (three.js) and shipping

In this repo: `Scene3D/src/`. A new project can copy the lib folder. The pieces and what each is for:

| File | Role |
|---|---|
| `lib/glbship.js` | Loads a GLB with a module config: orients and centres it, scale correction, `hullNodes` (only these are hull, for raycasts and crease analysis), material upgrade (livery, PATINA detail, finish, glass whitelist), engines, lights, anchors |
| `lib/livery.js` | Runtime repaint: neutral luminance goes to the operational colour, saturated markings are kept (`mark`, `markSat`); two-tone schemes by zone boxes; glass glow per compartment (`glassGlow`, `glassLit`, `glassCell`, `glassPhase`, `glassDark` / `glassZones` up to 8 boxes, `glassParts` whitelist, range fade for kit glass) |
| `lib/finish.js`, `lib/patina.js` | Tri-planar PATINA detail at an absolute tile; worn finish (plate tone, grit, soot); GTAO contact shadows |
| `lib/lightscape.js` | Generates lights from the hull: crease pins, recess and corner slits (exposure-tested with a triangle grid), louvre filter, zones, authored patterns (row, surface, ring, points, slit, slitRow; chase, pulse, skip, keep, mirrorX). The header is the spec |
| `lib/effects.js` | Draws them: Points for pins (Gaussian sprite, rank thinning), InstancedMesh for slits and halos (gain, saturation, far-field dash or dot), drive plumes and throat glow |
| `env/lighting.js` | Studio rig (single-asset look-dev, the default in ship mode) and orbital rig |
| `lib/device.js` | Phone tier: `LITE` loads `.lite` GLBs with capped textures, lower pixel ratio, fewer lights, no AO |
| `lib/scale.js`, `tools/scale-check.mjs` | The scale model (slot volume), hangar fits; must PASS before commit |

## Module (per asset) essentials

`glb`, `length`, `rotate` (the remodel exports in frame: `[0, 0, 0]`), `hullNodes: ['hull']`,
`livery {...}`, `liveryZones`, `detail {set, tile, normalStrength, cavity}`, `engines[]` (from the kit
bells), `lights[]` (nav only), `lightscape {...}`, `anchors.surfaces` (named flat faces). Comment every
number with its reason (what it is, and what was wrong before), in the file's style.

## Shipping checklist

1. `node --check` every changed JS file; run `node tools/scale-check.mjs` and require
   `SCALE CHECK PASSED`.
2. `tools/optimize-glb.mjs` (weld, simplify to budget, WebP, meshopt). Lite copies via
   `tools/lite-glb.mjs`, with textures capped at 1024 for assets, 2048 for the biggest, 512 for parts.
3. Artifact: `tools/build-artifact.mjs` writes the page and the file map.
   - GLBs go as base64 `.b64.txt`.
   - Limits: 16 MB per file and 64 MB per publish, so republish only what changed and split big sets.
   - List the published files first; a publish of files not yet seen is refused.
4. Commit and push after each accepted step. Checkpoint commits are fine on a feature branch; write
   honest messages ("reviews pending").

## Known runtime pitfalls

- Plume proxies drawn back-face with depth test clip into C-shaped rims from stern quarters. Pick the
  front face unless the camera is inside the proxy.
- The Neutral tone map and bloom pull bright amber toward cream. Keep emissive peaks modest and
  saturate beforehand.
- Pixel floors on distant lights (a 3 px minimum) change the scale read at range. Fade by true area
  instead.
- Materials shared between meshes must be keyed by everything that changes their shader (zones, glass
  on or off, transform), or one mesh's settings leak into another.
