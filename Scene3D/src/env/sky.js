// Background sky: star field + faint nebula dome. Follows the camera so it
// always sits at "infinity".
import * as THREE from 'three';
import { mulberry32 } from '../lib/rng.js';

export function createSky(scene, { stars = 9000, radius = 9000 } = {}) {
  const group = new THREE.Group();
  group.name = 'sky';

  const dome = new THREE.Mesh(
    new THREE.SphereGeometry(radius, 64, 32),
    new THREE.ShaderMaterial({
      side: THREE.BackSide, depthWrite: false,
      vertexShader: `varying vec3 vDir; void main(){ vDir = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
      fragmentShader: `
        varying vec3 vDir;
        float h(vec3 p){ return fract(sin(dot(p, vec3(12.9898,78.233,45.164))) * 43758.5453); }
        float n(vec3 p){ vec3 i=floor(p), f=fract(p); f=f*f*(3.0-2.0*f);
          return mix(mix(mix(h(i),h(i+vec3(1,0,0)),f.x),mix(h(i+vec3(0,1,0)),h(i+vec3(1,1,0)),f.x),f.y),
                     mix(mix(h(i+vec3(0,0,1)),h(i+vec3(1,0,1)),f.x),mix(h(i+vec3(0,1,1)),h(i+vec3(1,1,1)),f.x),f.y),f.z); }
        float fbm(vec3 p){ float s=0.0,a=0.5; for(int i=0;i<6;i++){ s+=a*n(p); p*=2.03; a*=0.5; } return s; }
        void main(){
          vec3 d = normalize(vDir);
          float band = exp(-pow(dot(d, normalize(vec3(0.25, 0.9, -0.35))) * 2.6, 2.0));
          float f = fbm(d * 3.0 + 4.0);
          float g = fbm(d * 7.0 - 2.0);
          vec3 c1 = vec3(0.30, 0.07, 0.34), c2 = vec3(0.05, 0.16, 0.36), c3 = vec3(0.55, 0.22, 0.10);
          vec3 neb = mix(c2, c1, smoothstep(0.35, 0.7, f)) * smoothstep(0.38, 0.75, f) * band;
          neb += c3 * smoothstep(0.62, 0.85, g) * band * 0.5;
          float dust = smoothstep(0.55, 0.8, fbm(d * 12.0)) * band * 0.25;
          gl_FragColor = vec4(neb * 0.55 - dust * 0.03 + vec3(0.004, 0.005, 0.01), 1.0);
        }`,
    }),
  );
  dome.renderOrder = -10;
  group.add(dome);

  const rnd = mulberry32(99);
  const pos = new Float32Array(stars * 3), col = new Float32Array(stars * 3), size = new Float32Array(stars);
  const c = new THREE.Color();
  for (let i = 0; i < stars; i++) {
    // concentrate some stars along the galactic band
    let v = new THREE.Vector3(rnd() * 2 - 1, rnd() * 2 - 1, rnd() * 2 - 1).normalize();
    if (rnd() < 0.45) { const bandN = new THREE.Vector3(0.25, 0.9, -0.35).normalize(); v.addScaledVector(bandN, -v.dot(bandN) * (0.7 + 0.3 * rnd())).normalize(); }
    pos.set(v.multiplyScalar(radius * 0.95).toArray(), i * 3);
    const t = rnd();
    c.setHSL(t < 0.2 ? 0.07 : t < 0.35 ? 0.6 : 0.12, t < 0.35 ? 0.6 : 0.15, 0.85);
    col.set([c.r, c.g, c.b], i * 3);
    size[i] = Math.pow(rnd(), 6) * 3.2 + 0.7;
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  g.setAttribute('color', new THREE.BufferAttribute(col, 3));
  g.setAttribute('size', new THREE.BufferAttribute(size, 1));
  const pts = new THREE.Points(g, new THREE.ShaderMaterial({
    uniforms: { uPx: { value: 1 } },
    vertexShader: `attribute vec3 color; attribute float size; uniform float uPx; varying vec3 vC; varying float vS;
      void main(){ vC = color; vS = size; vec4 mv = modelViewMatrix * vec4(position,1.0); gl_PointSize = size * uPx; gl_Position = projectionMatrix * mv; }`,
    fragmentShader: `varying vec3 vC; varying float vS; void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; float a = smoothstep(1.0, 0.0, r); a *= a; gl_FragColor = vec4(vC * a * (0.6 + vS * 0.5), a); }`,
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
  }));
  pts.renderOrder = -9;
  group.add(pts);
  scene.add(group);

  return {
    group,
    update(t, camera, renderer) {
      group.position.copy(camera.position);
      if (renderer) pts.material.uniforms.uPx.value = renderer.getPixelRatio();
    },
  };
}
