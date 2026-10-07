// Package regression check (run by tools/build-artifact.mjs after it writes dist/, or on its own):
// decode every model tier the way the published artifact does (src/lib/glbship.js loadGLB with window.__glbB64, every
// file through dist/files.json; a path the package does not hold is a 404) in headless Chromium, and compare it with
// the source GLB loaded by three's GLTFLoader:
//   nodes, meshes, triangles, materials, textures (per material slot), every texture decoded (non-zero size), each
//   texture's size within the tier's cap, and each material slot's texture looks like the source's (16 x 16 thumbnails,
//   mean abs difference), so a texture that fails to load, lands on the wrong material or the wrong slot fails the check.
// A tier's dropped nodes (tools/split-glb.mjs `drop`) are removed from the source before comparing.
//   node tools/check-package.mjs [--root <Scene3D dir>] [--only <substring>]   (tiers as build-artifact.mjs makes them)
import { chromium } from 'playwright-core';
import { readFile } from 'node:fs/promises';
import { join, extname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const CDN = 'https://cdn.jsdelivr.net/npm/three@0.186.1/';
const ORIGIN = 'https://artifact.test/';
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.webp': 'image/webp', '.png': 'image/png', '.jpg': 'image/jpeg', '.txt': 'text/plain' };
// The artifact host's policy as it bites a model load: scripts from the CDN allowlist, fetch() only of the package's own
// files (no blob: in connect-src, so a texture loaded by fetch(blob:) fails there and must fail here too), images from
// the package, data: and blob:. CHECK_CSP=0 turns it off.
export const HOST_CSP = process.env.CHECK_CSP === '0' ? '' : "default-src 'self'; script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval' https://cdn.jsdelivr.net; connect-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'";
const HARNESS = `<!doctype html><meta charset="utf-8">
<script type="importmap">{ "imports": { "three": "${CDN}build/three.module.js", "three/addons/": "${CDN}examples/jsm/" } }</script>
<script type="module">
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { loadGLB } from './src/lib/glbship.js';
const raw = new GLTFLoader(); raw.setMeshoptDecoder(MeshoptDecoder);
const SLOTS = ['map', 'normalMap', 'roughnessMap', 'metalnessMap', 'aoMap', 'emissiveMap', 'alphaMap'];
const cv = document.createElement('canvas'); cv.width = cv.height = 16;
const g2 = cv.getContext('2d', { willReadFrequently: true });
// 16 x 16 thumbnail, halving step by step (a box filter), so a 4096 px source and its 256 px copy compare fairly
const thumb = (img) => {
  try {
    let src = img, w = img.width, h = img.height;
    while (w > 32 || h > 32) {
      const c = document.createElement('canvas'); c.width = Math.max(16, w >> 1); c.height = Math.max(16, h >> 1);
      const g = c.getContext('2d'); g.imageSmoothingQuality = 'high'; g.drawImage(src, 0, 0, c.width, c.height);
      src = c; w = c.width; h = c.height;
    }
    g2.clearRect(0, 0, 16, 16); g2.imageSmoothingQuality = 'high'; g2.drawImage(src, 0, 0, 16, 16);
    return Array.from(g2.getImageData(0, 0, 16, 16).data);
  } catch (e) { return null; }
};
function stats(scene, drop = []) {
  if (drop.length) { const gone = []; scene.traverse((o) => { if (drop.includes(o.name)) gone.push(o); }); for (const o of gone) o.removeFromParent(); }
  let nodes = 0, meshes = 0, tris = 0; const mats = new Map(); const tex = new Set();
  scene.traverse((o) => {
    if (o !== scene) nodes++;
    if (!o.isMesh) return;
    meshes++;
    const gm = o.geometry; tris += (gm.index ? gm.index.count : gm.attributes.position.count) / 3;
    for (const m of [].concat(o.material)) if (!mats.has(m.name + '|' + m.uuid)) mats.set(m.name + '|' + m.uuid, m);
  });
  // materials keyed by name + first mesh that uses them (stable across both loads)
  const byName = {};
  const order = [];
  scene.traverse((o) => { if (o.isMesh) for (const m of [].concat(o.material)) if (!order.includes(m)) order.push(m); });
  order.forEach((m, i) => {
    const slots = {};
    for (const s of SLOTS) { const t = m[s]; if (!t) continue; tex.add(t); const img = t.image; slots[s] = { w: img?.width || 0, h: img?.height || 0, thumb: img ? thumb(img) : null }; }
    byName[i + ':' + m.name] = slots;
  });
  return { nodes, meshes, tris: Math.round(tris), materials: order.length, textures: tex.size, mats: byName };
}
// the package's decode (glbship.js loadGLB, page under the host's CSP) and the source GLB (three's GLTFLoader, page
// without a CSP, so the reference never depends on the loader under test)
window.pkgStats = async (url, tier, drop) => stats((await loadGLB(url, tier)).scene.clone(true), drop);
window.srcStats = async (url, drop) => stats((await raw.loadAsync('raw/' + url)).scene, drop);
window.harnessReady = true;
</script>`;

/**
 * models: [{ rel: 'assets/ships/carrier.glb', tiers: [{ name, cap, roleCaps, drop }] }] (build-artifact.mjs tiersOf)
 * Returns { ok, rows, failures }.
 */
export async function checkPackage({ root, models, distFiles = 'dist/files.json', log = console.log }) {
  const PKG = JSON.parse(await readFile(join(root, distFiles), 'utf8'));
  const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--enable-webgl'] });
  const failures = [], rows = [];
  try {
    const open = async (lite, csp) => {
      const ctx = await browser.newContext({ viewport: { width: 400, height: 300 } });
      const pg = await ctx.newPage();
      const errs = [];
      await pg.addInitScript(() => { window.__glbB64 = true; });
      // CHECK_VARIANT: exercise the loader's other browser paths (no Uint8Array base64 builtins; no createImageBitmap)
      for (const v of (process.env.CHECK_VARIANT || '').split(',').filter(Boolean)) {
        if (v === 'nob64') await pg.addInitScript(() => { delete Uint8Array.fromBase64; delete Uint8Array.prototype.setFromBase64; });
        if (v === 'noibm') await pg.addInitScript(() => { delete window.createImageBitmap; });
      }
      await pg.route(CDN + '**', async (r) => { try { await r.fulfill({ body: await readFile(join(root, 'node_modules/three', r.request().url().slice(CDN.length).split('?')[0])), contentType: 'text/javascript' }); } catch { await r.abort(); } });
      await pg.route(ORIGIN + '**', async (r) => {
        const p = decodeURIComponent(new URL(r.request().url()).pathname).replace(/^\/+/, '');
        if (p === 'harness.html') return r.fulfill({ body: HARNESS, contentType: 'text/html', headers: csp && HOST_CSP ? { 'Content-Security-Policy': HOST_CSP } : {} });
        let file = null;
        if (p.startsWith('raw/')) file = join(root, p.slice(4)); // the source GLB, for reference only
        else { const v = PKG[p]; if (v !== undefined) file = join(root, typeof v === 'string' ? v : v.from); }
        try { if (!file) throw new Error(); await r.fulfill({ body: await readFile(file), contentType: TYPES[extname(p)] || 'application/octet-stream' }); }
        catch { errs.push(`404 ${p}`); await r.fulfill({ status: 404, body: '' }); }
      });
      pg.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warning') errs.push(m.text().slice(0, 300)); });
      pg.on('pageerror', (e) => errs.push(e.message.slice(0, 300)));
      await pg.goto(`${ORIGIN}harness.html${lite ? '?lite=1' : '?lite=0'}`);
      await pg.waitForFunction(() => window.harnessReady === true, null, { timeout: 60000 });
      return { ctx, pg, errs };
    };
    for (const lite of [false, true]) {
      const { ctx, pg, errs } = await open(lite, true);
      const ref = await open(lite, false);
      for (const { rel, tiers } of models) {
        for (const t of tiers) {
          if ((t.name === 'full') === lite) continue; // desktop page: full; phone page: lite, mini
          const id = `${rel} .${t.name}`;
          errs.length = 0;
          let res;
          try {
            const [pkg, src] = await Promise.all([pg.evaluate(([u, n, d]) => window.pkgStats(u, n, d), [rel, t.name, t.drop || []]),
              ref.pg.evaluate(([u, d]) => window.srcStats(u, d), [rel, t.drop || []])]);
            res = { pkg, src };
          }
          catch (e) { failures.push(`${id}: load failed: ${e.message.split('\n')[0]}`); continue; }
          const { pkg, src } = res;
          const bad = [];
          for (const k of ['nodes', 'meshes', 'tris', 'materials', 'textures']) if (pkg[k] !== src[k]) bad.push(`${k} ${pkg[k]} != source ${src[k]}`);
          let worst = 0;
          for (const [mk, sslots] of Object.entries(src.mats)) {
            const pslots = pkg.mats[mk];
            if (!pslots) { bad.push(`material ${mk} missing`); continue; }
            for (const [s, st] of Object.entries(sslots)) {
              const pt = pslots[s];
              if (!pt) { bad.push(`${mk}.${s} missing`); continue; }
              if (!pt.w || !pt.h) { bad.push(`${mk}.${s} not decoded`); continue; }
              const cap = Math.min(...[t.cap, ...Object.values(t.roleCaps || {})].filter(Boolean), Infinity);
              const want = Math.max(st.w, st.h) <= cap ? [st.w, st.h] : null;
              if (want && (pt.w !== want[0] || pt.h !== want[1])) bad.push(`${mk}.${s} ${pt.w}x${pt.h} != source ${st.w}x${st.h}`);
              if (Math.max(pt.w, pt.h) > Math.max(st.w, st.h)) bad.push(`${mk}.${s} larger than source`);
              if (st.thumb && pt.thumb) {
                let d = 0; for (let i = 0; i < st.thumb.length; i++) d += Math.abs(st.thumb[i] - pt.thumb[i]);
                d /= st.thumb.length; worst = Math.max(worst, d);
                if (d > 12) bad.push(`${mk}.${s} differs from source (mean |d| ${d.toFixed(1)})`);
              }
            }
            for (const s of Object.keys(pslots)) if (!sslots[s]) bad.push(`${mk}.${s} extra texture`);
          }
          const loadErrs = errs.filter((e) => !/GL Driver Message/.test(e));
          if (loadErrs.length) bad.push(...loadErrs.map((e) => `console: ${e}`));
          rows.push({ id, ...Object.fromEntries(['nodes', 'meshes', 'tris', 'materials', 'textures'].map((k) => [k, pkg[k]])), worst: +worst.toFixed(2), bad });
          log(`${bad.length ? 'FAIL' : 'ok  '} ${id.padEnd(48)} nodes ${pkg.nodes} meshes ${pkg.meshes} tris ${pkg.tris} materials ${pkg.materials} textures ${pkg.textures} thumb diff ${worst.toFixed(1)}${bad.length ? '\n       ' + bad.slice(0, 12).join('\n       ') : ''}`);
          if (bad.length) failures.push(`${id}: ${bad.slice(0, 4).join('; ')}`);
        }
      }
      await ctx.close();
      await ref.ctx.close();
    }
  } finally { await browser.close(); }
  return { ok: failures.length === 0, rows, failures };
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  const args = process.argv.slice(2);
  const opt = (k, d) => { const i = args.indexOf(`--${k}`); return i < 0 ? d : args[i + 1]; };
  const root = resolve(opt('root', fileURLToPath(new URL('..', import.meta.url))));
  const only = opt('only', '');
  const { modelTiers } = await import('./artifact-tiers.mjs');
  const PKG = JSON.parse(await readFile(join(root, 'dist/files.json'), 'utf8'));
  const models = Object.keys(PKG).filter((k) => k.endsWith('.glb.shared.b64.txt')).map((k) => k.replace(/\.shared\.b64\.txt$/, ''))
    .filter((rel) => rel.includes(only)).map((rel) => ({ rel, tiers: modelTiers(rel) }));
  const r = await checkPackage({ root, models });
  console.log(r.ok ? `package check: ${r.rows.length} model tiers match their source` : `package check FAILED (${r.failures.length}):\n  ${r.failures.join('\n  ')}`);
  process.exit(r.ok ? 0 : 1);
}
