// Building catalogue for the UI (the Buildings menu) and the registry: the 16 colony buildings of the brief
// (style-library/styles/cqs-fleet/briefs/buildings.md) plus the two installations built earlier, grouped like the
// brief. `orbital`: built in orbit (space backdrop, no plinth); every other building stands on its plinth.
// A building opens in the building view only once its module is registered in ships/index.js BUILDINGS; the menu
// lists the rest as planned (disabled).
export const BUILDING_GROUPS = [
  { id: 'production', label: 'Production' },
  { id: 'storage', label: 'Storage' },
  { id: 'civic', label: 'Civic' },
  { id: 'science', label: 'Science' },
  { id: 'military', label: 'Military' },
  { id: 'megaproject', label: 'Megaproject' },
];

export const BUILDING_CATALOG = [
  { id: 'steel_mill', label: 'Steel Mill', gameId: 'STEEL_MILL', group: 'production' },
  { id: 'refinery', label: 'Refinery', gameId: 'REFINERY', group: 'production' },
  { id: 'silicon_foundry', label: 'Silicon Foundry', gameId: 'SILICON_FOUNDRY', group: 'production' },
  { id: 'processing_plant', label: 'Processing Plant', gameId: 'PROCESSING_PLANT', group: 'production' },
  { id: 'steel_depot', label: 'Steel Depot', gameId: 'STEEL_DEPOT', group: 'storage' },
  { id: 'oil_tanks', label: 'Oil Tanks', gameId: 'OIL_TANKS', group: 'storage' },
  { id: 'silicon_depot', label: 'Silicon Depot', gameId: 'SILICON_DEPOT', group: 'storage' },
  { id: 'deuterium_depot', label: 'Deuterium Depot', gameId: 'DEUTERIUM_DEPOT', group: 'storage' },
  { id: 'trade_center', label: 'Trade Center', gameId: 'TRADE_CENTER', group: 'civic' },
  { id: 'infrastructure', label: 'Infrastructure', gameId: 'INFRASTRUCTURE', group: 'civic' },
  { id: 'residence', label: 'Residence', gameId: 'RESIDENCE', group: 'civic' },
  { id: 'radio_telescope', label: 'Radio Telescope', gameId: 'RADIO_TELESCOPE', group: 'science' },
  { id: 'university', label: 'University', gameId: 'UNIVERSITY', group: 'science' },
  { id: 'library', label: 'Library', gameId: 'LIBRARY', group: 'science' },
  { id: 'military_base', label: 'Military Base', gameId: 'MILITARY_BASE', group: 'military' },
  { id: 'shipyard', label: 'Shipyard', gameId: 'SHIPYARD', group: 'military' },
  { id: 'spaceport', label: 'Spaceport', gameId: 'SPACEPORT', group: 'military', orbital: true },
  { id: 'transmitter', label: 'Transmitter', gameId: 'TRANSMITTER', group: 'megaproject', orbital: true },
];
