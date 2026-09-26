// Runtime effects attached to finished ships: plasma exhaust plumes and
// navigation / running lights. Both read anchors recorded by ShipBuilder.
import * as THREE from 'three';
import { LIVERY } from './materials.js';

const LIGHT_COLORS = {
  red: LIVERY.navRed, green: LIVERY.navGreen, white: '#ffffff', amber: LIVERY.amber, cyan: '#7fe8ff',
};

// Fusion-drive exhaust. In vacuum the plasma is nearly invisible a short way
// past the magnetic nozzle, so the drive reads as a hot glow in the bell and a
// short, soft plume (a few nozzle radii), never a long beam. The mesh is only a
// bounding cylinder (radius 1 = sheath edge, length 1, nozzle at z = 0, plume
// toward -z); the fragment shader finds where the view ray passes closest to
// the plume axis and integrates a Gaussian core + sheath there, so the plume
// reads as a luminous volume from any angle.
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
      uAspect: { value: 1 }, // plume length / sheath radius (for the ray metric)
    },
    vertexShader: /* glsl */`
      varying vec3 vObj; varying vec3 vCam;
      void main() {
        vObj = position;
        vCam = (inverse(modelMatrix) * vec4(cameraPosition, 1.0)).xyz;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }`,
    fragmentShader: /* glsl */`
      uniform float uTime, uPower, uSeed, uAspect; uniform vec3 uSheath;
      varying vec3 vObj; varying vec3 vCam;
      void main() {
        // work in a space where radial and axial units are both metres-proportional
        vec3 o = vCam * vec3(1.0, 1.0, uAspect);
        vec3 d = normalize(vObj * vec3(1.0, 1.0, uAspect) - o);
        float dxy2 = max(dot(d.xy, d.xy), 1e-4);
        float t = -dot(o.xy, d.xy) / dxy2;
        vec2 q = o.xy + t * d.xy;
        float rho = length(q);                       // closest distance to the axis (sheath radii)
        float s = clamp(-(o.z + t * d.z) / uAspect, -0.2, 1.2); // 0 at nozzle, 1 at plume tail
        float inside = smoothstep(-0.02, 0.03, s) * (1.0 - smoothstep(0.85, 1.0, s));
        float path = min(1.0 / sqrt(dxy2), 1.5);      // longer path when looking down the jet
        float sc = 0.10 * (1.0 + 1.8 * s);            // core radius grows downstream
        float ss = 0.42 * (1.0 + 1.1 * s);
        float diamonds = 1.0 + 0.5 * exp(-s * 6.0) * pow(0.5 + 0.5 * cos(s * 18.0 - uTime * 2.0), 8.0);
        float flick = 0.94 + 0.06 * sin(uTime * 61.0 + uSeed * 9.0) * sin(uTime * 23.0 + uSeed);
        float core = exp(-rho * rho / (sc * sc)) * exp(-s * 4.5) * diamonds;
        float sheath = exp(-rho * rho / (ss * ss)) * exp(-s * 3.0);
        vec3 col = vec3(1.0, 0.97, 1.0) * core * 2.2 + uSheath * sheath * 0.35;
        // seen end-on the plume is optically thin, not a searchlight: fade it
        // when looking down the axis so only the bell glow remains
        float axial = abs(normalize(vObj - vCam).z);
        col *= inside * path * flick * uPower * mix(1.0, 0.25, smoothstep(0.55, 0.95, axial));
        gl_FragColor = vec4(col, 1.0);
      }`,
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.BackSide,
  });
}

let flareTex = null;
function flareTexture() {
  if (flareTex) return flareTex;
  const c = document.createElement('canvas'); c.width = c.height = 256;
  const g = c.getContext('2d');
  const grd = g.createRadialGradient(128, 128, 0, 128, 128, 128);
  grd.addColorStop(0, 'rgba(255,255,255,1)'); grd.addColorStop(0.08, 'rgba(235,242,255,0.9)');
  grd.addColorStop(0.25, 'rgba(150,190,255,0.28)'); grd.addColorStop(1, 'rgba(90,130,255,0)');
  g.fillStyle = grd; g.fillRect(0, 0, 256, 256);
  flareTex = new THREE.CanvasTexture(c); flareTex.colorSpace = THREE.SRGBColorSpace;
  return flareTex;
}

const lightVS = /* glsl */`
  attribute vec3 color; attribute float size; attribute vec3 blink; // period, duty, phase
  uniform float uTime; uniform float uScale; uniform float uMinPx;
  varying vec3 vColor; varying float vOn;
  void main() {
    vColor = color;
    float on = 1.0;
    if (blink.x > 0.0) { float t = fract(uTime / blink.x + blink.z); on = step(t, blink.y); }
    vOn = on;
    vec4 mv = modelViewMatrix * vec4(position, 1.0);
    gl_PointSize = max(uMinPx, size * uScale / -mv.z) * on;
    gl_Position = projectionMatrix * mv;
  }`;
const lightFS = /* glsl */`
  varying vec3 vColor; varying float vOn;
  void main() {
    vec2 d = gl_PointCoord - 0.5; float r = length(d) * 2.0;
    float core = smoothstep(0.35, 0.0, r);
    float halo = pow(max(0.0, 1.0 - r), 3.0) * 0.6;
    float a = (core + halo) * vOn;
    if (a < 0.01) discard;
    gl_FragColor = vec4(mix(vColor, vec3(1.0), core * 0.7) * a * 4.0, a);
  }`;

/**
 * Attach plumes + lights to a ship group. Returns { update(t) }.
 * opts.power: 0..1 engine throttle multiplier; opts.plumeScale lengthens plumes.
 */
export function attachEffects(group, { power = 1, plumeScale = 1 } = {}) {
  const info = group.userData.ship;
  const updaters = [];
  const plumes = [];
  let seed = 1;
  for (const e of info.engines) {
    const m = plumeMaterial(e.color ?? '#3f6dff', seed++ * 1.37);
    const sheathR = e.radius * 1.35;
    const len = e.length * plumeScale; // short plume: a few nozzle radii (glbship default 3 r)
    m.uniforms.uPower.value = power;
    m.uniforms.uAspect.value = len / sheathR;
    const mesh = new THREE.Mesh(plumeGeometry, m);
    mesh.scale.set(sheathR, sheathR, len);
    mesh.position.copy(e.p);
    mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, -1), e.dir);
    mesh.renderOrder = 10;
    mesh.frustumCulled = false;
    mesh.name = 'plume';
    group.add(mesh);
    plumes.push(m);
    // glow in the nozzle throat
    const flare = new THREE.Sprite(new THREE.SpriteMaterial({ map: flareTexture(), color: new THREE.Color(1, 1, 1).multiplyScalar(0.45 * power), blending: THREE.AdditiveBlending, depthWrite: false, transparent: true }));
    flare.scale.setScalar(e.radius * 1.6);
    flare.position.copy(e.p).addScaledVector(e.dir, e.radius * 0.3);
    flare.renderOrder = 11;
    group.add(flare);
  }
  // one real light per capital ship so the drive illuminates its own stern
  const big = info.engines.filter((e) => e.radius >= 1.2);
  if (big.length && power > 0.05) {
    const c = big.reduce((acc, e) => acc.add(e.p), new THREE.Vector3()).divideScalar(big.length);
    const r = Math.max(...big.map((e) => e.radius));
    const dir = big[0].dir;
    const L = new THREE.PointLight('#b9cfff', 120 * r * r * big.length * power, r * 50, 2);
    L.position.copy(c).addScaledVector(dir, r * 2.5);
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
      uniforms: { uTime: { value: 0 }, uScale: { value: 800 }, uMinPx: { value: 2.0 } },
      vertexShader: lightVS, fragmentShader: lightFS,
      transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    });
    const pts = new THREE.Points(g, m);
    pts.frustumCulled = false;
    pts.renderOrder = 11;
    pts.name = 'navlights';
    group.add(pts);
    updaters.push((t, viewportH) => { m.uniforms.uTime.value = t; if (viewportH) m.uniforms.uScale.value = viewportH * 1.2; });
  }
  return { update: (t, viewportH) => updaters.forEach((u) => u(t, viewportH)) };
}
