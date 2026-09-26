// draft
export const meta = { name: 'Drover-class civil transport', designation: 'CT-4', blurb: 'draft' };
export const asset = {
  glb: './assets/ships/freighter.glb', generator: 'tripo3d/p2/image-to-3d',
  concept: './assets/concepts/freighter.webp', beauty: './assets/concepts/freighter-beauty.webp',
  rotate: [0, 0, 0],
  length: 30.88,
  detail: { set: 'hull', tile: 3, normalStrength: 0.6, roughAmount: 0.5, cavity: 0.5 },
  materials: { '*': { envMapIntensity: 1.0 } },
  engines: [
    { p: [1.866, -0.513, -15.44], radius: 0.953 },
    { p: [-1.725, -0.514, -15.44], radius: 0.955 },
  ],
  lights: [],
  anchors: {},
};
export const variants = {
  cargo: {},
  troops: {
    glb: './assets/ships/freighter-troops.glb',
    concept: './assets/concepts/freighter-troops.webp', beauty: './assets/concepts/freighter-troops-beauty.webp',
    length: 30.69,
  },
};
