// Procedural, tileable surface textures generated on <canvas>.
// Everything here is original: panel layouts, foil crinkle, radiator fins,
// window strips and livery decals are synthesised from seeded noise.
import * as THREE from 'three';
import { makeRng, tileFbm } from './rng.js';

const cache = new Map();

function canvas(size) {
  const c = document.createElement('canvas');
  c.width = c.height = size;
  return c;
}

function toTexture(c, { srgb = false, repeat = true } = {}) {
  const t = new THREE.CanvasTexture(c);
  if (repeat) t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace;
  t.anisotropy = 8;
  t.generateMipmaps = true;
  t.minFilter = THREE.LinearMipmapLinearFilter;
  t.needsUpdate = true;
  return t;
}

// Height field (Float32, wraps) -> tangent-space normal map canvas.
function heightToNormal(H, S, strength) {
  const c = canvas(S);
  const ctx = c.getContext('2d');
  const img = ctx.createImageData(S, S);
  const at = (x, y) => H[((y + S) % S) * S + ((x + S) % S)];
  for (let y = 0; y < S; y++) {
    for (let x = 0; x < S; x++) {
      const dx = (at(x + 1, y - 1) + 2 * at(x + 1, y) + at(x + 1, y + 1)) - (at(x - 1, y - 1) + 2 * at(x - 1, y) + at(x - 1, y + 1));
      const dy = (at(x - 1, y + 1) + 2 * at(x, y + 1) + at(x + 1, y + 1)) - (at(x - 1, y - 1) + 2 * at(x, y - 1) + at(x + 1, y - 1));
      let nx = -dx * strength, ny = dy * strength, nz = 1;
      const l = Math.hypot(nx, ny, nz);
      nx /= l; ny /= l; nz /= l;
      const i = (y * S + x) * 4;
      img.data[i] = (nx * 0.5 + 0.5) * 255;
      img.data[i + 1] = (ny * 0.5 + 0.5) * 255;
      img.data[i + 2] = (nz * 0.5 + 0.5) * 255;
      img.data[i + 3] = 255;
    }
  }
  ctx.putImageData(img, 0, 0);
  return c;
}

function grayCanvas(values, S, gamma = 1) {
  const c = canvas(S);
  const ctx = c.getContext('2d');
  const img = ctx.createImageData(S, S);
  for (let i = 0; i < S * S; i++) {
    const v = Math.max(0, Math.min(1, values[i])) ** gamma * 255;
    img.data[i * 4] = img.data[i * 4 + 1] = img.data[i * 4 + 2] = v;
    img.data[i * 4 + 3] = 255;
  }
  ctx.putImageData(img, 0, 0);
  return c;
}

/**
 * Hull plating: recursive panel subdivision with grooved seams, hatches,
 * fastener rows and soft grime. Returns { map, roughnessMap, normalMap }.
 *  - style 'hull'   : medium panels, mixed hatches (default)
 *  - style 'armor'  : large heavy plates with bolt rows
 *  - style 'tiles'  : regular thermal tile grid
 *  - style 'deck'   : big deck plates with anti-slip texture
 */
export function panelSet({ seed = 7, size = 1024, style = 'hull', strength = 2.2 } = {}) {
  const key = `panel:${seed}:${size}:${style}:${strength}`;
  if (cache.has(key)) return cache.get(key);
  const S = size;
  const rng = makeRng(seed);
  const H = new Float32Array(S * S).fill(0.5);
  const A = new Float32Array(S * S).fill(1);
  const R = new Float32Array(S * S).fill(0.5);
  const grime = tileFbm(seed * 3 + 1, 4, 6);
  const fine = tileFbm(seed * 5 + 2, 64, 3);

  const grid = style === 'armor' ? 64 : style === 'tiles' ? 64 : style === 'deck' ? 128 : 32;
  const seam = style === 'armor' ? 4 : style === 'tiles' ? 3 : 3;
  const panels = [];

  if (style === 'tiles') {
    const n = S / grid;
    for (let j = 0; j < n; j++) for (let i = 0; i < n; i++) panels.push([i * grid, j * grid, grid, grid]);
  } else {
    const minSize = style === 'armor' ? 128 : style === 'deck' ? 256 : 64;
    const split = (x, y, w, h, depth) => {
      const canW = w >= minSize * 2, canH = h >= minSize * 2;
      if (depth > 6 || (!canW && !canH) || (depth > 1 && rng.chance(0.18))) { panels.push([x, y, w, h]); return; }
      const vertical = canW && (!canH || (w > h ? rng.chance(0.7) : rng.chance(0.3)));
      if (vertical) {
        const cells = w / grid;
        const k = Math.max(minSize / grid, Math.min(cells - minSize / grid, Math.round(cells * rng.range(0.3, 0.7))));
        split(x, y, k * grid, h, depth + 1); split(x + k * grid, y, w - k * grid, h, depth + 1);
      } else {
        const cells = h / grid;
        const k = Math.max(minSize / grid, Math.min(cells - minSize / grid, Math.round(cells * rng.range(0.3, 0.7))));
        split(x, y, w, k * grid, depth + 1); split(x, y + k * grid, w, h - k * grid, depth + 1);
      }
    };
    split(0, 0, S, S, 0);
  }

  const set = (x, y, h, a, r) => {
    const i = (((y % S) + S) % S) * S + (((x % S) + S) % S);
    if (h !== null) H[i] = h;
    if (a !== null) A[i] *= a;
    if (r !== null) R[i] = r;
  };

  for (const [px, py, pw, ph] of panels) {
    const tint = style === 'tiles' ? rng.range(0.8, 1.08) : rng.range(0.94, 1.04);
    const rough = style === 'tiles' ? rng.range(0.55, 0.85) : rng.range(0.36, 0.62);
    const level = style === 'tiles' ? 0.5 : rng.pick([0.5, 0.5, 0.5, 0.44, 0.56]);
    for (let y = py; y < py + ph; y++) {
      for (let x = px; x < px + pw; x++) {
        const ex = Math.min(x - px, px + pw - 1 - x), ey = Math.min(y - py, py + ph - 1 - y);
        const e = Math.min(ex, ey);
        const i = y * S + x;
        if (e < seam / 2) { // groove
          H[i] = 0.18; A[i] = 0.5; R[i] = 0.8;
        } else if (e < seam / 2 + 1.5) { // bevel lip
          H[i] = level - 0.08; A[i] = tint * 0.86; R[i] = rough + 0.1;
        } else {
          H[i] = level; A[i] = tint; R[i] = rough;
        }
      }
    }
    // hatches, grilles and fastener rows
    if (style !== 'tiles' && pw >= 96 && ph >= 96) {
      const roll = rng.next();
      if (roll < 0.22) { // inset access hatch
        const m = 16 + rng.int(0, 2) * 8;
        const hx = px + m, hy = py + m, hw = pw - 2 * m, hh = ph - 2 * m;
        for (let y = hy; y < hy + hh; y++) for (let x = hx; x < hx + hw; x++) {
          const e = Math.min(x - hx, hx + hw - 1 - x, y - hy, hy + hh - 1 - y);
          if (e < 2) set(x, y, 0.25, 0.7, 0.75);
        }
      } else if (roll < 0.34) { // vent grille
        const gw = Math.min(pw - 32, 160), gh = Math.min(ph - 32, 64);
        const gx = px + ((pw - gw) >> 1), gy = py + ((ph - gh) >> 1);
        for (let y = gy; y < gy + gh; y++) for (let x = gx; x < gx + gw; x++) {
          const slot = ((y - gy) % 8) < 4;
          set(x, y, slot ? 0.2 : 0.46, slot ? 0.35 : 0.9, slot ? 0.85 : 0.5);
        }
      } else if (roll < 0.6) { // fastener rows along the panel border
        const step = style === 'armor' ? 24 : 16;
        const inset = seam + (style === 'armor' ? 10 : 6);
        const dot = (cx, cy) => {
          for (let y = -2; y <= 2; y++) for (let x = -2; x <= 2; x++) if (x * x + y * y <= 5) set(cx + x, cy + y, 0.62, 0.8, 0.35);
        };
        for (let x = px + inset; x < px + pw - inset; x += step) { dot(x, py + inset); dot(x, py + ph - 1 - inset); }
        for (let y = py + inset + step; y < py + ph - inset - step / 2; y += step) { dot(px + inset, y); dot(px + pw - 1 - inset, y); }
      }
    }
  }

  // grime + micro variation, anti-slip for decks
  for (let y = 0; y < S; y++) {
    for (let x = 0; x < S; x++) {
      const i = y * S + x;
      const g = grime(x / S, y / S);
      const f = fine(x / S, y / S);
      A[i] *= 0.9 + 0.12 * g - 0.05 * f;
      R[i] = Math.min(1, R[i] + (g - 0.5) * 0.18 + (f - 0.5) * 0.06);
      H[i] += (f - 0.5) * 0.02;
      if (style === 'deck' && ((x + y) % 6 === 0 || (x - y + S) % 6 === 0)) H[i] += 0.03;
    }
  }

  const out = {
    map: toTexture(grayCanvas(A, S, 1 / 2.2), { srgb: true }),
    roughnessMap: toTexture(grayCanvas(R, S)),
    normalMap: toTexture(heightToNormal(H, S, strength)),
  };
  cache.set(key, out);
  return out;
}

// Crinkled multi-layer-insulation foil (normal + roughness).
export function foilSet({ seed = 11, size = 512 } = {}) {
  const key = `foil:${seed}:${size}`;
  if (cache.has(key)) return cache.get(key);
  const S = size;
  const n1 = tileFbm(seed, 8, 5), n2 = tileFbm(seed + 9, 16, 4);
  const H = new Float32Array(S * S), R = new Float32Array(S * S), A = new Float32Array(S * S);
  for (let y = 0; y < S; y++) for (let x = 0; x < S; x++) {
    const u = x / S, v = y / S;
    const a = n1(u, v), b = n2(u, v);
    // ridged crinkle
    const h = 1 - Math.abs(a * 2 - 1) * 0.7 - Math.abs(b * 2 - 1) * 0.5;
    const i = y * S + x;
    H[i] = h; R[i] = 0.18 + 0.25 * (1 - h); A[i] = 0.78 + 0.28 * h;
  }
  const out = {
    map: toTexture(grayCanvas(A, S, 1 / 2.2), { srgb: true }),
    roughnessMap: toTexture(grayCanvas(R, S)),
    normalMap: toTexture(heightToNormal(H, S, 3.5)),
  };
  cache.set(key, out);
  return out;
}

// Radiator panels: fine vertical fins, emissive heat gradient in the fin roots.
export function radiatorSet({ size = 512 } = {}) {
  const key = `rad:${size}`;
  if (cache.has(key)) return cache.get(key);
  const S = size;
  const H = new Float32Array(S * S), E = new Float32Array(S * S), A = new Float32Array(S * S);
  for (let y = 0; y < S; y++) for (let x = 0; x < S; x++) {
    const fin = (x % 16) / 16;
    const h = Math.sin(fin * Math.PI);
    const i = y * S + x;
    H[i] = h * 0.8 + ((y % 128) < 3 ? -0.4 : 0);
    E[i] = (1 - h) ** 3 * (0.65 + 0.35 * Math.sin((y / S) * Math.PI * 2) ** 2);
    A[i] = 0.55 + 0.45 * h;
  }
  const out = {
    map: toTexture(grayCanvas(A, S, 1 / 2.2), { srgb: true }),
    normalMap: toTexture(heightToNormal(H, S, 2.5)),
    emissiveMap: toTexture(grayCanvas(E, S), { srgb: true }),
  };
  cache.set(key, out);
  return out;
}

// Rows of small windows, some lit. Used as emissive strip on habitable sections.
export function windowStrip({ seed = 5, size = 512, lit = 0.62 } = {}) {
  const key = `win:${seed}:${size}:${lit}`;
  if (cache.has(key)) return cache.get(key);
  const S = size;
  const rng = makeRng(seed);
  const cMap = canvas(S), cEm = canvas(S);
  const m = cMap.getContext('2d'), e = cEm.getContext('2d');
  m.fillStyle = '#2a2e35'; m.fillRect(0, 0, S, S);
  e.fillStyle = '#000'; e.fillRect(0, 0, S, S);
  const rows = 8, cols = 16;
  const cw = S / cols, rh = S / rows;
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
    const x = c * cw + cw * 0.22, y = r * rh + rh * 0.3, w = cw * 0.56, h = rh * 0.4;
    m.fillStyle = '#0c1118'; m.fillRect(x, y, w, h);
    if (rng.chance(lit)) {
      const warm = rng.chance(0.75);
      const k = rng.range(0.55, 1);
      e.fillStyle = warm ? `rgba(255,${190 + 40 * k | 0},${120 + 60 * k | 0},${k})` : `rgba(170,215,255,${k})`;
      e.fillRect(x, y, w, h);
    }
  }
  const out = { map: toTexture(cMap, { srgb: true }), emissiveMap: toTexture(cEm, { srgb: true }) };
  cache.set(key, out);
  return out;
}

// Diagonal hazard chevrons for hangar mouths, docking collars, etc.
export function hazardStripes({ size = 256, a = '#f2b705', b = '#15171a' } = {}) {
  const key = `haz:${size}:${a}:${b}`;
  if (cache.has(key)) return cache.get(key);
  const c = canvas(size); const g = c.getContext('2d');
  g.fillStyle = b; g.fillRect(0, 0, size, size);
  g.fillStyle = a;
  const w = size / 4;
  for (let k = -size; k < size * 2; k += w * 2) {
    g.beginPath(); g.moveTo(k, 0); g.lineTo(k + w, 0); g.lineTo(k + w - size, size); g.lineTo(k - size, size); g.closePath(); g.fill();
  }
  const out = toTexture(c, { srgb: true });
  cache.set(key, out);
  return out;
}

// Soft radial glow used for navigation lights and engine flares.
export function glowSprite({ size = 128, core = 0.12 } = {}) {
  const key = `glow:${size}:${core}`;
  if (cache.has(key)) return cache.get(key);
  const c = canvas(size); const g = c.getContext('2d');
  const grd = g.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
  grd.addColorStop(0, 'rgba(255,255,255,1)');
  grd.addColorStop(core, 'rgba(255,255,255,0.85)');
  grd.addColorStop(0.35, 'rgba(255,255,255,0.22)');
  grd.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = grd; g.fillRect(0, 0, size, size);
  const out = toTexture(c, { srgb: true, repeat: false });
  cache.set(key, out);
  return out;
}

/** Livery decal (hull number, class code, stripes). Transparent background. */
export function decalTexture(text, { color = '#ffffff', font = '800 180px "Arial Narrow", Arial, sans-serif', w = 1024, h = 256, outline = null, bar = null } = {}) {
  const key = `decal:${text}:${color}:${font}:${w}:${h}:${outline}:${bar}`;
  if (cache.has(key)) return cache.get(key);
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  const g = c.getContext('2d');
  g.clearRect(0, 0, w, h);
  if (bar) { g.fillStyle = bar; g.fillRect(0, h * 0.08, w * 0.06, h * 0.84); }
  g.font = font;
  g.textAlign = 'center'; g.textBaseline = 'middle';
  if (outline) { g.lineWidth = 10; g.strokeStyle = outline; g.strokeText(text, w / 2, h / 2 + 6); }
  g.fillStyle = color;
  g.fillText(text, w / 2, h / 2 + 6);
  const t = toTexture(c, { srgb: true, repeat: false });
  cache.set(key, t);
  return t;
}
