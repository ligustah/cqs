# Brief: the colony buildings (16)

**Source:** the user's approved concepts (correction 35), `images/buildings/<id>-concept.jpg`. They
were made with an image model; an earlier procedural Blender pass (`<id>-old-render.jpg`) fell short of
them. The target is the concept. The shipyard and spaceport stay as built (`assets/buildings/`).

| id | game building | concept in one line |
|---|---|---|
| steel_mill | STEEL_MILL | blast furnace tower with skip hoist, glowing pour bay, three stacks, long shed |
| refinery | REFINERY | three tall distillation columns in lattice, pipe racks, control block, horizontal tanks |
| silicon_foundry | SILICON_FOUNDRY | long sawtooth-roof fab hall, glazed bay showing a violet-lit reactor |
| processing_plant | PROCESSING_PLANT | three tall banded process vessels, a low round tank, pipe manifolds, plant house |
| trade_center | TRADE_CENTER | two towers joined by a sky bridge, glazed arcade between, annex block |
| infrastructure | INFRASTRUCTURE | cross-plan admin block round a domed hub, courtyard trees, water tower, utilities |
| residence | RESIDENCE | curved terraced apartment blocks with balconies and roof gardens round a courtyard |
| steel_depot | STEEL_DEPOT | open-sided portal shed with an amber overhead crane over stacked beams |
| oil_tanks | OIL_TANKS | three large floating-roof tanks in a bunded yard, pump house, pipe manifold |
| silicon_depot | SILICON_DEPOT | tall monolithic vault block with dark rack bays and violet accent strips |
| deuterium_depot | DEUTERIUM_DEPOT | three spherical tanks on legs with cobalt bands, pipe manifold, pump houses |
| military_base | MILITARY_BASE | walled compound, two armoured vehicle hangars, command block, corner towers |
| radio_telescope | RADIO_TELESCOPE | large dish on an alt-az mount over an armoured base building |
| university | UNIVERSITY | three faceted wings with observatory domes round a glazed atrium and garden |
| library | LIBRARY | stepped monumental archive block, tall glazed central slot, grand stair |
| transmitter | TRANSMITTER | orbital hexagonal ring (megaproject), glowing blue inner field, solar wings, modules |

**What the concepts have that the old renders lacked** (the fidelity checklist):
- a chamfered concrete **plinth slab** with edge lamps, kerbs and markings;
- **contrast**: off-white panels framed by dark gunmetal posts, beams, bands and plinths; not flat grey;
- **dense secondary detail**: pipe runs with flanges and amber rings, catwalks, railings, ladders, roof
  units, vents, cable trays, small vehicles and crates;
- **light**: warm lit windows, amber lamps on corners and plinth edges, door lamps, a few floods; the
  dusk-blue studio;
- **wear**: panel-to-panel tone, grime under edges, streaks; worn, not dirty;
- **depth**: recesses, layered volumes, shadowed bays.

**Rules that apply:** STYLE.md Installations (light paint, lights and small detail, depth), Thumbnail
readability (each building identifiable at 80 / 40 px and distinct from the others), Reuse first
(shared components, kit parts, PATINA), Phone first (per-view loading, phone budget per building).
Sizes are real-world and plausible for the function; record each footprint and height in the module.
