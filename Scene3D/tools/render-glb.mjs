// Inspection stills of any GLB (mesh step of the asset pipeline): studio light, auto framing,
// axis gizmo (+Z = bow), one PNG per angle plus a labelled contact sheet; prints the mesh info JSON.
//   node tools/render-glb.mjs <file.glb> <outPrefix> [--rot x,y,z] [--angles "az:el,az:el,..."]
//        [--w 900 --h 650] [--bg light|dark] [--wire] [--fov 30] [--timeout 240000]
// Writes <outPrefix>-<az>_<el>.png, <outPrefix>-sheet.png and <outPrefix>-info.json.
// The info JSON goes to stdout, progress and page logs to stderr.
import { access, mkdir, symlink, unlink, writeFile } from 'node:fs/promises';
import { basename, dirname, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { randomBytes } from 'node:crypto';
import sharp from 'sharp';
import { openBrowser } from './browser.mjs';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
const NAMES = { '35:20': 'three-quarter front-left', '90:0': 'left side (port)', '0:89': 'top', '180:10': 'rear', '0:5': 'front', '35:-30': 'below' };

const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf(`--${k}`); if (i < 0) return d; const v = args[i + 1]; args.splice(i, 2); return v; };
const flag = (k) => { const i = args.indexOf(`--${k}`); if (i < 0) return false; args.splice(i, 1); return true; };
const w = parseInt(opt('w', '900')), h = parseInt(opt('h', '650')), timeout = parseInt(opt('timeout', '240000'));
const rot = opt('rot', '0,0,0'), bg = opt('bg', 'light'), fov = opt('fov', '30');
const angles = opt('angles', Object.keys(NAMES).join(',')).split(',').map((s) => s.trim().split(':').map(Number));
const wire = flag('wire');
const [input, outPrefix] = args;
if (!input || !outPrefix || angles.some((a) => a.length !== 2 || a.some((v) => !Number.isFinite(v)))) {
  console.error('usage: render-glb.mjs <file.glb> <outPrefix> [--rot x,y,z] [--angles "az:el,..."] [--w 900 --h 650] [--bg light|dark] [--wire]');
  process.exit(2);
}

// make the file reachable by the static server (rooted at Scene3D): link its folder under .glbtmp/
const abs = resolve(input);
await access(abs).catch(() => { console.error(`FAIL ${input}: file not found`); process.exit(1); });
let rel = relative(ROOT, abs), link = null;
if (rel.startsWith('..') || resolve(ROOT, rel) !== abs) {
  link = resolve(ROOT, '.glbtmp', `${process.pid}-${randomBytes(3).toString('hex')}`);
  await mkdir(dirname(link), { recursive: true });
  await symlink(dirname(abs), link, 'dir');
  rel = relative(ROOT, resolve(link, basename(abs)));
}
const src = rel.split(sep).map(encodeURIComponent).join('/');
const cleanup = async () => { if (link) { await unlink(link).catch(() => {}); link = null; } };
process.on('SIGINT', async () => { await cleanup(); process.exit(130); });

const b = await openBrowser();
const shots = [];
let info = null, failed = false;
const { pg, ctx, logs } = await b.page({ w, h });
try {
  const [az0, el0] = angles[0];
  const t0 = Date.now();
  const qs = new URLSearchParams({ src, rot, az: az0, el: el0, w, h, bg, fov, wire: wire ? 1 : 0 });
  await pg.goto(`${b.base}tools/glb-view.html?${qs}`);
  await pg.waitForFunction(() => window.__ready === true || window.__error, null, { timeout, polling: 250 });
  const err = await pg.evaluate(() => window.__error);
  if (err) throw new Error(err);
  info = await pg.evaluate(() => window.__info);
  console.error(`load ${input}  (${((Date.now() - t0) / 1000).toFixed(1)}s)`);
  await mkdir(dirname(resolve(outPrefix)), { recursive: true });
  for (const [i, [az, el]] of angles.entries()) {
    const t1 = Date.now();
    if (i > 0) await pg.evaluate((v) => window.__render(v), { az, el });
    const out = `${outPrefix}-${az}_${el}.png`;
    await pg.screenshot({ path: out });
    shots.push({ az, el, out });
    console.error(`ok   ${out}  (${((Date.now() - t1) / 1000).toFixed(1)}s)`);
  }
} catch (e) {
  failed = true;
  console.error(`FAIL ${input}: ${e.message.split('\n').slice(0, 4).join('\n     ')}`);
}
for (const l of logs.slice(0, 20)) console.error('     ' + l);
await ctx.close();
await b.close();
await cleanup();

if (shots.length) {
  const out = `${outPrefix}-sheet.png`;
  await contactSheet(out);
  console.error(`ok   ${out}`);
}
if (info) {
  // pretty, but with short arrays (bbox, rot, maps) kept on one line
  const json = JSON.stringify(info, null, 2).replace(/\[\s+([^[\]{}]*?)\s+\]/g, (_, a) => `[${a.replace(/,\s+/g, ', ')}]`);
  await writeFile(`${outPrefix}-info.json`, json + '\n');
  console.log(json);
}
process.exit(failed ? 1 : 0);

async function contactSheet(out) {
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => `&#${c.charCodeAt(0)};`);
  const dark = bg === 'dark';
  const [fg, dim, back] = dark ? ['#e8e8e8', '#9a9ea6', '#131417'] : ['#1b1c1e', '#5d6168', '#f3f3f1'];
  const cols = Math.min(3, shots.length), rows = Math.ceil(shots.length / cols);
  const tw = Math.min(w, Math.floor(2400 / cols)), th = Math.round((h * tw) / w);
  const gap = 8, cap = 30, head = 58;
  const W = cols * tw + (cols + 1) * gap, H = head + rows * (th + cap + gap) + gap;
  const text = (x, y, s, size, color, weight = 400) =>
    `<text x="${x}" y="${y}" font-family="DejaVu Sans, sans-serif" font-size="${size}" font-weight="${weight}" fill="${color}">${esc(s)}</text>`;
  const sz = info ? info.bbox.size.map((v) => +v.toPrecision(4)).join(' x ') : '?';
  const facts = info
    ? `${info.tris.toLocaleString('en')} tris · ${info.meshes} mesh${info.meshes === 1 ? '' : 'es'} · ${info.materials.length} material${info.materials.length === 1 ? '' : 's'} · bbox ${sz} (longest ${info.longestAxis}) · rot ${rot}`
    : '';
  const svg = [`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">`,
    text(gap + 2, 26, basename(input), 20, fg, 700), text(gap + 2, 48, facts, 14, dim)];
  const layers = [];
  for (const [i, s] of shots.entries()) {
    const x = gap + (i % cols) * (tw + gap), y = head + Math.floor(i / cols) * (th + cap + gap);
    layers.push({ input: await sharp(s.out).resize(tw, th).toBuffer(), left: x, top: y });
    const name = NAMES[`${s.az}:${s.el}`];
    svg.push(text(x + 2, y + th + 21, `az ${s.az}°  el ${s.el}°${name ? '  ·  ' + name : ''}`, 15, fg, 600));
  }
  svg.push('</svg>');
  await sharp({ create: { width: W, height: H, channels: 3, background: back } })
    .composite([...layers, { input: Buffer.from(svg.join('')), left: 0, top: 0 }])
    .png().toFile(out);
}
