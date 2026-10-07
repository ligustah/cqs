// Package the scene as a claude.ai Artifact: the page body (the host adds the
// document skeleton) plus every module under src/ and every runtime asset under assets/
// (GLBs, concept art, PATINA maps) as supporting files. That includes the ground unit
// (assets/ships/vehicle.glb) and the buildings (assets/buildings/*.glb). Not shipped: assets/ships/raw and the parts
// kits (assets/parts, parts-blender, parts-yard, parts-spaceport, parts-colony): assembled ships and buildings carry their parts in
// their own GLB, and nothing loads a kit at runtime.
// Models (tools/split-glb.mjs): each GLB goes out split by tier, so the tiers share one copy of the geometry and the
// big textures are plain WebP files (base64 costs a third more, and artifact hosting does not serve model/gltf-binary):
//   <name>.glb.shared.b64.txt    geometry (meshopt, bit-identical) + the textures every tier uses unchanged
//   <name>.glb.b64.txt           desktop tier: the model's JSON + its own textures (originals; desktop role caps in tools/artifact-tiers.mjs)
//   <name>.glb.<tier>.b64.txt    phone tiers (src/lib/device.js, README "Phone budget"): JSON + downscaled textures
//   assets/tex/<hash>.webp       every texture of 2048 px or more, as a plain image file (shared by content hash)
//   ships      .lite  1024 px textures (the subject of a ship studio)
//              .mini   256 px, the carrier 512 px (ships in a crowd: fleet, lineup, parked loads, building scenes)
//   buildings  .lite   512 px, small dressing parts left out of the scene graph (tools/artifact-tiers.mjs LITE_BUILDINGS); the bbox must not move
// PATINA sets ship only the maps the runtime loads (manifest runtimeMaps / maps), each with a 512 px .lite copy.
// Package limits (one artifact version): 256 MiB in all, 511 files, 15 MB per binary and 16 MB per text file.
//   node tools/build-artifact.mjs [--out dist]  -> <out>/orbital-fleet.html + <out>/files.json
import { readFile, writeFile, mkdir, readdir, stat, rm } from 'node:fs/promises';
import { join, relative, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';
import { splitGLB } from './split-glb.mjs';
import { modelTiers } from './artifact-tiers.mjs';
import { checkPackage } from './check-package.mjs';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
const argv = process.argv.slice(2);
const OUT = argv.includes('--out') ? argv[argv.indexOf('--out') + 1] : 'dist';
const DIST = join(ROOT, OUT);
const relOf = (p) => relative(ROOT, p).split('\\').join('/');
let html = await readFile(join(ROOT, 'index.html'), 'utf8');
html = html
  .replace(/<!doctype html>\s*/i, '')
  .replace(/<html[^>]*>\s*/i, '').replace(/<\/html>\s*/i, '')
  .replace(/<head>\s*/i, '').replace(/<\/head>\s*/i, '')
  .replace(/<body>\s*/i, '').replace(/<\/body>\s*/i, '')
  .replace(/<meta charset[^>]*>\s*/i, '').replace(/<meta name="viewport"[^>]*>\s*/i, '');
await rm(DIST, { recursive: true, force: true }); // no stale files from an earlier package
await mkdir(DIST, { recursive: true });
// models go out split by tier (src/lib/glbship.js loadB64)
html = '<script>window.__glbB64 = true;</script>\n' + html;
await writeFile(join(DIST, 'orbital-fleet.html'), html);

const files = {};
const TYPES = { '.glb': 'model/gltf-binary', '.webp': 'image/webp', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg' };
const MAX_BIN = 15e6, MAX_TEXT = 16e6;
const LIMIT = { bytes: 256 * 2 ** 20, files: 511 };
// model tiers (desktop full; phone lite/mini; buildings' dropped dressing; desktop role caps): tools/artifact-tiers.mjs
const tiersOf = modelTiers;
const SKIP = ['assets/ships/raw', 'assets/buildings/raw', 'assets/parts', 'assets/parts-blender', 'assets/parts-yard', 'assets/parts-spaceport', 'assets/parts-colony'];
// PATINA: only the maps loadPatinaLibrary fetches
const manifest = JSON.parse(await readFile(join(ROOT, 'assets/materials/manifest.json'), 'utf8'));
const patinaMaps = (set) => { const m = manifest.sets?.[set]; return m ? (m.runtimeMaps || m.maps || ['basecolor', 'normal', 'roughness', 'metalness', 'height']) : []; };
const report = [];
const sizes = {};
const models = []; // { rel, tiers } for the package check
const emit = async (key, abs, contentType, bytes) => {
  if (bytes !== undefined) { await mkdir(dirname(abs), { recursive: true }); await writeFile(abs, bytes); }
  const size = (await stat(abs)).size;
  const text = contentType.startsWith('text/') || contentType === 'application/json' || contentType === 'text/javascript';
  if (size > (text ? MAX_TEXT : MAX_BIN)) throw new Error(`${key} is ${(size / 1e6).toFixed(1)} MB (> ${text ? 16 : 15} MB artifact limit)`);
  files[key] = { from: relOf(abs), contentType };
  sizes[key] = size;
};
async function walk(dir, keep) {
  for (const e of (await readdir(dir, { withFileTypes: true })).sort((a, b) => a.name.localeCompare(b.name))) {
    const p = join(dir, e.name);
    const rel = relOf(p);
    if (e.isDirectory()) { if (!SKIP.includes(rel)) await walk(p, keep); continue; }
    const ext = e.name.slice(e.name.lastIndexOf('.'));
    if (!keep(ext)) continue;
    // local lite copies (e.g. assets/buildings/*.lite.glb) are not shipped as models: every GLB's tiers are made below
    if (e.name.endsWith('.lite.glb')) continue;
    if (ext === '.glb') {
      const tiers = tiersOf(rel);
      models.push({ rel, tiers });
      const r = await splitGLB(p, tiers, { ext: 2048 });
      await emit(`${rel}.shared.b64.txt`, join(DIST, `${rel}.shared.b64.txt`), 'text/plain', r.shared.toString('base64'));
      for (const t of tiers) {
        const key = `${rel}${t.name === 'full' ? '' : `.${t.name}`}.b64.txt`;
        await emit(key, join(DIST, key), 'text/plain', r.tiers[t.name].toString('base64'));
      }
      for (const [name, b] of Object.entries(r.tex)) {
        const key = `assets/tex/${name}`;
        if (!files[key]) await emit(key, join(DIST, key), TYPES[name.slice(name.lastIndexOf('.'))], b);
      }
      for (const x of r.report) {
        report.push(`${rel} .${x.tier}: ${x.maxPx} px max${x.cap ? ` (cap ${x.cap})` : ''}, ${x.external} WebP files, ${(x.ownBytes / 1e6).toFixed(2)} MB own textures${x.tris ? `, ${Math.round(x.tris[1] / 1e3)}k of ${Math.round(x.tris[0] / 1e3)}k tris` : ''}`);
      }
      report.push(`${rel} shared: ${(r.shared.length / 1e6).toFixed(2)} MB`);
      continue;
    }
    if (rel.startsWith('assets/materials/') && ext === '.webp') {
      const [, set, map] = rel.match(/^assets\/materials\/([^/]+)\/([^/.]+)\.webp$/) || [];
      if (!patinaMaps(set).includes(map)) continue; // not loaded at runtime
      const liteRel = rel.replace(/\.webp$/, '.lite.webp');
      const liteOut = join(DIST, liteRel);
      await mkdir(dirname(liteOut), { recursive: true });
      await sharp(p).resize(512, 512, { fit: 'inside' }).webp({ quality: 88 }).toFile(liteOut);
      await emit(liteRel, liteOut, 'image/webp');
    }
    if (TYPES[ext]) await emit(rel, p, TYPES[ext]); else { files[rel] = rel; sizes[rel] = (await stat(p)).size; }
  }
}
await walk(join(ROOT, 'src'), (ext) => ext === '.js');
await walk(join(ROOT, 'assets'), (ext) => ext in TYPES);
await writeFile(join(DIST, 'files.json'), JSON.stringify(files, null, 2));
const page = (await stat(join(DIST, 'orbital-fleet.html'))).size;
const total = page + Object.values(sizes).reduce((a, b) => a + b, 0);
const count = Object.keys(files).length + 1;
const largest = Object.entries(sizes).sort((a, b) => b[1] - a[1]).slice(0, 5).map(([k, v]) => `${k} ${(v / 1e6).toFixed(1)} MB`);
for (const r of report) console.log(`  ${r}`);
console.log(`${OUT}/orbital-fleet.html (${(page / 1e3).toFixed(1)} kB page) + ${count - 1} supporting files: ${(total / 1e6).toFixed(1)} MB (${(total / 2 ** 20).toFixed(1)} MiB) of ${LIMIT.bytes / 2 ** 20} MiB, ${count} of ${LIMIT.files} files`);
console.log(`largest: ${largest.join(', ')}`);
if (total > LIMIT.bytes || count > LIMIT.files) throw new Error('package exceeds the artifact limits');
// Package check (tools/check-package.mjs): every model tier decoded the way the published page does it (glbship.js
// loadGLB, files through files.json, the host's CSP) must match its source GLB: nodes, meshes, triangles, materials,
// textures per material slot, each texture decoded and looking like the source's. --no-check skips it.
if (!argv.includes('--no-check')) {
  console.log(`package check: ${models.length} models ...`);
  const r = await checkPackage({ root: ROOT, models, distFiles: join(OUT, 'files.json'), log: (l) => { if (!l.startsWith('ok')) console.log(l); } });
  if (!r.ok) throw new Error(`package check failed (${r.failures.length}):\n  ${r.failures.join('\n  ')}`);
  console.log(`package check: ${r.rows.length} model tiers match their source GLB`);
}
