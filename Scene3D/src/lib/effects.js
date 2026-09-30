// Runtime effects attached to finished ships: plasma exhaust plumes and
// navigation / running lights. Both read anchors recorded by ShipBuilder.
import * as THREE from 'three';
import { LIVERY } from './materials.js';
import { PIN_COLORS } from './lightscape.js';
import { LIVERY_TIME } from './livery.js';

const LIGHT_COLORS = {
  red: LIVERY.navRed, green: LIVERY.navGreen, white: '#ffffff', amber: LIVERY.amber, cyan: '#7fe8ff',
};

// Fusion-drive exhaust. In vacuum the plasma is nearly invisible a short way
// past the magnetic nozzle, so the drive reads as a hot glow in the bell (the
// throat disc from glbship.js / kit.js) and a short, soft plume that fades
// within about one bell radius: never a beam. The mesh is only a bounding
// cylinder (radius 1 = bound, length 1, nozzle at z = 0, plume toward -z); the
// fragment shader finds where the view ray passes closest to the plume axis
// and evaluates Gaussian core + glow profiles there. Profiles are in units of
// the bell radius and fall to ~0 well inside the bound, so the volume never
// shows an edge (AgX's long toe would reveal even very faint steps on black).
const PLUME_BOUND = 2.4;  // bounding radius / bell radius
const PLUME_MAX = 3.0;    // bounding length / bell radius (before plumeScale)
const plumeGeometry = (() => {
  const g = new THREE.CylinderGeometry(1, 1, 1, 24, 1, false);
  g.translate(0, -0.5, 0);
  g.rotateX(-Math.PI / 2);
  g.rotateY(Math.PI);
  return g;
})();

function plumeMaterial(color, seed) {
  return new THREE.ShaderMaterial({
    uniforms: {
      uTime: { value: 0 }, uPower: { value: 1 }, uSeed: { value: seed },
      uSheath: { value: new THREE.Color(color) },
      uAspect: { value: 1 }, // bound length / bound radius (for the ray metric)
      uBound: { value: PLUME_BOUND },
      uLen: { value: PLUME_MAX }, // bound length in bell radii
    },
    vertexShader: /* glsl */`
      varying vec3 vObj; varying vec3 vCam;
      void main() {
        vObj = position;
        vCam = (inverse(modelMatrix) * vec4(cameraPosition, 1.0)).xyz;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }`,
    fragmentShader: /* glsl */`
      uniform float uTime, uPower, uSeed, uAspect, uBound, uLen; uniform vec3 uSheath;
      varying vec3 vObj; varying vec3 vCam;
      void main() {
        // work in a space where radial and axial units are both metres-proportional
        vec3 o = vCam * vec3(1.0, 1.0, uAspect);
        vec3 d = normalize(vObj * vec3(1.0, 1.0, uAspect) - o);
        float dxy2 = max(dot(d.xy, d.xy), 1e-4);
        float t = -dot(o.xy, d.xy) / dxy2;
        vec2 q = o.xy + t * d.xy;
        float rho = length(q) * uBound;              // closest distance to the axis (bell radii)
        float s = -(o.z + t * d.z) / uAspect;        // 0 at the exit plane, 1 at the end of the bound
        float z = clamp(s, 0.0, 1.0) * uLen;         // distance behind the exit (bell radii)
        float wc = 0.30 * (1.0 + 0.6 * z);           // hot core: narrow, gone within ~0.4 r
        float wg = 0.45 * (1.0 + 0.5 * z);           // soft glow: a narrow tapered column, gone within ~3 r
        float core = exp(-rho * rho / (wc * wc)) * exp(-z / 0.35);
        // the column builds up over the first ~0.6 r behind the exit (the plasma detaches from the
        // magnetic nozzle), so in stern quarter views it does not lie over the dark bell mouth
        float glow = exp(-rho * rho / (wg * wg)) * exp(-z / 1.2) * (0.15 + 0.85 * smoothstep(0.0, 0.7, z));
        // nothing upstream of the exit plane (the bell interior is the throat glow). The profiles
        // are evaluated where the ray passes closest to the axis, but an oblique ray crosses each
        // Gaussian over an axial stretch ~ width * (axial / radial travel): gate by the fraction of
        // that stretch that lies downstream of the exit (a smooth CDF, not a hard cut, which would
        // draw a straight edge across the dark bell mouth)
        float slope = abs(d.z) / (sqrt(dxy2) * uAspect);   // axial per radial travel (real units)
        float gc = smoothstep(-1.0, 1.0, s / max(0.02, 1.2 * wc * slope / uLen));
        float gg = smoothstep(-1.0, 1.0, s / max(0.02, 1.2 * wg * slope / uLen));
        float tail = 1.0 - smoothstep(0.55, 1.0, s);
        float path = min(inversesqrt(dxy2), 2.0);    // a little denser when looking along the jet
        float flick = 0.96 + 0.04 * sin(uTime * 61.0 + uSeed * 9.0) * sin(uTime * 23.0 + uSeed);
        // seen end-on the plume is optically thin: the hot core (right at the exit plane, where it
        // would lie over the bell mouth) fades almost away; the soft column keeps a hint
        float axial = abs(normalize(vObj - vCam).z);
        // (from a stern quarter the column behind the exit projects over the bell mouth: the fade
        // starts ~70 degrees off the axis, and only the thin core gets the longer path along the jet)
        float endOn = smoothstep(0.3, 0.92, axial);
        vec3 col = vec3(0.93, 0.95, 1.0) * core * 0.4 * gc * path * mix(1.0, 0.12, endOn)
                 + uSheath * glow * 0.25 * gg * mix(1.0, 0.22, endOn);
        col *= tail * flick * uPower;
        gl_FragColor = vec4(col, 1.0);
      }`,
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.BackSide,
  });
}

// Point lights (nav lights, v11 lightscape pins). blink = (period, duty, phase, soft):
//   period > 0, soft = 0: a hard on/off strobe (nav); soft > 0: a smooth pulse over the duty (slow
//   beacons, chaser runs); period = 0, soft < 0: a lit port with a faint unsteady light (rate -soft).
// A point never draws below uMinPx pixels so it stays visible at fleet range; a lightscape pin that
// is really smaller than that is dimmed toward its true energy (never below its `floor`), so a
// thousand pins on a distant carrier read as a fine scatter of crisp points, not a glittering haze.
const PIN_SPRITE = 2.0;
// Lightscape emissive gain (pins and slits, not nav lights). main.js raises it a little in the studio, whose key
// and fill light the dark hull far more than the orbital sun does; orbit / fleet stay at 1.
export const LIGHTSCAPE_GAIN = { value: 1 };
// Slits are the concept's signature (short, hard-edged amber bars, brighter than any pin): their radiance is
// scaled by this before display, so a radiance-1.5 bar just crosses the bloom threshold (2.0) along its centre
// line and stays amber through the tone map (much hotter and its core clips to cream: a neon tube, not a slit).
const SLIT_GAIN = 1.6;
const SLIT_SAT = 1.3;
const fract = (x) => x - Math.floor(x);
const blinkGLSL = /* glsl */`
  float blinkOn(vec4 b, float time) {
    if (b.x > 0.0) {
      float t = fract(time / b.x + b.z);
      if (b.w <= 0.0) return step(t, b.y);
      float x = clamp(t / b.y, 0.0, 1.0);
      return t < b.y ? pow(sin(3.14159265 * x), 2.0 * b.w) : 0.0;
    }
    if (b.w < 0.0) {
      float r = -b.w;
      float n = sin(time * r * 5.3 + b.z * 41.0) * sin(time * r * 1.7 + b.z * 13.0);
      float dip = smoothstep(0.55, 0.95, sin(time * r * 0.61 + b.z * 7.0));
      return 0.86 + 0.1 * n - 0.35 * dip * (0.5 + 0.5 * sin(time * 37.0 + b.z * 5.0));
    }
    return 1.0;
  }`;
const lightVS = /* glsl */`
  attribute vec3 color; attribute float size; attribute vec4 blink; attribute float floorE; attribute float rank;
  uniform float uTime; uniform float uScale; uniform float uMinPx; uniform float uGain; uniform float uShipLen;
  varying vec3 vColor; varying float vOn; varying float vSize; varying float vBurn;
  ${blinkGLSL}
  void main() {
    float on = blinkOn(blink, uTime);
    vec4 mv = modelViewMatrix * vec4(position, 1.0);
    // a few cm (+0.05 % of the range) toward the lens: pins sit just proud of the plating
    float d = max(-mv.z, 1e-3);
    mv.xyz *= 1.0 - min(0.5, (0.04 + 0.0005 * d) / d);
    float truePx = size * uScale / d;
    // sprites never draw below uMinPx (3 px, a soft Gaussian footprint: no coverage popping as a pin crosses pixel
    // boundaries); energy and thinning are measured against a 2 px reference
    float px = max(uMinPx, truePx);
    float energy = floorE >= 1.0 ? 1.0 : max(floorE, min(1.0, truePx / 2.0));
    // far off, a hull's pins would crowd into a solid glitter: keep a share that shrinks with their true size and
    // with the whole ship's size on screen (a 150 px ship keeps about a sixth), by a fixed per-pin rank: block
    // corners and authored rows rank low (lightscape.js) and are the last to go, crease-run pins go first
    float shipPx = length((modelViewMatrix * vec4(uShipLen, 0.0, 0.0, 0.0)).xyz) * uScale / max(-(modelViewMatrix * vec4(0.0, 0.0, 0.0, 1.0)).z, 1e-3);
    float keep = floorE >= 1.0 ? 1.0 : clamp(min(truePx / 2.0 * 0.9, shipPx / 900.0), 0.04, 1.0);
    on *= clamp((keep - rank) / 0.06, 0.0, 1.0);
    vColor = color * energy * (floorE >= 1.0 ? 1.0 : uGain);
    vBurn = floorE >= 1.0 ? 0.7 : 0.15; // lightscape pins keep their amber: only a hint of a warm-white core
    vOn = on;
    vSize = px;
    gl_PointSize = on > 0.004 ? px : 0.0;
    gl_Position = projectionMatrix * mv;
  }`;
// The core burns toward white only when the light is drawn large enough to show a halo around
// it: at the 2-3 px minimum (carrier and fleet distances) red and green stay saturated. Lit
// windows (dim warm colours) keep their colour at any size.
const lightFS = /* glsl */`
  varying vec3 vColor; varying float vOn; varying float vSize; varying float vBurn;
  void main() {
    vec2 d = gl_PointCoord - 0.5; float r = length(d) * 2.0;
    float core = smoothstep(0.35, 0.0, r);
    float halo = pow(max(0.0, 1.0 - r), 3.0) * 0.6;
    // drawn at a few pixels the fragments miss the core: a small sprite is a normalised Gaussian footprint instead
    // (same energy as the old 2 px flat dot on the 3 px minimum sprite; its coverage does not jump as it moves)
    float small = 1.0 - smoothstep(3.0, 7.0, vSize);
    float a = max(core + halo, small * exp(-r * r * 4.5)) * vOn;
    if (a < 0.01) discard;
    // (dim sources such as lit ports never burn white: only lamps, max channel >= ~0.5, do); the core burns toward
    // a warm white of the lamp's own hue, so amber pins stay amber at their centre
    float mx = max(vColor.r, max(vColor.g, vColor.b));
    float lamp = smoothstep(0.25, 0.5, mx);
    vec3 hot = vBurn > 0.5 ? vec3(1.0) : mix(vColor / max(mx, 1e-3), vec3(1.0), 0.6);
    gl_FragColor = vec4(mix(vColor, hot, core * vBurn * lamp * smoothstep(2.0, 6.0, vSize)) * a * 4.0, a);
  }`;

// Lightscape slits: short glowing bars in recesses (one InstancedMesh per ship), plus a soft halo quad per bar
// (a second InstancedMesh on the same instances: the warm pool the bar throws on its recess walls). Unlit colour =
// radiance x SLIT_GAIN; anim as blink above (chasers). The concept's hierarchy has the slits as the brightest thing
// on a hull at every range, so far off a bar is widened to at least 1.3 px and stretched to at least 3 px along its
// length; the widening dims it only by its square root, never below 0.45 of its near radiance, and the stretch not
// at all (a distant bar reads as a short bright dash; pins, by contrast, are thinned and fade toward their true energy).
const slitGeometry = new THREE.BoxGeometry(1, 1, 1);
const haloGeometry = new THREE.PlaneGeometry(1, 1);
const slitCommon = /* glsl */`
  attribute vec3 iColor; attribute vec4 iAnim; attribute float iRank;
  uniform float uTime; uniform float uScale; uniform float uGain; uniform float uShipLen;
  varying vec3 vC; varying vec2 vL;
  ${blinkGLSL}
  // a small ship on screen keeps only its lowest-ranked bars (corner bars first): about a quarter on a 70 px fighter,
  // all of them from ~250 px up. Pins thin far harder, so the bars carry the read at range
  float slitKeep() {
    float shipPx = length((modelViewMatrix * vec4(uShipLen, 0.0, 0.0, 0.0)).xyz) * uScale / max(-(modelViewMatrix * vec4(0.0, 0.0, 0.0, 1.0)).z, 1e-3);
    return clamp((clamp(shipPx / 250.0, 0.25, 1.0) - iRank) / 0.08 + 1.0, 0.0, 1.0);
  }
  // on-screen size of a bar: width / length in px at its centre's distance d
  void slitPx(out float d, out float wPx, out float lPx) {
    vec4 c = modelViewMatrix * instanceMatrix * vec4(0.0, 0.0, 0.0, 1.0);
    d = max(-c.z, 1e-3);
    float w = length((modelMatrix * vec4(instanceMatrix[1].xyz, 0.0)).xyz);
    float l = length((modelMatrix * vec4(instanceMatrix[0].xyz, 0.0)).xyz);
    wPx = w * uScale / d; lPx = l * uScale / d;
  }`;
const slitVS = /* glsl */`
  ${slitCommon}
  void main() {
    float on = blinkOn(iAnim, uTime) * slitKeep();
    float d, wPx, lPx; slitPx(d, wPx, lPx);
    float grow = min(max(1.0, 1.3 / max(wPx, 1e-4)), 8.0);
    float stretch = min(max(1.0, 3.0 / max(lPx, 1e-4)), 6.0);
    vec3 p = position; p.y *= grow; p.x *= stretch;
    vL = position.xy * 2.0; // -1..1 along and across the bar
    vC = iColor * on * uGain * max(inversesqrt(grow), 0.4);
    vec4 mv = modelViewMatrix * instanceMatrix * vec4(p, 1.0);
    mv.xyz *= 1.0 - min(0.5, (0.02 + 0.0003 * d) / d);
    gl_Position = projectionMatrix * mv;
  }`;
// a lit slot, not a painted bar: a crisp edge, brightest along its middle line, a little dimmer toward the lips
// and the ends; the middle line leans only slightly toward a warm white, so the bar stays amber (seen from far
// off the whole bar is a pixel wide and reads as its mean: amber)
const slitFS = /* glsl */`
  varying vec3 vC; varying vec2 vL;
  void main() {
    float across = 1.0 - smoothstep(0.45, 1.0, abs(vL.y));
    float along = 1.0 - smoothstep(0.8, 1.0, abs(vL.x));
    float k = (0.5 + 0.6 * across) * (0.55 + 0.45 * along);
    vec3 c = vC * k;
    float mx = max(c.r, max(c.g, c.b));
    c = mix(c, vec3(1.0, 0.86, 0.66) * mx, 0.15 * smoothstep(0.7, 1.0, across * along));
    gl_FragColor = vec4(c * ${SLIT_GAIN.toFixed(2)}, 1.0);
  }`;
// halo: a quad in the bar's own plane, ~3.5x its width (at least 3 px) and its length plus a couple of widths; a
// Gaussian across, soft ends; ~0.1 of the bar's radiance (a faint warm spill on the recess, not a neon bloom),
// fading out as the bar drops under ~1.5 px wide. Pulled a little further toward the lens than the bar, so the
// recess walls right next to it do not clip it
const haloVS = /* glsl */`
  ${slitCommon}
  void main() {
    float on = blinkOn(iAnim, uTime) * slitKeep();
    float d, wPx, lPx; slitPx(d, wPx, lPx);
    float hw = max(wPx * 3.5, 3.0), hl = max(lPx, 3.0) + max(wPx * 2.0, 2.0);
    float gw = hw / max(wPx, 1e-4), gl = hl / max(lPx, 1e-4);
    vec3 p = position; p.y *= gw; p.x *= gl;
    vL = position.xy * 2.0;
    // (fades out once the bar is under ~1.5 px wide: far off a slit is a crisp dash, not a blob)
    vC = iColor * on * uGain * 0.1 * ${SLIT_GAIN.toFixed(2)} * clamp(wPx / 1.5, 0.1, 1.0);
    vec4 mv = modelViewMatrix * instanceMatrix * vec4(p, 1.0);
    float m = max(length((modelMatrix * vec4(instanceMatrix[1].xyz, 0.0)).xyz) * 1.5, 0.05);
    mv.xyz *= 1.0 - min(0.5, (m + 0.0005 * d) / d);
    gl_Position = projectionMatrix * mv;
  }`;
const haloFS = /* glsl */`
  varying vec3 vC; varying vec2 vL;
  void main() {
    float a = exp(-vL.y * vL.y * 7.0) * (1.0 - smoothstep(0.35, 1.0, abs(vL.x)));
    if (a < 0.003) discard;
    gl_FragColor = vec4(vC * a, 1.0);
  }`;

/**
 * Attach plumes + lights to a ship group. Returns { update(t) }.
 * opts.power: 0..1 engine throttle multiplier. power <= 0 means engines off: no plume
 *   meshes are created and the throat glow in each bell (glbship.js) is hidden, so a
 *   parked ship costs nothing but its nav lights; opts.plumeScale lengthens plumes;
 * opts.spill: false skips the stern spill light (small or distant ships in a fleet).
 */
export function attachEffects(group, { power = 1, plumeScale = 1, spill = true } = {}) {
  const info = group.userData.ship;
  const updaters = [];
  const plumes = [];
  const enginesOn = power > 0;
  if (!enginesOn) for (const c of group.children) if (c.name === 'nozzle-glow' || c.name === 'nozzle-lining') c.visible = false;
  let seed = 1;
  for (const e of enginesOn ? info.engines : []) {
    const m = plumeMaterial(e.color ?? '#a4b2e2', seed++ * 1.37); // pale blue-white, not periwinkle
    const bound = e.radius * PLUME_BOUND;
    const lenR = Math.min(e.length / e.radius, PLUME_MAX) * plumeScale; // short: a few bell radii at most
    m.uniforms.uPower.value = power;
    m.uniforms.uLen.value = lenR;
    m.uniforms.uAspect.value = (lenR * e.radius) / bound;
    const mesh = new THREE.Mesh(plumeGeometry, m);
    mesh.scale.set(bound, bound, lenR * e.radius);
    mesh.position.copy(e.p);
    mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, -1), e.dir);
    mesh.renderOrder = 10;
    mesh.frustumCulled = false;
    mesh.name = 'plume';
    // Draw the proxy's near faces: its far faces lie behind the bell body, whose depth clipped
    // the glow along straight lines (a C-shaped rim) from a stern quarter. Only with the camera
    // inside the proxy are the far faces the visible ones. The ray metric is the same either way.
    const inv = new THREE.Matrix4(), cam = new THREE.Vector3();
    mesh.onBeforeRender = (_r, _s, camera) => {
      cam.setFromMatrixPosition(camera.matrixWorld).applyMatrix4(inv.copy(mesh.matrixWorld).invert());
      const inside = cam.x * cam.x + cam.y * cam.y < 1.05 && cam.z < 0.05 && cam.z > -1.05;
      m.side = inside ? THREE.BackSide : THREE.FrontSide;
    };
    group.add(mesh);
    plumes.push(m);
  }
  // Spill from the short plumes onto the ship's own stern: one light per ship,
  // aft of the engine cluster, inverse-square, short range. Only the plume can
  // light the stern plate (the throat glow radiates aft out of the bell), so
  // the intensity is that of the plume glow: radiance ~0.25 over ~1.5 r^2 per
  // engine. Two bell radii aft keeps the near field on the stern plate at a
  // few percent of the sun's irradiance, as an extended source would.
  if (spill && info.engines.length && power > 0.05) {
    const c = info.engines.reduce((acc, e) => acc.add(e.p), new THREE.Vector3()).divideScalar(info.engines.length);
    const rMax = Math.max(...info.engines.map((e) => e.radius));
    const spread = Math.max(...info.engines.map((e) => e.p.distanceTo(c)));
    const I = info.engines.reduce((acc, e) => acc + e.radius * e.radius, 0) * 0.4 * power;
    const L = new THREE.PointLight('#c4d3ff', I, spread + rMax * 6, 2);
    L.position.copy(c).addScaledVector(info.engines[0].dir, rMax * 2.0);
    L.name = 'drive-spill';
    group.add(L);
  }
  if (plumes.length) updaters.push((t) => { for (const m of plumes) m.uniforms.uTime.value = t; });

  // nav lights and the lightscape's pins: ONE Points object per ship
  const shipLen = info.envelope ? Math.max(info.envelope.size.x, info.envelope.size.y, info.envelope.size.z) : 100;
  const allPts = [...info.lights.map((l) => ({ ...l, floor: 1, intensity: 1, nav: true })), ...(info.pins || []).map((l) => ({ ...l, floor: l.floor ?? 0.4 }))];
  if (allPts.length) {
    const n = allPts.length;
    const pos = new Float32Array(n * 3), col = new Float32Array(n * 3), size = new Float32Array(n), blink = new Float32Array(n * 4), floorE = new Float32Array(n), rank = new Float32Array(n);
    const c = new THREE.Color();
    allPts.forEach((l, i) => {
      pos.set([l.p.x, l.p.y, l.p.z], i * 3);
      c.set((l.nav ? LIGHT_COLORS[l.color] : PIN_COLORS[l.color]) ?? PIN_COLORS[l.color] ?? LIGHT_COLORS[l.color] ?? l.color).multiplyScalar(l.intensity ?? 1);
      col.set([c.r, c.g, c.b], i * 3);
      // a pin's sprite spans its halo: the visible core is about a third of it, so a 0.3 m lamp draws 2.4x wide
      size[i] = l.nav ? l.size : l.size * PIN_SPRITE;
      floorE[i] = l.floor;
      // distance-thinning rank: structural (lightscape.js: corners / authored low, crease runs high), else random
      rank[i] = l.nav ? 0 : l.keep ? 0.03 : l.rank ?? fract(Math.sin(i * 12.9898 + 4.1) * 43758.5453);
      if (l.blink) {
        if (l.blink.flicker) blink.set([0, 0, (i * 0.618) % 1, -l.blink.flicker], i * 4);
        else blink.set([l.blink.period ?? 1.2, l.blink.duty ?? 0.12, l.blink.phase ?? 0, l.blink.soft ?? 0], i * 4);
      }
    });
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    g.setAttribute('color', new THREE.BufferAttribute(col, 3));
    g.setAttribute('size', new THREE.BufferAttribute(size, 1));
    g.setAttribute('blink', new THREE.BufferAttribute(blink, 4));
    g.setAttribute('floorE', new THREE.BufferAttribute(floorE, 1));
    g.setAttribute('rank', new THREE.BufferAttribute(rank, 1));
    const m = new THREE.ShaderMaterial({
      uniforms: { uTime: { value: 0 }, uScale: { value: 1160 }, uMinPx: { value: 3.0 }, uGain: LIGHTSCAPE_GAIN, uShipLen: { value: shipLen } },
      vertexShader: lightVS, fragmentShader: lightFS,
      transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    });
    const pts = new THREE.Points(g, m);
    pts.frustumCulled = false;
    pts.renderOrder = 11;
    pts.name = 'navlights';
    group.add(pts);
    // sprite size = the light's true projected size on this lens: pixels per metre at 1 m is
    // viewportH / 2 * P[1][1] (P[1][1] = 1 / tan(fov/2), view offsets included)
    updaters.push((t, viewportH, projY) => { m.uniforms.uTime.value = t; LIVERY_TIME.value = t; if (viewportH) m.uniforms.uScale.value = viewportH * 0.5 * (projY || 2.9); });
  }
  // the lightscape's slits: ONE InstancedMesh per ship
  const slits = info.slits || [];
  if (slits.length) {
    const n = slits.length;
    const m = new THREE.ShaderMaterial({ uniforms: { uTime: { value: 0 }, uScale: { value: 1160 }, uGain: LIGHTSCAPE_GAIN, uShipLen: { value: shipLen } }, vertexShader: slitVS, fragmentShader: slitFS });
    const mesh = new THREE.InstancedMesh(slitGeometry, m, n);
    const iColor = new Float32Array(n * 3), iAnim = new Float32Array(n * 4), iRank = new Float32Array(n);
    const M = new THREE.Matrix4(), v = new THREE.Vector3(), c = new THREE.Color();
    slits.forEach((s, i) => {
      v.crossVectors(s.n, s.u).normalize();
      const u = s.u.clone(), nn = new THREE.Vector3().crossVectors(u, v).normalize();
      M.makeBasis(u.multiplyScalar(s.len), v.multiplyScalar(s.width), nn.multiplyScalar(0.05)).setPosition(s.p);
      mesh.setMatrixAt(i, M);
      c.set(PIN_COLORS[s.color] ?? LIGHT_COLORS[s.color] ?? s.color);
      // a bar is bright enough that the tone map pulls it toward cream: start it a little more saturated so it
      // lands on the concept's orange-amber (neutral colours are left as they are)
      const Y = 0.2126 * c.r + 0.7152 * c.g + 0.0722 * c.b;
      c.setRGB(Math.max(0, Y + (c.r - Y) * SLIT_SAT), Math.max(0, Y + (c.g - Y) * SLIT_SAT), Math.max(0, Y + (c.b - Y) * SLIT_SAT)).multiplyScalar(s.radiance ?? 1);
      iColor.set([c.r, c.g, c.b], i * 3);
      iRank[i] = s.keep ? 0 : s.rank ?? 0;
      if (s.anim) iAnim.set([s.anim.period, s.anim.duty ?? 0.25, s.anim.phase ?? 0, s.anim.soft ?? 0.6], i * 4);
    });
    mesh.geometry = slitGeometry.clone();
    mesh.geometry.setAttribute('iColor', new THREE.InstancedBufferAttribute(iColor, 3));
    mesh.geometry.setAttribute('iAnim', new THREE.InstancedBufferAttribute(iAnim, 4));
    mesh.geometry.setAttribute('iRank', new THREE.InstancedBufferAttribute(iRank, 1));
    mesh.instanceMatrix.needsUpdate = true;
    mesh.frustumCulled = false;
    mesh.name = 'light-slits';
    group.add(mesh);
    // the halo: same instances, soft additive quads
    const hm = new THREE.ShaderMaterial({
      uniforms: { uTime: m.uniforms.uTime, uScale: m.uniforms.uScale, uGain: LIGHTSCAPE_GAIN, uShipLen: m.uniforms.uShipLen }, vertexShader: haloVS, fragmentShader: haloFS,
      transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide,
    });
    const hg = haloGeometry.clone();
    hg.setAttribute('iColor', mesh.geometry.getAttribute('iColor'));
    hg.setAttribute('iAnim', mesh.geometry.getAttribute('iAnim'));
    hg.setAttribute('iRank', mesh.geometry.getAttribute('iRank'));
    const halo = new THREE.InstancedMesh(hg, hm, n);
    halo.instanceMatrix = mesh.instanceMatrix;
    halo.frustumCulled = false;
    halo.renderOrder = 12;
    halo.name = 'light-slit-halos';
    group.add(halo);
    updaters.push((t, viewportH, projY) => { m.uniforms.uTime.value = t; if (viewportH) m.uniforms.uScale.value = viewportH * 0.5 * (projY || 2.9); });
  }
  return { update: (t, viewportH, projY) => updaters.forEach((u) => u(t, viewportH, projY)) };
}
