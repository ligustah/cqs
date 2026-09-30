# Parts kits (cqs-fleet)

Two kits, both at true metric size. Data (bbox, tris, mount, fal jobs, the engine data for bells) is in each kit's `parts.json`, and the contact sheets are the `kit-sheet.webp` files next to them.

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

## Built into asset scripts (not kit files)

| Part | Size | Notes |
|---|---|---|
| portlite | 0.86 m glass in a 1.14 m frame | civil-ship port, built in `tools/blender/hulls/freighter_extras.py` (node `parts_portlite`, materials `portlite_frame` / `portlite_glass`), sunk 0.03 m; promote it to the procedural kit before reusing it on another civil asset |

## Rules

- A human-scale part is never scaled down for a small craft. Bells and turrets are the only parts placed at a class scale (kit size times one factor per class).
- New parts go into the kit (file, `parts.json` entry, kit sheet) and into this table, not into an asset.
- **Moving parts** (a spinning grinder, turrets that train, doors that open): export them as their own `parts_<name>` node with the pivot at the node origin, and animate that node from the module at runtime. The fleet has no animated parts yet, so record the first one here.
