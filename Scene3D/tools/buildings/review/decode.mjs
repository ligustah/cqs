// decode.mjs <in.glb> <out.glb>: meshopt + quantization -> plain float GLB (run with cwd = Scene3D)
import { createRequire } from 'module';
import { pathToFileURL } from 'url';
const req = createRequire(process.cwd() + '/');
const imp = (m) => import(pathToFileURL(req.resolve(m)).href);
const { NodeIO } = await imp('@gltf-transform/core');
const { ALL_EXTENSIONS } = await imp('@gltf-transform/extensions');
const { dequantize } = await imp('@gltf-transform/functions');
const { MeshoptDecoder } = await imp('meshoptimizer');
await MeshoptDecoder.ready;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.decoder': MeshoptDecoder });
const doc = await io.read(process.argv[2]);
await doc.transform(dequantize());
for (const e of doc.getRoot().listExtensionsUsed()) if (/meshopt|quantization/.test(e.extensionName)) e.dispose();
await io.write(process.argv[3], doc);
console.log('ok');
