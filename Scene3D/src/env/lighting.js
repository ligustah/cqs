// Lighting rig shared by every view: a hard key light from the local star,
// blue planet-shine from below, a cool rim, and an image-based environment
// (PMREM) so metals, paint clearcoat and glass reflect the same world.
import * as THREE from 'three';

export const SUN_DIR = new THREE.Vector3(0.62, 0.42, 0.66).normalize();
export const PLANET_DIR = new THREE.Vector3(-0.15, -1, -0.25).normalize();

function envScene() {
  const scene = new THREE.Scene();
  // gradient dome: black zenith, planet-blue nadir glow, warm haze toward the star
  const mat = new THREE.ShaderMaterial({
    side: THREE.BackSide,
    uniforms: { uSun: { value: SUN_DIR }, uPlanet: { value: PLANET_DIR } },
    vertexShader: `varying vec3 vDir; void main(){ vDir = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
    fragmentShader: `
      uniform vec3 uSun; uniform vec3 uPlanet; varying vec3 vDir;
      void main(){
        vec3 d = normalize(vDir);
        float p = max(dot(d, uPlanet), 0.0);
        vec3 planet = vec3(0.10, 0.28, 0.62) * smoothstep(0.1, 0.9, p) * 1.6
                    + vec3(0.35, 0.6, 1.0) * pow(1.0 - abs(dot(d, uPlanet) - 0.25), 12.0) * 0.5; // limb glow
        float s = max(dot(d, uSun), 0.0);
        vec3 sun = vec3(1.0, 0.86, 0.66) * (pow(s, 6.0) * 0.6 + pow(s, 60.0) * 3.0);
        vec3 space = vec3(0.012, 0.014, 0.03);
        vec3 neb = vec3(0.35, 0.08, 0.35) * pow(max(dot(d, normalize(vec3(-0.7, 0.35, -0.6))), 0.0), 4.0) * 0.35;
        gl_FragColor = vec4(space + planet + sun + neb, 1.0);
      }`,
  });
  scene.add(new THREE.Mesh(new THREE.SphereGeometry(100, 64, 32), mat));
  // hot sun disc for sharp specular highlights
  const disc = new THREE.Mesh(new THREE.SphereGeometry(4, 16, 8), new THREE.MeshBasicMaterial({ color: new THREE.Color(1, 0.95, 0.85).multiplyScalar(40) }));
  disc.position.copy(SUN_DIR).multiplyScalar(90);
  scene.add(disc);
  return scene;
}

export function createLighting(renderer, scene, { shadowSize = 4096 } = {}) {
  const pmrem = new THREE.PMREMGenerator(renderer);
  const envRT = pmrem.fromScene(envScene(), 0.02);
  scene.environment = envRT.texture;
  scene.environmentIntensity = 0.9;

  const sun = new THREE.DirectionalLight(0xfff1de, 4.2);
  sun.position.copy(SUN_DIR).multiplyScalar(500);
  sun.castShadow = true;
  sun.shadow.mapSize.set(shadowSize, shadowSize);
  sun.shadow.bias = -0.0002;
  sun.shadow.normalBias = 0.04;
  scene.add(sun, sun.target);

  const planetShine = new THREE.HemisphereLight(0x0a0d18, 0x3d6fd6, 0.9);
  scene.add(planetShine);

  const rim = new THREE.DirectionalLight(0x8aa2ff, 0.6);
  rim.position.set(-0.7, 0.2, -0.8).multiplyScalar(500);
  scene.add(rim);

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

  return { sun, planetShine, rim, fitShadow, envTexture: envRT.texture };
}
