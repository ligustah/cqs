// Atmospheric scattering shared by the planet surface, the cloud deck and the
// atmosphere shell. Single scattering (Rayleigh + Mie) with analytic optical
// depths (Chapman grazing-incidence approximation, after C. Schüler), so the
// view and sun transmittances are smooth and cheap enough for SwiftShader.
//
// All lengths are in planet radii (planet centre at the origin, surface r = 1).
import * as THREE from 'three';
import { RAY, FAR_CLAMP } from './glsl.js';

// Physical set-up (Earth-like column optical depths, scale heights slightly
// exaggerated so the limb reads at fleet-camera distances).
export const ATMO = {
  HR: 0.0021,       // Rayleigh scale height  (≈ 13 km on an Earth-sized world)
  HM: 0.00045,      // Mie (haze) scale height
  top: 1.0 + 0.0021 * 12.0,
  cloud: 0.0022,    // cloud deck altitude
};

export const ATMO_GLSL = /* glsl */`
${RAY}
const float HR = ${ATMO.HR.toFixed(6)};
const float HM = ${ATMO.HM.toFixed(6)};
const float R_TOP = ${ATMO.top.toFixed(6)};
// scattering coefficients per planet radius; vertical optical depth ≈ Earth's
const vec3 BETA_R = vec3(0.0460, 0.1080, 0.2650) / HR;
const float BETA_M = 0.030 / HM;
const float BETA_ME = BETA_M * 1.11;
const float MIE_G = 0.76;

float chapmanC(float x, float mu) {
  float c = sqrt(1.5707963 * x);
  return c / ((c - 1.0) * mu + 1.0);
}
// ∫ρ ds (ρ0 = 1) from radius r to infinity along a ray with zenith cosine mu.
// Rays that dip below the surface are clamped at the grazing value; use
// sunShadow() for the planet's actual shadow.
float odepth(float r, float mu, float H) {
  float h = max(r - 1.0, 0.0) / H;
  if (mu >= 0.0) return H * exp(-h) * chapmanC(r / H, mu);
  float r0 = r * sqrt(max(1.0 - mu * mu, 0.0));
  float h0 = max(r0 - 1.0, 0.0) / H;
  return H * (2.0 * exp(-h0) * chapmanC(max(r0, 1.0) / H, 0.0) - exp(-h) * chapmanC(r / H, -mu));
}
vec3 transmittance(float r, float mu) {
  return exp(-(BETA_R * odepth(r, mu, HR) + BETA_ME * odepth(r, mu, HM)));
}
// soft planet shadow for a point at p (|p| >= 1) toward the sun
float sunShadow(vec3 p, vec3 L) {
  float r = length(p);
  float mu = dot(p, L) / r;
  if (mu >= 0.0) return 1.0;
  float r0 = r * sqrt(max(1.0 - mu * mu, 0.0));
  return smoothstep(0.9993, 1.0012, r0);
}
float phaseR(float c) { return 0.0596831 * (1.0 + c * c); }
float phaseM(float c) {
  float g2 = MIE_G * MIE_G;
  return 0.1193662 * (1.0 - g2) * (1.0 + c * c) / ((2.0 + g2) * pow(1.0 + g2 - 2.0 * MIE_G * c, 1.5));
}
// Diffuse skylight reaching the ground (cheap fit of the Rayleigh sky dome).
vec3 skyIrradiance(float muS) {
  float day = smoothstep(-0.18, 0.35, muS);
  vec3 blue = vec3(0.045, 0.085, 0.17);
  vec3 dusk = vec3(0.10, 0.055, 0.045);
  return mix(dusk * smoothstep(-0.18, 0.05, muS), blue, smoothstep(0.02, 0.35, muS)) * day * 1.4;
}
`;

// In-scattered light along a camera ray: rgb = radiance / sunE, a = grey
// transmittance to the background (only meaningful when the ray misses the planet).
export const INSCATTER_GLSL = /* glsl */`
const int ATMO_N = 8; // samples per half-ray
vec4 inscatter(vec3 ro, vec3 rd, vec3 L, out float hitPlanet) {
  hitPlanet = 0.0;
  vec2 ta = raySphere(ro, rd, R_TOP);
  if (ta.y <= 0.0 || ta.x > ta.y) return vec4(0.0, 0.0, 0.0, 1.0);
  float t0 = max(ta.x, 0.0), t1 = ta.y;
  vec2 tp = raySphere(ro, rd, 1.0);
  if (tp.x < tp.y && tp.x > 0.0) { hitPlanet = 1.0; t1 = tp.x; }
  // density peaks at the ray's closest approach to the planet centre
  float tc = clamp(-dot(ro, rd), t0, t1);
  vec3 sR = vec3(0.0), sM = vec3(0.0);
  for (int k = 0; k < 2; k++) {
    float len = k == 0 ? tc - t0 : t1 - tc;
    float dir = k == 0 ? -1.0 : 1.0;
    if (len <= 1e-7) continue;
    for (int i = 0; i < ATMO_N; i++) {
      float fi = float(i);
      float s = (fi + 0.5) / float(ATMO_N);
      float t = tc + dir * len * s * s;
      float ds = len * (2.0 * fi + 1.0) / float(ATMO_N * ATMO_N);
      vec3 p = ro + rd * t;
      float r = length(p);
      float h = max(r - 1.0, 0.0);
      float dR = exp(-h / HR) * ds, dM = exp(-h / HM) * ds;
      float muS = dot(p, L) / r, muV = -dot(p, rd) / r;
      vec3 tau = BETA_R * (odepth(r, muS, HR) + odepth(r, muV, HR)) + BETA_ME * (odepth(r, muS, HM) + odepth(r, muV, HM));
      vec3 T = exp(-tau) * sunShadow(p, L);
      sR += dR * T; sM += dM * T;
    }
  }
  float c = dot(rd, L);
  vec3 col = sR * BETA_R * phaseR(c) + sM * BETA_M * phaseM(c);
  // grey transmittance of the whole ray (camera sits above the atmosphere)
  float rc = length(ro);
  float muC = dot(ro, rd) / rc;
  vec3 Tv = hitPlanet > 0.5 ? vec3(1.0) : transmittance(rc, muC);
  return vec4(col, dot(Tv, vec3(0.2126, 0.7152, 0.0722)));
}
`;

export function createAtmosphereShell({ radius, center, sunDir, sunE, segments = 160 }) {
  const mat = new THREE.ShaderMaterial({
    uniforms: {
      uCenter: { value: center },
      uR: { value: radius },
      uSun: { value: sunDir },
      uSunE: { value: sunE },
      uBoost: { value: 1.6 },
    },
    vertexShader: /* glsl */`
      varying vec3 vRel;
      void main() {
        vec4 w = modelMatrix * vec4(position, 1.0);
        vRel = w.xyz - cameraPosition;
        gl_Position = projectionMatrix * viewMatrix * w;
        ${FAR_CLAMP}
      }`,
    fragmentShader: /* glsl */`
      uniform vec3 uCenter; uniform float uR; uniform vec3 uSun; uniform float uSunE; uniform float uBoost;
      varying vec3 vRel;
      ${ATMO_GLSL}
      ${INSCATTER_GLSL}
      void main() {
        vec3 ro = (cameraPosition - uCenter) / uR;
        vec3 rd = normalize(vRel);
        // draw front faces from outside, back faces from inside the shell
        bool inside = dot(ro, ro) < R_TOP * R_TOP;
        if (inside == gl_FrontFacing) discard;
        float hit;
        vec4 s = inscatter(ro, rd, uSun, hit);
        vec3 col = s.rgb * uSunE * uBoost;
        // premultiplied: rgb added, background scaled by grey transmittance
        gl_FragColor = vec4(col, 1.0 - s.a);
      }`,
    side: THREE.DoubleSide,
    transparent: false,
    depthTest: false,
    depthWrite: false,
    blending: THREE.CustomBlending,
    blendEquation: THREE.AddEquation,
    blendSrc: THREE.OneFactor,
    blendDst: THREE.OneMinusSrcAlphaFactor,
  });
  const mesh = new THREE.Mesh(new THREE.SphereGeometry(radius * ATMO.top, segments, segments / 2), mat);
  mesh.name = 'atmosphere';
  mesh.frustumCulled = false;
  return mesh;
}
