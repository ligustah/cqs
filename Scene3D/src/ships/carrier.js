// Fleet carrier CV-50 — generated with fal (Tripo H3.1 multiview, see pipeline/fal-pipeline.json).
// A 900 m design (warp-capable, never carried itself, so no hangar-slot normalisation: the
// class scale correction is exactly 1). Everything below was measured on the GLB in the
// centred ship frame (rotate -> length -> centre), metres, bow +Z, dorsal +Y, port +X.
// - rotate [0,-90,0] puts the bow mouth at +Z and the island up; CV-50 reads on the port
//   flank (+X). length 900 gives an envelope of 405.5 x 319.3 x 900 m: the beam is set by the
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
//   bells) from the lip to the throat plate at z -406; the radii are set 0.2 m inside the wall.
// - Lights sit ~8 cm proud of the surface along its normal. Besides the nav lights, small
//   running lights repeat every 75 m along both dorsal deck edges (white) and every ~90 m along
//   both flanks (amber, on the frames and the bow / stern sections): at 900 m they are the
//   scale cue that the 0.4 m nav lights of the escorts share.
// - Hangar floodlights: six warm-white (4,500 K) spot lights hang under the ceiling on the
//   centreline, one under each frame ring (y -7, just below the ring's -5.7) and one in the bow
//   section, aimed straight down (65-degree half-angle). Each is 34,000 cd: inverse-square, it
//   gives about the sun's irradiance (4.2 scene units) on the deck 89 m below and ~45 % of it on
//   the parked ships at the outboard rows (~120 m away), windowed to zero at 260 m, so nothing
//   outside the hull is lit. They cast no shadow maps: six more shadow passes of the whole
//   hangar every frame would cost more than they show; the sun's shadows still ground the
//   ships in the sunlit bays.
// - liveryKeep: the operational repaint stops at the hangar: inside the cavity box the generated
//   texture keeps its own plating (x 0.25, 40 % saturation), so the deck reads as lit grey steel
//   instead of the near-black hull paint.
export const meta = {
  name: 'Keystone-class fleet carrier', designation: 'CV-50', crew: 'about 9,000',
  blurb: 'Warp-capable fleet carrier: a 900 m armoured box hull around one through-deck hangar that opens at the bow mouth and through six framed bays along each flank, with a stepped island, twin-gun turrets along the spine and on two stern sponsons, and six fusion bells in the stern block.',
};

const STROBE = { period: 1.3, duty: 0.1 };
const RUN = 0.6; // running-light size (m)

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

// hangar floodlights: under the five frame rings (ceiling -5.7) and in the bow section (-6.4)
const FLOOD = { kind: 'spot', color: '#ffdbba', intensity: 34000, distance: 260, angle: 65, penumbra: 0.3 };

export const asset = {
  glb: './assets/ships/carrier.glb', generator: 'tripo3d/h3.1/multiview-to-3d',
  concept: './assets/concepts/carrier.webp', beauty: './assets/concepts/carrier-beauty.webp',
  rotate: [0, -90, 0],
  length: 900, // 900 x 405.5 x 319.3 m design (no slot normalisation)
  livery: 'dark',
  crease: 35, // armour blocks, turrets and the island shade flat; bells and barrels stay smooth
  liveryKeep: { box: [[-100, -97.5, -277], [101, -0.3, 414]], gain: 0.25, saturation: 0.4, feather: 1.5 },
  detail: { set: 'hull', tile: 6, normalStrength: 1.0, roughAmount: 0.5, cavity: 0.4 },
  engines: [
    { p: [58.36, -3.19, -449.9], radius: 18.3 },
    { p: [-56.36, -3.21, -449.9], radius: 18.3 },
    { p: [93.24, -50.10, -449.9], radius: 18.9 },
    { p: [-91.24, -50.18, -449.9], radius: 18.9 },
    { p: [58.31, -95.89, -449.9], radius: 18.3 },
    { p: [-56.41, -95.91, -449.9], radius: 18.3 },
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
  ],
  interiorLights: [-176.5, -86, 7, 99.4, 189.7].map((z) => ({ ...FLOOD, p: [0.9, -7.0, z], target: [0.9, -96, z] }))
    .concat([{ ...FLOOD, p: [0.9, -7.6, 350], target: [0.9, -91, 350] }]),
  anchors: {
    hangar: { p: [0.9, -48.7, 80], size: [155.8, 84.4, 670] },
    hangarMouth: { p: [0.9, -48.7, 418], dir: [0, 0, 1] },
    hangarDeck: {
      lane: [-22.1, 23.9], // 46 m launch lane on the centreline, clear to the mouth
      zones: {
        aft: { x: [-92.6, 94.4], z: [-255.5, -189], y: -92.45 },
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
