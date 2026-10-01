// Phone-tier copy of a GLB: the same nodes, every texture downscaled to at most --tex pixels (WebP), meshopt kept.
// --drop a,b,... also leaves out the named nodes (with their subtrees): small dressing parts of a building
// (parts_rail, parts_ladder, ...) that a phone screen cannot resolve. Prints the triangle count and the bounding
// box before and after, so the caller can check that a drop did not move the bbox centre the runtime frames on.
// Used by build-artifact.mjs.
//   node tools/lite-glb.mjs in.glb out.glb [--tex 1024] [--drop parts_rail,parts_ladder]
import { NodeIO, getBounds } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { textureCompress, meshopt, prune } from '@gltf-transform/functions';
import { MeshoptEncoder, MeshoptDecoder } from 'meshoptimizer';
import sharp from 'sharp';

const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf(`--${k}`); return i < 0 ? d : args.splice(i, 2)[1]; };
const tex = parseInt(opt('tex', '1024'));
const drop = (opt('drop', '') || '').split(',').filter(Boolean);
const [input, output] = args;
if (!input || !output) { console.error('usage: lite-glb.mjs in.glb out.glb [--tex N] [--drop node,node]'); process.exit(2); }

await Promise.all([MeshoptEncoder.ready, MeshoptDecoder.ready]);
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.encoder': MeshoptEncoder, 'meshopt.decoder': MeshoptDecoder });
const doc = await io.read(input);
const scene = doc.getRoot().getDefaultScene() || doc.getRoot().listScenes()[0];
const tris = () => doc.getRoot().listMeshes().reduce((n, m) => n + m.listPrimitives().reduce((k, p) => k + (p.getIndices() || p.getAttribute('POSITION')).getCount() / 3, 0), 0);
const box = () => { const b = getBounds(scene); return [...b.min, ...b.max].map((v) => +v.toFixed(3)); };
const before = { tris: tris(), box: box() };
const dropped = [];
for (const n of doc.getRoot().listNodes()) if (drop.includes(n.getName())) { dropped.push(n.getName()); n.dispose(); }
const steps = [];
if (dropped.length) steps.push(prune());
steps.push(textureCompress({ encoder: sharp, targetFormat: 'webp', resize: [tex, tex], quality: 85 }));
steps.push(meshopt({ encoder: MeshoptEncoder, level: 'medium' }));
await doc.transform(...steps);
await io.write(output, doc);
console.log(JSON.stringify({ before, after: { tris: tris(), box: box() }, dropped }));
