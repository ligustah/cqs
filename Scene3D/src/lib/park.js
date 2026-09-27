// Parks real ships on a carrier's hangar deck.
//
// The carrier module describes its deck in anchors.hangarDeck (ship frame, metres):
//   lane:  [x0, x1]   launch lane on the centreline, kept clear up to the bow mouth
//   zones: { name: { x: [x0, x1], z: [z0, z1], y } }  flat deck areas (y = deck plane)
//          between the frames / sills, x and z already inside walls and chamfers
//   openings (optional): { flank: { x: [stbd, port], y: [y0, y1], z: [[z0, z1], ...] },
//          mouth: { z, x: [x0, x1], y: [y0, y1] }, inside: { min, max } }
// Every parked ship is built with buildShip (so it shares geometry and materials with
// every other ship of its class), sits on the deck with its envelope bottom on the
// deck plane, bow toward the mouth (+Z), and becomes a child of the carrier group.
// Ships are packed per zone and side of the lane in tidy rows: rows fill from the
// forward end of the zone and from the outboard edge (next to the flank bays, where the
// parked ships can be seen from outside), with CLEARANCE metres between envelopes and
// to the zone's edges; each zone side's block of rows is then centred along the zone.
// Engines are off (no plume, no throat glow, no spill light); navigation lights stay on.
//
// Parked ships are only drawn while the camera can see into the hangar: the optional
// anchors.hangarDeck.openings describe the flank bays and the bow mouth, and a line of
// sight from the ship to the camera must pass through one of them (or the camera is
// inside the hangar). Hidden ships skip the draw and the shadow pass; a software
// renderer otherwise spends most of a fleet frame on ships nobody can see.
import * as THREE from 'three';
import { CLEARANCE } from './scale.js';

const _cam = new THREE.Vector3();

/**
 * Wrapper that shows its ship only while `seen(cameraPositionInCarrierFrame)` is true.
 * It uses three.js's LOD hook: the renderer calls update(camera) while projecting the
 * scene, i.e. before the shadow pass and before drawing, every frame.
 */
class HangarView extends THREE.Object3D {
  constructor(carrier, seen) {
    super();
    this.isLOD = true;
    this.autoUpdate = true;
    this.carrier = carrier;
    this.seen = seen;
    this.levels = []; // LOD interface (unused)
  }
  update(camera) {
    camera.getWorldPosition(_cam);
    this.carrier.worldToLocal(_cam);
    const on = this.seen(_cam);
    for (const c of this.children) c.visible = on;
  }
}

/**
 * Line-of-sight test through the hangar's openings (carrier frame). pts: sample points on
 * the parked ship; openings: { flank: { x: [stbd, port], y: [y0, y1], z: [[z0, z1], ...] },
 * mouth: { z, x: [x0, x1], y: [y0, y1] }, inside: { min, max } }.
 */
function openingTest(pts, o, margin = 3) {
  const within = (v, [a, b]) => v >= a - margin && v <= b + margin;
  return (C) => {
    if (o.inside && C.x > o.inside.min[0] && C.x < o.inside.max[0] && C.y > o.inside.min[1] && C.y < o.inside.max[1] && C.z > o.inside.min[2] && C.z < o.inside.max[2]) return true;
    for (const P of pts) {
      const f = o.flank;
      if (f) {
        const X = C.x > f.x[1] ? f.x[1] : C.x < f.x[0] ? f.x[0] : null;
        if (X !== null) {
          const t = (X - P.x) / (C.x - P.x);
          const y = P.y + t * (C.y - P.y), z = P.z + t * (C.z - P.z);
          if (within(y, f.y) && f.z.some((r) => within(z, r))) return true;
        }
      }
      const m = o.mouth;
      if (m && C.z > m.z) {
        const t = (m.z - P.z) / (C.z - P.z);
        const x = P.x + t * (C.x - P.x), y = P.y + t * (C.y - P.y);
        if (within(x, m.x) && within(y, m.y)) return true;
      }
    }
    return false;
  };
}

/**
 * Default loadout (the fleet, the ship studio and the scale chart all park this one): a
 * destroyer, 2 corvettes, a cargo ship and 21 fighters parked three abreast in one row per bay
 * side, centred between the frames (a single file along the sill would hide behind the sill and
 * the frames from any elevated view; a row abreast shows the inboard two in plan). With the 3
 * fighters of the launch and recovery cycle (lib/launch.js, always somewhere on the carrier's
 * track) that is 12 + 10 + 4 + 24 = 50 slots: exactly the carrier's legal load
 * (UnitEnum CARRIER spaceTransport = 50), never more.
 * Items: { cls, variant?, count = 1, zones: [name...], side: 'port'|'starboard'|'both', perSide?, perRow? }
 *  perSide: at most this many ships of the item per zone side (spreads a class over several bays);
 *  perRow: at most this many ships abreast (1 = a single file along the outboard edge).
 */
export const LAUNCH_CYCLE_FIGHTERS = 3;
export const DEFAULT_LOADOUT = [
  { cls: 'destroyer', zones: ['bow'], side: 'starboard' },
  { cls: 'corvette', count: 2, zones: ['bay1'], side: 'both', perSide: 1 },
  { cls: 'freighter', variant: 'cargo', zones: ['aft'], side: 'starboard' },
  { cls: 'fighter', count: 24 - LAUNCH_CYCLE_FIGHTERS, zones: ['bay2', 'bay3', 'bay4', 'bay5'], side: 'both', perSide: 3, perRow: 3 },
];

/**
 * @param {THREE.Group} carrierGroup  built by buildShip('carrier'); ships are added as its children
 * @param {object} o  { buildShip, palette, attachEffects, loadout = DEFAULT_LOADOUT,
 *   clearance = 2 m, gap = deck to envelope bottom (m), center = centre rows along each zone,
 *   cull = draw a ship only while it can be seen through an opening,
 *   dress = add the hangar dressing: deck paint, containers, tractors (see dressHangar) }
 * @returns {{ ships: {group, cls, variant, zone, side}[], effects: {update}[], skipped: object[] }}
 */
export function parkInHangar(carrierGroup, { buildShip, palette, attachEffects, loadout = DEFAULT_LOADOUT, clearance = CLEARANCE, gap = 0.3, center = true, cull = true, dress = true } = {}) {
  const info = carrierGroup.userData.ship;
  const deck = info?.anchors?.hangarDeck;
  const out = { ships: [], effects: [], skipped: [] };
  if (!deck) return out;
  const k = carrierGroup.scale.x || 1; // ship-frame units -> metres (1 for the carrier)
  const lane = deck.lane || [0, 0];
  // free space per zone side: rows are filled forward -> aft, outboard -> inboard
  const sides = new Map();
  const sideOf = (zone, side) => {
    const key = `${zone}:${side}`;
    if (!sides.has(key)) {
      const z = deck.zones[zone];
      if (!z) return null;
      const port = side === 'port';
      sides.set(key, {
        zone, side, y: z.y,
        out: (port ? z.x[1] : z.x[0]) * k, in: (port ? Math.max(lane[1], z.x[0]) : Math.min(lane[0], z.x[1])) * k,
        zFront: z.z[1] * k, zAft: z.z[0] * k, dir: port ? -1 : 1,
        row: null, count: {},
      });
    }
    return sides.get(key);
  };

  // try to place an envelope (metres, L along z, B along x) in a zone side; returns centre [x, z] or null
  const place = (s, L, B, cls, perRow = Infinity) => {
    const fitsRow = (row) => {
      const xOuter = row.cursor; // outboard edge of the next ship (already includes clearance)
      const xInner = xOuter + s.dir * B;
      const inboardLimit = s.in - s.dir * clearance;
      return (s.dir < 0 ? xInner >= inboardLimit : xInner <= inboardLimit) && row.front - L >= s.zAft + clearance && row.cls === cls && row.n < perRow;
    };
    if (!s.row || !fitsRow(s.row)) {
      const front = s.row ? s.row.front - s.row.depth - clearance : s.zFront - clearance;
      const row = { front, depth: 0, cursor: s.out + s.dir * clearance, cls, n: 0 };
      if (!fitsRow(row)) return null;
      s.row = row;
    }
    const r = s.row;
    const x = r.cursor + s.dir * B / 2;
    const z = r.front - L / 2;
    r.cursor += s.dir * (B + clearance);
    r.depth = Math.max(r.depth, L);
    r.n++;
    return [x, z];
  };

  for (const item of loadout) {
    const count = item.count ?? 1;
    const sideNames = item.side === 'both' ? ['port', 'starboard'] : [item.side || 'port'];
    let placed = 0;
    // round-robin over zones and sides so a class spreads evenly (perSide caps each side)
    outer: for (const zone of item.zones || Object.keys(deck.zones)) {
      for (let pass = 0; pass < 64 && placed < count; pass++) {
        let any = false;
        for (const sd of sideNames) {
          if (placed >= count) break outer;
          const s = sideOf(zone, sd);
          if (!s) continue;
          const key = `${item.cls}:${item.variant || ''}`;
          if (item.perSide && (s.count[key] || 0) >= item.perSide) continue;
          const g = buildShip(item.cls, palette, item.variant ? { variant: item.variant } : {});
          const e = g.userData.ship.envelope; // metres
          const at = place(s, e.size.z, e.size.x, item.cls, item.perRow);
          if (!at) continue;
          // envelope centre on (x, z), envelope bottom on the deck; child of the (possibly scaled) carrier
          g.scale.divideScalar(k);
          g.position.set(at[0] - e.center.x, s.y * k + gap - e.min.y, at[1] - e.center.z).divideScalar(k);
          g.name = `parked-${item.cls}`;
          carrierGroup.add(g);
          // engines off (power 0): nav lights only, no plume and no glow in the bells
          if (attachEffects) out.effects.push(attachEffects(g, { power: 0, spill: false }));
          s.count[key] = (s.count[key] || 0) + 1;
          out.ships.push({ group: g, cls: item.cls, variant: item.variant, zone, side: sd });
          placed++;
          any = true;
        }
        if (!any) break;
      }
    }
    if (placed < count) out.skipped.push({ ...item, placed });
  }
  // centre each zone side's block of rows along the zone, so no row hides behind the
  // frames at either end of an open bay (seen from a bow or a stern quarter)
  if (center) {
    for (const s of sides.values()) {
      const mine = out.ships.filter((q) => `${q.zone}:${q.side}` === `${s.zone}:${s.side}`);
      if (!mine.length) continue;
      const front = s.zFront - clearance, back = s.row.front - s.row.depth;
      const shift = ((s.zFront + s.zAft) / 2 - (front + back) / 2) / k;
      for (const q of mine) q.group.position.z += shift;
    }
  }
  // draw each ship only while it can be seen through a flank bay or the bow mouth
  const openings = deck.openings;
  if (cull && openings) {
    for (const q of out.ships) {
      const g = q.group;
      const e = g.userData.ship.envelope; // metres, relative to the ship's origin
      // sample points: the top corners and the centre of the envelope, in the carrier frame
      const pts = [[0, 1, 0], [1, 1, 0], [0, 1, 1], [1, 1, 1], [0.5, 0.5, 0.5]].map(([a, b, c]) => new THREE.Vector3(
        THREE.MathUtils.lerp(e.min.x, e.max.x, a), THREE.MathUtils.lerp(e.min.y, e.max.y, b), THREE.MathUtils.lerp(e.min.z, e.max.z, c),
      ).divideScalar(k).add(g.position));
      const view = new HangarView(carrierGroup, openingTest(pts, openings));
      view.name = g.name;
      carrierGroup.add(view);
      view.add(g); // g keeps its transform: HangarView sits at the carrier origin
      q.view = view;
    }
  }
  if (dress) out.dressing = dressHangar(carrierGroup, out.ships, deck, { clearance, k });
  if (out.skipped.length) console.warn('[park] not everything fitted:', out.skipped);
  return out;
}

// Hangar dressing: human-scale deck equipment that holds no hangar slot. The legal load is 50
// slots in a 670 m hangar, so most of the deck is bare; a real deck carries the kit that works
// it. Everything is instanced boxes (three draw calls in all), on the deck plane of each zone:
//   - painted parking boxes around every parked ship (worn yellow deck paint, 0.35 m lines,
//     1.5 m outside its envelope) and the edges of the launch lane
//   - stacks of 20-ft containers (6.06 x 2.44 x 2.59 m), two high, against the lane in the free
//     deck fore or aft of each parked block (or in the middle of an empty zone side)
//   - deck tractors (4.2 x 2.0 x 1.8 m) towing a train of two carts (2.8 x 1.4 x 1.1 m)
// The launch lane and the parked ships' boxes stay clear (clearance to both).
const CONTAINER = [2.44, 2.59, 6.06]; // x, y, z (m): containers lie along the hangar
const PAINT = '#8f8158', CONTAINER_TONES = ['#5c4b3b', '#46505a', '#5e3d33', '#50544a', '#6a5b3e', '#4b4b4f'];
const TRACTOR = [2.0, 1.8, 4.2], CART = [1.4, 1.1, 2.8];

function dressHangar(carrierGroup, ships, deck, { clearance = 2, k = 1 } = {}) {
  const lane = deck.lane || [0, 0];
  const lines = [], boxes = [], vehicles = [];
  const hash = (n) => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
  const line = (x0, x1, z0, z1, y) => lines.push({ p: [(x0 + x1) / 2, y + 0.025, (z0 + z1) / 2], s: [Math.max(0.35, Math.abs(x1 - x0)), 0.05, Math.max(0.35, Math.abs(z1 - z0))] });
  // footprints of the parked ships (carrier frame, metres)
  const foot = ships.map((q) => {
    const e = q.group.userData.ship.envelope, P = q.group.position.clone().multiplyScalar(k);
    return { zone: q.zone, side: q.side, x0: P.x + e.min.x, x1: P.x + e.max.x, z0: P.z + e.min.z, z1: P.z + e.max.z };
  });
  for (const f of foot) {
    const y = deck.zones[f.zone].y, m = 1.5;
    const X0 = f.x0 - m, X1 = f.x1 + m, Z0 = f.z0 - m, Z1 = f.z1 + m;
    line(X0, X1, Z0, Z0, y); line(X0, X1, Z1, Z1, y); line(X0, X0, Z0, Z1, y); line(X1, X1, Z0, Z1, y);
  }
  let n = 0;
  for (const [name, z] of Object.entries(deck.zones)) {
    // launch lane edges along the zone
    line(lane[0], lane[0], z.z[0] + 1, z.z[1] - 1, z.y); line(lane[1], lane[1], z.z[0] + 1, z.z[1] - 1, z.y);
    for (const side of ['port', 'starboard']) {
      const port = side === 'port', dir = port ? 1 : -1;
      const inner = (port ? lane[1] : lane[0]) + dir * clearance * 2; // first free x next to the lane
      const outer = port ? z.x[1] - clearance : z.x[0] + clearance;
      const mine = foot.filter((f) => f.zone === name && f.side === side);
      // free z strips in this zone side: fore and aft of the parked block, or all of it
      const zA = z.z[0] + clearance, zF = z.z[1] - clearance;
      const strips = mine.length
        ? [[zA, Math.min(...mine.map((f) => f.z0)) - clearance - 1.5], [Math.max(...mine.map((f) => f.z1)) + clearance + 1.5, zF]]
        : [[zA, (zA + zF) / 2 - clearance], [(zA + zF) / 2 + clearance, zF]];
      strips.forEach(([s0, s1], si) => {
        const depth = s1 - s0;
        if (depth < CONTAINER[2] + 1) return;
        n++;
        if (si === 0 || !mine.length) {
          // a block of containers against the lane: 3 abreast, 1-2 deep, 2 high (the top row short)
          const rows = depth > 2 * CONTAINER[2] + 4 ? 2 : 1;
          for (let r = 0; r < rows; r++) for (let c = 0; c < 3; c++) for (let h = 0; h < 2; h++) {
            if (h === 1 && hash(n * 31 + r * 7 + c) < 0.35) continue;
            const x = inner + dir * (c * (CONTAINER[0] + 0.3) + CONTAINER[0] / 2);
            const zc = (si === 0 ? s0 : s1) + (si === 0 ? 1 : -1) * (r * (CONTAINER[2] + 0.4) + CONTAINER[2] / 2);
            boxes.push({ p: [x, z.y + h * CONTAINER[1] + CONTAINER[1] / 2, zc], s: CONTAINER, c: CONTAINER_TONES[Math.floor(hash(n * 13 + r * 5 + c * 3 + h) * CONTAINER_TONES.length)] });
          }
        }
        if ((si === 1 || !mine.length) && depth >= 14) {
          // a tractor and its two carts, parked along the zone, part-way out from the lane
          const xv = inner + dir * (3 * (CONTAINER[0] + 0.3) + 6 + hash(n) * Math.max(0, Math.abs(outer - inner) - 30));
          if (Math.abs(xv - inner) > Math.abs(outer - inner) - 3) return;
          let zc = (s0 + s1) / 2 + 5.5;
          const yaw = (hash(n * 3) - 0.5) * 0.25;
          vehicles.push({ p: [xv, z.y + TRACTOR[1] / 2, zc], s: TRACTOR, c: '#6b6236', yaw });
          for (let i = 0; i < 2; i++) { zc -= (i ? CART[2] : TRACTOR[2] / 2 + CART[2] / 2) + 0.9; vehicles.push({ p: [xv, z.y + CART[1] / 2 + 0.2, zc], s: CART, c: '#4d5053', yaw }); }
        }
      });
    }
  }
  const unit = new THREE.BoxGeometry(1, 1, 1);
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), col = new THREE.Color(), up = new THREE.Vector3(0, 1, 0);
  const build = (list, name, mat, { cast = true } = {}) => {
    if (!list.length) return null;
    const mesh = new THREE.InstancedMesh(unit, mat, list.length);
    list.forEach((b, i) => {
      q.setFromAxisAngle(up, b.yaw || 0);
      m4.compose(new THREE.Vector3(...b.p).divideScalar(k), q, new THREE.Vector3(...b.s).divideScalar(k));
      mesh.setMatrixAt(i, m4);
      mesh.setColorAt(i, col.set(b.c || PAINT));
    });
    mesh.castShadow = cast; mesh.receiveShadow = true;
    mesh.name = name;
    carrierGroup.add(mesh);
    return mesh;
  };
  const paint = new THREE.MeshStandardMaterial({ color: '#ffffff', roughness: 0.9, metalness: 0, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 });
  const steel = new THREE.MeshStandardMaterial({ color: '#ffffff', roughness: 0.8, metalness: 0.15 });
  return {
    lines: build(lines, 'hangar-deck-paint', paint, { cast: false }),
    containers: build(boxes, 'hangar-containers', steel),
    vehicles: build(vehicles, 'hangar-vehicles', steel),
    counts: { lines: lines.length, containers: boxes.length, vehicles: vehicles.length },
  };
}

/** Hide / show every parked ship of a carrier (e.g. a UI toggle). */
export function setParkedVisible(carrierGroup, on) {
  for (const c of carrierGroup.children) if (c.name?.startsWith('parked-')) c.visible = on;
}
