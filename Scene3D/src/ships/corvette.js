// Corvette K-214 — generated with fal (see pipeline/fal-pipeline.json).
// Anchors were measured on the GLB in the centred ship frame (rotate -> length -> centre).
// The mesh is not exactly mirror-symmetric (main-hull nozzles sit ~6 cm to starboard),
// so port and starboard anchors are listed explicitly.
export const meta = {
  name: 'Warden-class corvette', designation: 'K-214',
  blurb: 'Armoured escort corvette with four bow torpedo tubes, two twin-barrel dorsal turrets and outrigger drive pods.',
};
export const asset = {
  glb: './assets/ships/corvette.glb', generator: 'tripo3d/p2/image-to-3d',
  concept: './assets/concepts/corvette.webp', beauty: './assets/concepts/corvette-beauty.webp',
  rotate: [0, -90, 0],
  length: 24,
  crease: 35,
  detail: { set: 'hull', tile: 3, normalStrength: 1.0, roughAmount: 0.5, cavity: 0.4 },
  materials: { '*': { envMapIntensity: 1.0 } },
  engines: [
    // main hull: four nozzles at the corners of the stern frame (exit plane z = -12)
    { p: [2.871, -1.368, -12.0], radius: 0.54 },
    { p: [-2.999, -1.368, -12.0], radius: 0.54 },
    { p: [2.870, -3.627, -12.0], radius: 0.54 },
    { p: [-2.999, -3.626, -12.0], radius: 0.54 },
    // outrigger drive pods
    { p: [6.538, -3.848, -7.65], radius: 0.82 },
    { p: [-6.526, -3.848, -7.65], radius: 0.82 },
  ],
  lights: [
    // sidelights on the outboard faces of the drive pods (beam extremities), steady
    { p: [7.665, -3.2, 0.0], color: 'red', size: 0.4 },
    { p: [-7.642, -3.2, 0.0], color: 'green', size: 0.4 },
    // anti-collision strobes: cap of the sensor-mast pole (highest solid point) and keel
    { p: [-0.05, 5.0, -4.6], color: 'white', size: 0.4, blink: { period: 1.4, duty: 0.1 } },
    { p: [-0.064, -5.015, -2.25], color: 'white', size: 0.4, blink: { period: 1.4, duty: 0.1, phase: 0.5 } },
    // stern light on the upper stern frame, steady
    { p: [-0.064, -0.92, -11.14], color: 'white', size: 0.3 },
  ],
  anchors: {},
};
