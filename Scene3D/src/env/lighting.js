// Lighting rig shared by every view, built like a photograph in orbit:
//   - ONE hard key light: the local star (DirectionalLight, shadowed).
//   - Fill only from what is physically there: the sunlit planet below. It
//     comes from an image-based environment (PMREM) that contains the planet
//     disc at its true direction and angular size, lit by the same star, over
//     near-black space. Diffuse planet-shine and the faint grazing reflections
//     of the planet both come from it.
//   - No rim light, no hemisphere fudge, and no sun in the environment map
//     (IBL is unshadowed, so a sun in it would leak light into every shadow).
import * as THREE from 'three';

// Key from port-high (+X, az ~95 deg, el ~32 deg in the ship frame, bow +Z, port +X):
// 3/4 modelling in bow and quarter views, raking light across the stern, and a
// true shadow side to starboard. The ground under the fleet stays in daylight (cos ~0.6).
export const SUN_DIR = new THREE.Vector3(0.845, 0.53, -0.074).normalize();
export const PLANET_DIR = new THREE.Vector3(-0.15, -1, -0.25).normalize();
// Irradiance of the key light (planet.js and atmosphere.js import it, so the planet, its
// clouds and its air are lit by exactly the same star as the hulls).
export const SUN_E = 4.2;
// The home world is Earth-sized and the fleet holds a 400 km orbit (ISS altitude). Both are
// in scene metres: planet.js builds the globe at true scale, so camera moves of a few km
// cause no parallax and the ground reads hundreds of km below.
export const PLANET_RADIUS = 6371e3;
export const ORBIT_ALTITUDE = 400e3;
// Planet as seen from the fleet: half-angle in degrees (~70.2), used by planet.js and the env map.
export const PLANET_HALF_ANGLE = THREE.MathUtils.radToDeg(Math.asin(PLANET_RADIUS / (PLANET_RADIUS + ORBIT_ALTITUDE)));
// Mean albedo of the planet's visible day side (ocean ~0.06, land ~0.2, cloud ~0.6;
// Earth's Bond albedo ~0.3), tinted by Rayleigh scattering. Sets the planet-shine.
export const PLANET_ALBEDO = 0.3;

function envScene() {
  const scene = new THREE.Scene();
  const mat = new THREE.ShaderMaterial({
    side: THREE.BackSide,
    uniforms: {
      uSun: { value: SUN_DIR },
      uPlanet: { value: PLANET_DIR },
      uSinA: { value: Math.sin(THREE.MathUtils.degToRad(PLANET_HALF_ANGLE)) },
      uSunE: { value: SUN_E },
      uAlbedo: { value: PLANET_ALBEDO },
    },
    vertexShader: `varying vec3 vDir; void main(){ vDir = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
    fragmentShader: `
      uniform vec3 uSun; uniform vec3 uPlanet; uniform float uSinA, uSunE, uAlbedo;
      varying vec3 vDir;
      const float PI = 3.14159265;
      void main(){
        vec3 d = normalize(vDir);
        // deep space: effectively black (faint stars carry no usable light)
        vec3 col = vec3(0.0004, 0.00045, 0.0007);
        // planet: exact ray/sphere hit, planet radius = 1, centre at distance 1/sin(a)
        float D = 1.0 / uSinA;
        float b = dot(d, uPlanet) * D;
        float disc = b * b - (D * D - 1.0);
        float cosT = dot(d, uPlanet), cosA = sqrt(1.0 - uSinA * uSinA);
        if (disc > 0.0 && b > 0.0) {
          vec3 N = normalize(d * (b - sqrt(disc)) - uPlanet * D);
          float muS = dot(N, uSun);
          float muV = max(dot(N, -d), 0.0);
          // Lambertian day side, Rayleigh-blue tint; a little skylight past the terminator
          vec3 tint = vec3(0.74, 0.86, 1.0);
          float lit = max(muS, 0.0) + 0.03 * smoothstep(-0.12, 0.05, muS);
          col = uAlbedo / PI * uSunE * lit * tint;
          // blue airglow of the limb: longer path through the lit atmosphere
          col += uSunE / PI * vec3(0.012, 0.03, 0.075) * pow(1.0 - muV, 3.0) * smoothstep(-0.15, 0.25, muS);
        } else if (cosT > 0.0) {
          // thin bright atmosphere just outside the limb (a couple of degrees)
          float x = (cosA - cosT) / 0.035;
          vec3 up = normalize(d - uPlanet * cosT);
          float muS = dot(up, uSun);
          col += uSunE / PI * vec3(0.012, 0.03, 0.075) * exp(-max(x, 0.0) * 4.0) * smoothstep(-0.2, 0.2, muS);
        }
        gl_FragColor = vec4(col, 1.0);
      }`,
  });
  scene.add(new THREE.Mesh(new THREE.SphereGeometry(100, 128, 64), mat));
  return scene;
}

export function createLighting(renderer, scene, { shadowSize = 4096 } = {}) {
  const pmrem = new THREE.PMREMGenerator(renderer);
  const envRT = pmrem.fromScene(envScene(), 0.0);
  pmrem.dispose();
  scene.environment = envRT.texture;
  scene.environmentIntensity = 1.0; // physical: the env map is in the same units as the key

  // the star: ~5800 K, essentially white above the atmosphere
  const sun = new THREE.DirectionalLight(0xfff8f0, SUN_E);
  sun.position.copy(SUN_DIR).multiplyScalar(500);
  sun.castShadow = true;
  sun.shadow.mapSize.set(shadowSize, shadowSize);
  sun.shadow.bias = -0.0002;
  sun.shadow.normalBias = 0.04;
  scene.add(sun, sun.target);

  /** Fit the sun's shadow frustum around a world-space box. */
  function fitShadow(box) {
    const center = box.getCenter(new THREE.Vector3());
    const radius = box.getSize(new THREE.Vector3()).length() / 2;
    sun.target.position.copy(center);
    sun.position.copy(center).addScaledVector(SUN_DIR, radius * 2 + 50);
    const cam = sun.shadow.camera;
    cam.left = -radius; cam.right = radius; cam.top = radius; cam.bottom = -radius;
    cam.near = 1; cam.far = radius * 4 + 100;
    cam.updateProjectionMatrix();
    sun.shadow.normalBias = Math.max(0.02, radius / 2000);
  }

  return { sun, fitShadow, envTexture: envRT.texture };
}

// ---------------------------------------------------------------------------------------------
// Showcase ("studio") rig for the single-ship view (main.js, mode=ship, default; ?studio=0 falls
// back to the orbital rig above). Product-shot lighting, as in the concept art:
//   - a soft KEY from the upper front-left of the camera (shadowed, soft PCF);
//   - a cool FILL from the lower right that keeps the shadow side dark but readable;
//   - a thin cool RIM (kicker) from behind-right that draws the silhouette edges, and a weaker
//     warm kicker from behind-left;
//   - an environment of soft boxes (PMREM) over a navy gradient dome toned to the backdrop:
//     broad reflections on glass and paint sheen, and the unshadowed ambient that lifts the
//     shadow side;
//   - a screen-space gradient BACKDROP (dark navy at the edges, lighter behind the ship).
// Directions are placed relative to the camera azimuth / elevation (degrees, ship frame), so
// every view is lit the same way. All values are scene-linear; STUDIO.exposure is the default
// tone-mapping exposure for this rig.
// v12: key 3.8 -> 2.6, fill 1.3 -> 0.8, env 0.8 -> 0.55 (rim and exposure unchanged): the dark livery sits near-black
// on its lit faces as in the concept (key-lit deck ~sRGB 55-60, was ~90), so the small lights (lightscape, lit ports)
// read against it; lightscapeGain lifts pins and slits a little more in this rig only (effects.js LIGHTSCAPE_GAIN)
export const STUDIO = {
  exposure: 1.4,
  key: { az: -40, el: 40, E: 2.6, color: '#fff4e8' },   // relative to the camera: az < 0 = camera left
  fill: { az: 75, el: -5, E: 0.8, color: '#dee3eb' },
  rim: { az: 125, el: 24, E: 3.0, color: '#dbe6ff' },
  kick: { az: -140, el: 34, E: 1.2, color: '#ffe9d2' },
  envIntensity: 0.55,
  lightscapeGain: 1.15,
  // backdrop, as displayed sRGB (0-255) after tone mapping, before the vignette/grain pass
  backdrop: { centre: [66, 78, 98], edge: [14, 19, 30], at: [0.56, 0.58] },
};

/** Unit vector for an azimuth/elevation (degrees) relative to a camera at camAz/camEl (degrees). */
export function studioDir(camAz, camEl, az, el) {
  const a = THREE.MathUtils.degToRad(camAz + az), e = THREE.MathUtils.degToRad(el + camEl * 0.5);
  return new THREE.Vector3(Math.sin(a) * Math.cos(e), Math.sin(e), Math.cos(a) * Math.cos(e)).normalize();
}

function studioEnvScene(dirs) {
  const scene = new THREE.Scene();
  const mat = new THREE.ShaderMaterial({
    side: THREE.BackSide,
    uniforms: { uKey: { value: dirs.key }, uFill: { value: dirs.fill }, uRim: { value: dirs.rim }, uKick: { value: dirs.kick } },
    vertexShader: `varying vec3 vDir; void main(){ vDir = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
    fragmentShader: `
      uniform vec3 uKey, uFill, uRim, uKick; varying vec3 vDir;
      // soft box: a rounded-rectangle lobe (angular half-sizes w, h) around direction c, soft edge
      float box(vec3 d, vec3 c, float w, float h, float soft) {
        vec3 up = abs(c.y) > 0.95 ? vec3(1.0, 0.0, 0.0) : vec3(0.0, 1.0, 0.0);
        vec3 r = normalize(cross(up, c)); vec3 u = cross(c, r);
        float z = dot(d, c); if (z <= 0.0) return 0.0;
        vec2 q = vec2(dot(d, r), dot(d, u)) / z;
        vec2 e = abs(q) - vec2(w, h);
        float dist = length(max(e, 0.0)) + min(max(e.x, e.y), 0.0);
        return 1.0 - smoothstep(-soft, soft, dist);
      }
      void main(){
        vec3 d = normalize(vDir);
        // navy dome toned to the backdrop: darker below, a little lighter overhead
        vec3 navy = vec3(0.62, 0.69, 0.82);
        vec3 col = navy * mix(0.022, 0.050, smoothstep(-0.6, 0.9, d.y));
        // key soft box (large, warm white) and a dimmer skirt around it
        col += vec3(1.0, 0.96, 0.9) * (0.8 * box(d, uKey, 0.42, 0.30, 0.10) + 0.05 * box(d, uKey, 1.0, 0.8, 0.5));
        // fill: a broad, dim cool panel
        col += vec3(0.75, 0.83, 1.0) * 0.10 * box(d, uFill, 0.9, 0.6, 0.4);
        // rim strips: tall and narrow, cool (edge highlights on glass and glossy parts)
        col += vec3(0.85, 0.9, 1.0) * 1.3 * box(d, uRim, 0.10, 0.75, 0.05);
        col += vec3(1.0, 0.92, 0.82) * 0.5 * box(d, uKick, 0.10, 0.6, 0.05);
        gl_FragColor = vec4(col, 1.0);
      }`,
  });
  scene.add(new THREE.Mesh(new THREE.SphereGeometry(100, 128, 64), mat));
  return scene;
}

/** Inverse of three's Khronos PBR Neutral below its compression knee (sRGB-linear out -> in). */
function neutralInverse(rgb255) {
  const lin = new THREE.Color().setRGB(rgb255[0] / 255, rgb255[1] / 255, rgb255[2] / 255, THREE.SRGBColorSpace);
  const c = [lin.r, lin.g, lin.b];
  const mn = Math.min(...c);
  // below x = 0.08 the curve subtracts x - 6.25 x^2 (x = the smallest channel), a constant 0.04 above
  let off;
  if (mn < 0.04) { const m = Math.sqrt(mn / 6.25); off = m - 6.25 * m * m; } else off = 0.04;
  return new THREE.Vector3(c[0] + off, c[1] + off, c[2] + off);
}

/**
 * Studio rig: key / fill / rim / kicker lights, a soft-box PMREM environment and the gradient
 * backdrop. `camAz` / `camEl` in degrees (ship frame); `keyDir` (optional) overrides the key.
 * Returns the same { sun, fitShadow, envTexture } contract as createLighting (sun = the key).
 */
export function createStudioLighting(renderer, scene, { shadowSize = 4096, camAz = 35, camEl = 18, keyDir = null, exposure = STUDIO.exposure, lite = false, backdrop: backdropColours = null } = {}) {
  const S = STUDIO;
  const dirs = {
    key: keyDir ? keyDir.clone().normalize() : studioDir(camAz, camEl, S.key.az, S.key.el),
    fill: studioDir(camAz, camEl, S.fill.az, S.fill.el),
    rim: studioDir(camAz, camEl, S.rim.az, S.rim.el),
    kick: studioDir(camAz, camEl, S.kick.az, S.kick.el),
  };
  const pmrem = new THREE.PMREMGenerator(renderer);
  const envRT = pmrem.fromScene(studioEnvScene(dirs), 0.02);
  pmrem.dispose();
  scene.environment = envRT.texture;
  scene.environmentIntensity = S.envIntensity;

  const key = new THREE.DirectionalLight(S.key.color, S.key.E);
  key.castShadow = true;
  key.shadow.mapSize.set(shadowSize, shadowSize);
  key.shadow.bias = -0.0002;
  key.shadow.normalBias = 0.04;
  // soft shadow edges: PCF over a Vogel disk of this many texels (the phone tier's smaller map
  // already has larger texels, so it gets a smaller radius for the same penumbra and less noise)
  key.shadow.radius = lite ? 2 : 3.5;
  key.name = 'studio-key';
  scene.add(key, key.target);
  const extra = [];
  for (const [name, spec] of [['fill', S.fill], ['rim', S.rim], ['kick', S.kick]]) {
    const L = new THREE.DirectionalLight(spec.color, spec.E);
    L.position.copy(dirs[name]).multiplyScalar(500);
    L.name = `studio-${name}`;
    L.userData.dir = dirs[name];
    scene.add(L, L.target);
    extra.push(L);
  }

  // backdrop: a clip-space quad drawn first behind everything (no depth), radial gradient in
  // aspect-corrected screen space. Colours are given as displayed sRGB and pre-inverted through
  // the tone curve and exposure, so the frame shows exactly them (before the vignette and grain).
  const bd = backdropColours || S.backdrop; // a building may bring its own (colony.js SPACE_BACKDROP for orbital ones)
  const backdrop = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), new THREE.ShaderMaterial({
    depthTest: false, depthWrite: false,
    uniforms: {
      uCentre: { value: neutralInverse(bd.centre).divideScalar(exposure) },
      uEdge: { value: neutralInverse(bd.edge).divideScalar(exposure) },
      uAt: { value: new THREE.Vector2(...bd.at) },
      uAspect: { value: 1.6 },
    },
    vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 1.0, 1.0); }',
    fragmentShader: `uniform vec3 uCentre, uEdge; uniform vec2 uAt; uniform float uAspect; varying vec2 vUv;
      void main(){
        vec2 q = (vUv - uAt) * vec2(uAspect, 1.0);
        float r = length(q) / (0.62 * uAspect);           // ~1 in the far corners
        float t = smoothstep(0.0, 1.05, r); t = t * t * (1.6 - 0.6 * t);
        vec3 c = mix(uCentre, uEdge, clamp(t, 0.0, 1.0));
        c *= mix(1.04, 0.92, vUv.y < uAt.y ? (uAt.y - vUv.y) / uAt.y : 0.0) ; // a touch darker toward the floor
        gl_FragColor = vec4(c, 1.0);
      }`,
  }));
  backdrop.frustumCulled = false;
  backdrop.renderOrder = -100;
  backdrop.name = 'studio-backdrop';
  backdrop.onBeforeRender = (r) => { const s = r.getDrawingBufferSize(_v2); backdrop.material.uniforms.uAspect.value = s.x / Math.max(1, s.y); };
  scene.add(backdrop);
  scene.background = null;

  function fitShadow(box) {
    const center = box.getCenter(new THREE.Vector3());
    const radius = box.getSize(new THREE.Vector3()).length() / 2;
    key.target.position.copy(center);
    key.position.copy(center).addScaledVector(dirs.key, radius * 2 + 50);
    const cam = key.shadow.camera;
    cam.left = -radius; cam.right = radius; cam.top = radius; cam.bottom = -radius;
    cam.near = 1; cam.far = radius * 4 + 100;
    cam.updateProjectionMatrix();
    key.shadow.normalBias = Math.max(0.02, radius / 2000);
    for (const L of extra) { L.target.position.copy(center); L.position.copy(center).addScaledVector(L.userData.dir, radius * 2 + 50); }
  }

  return { sun: key, fitShadow, envTexture: envRT.texture, backdrop, dirs, lights: extra };
}
const _v2 = new THREE.Vector2();
