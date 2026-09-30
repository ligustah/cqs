// Ray casts on the hull: env R=[[[x,y,z],[nx,ny,nz]],...] node tools/lights/raycast.mjs <ship>  (casts from p+3n along -n; prints hit + face normal)
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

const R=JSON.parse(process.env.R||"[]");
const rc=new THREE.Raycaster(); const objs=list.map(m=>{const o=new THREE.Mesh(m.geometry,new THREE.MeshBasicMaterial({side:THREE.DoubleSide})); o.matrixAutoUpdate=false; o.matrix.copy(m.matrix); o.matrixWorld.copy(m.matrix); return o;});
for(const [p,n] of R){const P=new THREE.Vector3(...p), N=new THREE.Vector3(...n).normalize(); rc.set(P.clone().addScaledVector(N,3),N.clone().negate()); rc.far=8; const h=rc.intersectObjects(objs,false)[0];
 console.log("RAY",p.join(","),"->",h?[h.point.x.toFixed(2),h.point.y.toFixed(2),h.point.z.toFixed(2)].join(",")+" d="+(h.distance-3).toFixed(2)+" fn="+h.face.normal.clone().transformDirection(h.object.matrixWorld).toArray().map(v=>v.toFixed(2)).join(","):"MISS");}
process.exit(0);
