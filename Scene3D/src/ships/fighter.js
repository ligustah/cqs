// Fighter F-402 — generated with fal (Tripo H3.1 multiview, see pipeline/fal-pipeline.json).
// Re-detailed at true size for the 70,000 m^3 slot: the concept was regenerated as a 71 m heavy
// fighter with a crew of about 40 (multi-deck bridge glazing band, rows of ~1 m windows on four
// decks, 2 x 1 m crew hatches, ~5 m plating repeat, ~20 m railgun barrels), then reconstructed.
// Anchors were measured on the GLB in the centred ship frame (rotate -> length -> centre),
// metres, bow +Z, dorsal +Y, port +X (the hull number is on both flanks; the concept's
// front-left view shows the port side).
// - length 71.712 m gives an envelope of 44.67 x 21.85 x 71.71 m = 70,000 m^3 (1 slot), so the
//   class volume correction is 1.00. The beam is set by the sponsons' outboard faces (x = +-22.33),
//   the height by the dorsal whip antenna (y = +10.93) and the keel strip (y = -10.93).
// - Main drive: two fusion bells in the armoured stern block, the only main drive. Centres are
//   circle fits of the inner wall over the outer 3.3 m of the bell (port 5.632 / 0.355,
//   starboard -5.616 / 0.350: symmetric to 16 mm, so one mirrored entry). Exit plane at the aft
//   face of the lip (z = -35.856); inner wall r 4.10 at the exit, 3.55 at 4.0 m deep, then the
//   bell closes steeply onto a throat plate (r ~2.0 at 4.6 m) round a central hub (r 1.05).
// - Secondary drive: each flank sponson ends in a small drive bell coaxial with its railgun.
//   Circle fits of the exit lip's inner edge: port (19.359, -3.588), starboard (-19.356, -3.602),
//   so one mirrored entry. Exit rim z = -18.045, inner wall r 1.23 at the exit, 1.02 at 0.6 m,
//   0.89 at 1.05 m, throat plate 1.2 m deep. The railgun muzzles are recorded as anchors.
export const meta = {
  name: 'Petrel-class fighter', designation: 'F-402', crew: 'about 40',
  blurb: 'Heavy space-superiority fighter: a faceted armoured pod with a multi-deck bridge glazing band, twin fusion bells in an armoured stern block and a 20 m railgun on each flank sponson, each sponson ending in a small secondary drive bell.',
};
export const asset = {
  glb: './assets/ships/fighter.glb', generator: 'tripo3d/h3.1/multiview-to-3d',
  concept: './assets/concepts/fighter.webp', beauty: './assets/concepts/fighter-beauty.webp',
  rotate: [0, -90, 0],
  length: 71.712,
  livery: 'dark',
  crease: 35, // faceted armour panels shade flat; bells and barrels (<12 deg per segment) stay smooth
  detail: { set: 'hull', tile: 6, normalStrength: 0.6, roughAmount: 0.5, cavity: 0.8 },
  materials: { '*': { envMapIntensity: 1.0 } },
  engines: [
    // twin fusion bells, exit plane at the aft face of the lip (z = -35.856)
    // depth / throat / wall: minimum vertex radius per 0.2 m slice round the fitted axis
    { p: [5.624, 0.352, -35.856], radius: 4.08, mirrorX: true, depth: 4.65, throat: 2.0,
      wall: [[0.8, 4.0], [1.8, 3.89], [2.8, 3.72], [3.8, 3.58], [4.2, 2.85], [4.4, 2.7]] },
    // secondary drive bells at the aft end of each flank sponson (exit rim z = -18.045)
    { p: [19.358, -3.595, -18.045], radius: 1.22, mirrorX: true, depth: 1.15, throat: 0.85,
      wall: [[0.3, 1.16], [0.6, 1.02], [0.9, 0.9]] },
  ],
  lights: [
    // steady sidelights on the outboard face of each sponson (beam extremity, x = +-22.32)
    { p: [22.52, -4.0, -5.0], color: 'red', mirrorX: true, mirrorColor: 'green', size: 0.4 },
    // anti-collision strobes: dorsal spine between the radiators (y = 7.22), keel strip (y = -10.83); alternating
    { p: [0, 7.42, -9.0], color: 'white', size: 0.4, blink: { period: 1.3, duty: 0.1 } },
    { p: [0, -11.03, 0], color: 'white', size: 0.4, blink: { period: 1.3, duty: 0.1, phase: 0.5 } },
    // steady white stern light on the aft face of the stern block between and above the bells (z = -26.04)
    { p: [0, 5.0, -26.24], color: 'white', size: 0.4 },
  ],
  anchors: {
    muzzlePort: { p: [19.37, -3.838, 18.666], dir: [0, 0, 1] },
    muzzleStbd: { p: [-19.433, -3.859, 18.67], dir: [0, 0, 1] },
  },
};
