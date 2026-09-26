// Geometry kit + ShipBuilder shared by all ship designs.
//
// Conventions (ship space, metres):
//   +Z = bow (forward), -Z = stern, +Y = dorsal (up), +X = port side viewer-left
//   when looking from the stern. Ships are built at real size in metres.
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { mergeGeometries, toCreasedNormals } from 'three/addons/utils/BufferGeometryUtils.js';
import { makeRng } from './rng.js';

const V3 = THREE.Vector3;
const DEG = Math.PI / 180;

// ---------------------------------------------------------------------------
// Cross-section generators. Every section is an array of N [x, y] points,
// ordered counter-clockwise when seen from +Z, starting at the top (x=0, y>0).
// Sections with the same N can be lofted together.
// ---------------------------------------------------------------------------
export const section = {
  /** Superellipse: n=2 ellipse, n=4..8 increasingly boxy rounded rectangle. */
  superellipse(w, h, n = 2, N = 48, { dy = 0, dx = 0 } = {}) {
    const pts = [];
    for (let i = 0; i < N; i++) {
      const t = Math.PI / 2 + (i / N) * Math.PI * 2;
      const c = Math.cos(t), s = Math.sin(t);
      const x = (w / 2) * Math.sign(c) * Math.abs(c) ** (2 / n);
      const y = (h / 2) * Math.sign(s) * Math.abs(s) ** (2 / n);
      pts.push([x + dx, y + dy]);
    }
    return pts;
  },
  ellipse(w, h, N = 48, opts) { return section.superellipse(w, h, 2, N, opts); },
  /** Arbitrary polygon (CCW from +Z) resampled to N points, corners preserved. */
  polygon(poly, N = 48) {
    const P = poly.map((p) => [p[0], p[1]]);
    if (signedArea(P) < 0) P.reverse();
    // rotate so the vertex closest to the +Y axis comes first
    let best = 0, bestScore = -Infinity;
    P.forEach((p, i) => { const s = p[1] - Math.abs(p[0]) * 4; if (s > bestScore) { bestScore = s; best = i; } });
    const Q = P.slice(best).concat(P.slice(0, best));
    const lens = Q.map((p, i) => Math.hypot(Q[(i + 1) % Q.length][0] - p[0], Q[(i + 1) % Q.length][1] - p[1]));
    const total = lens.reduce((a, b) => a + b, 0);
    const counts = lens.map((l) => Math.max(1, Math.round((l / total) * N)));
    let diff = N - counts.reduce((a, b) => a + b, 0);
    while (diff !== 0) {
      let idx = 0;
      if (diff > 0) { idx = lens.indexOf(Math.max(...lens.map((l, i) => l / counts[i]))); }
      else { let m = -1; counts.forEach((c, i) => { if (c > 1 && (m < 0 || lens[i] / c < lens[m] / counts[m])) m = i; }); idx = m; }
      counts[idx] += Math.sign(diff); diff -= Math.sign(diff);
    }
    const out = [];
    Q.forEach((p, i) => {
      const q = Q[(i + 1) % Q.length];
      for (let k = 0; k < counts[i]; k++) { const t = k / counts[i]; out.push([p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t]); }
    });
    return out;
  },
  /** Rectangle with chamfered corners (c = chamfer length), centred. */
  chamferRect(w, h, c = 0.2, N = 48, { dy = 0, cTop = c, cBottom = c } = {}) {
    const x = w / 2, y = h / 2;
    const poly = [
      [x - cTop, y], [-x + cTop, y], [-x, y - cTop], [-x, -y + cBottom], [-x + cBottom, -y], [x - cBottom, -y], [x, -y + cBottom], [x, y - cTop],
    ].map(([a, b]) => [a, b + dy]);
    return section.polygon(dedupe(poly), N);
  },
  /** Trapezoid: top width wt, bottom width wb. Optional chamfer. */
  trapezoid(wt, wb, h, N = 48, { c = 0, dy = 0 } = {}) {
    const t = wt / 2, b = wb / 2, y = h / 2;
    const poly = c > 0
      ? [[t - c, y], [-t + c, y], [-t, y - c], [-b, -y + c], [-b + c, -y], [b - c, -y], [b, -y + c], [t, y - c]]
      : [[t, y], [-t, y], [-b, -y], [b, -y]];
    return section.polygon(dedupe(poly.map(([a, q]) => [a, q + dy])), N);
  },
  /** Scale / offset an existing section. */
  transform(sec, { sx = 1, sy = 1, dx = 0, dy = 0 } = {}) {
    return sec.map(([x, y]) => [x * sx + dx, y * sy + dy]);
  },
  /** Linear blend between two sections with equal N. */
  lerp(a, b, t) { return a.map((p, i) => [p[0] + (b[i][0] - p[0]) * t, p[1] + (b[i][1] - p[1]) * t]); },
};

function dedupe(poly) {
  return poly.filter((p, i) => { const q = poly[(i + 1) % poly.length]; return Math.hypot(p[0] - q[0], p[1] - q[1]) > 1e-6; });
}
function signedArea(P) {
  let a = 0;
  for (let i = 0; i < P.length; i++) { const p = P[i], q = P[(i + 1) % P.length]; a += p[0] * q[1] - q[0] * p[1]; }
  return a / 2;
}

// ---------------------------------------------------------------------------
// Geometry primitives (all closed solids unless noted).
// ---------------------------------------------------------------------------
export const geo = {
  /**
   * Loft through cross-sections placed along Z.
   * stations: [{ z, sec }] (sec from `section`), sorted by z (stern -> bow).
   * A station with a degenerate section (all points equal) makes a pointed tip.
   * opts.crease: crease angle in degrees for normals (default 35). 0 = smooth.
   */
  loft(stations, { crease = 35, capStart = true, capEnd = true } = {}) {
    const N = stations[0].sec.length;
    const S = stations.length;
    const pos = [];
    for (const st of stations) for (const [x, y] of st.sec) pos.push(x, y, st.z);
    const idx = [];
    for (let s = 0; s < S - 1; s++) {
      for (let i = 0; i < N; i++) {
        const a = s * N + i, b = s * N + ((i + 1) % N), c = (s + 1) * N + i, d = (s + 1) * N + ((i + 1) % N);
        // sections are CCW seen from +Z; this winding gives outward normals
        idx.push(a, b, d, a, d, c);
      }
    }
    const addCap = (s, flip) => {
      const cx = stations[s].sec.reduce((m, p) => m + p[0], 0) / N;
      const cy = stations[s].sec.reduce((m, p) => m + p[1], 0) / N;
      const ci = pos.length / 3;
      pos.push(cx, cy, stations[s].z);
      for (let i = 0; i < N; i++) {
        const a = s * N + i, b = s * N + ((i + 1) % N);
        if (flip) idx.push(ci, b, a); else idx.push(ci, a, b);
      }
    };
    if (capStart) addCap(0, true);
    if (capEnd) addCap(S - 1, false);
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    g.setIndex(idx);
    return finishNormals(g, crease);
  },

  /** Straight prism of a section between z0 and z1. */
  prism(sec, z0, z1, opts) { return geo.loft([{ z: z0, sec }, { z: z1, sec }], opts); },

  /** Box centred at origin. r > 0 gives rounded edges. */
  box(w, h, d, r = 0, seg = 2) {
    if (r > 0) return new RoundedBoxGeometry(w, h, d, seg, Math.min(r, w / 2, h / 2, d / 2) * 0.999);
    return new THREE.BoxGeometry(w, h, d);
  },

  /** Cylinder along Z, centred. */
  cylinder(rBack, rFront, len, seg = 32, { open = false } = {}) {
    const g = new THREE.CylinderGeometry(rFront, rBack, len, seg, 1, open);
    g.rotateX(Math.PI / 2);
    return g;
  },

  sphere(r, seg = 32, { sx = 1, sy = 1, sz = 1 } = {}) {
    const g = new THREE.SphereGeometry(r, seg, Math.max(8, seg >> 1));
    g.scale(sx, sy, sz);
    return g;
  },

  /** Capsule along Z. */
  capsule(r, len, seg = 24) {
    const g = new THREE.CapsuleGeometry(r, len, 8, seg);
    g.rotateX(Math.PI / 2);
    return g;
  },

  /**
   * Solid of revolution around Z. profile: [[r, z], ...] from stern to bow.
   * Start/end points with r=0 close the solid.
   */
  lathe(profile, seg = 48, { crease = 40 } = {}) {
    const pts = profile.map(([r, z]) => new THREE.Vector2(Math.max(r, 1e-4), z));
    const g = new THREE.LatheGeometry(pts, seg);
    // Lathe revolves around +Y; map (x, y, z) -> (x, -z, y) so the axis is +Z
    g.rotateX(Math.PI / 2);
    g.deleteAttribute('normal');
    const merged = mergeVerticesSimple(g);
    return finishNormals(merged, crease);
  },

  /**
   * Engine bell with wall thickness (closed solid). Exit faces -Z.
   * The throat sits at z=0, exit at z=-len.
   */
  nozzle({ rThroat = 0.5, rExit = 1.0, len = 1.4, wall = 0.06, seg = 40, flare = 1.6 } = {}) {
    const prof = [];
    const n = 12;
    for (let i = 0; i <= n; i++) { const t = i / n; prof.push([rThroat + (rExit - rThroat) * t ** flare + wall, -len * t]); }
    for (let i = n; i >= 0; i--) { const t = i / n; prof.push([rThroat + (rExit - rThroat) * t ** flare, -len * t + (i === n ? 0.001 : 0)]); }
    prof.push(prof[0]);
    return geo.lathe(prof.map(([r, z]) => [r, z]).reverse(), seg, { crease: 70 });
  },

  /** Parabolic dish (open shell, keep out of envelope if tiny). Faces +Z. */
  dish(r, depth, seg = 32) {
    const prof = [];
    for (let i = 0; i <= 10; i++) { const t = i / 10; prof.push([r * t, depth * t * t]); }
    for (let i = 10; i >= 0; i--) { const t = i / 10; prof.push([r * t, depth * t * t - 0.04 * r]); }
    return geo.lathe(prof.reverse(), seg, { crease: 60 });
  },

  /** Tube along a polyline/curve (open ends). */
  pipe(points, radius, { tubular = 48, radial = 10, closed = false } = {}) {
    const curve = new THREE.CatmullRomCurve3(points.map((p) => new V3(...p)), closed, 'centripetal');
    return new THREE.TubeGeometry(curve, tubular, radius, radial, closed);
  },

  /** Wedge: loft of two chamfered rectangles of different size. */
  wedge({ len, wBack, hBack, wFront, hFront, cBack = 0, cFront = 0, dyFront = 0, N = 32, crease = 35 }) {
    return geo.loft([
      { z: -len / 2, sec: section.chamferRect(wBack, hBack, cBack, N) },
      { z: len / 2, sec: section.chamferRect(wFront, hFront, cFront, N, { dy: dyFront }) },
    ], { crease });
  },

  /**
   * Open lattice truss along Z between z0 and z1 with square cross-section.
   * Returns one merged geometry (chords + diagonals).
   */
  truss({ z0, z1, width = 2, bays = 8, chord = 0.12, strut = 0.06 }) {
    const parts = [];
    const L = z1 - z0, h = width / 2;
    const corners = [[-h, -h], [h, -h], [h, h], [-h, h]];
    for (const [x, y] of corners) { const c = geo.box(chord, chord, L); c.translate(x, y, z0 + L / 2); parts.push(c); }
    const bay = L / bays;
    const beam = (a, b, r) => {
      const va = new V3(...a), vb = new V3(...b);
      const len = va.distanceTo(vb);
      const g = new THREE.CylinderGeometry(r, r, len, 6);
      g.translate(0, len / 2, 0);
      const q = new THREE.Quaternion().setFromUnitVectors(new V3(0, 1, 0), vb.clone().sub(va).normalize());
      g.applyQuaternion(q); g.translate(va.x, va.y, va.z);
      parts.push(g);
    };
    for (let i = 0; i <= bays; i++) {
      const z = z0 + i * bay;
      for (let k = 0; k < 4; k++) { const [x0, y0] = corners[k], [x1, y1] = corners[(k + 1) % 4]; beam([x0, y0, z], [x1, y1, z], strut); }
      if (i < bays) for (let k = 0; k < 4; k++) {
        const [x0, y0] = corners[k], [x1, y1] = corners[(k + 1) % 4];
        if ((i + k) % 2) beam([x0, y0, z], [x1, y1, z + bay], strut); else beam([x1, y1, z], [x0, y0, z + bay], strut);
      }
    }
    return mergeAll(parts);
  },

  /**
   * Scatter small mechanical boxes ("greebles") on a rectangular patch of a
   * surface. The patch lies in the plane y = `y` (facing +Y); use the builder
   * transform to put it on other faces.
   */
  greebles({ seed = 1, x0, x1, z0, z1, y = 0, count = 30, min = 0.15, max = 0.6, hMin = 0.05, hMax = 0.3 }) {
    const rng = makeRng(seed);
    const parts = [];
    for (let i = 0; i < count; i++) {
      const w = rng.range(min, max), d = rng.range(min, max) * rng.range(0.6, 2.2), hgt = rng.range(hMin, hMax);
      const x = rng.range(x0 + w / 2, x1 - w / 2), z = rng.range(z0 + d / 2, z1 - d / 2);
      const g = rng.chance(0.2) ? geo.cylinder(w / 2, w / 2, hgt, 10) : geo.box(w, hgt, d);
      if (rng.chance(0.2) && g.type === 'CylinderGeometry') g.rotateX(Math.PI / 2);
      g.translate(x, y + hgt / 2, z);
      parts.push(g);
    }
    return mergeAll(parts);
  },

  /** Flat plate (for decals / markings) facing +Y, w along X, d along Z. */
  plate(w, d, t = 0.01) { return new THREE.BoxGeometry(w, t, d); },

  /** Extrude a 2D outline (in XY) along Z by `depth`, centred. Bevel optional. */
  extrude(outline, depth, { bevel = 0, bevelSegments = 1, curveSegments = 12 } = {}) {
    const shape = new THREE.Shape(outline.map(([x, y]) => new THREE.Vector2(x, y)));
    const g = new THREE.ExtrudeGeometry(shape, {
      depth, bevelEnabled: bevel > 0, bevelThickness: bevel, bevelSize: bevel, bevelSegments, curveSegments,
    });
    g.translate(0, 0, -depth / 2);
    return g;
  },
};

function finishNormals(g, crease) {
  if (crease > 0) {
    const out = toCreasedNormals(g, crease * DEG);
    return out;
  }
  g.computeVertexNormals();
  return g;
}

// Weld duplicated seam vertices (Lathe) so smooth normals don't split.
function mergeVerticesSimple(g) {
  const pos = g.getAttribute('position');
  const map = new Map(), remap = new Array(pos.count);
  const out = [];
  for (let i = 0; i < pos.count; i++) {
    const k = `${pos.getX(i).toFixed(5)},${pos.getY(i).toFixed(5)},${pos.getZ(i).toFixed(5)}`;
    if (!map.has(k)) { map.set(k, out.length / 3); out.push(pos.getX(i), pos.getY(i), pos.getZ(i)); }
    remap[i] = map.get(k);
  }
  const src = g.getIndex();
  const idx = [];
  for (let i = 0; i < src.count; i += 3) {
    const a = remap[src.getX(i)], b = remap[src.getX(i + 1)], c = remap[src.getX(i + 2)];
    if (a !== b && b !== c && a !== c) idx.push(a, b, c);
  }
  const r = new THREE.BufferGeometry();
  r.setAttribute('position', new THREE.Float32BufferAttribute(out, 3));
  r.setIndex(idx);
  return r;
}

export function mergeAll(geoms) {
  const prepared = geoms.map(normalizeForMerge);
  return mergeGeometries(prepared, false);
}

function normalizeForMerge(g) {
  let h = g.index ? g.toNonIndexed() : g.clone();
  for (const name of Object.keys(h.attributes)) if (!['position', 'normal', 'uv'].includes(name)) h.deleteAttribute(name);
  if (!h.getAttribute('normal')) h.computeVertexNormals();
  if (!h.getAttribute('uv')) h.setAttribute('uv', new THREE.Float32BufferAttribute(new Float32Array(h.getAttribute('position').count * 2), 2));
  h.morphAttributes = {};
  h.clearGroups();
  return h;
}

// ---------------------------------------------------------------------------
// ShipBuilder
// ---------------------------------------------------------------------------
/**
 * Collects parts, bakes transforms, box-projects UVs in metres, merges parts
 * by material, and records effect anchors (engines, lights, hangar...).
 *
 *   const b = new ShipBuilder('destroyer', mat, { uvScale: 6 });
 *   b.add(geo.box(4, 2, 10), 'hull', { p: [0, 1, 0] });
 *   b.add(wing, 'accent', { p: [3, 0, -2], mirrorX: true });
 *   b.engine({ p: [0, 0, -20], radius: 1.6 });
 *   b.light({ p: [6, 0, 0], color: 'green' });
 *   return b.finish({ role: 'Escort destroyer', ... });
 */
export class ShipBuilder {
  constructor(name, palette, { uvScale = 4 } = {}) {
    this.name = name;
    this.mat = palette;
    this.uvScale = uvScale;
    this.parts = [];
    this.engines = [];
    this.lights = [];
    this.anchors = {};
  }

  /**
   * Add a part.
   *  material: palette key (string) or a THREE.Material.
   *  opts.p  position [x,y,z]; opts.r Euler degrees [x,y,z]; opts.s scale (number or [x,y,z])
   *  opts.mirrorX  also add a copy mirrored across the X=0 plane
   *  opts.envelope false -> excluded from the hangar envelope (tiny antennas etc.)
   *  opts.shadow false -> does not cast shadows (glows, decals)
   *  opts.uvScale override metres per texture tile for this part
   */
  add(geometry, material, opts = {}) {
    const m = typeof material === 'string' ? this.mat[material] : material;
    if (!m) throw new Error(`${this.name}: unknown material '${material}'`);
    const matrix = composeMatrix(opts);
    this.parts.push({ geometry, material: m, matrix, opts });
    if (opts.mirrorX) {
      const mirror = new THREE.Matrix4().makeScale(-1, 1, 1).multiply(matrix);
      this.parts.push({ geometry, material: m, matrix: mirror, opts });
    }
    return this;
  }

  /** Register an engine exhaust. dir defaults to -Z. Adds a glowing core disc. */
  engine({ p, radius = 1, dir = [0, 0, -1], color = null, length = null, mirrorX = false, core = true }) {
    const add = (pp) => {
      this.engines.push({ p: new V3(...pp), dir: new V3(...dir).normalize(), radius, color, length: length ?? radius * 6 });
      if (core) {
        const d = new V3(...dir).normalize();
        const disc = geo.cylinder(radius, radius, radius * 0.08, 32);
        const q = new THREE.Quaternion().setFromUnitVectors(new V3(0, 0, -1), d);
        const e = new THREE.Euler().setFromQuaternion(q);
        this.add(disc, 'engine', { p: pp, r: [e.x / DEG, e.y / DEG, e.z / DEG], shadow: false, envelope: false });
      }
    };
    add(p);
    if (mirrorX) add([-p[0], p[1], p[2]]);
    return this;
  }

  /**
   * Navigation / running light. color: 'red' | 'green' | 'white' | 'amber' | 'cyan' | hex.
   * blink: null (steady) or { period (s), duty (0..1), phase (0..1) }.
   */
  light({ p, color = 'white', size = 0.3, blink = null, mirrorX = false, mirrorColor = null }) {
    this.lights.push({ p: new V3(...p), color, size, blink });
    if (mirrorX) this.lights.push({ p: new V3(-p[0], p[1], p[2]), color: mirrorColor ?? color, size, blink });
    return this;
  }

  /** Named anchor for scene choreography (e.g. 'hangarMouth', 'bridge'). */
  anchor(name, p, extra = {}) { this.anchors[name] = { p: new V3(...p), ...extra }; return this; }

  finish(info = {}) {
    const byMat = new Map();
    const envelope = new THREE.Box3();
    let triangles = 0;
    for (const part of this.parts) {
      let g = normalizeForMerge(part.geometry);
      g.applyMatrix4(part.matrix);
      if (part.matrix.determinant() < 0) flipWinding(g);
      boxProjectUV(g, part.opts.uvScale ?? this.uvScale);
      if (part.opts.envelope !== false && !isEmissive(part.material)) {
        g.computeBoundingBox();
        envelope.union(g.boundingBox);
      }
      triangles += g.getAttribute('position').count / 3;
      const key = part.material.uuid + (part.opts.shadow === false ? ':ns' : '');
      if (!byMat.has(key)) byMat.set(key, { material: part.material, shadow: part.opts.shadow !== false, geoms: [] });
      byMat.get(key).geoms.push(g);
    }
    const group = new THREE.Group();
    group.name = this.name;
    for (const { material, shadow, geoms } of byMat.values()) {
      const merged = mergeGeometries(geoms, false);
      merged.computeBoundingSphere();
      const mesh = new THREE.Mesh(merged, material);
      mesh.name = `${this.name}:${material.name || 'mat'}`;
      mesh.castShadow = shadow && !isEmissive(material) && !material.transparent;
      mesh.receiveShadow = !isEmissive(material);
      group.add(mesh);
    }
    const size = envelope.getSize(new V3());
    const center = envelope.getCenter(new V3());
    group.userData.ship = {
      name: this.name,
      ...info,
      envelope: { min: envelope.min.clone(), max: envelope.max.clone(), size, center },
      envelopeVolume: size.x * size.y * size.z,
      engines: this.engines,
      lights: this.lights,
      anchors: this.anchors,
      triangles,
      drawCalls: group.children.length,
    };
    return group;
  }
}

function isEmissive(m) {
  return m.emissive && m.emissiveIntensity > 2 && m.color && m.color.getHex() === 0;
}

function composeMatrix({ p = [0, 0, 0], r = [0, 0, 0], s = 1 } = {}) {
  const sc = Array.isArray(s) ? new V3(...s) : new V3(s, s, s);
  const q = new THREE.Quaternion().setFromEuler(new THREE.Euler(r[0] * DEG, r[1] * DEG, r[2] * DEG, 'XYZ'));
  return new THREE.Matrix4().compose(new V3(...p), q, sc);
}

function flipWinding(g) {
  const pos = g.getAttribute('position'), nor = g.getAttribute('normal'), uv = g.getAttribute('uv');
  for (let i = 0; i < pos.count; i += 3) {
    for (const a of [pos, nor, uv]) {
      if (!a) continue;
      for (let k = 0; k < a.itemSize; k++) {
        const t = a.array[(i + 1) * a.itemSize + k];
        a.array[(i + 1) * a.itemSize + k] = a.array[(i + 2) * a.itemSize + k];
        a.array[(i + 2) * a.itemSize + k] = t;
      }
    }
  }
}

// Box (tri-planar) projection in ship space: panels keep a constant size in
// metres across every part of every ship.
function boxProjectUV(g, scale) {
  const pos = g.getAttribute('position'), nor = g.getAttribute('normal');
  const uv = g.getAttribute('uv');
  // choose one projection axis per triangle (from its face normal) to avoid smearing
  const a = new V3(), b = new V3(), c = new V3(), n = new V3();
  for (let i = 0; i < pos.count; i += 3) {
    a.fromBufferAttribute(pos, i); b.fromBufferAttribute(pos, i + 1); c.fromBufferAttribute(pos, i + 2);
    n.subVectors(c, b).cross(a.clone().sub(b)).normalize();
    if (!Number.isFinite(n.x)) n.fromBufferAttribute(nor, i);
    const ax = Math.abs(n.x), ay = Math.abs(n.y), az = Math.abs(n.z);
    for (let k = 0; k < 3; k++) {
      const x = pos.getX(i + k), y = pos.getY(i + k), z = pos.getZ(i + k);
      let u, v;
      if (ay >= ax && ay >= az) { u = x; v = z; }
      else if (ax >= az) { u = z; v = y; }
      else { u = x; v = y; }
      uv.setXY(i + k, u / scale, v / scale);
    }
  }
  uv.needsUpdate = true;
}

export { V3, DEG };
