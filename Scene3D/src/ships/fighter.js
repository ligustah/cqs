// Fighter F-402 — v3 REMODEL: clean hard-surface hull (tools/blender/hulls/fighter.py) rebuilt from
// measurements of the fal / Tripo H3.1 blueprint (the v5 true-size re-detail), textured in texture space
// (tools/blender/hulls/fighter_paint.py over paint.py: light paint, plating seams and tone, PATINA plate
// tone, AO grime, edge wear, orange bands, the F-402 stencil) and assembled with the Blender parts kit
// (tools/blender/specs/fighter-v3.json via tools/blender/assemble.py).
// The GLB is already in the ship frame (metres, bow +Z, dorsal +Y, port +X): rotate [0, 0, 0], length =
// the assembled bbox length. Node 'hull' is the hull, 'parts_*' the kit parts (hullNodes).
// Beam = the equipment boxes on the sponsons' outboard faces (x +-23.45), height = the dorsal whip
// antenna (y +10.48) and the belly access plates (y -10.40), length = bow lip to the bell exits.
// Engines: kit bells (bell-L x1.014 main pair, r 3.55, exit z -35.856; bell-S x0.979 at the aft end
// of each sponson, r 1.37, exit z -16.64) with the kit's documented engine entry times that scale.
// Lights: at the lenses of the kit nav-light housings.
// Assembled envelope 46.90 x 20.84 x 71.76 m (bbox centre [0.0, 0.049, -0.022] in the model frame; every
// coordinate below is shifted by minus that centre, as glbship.js centres the GLB).
export const meta = {
  "name": "Petrel-class fighter",
  "designation": "F-402",
  "crew": "about 40",
  "blurb": "Heavy space-superiority fighter: a faceted armoured pod with a low bridge block and a five-pane canopy, twin fusion bells in an armoured stern block and a twin railgun on each flank sponson, each sponson ending in a small secondary drive bell."
};

export const asset = {
  glb: "./assets/ships/fighter.glb",
  generator: "tools/blender/hulls/fighter.py (remodel of the tripo3d/h3.1/multiview-to-3d hull) + tools/blender/assemble.py",
  concept: "./assets/concepts/fighter.webp",
  beauty: "./assets/concepts/fighter-beauty.webp",
  rotate: [0, 0, 0],
  hullNodes: ["hull"],
  // v14 (fleet lighting scale standard, R8/R9): a combat craft shows almost no lit glass. Only the kit glass parts
  // glow (the 5 canopy panes at x1.0 and the 2 x 1.0 m ports per side beside the crew door); the bow sensor lenses
  // and every other hull-texture glass stay dark without boxes. Each is one steady uniform compartment, and both
  // run well below R8's 0.45x: on this hull the canopy faces the hero camera, and any glass clearly brighter than
  // the plating round it reads as a lit window (at 0.45x the canopy was the ship's brightest mark at every range).
  // - canopy at 0.15x, whole panes (no glassDark): each pane glows as one fleet-size 1.0 x 1.15 m pane, the glazing
  //   bar only a hairline, barely over the bridge plating: a cockpit running dark. (A dark band over the upper lights
  //   left 0.67 m cells between black mullions, under the 0.8 m minimum of lit glass: a dotted window row at range.)
  // - door ports at 0.07x (about 1.3x the flank at the hero): a faint crew space; the amber door lamp beside them is
  //   the ruler.
  livery: {"gain": 0.05, "glassGlow": [0.52, 0.42, 0.28], "glassFlicker": 0, "glassParts": ["port", "pane"],
    "glassZones": [
      { box: [[-3.6, 2.6, 14.6], [3.6, 5.4, 17.4]], gain: 0.15, uniform: true },                 // canopy
      { box: [[11.0, -3.9, 10.2], [13.0, -1.4, 14.6]], mirrorX: true, gain: 0.07, uniform: true }, // door ports
    ]},
  // v11 lightscape (src/lib/lightscape.js): pins on the hull's convex creases (block corners and chines), short
  // amber bars in its recesses, blue-white status lights round the drive housings, and authored runs.
  // v12 (concept pass): far fewer pins, favouring block corners; short amber bars, not tubes; authored lamp-heads on
  // the sponson ends, the bow bezel posts, the bridge sill and the crew door lintel; the radiator bays kept dark.
  // v14 (scale pass): a 71.7 m strike craft is lit like an aircraft, not a ship. A fine scatter of small lamps and
  // evenly spaced rows read as deck lighting and windows on a hull 1.3-1.8x this size, so: no automatic crease pins
  // (small craft are authored, R4), no rows, a handful of amber bars at the block extremities and joints (the
  // concept's slits; at each stern-block corner a chamfer bar over a vertical corner bar), one lamp per door,
  // 2 masthead beacons on the dorsal centreline, a 2-lamp drive status and the aircraft nav set; no other lone pins
  // on open plating (a single dot on a flat reads as a small window or a random light). Every lamp is fleet size
  // (pins 0.2-0.3 m, bars 0.14-0.2 m wide), so it does not scale with the hull. 26 lamps (4 pins, 22 bars), 8 of
  // them `keep` (the sponson heads and bow bezels: all that is left of it at fleet range).
  lightscape: {
    seed: 11,
    creases: null,
    // four automatic amber corner bars, all at the stern-block corners: the upper chamfer bar over the vertical lower
    // corner bar, a 2-bar stack each side (caps: no recess bars, 4 corner bars; the first recess pair was a grazing
    // bar on the inboard-facing stern frame, a thin orange seam from the stern quarters); amber only: a cream bar
    // reads as a window
    slits: { angle: 35, minLen: 1.2, share: 0.6, every: 5, len: [0.8, 1.4], width: 0.2, radiance: [1.0, 1.5], spacing: 2.5, max: 0, mix: { amber: 1 }, corner: { share: 0.3, width: 0.2, len: [0.8, 1.3], radiance: [1.2, 1.6], max: 4 } },
    cool: { radius: 1.9, depth: 2.5 },
    zones: [
      // dorsal spine and its two radiator/louvre bays (x +-4.5..7, z -17..-5.5): no bars (its two masthead beacons
      // are authored below)
      { box: [[-7.8, 6.4, -19.2], [7.8, 7.4, -0.8]], creases: null, slits: null },
      // stern block: a few corner accents, not a glitter
      { box: [[-14, -9, -27.5], [14, 6, -24]], creases: { share: 0.12, corners: 0.35 } },
      // bow face: only the two authored bezel lamps (the concept's bow has two small slits, not a grille)
      { box: [[-13, -10, 34], [13, 6, 37]], creases: null, slits: null },
      // crew door (flank z 7.3..9.9): its lintel lamp only
      { box: [[11.2, -6.5, 7.0], [13.6, -1.6, 10.2]], mirrorX: true, slits: null },
      // aft (engine-room) door on the stern-block flank (z -17.0..-15.6): its lintel lamp only, the same fixture as
      // the crew door's (an automatic jamb bar here was a larger 0.8 x 0.2 m bar: two sizes of door lamp)
      { box: [[12.2, -4.3, -17.8], [13.7, -0.2, -14.8]], mirrorX: true, slits: null },
      // bridge glazing recess: no bar inside the glazing (a lit bar there reads as one more pane)
      { box: [[-3.6, 2.6, 14.6], [3.6, 5.4, 17.4]], slits: null },
      // pylon (x 13..17.5, y -6.5..-0.3): the pylon and hull are overlapping solids, so the junction has no mesh
      // crease for the automatic bars (v14: its warm riser row is gone; at 4.5 m pitch it read as a window row)
      { box: [[11.5, -7.5, -14.5], [17.8, 0.6, 2.8]], mirrorX: true, creases: { share: 0.1, corners: 0.4 } },
    ],
    patterns: [
      // bridge: two amber sill lamps on the proud sill face under the canopy (y 2.9..3.35, z 16.7..17.0); not kept,
      // so they go with the ship's screen size
      { slit: [1.5, 3.13, 16.89], u: [1, 0, 0], n: [0, 0.607, 0.795], len: 0.6, width: 0.14, radiance: 1.2, color: 'amber', mirrorX: true },
      // crew door (z 7.3..9.9): one amber F10 door lamp at the lintel (under the kit floodlight housing), the human
      // ruler beside the 2.4 m door
      { slit: [12.44, -1.98, 8.62], u: [-0.143, 0, 0.99], n: [0.99, 0, 0.143], len: 0.6, width: 0.14, radiance: 1.4, color: 'amber', mirrorX: true },
      // aft door (z -17.0..-15.6): the same lamp under its floodlight housing (x 12.96..13.44, y -0.76..-0.41)
      { slit: [13.03, -0.88, -16.28], u: [0, 0, 1], n: [1, 0, 0], len: 0.6, width: 0.14, radiance: 1.4, color: 'amber', mirrorX: true },
      // mid-block forward joint (z 15.5): one amber bar in each recess corner where a chamfer meets the step face,
      // upper and lower, the concept's hard slits at a block joint (2.9 m and 3.9 m clear of the door ports)
      { slit: [9.45, 0.51, 15.55], u: [-0.49, 0.87, 0], n: [0.80, 0.45, 0.40], len: 1.3, width: 0.2, radiance: 1.3, color: 'amber', mirrorX: true },
      { slit: [9.92, -6.61, 15.55], u: [-0.49, -0.87, 0], n: [0.76, -0.43, 0.48], len: 1.0, width: 0.2, radiance: 1.4, color: 'amber', mirrorX: true },
      // sponsons: upright lamp-heads on the bevelled ends (aft outboard / inboard, forward outboard), the concept's
      // nacelle-corner bars
      { slit: [22.74, -3.35, -13.55], u: [0, 1, 0], n: [0.318, 0, -0.948], len: 1.8, width: 0.2, radiance: 1.7, color: 'amber', keep: true, mirrorX: true },
      { slit: [17.36, -3.35, -13.55], u: [0, 1, 0], n: [-0.318, 0, -0.948], len: 1.4, width: 0.2, radiance: 1.4, color: 'amber', keep: true, mirrorX: true },
      { slit: [22.78, -3.35, 0.65], u: [0, 1, 0], n: [0.717, 0, 0.697], len: 1.4, width: 0.2, radiance: 1.6, color: 'amber', keep: true, mirrorX: true },
      // bow: a short upright lamp on each outer bezel post (x 6.1..6.5)
      { slit: [6.31, -3.3, 35.92], u: [0, 1, 0], n: [0, 0, 1], len: 1.1, width: 0.19, radiance: 1.6, color: 'amber', keep: true, mirrorX: true },
      // stern plate: drive status, one slow cool lamp each side of the white stern light (2.1 m clear of it)
      { points: [[2.1, 3.95, -26.13]], color: 'cool', size: 0.2, intensity: 0.8, pulse: 2.4, mirrorX: true },
      // dorsal centreline: two slow amber masthead beacons (F6), clear of the hatch covers at x +-1.9 and 4.7 m forward
      // of the dorsal strobe; off the hatch rows they read as the craft's beacons, not as a hatch lamp
      { points: [[0, 6.95, -3.6], [0, 6.95, -12.0]], color: 'amber', size: 0.3, intensity: 1.0, pulse: 3.2 },
    ],
  },
  detail: {"set": "hull", "tile": 6, "normalStrength": 0.6, "roughAmount": 0.5, "cavity": 0.2},
  // Two-tone armour zones (?livery=tone|bone, livery.js SCHEMES; ship frame, metres): the flank sponsons, the
  // stern engine block (aft deck and flanks, z -26.4..-18.5 step) and the forward flank cheeks (hull stations
  // z 20.5..30.5, outboard of the top flat) take the light paint; the spine, bridge block and nose stay dark.
  liveryZones: [
    { box: [[16.6, -6.8, -14.0], [23.8, 0.1, 2.3]], mirrorX: true },   // sponsons (SP: x 20.05 +- 3.1, y -3.35 +- 2.8, z -13.4..0.2 + nose)
    { box: [[-14.0, -8.5, -26.6], [14.0, 5.6, -18.5]] },               // stern block to the deck step
    { box: [[6.4, -9.5, 20.5], [12.0, 3.2, 30.5]], mirrorX: true },    // forward flank cheeks
  ],
  length: 71.756,
  engines: [
    // main bells: bell-L x1.0143 (r 3.55)
    {p: [5.9, -0.049, -35.834], radius: 3.55, depth: 4.793, throat: 1.775, wall: [[0.685, 3.496], [1.369, 3.363], [2.054, 3.164], [2.739, 2.902], [3.423, 2.581], [4.108, 2.205]]},
    // main bells: bell-L x1.0143 (r 3.55)
    {p: [-5.9, -0.049, -35.834], radius: 3.55, depth: 4.793, throat: 1.775, wall: [[0.685, 3.496], [1.369, 3.363], [2.054, 3.164], [2.739, 2.902], [3.423, 2.581], [4.108, 2.205]]},
    // sponson bells: bell-S x0.9786 (r 1.37)
    {p: [20.05, -3.349, -16.618], radius: 1.37, depth: 1.85, throat: 0.685, wall: [[0.264, 1.349], [0.528, 1.299], [0.793, 1.221], [1.057, 1.12], [1.321, 0.996], [1.585, 0.851]]},
    // sponson bells: bell-S x0.9786 (r 1.37)
    {p: [-20.05, -3.349, -16.618], radius: 1.37, depth: 1.85, throat: 0.685, wall: [[0.264, 1.349], [0.528, 1.299], [0.793, 1.221], [1.057, 1.12], [1.321, 0.996], [1.585, 0.851]]},
  ],
  lights: [
    // steady sidelights on the outboard face of each sponson (beam extremity): red port, green starboard
    {p: [23.38, -3.399, -6.778], color: "red", size: 0.4},
    {p: [-23.38, -3.399, -6.778], color: "green", size: 0.4},
    // anti-collision strobes, alternating: dorsal spine aft and keel
    {p: [0.0, 7.161, -16.678], color: "white", size: 0.4, blink: {period: 1.3, duty: 0.1}},
    {p: [0.0, -10.349, -0.978], color: "white", size: 0.4, blink: {period: 1.3, duty: 0.1, phase: 0.5}},
    // steady stern light on the stern plate between the bell sockets
    {p: [0.0, 3.951, -26.258], color: "white", size: 0.4},
    // (v12: the v10 amber running lights moved into lightscape; v14: the red sidelight stands alone, no lamp within 2 m)
  ],
  anchors: {
    // railgun muzzles (twin-bore muzzle block face, z 17.86 in the model frame), fire along +Z
    muzzlePort: { p: [20.05, -3.399, 17.882], dir: [0, 0, 1] },
    muzzleStbd: { p: [-20.05, -3.399, 17.882], dir: [0, 0, 1] },
    // Flat hull faces for the composition step, measured on the remodelled hull by ray casts (0.5 m
    // grid along -normal, plane refit; flat = share of samples within 0.15 m of the plane).
    surfaces: {
      'flank-fore-port': { centre: [12.02, -3.25, 10.5], normal: [0.994, -0.026, 0.106], u: [-0.106, -0.001, 0.994], width: 7.0, height: 3.0, flat: 0.77 }, // vertical flank forward of the pylon (crew door at z 8.6)
      'flank-fore-stbd': { centre: [-12.02, -3.25, 10.5], normal: [-0.994, -0.027, 0.106], u: [-0.106, 0.001, -0.994], width: 7.0, height: 3.0, flat: 0.77 },
      'chamfer-port': { centre: [10.71, 3.16, -8.48], normal: [0.796, 0.605, 0.0], u: [0.0, 0.0, 1.0], width: 16.0, height: 5.0, flat: 1.0 }, // upper chamfer above the pylon: F-402 stencil, port row
      'chamfer-stbd': { centre: [-10.71, 3.15, -8.48], normal: [-0.796, 0.605, -0.001], u: [0.001, -0.001, -1.0], width: 16.0, height: 5.0, flat: 1.0 },
      'dorsal-deck': { centre: [0.0, 6.82, -9.98], normal: [0.0, 1.0, 0.006], u: [0.0, -0.006, 1.0], width: 5.0, height: 14.0, flat: 0.79 }, // dorsal spine between the radiator bays (six hatches)
      'bow-deck': { centre: [0.0, 1.52, 25.03], normal: [0.0, 0.983, 0.183], u: [0.0, -0.183, 0.983], width: 9.0, height: 12.0, flat: 1.0 }, // sloping forward deck ahead of the bridge
      'bridge-glazing': { centre: [0.0, 3.91, 15.86], normal: [0.0, 0.61, 0.792], u: [1.0, 0.0, 0.0], width: 5.5, height: 1.6, flat: 1.0 }, // bridge glazing recess on the raked front face, kit panes x1.0 (five)
      'belly': { centre: [0.0, -10.13, -1.98], normal: [0.0, -1.0, 0.0], u: [0.0, 0.0, 1.0], width: 16.0, height: 10.0, flat: 0.97 }, // flat belly
      'stern-plate': { centre: [0.0, 3.95, -26.03], normal: [0.0, 0.0, -1.0], u: [-1.0, 0.0, 0.0], width: 5.0, height: 1.2, flat: 1.0 }, // recessed stern plate above the bell sockets
      'sponson-outboard-port': { centre: [23.15, -3.4, -6.78], normal: [1.0, 0.0, 0.0], u: [0.0, 0.0, 1.0], width: 1.6, height: 2.8, flat: 1.0 }, // sponson outboard face between the vent bay and the equipment box
      'sponson-outboard-stbd': { centre: [-23.15, -3.4, -6.78], normal: [-1.0, 0.0, 0.0], u: [0.0, 0.0, -1.0], width: 1.6, height: 2.8, flat: 1.0 },
    },
  },
};
