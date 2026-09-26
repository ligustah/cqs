// Verify every ship against the game-derived scale model (see src/lib/scale.js).
//   node tools/scale-check.mjs            -> table + exit code 1 on failure
//   node tools/scale-check.mjs --json     -> raw report
import { openBrowser } from './browser.mjs';
import { carrierLoads, CLASSES } from '../src/lib/scale.js';

const b = await openBrowser();
const { pg, logs } = await b.page();
await pg.goto(`${b.base}index.html?mode=check`);
let report;
try {
  await pg.waitForFunction(() => window.__ready === true, null, { timeout: 180000 });
  report = await pg.evaluate(() => window.__report);
} catch (e) {
  console.error('check failed to run:', e.message.split('\n')[0]);
  for (const l of logs) console.error(l);
  await b.close();
  process.exit(1);
}
await b.close();
if (process.argv.includes('--json')) { console.log(JSON.stringify(report, null, 2)); process.exit(0); }

let ok = true;
for (const [cls, err] of Object.entries(report.errors || {})) { console.log(`ERROR in ${cls}.js: ${err.split('\n').slice(0, 3).join(' | ')}`); ok = false; }
const pad = (s, n) => String(s).padEnd(n);
console.log(`slot volume: ${report.slotVolume} m^3\n`);
console.log(pad('class', 11) + pad('size', 6) + pad('L x B x H (m)', 26) + pad('volume', 10) + pad('slots', 8) + pad('design scale', 14) + pad('tris', 9) + 'draws');
for (const r of report.rows) {
  const flags = [];
  if (r.size && Math.abs(r.slots - r.size) > 0.01) { flags.push('SLOT MISMATCH'); ok = false; }
  if (Math.abs(r.scaleCorrection - 1) > 0.08) { flags.push(`built ${((1 / r.scaleCorrection - 1) * 100).toFixed(0)}% off target size`); }
  console.log(pad(r.cls, 11) + pad(r.size ?? '-', 6) + pad(`${r.L} x ${r.B} x ${r.H}`, 26) + pad(r.volume, 10) + pad(r.slots ?? '-', 8) + pad(r.scaleCorrection, 14) + pad(r.triangles, 9) + r.drawCalls + (flags.length ? '   <- ' + flags.join(', ') : ''));
}
if (report.hangar) {
  console.log(`\ncarrier hangar (clear, L x B x H): ${report.hangar[2]} x ${report.hangar[0]} x ${report.hangar[1]} m`);
  for (const l of report.loads) {
    console.log(`  ${pad(l.cls, 10)} need ${pad(l.need, 3)} fits ${pad(l.fits, 4)} ${l.ok ? 'OK' : 'FAIL'}`);
    if (!l.ok) ok = false;
  }
  if (report.hangarInside) {
    const hi = report.hangarInside;
    const pass = hi.fraction >= 0.95;
    console.log(`  hangar box inside hull: ${(hi.fraction * 100).toFixed(1)}% of ${hi.samples} samples ${pass ? 'OK' : 'FAIL (need >= 95%)'}${pass ? '' : ' escapes ' + JSON.stringify(hi.misses)}`);
    if (!pass) ok = false;
  }
  // Carrier capacity from game data: UnitEnum.CARRIER has spaceTransport = 50 and
  // Fleet.mayLeaveSystem() needs capacity >= the summed getSize() of the carried
  // non-warp ships. The carrier is a 900 m design; report how much smaller it
  // could be before its (scaled) hangar stopped fitting a legal full load.
  const carrierRow = report.rows.find((r) => r.cls === 'carrier');
  if (carrierRow) {
    const env = Object.fromEntries(report.rows.filter((r) => r.size).map((r) => [r.cls, { x: r.B, y: r.H, z: r.L }]));
    const fitsAt = (k) => carrierLoads({ x: report.hangar[0] * k, y: report.hangar[1] * k, z: report.hangar[2] * k }, env).every((l) => l.ok);
    let k = 1;
    if (fitsAt(1)) { while (k > 0.5 && fitsAt(k - 0.005)) k -= 0.005; }
    const tight = carrierLoads({ x: report.hangar[0] * k, y: report.hangar[1] * k, z: report.hangar[2] * k }, env).filter((l) => l.fits === l.need).map((l) => l.cls);
    console.log(`  capacity ${CLASSES.carrier.capacity} slots (UnitEnum.CARRIER spaceTransport); loads: ${report.loads.map((l) => `${l.need} ${l.cls} x ${CLASSES[l.cls].size}`).join(', ')}`);
    if (fitsAt(1)) console.log(`  smallest carrier whose hangar would still fit every load: ${(carrierRow.L * k).toFixed(1)} m (binding: ${tight.join(', ') || '-'}); built: ${carrierRow.L} m (design length)`);
    else console.log(`  the hangar does not fit every legal load at ${carrierRow.L} m`);
  }
  const carrier = report.rows.find((r) => r.cls === 'carrier');
  const hv = report.hangar[0] * report.hangar[1] * report.hangar[2];
  if (carrier && hv > carrier.volume * 0.6) { console.log('  hangar volume implausibly large for the hull'); ok = false; }
} else { console.log('\ncarrier hangar anchor missing'); ok = false; }
console.log(ok ? '\nSCALE CHECK PASSED' : '\nSCALE CHECK FAILED');
process.exit(ok ? 0 : 1);
