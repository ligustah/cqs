# Style: cqs-fleet

The orbital fleet of the Conquer-Space reboot. Every asset here must look like it came from the same
shipyards.

## Hard rules

- **Original IP only.** Never open, read or reference the legacy art: `Artwork/**`,
  `Html/Design/pack/units/*`, `*.blend` from the old game. Only class roster and gameplay stats come
  from the old code.
- **No imitation** of franchise ships: Star Wars, Star Trek, The Expanse, Halo, BSG, Homeworld, EVE.
  Do not name them in prompts either. A judge checks every concept for look-alikes.
- **Budget:** about **$100 of fal credit remaining** on the account (user, 2026-10-01; correction 17).
  This is the hard cap for all further work in this style: check spend before every batch, and record
  every job in `Scene3D/pipeline/fal-pipeline.json`. The fleet itself cost about $78.

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
- The prompts are in `prompts.md`; the files are in `Scene3D/assets/materials/` (`manifest.json`).

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
