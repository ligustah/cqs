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
| `destroyer.py` | Parametric hull: engine block, mid hull, bow block, tower, railgun; `MODULE` for module.py. |
| `destroyer_uv.py` | Per-volume UV projection **before** the bevel, one metre per UV unit, then one pack. |
| `destroyer_paint.py` | paint.py's layers evaluated in row chunks at 8192 on upsampled 4096 bakes; copper zone, varied access panels, a stencil with `D`, DD-12's scheme. |
| `destroyer_spec.py` → `../specs/destroyer-v3.json` | Kit placements (bells, turrets, PDCs, VLS, doors, ladders, rails, RCS, nav lights, floods, antennas, dome). |
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
- Bridge tower: eight glazed deck rows (0.9 m bands, 0.35 m recess, mullions every 1.12 m as
  unbevelled boxes), ledges every second deck, two balconies with rails.

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
