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
| SD-4 silicon depot (colony) | slab 74 x 48 m, 38 m | depot crew | 30 m monolithic vault block: four tall bays (three sealed vault doors, one open rack bay), violet strips, +X annex, entrance porch, roof crown and head tower | built v2 (fal components vaultBay x3, rackBay, entrancePorch + bkit); building view `#silicon_depot`; sheet `images/buildings/silicon_depot-v2.jpg` |
| MB-2 military base (colony) | slab 118 x 94 m, 22 m | garrison | walled compound: buttressed blast walls, fortified gate, four corner towers, two armoured hangars, stepped command bunker, a V-31 on the yard | built v2 (fal components wallSegment x15, gateHouse, guardTower x4, armouredHangar x2, commandBunker + bkit; the fleet's V-31 instanced at runtime); building view `#military_base`; sheet `images/buildings/military_base-v2.jpg` |
| RT-7 radio telescope (colony) | slab 48 x 58 m, 54 m | science crew | 42 m dish on a yoke and azimuth drum over a chamfered armoured base, stair tower, cryo plant | built v2 (fal component dishMount at 1.3, catalogue filterBank + bkit); building view `#radio_telescope`; sheet `images/buildings/radio_telescope-v2.jpg` |
| TC-2 trade center (colony) | slab 112 x 54 m, 52 m | exchange staff | two 50 m office towers joined by a glazed sky bridge, covered market arcade on the plaza, dark freight hall with docks and a truck | built v2 (fal components officeTower x2, skyBridge, marketArcade, loadingHall + bkit); building view `#trade_center`; sheet `images/buildings/trade_center-v2.jpg` |
| IN-4 infrastructure (colony) | slab 104 x 104 m, 30 m | admin crew | cross-plan two-storey wings round a domed command hub with antennas, courtyard garden and portico, water tower, utility skids | built v2 (fal components hubDrum, adminWing x4, waterTower, vesselSkid x4 + bkit); building view `#infrastructure`; sheet `images/buildings/infrastructure-v2.jpg` |
| HB-9 residence (colony) | slab 100 x 72 m, 32 m | residents | three curved 10-storey balcony blocks wrapped round a courtyard garden, two-storey podium on the street | built v2 (fal components curvedTerrace x3, podiumSegment x2 + bkit); building view `#residence`; sheet `images/buildings/residence-v2.jpg` |
| UN-3 university (colony) | slab 112 x 66 m, 30 m | faculty, students | three faceted wings with observatory domes and a radome round a glazed faceted atrium, front garden with pools | built v2 (fal components facetedWing x3 stretched, atriumHall, obsDome x2 + bkit); building view `#university`; sheet `images/buildings/university-v2.jpg` |
| LB-1 library (colony) | slab 112 x 70 m, 50 m | archivists | stepped battered archive wings either side of a 46 m portal tower with a gold-lit glazed slot, grand stair, lit pylons | built v2 (fal components portalTower, steppedWing x2, monumentPylon x6 + bkit); building view `#library`; sheet `images/buildings/library-v2.jpg` |
| TX-1 transmitter (orbital megaproject) | ring ~360 m (400 m with wings), 54 m | station crew | hexagonal ring: six thruster-clustered corner nodes, two rows of girder segments with a glowing blue inner edge, faint blue field, five solar wings, docking hub | built v2 (fal components ringModule x6, ringSegment x12, solarWing x5, dockingHub + bkit lights); space backdrop; building view `#transmitter`; sheet `images/buildings/transmitter-v2.jpg` |

The other 14 colony buildings (`briefs/buildings.md`) are listed in the Buildings menu as planned; recipe
`Scene3D/tools/blender/buildings/README-colony.md`.

Known open item: the reactor-flank CT-4 / CT-7 stencil reads like a row of small windows at steep
angles. It needs a paint change in `freighter_paint.py` and a rebuild.

Colony buildings v2, production / storage batch (2026-10-06): refinery, processing_plant, oil_tanks, silicon_foundry,
steel_depot (`assets/buildings/<id>.glb`, `src/buildings/<id>.js`, scripts `tools/blender/buildings/<id>.py`), composed
from twelve new fal components (distColumn, htankSkid, processVessel, bandedLowTank, plantBlock, bottleSkid, floatTank,
roofMonitor, crystalReactor, overheadCrane, beamStack, portalColumn) plus the pilots' plantHouse, manifoldSkid and
filterBank; review sheets `images/buildings/<id>-v2.jpg`; phone tier 106-127 MB heap + GPU.

## In design

None. The three assets built in v1 keep their briefs and concepts: V-31 `briefs/vehicle.md`,
`images/spread-vehicle-r1.jpg` (A), review sheet `images/build-vehicle-v1.jpg`; shipyard `briefs/shipyard.md`,
`images/shipyard-r3-A-fixed.jpg`, review sheet `images/build-shipyard-v1.jpg`; spaceport `briefs/spaceport.md`,
`images/spaceport-r6.jpg`, review sheet `images/build-spaceport-v1.jpg`.
