// F-402 fighter — generated with fal (see pipeline/fal-pipeline.json). WIP
export const meta = { name: 'Kestrel-class fighter', designation: 'F-402', blurb: 'Single-seat space-superiority fighter.' };
export const asset = {
  glb: './assets/ships/fighter.glb', generator: 'tripo3d/p2/image-to-3d',
  concept: './assets/concepts/fighter.webp', beauty: './assets/concepts/fighter-beauty.webp',
  rotate: [0, 0, 0],
  length: 15.6,
  crease: 35,
  detail: { set: 'hull', tile: 4, normalStrength: 0.8, roughAmount: 0.5, cavity: 0.4 },
  materials: { '*': { envMapIntensity: 1.0 } },
  engines: [
    { p: [1.383, 0.515, -7.775], radius: 0.96 },
    { p: [-1.385, 0.515, -7.665], radius: 0.96 },
  ],
  lights: [
    { p: [4.95, -0.30, -0.80], color: 'red', mirrorX: true, mirrorColor: 'green', size: 0.3 },
    { p: [0, 1.95, -1.0], color: 'white', size: 0.35, blink: { period: 1.3, duty: 0.1 } },
    { p: [0, -2.62, -1.5], color: 'white', size: 0.35, blink: { period: 1.3, duty: 0.1, phase: 0.5 } },
    { p: [0, 1.63, -5.22], color: 'white', size: 0.25 },
  ],
  anchors: {},
};
export const variants = {
  t4: { detail: { set: 'hull', tile: 4, normalStrength: 1.2, roughAmount: 0.6, cavity: 0.6 } },
};
