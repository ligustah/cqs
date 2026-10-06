// Package the scene as a claude.ai Artifact: the page body (the host adds the
// document skeleton) plus every module under src/ and every runtime asset under assets/
// (GLBs, concept art, PATINA maps) as supporting files. That includes the ground unit
// (assets/ships/vehicle.glb) and the buildings (assets/buildings/*.glb). Not shipped: assets/ships/raw and the parts
// kits (assets/parts, parts-blender, parts-yard, parts-spaceport, parts-colony): assembled ships and buildings carry their parts in
// their own GLB, and nothing loads a kit at runtime.
// Phone tier (src/lib/device.js, README "Phone budget"): every GLB gets copies made here by tools/lite-glb.mjs:
//   ships      .lite  1024 px textures (the subject of a ship studio)
//              .mini   256 px, the carrier 512 px (ships in a crowd: fleet, lineup, parked loads, building scenes)
//   buildings  .lite   512 px, small dressing parts left out (LITE_BUILDINGS); the bbox must not move
//   node tools/build-artifact.mjs  -> dist/orbital-fleet.html + dist/files.json
import { readFile, writeFile, mkdir, readdir, stat, rm } from 'node:fs/promises';
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
await rm(join(ROOT, 'dist'), { recursive: true, force: true }); // no stale files from an earlier package
await mkdir(join(ROOT, 'dist'), { recursive: true });
// GLBs go out as base64 text (artifact hosting does not serve model/gltf-binary)
html = '<script>window.__glbB64 = true;</script>\n' + html;
await writeFile(join(ROOT, 'dist/orbital-fleet.html'), html);

const files = {};
const TYPES = { '.glb': 'model/gltf-binary', '.webp': 'image/webp', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg' };
const MAX = 15e6;
// phone-tier copies per GLB: [suffix, texture cap, nodes to drop]
const LITE_BUILDINGS = {
  // workers, ladders, hand rails and vents: below a pixel on a phone; the bollards stay (amber pins sit on them)
  'assets/buildings/shipyard.glb': ['parts_ladder', 'parts_rail', 'parts_vent', 'parts_yard-worker'],
  'assets/buildings/spaceport.glb': ['parts_rail'],
};
// colony buildings (src/buildings/colony.js) not listed above: the 1.8 m workers and the kit vents are below a pixel
// on a phone (their amber pins and lamps are lightscape, not geometry, so they stay)
const LITE_COLONY = ['parts_yard-worker', 'parts_vent'];
const phoneCopies = (rel) => (rel.startsWith('assets/buildings/')
  ? [['lite', 512, LITE_BUILDINGS[rel] || LITE_COLONY]]
  : [['lite', 1024, []], ['mini', rel.endsWith('carrier.glb') ? 512 : 256, []]]);
const SKIP = ['assets/ships/raw', 'assets/buildings/raw', 'assets/parts', 'assets/parts-blender', 'assets/parts-yard', 'assets/parts-spaceport', 'assets/parts-colony'];
const report = [];
let bytes = 0;
async function walk(dir, keep) {
  for (const e of await readdir(dir, { withFileTypes: true })) {
    const p = join(dir, e.name);
    const rel = relative(ROOT, p).split('\\').join('/');
    if (e.isDirectory()) { if (!SKIP.includes(rel)) await walk(p, keep); continue; }
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
      // phone tier (src/lib/device.js): the same GLB with textures capped (and a building's dressing dropped)
      for (const [suffix, tex, drop] of phoneCopies(rel)) {
        const liteGlb = join(ROOT, 'dist', `${rel}.${suffix}.glb`);
        const out = execFileSync('node', [join(ROOT, 'tools/lite-glb.mjs'), p, liteGlb, '--tex', String(tex), ...(drop.length ? ['--drop', drop.join(',')] : [])], { encoding: 'utf8' });
        const info = JSON.parse(out.trim().split('\n').pop());
        if (info.before.box.some((v, i) => Math.abs(v - info.after.box[i]) > 0.01)) throw new Error(`${rel} .${suffix}: dropping ${drop} moved the bbox ${info.before.box} -> ${info.after.box}`);
        const liteOut = join(ROOT, 'dist', `${rel}.${suffix}.b64.txt`);
        await writeFile(liteOut, (await readFile(liteGlb)).toString('base64'));
        const lb = (await stat(liteOut)).size;
        bytes += lb;
        files[`${rel}.${suffix}.b64.txt`] = { from: relative(ROOT, liteOut).split('\\').join('/'), contentType: 'text/plain' };
        report.push(`${rel}.${suffix}: ${tex} px, ${Math.round(info.after.tris / 1e3)}k tris${drop.length ? ` (of ${Math.round(info.before.tris / 1e3)}k)` : ''}, ${(lb / 1e6).toFixed(1)} MB b64`);
      }
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
for (const r of report) console.log(`  ${r}`);
console.log(`dist/orbital-fleet.html (${(page / 1e3).toFixed(1)} kB page) + ${Object.keys(files).length} supporting files, ${(bytes / 1e6).toFixed(1)} MB; largest ${largest[0]} ${(largest[1] / 1e6).toFixed(1)} MB`);
