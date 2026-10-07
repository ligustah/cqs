# Style: cqs-fleet

The ships, ground units and buildings of the Conquer-Space reboot: one civilisation, one shipyard
tradition, one quality bar. This file is the specification that work and review follow. Every rule says
which asset types it applies to: **All**, **Ships**, **Ground** (ground units) or **Buildings**
(planetside and orbital).

**Sources of truth** (where this file and a source disagree, fix whichever is wrong; never leave the two
apart):

| What | Where |
|---|---|
| History: why each rule exists, in the user's words | `corrections.md` |
| Ship lights in full | `lighting-standard.md` (F1-F17, R1-R13, sections 4 and 8) |
| Ship sizes | `Scene3D/src/lib/scale.js` |
| Per-asset targets | the approved concept image, then `briefs/<asset>.md` (where they disagree the concept wins; fix the brief) |
| Recipes (how) | the family guide; see **Where to start** |
| Process | the model-forge skill |

## 1. Hard rules (All)

1. **Original IP.** Never open or reference `Artwork/**`, `Html/Design/pack/units/*`, or the old game's `*.blend`
   files. Only the class roster and gameplay stats come from the old code.
2. **No franchise imitation:** Star Wars, Star Trek, The Expanse, Halo, BSG, Homeworld, EVE. Never name them
   in a prompt. Every concept is judged for look-alikes.
3. **fal budget:** no cap. Don't plan around or report the remaining credit. Record every job (model, request
   id, inputs, use) in `Scene3D/pipeline/fal-pipeline.json`.
4. **Concepts before modelling.** All concepts of a batch are approved by the user before any turnaround, mesh or
   remodel. The 16 colony building concepts are already approved (`images/buildings/<id>-concept.jpg`).
5. **fal gives blueprints and small parts; Blender builds the asset.**
   - Anything whose longest side is over 3.0 m, and every signature shape, is rebuilt as parametric
     hard-surface geometry. An image-to-3D mesh of it serves only for measuring.
   - Raw fal meshes may remain only as kit parts of 3.0 m or less, cleaned to flat facets.
   - Nothing is scaled up past its source detail.
   - No image-to-3D texture stays on a rebuilt part.
6. **Compose from components and reuse.**
   - Complex assets are composed from reusable components.
   - Repeated parts, and ships or vehicles shown in a scene, are the existing models (instanced GLBs, kit
     parts in `kits.md`).
   - A new part goes into the kit.
7. **Base chassis only.** No module variants (weapon pods, add-on armour, speed packs) yet.
8. **Check what the user sees.** Review the published package on the desktop and phone tiers (section 8)
   before reporting. Show the user HD images, never file paths.
9. **Living guide.**
   - Every step, setting and gotcha goes into the family guide in the iteration it is learned.
   - Every iteration ends with a review against section 8 and the guide's checklist, item by item, pass or fail
     with evidence.

## 2. Quality bar (All)

Current-generation real-time game art. Pass means all of these hold:
- **Geometry:**
  - flat facets, with no wobble over 1 cm;
  - straight edges;
  - every exposed edge chamfered (hulls 4-10 cm, buildings and ground units 2-6 cm), showing as a lit 1-2 px
    line in the close view;
  - openings cut exactly, with real depth.
- **Texture:** in a close view (section 8, rendered at 1600 x 1000 and cropped without scaling), a 5 cm seam or bolt row
  is at least 2 px wide, with no visible texel blur or stretch.
- **Materials:** layered PBR, meaning base colour plus ORM (occlusion, roughness and metalness in R, G, B),
  a normal map, AO and wear.
- **Shadows:** real shadows on the desktop tier. The phone tier has no screen-space AO, and that is not a fail.

**Concept fidelity: "very similar vibes".** A concept-led asset matches its concept at a glance in silhouette,
mood, grit, density and warmth. It need not match pixel for pixel. Pass means:
- `paint-check` within band (section 8);
- the render's icon keeps the concept's signature shapes and light / dark value split (section 5's bounds apply to
  the render, not to the concept);
- a **blind judge** says "match" for each of the five qualities. The judge is a fresh subagent with no build
  context, shown only the concept and the render side by side, and answers match / no match per quality with one
  line of reason.

Keep iterating without asking the user until it passes, for at most 25 review rounds per asset. Round 25 at the latest
is the final build with its checks and evidence; anything still open goes to the user in the report.

## 3. Identity (All)

- **Naval-industrial,** near-future and credible: faceted hard-surface forms with chamfered, layered plates.
- **Engineering logic you can read:** radiators, shielding between drive and crew, RCS quads, hatches and rails
  at human scale.
- **Pipes and ducts connect.** Every run goes from a visible source to a visible destination (a vessel nozzle, a
  header, a valve, a pump house, a stack inlet), with flanged ends and its own supports at most 6 m apart. A run
  never passes through, or emerges from, an unrelated housing, wall or roof.
- **No aerodynamic wings, and no launch hardware.** Ships land and take off under their own power, so
  installations have no launch rails, cradles, towers or blast pits.
- **Ships:**
  - Warships are blunt and armoured, with the superstructure low and tiered and the armament readable in
    silhouette.
  - Civil ships are lean spines carrying modules.
  - Drives are fusion bells with magnetic-nozzle coils.
  - Weapons: railguns (spinal on the destroyer), turrets, PDC and missile cells.
- **Docks and yards** show the fleet's own spacecraft, never sea ships. A ship under construction is the real
  fleet model cut back to its build state. Scaffolding and gantries look clearly different from finished hulls.
- **Symmetry:** everything is symmetric unless the design says otherwise.

## 4. Per-type specification

| | Ships | Ground units | Planetside buildings | Orbital buildings |
|---|---|---|---|---|
| Size from | hangar slots (`scale.js`, section 6) | the brief, true size (V-31 body 6.5 x 2.6 x 2.5 m) | the concept, real-world plausible; footprint and height recorded in `SPEC` in `tools/blender/buildings/<id>.py` | ≤ 1.3x the length of its largest product |
| Paint | dark operational livery: low-visibility marks; civil ships keep weathered cargo colours | dark operational livery, with marks legible (amber, cobalt, unit number) | **light paint**: off-white panels and shells framed by dark neutral gunmetal | light station paint with dark structure |
| Finish level | worn, not dirty | matte and visibly used, not a wreck | worn, not dirty | worn, not dirty |
| Finish preset | `ship` | `ground` | `building` | `building` (the shipyard and spaceport use `ship`; to align when they are next rebuilt) |
| Texel density | hull ≥ 20 px/m | body: 2048 px over the vehicle | light surfaces ≥ 50 px/m; hero surfaces (the concept's signature element, e.g. the furnace shell) ≥ 70; dark structure ≥ 25 | as planetside |
| Lights | `lighting-standard.md` in full | authored only (section 7) | section 7 | section 7 |
| Studio | ship studio (`env/lighting.js` STUDIO) | ship studio | dusk studio (`colony.js` DUSK) at the concept camera | dusk rig with the space backdrop |
| Ground / base | — | contact with the ground: dust and mud | chamfered concrete plinth slab (kerbs, markings, edge lamps, staining) | none |
| Phone (per view) | heap + GPU < 300 MB | < 300 MB | < 300 MB, ≤ 150k tris, ≤ 7 MB fetched | < 300 MB |

**Buildings** (both kinds):
- **Function:**
  - Busy, not bulky: every large element has a job.
  - Enclosures stay thin and broken up: no single unbroken wall or roof spans more than 30 % of the silhouette's
    width at the concept camera (a judgement threshold).
  - Each main bay (a dock, berth, build hall or process bay) holds at least one live element: a docked ship, a
    crane, a vehicle, a tug or cargo.
- **Read:** a strong light / dark material split, with deep shadowed recesses and layered volumes.
- **Secondary detail at true scale:**
  - pipe runs with flanges and amber rings, cable trays, catwalks, railings, ladders and stairs;
  - roof units and vents, door canopies, small machinery, valves, crates and pallets;
  - lamp posts, vehicles and 1.8 m figures.
  - Pass: no bare run of plinth or apron over 15 m at the concept camera, measured against the 1.8 m figure or the
    plinth's 10 m grid (a judgement threshold).
- **Grit:**
  - panel-to-panel tone;
  - dark seams;
  - crisp **vertical** rust and grime streaks under seams and edges;
  - soot on roofs, with dark lap lines;
  - a stained plinth.

  Tonality is warm, with lifted shadows; the material split stays strong.
- **Colour** (`paint-check`, section 8):
  - the light paint's luminance is 0.9-1.1x the concept's, and its hue is within 10° of the concept's (the concepts
    sit at about 20-25°);
  - dark steel saturation ≤ 0.1 (neutral grey, never brown; the concepts are about 0.09). Measure it on a crop that
    holds only dark structure, because the tool's mid band also picks up the backdrop.

**Ground units:**
- Roughness 0.84-1.0. Glass is hazy, never a mirror.
- Dust is full up to 0.4 m and gone by 1.55 m. Dried mud below 0.75 m and in the wheel arches.
- Chips on every exposed edge, grime in recesses, run-off streaks under edges and panes.
- The silhouette and lamps stay clean.

**Ships:**
- **Drives:** a white-hot throat, a dark bell wall with a graded glow, and a short soft plume. Never a lit disc
  or a beam.
- **Wear:** drive soot and plate-tone wear.
- **Orbital scene:** one hard sun 50-62° off the lens axis, black space, and a true-scale planet 400 km below.
  Bloom only on the sun, drives and lights.

## 5. Thumbnail readability (All)

The game shows each asset as a square icon on #222d35: 80 px for the current job and on hover, 40 px in queues.

| Check | Pass |
|---|---|
| Icon camera | three-quarter view, az 35, el 30, square crop |
| Silhouette | max(w/h, h/w) ≤ 1.5 and fill ≥ 0.6 (`thumbs.mjs` prints `aspect` = w/h and `fill`; fill is a judgement threshold) |
| Signature shapes | 1-2 shapes carry the identity (a cab profile, a ring, an arch, a furnace, a dish); markings and small parts are a second layer |
| Value | a light / dark split, or one bright signature element |
| Recognition | on one `thumbs.mjs` sheet with its siblings (the other colony buildings, or the ship classes), a blind judge names the asset at 80 px and tells it apart from every sibling at 40 px |

## 6. Shared rules (All)

**Rulers.** True-size hardware, never scaled with the asset. A smaller asset gets **fewer** fixtures and
windows, never smaller ones.

| Item | Ships and buildings | Ground units |
|---|---|---|
| Crew door | 1.0 x 2.0 m leaf in a 1.4 x 2.4 m frame | 0.9 x 1.3-1.4 m door; 0.7-0.8 m hatch |
| Window | 1.0 m port in a 1.4 m frame (civil portlite 0.86 m); bridge pane 1.0 x 1.2 m at 1.12 m pitch | armoured pane 0.6-0.9 m |
| Shared by all | rail 1.1 m; deck pitch 3.0 m; port pitch 2.5 m; ISO 20-ft container; figure 1.8 m; the lamp sizes in section 7 | |

**Ship sizes** (one slot is 70,000 m³ of bounding box; `node tools/scale-check.mjs` must print SCALE CHECK PASSED):

| Class | Slots | Length | Crew |
|---|---|---|---|
| Fighter | 1 | 71.7 m | about 40 |
| Corvette | 5 | 108 m | about 350 |
| Civil ship (cargo / troops) | 4 | 134 / 129 m | about 80 / 750 troops |
| Destroyer | 12 | 203 m | about 2,000 |
| Carrier | 50 slots of hangar (670 x 155.8 x 84.4 m, 2 m clearance) | 900 m | about 20,000 |

A class not in the game's roster (`UnitEnum`) needs the user's decision first.

**Palette** (linear RGB unless marked):

| Role | Value |
|---|---|
| Light panel (buildings) | 0.60 / 0.60 / 0.585; second tone 0.47 |
| Dark frame (gunmetal) | 0.040 / 0.042 / 0.046 |
| Concrete | 0.30 |
| Cobalt band | 0.045 / 0.15 / 0.40 |
| Hazard amber (sRGB) | 0.93 / 0.58 / 0.12 (hue about 35°); prompt it as "amber", never "orange" |
| Window glow | ships 0.52 / 0.42 / 0.28; buildings `#ffd29a` at radiance 1.35 |

Other notes:
- Generation paint for image models is off-white thermal paint with amber and cobalt marks, gunmetal frames,
  gold / silver foil on sensor boxes and dark ceramic belly tiles. Generate light, because light paint
  reconstructs better.
- Livery schemes (`livery.js`): `dark` is the default for ships and ground units; `civil` is for cargo ships;
  `tone` and `bone` are opt-in only.

**ID codes.**
- Fleet stencil font. White numbers sit on a dark ID field, and never read as windows at oblique angles.
- Every asset has a code (class letters and number, e.g. DD-12, V-31, SM-1), listed in `assets.md`.

## 7. Lights

**All:**
- The signature is short, hard-edged, saturated amber slits at block corners and in real recesses: alive, not
  neon.
- No white core at the hero view. Amber slits and bars run at radiance 0.9-2.0; flood lenses go up to 2.2.
- Never on grilles, louvres or radiators, never within 1.5 m of glass, never grazing a face.
- One size per fixture within an asset family (ships: `lighting-standard.md` section 2; buildings: the table
  below). Never scaled with the asset.
- Warm, lit windows only on real glass in crew spaces.

**Ships:** `lighting-standard.md` applies in full. Pass:
- `node tools/lights/audit.mjs <ship>` reports PASS;
- `node tools/lights/cellcut.mjs <ship> <glassCell> <glassPhase> <parts>` (values from the ship's livery) finds 0
  split ports;
- `tools/lights/marks.py` (run with the Blender venv python) shows steps ≥ 1.8x / 1.2x / 1.1x / 1.5x up the class
  order, and the fighter shows ≤ 35 marks at hero and ≤ 18 at dist 5.

**A new ship class**, once the user has approved it:
- add it to `scale.js` CLASSES (slots) and `carrierLoads`;
- add it to the budget table in `audit.mjs`, `PRESET` in `pkg-diff.mjs` and `VIEWS` in `phone-check.mjs`;
- lamp budget: interpolate lamps per 1000 m² between the neighbouring classes (`lighting-standard.md` section 4),
  with `keep` ≤ the larger neighbour's;
- its marks count sits between its neighbours in the `marks.py` order.

**Ground units:**
- Authored lamps only (about 7): covered slits of 0.16 x 0.05 m at the kit lenses.
- No round headlamps, no light bars, and no lit glass.
- Red tail lamps and the convoy lamp are allowed.

**Buildings** (generated by `colony.js` from the building's DATA):

| Fixture | Spec |
|---|---|
| Corner / recess slit | 0.14-0.20 m wide (0.18 default) x 0.6-1.8 m, amber, radiance about 1.6 |
| Door lamp | 0.6 x 0.14 m over every crew door |
| Pin lamp | 0.3 m amber, at block corners, plinth corners and edges |
| Beacon | 2-4, 0.3 m, pulsing every 3.6 s |
| Obstruction | red 0.4 m on stacks and masts over 5 m; these are the only `lights[]` entries |
| Windows | about 55 % lit, warm |
| Floods | 2-4, aimed away from the camera |
| Process glow | molten metal, a reactor or an energy field: glow radiance ≥ 0.4, with a visible pool on the ground at the concept camera |

## 8. Review protocol (All)

**Views.**
- Ships and ground units: `node tools/shoot.mjs "<query>" out.png --w 1600 --h 1000`.
- Buildings: `node tools/buildings/compare.mjs <id> --w 1600 --h 1000`. Close-ups are added with
  `--extra "<name>=focus=x,y,z&dist=m"` (building frame, metres).
- Always freeze time with `t=20`, and compare before and after at the same camera and size.

| Type | Views |
|---|---|
| Ships | icon (az 35, el 30); hero (az 35, el 18); close (az 50, el 14, dist 0.72); range (dist 2.5 and 5); stern quarter (az 145, el 15); broadside (az 90, el 0); lineup (`mode=lineup`); scene (`mode=fleet&shot=hero`) |
| Ground units | icon; hero; close; lineup |
| Buildings | icon; the concept camera; 3 close-ups (the hero element, the main process element, a wall); the spaceport also in the scene (`mode=fleet&shot=spaceport`) |

**Checklist.** Each item is pass or fail, with the evidence logged per iteration.

| Check | Tool | Pass |
|---|---|---|
| Quality bar | the close views, at 1:1 | every section 2 item holds |
| Concept fidelity (concept-led assets) | `tools/buildings/compare.mjs` + blind judge | "match" on all five qualities (section 2) |
| Paint | `python3 tools/buildings/paint-check.py <concept> <render>` | light luminance 0.9-1.1x the concept's; hue within 10° |
| Type spec | section 4 table and notes | every row holds |
| Thumbnail | shoot the icon view, then `node tools/thumbs/thumbs.mjs sheet.png "<id>=icon.png" "<sibling>=…"` | section 5 |
| Texel density | `remodel.py` px/m report | section 4 |
| Geometry vs blueprint | ships: `hulls/compare.py`; buildings: `cmeasure.py --compare` per component | ships: `edge_p95_m` ≤ 0.3 per view; buildings: `iou_<view>` ≥ 0.9 (a judgement threshold), except deliberate fits to the concept recorded in the guide |
| Scale (ships, ground units) | `node tools/scale-check.mjs` | prints `SCALE CHECK PASSED` |
| Lights | section 7 (ships: the audit tools) | passes |
| Package | `node tools/build-artifact.mjs` (runs `check-package.mjs`) | prints `package check: … match their source`, with no FAIL rows |
| Package as served | `node tools/pkg-diff.mjs <view>` and `node tools/pkg-diff.mjs --device phone <view>` (view: `b_<id>`, a ship name, `fleet` or `spaceport`) | every line `ok` (desktop ≤ 2 %, phone ≤ 6 %, no shader program over 16 samplers) |
| Phone | `node tools/phone-check.mjs <view>` | from its line: `heap+gpu` < 300 MB; buildings also `tris` ≤ 150k and `fetched` ≤ 7 MB |
| Published | open the published preview and look at every changed asset | matches the local renders |

**Evidence per iteration** (in `images/<family>/<id>-vN*`):
- the concept-camera compare sheet, the close-up sheet and the thumbnail sheet with siblings;
- a log of the paint-check JSON, the px/m report, the geometry metric, and the package, pkg-diff (desktop and
  phone), phone-check and light-audit lines;
- the checklist review: every row pass or fail, with its evidence.

## Where to start

| Asset type | Guide | Also read |
|---|---|---|
| Ship | `Scene3D/tools/blender/hulls/README.md` + `README-<ship>.md` | `lighting-standard.md` |
| Ground unit | `Scene3D/tools/blender/hulls/README-vehicle.md` | `briefs/vehicle.md` |
| Colony building | `Scene3D/tools/blender/buildings/BUILDING-GUIDE.md` (with `README-colony.md` and `README-bkit.md`) | `briefs/buildings.md` |
| Shipyard / spaceport | `README-shipyard.md` / `README-spaceport.md` in the same folder | `briefs/shipyard.md`, `briefs/spaceport.md` |
| Any | `kits.md` (parts), `prompts.md` (prompts that worked), `lessons.md` (gotchas), `assets.md` (codes and status) | |
