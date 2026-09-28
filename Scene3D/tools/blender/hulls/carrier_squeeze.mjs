// The carrier's GLB budget pass (after assemble.py's optimize-glb.mjs): the 900 m hull's 8192 base colour
// and the kit textures re-encoded so the whole ship stays under ~11 MB.
//
//   node tools/blender/hulls/carrier_squeeze.mjs in.glb out.glb [--base-q 80] [--orm 2048] [--parts 1024] [--parts-q 82]
//
// base colour 'base': WebP at --base-q (size kept); hull ORM 'orm': resized to --orm; kit / fal part textures
// (every other image): resized to at most --parts, except --keep (turret-L, bell-XL: 2048 kept, q84). The hull's tangent-space 'normal' is left alone.
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { meshopt } from '@gltf-transform/functions';
import { MeshoptEncoder, MeshoptDecoder } from 'meshoptimizer';
import sharp from 'sharp';
import { stat } from 'node:fs/promises';

const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf(`--${k}`); if (i < 0) return d; const v = args[i + 1]; args.splice(i, 2); return v; };
const baseQ = parseInt(opt('base-q', '80')), ormSize = parseInt(opt('orm', '2048'));
const partSize = parseInt(opt('parts', '1024')), partQ = parseInt(opt('parts-q', '82'));
// the big machinery (34 m turrets, 38 m bells) keeps its 2048 kit textures: at 1024 they read as flat CG
const KEEP = (opt('keep', 'turret-L,bell-XL')).split(',');
const [input, output] = args;
await Promise.all([MeshoptEncoder.ready, MeshoptDecoder.ready]);
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.encoder': MeshoptEncoder, 'meshopt.decoder': MeshoptDecoder });
const doc = await io.read(input);
for (const t of doc.getRoot().listTextures()) {
  const name = t.getName() || t.getURI() || '';
  const img = t.getImage();
  if (!img) continue;
  const meta = await sharp(Buffer.from(img)).metadata();
  let pipe = sharp(Buffer.from(img));
  let q = partQ;
  if (name === 'base') q = baseQ;
  else if (name === 'normal') continue;
  else if (name === 'orm') { if (meta.width > ormSize) pipe = pipe.resize(ormSize, ormSize); q = 88; }
  else if (KEEP.some((k) => name.startsWith(k + '_'))) q = 84;
  else if (meta.width > partSize) pipe = pipe.resize(partSize, Math.round(partSize * meta.height / meta.width));
  const out = await pipe.webp({ quality: q, effort: 5 }).toBuffer();
  if (out.length < img.byteLength || name === 'orm') { t.setImage(new Uint8Array(out)); t.setMimeType('image/webp'); }
  console.log(`${name.padEnd(48)} ${meta.width}x${meta.height} ${(img.byteLength / 1e3).toFixed(0)} kB -> ${(Math.min(out.length, img.byteLength) / 1e3).toFixed(0)} kB`);
}
await doc.transform(meshopt({ encoder: MeshoptEncoder, level: 'medium' }));
await io.write(output, doc);
const [a, b] = await Promise.all([stat(input), stat(output)]);
console.log(`${input}: ${(a.size / 1e6).toFixed(2)} MB -> ${output}: ${(b.size / 1e6).toFixed(2)} MB`);
