// Destroyer DD-12 — generated with fal (Tripo H3.1 multiview, see pipeline/fal-pipeline.json).
// Re-detailed at true size for the 70,000 m^3 slot: the concept was regenerated (nano-banana-pro/edit
// of the approved design, two passes) as a 200 m heavy destroyer with a crew of about 2,000: a
// multi-deck bridge tower, rows of ~1 m portholes along the flanks, 2 x 1 m crew hatches, catwalks
// with 1 m hand rails beside the rails, capacitor banks the size of buildings; then a 4K turnaround
// sheet of it was reconstructed.
// Anchors were measured on the GLB in the centred ship frame (rotate -> length -> centre),
// metres, bow +Z, dorsal +Y, port +X, fleet scale 1 slot = 70,000 m^3.
// - rotate [0,-90,0] puts the bow block (railgun muzzle) at +Z and the bridge tower up; the hull
//   number reads on the port flank (+X) as in the concept's front-left view.
// - length 204.2 m gives an envelope of 56.04 x 73.39 x 204.2 m = 840,000 m^3 (12 slots), so the
//   class volume correction is ~1.000. The beam is set by the flank plates of the engine section
//   (x = +-28.02), the height by the tower's masts (y = +36.70) and the keel (y = -36.70).
// - Main drive: five bells in the stern block. Corner bells: circle fits of the inner wall at 4 m
//   (port 13.774 / 13.781 / 13.790 / 13.798 and starboard mirror, so one mirrored entry per pair),
//   exit plane at the lip's aft face (z -101.07), inner wall r 4.04 at the exit narrowing to 2.45
//   at 6 m, where the throat plate (7.2-7.9 m behind the lip face, flat to r 2.2) begins; the glow
//   sits 6.0 m in, in front of the plate. Centre bell: exit at z -102.03 (the aftmost lip),
//   inner wall r 6.22 at the exit, a throat ring r 4.10 at 9.7 m, a chamber behind it and a
//   central plate whose face is 12.26 m in; the glow sits 12.0 m in, in front of it.
// - Railgun: the bow block's octagonal shroud (mouth lip z +101.9, 18.4 m wide, 12.2 m high,
//   centre y -18.8) is recessed 11 m; a hexagonal barrel boss stands in it and the bore
//   (r 2.24-2.70, centre x 0, y -18.35) opens at its face at z +98.47. The muzzle anchor is the
//   centre of that bore opening; `mouth` is the shroud mouth on the same axis.
// - Lights sit ~6 cm proud of the surface they are mounted on.
export const meta = {
  name: 'Bastion-class destroyer', designation: 'DD-12', crew: 'about 2,000',
  blurb: 'Heavy line destroyer built around a massive spinal railgun: an armoured bow block with the recessed muzzle, an exposed rail channel with capacitor banks along the spine, a multi-deck bridge tower, heavy naval turrets, radiator panels on the flanks of the engine section and five fusion bells in the stern.',
};

const STROBE = { period: 1.3, duty: 0.1 };
const MUZZLE_RIM = { color: '#b4c2dc', radiance: 0.07 };
// corner bells: glow in front of the throat plate (see above)
const CORNER_BELL = {
  radius: 4.05, depth: 6.0, throat: 2.45,
  wall: [[0.72, 4.04], [1.72, 4.0], [2.72, 3.81], [3.72, 3.52], [4.72, 3.22], [5.22, 2.87], [5.72, 2.67]],
};

export const asset = {
  glb: './assets/ships/destroyer.glb', generator: 'tripo3d/h3.1/multiview-to-3d',
  concept: './assets/concepts/destroyer.webp', beauty: './assets/concepts/destroyer-beauty.webp',
  rotate: [0, -90, 0],
  length: 204.2, // 56.0 x 73.4 x 204.2 m -> 840,000 m^3 = 12 slots
  livery: 'dark',
  crease: 35, // chamfered armour blocks and the tower shade flat; bells, pipes and the dome stay smooth
  detail: { set: 'hull', tile: 6, normalStrength: 1.0, roughAmount: 0.5, cavity: 0.4 },
  // The spinal railgun keeps a muted version of the concept's copper coils, rails and conduits
  // instead of the grey repaint, at a little above the hull's value, so it reads as its own
  // machinery: the open gap between the mid hull and the bow block (ray-cast: rails and coil
  // cylinders at x +-5..10, y -30..-17, z +42..+58) and the dorsal rail spine running from the
  // mid hull into the bow block (x +-3.5, y -7..-2.5, z +18..+60). A second box keeps the texture's
  // steel inside the recessed muzzle shroud (the box stops short of the mouth plane so the bow
  // face keeps the livery).
  liveryKeep: [
    { box: [[-12, -31, 42], [12, -3, 58.5]], gain: 0.3, saturation: 0.6, feather: 0.8 },
    { box: [[-3.6, -7.5, 18], [3.6, -2.5, 60]], gain: 0.3, saturation: 0.6, feather: 0.5 },
    { box: [[-9.2, -24.8, 90.5], [9.2, -12.8, 101.6]], gain: 0.55, saturation: 0.2, feather: 0.3 },
  ],
  // Muzzle rim: a dim, cool field-coil band just inside the lip of the octagonal shroud (one strip
  // per face, 0.9 m inside the mouth, ray-cast: side faces x +-9.30, top y -12.61, bottom y -24.77,
  // short chamfers at the corners), so the gun's mouth reads as an octagon even when the bow face
  // is in shadow. Radiance 0.07: a faint glint in the shadow, not a lamp.
  fixtures: [
    { ...MUZZLE_RIM, p: [9.24, -18.8, 101.0], size: [6.4, 0.04, 0.12], rotZ: 1.5708 },
    { ...MUZZLE_RIM, p: [7.66, -13.8, 101.0], size: [3.0, 0.04, 0.12], rotZ: -0.62 },
    { ...MUZZLE_RIM, p: [0, -12.67, 101.0], size: [11.0, 0.04, 0.12], rotZ: 3.1416 },
    { ...MUZZLE_RIM, p: [-7.66, -13.8, 101.0], size: [3.0, 0.04, 0.12], rotZ: 0.62 },
    { ...MUZZLE_RIM, p: [-9.24, -18.8, 101.0], size: [6.4, 0.04, 0.12], rotZ: -1.5708 },
    { ...MUZZLE_RIM, p: [-7.57, -23.55, 101.0], size: [3.0, 0.04, 0.12], rotZ: -0.61 },
    { ...MUZZLE_RIM, p: [0, -24.71, 101.0], size: [10.6, 0.04, 0.12], rotZ: 0 },
    { ...MUZZLE_RIM, p: [7.57, -23.55, 101.0], size: [3.0, 0.04, 0.12], rotZ: 0.61 },
  ],
  engines: [
    // corner bells, upper and lower pair; exit plane at the lip's aft face (z -101.07)
    { p: [13.786, -13.22, -101.07], mirrorX: true, ...CORNER_BELL },
    { p: [13.794, -24.99, -101.07], mirrorX: true, ...CORNER_BELL },
    // centre bell, the aftmost lip (z -102.03)
    { p: [0, -19.602, -102.03], radius: 6.2, depth: 12.0, throat: 3.6,
      wall: [[0.7, 6.22], [1.7, 6.15], [2.7, 6.07], [3.7, 5.94], [4.7, 5.72], [5.7, 5.38], [6.7, 5.04],
        [7.7, 4.63], [8.7, 4.37], [9.7, 4.1], [10.7, 4.24], [11.7, 3.96]] },
  ],
  lights: [
    // steady sidelights on the flat flank plate of the engine section (the beam extremity, plate at
    // x = +-27.75), at its forward end so they read from ahead and abeam
    { p: [27.81, -19.5, -36], color: 'red', size: 0.4 },
    { p: [-27.79, -19.5, -36], color: 'green', size: 0.4 },
    // anti-collision strobes, alternating: bridge tower roof ahead of the dome and masts
    // (roof y 25.80) and the keel under the engine section (y -36.37)
    { p: [0, 25.86, -44], color: 'white', size: 0.4, blink: { ...STROBE } },
    { p: [0, -36.43, -50], color: 'white', size: 0.4, blink: { ...STROBE, phase: 0.5 } },
    // steady stern light on the stern plate above the centre bell (plate z -92.02)
    { p: [0, -10, -92.08], color: 'white', size: 0.4 },
  ],
  anchors: {
    railgunMuzzle: { p: [0, -18.35, 98.47], dir: [0, 0, 1], radius: 2.45, mouth: [0, -18.35, 101.9] },
  },
};
