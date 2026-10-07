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

**The photographic weathering library** `[mill v6 r14]` (the method that replaced 13 rounds of procedural grime):
- Four fal PATINA sets, generated once for all buildings (`fal-pipeline.json` `v27_mill_weathering`, prompts in
  `prompts.md` "Weathering library"): `wxCladding` (streaked off-white cladding with rust drips), `wxSteel` (grimy
  gunmetal plate), `wxConcrete` (stained slab, oil spots), `wxRoof` (sooty roof sheeting). square_hd, upscale 2,
  tiling both, maps basecolor / normal / roughness / height. Downloads go to their own scratch folder and are converted
  with `python3 -I` (`wxprep.py`) into `tools/blender/buildings/weather/<set>/{base.jpg, rough.png, height.png}` at 1024
  (build-time only, never shipped).
- `cpaint.PHOTO` maps each zone to (set, tile m, k value, k chroma, k roughness, height m): cladding 4.8 m, steel 2-2.5 m,
  concrete 9.2 m, roofs 6 m. The set is box-filtered to the zone's texel density before sampling (no moire) and
  modulates the calibrated zone colour by its relative luminance (mean 1), so paint-check holds. Each tile row gets its
  own horizontal offset (no visible repeat). The photo's own panel joints are removed (`_unline`), or they double the
  kit's seams into a tile grid.
- The hull shader (`lib._wx_photo`) box-projects the joint-free variants (`base_clean.jpg`) the same way on kit blocks
  and the plinth.
- A spec can override per zone: `'photo': (set, tile, kc, kch, kr, kh)` or `None`.

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

- `[mill v6 r7]` (r5 judge B): streak density varies per 2.4 m panel and course (0.25-1.75x) with a random start
  under the seam, or the same streak pattern reads as a repeating strip; dark steel needs mottling (`blot` 0.14,
  `tone` 0.12) and a bright bare-steel edge colour (EDGE_DARK sRGB 0.58) or the wear is invisible; AO grime 0.45 and
  ORM occlusion `0.1 + 0.9 * ao^1.3` for contact shadow at bases and brackets.
- Window reveals: `ckit.window_frame` (head, deeper sill, jambs 10 cm proud) with the glass 10 cm in; a lit card
  flush with the wall reads as a flat cream sticker.
- Big frame members belong in a crisp set: the furnace's leg trims and posts were 'frame' in the 13 px/m main atlas
  and read as "a blocky stretched texel mosaic" (r5 judge B); `leg_trim` / `post_mat` 'frame2' put them in set 3.
- Two instances of one part show identical paint (the two shed segments): acceptable at the hero view, but keep the
  instance's distinct faces (doors, dock) on the visible side.

- Per-part main-set UV weights (`ckit.UV_W[name]`) `[mill v6 r10]`: once a hero's light shell and big members have
  their own sets, its main atlas holds only dark structure, plinth and pipes; weighting frame 0.95 / pipeDark 0.9 /
  concrete 0.55 there lifted the furnace frame 6.4 -> 12.0 px/m at 2048 (~24 at 4096).

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
- **"Mostly enclosed", not "a cone in a derrick"** `[mill v6 r7]`: legs on the DIAGONALS close to the drum (centre
  ~ drum radius + 3 m, 3.6 -> 2.8 m plated boxes, trims in the crisp frame2 set), slim plated posts following the bell
  (no square ring beams, no X frame, no square top deck: they cut the shell or read as a derrick), ring decks, risers
  up the cone, a dark plated base band under the light drum. Tap-hole bays must move off the diagonals with the legs
  (`taps_a0`). The concept's stacked bands (dark top / light cone / dark bosh / thin glow slit / light drum / dark base)
  are the furnace's read; check them on the preview.
- **The crown is stepped dark drums** `[mill v6 r8]`: drum, ring deck, narrower drum, dark cap, uptakes rising
  straight beside the drum and turning in to a header. A light cap inside looping uptakes read as "a lantern".
- **Lamps everywhere small** `[mill v6 r8]`: plinth pins every ~4.6 m, pins up the hero's legs every 6 m, lamps on
  every ring deck; a few big floods are not the concept's "many small warm lamps".
- **Attached annexes, not cabins** `[mill v6 r7]`: 2-3 larger light blocks (8-15 m) against the hero and the sheds
  (a 15 m annex under the hero's elbow pipe, a 10 m one beside it, one on the shed's end by the process bay), never a
  free-standing control house on the apron.
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
- Pour strip: wide enough to light the ground (runner 3.6 m with a 0.9 m hot core, its spill 260 cd / 18 m at 2.6 m).
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
**Round scripts and times** `[mill v6]` (4 CPU threads): a review round = remodel the changed parts at `--tex 2048`
(1.5-5 min a part; all five ~11 min), `colony_build.py --tex 2048 --samples 6` (~1.5 min), four shots at 1600 x 1000
(concept camera ~2 min, each close-up ~2-3.5 min; ~9 min); total ~22 min, ~12 min for a building-only change. A part
preview is ~40 s. Keep the round driver as a script (`round.sh <tag> [parts]`: remodel -> build -> shots, each step
logged) and a sheet maker (concept | previous | current; close-ups). Run one heavy job at a time; poll the round log
for a `done` line.

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
| Big structural members look like a blocky mosaic up close | they share the main atlas with the lattice (13 px/m) | put them in the crisp set (frame2 / its own SPLIT set) | mill v6 r5 |
| Window looks like a flat cream card | lit card flush with the wall, no frame | `window_frame` + glass 10 cm in | mill v6 r5 |
| A slab edge reads thin | dark 1.6 m body under a 0.34 m light kerb | `plinth(h=2.0, kerb_h=1.1)` | mill v6 r7 |
| "No lit chamfer line on structural steel" (r2, r5, r7 judges) although chamfers were added | the chamfers exist (flat-shaded debug shot shows them) but dark matte albedo + one roughness hides the highlight; chipped wear only marks a few edges | `cpaint` continuous edge line: convex curvature (0.05-0.18) lightens dark steel 55 % toward bare steel, roughness -0.25, metal +0.5; CHECK: render the part flat (`remodel.py --preview`) and textured (`render-glb.mjs --w 2400`) side by side and crop an edge | mill v6 r8 |
| Streaks and joints "run diagonally" on a cone (r7 judge B) | the paint's arc coordinate was angle x the texel's own radius, which drifts in angle as the cone narrows | `axis_r`: angle x a fixed radius (generators stay straight up the slant); CHECK: the painted joints run parallel to the cone's silhouette in the close view | mill v6 r8 |
| A big pipe bend kinks at 1:1 | 4 fillet segments per bend; a closed ring capped at its joint | 8 segments for r > 0.5 m (bkit `tube`); closed rings `caps=False` | mill v6 r8 |
| A shed roof shows dark stripes along the ridges | full-length louvred monitors | half-length, lower monitors (`monitor` (5.6, 14, 1.6, 0.5)) | mill v6 r8 |
| A parameter silently not applied | an edit appended a key inside a trailing comment (`# ... 'monitor': ...`) | after editing a parameter dict, print the effective value (`python -c 'import ckit; print(ckit.SHED_V6[...])'` in the venv) | mill v6 r8 |
| "Grit" fails at the concept camera round after round | every weathering layer was sub-metre (seams, 9-22 cm streaks, chips): at the concept camera a panel is ~6 px, so it averages to a clean tone | `cpaint.macro`: per bay x storey panel value +-12-15 % (`mpanel`, `mtone`), soft streaks 0.8-1.6 m wide and 3-10 m long from storey lines (`mstorey`, `mstreak`), a top-down soot gradient on tall elements (`soot_top`), base grime to ~2 m (`mbase`); the hull shader (`lib._grit`) carries the same; CHECK on the concept-camera render (paint-check + a crop next to the concept), never on the close-ups | mill v6 r10 |
| Streaks show as blocky bars with hard texel steps | 9 cm columns with hard sides = 2-4 texels; one column grid on every course | columns 16 / 40 cm, sides softened over a quarter width, grid shifted per course | mill v6 r10 |
| The same grime pattern repeats on every part | every part painted with the same seeds | per-part seed from the work folder name (`pseed`) | mill v6 r10 |
| Small curved props read as wood (a barrel, a hut) | fixed-pitch plate seams and streak columns on objects under ~3 m | no seams / column streaks on small props: 1-2 welded courses, mottling, metal roughness | mill v6 r10 |
| Edge line only on some parts | narrow flange / trim islands (< 0.25 m) stacked into a shared swatch (random geometry per texel); 5 cm curvature radius too tight | `STACK_NARROW` 0.12, curvature bake radius 8 cm, edge line from curvature 0.03-0.12 | mill v6 r10 |
| A ring main shows a kink and open ends | a closed tube path has a joint | revolve a circle profile (`bustle_torus`): a true torus, no joint | mill v6 r10 |
| The plinth sits off-centre / the apron reads "spread" | an edit appended a comment mid-call and swallowed the `centre=` argument (r1 -> r12 unnoticed) | never append comments inside a call's argument lines; after a round, grep for `#.*key=` / `#.*'key':` in edited lines | mill v6 r12 |
| "Evenly lit, a toy / diorama" (judge A) | a strong fill (1.5) lifted the shadow side 1.2x over the concept's | lower fill / env, raise key to keep the light band; measure with grit-check `shadow` | mill v6 r12 |
| Moire grain on a wall at review size | 8 cm bolt heads on a 25 px/m texture (2 px): aliasing | band-limit fine features by texel density (`cpaint` bolts fade below ~3 texels a head) | mill v6 r12 |
| Streaks read as soft rectangular stamps | constant-width columns | taper the width down the run and wobble the centre line (`vstreaks` r12) | mill v6 r12 |
| Procedural grime reads "synthetic, tile-like", whatever the amplitude (judges r2-r13) | noise and hash fields have no photographic structure | the photographic weathering library (above); keep procedural layers for seams, edges and macro tone | mill v6 r14 |
| Walls read as a window / tile grid | 9 cm dark seams + halo, plus the photo's own joints | seams 6-7 cm at 0.5-0.6, halo 0.12-0.16; remove the photo's joints | mill v6 r14 |
| A kit block's wall is "a smeared photo" at 1:1 | the hull's single smart projection gave the 80 x 92 m plinth most of the atlas | the hull uses `remodel.unwrap` (stacking, concrete weighted 0.3) | mill v6 r14 |
| A big pipe "comes out of the housing for no apparent reason" (user, correction 45) | the gallery's gas main dropped behind the foot tower and ended at 3 m in the air; drops, mains and bundles elsewhere also had free ends | route each run source -> destination with flanges and supports (`GALLERY_V6['pipe_support']`, `pipe_bundle(drop_end=)`, `pipe(support_pitch=)` now ceil-spaced); audit on a top + rear view | mill v6 r18 |
| A multi-part remodel dies on the second part with `ReferenceError: StructRNA of type Image has been removed` | a module-level cache of a bpy image outlives the scene reset between parts | validate cached datablocks (`.name` in try / except ReferenceError) and reload | mill v6 r15 |
| Molten trough still a pale peach slab after the AO heat gradient | on a flat open trough the AO is high everywhere: heat ~1 over the whole stream, the crust suppressed, emission clipped above the tone-map knee | with a crust, heat is a minor term (x 0.35); open metal from noise + a narrow glow core; crust plates near black with bright cracks; body x 0.55-1.0 below the knee; check the part's emit texture, not only the render | mill v6 r16-r17 |
| A fine regular dot grid on large lit walls at close views ("moire"), unchanged with `?ao=0` and `?finish=off` | key-light shadow acne through the Vogel-disk PCF (normal bias radius / 2000 is too small for a 90 m building) | studio hint `shadowNB` (normal bias x 6 for the mill; `?snb=` to calibrate); textures were clean (checked by extracting the GLB images) | mill v6 r18 |
| Photo weathering pulled the light band to 0.76x | the photo's grime darkens the average under the ratio | recalibrate the key on the main shot with URL overrides (`?key=&keycolor=&fillcolor=`), not a repaint | mill v6 r16 |
| Molten metal reads as flat orange paint | one emissive tone | AO-driven heat (yellow-white in the open stream, deep red at the trough walls), crust with bright cracks | mill v6 r14 |
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
| G0 | Grit, measured | `python3 tools/buildings/grit-check.py <concept> <render> tools/buildings/grit-regions/<id>.json`: per surface (hero shell, wall, roof, plinth) luminance std and high-pass energy, render / concept; regions must be BARE surface (no posts, pipes or edges: structure dominates the variance) | each ratio 0.8-1.2 `[r12]` |
| M1 | Mood, measured | grit-check `shadow`: the darkest 20 % of the building's pixels, render / concept | 0.8-1.2 (the mill: fill 1.5 gave 1.20 = "evenly lit, a toy"; fill 0.6, env 0.5, key 1.15 gave ~0.97) `[r12]` |
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
| P1 | Pipe logic (correction 45) | trace every run on a top view (`?az=0&el=89`) and a rear view: crown uptakes, downcomer, gas mains, stack-base pipework, wall and roof runs, yard bundles | every run traced from a source (vessel nozzle, header, valve, pump skid, building wall) to a destination (vessel, stack inlet, building wall, buried service through a curb); flanged ends; no run through unrelated geometry (a housing, gallery, wall or roof it does not serve); a support, saddle, bracket or stool at least every 6 m; nothing ends in the air `[r18]` |
| I1 | Thumbnail | `thumbs.mjs` | aspect <= 1.5, fill >= 0.6, signature shapes readable at 40 px |
