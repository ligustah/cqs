# Style: cqs-fleet

The orbital fleet of the Conquer-Space reboot. Every asset here must look like it came from the same
shipyards.

## Hard rules

- **Original IP only.** Never open, read or reference the legacy art: `Artwork/**`,
  `Html/Design/pack/units/*`, `*.blend` from the old game. Only class roster and gameplay stats come
  from the old code.
- **No imitation** of franchise ships: Star Wars, Star Trek, The Expanse, Halo, BSG, Homeworld, EVE.
  Do not name them in prompts either. A judge checks every concept for look-alikes.
- **Budget** (correction 37, supersedes 17): no cap. Aim for the best result; do not plan around or
  report the remaining fal credit. If the account runs dry, say so and the user adds credit. Still
  record every job in `Scene3D/pipeline/fal-pipeline.json`.

- **Full pipeline** (correction 36): every asset goes through turnaround, blueprint mesh, fal parts
  where useful, remodel and review. Do not skip stages to save credit while the budget allows.
- **Compose from components** (correction 38): break a complex asset into components; make each with
  fal (isolated component image, then image-to-3D), simplify it in Blender, keep it as a reusable kit
  part, and compose the asset from parts. Do not reconstruct a whole building as one mesh.
- **Concepts first:** when several assets are designed together, every concept is settled with the
  user before any turnaround, blueprint mesh or remodel of any of them (correction 23).

- **Reuse first** (correction 32): docked freighters, ships under construction and every repeated part
  are the existing models (instanced GLBs, kit parts, PATINA sets). New geometry only for what does not
  exist yet, and new parts go into the kit for the next asset.

- **Phone first** (corrections 8, 33): the user views the preview on a phone. Every new asset gets a
  phone budget, the scene loads only what the current view needs, and the phone tier is tested before
  any publish.

- **Scope:** unit module variants (speed / attack / defense: weapon pods, add-on armour, speed packs)
  are not modelled yet, for ships or ground units. Build the base chassis; the variants come later
  (correction 18).

## Identity

Credible near-future "naval-industrial" spacecraft, photographed like studio models:
- faceted hard-surface hulls with chamfered edges and layered armour plates;
- no aerodynamic wings;
- real engineering logic: radiators, shielding between drive and crew, RCS quads, hatches and rails at
  human scale;
- drives are fusion bells with magnetic-nozzle coils.

Warships are blunt and armoured, civil ships are lean spines with modules. Weapons are railguns
(spinal on the destroyer), turrets, PDC and missile cells.

The same civilisation builds the ground units and the installations (shipyard, spaceport), in the same
construction, markings and rulers.

- **Ships land and take off under their own power on any planet** (a game rule; the user, correction
  20). Installations do not explain how: no launch rails, cradles, launch towers or blast pits, and
  no design question built round reaching orbit.

## Thumbnail readability (correction 22)

The user: "They need to be distinctly recognizable on a relatively small thumbnail. So we want rich
details for large shots, but also not too 'wide' like the shipyard designs."

The game shows every unit and building as a **square icon**: 40 px in queues and job lists, 80 px for
the current job and on hover, 20 px in compact lists, on the dark UI panel (#222d35). Sources: the CSS
in `Html/Design/pack/css*/` and `CqsSession.getUrl(..., big=false)`; the legacy icon images themselves
are not opened.

- **Identifiable at 80 px, still distinct from every sibling at 40 px.**
- **Compact massing.** From the icon camera (three-quarter, about 30° up), the silhouette fills a square
  frame: bounding aspect about 1.5:1 at most. A sprawl of similar sheds over a kilometre fails (the r1
  shipyard sites). Show one dominant structure with a clear outline, keep the rest tight round it, or
  leave it out.
- **One or two signature shapes** carry the identity at icon size (a cab profile, a ring, an arch, a
  tower, a dish). Markings and small parts are the second layer, for close shots, and stay rich there.
- **Value contrast that survives downscaling:** a light / dark split or one bright signature element.
  Uniform mid-grey reads as nothing.
- **Test (review gate, also for concepts before a pick):** render or crop the icon view, downscale to 80
  and 40 px on #222d35, and put it on a sheet with the sibling assets. A judge must name each one.
  Tool: `Scene3D/tools/thumbs/`.

## Installations (shipyard, spaceport and later buildings)

- **Lights and small detail are required** (correction 24): work floods, amber lamps and lit windows at
  the fleet's fixture sizes, plus dense small parts (rails, pipes, ladders, crates, vehicles, figures).
- **Darker, with depth** (correction 24): a lower overall value than the r2 daylight images, deep
  shadowed recesses and layered structure, not flat bright planes.
- **Sized by what they build** (correction 25): lean structure, only modestly larger than the biggest
  ship; no mass that is several times the ship's size without a reason.
- **Busy, not bulky** (corrections 25, 31): enclosures stay thin and broken up; life comes from activity
  (docked freighters at true scale, tugs, cargo, cranes, lights), never from a massive continuous shell.
- **Show the actual unit** (correction 26): the real fleet ship, part-built (the DD-12 in the shipyard,
  the CV-50 in the spaceport). At remodel, instance the real ship GLB, cut back to its build state.
- **Light paint** (correction 27): buildings keep the light concept paint with dark accents.

## Palette and livery

- **Generation paint:** off-white thermal paint with weathering, signal-orange hazard and ID markings,
  small cobalt bands, gunmetal frames, gold / silver MLI foil on sensor boxes, dark ceramic belly tiles.
  Generate light, because light reconstructs better.
- **Operational livery (runtime, the default):** dark matte grey. The user's reasoning: dark ships are
  harder to spot.
  - `livery.js` `dark`: base 0.016, gain 0.065, tint #e3e7eb, marks kept faint (mark 0.11, markSat
    0.05); warships may keep a little more (destroyer mark 0.18, markSat 0.3).
  - Opt-in two-tone schemes by armour zone: `tone` (warm mid grey) and `bone` (concept off-white next to
    charcoal). Opt-in only, never the default.
- **Hazard paint:** amber (0.93, 0.58, 0.12), not orange: orange reads salmon-pink through the livery.
- **Hull numbers:** fleet stencil font. Pale stencils read as low-visibility grey; white numbers need a
  dark ID field. Numbers used: F-402, K-214, CT-4 / CT-7, DD-12, CV-50.

## Materials

- **PATINA tri-planar detail** at one absolute tile (6 m) on every hull: set `hull`, with
  normalStrength about 0.6 and cavity about 0.2 on remodelled hulls, which carry their own seams.
- **Worn finish** (`finish.js`, on by default): `hullWear` (two-scale plate tone), `hullGrit`,
  `sootStreak` (drive soot), plus GTAO.
- **Hangar:** `deck` set, plus the same set 7.3x larger for panel tone that reads from a kilometre.
- **Scene-built parts:** full sets `armor`, `orange`, `ceramic`, `foil`, `radiator`.
- **Ground finish** (`finish.js` `FINISH_PRESETS.ground`, a module sets `finish: 'ground'`; the ships keep
  `ship`): every ground unit uses it.
  - Detail: set `groundPaint` (scratched worn armour paint, no seams) at a **1.5 m** tile, normalStrength 1.4,
    roughAmount 0.8, cavity 0, `skipGlass: true`.
  - Roughness 0.84-1.0 (mean 0.92); livery `matte: 0.75`, `glassRough: 0.8` (hazy panes, never mirrors).
  - Wear tone at 2.5 / 9 m (ships 24 / 110 m), grit at 0.35 m (ships 0.8 m), scratches show lighter.
  - Ground layer in true albedo over hull and every kit part, graded from `anchors.ground`: dust full to 0.4 m and
    gone by 1.55 m (ragged edge, max 0.66), dried mud clumps below 0.75 m, a thin dust film on up-facing surfaces.
  - Baked in the asset's paint script (`vehicle_paint.py` `weather()` is the template): edge chips (red-oxide primer
    round bare steel), stone chips low and on the nose, mud in the wheelhouses, arch rims and belly, recess grime,
    run-off streaks under the roof edge, vents and panes, a sun-faded roof, scuffed markings. True-colour texels are
    written with base-colour **alpha < 1** and the livery's `keep: 1` leaves them unrepainted.
- The prompts are in `prompts.md`; the files are in `Scene3D/assets/materials/` (`manifest.json`).

## Ground units (correction 34)

- Matte paint and visibly used: dust and dried mud on the lower body, wheels and arches; chipped and
  worn edges; grime in recesses. Never glossy. The user: "way too smooth and clean. Too shiny."
- Surface detail scaled to the asset: the ships' 6 m PATINA tile is far too coarse for a 6.5 m
  vehicle. Tile the detail at a size that shows plate texture, scratches and grit at close range.
- Worn and dirty, not a wreck: the marks (amber, cobalt, unit number) stay legible, the lamps and the
  silhouette are untouched, and the dark livery stays the default. Recipe: the ground finish under
  Materials (V-31 v2, `images/build-vehicle-v2.jpg`).

## Scale model and rulers

**Source of truth:** `Scene3D/src/lib/scale.js`, checked by `tools/scale-check.mjs`. Older notes that say
3,200 m³ or a 25.5 m fighter are historical.

**Adding a class.** "N slots" means the hangar slots the ship **occupies** when parked; a carrier's
capacity is separate. A class that is not in the game's roster (`UnitEnum`) is a design decision: ask the
user before inventing one. To add it:
- a `CLASSES` entry in `scale.js` (size, label, gameId, role);
- a module in `src/ships/<id>.js`, registered in `src/ships/index.js` (ORDER);
- the hangar check (`carrierLoads`) if carriers can park it;
- its row in `audit.mjs` and in the lighting standard.

- **Scale model:** size comes from the game, via hangar slots. One slot is 70,000 m³ of envelope, and
  each class is scaled so its bounding-box volume equals slots times 70,000 (`src/lib/scale.js`).
  | Class | Slots | Length | Crew |
  |---|---|---|---|
  | Fighter | 1 | 71.7 m | about 40 |
  | Corvette | 5 | 108 m | about 350 |
  | Civil ship (cargo) | 4 | 134 m | about 80 |
  | Civil ship (troops) | 4 | 129 m | 750 troops |
  | Destroyer | 12 | 203 m | about 2,000 |
  | Carrier | 50 slots of hangar | 900 m | about 20,000 |

  The carrier's hangar (670 x 155.8 x 84.4 m) must park every legal full load with 2 m clearance.
  `node tools/scale-check.mjs` must pass.
- **Human-scale rulers, identical on every hull (never scaled down for a small craft):**
  - crew door 1.0 x 2.0 m leaf in a 1.4 x 2.4 m frame;
  - port 1.0 m glass in a 1.4 m frame, 0.86 m portlites on civil ships;
  - bridge pane 1.0 x 1.2 m at 1.12 m pitch;
  - deck pitch 3.0 m, port pitch 2.5 m;
  - rail 1.1 m;
  - ISO 20-ft container;
  - crew figure 1.8 m.

  A small craft gets **fewer** windows, never smaller ones: the fighter's half-size ports made it read
  1.3-1.8x too long.

## Lights (summary; full standard F1-F17 / R1-R12 in `lighting-standard.md`, which is authoritative)

- **Signature look** (the user: "make it look alive", then "not neon"): short, hard-edged, saturated
  amber slits at block corners and in real recesses, with a faint warm spill.
  - Peak modest; colour pre-saturated about 1.3x; halo about 0.1 of the core; no white core; about 3 px
    wide at the hero view.
  - Never on grilles, louvres or radiators; never within 1.5 m of glass; never grazing a face.

| Fixture | Size | Colour | Use |
|---|---|---|---|
| Corner / recess slit | 0.6-1.8 m long x 0.14-0.2 m wide (0.26-0.30 m on ships of 200 m and more) | amber | block corners, joints, real recesses |
| Pin lamp | 0.2-0.3 m | amber (white up to 15 %) | block corners, deck edges; never a lone dot on open plating |
| Door lamp | 0.6 x 0.14 m bar | amber | one per crew door: the human ruler |
| Beacon | 0.26-0.30 m, slow pulse 3-4 s | amber | 2-4 per ship under 250 m, clear of antennas (a lamp on a whip tip reads as a lamp post) |
| Nav lights | 0.4 m | red port, green starboard, white stern and strobes | nothing else goes in `lights[]` |
| Drive status | 0.2 m pins or a short bar | cool blue-white | beside, never through, the white stern light |
| Window glow | real kit glass only, 0.86-1.0 m | warm, per compartment | crew spaces only |
| Bridge / cockpit glass | fleet panes | uniform, about 0.6-0.7x the lit cabins as displayed | bridges run dark; a canopy facing the hero camera even less |

- **Fixture sizes:** one physical size per fixture on every ship. Never scaled with the hull.
- **Budgets grow with class.** Audited ranges (`lighting-standard.md` section 4): fighter 26-34,
  corvette 115-145, civil 160-195 (built at about 120 and reviewed as fine, so the range is under
  review), destroyer about 200-250, carrier exterior 550-800 plus the hangar.
  - **A new class:** interpolate its budget by visible hull area between neighbours of similar size and
    role. Test it with an `OV=` override in `audit.mjs`, add its row to `audit.mjs` and the standard,
    and check that the mark order still holds in the lineup.
- **Small craft** (under about 100 m) are lit only by authored fixtures: no automatic pins, no rows.
- **Exterior work floods** on industrial faces (F17 outside a hangar) are not yet ruled. Decide with
  the user, keep them off in transit, and record the rule here.
- **Windows:**
  - only real kit glass in crew spaces (`livery.glassParts`);
  - lit share by role: warship about 0.45, civil about 0.55;
  - no compartment edge splits a port (`tools/lights/cellcut.mjs`);
  - bridges run dark;
  - fighter-class ports stay dark (a lit door, two windows and a lamp read as a house front).
- **At range:** lights thin by rank and fade by true area; kit glass fades like texture glass.
- **Order:** marks rise fighter < corvette < civil < destroyer < carrier at hero, at range and in the
  lineup.
- **Tools:** `Scene3D/tools/lights/` (audit, dump, raycast, cellcut, partbox, marks).

## Look-dev lighting

- **Studio** (single-ship default): key 2.6, fill 0.8, env 0.55, rim 3.0, exposure 1.4, Neutral tone
  map, lightscape gain 1.15.
- **Orbital** (fleet): one hard sun 50-62° off the lens axis, raking; black space; a true-scale planet
  400 km below; bloom only on the sun, drives and lights.
- **Drives:** a white-hot throat, a dark bell wall with a graded glow, and a short soft plume, never a
  lit disc or beam.

## Geometry language (remodel conventions)

- **Hull:** a loft of stations with planar facets, 4-10 cm bevels, exact boolean recesses (glazing
  bands, door bays, vents, radiator bays, hangars).
- **Superstructure:** tiered, and readable in silhouette from the side, because side views are
  back-lit and flanks sit in shadow.
- **Parts:** drive bells (S/M/L/XL) and turrets (S/M/L) from the procedural kit, at kit size times one
  scale per class.
- Everything is symmetric unless the design says otherwise.
