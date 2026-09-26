// Small deterministic helpers so every build of the fleet looks identical.

export function mulberry32(seed) {
  let a = seed >>> 0;
  return function () {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function makeRng(seed = 1) {
  const r = mulberry32(seed);
  return {
    next: r,
    range: (a, b) => a + (b - a) * r(),
    int: (a, b) => Math.floor(a + (b - a + 1) * r()),
    pick: (arr) => arr[Math.floor(r() * arr.length)],
    chance: (p) => r() < p,
  };
}

// Tileable value noise on an integer lattice of `period` cells.
export function tileNoise2D(seed, period) {
  const r = mulberry32(seed);
  const grid = new Float32Array(period * period);
  for (let i = 0; i < grid.length; i++) grid[i] = r();
  const at = (x, y) => grid[((y % period) + period) % period * period + ((x % period) + period) % period];
  const fade = (t) => t * t * (3 - 2 * t);
  return (u, v) => {
    // u, v in [0,1): tileable across the unit square
    const x = u * period, y = v * period;
    const xi = Math.floor(x), yi = Math.floor(y);
    const xf = fade(x - xi), yf = fade(y - yi);
    const a = at(xi, yi), b = at(xi + 1, yi), c = at(xi, yi + 1), d = at(xi + 1, yi + 1);
    return a + (b - a) * xf + (c - a) * yf + (a - b - c + d) * xf * yf;
  };
}

export function tileFbm(seed, basePeriod = 4, octaves = 5) {
  const layers = [];
  for (let o = 0; o < octaves; o++) layers.push(tileNoise2D(seed + o * 101, basePeriod << o));
  return (u, v) => {
    let sum = 0, amp = 0.5, norm = 0;
    for (const n of layers) { sum += n(u, v) * amp; norm += amp; amp *= 0.5; }
    return sum / norm;
  };
}
