// The local star: a screen-aligned billboard at SUN_DIR with a limb-darkened
// disc, a layered glare halo, four thin diffraction spikes and a faint cyan
// anamorphic streak. Its lens elements fade when the planet occludes the star.
import * as THREE from 'three';

export function createSun({ dir, distance, discRadius = 0.0052, extent = 0.62 }) {
  const mat = new THREE.ShaderMaterial({
    uniforms: {
      uDir: { value: dir.clone().normalize() },
      uDist: { value: distance },
      uExtent: { value: extent },
      uDisc: { value: discRadius },
      uVis: { value: 1 },
      uGlare: { value: 1 },
    },
    vertexShader: /* glsl */`
      uniform vec3 uDir; uniform float uDist; uniform float uExtent;
      varying vec3 vPos; varying vec3 vCenter; varying vec2 vOff;
      void main() {
        vec4 c = modelViewMatrix * vec4(uDir * uDist, 1.0);
        vec3 p = c.xyz + vec3(position.xy * uExtent * uDist, 0.0);
        vPos = p; vCenter = c.xyz; vOff = position.xy * uExtent;
        gl_Position = projectionMatrix * vec4(p, 1.0);
      }`,
    fragmentShader: /* glsl */`
      uniform float uDisc; uniform float uVis; uniform float uGlare;
      varying vec3 vPos; varying vec3 vCenter; varying vec2 vOff;
      void main() {
        vec3 dF = normalize(vPos), dS = normalize(vCenter);
        float th = length(dF - dS);                 // angle from the star centre (rad)
        // photosphere with limb darkening
        float x = clamp(th / uDisc, 0.0, 1.0);
        float mu = sqrt(1.0 - x * x);
        float disc = 1.0 - smoothstep(0.93, 1.05, th / uDisc);
        vec3 col = disc * (0.45 + 0.55 * mu) * vec3(1.0, 0.95, 0.87) * 120.0;
        // glare: inner corona, soft halo, wide veil
        float g = 2.2 * exp(-th / 0.0065) + 0.30 * exp(-th / 0.028) + 0.045 * exp(-th / 0.13);
        col += vec3(1.0, 0.84, 0.64) * g * uGlare * uVis;
        // diffraction spikes (screen aligned, tilted 28°)
        const float ca = 0.8829476, sa = 0.4694716;
        vec2 o = vec2(ca * vOff.x - sa * vOff.y, sa * vOff.x + ca * vOff.y);
        vec2 ao = abs(o);
        float spikes = exp(-ao.y / 0.0008) * exp(-ao.x / 0.075) + exp(-ao.x / 0.0008) * exp(-ao.y / 0.075);
        spikes += 0.35 * (exp(-ao.y / 0.0022) * exp(-ao.x / 0.02) + exp(-ao.x / 0.0022) * exp(-ao.y / 0.02));
        col += vec3(1.0, 0.93, 0.84) * spikes * 1.1 * uVis;
        // anamorphic streak: thin, long, horizontal, cyan like the drive glow
        float st = exp(-abs(vOff.y) / 0.0011) * (0.6 * exp(-abs(vOff.x) / 0.08) + 0.4 * exp(-abs(vOff.x) / 0.4));
        col += vec3(0.42, 0.74, 1.0) * st * 0.45 * uVis;
        gl_FragColor = vec4(col, 1.0);
      }`,
    transparent: false,
    depthTest: false,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  });
  const mesh = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), mat);
  mesh.name = 'sun';
  mesh.frustumCulled = false;
  return mesh;
}
