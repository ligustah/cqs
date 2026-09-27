// Fighter F-402 — generated with fal (Tripo H3.1 multiview, see pipeline/fal-pipeline.json).
// Anchors were measured on the GLB in the centred ship frame (rotate -> length -> centre),
// metres, bow +Z, dorsal +Y, port +X (the hull number is on both flanks; the concept's
// front-left view shows the port side).
// - length 25.452 m gives an envelope of 17.16 x 7.33 x 25.45 m = 3,200 m^3 (1 slot), so the
//   class volume correction is 1.00. The beam is set by the sponsons' outboard faces, the
//   height by the two dorsal antennas (y = +3.66) and the keel strip (y = -3.66).
// - Main drive: two fusion bells in the armoured stern block, the only main drive. Centres are
//   circle fits of the exit lip and the inner wall (port 2.332 / -0.042, starboard -2.335 /
//   -0.043: symmetric to 3 mm, so one mirrored entry). Radius = inner wall at the exit
//   (1.479 m; the lip's outer edge is at 1.64 m); exit plane at the aft face of the lip.
// - Secondary drive: each flank sponson ends in a small drive bell coaxial with its railgun
//   (same coil ring and cage hardware as the main bells; the beauty shows a soft pale-blue
//   plume from each). Exit rim at z = -6.36, inner wall r 0.59-0.60 at the exit, narrowing to
//   r 0.42 at the throat closure (z = -5.66, bell 0.70 m deep); outer lip r 0.72. Circle fits
//   of the exit slab: port (7.484, -0.980), starboard (-7.478, -0.979), mirror error < 7 mm,
//   so one mirrored entry. Radius 0.585 keeps the glow disc and lining inside the wall.
//   The railgun muzzles are recorded as anchors.
export const meta = {
  name: 'Petrel-class fighter', designation: 'F-402', crew: '3 (pilot, weapons, systems)',
  blurb: 'Space-superiority fighter: a faceted armoured pod with a three-pane flight-deck canopy, twin fusion bells in an armoured stern block and a long railgun on each flank sponson, each sponson ending in a small secondary drive bell.',
};
export const asset = {
  glb: './assets/ships/fighter.glb', generator: 'tripo3d/h3.1/multiview-to-3d',
  concept: './assets/concepts/fighter.webp', beauty: './assets/concepts/fighter-beauty.webp',
  rotate: [0, -90, 0],
  length: 25.452,
  livery: 'dark',
  crease: 35, // faceted armour panels shade flat; bells and barrels (<12 deg per segment) stay smooth
  detail: { set: 'hull', tile: 6, normalStrength: 0.6, roughAmount: 0.5, cavity: 0.8 },
  materials: { '*': { envMapIntensity: 1.0 } },
  engines: [
    // twin fusion bells, exit plane at the aft face of the lip (z = -12.725)
    // depth / throat / wall: ray-cast on the GLB (throat plate 1.3 r inside the lip, the bell
    // converges from 0.93 r at 0.75 r deep to a 0.48 r throat)
    { p: [2.333, -0.043, -12.72], radius: 1.479, mirrorX: true, depth: 1.92, throat: 0.7, wall: [[0.74, 1.43], [1.11, 1.37], [1.48, 0.86]] },
    // secondary drive bells at the aft end of each flank sponson (exit rim z = -6.36)
    { p: [7.481, -0.978, -6.355], radius: 0.585, mirrorX: true, depth: 0.7, throat: 0.4, wall: [[0.29, 0.545], [0.44, 0.5]] },
  ],
  lights: [
    // steady sidelights on the raised panel of each sponson's outboard face (beam extremity, x = +-8.58)
    { p: [8.66, -1.25, -1.5], color: 'red', mirrorX: true, mirrorColor: 'green', size: 0.4 },
    // anti-collision strobes: dorsal spine between the radiators (y = 3.02), keel strip (y = -3.66); alternating
    { p: [0, 3.1, -3.5], color: 'white', size: 0.4, blink: { period: 1.3, duty: 0.1 } },
    { p: [0, -3.74, -0.5], color: 'white', size: 0.4, blink: { period: 1.3, duty: 0.1, phase: 0.5 } },
    // steady white stern light on the upper frame of the stern block's aft face (z = -9.30), above the bells
    { p: [0, 2.12, -9.38], color: 'white', size: 0.4 },
  ],
  anchors: {
    muzzlePort: { p: [7.478, -0.978, 7.46], dir: [0, 0, 1] },
    muzzleStbd: { p: [-7.476, -0.991, 7.46], dir: [0, 0, 1] },
  },
};
