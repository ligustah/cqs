// Package the scene as a claude.ai Artifact: the page body (the host adds the
// document skeleton) plus every module under src/ and every asset under assets/
// (GLBs, concept art, PATINA maps; not assets/ships/raw) as supporting files.
//   node tools/build-artifact.mjs  -> dist/orbital-fleet.html + dist/files.json
import { readFile, writeFile, mkdir, readdir, stat } from 'node:fs/promises';
import { join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
let html = await readFile(join(ROOT, 'index.html'), 'utf8');
html = html
  .replace(/<!doctype html>\s*/i, '')
  .replace(/<html[^>]*>\s*/i, '').replace(/<\/html>\s*/i, '')
  .replace(/<head>\s*/i, '').replace(/<\/head>\s*/i, '')
  .replace(/<body>\s*/i, '').replace(/<\/body>\s*/i, '')
  .replace(/<meta charset[^>]*>\s*/i, '').replace(/<meta name="viewport"[^>]*>\s*/i, '');
await mkdir(join(ROOT, 'dist'), { recursive: true });
await writeFile(join(ROOT, 'dist/orbital-fleet.html'), html);

const files = {};
const TYPES = { '.glb': 'model/gltf-binary', '.webp': 'image/webp', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg' };
const MAX = 15e6;
let bytes = 0;
async function walk(dir, keep) {
  for (const e of await readdir(dir, { withFileTypes: true })) {
    const p = join(dir, e.name);
    const rel = relative(ROOT, p).split('\\').join('/');
    if (e.isDirectory()) { if (rel !== 'assets/ships/raw') await walk(p, keep); continue; }
    const ext = e.name.slice(e.name.lastIndexOf('.'));
    if (!keep(ext)) continue;
    const size = (await stat(p)).size;
    if (size > MAX) throw new Error(`${rel} is ${(size / 1e6).toFixed(1)} MB (> 15 MB artifact limit)`);
    bytes += size;
    files[rel] = TYPES[ext] ? { from: rel, contentType: TYPES[ext] } : rel;
  }
}
await walk(join(ROOT, 'src'), (ext) => ext === '.js');
await walk(join(ROOT, 'assets'), (ext) => ext in TYPES);
await writeFile(join(ROOT, 'dist/files.json'), JSON.stringify(files, null, 2));
console.log(`dist/orbital-fleet.html + ${Object.keys(files).length} supporting files, ${(bytes / 1e6).toFixed(1)} MB`);
