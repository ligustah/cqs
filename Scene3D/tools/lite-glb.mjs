// Lite (mobile) copy of a GLB: the same geometry and nodes, every texture downscaled to at
// most --tex pixels (WebP), meshopt kept. Used by build-artifact.mjs for the phone tier.
//   node tools/lite-glb.mjs in.glb out.glb [--tex 1024]
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { textureCompress, meshopt } from '@gltf-transform/functions';
import { MeshoptEncoder, MeshoptDecoder } from 'meshoptimizer';
import sharp from 'sharp';

const args = process.argv.slice(2);
const i = args.indexOf('--tex');
const tex = i < 0 ? 1024 : parseInt(args.splice(i, 2)[1]);
const [input, output] = args;
if (!input || !output) { console.error('usage: lite-glb.mjs in.glb out.glb [--tex N]'); process.exit(2); }

await Promise.all([MeshoptEncoder.ready, MeshoptDecoder.ready]);
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.encoder': MeshoptEncoder, 'meshopt.decoder': MeshoptDecoder });
const doc = await io.read(input);
await doc.transform(
  textureCompress({ encoder: sharp, targetFormat: 'webp', resize: [tex, tex], quality: 85 }),
  meshopt({ encoder: MeshoptEncoder, level: 'medium' }),
);
await io.write(output, doc);
