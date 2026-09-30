// Corvette K-214 — v3 REMODEL: clean hard-surface hull (tools/blender/hulls/corvette.py) rebuilt from
// measurements of the v7 fal / Tripo blueprint, textured in texture space (tools/blender/hulls/paint.py:
// light paint, plating seams and tone, PATINA plate tone, AO grime, edge wear, decals) and assembled with
// the Blender parts kit (tools/blender/specs/corvette-v3.json via tools/blender/assemble.py).
// The GLB is already in the ship frame (metres, bow +Z, dorsal +Y, port +X): rotate [0, 0, 0], length =
// the assembled bbox length. Node 'hull' is the hull, 'parts_*' the kit parts (hullNodes).
// Engines: kit bells (bell-L x1.463 centre, bell-M x1.114 / x1.064 upper / lower pairs, bell-L on each pod)
// with the kit's documented engine entry (depth to the throat plate, throat, inner wall) times that scale.
// Lights: at the lenses of the kit nav-light housings.
// Assembled envelope 69.46 x 46.71 x 108.13 m (bbox centre [0.0, -0.025, -0.014] in the model frame; every
// coordinate below is shifted by minus that centre, as glbship.js centres the GLB).
export const meta = {
  "name": "Warden-class corvette",
  "designation": "K-214",
  "crew": "about 350",
  "blurb": "Armoured escort corvette: a chamfered bow with four torpedo doors, a bridge house and a two-tier bridge tower, two twin-barrel dorsal gun mounts and a sensor mast, five fusion bells in the stern frame and two outrigger drive pods on pylons."
};

export const asset = {
  glb: "./assets/ships/corvette.glb",
  generator: "tools/blender/hulls/corvette.py (remodel of the tripo3d/h3.1/multiview-to-3d v7 hull) + tools/blender/assemble.py",
  concept: "./assets/concepts/corvette.webp",
  beauty: "./assets/concepts/corvette-beauty.webp",
  rotate: [0, 0, 0],
  hullNodes: ["hull"],
  // remodel paint is lighter than the generated textures: gain 0.05 matches the fleet grey. v11: lit cabins behind the
  // ports and bridge panes (warm, varied per compartment, a few dark, a few flickering).
  // v14 scale pass (fleet lighting standard): a warship's lit share (0.45, flicker 0.08); only the kit ports and panes
  // glow (glassParts: the turret sights and hull stencils stay dark, no cabin window on a gun); compartment grid 5.1 m
  // with phase 0.54 so no cell edge crosses a 1 m port (the old grid split 40 of 86 into two-tone half windows, which
  // read half size and made the flank read bigger); the bridge glazing band and the tower glazing are each one steady,
  // dim compartment (a bridge runs dark: gain 0.3 displays at about 0.65x the lit cabin ports after tone mapping, L 103
  // against 158; at 0.5 every pane showed at 0.85x and the band read as a lit promenade, the widest and brightest glass
  // on the ship where the fewest people are)
  livery: {
    gain: 0.05, glassGlow: [0.52, 0.42, 0.28], glassLit: 0.45, glassFlicker: 0.08, glassCell: 5.1, glassPhase: 0.54,
    glassParts: ['port', 'pane'],
    glassZones: [
      { box: [[-10.5, 0.2, 10.5], [10.5, 2.7, 25.5]], gain: 0.3, uniform: true },  // bridge glazing band
      { box: [[-8, 10.5, -18], [8, 12.5, -3]], gain: 0.3, uniform: true },         // tower glazing
    ],
  },
  // v11 lightscape (src/lib/lightscape.js); v12: the hierarchy turned round to the concept's: a few short amber bars in
  // real recesses and at block corners (door jambs, the bow torpedo frame, the pod radiator bay, the flank's forward
  // corner, vent floors, the deckhouse base) carry the look; crease pins are sparse background texture (no white pins
  // on the key-lit top, none on louvres or glazing).
  // v14 scale pass: lamps are fleet-size fixtures (pins 0.2-0.3 m, bars 0.14-0.2 m wide) and only where a fixture has a
  // job (door, block corner, torpedo and stern frames, drive status, deck edge, mast); no row runs beside or at the pitch
  // of the 2.5 m port grid (a dotted row there reads as another deck of windows); warm is an interior colour, so the
  // exterior is amber with a little white; the uncrewed drive pods are dark machinery with corner lamps only
  lightscape: {
    seed: 21,
    creases: { angle: 35, minLen: 3, pitch: 6, share: 0.2, run: [1, 2], runPitch: 1.1, corners: 0.3, spacing: 2.0, size: [0.2, 0.25], intensity: [0.45, 0.75], mix: { amber: 0.85, white: 0.15 }, max: 40, blinkShare: 0.03 },
    slits: { angle: 35, minLen: 1.5, share: 0.65, every: 8, len: [0.7, 1.2], width: 0.2, radiance: [1.0, 1.4], spacing: 4, max: 30, mix: { amber: 1 }, corner: { radiance: [1.1, 1.5], len: [0.8, 1.2], width: 0.2 } },
    cool: { radius: 1.8, depth: 2.5 },
    // first matching box wins (ship frame; mirrorX adds the starboard twin)
    zones: [
      // pod radiator bay (0.45 m recess x 34.0..34.45, y -17.05..-12.85, z -22.6..-9.4, fins at 0.3 m): no confetti in the fins
      { box: [[33.4, -17.6, -23.1], [35.3, -12.3, -8.9]], mirrorX: true, creases: null, slits: null },
      // v14: the rest of each drive pod (uncrewed machinery, 10 x 10.5 x 29 m): no automatic pins; the authored corner
      // lamps, bay bars, status bar and sidelight mark it. A fine scatter here read as portholes on a crewed module and
      // made the pod, and so the ship, read bigger
      { box: [[24.2, -20.8, -29.2], [35.0, -9.1, -0.3]], mirrorX: true, creases: null },
      // v14: stern frame side walls: the authored and corner bars mark the frame; crease pins stacked a column of dots
      // up the wall between them
      { box: [[12.0, -18.0, -50.2], [16.0, -1.5, -48.8]], mirrorX: true, creases: null },
      // shoulder vent bays (0.3 m recesses with slanted louvres) and the ribbed launcher tubes
      { box: [[12.5, -5.2, 5.6], [17.2, -0.6, 17.4]], mirrorX: true, creases: null, slits: null },
      { box: [[12.2, -5.2, -47.0], [16.9, -0.6, -39.8]], mirrorX: true, creases: null, slits: null },
      { box: [[12.5, -5.0, -38.2], [17.5, -0.6, -28.2]], mirrorX: true, creases: null },
      // bridge glazing band: the lit panes carry it
      { box: [[-10.5, 0.2, 10.5], [10.5, 2.7, 25.5]], creases: null, slits: null },
      // bow torpedo frame (lip z 54.05, plate 52.75): authored corner bars instead of the pin necklace
      { box: [[-9.6, -20.0, 52.2], [9.6, -4.0, 54.7]], creases: null, slits: null },
      // tapered bow flank: the belt thins to 0.01 m forward of z 21, so its top line is flat plating (no painted-on bars)
      { box: [[7.5, -12.4, 21.0], [16.0, -10.6, 54.0]], mirrorX: true, slits: null },
      // bow cap: only a few block corners
      { box: [[-20.0, -25.0, 41.5], [20.0, -1.0, 52.2]], creases: { share: 0.08, run: [1, 1], corners: 0.25 } },
      // v14: clear of the flank port grid (frames x 15.6..16.5, y -10.5..-6.1, z 0.3..19.2 and -43.4..-27.1) up to the
      // shoulder crease (y -4.4): pins on the belt top 1 m under the lower ports and a run along the shoulder crease
      // 2.4 m over the upper ports lined up as two more decks of windows, and a bar on the aft door head read as a lit
      // transom
      { box: [[15.2, -12.3, -44.9], [17.2, -3.8, 20.7]], mirrorX: true, creases: null, slits: null },
      // armour belt ledge (0.22 m proud): too shallow to read as a recess, so only the odd bar
      { box: [[15.9, -12.2, -49.5], [16.9, -10.9, 21.0]], mirrorX: true, slits: { share: 0.15 } },
      // v14: bridge tower and mast above the deckhouse: a mast carries a few lamps (sensor-block top, yardarm tips), not
      // the glitter of every rail corner, which made the 13 m tower read as a much wider block. No automatic bar here:
      // every one landed on a glazing sill or lintel, and the platform-corner pins sat at the corners of the lit band;
      // both read as more windows (exclude: 1.5 m round the panes, x +-6.9, y 10.9..12.1, z -14.6..-4.8)
      { box: [[-8, 10, -18], [8, 30, -3]], creases: { share: 0, corners: 0.15, exclude: [{ box: [[-8.5, 9.4, -16.2], [8.5, 13.7, -3.2]] }] }, slits: null },
      // key-lit top (deck, walkways, deckhouse, tower): sparse, the studio key washes pins there
      { box: [[-20.0, -2.0, -50.0], [20.0, 30.0, 50.0]], creases: { share: 0.12, corners: 0.2 } },
    ],
    patterns: [
      // (v14: the tower glazing sill row, 11 pins at 0.86 m under 9 panes at 1.12 m, is gone: twice the real window
      // frequency made the bridge read twice as wide. The dim tower panes carry the tower.)
      // armour belt: sparse amber marks on its lower edge (y about -16.5), well clear of the port grid; v14: moved off
      // the belt top and the shoulder row dropped, since specks 1.8 m from the port rows read as two more window decks
      { surface: 'belt-port', edge: 'bottom', inset: 0.3, pitch: 10, color: 'amber', size: 0.22, intensity: 0.8, skip: 0.45, mirrorX: true },
      // deckhouse base / walkway junction (concave corner at x 10.37, y -1.44): short amber bars
      { slitRow: [[10.43, -1.34, -27.0], [10.43, -1.34, 3.0]], pitch: 7.5, u: [0, 0, 1], n: [0.52, 0.85, 0], len: 1.1, width: 0.2, radiance: 1.5, color: 'amber', skip: 0.3, mirrorX: true },
      // crew-door bays (z 1.5 / 9.9 / -39.5, recess y -15.2..-12.2): short lamps at the head and foot of the aft jamb
      // wall (faces forward), inside the recess: the human ruler beside a 1 x 2 m door
      { slit: [16.285, -12.75, 0.555], u: [0, 1, 0], n: [0, 0, 1], len: 0.6, width: 0.14, radiance: 1.5, color: 'amber', mirrorX: true },
      { slit: [16.285, -14.65, 0.555], u: [0, 1, 0], n: [0, 0, 1], len: 0.5, width: 0.14, radiance: 1.2, color: 'amber', mirrorX: true },
      { slit: [16.285, -12.75, 8.955], u: [0, 1, 0], n: [0, 0, 1], len: 0.6, width: 0.14, radiance: 1.5, color: 'amber', mirrorX: true },
      { slit: [15.81, -12.75, -40.445], u: [0, 1, 0], n: [0, 0, 1], len: 0.6, width: 0.14, radiance: 1.5, color: 'amber', mirrorX: true },
      { slit: [15.81, -14.65, -40.445], u: [0, 1, 0], n: [0, 0, 1], len: 0.5, width: 0.14, radiance: 1.2, color: 'amber', mirrorX: true },
      // forward flank: a corner bar at the foot of the flank block's forward corner, on the bow taper 2 m forward of the
      // flat flank's edge (z 19.2) and 2.3 m clear of the port grid (v14: the bars beside and above the first port
      // column are gone: a lamp at a window reads as a door-jamb lamp or a lit transom, a human-scale cue that doubles
      // the window count), and one at the foot of the tapered bow flank by the torpedo frame lip (z 54.05)
      { slit: [15.67, -12.0, 21.18], u: [0, 1, 0], n: [0.974, 0, 0.225], len: 0.8, width: 0.17, radiance: 1.3, color: 'amber', mirrorX: true },
      { slit: [8.47, -12.9, 52.9], u: [0, 1, 0], n: [0.975, 0, 0.222], len: 1.0, width: 0.17, radiance: 1.4, color: 'amber', keep: true, mirrorX: true },
      // pod radiator bay: short corner bars in the open slots between the end walls and the first / last fin (in the
      // face plane, x 34.4: the fins hide anything deeper at oblique views). v14: the warm sill and amber head rows are
      // gone (a lamp rim round the bay read as a lit hangar mouth on an uncrewed pod)
      { slit: [34.4, -13.6, -9.56], u: [0, 1, 0], n: [1, 0, 0], len: 0.8, width: 0.17, radiance: 1.5, color: 'amber', keep: true, mirrorX: true },
      { slit: [34.4, -16.3, -22.49], u: [0, 1, 0], n: [1, 0, 0], len: 0.8, width: 0.17, radiance: 1.4, color: 'amber', keep: true, mirrorX: true },
      // pod extremities: fleet-size lamps (0.3 m) at the outboard face corners (fore steady, aft slow pulse)
      { points: [[34.56, -11.45, -2.4], [34.56, -18.45, -2.4]], color: 'amber', size: 0.3, intensity: 1.5, keep: true, mirrorX: true },
      { points: [[34.56, -11.45, -26.3], [34.56, -18.45, -26.3]], color: 'amber', size: 0.3, intensity: 1.5, pulse: 4.2, mirrorX: true },
      // drive pods: one cool drive-status bar on the flat outboard face between the radiator bay and the strap at z -5
      // (0.12 m proud), above the sidelight (2.5 m clear). v14: it replaces a cool row at 1.4 m and an amber row at
      // 1.8 m, which read as rows of portholes where no crew can be
      { slit: [34.47, -12.4, -6.2], u: [0, 0, 1], n: [1, 0, 0], len: 0.8, width: 0.15, radiance: 1.1, color: 'cool', mirrorX: true },
      // bow torpedo frame: upright bars on the inner side walls (x 7.6, facing in), one under the deck lintel, lamps at the lip's shoulder corners
      { slit: [7.57, -9.6, 53.4], u: [0, 1, 0], n: [-1, 0, 0], len: 1.0, width: 0.19, radiance: 1.6, color: 'amber', keep: true, mirrorX: true },
      { slit: [7.57, -13.8, 53.4], u: [0, 1, 0], n: [-1, 0, 0], len: 1.0, width: 0.19, radiance: 1.6, color: 'amber', keep: true, mirrorX: true },
      { slit: [3.2, -5.76, 53.4], u: [1, 0, 0], n: [0, -1, 0], len: 1.0, width: 0.17, radiance: 1.4, color: 'amber', mirrorX: true },
      { points: [[8.25, -8.4, 54.16]], color: 'amber', size: 0.3, intensity: 1.1, keep: true, mirrorX: true },
      // stern frame (0.3 m inner wall, lip z -49.53, plate -49.24): short bars either side of the drive chaser
      { slit: [14.68, -6.6, -49.39], u: [0, 1, 0], n: [-1, 0, 0], len: 1.0, width: 0.17, radiance: 1.4, color: 'amber', mirrorX: true },
      { slit: [14.895, -14.0, -49.39], u: [0, 1, 0], n: [-1, 0, 0], len: 1.0, width: 0.17, radiance: 1.4, color: 'amber', mirrorX: true },
      // shoulder vent bays: amber lamps on the recess floor between the slanted louvres (mid-gap, fins at z0 + 0.6 +
      // k 1.15). v14: the fore bays keep only the two end slots, as recess-corner lamps; a lit slot every 1.15 m read as a
      // third deck of letterbox windows at half the port pitch, in a machinery vent with no crew
      { slit: [14.627, -3.147, 7.375], u: [0, 0, 1], n: [0.752, 0.659, 0], len: 0.55, width: 0.14, radiance: 0.9, color: 'amber', mirrorX: true },
      { slit: [14.627, -3.147, 16.575], u: [0, 0, 1], n: [0.752, 0.659, 0], len: 0.55, width: 0.14, radiance: 0.9, color: 'amber', mirrorX: true },
      { slitRow: [[14.18, -3.075, -45.225], [14.18, -3.075, -41.775]], pitch: 1.15, u: [0, 0, 1], n: [0.751, 0.66, 0], len: 0.55, width: 0.14, radiance: 0.9, color: 'amber', skip: 0.4, mirrorX: true },
      // stern plate (x +-4): drive status chaser, a short run each side outboard of the stern light, 2.4 m clear of it
      // (v14: it ran through the light at 0.6 m pitch, 14 lamps in 8 m); the bow deck: two slow beacons
      { row: [[2.4, -2.88, -49.34], [3.6, -2.88, -49.34]], pitch: 1.2, color: 'cool', size: 0.2, intensity: 0.85, chase: 2.6, mirrorX: true },
      { surface: 'bow-deck', edge: 'left', inset: 0.5, pitch: 7, color: 'amber', size: 0.3, intensity: 1.0, pulse: 3.4 },
      { surface: 'bow-deck', edge: 'right', inset: 0.5, pitch: 7, color: 'amber', size: 0.3, intensity: 1.0, pulse: 3.4 },
      // bridge tower: a corner bar on each front chamfer (0.8 m plate between the front and side walls, flat y 7.1..10.3),
      // at the block extremity 2.2 m below the tower glass (bottom y 10.93): the command block keeps the concept's amber
      // without a lamp on the glazing sill or lip, where one reads as another window (last in the list, so the pattern
      // seeds above, and with them the aft vent skips and beacon phases, stay as they were)
      { slit: [5.5, 8.3, -6.16], u: [0, 1, 0], n: [0.707, 0, 0.707], len: 0.8, width: 0.17, radiance: 1.3, color: 'amber', mirrorX: true },
    ],
  },
  detail: {"set": "hull", "tile": 6, "normalStrength": 0.6, "roughAmount": 0.5, "cavity": 0.2},
  // Two-tone armour zones (?livery=tone|bone, livery.js SCHEMES; ship frame, metres): the outrigger drive pods, the
  // chamfered bow cap (forward of the deck slope, z 41.5) and the stern block below the main deck (aft of the
  // deckhouse end, z -38.8) take the light paint; the deckhouse, tower, spine and belly stay dark.
  liveryZones: [
    { box: [[24.2, -20.8, -29.2], [35.0, -9.1, -0.3]], mirrorX: true },  // drive pods (POD x 29.55 +- 4.9, y -14.95 +- 5.25)
    { box: [[-20.0, -25.0, 41.5], [20.0, -1.0, 55.0]] },                 // bow cap
    { box: [[-20.0, -25.0, -50.0], [20.0, -1.6, -38.8]] },               // stern block under the deck
  ],
  length: 108.129,
  engines: [
    // centre bell: bell-L x1.463 (r 5.12)
    {p: [0.0, -9.975, -52.586], radius: 5.12, depth: 6.912, throat: 2.56, wall: [[0.987, 5.043], [1.975, 4.851], [2.962, 4.563], [3.95, 4.185], [4.937, 3.723], [5.925, 3.18]]},
    // upper bells: bell-M x1.1136 (r 2.45)
    {p: [9.85, -5.415, -53.686], radius: 2.45, depth: 3.307, throat: 1.225, wall: [[0.472, 2.413], [0.945, 2.322], [1.418, 2.184], [1.89, 2.002], [2.362, 1.782], [2.835, 1.522]]},
    // upper bells: bell-M x1.1136 (r 2.45)
    {p: [-9.85, -5.415, -53.686], radius: 2.45, depth: 3.307, throat: 1.225, wall: [[0.472, 2.413], [0.945, 2.322], [1.418, 2.184], [1.89, 2.002], [2.362, 1.782], [2.835, 1.522]]},
    // lower bells: bell-M x1.0636 (r 2.34)
    {p: [9.8, -14.055, -54.036], radius: 2.34, depth: 3.159, throat: 1.17, wall: [[0.451, 2.305], [0.903, 2.218], [1.354, 2.086], [1.805, 1.912], [2.256, 1.702], [2.708, 1.454]]},
    // lower bells: bell-M x1.0636 (r 2.34)
    {p: [-9.8, -14.055, -54.036], radius: 2.34, depth: 3.159, throat: 1.17, wall: [[0.451, 2.305], [0.903, 2.218], [1.354, 2.086], [1.805, 1.912], [2.256, 1.702], [2.708, 1.454]]},
    // pod bells: bell-L (r 3.5)
    {p: [29.55, -14.925, -34.586], radius: 3.5, depth: 4.725, throat: 1.75, wall: [[0.675, 3.447], [1.35, 3.316], [2.025, 3.119], [2.7, 2.861], [3.375, 2.545], [4.05, 2.174]]},
    // pod bells: bell-L (r 3.5)
    {p: [-29.55, -14.925, -34.586], radius: 3.5, depth: 4.725, throat: 1.75, wall: [[0.675, 3.447], [1.35, 3.316], [2.025, 3.119], [2.7, 2.861], [3.375, 2.545], [4.05, 2.174]]},
  ],
  lights: [
    // v14: every nav light is the fleet's 0.4 m fixture (the kit housing), the same lamp on every hull
    // steady sidelights on the flat outboard face of each pod (the beam extremity): red port, green starboard
    {p: [34.68, -14.925, -6.986], color: "red", size: 0.4},
    {p: [-34.68, -14.925, -6.986], color: "green", size: 0.4},
    // anti-collision strobes, alternating: keel and masthead (top of the sensor block)
    {p: [0.0, -23.305, 0.014], color: "white", size: 0.4, blink: {period: 1.3, duty: 0.1, phase: 0.5}},
    {p: [0.0, 23.325, -11.486], color: "white", size: 0.4, blink: {period: 1.3, duty: 0.1}},
    // steady stern light on the stern plate above the centre bell
    {p: [0.0, -3.075, -49.466], color: "white", size: 0.4},
    // (v10 amber running lights on bare plating removed in v12: the lightscape's recess bars replace them)
  ],
  anchors: {
    // Flat hull faces for the composition step, measured on the remodelled hull by ray casts (0.5 m
    // grid along -normal, plane refit; flat = share of samples within 0.15 m of the plane).
    surfaces: {
      'flank-fore-port': { centre: [16.15, -8.03, 9.51], normal: [1.0, 0.0, 0.0], u: [0.0, 0.0, 1.0], width: 18.0, height: 6.6, flat: 1.0 }, // upper flank between the pylon and the bow taper (two port rows)
      'flank-fore-stbd': { centre: [-16.15, -8.03, 9.51], normal: [-1.0, 0.0, 0.0], u: [0.0, 0.0, -1.0], width: 18.0, height: 6.6, flat: 1.0 },
      'flank-aft-port': { centre: [15.74, -8.03, -35.99], normal: [1.0, 0.0, -0.018], u: [0.018, 0.0, 1.0], width: 17.0, height: 6.6, flat: 1.0 }, // upper flank aft of the pod
      'flank-aft-stbd': { centre: [-15.74, -8.03, -35.99], normal: [-1.0, 0.0, -0.018], u: [0.018, 0.0, -1.0], width: 17.0, height: 6.6, flat: 1.0 },
      'belt-port': { centre: [16.27, -14.28, -11.99], normal: [1.0, -0.025, -0.008], u: [0.008, 0.0, 1.0], width: 56.0, height: 5.0, flat: 0.87 }, // armour belt (0.22 m proud), crew-door bays at z 1.5 / 9.9 / -39.5
      'belt-stbd': { centre: [-16.27, -14.28, -11.99], normal: [-1.0, -0.025, -0.008], u: [0.008, 0.0, -1.0], width: 56.0, height: 5.0, flat: 0.87 },
      'flank-bow-port': { centre: [12.24, -9.97, 35.97], normal: [0.974, 0.025, 0.225], u: [-0.225, 0.0, 0.974], width: 26.0, height: 9.0, flat: 0.85 }, // tapered bow flank; K-214 at z 28-43
      'flank-bow-stbd': { centre: [-12.24, -9.97, 35.97], normal: [-0.974, 0.026, 0.225], u: [-0.225, 0.0, -0.974], width: 26.0, height: 9.0, flat: 0.85 },
      'shoulder-port': { centre: [14.73, -3.04, -11.99], normal: [0.739, 0.673, -0.007], u: [0.005, 0.005, 1.0], width: 30.0, height: 3.0, flat: 1.0 }, // shoulder chamfer from the flank to the walkway, clear stretch z -27..3 (vent bays at z 6-17 and -46..-40, launcher tubes at z -29..-37)
      'shoulder-stbd': { centre: [-14.73, -3.04, -11.99], normal: [-0.739, 0.673, -0.007], u: [0.005, -0.005, -1.0], width: 30.0, height: 3.0, flat: 1.0 },
      'deck-walk-port': { centre: [11.7, -1.44, -5.99], normal: [0.0, 1.0, 0.0], u: [0.0, 0.0, 1.0], width: 44.0, height: 2.0, flat: 1.0 }, // walkway outboard of the deckhouse (deck-edge rails)
      'deck-walk-stbd': { centre: [-11.7, -1.44, -5.99], normal: [0.0, 1.0, 0.0], u: [0.0, 0.0, 1.0], width: 44.0, height: 2.0, flat: 1.0 },
      'deckhouse-side-port': { centre: [9.14, 1.01, -11.99], normal: [0.893, 0.45, -0.001], u: [0.001, 0.0, 1.0], width: 36.0, height: 4.4, flat: 1.0 }, // sloped deckhouse side (ports, ladders)
      'deckhouse-side-stbd': { centre: [-9.14, 1.01, -11.99], normal: [-0.893, 0.449, -0.001], u: [0.001, 0.0, -1.0], width: 36.0, height: 4.4, flat: 1.0 },
      'dorsal-deck': { centre: [0.0, 3.48, 13.01], normal: [0.0, 1.0, -0.003], u: [0.0, 0.003, 1.0], width: 6.0, height: 10.0, flat: 1.0 }, // deckhouse roof between the forward turret and the bridge
      'stern-deck': { centre: [0.0, -1.44, -43.99], normal: [0.0, 1.0, 0.0], u: [0.0, 0.0, 1.0], width: 9.0, height: 20.0, flat: 1.0 }, // main deck aft of the deckhouse
      'bow-deck': { centre: [0.0, -3.37, 39.98], normal: [0.0, 0.989, 0.15], u: [0.0, -0.15, 0.989], width: 12.0, height: 8.0, flat: 1.0 }, // sloping bow deck (hatch plate, vent ramps)
      'bridge-glazing': { centre: [0.0, 1.38, 23.61], normal: [0.0, 0.0, 1.0], u: [1.0, 0.0, 0.0], width: 5.0, height: 1.2, flat: 0.6 }, // bridge glazing recess back wall (vertical, 0.9 m in from the glacis at the band top), kit panes
      'tower-front': { centre: [0.0, 8.18, -5.72], normal: [0.0, 0.0, 1.0], u: [1.0, 0.0, 0.0], width: 9.0, height: 2.2, flat: 1.0 }, // vertical tier of the tower front
      'tower-side-port': { centre: [5.95, 8.18, -10.99], normal: [1.0, 0.0, 0.0], u: [0.0, 0.0, 1.0], width: 8.0, height: 2.2, flat: 1.0 },
      'tower-side-stbd': { centre: [-5.95, 8.18, -10.99], normal: [-1.0, 0.0, 0.0], u: [0.0, 0.0, -1.0], width: 8.0, height: 2.2, flat: 1.0 },
      'tower-glazing': { centre: [0.0, 11.54, -5.34], normal: [0.0, -0.605, 0.796], u: [1.0, 0.0, 0.0], width: 9.0, height: 1.5, flat: 1.0 }, // leaning tower glazing (faces forward and down), recessed 0.3 m
      'stern-plate': { centre: [0.0, -2.88, -49.24], normal: [0.0, 0.0, -1.0], u: [-1.0, 0.0, 0.0], width: 8.0, height: 0.8, flat: 1.0 }, // recessed stern plate strip above the centre bell boss
      'pod-outboard-port': { centre: [34.46, -14.93, -4.99], normal: [1.0, 0.0, -0.001], u: [0.001, 0.0, 1.0], width: 6.0, height: 5.0, flat: 1.0 }, // pod outboard face forward of the radiator bay
      'pod-outboard-stbd': { centre: [-34.46, -14.93, -4.99], normal: [-1.0, 0.0, -0.001], u: [0.001, 0.0, -1.0], width: 6.0, height: 5.0, flat: 1.0 },
    },
  },
};
