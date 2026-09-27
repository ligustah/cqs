// Composition of generated hulls with the shared parts kit.
//
// Every small, human-scale component (crew door, airlock, window port, bridge pane,
// handrail, ladder, RCS quad, antenna, sensor dome, floodlight, container) is generated
// once with fal (assets/parts/*.glb, see assets/parts/parts.json) in metres, in a mount
// frame: origin at the centre of the mounting face, +Z out of the hull, +Y up. A ship
// module lists where its parts go (hand-authored placements, like its lights and engines);
// this module snaps each placement onto the hull and draws every part as one
// InstancedMesh per part mesh, so the same door is exactly the same size on every ship.
//
// Placement spec (ship frame, metres, before the class volume correction):
//   { part, p: [x,y,z], n?: [x,y,z], up?: [x,y,z], rot?: deg, scale?, mirrorX?,
//     snap?: true, lift?: 0.02 }
//   { part, row: { from: [x,y,z], to: [x,y,z], pitch }, rows?: { count, step: [x,y,z] }, n, ... }
// With snap (the default), a ray is cast from 8 m outside p along -n and the part sits on
// the first hull hit, its +Z along n (the authored mounting direction, so panes on a
// slightly lumpy surface still line up) unless `normal: 'hit'` asks for the hit normal.
// A placement whose ray misses the hull is dropped (logged), never left floating.
import * as THREE from 'three';
import { loadGLB } from './glbship.js';
import { applyLivery } from './livery.js';

const V3 = THREE.Vector3;
export const PARTS_DIR = './assets/parts';

/** Preload the parts a ship module places (returns { name: gltf }). */
export async function loadParts(placements = []) {
  const names = [...new Set(placements.map((q) => q.part))];
  const out = {};
  await Promise.all(names.map(async (n) => { out[n] = await loadGLB(`${PARTS_DIR}/${n}.glb`); }));
  return out;
}

/** Expand rows / row grids / mirrors into single placements { part, p, n, up, rot, scale, ... }. */
export function expandPlacements(placements) {
  const out = [];
  for (const q of placements) {
    const base = [];
    if (q.row) {
      const a = new V3(...q.row.from), b = new V3(...q.row.to);
      const len = a.distanceTo(b);
      const k = Math.max(1, Math.floor(len / q.row.pitch + 1e-6) + 1);
      const off = (len - (k - 1) * q.row.pitch) / 2; // centre the run between from and to
      const d = b.clone().sub(a).normalize();
      for (let i = 0; i < k; i++) base.push(a.clone().addScaledVector(d, off + i * q.row.pitch));
    } else base.push(new V3(...q.p));
    const step = q.rows ? new V3(...q.rows.step) : null;
    for (let r = 0; r < (q.rows?.count ?? 1); r++) {
      for (const p0 of base) {
        const p = step ? p0.clone().addScaledVector(step, r) : p0;
        out.push({ ...q, p, n: new V3(...(q.n || [0, 0, 1])).normalize(), up: new V3(...(q.up || [0, 1, 0])) });
        if (q.mirrorX) out.push({ ...q, p: new V3(-p.x, p.y, p.z), n: new V3(-(q.n?.[0] ?? 0), q.n?.[1] ?? 0, q.n?.[2] ?? 1).normalize(), up: new V3(-(q.up?.[0] ?? 0), q.up?.[1] ?? 1, q.up?.[2] ?? 0), mirrored: true });
      }
    }
  }
  return out;
}

const _m = new THREE.Matrix4(), _q = new THREE.Quaternion(), _s = new V3();

/** Orientation with +Z along n and +Y as close to `up` as possible, then `rot` degrees about n. */
function basis(n, up, rot = 0) {
  const z = n.clone().normalize();
  let y = up.clone().sub(z.clone().multiplyScalar(up.dot(z)));
  if (y.lengthSq() < 1e-6) y = Math.abs(z.y) < 0.9 ? new V3(0, 1, 0).sub(z.clone().multiplyScalar(z.y)) : new V3(0, 0, 1).sub(z.clone().multiplyScalar(z.z));
  y.normalize();
  const x = new V3().crossVectors(y, z);
  const m = new THREE.Matrix4().makeBasis(x, y, z);
  if (rot) m.multiply(new THREE.Matrix4().makeRotationZ(rot * Math.PI / 180));
  return new THREE.Quaternion().setFromRotationMatrix(m);
}

/**
 * Add the placed parts to a built ship group (buildGLBShip output, ship frame = group frame).
 * @returns {{ placed: number, dropped: number, instanced: THREE.InstancedMesh[] }}
 */
export function composeParts(group, placements, partsGltf, { livery = 'dark' } = {}) {
  group.updateMatrixWorld(true);
  const hull = [];
  group.traverse((o) => { if (o.isMesh && o.userData.hull) hull.push(o); });
  const toLocal = group.matrixWorld.clone().invert();
  const ray = new THREE.Raycaster();
  const nWorld = new THREE.Matrix3().getNormalMatrix(group.matrixWorld);
  const byPart = new Map();
  let dropped = 0;
  for (const q of expandPlacements(placements)) {
    let p = q.p, n = q.n;
    if (q.snap !== false) {
      const o = p.clone().addScaledVector(n, 8).applyMatrix4(group.matrixWorld);
      ray.set(o, n.clone().applyMatrix3(nWorld).normalize().negate());
      ray.far = 8 + (q.reach ?? 6);
      const hit = ray.intersectObjects(hull, false)[0];
      if (!hit) { dropped++; continue; }
      p = hit.point.clone().applyMatrix4(toLocal).addScaledVector(n, q.lift ?? 0.02);
      if (q.normal === 'hit' && hit.face) n = hit.face.normal.clone().transformDirection(hit.object.matrixWorld).transformDirection(toLocal);
    }
    const quat = basis(n, q.up, q.rot || 0);
    const sc = q.scale ?? 1;
    // a mirrored placement mirrors the part too, so handed parts (a door handle) stay handed
    _s.set(q.mirrored ? -sc : sc, sc, sc);
    if (!byPart.has(q.part)) byPart.set(q.part, []);
    byPart.get(q.part).push(new THREE.Matrix4().compose(p, quat, _s));
  }

  const instanced = [];
  for (const [name, mats] of byPart) {
    const gltf = partsGltf[name];
    if (!gltf) { console.warn(`[compose] part ${name} not loaded`); continue; }
    gltf.scene.updateMatrixWorld(true);
    gltf.scene.traverse((o) => {
      if (!o.isMesh) return;
      const mat = o.material.clone();
      if (livery) applyLivery(mat, livery);
      for (const t of [mat.map, mat.normalMap, mat.roughnessMap]) if (t) t.anisotropy = 8;
      // mirrored instances flip the winding: draw both faces of the (closed, small) part
      if (mats.some((m) => m.determinant() < 0)) mat.side = THREE.DoubleSide;
      const im = new THREE.InstancedMesh(o.geometry, mat, mats.length);
      mats.forEach((m, i) => im.setMatrixAt(i, _m.multiplyMatrices(m, o.matrixWorld)));
      im.instanceMatrix.needsUpdate = true;
      im.computeBoundingSphere();
      im.castShadow = im.receiveShadow = true;
      im.name = `part:${name}`;
      im.userData.part = name; // not hull: the hangar containment test ignores parts
      group.add(im);
      instanced.push(im);
    });
  }
  const placed = [...byPart.values()].reduce((a, m) => a + m.length, 0);
  if (dropped) console.warn(`[compose] ${group.name || ''}: ${dropped} placement(s) missed the hull`);
  return { placed, dropped, instanced };
}
