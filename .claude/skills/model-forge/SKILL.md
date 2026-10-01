---
name: model-forge
description: Build and refine 3D models and asset families (vehicles, ships, buildings, props, characters' gear, any hard-surface asset) with fal.ai image models, image-to-3D reconstruction, headless Blender and a real-time review scene, starting from style exploration with concept art and keeping every asset consistent through a style library that records the user's choices and corrections as constraints. Use this skill whenever the user wants to create, design, redesign, remodel, detail, texture, light or review a 3D model or asset, explore or define a visual style, generate concept art or turnaround sheets, make reusable parts or components, pick a fal model for images, meshes or materials, run review loops on renders, or start a new creation that should match earlier ones, even if they do not say "skill", "fal", "Blender" or "style" explicitly.
---

# Model forge

A pipeline for designing and building 3D assets that hold up under close inspection and stay
consistent across many creations. It is domain-neutral. What a particular project's assets must look like
(forms, palette, scale, lighting, budgets, taboos) is **not** in this skill. It lives in the project's
**style library** as constraints, and it grows from the user's own choices and corrections.

Two ideas carry everything else:
1. **The style is defined with the user, from images, before any modelling.** Generate a few divergent
   concept directions, let the user react, and converge on an approved art bible and written
   constraints.
2. **Every correction the user makes becomes a constraint.** It is recorded in the style library the
   moment it is made, so no later asset, session or agent repeats the mistake.

A third idea is technical, learned the hard way: **image-to-3D is a blueprint, not a product.**
Generated meshes average fine detail into soft lumps. The quality bar was met by rebuilding each model
as clean geometry in headless Blender, using the generated mesh only for measurements, and composing it
from small reusable parts designed once at true size.

## The library

The library lives at `style-library/` in the repo root. Read `references/style-library.md` for its
layout and how to edit it. In short, each style keeps:
- `STYLE.md`: the constraints;
- `corrections.md`: the user's corrections and the rule each became;
- `prompts.md`: prompts that worked;
- `kits.md`: reusable parts;
- `references.md`: approved images;
- `lessons.md`: technical surprises;
- `assets.md`: what has been built.

At the start of any job, find the style the work belongs to and load its `STYLE.md`, `corrections.md`
and `kits.md`. Every agent you start needs the same context: give it the paths, or paste the relevant
constraints into its prompt.

If no style fits, the job starts at stage 0.

## Stages

Every stage ends with rendered evidence that you, or independent reviewers, look at. Advance on what the
images show, not on intent.

| # | Stage | What happens | Reference |
|---|---|---|---|
| 0 | **Define the style** | interview; 3-5 divergent concept directions; the user picks, mixes and corrects; the approved art bible and constraints go into a new style | `references/style-discovery.md` |
| 1 | Brief | the asset's size, role and the style's rulers; what it must read as from the game camera | `references/readability.md` |
| 2 | Concept | variants through `nano-banana-pro/edit` with the style's references; the user approves one | `references/fal-models.md` |
| 3 | Turnaround | one 4K orthographic multi-view sheet, cropped | `references/fal-models.md` |
| 4 | Blueprint mesh | `tripo3d/h3.1/multiview-to-3d` | `references/fal-models.md` |
| 5 | Parts | reuse the style's kits; add missing parts to the kit, not to the asset | `references/parts-kits.md` |
| 6 | Remodel | headless Blender: measure, parametric model, bake, texture-space paint | `references/blender-pipeline.md` |
| 7 | Assemble | place kit parts from a spec; score against the blueprint | `references/blender-pipeline.md` |
| 8 | Look | materials (PATINA), runtime paint and finish, emissives, all to the style | `references/fal-models.md`, `references/readability.md` |
| 9 | Review | standard views, before/after evidence, adversarial judges | `references/review-loops.md` |
| 10 | Release | optimise, lightweight tier, publish, commit | `references/runtime.md` |
| — | **Capture** (continuous) | every user correction goes to `corrections.md`, then into `STYLE.md` as a rule | `references/style-library.md` |

### 0. Define the style (when it is new, or the user wants to change it)

Do not start from a blank prompt. Interview briefly about:
- what the assets are and where they will be seen: the game or scene camera, its distance, daylight or night;
- the mood and period;
- references the user likes or hates;
- hard taboos (IP to avoid, legacy art not to open);
- the budget.

Then generate a **spread** of three to five concept directions, shown from the game's own camera, that differ along real axes:
- form language;
- material and finish;
- colour story;
- realism versus stylisation;
- level of detail.

Show them side by side in one labelled sheet. Ask what the user likes and dislikes in each, mix, and
generate again. Two or three rounds usually converge. Then:
1. Generate the **art bible**: one sheet with the family's key assets, or a key asset with callouts.
2. Create `style-library/styles/<id>/` from `_template/`, add the row to `style-library/README.md`, and
   save the images in its `images/` folder.
3. Write `STYLE.md` from the decisions. Every line is a constraint with its reason.
4. Show the user a short summary and ask what is wrong. That answer is the first correction.

`references/style-discovery.md` has the prompts, the axes, and how to present choices.

### 1-4. From brief to blueprint

- **Brief:** pin down size, role and what the asset must read as, in writing, against the style's rulers
  (the human-scale or domain-scale references the style defines). Scale drift is the most expensive
  mistake, because every later stage inherits it.
- **Concept:** generate with `/edit` and the style's references; show variants, and let the user choose
  and correct. Generate the image you will reconstruct from as evenly lit and matte on a light-grey
  studio background, with no baked shadows. If the style recolours at runtime (e.g. a dark operational
  paint), generate it in light neutral paint, because that reconstructs far better. If the colour is the
  material itself (wood, stone, thatch), generate the real material.
- **Turnaround:** a 4K orthographic multi-view sheet. It keeps the views consistent, and multiview
  reconstruction needs them.
- **Blueprint mesh:** Tripo H3.1 multiview won two bake-offs. Treat its output as a blueprint.

### 5-7. Build

- **Parts first:** list every small or repeated component and reuse the style's kits at their true
  size. Identical small parts across assets are the strongest consistency and scale cue there is.
- **Remodel:** rebuild the asset as clean parametric geometry in headless Blender: volumes, exact
  boolean recesses, small bevels, texture-space paint.
- **Assemble:** place the parts from a spec, and keep the envelope stable.

The pitfalls are long and specific; read the references before you start.

### 8. Look

Materials, any runtime paint scheme, weathering and any emissive lights all follow the style's
constraints (a daylight-only style may have no emissives at all).
The generic principles (what makes an asset read at its true size, how to make it "alive" without it
looking "neon", how lights behave at range) are in `references/readability.md`. The style supplies the
numbers.

### 9. Review

Look at the standard views at matched resolution: **the game's own camera at gameplay distance first**,
then hero, close, range, a lineup with sister assets, and the scene.
Make before/after sheets and 1:1 crops. Use independent judges with opposing lenses, for example
"reads at its true size" against "still as alive as the user liked". Judges default to refuted and
return tested, concrete fixes. Cap the fix rounds. Turn recurring judgements into scripts.

### 10. Release

Optimise, make a lightweight (phone) tier, publish an interactive preview, run the project's checks,
and commit after each accepted step. Cloud containers restart, so keep work resumable.

## Capturing corrections (the part that makes the library grow)

Whenever the user corrects, rejects, prefers or praises something, record it **in the same turn**:
1. **Log it** in `style-library/styles/<id>/corrections.md`: date, asset, the user's words (verbatim,
   short), what was wrong, the fix, and the rule it implies.
2. **Promote it** to `STYLE.md` as a constraint with its reason, if it applies beyond this one asset.
   This covers:
   - a preference ("keep the dark livery as the default");
   - a dislike ("not neon");
   - a scale rule ("a small asset gets fewer windows, never smaller ones");
   - a process rule ("show me renders, not file paths").

   Praise counts too: "the lights make it look much better" protects that look from the next pass.
3. **Keep the rest of the library current:**
   - a prompt that produced the approved image goes to `prompts.md`;
   - a part made during the fix goes to `kits.md`;
   - a technical surprise goes to `lessons.md`.
4. **Say so** in your reply, in one line: "Recorded in the style: …". The user then sees the library
   learning and can correct the rule itself.

Before generating anything for a style, re-read `corrections.md` so the next result already respects it.

## Working with the user

- Show images, not paths: the user may be on a phone. Send HD renders, labelled comparison sheets and an
  interactive preview.
- Translate taste words into measurable properties ("mushy" means facet flatness and bevel width;
  "looks too big" means detail frequency and ruler size). Fix the property, and show that it moved.
- Keep what the user praised; it is a constraint for the next pass.
- For long autonomous runs, notify when done. State plainly what passed review, what did not, and what
  you chose not to do.
- Track spend against the style's budget and record every generation job (model, id, prompt, params).
