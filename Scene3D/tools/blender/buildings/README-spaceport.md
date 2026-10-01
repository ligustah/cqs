# SP-3 orbital spaceport: parametric build (model-forge stages 3-8)

The approved concept is `style-library/styles/cqs-fleet/images/spaceport-r6.jpg` (r5 C, offset half-shells, made
busier; corrections 25, 29-32). No turnaround or blueprint mesh was generated: the form is simple, parametric and
built to the brief's numbers, and every ship in it is an existing model (corrections 26, 32). fal spend: **$0**.

```sh
cd Scene3D
PY=<python with bpy 5.x> tools/blender/buildings/spaceport_build.sh <workdir> [--install]
#   spaceport.py <work>          station geometry          -> <work>/spaceport-hull.glb (+ .json: tris, bbox, mount data)
#   spaceport_spec.py            kit placements            -> tools/blender/specs/spaceport-v1.json
#   ../assemble.py --no-bake     kit parts at true size    -> <work>/spaceport.glb (+ .json report)
#   tools/lite-glb.mjs           phone tier                -> <work>/spaceport.lite.glb
#   --install                    -> assets/buildings/spaceport.glb, spaceport.lite.glb (temp file + rename)
$PY tools/blender/buildings/spaceport_kit.py --export assets/parts-spaceport   # the new kit parts as GLBs
```
The build is deterministic (the installed GLB and a rebuild have the same md5) and takes about 20 s.

## Files

| File | Role |
| --- | --- |
| `spaceport_dims.py` | Every dimension and placement (numpy only): the two shells (octagonal section, apothem, angular span, z span), rims, arches, panel and rib pitches; the carrier offset and cut; the bare frames (the carrier's own `P_END` section and frame stations); blocks, gantries, arms, berths, radiators, tugs; mount frames (`mount_frame`, `block_frame`) and the clamp geometry for each docked CT-4 (`freighter_clamps`, on the CT-4's collar airlock). |
| `spaceport_kit.py` | The polygon accumulator (`Acc`, transform stack, per-face material and linear vertex colour) and the **building kit parts** (below), plus the Blender mesh/material/GLB helpers. `--export <dir>` writes the parts as GLBs with `parts-buildings.json`. |
| `spaceport.py` | The station: shells with plating panels and seam grooves, inner ribs, pale corner bands at the octagon vertices, rims in 60 m segments with dark joints, end arches, work-light strips, rim dressing (pipe runs, plant boxes, tank clusters, cargo pallets), the kit parts, the part-built carrier's bare frames, keel, stringers, first plates, scaffold towers and keel cradles, the SP-3 code. One mesh `hull`. |
| `spaceport_spec.py` -> `../specs/spaceport-v1.json` | Procedural kit at scale 1: 320 ports (runs of five on the lit decks), 10 crew doors, 133 rail segments, 88 ISO containers, 16 floodlights, 5 nav-light housings, antennas and a radome. Not snapped: positions come from the same mount frames. |
| `spaceport_build.sh` | The chain. |
| `src/buildings/spaceport.js` | Runtime module (see Runtime). |

## Frame and layout

Station frame = the asset frame: metres, forward +Z, up +Y, left +X. The open slot faces **+X** (the studio camera at
az 35-45 sees it). Origin on the shells' common axis at the carrier's mid-length; glbship centres the GLB on its bbox
(centre (31.875, 34.22, -1.44)), and the module shifts every authored station-frame position by the same amount
(`CENTRE`, with a warning if the GLB's bbox ever moves).

| Element | Numbers |
| --- | --- |
| Trough (lower half-shell) | octagon apothem 175 m, plate 6 m, from the far wall's top corner (157.5 deg) round the bottom to the near wall's mid-height (0 deg); z -480 .. +520 |
| Hood (upper half-shell, shifted aft) | apothem 196 m, plate 6 m, 40 deg (upper-near chamfer) over the top to 200 deg (laps outside the trough's far wall); z -560 .. +40 |
| Slot | near side, between the trough rim (y 0..4) and the hood's near rim (y ~130), aft of z 40 the whole top is open |
| Rims / arches | pale, chamfered (3 m), 16 x 18 m section, 60 m segments with 1.2 m dark joints; arches 14 m deep |
| Ribs / corner bands | inner ribs every 40 m (3 x 5 m); pale corner bands 12 m wide on every octagon vertex, segmented |
| Carrier | the real CV-50 at (0, 61, 0), its body section centred on the axis; clipped at carrier z 87.42 (aft face of frame F4) |
| Bare frames | heavy rings (P_END outline, 10 m deep, 12 m thick) at the real F3/F2/F1 stations, a stern ring, light ribs every ~23 m, keel spine, stringers (upper ones partial), the first belly / flank / deck plates aft of the cut, scaffold towers, five keel cradles |
| Docked CT-4 | (218, -45, 250), (218, -45, -230) yaw 180, (-218, -40, 165), hood top (0, 233, -400) yaw 180; side berths clamp the collar airlock on a 25.5 m arm, the hood berth holds it belly-down on two 18.4 m arms |
| Envelope (station GLB) | **481.2 x 445.8 x 1131.3 m** (B x H x L); the docked ships stay inside it |

## Size check (measured in the running scene, `?mode=ship&ship=spaceport`)

| | |
| --- | --- |
| station length / carrier length | 1131.3 / 900 = **1.26** (brief and corrections 25, 31: about 1.1-1.3) |
| docked freighter / carrier | 134.12 / 900 = **0.149** (true scale, the real CT-4 GLB) |
| carrier plated length | 362.6 m of 900 (40 %): bow section, bay 1, F5, bay 2, F4; the rest bare frames |
| triangles | station 265.7k (hull 77.6k, kit ports 74k, rails 45k, containers 52k); with the clipped carrier and four CT-4s about 0.95 M |
| GLB | 4.27 MB (lite 4.17 MB: the station has no textures of its own; only the kit parts' are capped) |
| lights | 1494 pins, 512 slits, 48 nav lights in the merged record (station + the carrier's surviving bow lamps + four CT-4s) |

## Look

- **Paint** (correction 27, light buildings with dark accents; the concept's dark plated shells with pale rims):
  colours are authored in linear vertex colour (no UVs, no baked texture): shells 0.034-0.05 with darker seam grooves,
  rims and corner bands 0.43-0.52 warm off-white, habitat blocks 0.56, gunmetal trusses, primer-grey carrier frames,
  amber (0.80, 0.42, 0.06) hazard marks. The module's livery is an identity mapping (gain 1, no tint, marks at full
  saturation), so the paint is kept and only real kit glass (`glassParts: ['port']`) glows as lit cabins.
- **PATINA**: the `hull` set as the tri-planar detail layer (6 m tile, normalStrength 0.6, cavity 0.2), plus the worn
  finish, as on the remodelled hulls.
- **Carrier under construction**: built from the carrier module's own config with the `bone` two-tone scheme on its
  armour zones (the concept's light hull), then clipped; its engines, plumes and the lamps aft of the cut are removed.
- **Lights**: white work-light strips on the inner walls (emission 2.2: at 6 they bloomed), amber lamps at every rim
  joint (42) and arch corner (14), signature amber bars at the rim mouths, slow amber beacons on the hood arches and the
  control block, red obstruction lights at the extremities and white strobes on the two masts (nav path, 7 entries);
  automatic crease pins thinned on the open plating and none on the radiator arrays.

## New kit parts (`spaceport_kit.py`, GLBs in `assets/parts-spaceport/`, `parts-buildings.json`)

Parametric functions, true metric size, vertex-coloured (no textures). Reuse them in the next installations (shipyard,
stations); add rows to `style-library/styles/cqs-fleet/kits.md` when the kit is merged.

| Part | Exported size (m) | Tris | Mount | Notes |
| --- | --- | --- | --- | --- |
| habBlock(L, W, decks) | 16.1 x 25.5 x 40.5 (40 x 16, 5 decks) | 176 | +Y, length along Z | chamfered body on a 2 m plinth, 3 m decks, roof plant, door bay on +Z, amber corner marks; `habBlock_ports()` gives the kit-port positions (runs on the lit decks) |
| clampArm(reach) | 16 x 26.2 x 16 (reach 24) | 1288 | +Y, cradle at y = reach | base plate, two truss arms, rams, cradle with jaws and amber pads |
| manipulator(yaw, a1, a2, l1, l2) | 9 x 38 x 58 (34 + 30 m) | 288 | +Y | turret, boom with hazard band, forearm, wrist, effector, cable; returns the tip |
| gantryCrane(span, legL, legR) | 130 x 45 x 16 (span 120) | 1124 | bridge at y = 0 along X | twin pale box girders, amber stripe, truss legs to rail bogies, trolley, hoist and hook block |
| radiatorArray(n, w, h, solar) | 31 x 122 x 6 (3 pairs of 12 x 34 m) | 2908 | +Y | lattice mast, thin panels on outriggers (finned radiators or dark solar cells) |
| tug() | 16.8 x 12.3 x 21.1 | 528 | centre, bow +Z | yard tug: cab, push plate with fenders, four drive pods |
| truss(p0, p1, w) | - | - | - | square lattice (chords, rings, diagonals), the building block of masts, legs, cradles |

## Runtime (`src/buildings/spaceport.js`)

Exports `meta`, `station` (the GLB config: livery, PATINA detail, lights, lightscape), `DOCK` (carrier and freighter
placements, station frame), `CENTRE`, `preload()` (loads the station, carrier and freighter GLBs) and
`build(palette, { library })`: builds the station with `buildGLBShip`, the CV-50 from `ships/carrier.js`'s own config
(bone scheme) clipped by `clipGeometry` (exact triangle clipping on the plane, every attribute interpolated, so the cut
is a straight edge), and four CT-4s from `ships/freighter.js` (drives cold), then merges every pin, slit and nav light
into one `userData.ship` (so one `attachEffects()` draws the installation). Nothing is remodelled: the carrier and the
freighters are their shipped GLBs. It deliberately does not export `asset` (index.js would then build the station alone).

## Review (build v1, two fix rounds)

Sheet: `style-library/styles/cqs-fleet/images/build-spaceport-v1.jpg` (3/4, close-up, side, fleet scene, thumbnails,
size check, concept inset). Renders: `tools/shoot.mjs` in a scratch copy of the scene with the Integration diff applied.

| Check | Result |
| --- | --- |
| Concept match | **pass**: offset half-shells (trough under the carrier, hood shifted aft), open slot on the near side, dark plated shells with pale chamfered rims, blocks and cargo on the rims, gantry cranes over the open bay, manipulator arms under the hood and over the slot, white strips inside, amber lamps, docked CT-4s on clamp arms at the rims and on the hood, tugs, thin radiator / solar arrays. Differences: the build is longer and lower than the concept (the concept drew the hood as a taller round arch and the freighters about 3x too big); the carrier's bow is the real CV-50 in its bone scheme, not the concept's invented hull |
| Lean (corrections 25, 31) | **pass**: 1.26x the carrier, 6 m plates, no closed hall, no ring |
| Size check | **pass**: station / carrier 1.26, CT-4 / carrier 0.149 |
| Rulers (close-up) | **pass**: 1 m ports in runs on 3 m decks, crew doors, 1.1 m rails, ISO containers, the CT-4's own detail |
| Thumbnail (80 / 40 px) | **pass**: aspect 1.34 (limit 1.5), fill 0.59; the pale-rimmed dark hood over the trough reads at 40 px and is distinct from the shipyard and the vehicle |
| Side view | **weak**: lit from behind, the trough's lower chamfer still reads as a dark slab (round 2 added pale corner bands and more radiator arrays; next step if wanted: open lattice bays in the lower chamfer, or lit service galleries) |
| Lights | pass at the hero view (strips at emission 2.2 no longer bloom; rim-joint and arch lamps present); not audited against `lighting-standard.md` budgets (no installation row exists yet) |

Fix rounds: (1) work-light strips 6 -> 2.2 (they bloomed), shell albedo 0.05 -> 0.034, rim dressing (pipe runs,
plant, tanks, pallets), heavy frames thinned to 10 m-deep rings (they read as solid blocks), mirrored SP-3 code fixed;
(2) pale segmented corner bands on every octagon vertex, ten radiator / solar arrays, SP-3 moved clear of the rim, amber
lamps at rim joints and arch corners, the module's station-frame positions shifted by the GLB's bbox centre.

## Lessons

- `assemble_frame.load_hull` fails with `ReferenceError: StructRNA of type Object has been removed` when the hull GLB
  holds more than one mesh object; export the hull as one joined object (spaceport.py does).
- glbship centres every GLB on its bbox: a building authored in its own frame needs its authored lights, lightscape
  patterns, zones and docking positions shifted by the bbox centre (`CENTRE` in the module, checked at build).
- Clipping a shipped GLB at load (exact per-triangle clip) is enough to show a ship part-built: no second carrier GLB,
  no remodel, and the cut lands on a real frame face (F4's aft face) so it reads as a construction joint.
- Vertex-coloured, untextured building geometry plus the runtime PATINA layer and worn finish holds up from the
  close-up to the icon at a fraction of a textured hull's size (4.3 MB, of which the kit parts' textures are most).

## Integration

Not applied to the shared files. Tested in a scratch copy of the scene (studio and fleet shots). The diff below
applies cleanly from the repo root with `git apply --directory=Scene3D`. If the shipyard lands too, merge the two
`BUILDINGS` maps and `CLASSES` entries (`{ spaceport: '../buildings/spaceport.js', shipyard: ... }`).

- **Studio**: `?mode=ship&ship=spaceport` (main.js already loads just the studio ship; `index.js` needs the module path,
  the `preload()` hook and the PATINA library in `build()`; `scale.js` needs a `CLASSES` entry, `size: null`, so it
  gets no slot normalisation; `ui.js` labels it as a building).
- **Fleet**: the station 3 km off the carrier's starboard bow, yawed 30 deg so the slot faces the group, kept out of
  the shadow box; a new named shot `?mode=fleet&shot=spaceport`. `main.js` loads the `BUILDINGS` modules in fleet mode.
- Not in `ORDER`, the lineup or `scale-check.mjs` (buildings are not hangar units). The artifact packer
  (`build-artifact.mjs`) must also ship `assets/buildings/*.glb` (+ lite) and `assets/concepts/spaceport.webp`.

```diff
--- a/src/lib/scale.js
+++ b/src/lib/scale.js
@@ -26,6 +26,8 @@
   freighter: { size: 4,  label: 'Civil ship',  gameId: 'FREIGHTER', role: 'Cargo / troop transport' },
   destroyer: { size: 12, label: 'Destroyer',   gameId: 'DESTROYER', role: 'Heavy line warship' },
   carrier:   { size: null, capacity: 50, label: 'Carrier', gameId: 'CARRIER', role: 'Warp-capable fleet carrier' },
+  // orbital buildings (not hangar units: no slot normalisation, never in ORDER / the lineup / the scale check)
+  spaceport: { size: null, building: true, label: 'Spaceport', gameId: 'SPACEPORT', role: 'Orbital shipyard: builds the warp-capable units' },
 };
 
 export const CLEARANCE = 2; // metres around each parked hull
--- a/src/ships/index.js
+++ b/src/ships/index.js
@@ -7,6 +7,8 @@
 import { loadParts, composeParts } from '../lib/compose.js';
 
 export const ORDER = ['fighter', 'corvette', 'freighter', 'destroyer', 'carrier'];
+// orbital buildings: built through the same registry (studio ?mode=ship&ship=<id>, the fleet scene), module path below
+export const BUILDINGS = { spaceport: '../buildings/spaceport.js' };
 export const SHIPS = {};
 export const LOAD_ERRORS = {};
 const GLTFS = {};
@@ -21,7 +23,9 @@
   await Promise.all(only.map(async (cls) => {
     if (SHIPS[cls]) return;
     try {
-      const mod = await import(`./${cls}.js`);
+      const mod = await import(BUILDINGS[cls] || `./${cls}.js`);
+      // buildings load what they reuse (the ship GLBs they instance) before their synchronous build
+      if (mod.preload) await mod.preload();
       // generated ships: preload the fal GLB (and optional variants)
       if (mod.asset) {
         GLTFS[cls] = await loadGLB(mod.asset.glb);
@@ -59,7 +63,7 @@
       group = buildGLBShip(GLTFS[v?.glb ? `${cls}:${opts.variant}` : cls], cfg, { palette, library: CONTEXT.library });
       if (cfg.parts?.length) group.userData.ship.parts = composeParts(group, cfg.parts, PARTS, { livery: cfg.livery });
     } else {
-      group = mod.build(palette, opts);
+      group = mod.build(palette, { ...opts, library: CONTEXT.library });
     }
   } catch (e) {
     console.error(`[ships] ${cls}.build failed:`, e);
--- a/src/ui.js
+++ b/src/ui.js
@@ -62,7 +62,7 @@
         </tbody></table>`;
     }
     sheet.innerHTML = `
-      <p class="eyebrow">${s.source?.gameId || spec.gameId} · ${spec.size ? `${spec.size} hangar slot${spec.size > 1 ? 's' : ''}` : `carries ${spec.capacity} slots`}</p>
+      <p class="eyebrow">${s.source?.gameId || spec.gameId} · ${spec.building ? 'orbital building' : spec.size ? `${spec.size} hangar slot${spec.size > 1 ? 's' : ''}` : `carries ${spec.capacity} slots`}</p>
       <h2>${s.meta?.name ?? spec.label}</h2>
       <p class="role">${s.meta?.blurb || spec.role}</p>
       <dl class="specs">
--- a/src/main.js
+++ b/src/main.js
@@ -13,7 +13,7 @@
 import { attachEffects, LIGHTSCAPE_GAIN } from './lib/effects.js';
 import { CLASSES, SLOT_VOLUME, carrierLoads } from './lib/scale.js';
 import { hangarInsideFraction } from './lib/hangar.js';
-import { buildShip, loadShips, setShipContext, LOAD_ERRORS, ORDER } from './ships/index.js';
+import { buildShip, loadShips, setShipContext, LOAD_ERRORS, ORDER, BUILDINGS } from './ships/index.js';
 import { loadPatinaLibrary, proceduralStandIn } from './lib/patina.js';
 import { setLiveryScheme } from './lib/glbship.js';
 import { panelSet } from './lib/textures.js';
@@ -84,7 +84,8 @@
 // checks its hangar against every class's envelope
 const studioParked = mode === 'ship' && studioShip === 'carrier' ? params.get('parked') !== '0' : false;
 const onlyShip = mode === 'ship' && !studioParked && studioShip !== 'carrier' ? [studioShip] : ORDER;
-await loadShips(onlyShip);
+// the fleet scene also shows the orbital buildings (src/buildings/, registered in ships/index.js BUILDINGS)
+await loadShips(mode === 'fleet' ? [...onlyShip, ...Object.keys(BUILDINGS)] : onlyShip);
 
 // ---------------------------------------------------------------------------
 // check mode: build every ship, report envelopes vs. the game's size stat
--- a/src/fleet.js
+++ b/src/fleet.js
@@ -19,6 +19,8 @@
 import { launchCycle } from './lib/launch.js';
 
 const V = (x, y, z) => new THREE.Vector3(x, y, z);
+// orbital buildings in the fleet scene (main.js loads their modules in fleet mode)
+const ORBITAL_BUILDINGS = true;
 
 // The group's hangar (lib/park.js DEFAULT_LOADOUT, the same load the studio and the scale chart
 // park): 21 fighters three abreast in one row per bay side, 2 corvettes, a destroyer and a cargo
@@ -74,6 +76,10 @@
   place('freighter', V(409, 38, -868), { yaw: 3, variant: 'troops' });
   place('freighter', V(304, 42, -907), { yaw: 2, variant: 'cargo' });
 
+  // --- the SP-3 spaceport (an orbital building, src/buildings/spaceport.js): 3 km off the starboard bow, yawed
+  // 30 degrees so its open slot faces the group; drives of its docked freighters cold. Its own shot: ?shot=spaceport
+  const spaceport = ORBITAL_BUILDINGS ? place('spaceport', V(-2600, -150, 1900), { yaw: -30, power: 0, bob: 0 }) : null;
+
   // --- fighters ---------------------------------------------------------------
   const fighters = [];
   const addFighter = (parent = root) => {
@@ -151,7 +157,8 @@
   }
 
   const shadowBox = new THREE.Box3();
-  for (const s of ships) if (s.cls !== 'fighter') shadowBox.expandByObject(s.group);
+  // (the spaceport 3 km off is left out: the shadow map stays fitted to the carrier group)
+  for (const s of ships) if (s.cls !== 'fighter' && s.cls !== 'spaceport') shadowBox.expandByObject(s.group);
 
   // camera shots (world = carrier frame). The planet is true scale (planet.js): the fleet is
   // 400 km up, so its horizon sits 3.5-36 degrees below the fleet's horizontal depending on the
@@ -176,6 +183,8 @@
     // logistics convoy trailing in the foreground against the planet, the trailing corvette's
     // own bells to starboard, the limb across the lower third
     stern: { pos: V(330, 300, -1250), target: V(110, -70, -400), horizon: 5 },
+    // the spaceport: 45 degrees off its bow on the slot side, 30 degrees up, 2 km out
+    ...(spaceport ? { spaceport: { pos: V(-2152, 850, 3574), target: V(-2600, -150, 1900), fov: 34, horizon: 5 } } : {}),
   };
 
   return {
```
