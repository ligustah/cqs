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
// v12 lightscape tuning shared by both variants: crease pins warm (amber / warm, few white: white vanished on the
// key-lit paint), a little fewer and larger; recess bars wider and brighter so bars, not pins, carry the read
const CIVIL_CREASES = { angle: 35, minLen: 3, pitch: 7, share: 0.34, run: [1, 2], runPitch: 1.2, corners: 0.4, spacing: 1.6, size: [0.26, 0.38], intensity: [0.8, 1.1], mix: { amber: 0.6, warm: 0.3, white: 0.1 }, max: 170, blinkShare: 0.03 };
const CIVIL_SLITS = { angle: 35, minLen: 1.5, share: 0.5, every: 8, len: [0.9, 1.6], width: 0.23, radiance: [0.9, 1.4], spacing: 4, max: 44, mix: { amber: 0.7, warm: 0.3 }, corner: { width: 0.23, len: [0.9, 1.4], radiance: [1.1, 1.5] } };
// civil grey; the remodel paint is lighter than the generated textures (gain 0.05); lit cabins behind the ports (v11: warm, varied, a few flickering)
const CIVIL_LIVERY = { ...LIVERIES.civil, gain: 0.05, glassGlow: [0.52, 0.42, 0.28], glassLit: 0.55, glassFlicker: 0.14 };

export const asset = {
  glb: './assets/ships/freighter.glb',
  generator: 'tools/blender/hulls/freighter.py --variant cargo (remodel of the tripo3d/h3.1/multiview-to-3d hull) + tools/blender/assemble.py + freighter_extras.py',
  concept: './assets/concepts/freighter.webp',
  beauty: './assets/concepts/freighter-beauty.webp',
  rotate: [0, 0, 0],
  hullNodes: ['hull'],
  // v12: the container stacks (kit parts |x| < 6.1, y -14.1..9.7, z -19.9..23.1) have no ports: their dark blue door
  // corrugation passed the glass test and glowed as amber streaks; glass stays dark there
  livery: { ...CIVIL_LIVERY, glassDark: [[[-6.4, -14.4, -20.2], [6.4, 10.0, 23.4]]] },
  // v12 lightscape (src/lib/lightscape.js): warm crease pins; bright short bars at the block corners (reactor
  // forward face and flank, collar flank) and a steady rhythm on the payload truss (pins at the web nodes of the top
  // chord, bars mid-bay on the bottom chord, a slow loading-guide chaser toward the bow); radiators and the bow
  // louvre dark but for an authored top-edge row; docking-tube markers, engine-face ring, 4-light reactor sequencer
  lightscape: {
    seed: 31,
    creases: CIVIL_CREASES,
    slits: CIVIL_SLITS,
    cool: { radius: 1.7, depth: 2 },
    zones: [
      // radiator panels (x 21.7..27.3, z -29.5..-60.8): fins and louvre frames stay dark; the top edge is authored
      { box: [[18.5, -14, -63], [32, 3.6, -28]], mirrorX: true, creases: null, slits: null },
      // payload truss and container bay (reactor face z -22.5 to collar z 25.5): random crease pins would break the rhythm
      { box: [[-9, -15, -22.3], [9, 11, 25.4]], creases: { share: 0.06, corners: 0.15 }, slits: null },
      // bow-face vent louvre
      { box: [[-7.6, -11.2, 65.5], [7.6, -4.3, 68]], creases: null },
    ],
    patterns: [
      // crew module: white deck-edge lights along the walkway ledge, amber along the lower chine (y -10.45)
      { surface: 'cm-ledge-port', edge: 'top', inset: 0.1, pitch: 2.5, color: 'white', size: 0.22, intensity: 0.65, mirrorX: true },
      { row: [[10.36, -10.25, 36.0], [10.36, -10.25, 54.0]], pitch: 3.6, color: 'amber', size: 0.24, intensity: 0.85, mirrorX: true },
      { surface: 'cm-roof', edge: 'left', inset: 0.3, pitch: 5, color: 'amber', size: 0.3, intensity: 1.0, pulse: 3.8 },
      // collar flank, aft corner (x 11.0, z 25.5..34): upright bars above and below the airlock
      { slit: [11.04, 3.3, 26.2], u: [0, 1, 0], n: [1, 0, 0], len: 1.6, width: 0.25, radiance: 1.6, color: 'amber', mirrorX: true, keep: true },
      { slit: [11.04, -5.0, 26.2], u: [0, 1, 0], n: [1, 0, 0], len: 1.3, width: 0.23, radiance: 1.4, color: 'warm', mirrorX: true },
      // docking tubes (collar lower corners, r 1.85-2.15, z 24.9..33.7): marker ring round the aft mouth, beacon on top
      { ring: { c: [12.3, -8.4, 24.82], axis: [0, 0, -1], r: 1.95 }, n: 6, color: 'white', size: 0.22, intensity: 0.85, chase: 4, mirrorX: true },
      { points: [[12.3, -6.45, 33.0]], color: 'amber', size: 0.26, intensity: 0.9, pulse: 3, mirrorX: true },
      // payload truss, chord outer faces (x 7.8): web nodes every 5.45 m (z -20.3..23.3)
      { row: [[7.85, 1.55, 23.3], [7.85, 1.55, -20.3]], pitch: 5.45, color: 'amber', size: 0.28, intensity: 0.95, mirrorX: true },
      { slitRow: [[7.85, -5.95, 20.575], [7.85, -5.95, -17.575]], pitch: 5.45, u: [0, 0, 1], n: [1, 0, 0], len: 1.0, width: 0.22, radiance: 1.4, color: 'amber', skip: 0.2, mirrorX: true, keep: true },
      { row: [[7.85, -5.95, 23.3], [7.85, -5.95, -20.3]], pitch: 5.45, color: 'amber', size: 0.26, intensity: 1.0, chase: 6, reverse: true, mirrorX: true },
      // reactor block forward face (z -22.5, outboard of the truss): upright bars at the outer pillars, a lintel bar
      { slit: [12.35, 5.8, -22.42], u: [0, 1, 0], n: [0, 0, 1], len: 1.6, width: 0.25, radiance: 1.6, color: 'amber', mirrorX: true, keep: true },
      { slit: [12.35, -6.2, -22.42], u: [0, 1, 0], n: [0, 0, 1], len: 1.6, width: 0.25, radiance: 1.6, color: 'amber', mirrorX: true, keep: true },
      { slit: [9.0, 11.15, -22.42], u: [1, 0, 0], n: [0, 0, 1], len: 1.4, width: 0.23, radiance: 1.5, color: 'warm', mirrorX: true },
      // reactor flank: a bar just aft of the forward frame band (clear of the vent, z <= -24.6); a 4-light blue-white
      // sequencer under the vent between the amber running lights
      { slit: [13.58, 6.3, -23.3], u: [0, 1, 0], n: [1, 0, 0], len: 1.4, width: 0.23, radiance: 1.5, color: 'amber', mirrorX: true, keep: true },
      { surface: 'reactor-flank-port', edge: 'top', inset: 0.4, insetU: 1.5, pitch: 2.0, color: 'cool', size: 0.26, intensity: 1.0, chase: 2.4, keep: true, mirrorX: true },
      // engine housings: amber ring on the aft face round each bell mount (face z -55.98, r 4.75..5.6)
      { ring: { c: [7.74, 0.1, -56.05], axis: [0, 0, -1], r: 5.3 }, n: 8, color: 'amber', size: 0.26, intensity: 0.9, mirrorX: true },
      // radiator panels: one clean amber row along the whole outboard top edge (the sidelight sits at its forward end)
      { row: [[26.9, 3.2, -32.0], [26.9, 3.2, -58.0]], pitch: 3.25, color: 'amber', size: 0.26, intensity: 0.9, keep: true, mirrorX: true },
    ],
  },

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
    // v12 steady red obstruction lights on the mast tips (crew-module whips, reactor mast)
    { p: [3.6, 15.36, 48.51], color: 'red', size: 0.28 },
    { p: [-3.4, 14.28, 44.02], color: 'red', size: 0.28 },
    { p: [0.0, 19.16, -25.76], color: 'red', size: 0.3 },
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
    // the civil livery without the cargo ship's container glassDark: the habitats have real ports
    livery: CIVIL_LIVERY,
    // v12 lightscape: as on the cargo ship, at the troop hull's stations (reactor face z -20.5, flank x 15.6, collar
    // aft face z 24.0, girder chord outer face x 11.6, web nodes every 4.82 m, radiators to z -55.5)
    lightscape: {
      seed: 37,
      creases: CIVIL_CREASES,
      slits: CIVIL_SLITS,
      cool: { radius: 1.7, depth: 2 },
      zones: [
        { box: [[19.5, -14, -57], [33, 3.7, -26]], mirrorX: true, creases: null, slits: null },
        // payload girder and habitats: fewer random crease pins and no automatic bars (seen through the open truss
        // they float in the bays); the authored chord row and node pins carry it
        { box: [[-12.5, -15, -20.3], [12.5, 11, 23.9]], creases: { share: 0.06, corners: 0.15 }, slits: null },
        { box: [[-7.6, -11.2, 62.8], [7.6, -4.3, 65.5]], creases: null },
      ],
      patterns: [
        { surface: 'cm-ledge-port', edge: 'top', inset: 0.1, pitch: 2.5, color: 'white', size: 0.22, intensity: 0.65, mirrorX: true },
        { row: [[10.36, -10.25, 33.5], [10.36, -10.25, 51.5]], pitch: 3.6, color: 'amber', size: 0.24, intensity: 0.85, mirrorX: true },
        { surface: 'cm-roof', edge: 'left', inset: 0.3, pitch: 5, color: 'amber', size: 0.3, intensity: 1.0, pulse: 3.8 },
        { slit: [11.04, 3.3, 24.7], u: [0, 1, 0], n: [1, 0, 0], len: 1.6, width: 0.25, radiance: 1.6, color: 'amber', mirrorX: true, keep: true },
        { slit: [11.04, -5.0, 24.7], u: [0, 1, 0], n: [1, 0, 0], len: 1.3, width: 0.23, radiance: 1.4, color: 'warm', mirrorX: true },
        { ring: { c: [12.3, -8.4, 24.12], axis: [0, 0, -1], r: 1.95 }, n: 6, color: 'white', size: 0.22, intensity: 0.85, chase: 4, mirrorX: true },
        { points: [[12.3, -6.45, 30.4]], color: 'amber', size: 0.26, intensity: 0.9, pulse: 3, mirrorX: true },
        { row: [[11.65, 1.57, 18.9], [11.65, 1.57, -19.65]], pitch: 4.82, color: 'amber', size: 0.28, intensity: 0.95, mirrorX: true },
        { slitRow: [[11.65, -4.67, 16.49], [11.65, -4.67, -17.24]], pitch: 4.82, u: [0, 0, 1], n: [1, 0, 0], len: 1.0, width: 0.22, radiance: 1.4, color: 'amber', skip: 0.2, mirrorX: true, keep: true },
        { row: [[11.65, -4.67, 18.9], [11.65, -4.67, -19.65]], pitch: 4.82, color: 'amber', size: 0.26, intensity: 1.0, chase: 6, reverse: true, mirrorX: true },
        { slit: [14.5, 5.6, -20.42], u: [0, 1, 0], n: [0, 0, 1], len: 1.6, width: 0.25, radiance: 1.6, color: 'amber', mirrorX: true, keep: true },
        { slit: [14.5, -6.0, -20.42], u: [0, 1, 0], n: [0, 0, 1], len: 1.6, width: 0.25, radiance: 1.6, color: 'amber', mirrorX: true, keep: true },
        { slit: [11.5, 9.3, -20.42], u: [1, 0, 0], n: [0, 0, 1], len: 1.4, width: 0.23, radiance: 1.5, color: 'warm', mirrorX: true },
        // (no flank bar: the troop reactor's vent runs to z -21.8, 0.7 m off the forward frame)
        { surface: 'reactor-flank-port', edge: 'top', inset: 0.4, insetU: 1.5, pitch: 2.0, color: 'cool', size: 0.26, intensity: 1.0, chase: 2.4, keep: true, mirrorX: true },
        { ring: { c: [8.54, 0.0, -51.31], axis: [0, 0, -1], r: 6.4 }, n: 8, color: 'amber', size: 0.26, intensity: 0.9, mirrorX: true },
        { row: [[28.3, 3.3, -30.0], [28.3, 3.3, -54.0]], pitch: 3.0, color: 'amber', size: 0.26, intensity: 0.9, keep: true, mirrorX: true },
      ],
    },

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
      // v12 steady red obstruction lights on the mast tips
      { p: [3.6, 15.36, 45.93], color: 'red', size: 0.28 },
      { p: [-3.4, 14.28, 41.42], color: 'red', size: 0.28 },
      { p: [0.0, 18.91, -24.25], color: 'red', size: 0.3 },
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
