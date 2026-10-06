// Phone-tier budget check: load each view the way the published artifact does (GLBs as base64 .b64.txt from dist/,
// lite copies on the phone tier) in an emulated mid-range phone and report, per view: bytes fetched, peak and final JS
// heap (CDP), ArrayBuffer backing store, triangles drawn, GPU estimate (unique textures with mips + geometry buffers +
// render targets), time to __ready, errors. Run node tools/build-artifact.mjs first (dist/ must match the sources).
//   node tools/phone-check.mjs [--desktop] [--root <Scene3D dir>] [--json out.json] [--shots dir] [view ...]
// views: fleet (default page), lineup, fighter, corvette, freighter, destroyer, carrier, vehicle, shipyard, spaceport,
// and the colony buildings (COLONY_VIEWS)
// Budget (README "Phone budget"): heap peak + GPU estimate well under 300 MB per view on the phone tier.
import { chromium } from 'playwright-core';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { join, extname, resolve } from 'node:path';
import { execFileSync } from 'node:child_process';

// resident memory of the browser's renderer and GPU processes (MB): with SwiftShader the GPU process holds the
// textures and buffers in RAM, so renderer + GPU RSS is a fair stand-in for what a phone's tab is charged
function rssMB() {
  try {
    const out = execFileSync('ps', ['-eo', 'rss=,args='], { encoding: 'utf8', maxBuffer: 1 << 24 });
    let kb = 0;
    for (const line of out.split('\n')) if (/--type=(renderer|gpu-process)/.test(line) && /pw-browsers|chrom/i.test(line)) kb += parseInt(line.trim()) || 0;
    return kb / 1024;
  } catch { return 0; }
}

const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf(`--${k}`); if (i < 0) return d; const v = args[i + 1]; args.splice(i, 2); return v; };
const flag = (k) => { const i = args.indexOf(`--${k}`); if (i < 0) return false; args.splice(i, 1); return true; };
const ROOT = resolve(opt('root', fileURLToPath(new URL('..', import.meta.url))));
const jsonOut = opt('json', null);
const shots = opt('shots', null); // directory: also save a screenshot of each view (<view>.png)
const timeout = parseInt(opt('timeout', '600000'));
const desktop = flag('desktop');
const still = flag('still'); // stills (?still=1): three frames at pixel ratio 1, then idle; screenshots of heavy views finish
// colony buildings: one view each (#<id>), added as they are registered (src/ships/index.js BUILDINGS)
const COLONY_VIEWS = ['deuterium_depot', 'steel_mill'];
const VIEWS = args.length ? args : ['fleet', 'lineup', 'fighter', 'corvette', 'freighter', 'destroyer', 'carrier', 'vehicle', 'shipyard', 'spaceport', ...COLONY_VIEWS];
const CDN = 'https://cdn.jsdelivr.net/npm/three@0.186.1/';
const ORIGIN = 'https://artifact.test/';
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.webp': 'image/webp', '.png': 'image/png', '.jpg': 'image/jpeg', '.txt': 'text/plain' };
// a mid-range phone: iPhone 12-ish viewport, DPR 3, touch, mobile UA (device.js picks the lite tier from these)
const PHONE = { viewport: { width: 390, height: 844 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true,
  userAgent: 'Mozilla/5.0 (Linux; Android 13; Pixel 6a) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36' };
const DESKTOP = { viewport: { width: 1280, height: 800 }, deviceScaleFactor: 1 };

const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--enable-webgl', '--enable-precise-memory-info', '--js-flags=--expose-gc'] });
const rows = [];
for (const view of VIEWS) {
  const ctx = await browser.newContext(desktop ? DESKTOP : PHONE);
  const pg = await ctx.newPage();
  const fetched = { total: 0, glb: 0, files: 0 };
  await pg.addInitScript(() => { window.__glbB64 = true; });
  await pg.route(/fonts\.(googleapis|gstatic)\.com/, (r) => r.fulfill({ status: 200, contentType: 'text/css', body: '' }));
  await pg.route(CDN + '**', async (route) => {
    try { await route.fulfill({ body: await readFile(join(ROOT, 'node_modules/three', route.request().url().slice(CDN.length))), contentType: 'text/javascript' }); } catch { await route.abort(); }
  });
  await pg.route(ORIGIN + '**', async (route) => {
    const p = decodeURIComponent(new URL(route.request().url()).pathname).replace(/^\/+/, '') || 'index.html';
    // the artifact serves GLBs as base64 text and lite PATINA maps from dist/; everything else from the source tree
    const file = p.endsWith('.b64.txt') || p.endsWith('.lite.webp') ? join(ROOT, 'dist', p) : join(ROOT, p);
    try {
      const body = await readFile(file);
      fetched.total += body.length; fetched.files++;
      if (p.endsWith('.b64.txt')) fetched.glb += body.length;
      await route.fulfill({ body, contentType: TYPES[extname(p)] || 'application/octet-stream' });
    } catch { await route.fulfill({ status: 404, body: 'not found' }); }
  });
  const logs = [];
  pg.on('console', (m) => { if (['error'].includes(m.type())) logs.push(m.text().slice(0, 200)); });
  pg.on('pageerror', (e) => logs.push(`[pageerror] ${e.message.slice(0, 200)}`));
  pg.on('crash', () => logs.push('[crash] renderer process crashed'));
  const cdp = await ctx.newCDPSession(pg);
  await cdp.send('Performance.enable');
  let peak = 0, peakBacking = 0, peakRss = 0, polling = true;
  const rssPoll = setInterval(() => { peakRss = Math.max(peakRss, rssMB()); }, 150);
  const poll = (async () => {
    while (polling) {
      try {
        const u = await cdp.send('Runtime.getHeapUsage');
        peak = Math.max(peak, u.usedSize);
        if (u.backingStorageSize !== undefined) peakBacking = Math.max(peakBacking, u.backingStorageSize);
      } catch { /* page navigating */ }
      await new Promise((r) => setTimeout(r, 100));
    }
  })();
  const t0 = Date.now();
  const vp = (desktop ? DESKTOP : PHONE).viewport;
  const url = `${ORIGIN}index.html${still ? `?still=1&w=${vp.width}&h=${vp.height}` : ''}${view === 'fleet' ? '' : `#${view}`}`;
  let ok = true, readyS = null;
  try {
    await pg.goto(url, { timeout });
    await pg.waitForFunction(() => window.__ready === true || window.__fatal, null, { timeout, polling: 250 });
    readyS = (Date.now() - t0) / 1000;
  } catch (e) { ok = false; logs.push(`[timeout] ${e.message.split('\n')[0]}`); }
  polling = false; await poll;
  clearInterval(rssPoll);
  const endRss = rssMB();
  let info = null;
  try {
    info = await pg.evaluate(() => {
      const s = window.__scene;
      if (!s) return { fatal: window.__fatal || null };
      const { scene, renderer } = s;
      const tex = new Set(), geo = new Set();
      scene.traverse((o) => {
        if (o.geometry) geo.add(o.geometry);
        for (const m of [].concat(o.material || [])) for (const v of Object.values(m)) if (v && v.isTexture) tex.add(v);
        for (const m of [].concat(o.material || [])) for (const u of Object.values(m.uniforms || {})) if (u?.value?.isTexture) tex.add(u.value);
      });
      if (scene.environment) tex.add(scene.environment);
      let texB = 0, maxTex = 0;
      for (const t of tex) {
        const img = t.image; const w = img?.width || img?.data?.width || t.userData.size?.[0] || 0, h = img?.height || img?.data?.height || t.userData.size?.[1] || 0;
        const bpp = t.type === 1016 /* HalfFloat */ ? 8 : t.type === 1015 ? 16 : 4;
        texB += w * h * bpp * (t.generateMipmaps !== false ? 4 / 3 : 1) * (t.isCubeTexture ? 6 : 1);
        maxTex = Math.max(maxTex, w, h);
      }
      let geoB = 0;
      for (const g of geo) { for (const a of Object.values(g.attributes)) geoB += a.array?.byteLength || 0; if (g.index) geoB += g.index.array.byteLength; }
      const c = renderer.domElement;
      // composer: HalfFloat RGBA x MSAA samples + resolve, bloom mip chain (~2x a full target), AO when on; the sun's shadow map
      const px = c.width * c.height;
      let shadow = 0; scene.traverse((o) => { if (o.isLight && o.castShadow && o.shadow?.mapSize) shadow += o.shadow.mapSize.x * o.shadow.mapSize.y * 4 * 2; });
      const rt = px * 8 * 6 + shadow;
      const r = renderer.info;
      // triangles in the scene graph (visible meshes, instanced counts), as renderer.info only holds the last pass
      let tris = 0;
      scene.traverseVisible((o) => { if (!o.isMesh || !o.geometry) return; const g = o.geometry; const n = (g.index ? g.index.count : g.attributes.position?.count || 0) / 3; tris += n * (o.isInstancedMesh ? o.count : 1); });
      const bySrc = {};
      for (const t of tex) {
        const img = t.image; const w = img?.width || img?.data?.width || t.userData.size?.[0] || 0, h = img?.height || img?.data?.height || t.userData.size?.[1] || 0;
        const src = img?.src ? 'patina' : t.userData.size || (typeof ImageBitmap !== 'undefined' && img instanceof ImageBitmap) ? 'glb' : img?.data ? 'data' : img?.getContext ? 'canvas' : t.isRenderTargetTexture ? 'rt' : 'other';
        bySrc[src] = (bySrc[src] || 0) + w * h * 4 * (4 / 3) / 1e6;
      }
      const bySize = {};
      for (const t of tex) { const img = t.image; const k = `${img?.width || img?.data?.width || t.userData.size?.[0]}x${img?.height || img?.data?.height || t.userData.size?.[1]}`; bySize[k] = (bySize[k] || 0) + 1; }
      return { tris: Math.round(tris), texCount: tex.size, bySize, bySrc, calls: r.render.calls, textures: r.memory.textures, geometries: r.memory.geometries, texMB: texB / 1e6, maxTex, geoMB: geoB / 1e6, rtMB: rt / 1e6, canvas: [c.width, c.height], lost: renderer.getContext().isContextLost() };
    });
  } catch (e) { logs.push(`[eval] ${e.message.split('\n')[0]}`); }
  if (shots && readyS !== null) { try { await mkdir(shots, { recursive: true }); await pg.screenshot({ path: join(shots, `${view}.png`), timeout: 120000 }); } catch (e) { logs.push(`[shot] ${e.message.split('\n')[0]}`); } }
  let heap = 0;
  try { await cdp.send('HeapProfiler.collectGarbage'); } catch { /* crashed */ }
  try { const m = await cdp.send('Performance.getMetrics'); heap = m.metrics.find((x) => x.name === 'JSHeapUsedSize')?.value || 0; } catch { /* crashed */ }
  const row = { view, ok: ok && !!info?.tris, readyS, fetchedMB: fetched.total / 1e6, glbMB: fetched.glb / 1e6, files: fetched.files,
    heapPeakMB: peak / 1e6, rssPeakMB: peakRss, rssEndMB: endRss, heapMB: heap / 1e6, backingPeakMB: peakBacking / 1e6, ...(info || {}), errors: logs.slice(0, 6) };
  row.gpuMB = (row.texMB || 0) + (row.geoMB || 0) + (row.rtMB || 0);
  row.budgetMB = row.heapPeakMB + row.gpuMB;
  rows.push(row);
  const f = (v, d = 0) => (v === undefined || v === null ? '-' : Number(v).toFixed(d));
  console.log(`${view.padEnd(10)} ${row.ok ? 'ok  ' : 'FAIL'} ready ${f(readyS, 1)}s  fetched ${f(row.fetchedMB, 1)} MB (b64 ${f(row.glbMB, 1)})  heap peak ${f(row.heapPeakMB)} MB end ${f(row.heapMB)}  tris ${f((row.tris || 0) / 1e3)}k  tex ${f(row.texMB)} MB (max ${row.maxTex ?? '-'}px)  geo ${f(row.geoMB)} MB  rt ${f(row.rtMB)} MB  heap+gpu ${f(row.budgetMB)} MB  rss peak ${f(row.rssPeakMB)} end ${f(row.rssEndMB)} MB${row.errors.length ? `\n           ${row.errors.join('\n           ')}` : ''}`);
  await ctx.close();
}
await browser.close();
if (jsonOut) await writeFile(jsonOut, JSON.stringify({ desktop, root: ROOT, rows }, null, 2));
