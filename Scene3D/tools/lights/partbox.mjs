// node partbox.mjs <ship> [variant] <partName>: ship-frame bbox clusters of a kit part's vertices (1.5 m linkage)
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { MeshoptDecoder } from 'meshoptimizer';
import * as THREE from 'three';
import { fileURLToPath } from 'node:url';
const ROOT = fileURLToPath(new URL('../..', import.meta.url)).replace(/\/$/, '');
const args = process.argv.slice(2); const ship = args[0]; const part = args[args.length - 1]; const variant = args.length > 2 ? args[1] : null;
const base = await import(`${ROOT}/src/ships/${ship}.js?${Date.now()}`);
const cfg = { ...base.asset, ...(variant ? base.variants?.[variant] || {} : {}) };
await MeshoptDecoder.ready;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.decoder': MeshoptDecoder });
const doc = await io.read(ROOT + '/' + cfg.glb.replace('./', ''));
const box = new THREE.Box3(); const pts = [];
for (const node of doc.getRoot().listNodes()) {
  const mesh = node.getMesh(); if (!mesh) continue;
  const M = new THREE.Matrix4().fromArray(node.getWorldMatrix());
  const isPart = node.getName() === 'parts_' + part || node.getParentNode?.()?.getName?.() === 'parts_' + part;
  for (const p of mesh.listPrimitives()) {
    const pos = p.getAttribute('POSITION'); const t = [];
    for (let i = 0; i < pos.getCount(); i++) { pos.getElement(i, t); const v = new THREE.Vector3(...t).applyMatrix4(M); box.expandByPoint(v); if (isPart && i % 3 === 0) pts.push(v); }
  }
}
const size = box.getSize(new THREE.Vector3()), c = box.getCenter(new THREE.Vector3());
const s = cfg.length / size.z;
const W = new THREE.Matrix4().makeScale(s, s, s).premultiply(new THREE.Matrix4().makeTranslation(-c.x * s, -c.y * s, -c.z * s));
const P = pts.map((v) => v.applyMatrix4(W));
// cluster on a 1.5 m grid (union-find by cell adjacency)
const cell = 1.5, key = (v) => [Math.floor(v.x / cell), Math.floor(v.y / cell), Math.floor(v.z / cell)];
const cells = new Map(); P.forEach((v) => { const k = key(v).join(','); if (!cells.has(k)) cells.set(k, new THREE.Box3()); cells.get(k).expandByPoint(v); });
const ks = [...cells.keys()]; const par = new Map(ks.map((k) => [k, k])); const f = (k) => { while (par.get(k) !== k) k = par.get(k); return k; };
for (const k of ks) { const [i, j, l] = k.split(',').map(Number); for (let a = -1; a <= 1; a++) for (let b = -1; b <= 1; b++) for (let d = -1; d <= 1; d++) { const n = `${i + a},${j + b},${l + d}`; if (cells.has(n)) par.set(f(n), f(k)); } }
const groups = new Map(); for (const k of ks) { const r = f(k); if (!groups.has(r)) groups.set(r, new THREE.Box3()); groups.get(r).union(cells.get(k)); }
const r2 = (x) => Math.round(x * 100) / 100;
for (const g of [...groups.values()].sort((a, b) => b.min.z - a.min.z)) console.log(JSON.stringify([[r2(g.min.x), r2(g.min.y), r2(g.min.z)], [r2(g.max.x), r2(g.max.y), r2(g.max.z)]]));
process.exit(0);
