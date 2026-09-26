// draft 2
const ring = (c, r, color = 'white') => [0, 90, 180, 270].map((a) => ({ p: [c[0] + r * Math.cos(a * Math.PI / 180), c[1] + r * Math.sin(a * Math.PI / 180), c[2]], color: 'amber', size: 0.1 })).concat([{ p: c, color, size: 0.1 }]);
export const meta = { name: 'Drover-class civil transport', designation: 'CT-4', blurb: 'draft' };
const ENG_C = [
  { p: [1.866, -0.513, -15.44], radius: 0.953 },
  { p: [-1.725, -0.514, -15.44], radius: 0.955 },
];
const ENG_T = [
  { p: [1.771, -0.610, -15.305], radius: 1.054 },
  { p: [-1.766, -0.678, -15.155], radius: 1.054 },
];
const LIGHTS_C = [
  { p: [5.85, -0.10, -6.45], color: 'red', mirrorX: true, mirrorColor: 'green', size: 0.35 },
  { p: [-0.2, 1.94, -5.5], color: 'white', size: 0.35, blink: { period: 1.4, duty: 0.1 } },
  { p: [0.1, -2.80, -11.1], color: 'white', size: 0.35, blink: { period: 1.4, duty: 0.1, phase: 0.5 } },
  { p: [0.07, 1.1, -11.82], color: 'white', size: 0.3 },
];
const LIGHTS_T = [
  { p: [5.84, -0.15, -6.45], color: 'red', size: 0.35 },
  { p: [-5.80, -0.15, -6.7], color: 'green', size: 0.35 },
  { p: [0.3, 1.87, -5.7], color: 'white', size: 0.35, blink: { period: 1.4, duty: 0.1 } },
  { p: [0.07, -3.22, -11.0], color: 'white', size: 0.35, blink: { period: 1.4, duty: 0.1, phase: 0.5 } },
  { p: [0.07, 0.97, -12.0], color: 'white', size: 0.3 },
];
export const asset = {
  glb: './assets/ships/freighter.glb', generator: 'tripo3d/p2/image-to-3d',
  concept: './assets/concepts/freighter.webp', beauty: './assets/concepts/freighter-beauty.webp',
  rotate: [0, 0, 0],
  length: 30.88,
  detail: { set: 'hull', tile: 3, normalStrength: 0.6, roughAmount: 0.5, cavity: 0.5 },
  materials: { '*': { envMapIntensity: 1.0 } },
  engines: ENG_C,
  lights: LIGHTS_C,
  anchors: {},
};
const TROOPS = {
  glb: './assets/ships/freighter-troops.glb',
  concept: './assets/concepts/freighter-troops.webp', beauty: './assets/concepts/freighter-troops-beauty.webp',
  length: 30.69,
  engines: ENG_T,
  lights: LIGHTS_T,
};
export const variants = {
  cargo: {},
  troops: TROOPS,
  cr35: { crease: 35 },
  cr35d: { crease: 35, detail: { set: 'hull', tile: 3, normalStrength: 1.0, roughAmount: 0.6, cavity: 0.8 } },
  dbg: { engines: [], lights: [...LIGHTS_C, ...ENG_C.flatMap((e) => ring(e.p, e.radius))] },
  dbgt: { ...TROOPS, engines: [], lights: [...LIGHTS_T, ...ENG_T.flatMap((e) => ring(e.p, e.radius))] },
};
