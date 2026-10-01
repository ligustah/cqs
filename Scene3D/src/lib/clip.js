// Clip mesh geometry to a union of convex regions (the build state of a ship in a yard or a spaceport berth).
// A region is a list of half-spaces { n: [x, y, z], d }: keep where n . p <= d, p in the clip frame (`toFrame` maps the
// geometry's local space into it). Triangles are split along the planes (Sutherland-Hodgman, every attribute
// interpolated), so a cut is a straight line, not a ragged triangle edge.
//
// Memory (phone tier): the output grows in typed arrays, never in per-vertex JS objects or number arrays, and a mesh
// that lies wholly inside one region (or wholly outside all of them) is answered from its bounding box without copying
// its geometry. clipMesh() returns 'keep' | 'drop' | a new non-indexed BufferGeometry.
import * as THREE from 'three';

class Floats {
  constructor(n = 1 << 16) { this.a = new Float32Array(n); this.n = 0; }
  push(src, off, len) {
    if (this.n + len > this.a.length) { const b = new Float32Array(Math.max(this.a.length * 2, this.n + len)); b.set(this.a.subarray(0, this.n)); this.a = b; }
    for (let k = 0; k < len; k++) this.a[this.n++] = src[off + k];
  }
}

const _v = new THREE.Vector3();
const insideHalf = (h, p) => h.n[0] * p.x + h.n[1] * p.y + h.n[2] * p.z <= h.d + 1e-5;

/** Where a geometry's bounding box lies against the regions: 'in' (wholly inside one), 'out' (outside all), 'split'. */
export function boxSide(geom, toFrame, regions) {
  if (!geom.boundingBox) geom.computeBoundingBox();
  const b = geom.boundingBox;
  const corners = [];
  for (let i = 0; i < 8; i++) corners.push(new THREE.Vector3(i & 1 ? b.max.x : b.min.x, i & 2 ? b.max.y : b.min.y, i & 4 ? b.max.z : b.min.z).applyMatrix4(toFrame));
  if (regions.some((r) => corners.every((c) => r.every((h) => insideHalf(h, c))))) return 'in';
  // outside all: for every region some half-space has every corner beyond it (conservative: else 'split')
  if (regions.every((r) => r.some((h) => corners.every((c) => !insideHalf(h, c))))) return 'out';
  return 'split';
}

/** Clip one geometry; 'keep' (unchanged), 'drop' (nothing left) or a new non-indexed geometry. */
export function clipMesh(geom, toFrame, regions) {
  const side = boxSide(geom, toFrame, regions);
  if (side === 'in') return 'keep';
  if (side === 'out') return 'drop';
  const names = Object.keys(geom.attributes);
  const attrs = names.map((k) => geom.attributes[k]);
  const sizes = attrs.map((a) => a.itemSize);
  const stride = sizes.reduce((a, b) => a + b, 0) + 3; // attributes, then the clip-frame position
  const index = geom.index;
  const nTri = (index ? index.count : geom.attributes.position.count) / 3;
  const pos = geom.attributes.position;
  // one vertex record = its attributes (getComponent: interleaved / normalised / quantised data read as floats)
  const rec = (vi, o, off) => {
    let k = off;
    for (let j = 0; j < attrs.length; j++) for (let c = 0; c < sizes[j]; c++) o[k++] = attrs[j].getComponent(vi, c);
    _v.fromBufferAttribute(pos, vi).applyMatrix4(toFrame);
    o[k] = _v.x; o[k + 1] = _v.y; o[k + 2] = _v.z;
  };
  const dist = (h, o, off) => h.n[0] * o[off + stride - 3] + h.n[1] * o[off + stride - 2] + h.n[2] * o[off + stride - 1] - h.d;
  const out = new Floats(Math.min(1 << 22, nTri * 3 * stride));
  // scratch polygons: a triangle clipped by k planes has at most 3 + k vertices
  const MAXV = 3 + Math.max(...regions.map((r) => r.length));
  let polyA = new Float32Array(MAXV * stride), polyB = new Float32Array(MAXV * stride);
  const tri = new Float32Array(3 * stride);
  for (let t = 0; t < nTri; t++) {
    for (let k = 0; k < 3; k++) rec(index ? index.getX(t * 3 + k) : t * 3 + k, tri, k * stride);
    for (const r of regions) {
      let all = true;
      for (let k = 0; k < 3 && all; k++) for (const h of r) if (dist(h, tri, k * stride) > 1e-5) { all = false; break; }
      if (all) { out.push(tri, 0, 3 * stride); break; } // whole triangle in this region: kept once
      polyA.set(tri); let n = 3;
      for (const h of r) {
        if (n < 3) break;
        let m = 0;
        for (let i = 0; i < n; i++) {
          const a = i * stride, b = ((i + 1) % n) * stride;
          const da = dist(h, polyA, a), db = dist(h, polyA, b);
          if (da <= 0) { polyB.set(polyA.subarray(a, a + stride), m * stride); m++; }
          if ((da < 0 && db > 0) || (da > 0 && db < 0)) {
            const s = da / (da - db), o = m * stride;
            for (let q = 0; q < stride; q++) polyB[o + q] = polyA[a + q] + (polyA[b + q] - polyA[a + q]) * s;
            m++;
          }
        }
        [polyA, polyB] = [polyB, polyA]; n = m;
      }
      for (let i = 1; i + 1 < n; i++) { out.push(polyA, 0, stride); out.push(polyA, i * stride, stride); out.push(polyA, (i + 1) * stride, stride); }
    }
  }
  const nv = out.n / stride;
  if (!nv) return 'drop';
  const res = new THREE.BufferGeometry();
  let off = 0;
  names.forEach((k, j) => {
    const arr = new Float32Array(nv * sizes[j]);
    for (let i = 0; i < nv; i++) for (let c = 0; c < sizes[j]; c++) arr[i * sizes[j] + c] = out.a[i * stride + off + c];
    res.setAttribute(k, new THREE.BufferAttribute(arr, sizes[j]));
    off += sizes[j];
  });
  res.computeBoundingBox(); res.computeBoundingSphere();
  return res;
}
