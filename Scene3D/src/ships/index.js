// Ship registry. Each ship module exports `meta` and `build(palette, opts)`.
// Modules load independently so one broken design never takes down the scene.
import * as THREE from 'three';
import { normalizeShip, CLASSES } from '../lib/scale.js';
import { ShipBuilder, geo } from '../lib/kit.js';

export const ORDER = ['fighter', 'corvette', 'freighter', 'destroyer', 'carrier'];
export const SHIPS = {};
export const LOAD_ERRORS = {};

/** Load ship modules (all, or a subset). Safe to call more than once. */
export async function loadShips(only = ORDER) {
  await Promise.all(only.map(async (cls) => {
    if (SHIPS[cls]) return;
    try {
      SHIPS[cls] = await import(`./${cls}.js`);
    } catch (e) {
      LOAD_ERRORS[cls] = String(e?.stack || e);
      console.error(`[ships] failed to load ${cls}.js:`, e);
    }
  }));
  return SHIPS;
}

function fallback(cls, palette) {
  const b = new ShipBuilder(cls, palette);
  b.add(geo.box(8, 4, 16, 0.5), 'hazard');
  return b.finish({ broken: true });
}

/** Build a ship of class `cls`, normalised to its game-derived hangar size. */
export function buildShip(cls, palette, opts = {}) {
  const mod = SHIPS[cls];
  let group;
  try {
    if (!mod) throw new Error(LOAD_ERRORS[cls] || `${cls} not loaded`);
    group = mod.build(palette, opts);
  } catch (e) {
    console.error(`[ships] ${cls}.build failed:`, e);
    LOAD_ERRORS[cls] = LOAD_ERRORS[cls] || String(e?.stack || e);
    group = fallback(cls, palette);
  }
  normalizeShip(group, cls);
  Object.assign(group.userData.ship, { cls, meta: mod?.meta ?? { name: cls }, spec: CLASSES[cls] });
  return group;
}

export { THREE };
