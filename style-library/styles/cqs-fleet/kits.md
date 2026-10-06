# Parts kits (cqs-fleet)

Two ship kits (procedural and fal), the procedural kit's ground-unit family, two installation kits (yard, spaceport), the
shared building kit (bkit) and the colony components,
all at true metric size. Data (bbox, tris, mount, fal jobs, the engine data for bells, anchors) is in each kit's
`parts.json` (`parts-buildings.json` for the spaceport kit), and the contact sheets are the `kit-sheet.webp` files next
to them.

**The two kits use different mount axes.**
- Procedural kit: every part mounts with **+Z out of the mounting surface**, including stand-on parts such as the container and the antenna.
- fal kit: wall parts mount +Z, and stand-on parts (rail, antenna, container) mount **+Y**.
- assemble.py reads each part's mount, so pass the placement normal as the surface normal either way.

**Which to use.**
- Prefer the procedural kit for glass and functional parts: port, pane, door, bells, turrets, rail, container, navlight.
- Use the fal kit for dressing: dome, pdc, missilePod, sensorArray, dockingClamp, torpedoDoor.
- Duplicates: use `bell-S/M/L/XL` (procedural) over the fal `bell`, and `turret-S/M/L` over the fal `turret`/`twinBarrel`, unless a reference asset already uses the fal one.

## Procedural kit: `Scene3D/assets/parts-blender/` (`tools/blender/kit.py`)

| Part | Size w x h x d (m) | Notes |
|---|---|---|
| airlock | 2.57 x 3.37 x 0.91 | airlock hatch on a 0.8 m collar |
| antenna | 1.25 x 0.64 x 6.01 | mast along +Z, dipole yards at 4.2 m and 5.3 m |
| bell-L | 7.74 x 7.74 x 8.16 | drive bell: exit plane at z = 0 (origin), exhaust toward -Z, mounting back at z = back; engine = the ship-module engine entry (radius, depth of the glow in front of the throat plate, throat, wall) |
| bell-M | 4.86 x 4.86 x 5.13 | drive bell: exit plane at z = 0 (origin), exhaust toward -Z, mounting back at z = back; engine = the ship-module engine entry (radius, depth of the glow in front of the throat plate, throat, wall) |
| bell-S | 3.09 x 3.09 x 3.27 | drive bell: exit plane at z = 0 (origin), exhaust toward -Z, mounting back at z = back; engine = the ship-module engine entry (radius, depth of the glow in front of the throat plate, throat, wall) |
| bell-XL | 15.47 x 15.47 x 16.32 | drive bell: exit plane at z = 0 (origin), exhaust toward -Z, mounting back at z = back; engine = the ship-module engine entry (radius, depth of the glow in front of the throat plate, throat, wall) |
| cargoHatch | 7.80 x 4.89 x 0.54 | bi-parting cargo hatch with a 1 x 2 m crew door |
| clamp | 1.59 x 1.54 x 1.76 | docking clamp; arm swings about X at (0, 0.25, 0.75), claw faces -Y |
| conduit | 4.00 x 0.70 x 0.30 | covered cable conduit along X, tiles at 4 m pitch |
| container | 6.11 x 2.44 x 2.59 | 20-ft ISO container: length along X, height along +Z (deck normal), doors on +X |
| dome | 2.74 x 2.74 x 1.50 | sensor radome on a plinth |
| door | 1.40 x 2.40 x 0.33 | crew door, hinges on -X, handle on +X |
| engineHousing | 13.74 x 13.56 x 7.71 | engine housing with 2 x 2 M bells; exit planes at z = 0, exhaust toward -Z, mounting back at z = back |
| floodlight | 0.56 x 0.36 x 0.48 | floodlight on a yoke |
| ladder | 0.62 x 3.00 x 0.21 | ladder along Y, rungs every 0.3 m |
| missilePod | 3.19 x 5.59 x 0.59 | VLS block, 2 x 4 cells at 1.2 m pitch (X by Y) |
| navlight | 0.40 x 0.40 x 0.27 | nav light housing, 0.4 m; the runtime light sprite goes at `lens` |
| pane | 1.12 x 1.32 x 0.18 | bridge glazing module; tiles edge to edge at pitch (x, y) |
| pdc | 1.28 x 2.39 x 1.74 | rotary point-defence mount, barrels along +Y elevated 22 degrees |
| pipes | 4.00 x 0.86 x 0.47 | three-pipe run along X (0.24 / 0.16 / 0.16 m), tiles at 4 m pitch |
| port | 1.39 x 1.40 x 0.36 | window port, 1.0 m glass, round corners |
| radiator | 10.00 x 4.08 x 0.61 | radiator panel 10 x 4 m on standoffs, tiles along X at 10 m pitch; fins across X |
| rail | 1.00 x 0.12 x 1.13 | handrail segment along X, stanchion at x = 0; tiles at 1 m pitch |
| railgun-muzzle | 6.12 x 4.00 x 5.15 | railgun muzzle cap; joint face at y = 0 (butts on a segment end), muzzle face at y = +4 |
| railgun-segment | 7.50 x 10.00 x 5.30 | spinal railgun barrel segment, y -5..+5, tiles end to end at 10 m pitch |
| rcs | 0.76 x 0.76 x 0.51 | RCS quad block with an outboard nozzle |
| torpedoDoor | 4.09 x 4.09 x 0.47 | bow launch door, two leaves split on x = 0 |
| turret-L | 15.68 x 42.04 x 8.19 | twin gun turret on a barbette, guns along +Y; 1 x 2 m access door on the +X wall |
| turret-M | 8.96 x 24.36 x 4.70 | twin gun turret on a barbette, guns along +Y; 1 x 2 m access door on the +X wall |
| turret-S | 4.48 x 11.24 x 3.80 | twin gun turret on a barbette, guns along +Y; 1 x 2 m access door on the +X wall |
| vent | 1.39 x 0.99 x 0.19 | louvred hull vent 1.2 x 0.8 m |

### Ground-unit parts (procedural kit family, `tools/blender/parts_ground.py`, files in `assets/parts-blender/`)

First used by the V-31 vehicle. True size like every kit part: a heavier ground unit (the tank chassis, later module
variants) gets more wheels or more hatches, never bigger ones. Mount +Z out of the surface, as the procedural kit.

| Part | Size w x h x d (m) | Notes |
|---|---|---|
| foilBox | 0.40 x 0.40 x 0.36 | 0.32 m sensor box in gold MLI foil on a gunmetal plinth (ground units; `parts_ground.py`) |
| markerLamp | 0.26 x 0.16 x 0.13 | covered convoy / marker lamp 0.22 x 0.12 m, hooded slit lens; runtime light at `lens` (ground units) |
| roofHatch | 1.00 x 1.00 x 0.23 | round armoured roof hatch 0.8 m with a periscope, hinge at -Y (ground units) |
| rws | 0.82 x 1.69 x 0.49 | remote weapon station: 0.72 m ring, heavy-MG barrel along +Y, sensor head, ammo box; roof mount, up = forward (ground units) |
| suspension | 0.72 x 1.01 x 0.32 | double-wishbone corner + coil-over; hull wall at z = 0, hub at z = 0.315, damper top 0.62 m above the axle (ground units) |
| vehicleDoor | 1.00 x 1.40 x 0.14 | armoured vehicle door, 0.9 x 1.3 m leaf, surface-mounted frame, vision block; hinges -X (ground units: the ship's 1 x 2 m door does not fit a 2.5 m vehicle) |
| wheel | 1.15 x 1.15 x 0.44 | road wheel, 1.15 m deep-tread tyre, 0.42 m wide, bead-lock rim; axle along +Z, origin = centre of the inner face (ground units) |

**Ground finish (correction 34).** The kit parts of a ground unit take the module's finish, not their own: with
`finish: 'ground'` (`finish.js` `FINISH_PRESETS.ground`) the dust graded up from `anchors.ground`, the dried mud low
down and the matte roughness run continuously over the hull and every part (tyres and wheels dusty, door bottoms and
suspension muddy). The part textures stay clean, so the same parts serve any later ground unit; weathering that
needs the asset's own geometry (edge chips, wheelhouse mud, streaks under vents) is baked into its hull texture
(`vehicle_paint.py` `weather()`), with true-colour texels marked by base-colour alpha < 1 (livery `keep: 1`). PATINA
detail set for ground units: `groundPaint` at a 1.5 m tile (`STYLE.md`, Materials).

## fal kit: `Scene3D/assets/parts/` (nano-banana-pro/edit + Tripo H3.1, `tools/parts/`)

| Part | Size w x h x d (m) | Notes |
|---|---|---|
| door | 1.40 x 2.40 x 0.30 | Crew door: 1.0 x 2.0 m hinged leaf (hinges on the -X side, grab handle and lever on +X, small viewport at eye height) recessed in a 1.4 x 2.4 x 0.3 m chamfered frame. |
| airlock | 1.80 x 2.60 x 0.80 | Crew airlock: flat 1.8 x 2.6 m back flange at z = 0, protruding pressure collar with locking lugs, hatch with a round viewport and a handwheel; collar face at z = 0.8. |
| port | 1.30 x 1.30 x 0.30 | Single 1.0 x 1.0 m round-cornered window aperture in a thick 1.3 x 1.3 x 0.3 m chamfered, bolted frame (frame is crisp). Back at z = 0; sink 0.2 m into the hull for the ~0.1 m proud look. |
| pane | 1.20 x 1.40 x 0.30 | Bridge glazing module 1.2 x 1.4 x 0.3 m (1.0 x 1.2 m glass), square outer sides: tile at a 1.2 m pitch along X. Back at z = 0. |
| cargoHatch | 6.00 x 4.00 x 0.40 | Framed 6 x 4 m double-leaf cargo hatch (hinge blocks along the top, locking bolts on the centre seam), 0.4 m deep, back at z = 0. |
| rail | 1.00 x 1.10 x 0.20 | Handrail segment, 1.0 m long (X) x 1.1 m high (Y): two posts on bolted foot plates, top rail and mid rail. |
| ladder | 0.50 x 3.00 x 0.18 | Wall rung ladder 0.5 m wide x 3.0 m tall, 11 rungs (~0.28 m pitch), standoff brackets at top and bottom. Origin at the bottom centre of the back (bracket) face: foot at y = 0, back at z = 0, +Z out of the hull. |
| rcs | 1.00 x 1.00 x 0.60 | RCS quad: 1.0 x 1.0 m back plate at z = 0, chamfered block, four nozzles pointing +Y, -Y, +X, -X (nozzle exits roughly 0.35 m out from the part centre along each axis, at z ~0.3). |
| antenna | 0.43 x 6.00 x 0.35 | Mast 6.0 m tall (Y) on a 0.3 m square base box, three dipole pairs (0.43 m span) and a tip. Mounts by its base: origin at the base centre, base at y = 0, the hull normal is +Y. |
| dome | 2.50 x 2.50 x 2.36 | Sensor radome ~2.46 m diameter (near-spherical, with a seam band) on a short bolted octagonal ring; flange 2.5 m at z = 0, top at z = 2.36. Axis is +Z (hull normal). |
| floodlight | 0.60 x 0.49 x 0.70 | Floodlight: 0.6 m lamp housing on a U yoke, base plate at z = 0 on the hull, lamp centre ~0.4 m out. The lens aims +Y (along the hull); rotate about Z to aim it. |
| container | 6.06 x 2.59 x 2.44 | 20-ft ISO container 6.06 (X) x 2.59 (Y) x 2.44 (Z) m, doors at +X, bottom at y = 0 (deck normal +Y), origin at the bottom centre. |
| turret | 8.97 x 7.02 x 16.52 | Twin-barrel gun turret, ONE design: round bolted barbette ring (8 m at M), faceted gunhouse (~8.4 x 10 m, roof 6.0 m, blister top 7.0 m), flat mantlet at z = 4.06 with two embrasures, twin barrels (0.9 m OD, axes x = … |
| twinBarrel | 4.72 x 1.95 x 11.30 | Twin gun barrels on a 4.72 x 1.95 x 2.47 m breech block, same barrel spacing (2.54 m) and OD (0.94 m) as the turret, so it drops into the turret embrasures at the same variant scale. |
| pdc | 1.80 x 1.78 x 2.00 | Point-defence mount: bolted round pedestal (1.08 m flange), armoured cradle, six-barrel rotary cannon with two clamp rings pointing +Z and slightly up, ammunition box on one side, sensor box on the other. |
| missilePod | 3.48 x 5.63 x 1.19 | VLS block, 2 x 4 square cells at ~1.2 m pitch (1.23 across, 1.2 along), closed armoured hatch lids with hinge bars on the +Z deck; long axis along Y. |
| railgunSegment | 5.00 x 4.77 x 19.45 | Tileable spinal railgun section: gunmetal rails top and bottom, ceramic insulator stacks, three clamping collars / capacitor bands, cable trays on both sides, bolted end flanges. |
| railgunMuzzle | 4.40 x 4.48 x 6.21 | Muzzle end cap: bolted rear flange (4.4 x 4.48 m) at z = 0, armoured collar with vent slots, square dark bore on the front face, two rail tips protruding to z = 6.2. |
| torpedoDoor | 2.89 x 3.00 x 1.26 | Bow launch door: square chamfered armour frame (2.9 x 3 m), round domed door with centre boss, six locking lugs, two hinge blocks on -X. |
| bell | 4.81 x 5.26 x 8.30 | Drive bell: dark heat-stained bell with reinforcing bands, gimbal ring, off-white combustion chamber and mounting flange, four gimbal actuators. |
| engineHousing | 12.00 x 10.65 x 11.49 | Armoured engine block 12 x 10.66 x 11.5 m: chamfered plates, access hatch and handles on the flanks, four short bells in a 2 x 2 grid on the -Z face (exit r ~2.2 m, protruding only ~0.6 m, cups ~1 m deep, centres ~+-2.9 … |
| radiator | 10.00 x 6.17 x 1.38 | Radiator panel on a gunmetal root hinge beam with two knuckles, chamfered frame, vertical fins between top and bottom manifold pipes; fins on both faces (Tripo mirrored). |
| sensorArray | 4.00 x 3.23 x 0.96 | Phased-array panel 4 x 3.23 m: chamfered off-white frame, 4 x 3 grid of dark emitter tiles, junction box at the bottom edge. Mirrored onto the back by Tripo, so 0.96 m deep; sink it ~0.6 m (position.z = -0.6). |
| dockingClamp | 2.33 x 3.00 x 2.38 | Docking clamp: 2 x 2 m bolted base plate, two opposing jaw arms (one gunmetal, one off-white) closing over a round padded socket, driven by two hydraulic cylinders; 2.34 x 3 x 2.39 m. |

## Yard kit: `Scene3D/assets/parts-yard/` (`tools/blender/buildings/yard_kit.py`)

First used by the planetside shipyard. Mount: every yard part stands on y = 0 (`mount.normal` +Y), origin at the
footprint centre, front +Z. Anchors (lamps, beacons, obstruction lights, slits, windows, floods, doors, panes, vents,
ladders, hook) are in `parts.json`; doors, panes, vents, ladders, floodlights and containers on them are the fleet
procedural kit's parts.

| Part | Size w x h x d (m) | Notes |
|---|---|---|
| gantry | 112 x 115 x 51.2 | portal gantry: span 96 m, 95 m clear, double box girder, A-frame legs, crab with hoist house, fleet-stencil number (`mark`), tex 4096 |
| crane-A / crane-B | ~55 x 81-85 x 14-16 | level-luffing portal crane (12 m gauge, 70 m light jib with amber bands, beak, hook); one bake per pose (`slew`, `luff`, `hook`) |
| hall | 37.3 x 24.1 x 81.3 | workshop hall segment 80 x 36 m, light cladding, pilasters, chamfered roof, half-open 20 x 14 m end door, side roller doors; anchors for kit doors / panes / vents / ladder |
| floodMast | 2.6 x 32.2 x 2.0 | 32 m mast, head frame for 6 kit floodlights (anchors.floods, spot anchor anchors.light) |
| scaffold-S / M / L | 5.2 x 9 / 15 / 23 x 1.5 | scaffold tower, 2.5 x 1.3 m bays, 2 m lifts (4 / 7 / 11), amber toe boards |
| truck | 2.64 x 4.55 x 17.2 | semi: cab-over tractor + 13.6 m box trailer |
| forklift | 1.37 x 3.1 x 4.0 | counterbalance forklift, amber |
| worker | 0.64 x 1.8 x 0.27 | 1.8 m crew figure (the fleet ruler), amber vest, hard hat |
| keelBlock | 3.0 x 2.0 x 2.2 | keel / bilge block; scale y for other heights |
| bollard | 0.36 x 1.17 x 0.36 | lamp bollard; its amber lamp is a lightscape pin at anchors.lamp |

Container stacks are a placement macro (`shipyard_spec.container_stack`) over the fleet kit `container`, not a part.

## Spaceport kit: `Scene3D/assets/parts-spaceport/` (`tools/blender/buildings/spaceport_kit.py`, `parts-buildings.json`)

First used by the SP-3 orbital spaceport. Parametric functions (the GLBs are one baked instance each), vertex-coloured
(no UVs, no textures), true metric size.

| Part | Size w x h x d (m) | Notes |
|---|---|---|
| habBlock(L, W, decks) | 16.1 x 25.5 x 40.5 (40 x 16, 5 decks) | +Y, length along Z; chamfered body on a 2 m plinth, 3 m decks, roof plant, door bay on +Z, amber corner marks; `habBlock_ports()` gives the kit-port positions |
| clampArm(reach) | 16 x 26.2 x 16 (reach 24) | +Y, cradle at y = reach; base plate, two truss arms, rams, cradle with jaws and amber pads |
| manipulator(yaw, a1, a2, l1, l2) | 9 x 38 x 58 (34 + 30 m) | +Y; turret, boom with hazard band, forearm, wrist, effector, cable; returns the tip |
| gantryCrane(span, legL, legR) | 130 x 45 x 16 (span 120) | bridge at y = 0 along X; twin pale box girders, amber stripe, truss legs to rail bogies, trolley, hoist and hook block |
| radiatorArray(n, w, h, solar) | 31 x 122 x 6 (3 pairs of 12 x 34 m) | +Y; lattice mast, thin panels on outriggers (finned radiators or dark solar cells) |
| tug() | 16.8 x 12.3 x 21.1 | centre, bow +Z; yard tug: cab, push plate with fenders, four drive pods |
| truss(p0, p1, w) | - | square lattice (chords, rings, diagonals), the building block of masts, legs, cradles (function only, no GLB) |

**Merged for the colony buildings (2026-10-06).** `bkit.py` (below) is the shared building kit from now on: one
frame (+Y up, plinth top y = 0, front +Z), the yard kit's bake pipeline and materials, the spaceport kit's truss. The
shipyard and spaceport keep their own kits as built; new buildings use bkit, the fleet and yard kits' placed parts, and
the colony components.

## Building kit (bkit): `Scene3D/tools/blender/buildings/bkit.py` (`README-bkit.md`)

Parametric functions at true size, baked into each building's `hull` (lib.Part bake: panel tone, corner grime,
streaks, edge wear; `lib.BAKE` retuned for buildings). First used by the colony pilots (deuterium depot, steel mill).
Lights and placements go into the building's record (`B.R`), not geometry.

| Component | Size / parameters | Notes |
|---|---|---|
| plinth | w x d, 1.4-1.6 m deep, 2 m plan chamfer, 0.5 m kerb, slab joints every 6-8 m | light kerb band, dark toe, markings, grates, edge stairs; amber pins at corners and every 16-18 m |
| facade / block | bays 4-8 m, storeys 3.6-6 m, posts 0.6 m, pilasters 0.4 m, parapet cap 0.42 m | off-white panels in gunmetal frames; recessed warm windows (~55 % lit); roller doors with amber jamb slits; fleet-kit crew doors (1 x 2 m leaf) with 0.6 x 0.14 m lamps and canopies |
| roof units | hvac 3 x 2 x 1.3, vent 1.2, fan 0.8 r, antenna 6 m, solar 6 x 3, tank, box | on `roof_deck` with parapet |
| gable_roof | any span, rise 2-4 m | ridge cap, ribs, ridge skylights, light `panel2` |
| pipe / valve / pipe_rack / cable_tray | r 0.15-1.3 m; supports every 6-8 m | flanges 1.3 r, amber ID rings at the run ends |
| vtank / sphere_tank / htank / stack | any; sphere 21 m on 8 splayed legs; stacks with bands and platforms | stacks carry a red 0.4 m obstruction light |
| railing / catwalk / platform_ring / stair / ladder | rail 1.1 m, stair 0.18 / 0.28 m, ladder 0.62 m, rungs 0.3 m, cage above 2.5 m | fleet rulers |
| truss / lattice_tower | any | spaceport-kit lattice, ported |
| glazing / glow_ring | mullions 1.5 m | warm or hot glow boxes (runtime fixtures, `rotY` on round vessels) |
| tree / planter / crate / cabinet / bollards / lamp_post / hazard_band / stencil | true size | lamp posts: one pin at the head |
| truck / forklift / worker / container / flood_on_wall | yard-kit and fleet-kit parts | placements (`heading` sets `along` for +Y parts) |

## Colony components: `Scene3D/assets/parts-colony/` (`tools/blender/buildings/component.py`)

Fal-made components (an isolated component image with nano-banana-pro/edit in the concept's style, then
`tripo3d/h3.1/image-to-3d`), cleaned, decimated and stood on y = 0 at true size; mount +Y, placed as
`colony:<name>` by `bkit.component()`. The catalogue (made and planned, which buildings use each) is in
`Scene3D/tools/blender/buildings/README-colony.md`; data in `parts.json`. None made yet (fal was blocked in the
pilot session).

## Built into asset scripts (not kit files)

| Part | Size | Notes |
|---|---|---|
| portlite | 0.86 m glass in a 1.14 m frame | civil-ship port, built in `tools/blender/hulls/freighter_extras.py` (node `parts_portlite`, materials `portlite_frame` / `portlite_glass`), sunk 0.03 m; promote it to the procedural kit before reusing it on another civil asset |

## Rules

- A human-scale part is never scaled down for a small craft. Bells and turrets are the only parts placed at a class scale (kit size times one factor per class).
- New parts go into the kit (file, `parts.json` entry, kit sheet) and into this table, not into an asset.
- **Moving parts** (a spinning grinder, turrets that train, doors that open): export them as their own `parts_<name>` node with the pivot at the node origin, and animate that node from the module at runtime. The fleet has no animated parts yet, so record the first one here.
