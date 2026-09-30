# Assets built in this style

All of them are in `Scene3D/`. Each has its module in `src/ships/<id>.js`, its GLB in
`assets/ships/<id>.glb`, its hull script and spec in `tools/blender/hulls/<id>*.py` and
`tools/blender/specs/<id>-v3.json`, and its build notes in `tools/blender/hulls/README-<id>.md`.

| Asset | Length | Crew | Signature | Status |
|---|---|---|---|---|
| F-402 Petrel fighter | 71.7 m | about 40 | faceted armoured pod, flank sponsons with twin railguns, five-pane canopy, two ports by the crew door, twin main bells + sponson bells | remodelled, v14 lights (26 lamps) |
| K-214 Warden corvette | 108 m | about 350 | wedge hull, bow torpedo frame, deckhouse + tower, outrigger drive pods | remodelled, v14 lights |
| CT-4 Drover freighter | 134 m | about 80 | crew module, truss keel with 20-ft containers, reactor block, radiators | remodelled, v14 lights |
| CT-7 troop transport | 129 m | 750 troops | same spine, four habitat cylinders in the girder | remodelled, v14 lights |
| DD-12 Bastion destroyer | 203 m | about 2,000 | spinal railgun through a blunt octagonal bow, 12 turret-M, broadside sponsons, VLS, armoured command block, lattice mast | remodelled (v9 polish), v14 lights |
| CV-50 Keystone carrier | 900 m | about 20,000 | open-flank through-deck hangar (670 x 155.8 x 84.4 m) parking every legal load, 40-deck island, bow mouth | remodelled, v14 lights |

Known open item: the reactor-flank CT-4 / CT-7 stencil reads like a row of small windows at steep
angles. It needs a paint change in `freighter_paint.py` and a rebuild.
