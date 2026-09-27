// Civil ship CT-4 / CT-7 (Drover class): generated with fal (Tripo H3.1 multiview).
// Forward crew module, a truss keel carrying the payload, an aft reactor block
// with two engine bells and four radiator panels. The same hull carries
// containers (CT-4 cargo) or habitat cylinders (CT-7 troop transport).
//
// Scale: the game's civil ship is 4 hangar slots (UnitEnum getSize() = 4), so
// EACH variant's envelope is 4 x 70,000 = 280,000 m^3. Both hulls were regenerated at true size
// (20-ft ISO containers, ~1 m windows, 2 m hatches) and reconstructed with near-identical
// envelopes, so at exactly 4 slots they come out about the same length: 132.2 m (cargo) and
// 131.8 m (troops). Every anchor below is in these real metres (bow +Z, dorsal
// +Y, port +X), measured on the GLB after rotate -> scale -> centre.
// Troop capacity from game data: UnitEnum TRANSPORTER groundTransport = 750, counted in the
// game's ground-unit size units (UnitMap.getGroundUnitSize: infantry 1, vehicles 3, aircraft 4),
// not people.
export const meta = {
  name: 'Drover-class civil transport', designation: 'CT-4 / CT-7', crew: 'about 80 (troop variant: ground-unit capacity 750; infantry 1, vehicles 3, aircraft 4)',
  blurb: 'Civil workhorse: a forward crew module and an aft reactor block with two fusion bells and radiator panels, joined by a truss keel that carries twenty-foot containers (CT-4) or pressurised habitat cylinders (CT-7 troop transport: ground-unit capacity 750, the game\'s groundTransport).',
};

const STROBE = { period: 1.3, duty: 0.1 };

export const asset = {
  glb: './assets/ships/freighter.glb', generator: 'tripo3d/h3.1/multiview-to-3d',
  concept: './assets/concepts/freighter.webp', beauty: './assets/concepts/freighter-beauty.webp',
  rotate: [0, -90, 0],
  length: 132.16, // 132.2 x 51.5 x 41.2 m = 280,000 m^3: 4 slots
  livery: 'civil',
  crease: 35,
  detail: { set: 'hull', tile: 6, normalStrength: 0.9, roughAmount: 0.5, cavity: 0.4 },
  // two main bells side by side: exit rim at z -66.08, inner lip r 5.0 (outer 5.65)
  engines: [
    // depth / throat / wall ray-cast on the GLB: throat dish ~5.6 m in, an inner ring at r 3.0-3.3 sits ~1.5 m in
    { p: [7.13, -1.87, -66.08], radius: 5.0, mirrorX: true, depth: 5.5, throat: 2.6, wall: [[1.0, 4.97], [2.8, 4.64], [4.4, 4.31], [4.7, 3.97]] },
  ],
  lights: [
    // port / starboard: forward edge of the outboard radiator face (the beam extremity), near its top
    { p: [25.8, 0.3, -27.6], color: 'red', size: 0.4 },
    { p: [-25.8, 0.3, -27.6], color: 'green', size: 0.4 },
    // anti-collision strobes: reactor block top and belly, alternating
    { p: [0, 8.3, -26], color: 'white', size: 0.4, blink: { ...STROBE } },
    { p: [0, -15.45, -45], color: 'white', size: 0.4, blink: { ...STROBE, phase: 0.5 } },
    // stern light: aft face of the reactor block below the bell pair
    { p: [0, -9, -50.55], color: 'white', size: 0.4 },
  ],
  anchors: {},
};

export const variants = {
  cargo: {},
  troops: {
    gameId: 'TRANSPORTER', // UnitEnum TRANSPORTER (the cargo ship is FREIGHTER)
    glb: './assets/ships/freighter-troops.glb',
    concept: './assets/concepts/freighter-troops.webp', beauty: './assets/concepts/freighter-troops-beauty.webp',
    rotate: [0, -90, 0],
    length: 131.81, // 131.8 x 51.9 x 40.9 m = 280,000 m^3: 4 slots like the cargo ship
    // two bells side by side: exit rim at z -65.92, inner lip r 5.15 (outer 5.69); an inner
    // converging nozzle (lip r 3.0 about 0.4 m in) narrows to the throat ~8.4 m in
    engines: [
      { p: [6.78, -1.565, -65.915], radius: 5.15, mirrorX: true, depth: 8.3, throat: 1.6, wall: [[0.45, 3.0], [2.6, 2.7], [6.4, 2.36], [7.6, 2.02]] },
    ],
    lights: [ // same placement rules as the cargo ship, measured on this hull
      { p: [26.12, 0.3, -28], color: 'red', size: 0.4 },
      { p: [-26.07, 0.3, -28], color: 'green', size: 0.4 },
      { p: [0, 8.44, -27], color: 'white', size: 0.4, blink: { ...STROBE } },
      { p: [0, -15.22, -44], color: 'white', size: 0.4, blink: { ...STROBE, phase: 0.5 } },
      { p: [0, -9, -51.25], color: 'white', size: 0.4 },
    ],
  },
};
