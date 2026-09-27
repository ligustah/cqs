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

/** Repaint a MeshStandard/Physical material in place. opts: a LIVERIES key or an object. */
export function applyLivery(material, opts = 'dark') {
  const o = { ...LIVERIES.dark, ...(typeof opts === 'string' ? LIVERIES[opts] : opts) };
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
  material.userData.livery = uniforms;
  const prev = material.onBeforeCompile;
  material.onBeforeCompile = (shader, renderer) => {
    prev?.call(material, shader, renderer);
    Object.assign(shader.uniforms, uniforms);
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', '#include <common>\nuniform float uLivBase, uLivGain, uLivMark, uLivMatte, uLivMarkSat, uLivMetal, uLivCopperSat, uLivCyanSat; uniform vec3 uLivTint; uniform vec2 uLivSat, uLivMagHue, uLivMagSat; uniform float uLivMagOn, uLivMagMarkSat; float livGlass;')
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
          float cyan = smoothstep(160.0, 172.0, hue) * (1.0 - smoothstep(198.0, 210.0, hue));
          float mSat = mix(mix(uLivMarkSat, max(uLivMarkSat, uLivCopperSat), copper), min(uLivMarkSat, uLivCyanSat), cyan);
          // opt-in pink / magenta band (hue wraps through 360): its own saturation window and markSat
          float hm = hue < uLivMagHue.y ? hue + 360.0 : hue;
          float magenta = uLivMagOn * smoothstep(uLivMagHue.x - 10.0, uLivMagHue.x, hm) * (1.0 - smoothstep(uLivMagHue.y + 360.0, uLivMagHue.y + 370.0, hm));
          mSat = mix(mSat, min(mSat, uLivMagMarkSat), magenta);
          vec2 satWin = mix(uLivSat, uLivMagSat, magenta);
          vec3 mark = mix(vec3(l), c, mSat) * uLivMark; // dimmed low-visibility markings; copper keeps some hue
          diffuseColor.rgb = mix(grey, mark, smoothstep(satWin.x, satWin.y, sat));
          // glass: dark, blue-tinted, not strongly saturated (cobalt paint is)
          livGlass = smoothstep(1.12, 1.4, c.b / max(c.r, 1e-3)) * (1.0 - smoothstep(0.05, 0.12, l)) * (1.0 - smoothstep(0.55, 0.75, sat));
          diffuseColor.rgb *= mix(1.0, 0.4, livGlass);
        }`)
      .replace('#include <roughnessmap_fragment>', '#include <roughnessmap_fragment>\nroughnessFactor = mix(mix(roughnessFactor, 1.0, uLivMatte), 0.08, livGlass);')
      .replace('#include <metalnessmap_fragment>', '#include <metalnessmap_fragment>\nmetalnessFactor *= uLivMetal * (1.0 - livGlass);');
  };
  const prevKey = material.customProgramCacheKey.bind(material);
  material.customProgramCacheKey = () => `livery|${prevKey()}`;
  material.needsUpdate = true;
  return material;
}
