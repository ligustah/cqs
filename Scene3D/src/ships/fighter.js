// Fighter F-402 — generated with fal (see pipeline/fal-pipeline.json).
// Anchors were measured on the GLB in the centred ship frame (rotate -> length -> centre),
// metres, bow +Z, dorsal +Y, port +X, then rescaled with the fleet to 1 slot = 3,200 m^3.
// - length 24.76 m gives an envelope of 15.6 x 8.3 x 24.8 m = 3,200 m^3 (1 slot), so the
//   class volume correction is ~1.00. The envelope height is set by the dorsal antennas
//   and the keel.
// - Main drive: two fusion bells; centres are circle fits of the exit lip. The mesh is not
//   exactly mirror-symmetric (the starboard lip sits 0.17 m further forward), so both are
//   listed explicitly.
// - Each flank sponson ends in a small nozzle coaxial with its railgun: a recoil-compensation
//   thruster that pulses only when the gun fires, so it gets no continuous plume. It is
//   recorded as an anchor, as are the railgun muzzles.
export const meta = {
  name: 'Petrel-class fighter', designation: 'F-402', crew: '3 (pilot, weapons, systems)',
  blurb: 'Space-superiority fighter: a faceted armoured pod with a three-seat flight deck, twin fusion bells in an armoured stern block and a long railgun on each flank sponson.',
};
export const asset = {
  glb: './assets/ships/fighter.glb', generator: 'tripo3d/p2/image-to-3d',
  concept: './assets/concepts/fighter.webp', beauty: './assets/concepts/fighter-beauty.webp',
  rotate: [0, 0, 0],
  length: 24.763,
  crease: 35, // faceted armour panels shade flat; bells and barrels (<12 deg per segment) stay smooth
  detail: { set: 'hull', tile: 6, normalStrength: 0.6, roughAmount: 0.5, cavity: 0.8 },
  materials: { '*': { envMapIntensity: 1.0 } },
  engines: [
    { p: [2.195, 0.818, -12.342], radius: 1.524 }, // port bell, exit plane at the lip's inner edge
    { p: [-2.199, 0.818, -12.167], radius: 1.524 }, // starboard bell
  ],
  lights: [
    // steady nav lights on the outboard faces of the sponsons (the beam extremity, x = +-4.91)
    { p: [7.858, -0.476, -1.27], color: 'red', mirrorX: true, mirrorColor: 'green', size: 0.4 },
    // anti-collision strobes: dorsal spine between the radiators, keel; alternating flashes
    { p: [0, 3.095, -1.587], color: 'white', size: 0.4, blink: { period: 1.3, duty: 0.1 } },
    { p: [0, -4.159, -2.381], color: 'white', size: 0.4, blink: { period: 1.3, duty: 0.1, phase: 0.5 } },
    // steady white stern light on the upper aft chamfer of the engine block, above the bells
    { p: [0, 2.587, -8.286], color: 'white', size: 0.3 },
  ],
  anchors: {
    muzzlePort: { p: [6.754, -0.81, 7.937], dir: [0, 0, 1] },
    muzzleStbd: { p: [-6.754, -0.81, 7.937], dir: [0, 0, 1] },
    recoilThrusterPort: { p: [6.881, -0.198, -5.508], dir: [0, 0, -1], radius: 0.651 },
    recoilThrusterStbd: { p: [-6.881, -0.198, -5.508], dir: [0, 0, -1], radius: 0.651 },
  },
};
