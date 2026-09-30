// node cellcut.mjs <ship> [variant] <cell> <phase> [parts=port,pane,portlite]
// counts kit glass panes whose ship-frame box is crossed by a livery compartment boundary (cell = floor(p / C + phase))
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { MeshoptDecoder } from 'meshoptimizer';
import * as THREE from 'three';
import { fileURLToPath } from 'node:url';
const ROOT = fileURLToPath(new URL('../..', import.meta.url)).replace(/\/$/, '');
const a = process.argv.slice(2);
const ship = a[0]; const variant = /^[a-z]/i.test(a[1]) ? a[1] : null; const rest = variant ? a.slice(2) : a.slice(1);
const arr = (t) => (t.includes(',') ? t.split(',').map(Number) : [+t, +t, +t]);
const C = arr(rest[0]), PH = arr(rest[1]); const parts = (rest[2] || 'port,pane,portlite').split(',');
const EX = process.env.EX ? JSON.parse(process.env.EX) : [];
const LINK = +(process.env.LINK || 0.6);
const base = await import(`${ROOT}/src/ships/${ship}.js?${Date.now()}`);
const cfg = { ...base.asset, ...(variant ? base.variants?.[variant] || {} : {}) };
await MeshoptDecoder.ready;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.decoder': MeshoptDecoder });
const doc = await io.read(ROOT + '/' + cfg.glb.replace('./', ''));
const box = new THREE.Box3(); const tris = [];
for (const node of doc.getRoot().listNodes()) {
  const mesh = node.getMesh(); if (!mesh) continue;
  const M = new THREE.Matrix4().fromArray(node.getWorldMatrix());
  const nm = node.getName() || node.getParentNode?.()?.getName?.() || '';
  const part = parts.find((p) => nm === 'parts_' + p);
  for (const p of mesh.listPrimitives()) {
    const pos = p.getAttribute('POSITION'); const t = []; const idx = p.getIndices()?.getArray();
    const mat = p.getMaterial()?.getName() || '';
    const V = []; for (let i = 0; i < pos.getCount(); i++) { pos.getElement(i, t); const v = new THREE.Vector3(...t).applyMatrix4(M); box.expandByPoint(v); V.push(v); }
    if (!part) continue;
    // glass faces only: small, flat triangles; the portlite has its own glass material, the kit port / pane a glass zone
    if (part === 'portlite' && !/glass/.test(mat)) continue;
    const n = idx ? idx.length : V.length;
    for (let i = 0; i < n; i += 3) tris.push([V[idx ? idx[i] : i], V[idx ? idx[i + 1] : i + 1], V[idx ? idx[i + 2] : i + 2]]);
  }
}
const size = box.getSize(new THREE.Vector3()), c = box.getCenter(new THREE.Vector3());
const s = cfg.length / size.z;
const W = new THREE.Matrix4().makeScale(s, s, s).premultiply(new THREE.Matrix4().makeTranslation(-c.x * s, -c.y * s, -c.z * s));
// cluster triangles into panes: link by shared 0.25 m cells of their centroids
const cell = LINK; const map = new Map(); const pts = tris.map((t) => t.map((v) => v.clone().applyMatrix4(W)));
const key = (v) => `${Math.floor(v.x / cell)},${Math.floor(v.y / cell)},${Math.floor(v.z / cell)}`;
pts.forEach((t, i) => { for (const v of t) { const k = key(v); if (!map.has(k)) map.set(k, []); map.get(k).push(i); } });
const par = pts.map((_, i) => i); const f = (i) => { while (par[i] !== i) i = par[i] = par[par[i]]; return i; };
for (const l of map.values()) for (const i of l) par[f(i)] = f(l[0]);
const g = new Map(); pts.forEach((t, i) => { const r = f(i); if (!g.has(r)) g.set(r, new THREE.Box3()); for (const v of t) g.get(r).expandByPoint(v); });
const panes = [...g.values()].filter((b) => { const sz = b.getSize(new THREE.Vector3()); return Math.max(sz.x, sz.y, sz.z) < 3.0; });
const cuts = (lo, hi, i) => { const k0 = Math.floor(lo / C[i] + PH[i]); const b = C[i] * (k0 + 1 - PH[i]); return b < hi - 0.02 && b > lo + 0.02; };
const SH = +(process.env.SHRINK ?? 0.2);
for (const b of panes) { const sz = b.getSize(new THREE.Vector3()); const th = Math.min(sz.x, sz.y, sz.z); for (const ax of ['x','y','z']) if (sz[ax] > th + 1e-6 && sz[ax] > 2 * SH + 0.1) { b.min[ax] += SH; b.max[ax] -= SH; } }
const inEx = (b) => EX.some(([m, M]) => b.min.x >= m[0] && b.max.x <= M[0] && b.min.y >= m[1] && b.max.y <= M[1] && b.min.z >= m[2] && b.max.z <= M[2]);
const list = panes.filter((b) => !inEx(b));
if (process.env.SEARCH) {
  const out = [];
  for (const [i, ax] of [[0, 'x'], [1, 'y'], [2, 'z']]) {
    const best = [];
    for (let c = 3.0; c <= 8.0001; c += 0.05) for (let ph = 0; ph < 1; ph += 0.01) {
      let n = 0, m = 1e9;
      for (const b of list) { const lo = b.min[ax], hi = b.max[ax]; const k0 = Math.floor(lo / c + ph); for (let k = k0 - 1; k <= k0 + 2; k++) { const bb = c * (k - ph); if (bb > lo + 0.02 && bb < hi - 0.02) n++; m = Math.min(m, bb > lo && bb < hi ? 0 : Math.min(Math.abs(bb - lo), Math.abs(bb - hi))); } }
      if (n === 0) best.push([+m.toFixed(3), +c.toFixed(2), +ph.toFixed(2)]);
    }
    best.sort((a, b) => b[0] - a[0] || Math.abs(a[1] - 5) - Math.abs(b[1] - 5));
    const near5 = best.filter((q) => q[1] >= 4.5 && q[1] <= 6.5).slice(0, 3);
    console.log(ax, 'zero-cut (margin, cell, phase) best:', JSON.stringify(best.slice(0, 3)), 'cell 4.5-6.5:', JSON.stringify(near5));
  }
}
let n = 0; for (const b of list) if (cuts(b.min.x, b.max.x, 0) || cuts(b.min.y, b.max.y, 1) || cuts(b.min.z, b.max.z, 2)) n++;
if (process.env.DUMP) for (const b of list) console.log(b.min.toArray().map((v)=>v.toFixed(2)).join(','), b.max.toArray().map((v)=>v.toFixed(2)).join(','));
console.log(`${ship}${variant ? ':' + variant : ''} cell ${C} phase ${PH}: ${n} of ${list.length} glass pieces cut by a compartment boundary (${panes.length - list.length} excluded)`);
process.exit(0);
