// Shared GLSL chunks for the orbital environment (noise, ray/sphere, atmosphere).
// Everything here is procedural: no textures are sampled anywhere in src/env.
import * as THREE from 'three';

// 3D simplex noise, after Ashima Arts / Stefan Gustavson (MIT licence). Range ~[-1, 1].
export const NOISE = /* glsl */`
vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec4 mod289(vec4 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec4 permute(vec4 x) { return mod289(((x * 34.0) + 10.0) * x); }
vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }
float snoise(vec3 v) {
  const vec2 C = vec2(1.0 / 6.0, 1.0 / 3.0);
  const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);
  vec3 i = floor(v + dot(v, C.yyy));
  vec3 x0 = v - i + dot(i, C.xxx);
  vec3 g = step(x0.yzx, x0.xyz);
  vec3 l = 1.0 - g;
  vec3 i1 = min(g.xyz, l.zxy);
  vec3 i2 = max(g.xyz, l.zxy);
  vec3 x1 = x0 - i1 + C.xxx;
  vec3 x2 = x0 - i2 + C.yyy;
  vec3 x3 = x0 - D.yyy;
  i = mod289(i);
  vec4 p = permute(permute(permute(i.z + vec4(0.0, i1.z, i2.z, 1.0)) + i.y + vec4(0.0, i1.y, i2.y, 1.0)) + i.x + vec4(0.0, i1.x, i2.x, 1.0));
  float n_ = 0.142857142857;
  vec3 ns = n_ * D.wyz - D.xzx;
  vec4 j = p - 49.0 * floor(p * ns.z * ns.z);
  vec4 x_ = floor(j * ns.z);
  vec4 y_ = floor(j - 7.0 * x_);
  vec4 x = x_ * ns.x + ns.yyyy;
  vec4 y = y_ * ns.x + ns.yyyy;
  vec4 h = 1.0 - abs(x) - abs(y);
  vec4 b0 = vec4(x.xy, y.xy);
  vec4 b1 = vec4(x.zw, y.zw);
  vec4 s0 = floor(b0) * 2.0 + 1.0;
  vec4 s1 = floor(b1) * 2.0 + 1.0;
  vec4 sh = -step(h, vec4(0.0));
  vec4 a0 = b0.xzyw + s0.xzyw * sh.xxyy;
  vec4 a1 = b1.xzyw + s1.xzyw * sh.zzww;
  vec3 p0 = vec3(a0.xy, h.x);
  vec3 p1 = vec3(a0.zw, h.y);
  vec3 p2 = vec3(a1.xy, h.z);
  vec3 p3 = vec3(a1.zw, h.w);
  vec4 norm = taylorInvSqrt(vec4(dot(p0, p0), dot(p1, p1), dot(p2, p2), dot(p3, p3)));
  p0 *= norm.x; p1 *= norm.y; p2 *= norm.z; p3 *= norm.w;
  vec4 m = max(0.5 - vec4(dot(x0, x0), dot(x1, x1), dot(x2, x2), dot(x3, x3)), 0.0);
  m = m * m;
  return 105.0 * dot(m * m, vec4(dot(p0, x0), dot(p1, x1), dot(p2, x2), dot(p3, x3)));
}
// cheap lattice hash (Dave Hoskins), [0,1)
float hash13(vec3 p3) {
  p3 = fract(p3 * 0.1031);
  p3 += dot(p3, p3.zyx + 31.32);
  return fract((p3.x + p3.y) * p3.z);
}
vec3 hash33(vec3 p3) {
  p3 = fract(p3 * vec3(0.1031, 0.1030, 0.0973));
  p3 += dot(p3, p3.yxz + 33.33);
  return fract((p3.xxy + p3.yxx) * p3.zyx);
}
`;

// Ray / sphere helpers (sphere at the origin).
export const RAY = /* glsl */`
// returns (tNear, tFar); tFar < 0 or tNear > tFar means miss
vec2 raySphere(vec3 ro, vec3 rd, float r) {
  float b = dot(ro, rd);
  float c = dot(ro, ro) - r * r;
  float h = b * b - c;
  if (h < 0.0) return vec2(1e9, -1e9);
  h = sqrt(h);
  return vec2(-b - h, -b + h);
}
`;

// Pushes a vertex that would be clipped by the far plane back inside it. The
// environment never writes or tests depth, so this only keeps huge shells
// (the sky dome and star field) from being cut when the camera zooms far out.
export const FAR_CLAMP = /* glsl */`
  if (gl_Position.w > 0.0) gl_Position.z = min(gl_Position.z, gl_Position.w * 0.999999);
`;

// Per-pixel view ray from gl_FragCoord and the camera. The planet and its atmosphere are
// drawn as full-screen quads that ray-cast their spheres (SCREEN_VERT): a true-scale globe
// as a tessellated sphere has triangles crossing the near plane behind the camera, and
// their per-triangle clipping is not watertight (a dotted crack of missing samples along
// shared edges on software rasterisers).
export const VIEW_RAY = /* glsl */`
uniform vec4 uProj; // projection P00, P11, P20, P21
uniform vec2 uRes;  // size of the target being drawn (px)
vec3 viewRay() {
  vec2 ndc = gl_FragCoord.xy / uRes * 2.0 - 1.0;
  vec3 v = vec3((ndc.x + uProj.z) / uProj.x, (ndc.y + uProj.w) / uProj.y, -1.0);
  return normalize(v * mat3(viewMatrix)); // inverse view rotation (transpose) applied to v
}
// angle subtended by one pixel (rad)
float pixelAngle() { return 2.0 / (uProj.y * uRes.y); }
`;
export function viewRayUniforms() {
  return { uProj: { value: new THREE.Vector4(1, 1, 0, 0) }, uRes: { value: new THREE.Vector2(1, 1) } };
}
const _px = new THREE.Vector2();
/** onBeforeRender hook: feeds VIEW_RAY the camera projection and the current target size. */
export function bindViewRay(mesh, uniforms) {
  mesh.onBeforeRender = (renderer, _scene, camera) => {
    const rt = renderer.getRenderTarget();
    if (rt) _px.set(rt.width, rt.height); else renderer.getDrawingBufferSize(_px);
    const e = camera.projectionMatrix.elements; // column-major
    uniforms.uProj.value.set(e[0], e[5], e[8], e[9]);
    uniforms.uRes.value.copy(_px);
  };
}

// Full-screen quad (PlaneGeometry(2, 2)) just in front of the far plane; the environment
// never tests or writes depth.
export const SCREEN_VERT = /* glsl */`
void main() { gl_Position = vec4(position.xy, 0.999, 1.0); }
`;
