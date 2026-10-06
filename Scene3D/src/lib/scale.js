// Scale model: derived from the game's own unit data.
//
// Engine/net/cqs/engine/units/UnitEnum.java#getSize() assigns every space
// unit a "size" that is the hangar space it occupies inside a carrier:
//   FIGHTER 1, CORVETTE 5, DESTROYER 12, civil ship (freighter/transport) 4.
// The CARRIER carries getSpaceUnitCapacity() = 50 size units of non-warp ships.
//
// We read "size" as the ship's parking envelope in a hangar (the axis-aligned
// bounding box, L x B x H), so a destroyer takes 12x the fighter's volume, not
// 12x its length. One size unit is SLOT_VOLUME cubic metres, set from the
// carrier: its 900 m hull's measured hangar bay is exactly filled by the
// tightest legal full load (12 civil ships), so the 50-slot capacity is what
// sizes the bay. That puts the fighter at ~71 m and the destroyer at ~200 m.
// Each ship is uniformly scaled so its envelope volume = size x SLOT_VOLUME.
//
// The carrier's own hull is not a hangar slot (it is warp-capable and never
// carried). It is a 900 m design whose hangar bay must physically hold every
// legal full load (50 fighters, 10 corvettes, 4 destroyers or 12 civil ships,
// with 2 m clearance). See carrierLoads().

export const SLOT_VOLUME = 70000; // m^3 per hangar size unit: a full 50-slot load fills the 900 m carrier's bay

export const CLASSES = {
  fighter:   { size: 1,  label: 'Fighter',     gameId: 'FIGHTER',   role: 'Space-superiority strike craft' },
  corvette:  { size: 5,  label: 'Corvette',    gameId: 'CORVETTE',  role: 'Fast escort gunship' },
  freighter: { size: 4,  label: 'Civil ship',  gameId: 'FREIGHTER', role: 'Cargo / troop transport' },
  destroyer: { size: 12, label: 'Destroyer',   gameId: 'DESTROYER', role: 'Heavy line warship' },
  carrier:   { size: null, capacity: 50, label: 'Carrier', gameId: 'CARRIER', role: 'Warp-capable fleet carrier' },
  // Not hangar-slot classes (size null: normalizeShip leaves them at their authored real size; carrierLoads and the
  // hangar check only read the five space classes above).
  // Ground unit (ships/index.js GROUND: ship studio and lineup only, never in the orbital fleet). ground = the game's
  // ground-transport size (UnitEnum VEHICLE: 3; a CT-7 carries 750).
  vehicle:   { size: null, ground: 3, label: 'Vehicle', gameId: 'VEHICLE', role: 'Fast armoured all-terrain ground unit' },
  // Buildings (ships/index.js BUILDINGS: the building view ?mode=building&building=<id>; the spaceport also orbits in
  // the fleet scene). Never in ORDER, the lineup or the scale check.
  shipyard:  { size: null, building: 'planetside', label: 'Shipyard', gameId: 'SHIPYARD', role: 'Planetside yard: builds the line warships' },
  spaceport: { size: null, building: 'orbital', label: 'Spaceport', gameId: 'SPACEPORT', role: 'Orbital shipyard: builds the warp-capable units' },
  // colony buildings (briefs/buildings.md; src/buildings/catalog.js groups them for the Buildings menu)
  steel_mill: { size: null, building: 'planetside', label: 'Steel Mill', gameId: 'STEEL_MILL', role: 'Blast furnace, pour bay and rolling shed: produces steel' },
  refinery: { size: null, building: 'planetside', label: 'Refinery', gameId: 'REFINERY', role: 'Distillation columns and pipe racks: refines oil' },
  silicon_foundry: { size: null, building: 'planetside', label: 'Silicon Foundry', gameId: 'SILICON_FOUNDRY', role: 'Sawtooth fab hall round a crystal reactor: produces silicon' },
  processing_plant: { size: null, building: 'planetside', label: 'Processing Plant', gameId: 'PROCESSING_PLANT', role: 'Banded process vessels and manifolds: processes raw materials' },
  trade_center: { size: null, building: 'planetside', label: 'Trade Center', gameId: 'TRADE_CENTER', role: 'Twin towers on a sky bridge over a glazed arcade: trade' },
  infrastructure: { size: null, building: 'planetside', label: 'Infrastructure', gameId: 'INFRASTRUCTURE', role: 'Cross-plan admin block round a domed hub: colony administration' },
  residence: { size: null, building: 'planetside', label: 'Residence', gameId: 'RESIDENCE', role: 'Terraced apartment blocks round a garden court: housing' },
  steel_depot: { size: null, building: 'planetside', label: 'Steel Depot', gameId: 'STEEL_DEPOT', role: 'Portal shed with an overhead crane: stores steel' },
  oil_tanks: { size: null, building: 'planetside', label: 'Oil Tanks', gameId: 'OIL_TANKS', role: 'Floating-roof tanks in a bunded yard: stores oil' },
  silicon_depot: { size: null, building: 'planetside', label: 'Silicon Depot', gameId: 'SILICON_DEPOT', role: 'Monolithic vault with rack bays: stores silicon' },
  deuterium_depot: { size: null, building: 'planetside', label: 'Deuterium Depot', gameId: 'DEUTERIUM_DEPOT', role: 'Three pressure spheres on legs, manifold and pump houses: stores deuterium' },
  military_base: { size: null, building: 'planetside', label: 'Military Base', gameId: 'MILITARY_BASE', role: 'Walled compound with vehicle hangars: trains ground units' },
  radio_telescope: { size: null, building: 'planetside', label: 'Radio Telescope', gameId: 'RADIO_TELESCOPE', role: 'Large dish on an alt-az mount: research' },
  university: { size: null, building: 'planetside', label: 'University', gameId: 'UNIVERSITY', role: 'Faceted wings with observatory domes round an atrium: research' },
  library: { size: null, building: 'planetside', label: 'Library', gameId: 'LIBRARY', role: 'Stepped monumental archive block: research' },
  transmitter: { size: null, building: 'orbital', label: 'Transmitter', gameId: 'TRANSMITTER', role: 'Orbital hexagonal ring megaproject' },
};

/** Short label for a class's size stat: hangar slots, carrier capacity, ground unit or building. */
export function sizeLabel(spec, { long = false } = {}) {
  if (spec.size) return `${spec.size}${long ? ' hangar' : ''} slot${spec.size > 1 ? 's' : ''}`;
  if (spec.capacity) return long ? `carries ${spec.capacity} slots` : `hangar ${spec.capacity}`;
  if (spec.ground) return long ? 'ground unit, true size' : 'ground unit';
  if (spec.building) return `${spec.building} building`;
  return '';
}

export const CLEARANCE = 2; // metres around each parked hull

/** Uniformly scale a finished ship so its envelope volume matches its class size. */
export function normalizeShip(group, cls) {
  const info = group.userData.ship;
  const spec = CLASSES[cls];
  if (!spec || !spec.size) { info.scaleCorrection = 1; return group; }
  const target = spec.size * SLOT_VOLUME;
  const s = Math.cbrt(target / info.envelopeVolume);
  group.scale.setScalar(s);
  info.scaleCorrection = s;
  info.envelope.size.multiplyScalar(s);
  info.envelope.center.multiplyScalar(s);
  info.envelope.min.multiplyScalar(s);
  info.envelope.max.multiplyScalar(s);
  info.envelopeVolume = info.envelope.size.x * info.envelope.size.y * info.envelope.size.z;
  info.sizeSlots = spec.size;
  return group;
}

/**
 * How many ships of a given envelope fit into a hangar box (with clearance),
 * trying both yaw orientations and stacking in tiers where height allows.
 */
export function fitCount(hangar, env, clearance = CLEARANCE) {
  const tiers = Math.floor((hangar.y - clearance) / (env.y + clearance));
  const along = (L, W) => Math.floor((hangar.z - clearance) / (L + clearance)) * Math.floor((hangar.x - clearance) / (W + clearance));
  const perTier = Math.max(along(env.z, env.x), along(env.x, env.z));
  return Math.max(0, tiers) * perTier;
}

/**
 * Check each legal full load against the carrier hangar size (Vector3, metres). envelopes is
 * keyed by class, or 'class:variant' for a variant with its own envelope (the civil ship's
 * troop transport: same 4 slots, different shape).
 */
export function carrierLoads(hangarSize, envelopes) {
  const cap = CLASSES.carrier.capacity;
  const rows = [];
  for (const key of ['fighter', 'corvette', 'destroyer', 'freighter', 'freighter:troops']) {
    const env = envelopes[key];
    if (!env) continue;
    const [cls, variant] = key.split(':');
    const need = Math.floor(cap / CLASSES[cls].size);
    const fits = fitCount(hangarSize, env);
    rows.push({ cls, variant: variant || null, key, need, fits, ok: fits >= need });
  }
  return rows;
}
