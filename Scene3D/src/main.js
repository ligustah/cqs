// CQS reboot — orbital fleet scene.
// Modes (query ?mode=… or #token): fleet (default) | lineup | ship | building | check
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { CSS2DRenderer } from 'three/addons/renderers/CSS2DRenderer.js';

import { createPalette } from './lib/materials.js';
import { attachEffects, LIGHTSCAPE_GAIN } from './lib/effects.js';
import { CLASSES, SLOT_VOLUME, carrierLoads, sizeLabel } from './lib/scale.js';
import { hangarInsideFraction } from './lib/hangar.js';
import { buildShip, loadShips, setShipContext, LOAD_ERRORS, ORDER, GROUND, LINEUP, BUILDINGS, importBuilding, loadBuildings, buildBuilding } from './ships/index.js';
import { loadPatinaLibrary, proceduralStandIn } from './lib/patina.js';
import { setLiveryScheme } from './lib/glbship.js';
import { panelSet } from './lib/textures.js';
import { createLighting, createStudioLighting, studioDir, STUDIO, SUN_DIR } from './env/lighting.js';
import { TIER } from './lib/device.js';
import { AO_REQUESTED, createScreenAO } from './lib/finish.js';
import { createSky } from './env/sky.js';
import { createPlanet } from './env/planet.js';
import { ENV } from './env/state.js';
import { buildFleet } from './fleet.js';
import { parkInHangar } from './lib/park.js';
import { createUI } from './ui.js';
import { createChartOverlay, frameView } from './lib/chart.js';

const params = new URLSearchParams(location.search);
const EXPOSURE = 1.7; // default tone-mapping exposure (see start())
const hash = location.hash.replace('#', '');
const HASH_MODES = ['fleet', 'lineup'];
// #<ship or ground unit> opens the ship studio, #<building> the building view
let mode = params.get('mode') || (HASH_MODES.includes(hash) ? hash : LINEUP.includes(hash) ? 'ship' : BUILDINGS[hash] ? 'building' : 'fleet');
// one route per building: ?mode=building&building=<id>; ?mode=ship&ship=<building> is an alias for it
if (mode === 'ship' && BUILDINGS[params.get('ship')]) mode = 'building';
const buildingId = mode === 'building'
  ? [params.get('building'), params.get('ship'), hash].find((id) => BUILDINGS[id]) || 'shipyard'
  : null;
// the building's module (its studio hint is read before the lighting is set up); its assets load below
const BUILDING = buildingId ? await importBuilding(buildingId) : null;
const BSTUDIO = BUILDING?.studio ?? {};
// studio camera azimuth / elevation (degrees): ?az= / ?el=, else the building's hint, else 35 / 18 (buildings 30)
const camAz = parseFloat(params.get('az') ?? String(BSTUDIO.az ?? 35));
const camEl = parseFloat(params.get('el') ?? String(BSTUDIO.el ?? (mode === 'building' ? 30 : 18)));
const still = params.has('still');
const fixedTime = params.has('t') ? parseFloat(params.get('t')) : null;

// Studio key: in the ship studio the star is placed relative to the camera, not the ship, so the
// key always rakes the view: ~85 deg round from the camera azimuth (slightly behind the subject's
// visible flank) and 30 deg up. Every visible hull then splits into a lit plane and a shadowed
// plane (the fleet's port-high SUN_DIR lit most of the default 35/18 view flat and left the 270
// side views as silhouettes). SUN_DIR is shared by reference (env map, planet, sky, shadow fit),
// so it is set here, before anything reads it. ?sunaz= / ?sunel= override (degrees, ship frame).
// Showcase lighting (env/lighting.js createStudioLighting) is the ship studio's default: key, fill and
// rim lights, a soft-box environment and a gradient backdrop, no planet. ?studio=0 falls back to the
// orbital rig (the hard sun below over the planet). Every other view keeps the orbital rig.
// The building view uses the same showcase rig, dimmed per light by the building's `studio` hint (the shipyard's dusk).
const studio = (mode === 'ship' || mode === 'building') && params.get('studio') !== '0';
if (studio) {
  // the studio key and fill light the dark hull far more than the orbital sun: the lightscape (pins, slits) gets
  // STUDIO.lightscapeGain there so the small lights keep the concept's contrast; orbit and fleet stay at 1
  LIGHTSCAPE_GAIN.value = BSTUDIO.lightscapeGain ?? STUDIO.lightscapeGain ?? 1;
  // the key light is also SUN_DIR (the shadow fit reads it); ?sunaz= / ?sunel= still override it (ship frame)
  SUN_DIR.copy(studioDir(camAz, camEl, STUDIO.key.az, STUDIO.key.el));
  if (params.has('sunaz') || params.has('sunel')) {
    const sAz = THREE.MathUtils.degToRad(parseFloat(params.get('sunaz') ?? String(camAz + STUDIO.key.az)));
    const sEl = THREE.MathUtils.degToRad(parseFloat(params.get('sunel') ?? String(STUDIO.key.el)));
    SUN_DIR.set(Math.sin(sAz) * Math.cos(sEl), Math.sin(sEl), Math.cos(sAz) * Math.cos(sEl)).normalize();
  }
} else if (mode === 'ship' || mode === 'building') {
  const sAz = THREE.MathUtils.degToRad(parseFloat(params.get('sunaz') ?? String(camAz + 85)));
  const sEl = THREE.MathUtils.degToRad(parseFloat(params.get('sunel') ?? '30'));
  SUN_DIR.set(Math.sin(sAz) * Math.cos(sEl), Math.sin(sEl), Math.cos(sAz) * Math.cos(sEl)).normalize();
}

window.__report = null;
window.__ready = false;

const palette = createPalette();
// fal PATINA tiling PBR sets (assets/materials); ?standin uses procedural textures for testing
const library = await loadPatinaLibrary();
if (!Object.keys(library).length && params.has('standin')) library.hull = proceduralStandIn(panelSet({ seed: 7, style: 'hull' }));
// ?livery=none|dark|civil replaces every module's livery; ?livery=tone|bone keeps it and paints the
// module's liveryZones in a lighter two-tone scheme (lib/livery.js SCHEMES). Default: dark (each module's own)
const liveryQ = params.get('livery') || null;
const liveryScheme = liveryQ === 'tone' || liveryQ === 'bone' ? liveryQ : null;
setLiveryScheme(liveryScheme);
setShipContext({ library, livery: liveryScheme ? null : liveryQ });
const studioShip = params.get('ship') || (LINEUP.includes(hash) ? hash : 'fighter');
// The studio carrier's open bays show parked ships by default (?parked=0 empties the hangar,
// ?parked=1 also aims the camera at it), so every class is needed; the carrier's spec sheet also
// checks its hangar against every class's envelope
const studioParked = mode === 'ship' && studioShip === 'carrier' ? params.get('parked') !== '0' : false;
// The orbital fleet loads only the fleet classes (ORDER: never the ground units); the lineup and the check also load
// the ground units (GROUND); the building view loads only what its building asks for (load hook).
const onlyShip = mode === 'building' ? []
  : mode === 'ship' && !studioParked && studioShip !== 'carrier' ? [studioShip]
    : mode === 'lineup' || mode === 'check' ? LINEUP : ORDER;
await loadShips(onlyShip);
// buildings: the one on view, or those the fleet scene places (BUILDINGS[id].fleet)
const fleetBuildings = Object.keys(BUILDINGS).filter((id) => BUILDINGS[id].fleet);
if (buildingId) await loadBuildings([buildingId]);
else if (mode === 'fleet') await loadBuildings(fleetBuildings);

// ---------------------------------------------------------------------------
// check mode: build every ship, report envelopes vs. the game's size stat
// ---------------------------------------------------------------------------
if (mode === 'check') {
  const rows = [];
  const env = {};
  let hangar = null, hangarInside = null;
  // every class, plus the civil ship's troop variant (4 slots like the cargo ship, own envelope)
  // (and the ground units at their true size: no slots, scale 1; never in the hangar loads)
  for (const [cls, variant] of [...ORDER.map((c) => [c]), ['freighter', 'troops'], ...GROUND.map((c) => [c])]) {
    const t0 = performance.now();
    const g = buildShip(cls, palette, variant ? { variant } : {});
    const s = g.userData.ship;
    const key = variant ? `${cls}:${variant}` : cls;
    env[key] = s.envelope.size.clone();
    if (cls === 'carrier' && s.anchors.hangar) {
      hangar = new THREE.Vector3(...s.anchors.hangar.size).multiplyScalar(s.scaleCorrection);
      const r = hangarInsideFraction(g, s.anchors.hangar);
      hangarInside = { fraction: +r.fraction.toFixed(3), samples: r.samples, misses: r.misses };
    }
    rows.push({
      cls: key, name: s.meta?.name, size: CLASSES[cls].size,
      L: +s.envelope.size.z.toFixed(2), B: +s.envelope.size.x.toFixed(2), H: +s.envelope.size.y.toFixed(2),
      volume: Math.round(s.envelopeVolume), slots: CLASSES[cls].size ? +(s.envelopeVolume / SLOT_VOLUME).toFixed(3) : null,
      scaleCorrection: +s.scaleCorrection.toFixed(4), triangles: s.triangles, drawCalls: s.drawCalls,
      engines: s.engines.length, lights: s.lights.length, buildMs: Math.round(performance.now() - t0),
    });
  }
  const loads = hangar ? carrierLoads(hangar, env) : [];
  window.__report = { errors: LOAD_ERRORS, rows, hangar: hangar && hangar.toArray().map((v) => +v.toFixed(2)), loads, hangarInside, slotVolume: SLOT_VOLUME };
  window.__ready = true;
  document.body.dataset.ready = '1';
} else {
  start();
}

function start() {
  const container = document.getElementById('app') || document.body;
  const renderer = new THREE.WebGLRenderer({ antialias: false, powerPreference: 'high-performance' });
  const w = parseInt(params.get('w')) || container.clientWidth || innerWidth;
  const h = parseInt(params.get('h')) || container.clientHeight || innerHeight;
  renderer.setPixelRatio(still ? 1 : Math.min(devicePixelRatio, TIER.pixelRatio));
  renderer.setSize(w, h);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  // Exposed like a camera metered for sunlit subjects: Khronos PBR Neutral keeps the scene's
  // contrast up to ~0.8 and only rolls off the top, so a sunlit 0.055-albedo hull lands at a
  // median of ~70-80 sRGB while sunlit cloud tops sit just under clipping (~225-240) and stay
  // near-white. (AgX compressed the clouds to ~180 grey.) Exposure scales scene-linear
  // radiance, so the bloom threshold (applied before it) is unchanged.
  // Look-dev: ?tonemap=agx|neutral, ?exposure=
  const TONEMAPS = { agx: THREE.AgXToneMapping, neutral: THREE.NeutralToneMapping };
  renderer.toneMapping = TONEMAPS[params.get('tonemap')] ?? THREE.NeutralToneMapping;
  renderer.toneMappingExposure = parseFloat(params.get('exposure') || String(studio ? BSTUDIO.exposure ?? STUDIO.exposure : EXPOSURE));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFShadowMap;
  container.appendChild(renderer.domElement);
  renderer.domElement.id = 'scene';

  const labelRenderer = new CSS2DRenderer();
  labelRenderer.setSize(w, h);
  labelRenderer.domElement.className = 'labels';
  container.appendChild(labelRenderer.domElement);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#010205');
  const camera = new THREE.PerspectiveCamera(parseFloat(params.get('fov') || '38'), w / h, 0.5, 250000);
  // Shots are composed for a ~16:10 landscape frame. On a portrait screen (a phone) the same
  // vertical lens would show a thin slice, so the projection widens until the frame covers at
  // least 60 % of the landscape frame's width; the authored fov is left untouched.
  const updateProjection = camera.updateProjectionMatrix.bind(camera);
  camera.updateProjectionMatrix = () => {
    const fov = camera.fov, k = Math.max(1, (0.6 * 1.6) / camera.aspect);
    if (k > 1) camera.fov = 2 * Math.atan(Math.tan((fov * Math.PI) / 360) * k) * (180 / Math.PI);
    updateProjection();
    camera.fov = fov;
  };
  camera.updateProjectionMatrix();

  const lighting = studio
    ? createStudioLighting(renderer, scene, {
      shadowSize: TIER.shadowSize, lite: TIER.ao === false, exposure: renderer.toneMappingExposure,
      camAz, camEl, keyDir: SUN_DIR,
    })
    : createLighting(renderer, scene, { shadowSize: TIER.shadowSize });
  // a building's studio hint (e.g. the shipyard's dusk): the showcase rig dimmed per light (key, fill, rim, kick, env)
  if (studio && mode === 'building') {
    lighting.sun.intensity *= BSTUDIO.key ?? 1;
    for (const L of lighting.lights || []) L.intensity *= BSTUDIO[L.name.replace('studio-', '')] ?? 1;
    scene.environmentIntensity *= BSTUDIO.env ?? 1;
  }
  // the studio has no sky (star field, sun glare): its backdrop is part of the lighting rig
  const sky = studio ? { update() {} } : createSky(scene);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.06;
  controls.rotateSpeed = 0.6;
  controls.zoomSpeed = 0.9;

  const composer = new EffectComposer(renderer, new THREE.WebGLRenderTarget(w, h, { type: THREE.HalfFloatType, samples: TIER.samples }));
  composer.setPixelRatio(renderer.getPixelRatio());
  composer.addPass(new RenderPass(scene, camera));
  // Lens glare, not haze. Threshold is scene-linear radiance (before exposure):
  // sunlit clouds peak ~1.2 and dark hulls ~0.1, so only the star, the hot
  // throat of each drive bell and the nav lights (>= 3) pass. Mip weights fall
  // steeply so the glow stays tight around the source (~0.4x its energy).
  const bloom = new UnrealBloomPass(new THREE.Vector2(w, h), 0.12, 0.0, 2.0);
  bloom.highPassUniforms.smoothWidth.value = 1.0;
  bloom.compositeMaterial.uniforms.bloomFactors.value = [1.0, 0.45, 0.18, 0.06, 0.02];
  composer.addPass(bloom);
  composer.addPass(new OutputPass());
  // The camera's own imperfections, after the sRGB encode: a gentle corner falloff (lens
  // vignetting, ~6 % in the corners on the encoded value, ~12 % in light) and luminance-dependent
  // sensor grain (sigma ~1.5/255 in the shadows falling to ~0.5/255 in the highlights; it also
  // dithers the smooth sun glare and planet limb gradients, which band otherwise). Stills use a
  // fixed grain pattern; the interactive page re-seeds it every frame like video.
  const grainPass = new ShaderPass({
    uniforms: { tDiffuse: { value: null }, uSeed: { value: 0 }, uAspect: { value: w / h } },
    vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
    fragmentShader: `uniform sampler2D tDiffuse; uniform float uSeed, uAspect; varying vec2 vUv;
      float h(vec2 p){ return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
      void main(){
        vec4 c = texture2D(tDiffuse, vUv);
        vec2 q = (vUv - 0.5) * vec2(uAspect, 1.0);
        float r2 = dot(q, q) / dot(vec2(0.5 * uAspect, 0.5), vec2(0.5 * uAspect, 0.5)); // 1 in the corners
        c.rgb *= 1.0 - 0.06 * r2 * r2;
        vec2 p = gl_FragCoord.xy + uSeed * vec2(37.0, 17.0);
        float n = (h(p) + h(p.yx + 17.0) + h(p + 91.7) - 1.5) * 2.0; // ~unit-variance, zero mean
        float luma = dot(c.rgb, vec3(0.2126, 0.7152, 0.0722));
        float sigma = mix(1.5, 0.5, smoothstep(0.08, 0.7, luma));
        gl_FragColor = vec4(c.rgb + n * sigma / 255.0, c.a);
      }`,
  });
  composer.addPass(grainPass);

  // opt-in screen-space contact shadows (?ao=1, desktop tier only; src/lib/finish.js)
  const screenAO = AO_REQUESTED && TIER.ao ? createScreenAO(renderer, scene, camera) : null;

  const effects = [];
  const tickers = [];
  const overlays = []; // screen-space annotation, laid out after the camera has moved
  let world = null; // { ships:[{group, cls}], focus(cls) , bounds }

  if (mode === 'building') world = setupBuildingStudio();
  else if (mode === 'ship') world = setupShipStudio();
  else if (mode === 'lineup') world = setupLineup();
  else world = setupFleet();

  // hangar-load envelopes for the carrier's spec sheet: every loaded class (and the troop
  // variant), whatever this view happens to show
  const envelopes = {};
  if (!still) {
    for (const cls of onlyShip) envelopes[cls] = buildShip(cls, palette).userData.ship.envelope.size.clone();
    if (onlyShip.includes('freighter')) envelopes['freighter:troops'] = buildShip('freighter', palette, { variant: 'troops' }).userData.ship.envelope.size.clone();
  }
  // the registry lists whatever this view shows, in this order (fleet classes, ground units, buildings)
  const uiOrder = [...ORDER, ...GROUND, ...Object.keys(BUILDINGS)];
  // the view's id for the view switch: fleet / lineup, or the ship or building on view
  const view = mode === 'ship' ? studioShip : mode === 'building' ? buildingId : mode;
  const ui = createUI({
    mode, view, still, world, classes: CLASSES, order: uiOrder, envelopes,
    // switch views by #token (the hash route); a ?mode= / ?ship= / ?building= query would override the hash, so it
    // is dropped (look-dev parameters such as ?lite= stay)
    onMode: (m) => {
      const q = new URLSearchParams(location.search);
      for (const k of ['mode', 'ship', 'building', 'shot', 'variant', 'parked', 'lineup', 'focus', 'dist', 'az', 'el', 'cam', 'target']) q.delete(k);
      const qs = q.toString();
      if (qs === location.search.replace(/^\?/, '')) { location.hash = m; location.reload(); } else location.href = `${location.pathname}${qs ? `?${qs}` : ''}#${m}`;
    },
    onFocus: (cls) => world.focus?.(cls),
    onToggle: (key, on) => { if (key === 'orbit') { controls.autoRotate = on; controls.autoRotateSpeed = 0.35; } else world.toggle?.(key, on); },
  });
  world.reframe?.(); // the overlay panels are filled now: frame the view clear of them

  // --- ship studio: one ship, framed for inspection / screenshots ----------
  /** Up to ~`max` world-space vertices of a ship's hull meshes (strided), for framing. allMeshes: the parts too (a
   *  ground unit's wheels, collar and weapon station are a large share of its silhouette). */
  function hullPoints(g, max = 6000, allMeshes = false) {
    g.updateMatrixWorld(true);
    const meshes = [];
    g.traverse((o) => { if (o.isMesh && (allMeshes ? o.visible : o.userData.hull) && o.geometry?.attributes.position) meshes.push(o); });
    const total = meshes.reduce((n, m) => n + m.geometry.attributes.position.count, 0);
    const stride = Math.max(1, Math.ceil(total / max));
    const pts = [];
    for (const m of meshes) {
      const pos = m.geometry.attributes.position;
      for (let i = 0; i < pos.count; i += stride) pts.push(new THREE.Vector3().fromBufferAttribute(pos, i).applyMatrix4(m.matrixWorld));
    }
    return pts;
  }
  function setupShipStudio() {
    const cls = studioShip;
    const g = buildShip(cls, palette, { variant: params.get('variant') || undefined });
    const s = g.userData.ship;
    g.position.sub(s.envelope.center);
    scene.add(g);
    effects.push(attachEffects(g));
    if (studioParked && s.anchors.hangarDeck) effects.push(...parkInHangar(g, { buildShip, palette, attachEffects }).effects);
    const box = new THREE.Box3().setFromObject(g);
    lighting.fitShadow(box);
    const az = THREE.MathUtils.degToRad(camAz), el = THREE.MathUtils.degToRad(camEl);
    const dir = new THREE.Vector3(Math.sin(az) * Math.cos(el), Math.sin(el), Math.cos(az) * Math.cos(el));
    const k = parseFloat(params.get('dist') ?? '1');
    if (params.get('parked') === '1' && s.anchors.hangar) {
      // ?parked=1 frames the hangar (the parked ships)
      const focus = s.anchors.hangar.p.clone().multiplyScalar(s.scaleCorrection).sub(s.envelope.center);
      camera.position.copy(dir).multiplyScalar(s.envelope.size.length() * 1.15 * k).add(focus);
      controls.target.copy(focus);
    } else {
      // fit the hull's own silhouette in the frame from this direction (a sample of its mesh
      // vertices, projected), with a margin, then ?dist scales the camera distance. The envelope's
      // 8 corners would centre the box, not the ship: wedge and tapered hulls then sat high in
      // the frame over an empty bottom third
      let pts = hullPoints(g, 6000, GROUND.includes(cls));
      if (pts.length < 8) {
        const e = s.envelope; pts = [];
        for (let i = 0; i < 8; i++) pts.push(new THREE.Vector3(i & 1 ? e.max.x : e.min.x, i & 2 ? e.max.y : e.min.y, i & 4 ? e.max.z : e.min.z).sub(e.center));
      }
      const target = frameView(camera, pts, dir, { l: 64, r: 64, t: 56, b: 56 }, w, h);
      camera.position.sub(target).multiplyScalar(k).add(target);
      controls.target.copy(target);
    }
    // studio stills are shot in orbit, over the planet (?planet=0 for a black backdrop); the
    // interactive studio stays on black unless ?planet is given (the planet costs frame time)
    // (showcase lighting: never a planet)
    const studioPlanet = studio ? false : params.has('planet') ? params.get('planet') !== '0' : still && !params.has('debug');
    if (studioPlanet) createPlanet(scene);
    if (params.has('debug')) g.add(debugOverlay(s));
    return { ships: [{ group: g, cls }], selected: cls, focus: () => {} };
  }

  // --- building view: one building (src/buildings/<id>.js), framed like the ship studio -----------
  // ?mode=building&building=<id> (or #<id>; ?mode=ship&ship=<id> is an alias). Showcase rig with the building's
  // `studio` hint; ?az= / ?el= / ?dist= as in the ship studio; ?focus=x,y,z&dist=m (metres, building frame) aims a
  // close-up at a point of the building instead of fitting the whole of it.
  function setupBuildingStudio() {
    const g = buildBuilding(buildingId, palette);
    const b = g.userData.building;
    scene.add(g);
    // a building's drives (tugs, docked ships) stay cold
    for (const t of b.effectTargets) effects.push(attachEffects(t, { power: 0 }));
    lighting.fitShadow(new THREE.Box3().setFromObject(g));
    const az = THREE.MathUtils.degToRad(camAz), el = THREE.MathUtils.degToRad(camEl);
    const dir = new THREE.Vector3(Math.sin(az) * Math.cos(el), Math.sin(el), Math.cos(az) * Math.cos(el));
    let target;
    if (params.has('focus')) {
      target = new THREE.Vector3(...params.get('focus').split(',').map(Number));
      camera.position.copy(dir).multiplyScalar(parseFloat(params.get('dist') ?? '120')).add(target);
    } else {
      // the whole silhouette: the hull node and every part (halls, cranes, the docked ships)
      let pts = hullPoints(g, 12000, true);
      if (pts.length < 8) { const bb = new THREE.Box3().setFromObject(g); pts = []; for (let i = 0; i < 8; i++) pts.push(new THREE.Vector3(i & 1 ? bb.max.x : bb.min.x, i & 2 ? bb.max.y : bb.min.y, i & 4 ? bb.max.z : bb.min.z)); }
      target = frameView(camera, pts, dir, { l: 64, r: 64, t: 56, b: 56 }, w, h);
      camera.position.sub(target).multiplyScalar(parseFloat(params.get('dist') ?? String(b.studio?.dist ?? 1))).add(target);
    }
    camera.lookAt(target);
    controls.target.copy(target);
    return { ships: [{ group: g, cls: buildingId }], selected: buildingId, focus: () => {} };
  }

  // ?debug: ship-frame axes (X red = port, Y green = dorsal, Z blue = bow), a
  // 1 m / 5 m keel grid, engine and light anchors, hangar box and mouth.
  function debugOverlay(s) {
    const o = new THREE.Group();
    const e = s.envelope, inv = 1 / s.scaleCorrection;
    const min = e.min.clone().multiplyScalar(inv), max = e.max.clone().multiplyScalar(inv), size = max.clone().sub(min);
    const L = Math.max(size.x, size.z);
    const axes = new THREE.AxesHelper(L * 0.6);
    axes.material.depthTest = false; axes.renderOrder = 10;
    o.add(axes);
    const n = Math.ceil(L / 5) * 5 + 10;
    const grid = new THREE.GridHelper(n, n, '#ff8a4c', '#3a4150');
    grid.position.y = min.y;
    o.add(grid);
    const box = new THREE.Box3Helper(new THREE.Box3(min, max), '#62dcff');
    o.add(box);
    const dot = (p, color, r) => { const m = new THREE.Mesh(new THREE.SphereGeometry(r, 12, 8), new THREE.MeshBasicMaterial({ color, depthTest: false })); m.position.copy(p); m.renderOrder = 11; o.add(m); };
    for (const en of s.engines) dot(en.p, '#ff2020', Math.max(0.15, en.radius * 0.25));
    for (const l of s.lights) dot(l.p, l.color === 'red' ? '#ff3030' : l.color === 'green' ? '#30ff60' : '#ffffff', Math.max(0.12, L * 0.004));
    for (const l of s.interiorLights || []) dot(l.p, '#ffc070', Math.max(0.2, L * 0.006));
    const h = s.anchors.hangar;
    if (h) {
      const hb = new THREE.Box3().setFromCenterAndSize(h.p, new THREE.Vector3(...h.size));
      const hh = new THREE.Box3Helper(hb, '#ff5a14'); hh.material.depthTest = false; hh.renderOrder = 10; o.add(hh);
    }
    const mo = s.anchors.hangarMouth;
    if (mo) o.add(new THREE.ArrowHelper((mo.dir || new THREE.Vector3(0, 0, 1)).clone().normalize(), mo.p, L * 0.25, '#ffd000'));
    return o;
  }

  // --- lineup: scale chart. Sterns aligned at x = 0 on a shared metre ruler,
  // one row per class (smallest in front), bows toward +X. The annotation (callouts with
  // leader lines on the stern side, the ruler) is screen-space (lib/chart.js), so it stays
  // legible at any zoom. ?lineup=small frames only the small ships, the slot cube and the
  // crew member, like the enlarged inset of a technical drawing.
  function setupLineup() {
    const small = params.get('lineup') === 'small';
    camera.fov = parseFloat(params.get('fov') || '24');
    camera.updateProjectionMatrix();
    const ships = [];
    const gap = 24;
    // one row per class, plus the civil ship's troop variant (4 slots like the cargo ship, its own shape)
    // (the ground units come first: a 7 m vehicle reads only in the front row, beside the slot cube and the crew member)
    const rows = LINEUP.flatMap((cls) => (cls === 'freighter' ? [{ cls }, { cls, variant: 'troops' }] : [{ cls }]));
    const built = rows.map(({ cls, variant }) => buildShip(cls, palette, variant ? { variant } : {}));
    const side = Math.cbrt(SLOT_VOLUME);
    const chart = createChartOverlay(container);
    overlays.push((cam) => chart.update(cam, renderer.domElement.clientWidth || w, renderer.domElement.clientHeight || h));
    let z = side / 2 + gap; // row 0 is the slot cube at z = 0
    let maxL = 0;
    built.forEach((g, i) => {
      const { cls, variant } = rows[i];
      const s = g.userData.ship, spec = CLASSES[cls];
      const L = s.envelope.size.z, B = s.envelope.size.x, H = s.envelope.size.y;
      g.rotation.y = Math.PI / 2; // bow -> +X
      const rowZ = -(z + B / 2);
      z += B + gap;
      maxL = Math.max(maxL, L);
      // local envelope min.z (stern) lands on x = 0; bottom on y = 0
      g.position.set(-s.envelope.min.z, -s.envelope.min.y, rowZ + s.envelope.center.x);
      scene.add(g);
      effects.push(attachEffects(g, { power: 0.6 }));
      // the carrier's open bays show its hangar load, as everywhere else
      if (cls === 'carrier' && s.anchors.hangarDeck) effects.push(...parkInHangar(g, { buildShip, palette, attachEffects }).effects);
      ships.push({ group: g, cls, variant, center: new THREE.Vector3(L / 2, H / 2, rowZ), length: L, beam: B, height: H });
      const slots = sizeLabel(spec, { long: !spec.size }); // '12 slots', 'carries 50 slots', 'ground unit, true size'
      chart.callout(new THREE.Vector3(-1, H / 2, rowZ), variant === 'troops' ? `${spec.label} (troops)` : spec.label, `${L.toFixed(1)} m · ${slots}`);
    });
    // reference cube: one hangar slot (SLOT_VOLUME m^3) in the front row, stern face on the zero line
    const cube = new THREE.Mesh(new THREE.BoxGeometry(side, side, side), new THREE.MeshBasicMaterial({ color: '#d9dde3', transparent: true, opacity: 0.07, depthWrite: false }));
    cube.add(new THREE.LineSegments(new THREE.EdgesGeometry(cube.geometry), new THREE.LineBasicMaterial({ color: '#c3c8d0', transparent: true, opacity: 0.75 })));
    cube.position.set(side / 2, side / 2, 0);
    scene.add(cube);
    chart.callout(new THREE.Vector3(0, side * 0.7, 0), '1 hangar slot', `${side.toFixed(2)} m cube · ${SLOT_VOLUME.toLocaleString('en-US')} m³`);
    // a 1.8 m crew member standing on the zero line in front of the cube: the same human
    // scale every hull is detailed to
    const person = new THREE.Group();
    const suit = new THREE.MeshStandardMaterial({ color: '#c9ccd2', roughness: 0.7 });
    const body = new THREE.Mesh(new THREE.CapsuleGeometry(0.22, 1.05, 4, 12), suit);
    body.position.y = 0.22 + 1.05 / 2 + 0.02;
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.15, 16, 12), suit);
    head.position.y = 1.62;
    person.add(body, head);
    person.traverse((o) => { o.castShadow = true; });
    const personAt = new THREE.Vector3(0.6, 0, side / 2 + 2.5);
    person.position.copy(personAt);
    scene.add(person);
    chart.callout(personAt.clone().setY(1.8), 'Crew member', '1.8 m');
    // metre ruler along the front edge: a tick every 10 m up to 100 m, then every 100 m
    const zR = side / 2 + 8;
    const rulerEnd = Math.ceil(maxL / 100) * 100;
    const marks = [];
    for (let m = 0; m <= 100; m += 10) marks.push({ m, size: m % 100 === 0 ? 2 : m % 50 === 0 ? 1 : 0, label: `${m}${m === 0 ? ' m' : ''}`, priority: m % 100 === 0 ? 3 : m % 50 === 0 ? 2 : 1, group: m % 50 ? 'fine' : undefined });
    for (let m = 200; m <= rulerEnd; m += 100) marks.push({ m, size: 2, label: `${m}`, priority: 3 });
    chart.ruler({ origin: new THREE.Vector3(0, 0, zR), axis: new THREE.Vector3(1, 0, 0), toward: new THREE.Vector3(0, 0, 1), length: rulerEnd, marks });
    // measuring grid under the chart: 10 m / 100 m lines, starting on the zero line
    const depth = z + zR + 20, width = rulerEnd + 60;
    const grid = measuringGrid(width, depth);
    grid.position.set(width / 2 - 20, 0, zR + 10 - depth / 2);
    scene.add(grid);
    const box = new THREE.Box3();
    ships.forEach((s) => box.expandByObject(s.group));
    lighting.fitShadow(box);
    // default: the whole chart; ?lineup=small: the small ships, the slot cube and the crew member.
    // Pixel margins keep room for the callout column (stern side) and the ruler labels, and in the
    // interactive page clear of the overlay panels (measured once they are filled: reframe()).
    const framed = small ? ships.filter((s) => s.cls !== 'carrier') : ships;
    // frame the hulls' silhouettes (a few hundred vertices per ship), not their bounding boxes:
    // the carrier's box corners reach far above its deck line
    const pts = [];
    scene.updateMatrixWorld(true);
    for (const s of framed) s.group.traverse((o) => {
      if (!o.isMesh || !o.userData.hull) return;
      const pos = o.geometry.attributes.position, step = Math.max(1, Math.floor(pos.count / 400));
      for (let k = 0; k < pos.count; k += step) pts.push(new THREE.Vector3().fromBufferAttribute(pos, k).applyMatrix4(o.matrixWorld));
    });
    pts.push(new THREE.Vector3(0, 0, zR), new THREE.Vector3(small ? 100 : rulerEnd, 0, zR), new THREE.Vector3(side, side, -side / 2));
    const dir = small ? new THREE.Vector3(-0.42, 0.62, 1).normalize() : new THREE.Vector3(-0.3, 1.3, 1).normalize();
    const reframe = () => {
      const W = renderer.domElement.clientWidth || w, Hh = renderer.domElement.clientHeight || h;
      const col = Math.min(225, W * 0.3); // callout column
      const margins = { l: col, r: 36, t: 24, b: 40 };
      const rect = (sel) => { const e = document.querySelector(sel); if (!e || e.hidden || !e.offsetParent) return null; const r = e.getBoundingClientRect(); return r.width && r.height ? r : null; };
      if (!still) {
        const head = rect('#ui header'), reg = rect('#registry-wrap'), sheet = rect('#sheet'), tog = rect('#ui .toggles');
        if (head) margins.t = Math.max(margins.t, head.bottom + 16);
        if (W > 860) {
          if (sheet) margins.r = Math.max(margins.r, W - sheet.left + 16);
          if (reg) margins.b = Math.max(margins.b, Hh - reg.top + 16);
          if (tog) margins.b = Math.max(margins.b, Hh - tog.top + 24);
        } else {
          const low = Math.min(reg?.top ?? Hh, sheet?.top ?? Hh);
          margins.b = Math.max(margins.b, Hh - low + 12);
        }
      }
      controls.target.copy(frameView(camera, pts, dir, margins, W, Hh));
      chart.bounds({ t: still ? 0 : margins.t - 16, b: still ? 0 : margins.b - 16 });
      if (inset) {
        // the detail box sits in the empty grid between the carrier row and the ruler
        const aw = W - margins.l - margins.r, ah = Hh - margins.t - margins.b;
        const iw = Math.round(aw * 0.31), ih = Math.round(iw * 0.86);
        inset.rect = { x: Math.round(margins.l + aw * 0.36), y: Math.round(margins.t + ah * 0.43), w: iw, h: ih };
        inset.camera.aspect = iw / ih;
        inset.camera.updateProjectionMatrix();
        frameView(inset.camera, smallPts, smallDir, { l: 10, r: 10, t: 34, b: 10 }, iw, ih);
        Object.assign(inset.el.style, { left: `${inset.rect.x}px`, top: `${inset.rect.y}px`, width: `${iw}px`, height: `${ih}px` });
      }
    };
    // Default view: a detail box (like the enlarged inset of a technical drawing) shows the
    // lineup=small framing of the small ships, the slot cube and the crew member, which are only
    // 20-40 px long at the full 900 m chart scale. A second render of the same scene into a
    // corner viewport, drawn after the main frame (see frame()).
    const smallPts = [];
    let inset = null;
    if (!small) {
      for (const sh of ships) if (sh.cls !== 'carrier') sh.group.traverse((o) => {
        if (!o.isMesh || !o.userData.hull) return;
        const pos = o.geometry.attributes.position, step = Math.max(1, Math.floor(pos.count / 400));
        for (let k = 0; k < pos.count; k += step) smallPts.push(new THREE.Vector3().fromBufferAttribute(pos, k).applyMatrix4(o.matrixWorld));
      });
      smallPts.push(new THREE.Vector3(0, 0, zR), new THREE.Vector3(side, side, -side / 2)); // (the ruler is an overlay: not in the inset)
      const el = document.createElement('div');
      el.className = 'lineup-inset';
      el.innerHTML = '<span>Detail · small ships, 1 slot, crew (rows as in the chart) · <a href="?lineup=small#lineup">lineup=small</a></span>';
      container.appendChild(el);
      inset = { camera: new THREE.PerspectiveCamera(camera.fov, 1, 0.5, 250000), el, rect: null };
    }
    const smallDir = new THREE.Vector3(-0.7, 0.75, 1).normalize();
    reframe();
    // ghost hangar with the 50-fighter load (toggle, or ?hangar=1)
    const carrierShip = ships.find((s) => s.cls === 'carrier');
    const fighterShip = ships.find((s) => s.cls === 'fighter');
    const hangarViz = carrierShip && fighterShip ? hangarLoadViz(carrierShip.group, fighterShip.group.userData.ship.envelope.size) : null;
    if (hangarViz && params.has('hangar') && params.get('hangar') !== '0') hangarViz.visible = true;
    return {
      ships, selected: small ? 'fighter' : 'carrier', lineupSmall: small, reframe, inset,
      focus(cls) {
        const s = ships.find((q) => q.cls === cls);
        if (!s) return;
        flyTo(s.center, Math.max(40, s.length * 2.4), new THREE.Vector3(-0.3, 0.55, 1));
      },
      toggle(key, on) { if (key === 'hangar' && hangarViz) hangarViz.visible = on; },
    };
  }

  // --- fleet: carrier group in orbit above the planet -----------------------
  function setupFleet() {
    const planet = createPlanet(scene);
    tickers.push((t) => planet.update(t, camera));
    const fleet = buildFleet({ palette, buildShip, attachEffects, buildBuilding, buildings: fleetBuildings.filter((id) => !LOAD_ERRORS[id]) });
    scene.add(fleet.root);
    effects.push(...fleet.effects);
    tickers.push((t, dt) => fleet.update(t, dt));
    lighting.fitShadow(fleet.shadowBox);
    const shots = fleet.shots;
    const shot = shots[params.get('shot') || 'hero'] || shots.hero;
    // ?cam=x,y,z&target=x,y,z (carrier frame, metres) overrides the named shot for look-dev
    const vec = (k) => { const v = (params.get(k) || '').split(',').map(Number); return v.length === 3 && v.every(Number.isFinite) ? new THREE.Vector3(...v) : null; };
    camera.position.copy(vec('cam') || shot.pos);
    controls.target.copy(vec('target') || shot.target);
    // a shot may choose its lens (?fov= still wins)
    if (shot.fov && !params.get('fov')) { camera.fov = shot.fov; camera.updateProjectionMatrix(); }
    // ?level=deg overrides the shot's horizon tilt (see levelHorizon)
    const level = params.has('level') ? parseFloat(params.get('level')) : shot.horizon;
    // The interactive page lays its panels over the frame (title, ship classes lower left, spec
    // sheet on the right, toggles bottom centre), right where a still keeps its counterweights
    // (the foreground escort, the limb). Measure the clear area the way the lineup does and shift
    // the lens (setViewOffset: an off-axis projection, the pose is unchanged) so the still's
    // frame is centred in it, scaled so its central 80 % fits (never below 0.55, a wide shot
    // rather than a thumbnail). The rest of the canvas shows more of the same scene. Stills keep
    // the plain lens; re-applied on resize.
    const reframe = () => {
      if (still) return;
      const W = renderer.domElement.clientWidth || w, Hh = renderer.domElement.clientHeight || h;
      const rect = (sel) => { const e = document.querySelector(sel); if (!e || e.hidden || !e.offsetParent) return null; const r = e.getBoundingClientRect(); return r.width && r.height ? r : null; };
      const head = rect('#ui header'), reg = rect('#registry-wrap'), sheet = rect('#sheet'), tog = rect('#ui .toggles');
      const top = head ? head.bottom + 8 : 0;
      const areas = [];
      if (W > 860) {
        const right = sheet ? sheet.left - 8 : W, bottom = tog ? tog.top - 8 : Hh;
        areas.push({ l: reg ? reg.right + 8 : 0, t: top, r: right, b: bottom }); // beside the class list
        areas.push({ l: 0, t: top, r: right, b: reg ? Math.min(reg.top - 8, bottom) : bottom }); // above it
      } else {
        areas.push({ l: 0, t: top, r: W, b: Math.min(reg?.top ?? Hh, sheet?.top ?? Hh) - 8 });
      }
      let best = null;
      for (const a of areas) {
        const fit = Math.min((a.r - a.l) / W, (a.b - a.t) / Hh);
        if (fit > 0 && (!best || fit > best.fit)) best = { ...a, fit };
      }
      if (!best) { camera.clearViewOffset(); return; }
      const k = THREE.MathUtils.clamp(best.fit / 0.8, 0.55, 1);
      const cx = (best.l + best.r) / 2, cy = (best.t + best.b) / 2;
      camera.setViewOffset(W, Hh, W / 2 - cx / k, Hh / 2 - cy / k, W / k, Hh / k);
      camera.updateProjectionMatrix();
    };
    return {
      horizon: Number.isFinite(level) ? level : null,
      reframe, lensReframe: true, // only the lens moves: safe during flights and follows
      ships: fleet.ships, selected: 'carrier',
      focus(cls) {
        const s = fleet.ships.find((q) => q.cls === cls);
        if (!s) return;
        const c = new THREE.Box3().setFromObject(s.group).getCenter(new THREE.Vector3());
        flyTo(c, Math.max(35, s.group.userData.ship.envelope.size.z * 1.7), new THREE.Vector3(0.6, 0.3, 0.8), s.group);
      },
      toggle(key, on) { fleet.toggle?.(key, on); },
    };
  }

  // --- camera flights -------------------------------------------------------
  let flight = null;
  function flyTo(target, distance, dir, follow = null) {
    const d = dir.clone().normalize();
    flight = {
      t: 0, fromPos: camera.position.clone(), fromTarget: controls.target.clone(),
      toTarget: target.clone(), toPos: target.clone().addScaledVector(d, distance), follow,
      offset: follow ? target.clone().sub(follow.getWorldPosition(new THREE.Vector3())) : null,
    };
  }

  // Neutral measuring grid: 10 m minor lines that fade out once they are closer than ~10 px
  // on screen, 100 m major lines, soft edges. Low-contrast grey so it reads as a drawing
  // sheet under the ships, not as a display.
  function measuringGrid(width, depth) {
    const g = new THREE.PlaneGeometry(width, depth);
    g.rotateX(-Math.PI / 2);
    const m = new THREE.ShaderMaterial({
      transparent: true, depthWrite: false, side: THREE.DoubleSide,
      vertexShader: `varying vec2 vP; varying vec2 vUv; void main(){ vUv = uv; vP = (modelMatrix * vec4(position, 1.0)).xz; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
      fragmentShader: `
        varying vec2 vP; varying vec2 vUv;
        float line(vec2 p, float s, float w){ vec2 g = abs(fract(p / s - 0.5) - 0.5) * s / fwidth(p); return 1.0 - clamp(min(g.x, g.y) - w, 0.0, 1.0); }
        void main(){
          float px = max(fwidth(vP).x, fwidth(vP).y);          // metres per pixel here
          float minorFade = smoothstep(4.0, 12.0, 10.0 / px);   // 10 m lines only when >= ~10 px apart
          float minor = line(vP, 10.0, 0.0) * minorFade, major = line(vP, 100.0, 0.0);
          vec2 e = min(vUv, 1.0 - vUv); float fade = smoothstep(0.0, 0.06, min(e.x, e.y));
          float a = max(minor * 0.045, major * 0.11) * fade;
          gl_FragColor = vec4(vec3(0.62, 0.64, 0.67), a);
          // no-ops into the composer's linear targets; encode it when drawn straight to the canvas
          // (the lineup's detail inset)
          #include <tonemapping_fragment>
          #include <colorspace_fragment>
        }`,
    });
    const mesh = new THREE.Mesh(g, m);
    mesh.renderOrder = -1;
    return mesh;
  }

  function hangarLoadViz(carrierGroup, fighterEnv) {
    const s = carrierGroup.userData.ship;
    const h = s.anchors.hangar;
    if (!h) return null;
    const sc = s.scaleCorrection;
    const size = new THREE.Vector3(...h.size).multiplyScalar(1);
    const group = new THREE.Group();
    group.visible = false;
    const shell = new THREE.Mesh(new THREE.BoxGeometry(size.x, size.y, size.z), new THREE.MeshBasicMaterial({ color: '#b4bac3', wireframe: true, transparent: true, opacity: 0.35 }));
    group.add(shell);
    // lay out 50 fighter envelopes in two tiers
    const fe = fighterEnv.clone().divideScalar(sc);
    const clear = 2 / sc;
    const cols = Math.floor((size.x - clear) / (fe.x + clear));
    const rows = Math.floor((size.z - clear) / (fe.z + clear));
    const boxGeo = new THREE.BoxGeometry(fe.x, fe.y, fe.z);
    const inst = new THREE.InstancedMesh(boxGeo, new THREE.MeshBasicMaterial({ color: '#dfe3e9', transparent: true, opacity: 0.3, depthWrite: false }), 50);
    const m = new THREE.Matrix4();
    let n = 0;
    for (let tier = 0; tier < 2 && n < 50; tier++) for (let r = 0; r < rows && n < 50; r++) for (let c = 0; c < cols && n < 50; c++) {
      m.makeTranslation(
        -size.x / 2 + clear + fe.x / 2 + c * (fe.x + clear),
        -size.y / 2 + clear / 2 + fe.y / 2 + tier * (fe.y + clear / 2),
        -size.z / 2 + clear + fe.z / 2 + r * (fe.z + clear));
      inst.setMatrixAt(n++, m);
    }
    inst.count = n;
    group.add(inst);
    group.position.copy(h.p);
    carrierGroup.add(group);
    return group;
  }

  // --- selection by double-click -------------------------------------------
  const ray = new THREE.Raycaster();
  renderer.domElement.addEventListener('dblclick', (ev) => {
    const r = renderer.domElement.getBoundingClientRect();
    const p = new THREE.Vector2(((ev.clientX - r.left) / r.width) * 2 - 1, -((ev.clientY - r.top) / r.height) * 2 + 1);
    ray.setFromCamera(p, camera);
    const hits = ray.intersectObjects(world.ships.map((s) => s.group), true);
    if (!hits.length) return;
    let o = hits[0].object;
    while (o && !o.userData.ship) o = o.parent;
    if (!o) return;
    ui.select(o.userData.ship.cls);
    const s = world.ships.find((q) => q.group === o);
    const c = new THREE.Box3().setFromObject(o).getCenter(new THREE.Vector3());
    flyTo(c, Math.max(30, o.userData.ship.envelope.size.z * 1.7), camera.position.clone().sub(c), s?.group);
  });

  function resize() {
    if (params.get('w')) return;
    const W = container.clientWidth || innerWidth, H = container.clientHeight || innerHeight;
    renderer.setSize(W, H); composer.setSize(W, H); labelRenderer.setSize(W, H);
    grainPass.uniforms.uAspect.value = W / H;
    bloom.setSize(W, H);
    camera.aspect = W / H; camera.updateProjectionMatrix();
    if (world.lensReframe || (!flight && !world.followTarget)) world.reframe?.();
  }
  addEventListener('resize', resize);

  // Roll the camera about its view axis so the planet's up direction (and so the horizon near
  // the frame centre) leans at most maxTilt degrees; k blends the correction in and out.
  let levelOn = true, levelK = 1;
  const _up = new THREE.Vector3(), _q = new THREE.Quaternion();
  function levelHorizon(maxTilt, k) {
    camera.updateMatrixWorld();
    _up.copy(camera.position).sub(ENV.planet.center).normalize();
    _up.applyQuaternion(_q.copy(camera.quaternion).invert()); // camera space
    const tilt = Math.atan2(_up.x, _up.y); // lean of "up" to the right of vertical
    const keep = Math.sign(tilt) * Math.min(Math.abs(tilt), THREE.MathUtils.degToRad(maxTilt));
    camera.rotateZ(-(tilt - keep) * k);
  }

  const timer = new THREE.Timer();
  let frames = 0;
  let simT = fixedTime ?? 0;
  function frame(now) {
    timer.update(now);
    const dt = Math.min(timer.getDelta(), 0.05);
    simT = fixedTime ?? simT + dt;
    if (flight) {
      flight.t = Math.min(1, flight.t + dt / 1.6);
      const e = flight.t < 0.5 ? 4 * flight.t ** 3 : 1 - (-2 * flight.t + 2) ** 3 / 2;
      let toTarget = flight.toTarget, toPos = flight.toPos;
      if (flight.follow) {
        const wp = flight.follow.getWorldPosition(new THREE.Vector3()).add(flight.offset);
        const delta = wp.clone().sub(flight.toTarget);
        toTarget = wp; toPos = flight.toPos.clone().add(delta);
      }
      controls.target.lerpVectors(flight.fromTarget, toTarget, e);
      camera.position.lerpVectors(flight.fromPos, toPos, e);
      if (flight.t >= 1) {
        if (flight.follow) world.followTarget = { obj: flight.follow, offset: flight.offset };
        flight = null;
      }
    }
    for (const tk of tickers) tk(simT, dt);
    if (!flight && world.followTarget) {
      // keep a followed ship centred as it moves
      const wp = world.followTarget.obj.getWorldPosition(new THREE.Vector3()).add(world.followTarget.offset);
      const delta = wp.sub(controls.target);
      controls.target.add(delta); camera.position.add(delta);
    }
    controls.update();
    // horizon levelling (fleet shots): the planet sits 16 deg off the fleet's nadir, so a camera
    // rolled only by the carrier's up vector sees the horizon tilted 12-18 deg. A shot can ask for
    // at most `horizon` degrees of tilt: the camera is rolled about its view axis after the
    // controls placed it. It holds until the viewer first drags, then eases out.
    if (world.horizon != null && ENV.planet) {
      if (!levelOn) levelK = Math.max(0, levelK - dt / 0.6);
      if (levelK > 0) levelHorizon(world.horizon, levelK);
    }
    const dist = camera.position.distanceTo(controls.target);
    camera.near = THREE.MathUtils.clamp(dist * 0.01, 0.05, 20);
    camera.updateProjectionMatrix();
    camera.updateMatrixWorld();
    for (const o of overlays) o(camera);
    sky.update(simT, camera, renderer);
    for (const e of effects) e.update(simT, renderer.domElement.height, camera.projectionMatrix.elements[5]);
    if (!still) grainPass.uniforms.uSeed.value = frames % 61;
    if (screenAO) screenAO.render(dist);
    composer.render();
    if (world.inset?.rect) {
      // lineup detail box: the same scene through the inset camera, into its corner of the canvas
      const r = world.inset.rect, H0 = renderer.domElement.clientHeight || h;
      renderer.setScissorTest(true);
      renderer.setScissor(r.x, H0 - r.y - r.h, r.w, r.h);
      renderer.setViewport(r.x, H0 - r.y - r.h, r.w, r.h);
      if (screenAO) screenAO.enabled = false; // the AO texture belongs to the main view
      renderer.render(scene, world.inset.camera);
      if (screenAO) screenAO.enabled = true;
      renderer.setScissorTest(false);
      renderer.setViewport(0, 0, renderer.domElement.clientWidth || w, H0);
    }
    labelRenderer.render(scene, camera);
    frames++;
    if (frames === 2) { const l = document.getElementById('loading'); if (l) { if (still) l.hidden = true; else l.classList.add('done'); } }
    // ready after the third frame (stills stop there; the interactive page keeps animating)
    if (frames === 3) { window.__ready = true; document.body.dataset.ready = '1'; if (still) return; }
    requestAnimationFrame(frame);
  }
  renderer.domElement.addEventListener('pointerdown', () => { world.followTarget = null; flight = null; levelOn = false; });
  window.__scene = { scene, camera, renderer, world, controls, composer, screenAO };
  frame();
}
