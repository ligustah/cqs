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
  "blurb": "Heavy space-superiority fighter: a faceted armoured pod with a low bridge block glazed in a band of small panes, twin fusion bells in an armoured stern block and a twin railgun on each flank sponson, each sponson ending in a small secondary drive bell."
};

export const asset = {
  glb: "./assets/ships/fighter.glb",
  generator: "tools/blender/hulls/fighter.py (remodel of the tripo3d/h3.1/multiview-to-3d hull) + tools/blender/assemble.py",
  concept: "./assets/concepts/fighter.webp",
  beauty: "./assets/concepts/fighter-beauty.webp",
  rotate: [0, 0, 0],
  hullNodes: ["hull"],
  livery: {"gain": 0.05, "glassGlow": [0.06, 0.055, 0.046], "glassLit": 0.3},
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
    // v10 amber running lights along the hull lines: the upper chamfer (ends of the stencil row) and the forward flank
    { p: [10.77, 3.21, -15.88], color: 'amber', size: 0.3, mirrorX: true },
    { p: [10.77, 3.21, -1.08], color: 'amber', size: 0.3, mirrorX: true },
    { p: [11.76, -2.36, 13.69], color: 'amber', size: 0.3, mirrorX: true },
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
      'bridge-glazing': { centre: [0.0, 3.91, 15.86], normal: [0.0, 0.61, 0.792], u: [1.0, 0.0, 0.0], width: 5.5, height: 1.6, flat: 1.0 }, // bridge glazing recess on the raked front face, kit panes x0.7
      'belly': { centre: [0.0, -10.13, -1.98], normal: [0.0, -1.0, 0.0], u: [0.0, 0.0, 1.0], width: 16.0, height: 10.0, flat: 0.97 }, // flat belly
      'stern-plate': { centre: [0.0, 3.95, -26.03], normal: [0.0, 0.0, -1.0], u: [-1.0, 0.0, 0.0], width: 5.0, height: 1.2, flat: 1.0 }, // recessed stern plate above the bell sockets
      'sponson-outboard-port': { centre: [23.15, -3.4, -6.78], normal: [1.0, 0.0, 0.0], u: [0.0, 0.0, 1.0], width: 1.6, height: 2.8, flat: 1.0 }, // sponson outboard face between the vent bay and the equipment box
      'sponson-outboard-stbd': { centre: [-23.15, -3.4, -6.78], normal: [-1.0, 0.0, 0.0], u: [0.0, 0.0, -1.0], width: 1.6, height: 2.8, flat: 1.0 },
    },
  },
};
