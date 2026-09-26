// Background sky at infinity: a restrained galactic band with dust lanes and a
// magenta emission nebula (matching the nebula glow baked into the env map),
// a magnitude-distributed star field with black-body tints, and the local star
// at SUN_DIR. The group follows the camera and draws first (renderOrder -10)
// with depth test/write off, so everything else paints over it.
import * as THREE from 'three';
import { mulberry32 } from '../lib/rng.js';
import { SUN_DIR } from './lighting.js';
import { NOISE, FAR_CLAMP } from './glsl.js';
import { createSun } from './sun.js';
import { ENV } from './state.js';

// Galactic frame: band plane through the env-map nebula direction, tilted so it
// crosses the hero and lineup skies diagonally.
const NEBULA_DIR = new THREE.Vector3(-0.7, 0.35, -0.6).normalize();
const BAND_B = new THREE.Vector3(0.3, 0.78, -0.55).normalize();
const BAND_N = new THREE.Vector3().crossVectors(NEBULA_DIR, BAND_B).normalize();
const CORE_DIR = NEBULA_DIR.clone().applyAxisAngle(BAND_N, -0.32).normalize();

// Tanner Helland's black-body fit → linear RGB with unit luminance
function starColor(kelvin) {
  const t = kelvin / 100;
  let r, g, b;
  if (t <= 66) { r = 255; g = 99.4708025861 * Math.log(t) - 161.1195681661; }
  else { r = 329.698727446 * Math.pow(t - 60, -0.1332047592); g = 288.1221695283 * Math.pow(t - 60, -0.0755148492); }
  if (t >= 66) b = 255; else if (t <= 19) b = 0; else b = 138.5177312231 * Math.log(t - 10) - 305.0447927307;
  const c = new THREE.Color().setRGB(
    THREE.MathUtils.clamp(r, 0, 255) / 255, THREE.MathUtils.clamp(g, 0, 255) / 255, THREE.MathUtils.clamp(b, 0, 255) / 255,
    THREE.SRGBColorSpace);
  const lum = 0.2126 * c.r + 0.7152 * c.g + 0.0722 * c.b;
  return c.multiplyScalar(1 / Math.max(lum, 1e-3));
}

function buildStars(count, radius, seed) {
  const rnd = mulberry32(seed);
  const gauss = () => Math.sqrt(-2 * Math.log(Math.max(rnd(), 1e-9))) * Math.cos(2 * Math.PI * rnd());
  const pos = new Float32Array(count * 3), col = new Float32Array(count * 3), size = new Float32Array(count);
  const v = new THREE.Vector3();
  const e1 = CORE_DIR.clone(), e2 = new THREE.Vector3().crossVectors(BAND_N, CORE_DIR).normalize();
  const mLo = -1.3, mHi = 7.6, slope = 0.43; // N(<m) ∝ 10^(slope·m): many faint, few bright
  for (let i = 0; i < count; i++) {
    const m = Math.max(mLo, mHi + Math.log10(Math.max(rnd(), 1e-12)) / slope);
    const faint = m > 4.5;
    if (faint && rnd() < 0.5) {
      // unresolved-disc population: concentrated in the band, denser toward the core
      const lon = rnd() < 0.35 ? gauss() * 0.7 : rnd() * Math.PI * 2;
      const lat = gauss() * 0.11;
      v.copy(e1).multiplyScalar(Math.cos(lon)).addScaledVector(e2, Math.sin(lon)).multiplyScalar(Math.cos(lat)).addScaledVector(BAND_N, Math.sin(lat));
    } else {
      v.set(gauss(), gauss(), gauss());
    }
    v.normalize();
    pos[i * 3] = v.x * radius; pos[i * 3 + 1] = v.y * radius; pos[i * 3 + 2] = v.z * radius;
    // spectral mix: bright naked-eye stars skew hot (B/A), faint ones cool (K/M)
    const u = rnd();
    let K;
    if (m < 2.0) K = u < 0.45 ? 9000 + rnd() * 16000 : u < 0.75 ? 5800 + rnd() * 3000 : 3500 + rnd() * 1500;
    else K = u < 0.14 ? 8500 + rnd() * 12000 : u < 0.45 ? 5600 + rnd() * 2400 : 3300 + rnd() * 2300;
    const c = starColor(K).lerp(new THREE.Color(1, 1, 1), 0.35);
    // peak radiance of the PSF; compressed dynamic range (0.3 of true flux ratio)
    const peak = 0.012 * Math.pow(10, -0.4 * 0.72 * (m - mHi));
    col[i * 3] = c.r * peak; col[i * 3 + 1] = c.g * peak; col[i * 3 + 2] = c.b * peak;
    size[i] = m < 1.5 ? 15 : m < 3.5 ? 6 : 4;
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  g.setAttribute('color', new THREE.BufferAttribute(col, 3));
  g.setAttribute('size', new THREE.BufferAttribute(size, 1));
  return g;
}

export function createSky(scene, { stars = 15000, radius = 9000 } = {}) {
  const group = new THREE.Group();
  group.name = 'sky';
  group.renderOrder = -10;
  const common = { transparent: false, depthTest: false, depthWrite: false };

  // --- dome: galactic band, dust, emission nebula ---------------------------
  const dome = new THREE.Mesh(
    new THREE.SphereGeometry(radius, 96, 48),
    new THREE.ShaderMaterial({
      ...common,
      side: THREE.BackSide,
      blending: THREE.NoBlending,
      uniforms: {
        uBandN: { value: BAND_N }, uCore: { value: CORE_DIR }, uNeb: { value: NEBULA_DIR },
      },
      vertexShader: /* glsl */`
        varying vec3 vDir;
        void main() { vDir = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); ${FAR_CLAMP} }`,
      fragmentShader: /* glsl */`
        uniform vec3 uBandN; uniform vec3 uCore; uniform vec3 uNeb;
        varying vec3 vDir;
        ${NOISE}
        void main() {
          vec3 d = normalize(vDir);
          float n1 = snoise(d * 2.6 + 1.3);
          float n2 = snoise(d * 6.5 + 4.1);
          float n3 = snoise(d * 15.0 - 2.7);
          float b = dot(d, uBandN) + 0.03 * n1;           // warped galactic latitude
          float lc = dot(d, uCore);
          float coreW = smoothstep(-0.1, 1.0, lc);
          float width = mix(0.075, 0.19, coreW * coreW);
          float band = exp(-b * b / (width * width));
          float bulge = exp(-(1.0 - lc) * 7.0) * exp(-b * b / 0.05);
          float clump = clamp(0.6 + 0.35 * n2 + 0.2 * n3, 0.0, 1.4);
          // dark rifts hugging the mid-plane
          float lane = exp(-pow((b - 0.012 * n3) / 0.04, 2.0));
          float dust = smoothstep(0.05, 0.65, 0.55 * n2 + 0.35 * n1 + 0.35) * lane;
          vec3 starlight = mix(vec3(0.62, 0.70, 0.95), vec3(1.0, 0.80, 0.60), coreW);
          vec3 col = starlight * (band * clump * 0.016 + bulge * 0.028) * (1.0 - 0.8 * dust);
          // emission nebula near the env-map glow: H-alpha magenta core, teal O-III fringe
          float dn = 1.0 - dot(d, uNeb);
          float shape = smoothstep(-0.1, 0.9, 0.55 * snoise(d * 4.0 + 7.0) + 0.45 * n2 + 0.25);
          float neb = exp(-dn * 22.0) * shape;
          float fringe = exp(-dn * 9.0) * smoothstep(0.2, 0.8, n3 * 0.5 + n1 * 0.5 + 0.3) * (1.0 - neb);
          col += neb * vec3(0.050, 0.010, 0.040) + fringe * vec3(0.0, 0.012, 0.016);
          col *= 1.0 - 0.6 * dust * smoothstep(0.0, 0.3, neb);
          col += vec3(0.0016, 0.0019, 0.0034); // faint zodiacal/extragalactic floor
          gl_FragColor = vec4(col, 1.0);
        }`,
    }),
  );
  dome.renderOrder = 0;

  // --- stars -------------------------------------------------------------------
  const pts = new THREE.Points(buildStars(stars, radius * 0.9, 1207), new THREE.ShaderMaterial({
    ...common,
    blending: THREE.AdditiveBlending,
    uniforms: { uPx: { value: 1 } },
    vertexShader: /* glsl */`
      attribute vec3 color; attribute float size;
      uniform float uPx;
      varying vec3 vC; varying float vS;
      void main() {
        vC = color; vS = size;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        gl_PointSize = size * uPx;
        ${FAR_CLAMP}
      }`,
    fragmentShader: /* glsl */`
      uniform float uPx;
      varying vec3 vC; varying float vS;
      void main() {
        vec2 q = (gl_PointCoord - 0.5) * vS;          // offset in (CSS) pixels
        float r2 = dot(q, q);
        float psf = exp(-r2 / (2.0 * 0.62 * 0.62));
        float peak = max(max(vC.r, vC.g), vC.b);
        if (vS > 10.0) {
          // brightest stars: faint halo and tiny cross spikes (echo the sun's)
          vec2 a = abs(q);
          psf += 0.045 * exp(-sqrt(r2) / 1.6);
          psf += 0.05 * (exp(-a.y / 0.45) * exp(-a.x / 2.6) + exp(-a.x / 0.45) * exp(-a.y / 2.6));
        }
        gl_FragColor = vec4(vC * psf, 1.0);
      }`,
  }));
  pts.renderOrder = 1;

  // --- the local star --------------------------------------------------------
  const sun = createSun({ dir: SUN_DIR, distance: radius * 0.8 });
  sun.renderOrder = 2;

  for (const o of [dome, pts, sun]) { o.frustumCulled = false; group.add(o); }
  scene.add(group);

  const oc = new THREE.Vector3();
  const sunDir = SUN_DIR.clone().normalize();
  return {
    group,
    sun,
    update(t, camera, renderer) {
      group.position.copy(camera.position);
      if (renderer) pts.material.uniforms.uPx.value = renderer.getPixelRatio();
      // fade the star's lens elements as it sets behind the planet / atmosphere
      let vis = 1;
      const p = ENV.planet;
      if (p) {
        oc.copy(camera.position).sub(p.center);
        const tc = -oc.dot(sunDir);
        if (tc > 0) {
          const closest = Math.sqrt(Math.max(oc.lengthSq() - tc * tc, 0)) / p.radius - 1;
          vis = THREE.MathUtils.smoothstep(closest, 0.0, 0.012);
        }
      }
      sun.material.uniforms.uVis.value = vis;
    },
  };
}
