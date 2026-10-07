// Model tiers of the artifact package (tools/build-artifact.mjs splits each GLB by these; tools/check-package.mjs
// checks the package against them).
// phone-tier dressing left out of the building's scene graph: workers, ladders, hand rails and vents are below a pixel
// on a phone; the bollards stay (amber pins sit on them)
export const LITE_BUILDINGS = {
  'assets/buildings/shipyard.glb': ['parts_ladder', 'parts_rail', 'parts_vent', 'parts_yard-worker'],
  'assets/buildings/spaceport.glb': ['parts_rail'],
};
// colony buildings (src/buildings/colony.js) not listed above: the 1.8 m workers and the kit vents are below a pixel
// on a phone (their amber pins and lamps are lightscape, not geometry, so they stay)
// v6 (steel mill, phone budget 150k tris): the 1 x 2 m kit crew doors too (3-5 px on a phone; their amber door lamps
// are lightscape and stay): ~300 tris each, 10-30 per building
export const LITE_COLONY = ['parts_yard-worker', 'parts_vent', 'parts_door'];
// desktop texture caps by material role, to keep the package inside the limit: the colony buildings' own
// metallic-roughness map (4096 px) goes out at 2048 px; base colour, normals and every ship texture stay as authored
const DESKTOP_ROLE_CAPS = (rel) => (rel.startsWith('assets/buildings/') && !LITE_BUILDINGS[rel] ? { metallicRoughness: 2048 } : {});
export const modelTiers = (rel) => [{ name: 'full', cap: 0, roleCaps: DESKTOP_ROLE_CAPS(rel) }, ...(rel.startsWith('assets/buildings/')
  ? [{ name: 'lite', cap: 512, drop: LITE_BUILDINGS[rel] || LITE_COLONY }]
  : [{ name: 'lite', cap: 1024 }, { name: 'mini', cap: rel.endsWith('carrier.glb') ? 512 : 256 }])];
