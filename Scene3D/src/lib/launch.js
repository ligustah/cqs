// Launch and recovery cycle for fighters flying from a carrier's hangar (carrier ship frame,
// metres: bow +Z, dorsal +Y, port +X). One closed track, flown by each fighter with its own
// time offset, so nothing ever appears or vanishes in view:
//
//   1. a deck lift in the enclosed bow section raises the fighter onto the launch half of the
//      lane (while it is below the deck it is hidden by the hull, and not drawn);
//   2. drive cold, it is catapulted along the lane (a linear motor in the deck, ~2 g) and out
//      of the bow mouth, coasts clear of the bow, and only then lights its drive;
//   3. it climbs away to starboard and flies a wide teardrop (~700 m turn radius, ~4 g at the
//      top speed of ~170 m/s), lines up far ahead on the centreline and glides back in, drive
//      off, low along the recovery half of the lane;
//   4. the deck's linear motor brakes it to a stop at the recovery lift, which lowers it below
//      the deck; there it is moved to the launch lift for the next cycle.
//
// Launch (starboard) and recovery (port) use the two halves of the centreline lane, ~6 m apart,
// and the default period staggers three fighters so that no launch meets a recovery in the
// mouth. Everything is a pure function of time: frozen stills (?t=) are reproducible.
import * as THREE from 'three';

const V = (x, y, z) => new THREE.Vector3(x, y, z);
const UP = V(0, 1, 0);
const smoother = (k) => { k = THREE.MathUtils.clamp(k, 0, 1); return k * k * k * (k * (k * 6 - 15) + 10); };

// --- track legs: { T, at(t) -> { p, dir, speed, power } } -------------------------------------
/** Straight run from a to b with constant acceleration from v0 to v1 (m/s). */
function line(a, b, v0, v1, power = () => 0) {
  const L = a.distanceTo(b), T = (2 * L) / (v0 + v1), acc = (v1 - v0) / T, dir = b.clone().sub(a).normalize();
  return { T, at: (t) => ({ p: a.clone().addScaledVector(dir, v0 * t + 0.5 * acc * t * t), dir, speed: v0 + acc * t, power: power(t / T) }) };
}
/** Stand still at p, nose along dir. */
function hold(p, dir, T) {
  return { T, at: () => ({ p: p.clone(), dir, speed: 0, power: 0 }) };
}
/** Deck lift: vertical move by dy (negative = down) with eased start and stop. */
function lift(p, dy, dir, T) {
  return { T, at: (t) => ({ p: p.clone().add(V(0, dy * smoother(t / T), 0)), dir, speed: 0, power: 0 }) };
}
/**
 * Flight along a centripetal Catmull-Rom spline. The first two and the last two points fix the
 * end tangents. Speed follows a smooth profile v(u) = v0 + (v1 - v0) u + 4 c u (1 - u) that peaks
 * near vPeak mid-way; the leg's duration follows from the path length.
 */
function flight(points, v0, vPeak, v1, power) {
  const curve = new THREE.CatmullRomCurve3(points, false, 'centripetal');
  curve.arcLengthDivisions = 4000;
  const L = curve.getLength();
  const c = vPeak - (v0 + v1) / 2;
  const T = L / ((v0 + v1) / 2 + (2 / 3) * c);
  const s = (u) => T * (v0 * u + (v1 - v0) * u * u / 2 + 4 * c * (u * u / 2 - u * u * u / 3));
  const vel = (u) => v0 + (v1 - v0) * u + 4 * c * u * (1 - u);
  return {
    T, L, curve,
    at(t) {
      const u = t / T, w = THREE.MathUtils.clamp(s(u) / L, 0, 1), speed = vel(u);
      const dir = curve.getTangentAt(w);
      // lateral acceleration v^2 * curvature, from the tangent's change over +-8 m of path
      const dw = 8 / L;
      const t0 = curve.getTangentAt(Math.max(0, w - dw)), t1 = curve.getTangentAt(Math.min(1, w + dw));
      const kappa = t1.sub(t0).divideScalar(Math.min(1, w + dw) * L - Math.max(0, w - dw) * L);
      return { p: curve.getPointAt(w), dir, speed, power: power(u), accel: kappa.multiplyScalar(speed * speed) };
    },
  };
}

/**
 * The flight out and back, as spline points every ~50 m (carrier frame). Plan view: a turn of
 * TURN_DEG to starboard (radius R1) off the bow, a straight climb-out tangent to the loop, a
 * clockwise loop of radius R centred R to starboard of the centreline (its port-most point, where
 * the fighter heads aft, lies on the centreline), then straight in along the centreline to the
 * approach gate. Height: climb to the loop altitude, a gentle hump over the loop, and a descent
 * that levels off at the gate; all eased, so there is no kink in pitch.
 */
function teardrop({ start, mid, gate, touch, R = 700, R1 = 700, turnDeg = 60, alt = 290, hump = 40 }) {
  const th = THREE.MathUtils.degToRad(turnDeg), s = Math.sin(th), c = Math.cos(th);
  // plan view in (x, z); the turn off the bow bends toward -x (starboard)
  const E = { x: start.x - R1 * (1 - c), z: start.z + R1 * s };                 // end of the turn off the bow
  const cx = mid - R;
  const cz = E.z + R * s - ((mid - R * (1 + c) - E.x) * c) / s;                 // loop centre: climb-out line tangent to it
  const Q = { x: cx - R * c, z: cz - R * s };                                   // where the climb-out joins the loop
  const segs = [
    { L: R1 * th, at: (d) => { const a = d / R1; return { x: start.x - R1 * (1 - Math.cos(a)), z: start.z + R1 * Math.sin(a) }; } },
    { L: Math.hypot(Q.x - E.x, Q.z - E.z), at: (d) => ({ x: E.x - s * d, z: E.z + c * d }) },
    { L: R * (Math.PI + th), at: (d) => { const a = Math.PI + th - d / R; return { x: cx + R * Math.cos(a), z: cz + R * Math.sin(a) }; } },
    { L: Math.hypot(gate.x - mid, cz - gate.z), at: (d, L) => ({ x: THREE.MathUtils.lerp(mid, gate.x, smoother(d / L)), z: cz - d }) },
  ];
  const total = segs.reduce((a, g) => a + g.L, 0);
  const sClimb = segs[0].L + segs[1].L, sLoop = sClimb + segs[2].L;
  // the last 60 m before the gate already follow the approach glide line
  const inbound = touch.clone().sub(gate).normalize();
  const preGate = gate.clone().addScaledVector(inbound, -60);
  const height = (d) => {
    if (d <= sClimb) return THREE.MathUtils.lerp(start.y, alt, smoother(d / sClimb));
    if (d <= sLoop) return alt + hump * Math.sin(Math.PI * (d - sClimb) / segs[2].L);
    return THREE.MathUtils.lerp(alt, preGate.y, smoother((d - sLoop) / (total - 60 - sLoop)));
  };
  const pts = [];
  let d0 = 0;
  for (const g of segs) {
    const n = Math.max(2, Math.ceil(g.L / 50));
    for (let i = pts.length ? 1 : 0; i <= n; i++) { const d = (g.L * i) / n; const p = g.at(d, g.L); pts.push(V(p.x, height(d0 + d), p.z)); }
    d0 += g.L;
  }
  // arrive along the approach line (gate -> touch), so the glide in continues the same heading
  while (pts.length > 2 && pts[pts.length - 1].distanceTo(gate) < 110) pts.pop();
  pts.push(preGate, gate.clone());
  return pts;
}

/**
 * Build the cycle for one carrier.
 * @param {object} carrier  userData.ship of the carrier (anchors.hangarDeck, anchors.hangarMouth)
 * @param {THREE.Vector3} fighter  fighter envelope size (m)
 * @returns {{ period, legs, at(t) -> { position, quaternion, power, visible, phase } } | null}
 */
export function launchCycle(carrier, fighter, { period = 105 } = {}) {
  const deck = carrier.anchors?.hangarDeck, mouth = carrier.anchors?.hangarMouth;
  if (!deck?.lane || !deck.zones?.bow || !mouth) return null;
  const bow = deck.zones.bow;
  const mid = (deck.lane[0] + deck.lane[1]) / 2, half = (deck.lane[1] - deck.lane[0]) / 2;
  // launch on the starboard half of the lane (the climb-out turns to starboard, away from the
  // inbound flow), recover on the port half (wingtips ~6 m apart)
  const xL = mid - half / 2, xR = mid + half / 2;
  const yDeck = bow.y + 0.3 + fighter.y / 2;          // envelope centre, standing on the bow-section deck
  const zLift = bow.z[0] + 0.38 * (bow.z[1] - bow.z[0]); // ~330 m: the lifts sit in the enclosed bow section
  const zEdge = bow.z[1];                              // forward edge of the deck (the mouth lip is just ahead)
  const zMouth = mouth.p.z;
  const drop = -(fighter.y + 4.5);                     // lift travel: the whole fighter below the deck plate
  const FWD = V(0, 0, 1), AFT = V(0, 0, -1);

  const launchPad = V(xL, yDeck, zLift), recoveryPad = V(xR, yDeck, zLift);
  const clear = V(xL, yDeck, zMouth + 142);            // drive ignition: ~140 m clear of the bow
  // final approach: from 300 m ahead of the mouth, 12 m high, gliding down to the deck just inside it
  const gate = V(xR, yDeck + 12, zMouth + 300), touch = V(xR, yDeck, zEdge - 10);
  const route = teardrop({ start: clear, mid, gate, touch });
  // drive: cold on the deck and in the catapult run; lights ~140 m clear of the bow (ramp over
  // the first ~1.5 s), full power while accelerating, trimmed back through the turn, off for the
  // glide in (the deck's linear motor catches and brakes the fighter)
  const drive = (u) => smoother(u / 0.03) * THREE.MathUtils.lerp(1, 0.35, smoother((u - 0.32) / 0.14)) * (1 - smoother((u - 0.8) / 0.08));

  const legs = [
    { name: 'lift-up', ...lift(launchPad.clone().add(V(0, drop, 0)), -drop, FWD, 4) },
    { name: 'ready', ...hold(launchPad, FWD, 2.5) },
    { name: 'catapult', ...line(launchPad, V(xL, yDeck, zEdge), 0, 60) },
    { name: 'clear-bow', ...line(V(xL, yDeck, zEdge), clear, 60, 60) },
    { name: 'flight', ...flight(route, 60, 150, 55, drive) },
    { name: 'approach', ...line(gate, touch, 55, 22) },
    { name: 'rollout', ...line(touch, recoveryPad, 22, 0) },
    { name: 'secure', ...hold(recoveryPad, AFT, 1.5) },
    { name: 'lift-down', ...lift(recoveryPad, drop, AFT, 4) },
  ];
  const busy = legs.reduce((a, l) => a + l.T, 0);
  if (busy > period) period = Math.ceil(busy + 5);
  legs.push({ name: 'below-deck', ...hold(launchPad.clone().add(V(0, drop, 0)), FWD, period - busy), hidden: true });
  const starts = []; let acc = 0; for (const l of legs) { starts.push(acc); acc += l.T; }

  const m = new THREE.Matrix4(), q = new THREE.Quaternion(), up = new THREE.Vector3(), tmp = new THREE.Vector3();
  return {
    period, legs, starts, lanes: { launch: xL, recovery: xR }, zLift, yDeck,
    /** state at cycle time t (seconds, any value: wrapped to the period) */
    at(t) {
      const tc = ((t % period) + period) % period;
      let i = legs.length - 1; while (i > 0 && starts[i] > tc) i--;
      const leg = legs[i], st = leg.at(Math.min(leg.T, tc - starts[i]));
      // bank into turns: "up" leans toward the turn so the pull goes through the seat
      // (a 1 g reference keeps level flight upright)
      up.copy(UP).multiplyScalar(9.8);
      if (st.accel) up.add(tmp.copy(st.accel).addScaledVector(st.dir, -st.accel.dot(st.dir)));
      up.normalize();
      m.lookAt(st.dir, new THREE.Vector3(), up); // rotation whose +Z points along dir
      q.setFromRotationMatrix(m);
      // drawn while any part of it is above the deck plate; below it the hull hides it
      const visible = !leg.hidden && st.p.y + fighter.y / 2 > bow.y - 0.5;
      return { position: st.p, quaternion: q.clone(), power: st.power, visible, phase: leg.name, speed: st.speed };
    },
  };
}
