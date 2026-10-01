// V-31 wheeled 4x4 (ground unit, game class VEHICLE "jeep") — v3 REMODEL: clean hard-surface body
// (tools/blender/hulls/vehicle.py) built to the brief's TRUE SIZE from the approved concept A and measurements of the
// fal / Tripo H3.1 blueprint, textured in texture space (vehicle_paint.py over paint.py: light paint, plating seams and
// tone, PATINA plate tone, AO grime, edge wear, amber corner hatching, one amber flank band, cobalt square, V-31) and
// assembled with the procedural kit (tools/blender/specs/vehicle-v3.json via assemble.py): four kit wheels and
// double-wishbone corners, the remote weapon station, two round roof hatches, five vehicle doors, the engine-deck
// vent, a foil box and seven covered marker lamps (parts_ground.py, new ground-vehicle kit parts).
// The GLB is in the ship frame (metres, front +Z, up +Y, left +X): rotate [0, 0, 0]. REAL-WORLD SIZE: this is not a
// hangar-slot class (scale.js CLASSES.vehicle has size: null, so normalizeShip leaves it at scale 1). Node 'hull' is
// the body, 'parts_*' the kit parts (hullNodes).
// Assembled envelope 2.63 x 2.99 x 6.95 m (body 6.5 x 2.6 x 2.5 m; tyres 1.15 m at x +-1.315 outer face; RWS top 2.99 m;
// length adds the collar lamps and the tow pintle). Authored with the ground at y = 0; bbox centre [0, 1.494, -0.005]:
// every coordinate below is shifted by minus that centre, as glbship.js centres the GLB.
export const meta = {
  name: 'Kestrel-class light armoured vehicle',
  designation: 'V-31',
  crew: '2-4',
  blurb: 'Fast wheeled 4x4 for the ground forces: a tall faceted armoured cab whose flat roof runs unbroken to the tail, a gunmetal nose collar and belly band, four 1.15 m tyres on independent suspension, and one small remote weapon station behind two round roof hatches.',
};

export const asset = {
  glb: './assets/ships/vehicle.glb',
  generator: 'tools/blender/hulls/vehicle.py (remodel of the tripo3d/h3.1/multiview-to-3d blueprint) + tools/blender/assemble.py',
  concept: './assets/concepts/vehicle.webp',
  rotate: [0, 0, 0],
  hullNodes: ['hull'],
  // dark operational grey by default (correction 10; the ground-livery question is open, correction 19). The remodel
  // paint is lighter than the generated textures (gain 0.05, as the fighter); marks kept a little stronger than the
  // fleet default, like the destroyer (mark 0.18, markSat 0.3), so the amber band, the hatching and the cobalt square
  // still read as low-visibility tones (markSat 0.5: at 0.3 the amber band read tan-brown in the studio). No lit glass: a 2-4 crew vehicle keeps its armoured panes dark.
  // v2 (correction 34, "way too smooth and clean. Too shiny"): matte 0.75 (paint roughness ~0.9 before the finish, which
  // re-derives it at 0.84-1.0), and keep: 1 so the chips (primer, bare metal), dust and mud that vehicle_paint.py bakes in
  // true albedo (base-colour alpha < 1) are not repainted grey. glassRough 0.8: hazy, dusty armoured panes (dark, no glare).
  livery: { gain: 0.05, mark: 0.18, markSat: 0.5, matte: 0.75, keep: 1, glassRough: 0.8 },
  // ground-unit finish (finish.js FINISH_PRESETS.ground): vehicle-scale wear and grit, matte roughness, scratches from the
  // groundPaint set, dust graded up from anchors.ground and dried mud low down, continuous over the hull and every kit part
  finish: 'ground',
  // authored lights only (small-craft rule, R4): seven covered lamps at the kit markerLamp lenses, no automatic pins or
  // slits, no headlamps, no light bars. Pins are fleet size (0.2 m), never scaled to the vehicle.
  lightscape: {
    seed: 31,
    creases: null,
    slits: null,
    patterns: [
      // covered front lamps: a short upright slit at each collar-cheek lens (0.16 x 0.05 m, the kit lens), dim; as 0.2 m
      // round pins they read as a pair of round headlamps, which the brief excludes
      { slit: [0.835, -0.164, 3.432], u: [0, 1, 0], n: [0, 0, 1], len: 0.16, width: 0.05, radiance: 0.9, color: 'amber', keep: true, mirrorX: true },
      // amber side markers on the bonnet flanks, ahead of the front arches
      { slit: [1.05, -0.164, 2.885], u: [0, 0, 1], n: [0.97, 0, -0.25], len: 0.16, width: 0.05, radiance: 1.0, color: 'amber', mirrorX: true },
      // covered convoy lamp over the tail door (lights the convoy marking for the vehicle behind)
      { slit: [0, 0.836, -3.332], u: [1, 0, 0], n: [0, 0, -1], len: 0.16, width: 0.05, radiance: 0.6, color: 'white' },
    ],
  },
  // v2: the ships' 6 m 'hull' tile spanned the whole 6.5 m body (no visible surface texture, and its 1.5 m plate grid
  // ignored the vehicle's own seams). groundPaint (scratched, scuffed armour paint, no seams) at a 1.5 m tile
  detail: { set: 'groundPaint', tile: 1.5, normalStrength: 1.4, roughAmount: 0.8, cavity: 0, skipGlass: true },
  // two-tone (opt-in ?livery=tone|bone): the cab flanks and the doors' band of the flank take the light paint
  liveryZones: [
    { box: [[1.0, -0.72, -3.3], [1.35, 0.73, 3.3]], mirrorX: true },
  ],
  length: 6.95,
  engines: [],
  lights: [
    // red tail lamps in the tail face beside the tail door
    { p: [0.77, 0.526, -3.335], color: 'red', size: 0.2 },
    { p: [-0.77, 0.526, -3.335], color: 'red', size: 0.2 },
  ],
  anchors: {
    // remote weapon station: muzzle of the heavy-MG barrel (kit rws muzzle [0, 1.28, 0.37] at the roof mount z -1.22)
    muzzle: { p: [0, 1.376, 0.065], dir: [0, 0, 1] },
    // the ground contact plane (wheels on the ground at y = 0 in the model frame)
    ground: { y: -1.494 },
    surfaces: {
      'flank-port': { centre: [1.10, 0.346, -2.0], normal: [1, 0, 0], u: [0, 0, -1], width: 1.4, height: 0.7 },   // above the rear arch: V-31
      'flank-stbd': { centre: [-1.10, 0.346, -2.0], normal: [-1, 0, 0], u: [0, 0, 1], width: 1.4, height: 0.7 },
      'roof': { centre: [0, 1.006, -0.4], normal: [0, 1, 0], u: [0, 0, 1], width: 1.6, height: 5.0 },             // hatches, RWS, vent
      'tail': { centre: [0, 0.006, -3.255], normal: [0, 0, -1], u: [-1, 0, 0], width: 1.9, height: 1.3 },          // tail door
      'windscreen': { centre: [0, 0.756, 1.675], normal: [0, 0.74, 0.67], u: [1, 0, 0], width: 1.6, height: 0.7 },
    },
  },
};
