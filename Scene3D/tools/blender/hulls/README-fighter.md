# Fighter F-402 (Petrel class): hard-surface remodel

The second ship through the method in `README.md` (after the corvette). The fal / Tripo H3.1 hull
(`assets/ships/raw/fighter.glb`, the v5 true-size re-detail) is only the blueprint; the installed
hull is parametric geometry from `fighter.py`.

```sh
PY=<python with bpy 5.x, scipy, pillow>
cd Scene3D
$PY tools/blender/hulls/measure.py assets/ships/raw/fighter.glb <work>/measure --rotate 0,-90,0 --length 71.712 --res 0.05 --stations 1
PY=$PY tools/blender/hulls/build.sh fighter <work>/m4        # model + bake (~9 min on 4 CPUs), paint, spec, assemble, module
$PY tools/blender/hulls/compare.py <work>/m4/fighter-hull.blend <work>/measure <work>/m4/cmp --views port,top,stern,bow
```

## Files

| File | Role |
| --- | --- |
| `fighter_dims.py` | Pure-Python dimension tables: hull stations (top, top-flat half-width, flank, flank top / bottom, belly-flat half-width, belly) every few metres, bridge block, sponson, bells, doors, glazing recesses. Shared by the model and the spec. |
| `fighter.py` | The volumes, recess cutters, the density-aware unwrap, the build and `MODULE` (module.py's fixed fields, light roles, surfaces). |
| `fighter_paint.py` | The paint scheme over `paint.py` (plating frames, bands, hazard frames, cobalt IDs, the F-402 stencil). Adds the F and 0 glyphs to the fleet stencil and prefilters the stencil to the texel size (crisp, anti-aliased edges). |
| `fighter_spec.py` | Writes `../specs/fighter-v3.json`: kit bells, doors, floodlights, ports, bridge panes, nav lights, antennas, domes. Plain `python3`. |

## Measured layout (ship frame, metres)

- Envelope of the blueprint at the module length 71.712: 46.92 x 20.96 x 71.71. The remodel
  assembles to 46.90 x 20.84 x 71.76 (bow lip z +35.856, bell exits z -35.856 plus the kit lip;
  beam = sponson equipment boxes x +-23.45; height = dorsal whip y +10.47 and belly plates y -10.37).
- Octagonal pod: flat top, upper chamfer x = 13 - 0.75 (y - 0.2), vertical flank x 13.0 from
  y -6.4 to 0.2, lower chamfer to the flat belly (y -10.07, half-width 10.65). Full size from the
  stern face (z -26) to z 4, tapering in plan (flank 13.0 -> 6.75, a 0.7 m step at z 15) and
  height to the framed bow face. Raised dorsal deck y 6.84 from z -18.5 to -3; aft deck y 5.28.
- Spine y 6.98 (six oval hatches) runs forward into the bridge block (walls x 3.85 -> 3.3), roof
  raked from z 11.3, glazed front face z 15.1-17.0 (recess 0.32 m, one row of 5 kit panes at the
  fleet size x1.0; the side bands are unglazed dark visor slots). Two fleet-size ports (kit port
  x1.0) each side just ahead of the forward crew door (v14 scale pass: the v5 rows of 36 half-size
  ports and the 24-pane bridge grid made the fighter read like a much bigger crewed ship).
- Sponsons: chamfered octagon x 16.95-23.15, y -6.15..-0.55, z -13.7..0.2, nose to z 1.9; pylon
  hexagon lofts from z -13.5..2.5 at the flank to z -11.4..0.6 at the sponson. Twin railgun:
  mantlet z 1.6-5.4, sleeve, two barrels r 0.42 (y +-0.475 about -3.35) to z 14.6, slotted muzzle
  block to z 17.86.
- Drive: kit bell-L x1.0143 (r 3.55) at (+-5.9, 0, -35.856) on hubs in r 4.3 stern sockets, eight
  struts from the back flange to a clamp band on the neck; kit bell-S x0.9786 (r 1.37) at
  (+-20.05, -3.3, -16.64) on the sponson tails.
- Blueprint fit (compare.py, hull only, blueprint includes the bells): IoU port 0.91, top 0.90,
  stern / bow 0.94; sections within ~0.3 m except the blueprint's melted strakes.

## Lessons (fighter)

- UV density: grab rails, louvre fins, struts, lenses and RCS nozzles are many small islands. The
  unwrap packs them at 0.4 x the hull density (face attribute `small`), so the plated faces get
  ~32 px/m at 4096 (the corvette: ~20).
- Snapping: a part's snap ray starts 8 m out along its normal, so the forward crew door's ray began
  inside the sponson railgun. Doors are placed on the bay floor with `snap: false`.
- A closed end cap on a band volume (the stern collar) covers a recessed plate behind it: build
  bands as annuli (outer and inner rings, no caps).
- The kit RCS block reads as a dark blob; the fighter's RCS quads are modelled on the hull in
  hull paint (housing, four side nozzles, one outboard), and the stern cluster is four shallow
  raised thruster discs rather than deep cups (AO turned deep cups black).
- The hull number is a pale, saturated stencil colour: livery.js treats it as a marking and keeps
  it as a light low-visibility grey, crisp against the dark hull (a white stencil would be mapped
  almost to the hull grey).
