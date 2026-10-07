// Package-vs-dev render diff: render each view through the artifact package exactly as published (the host's document
// skeleton around dist/orbital-fleet.html, every other path through dist/files.json, a 404 for anything else) and
// through the dev path (index.html, raw GLBs), save both stills and a diff image, and fail when they differ by more
// than the threshold. One headless browser, one view at a time (SwiftShader renders are CPU-heavy).
//   node tools/pkg-diff.mjs [--root <Scene3D>] [--device desktop|phone] [--only pkg|dev] [--out dir]
//        [--threshold 0.02] [--csp 0|1] [--units 16] [--json out.json] [view ...]
// views: fleet, spaceport (fleet ?shot=spaceport), the ship studios (carrier fighter destroyer freighter corvette
// vehicle) and b_<building> for every building in src/ships/index.js BUILDINGS (default: all of them).
// Metric: share of pixels whose largest channel difference is over 32 (of 255). Phone: the package serves the phone
// tiers (512-1024 px textures, buildings without small dressing) while dev loads the full GLBs, so compare phone with
// a looser threshold (the default is 0.06 there) or against a package render of a known-good build.
import { chromium } from 'playwright-core';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { join, extname, resolve } from 'node:path';
import sharp from 'sharp';

const a = process.argv.slice(2);
const opt = (k, d) => { const i = a.indexOf(`--${k}`); if (i < 0) return d; const v = a[i + 1]; a.splice(i, 2); return v; };
const ROOT = resolve(opt('root', fileURLToPath(new URL('..', import.meta.url))));
const device = opt('device', 'desktop');
const only = opt('only', null);
const out = resolve(opt('out', join(ROOT, 'shots/pkg-diff', device)));
const threshold = parseFloat(opt('threshold', device === 'phone' ? '0.06' : '0.02'));
const csp = opt('csp', '0') === '1';
// --units 16: emulate a GPU with 16 fragment texture units (ANGLE on D3D11 / Metal, iOS, most Android): a program with
// more active samplers fails to link, as it does there (SwiftShader has 32, so it would draw it)
const units = parseInt(opt('units', '0'));
const jsonOut = opt('json', join(out, 'diff.json'));
// a strict host-like CSP (optional): the page and package files same-origin, three from the CDN, images from data:/blob:
const HOST_CSP = "default-src 'self'; script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval' https://cdn.jsdelivr.net; connect-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com";

const BUILDINGS = ['shipyard', 'spaceport', 'deuterium_depot', 'steel_mill', 'refinery', 'residence', 'processing_plant', 'oil_tanks', 'silicon_foundry', 'steel_depot', 'trade_center', 'infrastructure', 'university', 'library', 'silicon_depot', 'military_base', 'radio_telescope', 'transmitter'];
const PRESET = { fleet: '', spaceport: 'shot=spaceport' };
for (const s of ['carrier', 'fighter', 'destroyer', 'freighter', 'corvette', 'vehicle']) PRESET[s] = `mode=ship&ship=${s}`;
for (const b of BUILDINGS) PRESET[`b_${b}`] = `mode=building&building=${b}`;
const views = a.length ? a : Object.keys(PRESET);
for (const v of views) if (PRESET[v] === undefined) throw new Error(`unknown view ${v}`);

const PKG = JSON.parse(await readFile(join(ROOT, 'dist/files.json'), 'utf8'));
// the host's document skeleton (what a published .html page is wrapped in)
const SKELETON = '<!doctype html><html><head><meta charset=utf8><meta name=viewport content="width=device-width,initial-scale=1,viewport-fit=cover"><style>:root{color-scheme:light;box-sizing:border-box}body{margin:0;padding:0}</style></head><body>\n';
const PAGE = {
  pkg: Buffer.from(SKELETON + (await readFile(join(ROOT, 'dist/orbital-fleet.html'), 'utf8')) + '\n</body></html>'),
  dev: await readFile(join(ROOT, 'index.html')),
};
const CDN = 'https://cdn.jsdelivr.net/npm/three@0.186.1/', ORIGIN = 'https://artifact.test/';
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.webp': 'image/webp', '.png': 'image/png', '.jpg': 'image/jpeg', '.txt': 'text/plain', '.glb': 'model/gltf-binary' };
const PHONE = { viewport: { width: 390, height: 844 }, deviceScaleFactor: 1, isMobile: true, hasTouch: true,
  userAgent: 'Mozilla/5.0 (Linux; Android 13; Pixel 6a) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36' };
const DESK = { viewport: { width: 1280, height: 800 }, deviceScaleFactor: 1 };
const D = device === 'phone' ? PHONE : DESK;

await mkdir(out, { recursive: true });
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--enable-webgl'] });

async function render(mode, name) {
  const ctx = await browser.newContext(D);
  const pg = await ctx.newPage();
  const logs = [];
  if (units) await pg.addInitScript((N) => {
    const SAMPLERS = [0x8b5e, 0x8b60, 0x8b5f, 0x8dc1, 0x8b62, 0x8dca, 0x8dd2, 0x8dc4, 0x8dcc, 0x8dd4, 0x8dc5, 0x8dcf, 0x8dd7];
    for (const C of [self.WebGL2RenderingContext, self.WebGLRenderingContext].filter(Boolean)) {
      const gp = C.prototype.getParameter, link = C.prototype.linkProgram;
      C.prototype.getParameter = function (p) { const v = gp.call(this, p); return p === this.MAX_TEXTURE_IMAGE_UNITS ? Math.min(N, v) : v; };
      C.prototype.linkProgram = function (prog) {
        link.call(this, prog);
        if (!this.getProgramParameter(prog, this.LINK_STATUS)) return;
        let s = 0;
        for (let i = 0, n = this.getProgramParameter(prog, this.ACTIVE_UNIFORMS); i < n; i++) { const u = this.getActiveUniform(prog, i); if (SAMPLERS.includes(u.type)) s += u.size; }
        if (s <= N) return;
        console.error(`[units] program with ${s} samplers > ${N}: link fails on this GPU`);
        for (const sh of this.getAttachedShaders(prog)) this.detachShader(prog, sh);
        const bad = this.createShader(this.VERTEX_SHADER); this.shaderSource(bad, 'void main() { gl_Position = undefined_symbol; }'); this.compileShader(bad);
        this.attachShader(prog, bad); link.call(this, prog);
      };
    }
  }, units);
  await pg.route(/fonts\.(googleapis|gstatic)\.com/, (r) => r.fulfill({ status: 200, contentType: 'text/css', body: '' }));
  await pg.route(CDN + '**', async (r) => { try { await r.fulfill({ body: await readFile(join(ROOT, 'node_modules/three', r.request().url().slice(CDN.length).split('?')[0])), contentType: 'text/javascript' }); } catch { await r.abort(); } });
  await pg.route(ORIGIN + '**', async (r) => {
    const p = decodeURIComponent(new URL(r.request().url()).pathname).replace(/^\/+/, '') || 'index.html';
    if (p === 'index.html') return r.fulfill({ body: PAGE[mode], contentType: 'text/html', headers: csp && mode === 'pkg' ? { 'Content-Security-Policy': HOST_CSP } : {} });
    let file = null;
    if (mode === 'dev') file = join(ROOT, p);
    else { const e = PKG[p]; if (e !== undefined) file = resolve(ROOT, typeof e === 'string' ? e : e.from); }
    try { if (!file) throw 0; await r.fulfill({ body: await readFile(file), contentType: TYPES[extname(p)] || 'application/octet-stream' }); }
    catch { logs.push(`[404] ${p}`); await r.fulfill({ status: 404, body: '' }); }
  });
  pg.on('console', (m) => { if (['error', 'warning'].includes(m.type()) && !/GL Driver Message|GPU stall|nav path/.test(m.text())) logs.push(`[${m.type()}] ${m.text().slice(0, 300)}`); });
  pg.on('pageerror', (e) => logs.push(`[pageerror] ${e.message.slice(0, 300)}`));
  const q = PRESET[name];
  const url = `${ORIGIN}index.html?${q ? q + '&' : ''}still=1&w=${D.viewport.width}&h=${D.viewport.height}`;
  const t0 = Date.now();
  const png = join(out, `${name}.${mode}.png`);
  let ok = false;
  try {
    await pg.goto(url, { timeout: 900000 });
    await pg.waitForFunction(() => window.__ready === true || window.__fatal, null, { timeout: 900000, polling: 500 });
    const fatal = await pg.evaluate(() => window.__fatal || null);
    if (fatal) logs.push(`[fatal] ${fatal}`);
    await pg.screenshot({ path: png, timeout: 900000 });
    ok = true;
  } catch (e) { logs.push(`[fail] ${e.message.split('\n')[0]}`); }
  await ctx.close();
  const counts = new Map();
  for (const l of logs) { const k = l.replace(/blob:\S+/g, 'blob:*'); counts.set(k, (counts.get(k) || 0) + 1); }
  return { ok, png, s: +((Date.now() - t0) / 1000).toFixed(1), logs: [...counts].map(([k, n]) => (n > 1 ? `${n}x ${k}` : k)) };
}

async function diff(pa, pb, outPng) {
  const [A, B] = await Promise.all([pa, pb].map((p) => sharp(p).removeAlpha().raw().toBuffer({ resolveWithObject: true })));
  if (A.info.width !== B.info.width || A.info.height !== B.info.height) return { share: 1, mean: 255 };
  const n = A.info.width * A.info.height, d = Buffer.alloc(n * 3);
  let over = 0, sum = 0;
  for (let i = 0; i < n; i++) {
    let m = 0;
    for (let c = 0; c < 3; c++) m = Math.max(m, Math.abs(A.data[i * 3 + c] - B.data[i * 3 + c]));
    sum += m;
    if (m > 32) { over++; d[i * 3] = 255; d[i * 3 + 1] = Math.min(255, m * 2); }
    else d[i * 3] = d[i * 3 + 1] = d[i * 3 + 2] = A.data[i * 3 + 1] >> 2; // dimmed package frame for context
  }
  await sharp(d, { raw: { width: A.info.width, height: A.info.height, channels: 3 } }).png().toFile(outPng);
  return { share: +(over / n).toFixed(4), mean: +(sum / n).toFixed(2) };
}

const report = {};
let failed = 0;
for (const name of views) {
  const r = {};
  for (const mode of only ? [only] : ['pkg', 'dev']) r[mode] = await render(mode, name);
  if (r.pkg && r.dev) {
    r.diff = r.pkg.ok && r.dev.ok ? await diff(r.pkg.png, r.dev.png, join(out, `${name}.diff.png`)) : { share: 1 };
    r.pass = r.diff.share <= threshold && !r.pkg.logs.some((l) => /^\d*x? ?\[(error|pageerror|fatal|fail|404)\]/.test(l));
    if (!r.pass) failed++;
  }
  report[name] = r;
  const line = Object.entries(r).filter(([k]) => k === 'pkg' || k === 'dev').map(([k, v]) => `${k} ${v.s}s${v.logs.length ? ` [${v.logs.length} msgs]` : ''}`).join(', ');
  console.log(`${name}: ${line}${r.diff ? `, diff ${(r.diff.share * 100).toFixed(2)}% (mean ${r.diff.mean}) ${r.pass ? 'ok' : 'FAIL'}` : ''}`);
  for (const k of ['pkg', 'dev']) for (const l of r[k]?.logs.slice(0, 6) || []) console.log(`  ${k} ${l}`);
  await writeFile(jsonOut, JSON.stringify({ device, threshold, csp, report }, null, 1));
}
await browser.close();
if (failed) { console.log(`${failed} of ${views.length} views over ${threshold * 100}% or with errors`); process.exitCode = 1; }
