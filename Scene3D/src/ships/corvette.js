// Corvette K-214 — v3 REMODEL: clean hard-surface hull (tools/blender/hulls/corvette.py) rebuilt from
// measurements of the v7 fal / Tripo blueprint, textured in texture space (tools/blender/hulls/paint.py:
// light paint, plating seams and tone, PATINA plate tone, AO grime, edge wear, decals) and assembled with
// the Blender parts kit (tools/blender/specs/corvette-v3.json via tools/blender/assemble.py).
// The GLB is already in the ship frame (metres, bow +Z, dorsal +Y, port +X): rotate [0, 0, 0], length =
// the assembled bbox length. Node 'hull' is the hull, 'parts_*' the kit parts (hullNodes).
// Engines: kit bells (bell-L x1.463 centre, bell-M x1.114 / x1.064 upper / lower pairs, bell-L on each pod)
// with the kit's documented engine entry (depth to the throat plate, throat, inner wall) times that scale.
// Lights: at the lenses of the kit nav-light housings.
// Assembled envelope 69.46 x 46.71 x 108.13 m (bbox centre [0.0, -0.025, -0.014] in the model frame; every
// coordinate below is shifted by minus that centre, as glbship.js centres the GLB).
export const meta = {
  "name": "Warden-class corvette",
  "designation": "K-214",
  "crew": "about 350",
  "blurb": "Armoured escort corvette: a chamfered bow with four torpedo doors, a bridge house and a two-tier bridge tower, two twin-barrel dorsal gun mounts and a sensor mast, five fusion bells in the stern frame and two outrigger drive pods on pylons."
};

export const asset = {
  glb: "./assets/ships/corvette.glb",
  generator: "tools/blender/hulls/corvette.py (remodel of the tripo3d/h3.1/multiview-to-3d v7 hull) + tools/blender/assemble.py",
  concept: "./assets/concepts/corvette.webp",
  beauty: "./assets/concepts/corvette-beauty.webp",
  rotate: [0, 0, 0],
  hullNodes: ["hull"],
  livery: { gain: 0.05, glassGlow: [0.06, 0.055, 0.046], glassLit: 0.3 }, // remodel paint is lighter than the generated textures: gain 0.05 matches the fleet grey
  detail: {"set": "hull", "tile": 6, "normalStrength": 0.6, "roughAmount": 0.5, "cavity": 0.2},
  // Two-tone armour zones (?livery=tone|bone, livery.js SCHEMES; ship frame, metres): the outrigger drive pods, the
  // chamfered bow cap (forward of the deck slope, z 41.5) and the stern block below the main deck (aft of the
  // deckhouse end, z -38.8) take the light paint; the deckhouse, tower, spine and belly stay dark.
  liveryZones: [
    { box: [[24.2, -20.8, -29.2], [35.0, -9.1, -0.3]], mirrorX: true },  // drive pods (POD x 29.55 +- 4.9, y -14.95 +- 5.25)
    { box: [[-20.0, -25.0, 41.5], [20.0, -1.0, 55.0]] },                 // bow cap
    { box: [[-20.0, -25.0, -50.0], [20.0, -1.6, -38.8]] },               // stern block under the deck
  ],
  length: 108.129,
  engines: [
    // centre bell: bell-L x1.463 (r 5.12)
    {p: [0.0, -9.975, -52.586], radius: 5.12, depth: 6.912, throat: 2.56, wall: [[0.987, 5.043], [1.975, 4.851], [2.962, 4.563], [3.95, 4.185], [4.937, 3.723], [5.925, 3.18]]},
    // upper bells: bell-M x1.1136 (r 2.45)
    {p: [9.85, -5.415, -53.686], radius: 2.45, depth: 3.307, throat: 1.225, wall: [[0.472, 2.413], [0.945, 2.322], [1.418, 2.184], [1.89, 2.002], [2.362, 1.782], [2.835, 1.522]]},
    // upper bells: bell-M x1.1136 (r 2.45)
    {p: [-9.85, -5.415, -53.686], radius: 2.45, depth: 3.307, throat: 1.225, wall: [[0.472, 2.413], [0.945, 2.322], [1.418, 2.184], [1.89, 2.002], [2.362, 1.782], [2.835, 1.522]]},
    // lower bells: bell-M x1.0636 (r 2.34)
    {p: [9.8, -14.055, -54.036], radius: 2.34, depth: 3.159, throat: 1.17, wall: [[0.451, 2.305], [0.903, 2.218], [1.354, 2.086], [1.805, 1.912], [2.256, 1.702], [2.708, 1.454]]},
    // lower bells: bell-M x1.0636 (r 2.34)
    {p: [-9.8, -14.055, -54.036], radius: 2.34, depth: 3.159, throat: 1.17, wall: [[0.451, 2.305], [0.903, 2.218], [1.354, 2.086], [1.805, 1.912], [2.256, 1.702], [2.708, 1.454]]},
    // pod bells: bell-L (r 3.5)
    {p: [29.55, -14.925, -34.586], radius: 3.5, depth: 4.725, throat: 1.75, wall: [[0.675, 3.447], [1.35, 3.316], [2.025, 3.119], [2.7, 2.861], [3.375, 2.545], [4.05, 2.174]]},
    // pod bells: bell-L (r 3.5)
    {p: [-29.55, -14.925, -34.586], radius: 3.5, depth: 4.725, throat: 1.75, wall: [[0.675, 3.447], [1.35, 3.316], [2.025, 3.119], [2.7, 2.861], [3.375, 2.545], [4.05, 2.174]]},
  ],
  lights: [
    // steady sidelights on the flat outboard face of each pod (the beam extremity): red port, green starboard
    {p: [34.68, -14.925, -6.986], color: "red", size: 0.4},
    {p: [-34.68, -14.925, -6.986], color: "green", size: 0.4},
    // anti-collision strobes, alternating: keel and masthead (top of the sensor block)
    {p: [0.0, -23.305, 0.014], color: "white", size: 0.4, blink: {period: 1.3, duty: 0.1, phase: 0.5}},
    {p: [0.0, 23.325, -11.486], color: "white", size: 0.4, blink: {period: 1.3, duty: 0.1}},
    // steady stern light on the stern plate above the centre bell
    {p: [0.0, -3.075, -49.466], color: "white", size: 0.4},
    // v10 amber running lights along the hull lines: the armour belt and the tapered bow flank
    { p: [16.19, -14.28, -31.99], color: 'amber', size: 0.3, mirrorX: true },
    { p: [16.32, -14.28, -15.99], color: 'amber', size: 0.3, mirrorX: true },
    { p: [16.48, -14.28, 4.01], color: 'amber', size: 0.3, mirrorX: true },
    { p: [14.12, -7.37, 28.2], color: 'amber', size: 0.3, mirrorX: true },
    { p: [11.19, -7.37, 40.86], color: 'amber', size: 0.3, mirrorX: true },
  ],
  anchors: {
    // Flat hull faces for the composition step, measured on the remodelled hull by ray casts (0.5 m
    // grid along -normal, plane refit; flat = share of samples within 0.15 m of the plane).
    surfaces: {
      'flank-fore-port': { centre: [16.15, -8.03, 9.51], normal: [1.0, 0.0, 0.0], u: [0.0, 0.0, 1.0], width: 18.0, height: 6.6, flat: 1.0 }, // upper flank between the pylon and the bow taper (two port rows)
      'flank-fore-stbd': { centre: [-16.15, -8.03, 9.51], normal: [-1.0, 0.0, 0.0], u: [0.0, 0.0, -1.0], width: 18.0, height: 6.6, flat: 1.0 },
      'flank-aft-port': { centre: [15.74, -8.03, -35.99], normal: [1.0, 0.0, -0.018], u: [0.018, 0.0, 1.0], width: 17.0, height: 6.6, flat: 1.0 }, // upper flank aft of the pod
      'flank-aft-stbd': { centre: [-15.74, -8.03, -35.99], normal: [-1.0, 0.0, -0.018], u: [0.018, 0.0, -1.0], width: 17.0, height: 6.6, flat: 1.0 },
      'belt-port': { centre: [16.27, -14.28, -11.99], normal: [1.0, -0.025, -0.008], u: [0.008, 0.0, 1.0], width: 56.0, height: 5.0, flat: 0.87 }, // armour belt (0.22 m proud), crew-door bays at z 1.5 / 9.9 / -39.5
      'belt-stbd': { centre: [-16.27, -14.28, -11.99], normal: [-1.0, -0.025, -0.008], u: [0.008, 0.0, -1.0], width: 56.0, height: 5.0, flat: 0.87 },
      'flank-bow-port': { centre: [12.24, -9.97, 35.97], normal: [0.974, 0.025, 0.225], u: [-0.225, 0.0, 0.974], width: 26.0, height: 9.0, flat: 0.85 }, // tapered bow flank; K-214 at z 28-43
      'flank-bow-stbd': { centre: [-12.24, -9.97, 35.97], normal: [-0.974, 0.026, 0.225], u: [-0.225, 0.0, -0.974], width: 26.0, height: 9.0, flat: 0.85 },
      'shoulder-port': { centre: [14.73, -3.04, -11.99], normal: [0.739, 0.673, -0.007], u: [0.005, 0.005, 1.0], width: 30.0, height: 3.0, flat: 1.0 }, // shoulder chamfer from the flank to the walkway, clear stretch z -27..3 (vent bays at z 6-17 and -46..-40, launcher tubes at z -29..-37)
      'shoulder-stbd': { centre: [-14.73, -3.04, -11.99], normal: [-0.739, 0.673, -0.007], u: [0.005, -0.005, -1.0], width: 30.0, height: 3.0, flat: 1.0 },
      'deck-walk-port': { centre: [11.7, -1.44, -5.99], normal: [0.0, 1.0, 0.0], u: [0.0, 0.0, 1.0], width: 44.0, height: 2.0, flat: 1.0 }, // walkway outboard of the deckhouse (deck-edge rails)
      'deck-walk-stbd': { centre: [-11.7, -1.44, -5.99], normal: [0.0, 1.0, 0.0], u: [0.0, 0.0, 1.0], width: 44.0, height: 2.0, flat: 1.0 },
      'deckhouse-side-port': { centre: [9.14, 1.01, -11.99], normal: [0.893, 0.45, -0.001], u: [0.001, 0.0, 1.0], width: 36.0, height: 4.4, flat: 1.0 }, // sloped deckhouse side (ports, ladders)
      'deckhouse-side-stbd': { centre: [-9.14, 1.01, -11.99], normal: [-0.893, 0.449, -0.001], u: [0.001, 0.0, -1.0], width: 36.0, height: 4.4, flat: 1.0 },
      'dorsal-deck': { centre: [0.0, 3.48, 13.01], normal: [0.0, 1.0, -0.003], u: [0.0, 0.003, 1.0], width: 6.0, height: 10.0, flat: 1.0 }, // deckhouse roof between the forward turret and the bridge
      'stern-deck': { centre: [0.0, -1.44, -43.99], normal: [0.0, 1.0, 0.0], u: [0.0, 0.0, 1.0], width: 9.0, height: 20.0, flat: 1.0 }, // main deck aft of the deckhouse
      'bow-deck': { centre: [0.0, -3.37, 39.98], normal: [0.0, 0.989, 0.15], u: [0.0, -0.15, 0.989], width: 12.0, height: 8.0, flat: 1.0 }, // sloping bow deck (hatch plate, vent ramps)
      'bridge-glazing': { centre: [0.0, 1.38, 23.61], normal: [0.0, 0.0, 1.0], u: [1.0, 0.0, 0.0], width: 5.0, height: 1.2, flat: 0.6 }, // bridge glazing recess back wall (vertical, 0.9 m in from the glacis at the band top), kit panes
      'tower-front': { centre: [0.0, 8.18, -5.72], normal: [0.0, 0.0, 1.0], u: [1.0, 0.0, 0.0], width: 9.0, height: 2.2, flat: 1.0 }, // vertical tier of the tower front
      'tower-side-port': { centre: [5.95, 8.18, -10.99], normal: [1.0, 0.0, 0.0], u: [0.0, 0.0, 1.0], width: 8.0, height: 2.2, flat: 1.0 },
      'tower-side-stbd': { centre: [-5.95, 8.18, -10.99], normal: [-1.0, 0.0, 0.0], u: [0.0, 0.0, -1.0], width: 8.0, height: 2.2, flat: 1.0 },
      'tower-glazing': { centre: [0.0, 11.54, -5.34], normal: [0.0, -0.605, 0.796], u: [1.0, 0.0, 0.0], width: 9.0, height: 1.5, flat: 1.0 }, // leaning tower glazing (faces forward and down), recessed 0.3 m
      'stern-plate': { centre: [0.0, -2.88, -49.24], normal: [0.0, 0.0, -1.0], u: [-1.0, 0.0, 0.0], width: 8.0, height: 0.8, flat: 1.0 }, // recessed stern plate strip above the centre bell boss
      'pod-outboard-port': { centre: [34.46, -14.93, -4.99], normal: [1.0, 0.0, -0.001], u: [0.001, 0.0, 1.0], width: 6.0, height: 5.0, flat: 1.0 }, // pod outboard face forward of the radiator bay
      'pod-outboard-stbd': { centre: [-34.46, -14.93, -4.99], normal: [-1.0, 0.0, -0.001], u: [0.001, 0.0, -1.0], width: 6.0, height: 5.0, flat: 1.0 },
    },
  },
};
