// Fleet carrier CV-50 — v3 REMODEL: clean hard-surface hull (tools/blender/hulls/carrier.py, dimensions in
// carrier_dims.py) rebuilt from measurements of the fal / Tripo H3.1 blueprint (the v5 hull), painted in
// texture space at 8192 px (tools/blender/hulls/carrier_paint.py: light paint, plating seams and tone, varied
// access panels, PATINA plate tone, AO grime, edge wear, decals incl. the CV-50 stencils, 15 m letters) and
// assembled with the Blender parts kit (tools/blender/specs/carrier-v3.json via tools/blender/assemble.py).
// A 900 m design (never carried itself, so no hangar-slot normalisation: the class scale correction is 1).
// The GLB is in the ship frame (metres, bow +Z, dorsal +Y, port +X), built symmetric about x = 0 (the
// blueprint sat 0.9 m to port, so every old centre-line coordinate x ~ +0.9 is x = 0 here) with its bbox
// centre at the origin: rotate [0, 0, 0], length = the bbox length. Node 'hull' is the hull, 'parts_*' the kit.
// Assembled envelope 406.04 x 319.33 x 900.00 m (bbox centre [0.0, 0.0, 0.001]; every coordinate below is
// shifted by minus that centre, as glbship.js centres the GLB). Everything below is measured on the assembled
// remodel by tools/blender/hulls/carrier_module.py (ray casts), as the other remodels' modules are.
// - Hangar: one through-deck bay from the back wall (z -276) to the bow mouth (lip z 421.4). Along the flanks it is
//   open between the stern block, five 24 m frame rings and the bow section (six bays per side, flank plating at
//   x = +-121, frame posts and end blocks at +-131). Decks (the lower slab's top, heights kept from the v5
//   module): aft bay -92.45, bays 5-2 -96.35 (continuous under frames F2-F4), bay 1 -93.61, bow section -90.97;
//   sills of F1 / F5 -91.9. Ceilings: bays -0.6 (with transverse girders to -3.2 and crane gantries to -4.7),
//   frame rings -5.7, bow section -6.4. Walls of the rings, the back recess and the bow section at x = +-95 with
//   45-degree chamfers. anchors.hangar (155.8 x 84.4 x 670 m) stands on the bow-section deck inside every chamfer,
//   ring and ceiling, as before.
// - Drive: six kit bell-XL (x2.614 upper / lower, r 18.3; x2.7 outboard, r 18.9) at the blueprint's circle fits,
//   exit planes on z -450, in collars on the stern plate; depth / throat / wall = the kit's engine entry x scale.
// - Lights sit 8 cm proud of the surface. Nav path (lights[]): the five nav lights and white outline markers on the
//   deck-edge chamfer every 75 m. Amber lamps every 25 m between them, at mid-height (y -50) on the frame posts'
//   capital band and the end blocks, and on the sponsons' outer faces (lightscape); eleven slow amber beacons on the
//   dorsal centreline, block tops, sponsons and island roofs; a cool drive-status bar and amber corner strips on the
//   stern plate; amber corner markers at the outer corners of the frame posts, the stern block and the sponsons, none on
//   the drive collars or in the posts' door-shaped recesses (a lit recess edge is a door, and shrinks the post). Lit ports: grouped runs of 1 m window points on real glass (ray-cast) on the flank port grids of the
//   stern block and bow section and on the keel wedge; the island is lit by its own glass (livery). No automatic lamp
//   sits within 1.5 m of glass (zones): a lamp on a port band's lip reads as one more, larger window.
// - v14 fleet lighting scale standard (one fixture, one size on every hull; lamps where a fixture has a job; windows
//   only on real glass at the 1 m port size). The carrier's lamps had been scaled up with the hull (pins 0.45-0.7 m,
//   bars 0.65-1.4 m wide): a 0.87 m bright band in a recess reads as a row of 1 m windows and the 130 m bow face shrinks
//   to a 30-40 m one. Now every lamp is the size it is on the fighter and destroyer (pins 0.22-0.28 m, automatic bars
//   0.2 m wide, joint strips 0.26-0.30 m, hangar lamps 0.26 m, 1.5-2 m lamp bars), so a lamp is 1/3000 of the hull and
//   the hull reads 900 m long; it reads busy through its lit bays, island and frame strips, not through glitter.
// - Hangar floodlights and strips as before (see the v5 notes): six spots under the frame rings and in the bow
//   section, light-linked to the hangar by interiorLightGate, plus interiorBounce; emissive strips across every
//   bay ceiling and down every bay-facing frame face.
export const meta = {
  "name": "Keystone-class fleet carrier",
  "designation": "CV-50",
  "crew": "about 20,000",
  "blurb": "Warp-capable fleet carrier: a 900 m armoured box hull around one through-deck hangar that opens at the bow mouth and through six framed bays along each flank, with a stepped island, twin-gun turrets along the spine and on two stern sponsons, and six fusion bells in the stern block."
};

const STROBE = { period: 1.3, duty: 0.1 };
const RUN = 0.4; // nav and outline light size (m): the same 0.4 m as every nav light on every hull
// window point: a 1 m port drawn as a lightscape point (sprite 2 x size = the glass); portDim, never keep, so it fades
// with its true area far off instead of growing into a 5-10 m blob (effects.js, window energy floor)
const WIN = { color: 'portDim', size: 0.5 };
// amber running lamp at the fleet pin size (lightscape: it thins and fades with range like every other lamp)
const LAMP = { color: 'amber', size: 0.26, intensity: 0.9 };

// dorsal deck edge: white outline markers every 75 m (nav path), amber lamps every 25 m between them (top of the
// deck-edge chamfer)
const DECK_EDGE = [[102.19, 18.95, -255.0], [-102.19, 18.95, -255.0], [100.15, 20.96, -180.0], [-100.15, 20.96, -180.0], [102.19, 18.95, -105.0], [-102.19, 18.95, -105.0], [102.19, 18.95, -30.0], [-102.19, 18.95, -30.0], [102.19, 18.95, 45.0], [-102.19, 18.95, 45.0], [102.19, 18.95, 120.0], [-102.19, 18.95, 120.0], [100.15, 20.96, 195.0], [-100.15, 20.96, 195.0], [102.19, 18.95, 270.0], [-102.19, 18.95, 270.0], [100.16, 20.92, 345.0], [-100.16, 20.92, 345.0]];
const EDGE_RUN = [[100.16, 20.92, -355.0], [-100.16, 20.92, -355.0], [100.16, 20.92, -305.0], [-100.16, 20.92, -305.0], [100.16, 20.92, -280.0], [-100.16, 20.92, -280.0], [102.19, 18.95, -230.0], [-102.19, 18.95, -230.0], [102.19, 18.95, -205.0], [-102.19, 18.95, -205.0], [102.19, 18.95, -155.0], [-102.19, 18.95, -155.0], [102.19, 18.95, -130.0], [-102.19, 18.95, -130.0], [100.15, 20.96, -80.0], [-100.15, 20.96, -80.0], [102.19, 18.95, -55.0], [-102.19, 18.95, -55.0], [100.15, 20.96, -5.0], [-100.15, 20.96, -5.0], [102.16, 18.92, 20.0], [-102.16, 18.92, 20.0], [102.19, 18.95, 70.0], [-102.19, 18.95, 70.0], [100.15, 20.96, 95.0], [-100.15, 20.96, 95.0], [102.19, 18.95, 145.0], [-102.19, 18.95, 145.0], [102.19, 18.95, 170.0], [-102.19, 18.95, 170.0], [102.19, 18.95, 220.0], [-102.19, 18.95, 220.0], [102.19, 18.95, 245.0], [-102.19, 18.95, 245.0], [100.16, 20.92, 295.0], [-100.16, 20.92, 295.0], [100.16, 20.92, 320.0], [-100.16, 20.92, 320.0], [100.16, 20.92, 370.0], [-100.16, 20.92, 370.0], [100.16, 20.92, 395.0], [-100.16, 20.92, 395.0]];
// flanks at mid-height (y -50): stern block, the five frame posts' capital band, bow section; sponson outer faces
const FLANK = [[202.83, -50.0, -300.0], [-202.83, -50.0, -300.0], [131.9, -50.0, -268.0], [-131.9, -50.0, -268.0], [131.06, -50.0, -176.2], [-131.06, -50.0, -176.2], [131.06, -50.0, -85.75], [-131.06, -50.0, -85.75], [131.06, -50.0, 6.97], [-131.06, -50.0, 6.97], [131.06, -50.0, 99.51], [-131.06, -50.0, 99.51], [131.06, -50.0, 190.1], [-131.06, -50.0, 190.1], [131.06, -50.0, 290.0], [-131.06, -50.0, 290.0], [131.06, -50.0, 350.0], [-131.06, -50.0, 350.0], [131.06, -50.0, 410.0], [-131.06, -50.0, 410.0]];
const SPONSON_RUN = [[202.83, -46.0, -330.0], [-202.83, -46.0, -330.0], [202.83, -46.0, -290.0], [-202.83, -46.0, -290.0]];

// hangar: ports every 12.5 m along the bow section's inner walls; amber lamps along the mouth's lintel.
// (v14: window points, dim and half of them dark (skip); the mouth's sill lamps went: they sat on the sill chaser's own
// lamps. The bay-facing frame faces' gallery ports carry no window points: the livery already lights 40 % of that
// glass, and a second lit layer on it is the double lighting that took ISLAND_PORTS out)
const FRAME_FACES = [[-261.02, 1], [-188.09, -1], [-164.27, 1], [-98.0, -1], [-73.49, 1], [-5.24, -1], [19.21, 1], [87.42, -1], [111.6, 1], [178.09, -1], [202.12, 1], [275.99, -1]];
const POSTS = [-176.2, -85.75, 6.97, 99.51, 190.1]; // frame post centres (z)
const BOW_WALL = Array.from({ length: 11 }, (_, i) => 285 + i * 12.5).flatMap((z) => [[94.93, -48, z], [-94.93, -48, z]]);
const MOUTH_RIM = [-80, -40, 0, 40, 80].map((x) => [x, -3, 421.5]);

// Hangar light strips (emissive fixtures, see glbship.js): three 150 m strips across each bay ceiling (ray-cast
// ceilings, between the girders) and the bow section, and a 64 m vertical strip on every bay-facing frame face (x +-108.5,
// between the gallery ports, 0.25 m off the face). Radiance ~1.8 (ceiling) / 0.9 (posts).
// (v12: warm, ~3500 K, and a little dimmer: the bay glows warm as in the concept instead of a flat grey-white)
const STRIP = { color: '#ffd4a2', radiance: 1.5 };
const POST_STRIP = { color: '#ffc58a', radiance: 0.8 };
const BAY_CEILINGS = [[-260.5, -188.6, -0.58], [-163.8, -98.5, -0.58], [-73.0, -5.8, -0.58], [19.7, 86.9, -0.58], [112.1, 177.6, -0.58], [202.6, 275.5, -0.58], [276.8, 415.0, -6.39]];
// (v12 apply: every ceiling strip is five 18 m lamp bars 30 m apart and every frame-face tube three 6 m lamps, so the
// bays read as lamp-lit rooms with dark gaps instead of neon lines; short lamps run a little hotter)
// (v14: fleet-size lamps. Each 18 m ceiling bar is now five 2 x 0.3 m high-bay lamps at 4 m pitch and each 6 m tube two
// 1.5 x 0.3 m lamps: a grid of long tubes has no built-in scale and made a 90 m ceiling read as a 3 m car park, and a
// 6 m tube in a dark bay read as a slot window. Many small, human-size lamps make the bays read as vast halls up close;
// far off the dashed lines stay)
const STRIPS = [
  ...BAY_CEILINGS.flatMap(([z0, z1, y]) => [1 / 6, 1 / 2, 5 / 6].flatMap((f) => [-60, -30, 0, 30, 60].flatMap((x) => [-8, -4, 0, 4, 8].map((dx) => ({ ...STRIP, p: [x + dx, y - 0.35, z0 + (z1 - z0) * f], size: [2, 0.3, 0.3] }))))),
  // (fix 2: the post pair 5 m apart, a 3.5 m gap: at 3 m pitch the pair read as one split slot 4.5 m tall far off, the
  // old tube again; F16, lamp bars at 4 m pitch or more)
  ...FRAME_FACES.flatMap(([z, s]) => [108.5, -108.5].flatMap((x) => [-20, -47, -74].flatMap((y) => [-2.5, 2.5].map((dy) => ({ ...POST_STRIP, radiance: 1.3, p: [x, y + dy, z + s * 0.25], size: [0.3, 1.5, 0.1] }))))),
];

// hangar floodlights: under the five frame rings (ray-cast ring ceilings) and in the bow section
// (v12: ~3500 K sodium-warm work light instead of #fff3e8, 52000 -> 36000 cd, a narrower cone with a long penumbra
// (64 -> 46 deg, 0.55 -> 0.85) so each lamp throws a pool on the deck with dimmer deck between the pools)
// (v14: the emissive lens is the fleet floodlight housing, 0.5 m across (fixture = its radius); at 3 m it was the one
// lamp still scaled with the hull, a spotlight head as long as the 2 m ceiling lamps beside it that shrank the 85 m
// hangar ceiling. The pools on the deck are unchanged)
const FLOOD = { kind: 'spot', color: '#ffc68c', intensity: 36000, distance: 240, angle: 46, penumbra: 0.85, fixture: 0.25 };
const RING_CEIL = [[-176.2, -5.71], [-85.75, -5.71], [6.97, -5.71], [99.51, -5.71], [190.1, -5.71]];

// v12 apply: lit compartments on the stern block's and bow section's flank port grids (1.1 x 0.9 m ports, 2.5 m apart,
// rows 3 m apart; ray-cast): a few runs of 3-6 neighbouring ports on one deck, the rest dark, instead of the painted
// grid glowing everywhere (the livery glass glow is off on these flanks, glassDark). [row y, first column, count];
// the starboard flank takes the same runs mirrored end for end so the two sides do not match exactly.
const BOW_PORT_Z = [280.95, 288.5, 290.95, 303, 305.45, 308, 310.55, 313, 315.45, 317.95, 320.55, 323, 325.45, 327.95, 330.55, 333, 335.45, 337.95, 340.55, 343.05, 345.45, 348.05, 350.55, 353.05, 355.45, 358, 360.55, 363.05, 365.45, 368, 370.55, 373.05, 375.45, 378, 380.55, 383.05, 385.45, 387.95, 390.55, 393.05];
const STERN_PORT_HI = [-359, -356.45, -354.05, -341.95, -339.55, -337.05, -334.5, -331.95, -286.75, -284.25, -281.75, -279.25, -276.75, -274.25, -271.75];
const STERN_PORT_LO = [-359, -356.45, -354.05, -341.95, -339.55, -337.05, -334.5, -331.95, -329.55, -327.05, -324.5, -321.95, -319.55, -317.05, -314.55, -311.95, -309.55, -307.05, -304.55, -301.95, -289.25, -286.75, -284.25, -281.75, -279.25, -276.75, -274.25, -271.75];
const PORT_RUNS = [
  [BOW_PORT_Z, [[-17, 3, 5], [-20, 3, 5], [-26, 14, 6], [-14, 27, 4], [-29, 31, 5], [-32, 31, 5], [-35, 20, 3], [-23, 36, 4],
    [-73, 6, 6], [-76, 6, 6], [-82, 22, 5], [-88, 13, 4], [-91, 30, 6], [-70, 35, 3], [-85, 33, 3]]],
  [STERN_PORT_HI, [[-14, 0, 3], [-17, 9, 4], [-26, 3, 4]]],
  [STERN_PORT_LO, [[-76, 2, 5], [-79, 2, 5], [-85, 12, 6], [-91, 20, 5], [-82, 22, 4]]],
];
const WINDOW_RUNS = PORT_RUNS.flatMap(([cols, runs]) => runs.flatMap(([y, i0, n]) => Array.from({ length: n }, (_, k) => [
  [131.1, y, cols[i0 + k]], [-131.1, y, cols[cols.length - 1 - (i0 + k)]]]).flat()));
// v14: the keel wedge's port rows (row A x +-90.21, y -125.21; row B x +-82.21, y -133.21: 0.3 m off the 45-degree faces;
// glass every 2.5 m on one lattice z = -311.45 + 2.5 k, row A k 0-210, row B k 3-207; ray-cast) had every fourth port
// lit, all of them, over the livery glow of the glass between: two unbroken dotted lines 520 m long that read as rope
// lights on a small hull. The keel glass is dark now (livery glassDark) and a few compartments are lit instead, like the
// flanks: runs of 3-5 neighbouring ports on one deck, [row, first k, count], the starboard side mirrored end for end.
// (fix: 12 runs a side, the rows alternating, 15-17 slots (38-43 m) between run starts: 92 ports, 11 % of the 832, lit as
// the flank runs are (port, 1.25); every slot checked on the hull texture's glass on both sides)
const KEEL_ROWS = [[90.21, -125.21], [82.21, -133.21]];
const KEEL_RUNS = [[1, 15, 3], [0, 31, 4], [1, 46, 5], [0, 63, 4], [1, 80, 3], [0, 95, 5], [1, 111, 4], [0, 128, 4], [1, 145, 3], [0, 160, 5], [1, 176, 3], [0, 191, 3]];
const KEEL_PORTS = KEEL_RUNS.flatMap(([r, k0, n]) => Array.from({ length: n }, (_, i) => [
  [KEEL_ROWS[r][0], KEEL_ROWS[r][1], -311.45 + 2.5 * (k0 + i)], [-KEEL_ROWS[r][0], KEEL_ROWS[r][1], -311.45 + 2.5 * (210 - k0 - i)]]).flat());

// island roof edges (fix): the only places on the island where an automatic pin is 1.5 m or more from its glass. Each
// tier's 1 m window ribbons (3 m deck pitch) run up to 2-4 m under its roof, and the next tier's lowest ribbon sits right
// at that roof, so every wall crease is a lit sill in a window band. A pin may sit on a roof's outer edge only: from
// 1.6 m over the tier's top ribbon to its parapet, and 1.6 m clear of the next tier's walls (tiers from
// tools/blender/hulls/carrier_dims.py; ribbons from the hull texture). [y0, y1, tier [half-width, z0, z1], next tier]
const ISLAND_ROOFS = [
  [35.6, 41.5, [46, -250, 22], [33, -218, -18]], // plinth (ribbons up to y 34), round t1
  [55.6, 60, [34, -219, -17], [25, -196, -46]], // t1 (to 54), round t2
  [76.6, 81, [26, -197, -45], [22, -183, -65]], // t2 (to 75), round t3
  [98, 102, [23, -184, -92.6], [18, -171, -85]], // t3 (to 96.5), round t4; its front lies under the hammerhead bridge
  [122.4, 124.5, [19, -172, -84], [12, -156, -106]], // t4's parapet (its top ribbon is at the roof, 121), round t5
  [133.6, 137.5, [13, -157, -105], [6.5, -142, -124]], // t5 (to 132), round t6
];
const ISLAND_ROOF_EDGES = ISLAND_ROOFS.flatMap(([y0, y1, [w, z0, z1], [wn, zn0, zn1]]) => [
  { box: [[wn + 1.6, y0, z0], [w, y1, z1]], mirrorX: true },
  { box: [[-w, y0, z0], [w, y1, zn0 - 1.6]] },
  ...(zn1 + 1.6 < z1 ? [{ box: [[-w, y0, zn1 + 1.6], [w, y1, z1]] }] : []),
]);

// signs of life (R12: the carrier keeps 8-16 slow amber beacons): the dorsal centreline over frame rings F4 and F5, the
// bow section and stern block tops, the sponson roofs and the island's tier roofs (t1 fore, t2 and t3 aft of the tier
// above). Ray-cast, 8 cm proud; the sponson pair is 31 m from the sidelights, all are far from the strobes
const BEACONS = [[0, 23.06, 99.51], [0, 23.06, 190.1], [90, 23.9, 405], [-90, 23.9, 405], [90, 23.06, -320], [-90, 23.06, -320],
  [185, -29.91, -310], [-185, -29.91, -310], [0, 58.5, -30], [0, 79.49, -190], [0, 100.48, -180]];

export const asset = {
  glb: './assets/ships/carrier.glb', generator: 'tools/blender/hulls/carrier.py (remodel of the tripo3d/h3.1/multiview-to-3d hull) + tools/blender/assemble.py',
  concept: './assets/concepts/carrier.webp', beauty: './assets/concepts/carrier-beauty.webp',
  rotate: [0, 0, 0], hullNodes: ['hull'],
  length: 899.998, // 406.0 x 319.3 x 900.0 m design (no slot normalisation)
  // Two-tone armour zones (?livery=tone|bone, livery.js SCHEMES; ship frame, metres): the bow section (aft face
  // z 276 to the probes), the stern block (stern plate to its front face z -261, with the gun sponsons) and the
  // five frame rings between the open bays take the light paint, a bold light/dark rhythm along the flank; the
  // bays' flank plating, the island, the keel wedge and the dorsal deck between stay dark. (The hangar interior
  // keeps its own plating: liveryKeep wins inside the cavity.)
  liveryZones: [
    { box: [[-215, -165, 276.0], [215, 165, 455]] },       // bow section
    { box: [[-215, -165, -460], [215, 165, -261.0]] },     // stern block
    { box: [[-215, -165, -188.1], [215, 21.6, -164.3]] },    // frame F1 (up to the dorsal deck: the island stays dark)
    { box: [[-215, -165, -98.0], [215, 21.6, -73.5]] },      // frame F2
    { box: [[-215, -165, -5.25], [215, 21.6, 19.2]] },       // frame F3
    { box: [[-215, -165, 87.42], [215, 21.6, 111.6]] },      // frame F4
    { box: [[-215, -165, 178.1], [215, 21.6, 202.1]] },      // frame F5
  ],
  // remodel paint is lighter than the generated textures: gain 0.05 matches the fleet grey; kit and hull glass get a
  // dim warm interior light (livery.js glassGlow, opt-in)
  // (v12 apply: the flank port grids of the bow section and stern block (with the sponsons) and the bow-face louvre
  // panels stay dark: at 50 % lit they read as a perforated LED sheet; their lit compartments are WINDOW_RUNS)
  // (v14: a working warship's lit share, 0.4 (the island: 40 decks, mostly dark) and warship flicker 0.08; the keel
  // wedge's glass is dark too (its lit compartments are KEEL_PORTS); the hammerhead bridge (x +-32, y 100-112,
  // z -91..-57, two 1.6 m pane bands) is one steady compartment at half the cabin glow: bridges run dark)
  // (fix: the lower louvre chamfer under the bays (y -97.5..-123) is machinery, but its dark grille paint passes the
  // glass test and glowed as a dotted sheet from below: dark. It holds no crew glass: the keel rows are at y -125 / -133
  // and the hangar deck is above -97.5. Seven of the eight glass boxes are used)
  livery: { gain: 0.05, glassGlow: [0.52, 0.42, 0.28], glassLit: 0.4, glassFlicker: 0.08,
    glassDark: [[[95.5, -126, 276.5], [140, 26, 460]], [[-140, -126, 276.5], [-95.5, 26, 460]], [[124, -126, -460], [210, 26, -261.5]], [[-210, -126, -460], [-124, 26, -261.5]],
      [[-125, -150, -320], [125, -112, 220]], [[-127, -123, -262], [127, -97.5, 277]]],
    glassZones: [{ box: [[-33, 102, -91.2], [33, 109.5, -56]], gain: 0.5, uniform: true }] },
  // v11 lightscape (src/lib/lightscape.js): crease pins over the whole hull (block corners, chines, frame edges), recess
  // bars, blue-white status lights round the drive collars; inside the hangar (the zone) a denser, warmer set, plus
  // authored deck, lane and ceiling lights, and chasers along the launch lane toward the bow mouth.
  // v12 apply (concept: the armour stays dark, the light comes from a few bright bars at block corners, seams and
  // recesses, lit window groups, lamp-lit bays and one cool intake accent): the pin budget is cut to a third and moved to
  // block corners; automatic bars are sized for a 900 m hull; authored bars go into the bow face's recessed header and
  // chin panels (the lit brow and waist band), the dorsal armour gaps at every frame ring, the frame posts' recessed
  // panels (window boxes), the bays' lintels and sills, the hangar lanes and the sponsons' forward intakes (ice). All
  // positions are ray-cast (bow face plane z 418.02, its panels 417.39; flank 130.98; post recesses 129.99, y -19.5..-44;
  // sponson face -278.98, its recess -280.18). Signature bars are `keep` (phone tier, distance thinning).
  // v14 (fleet lighting scale standard): every lamp at the fleet fixture size, whatever the hull. Crease pins 0.22-0.28 m
  // (were 0.45-0.7), automatic bars 0.2 m wide and 1.2-2.4 m long (were 0.65-0.72 x 2.5-5.5), authored joint strips
  // 0.30 m wide on the signature set and 0.26 m elsewhere (were 0.72-0.87), hangar pins 0.26 m: the lamps of the ships
  // parked in the hangar are 0.2-0.3 m, so the carrier's lamps now match them size for size. No warm lamp outside the
  // hangar and bays (warm is lit interior); the keep set is the 54 signature bars (brow, chin, waist, corners, frame
  // gaps, end blocks, ice) that must survive to fleet range; everything else thins and fades with range.
  // v14 fix (review): no automatic lamp within 1.5 m of glass (zones: the flank port grids, the keel port rows, the
  // island's window bands, the hangar's back-wall window and bow-wall gallery) and none on the stern plate's grilles;
  // the frame faces' gallery glass is lit by the livery alone;
  // signs of life for a 20,000-crew ship (R12): eleven slow amber beacons, a drive-status bar and amber corner strips on
  // the stern plate, which had no light at all; the keel's lit compartments are 12 runs a side at the flank ports'
  // brightness (they had faded to nothing in the dark)
  // (fix 2: the drive collars, the posts' recesses and the sponsons' aft recess lose their automatic lamps, and the caps
  // come down so the lamps they free do not refill the hangar past its 900: creases 560 -> 525, corner bars 60 -> 45
  // with the hangar zone's corner share at 0.2, so the cut falls on hangar corner bars, not on the stern block's and
  // bow section's corner bars (a lower cap alone takes those first: the order interleaves hull and hangar). The
  // recess-bar cap, 120 -> 100, is a guard only: 41 bars)
  lightscape: {
    seed: 51,
    creases: { angle: 35, minLen: 7, pitch: 16, share: 0.2, run: [1, 3], runPitch: 1.8, corners: 0.35, spacing: 5, size: [0.22, 0.28], intensity: [0.8, 1.1], mix: { amber: 0.85, white: 0.15 }, max: 525, blinkShare: 0.02 },
    slits: { angle: 35, minLen: 3, share: 0.3, every: 24, len: [1.2, 2.4], width: 0.2, radiance: [1.0, 1.5], spacing: 16, max: 100, mix: { amber: 1 },
      corner: { share: 0.4, len: [1.4, 2.4], width: 0.2, radiance: [1.2, 1.7], inset: 0.8, spacing: 14, max: 45 } },
    // (no crease on this hull falls inside it: the drive-status fixture is the authored cool bar on the stern plate)
    cool: { radius: 1.7, depth: 4.5 },
    zones: [
      // (fix 2) the six drive-bell collars behind the stern plate (z -376.5..-408): uncrewed machinery (R3), no lamps. 28
      // automatic bars sat round them, lit slots on the engines; the box stops at z -371.5, so the stern plate's own
      // corner pins stay, and its drive-status fixture is the one cool bar on the plate (patterns ignore zones)
      { box: [[-125, -125, -412], [125, 25, -371.5]], creases: null, slits: null },
      // (fix) no automatic lamp within 1.5 m of glass: the flank port grids of the bow section and the stern block
      // (1 m port ribbons at y -13.5..-37 and -70..-92; bow z 279-410, stern z -366..-265) and the keel wedge's two port
      // rows (x 82 / 90). A crease pin on a port band's lip or a recess bar in its foot is a lit sill in a row of windows,
      // a window-shaped light twice the port size. The block-corner pins above and below the bands (y -10.3, -94.7) and
      // every authored lamp (patterns ignore zones) stay
      { box: [[125, -38, 277], [137, -12, 412]], mirrorX: true, creases: null, slits: null },
      { box: [[125, -93.5, 277], [137, -68.5, 412]], mirrorX: true, creases: null, slits: null },
      { box: [[125, -31.5, -368], [137, -12, -262.5]], mirrorX: true, creases: null, slits: null },
      { box: [[125, -93.5, -368], [137, -74.5, -262.5]], mirrorX: true, creases: null, slits: null },
      { box: [[79, -136, -308], [93, -122, 212]], mirrorX: true, creases: null, slits: null },
      // (fix) the stern plate's three louvred grilles between the bells (2 m-deep recesses: x +-19, y 1..17 and -98..-110;
      // the centre grille x +-27, y -34..-67): uncrewed machinery, no lamps (30 pins and bars sat round its ribs, rows at
      // every rib end); the plate's amber is its authored corner strips, its status fixture the cool bar under the grille
      { box: [[-30, -112, -372], [30, 18, -368.5]], creases: null, slits: null },
      // (v14) the stern sponsons' aft recess (x 153.2-176.8, y -50.5, z -339.9) and forward intake recess: a lit bar at
      // each end of a rectangular recess turned it into a vehicle's side window or visor (a 60 m sponson read as a pod)
      // (fix 2: and no pins round the aft recess either: four or five crease pins still framed it like a lit hatch)
      { box: [[151, -60, -343], [179, -40, -338]], mirrorX: true, creases: null, slits: null },
      { box: [[140, -70, -345], [210, -30, -275]], mirrorX: true, slits: null },
      // louvre panels either side of the bow mouth (x 106.75-119.75, y -18..-81 at z 416.6) and the forward flank: no pins
      // on the slats (they are framed by authored bars instead)
      { box: [[96, -100, 405], [135, 0, 432]], mirrorX: true, creases: { share: 0.03, corners: 0 }, slits: null },
      // the vent grilles on the upper chamfers above the bays and the lower louvre chamfer under them (y below the sill
      // at -96.3): uncrewed machinery, no lamps at all (v14: 35 + 67 pins on grilles no crew or fixture would light)
      { box: [[100, -1, -262], [140, 24, 277]], mirrorX: true, creases: null, slits: null },
      { box: [[100, -122, -262], [126, -97.6, 277]], mirrorX: true, creases: null, slits: null },
      // (fix 2) the frame posts' two door-shaped recesses (upper y -19.5..-44, lower -56..-83, z +-8 round the post
      // centre, floor x 129.99): no automatic lamp on their lintels, sills or jambs (rule 3.5). A tall rounded recess with a
      // lit sill and lit jambs reads as a hatch or a door in its frame and shrinks the 95 m post about ten times, the same
      // cue as the window box it replaced. The post face's top and bottom corner bands (y over -15, under -87) take no
      // automatic lamp either: the authored corner markers stand there (one lamp per corner, F7)
      ...POSTS.flatMap((zc) => [[-46, -17.5, 9.5], [-85, -54, 9.5], [-15, -9, 13], [-95, -87, 13]].map(([y0, y1, dz]) => (
        { box: [[128.5, y0, zc - dz], [131.6, y1, zc + dz]], mirrorX: true, creases: null, slits: null }))),
      // frame posts' corners: a light at a corner, no dotted chains up the long verticals
      { box: [[119, -95, -262], [133, -2, 277]], mirrorX: true, creases: { share: 0.1, run: [1, 1], corners: 0.6 } },
      // the bow face: corner accents, no speckle (its brow and waist bars are authored)
      { box: [[-126, -116, 416], [126, 18, 423]], creases: { share: 0.12, corners: 0.7 } },
      // the island: its window glow already lights it (v14: corners only, about 70 pins instead of 186 fairy lights on
      // its parapets; a working superstructure, not a hotel at night)
      // (fix: and only on the tiers' roof edges, ISLAND_ROOF_EDGES; no bars at all: 19 of its 21 sat in the window
      // bands, lit slivers in a row of panes)
      { box: [[-50, 23, -250], [50, 160, 25]], creases: { share: 0.06, corners: 0.3, only: ISLAND_ROOF_EDGES }, slits: null },
      // the flat dorsal deck: block and hatch corners, not a sparkle over the plates
      { box: [[-100, 14, -262], [100, 24, 421]], creases: { share: 0.1, run: [1, 2], corners: 0.6 } },
      // (fix) the hangar's back wall (z -276.3): its long control-room window (x +-60, y -14..-17) takes no lamp on its
      // lip: a bar along its top edge read as a lit transom over the window
      { box: [[-62, -19, -280], [62, -12, -275.5]], creases: null, slits: null },
      // and the bow section's inner walls: the glazed gallery strip at y -60.3..-61.9 (x +-92..95, z 278-412)
      { box: [[85, -63.5, 277], [97, -58.5, 416]], mirrorX: true, creases: null, slits: null },
      // hangar interior (the cavity and the open bays out to the flank plating): warmer work lights on girder and wall
      // corners, not on the plate seams
      // (fix: share 0.25 -> 0.2, corners 0.7 -> 0.3. The pins the glass zones above freed would otherwise refill here (the
      // crease cap is global) and push the hangar past its 900-lamp budget; fewer loose warm dots in the dark bays, which
      // hinted at a lit tower facade, and the freed share goes back to the exterior's block corners)
      // (fix 2: corner bars share 0.2, down from the hull's 0.4: the corner-bar cap is global too, and the bars freed on the
      // drive collars and post recesses had refilled here, 20 -> 42)
      { box: [[-121, -97.5, -277], [121, -0.2, 421]],
        creases: { minLen: 5, pitch: 16, share: 0.2, run: [1, 2], runPitch: 1.5, corners: 0.3, spacing: 4, mix: { warm: 0.55, amber: 0.3, white: 0.15 }, intensity: [0.6, 0.95] },
        slits: { minLen: 3, share: 0.35, every: 16, spacing: 12, mix: { warm: 0.6, amber: 0.4 }, corner: { share: 0.2 } } },
    ],
    patterns: [
      // ---- bow face (z 418.02): the brow and the waist band. A bar along the lower lip of each recessed header panel
      // (x 8.25-31.75 / 38.25-61.75 / 68-91.75, y 5.25-12.75, floor 417.39) and a pair under the upper lip of each chin
      // panel (y -102.25..-110.75), right under the mouth sill (the middle chin panel left dark: a few signature slits,
      // not a marquee)
      // (v14: 0.30 m lip strips, not 0.87 m bands: a bright band that fills the bottom of a recess reads as a row of
      // 1-1.5 m windows, a bus front, and shrank the 130 m bow face to 30-40 m. The signature strips here and at the
      // frame gaps run at radiance 2.0, the joint-strip maximum, so the narrower brow still carries the hero)
      { slitRow: [[20, 6.1, 417.45], [80, 6.1, 417.45]], pitch: 30, len: 13, width: 0.3, u: [1, 0, 0], n: [0, 0, 1], color: 'amber', radiance: 2.0, mirrorX: true, keep: true },
      ...[[14, 26], [74, 86]].map(([a, b]) => ({ slitRow: [[a, -103.0, 417.45], [b, -103.0, 417.45]], pitch: 12, len: 8, width: 0.3, u: [1, 0, 0], n: [0, 0, 1], color: 'amber', radiance: 2.0, mirrorX: true, keep: true })),
      // the waist band wraps round the corner onto the flank above the lower chamfer, and an amber bar marks each upper
      // corner (bow face above the louvres and the flank just under the deck-edge chamfer)
      { slitRow: [[131.04, -93.1, 393], [131.04, -93.1, 399]], pitch: 6, len: 4.5, width: 0.3, u: [0, 0, 1], n: [1, 0, 0], color: 'amber', radiance: 2.0, mirrorX: true, keep: true },
      { slit: [131.04, -11.6, 396], u: [0, 0, 1], n: [1, 0, 0], len: 7, width: 0.3, color: 'amber', radiance: 2.0, mirrorX: true, keep: true },
      { slit: [121, -11.2, 418.08], u: [1, 0, 0], n: [0, 0, 1], len: 5, width: 0.3, color: 'amber', radiance: 2.0, mirrorX: true, keep: true },
      // louvre panels beside the mouth (x 106.75-119.75; y -18.25..-45.25 and -54.25..-81.25, floor 416.6): lit along
      // their top lips, so the vents are framed by light instead of sprinkled with it
      ...[-18.9, -54.9].map((y) => ({ slit: [113.25, y, 416.66], u: [1, 0, 0], n: [0, 0, 1], len: 11, width: 0.26, color: 'amber', radiance: 1.35, mirrorX: true })),
      // ---- armour gaps: every frame ring's cap (and the end blocks) stands 2 m above the bay slabs of the dorsal deck
      // (22.98 vs 20.99); a bright bar on that step face next to the deck-edge chamfer marks where the blocks meet
      ...FRAME_FACES.slice(1, -1).map(([z, s]) => ({ slit: [94, 21.9, z + s * 0.06], u: [1, 0, 0], n: [0, 0, s], len: 6, width: 0.3, color: 'amber', radiance: 2.0, mirrorX: true, keep: true })),
      // (the end blocks meet the deck with a 45-degree chamfer instead of a step face)
      { slit: [94, 21.94, -261.9], u: [1, 0, 0], n: [0, 0.7071, 0.7071], len: 6, width: 0.3, color: 'amber', radiance: 2.0, mirrorX: true, keep: true },
      { slit: [94, 21.94, 276.87], u: [1, 0, 0], n: [0, 0.7071, -0.7071], len: 6, width: 0.3, color: 'amber', radiance: 2.0, mirrorX: true, keep: true },
      // ---- frame posts (outer faces x 131, recessed panels 129.99, y -19.5..-44, z +-8 round the post centre)
      // (v14: the 'window box' of four lamp-bright panes across the top of the recess is gone: a tall door-shaped recess
      // with a lit row over it read as a 2.5 m door with its transom and shrank the 95 m post about ten times. The
      // recess keeps one upright amber strip on its floor along the aft jamb (z -8.01 from the post centre; seen from the
      // bow quarter, where the forward jamb would hide it): a lamp washing the recess, not a glazed opening)
      ...POSTS.map((zc) => ({ slit: [130.05, -24.0, zc - 7.6], u: [0, 1, 0], n: [1, 0, 0], len: 6, width: 0.26, color: 'amber', radiance: 1.5, mirrorX: true })),
      // ---- stern plate (z -371.01, ray-cast; fix: every aft view had no amber at all): joint strips at the block's
      // upper and lower outboard corners and one up its outboard edge, all outside the drive collars and 100 m from the
      // stern light; and the drive-status fixture, a cool bar on the centreline level with the upper drives' axis,
      // between their collars and 4 m under the upper grille's recess (the plate at y 1..17 is that 2 m-deep grille)
      { slit: [100, 10, -371.09], u: [1, 0, 0], n: [0, 0, -1], len: 6, width: 0.3, color: 'amber', radiance: 1.8, mirrorX: true },
      { slit: [100, -108, -371.09], u: [1, 0, 0], n: [0, 0, -1], len: 6, width: 0.3, color: 'amber', radiance: 1.8, mirrorX: true },
      { slit: [123, -50, -371.09], u: [0, 1, 0], n: [0, 0, -1], len: 6, width: 0.3, color: 'amber', radiance: 1.8, mirrorX: true },
      { slit: [0, -3.2, -371.09], u: [1, 0, 0], n: [0, 0, -1], len: 2.4, width: 0.15, color: 'cool', radiance: 1.0 },
      // ---- beacons (BEACONS): slow amber pulses, the sign of life that lasts to fleet range (animated: rank 0, floor 0.4)
      { points: BEACONS, color: 'amber', size: 0.3, intensity: 1.0, pulse: 3.9 },
      // ---- lit compartments on the flank port grids (grouped runs, see WINDOW_RUNS) and the keel wedge (KEEL_PORTS):
      // window points at the glass size, not keep (a lit port far off fades with its area)
      { points: WINDOW_RUNS, color: 'port', size: 0.5, intensity: 1.25 },
      { points: KEEL_PORTS, color: 'port', size: 0.5, intensity: 1.25 },
      // ---- running lamps (v14: out of the never-dimmed nav path, lights[]): amber on the deck-edge chamfer every 25 m
      // between the white outline markers, at mid-height on the frame posts' capital band, the end blocks and the
      // sponsons, and along the mouth's lintel
      { points: [...EDGE_RUN, ...FLANK, ...SPONSON_RUN, ...MOUTH_RIM], ...LAMP },
      // ---- the open flank bays: a lamp bar under the lintel of each bay-facing frame face (lamp segments in the
      // fixtures below it), a few warm pins down the face, and amber sill bars along each bay's deck edge
      ...FRAME_FACES.map(([z, s]) => ({ slit: [115, -5.6, z + s * 0.06], u: [1, 0, 0], n: [0, 0, s], len: 6, width: 0.26, color: 'warm', radiance: 1.8, mirrorX: true })),
      ...FRAME_FACES.map(([z, s]) => ({ row: [[127.5, -90, z + s * 0.12], [127.5, -8, z + s * 0.12]], pitch: 7, mix: { warm: 0.6, amber: 0.4 }, size: 0.26, intensity: 0.85, skip: 0.8, mirrorX: true, seed: Math.round(z) })),
      ...BAY_CEILINGS.slice(0, 6).map(([z0, z1]) => ({ row: [[120, -0.72, z0 + 3], [120, -0.72, z1 - 3]], pitch: 8, color: 'warm', size: 0.26, intensity: 0.8, skip: 0.75, mirrorX: true, seed: Math.round(z0) })),
      ...BAY_CEILINGS.slice(0, 6).map(([z0, z1], i) => ({ slitRow: [[119.6, (i === 0 ? -92.45 : i === 5 ? -93.61 : -96.33) + 0.06, z0 + 8], [119.6, (i === 0 ? -92.45 : i === 5 ? -93.61 : -96.33) + 0.06, z1 - 8]], pitch: 14, len: 4, width: 0.26, u: [0, 0, 1], n: [0, 1, 0], color: 'amberDeep', radiance: 1.5, mirrorX: true })),
      // ---- stern gun sponsons: the forward face's recessed panel (x 156.5-174, y -45..-55, floor -280.18) glows as a
      // cool intake, the one cold note the hero view sees (the drive collars face aft)
      // (v14: four 2.5 x 0.3 m lamps instead of one 14 x 1.4 m glowing bar, which read as a visor on a small pod)
      { slitRow: [[160.0, -50.0, -280.12], [170.5, -50.0, -280.12]], pitch: 3.5, len: 2.5, width: 0.3, u: [1, 0, 0], n: [0, 0, 1], color: 'ice', radiance: 1.0, mirrorX: true, keep: true },
      // ---- hangar
      // launch lane edges on the long deck (x +-25): warm bars every 8 m; in the bow section amber lane bars run as
      // chasers toward the mouth (bars, not pins, so they read against the deck and reflect in it)
      { slitRow: [[25.5, -96.26, -160], [25.5, -96.26, 176]], pitch: 8, len: 2.4, width: 0.26, u: [0, 0, 1], n: [0, 1, 0], color: 'warm', radiance: 1.4, mirrorX: true },
      { slitRow: [[25.5, -90.91, 280], [25.5, -90.91, 414]], pitch: 4, len: 2.2, width: 0.26, u: [0, 0, 1], n: [0, 1, 0], color: 'amber', radiance: 1.5, chase: 3.0, duty: 0.18, mirrorX: true },
      { row: [[25.5, -93.51, 205], [25.5, -93.51, 274]], pitch: 6, color: 'amber', size: 0.26, intensity: 1.0, chase: 3.0, duty: 0.18, chaseSpan: 0.5, mirrorX: true },
      { row: [[25.5, -92.35, -254], [25.5, -92.35, -192]], pitch: 8, color: 'white', size: 0.26, intensity: 0.75, mirrorX: true },
      // bay deck edges (x +-93.5): sparse amber pins at the open flank
      { row: [[93.2, -96.25, -160], [93.2, -96.25, 176]], pitch: 12, color: 'amber', size: 0.26, intensity: 0.8, skip: 0.25, mirrorX: true },
      // bay ceilings: two rows of warm work lights either side of the centre strip
      { row: [[45, -1.0, -258], [45, -1.0, 412]], pitch: 11, color: 'warm', size: 0.26, intensity: 0.8, skip: 0.3, mirrorX: true },
      { row: [[80, -1.0, -258], [80, -1.0, 412]], pitch: 13, color: 'white', size: 0.26, intensity: 0.7, skip: 0.4, mirrorX: true },
      // bow-section walls: amber guidance lights at deck height and a white row above
      { row: [[94.8, -88.5, 282], [94.8, -88.5, 414]], pitch: 7, color: 'amber', size: 0.26, intensity: 0.9, mirrorX: true },
      { row: [[94.8, -20, 282], [94.8, -20, 414]], pitch: 12, color: 'white', size: 0.26, intensity: 0.7, skip: 0.2, mirrorX: true },
      // mouth lip: an amber chaser across the sill
      { row: [[-88, -94.4, 421.6], [88, -94.4, 421.6]], pitch: 8, color: 'amber', size: 0.26, intensity: 1.0, chase: 2.4, duty: 0.2 },
      // ports on the bow section's inner walls (window points, half of them dark; the frame faces' gallery ports are
      // lit by the livery alone)
      { points: BOW_WALL, ...WIN, skip: 0.5, seed: 13 },
      // ---- corner markers (fix 2; F7: upright 1.5 x 0.22 m amber bars, radiance 1.4, not keep; all ray-cast). Last in the
      // list, so the patterns above keep their seeds (a pattern's skip hash follows its place in the list).
      // The frame posts: one at each of the four outer corners of every post's outer face (x 130.98, y -9.9..-93.8, z +-12
      // round the centre), 0.85 m in from its top and bottom edges and 1 m from its sides. They take over from the
      // automatic lamps that outlined the door-shaped recesses: a lamp at each corner marks the 24 x 84 m block, so the post
      // keeps its size and the flank keeps its amber
      ...POSTS.flatMap((zc) => [-11.5, -92.2].flatMap((y) => [-11.2, 11.2].map((dz) => (
        { slit: [131.06, y, zc + dz], u: [0, 1, 0], n: [1, 0, 0], len: 1.5, width: 0.22, color: 'amber', radiance: 1.4, mirrorX: true })))),
      // the stern block's lower outboard corners, on its forward chamfer (z -261.6, the bay-6 edge) and on its aft chamfer to
      // the stern plate (z -370.4): their top corners already carry an automatic corner bar. 3.4 m or more from the port
      // ribbons
      { slit: [129.6, -91.5, -261.55], u: [0, 1, 0], n: [0.7071, 0, 0.7071], len: 1.5, width: 0.22, color: 'amber', radiance: 1.4, mirrorX: true },
      { slit: [127.6, -91.5, -370.48], u: [0, 1, 0], n: [0.7071, 0, -0.7071], len: 1.5, width: 0.22, color: 'amber', radiance: 1.4, mirrorX: true },
      // the stern gun sponsons' outboard corners, on the flat of the forward face (z -278.98, y -42.3..-61.8) and the aft
      // face (z -341.02), 0.8 m in from the outboard chamfer and 31 m from the sidelight: a gun block gets corner markers
      // only (R3), and they give the 60 m sponson its size where the lit recess ends had made it read as a pod with a visor
      ...[[-278.92, [0, 0, 1]], [-341.08, [0, 0, -1]]].flatMap(([z, n]) => [-44.3, -59.7].map((y) => (
        { slit: [197.8, y, z], u: [0, 1, 0], n, len: 1.5, width: 0.22, color: 'amber', radiance: 1.4, mirrorX: true }))),
    ],
  },
  // the operational repaint stops at the hangar: inside the cavity box the texture keeps its own plating (x 0.14, 8 %
  // saturation), so the deck and walls read as lit grey steel instead of the near-black hull paint
  liveryKeep: { box: [[-100.5, -97.5, -277], [100.5, -0.3, 414]], gain: 0.14, saturation: 0.08, feather: 1.5 },
  // runtime PATINA micro detail, turned down (the hull carries its own plating seams); the hangar takes the 'deck' set
  detail: {
    set: 'hull', tile: 6, normalStrength: 0.6, roughAmount: 0.5, cavity: 0.2,
    interior: { set: 'deck', tile: 6, normalStrength: 0.8, roughAmount: 0.6, cavity: 0.25, albedo: 0.9, seam: 0.5, grime: 1.6, feather: 1.5 },
  },
  engines: [
    { p: [57.4, -3.2, -449.781], radius: 18.3, depth: 24.705, throat: 9.15, wall: [[3.529, 18.026], [7.059, 17.341], [10.588, 16.308], [14.117, 14.959], [17.647, 13.307], [21.176, 11.367]] },
    { p: [-57.4, -3.2, -449.781], radius: 18.3, depth: 24.705, throat: 9.15, wall: [[3.529, 18.026], [7.059, 17.341], [10.588, 16.308], [14.117, 14.959], [17.647, 13.307], [21.176, 11.367]] },
    { p: [92.3, -50.1, -449.774], radius: 18.9, depth: 25.515, throat: 9.45, wall: [[3.645, 18.616], [7.29, 17.909], [10.935, 16.843], [14.58, 15.449], [18.225, 13.743], [21.87, 11.74]] },
    { p: [-92.3, -50.1, -449.774], radius: 18.9, depth: 25.515, throat: 9.45, wall: [[3.645, 18.616], [7.29, 17.909], [10.935, 16.843], [14.58, 15.449], [18.225, 13.743], [21.87, 11.74]] },
    { p: [57.4, -95.9, -449.781], radius: 18.3, depth: 24.705, throat: 9.15, wall: [[3.529, 18.026], [7.059, 17.341], [10.588, 16.308], [14.117, 14.959], [17.647, 13.307], [21.176, 11.367]] },
    { p: [-57.4, -95.9, -449.781], radius: 18.3, depth: 24.705, throat: 9.15, wall: [[3.529, 18.026], [7.059, 17.341], [10.588, 16.308], [14.117, 14.959], [17.647, 13.307], [21.176, 11.367]] },
  ],
  lights: [
    // steady sidelights on the outboard face of each stern gun sponson (the beam extremity): red port, green starboard
    { p: [202.98, -55, -310], color: 'red', size: 0.4 },
    { p: [-202.98, -55, -310], color: 'green', size: 0.4 },
    // anti-collision strobes, alternating: island crown roof and the keel pod
    { p: [4, 145.63, -127], color: 'white', size: 0.4, blink: { ...STROBE } },
    { p: [8, -152.23, 182], color: 'white', size: 0.4, blink: { ...STROBE, phase: 0.5 } },
    // steady stern light on the stern plate above the upper grille
    { p: [0, 18.5, -371.23], color: 'white', size: 0.4 },
    // white outline markers every 75 m on the deck-edge chamfer (a ship of 500 m or more); v14: this is the whole nav
    // path. The amber running lamps and the window points are lightscape points now (they thin and fade with range)
    ...DECK_EDGE.map((p) => ({ p, color: 'white', size: RUN })),
  ],
  fixtures: STRIPS,
  interiorLights: RING_CEIL.map(([z, y]) => ({ ...FLOOD, p: [0, y - 1.3, z], target: [0, -96, z] }))
    .concat([{ ...FLOOD, p: [0, -7.59, 350], target: [0, -91, 350] }]),
  // only the hangar's own surfaces receive the floodlights: back wall to just past the mouth lip, from 1.1 m below the
  // lowest deck up, out to the flank plating (so the open bays' floors and frame sides still catch the light)
  interiorLightGate: { box: [[-133, -97.5, -277], [133, 0, 425]], feather: 1 },
  // (v12: the deck's bounce is warm and low, 1.2 -> 0.45: the ceiling and walls sit dim above the lamp pools)
  interiorBounce: { box: [[-100.5, -97.5, -277], [100.5, 4, 416]], color: '#f2c898', irradiance: 0.45, feather: 3 },
  anchors: {
    hangar: { p: [0, -48.7, 80], size: [155.8, 84.4, 670] },
    hangarMouth: { p: [0, -48.7, 418], dir: [0, 0, 1] },
    hangarDeck: {
      lane: [-25, 25], // 50 m launch lane on the centreline, clear to the mouth (a fleet-scale fighter is 48 m wide)
      zones: {
        aft: { x: [-93.5, 93.5], z: [-255.5, -189], y: -92.45 },
        long: { x: [-95.75, 95.75], z: [-164.3, 178.1], y: -96.35 },
        bay5: { x: [-95.75, 95.75], z: [-164.3, -98.2], y: -96.35 },
        bay4: { x: [-95.75, 95.75], z: [-73.4, -5.4], y: -96.35 },
        bay3: { x: [-95.75, 95.75], z: [19.5, 87.1], y: -96.35 },
        bay2: { x: [-95.75, 95.75], z: [111.8, 178.1], y: -96.35 },
        bay1: { x: [-82.35, 82.35], z: [202.4, 275.8], y: -93.61 },
        bow: { x: [-78.65, 78.65], z: [276.8, 415], y: -90.97 },
      },
      // where the hangar can be seen from outside (lib/park.js draws parked ships only then): the six flank bays at the
      // flank plating (clear z runs of a ray from the centre line, y range of the opening) and the bow mouth
      openings: {
        flank: { x: [-121, 121], y: [-96.35, -0.58], z: [[-260.8, -188.3], [-164.0, -98.3], [-73.0, -5.3], [19.5, 87.2], [112.0, 178.0], [202.5, 275.7]] },
        mouth: { z: 418, x: [-95, 95], y: [-90.97, -6.39] },
        inside: { min: [-95, -97, -276], max: [95, 0, 418] },
      },
    },
  },
};
