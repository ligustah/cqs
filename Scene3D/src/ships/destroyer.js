// Destroyer DD-12 — v3 REMODEL: clean hard-surface hull (tools/blender/hulls/destroyer.py) rebuilt from
// measurements of the fal / Tripo H3.1 blueprint (the v5 true-scale-details hull), painted in texture space
// (tools/blender/hulls/destroyer_paint.py: light paint, plating seams and tone, varied access panels, PATINA
// plate tone, AO grime, edge wear, decals incl. the DD-12 stencils) at 8192 px, and assembled with the Blender
// parts kit (tools/blender/specs/destroyer-v3.json via tools/blender/assemble.py).
// The GLB is in the ship frame at the RENDERED size (metres, bow +Z, dorsal +Y, port +X): rotate [0, 0, 0],
// length = the assembled bbox length, so the 12-slot class correction stays ~1.0. Node 'hull' is the hull,
// 'parts_*' the kit parts (hullNodes).
// The spinal railgun is modelled parametrically (the kit's railgun-segment would have to be scaled x2.3 to
// the blueprint's 6 m bore, blowing its hatches and walkways up to giant size): the octagonal muzzle shroud
// (18.4 x 11.8 m, 13.8 m deep) with a barrel boss and a hexagonal bore, the barrel exposed in the gap between
// the mid hull and the bow block (liner, two rail bars, clamp rings, copper-wound coil packs, cable
// conduits, walkways with 1 x 2 m doors, ladders and hand rails at true scale), the dorsal spine with its
// rails and the capacitor banks.
// Engines: kit bells (bell-L x1.237 corner bells: CORNER_BELL, bell-XL x1.106 centre dish) with the kit's
// documented engine entry (depth to the throat plate, throat, inner wall) times that scale.
// Lights: at the lenses of the kit nav-light housings.
// Assembled envelope 55.91 x 73.95 x 202.71 m (bbox centre [0.0, -0.107, -0.016] in the model frame; every
// coordinate below is shifted by minus that centre, as glbship.js centres the GLB).
export const meta = {
  "name": "Bastion-class destroyer",
  "designation": "DD-12",
  "crew": "about 2,000",
  "blurb": "Heavy line destroyer built around a massive spinal railgun: an armoured bow block with the recessed muzzle, the barrel exposed in the gun gap between the bow block and the mid hull, a rail spine with capacitor banks along the back, a many-deck bridge tower, naval turrets fore, aft and in flank sponsons, louvred intakes on the engine section and five fusion bells in the stern."
};

const STROBE = { period: 1.3, duty: 0.1 };
const MUZZLE_RIM = { color: '#b4c2dc', radiance: 0.07 };
// corner bells: kit bell-L x1.237 (exit r 4.33, the blueprint's inner-wall fit); depth to the throat plate,
// throat and inner wall are the kit's documented engine entry times that scale
const CORNER_BELL = { radius: 4.33, depth: 5.845, throat: 2.165, wall: [[0.835, 4.264], [1.67, 4.102], [2.505, 3.858], [3.34, 3.539], [4.175, 3.148], [5.01, 2.689]] };

export const asset = {
  glb: "./assets/ships/destroyer.glb",
  generator: "tools/blender/hulls/destroyer.py (remodel of the tripo3d/h3.1/multiview-to-3d hull) + tools/blender/assemble.py",
  concept: "./assets/concepts/destroyer.webp",
  beauty: "./assets/concepts/destroyer-beauty.webp",
  rotate: [0, 0, 0],
  hullNodes: ["hull"],
  livery: {"gain": 0.05, "glassGlow": [0.06, 0.055, 0.046], "glassLit": 0.35},
  detail: {"set": "hull", "tile": 6, "normalStrength": 0.6, "roughAmount": 0.5, "cavity": 0.2},
  // The exposed barrel in the gun gap keeps a muted version of its copper coils and bus bars instead of the
  // grey repaint, a little above the hull's value, so it reads as its own machinery (box stops short of the gap faces).
  liveryKeep: [{ box: [[-11.6, -27.293, 43.216], [11.6, -10.893, 54.616]], gain: 0.3, saturation: 0.6, feather: 0.5 }],
  // Muzzle rim: a dim, cool field-coil band just inside the lip of the octagonal shroud (one strip per face,
  // 0.9 m inside the lip, on the ray-cast shroud walls), so the gun's mouth reads as an octagon when the bow
  // face is in shadow. Radiance 0.07: a faint glint, not a lamp.
  fixtures: [
    { ...MUZZLE_RIM, p: [9.165, -18.443, 100.456], size: [6.60, 0.04, 0.12], rotZ: 1.5708 },
    { ...MUZZLE_RIM, p: [-9.165, -18.443, 100.456], size: [6.60, 0.04, 0.12], rotZ: -1.5708 },
    { ...MUZZLE_RIM, p: [0.0, -12.569, 100.456], size: [13.20, 0.04, 0.12], rotZ: 3.1416 },
    { ...MUZZLE_RIM, p: [0.0, -24.309, 100.456], size: [13.20, 0.04, 0.12], rotZ: 0 },
    { ...MUZZLE_RIM, p: [7.865, -13.869, 100.456], size: [3.68, 0.04, 0.12], rotZ: -0.7854 },
    { ...MUZZLE_RIM, p: [7.865, -23.009, 100.456], size: [3.68, 0.04, 0.12], rotZ: 0.7854 },
    { ...MUZZLE_RIM, p: [-7.865, -13.869, 100.456], size: [3.68, 0.04, 0.12], rotZ: 0.7854 },
    { ...MUZZLE_RIM, p: [-7.865, -23.009, 100.456], size: [3.68, 0.04, 0.12], rotZ: -0.7854 },
  ],
  length: 202.711,
  engines: [
    // corner bells, upper pair: bell-L x1.237 (r 4.33)
    { p: [13.45, -13.603, -101.304], mirrorX: true, ...CORNER_BELL },
    // corner bells, lower pair: bell-L x1.237 (r 4.33)
    { p: [13.45, -25.343, -101.304], mirrorX: true, ...CORNER_BELL },
    // centre dish: bell-XL x1.106 (r 7.74), lip 10.7 m forward of the corner lips
    {p: [0.0, -19.833, -90.584], radius: 7.742, depth: 10.452, throat: 3.871, wall: [[1.493, 7.626], [2.986, 7.336], [4.479, 6.899], [5.972, 6.329], [7.466, 5.63], [8.959, 4.809]]},
  ],
  lights: [
    // steady sidelights on the flat flank of the engine section (the beam extremity): red port, green starboard
    {p: [27.9, -19.593, -49.984], color: "red", size: 0.4},
    {p: [-27.9, -19.593, -49.984], color: "green", size: 0.4},
    // anti-collision strobes, alternating: tower roof ahead of the dome and the keel fin under the tower
    {p: [0.0, 26.337, -34.284], color: "white", size: 0.4, blink: { ...STROBE }},
    {p: [0.0, -36.923, -49.984], color: "white", size: 0.4, blink: { ...STROBE, phase: 0.5 }},
    // steady stern light on the stern plate above the centre dish
    {p: [0.0, -7.693, -85.214], color: "white", size: 0.4},
  ],
  anchors: {
    // Railgun, re-measured on the assembled hull: p = centre of the hexagonal bore opening on the barrel boss
    // face (bore floor at z 88.52), radius = inscribed bore radius, mouth = the shroud lip on the same axis.
    railgunMuzzle: { p: [0.0, -18.443, 95.849], dir: [0, 0, 1], radius: 2.71, mouth: [0.0, -18.443, 101.356] },
    // Flat hull faces for the composition step, measured on the remodelled hull by ray casts (0.5 m
    // grid along -normal, plane refit; flat = share of samples within 0.15 m of the plane).
    surfaces: {
      'engine-flank-port': { centre: [27.66, -20.09, -46.98], normal: [1.0, 0.0, 0.0], u: [0.0, 0.0, 1.0], width: 18.0, height: 9.0, flat: 0.93 }, // flat flank of the engine section ahead of the mid band (three port rows)
      'engine-flank-stbd': { centre: [-27.66, -20.09, -46.98], normal: [-1.0, 0.0, 0.0], u: [0.0, 0.0, -1.0], width: 18.0, height: 9.0, flat: 0.93 },
      'engine-flank-aft-port': { centre: [27.66, -20.09, -69.98], normal: [1.0, 0.0, 0.0], u: [0.0, 0.0, 1.0], width: 22.0, height: 9.0, flat: 0.93 },
      'engine-flank-aft-stbd': { centre: [-27.66, -20.09, -69.98], normal: [-1.0, 0.0, 0.0], u: [0.0, 0.0, -1.0], width: 22.0, height: 9.0, flat: 0.93 },
      'mid-flank-port': { centre: [17.48, -19.89, -1.98], normal: [1.0, -0.001, 0.0], u: [0.0, 0.0, 1.0], width: 18.0, height: 8.6, flat: 0.92 }, // mid-hull flank between the boat hatch and the sponson (three port rows, cobalt band)
      'mid-flank-stbd': { centre: [-17.48, -19.89, -1.98], normal: [-1.0, -0.001, 0.0], u: [0.0, 0.0, -1.0], width: 18.0, height: 8.6, flat: 0.92 },
      'boat-hatch-port': { centre: [17.16, -19.79, -18.98], normal: [1.0, 0.0, -0.003], u: [0.003, 0.0, 1.0], width: 5.8, height: 6.8, flat: 0.98 }, // boat hatch leaves (6 x 7 m opening, 1 x 2 m personnel door in the aft leaf)
      'boat-hatch-stbd': { centre: [-17.16, -19.79, -18.98], normal: [-1.0, 0.0, 0.003], u: [-0.003, 0.0, -1.0], width: 5.8, height: 6.8, flat: 0.98 },
      'bow-flank-port': { centre: [17.1, -18.09, 70.52], normal: [1.0, 0.0, 0.002], u: [-0.002, 0.0, 1.0], width: 24.0, height: 8.6, flat: 0.93 }, // bow block flank (two port rows)
      'bow-flank-stbd': { centre: [-17.1, -18.09, 70.52], normal: [-1.0, 0.0, 0.002], u: [-0.002, 0.0, -1.0], width: 24.0, height: 8.6, flat: 0.93 },
      'engine-deck': { centre: [0.0, -4.14, -80.48], normal: [0.0, 0.999, 0.033], u: [0.0, -0.033, 0.999], width: 5.0, height: 3.0, flat: 1.0 }, // engine-section deck aft of the aft turret
      'spine-top': { centre: [0.0, -5.39, 32.02], normal: [0.0, 1.0, 0.0], u: [1.0, 0.0, 0.0], width: 3.0, height: 20.0, flat: 1.0 }, // rail spine catwalk between the spine rails
      'gap-face-mid': { centre: [0.0, -17.89, 42.92], normal: [0.0, 0.0, 1.0], u: [-1.0, 0.0, 0.0], width: 4.0, height: 3.0, flat: 1.0 }, // gun-gap face of the mid hull (above the barrel)
      'tower-front': { centre: [0.0, 13.11, -31.47], normal: [0.0, 0.0, 1.0], u: [1.0, 0.0, 0.0], width: 14.0, height: 1.6, flat: 1.0 }, // bridge tower front between two glazed rows
      'tower-side-port': { centre: [10.5, 13.41, -40.48], normal: [1.0, 0.0, 0.0], u: [0.0, 0.0, 1.0], width: 12.0, height: 1.6, flat: 1.0 },
      'tower-side-stbd': { centre: [-10.5, 13.41, -40.48], normal: [-1.0, 0.0, 0.0], u: [0.0, 0.0, -1.0], width: 12.0, height: 1.6, flat: 1.0 },
      'stern-plate': { centre: [0.0, -7.89, -84.98], normal: [0.0, 0.0, -1.0], u: [-1.0, 0.0, 0.0], width: 8.0, height: 1.0, flat: 1.0 }, // stern plate above the centre dish
    },
  },
};
