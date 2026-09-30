// Uniform-scale normaliser for the parts kit (parts2). Same steps as v7/parts/normalize.mjs, but ONE scale factor.
//   node normalize2.mjs raw.glb out.glb --rot rx,ry,rz --key <spec> --anchor back|base|foot|bell|join [--tex 1024] [--tris N]
// rot: degrees, R = Rz*Ry*Rx (front to +Z, up to +Y; for the bell: exit to -Z).
// key: uniform scale so that one measured dimension hits a target:
//   x:8 | y:4 | z:10      bbox extent along that axis
//   max:3                 largest bbox extent
//   footx:8               x extent of the vertices in the lowest 12 % of the height (turret barbette)
//   exitr:2.2             exit radius of a bell whose exit plane is at z min (vertices within 3 % of zmin)
// anchor: back -> x,y centred, zmin = 0;  base -> x,z centred, ymin = 0;
//         foot -> x,z centred on the foot (lowest 12 %), ymin = 0;  bell -> x,y centred on the exit ring, zmin = 0 then
//         flipped so the exit plane is z = 0 and the bell runs to -Z (the input rot must put the exit at z MAX);
//         join -> x centred, ymin = 0, zmin = 0 (railgun muzzle: joining face at z = 0, extends +Z)
//         seg  -> x centred, ymin = 0, z centred (tileable railgun segment)
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { dedup, prune, weld, simplify, textureCompress, meshopt, flatten, clearNodeTransform, transformMesh, getBounds } from '@gltf-transform/functions';
import { MeshoptSimplifier, MeshoptEncoder, MeshoptDecoder } from 'meshoptimizer';
import sharp from 'sharp';

const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf(`--${k}`); if (i < 0) return d; const v = args[i + 1]; args.splice(i, 2); return v; };
const rot = opt('rot', '0,0,0').split(',').map(Number);
const [keyK, keyV] = opt('key', 'max:1').split(':');
const anchor = opt('anchor', 'back');
const tex = parseInt(opt('tex', '1024'));
const tris = parseInt(opt('tris', '0'));
const [input, output] = args;

await Promise.all([MeshoptSimplifier.ready, MeshoptEncoder.ready, MeshoptDecoder.ready]);
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.encoder': MeshoptEncoder, 'meshopt.decoder': MeshoptDecoder });
const doc = await io.read(input);
const root = doc.getRoot();
await doc.transform(flatten());
for (const n of root.listNodes()) if (n.getMesh()) clearNodeTransform(n);
const scene = root.getDefaultScene() || root.listScenes()[0];

const mul = (a, b) => { const o = new Array(16).fill(0); for (let c = 0; c < 4; c++) for (let r = 0; r < 4; r++) for (let k = 0; k < 4; k++) o[c * 4 + r] += a[k * 4 + r] * b[c * 4 + k]; return o; };
const rx = (d) => { const t = (d * Math.PI) / 180, c = Math.cos(t), s = Math.sin(t); return [1, 0, 0, 0, 0, c, s, 0, 0, -s, c, 0, 0, 0, 0, 1]; };
const ry = (d) => { const t = (d * Math.PI) / 180, c = Math.cos(t), s = Math.sin(t); return [c, 0, -s, 0, 0, 1, 0, 0, s, 0, c, 0, 0, 0, 0, 1]; };
const rz = (d) => { const t = (d * Math.PI) / 180, c = Math.cos(t), s = Math.sin(t); return [c, s, 0, 0, -s, c, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]; };
const meshes = root.listMeshes();
const apply = (m) => { for (const mesh of meshes) transformMesh(mesh, m); };
const verts = () => { const out = []; for (const mesh of meshes) for (const p of mesh.listPrimitives()) { const a = p.getAttribute('POSITION'); const v = [0, 0, 0]; for (let i = 0; i < a.getCount(); i++) { a.getElement(i, v); out.push([...v]); } } return out; };
const box = (vs) => { const mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9]; for (const v of vs) for (let i = 0; i < 3; i++) { mn[i] = Math.min(mn[i], v[i]); mx[i] = Math.max(mx[i], v[i]); } return { mn, mx }; };

apply(mul(rz(rot[2]), mul(ry(rot[1]), rx(rot[0]))));
const V = verts();
const { mn: min, mx: max } = box(V);
const ext = [0, 1, 2].map((i) => max[i] - min[i]);
const foot = box(V.filter((v) => v[1] < min[1] + 0.12 * ext[1]));
const ring = V.filter((v) => v[2] > max[2] - 0.03 * ext[2]); // exit plane at z max before the bell flip
const ringBox = box(ring);
const ringC = [(ringBox.mn[0] + ringBox.mx[0]) / 2, (ringBox.mn[1] + ringBox.mx[1]) / 2];
const ringR = ring.reduce((m, v) => Math.max(m, Math.hypot(v[0] - ringC[0], v[1] - ringC[1])), 0);

let measured;
if (keyK === 'x' || keyK === 'y' || keyK === 'z') measured = ext['xyz'.indexOf(keyK)];
else if (keyK === 'max') measured = Math.max(...ext);
else if (keyK === 'footx') measured = foot.mx[0] - foot.mn[0];
else if (keyK === 'exitr') measured = ringR;
else throw new Error('bad key ' + keyK);
const s = Number(keyV) / measured;

const c = [0, 1, 2].map((i) => (min[i] + max[i]) / 2);
let t = [-c[0] * s, -c[1] * s, -c[2] * s];
if (anchor === 'back') t[2] = -min[2] * s;
if (anchor === 'base') t[1] = -min[1] * s;
if (anchor === 'foot') t = [-(foot.mn[0] + foot.mx[0]) / 2 * s, -min[1] * s, -(foot.mn[2] + foot.mx[2]) / 2 * s];
if (anchor === 'join') { t[1] = -min[1] * s; t[2] = -min[2] * s; }
if (anchor === 'seg') t[1] = -min[1] * s;
if (anchor === 'front') t[2] = -max[2] * s;
if (anchor === 'bell') t = [-ringC[0] * s, -ringC[1] * s, -max[2] * s];
apply([s, 0, 0, 0, 0, s, 0, 0, 0, 0, s, 0, t[0], t[1], t[2], 1]);
const bb = getBounds(scene);

const countTris = () => { let n = 0; for (const mesh of root.listMeshes()) for (const p of mesh.listPrimitives()) { const idx = p.getIndices(); n += (idx ? idx.getCount() : p.getAttribute('POSITION').getCount()) / 3; } return Math.round(n); };
const before = countTris();
const ratio = tris ? Math.min(1, tris / before) : 1;
await doc.transform(
  dedup(), prune(), weld(),
  ...(ratio < 1 ? [simplify({ simplifier: MeshoptSimplifier, ratio, error: 0.001, lockBorder: false })] : []),
  textureCompress({ encoder: sharp, targetFormat: 'webp', resize: [tex, tex], quality: 88 }),
  meshopt({ encoder: MeshoptEncoder, level: 'medium' }),
);
await io.write(output, doc);
const r3 = (a) => a.map((v) => +v.toFixed(3));
console.log(JSON.stringify({ input, output, key: `${keyK}:${keyV}`, measuredRaw: +measured.toFixed(4), scale: +s.toFixed(4), rawExtent: r3(ext),
  foot: { w: +((foot.mx[0] - foot.mn[0]) * s).toFixed(3), d: +((foot.mx[2] - foot.mn[2]) * s).toFixed(3) },
  bbox: { min: r3(bb.min), max: r3(bb.max) }, size: [0, 1, 2].map((i) => +(bb.max[i] - bb.min[i]).toFixed(3)), trisBefore: before, tris: countTris() }));
