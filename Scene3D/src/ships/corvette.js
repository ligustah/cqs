// Corvette K-214 — v7 clean primary-form hull, generated with fal (see pipeline/fal-pipeline.json).
// fal-ai/nano-banana-pro/edit redrew the approved concept as big, clear primary forms (flat planes,
// hard chamfers, a few large panel breaks, one dark glazing band per bridge tier, no portholes, doors,
// rails, antennas or greebles; those come later as reusable fal-made parts placed on
// asset.anchors.surfaces). A 4K orthographic turnaround gave front / port / stern / starboard views
// for tripo3d/h3.1/multiview-to-3d (detailed geometry and texture), which won a bake-off for crisp
// planar faces against the same call with quad topology (rounded, blobby edges) and
// fal-ai/hunyuan-3d/v3.1/pro multiview (stubby proportions, garbled hull number).
// Measured on the GLB in the centred ship frame (rotate -> length -> centre), metres, bow +Z,
// dorsal +Y, port +X, fleet scale 1 slot = 70,000 m^3.
// - rotate [0,-90,0] puts the bow (four torpedo doors) at +Z and the mast up.
// - length 108.1 m gives an envelope of 69.5 x 46.6 x 108.1 m = 350,000 m^3 (5 slots), so the class
//   volume correction is ~1.000. The beam is set by the drive pods, the height by the mast and keel.
// - Main drive: one large central bell and four small bells in the stern frame, plus one bell at the
//   aft end of each outrigger pod. Centres and radii are circle fits of the inner wall 0.15 m inside
//   the lip (the exit plane); radius set a few cm inside the fit; depth = axial ray to the throat plate.
export const meta = {
  name: 'Warden-class corvette', designation: 'K-214', crew: 'about 350',
  blurb: 'Armoured escort corvette: a chamfered bow with four torpedo doors, a bridge house and a two-tier bridge tower, two twin-barrel dorsal gun mounts and a sensor mast, five fusion bells in the stern frame and two outrigger drive pods on pylons.',
};
// wall: [depth in from the lip, inner radius] from radial circle fits at slices behind the lip
const CENTRE_BELL = { depth: 8.85, throat: 3.6, wall: [[0.3, 5.06], [1.0, 4.79], [2.0, 4.44], [3.0, 4.15], [4.0, 3.95], [5.0, 3.85], [6.0, 3.74], [7.0, 3.64]] };
const UPPER_BELL = { depth: 8.15, throat: 1.7, wall: [[0.3, 2.39], [1.0, 2.22], [2.0, 1.98], [3.0, 1.75], [5.0, 1.73], [7.0, 1.75]] };
const LOWER_BELL = { depth: 9.05, throat: 1.7, wall: [[0.3, 2.29], [1.0, 2.13], [2.0, 1.9], [3.0, 1.69], [5.0, 1.71], [7.0, 1.74]] };
const POD_BELL = { depth: 7.6, throat: 2.15, wall: [[0.3, 3.4], [1.0, 3.17], [2.0, 2.86], [3.0, 2.59], [4.0, 2.43], [5.0, 2.3], [6.0, 2.21], [7.0, 2.19]] };

export const asset = {
  glb: './assets/ships/corvette.glb', generator: 'tripo3d/h3.1/multiview-to-3d',
  concept: './assets/concepts/corvette.webp', beauty: './assets/concepts/corvette-beauty.webp',
  rotate: [0, -90, 0],
  length: 108.1,
  livery: 'dark',
  crease: 35, // flat armour panels shade flat; bells, barrels and the mast stay smooth
  detail: { set: 'hull', tile: 6, normalStrength: 1.0, roughAmount: 0.5, cavity: 0.4 },
  engines: [
    { p: [0.062, -10.0, -52.52], radius: 5.12, ...CENTRE_BELL },
    { p: [9.912, -5.445, -53.69], radius: 2.45, ...UPPER_BELL },
    { p: [-9.792, -5.437, -53.69], radius: 2.45, ...UPPER_BELL },
    { p: [9.847, -14.087, -53.99], radius: 2.34, ...LOWER_BELL },
    { p: [-9.748, -14.079, -54.04], radius: 2.34, ...LOWER_BELL },
    // outrigger drive pods
    { p: [28.659, -15.071, -34.5], radius: 3.46, ...POD_BELL },
    { p: [-28.574, -15.074, -34.5], radius: 3.46, ...POD_BELL },
  ],
  lights: [
    // steady sidelights on the flat outboard face of each pod (the beam extremity): red port, green starboard
    { p: [34.17, -15.1, -8], color: 'red', size: 0.4 },
    { p: [-34.07, -15.1, -8], color: 'green', size: 0.4 },
    // anti-collision strobes, alternating: masthead (top of the sensor block) and keel
    { p: [0.14, 23.34, -12.4], color: 'white', size: 0.4, blink: { period: 1.3, duty: 0.1 } },
    { p: [0, -23.14, 0], color: 'white', size: 0.4, blink: { period: 1.3, duty: 0.1, phase: 0.5 } },
    // steady stern light on the flat stern-frame face above the centre bell
    { p: [0, -2.5, -49.22], color: 'white', size: 0.4 },
  ],
  anchors: {
    // Flat hull faces for the composition step (window rows, doors, rails): rectangles in the
    // centred ship frame before the ~1.000 class correction. width runs along u, height along
    // normal x u (for the flanks that is up). Ray-cast on the mesh (0.5 m grid along -normal,
    // plane refit): flat = share of samples within 0.15 m of the plane (panel seams and raised
    // panels count against it). The pod hides flank-mid from abeam; turret barrels overhang the
    // dorsal deck; the bridge front is faceted (+-13 deg side facets) with the glazing recessed.
    surfaces: {
    'flank-fore-port': { centre: [16.22, -11, 8.75], normal: [1, 0.011, -0.002], u: [0.002, 0, 1], width: 19.5, height: 10.5, flat: 0.84 }, // vertical flank between the pylon and the bow taper
    'flank-fore-stbd': { centre: [-16.16, -11, 8.75], normal: [-1, 0.009, -0.004], u: [-0.004, 0, 1], width: 19.5, height: 10.5, flat: 0.85 }, // vertical flank between the pylon and the bow taper
    'flank-mid-port': { centre: [15.96, -11, -26.5], normal: [1, 0.007, -0.006], u: [0.006, 0, 1], width: 15, height: 10.5, flat: 0.9 }, // vertical flank behind the drive pod (seen past the pod from above or below)
    'flank-mid-stbd': { centre: [-15.88, -11, -26.5], normal: [-1, 0.004, -0.006], u: [-0.006, 0, 1], width: 15, height: 10.5, flat: 0.91 }, // vertical flank behind the drive pod (seen past the pod from above or below)
    'flank-aft-port': { centre: [15.58, -10.75, -41.25], normal: [0.999, -0.008, -0.034], u: [0.034, 0, 0.999], width: 12.5, height: 9.5, flat: 0.85 }, // vertical flank between the stern frame and the drive pod
    'flank-aft-stbd': { centre: [-15.51, -10.75, -41.25], normal: [-0.999, -0.009, -0.036], u: [-0.036, 0, 0.999], width: 12.5, height: 9.5, flat: 0.85 }, // vertical flank between the stern frame and the drive pod
    'flank-bow-port': { centre: [12.46, -11, 34.74], normal: [0.973, 0.02, 0.229], u: [-0.23, 0, 0.973], width: 31, height: 10.5, flat: 0.73 }, // tapered bow flank; carries the K-214 hull number (about z 30-45)
    'flank-bow-stbd': { centre: [-12.38, -11, 34.72], normal: [-0.973, 0.021, 0.231], u: [0.231, 0, 0.973], width: 31, height: 10.5, flat: 0.69 }, // tapered bow flank; carries the K-214 hull number (about z 30-45)
    'shoulder-port': { centre: [14.92, -3.49, -6], normal: [0.81, 0.586, -0.008], u: [0.006, 0.004, 1], width: 48, height: 3.5, flat: 0.98 }, // 45-degree chamfer from the flank up to the main-deck edge
    'shoulder-stbd': { centre: [-14.88, -3.52, -6], normal: [-0.808, 0.59, -0.007], u: [-0.005, 0.004, 1], width: 48, height: 3.5, flat: 0.98 }, // 45-degree chamfer from the flank up to the main-deck edge
    'deck-walk-port': { centre: [11.9, -1.52, -9.5], normal: [0.012, 1, 0], u: [0, 0, 1], width: 71, height: 2.6, flat: 0.99 }, // main-deck side walkway outboard of the deckhouse (deck-edge rails along its outer edge)
    'deck-walk-stbd': { centre: [-11.9, -1.52, -9.5], normal: [-0.029, 1, 0], u: [0, 0, 1], width: 71, height: 2.6, flat: 0.98 }, // main-deck side walkway outboard of the deckhouse (deck-edge rails along its outer edge)
    'deckhouse-side-port': { centre: [9.17, 0.98, -5.5], normal: [0.889, 0.459, 0], u: [0, 0, 1], width: 47, height: 4.4, flat: 0.71 }, // sloped deckhouse flank under the turrets and tower, main deck to roof
    'deckhouse-side-stbd': { centre: [-9.09, 0.94, -5.5], normal: [-0.881, 0.473, -0.001], u: [-0.001, 0.001, 1], width: 47, height: 4.4, flat: 0.7 }, // sloped deckhouse flank under the turrets and tower, main deck to roof
    'tower-side-port': { centre: [5.92, 7.85, -10.75], normal: [1, -0.004, -0.012], u: [0.012, 0, 1], width: 6.5, height: 1.7, flat: 1 }, // vertical lower-tier side of the bridge tower
    'tower-side-stbd': { centre: [-5.81, 7.85, -10.75], normal: [-1, -0.015, -0.024], u: [-0.024, 0, 1], width: 6.5, height: 1.7, flat: 1 }, // vertical lower-tier side of the bridge tower
    'stern-deck': { centre: [0, -1.47, -42.75], normal: [0.001, 1, 0], u: [0, 0, 1], width: 9.5, height: 22, flat: 0.74 }, // flat main deck aft of the deckhouse, between the shoulder chamfers
    'dorsal-deck': { centre: [0, 3.45, 14.75], normal: [0, 1, -0.01], u: [0, 0.01, 1], width: 8.5, height: 14, flat: 0.82 }, // deckhouse roof between the bridge front and the forward turret
    'bridge-glacis': { centre: [0, -0.55, 27.08], normal: [0, 0.707, 0.707], u: [1, 0, 0], width: 9, height: 2.9, flat: 0.26 }, // 45-degree bridge front below the glazing band
    'bridge-glazing': { centre: [0, 1.3, 23.78], normal: [0, 0.707, 0.707], u: [1, 0, 0], width: 9, height: 1.4, flat: 0.39 }, // the bridge glazing band: a recess ~1 m deep across the glacis
    'tower-front': { centre: [0, 7.75, -5.73], normal: [0.001, -0.005, 1], u: [1, 0, -0.001], width: 9, height: 1.9, flat: 1 }, // vertical lower tier of the bridge-tower front, behind the forward turret
    'tower-glazing': { centre: [0, 11.51, -5.06], normal: [-0.001, -0.605, 0.796], u: [1, 0, 0.001], width: 9, height: 2.2, flat: 1 }, // canted tower glazing band (leans out, faces forward and down)
    },
  },
};
