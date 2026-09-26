// Corvette K-214 — generated with fal (see pipeline/fal-pipeline.json).
// Anchors were measured on the GLB in the centred ship frame (rotate -> length -> centre),
// then rescaled with the fleet to 1 slot = 3,200 m^3 (5 slots = 16,000 m^3 envelope).
// The mesh is not exactly mirror-symmetric (main-hull nozzles sit ~6 cm to starboard),
// so port and starboard anchors are listed explicitly.
export const meta = {
  name: 'Warden-class corvette', designation: 'K-214', crew: 'about 25',
  blurb: 'Armoured escort corvette with four bow torpedo tubes, two twin-barrel dorsal turrets and outrigger drive pods.',
};
export const asset = {
  glb: './assets/ships/corvette.glb', generator: 'tripo3d/p2/image-to-3d',
  concept: './assets/concepts/corvette.webp', beauty: './assets/concepts/corvette-beauty.webp',
  rotate: [0, -90, 0],
  length: 38.098,
  crease: 35,
  detail: { set: 'hull', tile: 6, normalStrength: 1.0, roughAmount: 0.5, cavity: 0.4 },
  materials: { '*': { envMapIntensity: 1.0 } },
  engines: [
    // main hull: four nozzles at the corners of the stern frame (exit plane z = -12)
    { p: [4.557, -2.172, -19.049], radius: 0.857 },
    { p: [-4.761, -2.172, -19.049], radius: 0.857 },
    { p: [4.556, -5.758, -19.049], radius: 0.857 },
    { p: [-4.761, -5.756, -19.049], radius: 0.857 },
    // outrigger drive pods
    { p: [10.378, -6.108, -12.144], radius: 1.302 },
    { p: [-10.359, -6.108, -12.144], radius: 1.302 },
  ],
  lights: [
    // sidelights on the outboard faces of the drive pods (beam extremities), steady
    { p: [12.167, -5.08, 0], color: 'red', size: 0.4 },
    { p: [-12.131, -5.08, 0], color: 'green', size: 0.4 },
    // anti-collision strobes: cap of the sensor-mast pole (highest solid point) and keel
    { p: [-0.079, 7.937, -7.302], color: 'white', size: 0.4, blink: { period: 1.4, duty: 0.1 } },
    { p: [-0.102, -7.961, -3.572], color: 'white', size: 0.4, blink: { period: 1.4, duty: 0.1, phase: 0.5 } },
    // stern light on the upper stern frame, steady
    { p: [-0.102, -1.46, -17.684], color: 'white', size: 0.3 },
  ],
  anchors: {},
};
