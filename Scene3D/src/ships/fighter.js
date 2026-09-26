// Fighter F-402 — generated with fal (see pipeline/fal-pipeline.json).
// Anchors were measured on the GLB in the centred ship frame (rotate -> length -> centre),
// metres, bow +Z, dorsal +Y, port +X.
// - length 15.6 m gives an envelope of 9.82 x 5.22 x 15.6 m = 800 m^3 (1 slot), so the
//   class volume correction is ~1.00. The envelope height is set by the dorsal antennas
//   (y = +2.61) and the keel (y = -2.61).
// - Main drive: two fusion bells with a thin exit lip (inner edge r = 0.977 m). Centres are
//   circle fits of the lip rim. The mesh is not exactly mirror-symmetric: the starboard lip
//   sits 0.11 m further forward (z -7.665 vs -7.775), so both are listed explicitly.
// - Each flank sponson ends in a small converging-diverging nozzle (exit r = 0.42 m, throat
//   0.4 m deeper) coaxial with its railgun: read as a recoil-compensation thruster that pulses
//   only when the gun fires, so it gets no continuous plume (dark in the concept too). It is
//   recorded as an anchor, as are the railgun muzzles.
export const meta = {
  name: 'Petrel-class fighter', designation: 'F-402',
  blurb: 'Single-seat space-superiority fighter: a faceted armoured pod with a flush canopy, twin fusion bells in an armoured stern block and a long railgun on each flank sponson.',
};
export const asset = {
  glb: './assets/ships/fighter.glb', generator: 'tripo3d/p2/image-to-3d',
  concept: './assets/concepts/fighter.webp', beauty: './assets/concepts/fighter-beauty.webp',
  rotate: [0, 0, 0],
  length: 15.6,
  crease: 35, // faceted armour panels shade flat; bells and barrels (<12 deg per segment) stay smooth
  detail: { set: 'hull', tile: 4, normalStrength: 0.6, roughAmount: 0.5, cavity: 0.8 },
  materials: { '*': { envMapIntensity: 1.0 } },
  engines: [
    { p: [1.383, 0.515, -7.775], radius: 0.96 }, // port bell, exit plane at the lip's inner edge
    { p: [-1.385, 0.515, -7.665], radius: 0.96 }, // starboard bell
  ],
  lights: [
    // steady nav lights on the outboard faces of the sponsons (the beam extremity, x = +-4.91)
    { p: [4.95, -0.30, -0.80], color: 'red', mirrorX: true, mirrorColor: 'green', size: 0.4 },
    // anti-collision strobes: dorsal spine between the radiators, keel; alternating flashes
    { p: [0, 1.95, -1.0], color: 'white', size: 0.4, blink: { period: 1.3, duty: 0.1 } },
    { p: [0, -2.62, -1.5], color: 'white', size: 0.4, blink: { period: 1.3, duty: 0.1, phase: 0.5 } },
    // steady white stern light on the upper aft chamfer of the engine block, above the bells
    { p: [0, 1.63, -5.22], color: 'white', size: 0.3 },
  ],
  anchors: {
    muzzlePort: { p: [4.255, -0.51, 5.0], dir: [0, 0, 1] },
    muzzleStbd: { p: [-4.255, -0.51, 5.0], dir: [0, 0, 1] },
    recoilThrusterPort: { p: [4.335, -0.125, -3.47], dir: [0, 0, -1], radius: 0.41 },
    recoilThrusterStbd: { p: [-4.335, -0.125, -3.47], dir: [0, 0, -1], radius: 0.41 },
  },
};
