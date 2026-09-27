// Turn a generated GLB (fal image-to-3D) into a scene ship with the same
// contract as ShipBuilder.finish(): a Group whose userData.ship carries the
// envelope, engines, lights and anchors used by scale.js, effects.js and fleet.js.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { toCreasedNormals, mergeVertices, mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { addDetailLayer } from './patina.js';
import { applyLivery } from './livery.js';

const loader = new GLTFLoader();
loader.setMeshoptDecoder(MeshoptDecoder);
const cache = new Map();
const DEG = Math.PI / 180;

let throatTex = null;
/** Radial glow for a nozzle throat: a small white-hot core (the inner ~25 % of the radius, the
 *  only part that crosses the bloom threshold), a dim blue body and a dark rim, so the disc melts
 *  into the glowing bell wall around it instead of reading as a flat lamp. */
function throatTexture() {
  if (throatTex) return throatTex;
  const c = document.createElement('canvas'); c.width = c.height = 128;
  const g = c.getContext('2d');
  const grd = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  // smooth, near-exponential fall-off past the core: no step anywhere that could draw a ring
  grd.addColorStop(0, '#ffffff'); grd.addColorStop(0.1, '#eef1ff'); grd.addColorStop(0.2, '#aab5e0');
  grd.addColorStop(0.3, '#6a76a8'); grd.addColorStop(0.42, '#3a4470'); grd.addColorStop(0.56, '#1f2645');
  grd.addColorStop(0.72, '#10142a'); grd.addColorStop(0.88, '#070913'); grd.addColorStop(1, '#030409');
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
function keepInterior(material, keep, toShip, k = 0) {
  const [min, max] = keep.box;
  const K = `uKeep${k}`, V = `vKeepPos${k}`;
  const uniforms = {
    [`${K}M`]: { value: toShip.clone() },
    [`${K}Min`]: { value: new THREE.Vector3(...min) }, [`${K}Max`]: { value: new THREE.Vector3(...max) },
    [`${K}Feather`]: { value: keep.feather ?? 1.5 }, [`${K}Gain`]: { value: keep.gain ?? 0.5 },
    [`${K}Amount`]: { value: keep.amount ?? 1 }, [`${K}Sat`]: { value: keep.saturation ?? 1 },
  };
  const prev = material.onBeforeCompile;
  material.onBeforeCompile = (shader, renderer) => {
    prev?.call(material, shader, renderer);
    Object.assign(shader.uniforms, uniforms);
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', `#include <common>\nuniform mat4 ${K}M; varying vec3 ${V};`)
      .replace('#include <begin_vertex>', `#include <begin_vertex>\n${V} = (${K}M * vec4(transformed, 1.0)).xyz;`);
    // the texture paint is captured once, right after map_fragment (before the livery repaint)
    const capture = shader.fragmentShader.includes('vec3 keepPaint =') ? '' : '\nvec3 keepPaint = diffuseColor.rgb;';
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', `#include <common>\nuniform vec3 ${K}Min, ${K}Max; uniform float ${K}Feather, ${K}Gain, ${K}Amount, ${K}Sat; varying vec3 ${V};`)
      .replace('#include <map_fragment>', `#include <map_fragment>${capture}`)
      .replace('#include <color_fragment>', `{
          vec3 kd = min(${V} - ${K}Min, ${K}Max - ${V});
          vec3 km = smoothstep(vec3(0.0), vec3(${K}Feather), kd);
          vec3 kp = mix(vec3(dot(keepPaint, vec3(0.2126, 0.7152, 0.0722))), keepPaint, ${K}Sat) * ${K}Gain;
          diffuseColor.rgb = mix(diffuseColor.rgb, kp, km.x * km.y * km.z * ${K}Amount);
        }
        #include <color_fragment>`);
  };
  const prevKey = material.customProgramCacheKey.bind(material);
  material.customProgramCacheKey = () => `keep-interior${k}|${prevKey()}`;
  material.needsUpdate = true;
  return material;
}

/**
 * Light-link the ship's interior spot lights (hangar floodlights) to its interior: on this hull,
 * only surfaces inside the ship-frame box `gate.box` receive spot light. The floodlights cast no
 * shadow maps, so without the gate they would shine through the hangar deck and light exterior
 * surfaces under it (the chin below the bow mouth, the lower flank under the bays). The gate
 * stands in for the hull that occludes them. Point lights (the stern's drive spill) are not
 * gated, and other ships (parked on the deck, launching) are lit normally.
 *
 * `bounce` (optional) adds the light the floodlit deck reflects back up: { box, color,
 * irradiance, feather }. Inside its ship-frame box (the hangar cavity) surfaces receive
 * irradiance * (0.5 - 0.5 n.y) (n in the ship frame): the ceiling the full amount, walls and
 * frame faces half, the deck none. A deck of albedo ~0.12 under ~4-7 units of flood irradiance
 * sends ~0.5 back to a ceiling that sees most of it: ~12 % of the sun. It is a term in this
 * hull's shader, not a light, so parked and launching ships (which hang metres above the deck)
 * are never blown out by a point source standing in for a 190 m-wide lit floor.
 */
function gateInteriorLights(material, gate, toShip, bounce = null) {
  const [min, max] = gate.box;
  const uniforms = {
    uGateM: { value: toShip.clone() },
    uGateMin: { value: new THREE.Vector3(...min) }, uGateMax: { value: new THREE.Vector3(...max) },
    uGateFeather: { value: gate.feather ?? 1 },
  };
  if (bounce) {
    Object.assign(uniforms, {
      uBounceMin: { value: new THREE.Vector3(...bounce.box[0]) }, uBounceMax: { value: new THREE.Vector3(...bounce.box[1]) },
      uBounceFeather: { value: bounce.feather ?? 3 },
      uBounce: { value: new THREE.Color(bounce.color || '#e9e4dc').multiplyScalar(bounce.irradiance ?? 0.5) },
    });
  }
  const lights = THREE.ShaderChunk.lights_fragment_begin;
  const hook = 'getSpotLightInfo( spotLight, geometryPosition, directLight );';
  if (!lights.includes(hook)) { console.warn('[glbship] interior light gate: three.js light loop changed, gate skipped'); return material; }
  const prev = material.onBeforeCompile;
  material.onBeforeCompile = (shader, renderer) => {
    prev?.call(material, shader, renderer);
    Object.assign(shader.uniforms, uniforms);
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nuniform mat4 uGateM; varying vec3 vGatePos; varying vec3 vGateNrm;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvGatePos = (uGateM * vec4(transformed, 1.0)).xyz;\nvGateNrm = mat3(uGateM) * objectNormal;');
    let frag = shader.fragmentShader
      .replace('#include <common>', `#include <common>\nuniform vec3 uGateMin, uGateMax; uniform float uGateFeather; varying vec3 vGatePos; varying vec3 vGateNrm;${bounce ? '\nuniform vec3 uBounceMin, uBounceMax, uBounce; uniform float uBounceFeather;' : ''}`)
      .replace('#include <lights_fragment_begin>', `
        vec3 interiorGateD = min(vGatePos - uGateMin, uGateMax - vGatePos);
        vec3 interiorGateM = smoothstep(vec3(0.0), vec3(uGateFeather), interiorGateD);
        float interiorGate = interiorGateM.x * interiorGateM.y * interiorGateM.z;
        ${lights.replace(hook, `${hook}\n\t\tdirectLight.color *= interiorGate;`)}`);
    if (bounce) {
      frag = frag.replace('#include <lights_fragment_end>', `#include <lights_fragment_end>
        {
          vec3 bd = min(vGatePos - uBounceMin, uBounceMax - vGatePos);
          vec3 bm = smoothstep(vec3(0.0), vec3(uBounceFeather), bd);
          float facing = 0.5 - 0.5 * normalize(vGateNrm).y; // ceiling 1, walls 0.5, deck 0
          reflectedLight.indirectDiffuse += uBounce * (bm.x * bm.y * bm.z * facing) * BRDF_Lambert( material.diffuseColor );
        }`);
    }
    shader.fragmentShader = frag;
  };
  const prevKey = material.customProgramCacheKey.bind(material);
  material.customProgramCacheKey = () => `interior-gate${bounce ? '-bounce' : ''}|${prevKey()}`;
  material.needsUpdate = true;
  return material;
}

const fixtureGeometry = new THREE.CircleGeometry(1, 24);
const fixtureMaterial = new THREE.MeshBasicMaterial({ color: new THREE.Color('#fff3e8').multiplyScalar(6), side: THREE.DoubleSide });

/**
 * Lights the ship carries inside itself (hangar floodlights). Physical units: SpotLight /
 * PointLight intensity in candela, inverse-square falloff (decay 2) windowed to `distance`.
 * spec: { p, color, intensity, distance, kind: 'spot'|'point', angle (deg, half-angle),
 *         penumbra, target: [x,y,z] | dir: [x,y,z], castShadow, shadowMapSize, name,
 *         fixture: radius (m) of an emissive lens at the lamp (spot lights) }
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
    // the lamp itself: a small emissive lens facing the target, bright enough to bloom, so the
    // light visibly comes from a fixture under the ceiling
    if (spec.fixture) {
      const lens = new THREE.Mesh(fixtureGeometry, fixtureMaterial);
      lens.scale.setScalar(spec.fixture);
      lens.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), t.clone().normalize());
      lens.name = 'light-fixture';
      L.add(lens);
    }
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
 *   gameId     optional game unit id shown on the spec sheet (a variant's own id, e.g. TRANSPORTER)
 *   rotate     [x, y, z] degrees applied first so that the bow faces +Z and dorsal +Y
 *   length     design length in metres (bounding-box Z); scale.js then applies
 *              the small volume correction for the class's hangar slots
 *   detail     { set: 'hull', tile: 4, normalStrength, roughAmount, cavity }
 *   livery     optional repaint of the generated texture: 'dark' | 'civil' | {base, gain, mark, ...} (see livery.js)
 *   materials  optional per-material overrides by GLB material name or '*'
 *   crease     optional angle in degrees: split vertex normals at sharper edges
 *              so faceted hard-surface hulls shade flat instead of rounded
 *   engines    [{ p: [x,y,z], radius, dir?, depth?, throat?, wall? }]    (metres, ship frame, before
 *              correction): p = centre of the exit plane, radius = inner wall at the exit, depth =
 *              how far inside the lip the throat plate sits, throat = radius of the hot throat
 *              there, wall = optional measured inner-wall points [[depth, radius], ...] between
 *              the lip and the throat (the glowing lining follows them)
 *   lights     [{ p, color, size, blink }]
 *   anchors    { name: { p, ...extra } }
 *   interiorLights  optional lights carried inside the hull, e.g. hangar floodlights
 *              [{ p, color, intensity (cd), distance, kind: 'spot'|'point', angle, penumbra, target | dir, castShadow }]
 *   interiorLightGate optional { box: [[x,y,z], [x,y,z]] (ship frame), feather }: this hull's surfaces
 *              outside the box receive no spot light (see gateInteriorLights)
 *   interiorBounce optional { box, color, irradiance, feather }: light the floodlit deck reflects
 *              onto the ceiling and walls inside the box (needs interiorLights + interiorLightGate)
 *   fixtures   optional [{ p: [x,y,z] (centre), size: [sx,sy,sz], rotZ (rad), color, radiance, mirrorX, mirrorOffset }]:
 *              emissive light fixtures (hangar light strips), drawn as unlit boxes of that radiance
 *   liveryKeep optional { box: [[x,y,z], [x,y,z]] (ship frame), gain, saturation, feather } or a list
 *              of them: inside a box the texture keeps its own paint (scaled by gain) instead of the livery repaint
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
  // liveryKeep: one box or a list of boxes (the first is the interior box other features use)
  const keeps = cfg.liveryKeep ? [].concat(cfg.liveryKeep) : [];
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
    const gate = cfg.interiorLights?.length && cfg.interiorLightGate;
    const keyOf = (m) => (cfg.liveryKeep || gate || cfg.detail?.interior ? `${m.uuid}|${o.matrixWorld.elements.map((e) => e.toFixed(6)).join(',')}` : m);
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
      if (cfg.livery && cfg.liveryKeep) keeps.forEach((kp, k) => keepInterior(mm, kp, o.matrixWorld, k));
      if (gate) gateInteriorLights(mm, gate, o.matrixWorld, cfg.interiorBounce || null);
      if (detailSet) {
        // object-space units per metre: undo the model scale and any node scale
        const nodeScale = new THREE.Vector3(); o.getWorldScale(nodeScale);
        // an interior set (the hangar's deck plating) inside the interior box, if the ship has one
        const inner = cfg.detail.interior && library[cfg.detail.interior.set]
          ? { ...cfg.detail.interior, set: library[cfg.detail.interior.set], box: cfg.detail.interior.box || keeps[0]?.box, toShip: o.matrixWorld } : null;
        addDetailLayer(mm, detailSet, { unitsPerMetre: 1 / nodeScale.x, ...cfg.detail, interior: inner?.box ? inner : null });
      }
      upgraded.set(keyOf(m), mm);
      return mm;
    });
    o.material = Array.isArray(o.material) ? next : next[0];
  });

  const group = new THREE.Group();
  group.name = cfg.name || 'glb-ship';
  group.add(model);

  // Hot glow in each nozzle throat, recessed at the measured depth of the bell's throat plate so
  // it is seen only through the bell mouth (the short plume itself comes from effects.js). The
  // bell wall between throat and lip catches the throat's light: a lining that follows the
  // measured inner wall, hot at the throat and fading to nothing over the outer 40 % toward the
  // lip. Seen off-axis the lip hides the throat and the eye reads a graded, glowing inner wall.
  // Centre radiance = throatGlow: above the bloom threshold only in the white-hot core.
  const V3 = THREE.Vector3;
  const engines = (cfg.engines || []).flatMap((e) => {
    const list = [{ ...e }];
    if (e.mirrorX) list.push({ ...e, p: [-e.p[0], e.p[1], e.p[2]] });
    return list;
  }).map((e) => ({
    p: new V3(...e.p), dir: new V3(...(e.dir || [0, 0, -1])).normalize(), radius: e.radius, color: e.color || null, length: e.length ?? e.radius * 2.5,
    depth: e.depth ?? e.radius * 0.8, throat: e.throat ?? e.radius * 0.68, wall: e.wall || [],
  }));
  if (engines.length) {
    const disc = new THREE.CircleGeometry(1, 40);
    const glow = new THREE.MeshBasicMaterial({ map: throatTexture(), color: new THREE.Color(1, 1, 1).multiplyScalar(cfg.throatGlow ?? 1.2), side: THREE.DoubleSide });
    // FrontSide: the lathe below winds its front faces toward the axis, so only the inner wall
    // seen through the mouth is drawn (DoubleSide added near and far walls and flooded the mouth)
    const liningMat = new THREE.MeshBasicMaterial({ vertexColors: true, side: THREE.FrontSide, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true });
    const hot = new THREE.Color('#d2d8f0'), deep = new THREE.Color('#5a6690'); // pale, not periwinkle
    const linings = new Map();
    // lining: a lathe through the lip (0.97 r), the measured wall points and the throat, in metres,
    // axis along +Z (z = 0 at the lip, -depth at the throat), vertex colours = the glow ramp
    const liningFor = (e) => {
      const key = JSON.stringify([e.radius, e.depth, e.throat, e.wall]);
      if (linings.has(key)) return linings.get(key);
      // 4 % inside the measured wall, so the wall itself never hides the lining in a thin sliver
      const prof = [[0, e.radius * 0.95], ...e.wall.filter(([d]) => d > 0 && d < e.depth).map(([d, r]) => [d, r * 0.96]), [e.depth, e.throat]];
      // resample densely along depth so the ramp is smooth
      const pts = [];
      const N = 24;
      for (let i = 0; i <= N; i++) {
        const d = (i / N) * e.depth;
        let k = 1; while (k < prof.length - 1 && prof[k][0] < d) k++;
        const [d0, r0] = prof[k - 1], [d1, r1] = prof[k];
        const r = r0 + (r1 - r0) * THREE.MathUtils.clamp((d - d0) / Math.max(d1 - d0, 1e-6), 0, 1);
        pts.push(new THREE.Vector2(r, -d)); // lathe: x = radius, y = axis
      }
      const g = new THREE.LatheGeometry(pts, 40);
      g.rotateX(Math.PI / 2); // lathe axis +Y -> +Z: lip at z = 0, throat at z = -depth
      const ramp = [];
      const pos = g.attributes.position;
      for (let i = 0; i < pos.count; i++) {
        const u = THREE.MathUtils.clamp(-pos.getZ(i) / e.depth, 0, 1); // 0 at the lip, 1 at the throat
        // 0.12 at the throat, a sixth of that 0.75 of the way down, dark over the outer 60 %: a
        // graded glow near the throat only; white-blue at the throat, deeper blue where dimmer
        // (the last 10 % fades back down: the steep converging end next to the throat is seen
        // almost edge-on from a stern quarter and would draw a thin bright ring round the disc)
        const endFade = 1 - 0.75 * THREE.MathUtils.smoothstep(u, 0.88, 1.0);
        ramp.push(...deep.clone().lerp(hot, u * u).multiplyScalar(0.12 * u ** 6 * endFade).toArray());
      }
      g.setAttribute('color', new THREE.Float32BufferAttribute(ramp, 3));
      linings.set(key, g);
      return g;
    };
    for (const e of engines) {
      const q = new THREE.Quaternion().setFromUnitVectors(new V3(0, 0, 1), e.dir);
      const m = new THREE.Mesh(disc, glow);
      m.scale.setScalar(e.throat * 0.92); // the disc edge tucks behind the lining
      m.position.copy(e.p).addScaledVector(e.dir, -e.depth);
      m.quaternion.copy(q);
      m.name = 'nozzle-glow';
      group.add(m);
      const w = new THREE.Mesh(liningFor(e), liningMat);
      w.position.copy(e.p);
      w.quaternion.copy(q);
      w.name = 'nozzle-lining';
      group.add(w);
    }
  }
  // light fixtures built into the hull (hangar light strips): emissive boxes, merged into one
  // mesh per colour and radiance. They light nothing themselves (the floodlights and the bounce
  // term do); they show where the light comes from
  const fixtureGroups = new Map();
  for (const f of cfg.fixtures || []) {
    const list = f.mirrorX ? [f, { ...f, p: [-f.p[0] + (f.mirrorOffset ?? 0), f.p[1], f.p[2]] }] : [f];
    for (const q of list) {
      const key = `${q.color || '#fff4e6'}|${q.radiance ?? 2}`;
      const g = new THREE.BoxGeometry(...q.size);
      if (q.rotZ) g.rotateZ(q.rotZ);
      g.translate(...q.p);
      if (!fixtureGroups.has(key)) fixtureGroups.set(key, []);
      fixtureGroups.get(key).push(g);
    }
  }
  for (const [key, geoms] of fixtureGroups) {
    const [color, radiance] = key.split('|');
    const strip = new THREE.Mesh(mergeGeometries(geoms), new THREE.MeshBasicMaterial({ color: new THREE.Color(color).multiplyScalar(parseFloat(radiance)) }));
    strip.name = 'light-strips';
    group.add(strip);
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
    source: { glb: cfg.glb, generator: cfg.generator, concept: cfg.concept, beauty: cfg.beauty, gameId: cfg.gameId || null },
    envelope: { min: env.min.clone(), max: env.max.clone(), size, center: env.getCenter(new V3()) },
    envelopeVolume: size.x * size.y * size.z,
    engines, lights, anchors, interiorLights,
    triangles: Math.round(triangles),
    drawCalls: meshes,
  };
  return group;
}
