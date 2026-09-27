// Fleet carrier CV-50 — generated with fal (Tripo H3.1 multiview, see pipeline/fal-pipeline.json).
// A 900 m design (warp-capable, never carried itself, so no hangar-slot normalisation: the
// class scale correction is exactly 1). Everything below was measured on the GLB in the
// centred ship frame (rotate -> length -> centre), metres, bow +Z, dorsal +Y, port +X.
// - rotate [0,-90,0] puts the bow mouth at +Z and the island up; the stencil CV-50 reads on
//   both flanks of the bow section (re-projected onto the texture, see README). length 900 gives an envelope of 405.5 x 319.3 x 900 m: the beam is set by the
//   stern gun sponsons (x = +-202.8), the height by the island mast (y = +159.6) and the keel.
//   The hull itself is ~262 m wide (flank plating x = +131.5 / -129.7) and the mesh sits about
//   0.9 m to port of the envelope centre, so centreline features are at x ~ +0.9.
// - Hangar: one through-deck bay running from the back wall (z -256 .. -276, stepped) to the
//   bow mouth (lip at z ~ +418). Along the flanks it is open between six pairs of frames: open
//   bays at z [-256,-189], [-165,-98], [-73,-5], [19,87], [112,178], [201,276]; the enclosed bow
//   section z [277, 416] has solid side walls. The inner section is an octagon: walls at
//   x = +95.8 / -94.1, ceiling y -0.6 (bays) / -5.7 (frame rings) / -6.4 (bow section), deck
//   y -96.35 (bays 2-5), -92.45 (aft bay), -93.6 (forward bay), -91.9 (frame sills), -90.97
//   (bow section), 45-degree chamfers ~15 m at the corners. anchors.hangar is the clear box
//   that stands on the highest deck (bow section, y -90.97) and stays inside every chamfer,
//   frame ring, the bow-section ceiling and the back wall: 155.8 x 84.4 x 670 m.
//   anchors.hangarDeck lists the flat deck areas between the frames (measured deck planes and
//   limits) used by lib/park.js, and the launch lane kept clear on the centreline.
// - Main drive: six bells in the stern block (three per side: upper, outboard, lower). Centres
//   are circle fits of the exit lip's inner edge (rms <= 0.24 m); the exit plane is the lip's aft
//   face at z -449.9. The inner wall is r 18.5 (upper / lower bells) and 19.1-19.2 (outboard
//   bells) for the first ~1.5 r, then converges to the throat plate ~46 m (2.5 r) inside the lip
//   (ray-cast on axis; the outboard pair narrows to ~0.5 r); the radii are set 0.2 m inside the
//   wall. The throat glow sits on that plate, so the lip hides it from off-axis views.
// - Lights sit ~8 cm proud of the surface along its normal. Besides the nav lights, small
//   running lights repeat every 75 m along both dorsal deck edges (white) and every ~90 m along
//   both flanks (amber, on the frames and the bow / stern sections): at 900 m they are the
//   scale cue that the 0.4 m nav lights of the escorts share.
// - Hangar floodlights: six neutral-white (~5,800 K) spot lights hang under the ceiling on the
//   centreline, one under each frame ring (y -7, just below the ring's -5.7) and one in the bow
//   section, aimed straight down. Each is 36,000 cd: inverse-square, it gives about the sun's
//   irradiance (4.2 scene units) on the deck 89 m below and ~40 % of it on the parked ships at
//   the outboard rows (~125 m away, ~48 degrees off the beam axis). The cone is sized to that
//   job: full strength to 49 degrees, gone at 58 (the deck edge at the walls, mid-bay, is 50
//   degrees off axis), windowed to zero at 230 m. They cast no shadow maps (six more shadow
//   passes of the whole hangar every frame would cost more than they show), so the deck
//   cannot stop them: `interiorLightGate` light-links them to the hangar volume on this hull
//   (the cavity from the back wall to just past the mouth lip, deck level up, out to the flank
//   plating so the open bays' floors and frame sides still catch the light). Everything under
//   the deck (the chin below the bow mouth, the lower flank below the bays) stays unlit. The
//   sun's shadows still ground the ships in the sunlit bays. Each flood shows as a 3 m emissive
//   lens under the ceiling (it blooms), and `interiorBounce` adds what the lit deck reflects
//   back up: ~12 % of the deck's irradiance on the ceiling, half that on walls and frame faces.
// - liveryKeep: the operational repaint stops at the hangar: inside the cavity box the generated
//   texture keeps its own plating (x 0.2, 8 % saturation: the bake is a warm tan, the deck is
//   grey steel), so the deck reads as lit grey steel instead of the near-black hull paint. The
//   interior also takes the 'deck' PATINA set as its detail layer (plating relief, seams, tone).
export const meta = {
  name: 'Keystone-class fleet carrier', designation: 'CV-50', crew: 'about 20,000',
  blurb: 'Warp-capable fleet carrier: a 900 m armoured box hull around one through-deck hangar that opens at the bow mouth and through six framed bays along each flank, with a stepped island, twin-gun turrets along the spine and on two stern sponsons, and six fusion bells in the stern block.',
};

const STROBE = { period: 1.3, duty: 0.1 };
const RUN = 0.4; // running-light size (m): the same 0.4 m as every nav light on every hull

// dorsal deck edges: on the 30-degree edge chamfer, every 75 m (port, starboard pairs)
const DECK_EDGE = [
  [97.04, 18.55, -255], [-95.04, 18.77, -255], [97.04, 18.51, -180], [-95.03, 18.67, -180],
  [97.04, 18.18, -105], [-95.04, 18.45, -105], [97.04, 18.33, -30], [-95.04, 18.52, -30],
  [97.04, 18.52, 45], [-95.04, 18.65, 45], [97.04, 18.14, 120], [-95.04, 18.38, 120],
  [97.04, 18.56, 195], [-95.04, 18.69, 195], [97.05, 18.51, 270], [-95.04, 18.72, 270],
  [97.04, 18.5, 345], [-95.03, 18.65, 345], [97.04, 18.31, 410], [-95.04, 18.49, 410],
];
// flanks at mid-height (y -50): stern section, the five bay frames, bow section
const FLANK = [
  [130.93, -50, -270], [-129.26, -50, -270], [131.6, -50, -183.5], [-129.74, -50, -183.5],
  [131.49, -50, -91.5], [-129.65, -50, -91.5], [131.45, -50, 0], [-129.67, -50, 0],
  [131.59, -50, 91.5], [-129.7, -50, 91.5], [131.54, -50, 181.5], [-129.69, -50, 181.5],
  [127.76, -50, 285], [-126.04, -50, 285], [128.0, -50, 350], [-126.18, -50, 350],
  [127.86, -50, 410], [-126.2, -50, 410],
];

// drive bells (ray-cast on the GLB): a straight wall to ~1.5 r, converging to the throat plate
// 46 m (2.5 r) inside the lip; the outboard pair converges harder, to a ~0.5 r throat
const BELL = { depth: 46, throat: 12.5, wall: [[18, 17.9], [27.5, 17.9], [36.6, 16.6], [43.9, 14.4]] };
const BELL_OUT = { depth: 46.5, throat: 9.4, wall: [[18.9, 18.5], [28.4, 18.5], [37.8, 16.9], [45.4, 9.7]] };

// Human-scale lights in and around the hangar (ray-cast on the GLB, 8 cm proud of the surface):
// - gallery ports: 1 m warm windows, two rows (y -32 / -64) of three, 6 m apart, on every frame
//   face that looks into a flank bay (the flat outboard part of each frame post), and a row every
//   12.5 m along both inner walls of the enclosed bow section. Dim steady interior light, not
//   lamps: they carry the 1 m scale of a window, like the 0.4 m nav lights on every hull.
// - approach lights: steady amber 0.4 m points along the top and bottom edges of the bow mouth.
const PORT = '#4a3a26'; // lit interior behind a 1 m port (x4 in the light shader: well under the bloom threshold)
const FRAME_FACES = [[-261.0, 1], [-188.1, -1], [-164.3, 1], [-98.0, -1], [-73.5, 1], [-5.25, -1], [19.2, 1], [87.42, -1], [111.6, 1], [178.1, -1], [202.1, 1], [276.0, -1]];
const GALLERY = FRAME_FACES.flatMap(([z, s]) => [113, 119, 125, -111, -117, -123].flatMap((x) => [-32, -64].map((y) => ({ p: [x, y, z + s * 0.08], color: PORT, size: 1 }))));
const BOW_WALL = Array.from({ length: 11 }, (_, i) => 285 + i * 12.5).flatMap((z) => [{ p: [95.17, -48, z], color: PORT, size: 1 }, { p: [-93.33, -48, z], color: PORT, size: 1 }]);
const MOUTH_RIM = [-80, -40, 0, 40, 80].flatMap((x) => [{ p: [x, -2, 421.38], color: 'amber', size: 0.4 }, { p: [x, -98, 421.0], color: 'amber', size: 0.4 }]);

// Human-scale emitters on the outer hull, so the 900 m hull reads at full-ship framings (its turrets,
// island and baked panel lines are ship-sized, and the 6 m plating and 0.4 m lights vanish there):
// - HULL_PORTS: one row of 1 m warm ports every 6 m along the upper flank band (y 6: the vertical
//   band under the bays' eaves and the upper chamfer of the frames, bow and stern sections),
//   ray-cast per station [z, x port, x starboard], set 0.3 m proud (point sprites are depth-tested
//   at their centre)
// - ISLAND_PORTS: 1 m ports every 6 m along the island's tiers (y 30 base, 50, 66, 86, 100), ray-cast
//   the same way and kept only where the tier face is flat (within 1.5 m of the tier's median)
// - EDGE_RUN: 0.4 m amber running lights every 25 m along the dorsal deck edge (ray-cast at y 20.3,
//   the edge of the eave over the bays, the top of the chamfer elsewhere), between the white
//   DECK_EDGE lights; SPONSON_RUN along the outer face of each stern gun sponson
const HULL_PORTS = [
  [-368, 108.2, -106.5], [-362, 108.2, -106.3], [-356, 115.4, -113.7], [-350, 115.5, -113.8], [-344, 115.9, -114.0], [-338, 115.9, -114.1],
  [-332, 115.8, -114.0], [-326, 115.8, -114.0], [-320, 115.8, -114.0], [-314, 115.7, -113.9], [-308, 115.6, -113.9], [-302, 115.9, -114.0],
  [-296, 115.8, -114.0], [-290, 115.6, -113.8], [-284, 115.5, -113.7], [-278, 113.4, -112.0], [-272, 108.3, -106.6], [-266, 108.5, -106.7],
  [-260, 107.3, -105.5], [-254, 107.3, -105.5], [-248, 107.3, -105.6], [-242, 107.3, -105.6], [-236, 107.3, -105.7], [-230, 107.3, -105.8],
  [-224, 107.3, -105.6], [-218, 107.3, -105.7], [-212, 107.4, -105.8], [-206, 107.3, -105.9], [-200, 107.3, -106.0], [-194, 107.4, -106.1],
  [-188, 107.7, -106.4], [-182, 108.8, -106.7], [-176, 110.2, -108.5], [-170, 109.5, -107.9], [-164, 110.8, -108.6], [-158, 110.5, -108.7],
  [-152, 110.5, -108.6], [-146, 110.5, -108.7], [-140, 110.5, -108.7], [-134, 110.5, -108.7], [-128, 110.4, -108.7], [-122, 110.4, -108.7],
  [-116, 110.5, -108.7], [-110, 110.4, -108.7], [-104, 110.3, -108.5], [-98, 110.7, -108.7], [-92, 109.4, -107.8], [-86, 110.2, -108.4],
  [-80, 110.1, -108.6], [-74, 110.7, -108.7], [-68, 110.4, -108.5], [-62, 110.2, -108.4], [-56, 110.2, -108.4], [-50, 110.2, -108.5],
  [-44, 110.2, -108.6], [-38, 110.2, -108.5], [-32, 110.2, -108.4], [-26, 110.3, -108.3], [-20, 110.3, -108.3], [-14, 110.2, -108.3],
  [-8, 110.2, -108.2], [-2, 110.1, -108.2], [4, 110.1, -108.5], [10, 110.2, -108.5], [16, 110.2, -108.0], [22, 110.5, -108.4],
  [28, 110.3, -108.5], [34, 110.4, -108.4], [40, 110.3, -108.5], [46, 110.3, -108.4], [52, 110.2, -108.5], [58, 110.3, -108.5],
  [64, 110.3, -108.5], [70, 110.3, -108.5], [76, 110.3, -108.5], [82, 110.3, -108.6], [88, 110.5, -108.7], [94, 110.2, -108.5],
  [100, 110.2, -108.6], [106, 109.4, -107.8], [112, 110.3, -108.4], [118, 110.1, -108.2], [124, 110.0, -108.1], [130, 109.8, -108.1],
  [136, 110.0, -108.1], [142, 110.0, -108.1], [148, 109.9, -108.1], [154, 109.9, -108.1], [160, 109.9, -108.1], [166, 109.9, -108.1],
  [172, 110.0, -108.1], [178, 110.3, -108.4], [184, 109.6, -107.9], [190, 110.2, -108.4], [196, 110.0, -108.5], [202, 107.2, -105.3],
  [208, 107.1, -105.4], [214, 107.1, -105.4], [220, 107.1, -105.3], [226, 107.1, -105.3], [232, 107, -105.2], [238, 106.9, -105.3],
  [244, 107.0, -105.4], [250, 107.0, -105.4], [256, 106.9, -105.3], [262, 106.9, -105.3], [268, 107.0, -105.4], [274, 106.9, -105.3],
  [280, 106.8, -105.2], [286, 108.1, -106.4], [292, 108.1, -106.3], [298, 108.1, -106.3], [304, 108.0, -106.3], [310, 108.0, -106.3],
  [316, 108.1, -106.2], [322, 108.0, -106.2], [328, 107.9, -106.1], [334, 107.8, -106.0], [340, 107.7, -106.0], [346, 107.7, -105.8],
  [352, 107.7, -105.9], [358, 107.7, -105.9], [364, 107.7, -105.9], [370, 107.6, -105.8], [376, 107.6, -105.8], [382, 107.5, -105.8],
  [388, 107.5, -105.7], [394, 107.7, -105.8], [400, 107.8, -106.0], [406, 107.3, -105.5], [412, 107.3, -105.5],
];
const EDGE_RUN = [
  [-356, 96.0, -93.9], [-329, 95.8, -94.0], [-305, 95.8, -93.9], [-281, 95.8, -93.8], [-230, 93.4, -92.2], [-206, 93.7, -92],
  [-155, 122.8, -120.3], [-131, 122.8, -120.3], [-80, 93.3, -91.6], [-56, 122.5, -120.2], [-5, 122.0, -120.1], [19, 122.5, -120.1],
  [70, 122.6, -120.3], [94, 93.3, -91.5], [145, 122.2, -120.0], [169, 122.2, -119.9], [220, 93.5, -91.8], [244, 93.7, -91.8],
  [295, 93.2, -91.3], [319, 93.2, -91.2], [370, 93.3, -91.5], [394, 93.1, -91.3],
];
const ISLAND_PORTS = [
  [30, [[-132, 47.1, -45.1], [-126, 47.2, -45.4], [-120, 47.4, -45.6], [-114, 47.6, -45.8], [-108, 47.8, -46.1], [-102, 48.0, -46.1], [-78, 47.9, -46.3], [-72, 48.0, -46.3], [-66, 48.0, -46.3], [-60, 48.0, -46.5], [-54, 48.1, -46.5], [-30, 48.5, -47.0]]],
  [50, [[-162, 30.7, -28.7], [-156, 30.6, -28.8], [-126, 29.6, -27.7], [-120, 29.8, -28.0], [-114, 30.0, -28.0], [-108, 29.6, -27.8], [-102, 29.2, -27.8], [-96, 29.7, -27.7], [-90, 29.7, -27.5], [-84, 29.8, -27.8], [-78, 29.9, -27.9], [-72, 29.9, -28.0], [-66, 29.8, -28.1], [-60, 28.3, -26.2]]],
  [66, [[-108, 24.9, -23.1], [-102, 24.8, -23.0], [-96, 24.7, -22.9], [-90, 24.7, -22.8], [-84, 24.8, -22.8], [-78, 24.8, -22.7], [-72, 24.8, -22.9], [-66, 23.8, -21.8]]],
  [86, [[-114, 25.6, -23.4], [-108, 25.5, -23.2], [-102, 25.4, -23.1], [-96, 25.4, -22.9], [-90, 25.2, -23.2]]],
  [100, [[-114, 22.2, -20.3], [-108, 21.9, -20.2], [-102, 22.1, -20.1], [-96, 22.1, -20.4]]],
];
const SPONSON_RUN = [[192.6, -49, -336], [192.5, -49, -312], [191.7, -49, -288]];
const OUTER = [
  ...HULL_PORTS.flatMap(([z, xp, xs]) => [{ p: [xp + 0.3, 6, z], color: PORT, size: 1 }, { p: [xs - 0.3, 6, z], color: PORT, size: 1 }]),
  ...ISLAND_PORTS.flatMap(([y, pts]) => pts.flatMap(([z, xp, xs]) => [{ p: [xp + 0.3, y, z], color: PORT, size: 1 }, { p: [xs - 0.3, y, z], color: PORT, size: 1 }])),
  ...EDGE_RUN.flatMap(([z, xp, xs]) => [{ p: [xp + 0.3, 20.6, z], color: 'amber', size: RUN }, { p: [xs - 0.3, 20.6, z], color: 'amber', size: RUN }]),
  // starboard sponson mirrored about the mesh's centreline (x ~ +0.97)
  ...SPONSON_RUN.flatMap(([x, y, z]) => [{ p: [x + 0.3, y, z], color: 'amber', size: RUN }, { p: [-(x - 1.94) - 0.3, y, z], color: 'amber', size: RUN }]),
];

// Hangar light strips (emissive fixtures, see glbship.js): three 150 m strips across each bay
// ceiling (ray-cast ceilings: bays 2-5 y -0.55, aft bay -4.07, bay 1 -2.8, bow section -6.37),
// and a 64 m vertical strip on every frame face that looks into a flank bay, on the flat inboard
// part of the post (x 107..110 port, -105..-108 starboard, y -80..-15), 0.25 m off the face.
// Radiance ~1.8 (ceiling) / 0.9 (posts): they read as lit fixtures without crossing the bloom threshold.
const STRIP = { color: '#fff1e0', radiance: 1.8 };
const POST_STRIP = { color: '#ffe9d2', radiance: 0.9 }; // the vertical post strips: dimmer, seen face-on from outside
const BAY_CEILINGS = [[-255.5, -189, -4.07], [-164.6, -98.2, -0.55], [-73.4, -5.4, -0.55], [19.5, 87.1, -0.55], [111.8, 178.1, -0.55], [201.4, 275.8, -2.8], [276.8, 415, -6.37]];
const STRIPS = [
  ...BAY_CEILINGS.flatMap(([z0, z1, y]) => [1 / 6, 1 / 2, 5 / 6].map((f) => ({ ...STRIP, p: [0.9, y - 0.35, z0 + (z1 - z0) * f], size: [150, 0.3, 1.0] }))),
  ...FRAME_FACES.flatMap(([z, s]) => [108.5, -106.5].map((x) => ({ ...POST_STRIP, p: [x, -47.5, z + s * 0.25], size: [0.45, 64, 0.1] }))),
];

// hangar floodlights: under the five frame rings (ceiling -5.7) and in the bow section (-6.4)
// (a soft penumbra over the outer half of the cone gives each lamp a pool on the deck that falls
// off toward the bay backs and the flank sills instead of a flat, even fill; the stronger centre
// keeps the outboard rows at about the old irradiance)
const FLOOD = { kind: 'spot', color: '#fff3e8', intensity: 52000, distance: 240, angle: 64, penumbra: 0.55, fixture: 1.5 };

export const asset = {
  glb: './assets/ships/carrier.glb', generator: 'tripo3d/h3.1/multiview-to-3d',
  concept: './assets/concepts/carrier.webp', beauty: './assets/concepts/carrier-beauty.webp',
  rotate: [0, -90, 0],
  length: 900, // 900 x 405.5 x 319.3 m design (no slot normalisation)
  livery: 'dark',
  crease: 35, // armour blocks, turrets and the island shade flat; bells and barrels stay smooth
  liveryKeep: { box: [[-100, -97.5, -277], [101, -0.3, 414]], gain: 0.2, saturation: 0.08, feather: 1.5 },
  // the hangar (liveryKeep box) takes the 'deck' PATINA set instead of the hull set: 6 m tiles of
  // ~1.5 m tread plates with seams, tie-down cups and plate-to-plate tone, on the deck, walls and
  // ceiling alike (tri-planar). The tile-scale seams are held at half contrast (seam) and the
  // low-frequency grime / tyre-scuff tone is boosted (grime), so the deck reads as worn steel,
  // not a fine grid
  detail: {
    set: 'hull', tile: 6, normalStrength: 1.0, roughAmount: 0.5, cavity: 0.6,
    interior: { set: 'deck', tile: 6, normalStrength: 0.8, roughAmount: 0.6, cavity: 0.25, albedo: 0.9, seam: 0.5, grime: 1.6, feather: 1.5 },
  },
  engines: [
    { p: [58.36, -3.19, -449.9], radius: 18.3, ...BELL },
    { p: [-56.36, -3.21, -449.9], radius: 18.3, ...BELL },
    { p: [93.24, -50.10, -449.9], radius: 18.9, ...BELL_OUT },
    { p: [-91.24, -50.18, -449.9], radius: 18.9, ...BELL_OUT },
    { p: [58.31, -95.89, -449.9], radius: 18.3, ...BELL },
    { p: [-56.41, -95.91, -449.9], radius: 18.3, ...BELL },
  ],
  lights: [
    // steady sidelights on the outboard face of each stern gun sponson (the beam extremity)
    { p: [194.59, -55, -305], color: 'red', size: 0.4 },
    { p: [-192.65, -55, -305], color: 'green', size: 0.4 },
    // anti-collision strobes, alternating: island roof and keel flat
    { p: [0, 145.55, -110], color: 'white', size: 0.4, blink: { ...STROBE } },
    { p: [1, -145.61, -20], color: 'white', size: 0.4, blink: { ...STROBE, phase: 0.5 } },
    // steady stern light on the stern plate above the centre grille
    { p: [1, 9.99, -371.22], color: 'white', size: 0.4 },
    ...DECK_EDGE.map((p) => ({ p, color: 'white', size: RUN })),
    ...FLANK.map((p) => ({ p, color: 'amber', size: RUN })),
    ...MOUTH_RIM, ...GALLERY, ...BOW_WALL, ...OUTER,
  ],
  fixtures: STRIPS,
  interiorLights: [-176.5, -86, 7, 99.4, 189.7].map((z) => ({ ...FLOOD, p: [0.9, -7.0, z], target: [0.9, -96, z] }))
    .concat([{ ...FLOOD, p: [0.9, -7.6, 350], target: [0.9, -91, 350] }]),
  // only the hangar's own surfaces receive the floodlights: back wall to just past the mouth lip
  // (z -277 .. 425), from 1.1 m below the lowest deck (-96.36) up, out to the flank plating
  interiorLightGate: { box: [[-133, -97.5, -277], [135, 0, 425]], feather: 1 },
  // what the floodlit deck reflects onto the ceiling, the inner walls and the frame faces (the
  // hangar cavity only, so the outer flank plating inside the gate box stays unlit)
  interiorBounce: { box: [[-100, -97.5, -277], [101, 4, 416]], color: '#e9e4dc', irradiance: 1.2, feather: 3 },
  anchors: {
    hangar: { p: [0.9, -48.7, 80], size: [155.8, 84.4, 670] },
    hangarMouth: { p: [0.9, -48.7, 418], dir: [0, 0, 1] },
    hangarDeck: {
      lane: [-24, 26], // 50 m launch lane on the centreline, clear to the mouth (a fleet-scale fighter is 48 m wide)
      zones: {
        aft: { x: [-92.6, 94.4], z: [-255.5, -189], y: -92.45 },
        // bays 5-2 as one run of deck: the deck is continuous under the frame rings, so ships
        // longer than one bay (destroyers, corvettes at fleet scale) park across the frames
        long: { x: [-95.1, 96.4], z: [-164.6, 178.1], y: -96.35 },
        bay5: { x: [-95.1, 96.4], z: [-164.6, -98.2], y: -96.35 },
        bay4: { x: [-95.1, 96.4], z: [-73.4, -5.4], y: -96.36 },
        bay3: { x: [-95.1, 96.4], z: [19.5, 87.1], y: -96.36 },
        bay2: { x: [-95.1, 96.4], z: [111.8, 178.1], y: -96.34 },
        bay1: { x: [-81.6, 83.1], z: [201.4, 275.8], y: -93.61 },
        bow: { x: [-77.7, 79.6], z: [276.8, 415], y: -90.97 },
      },
      // where the hangar can be seen from outside (lib/park.js draws parked ships only then):
      // the six flank bays at the flank plating (clear z runs of a ray from inside, y range of
      // the opening) and the bow mouth; `inside` is the cavity itself
      openings: {
        flank: { x: [-129.7, 131.6], y: [-96, -1], z: [[-255, -191], [-163, -100], [-72, -7], [20, 86], [113, 177], [205, 273]] },
        mouth: { z: 418, x: [-93, 95], y: [-94.5, -6.4] },
        inside: { min: [-95, -97, -276], max: [96, 0, 418] },
      },
    },
  },
};
