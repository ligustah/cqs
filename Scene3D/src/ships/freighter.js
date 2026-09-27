// Civil ship CT-4 / CT-7 (Drover class): generated with fal (Tripo H3.1 multiview).
// Forward crew module, a truss keel carrying the payload, an aft reactor block
// with two engine bells and four radiator panels. The same hull carries
// containers (CT-4 cargo) or habitat cylinders (CT-7 troop transport).
//
// Scale: the game's civil ship is 4 hangar slots (UnitEnum getSize() = 4), so
// EACH variant's envelope is 4 x 70,000 = 280,000 m^3. v5 re-drew the small details of both hulls for
// a 132 m ship (nano-banana-pro/edit: rows of ~1 m ports one per deck, thin 1 m rails, small RCS quads,
// the big crew-module door removed; the troop habitats carry decks of tiny portholes) and rebuilt both
// meshes (Tripo H3.1 multiview, 4096 textures). At exactly 4 slots they come out 134.1 m (cargo) and
// 128.8 m (troops: its habitat block and radiators reconstructed a little bulkier). The troop hull's
// port "CT-7" (a bent 7) and a stain on its starboard C were repaired by texture re-projection.
// Every anchor below is in these real metres (bow +Z, dorsal +Y, port +X), measured on the GLB
// after rotate -> scale -> centre.
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
  rotate: [0, -90, 0], // bow +Z, dorsal +Y, port +X
  length: 134.12, // 134.1 x 54.7 x 38.2 m = 280,000 m^3: 4 slots (scaleCorrection ~1.000)
  livery: 'civil',
  crease: 35,
  detail: { set: 'hull', tile: 6, normalStrength: 0.9, roughAmount: 0.5, cavity: 0.4 },
  // two main bells side by side: exit rim at z -67.05, centres x +-7.74 y 0.1, inner lip r 4.75 (outer ~5.35)
  engines: [
    // depth / throat / wall ray-cast on the GLB: a converging ring (r ~3.3) sits ~2.3 m in, the throat plate
    // (r ~1.6) ~6.0 m in
    { p: [7.74, 0.1, -67.05], radius: 4.75, mirrorX: true, depth: 6.0, throat: 1.6, wall: [[0.47, 4.72], [1.12, 4.45], [2.12, 4.16], [2.4, 3.3], [3.38, 2.38], [4.39, 2.08], [5.45, 1.78]] },
  ],
  lights: [
    // port / starboard: forward edge of the outboard radiator face (the beam extremity), near its top
    { p: [27.1, 2.0, -31.0], color: 'red', size: 0.4 },
    { p: [-27.1, 2.0, -31.0], color: 'green', size: 0.4 },
    // anti-collision strobes: reactor block top and belly, alternating
    { p: [0, 10.35, -29], color: 'white', size: 0.4, blink: { ...STROBE } },
    { p: [0, -12.85, -45], color: 'white', size: 0.4, blink: { ...STROBE, phase: 0.5 } },
    // stern light: aft face of the reactor block below the bell pair
    { p: [0, -9.5, -55.05], color: 'white', size: 0.4 },
  ],
  anchors: {},
};

export const variants = {
  cargo: {},
  troops: {
    gameId: 'TRANSPORTER', // UnitEnum TRANSPORTER (the cargo ship is FREIGHTER)
    glb: './assets/ships/freighter-troops.glb',
    concept: './assets/concepts/freighter-troops.webp', beauty: './assets/concepts/freighter-troops-beauty.webp',
    rotate: [0, -90, 0], // bow +Z, dorsal +Y, port +X
    length: 128.84, // 128.8 x 57.7 x 37.7 m = 280,000 m^3: 4 slots like the cargo ship (scaleCorrection ~1.000)
    // two bells side by side: exit rim at z -64.42, centres x +-8.54 y -0.05, inner lip r 5.65 (outer ~6.4);
    // the wall narrows to r 4.6 ~6 m in, an inner converging nozzle (lip r ~2.5 ~4.5 m in) leads to the
    // throat plate (r ~1.4-1.8) ~7.4 m in
    engines: [
      { p: [8.54, -0.05, -64.42], radius: 5.65, mirrorX: true, depth: 7.3, throat: 1.6, wall: [[0.5, 5.62], [3.6, 5.3], [5.4, 4.94], [6.1, 4.55], [6.8, 3.3], [7.0, 1.77]] },
    ],
    lights: [ // same placement rules as the cargo ship, measured on this hull
      { p: [29.1, 2.0, -28.5], color: 'red', size: 0.4 },
      { p: [-29.1, 2.0, -28.5], color: 'green', size: 0.4 },
      { p: [0, 10.3, -27], color: 'white', size: 0.4, blink: { ...STROBE } },
      { p: [0, -13.02, -44], color: 'white', size: 0.4, blink: { ...STROBE, phase: 0.5 } },
      { p: [0, -10, -53.25], color: 'white', size: 0.4 },
    ],
  },
};
