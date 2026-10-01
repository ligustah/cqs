// Package the scene as a claude.ai Artifact: the page body (the host adds the
// document skeleton) plus every module under src/ and every asset under assets/
// (GLBs, concept art, PATINA maps; not assets/ships/raw) as supporting files. That includes the ground unit
// (assets/ships/vehicle.glb), the buildings (assets/buildings/*.glb) and the building kits (assets/parts-yard/,
// assets/parts-spaceport/), each GLB with its phone-tier lite copy made here.
//   node tools/build-artifact.mjs  -> dist/orbital-fleet.html + dist/files.json
import { readFile, writeFile, mkdir, readdir, stat } from 'node:fs/promises';
import { join, relative, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import sharp from 'sharp';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
let html = await readFile(join(ROOT, 'index.html'), 'utf8');
html = html
  .replace(/<!doctype html>\s*/i, '')
  .replace(/<html[^>]*>\s*/i, '').replace(/<\/html>\s*/i, '')
  .replace(/<head>\s*/i, '').replace(/<\/head>\s*/i, '')
  .replace(/<body>\s*/i, '').replace(/<\/body>\s*/i, '')
  .replace(/<meta charset[^>]*>\s*/i, '').replace(/<meta name="viewport"[^>]*>\s*/i, '');
await mkdir(join(ROOT, 'dist'), { recursive: true });
// GLBs go out as base64 text (artifact hosting does not serve model/gltf-binary)
html = '<script>window.__glbB64 = true;</script>\n' + html;
await writeFile(join(ROOT, 'dist/orbital-fleet.html'), html);

const files = {};
const TYPES = { '.glb': 'model/gltf-binary', '.webp': 'image/webp', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg' };
const MAX = 15e6;
// phone-tier texture caps: ships and buildings 1024 px (the carrier 2048: it fills the frame), kit parts 512
// (parts, parts-yard, parts-spaceport)
const liteTex = (rel) => (rel.includes('/parts') ? 512 : rel.endsWith('carrier.glb') ? 2048 : 1024);
let bytes = 0;
async function walk(dir, keep) {
  for (const e of await readdir(dir, { withFileTypes: true })) {
    const p = join(dir, e.name);
    const rel = relative(ROOT, p).split('\\').join('/');
    // raw meshes and the ship parts kits stay out: assembled ships carry their parts in their own GLB. The building
    // kits (parts-yard, parts-spaceport) ship with the buildings.
    if (e.isDirectory()) { if (!['assets/ships/raw', 'assets/parts', 'assets/parts-blender'].includes(rel)) await walk(p, keep); continue; }
    const ext = e.name.slice(e.name.lastIndexOf('.'));
    if (!keep(ext)) continue;
    // local lite copies (e.g. assets/buildings/*.lite.glb) are not shipped as models: every GLB's lite copy is made below
    if (e.name.endsWith('.lite.glb')) continue;
    const size = (await stat(p)).size;
    if (size > MAX) throw new Error(`${rel} is ${(size / 1e6).toFixed(1)} MB (> 15 MB artifact limit)`);
    bytes += size;
    if (ext === '.glb') {
      const out = join(ROOT, 'dist', `${rel}.b64.txt`);
      await mkdir(dirname(out), { recursive: true });
      await writeFile(out, (await readFile(p)).toString('base64'));
      const b = (await stat(out)).size;
      if (b > MAX) throw new Error(`${rel} base64 is ${(b / 1e6).toFixed(1)} MB (> 15 MB)`);
      bytes += b - size;
      files[`${rel}.b64.txt`] = { from: relative(ROOT, out).split('\\').join('/'), contentType: 'text/plain' };
      // phone tier (src/lib/device.js): the same GLB with textures capped
      const liteGlb = join(ROOT, 'dist', `${rel}.lite.glb`);
      execFileSync('node', [join(ROOT, 'tools/lite-glb.mjs'), p, liteGlb, '--tex', String(liteTex(rel))]);
      const liteOut = join(ROOT, 'dist', `${rel}.lite.b64.txt`);
      await writeFile(liteOut, (await readFile(liteGlb)).toString('base64'));
      bytes += (await stat(liteOut)).size;
      files[`${rel}.lite.b64.txt`] = { from: relative(ROOT, liteOut).split('\\').join('/'), contentType: 'text/plain' };
      continue;
    }
    if (ext === '.webp' && rel.startsWith('assets/materials/')) {
      const liteRel = rel.replace(/\.webp$/, '.lite.webp');
      const liteOut = join(ROOT, 'dist', liteRel);
      await mkdir(dirname(liteOut), { recursive: true });
      await sharp(p).resize(512, 512, { fit: 'inside' }).webp({ quality: 88 }).toFile(liteOut);
      bytes += (await stat(liteOut)).size;
      files[liteRel] = { from: relative(ROOT, liteOut).split('\\').join('/'), contentType: 'image/webp' };
    }
    files[rel] = TYPES[ext] ? { from: rel, contentType: TYPES[ext] } : rel;
  }
}
await walk(join(ROOT, 'src'), (ext) => ext === '.js');
await walk(join(ROOT, 'assets'), (ext) => ext in TYPES);
await writeFile(join(ROOT, 'dist/files.json'), JSON.stringify(files, null, 2));
const page = (await stat(join(ROOT, 'dist/orbital-fleet.html'))).size;
let largest = ['', 0];
for (const [k, v] of Object.entries(files)) { const sz = (await stat(join(ROOT, typeof v === 'string' ? v : v.from))).size; if (sz > largest[1]) largest = [k, sz]; }
console.log(`dist/orbital-fleet.html (${(page / 1e3).toFixed(1)} kB page) + ${Object.keys(files).length} supporting files, ${(bytes / 1e6).toFixed(1)} MB; largest ${largest[0]} ${(largest[1] / 1e6).toFixed(1)} MB`);
