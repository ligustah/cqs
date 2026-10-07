// Before / after sheet for a remodelled colony building: concept | old | new at the building camera, then rows of
// close-ups at matched cameras (old | new, with the concept's crop of the same area), each at 1:1 pixels.
//   node tools/buildings/sheet-v4.mjs <out.jpg> --title "steel_mill" --row "label|concept.jpg|old.png|new.png[|cx,cy,cw,ch]" ...
//        [--cols "v4 (remodelled),v5 (second review)"]   (the old / new column names; default v3 / v4)
// A row's optional crop box (cx, cy, cw, ch) is taken from the concept (pixels) and scaled to the row's cell height;
// the old / new images are placed unscaled when they fit the cell (1:1), else scaled down.
import sharp from 'sharp';

const args = process.argv.slice(2);
const out = args[0];
const opt = (k) => { const i = args.indexOf(`--${k}`); return i < 0 ? null : args[i + 1]; };
const rows = [];
for (let i = 0; i < args.length; i++) if (args[i] === '--row') rows.push(args[i + 1].split('|'));
const title = opt('title') || '';
const cols = (opt('cols') || 'v3 (fal components),v4 (remodelled)').split(',');
const W = 1152, H = 768, PAD = 14, LAB = 30;
const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
const label = (txt, w) => Buffer.from(`<svg width="${w}" height="${LAB}"><text x="8" y="21" font-family="DejaVu Sans, sans-serif" font-size="17" font-weight="bold" fill="#e8ecef">${esc(txt)}</text></svg>`);
const comps = [];
let y = PAD;
comps.push({ input: label(title, 3 * W), top: y, left: PAD }); y += LAB;
for (const r of rows) {
  const [lab, concept, a, b, crop] = r;
  const names = [`${lab}: concept`, `${lab}: ${cols[0]}`, `${lab}: ${cols[1]}`];
  const imgs = [];
  if (crop) {
    const [cx, cy, cw, ch] = crop.split(',').map(Number);
    imgs.push(await sharp(concept).extract({ left: cx, top: cy, width: cw, height: ch }).resize(W, H, { fit: 'contain', background: '#151a20' }).toBuffer());
  } else imgs.push(await sharp(concept).resize(W, H, { fit: 'contain', background: '#151a20' }).toBuffer());
  for (const f of [a, b]) imgs.push(await sharp(f).resize(W, H, { fit: 'inside', withoutEnlargement: true }).toBuffer());
  for (let k = 0; k < 3; k++) {
    comps.push({ input: label(names[k], W), top: y, left: PAD + k * (W + PAD) });
    comps.push({ input: imgs[k], top: y + LAB, left: PAD + k * (W + PAD) });
  }
  y += LAB + H + PAD;
}
await sharp({ create: { width: 3 * W + 4 * PAD, height: y, channels: 3, background: '#151a20' } }).composite(comps).jpeg({ quality: 86 }).toFile(out);
console.log(out);
