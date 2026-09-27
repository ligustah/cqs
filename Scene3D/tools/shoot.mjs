// Render stills of the scene.
//   node tools/shoot.mjs "mode=ship&ship=fighter&az=35&el=20" shots/fighter.png [more pairs...]
// Options: --w 1280 --h 800 --timeout 180000 --net (allow Google Fonts via proxy) --ui (keep overlay)
import { mkdir } from 'node:fs/promises';
import { dirname } from 'node:path';
import { openBrowser } from './browser.mjs';

const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf(`--${k}`); if (i < 0) return d; const v = args[i + 1]; args.splice(i, 2); return v; };
const flag = (k) => { const i = args.indexOf(`--${k}`); if (i < 0) return false; args.splice(i, 1); return true; };
const w = parseInt(opt('w', '1280')), h = parseInt(opt('h', '800')), timeout = parseInt(opt('timeout', '240000'));
const net = flag('net'), ui = flag('ui');
if (args.length < 2 || args.length % 2) { console.error('usage: shoot.mjs "<query>" <out.png> [...]'); process.exit(2); }

const b = await openBrowser({ net });
let failed = false;
for (let i = 0; i < args.length; i += 2) {
  const q = args[i].replace(/^\?/, ''), out = args[i + 1];
  const { pg, ctx, logs } = await b.page({ w, h });
  const t0 = Date.now();
  const still = ui ? '' : `&still=1&w=${w}&h=${h}`;
  try {
    await pg.goto(`${b.base}index.html?${q}${still}`, { timeout });
    await pg.waitForFunction(() => window.__ready === true, null, { timeout, polling: 250 });
    if (ui) await pg.waitForTimeout(parseInt(opt('settle', '4000')));
    await mkdir(dirname(out), { recursive: true });
    // a fleet frame in software WebGL can take ~40 s, past Playwright's 30 s default
    await pg.screenshot({ path: out, timeout });
    console.log(`ok   ${out}  (${((Date.now() - t0) / 1000).toFixed(1)}s)`);
  } catch (e) {
    failed = true;
    console.log(`FAIL ${out}: ${e.message.split('\n')[0]}`);
  }
  for (const l of logs.slice(0, 20)) console.log('     ' + l);
  await ctx.close();
}
await b.close();
process.exit(failed ? 1 : 0);
