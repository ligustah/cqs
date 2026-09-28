# Carrier CV-50 (Keystone class): hard-surface remodel

The corvette's method (README.md) with the destroyer's and the freighter's lessons, at 900 m.

```sh
PY=<python with bpy 5.x, scipy, pillow>
cd Scene3D
$PY tools/blender/hulls/measure.py <old carrier.glb> <work>/measure --length 900     # the v5 GLB is the blueprint
PY=$PY python3 tools/blender/hulls/carrier_build.py <work>/m     # model, bake, paint @8192, spec, assemble, module
node tools/blender/hulls/carrier_squeeze.mjs <work>/m/carrier-v3.glb <work>/m/carrier.glb --base-q 82
# install: carrier.glb -> assets/ships/carrier.glb, <work>/m/carrier.js -> src/ships/carrier.js (temp file + rename)
```

## Files

| File | Role |
| --- | --- |
| `carrier_dims.py` | Every dimension (pure Python): stations of the stern block, the five frame rings, the six bays, the bow section; hangar decks / ceilings / walls (the v5 module's deck heights kept exactly); hull half-profiles with 45-degree chamfers; keel wedge; sponsons; bells; island tiers; turrets. |
| `carrier.py` | The hull: stern block (back recess, port rows, grilles, bell housings, sponsons, belts), the box (upper and lower slab cut by one hangar + flank-bay outline; radiator fields above and grilles below every bay), five frame rings, bow section (mouth, lip, belts, probes, wall walkways), keel wedge and pod, ceiling girders and gantries, the stepped island (plinth, six tiers of 1 m pane bands on the 3 m deck pitch, hammerhead bridge, parapets, roof machinery, mast), deck barbettes, armour plates and conduits. `MODULE` for module.py. |
| `carrier_uv.py` | destroyer_uv's per-volume projection before the bevel, plus 48 m tiling of giant flat faces and density classes (island x1.35, hangar deck x0.85, walls x0.7, ceiling / belly x0.55). |
| `carrier_paint.py` | destroyer_paint's chunked painter at 8192 with the carrier's plating scale, the CV-50 stencil glyphs (15 m letters on a dark ID field), orange bands, hazard frames, lane markings. |
| `carrier_spec.py` -> `../specs/carrier-v3.json` | Kit placements: six bell-XL at the measured radii, turret-L x2.2 (spine and sponsons), turret-M x1.4, PDC, VLS, airlocks, clamps, doors, ladders, rails, RCS, nav lights, floods, antennas, domes, sensor arrays. |
| `carrier_module.py` | Finishes module.py's draft: running lights, lit ports on real glass, gallery / bow-wall ports, mouth rim, ceiling strips, ring floodlights, deck zones, flank openings, liveryKeep and the light gates, all RE-MEASURED by ray casts on the assembled GLB. |
| `carrier_build.py` | The chain (build.sh with the carrier's texture sizes). |
| `carrier_squeeze.mjs` | Budget pass: base colour WebP q82 (8192 kept), hull ORM to 2048, kit textures to at most 1024. 12.7 -> 9.8 MB. |

## Lessons

- The hangar is the constraint: every deck height, the bay openings, the ring ceilings and the bow
  section's walls come from `carrier_dims`, and the module re-measures them on the final GLB (and
  asserts the measured decks agree with the design heights to the meshopt quantisation, ~0.03 m).
- 1.6 km^2 of surface: at 60 % UV fill that is only ~5 px/m at 8192. The painted plating is sized
  for that (11 m frames, 6 m bands); the runtime PATINA (6 m tile) and the worn finish carry the
  fine plating. Tiling the 537 x 242 m deck and ceiling into 48 m UV groups took the fill from
  0.15 to 0.6.
- Big open volumes (walls of fins, mullions, piers) are open 3-face meshes: ~40k triangles saved.
- In the dark livery, neutral paint maps by luminance only: white stencil letters on light paint
  came out at 1.3x contrast (invisible). The letters stand on a dark ID field.
- The GLB budget is the textures: the assembler's q88 base colour alone was 4.9 MB.
- Main guns: turret-L x2.6 (41 m base, 63 m twin barrels, the destroyer's turret-M is x1.15); at x2.2
  they read small against the 200 m deck next to the old v5 guns.

## Result

| | |
| --- | --- |
| envelope (B x H x L) | 406.04 x 319.33 x 900.00 m (v5: 405.5 x 319.3 x 900) |
| triangles (hull / total) | 174.9k / 314.9k, 17 draws |
| GLB | 10.4 MB (base colour 8192, ORM 2048, hull normal 4096) |
| texel density | ~5 px/m average at 8192 (island x1.35, hangar ceiling / belly x0.55) |
