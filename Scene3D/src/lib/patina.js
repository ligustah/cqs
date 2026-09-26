// PATINA material library (fal-ai/patina/material): seamless tiling PBR sets
// (basecolor, normal, roughness, metalness, height) generated with fal and stored
// in assets/materials/<name>/<map>.webp with a manifest.json.
//
// Two uses, mirroring the pipeline in the brief:
//  1. patinaMaterial(): full tiling PBR materials for parts we build ourselves
//     (UVs are box-projected in metres by kit.js).
//  2. addDetailLayer(): tri-planar detail on generated meshes. Their own baked
//     textures keep the livery; PATINA adds crisp, metre-scaled plating relief,
//     roughness breakup and seam cavities for close-up views.
import * as THREE from 'three';

export const MAPS = ['basecolor', 'normal', 'roughness', 'metalness', 'height'];
const loader = new THREE.TextureLoader();

function configure(tex, map) {
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.colorSpace = map === 'basecolor' ? THREE.SRGBColorSpace : THREE.NoColorSpace;
  tex.anisotropy = 8;
  return tex;
}

/** Load every set listed in <base>/manifest.json. Missing library -> {}. */
export async function loadPatinaLibrary(base = './assets/materials/') {
  let manifest;
  try {
    const r = await fetch(base + 'manifest.json');
    if (!r.ok) return {};
    manifest = await r.json();
  } catch { return {}; }
  const lib = {};
  await Promise.all(Object.entries(manifest.sets || {}).map(async ([name, meta]) => {
    const maps = {};
    await Promise.all((meta.maps || MAPS).map(async (m) => {
      try { maps[m] = configure(await loader.loadAsync(`${base}${name}/${m}.webp`), m); } catch (e) { console.warn(`[patina] ${name}/${m} missing`, e); }
    }));
    lib[name] = { name, meta, maps };
  }));
  return lib;
}

/** Full PBR material from a PATINA set. tile = metres per texture repeat (UVs are in metres/uvScale). */
export function patinaMaterial(set, { color = '#ffffff', metalness = null, roughness = 1, clearcoat = 0, normalScale = 1, envMapIntensity = 1 } = {}) {
  const m = set.maps;
  return new THREE.MeshPhysicalMaterial({
    color: new THREE.Color(color),
    map: m.basecolor || null,
    normalMap: m.normal || null,
    normalScale: new THREE.Vector2(normalScale, normalScale),
    roughnessMap: m.roughness || null,
    roughness,
    metalnessMap: metalness === null ? (m.metalness || null) : null,
    metalness: metalness === null ? (m.metalness ? 1 : 0) : metalness,
    clearcoat, clearcoatRoughness: 0.3,
    envMapIntensity,
  });
}

/**
 * Tri-planar PATINA detail on top of an existing (e.g. generated, UV-atlased)
 * MeshStandard/Physical material. Works in the mesh's object space.
 *  unitsPerMetre: object-space units per metre for this mesh
 *  tile: metres per detail repeat
 */
export function addDetailLayer(material, set, { unitsPerMetre = 1, tile = 4, normalStrength = 0.8, roughAmount = 0.5, cavity = 0.35 } = {}) {
  const maps = set?.maps || {};
  if (!maps.normal && !maps.roughness && !maps.height) return material;
  const uniforms = {
    uDetScale: { value: 1 / (tile * unitsPerMetre) },
    uDetNormal: { value: maps.normal || null },
    uDetRough: { value: maps.roughness || null },
    uDetHeight: { value: maps.height || null },
    uDetStrength: { value: normalStrength },
    uDetRoughAmt: { value: maps.roughness ? roughAmount : 0 },
    uDetCavity: { value: maps.height ? cavity : 0 },
  };
  material.userData.detail = uniforms;
  const prev = material.onBeforeCompile;
  material.onBeforeCompile = (shader, renderer) => {
    prev?.call(material, shader, renderer);
    Object.assign(shader.uniforms, uniforms);
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vDetPos;\nvarying vec3 vDetNrm;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvDetPos = position;\nvDetNrm = normal;');
    const detailFns = /* glsl */`
      varying vec3 vDetPos; varying vec3 vDetNrm;
      uniform float uDetScale, uDetStrength, uDetRoughAmt, uDetCavity;
      uniform sampler2D uDetNormal, uDetRough, uDetHeight;
      vec3 detW() { vec3 w = pow(abs(normalize(vDetNrm)), vec3(6.0)); return w / (w.x + w.y + w.z); }
      float detTri(sampler2D t) {
        vec3 p = vDetPos * uDetScale; vec3 w = detW();
        return texture2D(t, p.zy).g * w.x + texture2D(t, p.xz).g * w.y + texture2D(t, p.xy).g * w.z;
      }
      mat3 detTBN(vec3 eye, vec3 n, vec2 uv) {
        vec3 q0 = dFdx(eye), q1 = dFdy(eye); vec2 s0 = dFdx(uv), s1 = dFdy(uv);
        vec3 N = n; vec3 q1p = cross(q1, N), q0p = cross(N, q0);
        vec3 T = q1p * s0.x + q0p * s1.x; vec3 B = q1p * s0.y + q0p * s1.y;
        float det = max(dot(T, T), dot(B, B)); float sc = (det == 0.0) ? 0.0 : inversesqrt(det);
        return mat3(T * sc, B * sc, N);
      }
      vec3 detPerturb(vec3 n, vec3 eye) {
        vec3 p = vDetPos * uDetScale; vec3 w = detW();
        vec3 nx = texture2D(uDetNormal, p.zy).xyz * 2.0 - 1.0;
        vec3 ny = texture2D(uDetNormal, p.xz).xyz * 2.0 - 1.0;
        vec3 nz = texture2D(uDetNormal, p.xy).xyz * 2.0 - 1.0;
        nx.xy *= uDetStrength; ny.xy *= uDetStrength; nz.xy *= uDetStrength;
        vec3 px = detTBN(eye, n, p.zy) * nx, py = detTBN(eye, n, p.xz) * ny, pz = detTBN(eye, n, p.xy) * nz;
        return normalize(px * w.x + py * w.y + pz * w.z);
      }`;
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', '#include <common>\n' + detailFns)
      .replace('#include <roughnessmap_fragment>', '#include <roughnessmap_fragment>\nif (uDetRoughAmt > 0.0) roughnessFactor = clamp(roughnessFactor * mix(1.0, 0.55 + detTri(uDetRough), uDetRoughAmt), 0.04, 1.0);')
      .replace('#include <normal_fragment_maps>', '#include <normal_fragment_maps>\nif (uDetStrength > 0.0) normal = detPerturb(normal, -vViewPosition);')
      .replace('#include <aomap_fragment>', '#include <aomap_fragment>\nif (uDetCavity > 0.0) { float h = detTri(uDetHeight); float cav = mix(1.0, smoothstep(0.05, 0.45, h), uDetCavity); reflectedLight.indirectDiffuse *= cav; reflectedLight.directDiffuse *= mix(1.0, cav, 0.6); }');
  };
  material.customProgramCacheKey = () => 'patina-detail';
  material.needsUpdate = true;
  return material;
}

/** Stand-in library from the procedural canvas textures (used until PATINA sets exist). */
export function proceduralStandIn(panelSet) {
  return { name: 'procedural', meta: { standIn: true }, maps: { basecolor: panelSet.map, normal: panelSet.normalMap, roughness: panelSet.roughnessMap } };
}
