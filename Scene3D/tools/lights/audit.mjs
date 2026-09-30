// audit: node audit.mjs <ship> [variant]  (env OV = override module path; env BOX = JSON box to split counts in/out)
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { MeshoptDecoder } from 'meshoptimizer';
import * as THREE from 'three';
import { fileURLToPath } from 'node:url';
const ROOT = fileURLToPath(new URL('../..', import.meta.url)).replace(/\/$/, '');
const [ship, variant] = process.argv.slice(2);
const base = await import(`${ROOT}/src/ships/${ship}.js?${Date.now()}`);
const { buildLightscape } = await import(`${ROOT}/src/lib/lightscape.js?${Date.now()}`);
let asset = { ...base.asset, ...(variant ? base.asset.variants?.[variant] || base.variants?.[variant] || {} : {}) };
asset = JSON.parse(JSON.stringify(asset));
if (process.env.OV) asset = (await import(process.env.OV + '?' + Date.now())).default(asset, variant);
const cfg = asset;
await MeshoptDecoder.ready;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.decoder': MeshoptDecoder });
const doc = await io.read(ROOT + '/' + cfg.glb.replace('./', ''));
const meshes = []; const box = new THREE.Box3();
for (const node of doc.getRoot().listNodes()) {
  const mesh = node.getMesh(); if (!mesh) continue;
  const M = new THREE.Matrix4().fromArray(node.getWorldMatrix());
  for (const p of mesh.listPrimitives()) {
    const pos = p.getAttribute('POSITION'); const idx = p.getIndices();
    const g = new THREE.BufferGeometry(); const arr = new Float32Array(pos.getCount() * 3); const t = [];
    for (let i = 0; i < pos.getCount(); i++) { pos.getElement(i, t); arr.set(t, i * 3); }
    g.setAttribute('position', new THREE.BufferAttribute(arr, 3)); if (idx) g.setIndex(new THREE.BufferAttribute(idx.getArray().slice(), 1));
    g.computeBoundingBox(); box.union(g.boundingBox.clone().applyMatrix4(M));
    if (node.getName() === 'hull' || node.getParentNode?.()?.getName?.() === 'hull') meshes.push({ geometry: g, M });
  }
}
const size = box.getSize(new THREE.Vector3()), c = box.getCenter(new THREE.Vector3());
const s = cfg.length / size.z;
const W = new THREE.Matrix4().makeScale(s, s, s).premultiply(new THREE.Matrix4().makeTranslation(-c.x * s, -c.y * s, -c.z * s));
const list = meshes.map((m) => ({ geometry: m.geometry, matrix: m.M.clone().premultiply(W) }));
const engines = (cfg.engines || []).flatMap((e) => (e.mirrorX ? [e, { ...e, p: [-e.p[0], e.p[1], e.p[2]] }] : [e])).map((e) => ({ p: new THREE.Vector3(...e.p), dir: new THREE.Vector3(...(e.dir || [0, 0, -1])), radius: e.radius }));
const r = buildLightscape(cfg, list, engines);
const ra = buildLightscape({ ...cfg, lightscape: { ...cfg.lightscape, patterns: [] } }, list, engines);
const lights = (cfg.lights || []).flatMap((l) => (l.mirrorX ? [l, { ...l, p: [-l.p[0], l.p[1], l.p[2]] }] : [l]));
const nav = lights.filter((l) => ['red', 'green', 'white'].includes(l.color) && !l.blink);
const BOX = process.env.BOX ? JSON.parse(process.env.BOX) : ship === 'carrier' ? [[-129.5, -98.5, -277], [129.5, -0.2, 421]] : null;
const inB = (q) => BOX && q.x >= BOX[0][0] && q.x <= BOX[1][0] && q.y >= BOX[0][1] && q.y <= BOX[1][1] && q.z >= BOX[0][2] && q.z <= BOX[1][2];
const port = (p) => /^port/.test(p.color);
const pins = r.pins.filter((p) => !port(p)), ports = r.pins.filter(port);
const out = (arr) => BOX ? arr.filter((p) => !inB(p.p)) : arr;
const col = {}; for (const p of r.pins) col[p.color] = (col[p.color] || 0) + 1;
const scol = {}; for (const p of r.slits) scol[p.color] = (scol[p.color] || 0) + 1;
const near = (q, d) => nav.some((l) => q.distanceTo(new THREE.Vector3(...l.p)) < d);
const mm = (a) => a.length ? `${Math.min(...a).toFixed(2)}-${Math.max(...a).toFixed(2)}` : '-';
const keepP = r.pins.filter((p) => p.keep).length, keepS = r.slits.filter((p) => p.keep).length;
const lcol = {}; for (const l of lights) lcol[l.color.startsWith('#') ? 'hex' : l.color] = (lcol[l.color.startsWith('#') ? 'hex' : l.color] || 0) + 1;
console.log(`${ship}${variant ? ':' + variant : ''} lamps ${pins.length + r.slits.length} = pins ${pins.length} (auto ${ra.pins.length}) + bars ${r.slits.length} (auto ${ra.slits.length}) | portPts ${ports.length} | keep ${keepP}p+${keepS}b | lights[] ${lights.length} ${JSON.stringify(lcol)}`);
console.log(`  pin colours ${JSON.stringify(col)} bar colours ${JSON.stringify(scol)}`);
console.log(`  pin size ${mm(pins.map((p) => p.size))} bar width ${mm(r.slits.map((p) => p.width))} bar len ${mm(r.slits.map((p) => p.len))}`);
console.log(`  within 3 m of steady nav: pins ${pins.filter((p) => near(p.p, 3)).length} bars ${r.slits.filter((p) => near(p.p, 3)).length}; within 2 m: ${pins.filter((p) => near(p.p, 2)).length + r.slits.filter((p) => near(p.p, 2)).length}`);
if (BOX) console.log(`  outside BOX: pins ${out(pins).length} bars ${out(r.slits).length} ports ${out(ports).length}; inside: pins ${pins.length - out(pins).length} bars ${r.slits.length - out(r.slits).length}`);
// ---- STANDARD.md budgets and rules (v14) ----
const HANGAR = [[-129.5, -98.5, -277], [129.5, -0.2, 421]]; // the hangar zone out to just inside the flank plating (x 130.98): the open bays are interior
const inH = (q) => q.x >= HANGAR[0][0] && q.x <= HANGAR[1][0] && q.y >= HANGAR[0][1] && q.y <= HANGAR[1][1] && q.z >= HANGAR[0][2] && q.z <= HANGAR[1][2];
const B = {
  fighter: { lamps: [26, 34], bars: [16, 22], keep: 8, lights: 5, big: false },
  corvette: { lamps: [115, 145], bars: [55, 70], keep: 16, lights: 5, big: false },
  freighter: { lamps: [160, 195], bars: [45, 60], keep: 16, lights: 8, big: false },
  'freighter:troops': { lamps: [160, 195], bars: [45, 60], keep: 16, lights: 8, big: false },
  destroyer: { lamps: [205, 250], bars: [60, 75], keep: 24, lights: 7, big: true },
  carrier: { lamps: [550, 800], bars: [150, 200], keep: 60, lights: 29, big: true, hangar: [650, 900] },
}[ship + (variant ? ':' + variant : '')];
if (B) {
  const ext = (p) => !(ship === 'carrier' && inH(p.p));
  const eP = pins.filter(ext), eS = r.slits.filter(ext);
  const fails = [];
  const chk = (ok, msg) => { if (!ok) fails.push(msg); };
  const lamps = eP.length + eS.length;
  chk(lamps >= B.lamps[0] && lamps <= B.lamps[1], `lamps ${lamps} outside ${B.lamps}${ship === 'carrier' ? ' (exterior)' : ''}`);
  chk(eS.length >= B.bars[0] && eS.length <= B.bars[1], `bars ${eS.length} outside ${B.bars}`);
  if (B.hangar) { const h = r.pins.length - ports.length - eP.length + r.slits.length - eS.length; chk(h >= B.hangar[0] && h <= B.hangar[1], `hangar lamps ${h} outside ${B.hangar}`); }
  const keep = r.pins.filter((p) => p.keep).length + r.slits.filter((p) => p.keep).length;
  chk(keep <= B.keep, `keep ${keep} > ${B.keep}`);
  chk(lights.length <= B.lights, `lights[] ${lights.length} > ${B.lights}`);
  chk(lights.every((l) => ['red', 'green', 'white'].includes(l.color) && l.size >= 0.25 && l.size <= 0.45), 'lights[] holds a non-nav colour or a size outside 0.25-0.45');
  chk(ports.every((p) => !p.keep), 'a window point is keep');
  const warm = [...eP, ...eS].filter((p) => p.color === "warm");
  if (process.env.WARM) for (const w of warm) console.log("  warm", w.p.x.toFixed(1), w.p.y.toFixed(1), w.p.z.toFixed(1), w.len ? "bar" : "pin");
  chk(warm.length === 0, `${warm.length} warm exterior lamps`);
  chk(pins.every((p) => p.size <= 0.3 + 1e-6 && p.size >= 0.16 - 1e-6), `pin size outside 0.16-0.30: ${mm(pins.map((p) => p.size))}`);
  chk(ra.pins.every((p) => p.size >= 0.2 - 1e-6 && p.size <= 0.28 + 1e-6), `automatic pin size outside 0.20-0.28: ${mm(ra.pins.map((p) => p.size))}`);
  chk(ra.slits.every((p) => Math.abs(p.width - 0.2) <= 0.02 + 1e-6), `automatic bar width outside 0.18-0.22: ${mm(ra.slits.map((p) => p.width))}`);
  const wmax = B.big ? 0.3 : 0.22;
  chk(r.slits.every((p) => p.width <= wmax + 1e-6 && p.width >= 0.12 - 1e-6), `bar width outside 0.12-${wmax}: ${mm(r.slits.map((p) => p.width))}`);
  chk(r.slits.every((p) => p.len / p.width >= 3.5 - 1e-6), 'a bar under 3.5:1');
  const nearNav = [...pins, ...r.slits].filter((p) => near(p.p, 2)).length;
  chk(nearNav === 0, `${nearNav} lamps within 2 m of a steady nav light`);
  console.log(fails.length ? `  FAIL: ${fails.join('; ')}` : '  PASS (STANDARD.md budgets and fixture rules)');
}
process.exit(0);
