// Turn a generated GLB (fal image-to-3D) into a scene ship with the same
// contract as ShipBuilder.finish(): a Group whose userData.ship carries the
// envelope, engines, lights and anchors used by scale.js, effects.js and fleet.js.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { toCreasedNormals, mergeVertices } from 'three/addons/utils/BufferGeometryUtils.js';
import { addDetailLayer } from './patina.js';
import { applyLivery } from './livery.js';

const loader = new GLTFLoader();
loader.setMeshoptDecoder(MeshoptDecoder);
const cache = new Map();
const DEG = Math.PI / 180;

let throatTex = null;
/** Radial glow for a nozzle throat: small white-hot centre, pale blue body, dark rim
 *  so the disc melts into the unlit bell wall instead of reading as a flat lamp. */
function throatTexture() {
  if (throatTex) return throatTex;
  const c = document.createElement('canvas'); c.width = c.height = 128;
  const g = c.getContext('2d');
  const grd = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  grd.addColorStop(0, '#ffffff'); grd.addColorStop(0.12, '#f3f5ff'); grd.addColorStop(0.3, '#b3c0e8');
  grd.addColorStop(0.55, '#56669c'); grd.addColorStop(0.8, '#1d2340'); grd.addColorStop(1, '#06070d');
  g.fillStyle = grd; g.fillRect(0, 0, 128, 128);
  throatTex = new THREE.CanvasTexture(c); throatTex.colorSpace = THREE.SRGBColorSpace;
  return throatTex;
}

export function loadGLB(url) {
  if (!cache.has(url)) cache.set(url, loader.loadAsync(url));
  return cache.get(url);
}

/** A SpotLight whose target is its own child, so clones (buildShip instances) aim correctly. */
class ShipSpotLight extends THREE.SpotLight {
  copy(source, recursive) {
    super.copy(source, recursive);
    const i = source.children.indexOf(source.target);
    if (i >= 0) this.target = this.children[i];
    return this;
  }
}

/**
 * Keep the generated texture's own (light) paint inside a ship-frame box, scaled by `gain`,
 * instead of the operational repaint: interiors such as a hangar deck are plated grey steel,
 * not hull paint. Chained after applyLivery: the texture colour is captured right after
 * map_fragment (before the livery block that follows it) and blended back in before
 * color_fragment. `toShip` maps the mesh's object space to the ship frame.
 */
function keepInterior(material, keep, toShip) {
  const [min, max] = keep.box;
  const uniforms = {
    uKeepM: { value: toShip.clone() },
    uKeepMin: { value: new THREE.Vector3(...min) }, uKeepMax: { value: new THREE.Vector3(...max) },
    uKeepFeather: { value: keep.feather ?? 1.5 }, uKeepGain: { value: keep.gain ?? 0.5 },
    uKeepAmount: { value: keep.amount ?? 1 }, uKeepSat: { value: keep.saturation ?? 1 },
  };
  const prev = material.onBeforeCompile;
  material.onBeforeCompile = (shader, renderer) => {
    prev?.call(material, shader, renderer);
    Object.assign(shader.uniforms, uniforms);
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nuniform mat4 uKeepM; varying vec3 vKeepPos;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvKeepPos = (uKeepM * vec4(transformed, 1.0)).xyz;');
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', '#include <common>\nuniform vec3 uKeepMin, uKeepMax; uniform float uKeepFeather, uKeepGain, uKeepAmount, uKeepSat; varying vec3 vKeepPos;')
      .replace('#include <map_fragment>', '#include <map_fragment>\nvec3 keepPaint = diffuseColor.rgb;')
      .replace('#include <color_fragment>', `{
          vec3 kd = min(vKeepPos - uKeepMin, uKeepMax - vKeepPos);
          vec3 km = smoothstep(vec3(0.0), vec3(uKeepFeather), kd);
          vec3 kp = mix(vec3(dot(keepPaint, vec3(0.2126, 0.7152, 0.0722))), keepPaint, uKeepSat) * uKeepGain;
          diffuseColor.rgb = mix(diffuseColor.rgb, kp, km.x * km.y * km.z * uKeepAmount);
        }
        #include <color_fragment>`);
  };
  const prevKey = material.customProgramCacheKey.bind(material);
  material.customProgramCacheKey = () => `keep-interior|${prevKey()}`;
  material.needsUpdate = true;
  return material;
}

/**
 * Lights the ship carries inside itself (hangar floodlights). Physical units: SpotLight /
 * PointLight intensity in candela, inverse-square falloff (decay 2) windowed to `distance`.
 * spec: { p, color, intensity, distance, kind: 'spot'|'point', angle (deg, half-angle),
 *         penumbra, target: [x,y,z] | dir: [x,y,z], castShadow, shadowMapSize, name }
 */
function interiorLight(spec) {
  const kind = spec.kind || 'spot';
  const color = new THREE.Color(spec.color || '#ffd1a3');
  let L;
  if (kind === 'point') {
    L = new THREE.PointLight(color, spec.intensity, spec.distance ?? 0, spec.decay ?? 2);
  } else {
    L = new ShipSpotLight(color, spec.intensity, spec.distance ?? 0, (spec.angle ?? 45) * DEG, spec.penumbra ?? 0.5, spec.decay ?? 2);
    const t = spec.target ? new THREE.Vector3(...spec.target).sub(new THREE.Vector3(...spec.p))
      : new THREE.Vector3(...(spec.dir || [0, -1, 0])).normalize().multiplyScalar(10);
    L.add(L.target);
    L.target.position.copy(t);
  }
  L.position.set(...spec.p);
  if (spec.castShadow) {
    L.castShadow = true;
    const n = spec.shadowMapSize ?? 1024;
    L.shadow.mapSize.set(n, n);
    L.shadow.bias = spec.shadowBias ?? -0.0005;
    L.shadow.normalBias = spec.shadowNormalBias ?? 0.05;
    L.shadow.camera.near = spec.shadowNear ?? 1;
    L.shadow.camera.far = spec.distance || 500;
  }
  L.name = spec.name || 'interior-light';
  return L;
}

/**
 * cfg (from a ship module's `asset` export):
 *   glb        path to the optimised GLB
 *   concept    image-to-3D input image (fal concept art); beauty: in-orbit concept shot
 *   rotate     [x, y, z] degrees applied first so that the bow faces +Z and dorsal +Y
 *   length     design length in metres (bounding-box Z); scale.js then applies
 *              the small volume correction for the class's hangar slots
 *   detail     { set: 'hull', tile: 4, normalStrength, roughAmount, cavity }
 *   livery     optional repaint of the generated texture: 'dark' | 'civil' | {base, gain, mark, ...} (see livery.js)
 *   materials  optional per-material overrides by GLB material name or '*'
 *   crease     optional angle in degrees: split vertex normals at sharper edges
 *              so faceted hard-surface hulls shade flat instead of rounded
 *   engines    [{ p: [x,y,z], radius, dir? }]    (metres, ship frame, before correction)
 *   lights     [{ p, color, size, blink }]
 *   anchors    { name: { p, ...extra } }
 *   interiorLights  optional lights carried inside the hull, e.g. hangar floodlights
 *              [{ p, color, intensity (cd), distance, kind: 'spot'|'point', angle, penumbra, target | dir, castShadow }]
 *   liveryKeep optional { box: [[x,y,z], [x,y,z]] (ship frame), gain, saturation, feather }: inside
 *              the box the texture keeps its own paint (scaled by gain) instead of the livery repaint
 */
export function buildGLBShip(gltf, cfg, { palette, library = {} } = {}) {
  const model = gltf.scene.clone(true);
  model.rotation.set(...(cfg.rotate || [0, 0, 0]).map((d) => d * DEG), 'XYZ');
  model.updateMatrixWorld(true);
  const raw = new THREE.Box3().setFromObject(model);
  const rawSize = raw.getSize(new THREE.Vector3());
  const s = cfg.length / rawSize.z;
  model.scale.setScalar(s);
  model.updateMatrixWorld(true);
  const box = new THREE.Box3().setFromObject(model);
  const c = box.getCenter(new THREE.Vector3());
  model.position.sub(c);
  model.updateMatrixWorld(true);
  const env = new THREE.Box3().setFromObject(model);

  // material upgrade: shared per prototype (buildShip caches prototypes)
  const upgraded = new Map();
  const creased = new Map();
  const detailSet = cfg.detail ? library[cfg.detail.set] : null;
  let triangles = 0, meshes = 0;
  model.traverse((o) => {
    if (!o.isMesh) return;
    meshes++;
    let g = o.geometry;
    triangles += (g.index ? g.index.count : g.attributes.position.count) / 3;
    if (cfg.crease) {
      // toCreasedNormals un-indexes the mesh (3 vertices per triangle); weld it again so only the
      // vertices on creases stay split: about a third of the vertex work in every pass
      if (!creased.has(g)) creased.set(g, mergeVertices(toCreasedNormals(g, cfg.crease * DEG)));
      g = o.geometry = creased.get(g);
    }
    o.castShadow = true;
    o.receiveShadow = true;
    o.userData.hull = true; // raycast target for the hangar containment test
    const mats = Array.isArray(o.material) ? o.material : [o.material];
    // the interior keep-box is evaluated in the ship frame, so a material is shared only
    // between meshes with the same object-to-ship transform
    const keyOf = (m) => (cfg.liveryKeep ? `${m.uuid}|${o.matrixWorld.elements.map((e) => e.toFixed(6)).join(',')}` : m);
    const next = mats.map((m) => {
      if (upgraded.has(keyOf(m))) return upgraded.get(keyOf(m));
      const mm = m.clone();
      const over = { ...(cfg.materials?.['*'] || {}), ...(cfg.materials?.[m.name] || {}) };
      mm.envMapIntensity = over.envMapIntensity ?? 1.0;
      if (over.roughness !== undefined) mm.roughness = over.roughness;
      if (over.metalness !== undefined) mm.metalness = over.metalness;
      if (over.color) mm.color = new THREE.Color(over.color);
      if (over.emissiveBoost && mm.emissiveMap) mm.emissiveIntensity = over.emissiveBoost;
      if (cfg.livery) applyLivery(mm, cfg.livery);
      if (cfg.livery && cfg.liveryKeep) keepInterior(mm, cfg.liveryKeep, o.matrixWorld);
      if (detailSet) {
        // object-space units per metre: undo the model scale and any node scale
        const nodeScale = new THREE.Vector3(); o.getWorldScale(nodeScale);
        addDetailLayer(mm, detailSet, { unitsPerMetre: 1 / nodeScale.x, ...cfg.detail });
      }
      upgraded.set(keyOf(m), mm);
      return mm;
    });
    o.material = Array.isArray(o.material) ? next : next[0];
  });

  const group = new THREE.Group();
  group.name = cfg.name || 'glb-ship';
  group.add(model);

  // hot glow in each nozzle throat, recessed inside the bell so it is seen only
  // through the bell mouth (the short plume itself comes from effects.js).
  // Centre radiance = throatGlow: above the bloom threshold only in the hot core.
  const V3 = THREE.Vector3;
  const engines = (cfg.engines || []).flatMap((e) => {
    const list = [{ ...e }];
    if (e.mirrorX) list.push({ ...e, p: [-e.p[0], e.p[1], e.p[2]] });
    return list;
  }).map((e) => ({ p: new V3(...e.p), dir: new V3(...(e.dir || [0, 0, -1])).normalize(), radius: e.radius, color: e.color || null, length: e.length ?? e.radius * 2.5 }));
  if (engines.length) {
    const disc = new THREE.CircleGeometry(1, 32);
    const glow = new THREE.MeshBasicMaterial({ map: throatTexture(), color: new THREE.Color(1, 1, 1).multiplyScalar(cfg.throatGlow ?? 3.0), side: THREE.DoubleSide });
    // the bell wall between throat and lip catches the throat's light: a short
    // open cone, bright at the throat and fading toward the lip, seen from inside
    const lining = new THREE.CylinderGeometry(0.97, 0.85, 0.35, 32, 4, true);
    lining.rotateX(Math.PI / 2); // axis along +Z: +Z end = lip, -Z end = throat
    lining.translate(0, 0, -0.175);
    const ramp = [];
    const pos = lining.attributes.position;
    for (let i = 0; i < pos.count; i++) { const k = (pos.getZ(i) + 0.35) / 0.35; ramp.push(...new THREE.Color('#9fb8ff').multiplyScalar(0.9 * (1 - k) ** 2 + 0.04).toArray()); }
    lining.setAttribute('color', new THREE.Float32BufferAttribute(ramp, 3));
    const liningMat = new THREE.MeshBasicMaterial({ vertexColors: true, side: THREE.BackSide, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true });
    for (const e of engines) {
      const q = new THREE.Quaternion().setFromUnitVectors(new V3(0, 0, 1), e.dir);
      const m = new THREE.Mesh(disc, glow);
      m.scale.setScalar(e.radius * 0.85);
      m.position.copy(e.p).addScaledVector(e.dir, -e.radius * 0.35);
      m.quaternion.copy(q);
      m.name = 'nozzle-glow';
      group.add(m);
      const w = new THREE.Mesh(lining, liningMat);
      w.scale.setScalar(e.radius);
      w.position.copy(e.p);
      w.quaternion.copy(q);
      w.name = 'nozzle-lining';
      group.add(w);
    }
  }
  const lights = (cfg.lights || []).flatMap((l) => {
    const one = { p: new V3(...l.p), color: l.color || 'white', size: l.size ?? 0.3, blink: l.blink || null };
    if (!l.mirrorX) return [one];
    return [one, { ...one, p: new V3(-l.p[0], l.p[1], l.p[2]), color: l.mirrorColor ?? one.color }];
  });
  const anchors = {};
  for (const [k, a] of Object.entries(cfg.anchors || {})) anchors[k] = { ...a, ...(a.p ? { p: new V3(...a.p) } : {}), ...(a.dir ? { dir: new V3(...a.dir) } : {}) };
  // lights inside the hull (hangar floodlights): real light sources, children of the ship
  const interiorLights = (cfg.interiorLights || []).map((spec) => {
    const L = interiorLight(spec);
    group.add(L);
    return { p: new V3(...spec.p), kind: spec.kind || 'spot', color: spec.color, intensity: spec.intensity, distance: spec.distance };
  });

  const size = env.getSize(new V3());
  group.userData.ship = {
    name: cfg.name,
    source: { glb: cfg.glb, generator: cfg.generator, concept: cfg.concept, beauty: cfg.beauty },
    envelope: { min: env.min.clone(), max: env.max.clone(), size, center: env.getCenter(new V3()) },
    envelopeVolume: size.x * size.y * size.z,
    engines, lights, anchors, interiorLights,
    triangles: Math.round(triangles),
    drawCalls: meshes,
  };
  return group;
}
