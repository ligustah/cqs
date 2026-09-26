// Hangar containment test for generated carrier hulls.
//
// The hangar anchor is a box in the ship frame. A generated mesh has no notion
// of "interior", so we sample points on a grid inside the box and cast rays
// along the six axes against the hull. A point counts as inside when:
//   - it is under the roof and over the deck (dorsal and ventral rays hit) and
//     at least two of the four horizontal rays hit hull structure, or
//   - it is under the roof and over the deck and every one of the four
//     horizontal rays either hits hull structure or leaves through a framed
//     opening in it: a doorway with hull above, below and on both sides
//     (an open flank bay between two frames, or the bow mouth). A carrier's
//     bay may be open at the bow and along both flanks so ships parked inside
//     can be seen; the opening still has to be cut into the hull, which is
//     what tells a bay apart from open space beside or under the ship, or
//   - it lies inside solid hull (an odd number of crossings on most rays).
// A hangar is plausible when nearly all of the box is inside the hull.
//
// Rays are axis-aligned in the ship frame, so the hull triangles are binned
// once per axis on a 2D grid over the other two axes; a ray only tests the
// triangles of its own cell (fast enough to march along open rays).
import * as THREE from 'three';

const AXES = [[0, 1], [0, -1], [1, 1], [1, -1], [2, -1], [2, 1]]; // px nx py ny nz pz
const NAMES = ['px', 'nx', 'py', 'ny', 'nz', 'pz'];

/** Axis-aligned ray caster over the hull meshes of `ship`, in the ship's local frame. */
export function hullCaster(ship, { cells = 160 } = {}) {
  ship.updateMatrixWorld(true);
  const toLocal = ship.matrixWorld.clone().invert();
  const m = new THREE.Matrix4();
  const v = new THREE.Vector3();
  const chunks = [];
  let nTri = 0;
  ship.traverse((o) => {
    if (!o.isMesh || !o.userData.hull) return;
    m.multiplyMatrices(toLocal, o.matrixWorld);
    const pos = o.geometry.attributes.position;
    const P = new Float32Array(pos.count * 3);
    for (let i = 0; i < pos.count; i++) { v.fromBufferAttribute(pos, i).applyMatrix4(m); P[i * 3] = v.x; P[i * 3 + 1] = v.y; P[i * 3 + 2] = v.z; }
    const idx = o.geometry.index ? o.geometry.index.array : null;
    const n = idx ? idx.length / 3 : pos.count / 3;
    chunks.push({ P, idx, n, base: nTri });
    nTri += n;
  });
  // flat triangle table: 9 floats per triangle
  const T = new Float32Array(nTri * 9);
  for (const c of chunks) for (let t = 0; t < c.n; t++) for (let k = 0; k < 3; k++) {
    const i = c.idx ? c.idx[t * 3 + k] : t * 3 + k;
    T.set([c.P[i * 3], c.P[i * 3 + 1], c.P[i * 3 + 2]], (c.base + t) * 9 + k * 3);
  }
  const lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
  for (let i = 0; i < T.length; i += 3) for (let k = 0; k < 3; k++) { lo[k] = Math.min(lo[k], T[i + k]); hi[k] = Math.max(hi[k], T[i + k]); }
  const cell = Math.max(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]) / cells;
  // per ray axis a: bins over axes (u, w) = ((a+1)%3, (a+2)%3), CSR layout
  const grids = [0, 1, 2].map((a) => {
    const u = (a + 1) % 3, w = (a + 2) % 3;
    const nu = Math.ceil((hi[u] - lo[u]) / cell) + 1, nw = Math.ceil((hi[w] - lo[w]) / cell) + 1;
    const range = (t) => {
      const o = t * 9;
      const u0 = Math.min(T[o + u], T[o + 3 + u], T[o + 6 + u]), u1 = Math.max(T[o + u], T[o + 3 + u], T[o + 6 + u]);
      const w0 = Math.min(T[o + w], T[o + 3 + w], T[o + 6 + w]), w1 = Math.max(T[o + w], T[o + 3 + w], T[o + 6 + w]);
      return [Math.floor((u0 - lo[u]) / cell), Math.floor((u1 - lo[u]) / cell), Math.floor((w0 - lo[w]) / cell), Math.floor((w1 - lo[w]) / cell)];
    };
    const count = new Uint32Array(nu * nw + 1);
    for (let t = 0; t < nTri; t++) { const [a0, a1, b0, b1] = range(t); for (let i = a0; i <= a1; i++) for (let j = b0; j <= b1; j++) count[i * nw + j + 1]++; }
    for (let i = 1; i < count.length; i++) count[i] += count[i - 1];
    const fill = count.slice(0, -1);
    const list = new Uint32Array(count[count.length - 1]);
    for (let t = 0; t < nTri; t++) { const [a0, a1, b0, b1] = range(t); for (let i = a0; i <= a1; i++) for (let j = b0; j <= b1; j++) list[fill[i * nw + j]++] = t; }
    return { u, w, nu, nw, start: count, list };
  });

  /** Cast from o along axis a (sign s): { hits, dist } (dist = nearest hit, Infinity if none). */
  function cast(o, a, s) {
    const g = grids[a];
    const ci = Math.floor((o[g.u] - lo[g.u]) / cell), cj = Math.floor((o[g.w] - lo[g.w]) / cell);
    if (ci < 0 || cj < 0 || ci >= g.nu || cj >= g.nw) return { hits: 0, dist: Infinity };
    const c = ci * g.nw + cj;
    const pu = o[g.u], pw = o[g.w];
    let hits = 0, dist = Infinity;
    for (let k = g.start[c]; k < g.start[c + 1]; k++) {
      const q = g.list[k] * 9;
      const au = T[q + g.u] - pu, aw = T[q + g.w] - pw;
      const bu = T[q + 3 + g.u] - pu, bw = T[q + 3 + g.w] - pw;
      const cu = T[q + 6 + g.u] - pu, cw = T[q + 6 + g.w] - pw;
      // 2D point-in-triangle (origin) by edge signs; barycentric weights give the hit coordinate
      const e0 = bu * cw - bw * cu, e1 = cu * aw - cw * au, e2 = au * bw - aw * bu;
      if (!((e0 >= 0 && e1 >= 0 && e2 >= 0) || (e0 <= 0 && e1 <= 0 && e2 <= 0))) continue;
      const sum = e0 + e1 + e2;
      if (sum === 0) continue;
      const x = (e0 * T[q + a] + e1 * T[q + 3 + a] + e2 * T[q + 6 + a]) / sum;
      const d = (x - o[a]) * s;
      if (d > 0) { hits++; if (d < dist) dist = d; }
    }
    return { hits, dist };
  }
  return { cast, lo, hi, cell, triangles: nTri };
}

/**
 * @param {THREE.Object3D} ship   group built by buildShip (anchors in its local frame)
 * @param {{p: THREE.Vector3, size: number[]}} hangar  anchor (local frame, before scale correction)
 * @param {object} opts  grid: samples per axis [x, y, z]
 * @returns {{ fraction: number, samples: number, inside: number, misses: object, openings: number }}
 */
export function hangarInsideFraction(ship, hangar, { grid = [6, 4, 16], caster = null } = {}) {
  const { cast, lo, hi, cell } = caster || hullCaster(ship);
  const size = new THREE.Vector3(...hangar.size);
  const c = hangar.p;
  const step = cell * 1.5;
  const hit = (o, a, s) => cast(o, a, s).hits > 0;
  // does the open ray from o along (a, s) pass through an opening framed by hull
  // above, below and on both sides (the two other-axis horizontal directions)?
  const framed = (o, a, s) => {
    const b = a === 0 ? 2 : 0; // the other horizontal axis
    const q = [...o];
    for (q[a] = o[a] + s * step; q[a] > lo[a] - step && q[a] < hi[a] + step; q[a] += s * step) {
      if (hit(q, 1, 1) && hit(q, 1, -1) && hit(q, b, 1) && hit(q, b, -1)) return true;
    }
    return false;
  };
  const misses = Object.fromEntries(NAMES.map((n) => [n, 0]));
  let inside = 0, total = 0, openings = 0;
  for (let i = 0; i < grid[0]; i++) for (let j = 0; j < grid[1]; j++) for (let k = 0; k < grid[2]; k++) {
    const p = [
      c.x + ((i + 0.5) / grid[0] - 0.5) * size.x,
      c.y + ((j + 0.5) / grid[1] - 0.5) * size.y,
      c.z + ((k + 0.5) / grid[2] - 0.5) * size.z,
    ];
    let odd = 0, sides = 0, closed = 0, roof = false, deck = false;
    const open = [];
    AXES.forEach(([a, s], n) => {
      const r = cast(p, a, s);
      if (r.hits % 2 === 1) odd++;
      if (!r.hits) { if (a !== 1) open.push([a, s, n]); else misses[NAMES[n]]++; return; }
      if (n === 2) roof = true; else if (n === 3) deck = true; else { sides++; closed++; }
    });
    let ok = odd >= 4 || (roof && deck && sides >= 2);
    if (!ok && roof && deck) {
      for (const [a, s, n] of open) if (framed(p, a, s)) closed++; else misses[NAMES[n]]++;
      ok = closed === 4;
      if (ok) openings++;
    } else for (const [, , n] of open) misses[NAMES[n]]++;
    total++;
    if (ok) inside++;
  }
  return { fraction: inside / total, samples: total, inside, misses, openings };
}
