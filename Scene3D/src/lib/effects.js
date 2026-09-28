// Runtime effects attached to finished ships: plasma exhaust plumes and
// navigation / running lights. Both read anchors recorded by ShipBuilder.
import * as THREE from 'three';
import { LIVERY } from './materials.js';

const LIGHT_COLORS = {
  red: LIVERY.navRed, green: LIVERY.navGreen, white: '#ffffff', amber: LIVERY.amber, cyan: '#7fe8ff',
};

// Fusion-drive exhaust. In vacuum the plasma is nearly invisible a short way
// past the magnetic nozzle, so the drive reads as a hot glow in the bell (the
// throat disc from glbship.js / kit.js) and a short, soft plume that fades
// within about one bell radius: never a beam. The mesh is only a bounding
// cylinder (radius 1 = bound, length 1, nozzle at z = 0, plume toward -z); the
// fragment shader finds where the view ray passes closest to the plume axis
// and evaluates Gaussian core + glow profiles there. Profiles are in units of
// the bell radius and fall to ~0 well inside the bound, so the volume never
// shows an edge (AgX's long toe would reveal even very faint steps on black).
const PLUME_BOUND = 2.4;  // bounding radius / bell radius
const PLUME_MAX = 3.0;    // bounding length / bell radius (before plumeScale)
const plumeGeometry = (() => {
  const g = new THREE.CylinderGeometry(1, 1, 1, 24, 1, false);
  g.translate(0, -0.5, 0);
  g.rotateX(-Math.PI / 2);
  g.rotateY(Math.PI);
  return g;
})();

function plumeMaterial(color, seed) {
  return new THREE.ShaderMaterial({
    uniforms: {
      uTime: { value: 0 }, uPower: { value: 1 }, uSeed: { value: seed },
      uSheath: { value: new THREE.Color(color) },
      uAspect: { value: 1 }, // bound length / bound radius (for the ray metric)
      uBound: { value: PLUME_BOUND },
      uLen: { value: PLUME_MAX }, // bound length in bell radii
    },
    vertexShader: /* glsl */`
      varying vec3 vObj; varying vec3 vCam;
      void main() {
        vObj = position;
        vCam = (inverse(modelMatrix) * vec4(cameraPosition, 1.0)).xyz;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }`,
    fragmentShader: /* glsl */`
      uniform float uTime, uPower, uSeed, uAspect, uBound, uLen; uniform vec3 uSheath;
      varying vec3 vObj; varying vec3 vCam;
      void main() {
        // work in a space where radial and axial units are both metres-proportional
        vec3 o = vCam * vec3(1.0, 1.0, uAspect);
        vec3 d = normalize(vObj * vec3(1.0, 1.0, uAspect) - o);
        float dxy2 = max(dot(d.xy, d.xy), 1e-4);
        float t = -dot(o.xy, d.xy) / dxy2;
        vec2 q = o.xy + t * d.xy;
        float rho = length(q) * uBound;              // closest distance to the axis (bell radii)
        float s = -(o.z + t * d.z) / uAspect;        // 0 at the exit plane, 1 at the end of the bound
        float z = clamp(s, 0.0, 1.0) * uLen;         // distance behind the exit (bell radii)
        float wc = 0.30 * (1.0 + 0.6 * z);           // hot core: narrow, gone within ~0.4 r
        float wg = 0.45 * (1.0 + 0.5 * z);           // soft glow: a narrow tapered column, gone within ~3 r
        float core = exp(-rho * rho / (wc * wc)) * exp(-z / 0.35);
        // the column builds up over the first ~0.6 r behind the exit (the plasma detaches from the
        // magnetic nozzle), so in stern quarter views it does not lie over the dark bell mouth
        float glow = exp(-rho * rho / (wg * wg)) * exp(-z / 1.2) * (0.15 + 0.85 * smoothstep(0.0, 0.7, z));
        // nothing upstream of the exit plane (the bell interior is the throat glow). The profiles
        // are evaluated where the ray passes closest to the axis, but an oblique ray crosses each
        // Gaussian over an axial stretch ~ width * (axial / radial travel): gate by the fraction of
        // that stretch that lies downstream of the exit (a smooth CDF, not a hard cut, which would
        // draw a straight edge across the dark bell mouth)
        float slope = abs(d.z) / (sqrt(dxy2) * uAspect);   // axial per radial travel (real units)
        float gc = smoothstep(-1.0, 1.0, s / max(0.02, 1.2 * wc * slope / uLen));
        float gg = smoothstep(-1.0, 1.0, s / max(0.02, 1.2 * wg * slope / uLen));
        float tail = 1.0 - smoothstep(0.55, 1.0, s);
        float path = min(inversesqrt(dxy2), 2.0);    // a little denser when looking along the jet
        float flick = 0.96 + 0.04 * sin(uTime * 61.0 + uSeed * 9.0) * sin(uTime * 23.0 + uSeed);
        // seen end-on the plume is optically thin: the hot core (right at the exit plane, where it
        // would lie over the bell mouth) fades almost away; the soft column keeps a hint
        float axial = abs(normalize(vObj - vCam).z);
        // (from a stern quarter the column behind the exit projects over the bell mouth: the fade
        // starts ~70 degrees off the axis, and only the thin core gets the longer path along the jet)
        float endOn = smoothstep(0.3, 0.92, axial);
        vec3 col = vec3(0.93, 0.95, 1.0) * core * 0.4 * gc * path * mix(1.0, 0.12, endOn)
                 + uSheath * glow * 0.25 * gg * mix(1.0, 0.22, endOn);
        col *= tail * flick * uPower;
        gl_FragColor = vec4(col, 1.0);
      }`,
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.BackSide,
  });
}

const lightVS = /* glsl */`
  attribute vec3 color; attribute float size; attribute vec3 blink; // period, duty, phase
  uniform float uTime; uniform float uScale; uniform float uMinPx;
  varying vec3 vColor; varying float vOn; varying float vSize;
  void main() {
    vColor = color;
    float on = 1.0;
    if (blink.x > 0.0) { float t = fract(uTime / blink.x + blink.z); on = step(t, blink.y); }
    vOn = on;
    vec4 mv = modelViewMatrix * vec4(position, 1.0);
    float px = max(uMinPx, size * uScale / -mv.z);
    vSize = px;
    gl_PointSize = px * on;
    gl_Position = projectionMatrix * mv;
  }`;
// The core burns toward white only when the light is drawn large enough to show a halo around
// it: at the 2-3 px minimum (carrier and fleet distances) red and green stay saturated. Lit
// windows (dim warm colours) keep their colour at any size.
const lightFS = /* glsl */`
  varying vec3 vColor; varying float vOn; varying float vSize;
  void main() {
    vec2 d = gl_PointCoord - 0.5; float r = length(d) * 2.0;
    float core = smoothstep(0.35, 0.0, r);
    float halo = pow(max(0.0, 1.0 - r), 3.0) * 0.6;
    float a = (core + halo) * vOn;
    if (a < 0.01) discard;
    // (dim sources such as lit ports never burn white: only lamps, max channel >= ~0.5, do)
    float lamp = smoothstep(0.25, 0.5, max(vColor.r, max(vColor.g, vColor.b)));
    gl_FragColor = vec4(mix(vColor, vec3(1.0), core * 0.7 * lamp * smoothstep(2.0, 6.0, vSize)) * a * 4.0, a);
  }`;

/**
 * Attach plumes + lights to a ship group. Returns { update(t) }.
 * opts.power: 0..1 engine throttle multiplier. power <= 0 means engines off: no plume
 *   meshes are created and the throat glow in each bell (glbship.js) is hidden, so a
 *   parked ship costs nothing but its nav lights; opts.plumeScale lengthens plumes;
 * opts.spill: false skips the stern spill light (small or distant ships in a fleet).
 */
export function attachEffects(group, { power = 1, plumeScale = 1, spill = true } = {}) {
  const info = group.userData.ship;
  const updaters = [];
  const plumes = [];
  const enginesOn = power > 0;
  if (!enginesOn) for (const c of group.children) if (c.name === 'nozzle-glow' || c.name === 'nozzle-lining') c.visible = false;
  let seed = 1;
  for (const e of enginesOn ? info.engines : []) {
    const m = plumeMaterial(e.color ?? '#a4b2e2', seed++ * 1.37); // pale blue-white, not periwinkle
    const bound = e.radius * PLUME_BOUND;
    const lenR = Math.min(e.length / e.radius, PLUME_MAX) * plumeScale; // short: a few bell radii at most
    m.uniforms.uPower.value = power;
    m.uniforms.uLen.value = lenR;
    m.uniforms.uAspect.value = (lenR * e.radius) / bound;
    const mesh = new THREE.Mesh(plumeGeometry, m);
    mesh.scale.set(bound, bound, lenR * e.radius);
    mesh.position.copy(e.p);
    mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, -1), e.dir);
    mesh.renderOrder = 10;
    mesh.frustumCulled = false;
    mesh.name = 'plume';
    // Draw the proxy's near faces: its far faces lie behind the bell body, whose depth clipped
    // the glow along straight lines (a C-shaped rim) from a stern quarter. Only with the camera
    // inside the proxy are the far faces the visible ones. The ray metric is the same either way.
    const inv = new THREE.Matrix4(), cam = new THREE.Vector3();
    mesh.onBeforeRender = (_r, _s, camera) => {
      cam.setFromMatrixPosition(camera.matrixWorld).applyMatrix4(inv.copy(mesh.matrixWorld).invert());
      const inside = cam.x * cam.x + cam.y * cam.y < 1.05 && cam.z < 0.05 && cam.z > -1.05;
      m.side = inside ? THREE.BackSide : THREE.FrontSide;
    };
    group.add(mesh);
    plumes.push(m);
  }
  // Spill from the short plumes onto the ship's own stern: one light per ship,
  // aft of the engine cluster, inverse-square, short range. Only the plume can
  // light the stern plate (the throat glow radiates aft out of the bell), so
  // the intensity is that of the plume glow: radiance ~0.25 over ~1.5 r^2 per
  // engine. Two bell radii aft keeps the near field on the stern plate at a
  // few percent of the sun's irradiance, as an extended source would.
  if (spill && info.engines.length && power > 0.05) {
    const c = info.engines.reduce((acc, e) => acc.add(e.p), new THREE.Vector3()).divideScalar(info.engines.length);
    const rMax = Math.max(...info.engines.map((e) => e.radius));
    const spread = Math.max(...info.engines.map((e) => e.p.distanceTo(c)));
    const I = info.engines.reduce((acc, e) => acc + e.radius * e.radius, 0) * 0.4 * power;
    const L = new THREE.PointLight('#c4d3ff', I, spread + rMax * 6, 2);
    L.position.copy(c).addScaledVector(info.engines[0].dir, rMax * 2.0);
    L.name = 'drive-spill';
    group.add(L);
  }
  if (plumes.length) updaters.push((t) => { for (const m of plumes) m.uniforms.uTime.value = t; });

  if (info.lights.length) {
    const n = info.lights.length;
    const pos = new Float32Array(n * 3), col = new Float32Array(n * 3), size = new Float32Array(n), blink = new Float32Array(n * 3);
    const c = new THREE.Color();
    info.lights.forEach((l, i) => {
      pos.set([l.p.x, l.p.y, l.p.z], i * 3);
      c.set(LIGHT_COLORS[l.color] ?? l.color);
      col.set([c.r, c.g, c.b], i * 3);
      size[i] = l.size;
      if (l.blink) blink.set([l.blink.period ?? 1.2, l.blink.duty ?? 0.12, l.blink.phase ?? 0], i * 3);
    });
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    g.setAttribute('color', new THREE.BufferAttribute(col, 3));
    g.setAttribute('size', new THREE.BufferAttribute(size, 1));
    g.setAttribute('blink', new THREE.BufferAttribute(blink, 3));
    const m = new THREE.ShaderMaterial({
      uniforms: { uTime: { value: 0 }, uScale: { value: 1160 }, uMinPx: { value: 2.0 } },
      vertexShader: lightVS, fragmentShader: lightFS,
      transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    });
    const pts = new THREE.Points(g, m);
    pts.frustumCulled = false;
    pts.renderOrder = 11;
    pts.name = 'navlights';
    group.add(pts);
    // sprite size = the light's true projected size on this lens: pixels per metre at 1 m is
    // viewportH / 2 * P[1][1] (P[1][1] = 1 / tan(fov/2), view offsets included)
    updaters.push((t, viewportH, projY) => { m.uniforms.uTime.value = t; if (viewportH) m.uniforms.uScale.value = viewportH * 0.5 * (projY || 2.9); });
  }
  return { update: (t, viewportH, projY) => updaters.forEach((u) => u(t, viewportH, projY)) };
}
