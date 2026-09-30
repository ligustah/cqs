// Operational livery for generated hulls.
//
// The image-to-3D inputs are painted light (studio lighting on light paint
// gives the reconstruction the most shading detail), so the generated
// textures carry an off-white livery. In service the fleet wears a dark matte
// anti-reflective grey that is hard to spot against space. This pass repaints
// the base colour at shading time:
//   - neutral paint (low saturation) maps to dark grey, keeping the texture's
//     own weathering and panel-to-panel variation (compressed, not flattened);
//   - saturated markings (orange bands, cobalt IDs, civilian containers) keep
//     their hue but are dimmed to low-visibility tones;
//   - copper and gold texels (conduits, coils, MLI foil: hue 15-45 degrees, darker than the
//     orange paint bands) keep part of their hue (copperSat), so they still read as a
//     different material from the grey armour;
//   - dark, blue-tinted, unsaturated texels are glass (canopies, bridge windows): smooth
//     (roughness 0.08), dielectric and darker, so they catch the planet and the sun;
//   - opt-in (glassGlow, off by default so every other ship shades exactly as before): glass
//     texels also get a dim, warm interior light (lit cabins behind the ports and bridge panes), its
//     level varying smoothly between compartments (value noise on ~5 m cells in the ship frame), so
//     kit windows read as glass rather than flat dark plates when they reflect only black space.
//     Livery glass fields (all opt-in; ship frame metres, bow +Z, dorsal +Y, port +X):
//       glassGlow    [r, g, b] linear radiance of a lit cabin (fleet cabin value [0.52, 0.42, 0.28])
//       glassLit     share of compartments lit (default 0.6)
//       glassFlicker share of compartments with a faint unsteady light (default 0)
//       glassCell    compartment size, m: a number or [x, y, z] per axis (default 5)
//       glassPhase   compartment grid offset in cells: a number or [x, y, z] (default 0.37); a compartment edge
//                    sits where p / glassCell + glassPhase is an integer, so a grid aligned to the decks and port
//                    columns never splits a port into two-tone halves (v14 STANDARD section 3.4)
//       glassDark    [box, ...] boxes [[x0, y0, z0], [x1, y1, z1]] where glass stays dark (no interior light)
//       glassZones   [{ box, mirrorX = false, gain = 1, uniform = false, lit }]: regions of the glass with their
//                    own light. gain multiplies the glow (0 = dark, as glassDark); uniform: true makes the whole
//                    box one steady compartment (every pane lit, level 1, no flicker, neutral-warm tint: bridges,
//                    cockpits, CIC at gain 0.45-0.5); lit (0..1) replaces glassLit inside the box (ignored when
//                    uniform). glassDark and glassZones share one list of up to MAX_GLASS_ZONES (8) boxes,
//                    glassDark first (each dark box is a zone of gain 0); the first box containing a texel wins
//       glassParts   (read by glbship.js) kit part names whose glass may glow, e.g. ['port', 'pane']: the hull
//                    texture and every other part keep the dark glass look without interior light (stencils,
//                    sensor lenses, gun sights, containers). Unset: all glass glows. That kit glass also fades
//                    with its on-screen area once a port is under ~2 px (applyLivery kitGlass), as hull-texture
//                    ports do through texture filtering
//     glassDark and glassZones need the mesh's ship-frame matrix (glbship.js passes it).
//   - roughness is pushed toward matte (matte 0.35: a broad, dim sheen only at grazing angles,
//     never a glossy highlight), and metalness is scaled down: the hull is paint (a
//     dielectric), not bare metal.
import * as THREE from 'three';

export const LIVERIES = {
  // linear-space albedo: off-white paint (~0.6) -> ~0.055 (sRGB ~66), mid texel (~0.22) -> ~0.03,
  // dark metal (~0.08) -> ~0.02. Markings: low-visibility, a slightly lighter
  // grey that keeps only a hint of their hue (markSat) at about the hull's value.
  dark: { base: 0.016, gain: 0.065, tint: '#e3e7eb', mark: 0.11, markSat: 0.05, copperSat: 0.5, sat0: 0.22, sat1: 0.5, matte: 0.35, metal: 0.25 },
  // civilian hulls: same grey; cargo colours are weathered paint under the same sun (darker,
  // moderately saturated); cyan/teal trim (hue 170-200) is held near grey (cyanSat) so no stripe
  // reads as an emissive UI accent
  civil: { base: 0.018, gain: 0.07, tint: '#e8ebee', mark: 0.34, markSat: 0.7, cyanSat: 0.15, copperSat: 0.9, sat0: 0.22, sat1: 0.45, matte: 0.3, metal: 1 },
};

// Two-tone schemes (?livery=tone|bone, look-dev v10): the module's own livery stays the base (dark
// or civil), and texels inside its liveryZones (ship-frame boxes, see glbship.js) take a lighter paint:
//   light = (base + gain * l) * tint, l = the texture paint's luminance (its seams, grime, AO and
//   edge wear carry through). Saturated markings, glass and copper keep the base livery's handling;
//   markings on light zones are lifted by `mark` so hazard bands still read on the lighter paint.
//   tone: a warm mid grey, ~2.25x the dark hull's albedo (0.046 -> ~0.105 linear on the remodel paint)
//   bone: the concept art's warm off-white (~0.48 linear on the remodel paint's 0.6), next to charcoal
export const SCHEMES = {
  tone: { scale: 2.25, tint: '#f2ece2', mark: 1.6 },
  bone: { base: 0.004, gain: 0.62, tint: '#ece6dc', mark: 3.2 },
};
export const MAX_ZONES = 16;
// glassDark + glassZones: one list of boxes in the glass shader
export const MAX_GLASS_ZONES = 8;
// Shared clock for the lit-window flicker (effects.js sets it every frame).
export const LIVERY_TIME = { value: 0 };

/** Expand a module's liveryZones ([{ box: [[x,y,z],[x,y,z]], tone = 1, feather = 0.06, mirrorX }], ship frame,
 *  metres) into the uniform arrays; later zones win where they overlap (tone 0 carves a dark zone back out). */
export function zoneUniforms(zones = []) {
  const list = zones.flatMap((z) => (z.mirrorX ? [z, { ...z, box: [[-z.box[1][0], z.box[0][1], z.box[0][2]], [-z.box[0][0], z.box[1][1], z.box[1][2]]] }] : [z])).slice(0, MAX_ZONES);
  const V3 = THREE.Vector3;
  const pad = (a, f) => Array.from({ length: MAX_ZONES }, (_, i) => (a[i] ? f(a[i]) : f(null)));
  return {
    n: list.length,
    min: pad(list, (z) => new V3(...(z ? z.box[0] : [0, 0, 0]))),
    max: pad(list, (z) => new V3(...(z ? z.box[1] : [0, 0, 0]))),
    tf: pad(list, (z) => new THREE.Vector2(z ? z.tone ?? 1 : 0, z ? z.feather ?? 0.06 : 1)),
  };
}

/** Repaint a MeshStandard/Physical material in place. opts: a LIVERIES key or an object
 *  (merged over 'dark'); glassGlow: [r, g, b] linear radiance of lit interiors behind glass
 *  texels (opt-in), glassLit: share of compartments lit (default 0.6); the other glass fields
 *  (glassCell, glassPhase, glassDark, glassZones) are listed in the header. */
export function applyLivery(material, opts = 'dark', { scheme = null, zones = null, toShip = null, kitGlass = false } = {}) {
  const o = { ...LIVERIES.dark, ...(typeof opts === 'string' ? LIVERIES[opts] : opts) };
  // two-tone scheme: only with zones and the mesh's object -> ship-frame matrix
  const sc = scheme && SCHEMES[scheme] && zones?.length && toShip ? SCHEMES[scheme] : null;
  const uniforms = {
    uLivBase: { value: o.base }, uLivGain: { value: o.gain }, uLivTint: { value: new THREE.Color(o.tint) },
    uLivMark: { value: o.mark }, uLivSat: { value: new THREE.Vector2(o.sat0, o.sat1) }, uLivMatte: { value: o.matte },
    // opt-in (default: off, identical shading): texels in the pink / magenta hue band (magentaHue
    // [from, to] degrees, wrapping through red) use their own saturation window magentaSat [s0, s1] and
    // markSat magentaMarkSat, so a lilac-tinted paint reads as grey hull while vivid cargo colours stay
    uLivMagHue: { value: new THREE.Vector2(...(o.magentaHue || [285, 15])) }, uLivMagOn: { value: o.magentaSat ? 1 : 0 },
    uLivMagSat: { value: new THREE.Vector2(...(o.magentaSat || [o.sat0, o.sat1])) }, uLivMagMarkSat: { value: o.magentaMarkSat ?? o.markSat ?? 0.7 },
    uLivMarkSat: { value: o.markSat ?? 0.7 }, uLivCyanSat: { value: o.cyanSat ?? o.markSat ?? 0.7 }, uLivMetal: { value: o.metal ?? 1 }, uLivCopperSat: { value: o.copperSat ?? o.markSat ?? 0.7 },
  };
  const glow = o.glassGlow ? new THREE.Vector3(...o.glassGlow) : null;
  // v11: glassFlicker = share of compartments with a faint unsteady light; glassTint = [warm, cool] radiance
  // multipliers the compartments vary between (most warm, about one in five neutral / cool)
  // glassCell / glassPhase: a number (splatted) or [x, y, z] per axis
  const vec3Of = (v, d) => (Array.isArray(v) ? new THREE.Vector3(...v) : new THREE.Vector3().setScalar(v ?? d));
  if (glow) Object.assign(uniforms, { uLivGlassGlow: { value: glow }, uLivGlassLit: { value: o.glassLit ?? 0.6 }, uLivFlicker: { value: o.glassFlicker ?? 0 }, uLivTime: LIVERY_TIME, uLivCell: { value: vec3Of(o.glassCell, 5) }, uLivPhase: { value: vec3Of(o.glassPhase, 0.37) } });
  // glass zones (needs toShip): glassDark boxes (gain 0: sensor lenses and optics, not cabins) first, then glassZones
  // (mirrorX adds the reflected box); the first box containing a texel wins
  const mirrorBox = ([a, b]) => [[-b[0], a[1], a[2]], [-a[0], b[1], b[2]]];
  const zoneList = glow && toShip ? [
    ...(o.glassDark || []).map((box) => ({ box, gain: 0 })),
    ...(o.glassZones || []).flatMap((z) => (z.mirrorX ? [z, { ...z, box: mirrorBox(z.box) }] : [z])),
  ] : [];
  if (zoneList.length > MAX_GLASS_ZONES) console.warn(`[livery] glassDark + glassZones: ${zoneList.length} boxes, only the first ${MAX_GLASS_ZONES} are used`);
  const gz = zoneList.length ? zoneList.slice(0, MAX_GLASS_ZONES) : null;
  // compartments are laid out in the ship frame (metres) when the mesh's matrix is known: the GLB's own object
  // space is quantised (a node scale of tens to hundreds), where a 7 m cell would span the whole hull
  if (glow && toShip) Object.assign(uniforms, { uLivShipM: { value: toShip.clone() } });
  if (gz) Object.assign(uniforms, {
    uLivZoneN: { value: gz.length },
    uLivZoneMin: { value: Array.from({ length: MAX_GLASS_ZONES }, (_, i) => new THREE.Vector3(...(gz[i] ? gz[i].box[0] : [0, 0, 0]))) },
    uLivZoneMax: { value: Array.from({ length: MAX_GLASS_ZONES }, (_, i) => new THREE.Vector3(...(gz[i] ? gz[i].box[1] : [0, 0, 0]))) },
    // (gain, lit or -1 = glassLit, uniform 0 / 1, unused)
    uLivZoneP: { value: Array.from({ length: MAX_GLASS_ZONES }, (_, i) => (gz[i] ? new THREE.Vector4(gz[i].gain ?? 1, gz[i].lit ?? -1, gz[i].uniform ? 1 : 0, 0) : new THREE.Vector4(1, -1, 0, 0))) },
  });
  if (sc) {
    const z = zoneUniforms(zones);
    const lt = new THREE.Color(sc.tint); const lum = 0.2126 * lt.r + 0.7152 * lt.g + 0.0722 * lt.b; lt.multiplyScalar(1 / lum);
    Object.assign(uniforms, {
      uLivZM: { value: toShip.clone() }, uLivZN: { value: z.n }, uLivZMin: { value: z.min }, uLivZMax: { value: z.max }, uLivZTF: { value: z.tf },
      uLivLight: { value: new THREE.Vector3(sc.base ?? o.base * sc.scale, sc.gain ?? o.gain * sc.scale, sc.mark ?? 1) }, uLivLightTint: { value: lt },
    });
  }
  material.userData.livery = uniforms;
  const prev = material.onBeforeCompile;
  material.onBeforeCompile = (shader, renderer) => {
    prev?.call(material, shader, renderer);
    Object.assign(shader.uniforms, uniforms);
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', '#include <common>\nuniform float uLivBase, uLivGain, uLivMark, uLivMatte, uLivMarkSat, uLivMetal, uLivCopperSat, uLivCyanSat; uniform vec3 uLivTint; uniform vec2 uLivSat, uLivMagHue, uLivMagSat; uniform float uLivMagOn, uLivMagMarkSat; float livGlass; float livL; float livZone;' + (sc ? `
        uniform int uLivZN; uniform vec3 uLivZMin[${MAX_ZONES}], uLivZMax[${MAX_ZONES}]; uniform vec2 uLivZTF[${MAX_ZONES}]; uniform vec3 uLivLight, uLivLightTint; varying vec3 vLivZP;
        float livZoneAt(vec3 p) {
          float z = 0.0;
          // crisp painted edges, antialiased over about a pixel (or the zone's feather, if wider)
          vec3 aa = fwidth(p);
          for (int i = 0; i < ${MAX_ZONES}; i++) {
            if (i >= uLivZN) break;
            vec3 d = min(p - uLivZMin[i], uLivZMax[i] - p);
            vec3 f = max(vec3(uLivZTF[i].y), aa);
            vec3 m = clamp(d / f + 0.5, 0.0, 1.0);
            z = mix(z, uLivZTF[i].x, m.x * m.y * m.z);
          }
          return z;
        }` : ''))
      .replace('#include <map_fragment>', `#include <map_fragment>
        {
          vec3 c = diffuseColor.rgb;
          float l = dot(c, vec3(0.2126, 0.7152, 0.0722));
          float mx = max(c.r, max(c.g, c.b)), mn = min(c.r, min(c.g, c.b));
          float sat = (mx - mn) / max(mx, 1e-4);
          // hue (degrees) of saturated texels: copper / gold conduits, coils and foil sit at 15-45,
          // darker than the orange paint bands (which stay low-visibility grey)
          float hue = 0.0;
          if (mx - mn > 1e-4) {
            if (mx == c.r) hue = mod((c.g - c.b) / (mx - mn), 6.0);
            else if (mx == c.g) hue = (c.b - c.r) / (mx - mn) + 2.0;
            else hue = (c.r - c.g) / (mx - mn) + 4.0;
            hue *= 60.0;
          }
          float copper = smoothstep(10.0, 18.0, hue) * (1.0 - smoothstep(42.0, 52.0, hue)) * (1.0 - smoothstep(0.42, 0.62, mx));
          vec3 grey = (uLivBase + uLivGain * l) * uLivTint;
          livL = l; livZone = 0.0;
          ${sc ? 'livZone = livZoneAt(vLivZP); grey = mix(grey, (uLivLight.x + uLivLight.y * l) * uLivLightTint, livZone);' : ''}
          float cyan = smoothstep(160.0, 172.0, hue) * (1.0 - smoothstep(198.0, 210.0, hue));
          float mSat = mix(mix(uLivMarkSat, max(uLivMarkSat, uLivCopperSat), copper), min(uLivMarkSat, uLivCyanSat), cyan);
          // opt-in pink / magenta band (hue wraps through 360): its own saturation window and markSat
          float hm = hue < uLivMagHue.y ? hue + 360.0 : hue;
          float magenta = uLivMagOn * smoothstep(uLivMagHue.x - 10.0, uLivMagHue.x, hm) * (1.0 - smoothstep(uLivMagHue.y + 360.0, uLivMagHue.y + 370.0, hm));
          mSat = mix(mSat, min(mSat, uLivMagMarkSat), magenta);
          vec2 satWin = mix(uLivSat, uLivMagSat, magenta);
          vec3 mark = mix(vec3(l), c, mSat) * uLivMark; // dimmed low-visibility markings; copper keeps some hue
          ${sc ? 'mark *= mix(1.0, uLivLight.z, livZone * (1.0 - copper));' : ''}
          diffuseColor.rgb = mix(grey, mark, smoothstep(satWin.x, satWin.y, sat));
          // glass: dark, blue-tinted, not strongly saturated (cobalt paint is)
          livGlass = smoothstep(1.12, 1.4, c.b / max(c.r, 1e-3)) * (1.0 - smoothstep(0.05, 0.12, l)) * (1.0 - smoothstep(0.55, 0.75, sat));
          diffuseColor.rgb *= mix(1.0, 0.4, livGlass);
        }`)
      .replace('#include <roughnessmap_fragment>', '#include <roughnessmap_fragment>\nroughnessFactor = mix(mix(roughnessFactor, 1.0, uLivMatte), 0.08, livGlass);')
      .replace('#include <metalnessmap_fragment>', '#include <metalnessmap_fragment>\nmetalnessFactor *= uLivMetal * (1.0 - livGlass);');
    if (sc) {
      shader.vertexShader = shader.vertexShader
        .replace('#include <common>', '#include <common>\nuniform mat4 uLivZM; varying vec3 vLivZP;')
        .replace('#include <begin_vertex>', '#include <begin_vertex>\nvLivZP = (uLivZM * vec4(transformed, 1.0)).xyz;');
    }
    if (glow) {
      shader.vertexShader = shader.vertexShader
        .replace('#include <common>', `#include <common>\nvarying vec3 vLivPos;${toShip ? '\nuniform mat4 uLivShipM;' : ''}`)
        .replace('#include <begin_vertex>', `#include <begin_vertex>\nvLivPos = ${toShip ? '(uLivShipM * vec4(transformed, 1.0)).xyz' : 'position'};`);
      shader.fragmentShader = shader.fragmentShader
        .replace('#include <common>', `#include <common>
          varying vec3 vLivPos; uniform vec3 uLivGlassGlow, uLivCell, uLivPhase; uniform float uLivGlassLit, uLivFlicker, uLivTime;${gz ? `
          uniform int uLivZoneN; uniform vec3 uLivZoneMin[${MAX_GLASS_ZONES}], uLivZoneMax[${MAX_GLASS_ZONES}]; uniform vec4 uLivZoneP[${MAX_GLASS_ZONES}];` : ''}
          float livHash(vec3 p) { return fract(sin(dot(p, vec3(12.9898, 78.233, 45.164))) * 43758.5453); }
          float livNoise(vec3 p) {
            vec3 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
            return mix(mix(mix(livHash(i), livHash(i + vec3(1, 0, 0)), f.x), mix(livHash(i + vec3(0, 1, 0)), livHash(i + vec3(1, 1, 0)), f.x), f.y),
                       mix(mix(livHash(i + vec3(0, 0, 1)), livHash(i + vec3(1, 0, 1)), f.x), mix(livHash(i + vec3(0, 1, 1)), livHash(i + vec3(1, 1, 1)), f.x), f.y), f.z);
          }`)
        .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
          {
            // glass zones (glassDark = gain 0, glassZones): the first box containing the texel sets the gain, the lit
            // share and whether it is one uniform compartment
            float zGain = 1.0, zLit = uLivGlassLit, zUni = 0.0;
            ${gz ? `for (int i = 0; i < ${MAX_GLASS_ZONES}; i++) {
              if (i >= uLivZoneN) break;
              vec3 dd = min(vLivPos - uLivZoneMin[i], uLivZoneMax[i] - vLivPos);
              if (min(dd.x, min(dd.y, dd.z)) > 0.0) { zGain = uLivZoneP[i].x; if (uLivZoneP[i].y >= 0.0) zLit = uLivZoneP[i].y; zUni = uLivZoneP[i].z; break; }
            }` : ''}
            float n = livNoise(vLivPos / uLivCell);
            float lit = smoothstep(1.0 - zLit - 0.12, 1.0 - zLit + 0.12, n);
            // compartments differ: most burn warm, some neutral-cool, levels vary; a few flicker faintly
            vec3 cell = floor(vLivPos / uLivCell + uLivPhase);
            float h1 = livHash(cell + 3.1), h2 = livHash(cell + 17.7);
            // (v12: cool cells rarer and dimmer, like screens; no lit cell sits near the albedo level)
            vec3 tint = h1 > 0.93 ? vec3(0.7, 0.85, 1.1) * 0.7 : h1 > 0.45 ? vec3(1.0, 0.95, 0.86) : vec3(1.14, 0.9, 0.64);
            float level = 0.55 + 0.85 * livHash(cell + 9.3);
            float fl = h2 < uLivFlicker ? 0.84 + 0.16 * sin(uLivTime * (5.0 + 9.0 * h1) + h2 * 60.0) * sin(uLivTime * 1.9 + h1 * 20.0) : 1.0;
            // a uniform zone (bridge, cockpit, CIC): one steady compartment, every pane lit, neutral-warm
            if (zUni > 0.5) { tint = vec3(1.0, 0.95, 0.86); level = 1.0; fl = 1.0; lit = 1.0; }
            // the kit's port and pane glass is only partly caught by the glass test (its texels sit near the
            // thresholds): a lit window glows across its whole pane, so the partial mask is saturated here
            float pane = smoothstep(0.15, 0.6, livGlass);
            // saturation of the paint around the texel (12 taps, 3, 6 and 10 texels out): glass next to saturated paint
            // is a dark stripe of a hazard band or a marking, not a pane
            #ifdef USE_MAP
            {
              float satNear = 0.0;
              vec2 tpx = 1.0 / vec2(textureSize(map, 0));
              for (int i = 0; i < 12; i++) {
                float ring = floor(float(i) / 4.0);
                float a = float(i) * 1.5708 + ring * 0.5236;
                vec3 q = texture2D(map, vMapUv + vec2(cos(a), sin(a)) * tpx * (ring < 0.5 ? 3.0 : ring < 1.5 ? 6.0 : 10.0)).rgb;
                float qx = max(q.r, max(q.g, q.b)), qn = min(q.r, min(q.g, q.b));
                satNear = max(satNear, (qx - qn) / max(qx, 1e-3) * smoothstep(0.08, 0.2, qx));
              }
              pane *= 1.0 - smoothstep(0.32, 0.5, satNear);
            }
            #endif
            ${kitGlass ? `// kit glass (real port / pane geometry, livery.glassParts) fades with its area once a 0.86 m port is under
            // ~2 px: geometry never blurs into the plating the way hull-texture ports do under texture filtering, so a
            // distant crew block would otherwise stay a field of full-bright 1 px specks (a fine scatter of small lights
            // reads as a much bigger structure). vLivPos is in ship-frame metres
            float livMpp = max(length(dFdx(vLivPos)), length(dFdy(vLivPos)));
            float livGpx = 0.86 / max(livMpp, 1e-5);
            pane *= clamp(0.25 * livGpx * livGpx, 0.05, 1.0);` : ''}
            totalEmissiveRadiance += uLivGlassGlow * tint * pane * zGain * (0.06 + 0.94 * lit * level * fl);
          }`);
    }
  };
  const prevKey = material.customProgramCacheKey.bind(material);
  material.customProgramCacheKey = () => `livery${glow ? (toShip ? '-glowS' : '-glow') : ''}${glow && kitGlass ? '-kg' : ''}${gz ? `-zones${gz.length}` : ''}${sc ? `-${scheme}` : ''}|${prevKey()}`;
  material.needsUpdate = true;
  return material;
}
