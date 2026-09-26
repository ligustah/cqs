// Fleet composition + choreography for the orbital scene.
// Every ship is built through buildShip(), so relative sizes always follow the
// game-derived scale model in lib/scale.js.
import * as THREE from 'three';

const V = (x, y, z) => new THREE.Vector3(x, y, z);

export function buildFleet({ palette, buildShip, attachEffects }) {
  const root = new THREE.Group();
  root.name = 'fleet';
  const ships = [];
  const effects = [];
  const movers = [];

  const place = (cls, pos, { yaw = 0, pitch = 0, roll = 0, power = 1, variant, bob = 1 } = {}) => {
    const g = buildShip(cls, palette, { variant });
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
    const entry = { group: holder, cls, base: pos.clone(), phase: ships.length * 1.7, bob };
    ships.push(entry);
    return entry;
  };

  // --- capital ships ---------------------------------------------------------
  const carrier = place('carrier', V(0, 0, 0), { bob: 0.4 });
  const cL = carrier.group.userData.ship.envelope.size.z;
  const cB = carrier.group.userData.ship.envelope.size.x;
  place('destroyer', V(cB * 0.95, 18, cL * 0.62), { yaw: -2 });
  place('destroyer', V(-cB * 1.05, 26, cL * 0.48), { yaw: 3 });
  // corvette screen
  place('corvette', V(cB * 1.9, -12, cL * 0.2), { yaw: -4, roll: -4 });
  place('corvette', V(-cB * 2.0, 6, cL * 0.05), { yaw: 5, roll: 3 });
  place('corvette', V(cB * 0.35, 48, cL * 1.25), { yaw: 1 });
  place('corvette', V(-cB * 0.55, -34, cL * 1.1), { yaw: -2 });
  // logistics convoy trailing to port-low
  place('freighter', V(-cB * 1.3, -46, -cL * 0.85), { yaw: 4, variant: 'cargo' });
  place('freighter', V(-cB * 1.6, -38, -cL * 1.25), { yaw: 4, variant: 'troops' });
  place('freighter', V(-cB * 0.9, -58, -cL * 1.45), { yaw: 3, variant: 'cargo' });

  // --- fighters ---------------------------------------------------------------
  // combat air patrol: vic formations on slow elliptical loops around the group
  const fighters = [];
  const addFighter = (variant) => {
    const g = buildShip('fighter', palette, { variant });
    const s = g.userData.ship;
    g.position.sub(s.envelope.center);
    const holder = new THREE.Group();
    holder.add(g);
    holder.userData.ship = s;
    root.add(holder);
    effects.push(attachEffects(g, { power: 1, plumeScale: 1.4, spill: false }));
    const entry = { group: holder, cls: 'fighter' };
    ships.push(entry);
    fighters.push(entry);
    return holder;
  };

  const patrols = [
    { rx: cB * 2.6, rz: cL * 1.5, y: 70, speed: 0.045, phase: 0.0, tilt: 0.08, n: 3 },
    { rx: cB * 3.4, rz: cL * 1.9, y: -30, speed: -0.035, phase: 2.2, tilt: -0.06, n: 3 },
    { rx: cB * 1.8, rz: cL * 1.2, y: 120, speed: 0.06, phase: 4.1, tilt: 0.12, n: 2 },
  ];
  // vic formation spaced by the fighter's own size (about 1.6 spans abeam, 1.3 lengths astern)
  const fE = buildShip('fighter', palette).userData.ship.envelope.size;
  const vic = [V(0, 0, 0), V(-fE.x * 1.6, -fE.y * 0.3, -fE.z * 1.3), V(fE.x * 1.6, fE.y * 0.3, -fE.z * 1.3)];
  for (const p of patrols) {
    const members = [];
    for (let i = 0; i < p.n; i++) members.push({ holder: addFighter(i === 0 ? 'lead' : 'wing'), offset: vic[i] });
    const pathPos = (t) => {
      const a = p.phase + t * p.speed * Math.PI * 2;
      return V(Math.cos(a) * p.rx, p.y + Math.sin(a * 2) * 25 + Math.sin(a) * p.tilt * p.rx, Math.sin(a) * p.rz);
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

  // launch cycle from the carrier's hangar mouth
  const mouth = carrier.group.userData.ship.anchors.hangarMouth;
  if (mouth) {
    const sc = carrier.group.userData.ship.scaleCorrection;
    const ccenter = carrier.group.userData.ship.envelope.center;
    const start = mouth.p.clone().multiplyScalar(sc).sub(ccenter);
    const dir = (mouth.dir ? mouth.dir.clone() : V(0, 0, 1)).normalize();
    for (let i = 0; i < 3; i++) {
      const h = addFighter('wing');
      const period = 14;
      const offset = i * (period / 3);
      movers.push((t) => {
        const k = ((t + offset) % period) / period; // 0..1
        const d = 40 * k + 900 * k * k * k;        // accelerate out of the bay
        const climb = Math.max(0, d - 120) * 0.12 * (i % 2 ? 1 : -0.6);
        const side = Math.max(0, d - 200) * 0.18 * (i - 1);
        h.position.copy(start).addScaledVector(dir, d).add(V(side, climb, 0));
        h.quaternion.setFromUnitVectors(V(0, 0, 1), dir);
        h.visible = d < 1100;
      });
    }
  }

  const shadowBox = new THREE.Box3();
  for (const s of ships) if (s.cls !== 'fighter') shadowBox.expandByObject(s.group);

  const shots = {
    hero: { pos: V(cB * 2.2, -cL * 0.12, cL * 1.95), target: V(0, 8, cL * 0.18) },
    high: { pos: V(-cB * 2.6, cL * 1.2, cL * 1.4), target: V(0, 0, 0) },
    stern: { pos: V(cB * 1.1, cL * 0.25, -cL * 1.6), target: V(0, 0, -cL * 0.2) },
  };

  return {
    root, ships, effects, shadowBox, shots,
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
