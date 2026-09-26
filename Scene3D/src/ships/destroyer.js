// Destroyer DD-12 — generated with fal (see pipeline/fal-pipeline.json).
// Draft: anchors being measured.
export const meta = {
  name: 'Bastion-class destroyer', designation: 'DD-12',
  blurb: 'Heavy line destroyer built around a spinal mass driver in an armoured octagonal bow block, with twin-gun dorsal turrets, a stepped command tower and six fusion bells in the stern.',
};
export const asset = {
  glb: './assets/ships/destroyer.glb', generator: 'tripo3d/p2/image-to-3d',
  concept: './assets/concepts/destroyer.webp', beauty: './assets/concepts/destroyer-beauty.webp',
  rotate: [0, -90, 0],
  length: 38.3,
  crease: 35,
  detail: { set: 'armor', tile: 4, normalStrength: 1.0, roughAmount: 0.5, cavity: 0.5 },
  materials: { '*': { envMapIntensity: 1.0 } },
  engines: [
    { p: [5.057, -1.224, -19.15], radius: 1.19 },
    { p: [-0.517, -0.810, -19.15], radius: 1.19 },
    { p: [-5.129, -1.235, -19.15], radius: 1.19 },
    { p: [5.123, -4.368, -19.15], radius: 1.19 },
    { p: [-0.534, -5.262, -19.15], radius: 1.19 },
    { p: [-5.108, -4.377, -19.15], radius: 1.19 },
  ],
  lights: [
    { p: [7.41, -3.0, -3.80], color: 'red', mirrorX: true, mirrorColor: 'green', size: 0.5 },
    { p: [0, 4.82, -4.8], color: 'white', size: 0.5, blink: { period: 1.4, duty: 0.1 } },
    { p: [0, -7.28, -2.0], color: 'white', size: 0.5, blink: { period: 1.4, duty: 0.1, phase: 0.5 } },
    { p: [0, 4.45, -9.10], color: 'white', size: 0.4 },
  ],
  anchors: {},
};
