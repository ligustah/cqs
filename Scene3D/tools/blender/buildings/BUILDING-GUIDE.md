# BUILDING-GUIDE: a colony building from concept to release

The single entry point for the 16 colony buildings (`style-library/styles/cqs-fleet/briefs/buildings.md`). Follow it
top to bottom; it is enough to run the whole process. Details live in:
- `README-colony.md`: the stage details, the component catalogue, the remodel kit, the phone table;
- `README-bkit.md`: the kit's frame, materials and functions;
- `style-library/styles/cqs-fleet/STYLE.md` sections 1, 2, 4, 5, 7, 8: the rules and the review protocol this guide
  extends;
- `style-library/styles/cqs-fleet/lessons.md`: the history behind each rule.

This guide is living: every step, setting and fix that worked and every trap hit goes in **in the round it was learned**,
tagged `[mill vN rM]` (building, version, round). The pilot is the steel mill (v4-v6).

Conventions: `PY` = the venv python with bpy 5.x, numpy, pillow
(`scratchpad/blender-venv/bin/python`); paths from `Scene3D/`; `$W` = a scratch work dir (never in the repo).
Run heavy Blender jobs one at a time, in the background, with a log (`nohup ... > $W/x.log 2>&1 &`).

## 0. Targets (read before building)

The target is "very similar vibes" with the concept (STYLE section 2): silhouette, mood, grit, density and warmth match
at a glance at the concept camera. Not a pixel match. Every number in the checklist (section 9) is measurable.

## 1. Stage A: sizes and the concept camera (15 min)

1. Real-world sizes from the concept's rulers (doors 1 x 2 m in a 1.4 x 2.4 m frame, rails 1.1 m, figures 1.8 m).
   Record `SPEC` footprint and height.
2. **The concept camera from the plinth edges** `[mill v6 r0]`. Measure, on the concept, the screen slope (dy / dx) of
   the two plinth edges from the near corner: `s1` (the edge running along X, to the left) and `s2` (along Z, to the
   right). Orthographic: `sin(el)^2 = s1 * s2`, `tan(az)^2 = s1 / s2`. The concepts are drawn with a **long lens**:
   use `fov` 22 (the default 38 exaggerates the plinth's near corner and reads ~10 degrees higher than asked).
   Mill: s1 0.30, s2 0.24 -> az 48, el 12-15, fov 22. Eyeballing "about 20-27 degrees down" was wrong by 10+ degrees.
3. Put it in the module's studio hint (`src/buildings/<id>.js`):
   `studio: { az, el, fov, dist, sunaz, sunel, key, fill, keyColor, fillColor }` (`fov`, `keyColor`, `fillColor` are
   read by `main.js` for buildings `[mill v6 r0]`). Check the frame: the plinth spans ~95 % of the frame width, as in
   the concept. Test lens and angle on the existing GLB before any rebuild (`?az=&el=&fov=&dist=` on the URL: 100 s a
   shot).

## 2. Stage B: turnaround (5 min, optional)

`README-colony.md` B (nano-banana-pro/edit, 4K). Use the elevations for heights only; the turnaround's plan is
unreliable.

## 3. Stage C: components (15-40 min each)

`README-colony.md` C. Every fal job goes in `Scene3D/pipeline/fal-pipeline.json` (`v24_buildings`); never re-submit
(poll `check_job`, then `get_job_result`). fal meshes are blueprints: anything over ~3 m is rebuilt in stage R.

## 4. Stage R: remodel every large component (20-60 min a part)

`README-colony.md` "Component remodel" has the full recipe. The short form:
```sh
$PY tools/blender/buildings/cmeasure.py <name> $W/m-<name> --res 0.07                 # measure the blueprint
$PY tools/blender/buildings/remodel.py <name> --preview $W/<name>.glb                  # geometry, flat colours
node tools/render-glb.mjs $W/<name>.glb $W/p-<name> --angles "35:15"                   # 40 s: look before baking
$PY tools/blender/buildings/remodel.py <name> [...] --tex 2048 --work $W               # review bake (1-4 min a part)
$PY tools/blender/buildings/remodel.py <name> [...] --work $W                          # final (registry size, 4096 heroes)
```
Defaults that worked: the builder's parameter dict in `ckit.REMODELS`; 72 segments round hero shells; bevels 2-6 cm;
texel weights in `remodel.UV_WEIGHT`; the hero's light shell in its own texture set (`ckit.SPLIT`).
Fit the **concept's** stations and light / dark rhythm; the blueprint gives only the envelope and anchor.

## 5. Stage D: the building script (30-40 min)

`README-colony.md` D, `README-bkit.md`. Signature shapes first, then the secondary layer, then the clutter pass
(section 5a), then the lights.

### 5a. Clutter pass (the concept's density) `[mill v6 r1]`
See section 9 "Density". Work round the plinth in 15 m steps at the concept camera; every step that shows bare slab
gets kit parts at true scale: pipe runs on stools with valves, crates and pallets, skids, cabinets, ladders, stairs,
railings, small sheds, lamp posts, figures, a vehicle.

## 6. Stage E: build, compare, iterate

```sh
$PY tools/blender/buildings/colony_build.py <id> $W/b --tex 2048 --samples 6      # review build (~70 s)
node tools/buildings/compare.mjs <id> --version rN --w 1600 --h 1000 --out $W/<id>-rN.jpg \
  --extra "furnace=focus=x,y,z&dist=m" --extra "pour=..." --extra "wall=..."      # concept camera + close-ups
python3 tools/buildings/paint-check.py ../style-library/styles/cqs-fleet/images/buildings/<id>-concept.jpg \
  shots/buildings/<id>-rN.png
$PY tools/blender/buildings/colony_build.py <id> $W/b --tex 4096 --samples 10     # final (~10 min)
```
Each round: the concept | previous | current sheet, the three close-ups, the checklist review (section 9), two
judges (vibes; real-time quality at 1:1), fix the largest gap first. Stop when two rounds in a row bring only
marginal gains and both judges say "close enough".

## 7. Stage F: release checks

```sh
node tools/build-artifact.mjs                                  # "package check: ... match their source", no FAIL
node tools/pkg-diff.mjs --csp 1 --units 16 b_<id>              # desktop <= 2 %
node tools/pkg-diff.mjs --device phone --csp 1 --units 16 b_<id>   # phone <= 6 %
node tools/phone-check.mjs <id>                                # heap+gpu < 300 MB, tris <= 150k, fetched <= 7 MB
```
Then the evidence images (`images/buildings/<id>-vN.jpg`, `-vN-close.jpg`, `-vN-thumbs.png`), README-colony,
lessons, REMODEL-PROGRESS.

## 8. Gotchas (symptom -> cause -> fix)

| Symptom | Cause | Fix | Tag |
|---|---|---|---|
| The render looks 10 degrees higher and more distorted than the concept at the "same" az / el | default fov 38 (short lens) vs the concept's long lens | studio `fov` 22, el from the plinth slopes (section 1) | mill v6 r0 |
| A warm key turns the dark steel brown | `keyColor` saturation also tints the gunmetal | keep `keyColor` mild (sRGB sat <= 0.15); measure dark steel sat <= 0.1 | mill v6 r0 |
| Light band 0.8x the concept in `paint-check` | dusk key trimmed (`key` 0.6) for v3's light roofs; the v5 paint is darker | raise key / fill in the hint, not a paint lift | mill v6 r0 |
| Furnace shell blotchy, not streaked | streaks were stretched fbm noise (soft, patchy) | crisp per-column vertical streaks from seams (`cpaint` `vstreak`) | mill v6 r1 |
| Rails / braces glow orange at 4096 only | a tiny emissive island packed inside a stacked swatch | stack lamp lenses too; check the final size | mill v5 |
| Glow box reads as a solid orange slab or sticker | glow box thicker than 0.1 m, or square over a round surface | thin glow boxes for runners and openings only; emissive paint for round hot surfaces | mill v4-v5 |
| Black scaffold round a thin cylinder | a lattice tower around the hero shape | broad light hero shape in front, slim posts, lattice only at the top | mill v5 |
| Plinth top culled | culling with too few samples, first-hit test | `remodel.cull_buried` winding numbers, dense samples; re-preview | mill v5 |
| Atlas 37 % full | thousands of thin islands each paying a margin | stack thin / hollow islands (`remodel.unwrap`) | mill v4 |
| Dark mains vanish | near-black pipes on the slate backdrop | mid-grey `pipeDark` (sRGB ~0.42, metal 0.3) | mill v5 |

## 9. Family checklist (extends STYLE section 8; each round: pass / fail with evidence)

STYLE section 8's rows all apply (quality bar, concept fidelity, paint, type spec, thumbnail, texel density, geometry,
lights, package, pkg-diff, phone). The colony-building rows on top of them:

| # | Property | How to measure | Pass |
|---|---|---|---|
| C1 | Camera | plinth edge slopes on the render vs the concept | each within 0.05 |
| C2 | Framing | plinth width / frame width at the concept camera | 0.85-1.0 (concept 0.97) |
| C3 | Silhouette | side by side at 1600 x 1000 | same signature shapes in the same places (hero forward-left etc.) |
| G1 | Streak crispness | close-up wall crop | vertical streaks with hard sides (<= 3 px edge at 1:1), sourced at seams / edges |
| G2 | Roof soot | concept-camera crop of the roofs | roofs read mid-grey-warm, not white; dark lap lines visible |
| G3 | Plinth staining | concept-camera crop of the slab | visible stains, darkening at wall feet and joints |
| G4 | Panel edges | close-up | darkened seams on every light panel |
| W1 | Warmth / tonality | `paint-check` | light band 0.9-1.1x concept, hue within 10 deg, sat within 0.05 |
| W2 | Dark steel | `paint-check` mid band / crop | sat <= 0.1 (neutral, never brown) |
| D1 | Density | count kit items per 100 m2 of visible apron at the concept camera | >= 1 per 100 m2; no bare run > 15 m |
| L1 | Process glow | concept camera | the hero glow is the brightest area; spill visible on adjacent ground / structure |
| L2 | Lamps | concept camera | warm lamps along plinth edges, block corners, pilasters |
| T1 | Texel density | `remodel.py` px/m report | light >= 50, hero >= 70, dark structure >= 25 |
| T2 | Close crispness | close-up crops at 1:1 | a 5 cm seam >= 2 px; no blur on dark legs |
| I1 | Thumbnail | `thumbs.mjs` | aspect <= 1.5, fill >= 0.6, signature shapes readable at 40 px |
