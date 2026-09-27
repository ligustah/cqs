// Corvette K-214 — generated with fal (Tripo H3.1 multiview, see pipeline/fal-pipeline.json).
// Anchors were measured on the GLB in the centred ship frame (rotate -> length -> centre),
// metres, bow +Z, dorsal +Y, port +X, fleet scale 1 slot = 3,200 m^3.
// - rotate [0,-90,0] puts the bow (four torpedo doors) at +Z and the mast up; the hull
//   number is painted on both flanks, port (+X) as in the concept's front-left view.
// - length 36.6 m gives an envelope of 24.19 x 18.07 x 36.60 m = 15,996 m^3 (5 slots),
//   so the class volume correction is 1.000. The beam is set by the drive pods, the height
//   by the sensor mast and the keel.
// - Main drive: four bells at the corners of the stern frame and one bell at the aft end
//   of each outrigger pod. Centres are circle fits of the exit lip; the exit plane is the
//   lip's inner edge. The inner lip fits at r 0.72 m (main; lip 0.84 m outside) and 1.245 m
//   (pods; lip 1.39 m outside) but the generated wall wanders ~4 cm inside that, so the
//   radius is set 4 cm smaller (0.68 / 1.20) to keep the throat glow inside the bell wall.
//   The round openings at the pod noses are intakes, not drives. The mesh is not exactly
//   mirror-symmetric (the port bells sit ~4-5 cm further outboard), so port and starboard
//   anchors are listed explicitly.
// - Lights sit ~5 cm proud of the surface they are mounted on.
export const meta = {
  name: 'Warden-class corvette', designation: 'K-214', crew: 'about 25',
  blurb: 'Armoured escort corvette: a chamfered bow with four torpedo doors, a stepped bridge, two twin-barrel dorsal turrets and a sensor mast, four fusion bells in the stern frame and two outrigger drive pods on pylons.',
};
const MAIN_BELL = { depth: 1.04, throat: 0.34, wall: [[0.34, 0.61], [0.68, 0.54], [0.85, 0.5]] };
const POD_BELL = { depth: 1.74, throat: 0.49, wall: [[0.6, 1.07], [0.9, 1.0], [1.2, 0.63]] };

export const asset = {
  glb: './assets/ships/corvette.glb', generator: 'tripo3d/h3.1/multiview-to-3d',
  concept: './assets/concepts/corvette.webp', beauty: './assets/concepts/corvette-beauty.webp',
  rotate: [0, -90, 0],
  length: 36.6,
  livery: 'dark',
  crease: 35, // flat armour panels shade flat; bells, barrels and the mast pole stay smooth
  detail: { set: 'hull', tile: 6, normalStrength: 1.0, roughAmount: 0.5, cavity: 0.4 },
  engines: [
    // main hull: upper pair (port, starboard), lower pair. depth / throat / wall: ray-cast on the
    // GLB: the main bells converge steadily to a 0.5 r throat 1.53 r inside the lip; the pod bells
    // step in from 0.84 r to 0.53 r about 0.95 r deep, throat plate at 1.45 r
    { p: [3.748, -2.796, -18.25], radius: 0.68, ...MAIN_BELL },
    { p: [-3.677, -2.807, -18.25], radius: 0.68, ...MAIN_BELL },
    { p: [3.720, -6.200, -18.25], radius: 0.68, ...MAIN_BELL },
    { p: [-3.673, -6.180, -18.25], radius: 0.68, ...MAIN_BELL },
    // outrigger drive pods
    { p: [10.018, -6.439, -10.64], radius: 1.2, ...POD_BELL },
    { p: [-9.969, -6.436, -10.64], radius: 1.2, ...POD_BELL },
  ],
  lights: [
    // steady sidelights on the outboard face of each pod (the beam extremity), on the flat
    // plate just forward of the raised radiator grille: clear from ahead and abeam
    { p: [11.93, -6.55, -2.0], color: 'red', size: 0.4 },
    { p: [-11.905, -6.55, -2.0], color: 'green', size: 0.4 },
    // anti-collision strobes, alternating: masthead (between the antenna prongs) and keel
    { p: [0, 8.53, -6.08], color: 'white', size: 0.4, blink: { period: 1.3, duty: 0.1 } },
    { p: [0, -8.88, -6.0], color: 'white', size: 0.4, blink: { period: 1.3, duty: 0.1, phase: 0.5 } },
    // steady stern light on the stern plate between the upper bells
    { p: [0, -3.1, -18.15], color: 'white', size: 0.4 },
  ],
  anchors: {},
};
