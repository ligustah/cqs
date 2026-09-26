// Download fal.ai outputs into the scene's assets folder.
//
//   node tools/ingest-fal.mjs results.json
//
// results.json:
// {
//   "concepts":  { "bible": "https://…png", "fighter": "https://…png", … },
//   "meshes":    { "fighter": { "url": "https://…glb", "model": "tripo3d/p2/image-to-3d" }, … },
//   "materials": { "hull": { "basecolor": "https://…", "normal": "…", "roughness": "…", "metalness": "…", "height": "…", "prompt": "…" }, … }
// }
// Concepts -> assets/concepts/<name>.webp (1600 px), meshes -> assets/ships/<name>.glb
// (optimised with optimize-glb.mjs), materials -> assets/materials/<set>/<map>.webp + manifest.json.
import { mkdir, writeFile, readFile } from 'node:fs/promises';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import sharp from 'sharp';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
const spec = JSON.parse(await readFile(process.argv[2], 'utf8'));
const pipeline = JSON.parse(await readFile(join(ROOT, 'pipeline/fal-pipeline.json'), 'utf8'));

async function download(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${r.status} ${url}`);
  return Buffer.from(await r.arrayBuffer());
}

for (const [name, url] of Object.entries(spec.concepts || {})) {
  await mkdir(join(ROOT, 'assets/concepts'), { recursive: true });
  const buf = await download(url);
  await sharp(buf).resize({ width: 1600, withoutEnlargement: true }).webp({ quality: 86 }).toFile(join(ROOT, `assets/concepts/${name}.webp`));
  console.log(`concept ${name}`);
}

for (const [name, m] of Object.entries(spec.meshes || {})) {
  await mkdir(join(ROOT, 'assets/ships/raw'), { recursive: true });
  const raw = join(ROOT, `assets/ships/raw/${name}.glb`);
  await writeFile(raw, await download(m.url));
  const tris = String(pipeline.stages.C_optimise.tris[name.split('-')[0]] ?? 120000);
  execFileSync('node', [join(ROOT, 'tools/optimize-glb.mjs'), raw, join(ROOT, `assets/ships/${name}.glb`), '--tris', tris, '--tex', String(pipeline.stages.C_optimise.texture)], { stdio: 'inherit' });
}

if (spec.materials) {
  const manifestPath = join(ROOT, 'assets/materials/manifest.json');
  let manifest = { generator: pipeline.stages.D_materials.model, sets: {} };
  try { manifest = JSON.parse(await readFile(manifestPath, 'utf8')); } catch {}
  for (const [set, maps] of Object.entries(spec.materials)) {
    await mkdir(join(ROOT, `assets/materials/${set}`), { recursive: true });
    const have = [];
    for (const map of ['basecolor', 'normal', 'roughness', 'metalness', 'height']) {
      if (!maps[map]) continue;
      const buf = await download(maps[map]);
      await sharp(buf).resize(2048, 2048, { fit: 'fill' }).webp({ quality: map === 'normal' ? 95 : 88 }).toFile(join(ROOT, `assets/materials/${set}/${map}.webp`));
      have.push(map);
    }
    manifest.sets[set] = { maps: have, prompt: maps.prompt || pipeline.stages.D_materials.sets[set] };
    console.log(`material ${set}: ${have.join(', ')}`);
  }
  await writeFile(manifestPath, JSON.stringify(manifest, null, 2));
}
