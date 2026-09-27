// Shared headless-Chromium setup for screenshots and checks.
// three.js is served from node_modules instead of the CDN so runs are offline.
import { chromium } from 'playwright-core';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { join } from 'node:path';
import { startServer } from './serve.mjs';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
const CDN = 'https://cdn.jsdelivr.net/npm/three@0.186.1/';

export async function openBrowser({ net = false } = {}) {
  const server = await startServer(0);
  const base = `http://127.0.0.1:${server.address().port}/`;
  const browser = await chromium.launch({
    args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--enable-webgl'],
    ...(net && process.env.HTTPS_PROXY ? { proxy: { server: process.env.HTTPS_PROXY } } : {}),
  });
  async function page({ w = 1280, h = 800 } = {}) {
    const ctx = await browser.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
    const pg = await ctx.newPage();
    await pg.route(CDN + '**', async (route) => {
      const rel = route.request().url().slice(CDN.length);
      try {
        const body = await readFile(join(ROOT, 'node_modules/three', rel));
        await route.fulfill({ body, contentType: 'text/javascript' });
      } catch { await route.abort(); }
    });
    // offline: answer the Google Fonts requests with an empty stylesheet / font (the page falls
    // back to its system fonts) instead of aborting them, so real console errors are not buried
    // under a 'Failed to load resource' line on every shot
    if (!net) await pg.route(/fonts\.(googleapis|gstatic)\.com/, (r) => r.fulfill({ status: 200, contentType: /googleapis/.test(r.request().url()) ? 'text/css' : 'font/woff2', body: '' }));
    const logs = [];
    pg.on('console', (m) => { if (['error', 'warning'].includes(m.type())) logs.push(`[${m.type()}] ${m.text()}`); });
    pg.on('pageerror', (e) => logs.push(`[pageerror] ${e.message}`));
    return { pg, ctx, logs };
  }
  return { base, page, async close() { await browser.close(); server.close(); } };
}
