// Destroyer DD-12 — generated with fal (Tripo H3.1 multiview, see pipeline/fal-pipeline.json).
// v5 (true-scale details): the approved design was re-detailed with nano-banana-pro/edit (three
// passes) so its small details share the fleet's absolute scale on a 204 m hull: thin rows of ~1 m
// panes, one per deck at ~3 m pitch, on the bridge tower (seven rows), rows of ~0.8 m portholes
// along the flanks, 1 m hand rails on the tower balconies and the rail catwalks, and the exposed
// railgun as long parallel rails with coil rings, cable runs and walkways. A 4K orthographic
// turnaround of it (front / port / stern / starboard) was reconstructed, and the hull number (lost
// in the reconstruction on both flanks) was re-projected onto the texture as a 2.3 m stencil
// "DD-12" reading correctly on each side.
// Anchors were measured on the GLB in the centred ship frame (rotate -> length -> centre),
// metres, bow +Z, dorsal +Y, port +X, fleet scale 1 slot = 70,000 m^3.
// - rotate [0,-90,0] puts the bow block (railgun muzzle) at +Z, the bridge tower up and the port
//   flank at +X (bow on the left seen from +X, as in the turnaround's port view).
// - length 204.21 m gives an envelope of 56.52 x 74.44 x 204.21 m = 859,200 m^3, so the class
//   volume correction for 12 slots is 0.9925 (-0.75 %): 202.7 m as rendered. The beam is set by
//   the flank plates of the engine section (x = +-28.26), the height by the tower's masts
//   (y = +37.22) and the keel fin (y = -37.22).
// - Main drive: five bells in the stern block. Corner bells (x +-13.55, y -13.81 and -25.64,
//   circle fits of the inner wall 4 m in; port and starboard agree to 0.04 m, so one mirrored
//   entry per pair): exit plane at the lip's aft face (z -102.1, the envelope), inner wall r 4.36
//   at the exit narrowing to 3.38 at 5.25 m, then a conical throat plate (7.1 m in on the axis,
//   ~5.9 m at r 2.7); the glow sits 5.6 m in, in front of it. Centre bell: a wide shallow dish
//   whose lip is 10.8 m forward of the corner lips (z -91.3), inner wall r 7.9 at the exit
//   converging to 3.7 at 3.95 m and a flat plate ~4.2-4.9 m in; the glow sits 3.8 m in.
// - Railgun: the bow block's octagonal shroud (mouth lip z +101.3..102.1, 18.6 m wide, 12.0 m
//   high, centre y -18.6) is recessed ~14 m; a barrel boss stands in it and the hexagonal bore
//   (r 2.35-3.3, centre x 0, y -18.5) opens at its face at z +96.0. The muzzle anchor is the
//   centre of that bore opening; `mouth` is the shroud mouth on the same axis.
// - Lights sit ~6 cm proud of the surface they are mounted on.
export const meta = {
  name: 'Bastion-class destroyer', designation: 'DD-12', crew: 'about 2,000',
  blurb: 'Heavy line destroyer built around a massive spinal railgun: an armoured bow block with the recessed muzzle, an exposed rail channel with capacitor banks along the spine, a many-deck bridge tower, heavy naval turrets, radiator panels on the flanks of the engine section and five fusion bells in the stern.',
};

const STROBE = { period: 1.3, duty: 0.1 };
const MUZZLE_RIM = { color: '#b4c2dc', radiance: 0.07 };
// corner bells: glow in front of the throat plate (see above)
const CORNER_BELL = {
  radius: 4.4, depth: 5.6, throat: 2.9,
  wall: [[0.75, 4.25], [1.75, 4.11], [2.75, 3.95], [3.75, 3.72], [4.75, 3.5], [5.25, 3.37]],
};

export const asset = {
  glb: './assets/ships/destroyer.glb', generator: 'tripo3d/h3.1/multiview-to-3d',
  concept: './assets/concepts/destroyer.webp', beauty: './assets/concepts/destroyer-beauty.webp',
  rotate: [0, -90, 0],
  length: 204.21, // 56.5 x 74.4 x 204.2 m -> 859,200 m^3; x 0.9925 for 12 slots (840,000 m^3)
  livery: 'dark',
  crease: 35, // chamfered armour blocks and the tower shade flat; bells, pipes and the dome stay smooth
  detail: { set: 'hull', tile: 6, normalStrength: 1.0, roughAmount: 0.5, cavity: 0.4 },
  // The spinal railgun keeps a muted version of the concept's copper coils, rails and conduits
  // instead of the grey repaint, at a little above the hull's value, so it reads as its own
  // machinery: the open gap between the mid hull and the bow block (ray-cast: rails, coil
  // cylinders and walkways at x +-1..10, y -30..-8, z +43..+57) and the dorsal rail spine running
  // from the mid hull into the bow block (outer rails x +-10, y -6; centre rails y -7; z +20..+62).
  // A third box keeps the texture's steel inside the recessed muzzle shroud (the box stops short
  // of the lip, z +101.3, so the bow face keeps the livery).
  liveryKeep: [
    { box: [[-11, -31, 42.5], [11, -8.5, 57.5]], gain: 0.3, saturation: 0.6, feather: 0.8 },
    { box: [[-11, -7.8, 18], [11, -4.5, 62]], gain: 0.3, saturation: 0.6, feather: 0.5 },
    { box: [[-9.2, -24.6, 88], [9.2, -12.6, 100.8]], gain: 0.55, saturation: 0.2, feather: 0.3 },
  ],
  // Muzzle rim: a dim, cool field-coil band just inside the lip of the octagonal shroud (one strip
  // per face, 0.9 m inside the shallowest lip, ray-cast at z 100.4: side faces x +9.09 / -9.20,
  // top y -12.75, bottom y -24.37, chamfered corners), so the gun's mouth reads as an octagon even
  // when the bow face is in shadow. Radiance 0.07: a faint glint in the shadow, not a lamp.
  fixtures: [
    { ...MUZZLE_RIM, p: [9.06, -18.75, 100.4], size: [6.4, 0.04, 0.12], rotZ: 1.5708 },
    { ...MUZZLE_RIM, p: [7.49, -13.9, 100.4], size: [3.0, 0.04, 0.12], rotZ: -0.64 },
    { ...MUZZLE_RIM, p: [0, -12.78, 100.4], size: [11.4, 0.04, 0.12], rotZ: 3.1416 },
    { ...MUZZLE_RIM, p: [-7.53, -13.9, 100.4], size: [3.0, 0.04, 0.12], rotZ: 0.64 },
    { ...MUZZLE_RIM, p: [-9.17, -18.75, 100.4], size: [6.4, 0.04, 0.12], rotZ: -1.5708 },
    { ...MUZZLE_RIM, p: [-7.25, -23.39, 100.4], size: [3.0, 0.04, 0.12], rotZ: -0.53 },
    { ...MUZZLE_RIM, p: [0, -24.34, 100.4], size: [10.6, 0.04, 0.12], rotZ: 0 },
    { ...MUZZLE_RIM, p: [7.22, -23.38, 100.4], size: [3.0, 0.04, 0.12], rotZ: 0.54 },
  ],
  engines: [
    // corner bells, upper and lower pair; exit plane at the lips' aft face (z -102.1)
    { p: [13.55, -13.81, -102.08], mirrorX: true, ...CORNER_BELL },
    { p: [13.55, -25.64, -102.08], mirrorX: true, ...CORNER_BELL },
    // centre bell: a wide dish whose lip is 10.8 m forward of the corner lips
    { p: [0, -20.09, -91.3], radius: 7.8, depth: 3.8, throat: 3.7,
      wall: [[0.45, 7.26], [0.95, 6.9], [1.45, 6.43], [1.95, 5.95], [2.45, 5.06], [2.95, 4.96], [3.45, 4.72]] },
  ],
  lights: [
    // steady sidelights on the flat flank plate of the engine section (the beam extremity, plate at
    // x = +-27.88 over z -50..-80), at its forward end so they read from ahead and abeam
    { p: [27.94, -19.5, -50], color: 'red', size: 0.4 },
    { p: [-27.96, -19.5, -50], color: 'green', size: 0.4 },
    // anti-collision strobes, alternating: bridge tower roof ahead of the dome and masts
    // (roof y 24.86) and the keel fin under the engine section (y -36.83)
    { p: [0, 24.92, -42], color: 'white', size: 0.4, blink: { ...STROBE } },
    { p: [0, -36.89, -40], color: 'white', size: 0.4, blink: { ...STROBE, phase: 0.5 } },
    // steady stern light on the stern plate above the centre bell (plate z -84.07)
    { p: [0, -8, -84.13], color: 'white', size: 0.4 },
  ],
  anchors: {
    railgunMuzzle: { p: [0, -18.5, 96.0], dir: [0, 0, 1], radius: 2.4, mouth: [0, -18.6, 101.3] },
  },
};
