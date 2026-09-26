# Orbital Fleet — 3D scene for the Conquer-Space reboot

A real-time three.js scene with original models of the reboot's orbital ships:
fighter, corvette, civil ship (freighter / troop transport), destroyer and the
fleet carrier. All ships are drawn to one consistent scale taken from the game's
own unit data.

All ship designs, textures and the environment here are new work. None of the
original game's artwork or models (`Artwork/`, `Html/Design/pack/units/`) is
used or referenced. Only the class roster and the gameplay stats come from the
original code.

## Running it

No build step. The page loads three.js from the jsDelivr CDN through an import map.

```sh
cd Scene3D
node tools/serve.mjs 8080      # any static server works
# open http://127.0.0.1:8080/
```

Views (use the buttons, or a URL hash / query parameter):

| View | URL | What it shows |
| --- | --- | --- |
| Fleet in orbit | `#fleet` (default) | Carrier group above a procedural planet: fighter patrols, launches from the hangar, escorts, the logistics convoy |
| Scale lineup | `#lineup` | Scale chart: sterns aligned on a metre ruler, one row per class, a 1-slot reference cube, and an optional 50-fighter hangar load |
| Ship studio | `?mode=ship&ship=carrier&az=35&el=18&dist=1` | One ship, framed for inspection (`fighter`, `corvette`, `freighter`, `destroyer`, `carrier`; `variant=lead`/`troops`) |

Controls: drag to orbit, scroll to zoom, double-click a ship to fly to it and follow it.

## Scale model

The game gives each space unit a hangar **size** in
`Engine/net/cqs/engine/units/UnitEnum.java` (`getSize()`), and a carrier holds
`getSpaceUnitCapacity() = 50` size units of non-warp ships:

| Class | Game id | Size (hangar slots) |
| --- | --- | --- |
| Fighter | `FIGHTER*` | 1 |
| Civil ship | `FREIGHTER*`, `TRANSPORTER*` | 4 |
| Corvette | `CORVETTE*` | 5 |
| Destroyer | `DESTROYER*` | 12 |
| Carrier | `CARRIER` | carries 50 |

The scene reads *size* as a ship's parking envelope in a hangar: the
axis-aligned bounding box, length × beam × height. One slot is 800 m³, which
puts the fighter at about 16 m. `src/lib/scale.js` scales every ship uniformly
so that its envelope volume is exactly `size × 800 m³`. Each design is built at
real size in metres, so this correction is only a few percent.

The carrier's hangar bay is modelled as a real interior volume. It is sized so
that every legal full load (50 fighters, 10 corvettes, 4 destroyers or 12 civil
ships) fits with 2 m clearance on all sides. `node tools/scale-check.mjs`
verifies all of this against the geometry that is actually rendered:

<!-- scale-table -->

## Layout

```
Scene3D/
  index.html            page shell, UI overlay, import map
  src/main.js           renderer, views, camera, post-processing
  src/fleet.js          fleet composition and choreography
  src/ui.js             ship registry and spec sheet
  src/ships/*.js        one module per class: meta + build(palette, opts)
  src/lib/kit.js        geometry kit + ShipBuilder (merge by material, box-projected UVs, anchors)
  src/lib/materials.js  PBR livery palette (painted composite, armour, foil, ceramic, glass, emissives)
  src/lib/textures.js   procedural tileable plating / foil / radiator / window / decal textures
  src/lib/effects.js    plasma plumes and navigation lights
  src/lib/scale.js      game-derived scale model and hangar-fit check
  src/env/*.js          lighting rig, sky, planet
  tools/                static server, headless screenshots, scale check, artifact packaging
```

## Tools

```sh
npm install                     # three + playwright-core, only needed for the tools
node tools/scale-check.mjs      # envelope vs. game size for every ship + hangar loads
node tools/shoot.mjs "mode=ship&ship=destroyer&az=35&el=18" shots/destroyer.png
node tools/render-glb.mjs any/where/ship.glb shots/ship --rot 0,90,0   # GLB inspection stills + contact sheet + mesh info
node tools/build-artifact.mjs   # single-page package for sharing
```

`shoot.mjs` renders with headless Chromium and software WebGL, and serves
three.js from `node_modules`, so it works offline.
