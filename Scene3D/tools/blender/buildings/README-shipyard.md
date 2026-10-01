# Shipyard SY-1 (planetside, cqs-fleet): 3D build v1

Concept: `style-library/styles/cqs-fleet/images/shipyard-r3-A-fixed.jpg` (r3 A, corrections 24-28, 32).
Review sheet: `style-library/styles/cqs-fleet/images/build-shipyard-v1.jpg`.
No fal jobs were used ($0): a parametric Blender build from the concept, no image-to-3D.

```sh
PY=<python with bpy 5.x, scipy, pillow>
cd Scene3D
PY=$PY python3 tools/blender/buildings/shipyard_build.py <work> [--kit] [--measure] [--tex 2048]
#   --kit      rebuild the yard kit first (~40 min on 4 CPUs; the gantry's 4096 bake is ~17 min)
#   --measure  re-measure the DD-12 (only when destroyer.glb changes)
# the rest (hull, spec, assemble, lite) is ~6 min
```

## Files

| File | Role |
| --- | --- |
| `yard_kit.py` | Yard kit: reusable parametric parts built with the fleet kit's `lib.Part` + bake pipeline -> `assets/parts-yard/*.glb` + `parts.json` (mount +Y, anchors for lamps, windows, floods, doors, ladders, hooks). |
| `shipyard_dims.py` | Dimension tables: yard layout, the DD-12's placement (`SHIP_T`), build-state cuts, ring-frame stations, block stations. |
| `shipyard_measure.py` | Measures `assets/ships/destroyer.glb` (MODEL frame): ring-frame outlines from ray-cast sections, hull bottom at the block stations, bbox -> `specs/shipyard-dd12.json`. |
| `shipyard.py` | The yard's own geometry (node `hull`): ground apron with a generated 24 m concrete texture, berth floor, painted lines, gantry and crane rails, the DD-12's procedural ring frames, keel and stringers, the module on the gantry with spreader and ropes, the frame segment on crane A, the bell cradle. |
| `shipyard_spec.py` | Placements (`specs/shipyard-v1.json`) of the yard kit and fleet kit, plus the generated light / build-state block of `src/buildings/shipyard.js`. |
| `shipyard_build.py` | The chain above + `assemble.py --no-bake` + `tools/lite-glb.mjs`. |

Outputs: `assets/buildings/shipyard.glb` (244,264 tris, 9.98 MB, nodes `hull` + 20 `parts_*`), `assets/buildings/shipyard.lite.glb`
(textures <= 1024, 6.2 MB), `src/buildings/shipyard.js`.

## Frame and size

YARD frame: metres, ground top y = 0, +Y up, +Z front (bow end of the berth), +X left, origin at the berth centre.

| Item | Size |
| --- | --- |
| Apron (whole yard) | 258 x 282 m (x, z), plinth 1.6 m; GLB bbox 258 x 116.6 x 282 m |
| Berth floor | 80 x 250 m |
| Portal gantry "01" | span 96 m between rail centres, 95 m clear under the girders, girder top 105 m, crab house to 115 m; 112 m long double box girder |
| Luffing cranes A / B | 12 m portal on a runway at x = 68 m, 70 m jib (60 / 66 deg), ~81-85 m tall |
| Workshop halls | 4 segments 80 x 36 m, eaves 18 m, roof 21.5 m |
| Flood masts | 6 x 32 m, 6 kit floodlights each |
| DD-12 | the real `destroyer.glb` at its GLB size (202.7 m), yard = model + (0, 38.8, 10); keel blocks 1.64-~8.6 m |
| Icon (az 35, el 30) | subject aspect ~1.48 (STYLE limit 1.5) |

## The DD-12 in the berth (corrections 26, 32)

Not baked: `shipyard.js` calls `loadShips(['destroyer'])` / `buildShip('destroyer')` (same livery, finish, glass and
lightscape as in the fleet), sets its scale to 1 (the GLB's own size, on which the frames and blocks were measured)
and clips every mesh on the CPU (Sutherland-Hodgman per triangle, all attributes interpolated) to the union of keep
regions, MODEL frame z: `z >= 20` complete; `-6 <= z < 20` only `y <= -17`; `-34 <= z < -6` only `y <= -24`; aft of
`-34` nothing (the procedural keel + octagonal ring frames in the yard GLB follow the hull's measured sections:
main hull 35 m midships, engine block 55.3 m aft; the last three frames are open U's = the build front). Cut plating
gets a dark primer back face. The ship keeps only its bow's pins and slits; drives, nav lights and nozzle glows are off.
The clip runs once per build (~180k triangles, well under a second); the clipped geometry is per instance, so fleet
destroyers are untouched. No renderer flags (localClippingEnabled) are needed.

## Look and lights

- Buildings light concept paint (correction 27): `livery: null`; fleet PATINA `hull` detail at 6 m (normalStrength 0.45)
  and the worn finish still apply. Gantry and crane portals charcoal steel; crane jibs light with amber bands; amber
  (0.93, 0.58, 0.12) for hazard paint, never orange.
- Lights (yard frame, generated): 61 amber pins 0.3 m (block corners, bogies, bollards, trucks), 4 slow amber beacons
  (crab, crane A-frames, pulse 3.6 s), 4 red 0.4 m obstruction lights (the only `lights[]`), 24 slits (door lamps
  0.6 x 0.14 m over every crew door, leg-head and hall-door bars), 35 lit windows (gantry cabs, crane cabs, ~55 % of
  the office panes, behind real kit glass), warm glow in the open hall doors, 36 lit floodlight lenses and 6 spot
  lights (one per mast, no shadow maps).
- Dusk: the module exports `studio = { exposure 1.25, key 0.42, fill 0.55, rim 0.5, kick 0.6, env 0.6, lightscapeGain 1.3 }`,
  applied by the building view (Integration).

## Review (v1)

Renders (scratch scene with the Integration diff applied): hero az 35 / el 30, midships close-up, bow close-up,
top view, thumbnail test (`tools/thumbs/thumbs.mjs`, 80 / 40 px on #222d35 next to the concept, spaceport concept and
DD-12). Fix round 1: overlay hidden in stills, ground darker with a calmer slab tone (it read as a checkerboard), apron
trimmed (aspect), more activity on the empty front-right apron (truck, containers, crew).

Passed: the concept's composition (dominant dark gantry "01" over one berth, cranes behind, light halls on both sides,
flood masts, amber lamps, trucks, containers, forklifts, scaffolds, crew), the real DD-12 part-built, kit rulers at
true size, identifiable at 80 px and distinct at 40 px (gantry silhouette + light roofs). Open: hall roofs read plain;
the frame segment on crane A is small; the dark ship in the dark berth is weak at 40 px (as in the concept); the tall
bow keel blocks are y-scaled kit blocks (their concrete base stretches); no range / lineup views yet (no building
lineup exists); exterior floods (F17 outside a hangar) are not yet ruled in STYLE.md, so the user should confirm them.

## Draft kits section (for `style-library/styles/cqs-fleet/kits.md`)

### Yard kit: `Scene3D/assets/parts-yard/` (`tools/blender/buildings/yard_kit.py`)

Mount: every yard part stands on y = 0 (`mount.normal` +Y), origin at the footprint centre, front +Z. Anchors (lamps,
beacons, obstruction lights, slits, windows, floods, doors, panes, vents, ladders, hook) are in `parts.json`.

| Part | Size w x h x d (m) | Notes |
|---|---|---|
| gantry | 112 x 115 x 51.2 | portal gantry: span 96 m, 95 m clear, double box girder, A-frame legs, crab with hoist house, fleet-stencil number (`mark`), tex 4096 |
| crane-A / crane-B | ~55 x 81-85 x 14-16 | level-luffing portal crane (12 m gauge, 70 m light jib with amber bands, beak, hook); one bake per pose (`slew`, `luff`, `hook`) |
| hall | 37.3 x 24.1 x 81.3 | workshop hall segment 80 x 36 m, light cladding, pilasters, chamfered roof, half-open 20 x 14 m end door, side roller doors; anchors for kit doors / panes / vents / ladder |
| floodMast | 2.6 x 32.2 x 2.0 | 32 m mast, head frame for 6 kit floodlights (anchors.floods, spot anchor anchors.light) |
| scaffold-S / M / L | 5.2 x 9 / 15 / 23 x 1.5 | scaffold tower, 2.5 x 1.3 m bays, 2 m lifts (4 / 7 / 11), amber toe boards |
| truck | 2.64 x 4.55 x 17.2 | semi: cab-over tractor + 13.6 m box trailer |
| forklift | 1.37 x 3.1 x 4.0 | counterbalance forklift, amber |
| worker | 0.64 x 1.8 x 0.27 | 1.8 m crew figure (the fleet ruler), amber vest, hard hat |
| keelBlock | 3.0 x 2.0 x 2.2 | keel / bilge block; scale y for other heights |
| bollard | 0.36 x 1.17 x 0.36 | lamp bollard; its amber lamp is a lightscape pin at anchors.lamp |

Container stacks are a placement macro (`shipyard_spec.container_stack`) over the fleet kit `container`, not a part.
Note: the spaceport build (`spaceport_kit.py`) uses a separate vertex-colour kit; the two should be merged into one
building kit when the next installation is built.

## Integration

Shared files are not edited by this build. To show the yard in the scene, apply this to `Scene3D/src/main.js`
(tested in a scratch copy; it adds `?mode=building&building=shipyard`, or `#shipyard`, a building studio with the
module's dusk hint; stills hide the overlay; `?focus=x,y,z&dist=m` gives close-ups):

```diff
--- a/Scene3D/src/main.js
+++ b/Scene3D/src/main.js	2026-10-01 13:06:35.319349022 +0000
@@ -32,7 +32,10 @@
 const EXPOSURE = 1.7; // default tone-mapping exposure (see start())
 const hash = location.hash.replace('#', '');
 const HASH_MODES = ['fleet', 'lineup'];
-const mode = params.get('mode') || (HASH_MODES.includes(hash) ? hash : (ORDER.includes(hash) ? 'ship' : 'fleet'));
+// installations (src/buildings/<id>.js): ?mode=building&building=shipyard (or #shipyard)
+const BUILDINGS = ['shipyard'];
+const mode = params.get('mode') || (HASH_MODES.includes(hash) ? hash : (ORDER.includes(hash) ? 'ship' : BUILDINGS.includes(hash) ? 'building' : 'fleet'));
+const BUILDING = mode === 'building' ? await import(`./buildings/${params.get('building') || (BUILDINGS.includes(hash) ? hash : 'shipyard')}.js`) : null;
 const still = params.has('still');
 const fixedTime = params.has('t') ? parseFloat(params.get('t')) : null;
 
@@ -45,11 +48,11 @@
 // Showcase lighting (env/lighting.js createStudioLighting) is the ship studio's default: key, fill and
 // rim lights, a soft-box environment and a gradient backdrop, no planet. ?studio=0 falls back to the
 // orbital rig (the hard sun below over the planet). Every other view keeps the orbital rig.
-const studio = mode === 'ship' && params.get('studio') !== '0';
+const studio = (mode === 'ship' || mode === 'building') && params.get('studio') !== '0';
 if (studio) {
   // the studio key and fill light the dark hull far more than the orbital sun: the lightscape (pins, slits) gets
   // STUDIO.lightscapeGain there so the small lights keep the concept's contrast; orbit and fleet stay at 1
-  LIGHTSCAPE_GAIN.value = STUDIO.lightscapeGain ?? 1;
+  LIGHTSCAPE_GAIN.value = (BUILDING?.studio?.lightscapeGain ?? STUDIO.lightscapeGain) ?? 1;
   // the key light is also SUN_DIR (the shadow fit reads it); ?sunaz= / ?sunel= still override it (ship frame)
   const camAz = parseFloat(params.get('az') ?? '35'), camEl = parseFloat(params.get('el') ?? '18');
   SUN_DIR.copy(studioDir(camAz, camEl, STUDIO.key.az, STUDIO.key.el));
@@ -83,8 +86,9 @@
 // ?parked=1 also aims the camera at it), so every class is needed; the carrier's spec sheet also
 // checks its hangar against every class's envelope
 const studioParked = mode === 'ship' && studioShip === 'carrier' ? params.get('parked') !== '0' : false;
-const onlyShip = mode === 'ship' && !studioParked && studioShip !== 'carrier' ? [studioShip] : ORDER;
+const onlyShip = mode === 'building' ? [] : mode === 'ship' && !studioParked && studioShip !== 'carrier' ? [studioShip] : ORDER;
 await loadShips(onlyShip);
+if (BUILDING) await BUILDING.load(); // the building's GLB and the ships it shows (e.g. the shipyard's DD-12)
 
 // ---------------------------------------------------------------------------
 // check mode: build every ship, report envelopes vs. the game's size stat
@@ -137,7 +141,7 @@
   // Look-dev: ?tonemap=agx|neutral, ?exposure=
   const TONEMAPS = { agx: THREE.AgXToneMapping, neutral: THREE.NeutralToneMapping };
   renderer.toneMapping = TONEMAPS[params.get('tonemap')] ?? THREE.NeutralToneMapping;
-  renderer.toneMappingExposure = parseFloat(params.get('exposure') || String(studio ? STUDIO.exposure : EXPOSURE));
+  renderer.toneMappingExposure = parseFloat(params.get('exposure') || String(studio ? (BUILDING?.studio?.exposure ?? STUDIO.exposure) : EXPOSURE));
   renderer.shadowMap.enabled = true;
   renderer.shadowMap.type = THREE.PCFShadowMap;
   container.appendChild(renderer.domElement);
@@ -169,6 +173,13 @@
       camAz: parseFloat(params.get('az') ?? '35'), camEl: parseFloat(params.get('el') ?? '18'), keyDir: SUN_DIR,
     })
     : createLighting(renderer, scene, { shadowSize: TIER.shadowSize });
+  // a building's studio hint (e.g. the shipyard's dusk): the showcase rig dimmed per light
+  if (studio && BUILDING?.studio) {
+    const d = BUILDING.studio;
+    lighting.sun.intensity *= d.key ?? 1;
+    for (const L of lighting.lights || []) L.intensity *= d[L.name.replace('studio-', '')] ?? 1;
+    scene.environmentIntensity *= d.env ?? 1;
+  }
   // the studio has no sky (star field, sun glare): its backdrop is part of the lighting rig
   const sky = studio ? { update() {} } : createSky(scene);
 
@@ -222,7 +233,8 @@
   const overlays = []; // screen-space annotation, laid out after the camera has moved
   let world = null; // { ships:[{group, cls}], focus(cls) , bounds }
 
-  if (mode === 'ship') world = setupShipStudio();
+  if (mode === 'building') world = setupBuildingStudio();
+  else if (mode === 'ship') world = setupShipStudio();
   else if (mode === 'lineup') world = setupLineup();
   else world = setupFleet();
 
@@ -233,7 +245,8 @@
     for (const cls of onlyShip) envelopes[cls] = buildShip(cls, palette).userData.ship.envelope.size.clone();
     if (onlyShip.includes('freighter')) envelopes['freighter:troops'] = buildShip('freighter', palette, { variant: 'troops' }).userData.ship.envelope.size.clone();
   }
-  const ui = createUI({
+  // a building view has no class list or spec sheet yet: the overlay stays hidden
+  const ui = mode === 'building' ? (document.getElementById('ui')?.setAttribute('hidden', ''), { select() {} }) : createUI({
     mode, still, world, classes: CLASSES, order: ORDER, envelopes,
     onMode: (m) => { location.hash = m; location.reload(); },
     onFocus: (cls) => world.focus?.(cls),
@@ -298,6 +311,29 @@
     return { ships: [{ group: g, cls }], selected: cls, focus: () => {} };
   }
 
+  // --- building studio: one installation (src/buildings/<id>.js), framed like the ship studio ------------
+  function setupBuildingStudio() {
+    const g = BUILDING.build(palette, { library });
+    scene.add(g);
+    for (const t of g.userData.building.effectTargets) effects.push(attachEffects(t, { power: 0 }));
+    lighting.fitShadow(new THREE.Box3().setFromObject(g));
+    const az = THREE.MathUtils.degToRad(parseFloat(params.get('az') ?? '35'));
+    const el = THREE.MathUtils.degToRad(parseFloat(params.get('el') ?? '30'));
+    const dir = new THREE.Vector3(Math.sin(az) * Math.cos(el), Math.sin(el), Math.cos(az) * Math.cos(el));
+    let target;
+    if (params.has('focus')) {
+      // ?focus=x,y,z&dist=m: a close-up on a point of the building (its own frame)
+      target = new THREE.Vector3(...params.get('focus').split(',').map(Number));
+      camera.position.copy(dir).multiplyScalar(parseFloat(params.get('dist') ?? '120')).add(target);
+      camera.lookAt(target);
+    } else {
+      target = frameView(camera, hullPoints(g), dir, { l: 64, r: 64, t: 56, b: 56 }, w, h);
+      camera.position.sub(target).multiplyScalar(parseFloat(params.get('dist') ?? '1')).add(target);
+    }
+    controls.target.copy(target);
+    return { ships: [{ group: g, cls: g.userData.building.id }], selected: g.userData.building.id, focus: () => {} };
+  }
+
   // ?debug: ship-frame axes (X red = port, Y green = dorsal, Z blue = bow), a
   // 1 m / 5 m keel grid, engine and light anchors, hangar box and mouth.
   function debugOverlay(s) {
```

Nothing else is required: `src/ships/index.js`, `src/lib/scale.js` and `fleet.js` stay as they are (the yard is not a
ship class; the module loads the DD-12 through the existing registry). Optional later: a building entry in
`ui.js` (spec sheet), and `tools/build-artifact.mjs` already packs any GLB under `assets/` with its lite copy.
Note for the orchestrator: the spaceport build may propose its own building mode; merge both into one
`BUILDINGS` list (the module contract here is `load()`, `build(palette, { library })`, `studio`, `meta`, and
`group.userData.building.effectTargets`).
