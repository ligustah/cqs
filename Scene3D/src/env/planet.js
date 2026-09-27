// Procedural home world below the fleet, at true scale: an Earth-sized globe (6,371 km) seen
// from a 400 km orbit, lit by the same star as the ships.
//
//   - Terrain: domain-warped continents, fold belts and ridged mountains, then fractal detail
//     octaves down to the pixel (about 200 m straight down from orbit); biomes from latitude,
//     moisture and height, in the muted reflectances of real ground seen from orbit; a 3-10 km
//     drainage network (wetter, greener valley floors, paler interfluves), strong in dissected
//     uplands and faint on plains.
//   - Ocean: near-black water with blue shelves whose width follows a low-frequency field, a
//     GGX sun glint and a Fresnel sky sheen that share one Cox-Munk roughness field
//     (basin-scale wind, gusts, long wind rows, sinuous calm slicks), so the wind shows as a
//     faint sheen outside the glint, and calm water and slicks glint silver-bright inside it.
//   - Clouds: one deck ~2.5 km up. Coverage comes from climate bands, synoptic highs / lows,
//     frontal bands and two cyclones; the body is a warped fbm with billowed (cauliflower)
//     octaves down to the pixel, thresholded by coverage into a cover fraction and an optical
//     depth that climbs quickly inside the edge (crisp edges at any distance), mottled in
//     mesoscale cells, with wide soft closed-cell lanes of mixed cell size in stratocumulus
//     (faded in thick decks and toward nadir, where a line network would show). Fair-weather cumulus is a
//     separate field of 0.5-2.5 km cells whose local cover (clumps, streets along the wind)
//     only moves their threshold: a fine speckle from orbit, never solid lobed patches. Lit
//     with two-stream reflectance, a low relief field for the tops and aerial perspective. The
//     deck casts its shadows on the ground (sampled along the sun ray), so cumulus fields show
//     their offset shadows the way they do in orbital photographs.
//   - Night side: warm settlement lights beyond the terminator.
//   - Atmosphere: a separate single-scattering shell (atmosphere.js).
//
// Every noise octave fades out once it is smaller than ~2 pixels (analytic footprint from the
// pixel angle, distance and incidence), so detail scales with camera distance and the shader
// only pays for octaves it can show. Where cells or octaves drop below the pixel their mean
// stands in (partial cover, mean shadow, mean slick area). Stills render the planet at 2 x 2
// supersampling (supersampled()). Nothing is textured: no image is sampled anywhere here.
//
// Placement: the globe is centred on PLANET_DIR at the distance where it subtends
// PLANET_HALF_ANGLE (lighting.js), i.e. the fleet sits ORBIT_ALTITUDE above the surface. All
// lengths are scene metres, so a camera move of a kilometre or two changes nothing on the
// ground, as it should 400 km up.
//
// Rendering: surface and cloud deck are one shader on a full-screen quad that ray-casts both
// spheres per pixel (so cloud parallax is exact, and the ground is skipped under opaque
// cloud); the atmosphere is a second full-screen pass. The group draws in the opaque queue
// before the ships (renderOrder -5) with depth test/write off, so it never z-fights or clips
// against the far plane, and ships always draw over it.
import * as THREE from 'three';
import { SUN_DIR, PLANET_DIR, SUN_E, PLANET_HALF_ANGLE, PLANET_RADIUS } from './lighting.js';
import { NOISE, VIEW_RAY, SCREEN_VERT, viewRayUniforms, bindViewRay } from './glsl.js';
import { ATMO, ATMO_GLSL, createAtmosphereShell } from './atmosphere.js';
import { ENV } from './state.js';

const GM = 3.986e14; // m^3/s^2, Earth: sets the apparent ground speed under the fleet

const query = new URLSearchParams(typeof location !== 'undefined' ? location.search : '');
const vecParam = (k) => {
  const v = query.get(k);
  if (!v) return null;
  const a = v.split(',').map(Number);
  return a.length === 3 && a.every(Number.isFinite) ? a : null;
};

// ---------------------------------------------------------------------------
// GLSL: terrain, biomes, ocean, clouds, city lights (object space = unit sphere,
// +Y = spin axis so |y| is the sine of latitude)
// ---------------------------------------------------------------------------
const WORLD_GLSL = /* glsl */`
#define PI 3.14159265
const vec3 SEED = vec3(17.3, -4.1, 8.6);
const float SEA = 0.07;
const float CLOUD_H = ${ATMO.cloud.toFixed(7)};

// weight of a noise octave of frequency f (per planet radius) at pixel footprint fp:
// 1 while its features span ~3 pixels or more, fading to 0 at ~1.5 px (a simplex lattice cell
// is 1/f; its blobs are about half that)
float lodW(float f, float fp) { return 1.0 - smoothstep(0.3, 0.65, f * fp); }

struct Terrain { float h; float m; float t; float det; float ridge; float belt; float fine; float mid; float drain; float shelf; };

Terrain terrain(vec3 n, float fp) {
  Terrain T;
  vec3 p = n + SEED * 0.1;
  // continental warp: sinuous coasts, gulfs and peninsulas
  vec3 w = vec3(snoise(p * 1.9), snoise(p * 1.9 + vec3(19.1, 7.3, 2.9)), snoise(p * 1.9 + vec3(5.7, 31.3, 13.1)));
  vec3 q = p + w * 0.16;
  // ocean basins, continents, subcontinental shapes
  float c = 0.50 * snoise(q * 1.15 + SEED) + 0.30 * snoise(q * 2.7 + vec3(3.1, 1.7, 5.3))
          + 0.16 * snoise(q * 6.1 + vec3(9.2, 4.4, 0.7));
  // fold belts along the zero set of a second field (plate boundaries)
  float belt = smoothstep(0.72, 0.97, 1.0 - abs(snoise(q * 4.1 + vec3(7.1, 3.3, 9.9))));
  // regional-to-fine fractal: plain fbm for the coasts and plains, ridged multifractal for the
  // mountains; each octave fades out below the pixel
  vec3 r = q + w * 0.03;
  // fine / mid: normalised texture fields from the < 15 km and 25-110 km octaves (they fade to 0,
  // their mean, as their octaves drop below the pixel)
  float det = 0.0, ridg = 0.0, fine = 0.0, mid = 0.0, a = 0.5, f = 13.0, prev = 1.0, wf = 1.0;
  for (int i = 0; i < 13; i++) {
    float g = lodW(f, fp);
    if (g > 0.0) { // no per-pixel break: see cloudAt()
      float s = snoise(r * f + SEED * float(i + 2));
      det += a * g * s;
      float rr = 1.0 - abs(s);
      rr *= rr;
      ridg += a * g * rr * prev;
      prev = clamp(rr * 1.7, 0.0, 1.0);
      if (i >= 5) { fine += 0.42 * wf * g * s; wf *= 0.8; } // < ~15 km: fields, gullies, woods
      else if (i >= 2) mid += 0.55 * g * s;                 // 25-110 km: basins, ranges, forests
    }
    f *= 2.07; a *= 0.53;
  }
  // drainage: a branching valley network at ~3-10 km (a two-octave ridged multifractal in a domain
  // warped by the detail fields, so valleys meander and join): valley floors are wetter, darker
  // and greener, the interfluves paler. Centred on its mean, it fades to 0 below the pixel.
  float gd = lodW(900.0, fp), drain = 0.0;
  if (gd > 0.0) {
    vec3 rd = r + 0.0011 * vec3(det, mid + 0.3 * fine, fine - 0.5 * det);
    float v1 = 1.0 - abs(snoise(rd * vec3(900.0, 960.0, 900.0) + vec3(3.0, 1.0, 7.0)));
    float v1s = v1 * v1; v1s *= v1s;
    float g2 = lodW(2100.0, fp);
    float v2 = g2 > 0.0 ? 1.0 - abs(snoise(rd * 2100.0 + vec3(8.0, 5.0, 2.0))) : 0.0;
    float v2s = v2 * v2; v2s *= v2s;
    // regionally strong (dissected uplands, fold belts) or faint (plains, basins)
    float dAmp = min(0.25 + 0.85 * smoothstep(-0.35, 0.55, snoise(q * 6.3 + vec3(2.0, 9.0, 5.0))) + 0.5 * belt, 1.3);
    drain = gd * dAmp * (v1s - 0.2 + 0.8 * g2 * (v2s - 0.2) * (0.35 + 0.65 * v1));
  }
  T.drain = drain;
  // coastal shelves: their width comes from a low-frequency field (steep coasts with almost none,
  // broad shallow banks elsewhere), not one iso-depth band along every coast
  T.shelf = 0.25 + 2.2 * smoothstep(-0.45, 0.75, snoise(q * 3.3 + vec3(6.0, 2.0, 9.0)) + 0.45 * snoise(q * 9.5 + vec3(1.0, 8.0, 4.0)));
  float h = c + 0.13 * det - SEA;
  float landish = smoothstep(-0.01, 0.06, h);
  h += landish * belt * (0.03 + 0.2 * ridg);
  h += landish * 0.05 * ridg;
  T.h = h;
  T.det = det;
  T.ridge = ridg;
  T.belt = belt;
  T.fine = fine;
  T.mid = mid;
  float lat = abs(n.y);
  // moisture: large weather belts (wet tropics, dry subtropics ~20-32 deg, wet westerlies),
  // regional noise and a coastal gradient
  float mBelt = 0.62 - 0.36 * smoothstep(0.22, 0.34, lat) * (1.0 - smoothstep(0.44, 0.58, lat));
  // regional moisture: continental interiors, rain shadows, basins (~2000, ~600, ~200 km)
  float mReg = 0.34 * snoise(q * 4.3 + vec3(13.0, 2.0, 7.0)) + 0.2 * snoise(q * 13.0 + vec3(4.0, 11.0, 6.0))
             + 0.12 * snoise(r * 38.0 + vec3(8.0, 1.0, 3.0));
  // valleys (low ridged sum) collect water: greener drainage lines through dry country
  T.m = clamp(mBelt + mReg + 0.18 * w.z + 0.28 * (1.0 - smoothstep(0.0, 0.07, h)) + 0.1 * det
            + 0.22 * mid + 0.22 * (0.35 - ridg) - 0.2 * belt * ridg, 0.0, 1.0);
  // temperature: latitude and lapse rate
  T.t = 1.0 - 1.1 * pow(lat, 1.7) - 1.6 * max(h - 0.05, 0.0) + 0.08 * w.x + 0.03 * det;
  return T;
}

// Surface reflectance as seen from orbit (before the atmosphere): dark forests, olive
// grassland, tan steppe, ochre deserts; snow only on high or polar ground.
vec3 landAlbedo(Terrain T) {
  const vec3 RAIN = vec3(0.018, 0.040, 0.020);
  const vec3 FOREST = vec3(0.026, 0.045, 0.028);
  const vec3 BOREAL = vec3(0.020, 0.030, 0.024);
  const vec3 GRASS = vec3(0.070, 0.085, 0.045);
  const vec3 STEPPE = vec3(0.150, 0.130, 0.085);
  const vec3 SAVANNA = vec3(0.160, 0.130, 0.075);
  const vec3 DESERT = vec3(0.330, 0.225, 0.135);
  const vec3 SAND = vec3(0.440, 0.330, 0.205);
  const vec3 TUNDRA = vec3(0.085, 0.085, 0.070);
  const vec3 ROCK = vec3(0.120, 0.105, 0.088);
  const vec3 DARKROCK = vec3(0.055, 0.050, 0.046);
  const vec3 SNOW = vec3(0.78, 0.81, 0.86);
  float m = T.m, t = T.t;
  float fine = clamp(T.fine, -1.0, 1.0);
  // hot lands: erg / desert -> savanna -> rainforest
  vec3 hot = mix(DESERT, SAND, smoothstep(0.0, 0.5, T.det + 0.3 * fine));
  hot = mix(hot, SAVANNA, smoothstep(0.24, 0.4, m));
  hot = mix(hot, RAIN, smoothstep(0.52, 0.7, m));
  // temperate: steppe -> grassland / farmland -> forest
  vec3 mild = mix(STEPPE, GRASS, smoothstep(0.22, 0.42, m));
  mild = mix(mild, FOREST, smoothstep(0.46, 0.64, m + 0.15 * fine));
  vec3 cold = mix(TUNDRA, BOREAL, smoothstep(0.3, 0.55, m));
  vec3 col = mix(mild, hot, smoothstep(0.62, 0.76, t));
  col = mix(cold, col, smoothstep(0.26, 0.4, t));
  // albedo texture: patchwork of fields and woods, gullies, dunes, lava and salt flats
  col *= (0.72 + 0.56 * (0.5 + 0.5 * fine)) * (0.85 + 0.3 * (0.5 + 0.5 * T.mid));
  // drainage: darker, greener valley floors (strongest in dry country, where only they hold
  // vegetation) and paler bare interfluves
  float dry = 1.0 - smoothstep(0.3, 0.62, m);
  float dv = clamp(T.drain, -0.25, 0.8);
  col *= 1.0 - (0.45 + 0.35 * dry) * dv;
  col = mix(col, col * vec3(0.55, 0.95, 0.6), clamp(dv * 1.6, 0.0, 1.0) * dry * smoothstep(0.3, 0.5, t));
  // mountains: bare rock on the ridges, dark old rock in the valleys of the belts
  float rock = smoothstep(0.12, 0.26, T.h) * (0.35 + 0.65 * T.belt);
  col = mix(col, mix(DARKROCK, ROCK, smoothstep(0.35, 0.7, T.ridge)), rock * 0.85);
  // pale beaches / salt pans along dry coasts
  col = mix(vec3(0.34, 0.30, 0.22), col, mix(1.0, smoothstep(0.0, 0.004, T.h), smoothstep(0.55, 0.72, t) * (1.0 - m)));
  float snow = max(smoothstep(0.2, 0.1, t), smoothstep(0.34, 0.46, T.h + 0.08 * T.ridge + 0.03 * fine));
  return mix(col, SNOW, snow);
}

vec3 oceanAlbedo(Terrain T) {
  // water-leaving reflectance: deep water is nearly black, shelves turn blue-green,
  // warm shallow banks turquoise
  const vec3 DEEP = vec3(0.0025, 0.008, 0.022);
  const vec3 MID = vec3(0.004, 0.014, 0.034);
  const vec3 SHELF = vec3(0.010, 0.040, 0.055);
  const vec3 BANK = vec3(0.030, 0.110, 0.115);
  float k = T.shelf;
  vec3 col = mix(DEEP, MID, smoothstep(-0.3, -0.06, T.h));
  col = mix(col, SHELF, smoothstep(-0.05 * k, -0.012 * k, T.h));
  col = mix(col, BANK, smoothstep(-0.018 * k, -0.002 * k, T.h) * smoothstep(0.55, 0.75, T.t) * smoothstep(0.6, 1.4, k));
  // ~15 % darker and less saturated: navy open water, as ISS photos show it
  return mix(vec3(dot(col, vec3(0.2126, 0.7152, 0.0722))), col, 0.85) * 0.85;
}

vec3 rotAxis(vec3 p, vec3 axis, float ang) {
  float c = cos(ang), s = sin(ang);
  return p * c + cross(axis, p) * s + axis * dot(axis, p) * (1.0 - c);
}

// --- clouds ------------------------------------------------------------------
// view-dependent softening of the deck's cell lanes and top relief: 0 oblique .. 1 nadir. Set
// by the deck lookup in main(); shadow lookups use 0.
float cView = 0.0;
// smooth |v|: billowed noise with a rounded crease (a V crease shades as a dotted line)
float sabs(float v, float e) { return sqrt(v * v + e * e); }
// optical depth from a thresholded body value
float cloudTau(float x) { return 70.0 * pow(max(x, 0.0), 1.25); }
// two-stream reflectance of a conservative scattering layer (g ~ 0.85)
float cloudRefl(float tau) { float k = 0.15 * tau; return k / (2.0 + k); }

// The cloud deck at direction n (cloud-deck object space) as vec3(cover, tau, relief): the
// fraction of the pixel covered by cloud, the optical depth of that cloud and the height of
// its tops (radii). fp = pixel footprint (radii), oct caps the body octaves (cheap shadow
// lookups). Octaves below the pixel are dropped; their amplitude widens the threshold into a
// partial cover instead, so a broken field seen from afar keeps its ground showing through (a
// uniform thin layer would veil it). The relief is a separate fbm whose octaves all have the
// same slope (~0.3), so tops stay textured at any distance even where the deck is saturated.
vec3 cloudAt(vec3 n, float fp, int oct) {
  // cyclones: twist the synoptic-scale domain around two storm centres (~1000 km cores);
  // only the large fields follow the spiral, the convective cells stay isotropic
  const vec3 S1 = normalize(vec3(0.37, 0.45, 0.81));
  const vec3 S2 = normalize(vec3(-0.62, -0.38, 0.69));
  vec3 p = rotAxis(n, S1, 2.2 * exp(-(1.0 - dot(n, S1)) * 45.0));
  p = rotAxis(p, S2, -2.0 * exp(-(1.0 - dot(n, S2)) * 55.0));
  // synoptic flow: zonal (east-west) organisation and a large warp for fronts and commas
  vec3 pz = p * vec3(1.0, 1.7, 1.0);
  vec3 w = vec3(snoise(pz * 2.1 + vec3(4.0, 1.0, 8.0)), snoise(pz * 2.1 + vec3(8.1, 2.3, 5.5)), snoise(pz * 2.1 + vec3(3.3, 9.7, 1.1)));
  vec3 q = pz + w * 0.09;
  float lat = abs(n.y);
  // climatology: wet equatorial belt, clear subtropical highs, stormy mid-latitudes
  float clim = 0.5 - 0.24 * smoothstep(0.14, 0.3, lat) * (1.0 - smoothstep(0.42, 0.58, lat)) + 0.1 * smoothstep(0.6, 0.8, lat);
  // weather: highs (clear) and lows (overcast), then long frontal bands
  float wx = 0.62 * snoise(q * 3.1 + vec3(1.3, 7.7, 2.1)) + 0.38 * snoise(q * 7.4 + vec3(6.1, 0.4, 9.3));
  float fr = 1.0 - smoothstep(0.0, 0.1, abs(snoise(q * 1.7 + vec3(2.2, 5.1, 7.7)) + 0.25 * w.x));
  float cov = clim + 0.55 * wx + 0.3 * fr;
  // cloud regime: > 0 cumuliform (sharp, cauliflower), < 0 stratiform (soft, smoother tops)
  float regime = snoise(q * 4.6 + vec3(9.0, 3.0, 5.0)) + 0.3 * w.y;

  // body: synoptic octaves in the twisted, zonally stretched domain, mesoscale octaves in a
  // gently warped one; below ~12 km the octaves are billowed (2|v| - k: rounded tops, sharp
  // crevices) in cumuliform air
  vec3 u = (n + w * 0.05) * vec3(1.0, 1.2, 1.0);
  float bil = smoothstep(-0.2, 0.3, regime);
  // lost = amplitude of the octaves not drawn (faded or dropped). The loops never break on a
  // per-pixel condition: neighbouring pixels leaving a loop on different iterations corrupt the
  // quad's derivatives on software rasterisers (a dotted line along every iso-footprint
  // contour in the relief); skipped octaves cost no noise evaluation.
  float s = 0.0, a = 0.5, f = 11.0, lost = 0.0, rel = 0.0;
  for (int i = 0; i < 14; i++) {
    float g = i < oct ? lodW(f * (i >= 5 ? 2.0 : 1.0), fp) : 0.0;
    if (g > 0.0) {
      float v0 = snoise((i < 3 ? q : u) * f + vec3(1.7, 4.3, 2.9) * float(i));
      float v = i >= 5 ? mix(v0, 2.0 * sabs(v0, 0.1) - 0.78, bil) : v0;
      s += a * g * v;
      // relief uses a stricter LOD: its screen-space derivatives would hatch near the pixel limit.
      // Its billows get a wide, rounded crease: a sharp one shades as a thin dark line, and the
      // zero set of a noise is a polygonal network (a crackle of lines across every deck)
      float vr = i >= 5 ? mix(v0, 2.0 * sabs(v0, 0.45) - 1.0, bil) : v0;
      if (i >= 3) rel += lodW(f * 3.0, fp) * vr * mix(0.02, 0.05, bil) / (f * (1.0 + f * f / 1.5e6));
    }
    lost += a * (1.0 - g);
    f *= 2.08; a *= i < 3 ? 0.5 : 0.62;
  }
  // coverage moves the level set. Cloud edges stay sharp at every scale the pixel resolves: only
  // the unresolved octaves widen the threshold (into a partial cover), plus a trace of softness
  // for stratiform edges
  float x = s - (0.44 - 0.9 * cov);
  float k = 0.3 * lost + mix(0.008, 0.003, bil);
  float cB = smoothstep(-k, k, x);
  // optical depth climbs quickly inside the edge: a thin grey fringe, then white
  float tB = cloudTau(3.0 * max(x, 0.0) + 0.35 * k);
  // decks vary in thickness in soft mesoscale cells (~20 and ~8 km): thin parts go grey, thick
  // parts white, so a deck is mottled rather than one flat white (log-normal, x0.35 .. x2.8)
  float lt = 0.75 * lodW(300.0, fp) * snoise(u * 150.0 + vec3(2.0, 8.0, 4.0));
  if (lodW(840.0, fp) > 0.0) lt += 0.45 * lodW(840.0, fp) * snoise(u * 420.0 + vec3(7.0, 3.0, 1.0));
  tB *= exp(lt * mix(1.0, 0.8, bil));
  // stratocumulus: closed cells of mixed sizes (~8-30 km), thicker cell bodies parted by wide,
  // soft thinner lanes. Two scales are summed so cell size varies, and the lane profile is a
  // broad ramp, not a line: from above a deck reads as a soft cellular modulation of brightness.
  // Lanes fade in thick decks (the cells merge) and toward nadir views (cView), where a crisp
  // network would show; below the pixel they leave their mean thinning.
  float gl = lodW(900.0, fp);
  float cellN = gl > 0.0 ? 0.72 * snoise(u * vec3(300.0, 380.0, 300.0) + vec3(4.0, 2.0, 8.0))
                         + 0.45 * lodW(1600.0, fp) * snoise(u * vec3(690.0, 850.0, 690.0) + vec3(1.0, 7.0, 3.0)) : 0.0;
  float lane = smoothstep(0.02, 0.85, abs(cellN));
  float laneAmp = 0.34 * (1.0 - bil) * (1.0 - 0.55 * smoothstep(40.0, 140.0, tB)) * (1.0 - 0.45 * cView);
  tB *= 1.0 - laneAmp * (1.0 - mix(0.55, lane, gl));
  // tops rise smoothly from the edge inward (a pixel-wide step would shade as an outline)
  float dome = smoothstep(-2.0 * k - 0.02, 2.0 * k + 0.12, x);
  rel = dome * (rel + 0.00008 * sqrt(clamp(tB / 60.0, 0.0, 1.0)));
  // seen from straight above, the tops' relief barely shades (the sun is 40-60 degrees up and the
  // cells are wide and low): fade it toward nadir so thick decks keep soft cells, not a hatching
  rel *= 1.0 - 0.5 * cView;

  // Fair-weather cumulus (shallow convection in partly cloudy air). From 400 km a field is a fine
  // speckle: cells ~0.5-2.5 km across (a few px straight down), denser in mesoscale patches and
  // often lined up in streets along the low-level wind. The mesoscale fields only move the local
  // threshold (how many cells there are), never draw edges themselves, so a field cannot form
  // solid lobed patches. Cells below the pixel leave their mean cover (a grey veil) and, through
  // the ground's shadow lookup, their mean offset shadow.
  float cuMask = smoothstep(0.1, 0.32, cov) * (1.0 - smoothstep(0.55, 0.8, cov)) * smoothstep(-0.5, 0.2, regime);
  float cC = 0.0, cRel = 0.0, tauC = 10.0;
  if (cuMask > 0.001) {
    vec3 uc = n + w * 0.05;
    // cell density: ~60 km patches, ~17 km groups and ~6 km clumps (smooth; std ~0.48)
    float dens = snoise(uc * vec3(110.0, 70.0, 110.0) + vec3(5.0, 1.0, 7.0))
               + 0.7 * lodW(600.0, fp) * snoise(uc * 380.0 + vec3(1.0, 4.0, 2.0))
               + 0.5 * lodW(1500.0, fp) * snoise(uc * 1100.0 + vec3(8.0, 3.0, 5.0));
    // streets: rolls ~4 km apart along the zonal wind (features stretched east-west, meandering
    // with the synoptic warp); they come and go regionally
    float stAmt = smoothstep(-0.1, 0.6, snoise(uc * 38.0 + vec3(9.0, 2.0, 6.0)));
    float st = lodW(2400.0, fp) * snoise((uc + w * 0.0015 + dens * vec3(0.0004, 0.0, -0.0003)) * vec3(600.0, 1700.0, 600.0) + vec3(2.0, 7.0, 3.0));
    // cells: three octaves (~2.3 km, ~1 km, ~0.5 km lattice); thresholded near their peaks they
    // come out as discrete rounded cells, not a connected network
    vec3 ucw = uc + (dens + st) * vec3(0.00012, 0.00005, -0.0001);
    float cu = 0.0, ac = 0.5, fc = 2800.0, lc2 = 0.0;
    for (int j = 0; j < 3; j++) {
      float gj = lodW(fc * 1.3, fp);
      if (gj > 0.0) cu += ac * gj * snoise(ucw * fc * vec3(1.0, 1.12, 1.0) + vec3(3.0, 6.0, 1.0) * float(j + 1));
      lc2 += ac * ac * (1.0 - gj * gj);
      fc *= 2.2; ac *= 0.6;
    }
    // target cover: a few % between the groups, up to ~45 % in the clumps, lines of cells along
    // the streets. The threshold is its normal quantile over the cells' spread (std 0.36 x 0.56),
    // so the mean cover holds whatever the pixel resolves.
    float dl = smoothstep(-0.15, 1.05, dens);
    float cT = clamp(cuMask * (0.015 + 0.36 * dl * dl) * (1.0 + 0.6 * st * stAmt), 0.003, 0.5);
    float tq = sqrt(-2.0 * log(cT));
    float zq = tq - (2.515517 + 0.802853 * tq + 0.010328 * tq * tq) / (1.0 + 1.432788 * tq + 0.189269 * tq * tq + 0.001308 * tq * tq * tq);
    float xc = cu - 0.22 * zq;
    // unresolved cells spread the threshold by their own spread (partial cover of the pixel):
    // smoothstep(-k, k) matches a normal CDF of std k / 1.9
    float kc = 0.012 + 1.9 * 0.36 * sqrt(lc2);
    float on = smoothstep(0.001, 0.06, cuMask); // no seam where the branch switches on
    cC = on * smoothstep(-kc, kc, xc);
    // a sparse population of larger cells (~2-4 km, a few % cover) for the long tail of the size
    // distribution, so a field never looks like one repeated cell
    float gB = lodW(1500.0 * 1.3, fp);
    float cTB = clamp(0.035 * cuMask * dl, 0.001, 0.2);
    float tb = sqrt(-2.0 * log(cTB));
    float zb = tb - (2.515517 + 0.802853 * tb + 0.010328 * tb * tb) / (1.0 + 1.432788 * tb + 0.189269 * tb * tb + 0.001308 * tb * tb * tb);
    float xb = (gB > 0.0 ? gB * snoise(ucw * 1500.0 + vec3(7.0, 2.0, 5.0)) + 0.4 * cu : 0.0) - 0.36 * zb;
    float kb = 0.012 + 1.9 * 0.36 * (1.0 - gB);
    float cBig = smoothstep(-kb, kb, xb);
    cC = on * (1.0 - (1.0 - cC) * (1.0 - cBig));
    // each cell is thick in its core and thin at its rim (tau ~3 at the edge, ~25 in the core of
    // a resolved cell, the big ones thicker): a grey fringe round a white core instead of uniform
    // white specks. Unresolved cells keep the mean (~10).
    float core = smoothstep(0.0, 0.22 + 2.0 * kc, xc);
    tauC = mix(10.0, 3.0 + 24.0 * core, smoothstep(0.1, 0.03, kc));
    tauC = max(tauC, cBig * (8.0 + 30.0 * smoothstep(0.0, 0.25 + 2.0 * kb, xb)));
    float rc = cu;
    // barely any relief (tens of metres): from orbit the cells are not shaded as domes
    cRel = on * lodW(2.0 * 2800.0, fp) * smoothstep(-kc, kc + 0.2, xc) * (0.000006 * rc + 0.000012);
  }
  // combined outside the branch (a max taken only inside it would jump along its edge), smoothly
  float dr = rel - cRel;
  rel = 0.5 * (rel + cRel + sqrt(dr * dr + 4e-10));
  float cover = 1.0 - (1.0 - cB) * (1.0 - cC);
  // small cumulus are optically thinner than decks (tau ~3-25: grey rims, white cores, half-dark shadows)
  float tau = (cB * tB + cC * tauC) / max(cB + cC, 1e-4);
  return vec3(cover, tau, rel);
}

// warm settlement lights for the night side (luminance, ~0..1.5)
float cityLights(vec3 n, Terrain T, float fp, out float warm) {
  warm = 0.5;
  float land = smoothstep(0.004, 0.02, T.h) * (1.0 - smoothstep(0.12, 0.2, T.h));
  float hab = land * smoothstep(0.3, 0.45, T.t) * (1.0 - 0.85 * smoothstep(0.32, 0.14, T.m) * smoothstep(0.58, 0.72, T.t));
  float coast = 1.0 - smoothstep(0.012, 0.07, T.h);
  float region = smoothstep(-0.25, 0.55, snoise(n * 5.0 + vec3(4.0, 9.0, 1.0)));
  float pop = hab * (0.3 + 0.7 * coast) * region;
  if (pop <= 0.002) return 0.0;
  float lights = pop * 0.05;
  for (int k = 0; k < 3; k++) {
    float sc = k == 0 ? 600.0 : (k == 1 ? 1900.0 : 5200.0);
    vec3 c = n * sc;
    vec3 id = floor(c), f = fract(c);
    vec3 r = hash33(id + float(k) * 17.0);
    float present = step(1.0 - pop * (k == 0 ? 0.6 : 0.95), r.x);
    vec3 pt = 0.25 + 0.5 * hash33(id + 3.7);
    float d = length(f - pt);
    float rad = k == 0 ? mix(0.08, 0.22, r.y) : mix(0.05, 0.13, r.y);
    float px = fp * sc;
    float cov = rad * rad / (rad * rad + px * px);
    float s = present * cov * smoothstep(rad + px, rad * 0.15, d) * (0.5 + r.z);
    lights += s * (k == 0 ? 1.2 : (k == 1 ? 0.7 : 0.45));
    if (k == 0) warm = r.z;
  }
  return lights;
}
`;

const PLANET_FRAG = /* glsl */`
uniform vec3 uCenter; uniform float uR; uniform vec3 uSun; uniform float uSunE;
uniform mat3 uWorldToObj; uniform mat3 uWorldToCloud;
uniform float uShowSurface; uniform float uShowClouds;
${VIEW_RAY}
${NOISE}
${ATMO_GLSL}
${WORLD_GLSL}
float D_GGX(float NoH, float a) { float a2 = a * a; float d = NoH * NoH * (a2 - 1.0) + 1.0; return a2 / (PI * d * d); }
float V_GGX(float NoV, float NoL, float a) {
  float a2 = a * a;
  float gv = NoL * sqrt(NoV * NoV * (1.0 - a2) + a2);
  float gl = NoV * sqrt(NoL * NoL * (1.0 - a2) + a2);
  return 0.5 / max(gv + gl, 1e-5);
}
// bump a normal N with a height field h (same units as N's sphere) from screen-space
// derivatives. ok = 0 where the quad's derivatives are unusable (see main): N unchanged.
vec3 bump(vec3 N, float h, float ok) {
  vec3 dpx = dFdx(N), dpy = dFdy(N);
  float dhx = dFdx(h), dhy = dFdy(h);
  vec3 r1 = cross(dpy, N), r2 = cross(N, dpx);
  float det = dot(dpx, r1);
  return abs(det) > 1e-20 && ok > 0.5 ? normalize(N - (dhx * r1 + dhy * r2) / det) : N;
}
// pixel footprint on the sphere (radii) at distance t with view incidence cosine mu. Analytic
// rather than fwidth(): every octave's LOD weight is then smooth across the screen instead of
// stepping per 2x2 quad, and stays defined next to discarded (sky) pixels at the limb.
// The pixel's two axes on the ground are t*a (across the view) and t*a/mu (along it); the
// geometric mean t*a/sqrt(mu) keeps oblique views as crisp across the view as they can be (the
// isotropic 1/mu blurred that axis 3-10x toward the horizon) at the cost of some aliasing along
// it, which the still renders supersample away.
float footprint(float t, float mu) { return pixelAngle() * t * (0.4 + inversesqrt(max(mu, 0.02))); }
void main() {
  vec3 rd = viewRay();
  vec3 ro = (cameraPosition - uCenter) / uR;
  vec3 V = -rd, L = uSun;
  float rc = 1.0 + CLOUD_H;
  vec2 tc = raySphere(ro, rd, rc);
  if (!(tc.x < tc.y && tc.x > 0.0)) discard;
  vec2 ts = raySphere(ro, rd, 1.0);
  float hitS = ts.x < ts.y && ts.x > 0.0 ? 1.0 : 0.0;

  // ---- cloud deck ------------------------------------------------------------
  vec3 Nc = normalize(ro + rd * tc.x);
  vec3 nc = uWorldToCloud * Nc;
  float fpc = footprint(tc.x, dot(Nc, V));
  // screen-space derivatives (bumps, coast anti-aliasing) are trusted only where they agree with
  // the analytic footprint (not across the limb, where quad neighbours were discarded)
  float fdc = length(fwidth(Nc));
  float dOk = fdc > 0.2 * fpc && fdc < 5.0 * fpc ? 1.0 : 0.0;
  cView = smoothstep(0.55, 0.95, dot(Nc, V));
  vec3 cd = uShowClouds > 0.5 ? cloudAt(nc, fpc, 14) : vec3(0.0);
  cView = 0.0;
  float cover = cd.x, tau = cd.y;
  float muVc = max(dot(Nc, V), 0.02);
  // relief of the tops (cauliflower cells, domes), lit from the side
  vec3 Ncb = normalize(mix(Nc, bump(Nc, cd.z, dOk), smoothstep(0.04, 0.2, dot(Nc, V))));
  {
    // a pixel-wide height step would tilt the normal to grazing: cap the slope at ~40 deg
    vec3 tg = Ncb - Nc * dot(Ncb, Nc);
    float sl = length(tg) / max(dot(Ncb, Nc), 1e-3);
    if (sl > 0.85) Ncb = normalize(Nc + tg * (0.85 / sl / max(dot(Ncb, Nc), 1e-3)));
  }
  float muSc = dot(Nc, L);
  vec3 sunC = uSunE * transmittance(rc, muSc) * sunShadow(Nc * rc, L);
  float Rc = cloudRefl(tau);
  // multiple scattering evens out a cloud's lit and shaded faces: relief modulates about a third
  float lit = max(0.65 * muSc + 0.35 * dot(Ncb, L), 0.3 * muSc);
  // self-shadowing: cloud a step toward the sun (~2.9 km along the sun's direction in the deck)
  // that reflects more than the cloud here shades this side of it: the anti-sun flanks of cumulus
  // and the lee sides of deck cells go grey, while a uniform deck (the same both ways) is
  // unchanged. Plus billow lumps, where the pixel resolves them.
  if (cd.x > 0.01) {
    vec3 Lc = uWorldToCloud * L;
    vec3 Lt = Lc - nc * dot(Lc, nc);
    float lt = length(Lt);
    if (lt > 1e-3) {
      float cv0 = cView; cView = 0.0;
      vec3 cs2 = cloudAt(normalize(nc + Lt / lt * 4.5e-4), fpc * 1.2, 8);
      cView = cv0;
      float dS = cs2.x * cloudRefl(cs2.y) - cd.x * cloudRefl(tau);
      lit *= 1.0 - 0.6 * smoothstep(0.0, 0.3, dS);
      // billows: cauliflower lumps (~1.3 km and ~0.5 km) shade the tops, most on thinner cloud and
      // the rims; each octave only where the pixel resolves it
      float thin = 1.0 - 0.6 * smoothstep(8.0, 30.0, tau);
      float b1 = lodW(5000.0 * 1.3, fpc) * (0.5 + 0.5 * snoise(nc * 5000.0 + vec3(3.0, 1.0, 7.0)));
      float b2 = lodW(12000.0 * 1.3, fpc) * (0.5 + 0.5 * snoise(nc * 12000.0 + vec3(9.0, 4.0, 2.0)));
      lit *= 1.0 - thin * (0.2 * b1 + 0.14 * b2);
    }
  }
  // oblique views see the cells' sides too: broken fields close up toward the horizon
  cover = 1.0 - pow(1.0 - cover, mix(1.0, 3.0, pow(1.0 - muVc, 3.0)));
  float aC = cover * (1.0 - exp(-tau / muVc));
  // two-stream reflectance lit by the sun and the sky, plus the faint forward glow of thin edges
  vec3 cloudCol = cover * Rc / PI * (sunC * lit + uSunE * skyIrradiance(muSc) * 0.9);
  cloudCol += (1.0 - Rc) * aC * 0.012 * sunC;
  cloudCol *= transmittance(rc, muVc);
  aC *= uShowClouds;

  // ---- ground ----------------------------------------------------------------
  vec3 N = hitS > 0.5 ? normalize(ro + rd * ts.x) : Nc;
  vec3 n = uWorldToObj * N;
  float fp = footprint(hitS > 0.5 ? ts.x : tc.x, max(dot(N, V), 0.0));
  float aCw = dOk > 0.5 ? fwidth(aC) : 0.1;
  vec3 ground = vec3(0.0);
  // skip the ground where the deck is opaque over the whole pixel neighbourhood
  if (hitS > 0.5 && uShowSurface > 0.5 && aC - 2.0 * aCw < 0.997) {
    Terrain T = terrain(n, fp);
    float aaH = dOk > 0.5 ? max(fwidth(T.h), 1e-6) : 0.002;
    float water = 1.0 - smoothstep(-aaH, aaH, T.h);
    float seaIce = smoothstep(0.1, 0.04, T.t + 0.05 * T.det) * water;
    vec3 alb = mix(landAlbedo(T), oceanAlbedo(T), water);
    alb = mix(alb, vec3(0.62, 0.68, 0.76), seaIce);
    // relief from the height field (land only); ~8 km of height span
    // (faded out toward grazing views: unresolvable there, and derivative noise shows as stipple)
    vec3 Nb = normalize(mix(N, bump(N, max(T.h, 0.0) * 0.0045, dOk), smoothstep(0.12, 0.35, dot(N, V))));

    float muS = dot(N, L);
    float muV = max(dot(N, V), 0.0);
    vec3 sunL = uSunE * transmittance(1.0, muS) * sunShadow(N * 1.00002, L);
    // cloud shadows: the deck where the sun ray from this point crosses it (fewer octaves)
    float cs = 1.0;
    if (uShowClouds > 0.5 && muS > -0.05) {
      vec3 pc = normalize(N + L * (CLOUD_H / max(muS, 0.08)));
      vec3 sh = cloudAt(uWorldToCloud * pc, fp * 1.15, 9);
      cs = 1.0 - sh.x * min(1.15 * cloudRefl(sh.y), 0.9);
    }
    vec3 col = alb / PI * (sunL * max(dot(Nb, L), 0.0) * cs + uSunE * skyIrradiance(muS) * mix(1.0, cs, 0.5));

    // ocean: GGX sun glint and Fresnel sky sheen, both following one roughness field: basin-scale
    // wind, ~40 km gusts, wind rows along the wind and calm slicks (filaments where the surface
    // converges). Inside the glint rough water spreads the sun wider and slicks glint sharp and
    // bright; outside it slicks and calm water mirror more of the bright low sky, so the wind
    // field shows as a faint sheen everywhere, not only in the glint.
    float wet = water * (1.0 - seaIce);
    if (wet > 0.0) {
      float wind = 0.5 + 0.5 * snoise(n * 9.0 + vec3(3.0, 7.0, 1.0)) + 0.25 * snoise(n * 41.0 + vec3(1.0, 2.0, 9.0))
                 + 0.18 * lodW(300.0, fp) * snoise(n * 160.0 + vec3(7.0, 5.0, 2.0));
      // wind rows: long thin streaks ~3 km apart along the wind (ridged, ~20:1)
      float gr = lodW(2600.0, fp);
      float rows = gr > 0.0 ? gr * (1.0 - 2.0 * abs(snoise(n * vec3(130.0, 2600.0, 130.0) + vec3(2.0, 9.0, 4.0)))) : 0.0;
      // slicks: thin sinuous filaments tens of km long, drawn out by eddies (a strongly warped
      // domain, so the ridge lines stretch into streaks instead of closing into rings); their
      // mean area where unresolved
      float g1 = lodW(2200.0, fp), g2 = lodW(5000.0, fp);
      float sl1 = 0.0, sl2 = 0.0;
      if (g1 > 0.0) {
        vec3 ns = n + 0.012 * vec3(snoise(n * 55.0 + vec3(4.0, 4.0, 1.0)), 0.4 * snoise(n * 55.0 + vec3(9.0, 1.0, 6.0)), -snoise(n * 55.0 + vec3(2.0, 7.0, 3.0)));
        sl1 = smoothstep(0.86, 0.975, 1.0 - abs(snoise(ns * vec3(150.0, 480.0, 150.0) + vec3(5.0, 1.0, 3.0))));
        if (g2 > 0.0) sl2 = smoothstep(0.88, 0.98, 1.0 - abs(snoise(ns * vec3(380.0, 1200.0, 380.0) + vec3(1.0, 8.0, 2.0))));
      }
      float slick = clamp(mix(0.05, sl1, g1) + 0.6 * mix(0.04, sl2, g2), 0.0, 1.0) * smoothstep(1.1, 0.4, wind);
      // GGX alpha ~ the Cox-Munk rms slope (mean square slope 0.003 + 0.00512 U): ~0.05 in light
      // air, ~0.1 at 2 m/s, ~0.18 at 6 m/s. Surfactant slicks damp the capillary waves and
      // roughly halve the slope variance: inside the glint they are the brightest, silvery streaks.
      float calm = clamp(wind, 0.0, 1.0);
      float rough = mix(0.052, 0.18, calm * calm) * (1.0 - 0.5 * slick) * (1.0 + 0.07 * rows);
      vec3 H = normalize(L + V);
      float NoH = max(dot(N, H), 0.0), VoH = max(dot(V, H), 0.0), NoL = max(muS, 0.0);
      float F = 0.02 + 0.98 * pow(1.0 - VoH, 5.0);
      // a sharp core (the local slope distribution) over a wider skirt (swell and gust-scale tilt)
      float spec = (0.75 * D_GGX(NoH, rough) * V_GGX(muV, NoL, rough) + 0.25 * D_GGX(NoH, rough * 2.4) * V_GGX(muV, NoL, rough * 2.4)) * F * NoL;
      // sky sheen: the facets of a rough sea tilt toward the viewer, so it mirrors less sky than
      // smooth water at the same angle; the low sky it sees near the horizon is brighter and paler
      float Fv = 0.02 + 0.98 * pow(1.0 - muV, 5.0) * clamp(1.0 - 2.2 * (rough - 0.11), 0.55, 1.1);
      vec3 sky = uSunE * mix(vec3(0.012, 0.028, 0.065), vec3(0.022, 0.04, 0.07), pow(1.0 - muV, 3.0)) * smoothstep(-0.1, 0.3, muS);
      col += wet * (sunL * cs * spec + sky * Fv * mix(1.0, cs, 0.4));
    }

    // city lights beyond the terminator
    float night = smoothstep(0.05, -0.12, muS);
    if (night > 0.0) {
      float warm;
      float cl = cityLights(n, T, fp, warm);
      col += night * cl * mix(vec3(1.0, 0.52, 0.20), vec3(1.0, 0.78, 0.50), warm) * 0.9 * cs;
    }
    // aerial perspective (the atmosphere shell adds the in-scattered light)
    ground = col * transmittance(1.0, muV);
  }
  float aG = hitS * uShowSurface;
  // premultiplied: deck over ground; where the ray only grazes the deck, over the sky
  gl_FragColor = vec4(cloudCol * uShowClouds + (1.0 - aC) * ground, aC + (1.0 - aC) * aG);
}`;

// ---------------------------------------------------------------------------
// Draws `meshes` (full-screen, premultiplied) into an ss x ss target and composites the box-
// filtered result in their place. Re-renders only when the camera, the target size or time()
// changed. Returns the compositing quad (add it where the meshes would have been).
function supersampled(meshes, ss, time) {
  const inner = new THREE.Scene();
  inner.add(...meshes);
  const rt = new THREE.WebGLRenderTarget(1, 1, { type: THREE.HalfFloatType, depthBuffer: false });
  rt.texture.minFilter = rt.texture.magFilter = THREE.LinearFilter;
  rt.texture.generateMipmaps = false;
  const mat = new THREE.ShaderMaterial({
    uniforms: { tPlanet: { value: rt.texture }, uRes: { value: new THREE.Vector2(1, 1) }, uSS: { value: ss } },
    vertexShader: SCREEN_VERT,
    fragmentShader: /* glsl */`
      uniform sampler2D tPlanet; uniform vec2 uRes; uniform float uSS;
      void main() {
        // box filter over the ss x ss texels under this pixel (2 x 2 taps: one per texel at ss 2,
        // bilinear pairs at ss 3)
        vec2 base = floor(gl_FragCoord.xy) * uSS;
        vec2 texel = 1.0 / (uRes * uSS);
        vec4 c = vec4(0.0);
        float n = 0.0;
        for (int j = 0; j < 2; j++) for (int i = 0; i < 2; i++) {
          vec2 o = (vec2(float(i), float(j)) + 0.5) * uSS * 0.5;
          c += texture2D(tPlanet, (base + o) * texel);
          n += 1.0;
        }
        gl_FragColor = c / n;
      }`,
    depthTest: false,
    depthWrite: false,
    blending: THREE.CustomBlending,
    blendEquation: THREE.AddEquation,
    blendSrc: THREE.OneFactor,
    blendDst: THREE.OneMinusSrcAlphaFactor,
  });
  const quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), mat);
  quad.name = 'planet-composite';
  quad.frustumCulled = false;
  const size = new THREE.Vector2(), clear = new THREE.Color();
  let key = '';
  quad.onBeforeRender = (renderer, _scene, camera) => {
    const target = renderer.getRenderTarget();
    if (target) size.set(target.width, target.height); else renderer.getDrawingBufferSize(size);
    mat.uniforms.uRes.value.copy(size);
    const W = size.x * ss, H = size.y * ss;
    if (rt.width !== W || rt.height !== H) rt.setSize(W, H);
    const k = [W, H, time(), ...camera.matrixWorld.elements, ...camera.projectionMatrix.elements].join(',');
    if (k === key) return;
    key = k;
    const autoClear = renderer.autoClear, alpha = renderer.getClearAlpha();
    renderer.getClearColor(clear);
    renderer.setRenderTarget(rt);
    renderer.setClearColor(0x000000, 0);
    renderer.clear(true, false, false);
    renderer.autoClear = false;
    renderer.render(inner, camera);
    renderer.autoClear = autoClear;
    renderer.setClearColor(clear, alpha);
    renderer.setRenderTarget(target);
  };
  return quad;
}

export function createPlanet(scene, {
  radius = PLANET_RADIUS,
  angularRadius = PLANET_HALF_ANGLE, // half-angle subtended from the fleet (deg) -> altitude
  direction = PLANET_DIR,
  orbitRate = null,       // rad/s of apparent ground motion (default: circular orbit at that altitude)
  windRate = 3e-6,        // extra zonal drift of the cloud deck (rad/s, ~20 m/s)
  pole = new THREE.Vector3(-0.597, 0.726, -0.340), // world direction of the north pole at t = 0
  longitude = 0,          // spin about the pole (deg): picks which lands face the fleet
} = {}) {
  const dirOverride = vecParam('envdir');
  const poleOverride = vecParam('envpole');
  const lonOverride = parseFloat(query.get('envlon'));
  const angOverride = parseFloat(query.get('envang'));
  if (Number.isFinite(angOverride)) angularRadius = angOverride;
  const dir = (dirOverride ? new THREE.Vector3(...dirOverride) : direction.clone()).normalize();
  if (poleOverride) pole = new THREE.Vector3(...poleOverride);
  if (Number.isFinite(lonOverride)) longitude = lonOverride;

  const dist = radius / Math.sin(THREE.MathUtils.degToRad(angularRadius));
  const center = dir.clone().multiplyScalar(dist);
  const sunDir = SUN_DIR.clone().normalize();
  if (orbitRate === null) orbitRate = Math.sqrt(GM / dist ** 3);

  const group = new THREE.Group();
  group.name = 'planet';
  group.position.copy(center);
  group.renderOrder = -5;

  // --- ground + cloud deck: one ray-casting shader -----------------------------------
  const hide = new Set((query.get('envhide') || '').split(','));
  const mat = new THREE.ShaderMaterial({
    uniforms: {
      uCenter: { value: center },
      uR: { value: radius },
      uSun: { value: sunDir },
      uSunE: { value: SUN_E },
      uWorldToObj: { value: new THREE.Matrix3() },
      uWorldToCloud: { value: new THREE.Matrix3() },
      uShowSurface: { value: hide.has('surface') ? 0 : 1 },
      uShowClouds: { value: hide.has('clouds') ? 0 : 1 },
      ...viewRayUniforms(),
    },
    vertexShader: SCREEN_VERT,
    fragmentShader: PLANET_FRAG,
    transparent: false,
    depthTest: false,
    depthWrite: false,
    blending: THREE.CustomBlending,
    blendEquation: THREE.AddEquation,
    blendSrc: THREE.OneFactor,
    blendDst: THREE.OneMinusSrcAlphaFactor,
  });
  // a full-screen quad: every pixel ray-casts the deck and the ground, misses are discarded
  const surface = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), mat);
  surface.name = 'planet-surface';
  surface.renderOrder = 0;
  bindViewRay(surface, mat.uniforms);

  // --- atmosphere --------------------------------------------------------------
  const atmosphere = createAtmosphereShell({ radius, center, sunDir, sunE: SUN_E });
  atmosphere.renderOrder = 2;
  if (hide.has('atmosphere')) atmosphere.visible = false;
  if (hide.has('surface') && hide.has('clouds')) surface.visible = false;

  for (const m of [surface, atmosphere]) m.frustumCulled = false;
  // Stills supersample the planet (?planetss=N, default 2 for stills, 1 interactive): the
  // octaves are kept down to ~2 px and the footprint is the geometric mean of the pixel's axes,
  // so oblique ground aliases a little along the view; rendered at N x N and box-filtered it
  // doesn't. The planet renders into its own target once per camera pose and time (a still
  // draws three identical frames) and a quad composites it where the planet would have drawn.
  const ssParam = parseFloat(query.get('planetss'));
  const ss = Math.max(1, Math.min(3, Math.round(Number.isFinite(ssParam) ? ssParam : (query.has('still') ? 2 : 1))));
  if (ss > 1) group.add(supersampled([surface, atmosphere], ss, () => poseT));
  else group.add(surface, atmosphere);
  scene.add(group);

  // Apparent orbital motion: the ground flows under the fleet from bow (+Z)
  // to stern, i.e. a rotation about the axis Z x up through the planet centre.
  const up = dir.clone().negate();
  const orbitAxis = new THREE.Vector3(0, 0, 1).cross(up).normalize();
  const poleDir = pole.clone().normalize();
  const q0 = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), poleDir)
    .multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), THREE.MathUtils.degToRad(longitude)));
  const qGround = new THREE.Quaternion();
  const qCloud = new THREE.Quaternion();
  const qWind = new THREE.Quaternion();
  const Y = new THREE.Vector3(0, 1, 0);
  const m4 = new THREE.Matrix4();

  let poseT = 0;
  function pose(t) {
    poseT = t;
    qGround.setFromAxisAngle(orbitAxis, orbitRate * t).multiply(q0);
    qWind.setFromAxisAngle(Y, windRate * t);
    qCloud.copy(qGround).multiply(qWind);
    m4.makeRotationFromQuaternion(qGround).transpose();
    mat.uniforms.uWorldToObj.value.setFromMatrix4(m4);
    m4.makeRotationFromQuaternion(qCloud).transpose();
    mat.uniforms.uWorldToCloud.value.setFromMatrix4(m4);
  }
  pose(0);

  ENV.planet = { center, radius, top: ATMO.top, group };

  return {
    group,
    radius,
    center,
    sunDir,
    altitude: dist - radius,
    update(t) { pose(t); },
  };
}
