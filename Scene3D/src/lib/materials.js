// Shared PBR material palette for the reboot fleet livery.
//
// Livery: bone-white composite hull, signal-orange command markings, cobalt
// trim, gunmetal armour, gold MLI foil on sensors, cyan plasma drives.
// Ship modules reference materials by name (e.g. 'hull', 'accent', 'glass').
import * as THREE from 'three';
import { panelSet, foilSet, radiatorSet, windowStrip, hazardStripes, decalTexture } from './textures.js';

export const LIVERY = {
  hull: '#e7e3da',
  hullShade: '#c9c6bf',
  accent: '#ff5a14',     // signal orange
  cobalt: '#2152ff',     // vivid cobalt trim
  teal: '#12c2b0',
  armor: '#59606c',
  gunmetal: '#2b3038',
  steel: '#b9c0c9',
  darkSteel: '#3b3f46',
  gold: '#e0a84a',
  copper: '#c7703f',
  ceramic: '#1d1f23',
  engine: '#62dcff',     // plasma drive core
  engineHot: '#ffb36b',
  navRed: '#ff2a2a',
  navGreen: '#2bff6a',
  strobe: '#ffffff',
  amber: '#ffae3b',
};

function physical(params) {
  return new THREE.MeshPhysicalMaterial(params);
}

export function createPalette() {
  const hullTex = panelSet({ seed: 7, style: 'hull' });
  const armorTex = panelSet({ seed: 21, style: 'armor', strength: 2.6 });
  const tileTex = panelSet({ seed: 33, style: 'tiles', strength: 1.6 });
  const deckTex = panelSet({ seed: 45, style: 'deck', strength: 1.4 });
  const foil = foilSet({ seed: 11 });
  const rad = radiatorSet();
  const win = windowStrip({ seed: 5 });

  const painted = (color, { gloss = 0.35, tex = hullTex, metal = 0.05, normalScale = 0.8 } = {}) => physical({
    color: new THREE.Color(color),
    map: tex.map, roughnessMap: tex.roughnessMap, normalMap: tex.normalMap,
    normalScale: new THREE.Vector2(normalScale, normalScale),
    roughness: 0.95, metalness: metal,
    clearcoat: gloss, clearcoatRoughness: 0.28,
    envMapIntensity: 1.0,
  });

  const P = {
    // painted composite hull
    hull: painted(LIVERY.hull, { gloss: 0.3 }),
    hullShade: painted(LIVERY.hullShade, { gloss: 0.2 }),
    accent: painted(LIVERY.accent, { gloss: 0.6 }),
    cobalt: painted(LIVERY.cobalt, { gloss: 0.6 }),
    teal: painted(LIVERY.teal, { gloss: 0.55 }),
    // structural metals
    armor: painted(LIVERY.armor, { gloss: 0.1, tex: armorTex, metal: 0.55, normalScale: 1.0 }),
    gunmetal: physical({ color: LIVERY.gunmetal, metalness: 0.85, roughness: 0.38, map: armorTex.map, normalMap: armorTex.normalMap, normalScale: new THREE.Vector2(0.6, 0.6) }),
    steel: physical({ color: LIVERY.steel, metalness: 1.0, roughness: 0.26, roughnessMap: hullTex.roughnessMap }),
    darkSteel: physical({ color: LIVERY.darkSteel, metalness: 1.0, roughness: 0.42 }),
    copper: physical({ color: LIVERY.copper, metalness: 1.0, roughness: 0.3 }),
    gold: physical({ color: LIVERY.gold, metalness: 1.0, roughness: 0.7, map: foil.map, roughnessMap: foil.roughnessMap, normalMap: foil.normalMap, normalScale: new THREE.Vector2(1.2, 1.2) }),
    ceramic: physical({ color: LIVERY.ceramic, metalness: 0.0, roughness: 1.0, map: tileTex.map, roughnessMap: tileTex.roughnessMap, normalMap: tileTex.normalMap }),
    deck: physical({ color: '#4a4f57', metalness: 0.4, roughness: 1.0, map: deckTex.map, roughnessMap: deckTex.roughnessMap, normalMap: deckTex.normalMap }),
    // canopy / bridge glazing
    glass: physical({ color: '#0d1c26', metalness: 0.0, roughness: 0.03, clearcoat: 1.0, clearcoatRoughness: 0.02, ior: 1.52, specularIntensity: 1.0, envMapIntensity: 1.8 }),
    // lit habitation windows
    windows: physical({ color: '#ffffff', map: win.map, emissive: '#ffffff', emissiveMap: win.emissiveMap, emissiveIntensity: 2.2, roughness: 0.35, metalness: 0.2 }),
    // thermal
    radiator: physical({ color: '#30353c', map: rad.map, normalMap: rad.normalMap, emissive: '#ff5a1e', emissiveMap: rad.emissiveMap, emissiveIntensity: 0.9, metalness: 0.7, roughness: 0.45 }),
    hazard: physical({ color: '#ffffff', map: hazardStripes(), roughness: 0.6, metalness: 0.0 }),
    // emissives (bloom)
    engine: new THREE.MeshStandardMaterial({ color: '#000000', emissive: LIVERY.engine, emissiveIntensity: 9 }),
    engineHot: new THREE.MeshStandardMaterial({ color: '#000000', emissive: LIVERY.engineHot, emissiveIntensity: 5 }),
    navRed: new THREE.MeshStandardMaterial({ color: '#000000', emissive: LIVERY.navRed, emissiveIntensity: 6 }),
    navGreen: new THREE.MeshStandardMaterial({ color: '#000000', emissive: LIVERY.navGreen, emissiveIntensity: 6 }),
    strobe: new THREE.MeshStandardMaterial({ color: '#000000', emissive: LIVERY.strobe, emissiveIntensity: 8 }),
    amber: new THREE.MeshStandardMaterial({ color: '#000000', emissive: LIVERY.amber, emissiveIntensity: 5 }),
    cyanLight: new THREE.MeshStandardMaterial({ color: '#000000', emissive: '#7fe8ff', emissiveIntensity: 5 }),
    hangarGlow: new THREE.MeshStandardMaterial({ color: '#000000', emissive: '#ffd9a0', emissiveIntensity: 2.5 }),
  };

  const paintCache = new Map();
  /** Painted hull in any colour (containers, squadron markings). */
  P.paint = (hex, opts = {}) => {
    const k = hex + JSON.stringify(opts);
    if (!paintCache.has(k)) paintCache.set(k, painted(hex, opts));
    return paintCache.get(k);
  };

  const decalCache = new Map();
  /** Transparent text decal material, e.g. P.decal('CV-01', { color: '#ff5a14' }). */
  P.decal = (text, opts = {}) => {
    const k = text + JSON.stringify(opts);
    if (!decalCache.has(k)) {
      decalCache.set(k, new THREE.MeshStandardMaterial({
        map: decalTexture(text, opts), transparent: true, roughness: 0.5, metalness: 0.0,
        polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -4, depthWrite: false,
      }));
    }
    return decalCache.get(k);
  };

  // tag names so ShipBuilder can group merged meshes by material identity
  for (const [k, v] of Object.entries(P)) if (v && v.isMaterial) v.name = k;
  return P;
}
