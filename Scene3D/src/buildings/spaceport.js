// SP-3 orbital spaceport (cqs-fleet installation; game BuildingEnum.SPACEPORT): the station that builds the CV-50
// carrier. Approved concept: style-library/styles/cqs-fleet/images/spaceport-r6.jpg (r5 C, offset half-shells, made
// busier: corrections 25, 29-32).
//
// Three sources, assembled at load (corrections 26 and 32: reuse the real models, never redraw them):
//   - the station: assets/buildings/spaceport.glb, built in headless Blender by tools/blender/buildings/spaceport.py
//     (shells, rims, habitat blocks, cranes, manipulator arms, clamp arms, radiator arrays, tugs, the part-built
//     carrier's bare frames, keel and cradles) and tools/blender/assemble.py (kit ports, doors, rails, containers,
//     floodlights, nav-light housings at true size; spec tools/blender/specs/spaceport-v1.json);
//   - the real CV-50 carrier (assets/ships/carrier.glb, the carrier module's own config) clipped at the aft face of
//     its frame ring F4 (carrier z 87.42): the plated bow 40 % of the hull; aft of it the station's bare frames;
//   - four real CT-4 freighters (assets/ships/freighter.glb, 134.1 m = 0.149 of the carrier) on the clamp arms,
//     drives cold.
// Frames: station frame = asset frame (metres, forward +Z, up +Y, left +X; the open slot faces +X). The GLB is
// authored in the station frame (spaceport_dims.py, origin on the shells' axis at the carrier's mid-length) and is
// centred on its bbox by glbship like every asset; DOCK below is in the station frame and shifted the same way.
// Light paint (correction 27): the station keeps its authored paint (an identity livery, so only real kit glass
// glows); the carrier under construction wears the bone scheme (concept off-white on its armour zones), the docked
// freighters their civil livery. Effects (lightscape pins and slits, nav lights) of all three are merged into one
// userData.ship record, so attachEffects() draws them in one pass.
import * as THREE from 'three';
import { loadGLB, buildGLBShip } from '../lib/glbship.js';
import * as CARRIER from '../ships/carrier.js';
import * as FREIGHTER from '../ships/freighter.js';

export const meta = {
  name: 'SP-3 orbital spaceport',
  designation: 'SP-3',
  crew: 'about 6,000 yard crew in the rim habitats',
  blurb: 'Orbital shipyard that builds the warp-capable units: two thin offset half-shells round the build berth, a trough under the hull and a hood over its stern, with habitat blocks, cranes and manipulator arms along the pale rims; supply freighters dock on short clamp arms. In the berth: a CV-50 carrier with its bow plated and the rest still bare frames on the keel.',
};
export const building = true;
export const gameId = 'SPACEPORT';

// spaceport_dims.py, station frame (metres)
export const DOCK = {
  carrier: { p: [0, 61, 0], cutZ: 87.42 },  // CARRIER_AT, CV_CUT_Z (carrier frame z of the F4 aft face)
  freighters: [
    { name: 'near_fwd', p: [218, -45, 250], yaw: 0 },
    { name: 'near_aft', p: [218, -45, -230], yaw: 180 },
    { name: 'far_mid', p: [-218, -40, 165], yaw: 0 },
    { name: 'hood_top', p: [0, 233, -400], yaw: 180 },
  ],
};

const STROBE = { period: 1.6, duty: 0.1 };
// station-frame lamp positions (spaceport_dims RIM / ARCH): rim joints, arch outer corners
const RIM_JOINTS = [[172.3, 4.06, -419.58], [172.3, 4.06, -360.75], [172.3, 4.06, -301.93], [172.3, 4.06, -243.11], [172.3, 4.06, -184.28], [172.3, 4.06, -125.46], [172.3, 4.06, -66.64], [172.3, 4.06, -7.81], [172.3, 4.06, 51.01], [172.3, 4.06, 109.84], [172.3, 4.06, 168.66], [172.3, 4.06, 227.48], [172.3, 4.06, 286.31], [172.3, 4.06, 345.13], [172.3, 4.06, 403.95], [172.3, 4.06, 462.78], [-172.3, 79.56, 51.01], [-172.3, 79.56, 109.84], [-172.3, 79.56, 168.66], [-172.3, 79.56, 227.48], [-172.3, 79.56, 286.31], [-172.3, 79.56, 345.13], [-172.3, 79.56, 403.95], [-172.3, 79.56, 462.78], [151.87, 121.5, -498.4], [151.87, 121.5, -438.4], [151.87, 121.5, -378.4], [151.87, 121.5, -318.4], [151.87, 121.5, -258.4], [151.87, 121.5, -198.4], [151.87, 121.5, -138.4], [151.87, 121.5, -78.4], [151.87, 121.5, -18.4], [-193.3, -76.49, -498.4], [-193.3, -76.49, -438.4], [-193.3, -76.49, -378.4], [-193.3, -76.49, -318.4], [-193.3, -76.49, -258.4], [-193.3, -76.49, -198.4], [-193.3, -76.49, -138.4], [-193.3, -76.49, -78.4], [-193.3, -76.49, -18.4]];
const ARCH_CORNERS = [[-183.6, -76.05, -487.06], [-76.05, -183.6, -487.06], [76.05, -183.6, -487.06], [183.6, -76.05, -487.06], [-183.6, -76.05, 527.06], [-76.05, -183.6, 527.06], [76.05, -183.6, 527.06], [183.6, -76.05, 527.06], [84.75, 204.6, -567.06], [-84.75, 204.6, -567.06], [-204.6, 84.75, -567.06], [84.75, 204.6, 47.06], [-84.75, 204.6, 47.06], [-204.6, 84.75, 47.06]];
// bbox centre of spaceport.glb in the station frame (assemble report: bbox -208.70..272.45, -188.69..257.13,
// -567.10..564.22): glbship centres the model on it, so every authored station-frame position is shifted by minus this
export const CENTRE = [31.875, 34.22, -1.44];
// authored paint, unchanged (gain 1, no tint, markings at full saturation); kit ports glow as lit cabins (civil share)
const STATION_LIVERY = {
  base: 0.0, gain: 1.0, tint: '#ffffff', mark: 1.0, markSat: 1.0, cyanSat: 1.0, copperSat: 1.0, sat0: 0.22, sat1: 0.5, matte: 0.1, metal: 0.7,
  glassGlow: [0.52, 0.42, 0.28], glassLit: 0.55, glassFlicker: 0.1, glassCell: [3, 3, 7.5], glassParts: ['port'],
};

export const station = {
  glb: './assets/buildings/spaceport.glb',
  generator: 'tools/blender/buildings/spaceport.py + tools/blender/assemble.py (spec tools/blender/specs/spaceport-v1.json)',
  gameId,
  rotate: [0, 0, 0], hullNodes: ['hull'],
  length: 1131.322,   // station bbox z (-567.1 .. 564.2): tugs off the bow to the hood's aft arch
  livery: STATION_LIVERY,
  detail: { set: 'hull', tile: 6, normalStrength: 0.6, roughAmount: 0.5, cavity: 0.2 },
  // nav path (STANDARD R10): red obstruction lights at the extremities (the kit nav-light housings: rim ends, hood
  // arches, mast tops), white strobes on the two masts
  lights: [
    { p: [178, 4.4, 524.2], color: 'red', size: 0.4 },
    { p: [178, 4.4, -484.2], color: 'red', size: 0.4 },
    { p: [-178, 79.9, 524.2], color: 'red', size: 0.4 },
    { p: [0, 206.4, -562.2], color: 'red', size: 0.4 },
    { p: [0, 206.4, 42.2], color: 'red', size: 0.4 },
    { p: [-178, 135.5, 505], color: 'white', size: 0.4, blink: { ...STROBE } },
    { p: [-40, 257.0, -500], color: 'white', size: 0.4, blink: { ...STROBE, phase: 0.5 } },
  ],
  lightscape: {
    seed: 73,
    // block and rim corners: amber pins, a few white work lamps; no dotted chains (one light per corner)
    creases: { angle: 35, minLen: 6, pitch: 18, share: 0.14, run: [1, 2], runPitch: 1.8, corners: 0.5, spacing: 6, size: [0.24, 0.3], intensity: [0.8, 1.1], mix: { amber: 0.8, white: 0.2 }, max: 520, blinkShare: 0.02 },
    slits: { angle: 35, minLen: 3, share: 0.25, every: 24, len: [1.2, 2.2], width: 0.26, radiance: [1.0, 1.5], spacing: 14, max: 110, mix: { amber: 1 },
      corner: { share: 0.4, len: [1.2, 2.0], width: 0.26, radiance: [1.2, 1.6], inset: 0.8, spacing: 12, max: 60 } },
    zones: [
      // radiator / solar arrays: no lamps on fins or panels (rule: never on grilles, louvres or radiators)
      { box: [[100, -280, -470], [270, -100, 510]], creases: null, slits: null },
      { box: [[-270, -280, -370], [-100, -100, 460]], creases: null, slits: null },
      // the seam grooves of the plating are not block corners: no pins on the open shell faces
      { box: [[-215, -215, -575], [215, 215, 575]], creases: { share: 0.05, corners: 0.6 } },
    ],
    patterns: [
      // signature bars at the rim ends (the pale rims' mouths), amber, on the end faces of the trough and hood rims
      { slitRow: [[178, -3, 527.2], [178, 1, 527.2]], pitch: 4, len: 2.0, width: 0.3, u: [1, 0, 0], n: [0, 0, 1], color: 'amber', radiance: 1.8, keep: true },
      { slitRow: [[-178, 70, 527.2], [-178, 76, 527.2]], pitch: 6, len: 2.0, width: 0.3, u: [1, 0, 0], n: [0, 0, 1], color: 'amber', radiance: 1.8, keep: true },
      // amber lamps at the rim segment joints (one per joint, on the rim top at its bay-side edge: the concept's dotted
      // pale rims) and at the end arches' outer corners (spaceport_dims: RIM, ARCH; computed in spaceport_spec notes)
      { points: RIM_JOINTS, color: 'amber', size: 0.3, intensity: 1.0, keep: true },
      { points: ARCH_CORNERS, color: 'amber', size: 0.3, intensity: 1.0, keep: true },
      // slow amber beacons on the hood's arch crowns and the control block
      { points: [[0, 214, 47.5], [0, 214, -567.5], [0, 236.5, -200]], color: 'amber', size: 0.3, intensity: 1.0, pulse: 3.5, keep: true },
    ],
  },
};

// ------------------------------------------------------------------------------------------------
const toRad = THREE.MathUtils.degToRad;

/** The station config in the centred model frame: lights, lightscape patterns and zones shifted by -CENTRE. */
function centred(cfg, c = CENTRE) {
  const sh = (p) => [p[0] - c[0], p[1] - c[1], p[2] - c[2]];
  const ls = cfg.lightscape;
  return {
    ...cfg,
    lights: cfg.lights.map((l) => ({ ...l, p: sh(l.p) })),
    lightscape: {
      ...ls,
      zones: ls.zones.map((z) => ({ ...z, box: z.box.map(sh) })),
      patterns: ls.patterns.map((q) => ({
        ...q,
        ...(q.points ? { points: q.points.map(sh) } : {}),
        ...(q.slitRow ? { slitRow: q.slitRow.map(sh) } : {}),
        ...(q.row ? { row: q.row.map(sh) } : {}),
      })),
    },
  };
}

// buildGLBShip needs the parsed glTFs synchronously: preload() fills this cache
const SYNC = {};
/** Preload the station and the two reused ship GLBs (index.js calls it before build). */
export async function preload() {
  await Promise.all([station.glb, CARRIER.asset.glb, FREIGHTER.asset.glb].map(async (url) => { SYNC[url] = await loadGLB(url); }));
}

/** Read any (possibly quantised / normalised) attribute as float components. */
function readAttr(attr) {
  const n = attr.count, k = attr.itemSize, out = new Float32Array(n * k);
  for (let i = 0; i < n; i++) for (let c = 0; c < k; c++) out[i * k + c] = attr.getComponent(i, c);
  return out;
}

/**
 * Clip a mesh geometry to the half-space f(p) >= 0, where f is linear in local position: f = dot(w, p) + w0.
 * Triangles are split along the plane (Sutherland-Hodgman per triangle, every attribute interpolated), so the
 * cut is a straight line, not a ragged triangle edge. Returns a new non-indexed geometry (or null if empty).
 */
export function clipGeometry(geom, w, w0) {
  const g = geom.index ? geom.toNonIndexed() : geom;
  const names = Object.keys(g.attributes);
  const src = {}, size = {};
  for (const nm of names) { src[nm] = readAttr(g.attributes[nm]); size[nm] = g.attributes[nm].itemSize; }
  const P = src.position;
  const out = Object.fromEntries(names.map((nm) => [nm, []]));
  const f = (i) => w.x * P[i * 3] + w.y * P[i * 3 + 1] + w.z * P[i * 3 + 2] + w0;
  const tri = g.attributes.position.count / 3;
  const vert = (i) => ({ i, t: null });
  const emit = (v) => {
    for (const nm of names) {
      const k = size[nm], a = src[nm];
      if (v.t === null) for (let c = 0; c < k; c++) out[nm].push(a[v.i * k + c]);
      else for (let c = 0; c < k; c++) out[nm].push(a[v.a * k + c] + (a[v.b * k + c] - a[v.a * k + c]) * v.t);
    }
  };
  for (let t = 0; t < tri; t++) {
    const ids = [t * 3, t * 3 + 1, t * 3 + 2];
    const d = ids.map(f);
    if (d[0] >= 0 && d[1] >= 0 && d[2] >= 0) { ids.forEach((i) => emit(vert(i))); continue; }
    if (d[0] < 0 && d[1] < 0 && d[2] < 0) continue;
    const poly = [];
    for (let e = 0; e < 3; e++) {
      const a = ids[e], b = ids[(e + 1) % 3], da = d[e], db = d[(e + 1) % 3];
      if (da >= 0) poly.push(vert(a));
      if ((da >= 0) !== (db >= 0)) poly.push({ a, b, t: da / (da - db) });
    }
    for (let k = 1; k + 1 < poly.length; k++) { emit(poly[0]); emit(poly[k]); emit(poly[k + 1]); }
  }
  if (!out.position.length) return null;
  const res = new THREE.BufferGeometry();
  for (const nm of names) res.setAttribute(nm, new THREE.Float32BufferAttribute(out[nm], size[nm]));
  return res;
}

/** Cut a built carrier group (buildGLBShip) back to its build state: keep design z >= cutZ. */
function cutCarrier(group, cutZ) {
  const model = group.children.find((c) => c.isObject3D && !c.name.startsWith('nozzle') && c.type !== 'SpotLight' && c.type !== 'PointLight');
  const toDesign = model ? model.position.z : 0; // group z = design z - c.z (model.position = -c)
  const zCut = cutZ + toDesign;                   // in the group frame
  group.updateMatrixWorld(true);
  const inv = new THREE.Matrix4().copy(group.matrixWorld).invert();
  const drop = [];
  group.traverse((o) => {
    if (!o.isMesh) return;
    if (o.name === 'nozzle-glow' || o.name === 'nozzle-lining') { drop.push(o); return; }
    // z in the group frame as a linear function of local position: row 2 of (inv(group) * mesh.matrixWorld)
    const m = new THREE.Matrix4().multiplyMatrices(inv, o.matrixWorld).elements;
    const w = new THREE.Vector3(m[2], m[6], m[10]);
    const g = clipGeometry(o.geometry, w, m[14] - zCut);
    if (!g) drop.push(o);
    else { g.computeBoundingBox(); g.computeBoundingSphere(); o.geometry = g; }
  });
  for (const o of drop) o.parent.remove(o);
  // interior floodlights aft of the cut go dark with their hangar
  for (const o of [...group.children]) if ((o.isSpotLight || o.isPointLight) && o.position.z < zCut) group.remove(o);
  const s = group.userData.ship;
  const keep = (p) => p.z >= zCut + 1.0;
  group.userData.ship = { ...s, engines: [], lights: s.lights.filter((l) => keep(l.p)), pins: s.pins.filter((l) => keep(l.p)), slits: s.slits.filter((l) => keep(l.p)),
    interiorLights: (s.interiorLights || []).filter((l) => keep(l.p)) };
  return group;
}

/** Copy a child's effect records (pins, slits, nav lights) into the parent frame through the child's matrix. */
function liftEffects(child, into) {
  child.updateMatrix();
  const M = child.matrix, R = new THREE.Matrix3().setFromMatrix4(M);
  const s = child.userData.ship;
  const P = (v) => v.clone().applyMatrix4(M), D = (v) => (v ? v.clone().applyMatrix3(R).normalize() : v);
  into.pins.push(...s.pins.map((l) => ({ ...l, p: P(l.p), n: D(l.n) })));
  into.slits.push(...s.slits.map((l) => ({ ...l, p: P(l.p), u: D(l.u), n: D(l.n) })));
  into.lights.push(...s.lights.map((l) => ({ ...l, p: P(l.p) })));
}

/**
 * Build the spaceport: the station (buildGLBShip on spaceport.glb), the part-built carrier and the docked freighters,
 * as one group with one merged userData.ship. opts: { library, livery } from the ship context (index.js passes it).
 */
export function build(palette, opts = {}) {
  const library = opts.library || {};
  if (!SYNC[station.glb]) throw new Error('spaceport: call preload() before build()');
  const group = buildGLBShip(SYNC[station.glb], { name: 'spaceport', ...centred(station) }, { palette, library });
  const ship = group.userData.ship;
  const model = group.children[0];
  const offset = model.position.clone();   // station frame -> group frame (bbox centring)
  if (offset.distanceTo(new THREE.Vector3(...CENTRE).negate()) > 0.5) console.warn('[spaceport] GLB bbox centre moved: update CENTRE', offset.toArray());
  const at = (p) => new THREE.Vector3(...p).add(offset);

  // the CV-50 under construction: bone scheme (light primer on its armour zones), cut back at F4
  const cv = buildGLBShip(SYNC[CARRIER.asset.glb], { name: 'carrier', ...CARRIER.asset, liveryScheme: 'bone', lightscape: CARRIER.asset.lightscape }, { palette, library });
  cutCarrier(cv, DOCK.carrier.cutZ);
  cv.position.copy(at(DOCK.carrier.p));
  cv.name = 'spaceport-carrier';
  group.add(cv);
  const fr = [];
  for (const f of DOCK.freighters) {
    const g = buildGLBShip(SYNC[FREIGHTER.asset.glb], { name: 'freighter', ...FREIGHTER.asset }, { palette, library });
    for (const c of [...g.children]) if (c.name === 'nozzle-glow' || c.name === 'nozzle-lining') g.remove(c); // docked: drives cold
    g.userData.ship = { ...g.userData.ship, engines: [] };
    g.position.copy(at(f.p));
    g.rotation.set(0, toRad(f.yaw), 0);
    g.name = `spaceport-freighter-${f.name}`;
    group.add(g);
    fr.push(g);
  }
  // one effects record for the whole installation
  const merged = { pins: [...ship.pins], slits: [...ship.slits], lights: [...ship.lights] };
  for (const g of [cv, ...fr]) liftEffects(g, merged);
  group.userData.ship = {
    ...ship, ...merged, engines: [],
    source: { ...ship.source, gameId, concept: './assets/concepts/spaceport.webp' },
    building: true,
    parts: { carrier: cv, freighters: fr },
    dock: DOCK,
    triangles: ship.triangles + cv.userData.ship.triangles + fr.reduce((n, g) => n + g.userData.ship.triangles, 0),
  };
  return group;
}
