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
// v14 lightscape shared by both variants, at the fleet fixture standard (v14 STANDARD section 2): one lamp is one size on
// every hull, so the 134 m freighter's pins (0.20-0.28 m) and bars (0.20 m wide) match the corvette's and the
// destroyer's. Amber with a few white: warm and cream are the lit-port colours and stay on glass (R6). The crease cap
// is low (45): an 80-crew ship is mostly dark working structure, and a fine even scatter of lamps reads as a larger,
// populated hull (the fighter's "small random lights = windows")
const CIVIL_CREASES = { angle: 35, minLen: 3, pitch: 7, share: 0.34, run: [1, 2], runPitch: 1.2, corners: 0.4, spacing: 1.6, size: [0.2, 0.28], intensity: [0.7, 1.0], mix: { amber: 0.85, white: 0.15 }, max: 45, blinkShare: 0.03 };
const CIVIL_SLITS = { angle: 35, minLen: 1.5, share: 0.5, every: 8, len: [0.8, 1.3], width: 0.2, radiance: [0.9, 1.4], spacing: 4, max: 24, mix: { amber: 1 }, corner: { width: 0.2, len: [0.8, 1.2], radiance: [1.1, 1.5] } };
// civil grey; the remodel paint is lighter than the generated textures (gain 0.05); lit cabins behind the ports (v11: warm,
// varied, a few flickering). v14: only the kit glass glows (glassParts: the 0.86 m port lites and the bridge panes):
// the hull's dark CT-4 / CT-7 stencils and labels passed the glass test and lit as 0.1-0.55 m specks, sub-port
// "windows" on the uncrewed reactor block and beside the real ports. The port-lite mesh has three primitives (frame,
// glass, glass_lit), which GLTFLoader loads as a group 'parts_portlite' of meshes 'parts_portlite_1..3'; glbship.js
// reads the part name from the nearest named object, so the suffixed names are listed too (without them no port glows)
const CIVIL_LIVERY = { ...LIVERIES.civil, gain: 0.05, glassGlow: [0.52, 0.42, 0.28], glassLit: 0.55, glassFlicker: 0.14, glassParts: ['portlite', 'portlite_1', 'portlite_2', 'portlite_3', 'pane'] };
// v14 clearance boxes for the automatic lamps (creases / slits `exclude`, ship frame): no automatic pin or bar within
// 1.5 m of a port or pane (STANDARD 3.5: a lamp among the ports reads as one more, smaller window; bars on the
// bridge-pane lip read as lit slots): the kit glass grown by 1.5 m (crew-module flank ports and upper tier, bow chamfer
// ports, bridge panes, the collar's aft-facing control-cab panes). And none at the collar airlock or the reactor
// access door, where the recess corners drew 0.85-1.23 m bars: each door gets one authored F10 door lamp instead
// (one fixture, one size: a second, larger door lamp would be a second ruler). dz: the troop hull's crew module sits
// 2.6 m aft, its collar 1.5-2.0 m aft, its reactor door 2.0 m forward and 2.1 m outboard
const autoClear = ({ dz = 0, dzCollar = 0, dzLock = 0, reactorDoor }) => [
  { box: [[7.9, -10.85, 33.45 + dz], [12.5, 8.05, 56.35 + dz]], mirrorX: true },
  { box: [[5.5, -10.85, 55.0 + dz], [11.5, 2.05, 66.45 + dz]], mirrorX: true },
  { box: [[-10.9, -3.8, 55.2 + dz], [10.9, 3.9, 68.2 + dz]] },
  { box: [[-5.5, 7.1, 24.8 + dzCollar], [5.5, 11.4, 28.7 + dzCollar]] },
  { box: [[10.0, -5.0, 27.5 + dzLock], [12.5, 1.5, 32.0 + dzLock]], mirrorX: true },
  { box: reactorDoor, mirrorX: true },
];
const CARGO_CLEAR = autoClear({ reactorDoor: [[12.5, -10.0, -26.2], [14.5, -5.8, -23.2]] });
const TROOPS_CLEAR = autoClear({ dz: -2.6, dzCollar: -1.5, dzLock: -2.04, reactorDoor: [[14.6, -10.0, -24.2], [16.6, -5.8, -21.2]] });

export const asset = {
  glb: './assets/ships/freighter.glb',
  generator: 'tools/blender/hulls/freighter.py --variant cargo (remodel of the tripo3d/h3.1/multiview-to-3d hull) + tools/blender/assemble.py + freighter_extras.py',
  concept: './assets/concepts/freighter.webp',
  beauty: './assets/concepts/freighter-beauty.webp',
  rotate: [0, 0, 0],
  hullNodes: ['hull'],
  // v14 livery: only kit glass glows (CIVIL_LIVERY.glassParts), so the container stacks (dark blue door corrugation, the
  // v12 glassDark box) and the hull stencils stay dark without boxes. Compartment grid aligned to the decks and port
  // columns (cells 5.8 x 3.0 x 5.85 m): no 0.86 m port lite is split into two-tone halves (0 of 130; a half-lit port
  // reads as a half-size window, so the hull reads bigger). Bridge deck (panes x +-9.4, y -2.3..2.4, z 56.7..66.6, and
  // the 8 bridge-deck ports on the bow chamfers): one steady compartment at half the cabin glow (bridges run dark,
  // STANDARD R8); the box stops at y -2.4, above the next port row's glass (top y -2.47), so no port straddles it
  livery: { ...CIVIL_LIVERY, glassCell: [5.8, 3.0, 5.85], glassPhase: [0.0, 0.47, 0.49], glassZones: [{ box: [[-9.5, -2.4, 56.5], [9.5, 2.5, 67.0]], gain: 0.5, uniform: true }] },
  // v14 lightscape (src/lib/lightscape.js), fleet scale standard: the lit accommodation block (6 decks of ports, ~55 %
  // lit) carries the human scale; the working spine is dark structure marked only where a fixture has a job. Amber
  // bars at the block extremities (collar flank, reactor forward face and flank: the 8 keep bars), the truss marked at
  // every other web node plus one loading-guide chaser, the reactor dark but for its corner bars and cool sequencer,
  // the engine faces by 4 corner lamps, the radiators at their ends. Docking-tube markers and roof beacons stay
  lightscape: {
    seed: 31,
    creases: { ...CIVIL_CREASES, exclude: CARGO_CLEAR },
    slits: { ...CIVIL_SLITS, exclude: CARGO_CLEAR },
    cool: { radius: 1.7, depth: 2 },
    zones: [
      // radiator panels (x 21.7..27.3, z -29.5..-60.8): fins and louvre frames stay dark; the ends are authored
      { box: [[18.5, -14, -63], [32, 3.6, -28]], mirrorX: true, creases: null, slits: null },
      // payload truss and container bay (reactor face z -22.5 to collar z 25.5): no automatic lamps. The rack posts and
      // gantry tops carried 84 crease pins (1.5 lamps per metre on uncrewed structure, twice the crew module's): a
      // field of window-sized dots that read as more lit habitation. The authored node pins and chaser carry the bay
      { box: [[-9, -15, -22.3], [9, 11, 25.4]], creases: null, slits: null },
      // reactor block and engine section (uncrewed machinery): corner-rank crease pins only
      { box: [[-15, -15, -64], [15, 20, -22.3]], creases: { share: 0.05, corners: 0.2 } },
      // bow-face vent louvre
      { box: [[-7.6, -11.2, 65.5], [7.6, -4.3, 68]], creases: null },
    ],
    patterns: [
      // crew module: the walkway ledge (y 4.6) and the lower chine (y -10.45) each run 1.2-1.5 m from a port row, so
      // they carry no lamp rows (a row there reads as one more deck of small windows, STANDARD R2): one white lamp at
      // the ladder head on the ledge (ladder z 40.1..40.7 from the crew door up), amber lamps at the chine's two ends
      { points: [[10.15, 4.7, 40.4]], color: 'white', size: 0.22, intensity: 0.7, mirrorX: true },
      { points: [[10.36, -10.25, 34.6], [10.36, -10.25, 55.0]], color: 'amber', size: 0.24, intensity: 0.85, mirrorX: true },
      // crew doors (recesses z 37.65..39.55 and 50.25..52.15, 1.4 x 2.4 m leaves): one amber door lamp each, the fleet's
      // F10 fixture (0.6 x 0.14 m, as on the fighter), upright on the flank beside the forward jamb, its top 0.15 m under
      // the lintel: the human ruler beside the door. (Under the kit floodlight housing it would be hidden from above)
      { slit: [10.31, -7.75, 39.75], u: [0, 1, 0], n: [1, 0, 0], len: 0.6, width: 0.14, radiance: 1.4, color: 'amber', mirrorX: true },
      { slit: [10.31, -7.75, 52.35], u: [0, 1, 0], n: [1, 0, 0], len: 0.6, width: 0.14, radiance: 1.4, color: 'amber', mirrorX: true },
      { surface: 'cm-roof', edge: 'left', inset: 0.3, pitch: 5, color: 'amber', size: 0.3, intensity: 1.0, pulse: 3.8 },
      // collar flank, aft corner (x 11.0, z 25.5..34): upright bars above and below the airlock
      { slit: [11.04, 3.3, 26.2], u: [0, 1, 0], n: [1, 0, 0], len: 1.6, width: 0.2, radiance: 1.6, color: 'amber', mirrorX: true, keep: true },
      { slit: [11.04, -5.0, 26.2], u: [0, 1, 0], n: [1, 0, 0], len: 1.3, width: 0.2, radiance: 1.4, color: 'amber', mirrorX: true },
      // docking tubes (collar lower corners, r 1.85-2.15, z 24.9..33.7): marker ring round the aft mouth, beacon on top
      { ring: { c: [12.3, -8.4, 24.82], axis: [0, 0, -1], r: 1.95 }, n: 6, color: 'white', size: 0.22, intensity: 0.85, chase: 4, mirrorX: true },
      { points: [[12.3, -6.45, 33.0]], color: 'amber', size: 0.26, intensity: 0.9, pulse: 3, mirrorX: true },
      // collar airlock (z 28.5..31.0, in a 0.4 m recess): its door lamp on the recess back wall over the airlock frame
      // (y -0.51), clear of the recess lip and the floodlight housing above, so it shows from above
      { slit: [10.61, -0.43, 29.75], u: [0, 0, 1], n: [1, 0, 0], len: 0.6, width: 0.14, radiance: 1.4, color: 'amber', mirrorX: true },
      // payload truss, chord outer faces (x 7.8, web nodes every 5.45 m, z -20.3..23.3): a lamp at every other node on
      // the top chord and a bar in every other bay on the bottom chord (a lamp every ~2.7 m on three chord rows read as
      // a lit window band under the containers), plus the slow loading-guide chaser toward the bow
      { row: [[7.85, 1.55, 23.3], [7.85, 1.55, -20.3]], pitch: 10.9, color: 'amber', size: 0.24, intensity: 0.95, mirrorX: true },
      { slitRow: [[7.85, -5.95, 20.575], [7.85, -5.95, -12.125]], pitch: 10.9, u: [0, 0, 1], n: [1, 0, 0], len: 1.0, width: 0.2, radiance: 1.4, color: 'amber', skip: 0, mirrorX: true },
      { row: [[7.85, -5.95, 23.3], [7.85, -5.95, -14.85]], pitch: 5.45, color: 'amber', size: 0.26, intensity: 1.0, chase: 6, reverse: true, mirrorX: true },
      // reactor block forward face (z -22.5, outboard of the truss): upright bars at the outer pillars, a lintel bar
      { slit: [12.35, 5.8, -22.42], u: [0, 1, 0], n: [0, 0, 1], len: 1.6, width: 0.2, radiance: 1.6, color: 'amber', mirrorX: true, keep: true },
      { slit: [12.35, -6.2, -22.42], u: [0, 1, 0], n: [0, 0, 1], len: 1.6, width: 0.2, radiance: 1.6, color: 'amber', mirrorX: true, keep: true },
      { slit: [9.0, 11.15, -22.42], u: [1, 0, 0], n: [0, 0, 1], len: 1.4, width: 0.2, radiance: 1.5, color: 'amber', mirrorX: true },
      // reactor flank: a bar just aft of the forward frame band (clear of the vent, z <= -24.6); a 4-light blue-white
      // status sequencer under the vent between the amber corner lamps (animated, so it keeps its far-field floor)
      { slit: [13.58, 6.3, -23.3], u: [0, 1, 0], n: [1, 0, 0], len: 1.4, width: 0.2, radiance: 1.5, color: 'amber', mirrorX: true, keep: true },
      { surface: 'reactor-flank-port', edge: 'top', inset: 0.4, insetU: 1.5, pitch: 2.0, color: 'cool', size: 0.26, intensity: 1.0, chase: 2.4, mirrorX: true },
      // reactor access door (recess z -25.65..-23.75, lintel y -6.5): the same door lamp beside its forward jamb
      { slit: [13.41, -6.95, -23.55], u: [0, 1, 0], n: [1, 0, 0], len: 0.6, width: 0.14, radiance: 1.4, color: 'amber', mirrorX: true },
      // reactor flank top corners (the v10 amber running lights, moved out of the never-dimmed nav path)
      { points: [[13.55, 4.6, -32.05], [13.45, 4.6, -24.45]], color: 'amber', size: 0.26, intensity: 0.9, mirrorX: true },
      // engine housings: 4 amber corner lamps on the aft face round each bell mount (face z -55.98, r 4.75..5.6)
      { ring: { c: [7.74, 0.1, -56.05], axis: [0, 0, -1], r: 5.3 }, n: 4, color: 'amber', size: 0.26, intensity: 0.9, mirrorX: true },
      // radiator panels (uncrewed): the outboard top edge's aft corner and one mid-edge lamp, 17 m and more aft of the
      // sidelight at the forward corner (a 9-lamp row read as a lit roofline)
      { points: [[26.9, 3.2, -58.0], [26.9, 3.2, -47.0]], color: 'amber', size: 0.26, intensity: 0.7, mirrorX: true },
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
    // (v14: the v10 amber running lights left this never-dimmed nav path: the crew-module pair sat on the walkway
    // ledge between two port rows, where it read as a lit window at every range; the reactor-flank pair is a
    // lightscape pattern now, so it fades and thins with range like every other lamp)
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
    // v14 livery: lit share by role (STANDARD R9): the habitats' 750 berths at the troop share (0.45, at the destroyer's,
    // not above it; the lit mask is a smooth value noise, so on this hull that lights ~36 % of the berths), the crew
    // module at the civil crew share (0.55, as on the cargo ship: at 0.45 the same 80-crew block read half as occupied
    // as the cargo ship's), the bridge panes one dim steady compartment; only the kit glass glows (CIVIL_LIVERY.glassParts:
    // no stencil specks on the reactor). Compartment grid aligned to the decks and berth columns (5.8 x 6.1 x 5.8 m:
    // 0 of 386 port lites split)
    livery: {
      ...CIVIL_LIVERY, glassLit: 0.45, glassCell: [5.8, 6.1, 5.8], glassPhase: [0.0, 0.69, 0.86],
      glassZones: [{ box: [[-9.5, -2.4, 54.0], [9.5, 2.5, 64.5]], gain: 0.5, uniform: true }, { box: [[-12.0, -14.0, 31.4], [12.0, 11.0, 64.9]], lit: 0.55 }],
    },
    // v14 lightscape: as on the cargo ship, at the troop hull's stations (reactor face z -20.5, flank x 15.6, collar
    // aft face z 24.0, girder chord outer face x 11.6, web nodes every 4.82 m, radiators to z -55.5). The habitat
    // cylinders carry lit berths and no lamps: their railcar rows of ports are the human scale of the mid-body
    lightscape: {
      seed: 37,
      creases: { ...CIVIL_CREASES, exclude: TROOPS_CLEAR },
      slits: { ...CIVIL_SLITS, exclude: TROOPS_CLEAR },
      cool: { radius: 1.7, depth: 2 },
      zones: [
        { box: [[19.5, -14, -57], [33, 3.7, -26]], mirrorX: true, creases: null, slits: null },
        // payload girder and habitats: no automatic lamps (64 crease pins on the girder and cylinders floated in the
        // bays as specks between the lit berths); the authored node pins and chaser carry it
        { box: [[-12.5, -15, -20.3], [12.5, 11, 23.9]], creases: null, slits: null },
        // reactor block and engine section (uncrewed machinery): corner-rank crease pins only
        { box: [[-17, -15, -60], [17, 20, -20.3]], creases: { share: 0.05, corners: 0.2 } },
        { box: [[-7.6, -11.2, 62.8], [7.6, -4.3, 65.5]], creases: null },
      ],
      patterns: [
        // crew module (2.6 m aft of the cargo ship's): ladder-head lamp, chine ends, the two crew-door lamps
        { points: [[10.15, 4.7, 37.8]], color: 'white', size: 0.22, intensity: 0.7, mirrorX: true },
        { points: [[10.36, -10.25, 32.0], [10.36, -10.25, 52.4]], color: 'amber', size: 0.24, intensity: 0.85, mirrorX: true },
        { slit: [10.31, -7.75, 37.15], u: [0, 1, 0], n: [1, 0, 0], len: 0.6, width: 0.14, radiance: 1.4, color: 'amber', mirrorX: true },
        { slit: [10.31, -7.75, 49.75], u: [0, 1, 0], n: [1, 0, 0], len: 0.6, width: 0.14, radiance: 1.4, color: 'amber', mirrorX: true },
        { surface: 'cm-roof', edge: 'left', inset: 0.3, pitch: 5, color: 'amber', size: 0.3, intensity: 1.0, pulse: 3.8 },
        { slit: [11.04, 3.3, 24.7], u: [0, 1, 0], n: [1, 0, 0], len: 1.6, width: 0.2, radiance: 1.6, color: 'amber', mirrorX: true, keep: true },
        { slit: [11.04, -5.0, 24.7], u: [0, 1, 0], n: [1, 0, 0], len: 1.3, width: 0.2, radiance: 1.4, color: 'amber', mirrorX: true },
        { ring: { c: [12.3, -8.4, 24.12], axis: [0, 0, -1], r: 1.95 }, n: 6, color: 'white', size: 0.22, intensity: 0.85, chase: 4, mirrorX: true },
        { points: [[12.3, -6.45, 30.4]], color: 'amber', size: 0.26, intensity: 0.9, pulse: 3, mirrorX: true },
        { slit: [10.61, -0.43, 27.7], u: [0, 0, 1], n: [1, 0, 0], len: 0.6, width: 0.14, radiance: 1.4, color: 'amber', mirrorX: true },
        // girder: every other web node, every other bottom-chord bay, the loading-guide chaser
        // (row ends on exact multiples of the pitch, so the lamps sit on the nodes and bay centres: a row spreads its
        // lamps evenly between its ends)
        { row: [[11.65, 1.57, 18.9], [11.65, 1.57, -19.66]], pitch: 9.639, color: 'amber', size: 0.24, intensity: 0.95, mirrorX: true },
        { slitRow: [[11.65, -4.67, 16.49], [11.65, -4.67, -12.43]], pitch: 9.64, u: [0, 0, 1], n: [1, 0, 0], len: 1.0, width: 0.2, radiance: 1.4, color: 'amber', skip: 0, mirrorX: true },
        { row: [[11.65, -4.67, 18.9], [11.65, -4.67, -14.84]], pitch: 4.82, color: 'amber', size: 0.26, intensity: 1.0, chase: 6, reverse: true, mirrorX: true },
        { slit: [14.5, 5.6, -20.42], u: [0, 1, 0], n: [0, 0, 1], len: 1.6, width: 0.2, radiance: 1.6, color: 'amber', mirrorX: true, keep: true },
        { slit: [14.5, -6.0, -20.42], u: [0, 1, 0], n: [0, 0, 1], len: 1.6, width: 0.2, radiance: 1.6, color: 'amber', mirrorX: true, keep: true },
        { slit: [11.5, 9.3, -20.42], u: [1, 0, 0], n: [0, 0, 1], len: 1.4, width: 0.2, radiance: 1.5, color: 'amber', mirrorX: true },
        // (no flank bar: the troop reactor's vent runs to z -21.8, 0.7 m off the forward frame)
        { surface: 'reactor-flank-port', edge: 'top', inset: 0.4, insetU: 1.5, pitch: 2.0, color: 'cool', size: 0.26, intensity: 1.0, chase: 2.4, mirrorX: true },
        // reactor access door (recess z -23.65..-21.75, lintel y -6.32): door lamp beside its forward jamb
        { slit: [15.51, -6.77, -21.55], u: [0, 1, 0], n: [1, 0, 0], len: 0.6, width: 0.14, radiance: 1.4, color: 'amber', mirrorX: true },
        { points: [[15.59, 4.6, -29.3], [15.59, 4.6, -21.7]], color: 'amber', size: 0.26, intensity: 0.9, mirrorX: true },
        { ring: { c: [8.54, 0.0, -51.31], axis: [0, 0, -1], r: 6.4 }, n: 4, color: 'amber', size: 0.26, intensity: 0.9, mirrorX: true },
        { points: [[28.3, 3.3, -54.0], [28.3, 3.3, -44.0]], color: 'amber', size: 0.26, intensity: 0.7, mirrorX: true },
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
      // (v14: no amber running lights here; the reactor-flank pair is a lightscape pattern)
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
