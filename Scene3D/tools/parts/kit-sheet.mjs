// Render the parts kit sheet (multi-row, one scale): node kit2.mjs out.webp
import { openBrowser } from '../browser.mjs';
import { readFile } from 'node:fs/promises';
import sharp from 'sharp';
const out = process.argv[2];
const man = JSON.parse(await readFile(new URL('../../assets/parts/parts.json', import.meta.url), 'utf8'));
const ROW2 = ['pdc', 'torpedoDoor', 'sensorArray', 'dockingClamp', 'missilePod', 'bell', 'radiator'];
const ROW3 = ['turret', 'twinBarrel', 'engineHousing', 'railgunSegment', 'railgunMuzzle'];
const rowOf = (n) => (ROW2.includes(n) ? 1 : ROW3.includes(n) ? 2 : 0);
const order = (n) => { const r = rowOf(n); return r === 1 ? ROW2.indexOf(n) : r === 2 ? ROW3.indexOf(n) : 0; };
const fmt = (v) => +v.toFixed(2);
const parts = Object.entries(man.parts).map(([name, p]) => ({ name, row: rowOf(name), ord: order(name), file: '/assets/parts/' + p.file,
  standUp: p.mount.normal === '+Z' && ['dome', 'floodlight'].includes(name),
  rotY: name === 'bell' ? 90 : name === 'engineHousing' ? 180 : undefined,
  label: name === 'turret' ? `turret (M)  base 8 m, ${p.size.map(fmt).join(' × ')} m` : name === 'bell' ? `bell r 2.2  ${p.size.map(fmt).join(' × ')} m` : `${name}  ${p.size.map(fmt).join(' × ')} m` }))
  .sort((a, b) => a.row - b.row || a.ord - b.ord);
const W = 3600, H = 2300;
const b = await openBrowser();
const { pg, ctx, logs } = await b.page({ w: W, h: H });
await pg.route(b.base + 'kit/kit.html*', async (r) => r.fulfill({ body: await readFile(new URL('./kit2.html', import.meta.url)), contentType: 'text/html' }));
await pg.goto(`${b.base}kit/kit.html?` + new URLSearchParams({ w: W, h: H, parts: JSON.stringify(parts) }));
await pg.waitForFunction(() => window.__ready || window.__error, null, { timeout: 400000, polling: 250 });
const err = await pg.evaluate(() => window.__error); if (err) { console.error(err, logs); process.exit(1); }
const labels = await pg.evaluate(() => window.__labels);
const png = await pg.screenshot();
await ctx.close(); await b.close();
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => `&#${c.charCodeAt(0)};`);
const svg = [`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">`,
  `<text x="24" y="46" font-family="DejaVu Sans" font-size="32" font-weight="700" fill="#1b1c1e">CQS parts kit — every part at true relative size, one scale for all rows (metres; ground ticks every 1 m; turret at M, bell at exit r 2.2 m)</text>`];
let prevY = null, k = 0, maxY = 0;
labels.forEach((l) => {
  if (prevY == null || Math.abs(l.y - prevY) > 5) k = 0; prevY = l.y;
  const nl = l.y < H * 0.3 ? 3 : 2; const y = l.y + 50 + (k++ % nl) * 27; maxY = Math.max(maxY, y);
  svg.push(`<text x="${Math.min(W - 200, Math.max(200, l.x))}" y="${y}" text-anchor="middle" font-family="DejaVu Sans" font-size="19" font-weight="600" fill="#1b1c1e">${esc(l.label)}</text>`);
});
svg.push('</svg>');
const full = await sharp(png).composite([{ input: Buffer.from(svg.join('')) }]).png().toBuffer();
await sharp(full).extract({ left: 0, top: 0, width: W, height: Math.min(H, Math.ceil(maxY + 30)) }).webp({ quality: 88 }).toFile(out);
console.log('ok', out, logs.slice(0, 5));
