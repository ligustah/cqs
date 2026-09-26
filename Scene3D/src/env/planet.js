// Procedural home world below the fleet: terrain + biomes + oceans with sun
// glint, polar ice, an animated cloud deck (separate shell, casting shadows),
// city lights on the night side and a single-scattering atmosphere shell.
//
// Placement: the globe is centred on PLANET_DIR at an altitude chosen so it
// subtends ~71° of half-angle from the fleet (≈ a 370 km orbit around an
// Earth-sized world), giving a clearly curved horizon in the hero view.
// Lighting uses SUN_DIR with the same irradiance as the ships' key light.
//
// Rendering: the whole planet is drawn in the opaque queue before the ships
// (group renderOrder -5) with depth test/write off, so it never z-fights,
// never clips against the far plane, and ships always draw over it.
import * as THREE from 'three';
import { SUN_DIR, PLANET_DIR } from './lighting.js';
import { NOISE, FAR_CLAMP } from './glsl.js';
import { ATMO, ATMO_GLSL, createAtmosphereShell } from './atmosphere.js';
import { ENV } from './state.js';

const SUN_E = 4.2; // same irradiance as the DirectionalLight key in lighting.js

const query = new URLSearchParams(typeof location !== 'undefined' ? location.search : '');
const vecParam = (k) => {
  const v = query.get(k);
  if (!v) return null;
  const a = v.split(',').map(Number);
  return a.length === 3 && a.every(Number.isFinite) ? a : null;
};

// ---------------------------------------------------------------------------
// GLSL: terrain, biomes, clouds, city lights (object space = unit sphere,
// +Y = spin axis so |y| is the sine of latitude)
// ---------------------------------------------------------------------------
const WORLD_GLSL = /* glsl */`
#define PI 3.14159265
const vec3 SEED = vec3(17.3, -4.1, 8.6);
const float SEA = 0.045;
const float CLOUD_H = ${ATMO.cloud.toFixed(5)};

struct Terrain { float h; float m; float t; float rock; float det; float belt; };

float fbm4(vec3 p) {
  float s = 0.0, a = 0.5;
  for (int i = 0; i < 4; i++) { s += a * snoise(p); p = p * 2.07 + vec3(3.1, 1.7, 5.3); a *= 0.5; }
  return s;
}

Terrain terrain(vec3 n, float fp) {
  Terrain T;
  vec3 p = n * 1.3 + SEED;
  vec3 w = vec3(snoise(p * 0.75), snoise(p * 0.75 + vec3(19.1, 7.3, 2.9)), snoise(p * 0.75 + vec3(5.7, 31.3, 13.1)));
  vec3 q = p + w * 0.45;
  float c = fbm4(q);
  // fold belts along the zero-crossings of a second field (plate boundaries)
  float belt = 1.0 - abs(snoise(q * 1.6 + vec3(7.1, 3.3, 9.9)));
  belt *= belt; belt *= belt;
  // detail octaves, faded out once they get smaller than a pixel
  float det = 0.0, ridg = 0.0, a = 0.5, f = 26.0;
  for (int i = 0; i < 5; i++) {
    float wgt = 1.0 - smoothstep(0.18, 0.45, f * fp);
    if (wgt <= 0.0) break;
    float s = snoise(n * f + SEED * float(i + 2));
    det += a * wgt * s;
    ridg += a * wgt * (1.0 - abs(s));
    f *= 2.03; a *= 0.5;
  }
  float h = c + 0.06 * w.y - SEA;
  float landish = smoothstep(-0.02, 0.1, h);
  h += landish * belt * (0.12 + 0.16 * ridg);
  h += det * mix(0.045, 0.075, landish);
  T.h = h;
  T.det = det;
  T.belt = belt;
  T.m = clamp(0.45 + 0.6 * snoise(n * 2.3 + vec3(13.0, 2.0, 7.0)) + 0.3 * w.z + 0.3 * (1.0 - smoothstep(0.0, 0.1, h)), 0.0, 1.0);
  float lat = abs(n.y);
  T.t = 1.0 - 1.05 * pow(lat, 1.6) - 1.7 * max(h - 0.03, 0.0) + 0.1 * w.x + 0.03 * det;
  T.rock = smoothstep(0.09, 0.2, h) * (0.35 + 0.65 * belt);
  return T;
}

vec3 landAlbedo(Terrain T) {
  const vec3 JUNGLE = vec3(0.016, 0.048, 0.020);
  const vec3 FOREST = vec3(0.026, 0.056, 0.026);
  const vec3 GRASS = vec3(0.080, 0.100, 0.036);
  const vec3 SAVANNA = vec3(0.21, 0.165, 0.075);
  const vec3 DESERT = vec3(0.47, 0.27, 0.12);
  const vec3 ERG = vec3(0.58, 0.44, 0.27);
  const vec3 TUNDRA = vec3(0.12, 0.115, 0.085);
  const vec3 ROCK = vec3(0.17, 0.14, 0.11);
  const vec3 SNOW = vec3(0.82, 0.86, 0.92);
  float m = T.m, t = T.t;
  vec3 hot = mix(mix(DESERT, ERG, smoothstep(-0.15, 0.25, T.det)), SAVANNA, smoothstep(0.2, 0.36, m));
  hot = mix(hot, JUNGLE, smoothstep(0.5, 0.68, m));
  vec3 mild = mix(mix(SAVANNA, GRASS, smoothstep(0.2, 0.4, m)), FOREST, smoothstep(0.45, 0.62, m));
  vec3 col = mix(mild, hot, smoothstep(0.58, 0.72, t));
  col = mix(TUNDRA, col, smoothstep(0.2, 0.34, t));
  col *= 0.85 + 0.3 * (T.det * 0.5 + 0.5);
  col = mix(col, ROCK, T.rock);
  col = mix(vec3(0.40, 0.35, 0.25), col, smoothstep(0.0, 0.01, T.h));
  float snow = max(smoothstep(0.17, 0.10, t), smoothstep(0.23, 0.3, T.h + 0.04 * T.det));
  return mix(col, SNOW, snow);
}

vec3 oceanAlbedo(Terrain T) {
  const vec3 DEEP = vec3(0.004, 0.016, 0.042);
  const vec3 MID = vec3(0.008, 0.032, 0.070);
  const vec3 SHELF = vec3(0.020, 0.115, 0.125);
  vec3 col = mix(DEEP, MID, smoothstep(-0.35, -0.06, T.h));
  return mix(col, SHELF, smoothstep(-0.045, -0.004, T.h) * smoothstep(0.25, 0.5, T.t));
}

vec3 rotAxis(vec3 p, vec3 axis, float ang) {
  float c = cos(ang), s = sin(ang);
  return p * c + cross(axis, p) * s + axis * dot(axis, p) * (1.0 - c);
}

// cloud cover in [0,1] at object-space direction n
float cloudField(vec3 n, float t, int oct, float fp) {
  vec3 p = n;
  // cyclones: twist the domain around a few storm centres (sign by hemisphere)
  const vec3 S1 = normalize(vec3(0.37, 0.45, 0.81));
  const vec3 S2 = normalize(vec3(-0.62, -0.38, 0.69));
  const vec3 S3 = normalize(vec3(0.80, -0.25, -0.55));
  p = rotAxis(p, S1, 5.5 * exp(-(1.0 - dot(n, S1)) * 260.0));
  p = rotAxis(p, S2, -4.5 * exp(-(1.0 - dot(n, S2)) * 320.0));
  p = rotAxis(p, S3, -3.5 * exp(-(1.0 - dot(n, S3)) * 200.0));
  vec3 q = p * 2.6 + vec3(0.0, 0.0, t * 0.0015);
  vec3 w = vec3(snoise(q * 0.9 + vec3(0.0, t * 0.001, 0.0)), snoise(q * 0.9 + vec3(8.1, 2.3, 5.5)), snoise(q * 0.9 + vec3(3.3, 9.7, 1.1)));
  q += w * 0.55;
  q.y *= 1.7; // zonal shear: streaks run along the lines of latitude
  float s = 0.0, a = 0.5, f = 1.0;
  for (int i = 0; i < 7; i++) {
    if (i >= oct) break;
    float wgt = 1.0 - smoothstep(0.2, 0.5, f * 2.6 * fp);
    if (wgt <= 0.0) break;
    s += a * wgt * snoise(q * f);
    f *= 2.13; a *= 0.53;
  }
  float lat = abs(n.y);
  // wet equator, clear subtropics, stormy mid-latitudes
  float thr = 0.02 + 0.16 * smoothstep(0.1, 0.28, lat) * (1.0 - smoothstep(0.34, 0.5, lat)) - 0.05 * smoothstep(0.5, 0.75, lat);
  return smoothstep(thr, thr + 0.3, s + 0.12 * w.x);
}

// warm settlement lights for the night side (luminance, ~0..1.5)
float cityLights(vec3 n, Terrain T, float fp, out float warm) {
  warm = 0.5;
  float land = smoothstep(0.004, 0.02, T.h) * (1.0 - smoothstep(0.1, 0.18, T.h));
  float hab = land * smoothstep(0.3, 0.45, T.t) * (1.0 - 0.85 * smoothstep(0.32, 0.14, T.m) * smoothstep(0.58, 0.72, T.t));
  float coast = 1.0 - smoothstep(0.012, 0.07, T.h);
  float region = smoothstep(-0.25, 0.55, snoise(n * 5.0 + vec3(4.0, 9.0, 1.0)));
  float pop = hab * (0.3 + 0.7 * coast) * region;
  if (pop <= 0.002) return 0.0;
  float lights = pop * 0.05;
  for (int k = 0; k < 3; k++) {
    float sc = k == 0 ? 60.0 : (k == 1 ? 190.0 : 520.0);
    vec3 c = n * sc;
    vec3 id = floor(c), f = fract(c);
    vec3 r = hash33(id + float(k) * 17.0);
    float present = step(1.0 - pop * (k == 0 ? 0.6 : 0.95), r.x);
    vec3 pt = 0.25 + 0.5 * hash33(id + 3.7);
    float d = length(f - pt);
    float rad = k == 0 ? mix(0.08, 0.22, r.y) : mix(0.05, 0.13, r.y);
    float px = fp * sc;
    float cov = rad * rad / (rad * rad + px * px);
    float s = present * cov * smoothstep(rad + px, rad * 0.15, d) * (0.5 + r.z);
    lights += s * (k == 0 ? 1.2 : (k == 1 ? 0.7 : 0.45));
    if (k == 0) warm = r.z;
  }
  return lights;
}
`;

const COMMON = /* glsl */`
uniform vec3 uCenter; uniform float uR; uniform vec3 uSun; uniform float uSunE; uniform float uTime;
varying vec3 vObj; varying vec3 vWN; varying vec3 vRel;
`;

const VERT = /* glsl */`
uniform float uMeshR;
varying vec3 vObj; varying vec3 vWN; varying vec3 vRel;
void main() {
  vObj = position / uMeshR;
  vec4 w = modelMatrix * vec4(position, 1.0);
  vWN = mat3(modelMatrix) * position / uMeshR;
  vRel = w.xyz - cameraPosition;
  gl_Position = projectionMatrix * viewMatrix * w;
  ${FAR_CLAMP}
}`;

const SURFACE_FRAG = /* glsl */`
${COMMON}
uniform mat3 uWorldToCloud;
${NOISE}
${ATMO_GLSL}
${WORLD_GLSL}
float D_GGX(float NoH, float a) { float a2 = a * a; float d = NoH * NoH * (a2 - 1.0) + 1.0; return a2 / (PI * d * d); }
float V_GGX(float NoV, float NoL, float a) {
  float a2 = a * a;
  float gv = NoL * sqrt(NoV * NoV * (1.0 - a2) + a2);
  float gl = NoV * sqrt(NoL * NoL * (1.0 - a2) + a2);
  return 0.5 / max(gv + gl, 1e-5);
}
void main() {
  vec3 n = normalize(vObj);
  vec3 N = normalize(vWN);
  vec3 rd = normalize(vRel);
  vec3 V = -rd;
  vec3 L = uSun;
  float fp = max(length(fwidth(n)), 1e-6);
  Terrain T = terrain(n, fp);
  float aaH = max(fwidth(T.h), 1e-5);
  float water = 1.0 - smoothstep(-aaH, aaH, T.h);
  float seaIce = smoothstep(0.12, 0.06, T.t + 0.05 * T.det) * water;
  vec3 alb = mix(landAlbedo(T), oceanAlbedo(T), water);
  alb = mix(alb, vec3(0.60, 0.67, 0.76), seaIce);

  // relief: bump normal from screen-space height derivatives (land only)
  float hp = max(T.h, 0.0) * 0.010;
  vec3 Nb = N;
  {
    vec3 dpx = dFdx(vWN), dpy = dFdy(vWN);
    float dhx = dFdx(hp), dhy = dFdy(hp);
    vec3 r1 = cross(dpy, N), r2 = cross(N, dpx);
    float det = dot(dpx, r1);
    if (abs(det) > 1e-14) Nb = normalize(N - (dhx * r1 + dhy * r2) / det);
  }

  float muS = dot(N, L);
  float muV = max(dot(N, V), 0.0);
  vec3 sunL = uSunE * transmittance(1.00005, muS) * sunShadow(N * 1.00005, L);

  // cloud shadows: sample the deck where the sun ray through this point crosses it
  vec3 pc = normalize(N + L * (CLOUD_H / max(muS, 0.12)));
  float cden = cloudField(uWorldToCloud * pc, uTime, 3, 0.02);
  float cshadow = 1.0 - 0.7 * cden;

  vec3 col = alb / PI * (sunL * max(dot(Nb, L), 0.0) * cshadow + uSunE * skyIrradiance(muS));

  // ocean: GGX sun glint (two roughness lobes) + Fresnel sky reflection
  float wet = water * (1.0 - seaIce);
  if (wet > 0.0) {
    vec3 H = normalize(L + V);
    float NoH = max(dot(N, H), 0.0), VoH = max(dot(V, H), 0.0), NoL = max(muS, 0.0);
    float F = 0.02 + 0.98 * pow(1.0 - VoH, 5.0);
    float spec = (0.65 * D_GGX(NoH, 0.07) * V_GGX(muV, NoL, 0.07) + 0.35 * D_GGX(NoH, 0.2) * V_GGX(muV, NoL, 0.2)) * F * NoL;
    float Fv = 0.02 + 0.98 * pow(1.0 - muV, 5.0);
    vec3 sky = uSunE * vec3(0.010, 0.024, 0.060) * smoothstep(-0.1, 0.3, muS);
    col += wet * (sunL * cshadow * spec + sky * Fv);
  }

  // city lights beyond the terminator
  float night = smoothstep(0.05, -0.12, muS);
  if (night > 0.0) {
    float warm;
    float cl = cityLights(n, T, fp, warm);
    col += night * cl * mix(vec3(1.0, 0.52, 0.20), vec3(1.0, 0.78, 0.50), warm) * 0.9;
  }

  // aerial perspective (the atmosphere shell adds the in-scattered light)
  col *= transmittance(1.00005, muV);
  gl_FragColor = vec4(col, 1.0);
}`;

const CLOUD_FRAG = /* glsl */`
${COMMON}
${NOISE}
${ATMO_GLSL}
${WORLD_GLSL}
void main() {
  vec3 n = normalize(vObj);
  vec3 N = normalize(vWN);
  vec3 rd = normalize(vRel);
  vec3 V = -rd;
  vec3 L = uSun;
  float fp = max(length(fwidth(n)), 1e-6);
  float d = cloudField(n, uTime, 7, fp);
  if (d < 0.004) discard;
  // puffy relief from the screen-space density gradient
  vec3 Nc = N;
  {
    float hp = d * 0.0016;
    vec3 dpx = dFdx(vWN), dpy = dFdy(vWN);
    float dhx = dFdx(hp), dhy = dFdy(hp);
    vec3 r1 = cross(dpy, N), r2 = cross(N, dpx);
    float det = dot(dpx, r1);
    if (abs(det) > 1e-14) Nc = normalize(N - (dhx * r1 + dhy * r2) / det);
  }
  float muS = dot(N, L);
  float muV = max(dot(N, V), 0.0);
  float r = 1.0 + CLOUD_H;
  vec3 sunL = uSunE * transmittance(r, muS) * sunShadow(N * r, L);
  float lit = clamp((dot(Nc, L) + 0.15) / 1.15, 0.0, 1.0);
  float thick = mix(0.72, 1.0, smoothstep(0.2, 0.9, d)); // thin wisps let more light through, look greyer
  vec3 col = 0.88 / PI * (sunL * lit * thick + uSunE * skyIrradiance(muS) * 0.9);
  // grazing views see the deck edge-on: denser, merging toward the horizon
  float a = clamp(d, 0.0, 1.0) * 0.96;
  a = 1.0 - pow(1.0 - a, mix(1.0, 3.5, pow(1.0 - muV, 4.0)));
  col *= transmittance(r, muV);
  gl_FragColor = vec4(col * a, a);
}`;

// ---------------------------------------------------------------------------
export function createPlanet(scene, {
  radius = 200000,
  angularRadius = 71,     // half-angle subtended from the fleet (deg) → altitude
  direction = PLANET_DIR,
  orbitRate = 0.0006,     // rad/s of apparent ground motion under the fleet
  windRate = 0.00011,     // extra zonal drift of the cloud deck (rad/s)
  orientation = new THREE.Euler(0.0, 0.0, 0.0),
} = {}) {
  const dirOverride = vecParam('envdir');
  const rotOverride = vecParam('envrot');
  const angOverride = parseFloat(query.get('envang'));
  if (Number.isFinite(angOverride)) angularRadius = angOverride;
  const dir = (dirOverride ? new THREE.Vector3(...dirOverride) : direction.clone()).normalize();
  if (rotOverride) orientation = new THREE.Euler(...rotOverride.map(THREE.MathUtils.degToRad));

  const dist = radius / Math.sin(THREE.MathUtils.degToRad(angularRadius));
  const center = dir.clone().multiplyScalar(dist);
  const sunDir = SUN_DIR.clone().normalize();

  const group = new THREE.Group();
  group.name = 'planet';
  group.position.copy(center);
  group.renderOrder = -5;

  const baseUniforms = () => ({
    uCenter: { value: center },
    uR: { value: radius },
    uSun: { value: sunDir },
    uSunE: { value: SUN_E },
    uTime: { value: 0 },
  });
  const matOpts = { transparent: false, depthTest: false, depthWrite: false };

  // --- surface -------------------------------------------------------------
  const surfaceMat = new THREE.ShaderMaterial({
    ...matOpts,
    uniforms: { ...baseUniforms(), uMeshR: { value: radius }, uWorldToCloud: { value: new THREE.Matrix3() } },
    vertexShader: VERT,
    fragmentShader: SURFACE_FRAG,
    blending: THREE.NoBlending,
  });
  const surface = new THREE.Mesh(new THREE.SphereGeometry(radius, 384, 192), surfaceMat);
  surface.name = 'planet-surface';
  surface.renderOrder = 0;

  // --- cloud deck ------------------------------------------------------------
  const cloudR = radius * (1 + ATMO.cloud);
  const cloudMat = new THREE.ShaderMaterial({
    ...matOpts,
    uniforms: { ...baseUniforms(), uMeshR: { value: cloudR } },
    vertexShader: VERT,
    fragmentShader: CLOUD_FRAG,
    blending: THREE.CustomBlending,
    blendEquation: THREE.AddEquation,
    blendSrc: THREE.OneFactor,
    blendDst: THREE.OneMinusSrcAlphaFactor,
  });
  const clouds = new THREE.Mesh(new THREE.SphereGeometry(cloudR, 320, 160), cloudMat);
  clouds.name = 'planet-clouds';
  clouds.renderOrder = 1;

  // --- atmosphere --------------------------------------------------------------
  const atmosphere = createAtmosphereShell({ radius, center, sunDir, sunE: SUN_E });
  atmosphere.renderOrder = 2;

  for (const m of [surface, clouds, atmosphere]) { m.frustumCulled = false; group.add(m); }
  // debug: &envhide=atmosphere,clouds,surface
  for (const name of (query.get('envhide') || '').split(',')) {
    const m = { atmosphere, clouds, surface }[name];
    if (m) m.visible = false;
  }
  scene.add(group);

  // Apparent orbital motion: the ground flows under the fleet from bow (+Z)
  // to stern, i.e. a rotation about the axis Z × up through the planet centre.
  const up = dir.clone().negate();
  const orbitAxis = new THREE.Vector3(0, 0, 1).cross(up).normalize();
  const q0 = new THREE.Quaternion().setFromEuler(orientation);
  const qOrbit = new THREE.Quaternion();
  const qWind = new THREE.Quaternion();
  const Y = new THREE.Vector3(0, 1, 0);
  const m4 = new THREE.Matrix4();

  function pose(t) {
    qOrbit.setFromAxisAngle(orbitAxis, orbitRate * t);
    surface.quaternion.copy(qOrbit).multiply(q0);
    qWind.setFromAxisAngle(Y, windRate * t);
    clouds.quaternion.copy(qOrbit).multiply(q0).multiply(qWind);
    m4.makeRotationFromQuaternion(clouds.quaternion).transpose();
    surfaceMat.uniforms.uWorldToCloud.value.setFromMatrix4(m4);
    surfaceMat.uniforms.uTime.value = t;
    cloudMat.uniforms.uTime.value = t;
  }
  pose(0);

  ENV.planet = { center, radius, top: ATMO.top, group };

  return {
    group,
    radius,
    center,
    sunDir,
    update(t) { pose(t); },
  };
}
