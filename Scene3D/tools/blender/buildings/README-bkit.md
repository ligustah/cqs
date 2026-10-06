# bkit: the shared colony building kit

`bkit.py` is the one component library every colony building script (`<id>.py`) composes. It merges the earlier
building kits: the yard kit's bake pipeline, materials and helpers (`yard_kit.py`, through `lib.Part`), the spaceport
kit's lattice truss and palette (`spaceport_kit.py`), and the fleet kits' human-scale rulers (doors, floodlights,
containers) and the yard kit's vehicles and figures, which it places rather than re-models. Fal-made components
(`assets/parts-colony/`, `component.py`) are placed through it as well. The recipe for a building is
`README-colony.md`.

## Frame and conventions

- Building frame: metres, +Y up, the plinth top at y = 0, +Z the front, +X the building's left. The concepts' camera
  looks from the front-left (azimuth 30-55, 20-30 degrees down), so the +Z and +X faces carry most of the detail.
- `B = bkit.Build(id)`: the batched builder. Primitives with the same (material, bevel) merge into one bmesh as they
  are added; `B.part()` hands one object per batch to `lib.Part` for bevel, weighted normals and the join. A pilot
  building has about 45 batches and 50-70k triangles, and models in about 1 s.
- `B.at(at=, rot=)` / `B.at(M=)` is the transform stack. Lights and placements are recorded in the building frame,
  so call `facade()` and `block()` outside rotated contexts, or add the transform yourself.
- `B.R` (the `Rec`) collects everything that is not baked: lights (`pin`, `beacon`, `obstruction`, `slit`,
  `door_lamp`, `window`, `glowbox`, `flood`) and kit placements (`place`, `door`). `colony_build.py` writes the
  lights into the module's GENERATED block and the placements into `specs/<id>-v1.json`.
- Bake: `lib.bake` (Cycles, CPU): a weathered base colour (panel-to-panel tone in 3 x 1.8 x 3 m cells, AO grime in
  corners only, vertical run-off streaks, light edge wear) and an ORM map. `bkit` retunes `lib.BAKE` for building
  scale on import (AO distance 1.2 m, grime full below AO 0.45, gone by 0.88, strength 0.6). The ship-kit default
  greyed whole walls framed by proud gunmetal (depot r1).

## Materials (`BKIT_MATS`, linear base colour, added to `lib.MATS`)

| Name | Use |
|---|---|
| `panel`, `panel2` | off-white cladding (light concept paint, correction 27) and its darker variant |
| `frame`, `frame2` | dark gunmetal frames, posts, bands, legs; housings |
| `frameL` | light grey trim (linear 0.25) for plain-panel walls: `facade(frame='frameL', base_mat='frame2')` keeps a dark lower course (v3: silicon foundry, refinery control block, radio telescope base) |
| `stone` | pale civic stone, a touch warm (v3: the library's parametric stepped wings) |
| `seam` | panel seams, slab joints |
| `concrete`, `concrete2`, `kerb` | plinth top, sides and footings, the light kerb band |
| `roof` | dark roof membrane (gable roofs default to `panel2`: the concepts' roofs are light) |
| `pipe`, `pipeDark`, `grate` | light pipe steel, valve bodies, grating |
| `cobalt`, `violet`, `amber` (yard kit) | the small accent bands, hazard paint |
| `refractory`, `soot`, `interior` | hot zones, burnt lips, dark interiors behind open bays |
| `glassW` | window glass (lit ones get a runtime glow box) |
| `foliage`, `soil`, `bark` | landscape |

## Components

All true size. "Lights" says what each records in `B.R`.

| Function | What | Lights / placements |
|---|---|---|
| `plinth(B, w, d, h=1.4, chamfer=2, kerb=0.5, slab=8, lamp_pitch=18, markings, grates, steps, notch=None)` | chamfered concrete slab (`notch=(nx, nz)`: a notched cross, an nx x nz rectangle cut from each corner, lamps at every outline vertex; v3 infrastructure): light kerb band, dark toe and shadow line, slab joints, painted markings `[(polyline, width, mat)]`, drain grates, access stairs down the edge | amber pins in the kerb face at the corners and every `lamp_pitch` m along the front and left edges |
| `facade(B, o, u, w, h, bay, storey, base, windows, win, doors, rollers, louvres, slots, seams, bands, ...)` | one wall face: off-white panels, gunmetal base band, storey bands, pilasters per bay, parapet cap, seams, recessed windows (dark glass, proud surround and sill), tall glazed slots, louvre panels, roller doors (ribbed shutter in a portal frame), crew-door canopies | ~55 % of windows lit (`window`), amber jamb slits on roller doors, kit `door` + 0.6 x 0.14 m door lamp per crew door |
| `block(B, (x, y0, z), (w, h, d), sides={'+z': facade kwargs, ...}, roof={...}, post=0.6, chamfer)` | clad box building: core, four facades (`skip_face` to leave one open), corner posts, roof | amber pins at the top corners |
| `roof_deck(B, c, (w, d), parapet, units=[(kind, x, z, kwargs)])` + `hvac`, `vent_box`, `fan`, `antenna`, `solar`, `roof_tank`, `roof_box` | roof membrane, parapet, roof units | - |
| `gable_roof(B, x0, x1, z0, z1, y, rise, ridge='z'/'x')` | shallow gable section with ridge cap, rafters at the gable ends, standing-seam ribs, ridge skylights | - |
| `pipe(B, pts, r, flanges, rings, supports, support_pitch)` | filleted pipe run, flanges, amber ID rings at the first and last flange, T supports with footings on horizontal legs | - |
| `valve`, `pipe_rack`, `cable_tray` | gate valve with handwheel; portal pipe rack with pipes; cable tray | - |
| `vtank(B, (x, z), r, h, top='dome'/'cone'/'flat', bands, ladder_side, platforms, skirt, nozzles)` | vertical vessel / column | - |
| `sphere_tank(B, (x, z), r, yc, legs=8, band='cobalt', ladder_angle)` | Horton sphere: plate courses, cobalt equator band, splayed tapered legs with shoulder gussets, tie ring and diagonals, footings, top platform with valve housing and railing, meridian ladder | pins at the feet and the top |
| `htank(B, (x, z), r, L, axis, saddles, band)` | capsule tank on concrete saddles | - |
| `stack(B, (x, z), r0, h, r1, bands, platforms, base_h, base_r, ladder_side)` | chimney: flared base, dark / light bands, platform rings, sooted lip | a pin under each platform, a red 0.4 m obstruction light on top |
| `railing`, `catwalk`, `platform_ring`, `stair`, `ladder` | 1.1 m rails (posts 1.5 m), grating walks, ring platforms, 0.18 / 0.28 m stairs, 0.62 m caged ladders (rungs 0.3 m) | - |
| `truss(B, p0, p1, w)`, `lattice_tower(B, c, w, h, taper)` | square lattice between two points (spaceport kit); four-post tower | - |
| `glazing(B, o, u, w, h, mull)` | curtain wall with mullions in a heavy frame | warm interior glow |
| `glow_ring(B, (x, z), r, y)` | - | a band of hot glow boxes round a vessel (tuyere band) |
| `tree`, `planter` | low-poly trees, planters with shrubs | - |
| `crate`, `cabinet`, `bollards`, `lamp_post`, `hazard_band`, `stencil` | dressing; fleet stencil numbers | lamp posts: a pin at the head |
| `truck`, `forklift`, `worker` | yard-kit parts (`yard:truck`, ...), `heading` in degrees (0 = front +Z) | placements |
| `container`, `flood_on_wall` | fleet-kit ISO container; kit floodlight on a bracket | placement; flood: lit lens + one spot light |
| `component(B, name, p, heading)` | a fal-made colony component (`colony:<name>`, `assets/parts-colony/`) | placement |

Placement note: the yard kit and colony components mount +Y, and assemble.py lays the part's +X along `along`; the
kit helpers set `along` from `heading`. Passing only `up` turned the first truck 90 degrees.

## Runtime side

`src/buildings/colony.js` (the factory) turns a module's generated `DATA.lights` into the fleet light language
(pins 0.3 m, beacons, door lamps 0.6 x 0.14 m, jamb slits, window glow boxes, interior glow, flood lenses and spot
lights, red obstruction lights in `lights[]`), applies `livery: null`, the PATINA `hull` detail at 6 m and the
`building` finish preset (`finish.js`), and the dusk studio with a front-left key (`sunaz` / `sunel`) and the slate
backdrop. `glbship.js` fixtures accept `rotY` for glow boxes on round vessels.

## Tests

- `colony_build.py <id> <work> --stage hull --tex 1024 --samples 2`: about 40 s, prints triangles and bbox.
- Every function was smoke-tested in one scene (`catwalk`, `cable_tray`, `htank`, `vtank` with flat head, skirt,
  ladder, platform and nozzle, `glazing`, `planter`, roof units, `hazard_band`, `stencil`, `container`, `gable_roof`,
  tapered `lattice_tower`, `truss`).
