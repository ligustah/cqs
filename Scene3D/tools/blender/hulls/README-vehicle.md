# Vehicle V-31 (wheeled 4x4 ground unit): hard-surface remodel

The first ground unit through the method in `README.md`. Concept A (correction 19,
`style-library/styles/cqs-fleet/images/spread-vehicle-r1-A.jpg`) went through one 4K turnaround and a Tripo H3.1
multiview blueprint (`assets/ships/raw/vehicle.glb`, gitignored; job ids in `pipeline/fal-pipeline.json`
`v22_vehicle_build`). The installed model is parametric geometry from `vehicle.py`, built to the brief's TRUE SIZE
(`briefs/vehicle.md`), not to a hangar-slot volume.

```sh
PY=<python with bpy 5.x, scipy, pillow>
cd Scene3D
$PY tools/blender/kit.py wheel suspension rws roofHatch vehicleDoor markerLamp foilBox   # the ground parts (once)
$PY tools/blender/hulls/measure.py assets/ships/raw/vehicle.glb <work>/measure --rotate 0,-90,0 --length 6.5 --res 0.01 --stations 0.5
$PY tools/blender/hulls/vehicle.py <work>/m --stage model --bake --tex 2048 --ao 1024     # ~3 min on 4 CPUs
$PY tools/blender/hulls/vehicle.py <work>/m --stage paint --tex 2048                      # ~1 min
python3 tools/blender/hulls/vehicle_spec.py
$PY tools/blender/assemble.py tools/blender/specs/vehicle-v3.json <work>/m/vehicle-v3.glb --hull <work>/m/vehicle-hull.glb --tex 2048 --threads 4
cp <work>/m/vehicle-v3.glb assets/ships/vehicle.glb
node tools/lite-glb.mjs assets/ships/vehicle.glb dist/assets/ships/vehicle.glb.lite.glb --tex 1024   # phone tier
```

(`build.sh vehicle <work>` also works, but it assembles with `--tex 4096` and runs `module.py`, which has no bells or
nav-light housings to derive here: `src/ships/vehicle.js` is written by hand from the numbers below.)

## Files

| File | Role |
| --- | --- |
| `vehicle_dims.py` | Pure-Python dimension tables: body stations (roof, roof edge, flank, belly band, lower chamfer, belly), axles, wheel, arch outline, flares, doors, glazing, vent, collar, end frame, roof fittings, lamps, markings. Ground at y = 0. Shared by the model, the paint and the spec. |
| `vehicle.py` | Volumes (body loft, nose collar, tail end frame, fender flares, skirts and steps, roof appliqué, grab rails), EXACT boolean recesses (wheelhouses, windscreen and side panes, tail vents, nose panel), unwrap (fine parts at 0.4x), bake. |
| `vehicle_paint.py` | Paint over `paint.py`: vehicle-sized plating, amber corner hatching, one amber band per flank, cobalt square, V-31. Adds the V and 3 glyphs to the fleet stencil (via `fighter_paint`'s prefiltered stencil). |
| `vehicle_spec.py` | Writes `../specs/vehicle-v3.json`: 4 wheels, 4 suspension corners, 5 doors, 2 roof hatches, the RWS, the roof vent, the foil box, 7 marker lamps. Plain `python3`. |
| `../parts_ground.py` | NEW kit family (procedural kit, `kit.py`): `wheel`, `suspension`, `rws`, `roofHatch`, `vehicleDoor`, `markerLamp`, `foilBox`, at true size for every later ground unit. |

## Measured layout (vehicle frame = ship frame: metres, front +Z, up +Y, left +X; ground y = 0)

- Blueprint at length 6.5: 2.99 x 3.31 x 6.5 (tyres out to x +-1.48, roof 2.72, RWS 3.31, axles z +1.6 / -1.9,
  wheels ~1.2 m, belly 0.64, body half-width 1.13, roof half-width 0.94). The turnaround drew the vehicle taller than
  the brief (roof 2.77 at length 6.5), so heights were scaled to the brief's 2.5 m roof and widths so the tyres end
  at the brief's 2.6 m.
- Body: chamfered octagon, roof 2.5 (half-width 0.84), upper chamfer to the flank at 2.22, vertical flank x 1.10
  down to 0.78 (gunmetal belly band 0.78-0.98 and the lower chamfer), belly 0.55; unbroken roof from the tail
  (z -3.25) to the cab brow at z 1.40, windscreen raked to the bonnet at z 1.95 (y 2.0), bonnet to the nose face at
  z 3.25 (top 1.70, half-width 0.86). Gunmetal octagonal collar round the nose (1.92 x 0.86 m, z 3.08-3.34), end
  frame round the tail.
- Running gear: kit wheel 1.15 x 0.42 m at axles z +1.80 / -2.00 (wheelbase 3.8 m; the blueprint's 3.5 was opened so
  two vehicle doors and the band fit between the arches), tyre outer face x +-1.315; wheelhouse wall x 0.84 with the
  kit suspension corner (coil-over top 0.62 m above the axle, visible in the arch). Faceted arches to y 1.45, flares
  over the arch tops.
- Doors (kit vehicleDoor 0.9 x 1.3 m leaf, 1.0 x 1.4 m frame): cab door z +0.53 and rear-flank door z -0.75 on each
  flank, tail door. Roof: kit roofHatch 0.8 m at z +0.75 and -0.15 on the centreline, kit rws at z -1.22 (gun
  forward, top 2.99 m), kit vent (engine-deck grille) at z -2.42, kit foilBox at (0.52, -1.72). Windscreen: two
  0.72 x 0.46 m armoured panes; one 0.56 x 0.36 m side pane per cab flank.
- Assembled: 40,387 tris (hull 4,610, wheels 19,276), 1.84 MB, envelope 2.63 x 2.99 x 6.95 m (body 6.5 m; the collar
  lamps and the tow pintle add 0.45 m), bbox centre [0, 1.494, -0.005]. `dropped` empty.

## Lessons (vehicle)

- The brief's door rule decides the side layout: a 2.5 m vehicle has only ~1.45 m of vertical flank, so 0.9 x 1.3 m
  doors cannot sit over the wheel arches as the concept drew them (its doors were small). Both flank doors go between
  the arches, and the axles move apart to make room; markings take the remaining fields (band between the doors,
  V-31 over the rear arch, cobalt over the front arch).
- assemble's `mirrorX` mirrors positions and normals, not handedness: kit doors hinge forward on the port flank and
  aft on the starboard flank. Harmless here; author a starboard placement with its own `up` if a later unit needs
  matching hinges.
- 0.2 m round lightscape pins on the nose read as a pair of round headlamps (which the brief excludes). Covered lamps
  are short slits at the kit lens (0.16 x 0.05 m), dim.
- A dark stencil (the concept's) vanishes on the dark operational grey; the fighter's pale saturated stencil colour
  reads as light low-visibility grey (the fleet rule).
- Studio stills (`mode=ship`) frame the vehicle too tight at dist 1 (the RWS and nose crop); use dist 1.5.

## Look v2: matte, used ground unit (correction 34)

"The vehicle looks way too smooth and clean. Too shiny." Same geometry, spec and envelope; rebuilt with the commands
above (paint stage, then assemble, about 2.5 min; workdir of the accepted build: scratchpad `v23/m5`, maps.npz and
the .blend copied from the v1 build).
- `vehicle_paint.py` `weather()` runs after `paint.py` (`spec()['weather']`): sun-faded roof, recess grime, run-off
  streaks from the roof edge, side vents and side panes, edge chips (curvature edge dilated ~4 cm, red-oxide primer
  round bare steel), stone chips low and on the nose, dried mud in the wheelhouses, round the arch rims (more behind
  each wheel) and on the belly, scuffed markings (decal wear raised; V-31 kept legible at 0.3). True-colour texels get
  base-colour alpha < 1 (`keep.png` in the workdir); the alpha survives the contact bake, the glTF export (alphaMode
  stays OPAQUE), optimize-glb and the lite / mini copies. It also restores the glass zone's blue-dark colour, which
  paint.py's warm crease grime had shifted so far that the livery never detected the windscreen as glass.
- Runtime (`src/ships/vehicle.js`): `finish: 'ground'`, `detail: { set: 'groundPaint', tile: 1.5, normalStrength: 1.4,
  roughAmount: 0.8, cavity: 0, skipGlass: true }`, livery `matte: 0.75, keep: 1, glassRough: 0.8`. Dust and mud graded
  up from `anchors.ground` come from the finish, so they run over the kit doors, wheels and suspension too.
- Evidence: `style-library/styles/cqs-fleet/images/build-vehicle-v2.jpg`. GLB 2.18 MB (was 1.83; the RGBA base
  colour), 40.4k tris, length 6.950 m, `dropped` empty.

## Integration

Not applied (shared files belong to the integrating agent). Exact diffs:

**`src/lib/scale.js`** (CLASSES): a real-size class. `size: null` keeps `normalizeShip` at scale 1; `carrierLoads`
only iterates the five space classes, so the hangar check is unaffected.

```diff
   carrier:   { size: null, capacity: 50, label: 'Carrier', gameId: 'CARRIER', role: 'Warp-capable fleet carrier' },
+  // ground unit at REAL-WORLD size (not a hangar-slot class): size null keeps normalizeShip at scale 1; ground = the
+  // game's ground-transport size (UnitEnum VEHICLE: 3; a CT-7 carries 750)
+  vehicle:   { size: null, ground: 3, label: 'Vehicle', gameId: 'VEHICLE', role: 'Fast armoured all-terrain ground unit' },
 };
```

**`src/ships/index.js`** (ORDER):

```diff
-export const ORDER = ['fighter', 'corvette', 'freighter', 'destroyer', 'carrier'];
+export const ORDER = ['fighter', 'corvette', 'freighter', 'destroyer', 'carrier', 'vehicle'];
```

**`src/main.js`** (lineup callout; without it the vehicle row reads "carries undefined slots"):

```diff
-      const slots = spec.size ? `${spec.size} slot${spec.size > 1 ? 's' : ''}` : `carries ${spec.capacity} slots`;
+      const slots = spec.size ? `${spec.size} slot${spec.size > 1 ? 's' : ''}` : spec.capacity ? `carries ${spec.capacity} slots` : `ground unit, true size`;
```

**`src/fleet.js`**: no change. The fleet is in orbit; the vehicle is a ground unit and is not placed there (the CT-7
carries them internally). `ORDER` growing only adds one small GLB to the fleet view's preload.

**Checks after integrating** (tested in a scratch copy of the scene with exactly these three diffs):
- `node tools/shoot.mjs "mode=ship&ship=vehicle&az=35&el=18&dist=1.5&t=20" /ABS/v.png` renders the vehicle (dark
  livery, 7 lamps, no load errors). glbship warns once that the two red tail lamps are not 0.25-0.45 m nav lights
  (R10): they are 0.2 m vehicle tail lamps, deliberately; move them to `lightscape.patterns` (`points`, colour
  'red' is not a PIN colour, so use `lights` as now or add a red pin colour) if the warning must go.
- `node tools/scale-check.mjs`: the vehicle row prints with `size -`, scale 1, and the hangar loads are unchanged.
  The script's table header and the README scale table are regenerated by it.
- Lineup (`#lineup`, `?lineup=small#lineup`): the vehicle gets its own row beside the 1.8 m figure.
- Optional: the phone tier copy `dist/assets/ships/vehicle.glb.lite.glb` is made by `tools/build-artifact.mjs`
  like every ship (a copy made with `tools/lite-glb.mjs --tex 1024` is already there, 1.47 MB).
- Lighting standard / `audit.mjs`: add a vehicle row (7 authored lamps: 2 covered front slits, 2 amber side markers,
  2 red tail lamps, 1 covered convoy lamp; no glass lit) if the audit is run on ground units.
