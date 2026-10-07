# Style: cqs-fleet

The ships, ground units and buildings of the Conquer-Space reboot. Every asset must look like it came from
the same civilisation and the same shipyards, and hold up at the quality bar below.

This file says what an asset needs to get right. How each rule came about (the user's own words) is in
`corrections.md`. The step-by-step recipes live in each family's guide: buildings in
`Scene3D/tools/blender/buildings/BUILDING-GUIDE.md`, ships in `Scene3D/tools/blender/hulls/README.md`.

## Hard rules

- **Original IP only.** Never open, read or reference the legacy art: `Artwork/**`,
  `Html/Design/pack/units/*`, or the old game's `*.blend` files. Only the class roster and gameplay stats
  come from the old code.
- **No imitation of franchise designs** (Star Wars, Star Trek, The Expanse, Halo, BSG, Homeworld, EVE).
  Never name them in prompts. A judge checks every concept for look-alikes.
- **Budget:** no cap on fal. Aim for the best result, and don't plan around or report the remaining
  credit. If the account runs dry, say so. Record every job in `Scene3D/pipeline/fal-pipeline.json`.

## The quality bar

**Current-generation real-time game art, judged at 1:1.**
- Clean, dense hard-surface geometry: flat facets, straight edges, bevels that catch the light, real
  recesses and layered volumes.
- Texel density that holds at close range, with seams, bolts and grime crisp in a close-up.
- Layered PBR: base colour, ORM, detail normals, AO and wear.
- Real shadows.

A concept-led asset must **match its concept's vibes**: the same mood, grit, density, warmth and
silhouette at a glance. It does not have to match pixel for pixel. Keep iterating without asking until it
does.

## How assets are made

- **Concepts first.** When several assets are designed together, settle every concept with the user before
  any turnaround, mesh or remodel.
- **Full pipeline:** concept, turnaround, blueprint mesh, parts, remodel, assemble, look, review, release.
- **fal makes blueprints and small parts, Blender makes the asset.**
  - An image-to-3D mesh is a measuring blueprint.
  - Every component over about 3 m, and every signature shape, is rebuilt as clean parametric
    hard-surface geometry and painted in texture space.
  - Raw fal meshes survive only as small kit parts (about 3 m and under), cleaned and flattened.
  - A mesh is never scaled up past its source detail, and no Tripo texture stays on a remodelled part.
- **Compose from components.** Break a complex asset into reusable components and compose it from them.
  Never reconstruct a whole building as one mesh.
- **Reuse first.** Repeated parts, docked or part-built ships and vehicles are the existing models
  (instanced GLBs, kit parts, PATINA sets). A new part goes into the kit for the next asset.
- **Living guide.**
  - Each asset family keeps one guide. Every step, setting and gotcha goes into it in the iteration it is
    learned.
  - After each iteration, review the work against the guide's checklist, item by item, with evidence.
  - Fix the guide wherever the review shows a gap.
- **Check what the user sees.** Review the published preview through the real package, on desktop and
  phone tiers, before reporting a result.
- **Phone first.**
  - The user views the preview on a phone. Every asset has a phone budget (300 MB heap plus GPU per view).
  - The scene loads only what the current view needs.
  - The phone tier is tested before every publish.
  - A material uses at most 16 fragment samplers.
- **Scope.** Unit module variants (weapon pods, add-on armour, speed packs) come later. Build the base
  chassis.

## Identity

Credible near-future "naval-industrial" hardware, photographed like studio models.
- Faceted hard-surface forms with chamfered edges and layered armour plates. No aerodynamic wings.
- Real engineering logic: radiators, shielding between drive and crew, RCS quads, hatches and rails at human
  scale.
- **Drives** are fusion bells with magnetic-nozzle coils.
- **Ship types:**
  - Warships are blunt and armoured.
  - Civil ships are lean spines carrying modules.
- **Weapons** are railguns (spinal on the destroyer), turrets, PDC and missile cells.
- Ground units and buildings share the same construction, markings and rulers.
- Ships land and take off under their own power on any planet. Installations need no launch rails,
  cradles, towers or blast pits.

## Thumbnail readability

The game shows every unit and building as a **square icon**, on the dark UI panel (#222d35):
- 80 px for the current job and on hover;
- 40 px in queues and job lists;
- 20 px in compact lists.

Rich detail is for large shots. The icon needs the following:
- **Identifiable at 80 px**, and distinct from every sibling at 40 px.
- **Compact massing:** from the icon camera (three-quarter, about 30° up) the silhouette fills a square
  frame, with a bounding aspect of 1.5:1 at most. Show one dominant structure with the rest tight round it.
- **One or two signature shapes** carry the identity at icon size (a cab profile, a ring, an arch, a tower,
  a dish). Markings and small parts are the second layer.
- **Value contrast that survives downscaling:** a light / dark split, or one bright signature element.
- **Test (a review gate, and also for concepts):** render the icon view and downscale it to 80 and 40 px
  beside its siblings with `Scene3D/tools/thumbs/`. A judge must name each one.

## Buildings and installations

**Form**
- **Sized by function:** real-world, plausible footprints and heights, measured against the rulers.
- **An orbital or ship-building installation** is only modestly larger than the biggest ship it builds.
- **Busy, not bulky:** life comes from activity and parts (cranes, docked ships at true scale, tugs,
  cargo, vehicles, figures), never from a massive continuous shell.
- **Show the actual unit:** a yard shows the real fleet ship part-built (DD-12 in the shipyard, CV-50 in
  the spaceport), instanced from its GLB.
- **A chamfered concrete plinth slab** carries every colony building, with kerbs, markings, edge lamps and
  staining.

**Light paint with dark structure**
- Off-white to warm light-grey panels and shells, framed by dark neutral gunmetal posts, beams, bands and
  plinth edges.
- Dark steel is neutral grey, not brown.
- The light / dark contrast is the building's read.

**Depth**
- Deep, shadowed recesses and layered volumes.
- The overall value is lower than a daylight render.

**Dense secondary detail at true scale**
- Pipe runs with flanges and amber rings, cable trays, catwalks, railings, ladders and stairs.
- Roof units and vents, door canopies, small machinery, valves, crates and pallets, lamp posts, vehicles.
- The apron round the main volumes is packed, never bare.

**Grit: worn, not dirty**
- Panel-to-panel tone, dark panel seams, and crisp vertical rust and grime streaks under seams and edges.
- Soot on roofs, with dark lap lines.
- A stained plinth.
- Warm, lower-contrast tonality.

**Light**
- Warm lit windows and amber lamps on corners, pilasters, doors and the plinth edge.
- A few work floods.
- Process glow (molten metal, a reactor, an energy field) bright enough to spill onto nearby ground.
- The dusk-blue studio.

**Texel density** (light surfaces): about 50 px/m or more, and about 70 px/m on hero surfaces. Dark
structure must also stay crisp at the closest review crop.

## Ground units

- **Finish:** matte paint and visibly used, never glossy.
  - Dust and dried mud on the lower body, wheels and arches.
  - Chipped edges and grime in recesses.
- **Worn and dirty, not a wreck:** the marks (amber, cobalt, unit number), the lamps and the silhouette
  stay clean and legible. The dark livery is the default.
- **Surface detail is tiled at the asset's scale:** plate texture, scratches and grit show at close range.
  The recipe is the ground finish under Materials.

## Palette and livery

- **Generation paint:** off-white thermal paint with weathering, signal-orange hazard and ID markings, small
  cobalt bands, gunmetal frames, gold / silver MLI foil on sensor boxes, dark ceramic belly tiles.
  Generate in light paint, because it reconstructs better.
- **Ships and ground units: the operational livery is dark matte grey** (dark ships are harder to spot).
  - `livery.js` `dark`: base 0.016, gain 0.065, tint #e3e7eb, marks faint (mark 0.11, markSat 0.05).
    Warships may keep a little more (destroyer mark 0.18, markSat 0.3).
  - The two-tone schemes `tone` (warm mid grey) and `bone` (off-white next to charcoal) are opt-in only.
- **Buildings keep the light paint** (see Buildings).
- **Hazard paint:** amber (0.93, 0.58, 0.12), not orange.
- **Hull numbers:** the fleet stencil font. White numbers sit on a dark ID field. The numbers in use are
  F-402, K-214, CT-4 / CT-7, DD-12 and CV-50.

## Materials

- **Hulls:**
  - **PATINA tri-planar detail** at one absolute tile (6 m): set `hull`, normalStrength about 0.6 and cavity
    about 0.2 on remodelled hulls, which carry their own seams.
  - **Worn finish** (`finish.js`, on by default): `hullWear` (two-scale plate tone), `hullGrit`,
    `sootStreak` (drive soot), plus GTAO.
- **Hangar:** set `deck`, plus the same set at 7.3x scale for panel tone that reads from a kilometre.
- **Scene-built parts:** the full sets `armor`, `orange`, `ceramic`, `foil` and `radiator`.
- **Ground finish** (`finish.js` `FINISH_PRESETS.ground`; a module sets `finish: 'ground'`):
  - **Detail layer:** set `groundPaint` at a 1.5 m tile, normalStrength 1.4, roughAmount 0.8, cavity 0,
    `skipGlass: true`.
  - **Roughness and glass:** roughness 0.84-1.0 (mean 0.92). Livery `matte: 0.75`, `glassRough: 0.8`.
  - **Wear and grit:** wear tone at 2.5 / 9 m and grit at 0.35 m. Scratches show lighter.
  - **Ground layer:** in true albedo, graded from `anchors.ground`.
    - Dust: full up to 0.4 m and gone by 1.55 m.
    - Dried mud below 0.75 m.
    - A thin dust film on up-facing surfaces.
  - **Baked in the asset's paint script** (template: `vehicle_paint.py` `weather()`):
    - edge chips with red-oxide primer;
    - stone chips;
    - wheelhouse mud;
    - recess grime and run-off streaks;
    - a sun-faded roof;
    - scuffed markings.

    True-colour texels are written with base-colour alpha < 1, so the livery leaves them as they are.
- **Buildings:** the `building` finish preset. Colour comes from the kit's calibrated paint zones and
  texture-space layers (see the buildings guide).
- The prompts are in `prompts.md`; the files are in `Scene3D/assets/materials/` (`manifest.json`).

## Scale model and rulers

**Source of truth:** `Scene3D/src/lib/scale.js`, checked by `tools/scale-check.mjs`, which must pass.

**Size comes from the game,** via hangar slots. One slot is 70,000 m³ of envelope, and each class is
scaled so its bounding-box volume equals its slots times 70,000.

| Class | Slots | Length | Crew |
|---|---|---|---|
| Fighter | 1 | 71.7 m | about 40 |
| Corvette | 5 | 108 m | about 350 |
| Civil ship (cargo) | 4 | 134 m | about 80 |
| Civil ship (troops) | 4 | 129 m | 750 troops |
| Destroyer | 12 | 203 m | about 2,000 |
| Carrier | 50 slots of hangar | 900 m | about 20,000 |

The carrier's hangar (670 x 155.8 x 84.4 m) parks every legal full load with 2 m clearance.

**Adding a class.** "N slots" means the slots the ship occupies when parked. A class that is not in the
game's roster (`UnitEnum`) is a design decision for the user. To add one:
- a `CLASSES` entry in `scale.js` (size, label, gameId, role);
- a module in `src/ships/<id>.js`, registered in `src/ships/index.js`;
- the hangar check (`carrierLoads`) if carriers can park it;
- its rows in `audit.mjs` and in the lighting standard.

**Human-scale rulers**, identical on every asset and never scaled:
- crew door: a 1.0 x 2.0 m leaf in a 1.4 x 2.4 m frame;
- port: 1.0 m glass in a 1.4 m frame (0.86 m portlites on civil ships);
- bridge pane: 1.0 x 1.2 m at 1.12 m pitch;
- deck pitch 3.0 m and port pitch 2.5 m;
- rail 1.1 m;
- ISO 20-ft container;
- crew figure 1.8 m.

A small craft gets fewer windows, never smaller ones.

## Lights

This is a summary; `lighting-standard.md` (F1-F17, R1-R12) is authoritative.

**The signature look is alive, not neon:** short, hard-edged, saturated amber slits at block corners and in
real recesses, with a faint warm spill.
- A modest peak, colour pre-saturated about 1.3x, a halo about 0.1 of the core, no white core, and about
  3 px wide at the hero view.
- Never on grilles, louvres or radiators, never within 1.5 m of glass, and never grazing a face.

| Fixture | Size | Colour | Use |
|---|---|---|---|
| Corner / recess slit | 0.6-1.8 m x 0.14-0.2 m (0.26-0.30 m on ships of 200 m and more) | amber | block corners, joints, real recesses |
| Pin lamp | 0.2-0.3 m | amber (up to 15 % white) | block corners and deck edges, never a lone dot on open plating |
| Door lamp | 0.6 x 0.14 m bar | amber | one per crew door: the human ruler |
| Beacon | 0.26-0.30 m, slow pulse of 3-4 s | amber | 2-4 per ship under 250 m, clear of antennas |
| Nav lights | 0.4 m | red port, green starboard, white stern and strobes | nothing else goes in `lights[]` |
| Drive status | 0.2 m pins or a short bar | cool blue-white | beside the white stern light, never through it |
| Window glow | real kit glass only, 0.86-1.0 m | warm, per compartment | crew spaces only |
| Bridge / cockpit glass | fleet panes | uniform, about 0.6-0.7x the lit cabins | bridges run dark |

**Fixture sizes:** each fixture has one physical size on every asset, never scaled with the hull.

**Budgets grow with class.** These are the audited ranges:

| Class | Lights |
|---|---|
| Fighter | 26-34 |
| Corvette | 115-145 |
| Civil ship | 160-195 |
| Destroyer | about 200-250 |
| Carrier exterior | 550-800, plus the hangar |

A new class interpolates its budget by visible hull area and is checked in `audit.mjs`. Small craft (under
about 100 m) are lit only by authored fixtures.

**Windows**
- Real kit glass in crew spaces only.
- Lit share: warships about 0.45, civil ships about 0.55.
- No compartment edge splits a port.
- Bridges and fighter-class ports run dark.

**At range:** lights thin by rank and fade by true area.

**Order:** the marks rise fighter < corvette < civil < destroyer < carrier, at hero, at range and in the
lineup.

**Tools:** `Scene3D/tools/lights/`.

## Look-dev lighting

- **Studio** (single-asset default): key 2.6, fill 0.8, env 0.55, rim 3.0, exposure 1.4, Neutral tone map,
  lightscape gain 1.15. Buildings use the dusk-blue studio at the concept's camera.
- **Orbital** (fleet): one hard sun 50-62° off the lens axis, raking. Black space, and a true-scale planet
  400 km below. Bloom only on the sun, drives and lights.
- **Drives:** a white-hot throat, a dark bell wall with a graded glow, and a short soft plume. Never a lit
  disc or beam.

## Geometry language

- **Hull:** a loft of stations with planar facets, 4-10 cm bevels and exact boolean recesses (glazing
  bands, door bays, vents, radiator bays, hangars).
- **Superstructure:** tiered and readable in silhouette from the side.
- **Parts:** drive bells (S/M/L/XL) and turrets (S/M/L) from the procedural kit, at kit size times one scale
  per class.
- **Buildings:** parametric volumes on the shared building kit (`bkit.py`, `ckit.py`), with 2-6 cm chamfers,
  weighted normals, and every opening cut exactly.
- Everything is symmetric unless the design says otherwise.
