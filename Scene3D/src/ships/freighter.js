// Civil ship CT-4 / CT-7 (Drover class): generated with fal (Tripo H3.1 multiview).
// Forward crew module, a truss keel carrying the payload, an aft reactor block
// with two engine bells and four radiator panels. The same hull carries
// containers (CT-4 cargo) or habitat cylinders (CT-7 troop transport).
//
// Scale: the game's civil ship is 4 hangar slots (UnitEnum getSize() = 4), so
// EACH variant's envelope is 4 x 3,200 = 12,800 m^3. The troop variant's
// bulkier habitat cylinders make its envelope wider and taller than the cargo
// ship's, so at exactly 4 slots it comes out shorter: 48.4 m (cargo) versus
// 42.9 m (troops). Every anchor below is in these real metres (bow +Z, dorsal
// +Y, port +X), measured on the GLB after rotate -> scale -> centre.
export const meta = {
  name: 'Drover-class civil transport', designation: 'CT-4 / CT-7', crew: 'about 10 (troop variant: + about 600 troops)',
  blurb: 'Civil workhorse: a forward crew module and an aft reactor block with two fusion bells and radiator panels, joined by a truss keel that carries twenty-foot containers (CT-4) or pressurised habitat cylinders for about 600 troops (CT-7).',
};

const STROBE = { period: 1.3, duty: 0.1 };

export const asset = {
  glb: './assets/ships/freighter.glb', generator: 'tripo3d/h3.1/multiview-to-3d',
  concept: './assets/concepts/freighter.webp', beauty: './assets/concepts/freighter-beauty.webp',
  rotate: [0, -90, 0],
  length: 48.4, // 48.4 x 18.95 x 13.96 m = 12,803 m^3: 4 slots, scale correction 0.9998
  livery: 'civil',
  crease: 35,
  detail: { set: 'hull', tile: 6, normalStrength: 0.9, roughAmount: 0.5, cavity: 0.4 },
  // two main bells, exit rim at z -24.2, inner lip r 2.01 (outer 2.16)
  engines: [
    { p: [2.826, -0.486, -24.15], radius: 2.0, mirrorX: true },
  ],
  lights: [
    // port / starboard: forward edge frame of the outboard radiator face (the beam extremity), near its top
    { p: [9.483, 0.3, -9.6], color: 'red', size: 0.4 },
    { p: [-9.491, 0.3, -9.6], color: 'green', size: 0.4 },
    // anti-collision strobes: reactor block top and belly, alternating
    { p: [0, 3.61, -10.0], color: 'white', size: 0.4, blink: { ...STROBE } },
    { p: [0, -4.74, -9.6], color: 'white', size: 0.4, blink: { ...STROBE, phase: 0.5 } },
    // stern light: aft face of the reactor block below the bell pair (clear of the centre slot)
    { p: [0.1, -3.5, -18.76], color: 'white', size: 0.4 },
  ],
  anchors: {},
};

export const variants = {
  cargo: {},
  troops: {
    glb: './assets/ships/freighter-troops.glb',
    concept: './assets/concepts/freighter-troops.webp', beauty: './assets/concepts/freighter-troops-beauty.webp',
    rotate: [0, -90, 0],
    length: 42.9, // 42.9 x 19.04 x 15.71 m = 12,836 m^3: 4 slots like the cargo ship, correction 0.9991 (built 42.86 m)
    // exit rim at z -21.45, inner lip r 1.55 (outer 1.76)
    engines: [
      { p: [2.72, -1.65, -21.40], radius: 1.52, mirrorX: true },
    ],
    lights: [ // same placement rules as the cargo ship, measured on this hull
      { p: [9.547, -0.8, -9.6], color: 'red', size: 0.4 },
      { p: [-9.549, -0.8, -9.6], color: 'green', size: 0.4 },
      { p: [0, 1.61, -9.6], color: 'white', size: 0.4, blink: { ...STROBE } },
      { p: [0, -5.83, -9.5], color: 'white', size: 0.4, blink: { ...STROBE, phase: 0.5 } },
      { p: [0, -4.3, -17.83], color: 'white', size: 0.4 },
    ],
  },
};
