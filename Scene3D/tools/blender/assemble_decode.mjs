// Decode a web GLB (meshopt / quantized geometry) into a plain GLB that Blender's glTF importer
// reads (it has no EXT_meshopt_compression / KHR_mesh_quantization decoder). Textures are kept
// as they are (Blender imports EXT_texture_webp). Used by tools/blender/assemble.py.
//   node tools/blender/assemble_decode.mjs in.glb out.glb [in2.glb out2.glb ...]
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { dequantize } from '@gltf-transform/functions';
import { MeshoptDecoder, MeshoptEncoder } from 'meshoptimizer';

const args = process.argv.slice(2);
if (!args.length || args.length % 2) { console.error('usage: assemble_decode.mjs in.glb out.glb [...]'); process.exit(2); }
await Promise.all([MeshoptDecoder.ready, MeshoptEncoder.ready]);
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.decoder': MeshoptDecoder, 'meshopt.encoder': MeshoptEncoder });
for (let i = 0; i < args.length; i += 2) {
  const doc = await io.read(args[i]);
  for (const ext of doc.getRoot().listExtensionsUsed()) {
    if (['EXT_meshopt_compression', 'KHR_mesh_quantization'].includes(ext.extensionName)) ext.dispose();
  }
  await doc.transform(dequantize());
  await io.write(args[i + 1], doc);
}
