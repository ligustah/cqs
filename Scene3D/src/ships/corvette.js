// Corvette K-214 — generated with fal (Tripo H3.1 multiview, see pipeline/fal-pipeline.json).
// Anchors were measured on the GLB in the centred ship frame (rotate -> length -> centre),
// metres, bow +Z, dorsal +Y, port +X, fleet scale 1 slot = 70,000 m^3.
// - rotate [0,-90,0] puts the bow (four torpedo doors) at +Z and the mast up; the hull
//   number is painted on both flanks, port (+X) as in the concept's front-left view.
// - length 102.4 m gives an envelope of 67.7 x 50.5 x 102.4 m = 350,000 m^3 (5 slots),
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
  name: 'Warden-class corvette', designation: 'K-214', crew: 'about 350',
  blurb: 'Armoured escort corvette: a chamfered bow with four torpedo doors, a stepped bridge, two twin-barrel dorsal turrets and a sensor mast, four fusion bells in the stern frame and two outrigger drive pods on pylons.',
};
const MAIN_BELL = { depth: 2.909, throat: 0.951, wall: [[0.951, 1.706], [1.902, 1.51], [2.377, 1.398]] };
const POD_BELL = { depth: 4.866, throat: 1.37, wall: [[1.678, 2.992], [2.517, 2.797], [3.356, 1.762]] };

export const asset = {
  glb: './assets/ships/corvette.glb', generator: 'tripo3d/h3.1/multiview-to-3d',
  concept: './assets/concepts/corvette.webp', beauty: './assets/concepts/corvette-beauty.webp',
  rotate: [0, -90, 0],
  length: 102.36,
  livery: 'dark',
  crease: 35, // flat armour panels shade flat; bells, barrels and the mast pole stay smooth
  detail: { set: 'hull', tile: 6, normalStrength: 1.0, roughAmount: 0.5, cavity: 0.4 },
  engines: [
    // main hull: upper pair (port, starboard), lower pair. depth / throat / wall: ray-cast on the
    // GLB: the main bells converge steadily to a 0.5 r throat 1.53 r inside the lip; the pod bells
    // step in from 0.84 r to 0.53 r about 0.95 r deep, throat plate at 1.45 r
    { p: [10.482, -7.82, -51.04], radius: 1.902, ...MAIN_BELL },
    { p: [-10.284, -7.85, -51.04], radius: 1.902, ...MAIN_BELL },
    { p: [10.404, -17.34, -51.04], radius: 1.902, ...MAIN_BELL },
    { p: [-10.272, -17.284, -51.04], radius: 1.902, ...MAIN_BELL },
    // outrigger drive pods
    { p: [28.018, -18.008, -29.757], radius: 3.356, ...POD_BELL },
    { p: [-27.881, -18, -29.757], radius: 3.356, ...POD_BELL },
  ],
  lights: [
    // steady sidelights on the outboard face of each pod (the beam extremity), on the flat
    // plate just forward of the raised radiator grille: clear from ahead and abeam
    { p: [33.365, -18.319, -5.593], color: 'red', size: 0.4 },
    { p: [-33.295, -18.319, -5.593], color: 'green', size: 0.4 },
    // anti-collision strobes, alternating: masthead (between the antenna prongs) and keel
    { p: [0, 23.856, -17.004], color: 'white', size: 0.4, blink: { period: 1.3, duty: 0.1 } },
    { p: [0, -24.835, -16.78], color: 'white', size: 0.4, blink: { period: 1.3, duty: 0.1, phase: 0.5 } },
    // steady stern light on the stern plate between the upper bells
    { p: [0, -8.67, -50.761], color: 'white', size: 0.4 },
  ],
  anchors: {},
};
