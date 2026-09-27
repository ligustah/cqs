// Fighter F-402 — generated with fal (Tripo H3.1 multiview, see pipeline/fal-pipeline.json).
// Anchors were measured on the GLB in the centred ship frame (rotate -> length -> centre),
// metres, bow +Z, dorsal +Y, port +X (the hull number is on both flanks; the concept's
// front-left view shows the port side).
// - length 71.18 m gives an envelope of 48.0 x 20.5 x 71.2 m = 70,000 m^3 (1 slot), so the
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
  name: 'Petrel-class fighter', designation: 'F-402', crew: 'about 40',
  blurb: 'Space-superiority fighter: a faceted armoured pod with a three-pane flight-deck canopy, twin fusion bells in an armoured stern block and a long railgun on each flank sponson, each sponson ending in a small secondary drive bell.',
};
export const asset = {
  glb: './assets/ships/fighter.glb', generator: 'tripo3d/h3.1/multiview-to-3d',
  concept: './assets/concepts/fighter.webp', beauty: './assets/concepts/fighter-beauty.webp',
  rotate: [0, -90, 0],
  length: 71.182,
  livery: 'dark',
  crease: 35, // faceted armour panels shade flat; bells and barrels (<12 deg per segment) stay smooth
  detail: { set: 'hull', tile: 6, normalStrength: 0.6, roughAmount: 0.5, cavity: 0.8 },
  materials: { '*': { envMapIntensity: 1.0 } },
  engines: [
    // twin fusion bells, exit plane at the aft face of the lip (z = -12.725)
    // depth / throat / wall: ray-cast on the GLB (throat plate 1.3 r inside the lip, the bell
    // converges from 0.93 r at 0.75 r deep to a 0.48 r throat)
    { p: [6.525, -0.12, -35.574], radius: 4.136, mirrorX: true, depth: 5.37, throat: 1.958, wall: [[2.07, 3.999], [3.104, 3.832], [4.139, 2.405]] },
    // secondary drive bells at the aft end of each flank sponson (exit rim z = -6.36)
    { p: [20.922, -2.735, -17.773], radius: 1.636, mirrorX: true, depth: 1.958, throat: 1.119, wall: [[0.811, 1.524], [1.231, 1.398]] },
  ],
  lights: [
    // steady sidelights on the raised panel of each sponson's outboard face (beam extremity, x = +-8.58)
    { p: [24.22, -3.496, -4.195], color: 'red', mirrorX: true, mirrorColor: 'green', size: 0.4 },
    // anti-collision strobes: dorsal spine between the radiators (y = 3.02), keel strip (y = -3.66); alternating
    { p: [0, 8.67, -9.789], color: 'white', size: 0.4, blink: { period: 1.3, duty: 0.1 } },
    { p: [0, -10.46, -1.398], color: 'white', size: 0.4, blink: { period: 1.3, duty: 0.1, phase: 0.5 } },
    // steady white stern light on the upper frame of the stern block's aft face (z = -9.30), above the bells
    { p: [0, 5.929, -26.233], color: 'white', size: 0.4 },
  ],
  anchors: {
    muzzlePort: { p: [20.914, -2.735, 20.864], dir: [0, 0, 1] },
    muzzleStbd: { p: [-20.908, -2.772, 20.864], dir: [0, 0, 1] },
  },
};
