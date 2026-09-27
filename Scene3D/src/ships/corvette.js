// Corvette K-214 — generated with fal (Tripo H3.1 multiview, see pipeline/fal-pipeline.json).
// v5 re-detail at true size for the 70,000 m^3 slot: nano-banana-pro/edit of the approved design
// (bridge glazing as stacked rows of small framed panes, "K-214" in Latin capitals), then a 4K
// orthographic turnaround whose port / starboard views carry rows of ~0.7 m ports on a ~3 m deck
// pitch, thin rails and ladders; front / port / stern / starboard went to Tripo H3.1 multiview.
// Both flanks carry a clean, non-mirrored "K-214" stencil in the reconstruction (no texture fix).
// Anchors were measured on the GLB in the centred ship frame (rotate -> length -> centre),
// metres, bow +Z, dorsal +Y, port +X, fleet scale 1 slot = 70,000 m^3.
// - rotate [0,-90,0] puts the bow (four torpedo doors) at +Z and the mast up; the hull
//   number reads left-to-right on both flanks.
// - length 107.1 m gives an envelope of 68.8 x 47.5 x 107.1 m = 349,930 m^3 (5 slots),
//   so the class volume correction is 1.000. The beam is set by the drive pods, the height
//   by the mast's antenna cross and the keel.
// - Main drive: four bells in the stern frame (2 x 2) and one bell at the aft end of each
//   outrigger pod. Centres are circle fits of the inner wall just inside the lip; the exit plane
//   is the lip. Main bells: inner lip r 2.24 m; pod bells: a chamfered lip (r 3.6-3.9) opening to
//   r 3.46 m 0.3 m in. The radius is set a few cm inside (2.2 / 3.42) so the lining stays inside
//   the wall. The round openings at the pod noses are intakes, not drives. Port and starboard
//   anchors are listed explicitly (the mesh is not exactly mirror-symmetric).
// - Lights sit ~5 cm proud of the surface they are mounted on.
export const meta = {
  name: 'Warden-class corvette', designation: 'K-214', crew: 'about 350',
  blurb: 'Armoured escort corvette: a chamfered bow with four torpedo doors, a bridge house and a two-deck bridge tower, two twin-barrel dorsal gun mounts and a sensor mast, four fusion bells in the stern frame and two outrigger drive pods on pylons.',
};
// depth / throat / wall: ray-cast on the GLB (axial rays from astern + radial circle fits at
// slices behind the lip). The main bells are a straight cone from r 2.24 at the lip to a flat
// throat plate (r ~1.35) 3.37 m in, with a 0.75 m central recess behind it; the pod bells
// converge steadily from r 3.46 to a throat plate (r ~1.45) 7.3 m in
const MAIN_BELL = { depth: 3.35, throat: 1.3, wall: [[0.3, 2.18], [0.6, 2.09], [1.0, 1.98], [1.5, 1.84], [2.0, 1.69], [2.5, 1.55], [3.0, 1.42]] };
const POD_BELL = { depth: 7.25, throat: 1.4, wall: [[0.3, 3.46], [1.0, 3.3], [2.0, 3.05], [3.0, 2.79], [4.0, 2.53], [5.0, 2.26], [6.0, 1.95], [6.6, 1.8], [7.0, 1.69]] };

export const asset = {
  glb: './assets/ships/corvette.glb', generator: 'tripo3d/h3.1/multiview-to-3d',
  concept: './assets/concepts/corvette.webp', beauty: './assets/concepts/corvette-beauty.webp',
  rotate: [0, -90, 0],
  length: 107.1,
  livery: 'dark',
  crease: 35, // flat armour panels shade flat; bells, barrels and the mast pole stay smooth
  detail: { set: 'hull', tile: 6, normalStrength: 1.0, roughAmount: 0.5, cavity: 0.4 },
  engines: [
    // main hull: upper pair (starboard, port), lower pair
    { p: [-10.818, -6.227, -53.54], radius: 2.2, ...MAIN_BELL },
    { p: [10.814, -6.223, -53.53], radius: 2.2, ...MAIN_BELL },
    { p: [-10.822, -16.362, -53.53], radius: 2.2, ...MAIN_BELL },
    { p: [10.819, -16.363, -53.54], radius: 2.2, ...MAIN_BELL },
    // outrigger drive pods
    { p: [29.066, -16.405, -30.09], radius: 3.42, ...POD_BELL },
    { p: [-29.083, -16.45, -29.93], radius: 3.42, ...POD_BELL },
  ],
  lights: [
    // steady sidelights on the flat outboard face of each pod (the beam extremity): red port,
    // green starboard, clear from ahead and abeam
    { p: [34.25, -17, -12], color: 'red', size: 0.4 },
    { p: [-34.3, -17, -12], color: 'green', size: 0.4 },
    // anti-collision strobes, alternating: masthead (top of the antenna cross) and keel
    { p: [0.3, 23.78, -17.7], color: 'white', size: 0.4, blink: { period: 1.3, duty: 0.1 } },
    { p: [-0.2, -23.79, 19.7], color: 'white', size: 0.4, blink: { period: 1.3, duty: 0.1, phase: 0.5 } },
    // steady stern light on the stern plate between the four bells
    { p: [0, -11, -50.99], color: 'white', size: 0.4 },
  ],
  anchors: {},
};
