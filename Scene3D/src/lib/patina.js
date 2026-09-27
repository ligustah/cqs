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
import { LITE } from './device.js';

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
      // the phone tier of the artifact loads 512 px copies (<map>.lite.webp, written by build-artifact)
      try { maps[m] = configure(await loader.loadAsync(`${base}${name}/${m}${LITE && globalThis.__glbB64 ? '.lite' : ''}.webp`), m); } catch (e) { console.warn(`[patina] ${name}/${m} missing`, e); }
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
 *  interior: optional second set for an interior region (a hangar): { set, box: [[x,y,z],[x,y,z]]
 *    (ship frame), toShip (Matrix4: object -> ship frame), feather, tile, normalStrength,
 *    roughAmount, cavity, albedo, seam, grime }. Inside the box its normal, roughness and cavity replace the
 *    hull set's, and its basecolor luminance modulates the albedo by `albedo` (the set's
 *    painted markings are desaturated: a plated deck, not a repeated decal).
 */
export function addDetailLayer(material, set, { unitsPerMetre = 1, tile = 4, normalStrength = 0.8, roughAmount = 0.5, cavity = 0.35, interior = null } = {}) {
  const maps = set?.maps || {};
  if (!maps.normal && !maps.roughness && !maps.height) return material;
  const im = interior?.set?.maps || null;
  const inner = im && im.normal && im.height ? interior : null;
  const uniforms = {
    uDetScale: { value: 1 / (tile * unitsPerMetre) },
    uDetNormal: { value: maps.normal || null },
    uDetRough: { value: maps.roughness || null },
    uDetHeight: { value: maps.height || null },
    uDetStrength: { value: normalStrength },
    uDetRoughAmt: { value: maps.roughness ? roughAmount : 0 },
    uDetCavity: { value: maps.height ? cavity : 0 },
  };
  if (inner) {
    Object.assign(uniforms, {
      uInScale: { value: 1 / ((inner.tile ?? tile) * unitsPerMetre) },
      uInNormal: { value: im.normal }, uInRough: { value: im.roughness || im.height }, uInHeight: { value: im.height },
      uInBase: { value: im.basecolor || im.height },
      uInStrength: { value: inner.normalStrength ?? 1.6 }, uInRoughAmt: { value: im.roughness ? inner.roughAmount ?? 0.5 : 0 },
      uInCavity: { value: inner.cavity ?? 0.7 }, uInAlbedo: { value: im.basecolor ? inner.albedo ?? 0.5 : 0 },
      uInSeam: { value: inner.seam ?? 1 }, uInGrime: { value: inner.grime ?? 1 },
      uInM: { value: inner.toShip.clone() },
      uInMin: { value: new THREE.Vector3(...inner.box[0]) }, uInMax: { value: new THREE.Vector3(...inner.box[1]) },
      uInFeather: { value: inner.feather ?? 1.5 },
    });
  }
  material.userData.detail = uniforms;
  const prev = material.onBeforeCompile;
  material.onBeforeCompile = (shader, renderer) => {
    prev?.call(material, shader, renderer);
    Object.assign(shader.uniforms, uniforms);
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', `#include <common>\nvarying vec3 vDetPos;\nvarying vec3 vDetNrm;${inner ? '\nuniform mat4 uInM; varying vec3 vInPos;' : ''}`)
      .replace('#include <begin_vertex>', `#include <begin_vertex>\nvDetPos = position;\nvDetNrm = normal;${inner ? '\nvInPos = (uInM * vec4(transformed, 1.0)).xyz;' : ''}`);
    const detailFns = /* glsl */`
      varying vec3 vDetPos; varying vec3 vDetNrm;
      uniform float uDetScale, uDetStrength, uDetRoughAmt, uDetCavity;
      uniform sampler2D uDetNormal, uDetRough, uDetHeight;
      ${inner ? `
      varying vec3 vInPos;
      uniform float uInScale, uInStrength, uInRoughAmt, uInCavity, uInAlbedo, uInFeather, uInSeam, uInGrime;
      uniform vec3 uInMin, uInMax;
      uniform sampler2D uInNormal, uInRough, uInHeight, uInBase;
      float inMask() { vec3 d = min(vInPos - uInMin, uInMax - vInPos); vec3 m = smoothstep(vec3(0.0), vec3(uInFeather), d); return m.x * m.y * m.z; }
      ` : 'float inMask() { return 0.0; }'}
      vec3 detW() { vec3 w = pow(abs(normalize(vDetNrm)), vec3(6.0)); return w / (w.x + w.y + w.z); }
      float detTriS(sampler2D t, float sc) {
        vec3 p = vDetPos * sc; vec3 w = detW();
        return texture2D(t, p.zy).g * w.x + texture2D(t, p.xz).g * w.y + texture2D(t, p.xy).g * w.z;
      }
      float detTri(sampler2D t) { return detTriS(t, uDetScale); }
      mat3 detTBN(vec3 eye, vec3 n, vec2 uv) {
        vec3 q0 = dFdx(eye), q1 = dFdy(eye); vec2 s0 = dFdx(uv), s1 = dFdy(uv);
        vec3 N = n; vec3 q1p = cross(q1, N), q0p = cross(N, q0);
        vec3 T = q1p * s0.x + q0p * s1.x; vec3 B = q1p * s0.y + q0p * s1.y;
        float det = max(dot(T, T), dot(B, B)); float sc = (det == 0.0) ? 0.0 : inversesqrt(det);
        return mat3(T * sc, B * sc, N);
      }
      vec3 detPerturbS(vec3 n, vec3 eye, sampler2D tn, float scl, float strength) {
        vec3 p = vDetPos * scl; vec3 w = detW();
        vec3 nx = texture2D(tn, p.zy).xyz * 2.0 - 1.0;
        vec3 ny = texture2D(tn, p.xz).xyz * 2.0 - 1.0;
        vec3 nz = texture2D(tn, p.xy).xyz * 2.0 - 1.0;
        nx.xy *= strength; ny.xy *= strength; nz.xy *= strength;
        vec3 px = detTBN(eye, n, p.zy) * nx, py = detTBN(eye, n, p.xz) * ny, pz = detTBN(eye, n, p.xy) * nz;
        return normalize(px * w.x + py * w.y + pz * w.z);
      }
      vec3 detPerturb(vec3 n, vec3 eye) {
        vec3 h = detPerturbS(n, eye, uDetNormal, uDetScale, uDetStrength);
        ${inner ? 'float m = inMask(); if (m > 0.0) h = normalize(mix(h, detPerturbS(n, eye, uInNormal, uInScale, uInStrength), m));' : ''}
        return h;
      }`;
    const rough = inner
      ? 'if (uDetRoughAmt > 0.0 || uInRoughAmt > 0.0) { float mR = inMask(); float rH = mix(1.0, 0.55 + detTri(uDetRough), uDetRoughAmt); float rI = mix(1.0, 0.55 + detTriS(uInRough, uInScale), uInRoughAmt); roughnessFactor = clamp(roughnessFactor * mix(rH, rI, mR), 0.04, 1.0); }'
      : 'if (uDetRoughAmt > 0.0) roughnessFactor = clamp(roughnessFactor * mix(1.0, 0.55 + detTri(uDetRough), uDetRoughAmt), 0.04, 1.0);';
    // cavity: the seams and recesses of the plating darken diffuse light (all of the ambient,
    // most of the direct). Inside the interior box the deck set's own cavity takes over.
    const cav = inner
      ? '{ float mC = inMask(); float cH = uDetCavity > 0.0 ? mix(1.0, smoothstep(0.05, 0.45, detTri(uDetHeight)), uDetCavity) : 1.0; float hI = detTriS(uInHeight, uInScale); float cI = mix(1.0, smoothstep(0.3, 0.62, hI), uInCavity); float cav = mix(cH, cI, mC); reflectedLight.indirectDiffuse *= cav; reflectedLight.directDiffuse *= mix(1.0, cav, 0.7); }'
      : 'if (uDetCavity > 0.0) { float h = detTri(uDetHeight); float cav = mix(1.0, smoothstep(0.05, 0.45, h), uDetCavity); reflectedLight.indirectDiffuse *= cav; reflectedLight.directDiffuse *= mix(1.0, cav, 0.6); }';
    let frag = shader.fragmentShader
      .replace('#include <common>', '#include <common>\n' + detailFns)
      .replace('#include <roughnessmap_fragment>', '#include <roughnessmap_fragment>\n' + rough)
      .replace('#include <normal_fragment_maps>', '#include <normal_fragment_maps>\nif (uDetStrength > 0.0) normal = detPerturb(normal, -vViewPosition);')
      .replace('#include <aomap_fragment>', '#include <aomap_fragment>\n' + cav);
    if (inner) {
      // plate-to-plate tone of the deck set (luminance only, normalised to its linear mean ~0.17):
      // worn plates and grime in the seams at the tile scale, and the same set read 7.3x larger
      // for deck-panel tone, scuffed lanes and painted lines at the ~10-40 m scale that still
      // shows from a kilometre away (the 1.5 m plates average out there). Light lines are
      // clamped: markings are scuffed grey paint, not a bright grid. interior.seam scales the
      // tile-scale contrast, interior.grime the amplitude of the large-scale tone (1 = the
      // original 0.35 + 0.65 L mapping).
      frag = frag.replace('#include <color_fragment>', `#include <color_fragment>
        if (uInAlbedo > 0.0) {
          float mA = inMask();
          vec3 w = detW(); vec3 p = vDetPos * uInScale; vec3 P = p * 0.137 + vec3(0.31, 0.17, 0.53);
          vec3 lw = vec3(0.2126, 0.7152, 0.0722);
          float l = dot(texture2D(uInBase, p.zy).rgb * w.x + texture2D(uInBase, p.xz).rgb * w.y + texture2D(uInBase, p.xy).rgb * w.z, lw);
          float L = dot(texture2D(uInBase, P.zy).rgb * w.x + texture2D(uInBase, P.xz).rgb * w.y + texture2D(uInBase, P.xy).rgb * w.z, lw);
          // a third, much larger read of the same set (~0.2 km) for bay-to-bay grime and wear
          vec3 Q = p * 0.041 + vec3(0.71, 0.43, 0.29);
          float G = dot(texture2D(uInBase, Q.zy).rgb * w.x + texture2D(uInBase, Q.xz).rgb * w.y + texture2D(uInBase, Q.xy).rgb * w.z, lw);
          float fine = mix(1.0, clamp(l / 0.17, 0.5, 1.2), uInSeam);           // tile-scale plate tone (seam contrast)
          float big = clamp(1.0 + uInGrime * 0.65 * (L / 0.17 - 1.0), 0.4, 1.5); // tyre scuffs, lanes, grime (~10-40 m)
          float huge = clamp(1.0 + uInGrime * 0.35 * (G / 0.17 - 1.0), 0.6, 1.3); // bay-scale wear
          float k = fine * big * huge;
          diffuseColor.rgb *= mix(1.0, k, uInAlbedo * mA);
        }`);
    }
    shader.fragmentShader = frag;
  };
  const prevKey = material.customProgramCacheKey.bind(material);
  material.customProgramCacheKey = () => `patina-detail${inner ? '-in' : ''}|${prevKey()}`;
  material.needsUpdate = true;
  return material;
}

/** Stand-in library from the procedural canvas textures (used until PATINA sets exist). */
export function proceduralStandIn(panelSet) {
  return { name: 'procedural', meta: { standIn: true }, maps: { basecolor: panelSet.map, normal: panelSet.normalMap, roughness: panelSet.roughnessMap } };
}
