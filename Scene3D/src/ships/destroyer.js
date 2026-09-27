// Destroyer DD-12 — generated with fal (Tripo H3.1 multiview, see pipeline/fal-pipeline.json).
// Anchors were measured on the GLB in the centred ship frame (rotate -> length -> centre),
// metres, bow +Z, dorsal +Y, port +X, fleet scale 1 slot = 3,200 m^3.
// - rotate [0,-90,0] puts the bow block (railgun muzzle) at +Z and the command tower up; the
//   hull number DD-12 reads on the port flank (+X) as in the concept's front-left view.
// - length 71.7 m gives an envelope of 22.04 x 24.32 x 71.70 m = 38,430 m^3 (12 slots), so the
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
  name: 'Bastion-class destroyer', designation: 'DD-12', crew: 'about 150',
  blurb: 'Heavy line destroyer built around a massive spinal railgun: an armoured bow block with the recessed muzzle, an exposed rail channel with capacitor banks along the spine, a stepped command tower, two small turrets, radiator panels on the flanks of the engine section and five fusion bells in the stern.',
};

const STROBE = { period: 1.3, duty: 0.1 };
const CORNER_BELL = { depth: 1.43, throat: 0.96, wall: [[0.74, 1.4], [1.11, 1.36], [1.4, 1.34]] };

export const asset = {
  glb: './assets/ships/destroyer.glb', generator: 'tripo3d/h3.1/multiview-to-3d',
  concept: './assets/concepts/destroyer.webp', beauty: './assets/concepts/destroyer-beauty.webp',
  rotate: [0, -90, 0],
  length: 71.7, // 71.7 x 22.0 x 24.3 m -> 38,430 m^3 = 12 slots
  livery: 'dark',
  crease: 35, // chamfered armour blocks and the tower shade flat; bells, pipes and the dome stay smooth
  detail: { set: 'hull', tile: 6, normalStrength: 1.0, roughAmount: 0.5, cavity: 0.4 },
  // the exposed rail channel (ray-cast: the rails run at x 0, y -0.9 between raised walls at
  // x +-3 from the command tower to the bow block, open to the flanks at z +11..+20) keeps a
  // muted version of the concept's copper coils and conduits instead of the grey repaint, at
  // about the hull's value, so the spinal gun reads as its own machinery
  liveryKeep: { box: [[-3.4, -6, -4], [3.4, 0.4, 22]], gain: 0.15, saturation: 0.45, feather: 0.6 },
  engines: [
    // corner bells, upper and lower pair; exit plane at the lip's aft face (z -35.85 .. -35.75)
    // (depth = the flat throat plate, ray-cast at 0.97 r; the hot throat is its inner 0.65 r)
    { p: [5.595, -3.32, -35.75], radius: 1.48, mirrorX: true, ...CORNER_BELL },
    { p: [5.595, -7.805, -35.75], radius: 1.48, mirrorX: true, ...CORNER_BELL },
    // centre bell, set 3 m forward between the corner bells
    { p: [0, -5.64, -32.85], radius: 2.05, depth: 1.2, throat: 1.4, wall: [[0.5, 2.0], [1.0, 1.98], [1.18, 1.96]] },
  ],
  lights: [
    // steady sidelights on the flat flank band of the engine section (beam extremity, plate at
    // x = +-10.96), at its forward end so they read from ahead and abeam
    { p: [11.02, -5.7, -16.0], color: 'red', size: 0.4 },
    { p: [-11.02, -5.7, -16.0], color: 'green', size: 0.4 },
    // anti-collision strobes, alternating: command tower roof ahead of the dome and masts
    // (roof y 6.11) and the keel plate under the engine section (y -12.04)
    { p: [0, 6.17, -15.0], color: 'white', size: 0.4, blink: { ...STROBE } },
    { p: [0, -12.10, -18.0], color: 'white', size: 0.4, blink: { ...STROBE, phase: 0.5 } },
    // steady stern light on the stern plate above the centre bell (plate z -30.35)
    { p: [0, -1.5, -30.41], color: 'white', size: 0.4 },
  ],
  anchors: {
    railgunMuzzle: { p: [0, -5.41, 32.85], dir: [0, 0, 1], radius: 0.95, mouth: [0, -5.41, 35.85] },
  },
};
