// Ship registry. Each ship module exports `meta` and `build(palette, opts)`.
// Modules load independently so one broken design never takes down the scene.
import * as THREE from 'three';
import { normalizeShip, CLASSES } from '../lib/scale.js';
import { ShipBuilder, geo } from '../lib/kit.js';
import { loadGLB, buildGLBShip } from '../lib/glbship.js';
import { loadParts, composeParts } from '../lib/compose.js';

export const ORDER = ['fighter', 'corvette', 'freighter', 'destroyer', 'carrier'];
export const SHIPS = {};
export const LOAD_ERRORS = {};
const GLTFS = {};
const PARTS = {}; // parts kit GLBs by part name (assets/parts)
let CONTEXT = { library: {} };

/** Shared build context (e.g. the PATINA material library). */
export function setShipContext(ctx) { CONTEXT = { ...CONTEXT, ...ctx }; }

/** Load ship modules (all, or a subset). Safe to call more than once. */
export async function loadShips(only = ORDER) {
  await Promise.all(only.map(async (cls) => {
    if (SHIPS[cls]) return;
    try {
      const mod = await import(`./${cls}.js`);
      // generated ships: preload the fal GLB (and optional variants)
      if (mod.asset) {
        GLTFS[cls] = await loadGLB(mod.asset.glb);
        for (const [v, a] of Object.entries(mod.variants || {})) if (a.glb) GLTFS[`${cls}:${v}`] = await loadGLB(a.glb);
        // parts kit instances the module places on its hull (and its variants')
        const placements = [mod.asset, ...Object.values(mod.variants || {})].flatMap((a) => a.parts || []);
        if (placements.length) Object.assign(PARTS, await loadParts(placements));
      }
      SHIPS[cls] = mod;
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

const protos = new Map();

function buildFresh(cls, palette, opts) {
  const mod = SHIPS[cls];
  let group;
  try {
    if (!mod) throw new Error(LOAD_ERRORS[cls] || `${cls} not loaded`);
    if (mod.asset) {
      const v = opts.variant && mod.variants?.[opts.variant];
      const cfg = { name: cls, ...mod.asset, ...(v || {}) };
      if (CONTEXT.livery) cfg.livery = CONTEXT.livery === 'none' ? null : CONTEXT.livery; // ?livery= override for look-dev
      group = buildGLBShip(GLTFS[v?.glb ? `${cls}:${opts.variant}` : cls], cfg, { palette, library: CONTEXT.library });
      if (cfg.parts?.length) group.userData.ship.parts = composeParts(group, cfg.parts, PARTS, { livery: cfg.livery });
    } else {
      group = mod.build(palette, opts);
    }
  } catch (e) {
    console.error(`[ships] ${cls}.build failed:`, e);
    LOAD_ERRORS[cls] = LOAD_ERRORS[cls] || String(e?.stack || e);
    group = fallback(cls, palette);
  }
  normalizeShip(group, cls);
  Object.assign(group.userData.ship, { cls, meta: mod?.meta ?? { name: cls }, spec: CLASSES[cls] });
  return group;
}

/**
 * Build a ship of class `cls`, normalised to its game-derived hangar size.
 * Repeated calls with the same options return new instances that share
 * geometry, materials and the (read-only) userData.ship record.
 */
export function buildShip(cls, palette, opts = {}) {
  const key = `${cls}:${JSON.stringify(opts)}`;
  let proto = protos.get(key);
  if (!proto) { proto = buildFresh(cls, palette, opts); protos.set(key, proto); }
  const g = new THREE.Group();
  g.name = proto.name;
  for (const child of proto.children) g.add(child.clone());
  g.scale.copy(proto.scale);
  g.userData.ship = proto.userData.ship;
  return g;
}

export { THREE };
