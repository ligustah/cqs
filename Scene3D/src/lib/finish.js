// Look-dev v8 (opt-in): a "worn finish" for the hulls and screen-space contact shadows.
//
// Everything here is behind query flags so the default look is unchanged:
//   ?finish=worn  worn-paint finish on every GLB ship (hull and kit parts), see addWornFinish()
//   ?ao=1         screen-space ambient occlusion (GTAO) applied inside the lit materials, see createScreenAO()
// (lighting was reviewed and left as is: no ?light=v2; see the v8 note in pipeline/fal-pipeline.json)
// FINISH_DEFAULT / AO_DEFAULT below are the switches to flip once the look is approved;
// ?finish=off / ?ao=0 then turn each back off.
//
// Worn finish, in the ship frame (metres, so the pattern is continuous across hull and parts and
// has the same absolute size on every class):
//   - macro albedo tone: the fal PATINA 'hullWear' set's luminance, read at two scales (~24 m and
//     ~110 m, axes swapped between them so the repeats never line up), as a luminance-normalised
//     z-score: about +-6 % / +-8 % per scale at one sigma, clamped to +-20 %. Hue is untouched;
//   - optional plate tone (plateTone: true): the 'hull' set's base colour at the detail layer's tile.
//     Off: its 6 m grid read as a checkerboard that ignores a remodelled hull's own plate seams;
//   - roughness breakup: after the livery's matte push the hull's roughness is re-derived from the
//     wear set (two scales) and the plate tone: ~0.6-0.95, mean ~0.8, with worn (lighter) patches
//     slightly glossier, so the sun's broad sheen and the planet's reflection vary across plates;
//   - micro-surface: the 'hullGrit' set (0.8 m tile) perturbs the normal only where a tile spans
//     enough pixels (faded by the screen-space footprint, so it never aliases or shimmers); its
//     roughness (mip-filtered, safe at any distance) always adds a fine breakup, and the lost
//     normal variance of the faded grit is folded back into roughness;
//   - drive soot: near each drive bell's lip (userData.ship.engines / cfg.engines) the paint is
//     stained darker and rougher (the 'sootStreak' set breaks it up).
//   - v10 seam grime and edge wear push, read from the remodel's own texture paint (the livery exports its
//     luminance livL and the two-tone zone livZone): seams and AO grime (paint luminance ~0.2-0.5 around
//     the ~0.6 paint) are darkened further, warm-brown on light zones; edge wear (paint.py writes it into
//     the ORM metal channel, 0.03-0.28 on paint) is scuffed lighter on dark paint and chipped darker on
//     light paint; the plate tone breakup is stronger on light zones, where it would otherwise vanish.
// Glass (the livery's livGlass), saturated markings and container colours (reduced strength), and
// the carrier's hangar interior (excluded box) are respected. Kit parts get it at lower strength.
import * as THREE from 'three';
import { GTAOPass } from 'three/addons/postprocessing/GTAOPass.js';

const params = new URLSearchParams(globalThis.location?.search || '');
// ---- defaults to flip ------------------------------------------------------------------------
export const FINISH_DEFAULT = true;  // true: worn finish everywhere unless ?finish=off
export const AO_DEFAULT = true;      // true: screen-space AO (desktop tier only) unless ?ao=0
// -------------------------------------------------------------------------------------------------
const fq = params.get('finish');
export const FINISH = fq ? (fq === 'worn' ? 'worn' : null) : (FINISH_DEFAULT ? 'worn' : null);
const aq = params.get('ao');
export const AO_REQUESTED = aq ? aq === '1' : AO_DEFAULT;

// luminance stats of the 'hull' set's base colour (green channel, linear), measured offline
const PLATE_STAT = [0.7125, 0.0285];

// Finish presets (a module picks one with asset.finish = 'ground' or { preset: 'ground', ...overrides }).
//   ship   the fleet's worn hull (the original numbers: every ship shades exactly as before).
//   ground ground units (correction 34: "way too smooth and clean. Too shiny"): the macro tone and grit are read at
//          vehicle scale (2.5 m / 9 m wear, 0.35 m grit) instead of ship scale (24 m / 110 m, 0.8 m), roughness is
//          matte (0.84-1.0, mean 0.92: no glossy highlight), scratches in the groundPaint detail set show lighter
//          (paint scratched to primer), and a ground layer in TRUE albedo (after the livery, so it reads on any
//          scheme and is continuous across the hull and every kit part): dust graded up from the ground (full to
//          dustFull m, gone by dustTop m, ragged edge), clumped dried mud low down (to mudTop m), a light dust film
//          on up-facing surfaces. groundY is the contact plane in the ship frame (glbship: anchors.ground.y).
export const FINISH_PRESETS = {
  ship: { scale: [24, 110], tone: [0.06, 0.08], rough: [0.78, 0.55, 0.95], grit: 0.8, gritNrm: 0.55, seam: 0.45, edge: [1.2, 0.5] },
  ground: {
    scale: [2.5, 9], tone: [0.07, 0.08], rough: [0.92, 0.84, 1.0], grit: 0.35, gritNrm: 0.6, seam: 0.6, edge: [1.5, 0.6],
    ground: {
      dust: [0.2, 0.165, 0.12], mud: [0.105, 0.08, 0.056],  // linear albedo: dry dust, dried mud
      dustFull: 0.4, dustTop: 1.55, dustMax: 0.66,           // dust opacity: dustMax at the ground ... 0 at dustTop
      mudTop: 0.75, mudMax: 0.85, film: 0.16,                 // mud clumps below mudTop; dust film on roofs and decks
      scratch: 0.9,                                          // groundPaint scratches lighten the paint (0 = off)
    },
  },
};

/**
 * Chain the worn finish onto a MeshStandard/Physical material that may already carry the livery
 * (applyLivery) and the PATINA detail layer (addDetailLayer). Apply it LAST.
 *   lib        PATINA library (needs hullWear; hullGrit, sootStreak and hull are optional)
 *   toShip     Matrix4: the mesh's object space -> ship frame (metres)
 *   strength   0..1 overall (kit parts ~0.6)
 *   engines    [{ p: [x,y,z] | Vector3, dir, radius }] in the ship frame
 *   exclude    optional { box: [[x,y,z],[x,y,z]], feather }: no finish inside (a hangar interior)
 */
export function addWornFinish(material, lib, { toShip, strength = 1, tone = 1, engines = [], exclude = null, plateTone = false, preset = 'ship', groundY = 0 } = {}) {
  const wear = lib.hullWear?.maps?.pack;
  if (!wear) return material;
  // preset: a FINISH_PRESETS key, or { preset: key, ...overrides } (ground overrides merge into the preset's ground)
  const pName = typeof preset === 'string' ? preset : preset?.preset || 'ship';
  const pOver = typeof preset === 'object' && preset ? preset : {};
  const F = { ...FINISH_PRESETS[pName] || FINISH_PRESETS.ship, ...pOver };
  const G = F.ground ? { ...FINISH_PRESETS[pName]?.ground, ...pOver.ground } : null;
  // the groundPaint scratches come from the detail layer's height map (addDetailLayer, chained before this)
  const scratchOn = !!(G && G.scratch > 0 && material.userData.detail?.uDetHeight?.value);
  const wearStat = lib.hullWear.meta.stats;
  const grit = lib.hullGrit?.maps?.pack || null;
  const gritStat = lib.hullGrit?.meta.stats;
  const soot = lib.sootStreak?.maps?.pack || null;
  const sootStat = lib.sootStreak?.meta.stats;
  // plate tone from the 'hull' set (off by default: its 6 m grid does not follow a remodelled hull's own seams)
  const plate = plateTone && material.userData.detail && lib.hull?.maps?.basecolor ? lib.hull.maps.basecolor : null;
  const hasLiv = !!material.userData.livery;
  const V3 = THREE.Vector3;
  const eng = engines.slice().sort((a, b) => b.radius - a.radius).slice(0, 8);
  const engP = Array.from({ length: 8 }, (_, i) => (eng[i] ? new THREE.Vector4(...new V3().copy(eng[i].p).toArray(), eng[i].radius) : new THREE.Vector4(0, 0, 0, 0)));
  const engD = Array.from({ length: 8 }, (_, i) => (eng[i] ? new V3().copy(eng[i].dir || new V3(0, 0, -1)).normalize() : new V3(0, 0, -1)));
  const uniforms = {
    uFinM: { value: toShip.clone() },
    uFinAmt: { value: strength },
    uFinWear: { value: wear },
    uFinWearStat: { value: new THREE.Vector4(wearStat.lum[0], wearStat.lum[1], wearStat.rough[0], wearStat.rough[1]) },
    uFinScale: { value: new THREE.Vector2(1 / F.scale[0], 1 / F.scale[1]) },
    uFinTone: { value: new THREE.Vector2(...F.tone).multiplyScalar(tone) }, // per scale, at one sigma
    uFinRough: { value: new THREE.Vector3(...F.rough) }, // mean, min, max of the re-derived roughness
    uFinGrit: { value: grit },
    uFinGritOn: { value: grit ? 1 : 0 },
    uFinGritScale: { value: 1 / F.grit },
    uFinGritStat: { value: new THREE.Vector2(...(gritStat?.rough || [0.5, 0.1])) },
    uFinGritNrm: { value: F.gritNrm },
    uFinPlate: { value: plate },
    uFinPlateOn: { value: plate ? 1 : 0 },
    uFinPlateStat: { value: new THREE.Vector2(...PLATE_STAT) },
    uFinSoot: { value: soot || wear },
    uFinSootStat: { value: new THREE.Vector2(...(sootStat?.lum || wearStat.lum)) },
    uFinEngN: { value: eng.length },
    uFinEngP: { value: engP },
    uFinEngD: { value: engD },
    uFinExOn: { value: exclude ? 1 : 0 },
    uFinExMin: { value: new V3(...(exclude?.box[0] || [0, 0, 0])) },
    uFinExMax: { value: new V3(...(exclude?.box[1] || [0, 0, 0])) },
    uFinExFeather: { value: exclude?.feather ?? 2 },
    // v10 wear push: seam grime darkening, edge wear (x: lighten on dark paint, y: darken on light paint)
    uFinSeam: { value: F.seam * strength },
    uFinEdge: { value: new THREE.Vector2(...F.edge).multiplyScalar(strength) },
    // ground layer (preset.ground): x groundY, y dustFull, z dustTop, w dustMax; (mudTop, mudMax, film, scratch)
    ...(G ? {
      uFinGround: { value: new THREE.Vector4(groundY, G.dustFull, G.dustTop, G.dustMax) },
      uFinGround2: { value: new THREE.Vector4(G.mudTop, G.mudMax, G.film, G.scratch) },
      uFinDust: { value: new THREE.Color().setRGB(...G.dust) }, uFinMud: { value: new THREE.Color().setRGB(...G.mud) },
    } : {}),
  };
  material.userData.finish = uniforms;
  const prev = material.onBeforeCompile;
  material.onBeforeCompile = (shader, renderer) => {
    prev?.call(material, shader, renderer);
    Object.assign(shader.uniforms, uniforms);
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nuniform mat4 uFinM; varying vec3 vFinP; varying vec3 vFinN;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvFinP = (uFinM * vec4(transformed, 1.0)).xyz;\nvFinN = mat3(uFinM) * objectNormal;');
    const fns = /* glsl */`
      varying vec3 vFinP; varying vec3 vFinN;
      uniform float uFinSeam; uniform vec2 uFinEdge;
      uniform float uFinAmt, uFinGritOn, uFinGritScale, uFinGritNrm, uFinPlateOn, uFinExOn, uFinExFeather;
      uniform int uFinEngN;
      uniform vec4 uFinWearStat; uniform vec2 uFinTone, uFinScale, uFinGritStat, uFinPlateStat, uFinSootStat; uniform vec3 uFinRough;
      uniform sampler2D uFinWear, uFinGrit, uFinPlate, uFinSoot;
      uniform vec4 uFinEngP[8]; uniform vec3 uFinEngD[8];
      uniform vec3 uFinExMin, uFinExMax;${G ? '\n      uniform vec4 uFinGround, uFinGround2; uniform vec3 uFinDust, uFinMud;' : ''}
      float finGroundK = 0.0;
      float finMask, finSootK, finGritVis, finMark, finPlateZ; vec4 finA1, finA2, finGx, finGy, finGz; vec3 finDpx, finDpy;
      vec3 finW() { vec3 w = pow(abs(normalize(vFinN)), vec3(4.0)); return w / (w.x + w.y + w.z); }
      vec4 finTri(sampler2D t, vec3 p, vec3 w) { return texture2D(t, p.zy) * w.x + texture2D(t, p.xz) * w.y + texture2D(t, p.xy) * w.z; }
      // the second (large) scale reads the same set with its axes swapped and offset: no aligned repeats
      vec4 finTri2(sampler2D t, vec3 p, vec3 w) { return texture2D(t, p.yz + 0.37) * w.x + texture2D(t, p.zx + 0.61) * w.y + texture2D(t, p.yx + 0.19) * w.z; }
      float finExclude() {
        if (uFinExOn < 0.5) return 1.0;
        vec3 d = min(vFinP - uFinExMin, uFinExMax - vFinP); vec3 m = smoothstep(vec3(0.0), vec3(uFinExFeather), d);
        return 1.0 - m.x * m.y * m.z;
      }
      // drive soot: stained paint around each bell lip and on the structure just forward of it
      float finSoot() {
        float s = 0.0;
        for (int i = 0; i < 8; i++) {
          if (i >= uFinEngN) break;
          vec3 d = vFinP - uFinEngP[i].xyz; float r = uFinEngP[i].w;
          float ax = dot(d, uFinEngD[i]); float rad = length(d - uFinEngD[i] * ax);
          float along = smoothstep(-3.2 * r, -0.2 * r, ax) * (1.0 - smoothstep(0.1 * r, 0.6 * r, ax));
          float ring = exp(-pow(max(rad - 0.85 * r, 0.0) / (0.9 * r), 2.0));
          s = max(s, along * ring);
        }
        return s;
      }
      // cotangent frame from screen derivatives taken in uniform control flow (see the normal block)
      mat3 finTBN(vec3 q0, vec3 q1, vec3 n, vec2 s0, vec2 s1) {
        vec3 q1p = cross(q1, n), q0p = cross(n, q0);
        vec3 T = q1p * s0.x + q0p * s1.x; vec3 B = q1p * s0.y + q0p * s1.y;
        float det = max(dot(T, T), dot(B, B)); float sc = (det == 0.0) ? 0.0 : inversesqrt(det);
        return mat3(T * sc, B * sc, n);
      }`;
    const liv = hasLiv ? 'livGlass' : '0.0';
    // albedo (before color_fragment, after the livery repaint and any interior keep)
    const albedo = /* glsl */`{
        finMask = uFinAmt * finExclude() * (1.0 - ${liv});
        vec3 c = diffuseColor.rgb; float mx = max(c.r, max(c.g, c.b)), mn = min(c.r, min(c.g, c.b));
        finMark = smoothstep(0.18, 0.4, (mx - mn) / max(mx, 1e-4)); // markings / container colours
        vec3 w = finW();
        finA1 = finTri(uFinWear, vFinP * uFinScale.x, w); finA2 = finTri2(uFinWear, vFinP * uFinScale.y, w);
        float tone = uFinTone.x * clamp((finA1.r - uFinWearStat.x) / uFinWearStat.y, -2.0, 2.0) + uFinTone.y * clamp((finA2.b - uFinWearStat.x) / uFinWearStat.y, -2.0, 2.0);
        finPlateZ = 0.0;
        ${plate ? 'finPlateZ = clamp((detTriS(uFinPlate, uDetScale) - uFinPlateStat.x) / uFinPlateStat.y, -2.0, 2.0) * uFinPlateOn;' : ''}
        tone += 0.025 * finPlateZ;
        float finLZ = ${hasLiv ? 'livZone' : '0.0'}, finLL = ${hasLiv ? 'livL' : '0.6'};
        tone = clamp(tone, -0.2, 0.2) * mix(1.0, 0.5, finMark) * (1.0 + 0.6 * finLZ);
        finSootK = finSoot();
        // soot breakup: the soot set's streaks where the drive stains the paint (uniform branch: ships
        // without drives skip the fetches; they stay out of per-pixel branches so their mips are defined)
        float sootAmt = 0.0;
        if (uFinEngN > 0) { float sootTex = finTri(uFinSoot, vFinP * 0.18, w).r; sootAmt = finSootK * clamp(0.75 + 0.5 * (uFinSootStat.x - sootTex) / max(uFinSootStat.y, 1e-3), 0.3, 1.2); }
        diffuseColor.rgb *= mix(1.0, (1.0 + tone) * (1.0 - 0.6 * sootAmt), finMask);
        ${hasLiv ? `{
          // seams and AO grime: the paint's darker texels, not its dark zones (belly, recess plates < ~0.15)
          float grime = smoothstep(0.52, 0.3, finLL) * smoothstep(0.1, 0.2, finLL) * (1.0 - finMark) * finMask * (1.0 - livKeep);
          vec3 gcol = mix(vec3(1.0), vec3(0.86, 0.8, 0.72), finLZ) * (1.0 - uFinSeam * (0.6 + 0.4 * finLZ));
          diffuseColor.rgb *= mix(vec3(1.0), gcol, grime);
          float edge = 0.0;
          #ifdef USE_METALNESSMAP
            float mt = texture2D(metalnessMap, vMetalnessMapUv).b;
            edge = smoothstep(0.03, 0.16, mt) * (1.0 - smoothstep(0.3, 0.38, mt));
          #endif
          edge *= finMask * (1.0 - finMark) * (1.0 - livKeep);
          diffuseColor.rgb *= mix(1.0, mix(1.0 + uFinEdge.x, 1.0 - uFinEdge.y, finLZ), edge);
        }` : ''}
        ${scratchOn ? `{
          // groundPaint scratches (grooves in its height map, z < -1.2) show lighter: paint scratched to the primer
          float hz = (detTri(uDetHeight) - 0.6) / 0.09;
          diffuseColor.rgb *= 1.0 + 1.3 * smoothstep(-1.2, -2.8, hz) * uFinGround2.w * finMask * (1.0 - finMark)${hasLiv ? ' * (1.0 - livKeep)' : ''};
        }` : ''}
        ${G ? `{
          // ground layer in true albedo: dust graded up from the ground plane, dried mud clumps low down, a dust film on
          // up-facing surfaces. Ragged edges from the wear set at ~1.1 m and ~0.3 m (z-scored). Full strength on kit parts too
          // (tyres, doors, suspension): the layer is continuous in the ship frame
          vec3 wg = finW();
          float hg = vFinP.y - uFinGround.x;
          float nz1 = clamp((finTri(uFinWear, vFinP * 0.9, wg).r - uFinWearStat.x) / uFinWearStat.y, -2.5, 2.5);
          float nz2 = clamp((finTri2(uFinWear, vFinP * 3.1, wg).b - uFinWearStat.x) / uFinWearStat.y, -2.5, 2.5);
          float gx = finExclude() * (1.0 - ${liv});
          float dust = uFinGround.w * (1.0 - smoothstep(uFinGround.y, uFinGround.z, hg + 0.16 * nz1 + 0.07 * nz2));
          float up = smoothstep(0.55, 0.9, normalize(vFinN).y);
          dust = max(dust, uFinGround2.z * up * clamp(0.6 + 0.35 * nz1, 0.0, 1.0)) * gx;
          // a thinner film on up-facing glass (raked windscreens): dusty panes, not mirrors
          dust = max(dust, 0.3 * uFinGround2.z * up * clamp(0.6 + 0.35 * nz1, 0.0, 1.0) * finExclude() * ${liv});
          float mud = uFinGround2.y * (1.0 - smoothstep(uFinGround2.x * 0.45, uFinGround2.x, hg + 0.12 * nz1))
                    * smoothstep(0.1, 0.9, 0.5 * nz2 + 0.35 * nz1 + 0.2) * gx;
          finGroundK = max(dust, mud);
          diffuseColor.rgb = mix(diffuseColor.rgb, uFinDust, dust);
          diffuseColor.rgb = mix(diffuseColor.rgb, uFinMud, mud);
        }` : ''}
      }`;
    // roughness (after the livery's matte push and the detail layer)
    const rough = /* glsl */`{
        vec3 w = finW();
        // pack: r = luminance, g = warm/cool chroma, b = soft luminance (all z-normalised). The chroma
        // (discoloured patches) and the large-scale soft tone drive roughness: related to the tone, not a copy
        float zr = clamp((finA1.g - uFinWearStat.z) / uFinWearStat.w, -1.5, 1.5) * 0.55 + clamp((finA2.b - uFinWearStat.z) / uFinWearStat.w, -2.0, 2.0) * 0.45;
        float worn = clamp((finA1.r - uFinWearStat.x) / uFinWearStat.y, 0.0, 2.0); // lighter, worn patches: a little glossier
        float r = uFinRough.x + 0.1 * zr - 0.04 * worn + 0.04 * finPlateZ;
        // grit: footprint of one grit tile on screen -> visibility of its normals (1 = >= 100 px per tile, 0 below 20;
        // the mip chain already flattens the normals in between, so they cannot shimmer)
        vec3 pg = vFinP * uFinGritScale;
        finDpx = dFdx(pg); finDpy = dFdy(pg);
        float fw = max(length(finDpx), length(finDpy));
        finGritVis = uFinGritOn * (1.0 - smoothstep(1.0 / 100.0, 1.0 / 20.0, fw));
        if (uFinGritOn > 0.5) {
          finGx = texture2D(uFinGrit, pg.zy); finGy = texture2D(uFinGrit, pg.xz); finGz = texture2D(uFinGrit, pg.xy);
          float gr = finGx.b * w.x + finGy.b * w.y + finGz.b * w.z;
          r += 0.05 * clamp((gr - uFinGritStat.x) / uFinGritStat.y, -2.0, 2.0) + 0.03 * (1.0 - finGritVis);
        }
        r += 0.12 * finSootK;
        ${scratchOn ? 'r += 0.3 * (detTri(uDetRough) - 0.45);' : ''}
        r = clamp(r, uFinRough.y, uFinRough.z);
        // only paint takes it: glass and the deliberately glossy texels keep their own roughness
        float k = finMask * smoothstep(0.35, 0.55, roughnessFactor);
        ${G ? `k *= 1.0 - ${hasLiv ? 'livKeep' : '0.0'}; r = mix(r, 0.97, finGroundK); k = max(k, finGroundK);` : ''}
        roughnessFactor = mix(roughnessFactor, r, k);
      }`;
    const nrm = /* glsl */`
      if (uFinGritOn > 0.5) { // uniform branch
        vec3 q0 = dFdx(-vViewPosition), q1 = dFdy(-vViewPosition); // derivatives outside the per-pixel branch below
        if (finGritVis * finMask > 0.001) {
          vec3 w = finW();
          // the grit samples fetched for its roughness (same coordinates) carry the normal in rg
          vec3 nx = vec3((finGx.rg * 2.0 - 1.0) * uFinGritNrm, 1.0);
          vec3 ny = vec3((finGy.rg * 2.0 - 1.0) * uFinGritNrm, 1.0);
          vec3 nz = vec3((finGz.rg * 2.0 - 1.0) * uFinGritNrm, 1.0);
          vec3 g = normalize(finTBN(q0, q1, normal, finDpx.zy, finDpy.zy) * nx * w.x + finTBN(q0, q1, normal, finDpx.xz, finDpy.xz) * ny * w.y + finTBN(q0, q1, normal, finDpx.xy, finDpy.xy) * nz * w.z);
          normal = normalize(mix(normal, g, finGritVis * finMask));
        }
      }`;
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', '#include <common>\n' + fns)
      .replace('#include <color_fragment>', albedo + '\n#include <color_fragment>')
      .replace('#include <metalnessmap_fragment>', rough + '\n#include <metalnessmap_fragment>' + (G ? '\nmetalnessFactor *= 1.0 - finGroundK;' : ''))
      .replace('#include <emissivemap_fragment>', nrm + '\n#include <emissivemap_fragment>');
  };
  const prevKey = material.customProgramCacheKey.bind(material);
  material.customProgramCacheKey = () => `worn${plate ? '-p' : ''}${hasLiv ? '-l' : ''}${G ? '-g' : ''}${scratchOn ? 's' : ''}|${prevKey()}`;
  material.needsUpdate = true;
  return material;
}

/**
 * Screen-space ambient occlusion (three's GTAO) applied INSIDE the lit materials, before the
 * main render: a normal/depth pre-pass of the lit meshes, GTAO + its Poisson denoise into a
 * texture, then every MeshStandard/Physical material samples it at its own pixel and darkens its
 * indirect light (planet-shine and its reflections) fully and its direct light by `direct` only
 * (a hint of contact shadow where parts meet the hull; the sun's own shadow map does the rest).
 * Unlit meshes (glows, plumes, the planet, the sky) are left out of the pre-pass.
 */
export function createScreenAO(renderer, scene, camera, { direct = 0.45, strength = 1, resolution = 0.5 } = {}) {
  // AO is computed at `resolution` of the drawing buffer (half by default: a quarter of the pixel work
  // in the pre-pass and GTAO; the denoised result is smooth, and materials sample it by screen UV)
  const size = renderer.getDrawingBufferSize(new THREE.Vector2());
  const aoSize = (v) => Math.max(1, Math.round(v * resolution));
  const pass = new GTAOPass(scene, camera, aoSize(size.x), aoSize(size.y));
  pass.output = GTAOPass.OUTPUT.Off;
  pass.updateGtaoMaterial({ radius: 3, distanceExponent: 1.5, thickness: 4.5, distanceFallOff: 1, scale: 1.3, samples: 16 });
  pass.updatePdMaterial({ lumaPhi: 10, depthPhi: 2, normalPhi: 3, radius: 6, rings: 2, samples: 16 });
  // pre-pass: only lit, opaque meshes cast AO
  pass._overrideVisibility = function () {
    const cache = this._visibilityCache;
    scene.traverse((o) => {
      if (!o.visible) return;
      const m = Array.isArray(o.material) ? o.material[0] : o.material;
      const lit = o.isMesh && m && (m.isMeshStandardMaterial || m.isMeshPhysicalMaterial) && !m.transparent;
      if ((o.isPoints || o.isLine || o.isLine2 || o.isSprite || (o.isMesh && !lit))) { o.visible = false; cache.push(o); }
    });
  };
  const U = {
    uSAOTex: { value: pass.pdRenderTarget.texture },
    uSAOInvRes: { value: new THREE.Vector2(1 / size.x, 1 / size.y) },
    uSAOStr: { value: strength },
    uSAODirect: { value: direct },
  };
  const patched = new WeakSet();
  function patch(m) {
    if (patched.has(m) || !(m.isMeshStandardMaterial || m.isMeshPhysicalMaterial)) return;
    patched.add(m);
    const prev = m.onBeforeCompile;
    m.onBeforeCompile = (shader, r) => {
      prev?.call(m, shader, r);
      Object.assign(shader.uniforms, U);
      shader.fragmentShader = shader.fragmentShader
        .replace('#include <common>', '#include <common>\nuniform sampler2D uSAOTex; uniform vec2 uSAOInvRes; uniform float uSAOStr, uSAODirect;')
        .replace('#include <aomap_fragment>', `#include <aomap_fragment>
          {
            float sao = mix(1.0, texture2D(uSAOTex, gl_FragCoord.xy * uSAOInvRes).r, uSAOStr);
            reflectedLight.indirectDiffuse *= sao;
            reflectedLight.indirectSpecular *= mix(1.0, sao, 0.8);
            float sd = mix(1.0, sao, uSAODirect);
            reflectedLight.directDiffuse *= sd; reflectedLight.directSpecular *= sd;
          }`);
    };
    const prevKey = m.customProgramCacheKey.bind(m);
    m.customProgramCacheKey = () => `sao|${prevKey()}`;
    m.needsUpdate = true;
  }
  const patchScene = () => scene.traverse((o) => { if (o.isMesh) (Array.isArray(o.material) ? o.material : [o.material]).forEach(patch); });
  let frames = 0;
  return {
    pass, uniforms: U,
    /** run before the main render; `dist` = camera-to-subject distance (m) sets the radius */
    render(dist) {
      if (frames++ % 120 === 0) patchScene();
      const s = renderer.getDrawingBufferSize(new THREE.Vector2());
      if (aoSize(s.x) !== pass.width || aoSize(s.y) !== pass.height) { pass.setSize(aoSize(s.x), aoSize(s.y)); U.uSAOInvRes.value.set(1 / s.x, 1 / s.y); }
      // metre-scale grounding in close views, a few metres on a 900 m carrier seen whole
      const radius = THREE.MathUtils.clamp(dist * 0.025, 1.5, 14);
      pass.updateGtaoMaterial({ radius, thickness: radius * 1.5 });
      pass.render(renderer, null, null);
      renderer.setRenderTarget(null);
    },
    set enabled(on) { U.uSAOStr.value = on ? strength : 0; },
  };
}
