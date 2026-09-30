---
name: model-forge
description: Build and refine game-ready 3D models (ships, vehicles, buildings, props, any hard-surface asset) with fal.ai image models, image-to-3D reconstruction, headless Blender and a three.js review scene, and keep every new asset consistent with a shared style library (art bible, parts kits, materials, scale and lighting standards). Use this skill whenever the user wants to create, redesign, remodel, detail, texture, light or review a 3D model or asset, generate concept art or turnaround sheets for one, make reusable parts or components, pick a fal model for images, meshes or materials, run review loops on renders, or add or extend a style for a new creation, even if they do not say "skill", "fal" or "Blender" explicitly.
---

# Model forge

A proven pipeline for hard-surface 3D assets. It came out of building and repeatedly refining a five-class
space fleet (fighter to 900 m carrier) for an original-IP game. The lessons are general: they apply to any
asset family that has to look consistent, read at the right scale and survive close inspection.

The core insight, learned the hard way: **image-to-3D is a blueprint, not a product.** Generated meshes
average fine detail into soft "mushy" lumps, bake lighting into textures and hallucinate the unseen sides.
The quality bar was only met by rebuilding each hull as clean parametric geometry in Blender, using the
generated mesh purely for measurements, and composing it from small reusable parts that are designed
once at true size and reused everywhere. Consistency comes from the style library, not from prompting
harder.

## Before you start

1. **Read the style library.** It lives at `style-library/` in the repo root (see
   `references/style-library.md`). Find the style the asset belongs to, e.g.
   `style-library/styles/cqs-fleet/`, or create a new one. Load its `STYLE.md`, which holds the art bible,
   palette, livery, materials, scale rules and lighting standard. Load its `kits.md`, the catalogue of
   reusable parts. A new asset in an existing style reuses those kits and rules. Do not reinvent them.
2. **Check the hard rules of the project.** Typical ones:
   - original IP only;
   - never open or reference legacy art (list the folders);
   - no imitation of named franchises;
   - a budget for fal spend.

   Put them in `STYLE.md` so every agent sees them.
3. **Check the environment.**
   - Blender: the `bpy` pip wheel works headless. Run
     `.claude/skills/model-forge/scripts/setup_blender_venv.sh <dir>` (bpy 5.0.1 needs Python 3.11).
   - Node deps: `npm install` in the scene folder (three, gltf-transform, meshoptimizer, sharp,
     playwright-core).
   - Chromium for renders.
   - The fal connector for generation.

   Cloud containers restart often. Write notes and intermediate results to disk as you go, schedule
   check-ins for long runs, and make every stage resumable.

## The pipeline

Each stage ends with rendered evidence that you (or independent reviewers) look at. Never advance on
numbers alone. Details and exact parameters are in the references.

| # | Stage | Tooling | Reference |
|---|---|---|---|
| 1 | Brief and scale | style's scale model, crew and role, real-world refs | `references/scale-and-lighting.md` |
| 2 | Concept art | `fal-ai/nano-banana-pro` + `/edit` with the style's references | `references/fal-models.md` |
| 3 | Turnaround | nano-banana-pro 4K six-view sheet, cropped | `references/fal-models.md` |
| 4 | Blueprint mesh | `tripo3d/h3.1/multiview-to-3d` | `references/fal-models.md` |
| 5 | Parts kit (reuse first) | style kits; new parts via fal (image then Tripo) or procedural `kit.py` | `references/parts-kits.md` |
| 6 | Hard-surface remodel | headless Blender: measure, model, bake, paint | `references/blender-pipeline.md` |
| 7 | Assemble | `assemble.py` places kit parts from a spec | `references/blender-pipeline.md` |
| 8 | Materials and finish | `fal-ai/patina/material` tiling sets, runtime livery and worn finish | `references/fal-models.md`, `references/runtime-threejs.md` |
| 9 | Lights and life | lightscape: slits, pins, windows, nav lights, to the style's fixture standard | `references/scale-and-lighting.md` |
| 10 | Review loops | renders at hero / close / range / lineup; adversarial judges | `references/review-loops.md` |
| 11 | Ship it | GLB optimise, phone tier, artifact packaging, commit | `references/runtime-threejs.md` |
| 12 | Feed the library | new parts, prompts, rules and lessons back into the style | `references/style-library.md` |

### 1. Brief and scale

Pin down, in writing, before any image is generated:
- **Size and role:** true size in metres, crew, role.
- **Scale ruler:** what anchors human scale on it (doors 1 x 2 m, ports 1 m, rails 1.1 m, 20-ft
  containers).
- **Envelope:** the size the asset must hit.

Scale drift is the most expensive mistake: every later stage inherits it. In the fleet, a scale judge
measured doors and windows in every concept against the final length.

### 2-3. Concept and turnaround

Use nano-banana-pro for concepts, always through `/edit` with the style's art-bible sheet and approved
sister assets as references, so the family stays coherent. For each asset, make:
- an isolated three-quarter studio image on light grey, which is the reconstruction input;
- a beauty shot in the operational look;
- a 4K orthographic six-view turnaround, cropped into views.

Generate in **light paint**, even if the final look is dark: light surfaces reconstruct far better, and
the runtime livery darkens them. State the final length in the prompt. Make openings you need to keep
(hangar bays, recesses) see-through or explicit in the turnaround, or the reconstruction closes them.

### 4. Blueprint mesh

Tripo H3.1 multiview-to-3D, fed front / port / stern / starboard, won two independent bake-offs. It
gives crisp facets, legible markings, and a real stern and belly instead of hallucinated ones. Use the
result as a blueprint. Where a fast placeholder is acceptable, it can ship after
`tools/optimize-glb.mjs`, but expect "mushy" detail. The user rejected that quality level.

### 5. Parts first

Before modelling a hull, list every small human-scale or repeated component: doors, ports, panes,
hatches, rails, ladders, RCS, nav lights, floodlights, antennas, domes, turrets, drive bells, weapons,
containers. Reuse the style's kits at their **true metric size**. The same door on a 70 m and a 900 m
hull is what makes both read at the right scale. Add missing parts to the kit, not to the asset. See
`references/parts-kits.md` for:
- when to use fal (organic, detailed dressing) versus procedural Blender (anything with exact
  dimensions: bells, turrets, glass);
- the normalisation frame;
- known reconstruction failures, e.g. glass rebuilt as holes, and backs mirrored onto hidden faces.

### 6-7. Remodel and assemble

In headless Blender:
1. **Measure** the blueprint in the asset frame (sections, silhouettes, height maps).
2. **Model:** build the hull parametrically as closed volumes, with exact boolean recesses and
   4-10 cm bevels with weighted normals.
3. **Bake** maps.
4. **Paint** in texture space (light base, seams, panel tone, grime, edge wear, crisp stencils).
5. **Assemble:** place kit parts from a JSON spec.
6. **Score:** run `compare.py` against the blueprint (silhouette IoU about 0.9 or better).

Keep the envelope within about 0.5 % so downstream scale systems do not move. One `build.sh` per asset
reproduces it end to end. `references/blender-pipeline.md` has the method and the long list of pitfalls
(snap rays starting inside other parts, decimation eating thin round pieces, UV density on thin bands,
and more).

### 8-9. Look

- **Finish:** a runtime livery repaints generation paint into the operational scheme. The
  tone / bone two-tone schemes are opt-in; the default stays dark.
- **Materials:** tri-planar PATINA sets add plate tone, roughness breakup, grit and soot at one absolute
  tile size on every asset.
- **Lighting look:** studio lighting for single-asset views, orbital for scenes.
- **Lights:** follow the style's **fixture standard**. One physical size per fixture type on every
  asset. Windows only on real glass in crew spaces. Density grows with size. Small craft get authored
  lights, not scattered automatic pins. Distant lights thin and fade instead of becoming window-shaped
  boxes.

  This is where "make it look alive" and "it looks too big" pull against each other. The resolution is
  in `references/scale-and-lighting.md`.

### 10. Review loops

Every change is judged on renders, not on intent. The review toolkit, the render harness and the
multi-agent patterns that worked are in `references/review-loops.md`. The short version:
- **Views:** always look at hero, close, range (the asset small on screen) and a lineup next to other
  assets at the same scale. A problem that only shows at range is still a problem.
- **Comparisons:** make before/after sheets and 1:1 crops. Compare at matched resolution and camera, or
  the comparison lies.
- **Independent judges:** use lenses that pull in different directions, e.g. SCALE ("does it read at its
  true size?") and LIFE ("is it still as alive as the user liked?"). Judges try to refute, default to
  refuted, and must give concrete, tested must-fix items. Cap fix rounds at two, then the orchestrator
  applies the last narrow items.
- **Rules as code:** turn recurring judgements into measurable checks (audit scripts, mark counters,
  luminance splits) and put them in the style library.

### 11. Ship

- **Optimise:** meshopt and WebP.
- **Phone tier:** a lite copy of every GLB with capped textures. Phones crash on about 2 GB of texture
  memory.
- **Packaging:** GLBs go into an artifact as base64 text files, with a per-file and per-publish size
  limit, so publish in batches.
- **Scale check:** run it and require a pass before committing.
- **Commit:** checkpoint-commit finished work often, because the container can restart.

### 12. Feed the library

After an asset is accepted, update the style:
- new kit parts go into the catalogue;
- prompts that worked go into `prompts.md`;
- any rule a reviewer had to enforce goes into `STYLE.md`;
- surprises go into `lessons.md`.

The next asset should start where this one ended. Skipping this step is how a family drifts apart.

## Working with the user

- Show images, not file paths: the user may be on a phone. Send HD renders and before/after sheets, and
  publish the scene as an artifact.
- When the user gives taste feedback ("mushy", "wobbly", "looks too big", "make it look alive"),
  translate it into a measurable property, fix that property, and show it moved. Keep what they
  praised: the user's "much better" is a constraint for the next pass.
- For long autonomous runs, notify when done, and state clearly what passed review, what did not, and
  what you chose not to do.
- Track fal spend against the budget and record every job in the pipeline record
  (`pipeline/fal-pipeline.json` or the style's equivalent).
