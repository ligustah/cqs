// Fleet composition + choreography for the orbital scene.
// Every ship is built through buildShip(), so relative sizes always follow the
// game-derived scale model in lib/scale.js: the escorts are 25-72 m long next to
// a 900 m carrier. The group is laid out at that true scale, with the escorts
// close enough to read against the carrier:
//   - the carrier at the origin (bow +Z), its hangar stocked by lib/park.js
//     (21 fighters, 2 corvettes, a destroyer and a cargo ship on the deck,
//     visible through the open flank bays and lit by the hangar floodlights);
//   - two destroyers (off the port bow and the starboard bow), four
//     corvettes screening ahead, abeam and astern above the drive axis, the logistics convoy
//     trailing astern to port;
//   - fighter patrols in vic formation on loops within ~1 km of the group, and a
//     launch and recovery cycle (lib/launch.js): a deck lift in the enclosed bow section
//     raises each fighter onto the centreline lane, the deck catapults it out of the bow
//     mouth, it lights its drive clear of the bow, climbs away, flies a wide loop and
//     glides back in to the recovery lift. It is only ever hidden below the deck;
//   - the SP-3 orbital spaceport (a building, src/buildings/spaceport.js, ships/index.js BUILDINGS with fleet: true)
//     3 km off the starboard bow. Ground units (ships/index.js GROUND) are never placed here.
import * as THREE from 'three';
import { parkInHangar, DEFAULT_LOADOUT, LAUNCH_CYCLE_FIGHTERS } from './lib/park.js';
import { launchCycle } from './lib/launch.js';

const V = (x, y, z) => new THREE.Vector3(x, y, z);

// The group's hangar (lib/park.js DEFAULT_LOADOUT, the same load the studio and the scale chart
// park): 21 fighters three abreast in one row per bay side, 2 corvettes, a destroyer and a cargo
// ship on the deck. The 3 fighters of the launch and recovery cycle below belong to the same
// carrier (they are recovered into it and wait below the deck between sorties), so the carrier
// carries the park.js load: 24 + 8 + 2 + 3 launch-cycle fighters = 37 of its 50 slots
// (UnitEnum CARRIER spaceTransport = 50).
const HANGAR_LOADOUT = DEFAULT_LOADOUT;

export function buildFleet({ palette, buildShip, attachEffects, buildBuilding = null, buildings = [] }) {
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
  const parked = parkInHangar(carrier.ship, { buildShip, palette, attachEffects, loadout: HANGAR_LOADOUT });
  effects.push(...parked.effects);

  // --- escorts (metres, carrier frame: port +X, dorsal +Y, bow +Z) ---------------
  // destroyers: one off the port bow, 440 m out (the hero shot's foreground escort), one off the
  // starboard bow. The port one is yawed 22 degrees toward the sun (port-high, a touch aft), so
  // the bow block's chamfers and the spinal rail channel are raked instead of end-on in shadow.
  place('destroyer', V(571, 72, 478), { yaw: 22, roll: -2 });
  place('destroyer', V(-360, 60, 520), { yaw: 3 });
  // corvette screen: ahead, and abeam of the hangar bays
  place('corvette', V(160, 150, 980), { yaw: 1, roll: -3 });
  place('corvette', V(-190, -170, 860), { yaw: -2, roll: 3 });
  place('corvette', V(76, 140, -880), { yaw: -3, roll: -4 }); // astern, above the drive axis: the stern shot's near escort
  place('corvette', V(-480, -110, -60), { yaw: 4, roll: 3 });
  // logistics convoy trailing 300-460 m astern, well to port of the drive axis (clear of the plumes)
  place('freighter', V(354, 4, -775), { yaw: 3, variant: 'cargo' });
  place('freighter', V(409, 38, -868), { yaw: 3, variant: 'troops' });
  place('freighter', V(304, 42, -907), { yaw: 2, variant: 'cargo' });

  // --- orbital buildings (main.js loads every BUILDINGS entry with fleet: true and passes the ids) ----------------
  // the SP-3 spaceport: 3 km off the starboard bow, yawed 30 degrees so its open slot faces the group; the drives of
  // its tugs and docked freighters stay cold. Not in the shadow box (below). Its own shot: ?shot=spaceport
  const SPACEPORT_AT = V(-2600, -150, 1900);
  let spaceport = null;
  if (buildBuilding && buildings.includes('spaceport')) {
    const g = buildBuilding('spaceport', palette);
    const s = g.userData.ship;
    const holder = new THREE.Group();
    holder.position.copy(SPACEPORT_AT);
    holder.rotation.set(0, THREE.MathUtils.degToRad(-30), 0);
    g.position.sub(s.envelope.center);
    holder.add(g);
    holder.userData.ship = s;
    root.add(holder);
    for (const t of g.userData.building.effectTargets) effects.push(attachEffects(t, { power: 0 }));
    spaceport = { group: holder, ship: g, cls: 'spaceport', base: SPACEPORT_AT.clone(), phase: 0, bob: 0, building: true };
    ships.push(spaceport);
  }

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
    holder.userData.model = g; // the fighter itself (holder = its pose)
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
      // time always runs forward; the loop's direction is already in p.speed
      const pos = pathPos(t), ahead = pathPos(t + 0.35);
      const fwd = ahead.clone().sub(pos).normalize();
      const q = new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().lookAt(ahead, pos, V(0, 1, 0)));
      // bank into the turn
      const prev = pathPos(t - 0.35);
      const turn = fwd.clone().cross(pos.clone().sub(prev).normalize()).y;
      const bank = new THREE.Quaternion().setFromAxisAngle(V(0, 0, 1), THREE.MathUtils.clamp(turn * 18, -0.9, 0.9));
      q.multiply(bank);
      for (const m of members) {
        m.holder.position.copy(pos).add(m.offset.clone().applyQuaternion(q));
        m.holder.quaternion.copy(q);
      }
    });
  }

  // launch and recovery cycle (lib/launch.js): three fighters on one closed track, staggered by
  // a third of its period. They are children of the carrier, so they share its frame (and its
  // slow bob). The drive is lit only in flight: plume power and the glow in the bells follow the
  // track's throttle (the bell glow materials are cloned per fighter so each can dim its own).
  const cycle = launchCycle(cs, fE);
  if (cycle) {
    for (let i = 0; i < LAUNCH_CYCLE_FIGHTERS; i++) {
      const h = addFighter(carrier.ship);
      const g = h.userData.model;
      const plumes = g.children.filter((c) => c.name === 'plume').map((c) => c.material.uniforms.uPower);
      const bells = g.children.filter((c) => c.name === 'nozzle-glow' || c.name === 'nozzle-lining');
      for (const b of bells) { b.material = b.material.clone(); b.userData.color = b.material.color.clone(); }
      // in the ?t=5 stills the first fighter is just leaving the bow mouth
      const offset = 5 + i * (cycle.period / 3);
      movers.push((t) => {
        const st = cycle.at(t + offset);
        h.visible = st.visible;
        h.position.copy(st.position);
        h.quaternion.copy(st.quaternion);
        for (const u of plumes) u.value = st.power;
        for (const b of bells) { b.visible = st.power > 0.005; b.material.color.copy(b.userData.color).multiplyScalar(st.power); }
      });
    }
  }

  const shadowBox = new THREE.Box3();
  // (buildings are left out: the spaceport 3 km off would spread the shadow map over the whole gap)
  for (const s of ships) if (s.cls !== 'fighter' && !s.building) shadowBox.expandByObject(s.group);

  // camera shots (world = carrier frame). The planet is true scale (planet.js): the fleet is
  // 400 km up, so its horizon sits 3.5-36 degrees below the fleet's horizontal depending on the
  // bearing (lowest ahead, highest astern to starboard), and the ground below is 400+ km away.
  // fov: the shot's lens (vertical, deg); horizon: the most tilt the horizon may keep (deg; the
  // planet sits 16 deg off the fleet's nadir, so an unrolled camera sees it tilted 12-18 deg).
  const shots = {
    // port bow quarter, 44 degrees off the bow and 12 degrees up, ~1 km out on a 34 degree lens:
    // the sun (95 deg az, 32 deg el) is 51 degrees off the lens axis, behind the left shoulder,
    // so it rakes the flank: the frames' forward faces fall into deep shadow and throw theirs
    // across the sunlit deck inside the bays. The whole bow (mouth and the CV-50 stencil) at the
    // left, the six open bays with their parked rows across the middle (0.6-0.85 m per pixel:
    // inside what the hull bake resolves), the island against black space, the horizon behind
    // the hull (5 degrees below the fleet's horizontal on this bearing), the port destroyer in
    // the foreground over the planet, lower right. The drive cluster is at the far right.
    hero: { pos: V(700, 188, 724), target: V(20, -20, 20), fov: 34, horizon: 5 },
    // above and behind the port quarter, 44 degrees down from 2.9 km: the whole group (screen,
    // destroyers, convoy astern) over the ground 400 km below, the limb across the top corner
    // (its 15 degree tilt kept: it reads as the curve of the planet under a banking camera)
    high: { pos: V(505, 1895, -2174), target: V(0, -120, -150) },
    // astern and above the port quarter, 23 degrees down: the carrier's six drive bells, the
    // logistics convoy trailing in the foreground against the planet, the trailing corvette's
    // own bells to starboard, the limb across the lower third
    stern: { pos: V(330, 300, -1250), target: V(110, -70, -400), horizon: 5 },
  };
  // the spaceport: 45 degrees off its bow on the slot side, 30 degrees up, 2 km out (only when it is placed)
  if (spaceport) shots.spaceport = { pos: V(-2152, 850, 3574), target: SPACEPORT_AT.clone(), fov: 34, horizon: 5 };

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
