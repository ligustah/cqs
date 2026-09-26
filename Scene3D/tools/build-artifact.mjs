// Package the scene as a claude.ai Artifact: the page body (the host adds the
// document skeleton) plus every module under src/ as supporting files.
//   node tools/build-artifact.mjs  -> dist/orbital-fleet.html + dist/files.json
import { readFile, writeFile, mkdir, readdir } from 'node:fs/promises';
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
async function walk(dir) {
  for (const e of await readdir(dir, { withFileTypes: true })) {
    const p = join(dir, e.name);
    if (e.isDirectory()) await walk(p);
    else if (e.name.endsWith('.js')) { const rel = relative(ROOT, p).split('\\').join('/'); files[rel] = rel; }
  }
}
await walk(join(ROOT, 'src'));
await writeFile(join(ROOT, 'dist/files.json'), JSON.stringify(files, null, 2));
console.log(`dist/orbital-fleet.html + ${Object.keys(files).length} module files`);
