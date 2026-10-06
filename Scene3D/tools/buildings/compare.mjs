// Compare a colony building with its approved concept (brief: style-library/styles/cqs-fleet/briefs/buildings.md).
// Renders the building view at the concept's camera (the module's studio az / el hint, or --az / --el: an elevated
// three-quarter view 27-35 deg down from the front-left, the dusk-blue studio) at the concept's 3:2 frame, then writes
// one sheet: concept | old procedural render | new render (labelled), and below it each one's 80 px and 40 px icon
// on the game's UI panel (#222d35), trimmed like tools/thumbs/thumbs.mjs.
//
//   node tools/buildings/compare.mjs <id> [--version v1] [--az 30] [--el 27] [--dist 1] [--w 1152 --h 768]
//        [--render existing.png] [--out sheet.jpg] [--extra "label=query" ...]
// Writes  style-library/styles/cqs-fleet/images/buildings/<id>-<version>.jpg   (the sheet, ~1-2 MB jpg)
//         shots/buildings/<id>-<version>.png                                     (the raw render, gitignored)
// --extra adds more renders of the same building (e.g. a close-up "close=focus=0,10,12&dist=60") as a second row.
import sharp from 'sharp';
import { mkdir, access } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

const ROOT = fileURLToPath(new URL('../..', import.meta.url));
const REPO = resolve(ROOT, '..');
const IMG = join(REPO, 'style-library/styles/cqs-fleet/images/buildings');
const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf(`--${k}`); if (i < 0) return d; const v = args[i + 1]; args.splice(i, 2); return v; };
const multi = (k) => { const out = []; let i; while ((i = args.indexOf(`--${k}`)) >= 0) out.push(args.splice(i, 2)[1]); return out; };
const version = opt('version', 'v1');
const W = parseInt(opt('w', '1152')), H = parseInt(opt('h', '768'));
const az = opt('az', null), el = opt('el', null), dist = opt('dist', null);
const given = opt('render', null);
const outArg = opt('out', null);
const extras = multi('extra');
const id = args[0];
if (!id) { console.error('usage: compare.mjs <id> [--version v1] [--az deg] [--el deg] [--dist k] [--render png] [--extra "label=query"]'); process.exit(2); }

const shots = join(ROOT, 'shots/buildings');
await mkdir(shots, { recursive: true });
const shoot = (query, out) => {
  execFileSync('node', [join(ROOT, 'tools/shoot.mjs'), query, out, '--w', String(W), '--h', String(H), '--timeout', '900000'], { stdio: 'inherit', cwd: ROOT });
};
const render = given ? resolve(given) : join(shots, `${id}-${version}.png`);
if (!given) {
  const q = new URLSearchParams({ mode: 'building', building: id, t: '20' });
  if (az) q.set('az', az);
  if (el) q.set('el', el);
  if (dist) q.set('dist', dist);
  shoot(q.toString(), render);
}
const extraShots = [];
for (const e of extras) {
  const [label, query] = [e.slice(0, e.indexOf('=')), e.slice(e.indexOf('=') + 1)];
  const out = join(shots, `${id}-${version}-${label}.png`);
  shoot(`mode=building&building=${id}&t=20&${query}`, out);
  extraShots.push([label, out]);
}

const exists = async (p) => { try { await access(p); return true; } catch { return false; } };
const cells = [['concept', join(IMG, `${id}-concept.jpg`)], ['old render', join(IMG, `${id}-old-render.jpg`)], [`new ${version}`, render]];
const CW = 768, CH = 512, LBL = 34, ICON = 80, ICON2 = 40, PAD = 16;
const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const label = (w, h, s, size = 20) => Buffer.from(`<svg width="${w}" height="${h}" xmlns="http://www.w3.org/2000/svg"><text x="10" y="${Math.round(h * 0.72)}" font-family="DejaVu Sans, sans-serif" font-size="${size}" font-weight="600" fill="#e8edf2">${esc(s)}</text></svg>`);

// trim the studio background: the subject is where the image differs from its border colour
async function icon(path, size) {
  const img = sharp(path).removeAlpha();
  const { data, info } = await img.clone().raw().toBuffer({ resolveWithObject: true });
  const { width: w, height: h, channels: ch } = info;
  const px = (x, y) => { const i = (y * w + x) * ch; return [data[i], data[i + 1], data[i + 2]]; };
  // background reference: the median of the four corners' 8x8 blocks, per row (gradient backdrops vary with y)
  let x0 = w, y0 = h, x1 = 0, y1 = 0;
  const rowBg = (y) => { const a = px(2, y), b = px(w - 3, y); return a.map((v, k) => (v + b[k]) / 2); };
  for (let y = 0; y < h; y += 2) {
    const bg = rowBg(y);
    for (let x = 0; x < w; x += 2) {
      const p = px(x, y);
      if (Math.abs(p[0] - bg[0]) + Math.abs(p[1] - bg[1]) + Math.abs(p[2] - bg[2]) > 36) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
    }
  }
  if (x1 <= x0 || y1 <= y0) { x0 = 0; y0 = 0; x1 = w - 1; y1 = h - 1; }
  const side = Math.round(Math.max(x1 - x0, y1 - y0) * 1.08);
  const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
  const L = Math.max(0, Math.round(cx - side / 2)), T = Math.max(0, Math.round(cy - side / 2));
  const cw = Math.min(side, w - L), chh = Math.min(side, h - T);
  const crop = await sharp(path).extract({ left: L, top: T, width: cw, height: chh }).resize(size, size, { fit: 'contain', background: '#222d35' }).flatten({ background: '#222d35' }).png().toBuffer();
  return { buf: crop, aspect: +((x1 - x0) / (y1 - y0)).toFixed(2) };
}

const rows = [];
const comps = [];
const SW = PAD + cells.length * (CW + PAD);
let y = PAD;
for (const [i, [name, path]] of cells.entries()) {
  const x = PAD + i * (CW + PAD);
  comps.push({ input: label(CW, LBL, `${id} — ${name}`), left: x, top: y });
  if (await exists(path)) comps.push({ input: await sharp(path).resize(CW, CH, { fit: 'cover' }).toBuffer(), left: x, top: y + LBL });
}
y += LBL + CH + PAD;
// icon row: 80 and 40 px on the UI panel, shown 1:1 and 3x enlarged (nearest)
const iconInfo = {};
for (const [i, [name, path]] of cells.entries()) {
  if (!(await exists(path))) continue;
  const x = PAD + i * (CW + PAD);
  const big = await icon(path, ICON), small = await icon(path, ICON2);
  iconInfo[name] = big.aspect;
  comps.push({ input: big.buf, left: x, top: y });
  comps.push({ input: small.buf, left: x + ICON + 12, top: y + ICON - ICON2 });
  comps.push({ input: await sharp(big.buf).resize(ICON * 3, ICON * 3, { kernel: 'nearest' }).toBuffer(), left: x + ICON + ICON2 + 28, top: y });
  comps.push({ input: await sharp(small.buf).resize(ICON2 * 3, ICON2 * 3, { kernel: 'nearest' }).toBuffer(), left: x + ICON + ICON2 + 40 + ICON * 3, top: y + ICON * 3 - ICON2 * 3 });
  comps.push({ input: label(260, 26, `icon aspect ${big.aspect}`, 15), left: x + ICON + ICON2 + 40 + ICON * 3 + ICON2 * 3 + 8, top: y + ICON * 3 - 26 });
}
y += ICON * 3 + PAD;
if (extraShots.length) {
  for (const [i, [name, path]] of extraShots.entries()) {
    const x = PAD + (i % cells.length) * (CW + PAD);
    comps.push({ input: label(CW, LBL, `${id} — ${name}`), left: x, top: y });
    comps.push({ input: await sharp(path).resize(CW, CH, { fit: 'cover' }).toBuffer(), left: x, top: y + LBL });
  }
  y += LBL + CH + PAD;
}
const out = outArg ? resolve(outArg) : join(IMG, `${id}-${version}.jpg`);
await sharp({ create: { width: SW, height: y, channels: 3, background: '#161b22' } }).composite(comps).jpeg({ quality: 86 }).toFile(out);
console.log(JSON.stringify({ sheet: out, render, iconAspect: iconInfo }));
