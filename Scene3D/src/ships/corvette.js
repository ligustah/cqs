// Corvette K-214 — generated with fal (Tripo H3.1 multiview, see pipeline/fal-pipeline.json).
// Re-detailed at true size for the 70,000 m^3 slot: the concept was regenerated as a ~105 m ship
// (nano-banana-pro/edit of the approved design), so its baked details are human-scale: rows of
// ~1 m windows, 2 m hatches, 1 m rails, a two-deck bridge tower, ~20 m twin barrels.
// Anchors were measured on the GLB in the centred ship frame (rotate -> length -> centre),
// metres, bow +Z, dorsal +Y, port +X, fleet scale 1 slot = 70,000 m^3.
// - rotate [0,-90,0] puts the bow (four torpedo doors) at +Z and the mast up; the hull
//   number is painted on both flanks, port (+X) as in the concept's front-left view.
// - length 105.46 m gives an envelope of 65.7 x 50.5 x 105.5 m = 350,000 m^3 (5 slots),
//   so the class volume correction is 1.000. The beam is set by the drive pods, the height
//   by the sensor mast and the keel.
// - Main drive: four bells in the stern frame (2 x 2) and one bell at the aft end of each
//   outrigger pod. Centres are circle fits of the inner lip just inside the exit; the exit plane
//   is the lip's inner edge. The inner lip fits at r 2.19-2.24 m (main) and 2.40-2.42 m (pods);
//   the radius is set a few cm smaller (2.18 / 2.38) to keep the throat glow inside the wall.
//   The round openings at the pod noses are intakes, not drives, and the two small tubes
//   above the stern frame are the aft turret's muzzles. Port and starboard anchors are
//   listed explicitly (the mesh is not exactly mirror-symmetric).
// - Lights sit ~5 cm proud of the surface they are mounted on.
export const meta = {
  name: 'Warden-class corvette', designation: 'K-214', crew: 'about 350',
  blurb: 'Armoured escort corvette: a chamfered bow with four torpedo doors, a bridge house and a two-deck bridge tower, two twin-barrel dorsal gun mounts and a sensor mast, four fusion bells in the stern frame and two outrigger drive pods on pylons.',
};
// depth / throat / wall: ray-cast on the GLB (axial rays from astern + radial slices). The main
// bells converge to a ledge ~2 m in (r 2.0 -> 1.8), then steadily to a shallow conical throat
// plate ~5.4 m deep; the pod bells converge smoothly to a throat plate ~5.1 m deep
const MAIN_BELL = { depth: 5.35, throat: 1.2, wall: [[0.85, 2.13], [1.85, 1.98], [2.0, 1.8], [3.4, 1.7], [4.0, 1.62], [4.4, 1.53], [4.75, 1.43], [5.05, 1.33]] };
const POD_BELL = { depth: 5.1, throat: 1.1, wall: [[0.9, 2.37], [1.9, 2.29], [2.9, 2.07], [3.4, 1.94], [3.9, 1.76], [4.2, 1.66], [4.6, 1.53], [4.9, 1.35]] };

export const asset = {
  glb: './assets/ships/corvette.glb', generator: 'tripo3d/h3.1/multiview-to-3d',
  concept: './assets/concepts/corvette.webp', beauty: './assets/concepts/corvette-beauty.webp',
  rotate: [0, -90, 0],
  length: 105.46,
  livery: 'dark',
  crease: 35, // flat armour panels shade flat; bells, barrels and the mast pole stay smooth
  detail: { set: 'hull', tile: 6, normalStrength: 1.0, roughAmount: 0.5, cavity: 0.4 },
  engines: [
    // main hull: upper pair (starboard, port), lower pair
    { p: [-9.694, -7.812, -52.51], radius: 2.18, ...MAIN_BELL },
    { p: [9.691, -7.787, -52.57], radius: 2.18, ...MAIN_BELL },
    { p: [-9.54, -16.88, -52.21], radius: 2.18, ...MAIN_BELL },
    { p: [9.588, -16.848, -52.31], radius: 2.18, ...MAIN_BELL },
    // outrigger drive pods
    { p: [27.336, -17.165, -29.42], radius: 2.38, ...POD_BELL },
    { p: [-27.354, -17.154, -29.42], radius: 2.38, ...POD_BELL },
  ],
  lights: [
    // steady sidelights on the flat outboard face of each pod (the beam extremity): clear from
    // ahead and abeam
    { p: [32.9, -17.2, -12], color: 'red', size: 0.4 },
    { p: [-32.88, -17.2, -12], color: 'green', size: 0.4 },
    // anti-collision strobes, alternating: masthead (between the antenna prongs) and keel
    { p: [0, 23.4, -16.3], color: 'white', size: 0.4, blink: { period: 1.3, duty: 0.1 } },
    { p: [0, -25.29, -10], color: 'white', size: 0.4, blink: { period: 1.3, duty: 0.1, phase: 0.5 } },
    // steady stern light on the stern plate between the four bells
    { p: [0, -12, -51.37], color: 'white', size: 0.4 },
  ],
  anchors: {},
};
