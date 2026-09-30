// Normalise a raw fal/Tripo part GLB into the parts-kit mount frame.
//   node normalize.mjs raw.glb out.glb --rot rx,ry,rz --size w,h,d --anchor back|base|backbase [--tex 1024] [--tris N]
// rot: degrees, applied X then Y then Z (intrinsic via matrix R = Rz*Ry*Rx) to bring the part's front to +Z and up to +Y.
// size: target bbox in metres; '-' marks a free axis (scaled by the mean factor of the given axes).
// anchor: back     -> x,y centred, z min = 0 (mounting face is the back, normal +Z)
//         base     -> x,z centred, y min = 0 (stands on its foot, normal +Y)
//         backbase -> x centred, y min = 0, z min = 0 (wall ladder)
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { dedup, prune, weld, simplify, textureCompress, meshopt, flatten, clearNodeTransform, transformMesh, getBounds } from '@gltf-transform/functions';
import { MeshoptSimplifier, MeshoptEncoder, MeshoptDecoder } from 'meshoptimizer';
import sharp from 'sharp';

const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf(`--${k}`); if (i < 0) return d; const v = args[i + 1]; args.splice(i, 2); return v; };
const rot = opt('rot', '0,0,0').split(',').map(Number);
const size = opt('size', '-,-,-').split(',').map((v) => (v === '-' ? null : Number(v)));
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

// column-major mat4 helpers
const mul = (a, b) => { const o = new Array(16).fill(0); for (let c = 0; c < 4; c++) for (let r = 0; r < 4; r++) for (let k = 0; k < 4; k++) o[c * 4 + r] += a[k * 4 + r] * b[c * 4 + k]; return o; };
const rx = (d) => { const t = (d * Math.PI) / 180, c = Math.cos(t), s = Math.sin(t); return [1, 0, 0, 0, 0, c, s, 0, 0, -s, c, 0, 0, 0, 0, 1]; };
const ry = (d) => { const t = (d * Math.PI) / 180, c = Math.cos(t), s = Math.sin(t); return [c, 0, -s, 0, 0, 1, 0, 0, s, 0, c, 0, 0, 0, 0, 1]; };
const rz = (d) => { const t = (d * Math.PI) / 180, c = Math.cos(t), s = Math.sin(t); return [c, s, 0, 0, -s, c, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]; };
const meshes = root.listMeshes();
const apply = (m) => { for (const mesh of meshes) transformMesh(mesh, m); };

apply(mul(rz(rot[2]), mul(ry(rot[1]), rx(rot[0]))));
let { min, max } = getBounds(scene);
const ext = [0, 1, 2].map((i) => max[i] - min[i]);
const given = [0, 1, 2].filter((i) => size[i] != null);
const f = [0, 1, 2].map((i) => (size[i] != null ? size[i] / ext[i] : null));
const mean = given.reduce((s, i) => s + f[i], 0) / given.length;
const S = f.map((v) => v ?? mean);
const c = [0, 1, 2].map((i) => (min[i] + max[i]) / 2);
const t = [-c[0] * S[0], -c[1] * S[1], -c[2] * S[2]];
if (anchor === 'back' || anchor === 'backbase') t[2] = -min[2] * S[2];
if (anchor === 'base' || anchor === 'backbase') t[1] = -min[1] * S[1];
apply([S[0], 0, 0, 0, 0, S[1], 0, 0, 0, 0, S[2], 0, t[0], t[1], t[2], 1]);
({ min, max } = getBounds(scene));

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
console.log(JSON.stringify({ input, output, rawExtent: ext.map((v) => +v.toFixed(4)), scale: S.map((v) => +v.toFixed(4)), bbox: { min: min.map((v) => +v.toFixed(3)), max: max.map((v) => +v.toFixed(3)) }, size: [0, 1, 2].map((i) => +(max[i] - min[i]).toFixed(3)), trisBefore: before, tris: countTris() }));
