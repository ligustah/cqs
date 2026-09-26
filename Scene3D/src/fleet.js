// Fleet composition + choreography for the orbital scene.
// Every ship is built through buildShip(), so relative sizes always follow the
// game-derived scale model in lib/scale.js: the escorts are 25-72 m long next to
// a 900 m carrier. The group is laid out at that true scale, with the escorts
// close enough to read against the carrier:
//   - the carrier at the origin (bow +Z), its hangar stocked by lib/park.js
//     (16 fighters, 2 corvettes, a destroyer and a cargo ship on the deck,
//     visible through the open flank bays and lit by the hangar floodlights);
//   - two destroyers a few hundred metres off the bows, four corvettes screening
//     ahead and abeam, the logistics convoy trailing astern to port and below;
//   - fighter patrols in vic formation on loops within ~1 km of the group, and a
//     launch cycle: fighters taxi along the clear lane on the hangar's centreline
//     and accelerate out of the bow mouth.
import * as THREE from 'three';
import { parkInHangar } from './lib/park.js';

const V = (x, y, z) => new THREE.Vector3(x, y, z);

export function buildFleet({ palette, buildShip, attachEffects }) {
  const root = new THREE.Group();
  root.name = 'fleet';
  const ships = [];
  const effects = [];
  const movers = [];

  const place = (cls, pos, { yaw = 0, pitch = 0, roll = 0, power = 1, variant, bob = 1 } = {}) => {
    const g = buildShip(cls, palette, variant ? { variant } : {});
    const s = g.userData.ship;
    const holder = new THREE.Group();
    holder.position.copy(pos);
    holder.rotation.set(THREE.MathUtils.degToRad(pitch), THREE.MathUtils.degToRad(yaw), THREE.MathUtils.degToRad(roll), 'YXZ');
    g.position.sub(s.envelope.center);
    holder.add(g);
    holder.userData.ship = s;
    root.add(holder);
    const fx = attachEffects(g, { power });
    effects.push(fx);
    const entry = { group: holder, ship: g, cls, base: pos.clone(), phase: ships.length * 1.7, bob };
    ships.push(entry);
    return entry;
  };

  // --- carrier and its hangar -------------------------------------------------
  const carrier = place('carrier', V(0, 0, 0), { bob: 0.4 });
  const cs = carrier.group.userData.ship;
  const parked = parkInHangar(carrier.ship, { buildShip, palette, attachEffects });
  effects.push(...parked.effects);

  // --- escorts (metres, carrier frame: port +X, dorsal +Y, bow +Z) ---------------
  // destroyers: one off the port bow quarter (the hero shot's foreground ship), one to starboard
  place('destroyer', V(520, -10, 330), { yaw: -2, roll: -2 });
  place('destroyer', V(-360, 60, 520), { yaw: 3 });
  // corvette screen: ahead, and abeam of the hangar bays
  place('corvette', V(160, 150, 980), { yaw: 1, roll: -3 });
  place('corvette', V(-190, -170, 860), { yaw: -2, roll: 3 });
  place('corvette', V(470, 190, -160), { yaw: -3, roll: -4 });
  place('corvette', V(-480, -110, -60), { yaw: 4, roll: 3 });
  // logistics convoy trailing astern, to port and below the carrier's drive axis (clear of the plumes)
  place('freighter', V(420, -130, -980), { yaw: 3, variant: 'cargo' });
  place('freighter', V(500, -100, -1100), { yaw: 3, variant: 'troops' });
  place('freighter', V(390, -160, -1220), { yaw: 2, variant: 'cargo' });

  // --- fighters ---------------------------------------------------------------
  const fighters = [];
  const addFighter = (parent = root) => {
    const g = buildShip('fighter', palette);
    const s = g.userData.ship;
    g.position.sub(s.envelope.center);
    const holder = new THREE.Group();
    holder.add(g);
    holder.userData.ship = s;
    parent.add(holder);
    effects.push(attachEffects(g, { power: 1, plumeScale: 1.4, spill: false }));
    const entry = { group: holder, cls: 'fighter' };
    ships.push(entry);
    fighters.push(entry);
    return holder;
  };

  // combat air patrol: vic formations on slow loops around the group
  const patrols = [
    { rx: 650, rz: 1150, y: 230, speed: 0.03, phase: 0.6, tilt: 0.08, n: 3 },
    { rx: 900, rz: 1400, y: -260, speed: -0.024, phase: 2.6, tilt: -0.06, n: 3 },
    { rx: 520, rz: 850, y: 380, speed: 0.04, phase: 4.3, tilt: 0.12, n: 2 },
  ];
  // vic formation spaced by the fighter's own size (about 1.6 spans abeam, 1.3 lengths astern)
  const fE = buildShip('fighter', palette).userData.ship.envelope.size;
  const vic = [V(0, 0, 0), V(-fE.x * 1.6, -fE.y * 0.3, -fE.z * 1.3), V(fE.x * 1.6, fE.y * 0.3, -fE.z * 1.3)];
  for (const p of patrols) {
    const members = [];
    for (let i = 0; i < p.n; i++) members.push({ holder: addFighter(), offset: vic[i] });
    const pathPos = (t) => {
      const a = p.phase + t * p.speed * Math.PI * 2;
      return V(Math.cos(a) * p.rx, p.y + Math.sin(a * 2) * 30 + Math.sin(a) * p.tilt * p.rx, Math.sin(a) * p.rz);
    };
    movers.push((t) => {
      const pos = pathPos(t), ahead = pathPos(t + 0.35 * Math.sign(p.speed));
      const fwd = ahead.clone().sub(pos).normalize();
      const q = new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().lookAt(ahead, pos, V(0, 1, 0)));
      // bank into the turn
      const prev = pathPos(t - 0.35 * Math.sign(p.speed));
      const turn = fwd.clone().cross(pos.clone().sub(prev).normalize()).y;
      const bank = new THREE.Quaternion().setFromAxisAngle(V(0, 0, 1), THREE.MathUtils.clamp(turn * 18, -0.9, 0.9));
      q.multiply(bank);
      for (const m of members) {
        m.holder.position.copy(pos).add(m.offset.clone().applyQuaternion(q));
        m.holder.quaternion.copy(q);
      }
    });
  }

  // launch cycle: fighters taxi along the hangar's centreline lane (clear of the parked
  // rows, above the frame sills) and accelerate out of the bow mouth. They are children
  // of the carrier, so they share its frame (and its slow bob).
  const mouth = cs.anchors.hangarMouth;
  const lane = cs.anchors.hangarDeck?.lane;
  if (mouth) {
    const dir = (mouth.dir ? mouth.dir.clone() : V(0, 0, 1)).normalize();
    const laneX = lane ? (lane[0] + lane[1]) / 2 : mouth.p.x;
    const start = V(laneX, mouth.p.y - 12, 60); // on the lane, mid-hangar, 12 m below the mouth centre
    const toMouth = mouth.p.z - start.z;
    const period = 16;
    for (let i = 0; i < 3; i++) {
      const h = addFighter(carrier.ship);
      const offset = i * (period / 3);
      movers.push((t) => {
        const k = ((t + offset) % period) / period; // 0..1
        const d = 90 * k + 2400 * k ** 3;         // taxi, then accelerate out of the bay
        const out = Math.max(0, d - toMouth);     // metres past the mouth
        // once clear of the mouth each fighter breaks away: one climbs, one dives, the
        // outer ones turn to either side (slopes per metre flown)
        const sx = out > 0 ? 0.16 * (i - 1) : 0, sy = out > 0 ? 0.1 * (i % 2 ? 1 : -0.7) : 0;
        h.position.copy(start).addScaledVector(dir, d).add(V(out * sx, out * sy, 0));
        h.quaternion.setFromUnitVectors(V(0, 0, 1), V(sx, sy, 1).normalize());
        h.visible = out < 1600;
      });
    }
  }

  const shadowBox = new THREE.Box3();
  for (const s of ships) if (s.cls !== 'fighter') shadowBox.expandByObject(s.group);

  // camera shots (world = carrier frame)
  const shots = {
    // port bow quarter, 13 degrees above the hangar: into the sunlit open bays and the parked
    // ships, the port destroyer in the foreground, the planet beyond
    hero: { pos: V(700, 110, 470), target: V(40, -70, 90) },
    // the whole group from high over the port bow: destroyers, screen, convoy astern
    high: { pos: V(1400, 1250, 900), target: V(60, -100, -150) },
    // astern, above the port quarter: the carrier's six drive bells and sunlit port flank,
    // the logistics convoy trailing below
    stern: { pos: V(560, 200, -1900), target: V(140, -150, -700) },
  };

  return {
    root, ships, effects, shadowBox, shots, parked,
    update(t) {
      for (const s of ships) {
        if (s.cls === 'fighter' || !s.base) continue;
        s.group.position.y = s.base.y + Math.sin(t * 0.25 + s.phase) * 1.2 * s.bob;
        s.group.rotation.z = Math.sin(t * 0.18 + s.phase) * 0.006 * s.bob;
      }
      for (const m of movers) m(t);
    },
  };
}
