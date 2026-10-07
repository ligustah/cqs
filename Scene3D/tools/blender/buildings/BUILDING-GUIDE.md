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
   But AI concepts are not consistent projections: the mill's plinth slopes say el ~7, its roofs and plinth top say
   ~15-20. el 8 / 5 made the plinth a sliver and hid the roofs `[mill v6 r5]`; settle by eye between the two.
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

**Grit paint (`cpaint.py` layers, on by default through `ckit.WORKS`)** `[mill v6 r1]`:
- `vstreak` (0.5-1.0): crisp vertical streak columns (9 and 22 cm wide, hard sides), each from a course seam
  (`course`, else `vsrc`, else 2.4 m) fading down over 0.4-3.4 m; ~25 % are rust, the rest grey-brown grime
  (`STREAK_C`). This replaced the soft fbm `streak` (keep it <= 0.1): fbm streaks read blotchy, not streaked.
- `halo` (0.1-0.15): plates darken toward their seams (the concept's darkened panel edges).
- `soot` (0.9 roofs, 0.3 dark membranes) with `lap` (2.9 m): soot patches, dark lap lines across the slope, a drip
  band under each lap and short soot streaks down the slope; only on up-facing faces (n.y > 0.3).
- Light paint a step greyer and darker (WORKS shell / clad / panel sRGB ~0.73 / 0.70 / 0.66), frames a step lighter
  (~0.36-0.40): the concept's lower contrast; the studio key then lifts the whole (section 6, studio).
- The hull bake (`lib.material`, `lib.BAKE['grit']`, set by bkit) carries the same idea for kit blocks: 12 / 28 cm
  streak columns from 3 m course lines on light walls, and stained concrete (broad damp stains, oil spots, an
  overall dusty grey) on the plinth. Plinth slab joints every 4.6 m (`plinth(slab=4.6)`), as in the concept.

**What reads as quality at 1:1** (r2 judge B) `[mill v6 r4]`:
- No soft fbm run-off or smeared drips: they read as UV stretch. Only crisp column streaks (`vstreak`).
- Roughness must vary: per-zone base (`rough`: clad 0.7, shell 0.66, frames 0.62-0.72, pipes 0.42 metal 0.45, amber
  0.45) plus patches and mottling (`cpaint` r4); edge wear wide enough to see (curvature 0.04-0.22, chips 0.26-0.5).
- A faint oil-can dent in the normal map of light plates (2.5 mm).
- Bolt heads 8 cm (5 cm ones were < 2 px at the close views).
- Chamfers: bkit boxes >= 0.3 m get up to 6 cm, I-beam flanges 2.5 cm; tori and round mains at >= 72 x 18 segments
  (40 x 14 showed stepped specular).
- Camera check: at fov 38 the close view's pixel is ~2.3 cm at 34 m, 3.2 cm at 46 m: a 5 cm feature reaches 2 px only
  at <= 34 m. Set the close-up distances so the 2 px test can pass at all.

**Texture sets** `[mill v6 r1]`: `ckit.SPLIT[name]` may list several sets, `[({'shell'}, 4096), ({'frame2'}, 4096)]`
-> materials `colony_<name>_2`, `_3`. The furnace's dark legs and bosh (frame2) went 28 -> ~59 px/m at 4096 in
their own set. Each set is one material with 4 maps (sampler limit 16 holds); the phone copy caps all at 512.

## 5. Stage D: the building script (30-40 min)

`README-colony.md` D, `README-bkit.md`. Signature shapes first, then the secondary layer, then the clutter pass
(section 5a), then the lights.

### 5a. Clutter pass (the concept's density) `[mill v6 r1]`
Work round the plinth in 15 m steps at the concept camera; every step that shows bare slab gets kit parts at true
scale. Kit (`bkit.py`, all boxy and cheap): `pallet(B, p, rot, load='sacks'|'boxes'|'plate'|None)`, `drums(B, p, n)`,
`pump_skid(B, p, rot, scale)`, `gas_bottles(B, p, n, rot)`, `pipe_bundle(B, ground_pts, n=3, r=0.22)` (parallel pipes
on concrete stools with flanges and amber rings), plus `crate`, `cabinet`, `valve`, `stair`, `ladder`, `railing`,
`lamp_post`, small `block` sheds (4-5 x 3.2-3.6 x 3.6-4.4 m, `frame='frameL'`), `worker`, `forklift`, `truck`.
Write them in one `clutter(B)` function at the end of the building script, grouped by apron zone with a comment
giving the zone's extent (x / z range), so collisions can be checked by reading.
- Before placing, list what is already there (pipes on stools, stairs, crates of earlier rounds): the mill's first
  clutter pass put pallets on top of the cooling main along the furnace front. `[mill v6 r1]`
- Cost: ~80 items added ~19k triangles to the hull (27k -> 46k). Watch the phone budget (150k). `[mill v6 r1]`
- Lights in the same pass: plinth edge pins every 9 m (`plinth(lamp_pitch=9)`), lamp posts every ~20 m on the
  visible edges, and the process glow's spill (`B.R.spill`, section 5b).

### 5a2. Massing and composition rules `[mill v6 r4]`
- **The hero tower is compact.** Heavy legs and posts stand near-vertical and tight to the shell (frame half-width
  ~ shell radius + 1 m), railed decks at 2-3 levels, the frame stops at the hood deck; the narrow upper stack carries
  its own railed ring platforms. Raking legs that spread out and posts that converge to a high top read as a
  "spidery derrick / open A-frame" (r2 judges), the biggest silhouette miss of the mill.
- **Detail sits on the main masses, not scattered.** Free-standing huts, a parked trailer and an office-like block
  in front of the hero read as scattered props (judge A). Prefer: low light blocks against the hero's foot, stacks of
  plate / coils / pallets by the walls and the runner, roof machinery on the sheds.
- **Roofs:** shallow (~14 deg), light grey with dark laps, broken into bays by dark gable parapets
  (`gable_shed` `parapet`); a steep 26 deg roof showed a big gable face and read dark.
- **Low blocks between the hero and the process bay** (7 m, doors / louvres, no office window strip).

### 5b. Process glow `[mill v6 r1-r4]`
- Hot surfaces: zone `hot` (emissive paint) + thin glow boxes (`K.glow_ring`, `B.R.glowbox`, < 0.1 m thick).
- A band reads as a band only with few, thin posts in front of it: 12 tuyere stocks round a 9 m hearth, not 20-32
  (those read as a lit window grid).
- Glow colour: high radiance on an orange tone-maps to salmon / peach (#ff8a28 / #ff6c08 at 2.6: judge A "a wide
  pale-peach section"), and a deep red-orange (#ff6200 at 1.6) still reads pink-red because red clips first. What
  reads molten: a yellow-orange (#ffa03c) at ~1.2 on the glow boxes, the emissive paint carrying the deep orange.
  Spill lights the same yellow-orange, low (4-5 m) and weak (~110 cd / 14 m): a red spill on light paint reads pink.
  `[mill v6 r3-r6]`
- Spill on the ground and structure: `B.R.spill(p, color, intensity, distance)` -> a runtime point light
  (`colony.js` `spills` -> `interiorLights` kind 'point'). Defaults that worked: hearth 300 cd / 20 m placed 1.5 m
  outside the band toward the camera; runner 180 cd / 16 m, 3 m over it. 900 cd / 34 m washed the whole furnace
  foot and the shed gable orange (r1). 1-3 per building.

## 6. Stage E: build, compare, iterate

```sh
$PY tools/blender/buildings/colony_build.py <id> $W/b --tex 2048 --samples 6      # review build (~70 s)
node tools/buildings/compare.mjs <id> --version rN --w 1600 --h 1000 --out $W/<id>-rN.jpg \
  --extra "furnace=focus=x,y,z&dist=m" --extra "pour=..." --extra "wall=..."      # concept camera + close-ups
python3 tools/buildings/paint-check.py ../style-library/styles/cqs-fleet/images/buildings/<id>-concept.jpg \
  shots/buildings/<id>-rN.png
$PY tools/blender/buildings/colony_build.py <id> $W/b --tex 4096 --samples 10     # final (~10 min)
```
**Studio calibration** `[mill v6 r1]`: test lighting on the installed GLB with URL overrides (`&key=&fill=&keycolor=
ffeedd&fillcolor=`) and `paint-check` each; then write the winner into the studio hint. Mill: key 0.85, keyColor
#fff0e0, fill 1.5, fillColor #e8e2da -> light band 0.90x, all 0.99x, hue 27.5 (concept 23). A saturated key
(#ffd9ac) pushed light sat to 0.24-0.32 (concept 0.16) and browned the frames.

Each round: the concept | previous | current sheet, the three close-ups, the checklist review (section 9), two
judges (vibes; real-time quality at 1:1), fix the largest gap first.

**Judges** `[mill v6 r2]`: fresh subagents with no build context. Judge A (vibes, blind) sees only a
concept | render sheet and answers match / no match for silhouette, mood, grit, density, warmth, plus the top 3
gaps. Judge B (quality) sees the close-up sheet and the raw 1600 x 1000 close renders against STYLE section 2.
If the session cannot spawn subagents, ask the coordinator to run them (SendMessage to main) and keep building.
The judges found what self-review missed in r1-r2: the derrick silhouette, the scattered props, the salmon glow,
smeared streaks, uniform roughness. Run them from round 2 at the latest. Stop when two rounds in a row bring only
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
| A wait loop never ends | `pgrep -f <script>` matches the waiting shell's own command line | wait on a pid (`wait`, or `kill -0 $pid`) or a log line, never `pgrep -f` with the script name | mill v6 r1 |
| Clutter lands on top of earlier dressing | positions placed without reading the earlier rounds' items | group clutter by apron zone with extents in comments; read the zone before adding | mill v6 r1 |
| The whole furnace foot glows orange | spill light too strong / far reaching (900 cd, 34 m) | 300 cd, 20 m, just outside the band | mill v6 r1 |
| Hero glow reads pale salmon / peach | high radiance on a light orange saturates in the tone curve | deep orange (#ff6200) at ~1.6 | mill v6 r3 |
| Streaks read as "UV stretch" | soft fbm streaks / drips stretched 20:1 vertically | crisp column streaks only (`vstreak`); `streak` 0, `drip` 0 | mill v6 r4 |
| Everything has the same satin look | one roughness per zone, no variation | per-zone `rough` + patch / mottle variation + wider edge wear | mill v6 r4 |
| Light band falls 0.76x after a plinth pass | a big plinth darkened by a uniform dust term | keep the plinth's mean near the kit value; stains carry the grit | mill v6 r3 |
| Furnace top cut by the frame | `dist` < 1 at the 16:10 review frame | dist 0.95-1.0 (frameView fits with margins) | mill v6 r2 |
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
| C1 | Camera | plinth edge slopes on the render vs the concept, and by eye (roof tops visible as much as on the concept) | slopes within 0.15 (AI concepts are not consistent projections: by eye wins) `[r1]` |
| C2 | Framing | whole plant inside the 1600 x 1000 frame incl. the hero's top; plinth width / frame width | nothing cut; 0.8-0.95 `[r2]` |
| C3 | Silhouette | side by side at 1600 x 1000 | same signature shapes in the same places (hero forward-left etc.) |
| G1 | Streak crispness | close-up wall crop | vertical streaks with hard sides (<= 3 px edge at 1:1), sourced at seams / edges |
| G2 | Roof soot | concept-camera crop of the roofs | roofs read mid-grey-warm, not white; dark lap lines visible |
| G3 | Plinth staining | concept-camera crop of the slab | visible stains, darkening at wall feet and joints |
| G4 | Panel edges | close-up | darkened seams on every light panel |
| W1 | Warmth / tonality | `paint-check` | light band 0.9-1.1x concept, hue within 10 deg, sat within 0.05 |
| W2 | Dark steel | `paint-check` mid band / crop | sat <= 0.1 (neutral, never brown) |
| D1 | Density | count kit items per 100 m2 of visible apron at the concept camera | >= 1 per 100 m2; no bare run > 15 m |
| D2 | Detail placement | concept camera | detail gathered on / against the main masses and the process; no free-standing huts or parked vehicles as filler `[r4]` |
| S1 | Hero structure | concept camera | compact: frame tight to the shell, near-vertical, decks at 2-3 levels, no wide splayed legs `[r4]` |
| L1 | Process glow | concept camera + crop | the hero glow is the brightest, a saturated orange (not salmon / peach); spill visible on adjacent ground `[r3]` |
| L2 | Lamps | concept camera | warm lamps along plinth edges, block corners, pilasters |
| T1 | Texel density | `remodel.py` px/m report | light >= 50, hero >= 70, dark structure >= 25 |
| T2 | Close crispness | close-up crops at 1:1 | a 5 cm seam >= 2 px (needs close views <= 34 m at fov 38); no blur on dark legs; no smeared streaks |
| T3 | Material variety | close-ups | roughness visibly varies (pipes glossier, frames matte, grime matte); chips on edges; lit chamfer lines `[r4]` |
| I1 | Thumbnail | `thumbs.mjs` | aspect <= 1.5, fill >= 0.6, signature shapes readable at 40 px |
