# Destroyer DD-12 (Bastion class): hard-surface remodel

Same method as the corvette (README.md), with the changes a 200 m hull needs.

```sh
PY=<python with bpy 5.x, scipy, pillow>
cd Scene3D
$PY tools/blender/hulls/measure.py assets/ships/raw/destroyer.glb <work>/measure --rotate 0,-90,0 --length 202.68 --res 0.12
PY=$PY python3 tools/blender/hulls/destroyer_build.py <work>/m      # model, bake, paint @8192, spec, assemble, module
$PY tools/blender/hulls/compare.py <work>/m/destroyer-hull.blend <work>/measure <work>/m/cmp
```

## Files

| File | Role |
| --- | --- |
| `destroyer.py` | Parametric hull: engine block, mid hull, bow block, command block, railgun, barbettes and VLS coamings; `MODULE` for module.py. |
| `destroyer_uv.py` | Per-volume UV projection **before** the bevel, one metre per UV unit, then one pack. |
| `destroyer_paint.py` | paint.py's layers evaluated in row chunks at 8192 on upsampled 4096 bakes; copper zone, varied access panels, a stencil with `D`, DD-12's scheme. |
| `destroyer_spec.py` → `../specs/destroyer-v3.json` | Kit placements (bells, 12 turret-M, 26 VLS pods, 28 PDCs, 4 fal sensor arrays, doors, ladders, rails, RCS, nav lights, floods, antennas, dome). |
| `destroyer_module.py` | Finishes module.py's draft: `CORNER_BELL`, the re-measured `railgunMuzzle` anchor, the muzzle-rim fixtures, `liveryKeep` for the gun gap. |
| `destroyer_build.py` | The chain above (build.sh with the destroyer's texture sizes). |

## Frame and size

The blueprint is measured at the RENDERED size (length 202.68 m = the old module's 204.21 m x its
class correction 0.9925), so the model is built directly at the 840,000 m^3 envelope and the class
correction stays ~1.0 (scale-check: 1.0008, 202.87 x 55.95 x 74.01 m).

## Design notes

- Every taper (engine front, mid-hull front, bow rear and nose) is a **uniform scale** of the
  section about a point on the centre line, so all tapered facets stay planar.
- The spinal railgun is parametric: scaling the kit's railgun-segment to the blueprint's ~6 m bore
  would scale its hatches and walkways x2.3. The gun gap (widened from the blueprint's 9 m to 11 m
  so the barrel reads) shows the bore liner, two rail bars, four clamp rings, copper-wound coil
  packs and conduits, with walkways, 1 x 2 m kit doors, ladders and hand rails at true scale.
- (v7 had an eight-deck bridge tower here; v8 replaced it, see below.)

## Lessons

- **Coincident cutters break the EXACT boolean silently**: a shoulder port row whose cutter edge
  touched a vent-bay cutter returned an EMPTY engine block (0 faces), and every kit part snapped to
  it was dropped. The build now raises if a boolean loses faces.
- **UVs before the bevel.** common.unwrap on the bevelled, joined hull turned every chamfer strip and
  box face into its own island: 17 % fill (7 px/m). Projecting each volume before the bevel lets the
  chamfers ride on their neighbours' islands: 45-60 % fill.
- Big closed "band" slabs leave huge internal caps that the cull cannot remove (their corners lie
  outside the hull): bands are ring solids.
- Unbevelled thin fins (mullions, louvres, slats, coil turns) save ~35k triangles with no visible
  loss.
- Texel density: ~50,900 m^2 of surface at 45 % fill is ~12 px/m at 4096; the base colour is
  painted at 8192 (~24 px/m average, more on the main plating since thin repeated fins, clamps,
  walkways and ledges are unwrapped at 0.3 density) from 4096 bakes upsampled (position and
  normal are linear inside a face); ORM and normal stay 4096.
- Reduced-density islands must stay single-zone: the copper coil turns (0.2 m faces) at 0.3
  density fell between texel centres and sampled the neighbouring light trim collars (white turns).
  Mixed-zone detail (coil packs, bus bars, muzzle coils, spine rails) is unwrapped at full density.
- Edge wear only on painted plating: on bare copper / steel machinery the thin faces read as all
  'edge' and went white.
- Result: 163,581 triangles (hull 76,796), 8.3 MB GLB, blueprint silhouette IoU (hull only, no kit
  parts) port 0.89 / top 0.95 / stern 0.95 / bow 0.95.

## v8 redesign: low command block, visible weaponisation

User feedback on v7: "looks a little bit weird with that massive tower on it and seemingly relatively
little weaponisation". Hull body, bow, gun gap, stern block, DD-12 stencil, drives, livery and detail
settings are unchanged.

- **Command block** (z -59 .. -31, `command_block()`): armoured base deck (23 x 28.4 m, top y -0.4, a
  row of 1 m ports, 1 x 2 m doors aft and on the sides, ladders, a railed roof walk) and a sloped
  two-deck casemate to y 5.6 (10 m above the engine deck) with one narrow armoured glazing slit
  (0.5 m, 0.45 m deep, glass on the back wall, armoured mullions every 1.5 m) round its front.
  Roof: radome drum (kit dome x1.8), four PDCs, a fire-control director with four fal sensorArray
  faces, and a slim tapered pylon + pole + kit whip.
- **Envelope height**: without the tower the top fell ~30 m. The ventral superfiring barbettes
  (bottom -44.2) and the sensor pole + whip (top ~29.5) keep the height at ~73.7 m (-0.5 %), so the
  12-slot class correction stays ~1.002. The high point is a 0.3 m pole and a whip, not a structure.
- **Turrets**: 12 kit turret-M: A (x1.15, low ring) and B (x1.15, 3 m superfiring barbette) on the
  bow block; X / Y the same on the engine block, guns aft; the same four mirrored ventrally
  (A'/B' under the bow block, X'/Y' under the engine block); two x1.0 on ribbed shoulder drums
  rising out of the engine shoulders; two x1.0 on enlarged flank sponsons. The B/X barbette height
  (3 m) clears the A/Y roof (turret-M x1.15: roof 4.44 m, trunnion 2.6 m).
- **VLS**: 26 kit missilePod blocks (208 cells) set flush in armoured coamings (`vls_bay()`, 0.62 m
  walls = the pod height) on the bow deck (2 x 4), the mid-hull forward deck (2 x 3, on the tapered
  deck plane) and the engine deck (2 x 2 x 3), coaming tops framed in hazard stripes.
- **PDC clusters**: bow shoulders and lower chamfers, mid shoulders, engine shoulders fore and at the
  stern corners, lower chamfers, keel, command block roof.
- **Railgun**: finned cooling ridge along the spine crown (unbevelled 0.1 m fins, 0.45 m pitch),
  eight heavy clamp bands round spine and ridge (`SPINE_BANDS`, placed in the bus-bar gaps between
  the capacitor banks), three 1.5 m clamp rings with bolted lugs in the gun gap (steel / dark zones:
  the gap keeps a muted livery), an armoured bare-steel muzzle collar 1.3 m proud of the nose facets
  (6 m deep, replacing the flush lip) and a nose band.
- Ports are 1.0 m (were 0.8 m) on the 3 m deck rows.
- Budget: turret-M decimated to 0.26, missilePod 0.18, pdc 0.25, rails 0.5, sensorArray 0.3.

Lessons (v8)
- Kit placements that snap along -n start 8 m outside: a door facing a barbette landed on the
  barbette. Doors there are placed unsnapped at the measured face.
- A mixed-zone volume (clamp rings: trim + metal bands) must stay at full UV density, or the thin
  bands sample their neighbours (white banding in the gap).
- Training the shoulder turrets 20 deg outboard pushed the barrels past the beam (+4.7 % width).
