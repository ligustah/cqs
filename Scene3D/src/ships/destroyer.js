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
// rails, finned cooling ridge, heavy clamp bands and the capacitor banks.
// v8 redesign (user feedback: 'massive tower, relatively little weaponisation'): the bridge tower is gone;
// a low armoured command block sits on the spine, crew live inside the armoured hull (rows of 1 m ports on
// 3 m decks).
// v9 polish: the command block carries a bridge slit under an armour visor and a CIC slit, applique armour,
// sensor fairings, docking collars and a designed sensor mast (a tapered trunk with four phased arrays, a
// railed gallery, a lattice section, the surveillance radar, a topmast with the masthead strobe and whip:
// the envelope top). Weapons: 12 kit turret-M with full-resolution guns (tools/blender/hulls/
// destroyer_assemble.py): bow A/B and aft X/Y with superfiring barbettes, X'/Y' ventral aft, two on
// flat-topped shoulder bastions and four in the broadside (two sponsons a side on the upper flank, the aft
// one superfiring), 28 flush VLS blocks (224 cells) in armoured coamings on open deck (bow, deckhouse roof,
// engine deck), point-defence clusters at bow, shoulders, stern, sponsons and on the command block.
// The aft superfiring X turret cannot fire forward over the command block: its arc is aft and abeam, as a
// sea-going ship's after turrets (A/B cover the forward arc, the shoulder and broadside guns the beam).
// Engines: kit bells (bell-L x1.237 corner bells: CORNER_BELL, bell-XL x1.106 centre dish) with the kit's
// documented engine entry (depth to the throat plate, throat, inner wall) times that scale.
// Lights: at the lenses of the kit nav-light housings.
// Assembled envelope 55.91 x 73.66 x 202.71 m (bbox centre [0.0, -7.358, -0.016] in the model frame; every
// coordinate below is shifted by minus that centre, as glbship.js centres the GLB).
export const meta = {
  "name": "Bastion-class destroyer",
  "designation": "DD-12",
  "crew": "about 2,000",
  "blurb": "Heavy line destroyer built around a massive spinal railgun: an armoured bow block with the heavy-collared muzzle, the barrel exposed in the gun gap between the bow block and the mid hull, a finned cooling spine with capacitor banks and clamp bands along the back, a low armoured command block with bridge and combat-centre slits under a lattice sensor mast, twelve twin turrets (superfiring batteries fore and aft, a ventral pair, shoulder bastions and a four-gun broadside on flank sponsons), 224 vertical launch cells, point-defence clusters, and five fusion bells in the stern."
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
  livery: {"gain": 0.05, "glassGlow": [0.06, 0.055, 0.046], "glassLit": 0.35, "mark": 0.18, "markSat": 0.3},
  detail: {"set": "hull", "tile": 6, "normalStrength": 0.6, "roughAmount": 0.5, "cavity": 0.2},
  // The exposed barrel in the gun gap keeps a muted version of its copper coils and bus bars instead of the
  // grey repaint, a little above the hull's value, so it reads as its own machinery (box stops short of the gap faces).
  liveryKeep: [{ box: [[-11.6, -20.042, 43.216], [11.6, -3.642, 54.616]], gain: 0.3, saturation: 0.6, feather: 0.5 }],
  // Muzzle rim: a dim, cool field-coil band just inside the lip of the octagonal shroud (one strip per face,
  // 0.9 m inside the lip, on the ray-cast shroud walls), so the gun's mouth reads as an octagon when the bow
  // face is in shadow. Radiance 0.07: a faint glint, not a lamp.
  fixtures: [
    { ...MUZZLE_RIM, p: [9.165, -11.192, 100.456], size: [6.60, 0.04, 0.12], rotZ: 1.5708 },
    { ...MUZZLE_RIM, p: [-9.165, -11.192, 100.456], size: [6.60, 0.04, 0.12], rotZ: -1.5708 },
    { ...MUZZLE_RIM, p: [0.0, -5.315, 100.456], size: [13.20, 0.04, 0.12], rotZ: 3.1416 },
    { ...MUZZLE_RIM, p: [0.0, -17.056, 100.456], size: [13.20, 0.04, 0.12], rotZ: 0 },
    { ...MUZZLE_RIM, p: [7.865, -6.615, 100.456], size: [3.68, 0.04, 0.12], rotZ: -0.7854 },
    { ...MUZZLE_RIM, p: [7.865, -15.756, 100.456], size: [3.68, 0.04, 0.12], rotZ: 0.7854 },
    { ...MUZZLE_RIM, p: [-7.865, -6.615, 100.456], size: [3.68, 0.04, 0.12], rotZ: 0.7854 },
    { ...MUZZLE_RIM, p: [-7.865, -15.756, 100.456], size: [3.68, 0.04, 0.12], rotZ: -0.7854 },
  ],
  length: 202.712,
  engines: [
    // corner bells, upper pair: bell-L x1.237 (r 4.33)
    { p: [13.45, -6.352, -101.304], mirrorX: true, ...CORNER_BELL },
    // corner bells, lower pair: bell-L x1.237 (r 4.33)
    { p: [13.45, -18.092, -101.304], mirrorX: true, ...CORNER_BELL },
    // centre dish: bell-XL x1.106 (r 7.74), lip 10.7 m forward of the corner lips
    {p: [0.0, -12.582, -90.584], radius: 7.742, depth: 10.452, throat: 3.871, wall: [[1.493, 7.626], [2.986, 7.336], [4.479, 6.899], [5.972, 6.329], [7.466, 5.63], [8.959, 4.809]]},
  ],
  lights: [
    // steady sidelights on the flat flank of the engine section (the beam extremity): red port, green starboard
    {p: [27.9, -12.342, -49.984], color: "red", size: 0.4},
    {p: [-27.9, -12.342, -49.984], color: "green", size: 0.4},
    // anti-collision strobes, alternating: the masthead (topmast cap) and the keel fin
    {p: [0.0, 31.638, -51.234], color: "white", size: 0.4, blink: { ...STROBE }},
    {p: [0.0, -29.672, -49.984], color: "white", size: 0.4, blink: { ...STROBE, phase: 0.5 }},
    // steady stern light on the stern plate above the centre dish
    {p: [0.0, -0.442, -85.214], color: "white", size: 0.4},
  ],
  anchors: {
    // Railgun, re-measured on the assembled hull: p = centre of the hexagonal bore opening on the barrel boss
    // face (bore floor at z 88.52), radius = inscribed bore radius, mouth = the shroud lip on the same axis.
    railgunMuzzle: { p: [0.0, -11.192, 95.849], dir: [0, 0, 1], radius: 2.71, mouth: [0.0, -11.192, 101.356] },
    // Flat hull faces for the composition step, measured on the remodelled hull by ray casts (0.5 m
    // grid along -normal, plane refit; flat = share of samples within 0.15 m of the plane).
    surfaces: {
      'engine-flank-port': { centre: [27.65, -12.84, -46.98], normal: [1.0, 0.0, 0.0], u: [0.0, 0.0, 1.0], width: 18.0, height: 9.0, flat: 0.93 }, // flat flank of the engine section ahead of the mid band (three port rows)
      'engine-flank-stbd': { centre: [-27.65, -12.84, -46.98], normal: [-1.0, 0.0, 0.0], u: [0.0, 0.0, -1.0], width: 18.0, height: 9.0, flat: 0.93 },
      'engine-flank-aft-port': { centre: [27.64, -12.84, -69.98], normal: [1.0, 0.0, 0.0], u: [0.0, 0.0, 1.0], width: 22.0, height: 9.0, flat: 0.93 },
      'engine-flank-aft-stbd': { centre: [-27.64, -12.84, -69.98], normal: [-1.0, 0.0, 0.0], u: [0.0, 0.0, -1.0], width: 22.0, height: 9.0, flat: 0.93 },
      'mid-flank-port': { centre: [17.46, -14.14, -1.98], normal: [1.0, -0.003, 0.0], u: [0.0, 0.0, 1.0], width: 18.0, height: 5.4, flat: 0.87 }, // mid-hull flank under the S2 sponson (two port rows)
      'mid-flank-stbd': { centre: [-17.46, -14.14, -1.98], normal: [-1.0, -0.003, 0.0], u: [0.0, 0.0, -1.0], width: 18.0, height: 5.4, flat: 0.86 },
      'boat-hatch-port': { centre: [17.16, -12.54, -18.98], normal: [1.0, 0.0, -0.003], u: [0.003, 0.0, 1.0], width: 5.8, height: 6.8, flat: 0.98 }, // boat hatch leaves (6 x 7 m opening, 1 x 2 m personnel door in the aft leaf)
      'boat-hatch-stbd': { centre: [-17.16, -12.54, -18.98], normal: [-1.0, 0.0, 0.003], u: [-0.003, 0.0, -1.0], width: 5.8, height: 6.8, flat: 0.98 },
      'bow-flank-port': { centre: [17.09, -10.84, 70.52], normal: [1.0, 0.0, 0.002], u: [-0.002, 0.0, 1.0], width: 24.0, height: 8.6, flat: 0.92 }, // bow block flank (two port rows)
      'bow-flank-stbd': { centre: [-17.09, -10.84, 70.52], normal: [-1.0, 0.0, 0.002], u: [-0.002, 0.0, -1.0], width: 24.0, height: 8.6, flat: 0.92 },
      'engine-deck': { centre: [0.0, 3.4, -80.48], normal: [0.0, 1.0, 0.0], u: [0.0, 0.0, 1.0], width: 5.0, height: 3.0, flat: 1.0 }, // engine-section deck aft of the aft turret
      'spine-top': { centre: [0.0, 2.57, 32.01], normal: [0.0, 1.0, -0.008], u: [1.0, 0.0, 0.0], width: 3.0, height: 20.0, flat: 0.37 }, // rail spine catwalk between the spine rails
      'gap-face-mid': { centre: [0.0, -10.64, 42.92], normal: [0.0, 0.0, 1.0], u: [-1.0, 0.0, 0.0], width: 4.0, height: 3.0, flat: 1.0 }, // gun-gap face of the mid hull (above the barrel)
      'command-front': { centre: [2.8, 10.09, -33.86], normal: [0.0, 0.445, 0.896], u: [1.0, 0.0, 0.0], width: 4.6, height: 1.6, flat: 1.0 }, // applique plate on the sloped casemate front between the CIC and bridge slits
      'command-aft': { centre: [0.0, 5.06, -61.51], normal: [0.0, 0.0, -1.0], u: [-1.0, 0.0, 0.0], width: 5.0, height: 2.0, flat: 0.4 }, // command block base, aft face between the two doors
      'command-roof': { centre: [0.0, 12.95, -46.48], normal: [0.0, 1.0, 0.0], u: [1.0, 0.0, 0.0], width: 6.0, height: 3.0, flat: 1.0 }, // casemate roof between the radome drum and the director
      'stern-plate': { centre: [0.0, -0.64, -84.98], normal: [0.0, 0.0, -1.0], u: [-1.0, 0.0, 0.0], width: 8.0, height: 1.0, flat: 1.0 }, // stern plate above the centre dish
    },
  },
};
