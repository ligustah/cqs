# Scale and lighting: making assets read at their true size and look alive

Two pieces of user feedback defined this area:
- "The main thing would be the lighting... all the small lights the concept art shows. Make it look
  alive."
- "On the fighter it kind of looks like windows, which distorts scale perception... The fighter looks
  too big with the small random lights."

Both are right, and a good result satisfies both.

## How viewers infer size

- **Human-scale references:** doors (1 x 2 m), windows (about 1 m), rails (1.1 m), containers (20 ft),
  deck pitch (3-3.5 m). A smaller window implies a bigger structure. Never shrink them.
- **Detail frequency:** many fine, evenly spaced points or rows read as a vast structure (city lights,
  a building's floors). A vertical column of evenly spaced dots reads as "one light per floor" and turns
  an 84 m post into a 7-storey building.
- **Fixture size:** the same lamp must be the same physical size on every asset. On a first pass,
  fixture sizes grew with the hull (0.2 m on a corvette, 0.65 m on a carrier). That makes the big asset
  read small.
- **At range:** pixel floors make every distant light the same 1-3 px blob. Bars stretched to a minimum
  length become 3 x 1.3 px "windows". Geometry glass never blurs away, unlike texture glass, so a
  distant crew block becomes a sparkle field. Fix this in the renderer: fade by true area, cap the
  stretch, thin by on-screen size.

## Fixture standard (summary)

This is a summary. The authoritative catalogue for a style is its lighting standard: for `cqs-fleet`,
`style-library/styles/cqs-fleet/lighting-standard.md`, fixtures F1-F17 and rules R1-R12, including walkway
lights, docking markers, chasers, drive status and hangar lamps, which are not listed here. Copy that file
to a new style and adapt it.


| Fixture | Size | Colour | Use |
|---|---|---|---|
| Recess / corner slit (the concept's signature) | 0.6-1.8 m long x 0.14-0.2 m wide (0.26-0.30 m wide on assets of 200 m and more) | amber | block corners, joints, real recesses; hard-edged, faint warm spill, never a tube |
| Pin lamp | 0.2-0.3 m | amber / warm | block corners, deck edges; never a lone dot on open plating |
| Door lamp | 0.6 x 0.14 m bar | amber | one over each crew door: the human ruler |
| Beacon | 0.26-0.30 m, slow pulse (3-4 s) | amber | 2-4 per asset, clear of antennas (a lamp on a whip tip reads as a lamp post) |
| Nav lights | 0.4 m | red port, green starboard, white stern and strobes | aircraft or ship practice; nothing else goes in the nav path |
| Drive status | 0.2 m pins or short bar | cool blue-white | beside, never through, the white stern light |
| Window glow | real glass only, 0.86-1.0 m | warm, varied per compartment | crew spaces only, lit share by role (warship about 0.45, civil about 0.55) |
| Bridge / cockpit glass | fleet panes | uniform, dim (about 0.6-0.7x the lit cabins as displayed) | bridges run dark; a canopy facing the hero camera needs even less |

Per-class budgets grow with size: fighter about 26 lamps, corvette about 117, civil about 120,
destroyer about 225, carrier about 560 exterior. Small craft (under about 100 m) get **authored lights
only**: no automatic crease pins, no rows. Every light must have a job: a corner, a door, a drive, a
beacon, a window.

## The amber slit look (what "looked much better")

From the concept art: short, hard-edged, saturated amber slits in recesses and at block corners, with
only a faint spill. Too dim and thin, and the ship reads dead. Too hot, and they become neon tubes.
Rules the fleet converged on:
- **Brightness:** keep the peak modest (the tone map turns bright amber cream).
- **Colour:** pre-saturate the slit colour a little (about 1.3x) so it lands on orange after tone
  mapping.
- **Edges:** crisp; a faint halo (about 0.1 of the core); no white hot core.
- **Width:** sized to read at the hero view (about 3 px), not to be physically tiny.
- **Placement:** never on a grille, louvre or radiator (families of parallel creases); never within
  1.5 m of glass (it reads as another window); never grazing a face so that it becomes a 1 px neon seam.

## Windows

- **Only real glass glows:** use a whitelist of kit glass parts. Otherwise, dark stencil paint, sensor
  lenses and gun sights pass the glass test and glow as specks.
- **Compartment cells** vary tint, level and flicker. Set the cell grid and phase so no cell edge
  splits a port (a half-lit port reads as two small windows).
- **Glow:** keep it steady; flicker is rare.
- **Small craft:** at most 1-2 ports near the door, dark or nearly dark. A lit "door plus two windows
  plus porch lamp" reads as a house front.

## Checks to run

The tools are in `Scene3D/tools/lights/`; run them from `Scene3D/`:
- `audit.mjs <asset> [variant]`: budgets, PASS/FAIL (`OV=override.mjs` tests a change without editing);
- `dump.mjs`: pins and bars in a box;
- `raycast.mjs`: snap authored positions onto real faces;
- `cellcut.mjs`: ports split by compartment cells;
- `partbox.mjs`: ship-frame boxes of kit parts;
- `marks.py`: count lit marks on a render.

What to check:

- Audit script per asset: counts by type, sizes, keep and animated counts, distances to nav lights,
  PASS/FAIL against the budget.
- Marks at hero, dist 2.5, dist 5 and in the lineup (a blob counter on renders). The order must hold
  at every range: fighter < corvette < civil < destroyer < carrier.
- Lamp versus glass energy split (render with and without each layer): amber lamps should carry the
  look, not glass.
- 1:1 crops of every authored light, and a thumbnail (about 400 px) of the whole asset.
