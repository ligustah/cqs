// Scale model: derived from the game's own unit data.
//
// Engine/net/cqs/engine/units/UnitEnum.java#getSize() assigns every space
// unit a "size" that is the hangar space it occupies inside a carrier:
//   FIGHTER 1, CORVETTE 5, DESTROYER 12, civil ship (freighter/transport) 4.
// The CARRIER carries getSpaceUnitCapacity() = 50 size units of non-warp ships.
//
// We read "size" as the ship's parking envelope in a hangar (the axis-aligned
// bounding box, L x B x H). One size unit is fixed at SLOT_VOLUME cubic metres,
// set so that the fighter comes out at ~16 m long.
// Each ship is uniformly scaled so its envelope volume = size x SLOT_VOLUME.
//
// The carrier's own hull is not a hangar slot. Its hangar bay is sized so that
// every legal full load physically fits (50 fighters, 10 corvettes,
// 4 destroyers or 12 freighters, with 2 m clearance). See carrierLoads().

export const SLOT_VOLUME = 800; // m^3 per hangar size unit

export const CLASSES = {
  fighter:   { size: 1,  label: 'Fighter',     gameId: 'FIGHTER',   role: 'Space-superiority strike craft' },
  corvette:  { size: 5,  label: 'Corvette',    gameId: 'CORVETTE',  role: 'Fast escort gunship' },
  freighter: { size: 4,  label: 'Civil ship',  gameId: 'FREIGHTER', role: 'Cargo / troop transport' },
  destroyer: { size: 12, label: 'Destroyer',   gameId: 'DESTROYER', role: 'Heavy line warship' },
  carrier:   { size: null, capacity: 50, label: 'Carrier', gameId: 'CARRIER', role: 'Warp-capable fleet carrier' },
};

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

/** Check each legal full load against the carrier hangar size (Vector3, metres). */
export function carrierLoads(hangarSize, envelopes) {
  const cap = CLASSES.carrier.capacity;
  const rows = [];
  for (const cls of ['fighter', 'corvette', 'destroyer', 'freighter']) {
    const env = envelopes[cls];
    if (!env) continue;
    const need = Math.floor(cap / CLASSES[cls].size);
    const fits = fitCount(hangarSize, env);
    rows.push({ cls, need, fits, ok: fits >= need });
  }
  return rows;
}
