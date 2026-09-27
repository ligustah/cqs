// Fighter F-402 — generated with fal (Tripo H3.1 multiview, see pipeline/fal-pipeline.json).
// v5 re-detail at true size for the 70,000 m^3 slot: the approved v4 concept was edited
// (nano-banana-pro/edit) so its human-scale details share the fleet's absolute scale. The
// faceted glass canopy became a low bridge block with a band of ~0.8 m panes, the big dorsal
// hatches became plain plating with ~1.3 m grab bars, and the flank keeps a row of ~0.7 m
// ports. A 6-view turnaround of that image was reconstructed as front / port / stern / starboard.
// Anchors were measured on the GLB in the centred ship frame (rotate -> length -> centre),
// metres, bow +Z, dorsal +Y, port +X (the hull number is on both flanks; the concept's
// front-left view shows the port side).
// - length 71.712 m gives an envelope of 46.92 x 20.96 x 71.71 m = 70,516 m^3, so the class
//   volume correction is 0.9976 (the ship is drawn 71.54 m long). The beam is set by the
//   sponsons' outboard faces (x = +-23.46), the height by the dorsal whip antenna (y = +10.48)
//   and the keel plating just forward of midships (y = -10.48).
// - Main drive: two fusion bells in the armoured stern block, the only main drive. Centres are
//   circle fits of the inner wall over the outer 3.5 m of each bell (port 5.934 / -0.032,
//   starboard -5.830 / -0.047: 10 cm apart, so two entries). Exit plane at the aft face of the
//   lip (z = -35.856); inner wall r 3.55 at the exit, 3.26 at 4.4 m deep, then a throat plate at
//   4.6 m with a 1.95 m opening onto a recessed hub.
// - Secondary drive: each flank sponson ends in a small drive bell coaxial with its railgun.
//   Circle fits of the exit lip's inner edge: port (20.133, -3.234), starboard (-20.021,
//   -3.238). Exit rim z = -16.64, inner wall r 1.37 at the exit, 1.22 at 0.6 m, 1.0 at 2.0 m,
//   throat plate 2.4 m deep. The railgun muzzles are recorded as anchors.
export const meta = {
  name: 'Petrel-class fighter', designation: 'F-402', crew: 'about 40',
  blurb: 'Heavy space-superiority fighter: a faceted armoured pod with a low bridge block glazed in a band of small panes, twin fusion bells in an armoured stern block and a railgun on each flank sponson, each sponson ending in a small secondary drive bell.',
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
    { p: [5.934, -0.032, -35.856], radius: 3.55, depth: 4.6, throat: 1.95,
      wall: [[0.2, 3.54], [1.0, 3.48], [2.0, 3.41], [3.0, 3.37], [4.2, 3.26], [4.4, 3.26]] },
    { p: [-5.830, -0.047, -35.856], radius: 3.55, depth: 4.6, throat: 1.95,
      wall: [[0.2, 3.53], [1.0, 3.48], [2.0, 3.40], [3.0, 3.35], [4.2, 3.25], [4.4, 3.26]] },
    // secondary drive bells at the aft end of each flank sponson (exit rim z = -16.64)
    { p: [20.133, -3.234, -16.643], radius: 1.37, depth: 2.4, throat: 0.9,
      wall: [[0.3, 1.31], [0.6, 1.22], [1.05, 1.16], [1.65, 1.13], [2.0, 1.0]] },
    { p: [-20.021, -3.238, -16.638], radius: 1.37, depth: 2.4, throat: 0.9,
      wall: [[0.3, 1.33], [0.6, 1.25], [1.05, 1.18], [1.65, 1.11], [2.0, 1.04]] },
  ],
  lights: [
    // steady sidelights on the outboard face of each sponson (beam extremity, x = +-23.19 there)
    { p: [23.39, -3.9, -4.0], color: 'red', mirrorX: true, mirrorColor: 'green', size: 0.4 },
    // anti-collision strobes: dorsal spine between the radiators (y = 6.79), keel (y = -10.07); alternating
    { p: [0, 6.99, -9.0], color: 'white', size: 0.4, blink: { period: 1.3, duty: 0.1 } },
    { p: [0, -10.27, 0], color: 'white', size: 0.4, blink: { period: 1.3, duty: 0.1, phase: 0.5 } },
    // steady white stern light on the aft face of the stern block between the bells (z = -25.89)
    { p: [0, 2.5, -26.09], color: 'white', size: 0.4 },
  ],
  anchors: {
    muzzlePort: { p: [20.17, -3.683, 17.851], dir: [0, 0, 1] },
    muzzleStbd: { p: [-20.114, -3.635, 17.864], dir: [0, 0, 1] },
  },
};
