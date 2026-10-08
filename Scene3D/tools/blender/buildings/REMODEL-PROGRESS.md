# Steel mill remodel pilot: progress (resumable)

PY=/tmp/claude-0/-home-user-cqs/e592383b-a9f6-5dde-82a6-4494b59b11a7/scratchpad/blender-venv/bin/python
W=/tmp/claude-0/-home-user-cqs/e592383b-a9f6-5dde-82a6-4494b59b11a7/scratchpad/rm   (scratch work dir)

## Done
- Kit: cmeasure.py, ckit.py (furnace, banded_stack, gable_shed, pour_bay, incline_gallery), cpaint.py, remodel.py.
- R1 measure + R2-R5 r1 for all five parts (installed 2026-10-06 23:3x, commit 8703e98).
- r2 kit changes (lap rings, ribbed roofs, pour bay roof deck, molten paint, glTF occlusion) committed 1d6d679, NOT yet run.

- r3 (2026-10-07): remodel.unwrap stacks tiny / narrow islands into one swatch per zone (merge_overlap pack):
  furnace shell 27.6 -> 38.4 px/m at 4096, shed clad 47 -> 52, pour bay 64 -> 76, stack 42 -> 39 (2048), gallery 45 (2048).

- r3 geometry: ckit.FURNACE_V4 (concept stations: light hearth drum, stepped dark bosh, light cone, dark hood, upper
  drum, raking plated legs with ties) and SHED_V4 (panel walls, heavy pilasters, roller + crew doors, no windows).
- r7 bake (r2 kit + r3 unwrap): bandedStack, pourBay, skipGallery installed (furnace/shed from r7 are superseded).
- Preview a part's geometry fast: $W/../uvx/prev.sh <part> "az:el" -> $W/../uvx/<part>-az_el.png

- Fix rounds on the building (2048 review builds r1-r3): dark pour bay deck, lighter gunmetal, low light annex, light
  casthouse front block (steel_mill.py), slimmer tower walkways. README-colony + lessons 56-59 written; remodel --preview.
- v3 evidence shots at fixed cameras: scratchpad/ev/v3-{main,furnace,pour,shed}.png (shots.sh swaps the v3 GLB+js in
  from $W/steel_mill-v3.*, shoots, restores).

- r10 paint pass, final 4096 build (197k tris, 11.6 MB), evidence sheets, thumbnails, build-artifact + package check,
  pkg-diff desktop/phone (--csp 1 --units 16), phone-check: all done 2026-10-07.

## Status
DONE (steel mill pilot). Next building: follow README-colony.md "Component remodel".

## v5: second fidelity round (2026-10-07, user review of v4; scratch $S/v5, logs there)
Review points: 1 furnace silhouette (broad light bell, open light frame, downcomer / uptakes / skip bridge), 2 pour bay
(open portal, amber crane visible, longer brighter runner, control house), 3 density + wear (kit detail on walls,
plinth, furnace base; seam / grime contrast; trailer texture), 4 furnace shell texel density (second texture set),
5 neutral gunmetal.
- S1 geometry (done): ckit FURNACE_V5 (+ _posts_tower, _raking_legs, decks, header, 6-point downcomer), GALLERY_V5
  (open truss + gas main + tall tower), POUR_V5 (partial roof 0.32, bigger crane girder, runner along +Z 22 m, glow
  2.6, control house), SHED_V5 (_shed_dressing: canopies, wall pipes, tray, roof units, ridge vents, dock);
  steel_mill.py layout (furnace z 24, annex / dust catcher / stacks moved, bridge at heading 161.6, base dressing).
- S1 paint/kit (done, not yet baked): cpaint seam_w / streak / drip, neutral GRIME_D / DIRT_D / EDGE_DARK; WORKS
  lighter neutral gunmetal, less yellow light paint; remodel.py cull_buried (REMODEL_FLAGS="--no-cull" to skip) and
  ckit.SPLIT (blastFurnace shell -> colony_blastFurnace_2, own atlas).
- Next: S2 review bake (2048) of the 5 parts + building 2048, compare rounds; truck trailer (yard_kit); final 4096.
- S2 round 1 (2048 review, shots $S/v5/r1-*.png): bell, open portal, crane, control house, bridge all read. Fixes in
  round 2: thinner streaks (streak_f 3.2), finer drips, lighter neutral frames / mid-grey mains (pipeDark metal 0.3),
  tray up to 13 m, ladle glow box dropped, annex + downcomer elbow forward (z 30 / part z 7), building pipes 'pipe'.
- Texel density: remodel.unwrap stacks HOLLOW islands (annuli: area < 12 % of the bbox) and unrolls the split set's
  revolved faces (CYL: 24 sectors x 6 m bands): furnace shell set fill 0.50 -> 0.79, 66 px/m at 4096 (v4 34).
- yard_kit truck: van body detail (posts, rails, rear doors, guards); assets/parts-yard/truck.glb rebuilt.
- S2 round 3 + final (done): culling by winding number (dense samples; first versions culled the furnace plinth
  top), leg corner angles in the strut frame, downcomer onto the annex; final 4096 build. Final showed orange rails
  (lamp lenses packed into the frame swatch): lamps now stacked, final rebuilt (rf2.log / bfin2.log).
- Evidence: images/buildings/steel_mill-v5.jpg, -v5-close.jpg, -v5-thumbs.png. Checks: build-artifact 57 tiers OK,
  pkg-diff desktop 0.00 % / phone 0.01 %, phone-check 137 MB. README v5 section, lessons 60-67.

## Status
v5 DONE (2026-10-07).

## v6: vibes iteration (correction 43-44, 2026-10-07; scratch $S/mill, logs there)
Goal: "very similar vibes" with the concept (grit, warmth, density, composition, glow). Guide: BUILDING-GUIDE.md.
- r0 (camera + warmth, no rebuild): concept camera from the plinth edge slopes = az 48, el 12, fov 22 (main.js reads
  studio `fov`, `keyColor`, `fillColor` for buildings). paint-check on v5 at that camera: light band 0.80x (FAIL),
  a warm key '#ffd9ac' raised light sat to 0.235 (concept 0.164): too warm; tune after the r1 paint.

## STYLE.md proposals (for the coordinator to merge)
- (none yet)

### v6 round 1 (2026-10-07 12:16-13:10; scratch $S/mill: round.sh, shots.sh, sheet.py, pc.sh, shoot-v5.sh)
Changes: cpaint `vstreak` / `halo` / `soot`+`lap` (WORKS on by default), greyer light paint, lighter frames; hull bake
grit (`lib._grit`: streak columns, stained concrete); FURNACE_V6 (frame hugs the bell: top 7.2, deck 7.6; band 14.8-18
m), GALLERY_V6 (clad box gallery + gas main), POUR_V6 (portal against the shed wall, dark back, full dark roof,
shallower), SPLIT third set (frame2 legs/bosh 29.7 px/m at 2048 -> ~59 at 4096); bkit clutter kit (pallet, drums,
pump_skid, gas_bottles, pipe_bundle) + `Rec.spill` point lights (colony.js); steel_mill.py `clutter()` (~80 items);
studio fov / keyColor / fillColor. Build 199k tris (hull 27k -> 46k), 8.0 MB.
Evidence: $S/mill/r1-sheet.jpg (concept | v5 | r1), r1-closesheet.jpg, crops-r1.jpg.
Checklist review (BUILDING-GUIDE section 9 + STYLE 8):
- C1 camera: FAIL-ish. Plinth slopes r1 0.44 / 0.36 vs concept 0.30 / 0.24 (the concept's perspective is not
  consistent: its roofs read from higher than its plinth edges); kept el 12 by eye. Guide row loosened to "by eye
  + slopes within 0.15".
- C2 framing: FAIL (plinth ~0.80 of the frame width vs concept 0.97) -> r2 dist 0.97 -> 0.88.
- C3 silhouette: PASS-ish: furnace forward-left, bell + hugging frame, clad gallery, stacks, long shed, portal.
- G1 streaks: PASS (close-ups: crisp vertical columns on the shed wall and the furnace shell).
- G2 roof soot: PASS (roofs mid grey with dark laps; slightly heavier than the concept's).
- G3 plinth staining: FAIL (crop: plinth top reads light and clean) -> r2 stronger stains, 4.6 m slab joints.
- G4 panel edges: PASS (halo + seams).
- W1 warmth: r1 as built FAIL (light 0.67x, sat 0.32: warm key + 900 cd spill); with r2 studio (key 0.85 #fff0e0)
  PASS: light 0.90x, all 0.99x, hue 27.5 (c 23.2), sat 0.19 (c 0.16).
- W2 dark steel: PASS with the r2 studio (mid band sat 0.146, frames read grey); r1 studio FAIL (brown legs).
- D1 density: PASS on the +X apron and casthouse front; the pour bay apron needed the runner (r2).
- L1 process glow: FAIL: hearth band reads as lit windows, not a bright band -> r2 12 stocks, radiance 2.6; runner
  inside the portal invisible -> r2 runner on the apron in front of the portal.
- L2 lamps: PASS (plinth pins every 9 m, lamp posts, pilaster lamps).
- T1 texel density: light shell 34.8 px/m at 2048 (~70 at 4096), frame2 29.7 (~59), shed clad 25.5 (~51): PASS at
  the 4096 final; review builds are 2048.
- T2 close crispness: PASS-ish at 2048 (legs now in their own set).
- I1 thumbnail: not run this round.
- Phone: tris 199k > 150k (STYLE 4 phone row): FAIL, to fix before the final (doors 14k, stacks 40k, workers).
Judges: no Agent tool in this session; the two lenses applied by me this round (vibes: "not yet": glow, framing,
plinth; quality: "not yet": phone tris, plinth texture). Asked the coordinator for blind judges from r2.

### v6 round 2 (13:04-13:22): furnace (12 stocks, glow 2.6), pour bay (runner on the apron in front of the portal),
hull (stronger stains, 4.6 m slab joints), spills 300 / 180 cd, studio key 0.85 #fff0e0, fill 1.5, dist 0.88.
Build 192k tris. Evidence $S/mill/r2-sheet.jpg, r2-closesheet.jpg, r2-blind.jpg.
Checklist review:
- C2 framing: FAIL the other way: dist 0.88 at 1600 x 1000 (16:10) cut the furnace top -> r3 dist 0.95.
- W1 warmth: PASS: light 1.02x, all 1.13x, hue 26.2 (c 23.2), light sat 0.21 (c 0.16; borderline).
- W2 dark steel: PASS-ish: mid band sat 0.20 = concept's 0.21 (the concept's darks are warm too); frames read grey.
- G3 plinth staining: FAIL: atlas shows fine dots and faint blotches only; render reads clean -> r3 bigger / darker
  stains (oil spots in 3.5 m cells, ragged), +0.2 dusty grey.
- L1 process glow: band now continuous but reads pale salmon (#ff8a28 at 2.6 tone-maps pale) and the spill tints
  the lower drum peach -> r3 #ff6c08, spill #ff8030. Runner on the apron: PASS (bright trough, lights the apron).
- D1 density: PASS (apron fronts packed; the -X side behind the furnace is sparse but not visible).
- C3 silhouette: PASS-ish; the pour bay's dark roof deck reads as a slab from this height (the concept's portal top is
  a lattice girder); kept for the dark interior.
- Phone tris: 192k: FAIL -> r3 stacks 56 -> 40 segments with laps every 4.4 m, furnace 72 -> 60, door decimate
  0.3 -> 0.2.
- Judges: requested from the coordinator for r2 (no Agent tool in this session).
- r2 judges (blind, run by the coordinator): BOTH "NOT YET".
  - A (vibes): silhouette NO (open A-frame lattice + bare cone, top cut by the frame), mood match, grit NO (clean,
    evenly toned), density NO (props scattered on the slab, main masses sparse), warmth barely (pale-peach band).
    Gaps: tighten the tower round the shell with ring platforms; grime / rust pass on roofs and cone; cut huts,
    trailer and the office block, gather detail at the runner and on the main masses.
  - B (1:1 quality): only shadows pass. Faceted bustle torus; no lit chamfer line on most edges (pilasters, parapet,
    girder ends); streaks read smeared / vertically stretched; roof seams soft; no 5 cm bolt row at 2 px; uniform
    satin roughness / metal; weak edge wear and contact AO.
  - Coordinator: framing (furnace top cut), compact heavy tower, shallow light roofs in bays with dark parapets,
    light boxy blocks round the furnace foot, thick plinth edge.

### v6 round 3 (13:24-13:40): stacks 40 seg / laps 4.4, furnace 60 seg, doors decimate 0.2, stronger plinth stains,
tuyere #ff6c08, dist 0.95. 177k tris. paint-check light 0.76x (FAIL: the +0.2 plinth dust), hue 25.9.
Review: G3 plinth staining PASS (stains and oil spots read at the concept camera); W1 FAIL (dark); L1 band still
salmon (radiance 2.6 tone-maps pale whatever the hue) -> r4 radiance 1.6 #ff6200; phone tris 177k FAIL.

### v6 round 4 (started 13:58): the judges' fixes
- FURNACE_V6 tower: near-vertical legs (12.8 -> 12.5) and posts (12.5 -> 10.2) to a railed deck at the hood (44 m),
  no frame above; railed rings at 49 / 54 on the upper stack; bustle torus 72 x 18; lap rings every 4.5 m (bosh 2.4).
- SHED_V6: ridge 21.2 -> 17.8 (14 deg), dark gable parapets, lighter roof (soot 0.6), 6 roof units, 4 ridge vents.
- GALLERY_V6 lands on the hood deck (B y 44.6).
- Paint: fbm `streak` and `drip` off (read as UV stretch), vstreak denser and darker, tone 0.16, bolts 8 cm, roughness
  patches + per-zone roughness, oil-can dents in the normal map, wider edge wear.
- Kit: default box chamfer up to 6 cm on members >= 0.3 m; I-beam flange chamfer 2.5 cm.
- steel_mill.py: casthouse 10 -> 7 m without the office window strip; switch room, small sheds and the truck gone
  (plate stacks and coils instead); two low light blocks on the furnace plinth front and a low annex on the -X side.
Round 4 result (13:41-14:03): 172.7k tris (phone copy now also drops parts_door: ~160k). paint-check light 0.92x,
all 0.99x, hue 25.4 (c 23.2), light sat 0.21 (c 0.16). Evidence $S/mill/r4-blind.jpg, r4-closesheet.jpg (new close
cameras: furnace dist 34, pour 32, shed 30, so 5 cm can reach 2 px), r4-thumbs.png.
Checklist review r4:
- S1 hero structure: PASS (compact: vertical legs, posts to the hood deck, ring platforms on the upper stack).
- C2 framing: PASS (whole plant in frame, dist 0.95). C3 silhouette: PASS-ish (bell + stacks + long shed + portal).
- G1 streaks: PASS (crisp columns only; no smear). G2 roofs: PASS (shallow, light, dark laps, parapet bays).
- G3 plinth: PASS-ish (stains and spots read near the furnace; the shed apron reads clean under the floods).
- W1 / W2: PASS (0.92x, hue 25.4; dark mid band neutral, sat 0.11).
- D1 / D2: PASS (huts and truck gone; plate / coil stacks at the walls; blocks at the furnace foot).
- L1 glow: FAIL: band still pink (the part still had radiance 2.6) and the 13 m spill reddened the bosh -> r5.
- L2 lamps: PASS.  T3 material variety: PASS-ish (pipes glossier, frames matte; chips visible on the legs).
- Gas main: FAIL: ended in the air over the gallery -> r5 runs it into the upper stack.
- I1 thumbnail: PASS: aspect 1.12, fill 0.71; furnace + glow + stacks read at 40 px, distinct from the siblings.
- Phone: ~160k (lite) FAIL by ~7 % -> r5 shed ribs 0.9 -> 1.8 m.

### v6 round 5 (14:16-14:34): furnace glow 1.6 #ff6200 + spill 6.5 m, gas main into the upper stack, shed ribs 1.8 m.
171.8k tris (phone copy ~158.7k after workers + doors). paint-check light 0.95x, all 0.99x, hue 25.2 (c 23.2).
Evidence $S/mill/r5-blind.jpg, r5-closesheet.jpg; camera test cam-sheet.jpg (el 8 / 5 with fov 18 / 16: the plinth
became a sliver and the roofs vanished; the concept shows both plinth top and facades: el 12, fov 22 kept).
Checklist review r5: S1 / C2 / G1 / G2 / D1 / D2 / W1 / W2 / L2 / I1 PASS as r4; gas main PASS (runs into the stack);
L1 FAIL: band and lower drum still pink-red (the red channel clips first at radiance 1.6; a red spill on light paint
reads pink) -> r6 #ffa03c at 1.2, spill #ffa048 110 cd at 4.5 m; phone tris FAIL (158.7k vs 150k).
Judges for r5 requested from the coordinator.
- r5 judges: BOTH "NOT YET". A: silhouette match; mood NO (clean, bright, toy-like diorama; the lattice's cast shadow
  reads as a decal), grit NO (flat surfaces), density NO (separate little boxes, airy core), warmth NO (pink-salmon
  band, thin pour, weak interior glow). B: shadows pass; geometry (flat emissive window cards, no lit chamfer on the
  gantry columns), texture (blocky stretched mosaic on the left lattice column, 1 px soft seams), materials (repeating
  drip strip, uniform matte dark steel, no edge wear, weak AO) fail. Coordinator: the furnace as a solid clad mass with
  the light / dark band stack; tonality heavier; merge cabins; Judge B's pipeline fixes.

### v6 round 6 (14:39-14:55): glow #ffa03c at 1.2 + yellow spill at 4.5 m: band reads saturated orange (PASS L1
colour); light 0.94x, hue 27.3. Evidence $S/mill/r6-hearth.png.

### v6 round 7 (started 14:55): the r5 judges' fixes
- FURNACE_V6: legs on the diagonals hugging the drum (3.6 -> 2.8 m plated boxes, trims frame2), slim frame2 posts
  following the bell, no square ring beams / X frame / top deck, ring decks at 26.6 and 43.1, dark plated hearth base,
  thinner glow slit (15-17.2 m), the elbow downcomer off the bosh into the 15 m annex, four risers, taps on the axes.
- Paint: per-panel streak density + random start, dark steel darker with mottling, brighter bare-steel wear, deeper
  AO; shed clad tone 0.22, roofs a step darker; deeper shed pilasters (0.95 m) and dark door surrounds.
- Kit: `ckit.window_frame` (control house, crane cab), `plinth(kerb_h)` (mill h 2.0, kerb 1.1 m).
- steel_mill.py: the control house and the furnace-plinth mini blocks replaced by one 12 m casthouse block across
  the furnace front, a 10 m annex on the -X side (the 15 m annex under the elbow), an annex on the shed's front end;
  the runner 3.6 m wide with a 0.9 m core, runner spill 260 cd.
Round 7 result (14:54-15:15): 176.4k tris; paint-check light 0.94x, all 0.99x, hue 27.1. Phone (build-artifact +
phone-check on r7): `steel_mill ok ready 6.1s fetched 6.1 MB tris 163k tex 49 MB heap+gpu 134 MB`; package check 57
tiers OK. Evidence $S/mill/r7-blind.jpg, r7-closesheet.jpg.
Checklist review r7: S1 PASS (bands, slit, ring decks, elbow, annex); W1 / W2 PASS; L1 PASS (saturated slit, runner
lights the apron); G1 PASS; G2 FAIL-ish (roofs clean light grey, judge A "plastic"); D2 PASS-ish (annexes, but the
front-left reads as separate boxes); T3 FAIL (no lit chamfer line: the 3rd time); phone tris 163k FAIL; heap / fetched
PASS.
r7 judges: both NOT YET. A: silhouette MATCH, mood MATCH; grit NO (clean plastic roofs, white annexes), density NO
(bare tower legs; crown an open cage), warmth NO (little spill, few small wall lamps). B: shadows and openings pass;
bustle bend kinks; no lit chamfer line on I-columns / gantry / chords; diagonal streaks on the upper cone; 1 px shed
seams; flat crane girder and ladle; edge wear absent. Coordinator: crown, merge front-left annexes, tighter apron,
lighter roof louvre bands; root-cause the chamfer and cone-skew issues.

### v6 round 8 (started 15:40)
- Root causes: chamfer debug (flat preview vs textured, 2400 px crop of the pour bay, $S/mill/dbg-chamfer.jpg): the
  bevels exist; the dark matte paint hid them -> cpaint continuous edge line. Cone skew: arc coordinate drift ->
  `axis_r`. Bend kinks: 8 fillet segments for big pipes, the bustle ring uncapped.
- Furnace: third catwalk ring (35 m), six risers, straight uptakes into the header, a dark cap; segments 52.
- Shed: the r5 'monitor' edit had landed inside a comment (never applied); now half-length low monitors; roofs a step
  darker with per-sheet tone 0.2. Crane girder plated with bolts, chips, mottling; ladle plates + slag lip.
- Building: plain dark-framed annexes (one window row at most), dark frames on the casthouse and the shed-end annex;
  plinth pins every 4.6 m, pins up the furnace legs; hearth spill 220 cd + a 90 cd spill under the bustle.
- Not changed: the +X apron width (the portal and its runner reach x 38.4 of the 40 m edge; a narrower plinth would cut
  them) -> left as is, noted under "still different".
- Stacks 32 segments (phone budget).

### v6 round 9 (16:00, build only): plain light-framed casthouse / shed annex (the dark frames read as a half-timber
grid), the furnace-front block 3.6 m (5.5 hid the light drum). 175.7k tris; paint-check light 0.92x, all 0.97x, hue
26.4. Evidence $S/mill/r9-blind.jpg, r9-closesheet.jpg.
r9 judges: both NOT YET, closer. A: silhouette, mood, warmth MATCH; grit NO ("clean even off-white tiles, flat dark
trim, a new toy"), density NO (bare tower cage, plain shed surfaces). B: seam width OK (2-4 px at 4096); edge line only
on the pour column and gantry (not pilasters, parapets, cap plates); ring-pipe kinks and open ends; blocky streak bars;
blurry molten channel; repeating grime; ladle and booth read as wood. Coordinator root causes: macro grit, streak
sampling, edge-pass coverage, small-prop seams.
Checklist review r9: S1 / C2 / C3 / W1 / W2 / L1 / L2 / I1 PASS; G1 FAIL (bars), G2 / G3 FAIL at the concept camera
(too fine), D1 PASS, D2 PASS-ish, T2 PASS (seams 2-4 px at 4096), T3 FAIL (edge line partial), phone tris 162k FAIL.

### v6 round 10 (started 16:08): root causes
- `cpaint.macro` (per-bay panel tone, 3-10 m soft streaks, soot_top on furnace / stacks, base grime) and the same in
  the hull shader; streak columns 16 / 40 cm, soft sides, per-course shifted grid; per-part seeds.
- Edge coverage: STACK_NARROW 0.25 -> 0.12, curvature bake 5 -> 8 cm, edge line from curvature 0.03.
- Small props: ladle 1 welded course + mottling, booth no column streaks. Molten channel UV weight 0.5 -> 1.0.
- Bustle a true torus; three hot-blast drops; shed pilaster lamps in three rows; roofs darker with per-bay tone;
  roof exhaust ducts on saddles; stack base pipework, valves, cabinets; runner core 1.4 m; plinth stains stronger;
  furnace main-set UV weights (frame 6.4 -> 12.0 px/m at 2048).
Round 10 result (16:08-16:30): 182.1k tris; px/m at 2048: furnace frame 12.1 (main set, UV_W), shell 36.4, frame2 24.9,
pour hot 40.1 (was 21.8); paint-check light 0.84x (the macro layer darkened; FAIL) -> r11 key 0.95.
Checklist review r10: G1 PASS (soft-sided columns), G2 PASS (darker roofs, per-bay tone, soot), G3 PASS-ish (stains
read at the concept camera near the furnace), macro grit visible on the furnace, stacks and shed walls (soot tops);
W1 FAIL (0.84x); L1 runner core read pastel pink (FAIL) -> r11.
### v6 round 11 (16:40-16:55, pourBay + build): runner #ffa03c at 1.2; key 0.95. paint-check light 0.90x, all
0.96x, hue 26.7 (c 23.2): W1 PASS. Evidence $S/mill/r11-blind.jpg, r11-closesheet.jpg. Judges requested.
- r11 judges: both NOT YET. A: silhouette, warmth match; mood NO (evenly lit, pale clean plinth: a diorama), grit NO,
  density NO (sparse tower and shed, detail in small boxes). B (all three gaps "major"): grime texel quality (soft
  rectangular stamps, repeating columns, moire grain on the shed wall), flat molten metal and floor, edges on I-beams /
  truss / girder, bustle banding. Coordinator: stop the final; crown and annexes first; make grit and mood measurable.
- The 4096 final started at 16:44 was stopped (16:55) on that instruction.

### v6 round 12 (started ~17:15)
- Measurable grit / mood: `tools/buildings/grit-check.py` + `grit-regions/steel_mill.json`. r11 at the concept
  camera: shell std 0.71x / hp 1.17x, wall 1.02 / 0.87, roof 1.17 / 0.98, plinth 1.01 / 1.55 (crops not yet fully bare);
  shadow side 1.20x (FAIL) -> studio fill 1.5 -> 0.6, env 0.5, key 1.15: shadow 0.97x, light band 0.88x (test on r11).
- Found: since r1 the plinth's `centre=(0, -4)` sat inside an appended comment (slab 4 m forward: the spread apron).
- Crown: cap2 (a second, narrower dark drum), a railed deck on the cap, three straight uptakes into its side, no header.
- Annexes: one plain 12 m block between the furnace foot and the shed gable (one window row), a plain 10 m shed-end
  annex, the furnace-front block removed. Plinth top 'concreteD' (mid grey) with the stains.
- Paint: organic tapered / wobbling drips; bolts band-limited by texel density; macro tone 0.18 and streaks 0.32;
  shell and clad seams 9 cm, darker, halo 0.22; molten crust 0.65. Kit: warren chords / webs and I-beam flanges
  chamfered for an edge line.

## STYLE.md proposals (for the coordinator to merge)
- Section 4 phone row "≤ 150k tris": the mill measures 163k on the phone tier (r7, doors and workers dropped) with
  heap+gpu 134 MB, fetched 6.1 MB, ready 6.1 s (all far inside budget). Propose ≤ 175k tris for hero process
  buildings, or state tris as advisory with heap+gpu the binding limit.
- Section 4 "dark structure ≥ 25 px/m": met by crisp sets (furnace frame2 ~50 at 4096) but not by stacked lattice /
  rail swatches (their density is not measurable as a density); propose "≥ 25 px/m on dark members ≥ 0.3 m wide".
- Section 8: add the grit / mood measures (grit-check std and high-pass 0.8-1.2x on bare-surface crops; shadow side
  0.8-1.2x), and "close-up views at ≤ 34 m with fov 38" (the 5 cm / 2 px test cannot pass further away).
- The 15 m bare-apron rule held as written; icon fill ≥ 0.6 held (0.71).
Round 12 result (17:04-17:27): 178.9k tris; light 0.87x; the new 12 m block and annexes drew a bold dark half-timber
grid (5 m bays of dark posts and bands). Evidence $S/mill/r12-blind.jpg, r12-closesheet.jpg.
### v6 round 13 (17:30-17:45, build only): plain facades (corner posts only, no bands / seam grid) on the 12 m block
and all annexes; key 1.25. paint-check light 1.00x, hue 27.4 (c 23.2); grit-check (regions re-fitted to the r13 camera,
still approximate: see grit-crops-r13.png): shell std 0.69x / hp 1.59x, wall 0.71 / 1.0, roof 0.84 / 0.97, plinth
0.86 / 1.81; shadow 1.00x.
Checklist review r13: S1 PASS (compact tower, stepped dark crown), C2 / C3 PASS, D2 PASS (one block + annexes, no
cabins), W1 PASS (1.00x), M1 PASS (shadow 1.00x), G0 FAIL on shell / wall std (0.69 / 0.71x) -> mtone 0.26, mstreak 0.4
for the next bake, G1 PASS (tapered drips), G2 PASS, G3 PASS-ish, L1 / L2 PASS, T2 PASS at 4096 (seams 2-4 px), T3
PASS-ish (edge line on chamfered members), phone tris FAIL (see STYLE proposals). Judges requested.
- r13 judges: both NOT YET. A: silhouette, mood MATCH; grit NO (clean even tiles, spotless base, white annexes),
  density NO (furnace base, right yard, shed roof), warmth NO (regressed with the fill cut; orange only in strips).
  B: chamfers now MINOR; MAJOR: blurry stretched block wall (hull UV), blocky shell smudges, moire dots; MAJOR: molten
  metal and ladle read as flat paint. Coordinator: change the method: a photographic fal weathering library.

### v6 round 14 (aborted in its shots stage: superseded) and round 15 (started 18:16)
- fal: four PATINA weathering sets (`v27_mill_weathering`: wxCladding, wxSteel, wxConcrete, wxRoof; ~$0.5), downloaded
  to scratch, converted with `python3 -I` (`weather/wxprep.py`) to `tools/blender/buildings/weather/<set>/`.
- `cpaint.PHOTO` photo layer (band-limited, per-row offsets, joints removed), `lib._wx_photo` for the hull.
- Hull UV: `colony_build.py` uses `remodel.unwrap` (stacking, concrete weighted 0.3).
- Seams softened (6-7 cm, 0.5-0.6) after a test bake showed a window-grid look; procedural streaks a step down.
- Molten: AO-driven heat gradient + crust; ladle scorched steel with slag drips.
- Lights: hearth pool 380 cd, two runner pools 260 cd, a portal light 160 cd.
- Density: stepped concrete blocks round the furnace foot, a stair + catwalk + stair toward the tuyere deck, a pipe
  bundle on the furnace plinth, a pipe rack and a switchgear skid across the right yard, catwalks along the shed
  ridges; annex blocks in mid-grey 'panel2'.

### v6 round 15 (18:07-18:50; the remodel died after the furnace on a stale image cache, fixed and resumed at 18:30)
All five parts re-baked with the photo layer, hull on `remodel.unwrap`, the r14 lights and density. 186.9k tris desktop.
paint-check: light 0.76x (the photo layer pulls the light paint down), mid hue 232 (bluish; concept 21.5); grit-check:
shell std 0.73x / hp 1.51x, wall 0.69 / 0.93, roof 0.81 / 0.96, plinth 0.96 / 2.08; shadow 0.95x. Evidence
$S/mill/r15-blind.jpg, r15-closesheet.jpg, grit-crops-r15.png.
Close-ups: the photo grime reads on walls, shell and roof (no tile grid); the hull block walls are sharp; but the runner
and the ladle top are still a pale peach slab (emission clipped above the tone-map knee, crust too sparse) and the
runner / portal spills wash the whole bay floor orange.
Checklist review r15: C1-C3 PASS; S1 PASS; D1 PASS (furnace foot blocks, stair / catwalk, right-yard pipe rack and skid,
roof catwalks; no bare run > 15 m); D2 PASS; G0 FAIL-ish (shell / wall std 0.73 / 0.69x: the concept's crops include
light falloff the bare crops of the render lack), G1 PASS (photo + drips), G2 PASS, G3 PASS (plinth std 0.96x), G4 PASS;
W1 FAIL (0.76x), W2 PASS; M1 PASS (0.95x); L1 FAIL at close range (peach runner), L2 PASS; T2 PASS (hull wall sharp);
T3 PASS; phone tris see the proposals.
Lighting calibration (main shot only, URL overrides): key 1.5, keyColor #fff3e8, fillColor #f0dcc8 -> light 1.04x,
mid hue 12 (c 21.5), all 1.09x, shadow 1.04x (adopted); with fill 0.75 / env 0.45 the shadow rose to 1.24x (rejected).

### v6 round 16 (pour bay + build)
- Molten: crust plates over most of the trough away from the AO ridge (near black-red, crust 0.95), bright cracks,
  the body held below the tone-map knee (x 0.55-1.0 by core); the stream narrowed to 1.8 m in a dark lined trough,
  glow core 0.55 m.
- Spills: runner pools 170 cd / 12 m (260 / 16), portal 110 cd (160).
- Studio: key 1.5, keyColor #fff3e8, fillColor #f0dcc8.
Round 16 result (18:57-19:11): light 1.02x, shadow 0.83x; but the runner was unchanged: its emit texture (extracted from
the GLB) was pale yellow over the whole stream: the AO heat term saturates on a flat open trough.
### v6 round 17 (19:13-19:28, pour bay + build): heat a minor term where there is a crust (x 0.35), the open metal from
noise; crust tied to (1 - core). Close-up: dark crust plates with bright cracks, the hot core stream, the ladle top
crusted. light 1.02x, mid hue 12, all 1.06x; grit shell 0.80 / 1.63, wall 0.76 / 1.02, roof 0.86 / 0.99, plinth
1.01 / 2.16; shadow 1.15x (GrabCut varies +-0.15 between identical-lighting shots).
### v6 round 18 (shots only): the shed wall's fine dot grid (judge B's "moire") is key-shadow acne, not texture (GLB
textures clean; unchanged with ?ao=0 and ?finish=off; gone with the normal bias x 10). Studio hint shadowNB 6
(src/main.js + env/lighting.js fitShadow; ?snb= calibrates).

### v6 rounds 19-20 (correction 45, pipe logic; user: "the large pipe kind of comes out of the housing there for no
apparent reason")
Audit (top view `az=0&el=89`, rear views az 250 / 300 / 165): the gallery gas main ran over the foot tower and dropped
behind it to end at 3 m in the air; the furnace hot-blast drops hooked out and ended above the base; the risers stopped
beside the shell; the dust-catcher pipe started in the air beside its cone; the shed flue ducts stopped 0.9 m short of
stack 1; the stack-base pipes, the furnace-foot mains, the pipe bundle on the furnace base, the casthouse wall run, the
pipe rack and three plinth-edge bundles all had free ends; the roof exhaust ducts ended blind.
Fixes: gas main = crown drum nozzle (flange) -> saddles over the gallery -> a jog over the foot tower's roof corner on a
saddle -> a drop on the tower's +X side on brackets with clamp bands every 6 m -> 2.8 m into stack 1's flared base
(flanged inlet) [r20: r19 dropped behind the tower and still read from the concept camera as diving into its roof];
drops straight down into the furnace base with flanges; risers leave / re-enter the shell; downcomer nozzle flange and a
roof curb on the gas-cleaning annex; flue ducts level into both stacks on a support; stack-base pipes from the base block
past the valve into the shed wall; furnace-foot mains from the annex down into the slab; the base bundle from a stepped
block into the casthouse block; the casthouse wall run out of and back into the wall on brackets; the rack's pipes out of
the shed wall; bundles shed wall -> switchgear skid, pump skid -> shed wall, pump skid -> buried main (`drop_end`); roof
ducts out of a roof curb into capped exhaust stubs. `bkit.pipe` supports now ceil-spaced (never a gap over the pitch).
r19: 195.0k tris desktop; light 1.07x, shadow 0.98x. Guide: checklist row P1, gotcha.
r20 (behind-the-tower drop moved to its +X side) still hid the drop from the concept camera; r21 put it at the tower's
front-left corner, braced to the corner: in the main view the main now runs down the gallery and continues as a visible
vertical on clamp bands beside the tower (evidence $S/mill/r21-crowncrop.png, aud2-drop.png, aud2-top.png).
Checklist review r21 (evidence $S/mill/r21-blind.jpg, r21-closesheet.jpg, grit-crops-r20.png):
C1-C3 PASS; S1 PASS; D1 / D2 PASS; G0 shell 0.86x / wall 0.75x std (hp 1.62 / 1.0), roof 0.86, plinth 1.02: PASS-ish
(the wall crop's concept variance includes light falloff); G1-G4 PASS (photo weathering, drips, roof soot, stains,
seams); W1 PASS (light 1.07x, hue 27.6 vs 23.2), W2 PASS; M1 PASS (shadow 0.98-1.09x); L1 PASS (hearth glow, crusted
runner with bright cracks and core, ladle crust; spill pools local), L2 PASS; T1 PASS; T2 PASS (no acne dot grid with
shadowNB 6; hull walls sharp); T3 PASS; P1 PASS (every run traced: see rounds 19-20); I1 not re-run (final);
phone tris: 194.7k desktop (see the STYLE proposals; the phone tier is measured at the final).
- r21 judges: both NOT YET. A: mood, density, warmth now MATCH; silhouette (a bulging cage with heavy ribs and a dark
  dome; camera too high) and grit (toy-like white annexes with black trim) do not. B: shadows pass; repeat faults:
  torus facets, a smeared wall in the pour view, shed moire; the ladle reads as polished copper; three pipe-logic faults.
- Correction 46 (user): at most 25 rounds; r25 = the 4096 final. Coordinator: the session migrates after the mill:
  everything needed in the repo.

### v6 round 22 (21:26-21:44; scratch now $REVIEW_DIR = scratchpad/review, driver tools/buildings/review/round.sh)
Diagnosed each repeat fault from a 1:1 crop of r21 and the BUILT GLB (tools/buildings/review/decode.mjs + glbppm.py):
- Torus facets: the GLB had all 72 segments (5 deg, sagitta ~1 cm). Causes: the ring (R 12.6) ran through the four
  raking legs (inner corners at 10.8 m radial) and its pipeDark zone sat in the furnace main set at ~11 px/m (2048).
  Fix: R 10.15 / tube 0.45 at 19.5 m between bosh and legs; pipeDark into the frame2 set (17.4 px/m at 2048, ~35 at 4096).
  The main set's 0.10-0.14 fill is a separate packer problem left open (wedge cuts, AABB / CONVEX, FRACTION margins
  tested: no change; env hooks REMODEL_SHAPE / _MERGE / _MARGIN kept).
- Smeared pour-left wall: the shed-end annex's +X face, 25.7 px/m area-weighted at 2048; the hull atlas also held the
  plinth's underside and buried slab layers (~32 %). Fix: colony_build culls down-facing plinth faces + buried faces
  (58.7k -> 52.8k hull tris; light walls 49 -> 64 px/m mean, casthouse wall 37 -> 49); r23 adds a second hull texture
  set for the ground (`HULL_SPLIT`) and lower kerb / side weights.
- Shed moire: unchanged with ?ao=0, ?finish=off, ?snb=12; gone with ?srad=1.5: the key's 3.5-texel Vogel-disk PCF
  pattern in every penumbra. Fix: studio hint shadowRadius 1.5 (main.js reads it; ?srad= calibrates). r22 crop clean.
- Pipe logic: the shed's upper wall pipes leave and re-enter the wall (the 2.2 m drop ended in the air); the bustle no
  longer meets the legs; the downcomer has a nozzle flange, flanged joints, a braced column on the base block and a
  roof curb.
- Annexes: new kit material panelW (weathered grey-beige), light-grey 0.35 m corner posts (frameL) instead of the black
  0.6 m trim on all annexes and the furnace-foot blocks. Ladle: near-black matte scorched steel. Furnace form: the hood
  cone light (shell), posts 0.95 x 0.75 (1.5 x 1.1), no 35 m deck band. Camera: el 10, dist 0.88 (plinth-edge slopes
  0.35 / 0.28 vs the concept's 0.29 / 0.24). Runner glow 1.6, core 0.8.
r22 check (grit regions not re-fitted to the new camera, so G0 numbers are not comparable): light 1.15x, shadow 1.21x.
### v6 rounds 23-24 (22:07-22:30)
- r23 (pour bay + build): ladle drip streaks 1.0 -> 0.25 (they read as barrel staves), portal spill 110 -> 70 cd;
  the hull ground in a second texture set (`HULL_SPLIT`): the slab came out black (bake selection + a stale
  BAKE_TARGET node; both fixed, unit-tested with `--stage hull --tex 512`). A comment had swallowed the ladle paint
  line's closing brace (r23's first start died; fixed in 81aeb53).
- r24 (build only): walls fine, slab still black (the second cause). After the fix the unit test showed the split
  makes the wall set pack worse (3.0 px/m at 512 on the annex walls, ~half the single set): HULL_SPLIT is off for the
  mill; kept as an opt-in. Grit regions re-fitted to the r22 camera (tools/buildings/grit-regions/steel_mill.json).
- r25 = the 4096 final (correction 46: 25 rounds).

### v6 round 25: the 4096 final (22:33-23:30, reshoot 23:35)
Parts at their registry sizes (furnace / shed / pour bay 4096, stack / gallery 2048), building 4096 x 10 samples,
189.6k tris desktop. px/m at 4096: furnace shell 67.6, frame2 55.0, pipeDark 35.4 (main set: frame 26.4, fill 0.14);
shed clad 52.5; pour bay panel 91, hot 82; gallery panel 45 (2048); stack shell 51 (2048). Studio final: key 1.35
(1.5 gave light 1.16x at the tighter frame).
Checks (final camera, regions re-fitted): light 1.06x, hue 27.2 (c 23.2), sat 0.226 (c 0.164); shadow side 0.91x;
grit std: shell 0.51x (hp 1.41), wall 0.96x (hp 1.52), roof 0.69x (hp 0.81), plinth 0.65x (hp 1.18).
Evidence (repo): style-library/styles/cqs-fleet/images/buildings/steel_mill-v6.jpg (concept | v5 | v6),
steel_mill-v6-close.jpg (concept crop | v5 | final per close-up), steel_mill-v6-thumbs.png (80 / 40 px; v6 icon
aspect 1.23, fill 0.65). v5 shot from git 698deb2 with today's studio (tools/buildings/review/shoot-rev.sh).

Checklist review r25 (BUILDING-GUIDE section 9):
| row | result | evidence |
|---|---|---|
| C1 camera | PASS | el 10 / dist 0.88 / fov 22; plinth-edge slopes lowered toward the concept's 0.29 / 0.24 |
| C2 framing | PASS | whole plant in frame, the tower dominates the left |
| C3 silhouette | PASS-ish | furnace forward-left, gallery, two banded stacks, long shed, portal pour bay; the furnace still reads rounder than the concept's straight lower drum |
| S1 hero structure | PASS | slim posts, legs tight to the drum, light cone, dark slim upper section |
| G0 grit measured | FAIL (shell 0.51x, roof 0.69x, plinth 0.65x std; wall 0.96x) | grit-crops in $REVIEW_DIR; the 4096 textures are smoother at the concept camera than the concept's painted grit |
| G1-G4 | PASS | photo weathering, drips, roof soot, stained slab, seams |
| M1 mood | PASS | shadow 0.91x |
| W1 warmth | PASS | light 1.06x, hue +4 deg; sat 0.23 vs 0.16 (warmer than the concept) |
| W2 dark steel | PASS | neutral gunmetal |
| D1 / D2 density | PASS | clutter on the masses, no bare run > 15 m |
| L1 glow | PASS | hearth band brightest; runner a second hot spot with crust and cracks |
| L2 lamps | PASS | |
| T1 texel density | PARTIAL | light >= 50 (shell 68, clad 52, pour 91); hull walls ~50 (casthouse 49 at 2048 x2); furnace main-set dark parts 26 (< 25 target only for grating 14) |
| T2 close crispness | PASS-ish | no moire (shadowRadius 1.5), hull walls ~2x sharper than r21; the stacked swatches stay soft at 1:1 |
| T3 material variety | PASS | ladle matte near-black steel (still warm-tinted by the bay's glow) |
| P1 pipe logic | PASS | every run traced (rounds 19-22): no free ends, flanges, supports <= 6 m, nothing through unrelated geometry |
| I1 thumbnail | PASS | aspect 1.23, fill 0.65 |
Release checks (r25): `tools/build-artifact.mjs` exit 0, "package check: 57 model tiers match their source GLB";
`tools/phone-check.mjs steel_mill`: ok, ready 6.1 s, fetched 6.5 MB, tris 178k, heap+gpu 134 MB (budget 300);
`tools/pkg-diff.mjs --csp 1 --units 16 b_steel_mill`: diff 0.00 % ok; `--device phone`: 0.40 % ok.

### STYLE.md proposals (r25 update)
- Phone tris: the final mill measures 178k on the phone tier with heap+gpu 134 MB, fetched 6.5 MB: propose the tri
  row as advisory for hero process buildings (<= 200k) with heap+gpu (< 300 MB) and fetched (<= 7 MB) binding.
- Section 8: add P1 pipe logic (correction 45) and the 25-round iteration budget (correction 46).
- Section 4 texel density: state it for non-stacked surfaces (stacked swatches report meaningless px/m) and measure on
  the built GLB (tools/buildings/review/glbppm.py).

## State at handoff (2026-10-08)
**Done:** steel mill v6, 25 rounds (24 reviews + the 4096 final), committed and pushed on
claude/vibrant-knuth-tx4hru. Assets: assets/buildings/steel_mill.glb / .lite.glb, assets/parts-colony/*.glb +
parts.json, src/buildings/steel_mill.js (studio hint: az 48, el 10, fov 22, dist 0.88, key 1.35 #fff3e8, fill 0.6
#f0dcc8, env 0.5, shadowNB 6, shadowRadius 1.5). Evidence in style-library/styles/cqs-fleet/images/buildings/
(steel_mill-v6.jpg, -v6-close.jpg, -v6-thumbs.png); the checklist review is above (r25). Everything needed to continue
is in the repo: BUILDING-GUIDE.md (section 0b: the bpy venv and the review toolkit tools/buildings/review/), the
weathering library (tools/blender/buildings/weather/, fal v27 recorded in pipeline/fal-pipeline.json), grit regions
and cameras per building. No scratchpad path is needed (REVIEW_DIR / BPY env vars).
**Open items (mill):**
1. Grit at the concept camera: G0 std 0.5-0.7x on the shell, roof and plinth crops (the concept's painted grit is
   coarser); the user to steer (judge A r21: "too clean").
2. The packer: remodel.unwrap packs the furnace main set and the hull's wall set at ~0.10-0.14 fill (half the square
   empty, see uvdraw.py); fixing it would roughly double those texel densities. Tested and ruled out: wedge cuts of
   hollow islands, AABB / CONVEX shapes, FRACTION margins, the UDIM source, a separate ground set (HULL_SPLIT).
3. Silhouette: the furnace still reads rounder than the concept's straight lower drum; the ladle still warm-tinted.
4. Phone tris 178k vs the 150k row (proposal above).
5. The coordinator's last judges ran on r21; the r22-r25 changes have not been judged.
**Next building:** follow BUILDING-GUIDE.md from stage A with the toolkit; budget 25 rounds (correction 46); run the
P1 audit views from the first full build.
