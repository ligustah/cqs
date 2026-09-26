// Runtime effects attached to finished ships: plasma exhaust plumes and
// navigation / running lights. Both read anchors recorded by ShipBuilder.
import * as THREE from 'three';
import { LIVERY } from './materials.js';

const LIGHT_COLORS = {
  red: LIVERY.navRed, green: LIVERY.navGreen, white: '#ffffff', amber: LIVERY.amber, cyan: '#7fe8ff',
};

const plumeGeometry = (() => {
  // unit plume: radius 1 at z=0 widening to 1.35 at z=-1 (scaled per engine)
  const g = new THREE.CylinderGeometry(1.0, 1.35, 1, 32, 12, true);
  g.translate(0, -0.5, 0);
  g.rotateX(-Math.PI / 2);
  g.rotateY(Math.PI);
  return g;
})();

function plumeMaterial(color) {
  return new THREE.ShaderMaterial({
    uniforms: { uTime: { value: 0 }, uColor: { value: new THREE.Color(color) }, uPower: { value: 1 }, uSeed: { value: Math.random() * 10 } },
    vertexShader: /* glsl */`
      varying float vT; varying vec3 vN; varying vec3 vV;
      void main() {
        vT = clamp(-position.z, 0.0, 1.0);
        vec4 mv = modelViewMatrix * vec4(position, 1.0);
        vN = normalize(normalMatrix * normal);
        vV = normalize(-mv.xyz);
        gl_Position = projectionMatrix * mv;
      }`,
    fragmentShader: /* glsl */`
      uniform float uTime; uniform vec3 uColor; uniform float uPower; uniform float uSeed;
      varying float vT; varying vec3 vN; varying vec3 vV;
      void main() {
        float edge = pow(abs(dot(normalize(vN), normalize(vV))), 1.6);
        float along = pow(1.0 - vT, 2.2);
        float diamonds = 0.75 + 0.25 * sin(vT * 38.0 - uTime * 30.0 + uSeed);
        float flicker = 0.9 + 0.1 * sin(uTime * 53.0 + uSeed * 7.0) * sin(uTime * 17.0 + uSeed);
        float a = edge * along * diamonds * flicker * uPower;
        vec3 col = mix(uColor, vec3(1.0), smoothstep(0.55, 1.0, edge) * (1.0 - vT) * 0.8);
        gl_FragColor = vec4(col * a * 3.2, a);
      }`,
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide,
  });
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
  for (const e of info.engines) {
    const m = plumeMaterial(e.color ?? LIVERY.engine);
    m.uniforms.uPower.value = power;
    const mesh = new THREE.Mesh(plumeGeometry, m);
    mesh.scale.set(e.radius * 0.92, e.radius * 0.92, e.length * plumeScale);
    mesh.position.copy(e.p);
    mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, -1), e.dir);
    mesh.renderOrder = 10;
    mesh.frustumCulled = false;
    mesh.name = 'plume';
    group.add(mesh);
    plumes.push(m);
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
