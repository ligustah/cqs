// Optimise a generated GLB for the web scene (the "take high poly, optimise,
// re-bake" step of the asset pipeline, done with glTF-Transform instead of Blender):
// dedup + weld, simplify to a triangle budget, resize textures and encode them as
// WebP, then meshopt-compress the geometry.
//
//   node tools/optimize-glb.mjs in.glb out.glb [--tris 150000] [--tex 2048]
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { dedup, prune, weld, simplify, textureCompress, meshopt } from '@gltf-transform/functions';
import { MeshoptSimplifier, MeshoptEncoder, MeshoptDecoder } from 'meshoptimizer';
import sharp from 'sharp';
import { stat } from 'node:fs/promises';

const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf(`--${k}`); if (i < 0) return d; const v = args[i + 1]; args.splice(i, 2); return v; };
const targetTris = parseInt(opt('tris', '150000'));
const texSize = parseInt(opt('tex', '2048'));
const [input, output] = args;
if (!input || !output) { console.error('usage: optimize-glb.mjs in.glb out.glb [--tris N] [--tex N]'); process.exit(2); }

await Promise.all([MeshoptSimplifier.ready, MeshoptEncoder.ready, MeshoptDecoder.ready]);
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({
  'meshopt.encoder': MeshoptEncoder, 'meshopt.decoder': MeshoptDecoder,
});

const doc = await io.read(input);
const countTris = () => {
  let n = 0;
  for (const mesh of doc.getRoot().listMeshes()) for (const p of mesh.listPrimitives()) {
    const idx = p.getIndices();
    n += (idx ? idx.getCount() : p.getAttribute('POSITION').getCount()) / 3;
  }
  return Math.round(n);
};
const before = countTris();
const ratio = Math.min(1, targetTris / Math.max(1, before));

await doc.transform(
  dedup(),
  prune(),
  weld(),
  ...(ratio < 1 ? [simplify({ simplifier: MeshoptSimplifier, ratio, error: 0.002, lockBorder: false })] : []),
  textureCompress({ encoder: sharp, targetFormat: 'webp', resize: [texSize, texSize], quality: 88 }),
  meshopt({ encoder: MeshoptEncoder, level: 'medium' }),
);
await io.write(output, doc);
const [a, b] = await Promise.all([stat(input), stat(output)]);
console.log(`${input}: ${before} tris, ${(a.size / 1e6).toFixed(1)} MB -> ${output}: ${countTris()} tris, ${(b.size / 1e6).toFixed(1)} MB`);
