// Turn a generated GLB (fal image-to-3D) into a scene ship with the same
// contract as ShipBuilder.finish(): a Group whose userData.ship carries the
// envelope, engines, lights and anchors used by scale.js, effects.js and fleet.js.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { addDetailLayer } from './patina.js';

const loader = new GLTFLoader();
loader.setMeshoptDecoder(MeshoptDecoder);
const cache = new Map();
const DEG = Math.PI / 180;

export function loadGLB(url) {
  if (!cache.has(url)) cache.set(url, loader.loadAsync(url));
  return cache.get(url);
}

/**
 * cfg (from a ship module's `asset` export):
 *   glb        path to the optimised GLB
 *   concept    image-to-3D input image (fal concept art); beauty: in-orbit concept shot
 *   rotate     [x, y, z] degrees applied first so that the bow faces +Z and dorsal +Y
 *   length     design length in metres (bounding-box Z); scale.js then applies
 *              the small volume correction for the class's hangar slots
 *   detail     { set: 'hull', tile: 4, normalStrength, roughAmount, cavity }
 *   materials  optional per-material overrides by GLB material name or '*'
 *   engines    [{ p: [x,y,z], radius, dir? }]    (metres, ship frame, before correction)
 *   lights     [{ p, color, size, blink }]
 *   anchors    { name: { p, ...extra } }
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
  const detailSet = cfg.detail ? library[cfg.detail.set] : null;
  let triangles = 0, meshes = 0;
  model.traverse((o) => {
    if (!o.isMesh) return;
    meshes++;
    const g = o.geometry;
    triangles += (g.index ? g.index.count : g.attributes.position.count) / 3;
    o.castShadow = true;
    o.receiveShadow = true;
    o.userData.hull = true; // raycast target for the hangar containment test
    const mats = Array.isArray(o.material) ? o.material : [o.material];
    const next = mats.map((m) => {
      if (upgraded.has(m)) return upgraded.get(m);
      const mm = m.clone();
      const over = { ...(cfg.materials?.['*'] || {}), ...(cfg.materials?.[m.name] || {}) };
      mm.envMapIntensity = over.envMapIntensity ?? 1.0;
      if (over.roughness !== undefined) mm.roughness = over.roughness;
      if (over.metalness !== undefined) mm.metalness = over.metalness;
      if (over.color) mm.color = new THREE.Color(over.color);
      if (over.emissiveBoost && mm.emissiveMap) mm.emissiveIntensity = over.emissiveBoost;
      if (detailSet) {
        // object-space units per metre: undo the model scale and any node scale
        const nodeScale = new THREE.Vector3(); o.getWorldScale(nodeScale);
        addDetailLayer(mm, detailSet, { unitsPerMetre: 1 / nodeScale.x, ...cfg.detail });
      }
      upgraded.set(m, mm);
      return mm;
    });
    o.material = Array.isArray(o.material) ? next : next[0];
  });

  const group = new THREE.Group();
  group.name = cfg.name || 'glb-ship';
  group.add(model);

  // glowing engine cores so bloom has a source even if the texture is dark
  const V3 = THREE.Vector3;
  const engines = (cfg.engines || []).flatMap((e) => {
    const list = [{ ...e }];
    if (e.mirrorX) list.push({ ...e, p: [-e.p[0], e.p[1], e.p[2]] });
    return list;
  }).map((e) => ({ p: new V3(...e.p), dir: new V3(...(e.dir || [0, 0, -1])).normalize(), radius: e.radius, color: e.color || null, length: e.length ?? e.radius * 6 }));
  if (engines.length && palette?.engine) {
    const disc = new THREE.CylinderGeometry(1, 1, 0.08, 32);
    disc.rotateX(Math.PI / 2);
    for (const e of engines) {
      const m = new THREE.Mesh(disc, palette.engine);
      m.scale.set(e.radius, e.radius, e.radius);
      m.position.copy(e.p);
      m.quaternion.setFromUnitVectors(new V3(0, 0, -1), e.dir);
      group.add(m);
    }
  }
  const lights = (cfg.lights || []).flatMap((l) => {
    const one = { p: new V3(...l.p), color: l.color || 'white', size: l.size ?? 0.3, blink: l.blink || null };
    if (!l.mirrorX) return [one];
    return [one, { ...one, p: new V3(-l.p[0], l.p[1], l.p[2]), color: l.mirrorColor ?? one.color }];
  });
  const anchors = {};
  for (const [k, a] of Object.entries(cfg.anchors || {})) anchors[k] = { ...a, p: new V3(...a.p), ...(a.dir ? { dir: new V3(...a.dir) } : {}) };

  const size = env.getSize(new V3());
  group.userData.ship = {
    name: cfg.name,
    source: { glb: cfg.glb, generator: cfg.generator, concept: cfg.concept, beauty: cfg.beauty },
    envelope: { min: env.min.clone(), max: env.max.clone(), size, center: env.getCenter(new V3()) },
    envelopeVolume: size.x * size.y * size.z,
    engines, lights, anchors,
    triangles: Math.round(triangles),
    drawCalls: meshes,
  };
  return group;
}
