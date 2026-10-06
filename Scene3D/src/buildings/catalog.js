// Building catalogue for the UI (the Buildings menu) and the registry: the 16 colony buildings of the brief
// (style-library/styles/cqs-fleet/briefs/buildings.md) plus the two installations built earlier, grouped like the
// brief. `orbital`: built in orbit (space backdrop, no plinth); every other building stands on its plinth.
// `built`: modelled (v2, README-colony.md recipe); the menu still enables a building by its ships/index.js entry.
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
  { id: 'steel_mill', label: 'Steel Mill', gameId: 'STEEL_MILL', group: 'production', built: true },
  { id: 'refinery', label: 'Refinery', gameId: 'REFINERY', group: 'production', built: true },
  { id: 'silicon_foundry', label: 'Silicon Foundry', gameId: 'SILICON_FOUNDRY', group: 'production', built: true },
  { id: 'processing_plant', label: 'Processing Plant', gameId: 'PROCESSING_PLANT', group: 'production', built: true },
  { id: 'steel_depot', label: 'Steel Depot', gameId: 'STEEL_DEPOT', group: 'storage', built: true },
  { id: 'oil_tanks', label: 'Oil Tanks', gameId: 'OIL_TANKS', group: 'storage', built: true },
  { id: 'silicon_depot', label: 'Silicon Depot', gameId: 'SILICON_DEPOT', group: 'storage', built: true },
  { id: 'deuterium_depot', label: 'Deuterium Depot', gameId: 'DEUTERIUM_DEPOT', group: 'storage', built: true },
  { id: 'trade_center', label: 'Trade Center', gameId: 'TRADE_CENTER', group: 'civic', built: true },
  { id: 'infrastructure', label: 'Infrastructure', gameId: 'INFRASTRUCTURE', group: 'civic', built: true },
  { id: 'residence', label: 'Residence', gameId: 'RESIDENCE', group: 'civic', built: true },
  { id: 'radio_telescope', label: 'Radio Telescope', gameId: 'RADIO_TELESCOPE', group: 'science', built: true },
  { id: 'university', label: 'University', gameId: 'UNIVERSITY', group: 'science', built: true },
  { id: 'library', label: 'Library', gameId: 'LIBRARY', group: 'science', built: true },
  { id: 'military_base', label: 'Military Base', gameId: 'MILITARY_BASE', group: 'military', built: true },
  { id: 'shipyard', label: 'Shipyard', gameId: 'SHIPYARD', group: 'military', built: true },
  { id: 'spaceport', label: 'Spaceport', gameId: 'SPACEPORT', group: 'military', orbital: true, built: true },
  { id: 'transmitter', label: 'Transmitter', gameId: 'TRANSMITTER', group: 'megaproject', orbital: true, built: true },
];
