# Assets built in this style

All of them are in `Scene3D/`. Each ship and ground unit has its module in `src/ships/<id>.js`, its GLB in
`assets/ships/<id>.glb`, its hull script and spec in `tools/blender/hulls/<id>*.py` and
`tools/blender/specs/<id>-v3.json`, and its build notes in `tools/blender/hulls/README-<id>.md`. Buildings have their
module in `src/buildings/<id>.js`, their GLB in `assets/buildings/<id>.glb`, their scripts in `tools/blender/buildings/`,
their spec in `tools/blender/specs/<id>-v1.json` and their notes in `tools/blender/buildings/README-<id>.md`.

| Asset | Length | Crew | Signature | Status |
|---|---|---|---|---|
| F-402 Petrel fighter | 71.7 m | about 40 | faceted armoured pod, flank sponsons with twin railguns, five-pane canopy, two ports by the crew door, twin main bells + sponson bells | remodelled, v14 lights (26 lamps) |
| K-214 Warden corvette | 108 m | about 350 | wedge hull, bow torpedo frame, deckhouse + tower, outrigger drive pods | remodelled, v14 lights |
| CT-4 Drover freighter | 134 m | about 80 | crew module, truss keel with 20-ft containers, reactor block, radiators | remodelled, v14 lights |
| CT-7 troop transport | 129 m | 750 troops | same spine, four habitat cylinders in the girder | remodelled, v14 lights |
| DD-12 Bastion destroyer | 203 m | about 2,000 | spinal railgun through a blunt octagonal bow, 12 turret-M, broadside sponsons, VLS, armoured command block, lattice mast | remodelled (v9 polish), v14 lights |
| CV-50 Keystone carrier | 900 m | about 20,000 | open-flank through-deck hangar (670 x 155.8 x 84.4 m) parking every legal load, 40-deck island, bow mouth | remodelled, v14 lights |
| V-31 Kestrel light armoured vehicle | 6.95 m (body 6.5 x 2.6 x 2.5 m) | 2-4 | ground unit at true size: tall faceted cab with a flat roof to the tail, gunmetal nose collar, four 1.15 m tyres on double wishbones, RWS behind two round roof hatches, 7 covered lamps | built v1; ship studio `#vehicle` and the lineup (front row), never in the orbital fleet |
| SY-1 planetside shipyard | 250 m berth, yard about 250 x 270 m | yard crew | dark portal gantry "01" over one berth, two luffing cranes, light workshop halls, flood masts; the real DD-12 cut back to its build state; dusk | built v1; building view `#shipyard` |
| SP-3 orbital spaceport | 1,131 m | about 6,000 | two offset dark half-shells with pale rims round the berth, habitat blocks, cranes, manipulator arms; the real CV-50 under construction (bow plated, frames aft), four docked CT-4s | built v1; building view `#spaceport`, in the fleet scene 3 km off the carrier's starboard bow (`shot=spaceport`) |
| DP-3 deuterium depot (colony) | slab 72 x 48 m, 26 m | depot crew | three 21 m spheres on braced legs with cobalt bands, manifold, two pump houses | built v2 (fal components sphereTank x3, plantHouse x2, manifoldSkid, filterBank + bkit); building view `#deuterium_depot`; sheets `images/buildings/deuterium_depot-v1.jpg` (kit only), `-v2.jpg` |
| SM-1 steel mill (colony) | slab 80 x 92 m, 61 m | works crew | blast furnace in a steel tower frame, skip gallery, glowing pour bay with amber crane, two banded stacks, long shed | built v2 (fal components blastFurnace, skipGallery, bandedStack x2, shedSegment x2, pourBay + bkit); building view `#steel_mill`; sheets `images/buildings/steel_mill-v1.jpg` (kit only), `-v2.jpg` |

The other 14 colony buildings (`briefs/buildings.md`) are listed in the Buildings menu as planned; recipe
`Scene3D/tools/blender/buildings/README-colony.md`.

Known open item: the reactor-flank CT-4 / CT-7 stencil reads like a row of small windows at steep
angles. It needs a paint change in `freighter_paint.py` and a rebuild.

## In design

None. The three assets built in v1 keep their briefs and concepts: V-31 `briefs/vehicle.md`,
`images/spread-vehicle-r1.jpg` (A), review sheet `images/build-vehicle-v1.jpg`; shipyard `briefs/shipyard.md`,
`images/shipyard-r3-A-fixed.jpg`, review sheet `images/build-shipyard-v1.jpg`; spaceport `briefs/spaceport.md`,
`images/spaceport-r6.jpg`, review sheet `images/build-spaceport-v1.jpg`.
