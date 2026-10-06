// Ship registry. Each ship module exports `meta` and `build(palette, opts)`.
// Modules load independently so one broken design never takes down the scene.
import * as THREE from 'three';
import { normalizeShip, CLASSES } from '../lib/scale.js';
import { ShipBuilder, geo } from '../lib/kit.js';
import { loadGLB, buildGLBShip } from '../lib/glbship.js';
import { loadParts, composeParts } from '../lib/compose.js';

// orbital fleet classes: the fleet scene, the hangar loads, the scale check
export const ORDER = ['fighter', 'corvette', 'freighter', 'destroyer', 'carrier'];
// ground units (true size, scale.js size null): ship studio (?mode=ship&ship=<id>) and the lineup only; never placed in
// the orbital fleet. Built through the same ship path as ORDER.
export const GROUND = ['vehicle'];
// Buildings (src/buildings/<id>.js), shown in the building view ?mode=building&building=<id> (or #<id>;
// ?mode=ship&ship=<id> is an alias). fleet: also placed in the orbital fleet scene (fleet.js). Module contract:
// `meta`, an async load hook (`load()` or `preload()`: the GLBs it needs, including the real ship GLBs it reuses),
// `build(palette, { library })` -> Group with userData.ship (envelope, lights) and optionally userData.building
// { effectTargets } (the sub-groups that carry their own light records; default: the group itself), and an optional
// `studio` hint for the building view ({ exposure, key, fill, rim, kick, env, lightscapeGain, az, el, dist }).
export const BUILDINGS = {
  shipyard: { module: '../buildings/shipyard.js', fleet: false },
  spaceport: { module: '../buildings/spaceport.js', fleet: true },
  // colony buildings (src/buildings/colony.js factory; catalogue and menu groups in src/buildings/catalog.js)
  deuterium_depot: { module: '../buildings/deuterium_depot.js', fleet: false },
  steel_mill: { module: '../buildings/steel_mill.js', fleet: false },
  refinery: { module: '../buildings/refinery.js', fleet: false },
  residence: { module: '../buildings/residence.js', fleet: false },
  processing_plant: { module: '../buildings/processing_plant.js', fleet: false },
  oil_tanks: { module: '../buildings/oil_tanks.js', fleet: false },
  silicon_foundry: { module: '../buildings/silicon_foundry.js', fleet: false },
  steel_depot: { module: '../buildings/steel_depot.js', fleet: false },
  silicon_depot: { module: '../buildings/silicon_depot.js', fleet: false },
  military_base: { module: '../buildings/military_base.js', fleet: false },
  trade_center: { module: '../buildings/trade_center.js', fleet: false },
  infrastructure: { module: '../buildings/infrastructure.js', fleet: false },
  university: { module: '../buildings/university.js', fleet: false },
  library: { module: '../buildings/library.js', fleet: false },
  radio_telescope: { module: '../buildings/radio_telescope.js', fleet: false },
  transmitter: { module: '../buildings/transmitter.js', fleet: false },
};
/** Every class the ship path builds (studio, lineup): the fleet classes and the ground units. */
export const LINEUP = [...GROUND, ...ORDER];
export const SHIPS = {};
const BUILDING_MODS = {};
const BUILDINGS_LOADED = new Set();
export const LOAD_ERRORS = {};
const GLTFS = {};
const PARTS = {}; // parts kit GLBs by part name (assets/parts)
let CONTEXT = { library: {} };

/** Shared build context (e.g. the PATINA material library). */
export function setShipContext(ctx) { CONTEXT = { ...CONTEXT, ...ctx }; }

/**
 * Load ship modules (all, or a subset). Safe to call more than once (a class keeps the copy it was first loaded with).
 * tier: the phone-tier copy of the GLBs (glbship.js loadGLB; desktop always loads the full GLB): 'lite' for the
 * subject of a view, 'mini' for ships in a crowd (fleet, lineup, parked loads, ships in a building scene). A string
 * applies to every class, a function (cls) => tier picks per class.
 */
export async function loadShips(only = ORDER, tier = 'lite') {
  const tierOf = typeof tier === 'function' ? tier : () => tier;
  await Promise.all(only.map(async (cls) => {
    if (SHIPS[cls]) return;
    try {
      const mod = await import(`./${cls}.js`);
      // generated ships: preload the fal GLB (and optional variants)
      if (mod.asset) {
        const t = tierOf(cls);
        const [main, ...vars] = await Promise.all([mod.asset.glb, ...Object.values(mod.variants || {}).map((a) => a.glb)]
          .map((u) => (u ? loadGLB(u, t) : null)));
        GLTFS[cls] = main;
        Object.keys(mod.variants || {}).forEach((v, i) => { if (vars[i]) GLTFS[`${cls}:${v}`] = vars[i]; });
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

/** Import a building module (no assets yet); null if it fails. */
export async function importBuilding(id) {
  if (BUILDING_MODS[id]) return BUILDING_MODS[id];
  try {
    if (!BUILDINGS[id]) throw new Error(`unknown building ${id}`);
    BUILDING_MODS[id] = await import(BUILDINGS[id].module);
  } catch (e) {
    LOAD_ERRORS[id] = String(e?.stack || e);
    console.error(`[buildings] failed to import ${id}:`, e);
    return null;
  }
  return BUILDING_MODS[id];
}

/** Load building modules and their assets (load() / preload() hooks). Safe to call more than once. */
export async function loadBuildings(ids = Object.keys(BUILDINGS)) {
  await Promise.all(ids.map(async (id) => {
    const mod = await importBuilding(id);
    if (!mod || BUILDINGS_LOADED.has(id)) return;
    try {
      await (mod.load ?? mod.preload)?.();
      BUILDINGS_LOADED.add(id);
    } catch (e) {
      LOAD_ERRORS[id] = String(e?.stack || e);
      console.error(`[buildings] failed to load ${id}:`, e);
    }
  }));
}

/**
 * Build a building (real size, never normalised). Always a fresh build: a building is placed once per view, and its
 * effect targets are sub-groups of this instance. userData.ship gets cls/meta/spec like a ship; userData.building
 * { id, meta, studio, effectTargets }.
 */
export function buildBuilding(id, palette) {
  const mod = BUILDING_MODS[id];
  let group;
  try {
    if (!BUILDINGS_LOADED.has(id)) throw new Error(LOAD_ERRORS[id] || `${id} not loaded`);
    group = mod.build(palette, { library: CONTEXT.library });
  } catch (e) {
    console.error(`[buildings] ${id}.build failed:`, e);
    LOAD_ERRORS[id] = LOAD_ERRORS[id] || String(e?.stack || e);
    group = fallback(id, palette);
  }
  const b = (group.userData.building ||= {});
  Object.assign(b, { id, meta: b.meta ?? mod?.meta, studio: b.studio ?? mod?.studio ?? null, effectTargets: b.effectTargets ?? [group] });
  Object.assign(group.userData.ship, { cls: id, meta: mod?.meta ?? { name: id }, spec: CLASSES[id], scaleCorrection: 1 });
  return group;
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
