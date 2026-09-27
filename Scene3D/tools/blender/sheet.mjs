// Headless render of tools/blender/kit-view.html (the parts kit through the runtime livery).
//   node tools/blender/sheet.mjs out.png "files=all&livery=dark&w=2400&h=900"
//   node tools/blender/sheet.mjs --kit     # assets/parts-blender/kit-sheet.webp + kit-close.webp
// out: .png or .webp (by extension).
import sharp from 'sharp';
import { openBrowser } from '../browser.mjs';
import { fileURLToPath } from 'node:url';
import { readFile } from 'node:fs/promises';

const ROOT = fileURLToPath(new URL('../..', import.meta.url));

async function shoot(b, qs, out) {
  const p = new URLSearchParams(qs);
  const w = +(p.get('w') || 1600), h = +(p.get('h') || 900);
  const { pg, ctx, logs } = await b.page({ w, h });
  await pg.goto(`${b.base}tools/blender/kit-view.html?${qs}`);
  await pg.waitForFunction(() => window.__ready || window.__error, null, { timeout: 600000, polling: 500 });
  const err = await pg.evaluate(() => window.__error);
  if (err) throw new Error(err + '\n' + logs.join('\n'));
  const png = await pg.screenshot();
  await ctx.close();
  if (out?.endsWith('.webp')) await sharp(png).webp({ quality: 90 }).toFile(out);
  else if (out) await sharp(png).toFile(out);
  for (const l of logs.slice(0, 10)) console.error('  ' + l);
  if (out) console.log(`ok ${out}`);
  return png;
}

const args = process.argv.slice(2);
const b = await openBrowser();
try {
  if (args[0] === '--kit') {
    const man = JSON.parse(await readFile(`${ROOT}assets/parts-blender/parts.json`, 'utf8'));
    const all = Object.keys(man.parts);
    const maxd = (f) => Math.max(...man.parts[f].bbox.size);
    const rows = [
      ['Parts kit (Blender, procedural) — large parts', all.filter((f) => maxd(f) > 12), 900],
      ['Medium parts', all.filter((f) => maxd(f) > 3.2 && maxd(f) <= 12), 700],
      ['Human-scale parts', all.filter((f) => maxd(f) <= 3.2), 700],
    ];
    const sub = 'true relative size within each row · 1.8 m crew box (orange) · dark operational livery (src/lib/livery.js) · ortho';
    const W = 3000;
    const layers = [];
    let top = 0;
    for (const [title, files, h] of rows) {
      const png = await shoot(b, `files=${files.join(',')}&livery=dark&w=${W}&h=${h}&az=14&el=13&title=${encodeURIComponent(title)}&sub=${encodeURIComponent(sub)}`, null);
      layers.push({ input: png, left: 0, top }); top += h;
    }
    await sharp({ create: { width: W, height: top, channels: 3, background: '#101216' } })
      .composite(layers).webp({ quality: 88 })
      .toFile(`${ROOT}assets/parts-blender/kit-sheet.webp`);
    console.log('ok assets/parts-blender/kit-sheet.webp');
    await shoot(b, `files=door,port,pane,turret-M&layout=grid&cols=2&livery=dark&w=2000&h=1560&az=30&el=14&human=0&zooms=turret-M:0.72&title=${encodeURIComponent('Close-ups, dark livery')}`, `${ROOT}assets/parts-blender/kit-close.webp`);
  } else {
    await shoot(b, args[1] || 'files=all', args[0]);
  }
} finally {
  await b.close();
}
