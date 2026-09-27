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
