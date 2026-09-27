// Destroyer DD-12 — generated with fal (Tripo H3.1 multiview, see pipeline/fal-pipeline.json).
// Anchors were measured on the GLB in the centred ship frame (rotate -> length -> centre),
// metres, bow +Z, dorsal +Y, port +X, fleet scale 1 slot = 70,000 m^3.
// - rotate [0,-90,0] puts the bow block (railgun muzzle) at +Z and the command tower up; the
//   hull number DD-12 reads on the port flank (+X) as in the concept's front-left view.
// - length 200.5 m gives an envelope of 61.6 x 68.0 x 200.5 m = 840,000 m^3 (12 slots), so the
//   class volume correction is 0.9997. The beam is set by the flank plates of the engine
//   section (x = +-11.02), the height by the tower's antenna (y = +12.16) and the keel plate
//   under the engine section (y = -12.04; the envelope bottom -12.16 is a keel fitting).
// - Main drive: five bells in the stern block, the four corner bells of the concept plus the
//   large centre bell of the turnaround stern view (the biggest nozzle, with its own throat:
//   a main drive, not a recoil or RCS nozzle). Centres are circle fits of the exit lip
//   (corner bells: port 5.586 / 5.592, starboard -5.605 / -5.590, so one mirrored entry each);
//   the exit plane is the aft face of the lip. Corner bells: lip r 1.72-1.92, inner wall 1.50-1.54
//   at the exit, throat plate 1.45 m deep -> radius 1.48. Centre bell: lip r 2.52-2.71 at
//   z -32.90 (3 m forward of the corner lips), inner wall 2.09-2.19, throat plate 1.2 m deep
//   -> radius 2.05.
// - Railgun: the bow block's stepped octagonal shroud (mouth at z = +35.85) is recessed 3 m to a
//   step face at z = +32.85 where the bore opens (r 0.95, centre x 0, y -5.41); the muzzle anchor
//   is the centre of that bore opening. `mouth` is the shroud mouth on the same axis.
// - Lights sit ~6 cm proud of the surface they are mounted on.
export const meta = {
  name: 'Bastion-class destroyer', designation: 'DD-12', crew: 'about 2,000',
  blurb: 'Heavy line destroyer built around a massive spinal railgun: an armoured bow block with the recessed muzzle, an exposed rail channel with capacitor banks along the spine, a stepped command tower, two small turrets, radiator panels on the flanks of the engine section and five fusion bells in the stern.',
};

const STROBE = { period: 1.3, duty: 0.1 };
const MUZZLE_RIM = { color: '#b4c2dc', radiance: 0.07 };
// the glow sits just aft of the central plug (not at the throat plate behind it), so the plug
// does not show as a dark disc in the middle of the glow
const CORNER_BELL = { depth: 1.538, throat: 3.356, wall: [[0.839, 3.971]] };

export const asset = {
  glb: './assets/ships/destroyer.glb', generator: 'tripo3d/h3.1/multiview-to-3d',
  concept: './assets/concepts/destroyer.webp', beauty: './assets/concepts/destroyer-beauty.webp',
  rotate: [0, -90, 0],
  length: 200.525, // 200.5 x 61.6 x 68.0 m -> 840,000 m^3 = 12 slots
  livery: 'dark',
  crease: 35, // chamfered armour blocks and the tower shade flat; bells, pipes and the dome stay smooth
  detail: { set: 'hull', tile: 6, normalStrength: 1.0, roughAmount: 0.5, cavity: 0.4 },
  // the exposed rail channel (ray-cast: the rails run at x 0, y -0.9 between raised walls at
  // x +-3 from the command tower to the bow block, open to the flanks at z +11..+20) keeps a
  // muted version of the concept's copper coils and conduits instead of the grey repaint, at
  // a little above the hull's value, so the copper coils and capacitor banks separate from the
  // grey armour in sunlight and the spinal gun reads as its own machinery. A second box keeps the
  // texture's steel inside the recessed muzzle shroud (ray-cast: the opening is ~3.5 m half-wide and
  // 2.3-2.5 m high about y -5.4, the bow face stands at z 35.85 only a narrow frame around it and
  // steps back to z ~32.5 beyond x ~4.5; the box stops short of the mouth plane so the bow face
  // keeps the livery): its paler steel walls around the dark bore show the gun's business end
  // whenever light reaches into the shroud
  liveryKeep: [
    { box: [[-3.4, -6, -4], [3.4, 0.4, 22]], gain: 0.3, saturation: 0.6, feather: 0.6 },
    { box: [[-4.2, -8.2, 31.2], [4.2, -2.4, 35.75]], gain: 0.55, saturation: 0.2, feather: 0.25 },
  ],
  // Muzzle rim: a dim, cool field-coil band just inside the lip of the octagonal shroud (one
  // strip per face, ray-cast: faces 3.5 m out at the sides, 2.5 m up, 2.3 m down, 3.2-3.5 m on the
  // diagonals, about the bore axis at y -5.41), so the gun's mouth reads as an octagon even
  // when the bow face is in shadow. Radiance 0.07: a faint glint in the shadow, not a lamp.
  fixtures: [
    { ...MUZZLE_RIM, p: [9.593, -14.635, 99.144], size: [2.32, 0.04, 0.12], rotZ: 1.5708 },
    { ...MUZZLE_RIM, p: [8.124, -9.886, 99.144], size: [1.48, 0.04, 0.12], rotZ: 2.3562 },
    { ...MUZZLE_RIM, p: [-0.02, -8.418, 99.144], size: [4.64, 0.04, 0.12], rotZ: 3.1416 },
    { ...MUZZLE_RIM, p: [-8.158, -9.881, 99.144], size: [1.48, 0.04, 0.12], rotZ: -2.3562 },
    { ...MUZZLE_RIM, p: [-9.621, -14.616, 99.144], size: [2.31, 0.04, 0.12], rotZ: -1.5708 },
    { ...MUZZLE_RIM, p: [-7.937, -19.571, 99.144], size: [1.7, 0.04, 0.12], rotZ: -0.7854 },
    { ...MUZZLE_RIM, p: [0, -21.255, 99.144], size: [4.35, 0.04, 0.12], rotZ: -0.0 },
    { ...MUZZLE_RIM, p: [7.923, -19.585, 99.144], size: [1.69, 0.04, 0.12], rotZ: 0.7854 },
  ],
  engines: [
    // corner bells, upper and lower pair; exit plane at the lip's aft face (z -35.85 .. -35.75)
    // (depth = the flat throat plate, ray-cast at 0.97 r; the hot throat is its inner 0.65 r)
    { p: [15.648, -9.285, -99.983], radius: 4.139, mirrorX: true, ...CORNER_BELL },
    { p: [15.648, -21.828, -99.983], radius: 4.139, mirrorX: true, ...CORNER_BELL },
    // centre bell, set 3 m forward between the corner bells
    { p: [0, -15.774, -91.872], radius: 5.733, depth: 3.356, throat: 3.915, wall: [[1.398, 5.593], [2.797, 5.538], [3.3, 5.482]] },
  ],
  lights: [
    // steady sidelights on the flat flank band of the engine section (beam extremity, plate at
    // x = +-10.96), at its forward end so they read from ahead and abeam
    { p: [30.82, -15.941, -44.748], color: 'red', size: 0.4 },
    { p: [-30.82, -15.941, -44.748], color: 'green', size: 0.4 },
    // anti-collision strobes, alternating: command tower roof ahead of the dome and masts
    // (roof y 6.11) and the keel plate under the engine section (y -12.04)
    { p: [0, 17.256, -41.951], color: 'white', size: 0.4, blink: { ...STROBE } },
    { p: [0, -33.84, -50.341], color: 'white', size: 0.4, blink: { ...STROBE, phase: 0.5 } },
    // steady stern light on the stern plate above the centre bell (plate z -30.35)
    { p: [0, -4.195, -85.048], color: 'white', size: 0.4 },
  ],
  anchors: {
    railgunMuzzle: { p: [0, -15.13, 91.872], dir: [0, 0, 1], radius: 2.657, mouth: [0, -5.41, 35.85] },
  },
};
