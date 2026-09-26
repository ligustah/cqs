// CQS reboot — orbital fleet scene.
// Modes (query ?mode=… or #token): fleet (default) | lineup | ship | check
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';

import { createPalette } from './lib/materials.js';
import { attachEffects } from './lib/effects.js';
import { CLASSES, SLOT_VOLUME, carrierLoads } from './lib/scale.js';
import { hangarInsideFraction } from './lib/hangar.js';
import { buildShip, loadShips, setShipContext, LOAD_ERRORS, ORDER } from './ships/index.js';
import { loadPatinaLibrary, proceduralStandIn } from './lib/patina.js';
import { panelSet } from './lib/textures.js';
import { createLighting } from './env/lighting.js';
import { createSky } from './env/sky.js';
import { createPlanet } from './env/planet.js';
import { buildFleet } from './fleet.js';
import { createUI } from './ui.js';

const params = new URLSearchParams(location.search);
const hash = location.hash.replace('#', '');
const HASH_MODES = ['fleet', 'lineup'];
const mode = params.get('mode') || (HASH_MODES.includes(hash) ? hash : (ORDER.includes(hash) ? 'ship' : 'fleet'));
const still = params.has('still');
const fixedTime = params.has('t') ? parseFloat(params.get('t')) : null;

window.__report = null;
window.__ready = false;

const palette = createPalette();
// fal PATINA tiling PBR sets (assets/materials); ?standin uses procedural textures for testing
const library = await loadPatinaLibrary();
if (!Object.keys(library).length && params.has('standin')) library.hull = proceduralStandIn(panelSet({ seed: 7, style: 'hull' }));
setShipContext({ library });
const onlyShip = mode === 'ship' ? [params.get('ship') || (ORDER.includes(hash) ? hash : 'fighter')] : ORDER;
await loadShips(onlyShip);

// ---------------------------------------------------------------------------
// check mode: build every ship, report envelopes vs. the game's size stat
// ---------------------------------------------------------------------------
if (mode === 'check') {
  const rows = [];
  const env = {};
  let hangar = null, hangarInside = null;
  for (const cls of ORDER) {
    const t0 = performance.now();
    const g = buildShip(cls, palette);
    const s = g.userData.ship;
    env[cls] = s.envelope.size.clone();
    if (cls === 'carrier' && s.anchors.hangar) {
      hangar = new THREE.Vector3(...s.anchors.hangar.size).multiplyScalar(s.scaleCorrection);
      const r = hangarInsideFraction(g, s.anchors.hangar);
      hangarInside = { fraction: +r.fraction.toFixed(3), samples: r.samples, misses: r.misses };
    }
    rows.push({
      cls, name: s.meta?.name, size: CLASSES[cls].size,
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
  renderer.setPixelRatio(still ? 1 : Math.min(devicePixelRatio, 2));
  renderer.setSize(w, h);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.AgXToneMapping;
  renderer.toneMappingExposure = parseFloat(params.get('exposure') || '1.0');
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

  const lighting = createLighting(renderer, scene);
  const sky = createSky(scene);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.06;
  controls.rotateSpeed = 0.6;
  controls.zoomSpeed = 0.9;

  const composer = new EffectComposer(renderer, new THREE.WebGLRenderTarget(w, h, { type: THREE.HalfFloatType, samples: 4 }));
  composer.setPixelRatio(renderer.getPixelRatio());
  composer.addPass(new RenderPass(scene, camera));
  const bloom = new UnrealBloomPass(new THREE.Vector2(w, h), 0.55, 0.5, 1.6);
  composer.addPass(bloom);
  composer.addPass(new OutputPass());

  const effects = [];
  const tickers = [];
  let world = null; // { ships:[{group, cls}], focus(cls) , bounds }

  if (mode === 'ship') world = setupShipStudio();
  else if (mode === 'lineup') world = setupLineup();
  else world = setupFleet();

  const ui = createUI({
    mode, still, world, classes: CLASSES, order: ORDER,
    onMode: (m) => { location.hash = m; location.reload(); },
    onFocus: (cls) => world.focus?.(cls),
    onToggle: (key, on) => { if (key === 'orbit') { controls.autoRotate = on; controls.autoRotateSpeed = 0.35; } else world.toggle?.(key, on); },
  });

  // --- ship studio: one ship, framed for inspection / screenshots ----------
  function setupShipStudio() {
    const cls = params.get('ship') || (ORDER.includes(hash) ? hash : 'fighter');
    const g = buildShip(cls, palette, { variant: params.get('variant') || undefined });
    const s = g.userData.ship;
    g.position.sub(s.envelope.center);
    scene.add(g);
    effects.push(attachEffects(g));
    const box = new THREE.Box3().setFromObject(g);
    lighting.fitShadow(box);
    const diag = s.envelope.size.length();
    const az = THREE.MathUtils.degToRad(parseFloat(params.get('az') ?? '35'));
    const el = THREE.MathUtils.degToRad(parseFloat(params.get('el') ?? '18'));
    const dist = diag * 1.15 * parseFloat(params.get('dist') ?? '1');
    camera.position.set(Math.sin(az) * Math.cos(el), Math.sin(el), Math.cos(az) * Math.cos(el)).multiplyScalar(dist);
    controls.target.set(0, 0, 0);
    if (params.has('planet')) createPlanet(scene);
    return { ships: [{ group: g, cls }], selected: cls, focus: () => {} };
  }

  // --- lineup: scale chart. Sterns aligned at x = 0 on a shared metre ruler,
  // one row per class (smallest in front), bows toward +X.
  function setupLineup() {
    camera.fov = parseFloat(params.get('fov') || '24');
    camera.updateProjectionMatrix();
    const ships = [];
    const gap = 16;
    const built = ORDER.map((cls) => buildShip(cls, palette));
    const side = Math.cbrt(SLOT_VOLUME);
    let z = side / 2 + gap; // row 0 is the slot cube at z = 0
    let maxL = 0;
    built.forEach((g, i) => {
      const s = g.userData.ship;
      const L = s.envelope.size.z, B = s.envelope.size.x, H = s.envelope.size.y;
      g.rotation.y = Math.PI / 2; // bow -> +X
      const rowZ = -(z + B / 2);
      z += B + gap;
      maxL = Math.max(maxL, L);
      // local envelope min.z (stern) lands on x = 0; bottom on y = 0
      g.position.set(-s.envelope.min.z, -s.envelope.min.y, rowZ + s.envelope.center.x);
      scene.add(g);
      effects.push(attachEffects(g, { power: 0.6 }));
      ships.push({ group: g, cls: ORDER[i], center: new THREE.Vector3(L / 2, H / 2, rowZ), length: L, beam: B });
      const label = document.createElement('div');
      label.className = 'ship-label row';
      label.innerHTML = `<b>${CLASSES[ORDER[i]].label}</b><span>${L.toFixed(1)} m · ${CLASSES[ORDER[i]].size ? CLASSES[ORDER[i]].size + ' slot' + (CLASSES[ORDER[i]].size > 1 ? 's' : '') : 'hangar ' + CLASSES[ORDER[i]].capacity + ' slots'}</span>`;
      const lo = new CSS2DObject(label);
      lo.center.set(0, 0.5);
      lo.position.set(L + 8, H / 2, rowZ);
      scene.add(lo);
    });
    // reference cube: one hangar slot (800 m^3) in the front row
    const cube = new THREE.Mesh(new THREE.BoxGeometry(side, side, side), new THREE.MeshBasicMaterial({ color: '#ff5a14', transparent: true, opacity: 0.2, depthWrite: false }));
    cube.add(new THREE.LineSegments(new THREE.EdgesGeometry(cube.geometry), new THREE.LineBasicMaterial({ color: '#ff8a4c' })));
    cube.position.set(side / 2, side / 2, 0);
    scene.add(cube);
    const cubeLabel = document.createElement('div');
    cubeLabel.className = 'ship-label row';
    cubeLabel.innerHTML = `<b>1 hangar slot</b><span>${side.toFixed(2)} m cube = ${SLOT_VOLUME} m³ of parking envelope</span>`;
    const cl = new CSS2DObject(cubeLabel);
    cl.center.set(0, 0.5);
    cl.position.set(side + 8, side / 2, 0);
    scene.add(cl);
    // grid + ruler
    const depth = z + 40, width = maxL + 140;
    const grid = measuringGrid(width, depth);
    grid.position.set(width / 2 - 40, 0, -depth / 2 + side / 2 + 24);
    scene.add(grid);
    for (let m = 0; m <= maxL + 1; m += 25) {
      const tick = document.createElement('div');
      tick.className = 'ruler-tick';
      tick.textContent = `${m} m`;
      const to = new CSS2DObject(tick);
      to.center.set(0, 0);
      to.position.set(m, 0, side / 2 + 10);
      scene.add(to);
    }
    const box = new THREE.Box3();
    ships.forEach((s) => box.expandByObject(s.group));
    lighting.fitShadow(box);
    box.expandByObject(cube);
    const center = box.getCenter(new THREE.Vector3());
    const span = Math.max(box.max.x - box.min.x, box.max.z - box.min.z);
    controls.target.copy(center).add(new THREE.Vector3(span * 0.06, 0, 0));
    camera.position.copy(center).add(new THREE.Vector3(-span * 0.55, span * 1.35, span * 1.9));
    // ghost hangar with the 50-fighter load
    const carrierShip = ships.find((s) => s.cls === 'carrier');
    const hangarViz = carrierShip ? hangarLoadViz(carrierShip.group, built[0].userData.ship.envelope.size) : null;
    return {
      ships, selected: 'carrier',
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
    const fleet = buildFleet({ palette, buildShip, attachEffects });
    scene.add(fleet.root);
    effects.push(...fleet.effects);
    tickers.push((t, dt) => fleet.update(t, dt));
    lighting.fitShadow(fleet.shadowBox);
    const shots = fleet.shots;
    const shot = shots[params.get('shot') || 'hero'] || shots.hero;
    camera.position.copy(shot.pos);
    controls.target.copy(shot.target);
    return {
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

  function measuringGrid(width, depth) {
    const g = new THREE.PlaneGeometry(width, depth);
    g.rotateX(-Math.PI / 2);
    const m = new THREE.ShaderMaterial({
      transparent: true, depthWrite: false, side: THREE.DoubleSide,
      uniforms: { uSize: { value: new THREE.Vector2(width, depth) } },
      vertexShader: `varying vec2 vP; varying vec2 vUv; void main(){ vUv = uv; vP = (modelMatrix * vec4(position, 1.0)).xz; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
      fragmentShader: `
        varying vec2 vP; varying vec2 vUv; uniform vec2 uSize;
        float line(vec2 p, float s, float w){ vec2 g = abs(fract(p / s - 0.5) - 0.5) * s / fwidth(p); return 1.0 - clamp(min(g.x, g.y) - w, 0.0, 1.0); }
        void main(){
          float minor = line(vP, 10.0, 0.0), major = line(vP, 50.0, 0.5);
          vec2 e = min(vUv, 1.0 - vUv); float fade = smoothstep(0.0, 0.12, min(e.x, e.y));
          vec3 c = mix(vec3(0.35, 0.55, 1.0), vec3(1.0, 0.45, 0.15), major);
          float a = max(minor * 0.18, major * 0.45) * fade;
          gl_FragColor = vec4(c * 1.4, a);
        }`,
    });
    return new THREE.Mesh(g, m);
  }

  function hangarLoadViz(carrierGroup, fighterEnv) {
    const s = carrierGroup.userData.ship;
    const h = s.anchors.hangar;
    if (!h) return null;
    const sc = s.scaleCorrection;
    const size = new THREE.Vector3(...h.size).multiplyScalar(1);
    const group = new THREE.Group();
    group.visible = false;
    const shell = new THREE.Mesh(new THREE.BoxGeometry(size.x, size.y, size.z), new THREE.MeshBasicMaterial({ color: '#ff5a14', wireframe: true, transparent: true, opacity: 0.35 }));
    group.add(shell);
    // lay out 50 fighter envelopes in two tiers
    const fe = fighterEnv.clone().divideScalar(sc);
    const clear = 2 / sc;
    const cols = Math.floor((size.x - clear) / (fe.x + clear));
    const rows = Math.floor((size.z - clear) / (fe.z + clear));
    const boxGeo = new THREE.BoxGeometry(fe.x, fe.y, fe.z);
    const inst = new THREE.InstancedMesh(boxGeo, new THREE.MeshBasicMaterial({ color: '#62dcff', transparent: true, opacity: 0.35, depthWrite: false }), 50);
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
    bloom.setSize(W, H);
    camera.aspect = W / H; camera.updateProjectionMatrix();
  }
  addEventListener('resize', resize);

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
    const dist = camera.position.distanceTo(controls.target);
    camera.near = THREE.MathUtils.clamp(dist * 0.01, 0.05, 20);
    camera.updateProjectionMatrix();
    sky.update(simT, camera, renderer);
    for (const e of effects) e.update(simT, renderer.domElement.height);
    composer.render();
    labelRenderer.render(scene, camera);
    frames++;
    if (frames === 2) { const l = document.getElementById('loading'); if (l) { if (still) l.hidden = true; else l.classList.add('done'); } }
    if (still && frames === 3) { window.__ready = true; document.body.dataset.ready = '1'; return; }
    requestAnimationFrame(frame);
  }
  renderer.domElement.addEventListener('pointerdown', () => { world.followTarget = null; flight = null; });
  window.__scene = { scene, camera, renderer, world, controls };
  frame();
}
