// Light dump: node tools/lights/dump.mjs <ship> [troops]; env Q=[[x0,y0,z0],[x1,y1,z1]] lists every pin / slit in that box (ship frame, m)
// node test: build the lightscape for a ship module straight from its GLB; stats + side/top scatter SVG
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { MeshoptDecoder } from 'meshoptimizer';
import * as THREE from 'three';
import { fileURLToPath } from 'node:url';
const ROOT = fileURLToPath(new URL('../..', import.meta.url)).replace(/\/$/, '');
import sharp from 'sharp';
const [ship, variant] = process.argv.slice(2);
const mod = await import(`${ROOT}/src/ships/${ship}.js?${Date.now()}`);
const { buildLightscape } = await import(`${ROOT}/src/lib/lightscape.js?${Date.now()}`);
const cfg = { ...mod.asset, ...(variant ? mod.variants[variant] : {}) };
await MeshoptDecoder.ready;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.decoder': MeshoptDecoder });
const doc = await io.read(ROOT + '/' + cfg.glb.replace('./', ''));
const meshes = []; const box = new THREE.Box3();
for (const node of doc.getRoot().listNodes()) {
  const mesh = node.getMesh(); if (!mesh) continue;
  const M = new THREE.Matrix4().fromArray(node.getWorldMatrix());
  for (const p of mesh.listPrimitives()) {
    const pos = p.getAttribute('POSITION'); const idx = p.getIndices();
    const g = new THREE.BufferGeometry();
    const arr = new Float32Array(pos.getCount() * 3); const t = [];
    for (let i = 0; i < pos.getCount(); i++) { pos.getElement(i, t); arr.set(t, i * 3); }
    g.setAttribute('position', new THREE.BufferAttribute(arr, 3));
    if (idx) g.setIndex(new THREE.BufferAttribute(idx.getArray().slice(), 1));
    g.computeBoundingBox(); box.union(g.boundingBox.clone().applyMatrix4(M));
    if (node.getName() === 'hull' || node.getParentNode?.()?.getName?.() === 'hull') meshes.push({ geometry: g, M, name: node.getName() });
  }
}
const size = box.getSize(new THREE.Vector3()), c = box.getCenter(new THREE.Vector3());
const s = cfg.length / size.z;
const W = new THREE.Matrix4().makeScale(s, s, s).premultiply(new THREE.Matrix4().makeTranslation(-c.x * s, -c.y * s, -c.z * s));
const list = meshes.map((m) => ({ geometry: m.geometry, matrix: m.M.clone().premultiply(W) }));
const engines = (cfg.engines || []).flatMap((e) => (e.mirrorX ? [e, { ...e, p: [-e.p[0], e.p[1], e.p[2]] }] : [e])).map((e) => ({ p: new THREE.Vector3(...e.p), dir: new THREE.Vector3(...(e.dir || [0, 0, -1])), radius: e.radius }));
const t0 = Date.now();
const r = buildLightscape(cfg, list, engines);
const ms = Date.now() - t0;
const byC = {}; for (const p of r.pins) byC[p.color] = (byC[p.color] || 0) + 1;
console.log(JSON.stringify(r.stats), ship + (variant ? ':' + variant : ''), 'hullMeshes', list.length, 'pins', r.pins.length, 'slits', r.slits.length, 'ms', ms, JSON.stringify(byC));

const Q=JSON.parse(process.env.Q||"null");
const inQ=(q)=>q.x>=Q[0][0]&&q.x<=Q[1][0]&&q.y>=Q[0][1]&&q.y<=Q[1][1]&&q.z>=Q[0][2]&&q.z<=Q[1][2];
if(Q){for(const p of r.pins){const q=p.p; if(inQ(q)) console.log("PIN",q.x.toFixed(2),q.y.toFixed(2),q.z.toFixed(2),p.color,(p.size||0).toFixed(2),(p.rank??-1).toFixed(2),p.blink?"blink":"");}
for(const p of r.slits){const q=p.p; if(inQ(q)) console.log("SLIT",q.x.toFixed(2),q.y.toFixed(2),q.z.toFixed(2),"u",p.u.x.toFixed(2),p.u.y.toFixed(2),p.u.z.toFixed(2),"n",p.n.x.toFixed(2),p.n.y.toFixed(2),p.n.z.toFixed(2),"len",p.len.toFixed(2),"w",p.width,"rad",p.radiance.toFixed(2),p.color,p.keep?"keep":"");}}
process.exit(0);
