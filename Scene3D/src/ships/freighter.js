// Civil ship CT-4 / CT-7 (Drover class) — v3 REMODEL: clean hard-surface hulls (tools/blender/hulls/freighter.py,
// one parametric script, --variant cargo|troops: common crew module, collar, reactor block and engine section,
// variant mid-body) rebuilt from measurements of the fal / Tripo H3.1 multiview blueprints, painted in texture
// space (paint.py with freighter_paint.py: light civil paint, irregular plating seams, PATINA plate tone, AO grime,
// edge wear, dark hull-number stencils, teal stripe, hazard frames) and assembled with the Blender parts kit
// (tools/blender/specs/freighter-v3.json, freighter-troops-v3.json via tools/blender/assemble.py), then
// tools/blender/hulls/freighter_extras.py: the container stacks (kit 20-ft ISO container baked onto 12-triangle
// boxes, six weathered cargo colours as material tints, so they survive the civil livery) and ~1 m port lites on
// the 3 m decks (the troop habitats' 750 berths).
// The GLBs are in the ship frame (metres, bow +Z, dorsal +Y, port +X): rotate [0, 0, 0], length = the assembled
// bbox length. Node 'hull' is the hull, 'parts_*' the kit parts, containers and port lites (hullNodes).
// Scale: the game's civil ship is 4 hangar slots (UnitEnum getSize() = 4), so EACH variant's envelope is
// 4 x 70,000 = 280,000 m^3; the pair is the carrier bay's binding load (12 of each), so both envelopes are kept
// to the blueprints' (cargo 134.1 x 54.7 x 38.2 m, troops 128.8 x 57.7 x 37.7 m): radiator fin tips set the beam,
// the mast whip and the landing-leg pads the height, the bow face and the bell lips the length.
// Engines: kit bell-L scaled to the blueprint exit radius, with the kit's engine entry (depth to the throat plate,
// throat, inner wall) times that scale. Lights: at the lenses of the kit nav-light housings.
// Troop capacity from game data: UnitEnum TRANSPORTER groundTransport = 750, counted in the game's ground-unit
// size units (UnitMap.getGroundUnitSize: infantry 1, vehicles 3, aircraft 4), not people.
// Assembled envelopes: cargo 134.12 x 54.68 x 38.16 m (bbox centre [0.0, -0.002, -0.001]), troops 128.84 x 57.74 x 37.66 m (centre [0.0, -0.001, -0.001]); coordinates below are shifted by minus the centre.
import { LIVERIES } from '../lib/livery.js';

export const meta = {
  "name": "Drover-class civil transport",
  "designation": "CT-4 / CT-7",
  "crew": "about 80 (troop variant: ground-unit capacity 750; infantry 1, vehicles 3, aircraft 4)",
  "blurb": "Civil workhorse: a forward crew module and an aft reactor block with two fusion bells, tanks and radiator panels, joined by a truss keel that carries twenty-foot containers (CT-4) or four pressurised habitat cylinders (CT-7 troop transport: ground-unit capacity 750, the game's groundTransport)."
};

const STROBE = { period: 1.3, duty: 0.1 };

export const asset = {
  glb: './assets/ships/freighter.glb',
  generator: 'tools/blender/hulls/freighter.py --variant cargo (remodel of the tripo3d/h3.1/multiview-to-3d hull) + tools/blender/assemble.py + freighter_extras.py',
  concept: './assets/concepts/freighter.webp',
  beauty: './assets/concepts/freighter-beauty.webp',
  rotate: [0, 0, 0],
  hullNodes: ['hull'],
  livery: { ...LIVERIES.civil, gain: 0.05, glassGlow: [0.06, 0.055, 0.046], glassLit: 0.45 }, // civil grey; the remodel paint is lighter than the generated textures (gain 0.05); lit cabins behind the ports
  detail: { set: 'hull', tile: 6, normalStrength: 0.6, roughAmount: 0.5, cavity: 0.2 }, // the hull carries its own seams: runtime PATINA turned down
  length: 134.122, // 134.12 x 54.68 x 38.16 m assembled (L x B x H), 4 slots
  // Two-tone zones (?livery=tone|bone, livery.js SCHEMES; ship frame, metres): the crew module (aft bulkhead z 34 to
  // the bow), the reactor block (z -34..-22.5) and the engine housings round the bells take the light paint; the
  // collar, payload truss, tanks and radiators stay the civil grey. Containers are kit parts: they keep their colours.
  liveryZones: [
    { box: [[-12.0, -14.0, 34.0], [12.0, 11.0, 67.5]] },                 // crew module
    { box: [[-14.5, -13.5, -34.2], [14.5, 13.0, -22.3]] },               // reactor block
    { box: [[1.4, -6.4, -60.5], [14.0, 6.6, -34.2]], mirrorX: true },    // engine housings (bell x 7.74, r 5.95)
  ],
  engines: [
    // main bells: bell-L x1.3571 (r 4.75)
    {p: [7.74, 0.102, -67.002], radius: 4.75, mirrorX: true, depth: 6.412, throat: 2.375, wall: [[0.916, 4.678], [1.832, 4.5], [2.748, 4.233], [3.664, 3.883], [4.58, 3.454], [5.496, 2.95]]},
  ],
  lights: [
    // steady sidelights on the top of each radiator, outboard forward corner (the beam extremity): red port, green starboard
    { p: [26.99, 3.332, -29.849], color: 'red', size: 0.4 },
    { p: [-26.99, 3.332, -29.849], color: 'green', size: 0.4 },
    // anti-collision strobes, alternating: mast housing and keel block
    { p: [1.1, 13.582, -26.699], color: 'white', size: 0.4, blink: { ...STROBE } },
    { p: [0.0, -13.028, -39.999], color: 'white', size: 0.4, blink: { ...STROBE, phase: 0.5 } },
    // steady stern light on the aft face of the dorsal block, between the bells
    { p: [0.0, 6.002, -56.012], color: 'white', size: 0.4 },
    // v10 amber running lights: the crew module's upper walkway ledge and the top of the reactor block flanks
    { p: [9.85, 4.68, 37.0], color: 'amber', size: 0.3, mirrorX: true },
    { p: [9.85, 4.68, 53.0], color: 'amber', size: 0.3, mirrorX: true },
    { p: [13.55, 4.6, -32.05], color: 'amber', size: 0.3, mirrorX: true },
    { p: [13.45, 4.6, -24.45], color: 'amber', size: 0.3, mirrorX: true },
  ],
  anchors: {
    // flat hull faces, measured on the remodelled hull by ray casts (0.5 m grid along -normal, plane refit;
    // flat = share of samples within 0.15 m of the plane)
    surfaces: {
      'cm-flank-port': { centre: [10.28, -4.4, 45.0], normal: [1.0, -0.005, 0.0], u: [0.0, 0.0, 1.0], width: 18.0, height: 8.0, flat: 0.95 }, // crew-module flank, decks 2-4 (port rows every 1.6 m, teal stripe at y 0)
      'cm-flank-stbd': { centre: [-10.28, -4.4, 45.0], normal: [-1.0, -0.005, 0.0], u: [0.0, 0.0, -1.0], width: 18.0, height: 8.0, flat: 0.95 },
      'cm-ledge-port': { centre: [9.85, 4.6, 45.0], normal: [0.0, 1.0, 0.0], u: [0.0, 0.0, 1.0], width: 18.0, height: 0.8, flat: 1.0 }, // upper-tier walkway ledge (rails)
      'cm-ledge-stbd': { centre: [-9.85, 4.6, 45.0], normal: [0.0, 1.0, 0.0], u: [0.0, 0.0, 1.0], width: 18.0, height: 0.8, flat: 1.0 },
      'cm-roof': { centre: [0.0, 10.43, 46.0], normal: [0.0, 1.0, 0.005], u: [0.0, -0.005, 1.0], width: 7.0, height: 10.0, flat: 0.81 }, // raised roof deck (hatches)
      'reactor-flank-port': { centre: [13.42, 2.0, -28.25], normal: [1.0, -0.007, 0.014], u: [-0.014, 0.0, 1.0], width: 9.0, height: 6.0, flat: 0.99 }, // reactor block flank (CT-4 stencil)
      'reactor-flank-stbd': { centre: [-13.42, 2.0, -28.25], normal: [-1.0, -0.007, 0.014], u: [-0.014, 0.0, -1.0], width: 9.0, height: 6.0, flat: 0.99 },
      'reactor-roof': { centre: [0.0, 12.57, -26.71], normal: [0.0, 0.995, -0.095], u: [0.0, 0.095, 0.995], width: 8.0, height: 4.0, flat: 0.0 },
      'radiator-top-port': { centre: [24.52, 3.1, -38.15], normal: [0.0, 1.0, 0.0], u: [0.0, 0.0, 1.0], width: 10.0, height: 4.0, flat: 1.0 }, // radiator panel top edge
      'radiator-top-stbd': { centre: [-24.52, 3.1, -38.15], normal: [0.0, 1.0, 0.0], u: [0.0, 0.0, 1.0], width: 10.0, height: 4.0, flat: 1.0 },
    },
  },
};

export const variants = {
  cargo: {},
  troops: {
    gameId: 'TRANSPORTER', // UnitEnum TRANSPORTER (the cargo ship is FREIGHTER)
    glb: './assets/ships/freighter-troops.glb',
    generator: 'tools/blender/hulls/freighter.py --variant troops + tools/blender/assemble.py + freighter_extras.py',
    concept: './assets/concepts/freighter-troops.webp',
    beauty: './assets/concepts/freighter-troops-beauty.webp',
    rotate: [0, 0, 0],
    length: 128.843, // 128.84 x 57.74 x 37.66 m assembled (L x B x H), 4 slots
    // two-tone zones as on the cargo ship, at the troop hull's stations (crew module from z 31.4, reactor z -30.5..-20.5)
    liveryZones: [
      { box: [[-12.0, -14.0, 31.4], [12.0, 11.0, 64.9]] },
      { box: [[-16.6, -13.5, -30.7], [16.6, 11.2, -20.3]] },
      { box: [[1.6, -7.2, -58.0], [15.6, 7.2, -30.7]], mirrorX: true },
      // the upper habitat pair (HAB x +-4.6, y 5.5, r 4.6) above the girder tops (y 2.0); the lower pair stays grey
      { box: [[-9.4, 2.1, -20.3], [9.4, 10.4, 24.0]] },
    ],
    engines: [
      // main bells: bell-L x1.6143 (r 5.65)
      {p: [8.54, -0.049, -64.351], radius: 5.65, mirrorX: true, depth: 7.628, throat: 2.825, wall: [[1.09, 5.564], [2.179, 5.353], [3.269, 5.035], [4.359, 4.619], [5.448, 4.108], [6.538, 3.509]]},
    ],
    lights: [
      // steady sidelights on the top of each radiator, outboard forward corner (the beam extremity): red port, green starboard
      { p: [28.52, 3.431, -27.849], color: 'red', size: 0.4 },
      { p: [-28.52, 3.431, -27.849], color: 'green', size: 0.4 },
      // anti-collision strobes, alternating: mast housing and keel block
      { p: [1.1, 11.681, -25.199], color: 'white', size: 0.4, blink: { ...STROBE } },
      { p: [0.0, -13.029, -36.499], color: 'white', size: 0.4, blink: { ...STROBE, phase: 0.5 } },
      // steady stern light on the aft face of the dorsal block, between the bells
      { p: [0.0, 4.101, -51.273], color: 'white', size: 0.4 },
      // v10 amber running lights: crew-module ledge and reactor block flanks
      { p: [9.85, 4.68, 34.4], color: 'amber', size: 0.3, mirrorX: true },
      { p: [9.85, 4.68, 50.4], color: 'amber', size: 0.3, mirrorX: true },
      { p: [15.59, 4.6, -29.3], color: 'amber', size: 0.3, mirrorX: true },
      { p: [15.59, 4.6, -21.7], color: 'amber', size: 0.3, mirrorX: true },
    ],
    anchors: {
      // flat hull faces, measured on the remodelled hull by ray casts (0.5 m grid along -normal, plane refit;
      // flat = share of samples within 0.15 m of the plane)
      surfaces: {
        'cm-flank-port': { centre: [10.28, -4.4, 42.4], normal: [1.0, -0.005, 0.0], u: [0.0, 0.0, 1.0], width: 18.0, height: 8.0, flat: 0.95 }, // crew-module flank, decks 2-4 (port rows every 1.6 m, teal stripe at y 0)
        'cm-flank-stbd': { centre: [-10.28, -4.4, 42.4], normal: [-1.0, -0.005, 0.0], u: [0.0, 0.0, -1.0], width: 18.0, height: 8.0, flat: 0.95 },
        'cm-ledge-port': { centre: [9.85, 4.6, 42.4], normal: [0.0, 1.0, 0.0], u: [0.0, 0.0, 1.0], width: 18.0, height: 0.8, flat: 1.0 }, // upper-tier walkway ledge (rails)
        'cm-ledge-stbd': { centre: [-9.85, 4.6, 42.4], normal: [0.0, 1.0, 0.0], u: [0.0, 0.0, 1.0], width: 18.0, height: 0.8, flat: 1.0 },
        'cm-roof': { centre: [0.0, 10.43, 43.4], normal: [0.0, 1.0, 0.005], u: [0.0, -0.005, 1.0], width: 7.0, height: 10.0, flat: 0.81 }, // raised roof deck (hatches)
        'reactor-flank-port': { centre: [15.51, 2.0, -25.5], normal: [1.0, 0.0, 0.0], u: [0.0, 0.0, 1.0], width: 9.0, height: 6.0, flat: 1.0 }, // reactor block flank (CT-7 stencil)
        'reactor-flank-stbd': { centre: [-15.51, 2.0, -25.5], normal: [-1.0, 0.0, 0.0], u: [0.0, 0.0, -1.0], width: 9.0, height: 6.0, flat: 1.0 },
        'reactor-roof': { centre: [0.0, 10.73, -23.9], normal: [0.0, 1.0, -0.006], u: [0.0, 0.006, 1.0], width: 8.0, height: 4.0, flat: 0.0 },
        'radiator-top-port': { centre: [25.78, 3.2, -34.5], normal: [0.0, 1.0, 0.0], u: [0.0, 0.0, 1.0], width: 10.0, height: 4.0, flat: 1.0 }, // radiator panel top edge
        'radiator-top-stbd': { centre: [-25.78, 3.2, -34.5], normal: [0.0, 1.0, 0.0], u: [0.0, 0.0, 1.0], width: 10.0, height: 4.0, flat: 1.0 },
      },
    },
  },
};
