// Lightscape: the many small lights that make a dark hull read as inhabited and operating
// (v11). Nav lights (red / green / strobes) stay in the module's `lights`; this adds
//   - pins: small amber / warm-white / cool points (0.2-0.3 m: fleet standard, v14 STANDARD section 2; window points
//     0.5 m) along the hull's real chines and block corners, and authored rows, rings and window runs;
//   - slits: short, dimmer glowing bars tucked into concave corners (recesses, vents, the gaps
//     between armour blocks) and authored bars.
// Both are generated once per ship prototype (buildGLBShip) and drawn by effects.js: every pin in
// the ship's single Points object, every slit in one InstancedMesh.
//
// Module field `lightscape` (ship frame, metres, before the class scale correction):
//   seed        integer: the whole pattern is deterministic
//   creases     automatic pins on the hull's convex creases (faces meeting at >= angle deg, crease >= minLen m):
//               { angle, minLen, pitch (m between run slots), share (0..1 of slots used), run: [min, max] pins
//                 per run, runPitch (m), corners (0..1 chance of a pin at each crease end: block corners),
//                 spacing (m, no two pins closer), lift (m off the edge), clear (m of open space in front),
//                 size: [min, max] m, intensity: [min, max], mix: { colour: weight }, blinkShare, max (cap) }
//   slits       automatic bars in concave creases (recess corners, block gaps): { angle, minLen, share, every
//               (m between bars on a long crease), len: [min, max], width, radiance: [min, max], mix, spacing, max,
//               orient (default true: upright bars in side-facing recesses are favoured, keel undersides and
//               edge-on horizontal corners rarely lit), symmetric (default true: drawn on x >= 0 and mirrored where the
//               hull has the same recess on the other flank) }
//   louvre      { minFamily: 4, pitch: 1.0, lenTol: 0.15 } | false (also accepted as creases.louvre): families of
//               parallel, same-length, same-facing creases side by side (grilles, louvres, radiator fins) get no
//               pins and no slits
//   (slits carry a rank too: corner bars 0-0.5, recess bars 0-1, authored `keep` / animated 0, other authored
//   hashed 0-1; mirror twins share it. effects.js thins bars by rank with the ship's screen size, as it does pins,
//   and rank-0 bars keep at least 0.45 of their radiance far off, the rest 0.2)
//   (every pin carries a distance-thinning rank for effects.js: crease-end corner pins 0.02-0.47, authored
//   rows 0.1-0.5, port rows 0.15-0.65, crease-run pins 0.4-1: corners and authored rows are the last left far off.
//   Far-field energy floor by type: `keep` and animated pins 0.4, plain lamps 0.25, port* window points fade with
//   their area to 0.05; the module's `lights[]` (nav path) is never dimmed or thinned, so it holds nav, red
//   obstruction and white outline lights only: amber running lights and window points belong here)
//   zones       [{ box, mirrorX, creases: {...overrides} | null, slits: {...} | null }]: inside the box the
//               overrides apply (null: none there), e.g. a warmer, denser hangar interior or a vent grille kept dark
//   cool        { radius, depth (x the bell radius) }: crease pins round a drive housing turn blue-white
//   patterns    authored lights (all take color | mix, size, intensity, skip (share left dark), keep, mirrorX, seed):
//               { row: [a, b], pitch, ends }              pins along a line
//               { surface: name, edge: top|bottom|left|right|centre, inset, lift, pitch }   a row on an
//                                                          anchors.surfaces face ('top' = its upper edge)
//               { ring: { c, axis, r, start, span }, n }  pins round a circle (housings, turret bases)
//               { points: [[x, y, z], ...] }
//               { slit: p, u, n, len, width, radiance } / { slitRow: [a, b], pitch, ... }   glowing bars
//               chase: period (s) -> a sequenced chaser along the row (reverse: runs b -> a instead of a -> b;
//               duty, chaseSpan); pulse: period -> slow soft beacons (random phases)
// Every generated candidate is ray-cast against the hull (TriGrid): the remodelled hulls are built from
// overlapping solids, so a crease can lie inside another solid; only exposed ones are lit.
// The phone tier (device.js LITE) keeps about half of the pins and slits (animated and `keep` ones stay).
import * as THREE from 'three';
import { LITE } from './device.js';

const V3 = THREE.Vector3;

// Pin colours (display-referred sRGB; effects.js scales them into scene-linear radiance).
// amber: the running-light amber; warm: tungsten-ish work lights; white: neutral LED; cool: the
// blue-white of drive and sensor status lights; port / portDim: lit interiors behind 1 m ports.
export const PIN_COLORS = {
  amber: '#ffae3b', amberDeep: '#ff9a2a', warm: '#ffd6a0', white: '#fff1dc', cool: '#bcd4ff', ice: '#9fc4ff',
  port: '#6a5236', portDim: '#46382a', portCool: '#3e4450',
};

/** Deterministic hash in [0, 1) of an integer and a seed. */
function hash1(i, seed = 0) {
  let h = (i | 0) ^ Math.imul(seed | 0, 0x9e3779b1);
  h = Math.imul(h ^ (h >>> 16), 0x85ebca6b);
  h = Math.imul(h ^ (h >>> 13), 0xc2b2ae35);
  h ^= h >>> 16;
  return (h >>> 0) / 4294967296;
}
/** Deterministic hash of a position (1 cm grid). */
function hashP(p, seed = 0) {
  return hash1(Math.round(p.x * 100) * 73856093 ^ Math.round(p.y * 100) * 19349663 ^ Math.round(p.z * 100) * 83492791, seed);
}
const lerp = (a, b, t) => a + (b - a) * t;
const range = (r, t) => (Array.isArray(r) ? lerp(r[0], r[1], t) : r);
function pick(mix, t) {
  const e = Object.entries(mix);
  const sum = e.reduce((s, [, w]) => s + w, 0);
  let acc = 0;
  for (const [k, w] of e) { acc += w / sum; if (t < acc) return k; }
  return e[e.length - 1][0];
}
const inBox = (p, [a, b]) => p.x >= a[0] && p.x <= b[0] && p.y >= a[1] && p.y <= b[1] && p.z >= a[2] && p.z <= b[2];
const mirrorBox = ([a, b]) => [[-b[0], a[1], a[2]], [-a[0], b[1], b[2]]];
const expandBoxes = (list = []) => list.flatMap((z) => {
  const box = z.box || z;
  const one = z.box ? z : { box };
  return z.mirrorX ? [one, { ...one, box: mirrorBox(box) }] : [one];
});

/** A spatial hash that refuses points closer than `spacing` to an accepted one. */
class Spacer {
  constructor(spacing) { this.s = Math.max(spacing, 1e-3); this.cells = new Map(); }
  key(i, j, k) { return `${i},${j},${k}`; }
  tryAdd(p, spacing = this.s) {
    const s = this.s, i = Math.floor(p.x / s), j = Math.floor(p.y / s), k = Math.floor(p.z / s);
    const r = Math.ceil(spacing / s);
    for (let a = -r; a <= r; a++) for (let b = -r; b <= r; b++) for (let c = -r; c <= r; c++) {
      const list = this.cells.get(this.key(i + a, j + b, k + c));
      if (list) for (const q of list) if (q.distanceToSquared(p) < spacing * spacing) return false;
    }
    const key = this.key(i, j, k);
    if (!this.cells.has(key)) this.cells.set(key, []);
    this.cells.get(key).push(p.clone());
    return true;
  }
}

/**
 * Crease edges of the hull in the ship frame: welded positions (1 cm), triangles, and for every
 * edge shared by two faces meeting at >= `angle` degrees: its ends, the outward bisector of the
 * two face normals and whether it is convex (a chine, a block corner) or concave (a recess corner).
 * meshes: [{ geometry, matrix }] (matrix: object -> ship frame).
 */
export function hullCreases(meshes, { angle = 35, minLen = 1 } = {}) {
  const cosT = Math.cos((angle * Math.PI) / 180);
  const out = [];
  const soupP = [], soupT = []; // every hull triangle in the ship frame, for the exposure test
  for (const { geometry, matrix } of meshes) {
    const pos = geometry.attributes.position;
    if (!pos) continue;
    const idx = geometry.index ? geometry.index.array : null;
    const nTri = (idx ? idx.length : pos.count) / 3;
    // weld: unique ship-frame positions on a 1 cm grid
    const remap = new Int32Array(pos.count);
    const P = [];
    const seen = new Map();
    const v = new V3();
    for (let i = 0; i < pos.count; i++) {
      v.fromBufferAttribute(pos, i).applyMatrix4(matrix);
      const key = `${Math.round(v.x * 100)},${Math.round(v.y * 100)},${Math.round(v.z * 100)}`;
      let id = seen.get(key);
      if (id === undefined) { id = P.length / 3; seen.set(key, id); P.push(v.x, v.y, v.z); }
      remap[i] = id;
    }
    const N = P.length / 3;
    const base = soupP.length / 3;
    for (let i = 0; i < P.length; i++) soupP.push(P[i]);
    const tri = new Int32Array(nTri * 3);
    const fn = new Float32Array(nTri * 3);
    const e1 = new V3(), e2 = new V3(), n = new V3(), a = new V3(), b = new V3(), c = new V3();
    const edges = new Map();
    for (let t = 0; t < nTri; t++) {
      const i0 = remap[idx ? idx[t * 3] : t * 3], i1 = remap[idx ? idx[t * 3 + 1] : t * 3 + 1], i2 = remap[idx ? idx[t * 3 + 2] : t * 3 + 2];
      tri[t * 3] = i0; tri[t * 3 + 1] = i1; tri[t * 3 + 2] = i2;
      if (i0 === i1 || i1 === i2 || i0 === i2) continue;
      soupT.push(base + i0, base + i1, base + i2);
      a.fromArray(P, i0 * 3); b.fromArray(P, i1 * 3); c.fromArray(P, i2 * 3);
      n.crossVectors(e1.subVectors(b, a), e2.subVectors(c, a));
      const area2 = n.length();
      if (area2 < 1e-6) continue;
      n.divideScalar(area2);
      fn[t * 3] = n.x; fn[t * 3 + 1] = n.y; fn[t * 3 + 2] = n.z;
      for (const [u, w] of [[i0, i1], [i1, i2], [i2, i0]]) {
        const key = u < w ? u * N + w : w * N + u;
        const e = edges.get(key);
        if (e === undefined) edges.set(key, t);
        else if (e >= 0) edges.set(key, -(e + 1) * 4194304 - t - 1); // pack two faces (t < 2^22)
        else edges.set(key, -1e18); // non-manifold: skip
      }
    }
    const nA = new V3(), nB = new V3(), opp = new V3();
    for (const [key, val] of edges) {
      if (val >= 0 || val === -1e18) continue;
      const packed = -val;
      const fa = Math.floor(packed / 4194304) - 1, fb = (packed % 4194304) - 1;
      if (fa < 0 || fb < 0) continue;
      nA.fromArray(fn, fa * 3); nB.fromArray(fn, fb * 3);
      if (nA.lengthSq() < 0.5 || nB.lengthSq() < 0.5) continue;
      const d = nA.dot(nB);
      if (d > cosT) continue;
      const u = Math.floor(key / N), w = key - u * N;
      a.fromArray(P, u * 3); b.fromArray(P, w * 3);
      const len = a.distanceTo(b);
      if (len < minLen) continue;
      // the vertex of face B that is not on the edge: behind face A's plane = convex
      let o = -1;
      for (let k = 0; k < 3; k++) { const q = tri[fb * 3 + k]; if (q !== u && q !== w) o = q; }
      if (o < 0) continue;
      opp.fromArray(P, o * 3).sub(a);
      const side = opp.dot(nA);
      const bis = new V3().addVectors(nA, nB);
      if (bis.lengthSq() < 1e-6) continue;
      out.push({ a: a.clone(), b: b.clone(), len, n: bis.normalize(), convex: side < 0, sharp: Math.acos(THREE.MathUtils.clamp(d, -1, 1)), nA: nA.clone(), nB: nB.clone() });
    }
  }
  // long creases first: the main chines claim their pins before greebles do
  out.sort((p, q) => q.len - p.len);
  out.grid = new TriGrid(new Float32Array(soupP), new Int32Array(soupT));
  return out;
}

/**
 * Uniform grid over the hull's triangles for short ray casts (Amanatides-Woo traversal,
 * Moller-Trumbore tests). The remodelled hulls are built from overlapping closed solids, so many
 * creases lie inside another solid or under a plate: a candidate light is kept only where a ray
 * from it along its outward normal first meets a front face far enough away, or nothing at all.
 */
export class TriGrid {
  constructor(P, T) {
    this.P = P; this.T = T;
    const n = T.length / 3;
    const min = new V3(Infinity, Infinity, Infinity), max = new V3(-Infinity, -Infinity, -Infinity);
    for (let i = 0; i < P.length; i += 3) { min.min(new V3(P[i], P[i + 1], P[i + 2])); max.max(new V3(P[i], P[i + 1], P[i + 2])); }
    min.subScalar(0.5); max.addScalar(0.5);
    const size = max.clone().sub(min);
    const cell = Math.max(0.5, Math.cbrt((size.x * size.y * size.z) / Math.max(1, n / 3)));
    this.min = min; this.cell = cell;
    this.nx = Math.max(1, Math.ceil(size.x / cell)); this.ny = Math.max(1, Math.ceil(size.y / cell)); this.nz = Math.max(1, Math.ceil(size.z / cell));
    const cells = new Map();
    for (let t = 0; t < n; t++) {
      let x0 = Infinity, y0 = Infinity, z0 = Infinity, x1 = -Infinity, y1 = -Infinity, z1 = -Infinity;
      for (let k = 0; k < 3; k++) {
        const v = T[t * 3 + k] * 3;
        x0 = Math.min(x0, P[v]); x1 = Math.max(x1, P[v]); y0 = Math.min(y0, P[v + 1]); y1 = Math.max(y1, P[v + 1]); z0 = Math.min(z0, P[v + 2]); z1 = Math.max(z1, P[v + 2]);
      }
      const i0 = this.ci(x0, 'x'), i1 = this.ci(x1, 'x'), j0 = this.ci(y0, 'y'), j1 = this.ci(y1, 'y'), k0 = this.ci(z0, 'z'), k1 = this.ci(z1, 'z');
      for (let i = i0; i <= i1; i++) for (let j = j0; j <= j1; j++) for (let k = k0; k <= k1; k++) {
        const key = (k * this.ny + j) * this.nx + i;
        let list = cells.get(key);
        if (!list) cells.set(key, (list = []));
        list.push(t);
      }
    }
    this.cells = cells;
  }
  ci(v, axis) {
    const n = axis === 'x' ? this.nx : axis === 'y' ? this.ny : this.nz;
    return Math.min(n - 1, Math.max(0, Math.floor((v - this.min[axis]) / this.cell)));
  }
  /** First hit along o + t d (d unit), t in (eps, maxT]: { t, front } or null. */
  cast(o, d, maxT = Infinity, eps = 1e-3) {
    const { P, T, cell, min } = this;
    let i = Math.floor((o.x - min.x) / cell), j = Math.floor((o.y - min.y) / cell), k = Math.floor((o.z - min.z) / cell);
    if (i < 0 || j < 0 || k < 0 || i >= this.nx || j >= this.ny || k >= this.nz) return null;
    const si = d.x > 0 ? 1 : -1, sj = d.y > 0 ? 1 : -1, sk = d.z > 0 ? 1 : -1;
    const next = (c, s, o0, m0, dd) => (dd === 0 ? Infinity : ((m0 + (c + (s > 0 ? 1 : 0)) * cell) - o0) / dd);
    let tx = next(i, si, o.x, min.x, d.x), ty = next(j, sj, o.y, min.y, d.y), tz = next(k, sk, o.z, min.z, d.z);
    const dx = d.x === 0 ? Infinity : cell / Math.abs(d.x), dy = d.y === 0 ? Infinity : cell / Math.abs(d.y), dz = d.z === 0 ? Infinity : cell / Math.abs(d.z);
    const seen = new Set();
    let tEnter = 0;
    for (let guard = 0; guard < 4096; guard++) {
      const tExit = Math.min(tx, ty, tz);
      const list = this.cells.get((k * this.ny + j) * this.nx + i);
      let best = null;
      if (list) for (const t of list) {
        if (seen.has(t)) continue;
        const h = this.hit(t, o, d, eps);
        if (h && h.t <= tExit + 1e-6 && (!best || h.t < best.t)) best = h;
        else if (!h) seen.add(t);
      }
      if (best) return best.t <= maxT ? best : null;
      tEnter = tExit;
      if (tEnter > maxT) return null;
      if (tx <= ty && tx <= tz) { i += si; tx += dx; } else if (ty <= tz) { j += sj; ty += dy; } else { k += sk; tz += dz; }
      if (i < 0 || j < 0 || k < 0 || i >= this.nx || j >= this.ny || k >= this.nz) return null;
    }
    return null;
  }
  hit(t, o, d, eps) {
    const P = this.P, T = this.T;
    const a = T[t * 3] * 3, b = T[t * 3 + 1] * 3, c = T[t * 3 + 2] * 3;
    const e1x = P[b] - P[a], e1y = P[b + 1] - P[a + 1], e1z = P[b + 2] - P[a + 2];
    const e2x = P[c] - P[a], e2y = P[c + 1] - P[a + 1], e2z = P[c + 2] - P[a + 2];
    const px = d.y * e2z - d.z * e2y, py = d.z * e2x - d.x * e2z, pz = d.x * e2y - d.y * e2x;
    const det = e1x * px + e1y * py + e1z * pz;
    if (Math.abs(det) < 1e-12) return null;
    const inv = 1 / det;
    const sx = o.x - P[a], sy = o.y - P[a + 1], sz = o.z - P[a + 2];
    const u = (sx * px + sy * py + sz * pz) * inv;
    if (u < 0 || u > 1) return null;
    const qx = sy * e1z - sz * e1y, qy = sz * e1x - sx * e1z, qz = sx * e1y - sy * e1x;
    const v = (d.x * qx + d.y * qy + d.z * qz) * inv;
    if (v < 0 || u + v > 1) return null;
    const tt = (e2x * qx + e2y * qy + e2z * qz) * inv;
    if (tt <= eps) return null;
    // det = -d . (e1 x e2): det > 0 means the ray runs against the face normal, i.e. meets its front
    return { t: tt, front: det > 0 };
  }
  /** A light at p (already lifted off the surface) with outward normal n is exposed when the first
   *  thing along n (and along two tilted directions) is a front face at least `clear` m away, or nothing. */
  exposed(p, n, clear = 0.4, reach = Infinity) {
    const t1 = new V3().crossVectors(n, Math.abs(n.y) < 0.9 ? new V3(0, 1, 0) : new V3(1, 0, 0)).normalize();
    const dirs = [n, n.clone().addScaledVector(t1, 0.6).normalize(), n.clone().addScaledVector(t1, -0.6).normalize()];
    for (const d of dirs) {
      const h = this.cast(p, d, reach);
      if (h && (!h.front || h.t < clear)) return false;
    }
    return true;
  }
}

/** Surface frame from anchors.surfaces: centre, normal, u (along), v = n x u (across). */
function surfaceFrame(s) {
  const c = new V3(...s.centre), n = new V3(...s.normal).normalize(), u = new V3(...s.u).normalize();
  const v = new V3().crossVectors(n, u).normalize();
  if (v.y < -1e-3) v.negate(); // 'top' is the upper edge of a wall
  return { c, n, u, v, w: s.width, h: s.height };
}

/**
 * Build the lightscape. cfg: the module asset (lightscape, anchors.surfaces, engines);
 * meshes: [{ geometry, matrix }] hull meshes in the ship frame; engines: glbship engine list.
 * Returns { pins: [{ p, n, color, size, intensity, blink }], slits: [{ p, u, n, len, width, color, radiance, anim }] }.
 */
export function buildLightscape(cfg, meshes, engines = []) {
  const L = cfg.lightscape;
  if (!L) return { pins: [], slits: [] };
  const seed = L.seed ?? 1;
  const pins = [], slits = [];
  const stats = { vent: 0 };
  let scapeCreases = null;
  const surfaces = cfg.anchors?.surfaces || {};
  let serial = 0;
  const addPin = (p, o) => {
    pins.push({
      p: p.clone(), n: o.n ? o.n.clone() : null, color: o.color || 'amber', size: o.size ?? 0.3, intensity: o.intensity ?? 1,
      blink: o.blink || null, keep: !!o.keep, rank: o.rank ?? null,
    });
  };
  const addSlit = (p, u, n, o) => {
    slits.push({ p: p.clone(), u: u.clone().normalize(), n: n.clone().normalize(), len: o.len ?? 1.4, width: o.width ?? 0.22, color: o.color || 'amber', radiance: o.radiance ?? 1.4, anim: o.anim || null, keep: !!o.keep, rank: o.rank ?? (o.keep || o.anim ? 0 : hashP(new V3(Math.abs(p.x), p.y, p.z), seed + 91)) });
  };

  // ---- authored patterns ------------------------------------------------------------------
  for (const pat0 of L.patterns || []) {
    const list = pat0.mirrorX ? [pat0, mirrorPattern(pat0)] : [pat0];
    for (const pat of list) pattern(pat);
  }
  function pattern(pat) {
    const base = { color: pat.color, size: pat.size, intensity: pat.intensity, keep: pat.keep };
    const skip = pat.skip ?? 0; // share of positions left dark (deterministic)
    const s0 = (pat.seed ?? 0) + seed * 7919 + serial++ * 104729;
    const jit = (i, k = 0) => hash1(i * 31 + k, s0);
    // points along a line a -> b with a pitch (a chaser gets sequential soft pulses running a -> b: the
    // pulse window fract(t / period + phase) < duty reaches larger phases first, so phases fall along the row)
    const along = (a, b, pitch, cb) => {
      const d = b.clone().sub(a), len = d.length();
      const n = Math.max(1, Math.floor(len / pitch + 1e-6) + (pat.ends === false ? -1 : 1));
      for (let i = 0; i < n; i++) {
        const t = n === 1 ? 0.5 : pat.ends === false ? (i + 1) / (n + 1) : i / (n - 1);
        cb(a.clone().addScaledVector(d, t), i, n, d.clone().normalize());
      }
    };
    const pinAt = (p, i, n, o = {}) => {
      if (skip && jit(i, 1) < skip) return;
      let blink = pat.blink || null;
      if (pat.chase) blink = { period: pat.chase, duty: pat.duty ?? 0.22, phase: (pat.reverse ? i : n - 1 - i) / n * (pat.chaseSpan ?? 1), soft: 0.6 };
      else if (pat.pulse) blink = { period: pat.pulse, duty: 0.5, phase: jit(i, 2), soft: 1 };
      const size = Array.isArray(pat.size) ? range(pat.size, jit(i, 3)) : pat.size ?? 0.3;
      const intensity = Array.isArray(pat.intensity) ? range(pat.intensity, jit(i, 4)) : pat.intensity ?? 1;
      const color = pat.mix ? pick(pat.mix, jit(i, 5)) : pat.color || 'amber';
      // distance-thinning rank (effects.js): authored rows outlast the automatic crease runs
      addPin(p, { ...base, ...o, size, intensity, color, blink, rank: blink ? 0.06 : 0.1 + 0.4 * jit(i, 7) });
    };
    if (pat.row) {
      const [a, b] = pat.row.map((q) => new V3(...q));
      along(a, b, pat.pitch ?? 5, (p, i, n) => pinAt(p, i, n));
    } else if (pat.surface) {
      // a row along one edge of a measured flat face (anchors.surfaces), inset from it, standing
      // `lift` m proud; or a grid of `rows` over its face (lit ports)
      // a mirrorX copy is built on the SOURCE surface and reflected (x -> -x): re-deriving the frame from the
      // other side's anchor put 'top' on the inboard edge of horizontal faces (v = n x u keeps its sign)
      const src = pat.mirrorSurface && surfaces[pat.mirrorSurface];
      const s = src || surfaces[pat.surface];
      if (!s) return;
      const f = surfaceFrame(src ? { ...s, centre: [-s.centre[0], s.centre[1], s.centre[2]], normal: [-s.normal[0], s.normal[1], s.normal[2]], u: [-s.u[0], s.u[1], s.u[2]] } : s);
      if (src) { const v0 = surfaceFrame(s).v; f.v.set(-v0.x, v0.y, v0.z); }
      const lift = pat.lift ?? 0.1;
      const inset = pat.inset ?? 0.4;
      const hu = f.w / 2 - (pat.insetU ?? inset), hv = f.h / 2 - inset;
      const off = (du, dv) => f.c.clone().addScaledVector(f.u, du).addScaledVector(f.v, dv).addScaledVector(f.n, lift);
      const edges = { top: [off(-hu, hv), off(hu, hv)], bottom: [off(-hu, -hv), off(hu, -hv)], left: [off(-hu, -hv), off(-hu, hv)], right: [off(hu, -hv), off(hu, hv)], centre: [off(-hu, 0), off(hu, 0)] };
      if (pat.rows) {
        // lit ports: rows across the face, v offsets in metres from the centre; runs of compartments
        // share a level, a few stay dark; pat.flicker: share of runs with a faint unsteady light
        pat.rows.forEach((dv, r) => {
          const a = off(-hu, dv), b = off(hu, dv);
          along(a, b, pat.pitch ?? 3, (p, i, n) => {
            const run = Math.floor(i / (pat.run ?? 4));
            const lvl = hash1(run * 7 + r * 131, s0);
            if (lvl < (pat.dark ?? 0.25)) return;
            if (skip && jit(i + r * 997, 1) < skip) return;
            const flick = pat.flicker && hash1(run * 13 + r * 71, s0 + 1) < pat.flicker;
            const color = pat.mix ? pick(pat.mix, hash1(run * 3 + r, s0 + 2)) : pat.color || 'port';
            addPin(p, { color, size: pat.size ?? 0.9, intensity: lerp(0.55, 1.1, (lvl - (pat.dark ?? 0.25)) / (1 - (pat.dark ?? 0.25))) * (pat.intensity ?? 1), blink: flick ? { period: 0, flicker: 1 + hash1(run, s0) * 3 } : null, keep: pat.keep, rank: 0.15 + 0.5 * jit(i + r * 997, 8) });
          });
        });
      } else {
        const [a, b] = edges[pat.edge || 'top'];
        along(a, b, pat.pitch ?? 4, (p, i, n) => pinAt(p, i, n));
      }
    } else if (pat.ring) {
      // n points on a circle (centre c, axis, radius r): drive housings, turret bases, sensor pods
      const c = new V3(...pat.ring.c), ax = new V3(...(pat.ring.axis || [0, 1, 0])).normalize();
      const t1 = new V3().crossVectors(ax, Math.abs(ax.y) < 0.9 ? new V3(0, 1, 0) : new V3(1, 0, 0)).normalize();
      const t2 = new V3().crossVectors(ax, t1);
      const n = pat.n ?? 8, a0 = ((pat.ring.start ?? 0) * Math.PI) / 180, span = ((pat.ring.span ?? 360) * Math.PI) / 180;
      for (let i = 0; i < n; i++) {
        const a = a0 + (span * (span >= 2 * Math.PI - 1e-3 ? i / n : n === 1 ? 0.5 : i / (n - 1)));
        const p = c.clone().addScaledVector(t1, Math.cos(a) * pat.ring.r).addScaledVector(t2, Math.sin(a) * pat.ring.r);
        pinAt(p, i, n);
      }
    } else if (pat.points) {
      pat.points.forEach((q, i) => pinAt(new V3(...q), i, pat.points.length));
    } else if (pat.slit || pat.slitRow) {
      // glowing bars: one (slit: p) or a row (slitRow: [a, b], pitch); u = bar direction, n = the
      // face it sits in (the bar is drawn a few mm proud of it)
      const u = new V3(...(pat.u || [0, 1, 0])), n = new V3(...(pat.n || [1, 0, 0]));
      const o = { len: pat.len, width: pat.width, color: pat.color || 'amber', radiance: pat.radiance, keep: pat.keep };
      if (pat.slit) addSlit(new V3(...pat.slit), u, n, o);
      else {
        const [a, b] = pat.slitRow.map((q) => new V3(...q));
        along(a, b, pat.pitch ?? 3, (p, i, cnt) => {
          if (skip && jit(i, 1) < skip) return;
          const anim = pat.chase ? { period: pat.chase, duty: pat.duty ?? 0.25, phase: (pat.reverse ? i : cnt - 1 - i) / cnt, soft: 0.6 } : null;
          addSlit(p, u, n, { ...o, radiance: Array.isArray(pat.radiance) ? range(pat.radiance, jit(i, 6)) : pat.radiance, anim });
        });
      }
    }
  }

  // ---- automatic crease pins and recess slits -------------------------------------------------
  const cz = L.creases, sz = L.slits;
  if ((cz || sz) && meshes.length) {
    const angle = Math.min(cz?.angle ?? 35, sz?.angle ?? 35);
    const minLen = Math.min(cz?.minLen ?? 3, sz?.minLen ?? 2);
    const creases = hullCreases(meshes, { angle, minLen });
    // visit the creases in a shuffled (deterministic) order: the caps then thin the whole hull evenly
    // instead of spending every pin on the longest lofts; long creases still carry more runs
    const grid = creases.grid;
    const order = creases.map((e, i) => [hashP(e.a.clone().lerp(e.b, 0.5), seed + 61) / Math.sqrt(1 + e.len / 20), i]).sort((a, b) => a[0] - b[0]).map(([, i]) => creases[i]);
    order.grid = grid;
    // grilles and louvres: a family of short parallel creases at sub-metre pitch would otherwise count as dozens of
    // independent candidates (pins floating on vent slats); flag them and light only the family's end walls
    const louvre = L.louvre ?? cz?.louvre ?? { minFamily: 4, pitch: 1.0 };
    const vent = louvre ? louvreFamilies(creases, louvre) : new Set();
    stats.vent = vent.size;
    const zones = expandBoxes(L.zones);
    const settings = (p, base, key) => {
      for (const z of zones) if (inBox(p, z.box)) return z[key] === null ? null : { ...base, ...(z[key] || z) };
      return base;
    };
    const excluded = (p, s) => (s.exclude && expandBoxes(s.exclude).some((z) => inBox(p, z.box))) || (s.only && !expandBoxes(s.only).some((z) => inBox(p, z.box)));
    scapeCreases = { order, grid, vent, settings, excluded: (p, s) => excluded(p, s) };
    const engineNear = (p) => {
      for (const e of engines) {
        const d = p.clone().sub(e.p);
        const ax = d.dot(e.dir); // + behind the exit, - forward into the housing
        const rad = d.addScaledVector(e.dir, -ax).length();
        if (ax < 0.5 && ax > -e.radius * (L.cool?.depth ?? 3) && rad < e.radius * (L.cool?.radius ?? 1.8) && rad > e.radius * 1.02) return true;
      }
      return false;
    };
    if (cz) {
      let count = 0;
      const cap = cz.max ?? 400;
      const pinSpacer = new Spacer(cz.spacing ?? 1.2);
      for (const p of pins) pinSpacer.tryAdd(p.p, 0.3);
      for (let ci = 0; ci < order.length && count < cap; ci++) {
        const e = order[ci];
        if (!e.convex || vent.has(e)) continue;
        const mid = e.a.clone().lerp(e.b, 0.5);
        const s = settings(mid, cz, 'creases');
        if (!s || e.len < (s.minLen ?? 3) || e.sharp < ((s.angle ?? 35) * Math.PI) / 180) continue;
        const dir = e.b.clone().sub(e.a).normalize();
        // rank (effects.js distance thinning: lower survives longer): block corners are the last to go, the
        // pins along a crease's run the first, so a distant hull keeps its corner accents, not a uniform glitter
        const place = (p, rank) => {
          if (count >= cap) return;
          const s2 = settings(p, cz, 'creases');
          if (!s2 || excluded(p, s2)) return;
          const hp = hashP(p, seed);
          const q = p.clone().addScaledVector(e.n, s2.lift ?? 0.1);
          if (!grid.exposed(q, e.n, s2.clear ?? 0.4)) return;
          if (!pinSpacer.tryAdd(q, s2.spacing ?? 1.2)) return;
          const cool = L.cool && engineNear(q);
          const color = cool ? (L.cool.color || 'cool') : pick(s2.mix || { amber: 1 }, hp);
          addPin(q, { color, n: e.n, size: range(s2.size ?? [0.22, 0.34], hashP(p, seed + 3)), intensity: range(s2.intensity ?? [0.7, 1.0], hashP(p, seed + 5)) * (cool ? 0.9 : 1), blink: s2.blinkShare && hashP(p, seed + 9) < s2.blinkShare ? { period: range(s2.blinkPeriod ?? [2.2, 4.5], hashP(p, seed + 13)), duty: 0.5, phase: hashP(p, seed + 17), soft: 1 } : null, rank });
          count++;
        };
        // block corners: the crease's ends
        if ((s.corners ?? 0.5) > 0) for (const [end, sgn] of [[e.a, 1], [e.b, -1]]) if (hashP(end, seed + 21) < s.corners) place(end.clone().addScaledVector(dir, sgn * Math.min(0.5, e.len * 0.15)), 0.02 + 0.45 * hashP(end, seed + 23));
        // runs along the crease: at `pitch` m, each slot used with probability `share`, a run of 1-3 pins
        const pitch = s.pitch ?? 8, runPitch = s.runPitch ?? 1.2;
        const slots = Math.floor(e.len / pitch);
        for (let k = 0; k < slots; k++) {
          const t0 = (k + 0.5) * pitch;
          const p0 = e.a.clone().addScaledVector(dir, t0);
          if (hashP(p0, seed + 31) >= (s.share ?? 0.3)) continue;
          const [rmin, rmax] = s.run ?? [1, 3];
          const nrun = rmin + Math.floor(hashP(p0, seed + 37) * (rmax - rmin + 1));
          for (let j = 0; j < nrun; j++) {
            const t = t0 + (j - (nrun - 1) / 2) * runPitch;
            if (t < 0.3 || t > e.len - 0.3) continue;
            place(e.a.clone().addScaledVector(dir, t), 0.4 + 0.6 * hashP(p0, seed + 29 + j));
          }
        }
      }
    }
    if (sz) {
      let count = 0;
      const cap = sz.max ?? 60;
      const slitSpacer = new Spacer(sz.spacing ?? 6);
      // symmetric (default): candidates are drawn on the port side (x >= 0) and mirrored, so a lit recess is lit on
      // both flanks (the twin only where the hull really has the same recess); centreline recesses stay single
      const sym = sz.symmetric ?? true;
      const mirrored = (v) => new V3(-v.x, v.y, v.z);
      const surfaceBehind = (q, n, lift) => { const h = grid.cast(q, n.clone().negate(), lift + 0.3); return !!h; };
      for (let ci = 0; ci < order.length && count < cap; ci++) {
        const e = order[ci];
        if (e.convex || vent.has(e)) continue;
        const mid = e.a.clone().lerp(e.b, 0.5);
        const s = settings(mid, sz, 'slits');
        if (!s || e.len < (s.minLen ?? 2) || excluded(mid, s)) continue;
        if (e.sharp < ((s.angle ?? 60) * Math.PI) / 180) continue;
        const dir = e.b.clone().sub(e.a).normalize();
        // orientation (orient: false turns it off): the concept's bars stand upright in side-facing recesses; a
        // horizontal crease in an up- or down-facing corner is seen edge-on, and the keel's underside rarely at all
        const ny = e.n.y, orient = s.orient ?? true;
        const w = orient ? 1.3 * (0.55 + 0.45 * Math.abs(dir.y)) * (ny < -0.6 ? 0.3 : 1) * (1 - 0.5 * THREE.MathUtils.smoothstep(Math.abs(ny), 0.75, 0.95)) : 1;
        const every = s.every ?? 14; // long recess corners carry a few bars
        const nb = Math.max(1, Math.floor(e.len / every));
        for (let k = 0; k < nb && count < cap; k++) {
          const p = e.a.clone().addScaledVector(dir, ((k + 0.5) / nb) * e.len);
          const lift = s.lift ?? 0.06;
          const q = p.clone().addScaledVector(e.n, lift);
          if (sym && q.x < -0.3) continue; // drawn as the port twin's mirror
          if (hashP(sym ? new V3(Math.abs(p.x), p.y, p.z) : p, seed + 41) >= (s.share ?? 0.3) * w) continue;
          if (excluded(p, s)) continue;
          if (!grid.exposed(q, e.n, s.clear ?? 0.3)) continue;
          if (!slitSpacer.tryAdd(q, s.spacing ?? 6)) continue;
          const len = Math.min(range(s.len ?? [0.8, 2.2], hashP(p, seed + 47)), e.len * 0.8);
          const o = { len, width: s.width ?? 0.22, color: pick(s.mix || { amber: 1 }, hashP(p, seed + 53)), radiance: range(s.radiance ?? [1.2, 2.0], hashP(p, seed + 59)) };
          addSlit(q, dir, e.n, o);
          count++;
          if (sym && q.x > 0.3 && count < cap) {
            const q2 = mirrored(q), n2 = mirrored(e.n), p2 = mirrored(p);
            const s2 = settings(p2, sz, 'slits');
            if (s2 && !excluded(p2, s2) && surfaceBehind(q2, n2, lift) && grid.exposed(q2, n2, s2.clear ?? 0.3) && slitSpacer.tryAdd(q2, (s2.spacing ?? 6) * 0.5)) {
              addSlit(q2, mirrored(dir), n2, { ...o, color: pick(s2.mix || { amber: 1 }, hashP(p, seed + 53)) });
              count++;
            }
          }
        }
      }
    }
  }
  // ---- corner slits: the concept's signature accent ------------------------------------------------------
  // short upright bars set into a side- or end-facing plate just inside a vertical block edge, near the edge's top or
  // bottom end (sz.corner: { share, max, len, width, radiance, inset, mix } | null; default on wherever `slits` is)
  const cs = sz && sz.corner !== null ? { share: 0.45, len: [1.0, 1.8], inset: 0.35, ...(sz.corner || {}) } : null;
  if (cs && meshes.length && scapeCreases) {
    const { order, grid, vent, settings, excluded } = scapeCreases;
    const cap = cs.max ?? Math.round((sz.max ?? 60) * 0.8);
    let count = 0;
    const spacer = new Spacer(cs.spacing ?? Math.max(1.5, (sz.spacing ?? 6) * 0.5));
    for (const q of slits) spacer.tryAdd(q.p, 0.5);
    const sym = sz.symmetric ?? true;
    const tryCorner = (e, end, sgn, fA, fB, o, dry) => {
      const dir = e.b.clone().sub(e.a).normalize();
      let t = new V3().crossVectors(dir, fA).normalize();
      if (t.dot(fB) > 0) t.negate(); // across face A, away from the edge
      const q = end.clone().addScaledVector(dir, sgn * (o.len / 2 + 0.35)).addScaledVector(t, cs.inset).addScaledVector(fA, 0.04);
      const h = grid.cast(q, fA.clone().negate(), 0.35); // the plate is really there
      if (!h || !grid.exposed(q, fA, 0.3)) return null;
      return { q, dir, n: fA };
    };
    for (let ci = 0; ci < order.length && count < cap; ci++) {
      const e = order[ci];
      if (!e.convex || vent.has(e) || e.len < 2.2) continue;
      const dir = e.b.clone().sub(e.a).normalize();
      if (Math.abs(dir.y) < 0.7) continue;
      const mid = e.a.clone().lerp(e.b, 0.5);
      if (sym && mid.x < -0.3) continue;
      const s = settings(mid, sz, 'slits');
      if (!s || excluded(mid, s)) continue;
      const h0 = hashP(sym ? new V3(Math.abs(mid.x), mid.y, mid.z) : mid, seed + 71);
      if (h0 >= (s.corner?.share ?? cs.share)) continue;
      // the face that looks more sideways / endways carries the bar
      const [fA, fB] = Math.abs(e.nA.y) <= Math.abs(e.nB.y) ? [e.nA, e.nB] : [e.nB, e.nA];
      if (Math.abs(fA.y) > 0.5) continue;
      const top = hashP(mid, seed + 73) < 0.5;
      const [end, sgn] = (e.a.y > e.b.y) === top ? [e.a, 1] : [e.b, -1];
      const o = {
        len: Math.min(range(cs.len, hashP(mid, seed + 77)), e.len * 0.45), width: cs.width ?? s.width ?? 0.2,
        color: pick(cs.mix || s.mix || { amber: 1 }, hashP(mid, seed + 79)), radiance: range(cs.radiance ?? [1.4, 2.0], hashP(mid, seed + 83)),
      };
      const c = tryCorner(e, end, sgn, fA, fB, o);
      if (!c || !spacer.tryAdd(c.q)) continue;
      o.rank = 0.5 * hashP(new V3(Math.abs(c.q.x), c.q.y, c.q.z), seed + 89); // corner bars outlast recess bars far off
      addSlit(c.q, c.dir, c.n, o);
      count++;
      if (sym && c.q.x > 0.3 && count < cap) {
        const q2 = new V3(-c.q.x, c.q.y, c.q.z), n2 = new V3(-c.n.x, c.n.y, c.n.z);
        const h = grid.cast(q2, n2.clone().negate(), 0.35);
        if (h && grid.exposed(q2, n2, 0.3) && spacer.tryAdd(q2, 0.5)) { addSlit(q2, new V3(-c.dir.x, c.dir.y, c.dir.z), n2, o); count++; }
      }
    }
    stats.corner = count;
  }
  // phone tier (device.js LITE): about half of the pins and slits (animated and `keep` ones stay; nav lights are in `lights`)
  if (LITE) {
    const thin = (list) => list.filter((l, i) => l.keep || l.blink || l.anim || hash1(i, seed + 97) < 0.5);
    return { pins: thin(pins), slits: thin(slits), stats };
  }
  return { pins, slits, stats };
}

function mirrorPattern(p) {
  const m = (q) => [-q[0], q[1], q[2]];
  const out = { ...p, mirrorX: false, seed: (p.seed ?? 0) + 5003 };
  if (p.row) out.row = p.row.map(m);
  if (p.points) out.points = p.points.map(m);
  if (p.slit) out.slit = m(p.slit);
  if (p.slitRow) out.slitRow = p.slitRow.map(m);
  if (p.u) out.u = m(p.u);
  if (Array.isArray(p.n)) out.n = m(p.n); // (a ring's n is its lamp count, not a normal)
  if (p.ring) out.ring = { ...p.ring, c: m(p.ring.c), axis: p.ring.axis ? m(p.ring.axis) : undefined };
  if (p.surface) { out.surface = p.surface.replace(/port$/, '\u0000').replace(/stbd$/, 'port').replace('\u0000', 'stbd'); out.mirrorSurface = p.surface; }
  if (p.mirrorColor) out.color = p.mirrorColor;
  return out;
}

/** Creases that belong to a grille or louvre: transitive families of >= minFamily creases that are parallel (|dot| >
 *  0.98), of the same kind (convex / concave), similar in length (lenTol), facing the same way (bisectors within
 *  ~25 deg), side by side (midpoints within `pitch` m across, a quarter length along). cfg: { minFamily, pitch, lenTol }. */
export function louvreFamilies(creases, { minFamily = 4, pitch = 1.0, lenTol = 0.15 } = {}) {
  const info = creases.map((e) => ({ e, m: e.a.clone().lerp(e.b, 0.5), d: e.b.clone().sub(e.a).normalize() }));
  const cell = Math.max(pitch, 0.25);
  const cells = new Map();
  const key = (i, j, k) => `${i},${j},${k}`;
  info.forEach((c, i) => {
    const k = key(Math.floor(c.m.x / cell), Math.floor(c.m.y / cell), Math.floor(c.m.z / cell));
    if (!cells.has(k)) cells.set(k, []);
    cells.get(k).push(i);
  });
  const parent = info.map((_, i) => i);
  const find = (i) => { while (parent[i] !== i) { parent[i] = parent[parent[i]]; i = parent[i]; } return i; };
  const off = new V3();
  info.forEach((c, i) => {
    const ci = Math.floor(c.m.x / cell), cj = Math.floor(c.m.y / cell), ck = Math.floor(c.m.z / cell);
    for (let a = -1; a <= 1; a++) for (let b = -1; b <= 1; b++) for (let d = -1; d <= 1; d++) {
      for (const j of cells.get(key(ci + a, cj + b, ck + d)) || []) {
        if (j <= i) continue;
        const o = info[j];
        if (o.e.convex !== c.e.convex || Math.abs(o.d.dot(c.d)) < 0.98 || o.e.n.dot(c.e.n) < 0.9) continue;
        if (Math.abs(o.e.len - c.e.len) > lenTol * Math.max(o.e.len, c.e.len)) continue;
        off.subVectors(o.m, c.m);
        const al = off.dot(c.d);
        if (Math.abs(al) > 0.25 * c.e.len) continue;
        const perp = off.addScaledVector(c.d, -al).length();
        if (perp > pitch || perp < 0.02) continue;
        parent[find(j)] = find(i);
      }
    }
  });
  const size = new Map();
  info.forEach((_, i) => { const r = find(i); size.set(r, (size.get(r) || 0) + 1); });
  const out = new Set();
  info.forEach((c, i) => { if (size.get(find(i)) >= minFamily) out.add(c.e); });
  return out;
}
