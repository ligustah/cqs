// Thumbnail readability test (STYLE.md "Thumbnail readability"): the game shows every unit and
// building as a square icon, 80 px (current job, hover) and 40 px (queues, job lists), on the
// dark UI panel #222d35. This makes those icons from concept images or renders and lays them out
// on one sheet, so a judge can check that each asset is identifiable and distinct from its siblings.
//
//   node tools/thumbs/thumbs.mjs <sheet.png> "Label=path/to/image.png" ... [options]
//     --sizes 80,40    icon sizes in px (first is the large one)
//     --bg '#222d35'   UI panel colour behind the icons
//     --pad 0.06       margin round the trimmed subject, as a share of its longer side
//     --no-trim        keep the whole image (default: trim the studio background first)
//     --threshold 10   edge strength that counts as subject when trimming
//     --zoom 3         nearest-neighbour enlargement of each icon on the sheet, to show its pixels
//     --icons <dir>    also write each icon as <dir>/<label>-<size>.png
//   An item may carry a crop before the trim: "Label=path.png@x,y,w,h" (pixels).
//
// Each row: label | the icons at 1:1 | the same icons enlarged (nearest) so the pixel content shows.
// Prints a JSON summary: per item, the trimmed subject's aspect (w/h) and its fill of the square.
import sharp from 'sharp';
import { mkdir } from 'node:fs/promises';
import { join } from 'node:path';

const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf(`--${k}`); if (i < 0) return d; const v = args[i + 1]; args.splice(i, 2); return v; };
const flag = (k) => { const i = args.indexOf(`--${k}`); if (i < 0) return false; args.splice(i, 1); return true; };
const sizes = opt('sizes', '80,40').split(',').map(Number);
const bg = opt('bg', '#222d35');
const pad = parseFloat(opt('pad', '0.06'));
const threshold = parseInt(opt('threshold', '10'));
const zoom = parseInt(opt('zoom', '3'));
const iconsDir = opt('icons', null);
const noTrim = flag('no-trim');
const [out, ...items] = args;
if (!out || !items.length) {
  console.error('usage: thumbs.mjs <sheet.png> "Label=image.png[@x,y,w,h]" ... [--sizes 80,40] [--bg #222d35] [--zoom 3] [--icons dir]');
  process.exit(2);
}

const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const text = (w, h, s, size = 18, color = '#e8edf2', weight = 600) => Buffer.from(
  `<svg width="${w}" height="${h}" xmlns="http://www.w3.org/2000/svg"><text x="0" y="${Math.round(h * 0.7)}" font-family="DejaVu Sans, sans-serif" font-size="${size}" font-weight="${weight}" fill="${color}">${esc(s)}</text></svg>`);

async function icon(file, crop) {
  let img = sharp(file).flatten({ background: '#ffffff' });
  if (crop) img = img.extract({ left: crop[0], top: crop[1], width: crop[2], height: crop[3] });
  let buf = await img.png().toBuffer();
  // the corner pixel is the studio background colour; it also fills the square's margin
  const { data } = await sharp(buf).extract({ left: 0, top: 0, width: 1, height: 1 }).raw().toBuffer({ resolveWithObject: true });
  const corner = { r: data[0], g: data[1], b: data[2] };
  if (!noTrim) {
    // subject box from edge energy, so a vignetted or graded studio background is not mistaken for subject
    const g = await sharp(buf).greyscale().blur(1.2).raw().toBuffer({ resolveWithObject: true });
    const { width: w, height: h } = g.info, px = g.data;
    const cols = new Uint32Array(w), rows = new Uint32Array(h);
    for (let y = 1; y < h - 1; y++) for (let x = 1; x < w - 1; x++) {
      const i = y * w + x;
      const e = Math.abs(4 * px[i] - px[i - 1] - px[i + 1] - px[i - w] - px[i + w]);
      if (e > threshold) { cols[x]++; rows[y]++; }
    }
    const span = (a, n) => { const min = Math.max(2, Math.round(n * 0.004)); let lo = 0, hi = a.length - 1; while (lo < hi && a[lo] < min) lo++; while (hi > lo && a[hi] < min) hi--; return [lo, hi]; };
    const [x0, x1] = span(cols, h), [y0, y1] = span(rows, w);
    if (x1 - x0 > 8 && y1 - y0 > 8) buf = await sharp(buf).extract({ left: x0, top: y0, width: x1 - x0 + 1, height: y1 - y0 + 1 }).png().toBuffer();
  }
  const m = await sharp(buf).metadata();
  const side = Math.round(Math.max(m.width, m.height) * (1 + 2 * pad));
  const sq = await sharp(buf).extend({
    top: Math.floor((side - m.height) / 2), bottom: Math.ceil((side - m.height) / 2),
    left: Math.floor((side - m.width) / 2), right: Math.ceil((side - m.width) / 2),
    background: corner,
  }).png().toBuffer();
  const icons = {};
  for (const s of sizes) icons[s] = await sharp(sq).resize(s, s, { kernel: 'lanczos3' }).png().toBuffer();
  return { icons, aspect: +(m.width / m.height).toFixed(2), fill: +((m.width * m.height) / (side * side)).toFixed(2) };
}

const rows = [];
for (const it of items) {
  const eq = it.indexOf('=');
  const label = it.slice(0, eq);
  let path = it.slice(eq + 1), crop = null;
  const at = path.lastIndexOf('@');
  if (at > 0 && /^\d+,\d+,\d+,\d+$/.test(path.slice(at + 1))) { crop = path.slice(at + 1).split(',').map(Number); path = path.slice(0, at); }
  rows.push({ label, path, ...(await icon(path, crop)) });
}

if (iconsDir) {
  await mkdir(iconsDir, { recursive: true });
  for (const r of rows) for (const s of sizes) await sharp(r.icons[s]).toFile(join(iconsDir, `${r.label.replace(/[^\w.-]+/g, '_')}-${s}.png`));
}

// layout
const M = 16, LABEL_W = 260, GAP = 14;
const big = sizes[0];
const rowH = Math.max(big * zoom, 60) + 2 * M;
const oneToOneW = sizes.reduce((a, s) => a + s + GAP, 0);
const zoomW = sizes.reduce((a, s) => a + s * zoom + GAP, 0); // each icon enlarged by zoom
const W = Math.max(980, M + LABEL_W + oneToOneW + GAP * 2 + zoomW + M);
const HEAD = 56;
const H = HEAD + rows.length * rowH + M;
const layers = [
  { input: text(W - 2 * M, 30, `Thumbnail test: square icons at ${sizes.join(' and ')} px on ${bg}. Left 1:1, right enlarged ${zoom}x (nearest)`, 15), left: M, top: 12 },
];
rows.forEach((r, i) => {
  const y = HEAD + i * rowH;
  layers.push({ input: text(LABEL_W - 10, 28, r.label, 17), left: M, top: y + M });
  layers.push({ input: text(LABEL_W - 10, 22, `aspect ${r.aspect}  fill ${r.fill}`, 13, '#9fb0bf', 400), left: M, top: y + M + 30 });
  let x = M + LABEL_W;
  for (const s of sizes) { layers.push({ input: r.icons[s], left: x, top: y + M }); x += s + GAP; }
  x += GAP * 2;
  for (const s of sizes) { layers.push({ s, left: x, y }); x += s * zoom + GAP; } // enlarged, filled below
});
// enlarged icons need async resize; replace placeholders
const final = [];
for (const l of layers) {
  if (l.input) { final.push(l); continue; }
  const r = rows[Math.round((l.y - HEAD) / rowH)];
  final.push({ input: await sharp(r.icons[l.s]).resize(l.s * zoom, l.s * zoom, { kernel: 'nearest' }).png().toBuffer(), left: l.left, top: l.y + M });
}
await sharp({ create: { width: Math.round(W), height: H, channels: 3, background: bg } }).composite(final).png().toFile(out);
console.log(JSON.stringify({ sheet: out, sizes, items: rows.map((r) => ({ label: r.label, path: r.path, aspect: r.aspect, fill: r.fill })) }, null, 1));
