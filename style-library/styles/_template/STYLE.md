# Style: <id>

Written at the end of stage 0 (style discovery), from the decisions the user made on concept images.
Each line is a rule with its reason; cite the correction (`corrections.md` #) that produced it.

## Hard rules

- IP rules: originality, legacy art that must not be opened, franchises not to imitate.
- Budget (fal spend cap) and where spend is recorded.

## Identity

Three to five sentences. Name the forms, the construction logic, the materials, the mood and the era.
Say what this style is NOT: forms and looks to avoid.

## Camera and viewing

The game or scene camera (isometric, third-person, orbital ...), the gameplay distance, close-up use,
daylight or night. Review renders always include this view.

## Palette and runtime look

- Generation colours: what the reconstruction images use. Use light neutral paint if a runtime pass
  recolours; otherwise use the real materials.
- Runtime look, if it differs (e.g. a recolour), plus any opt-in variants.
- Markings and accent colours. Calibrate them on renders, not swatches.

## Materials

Material families, finish level (clean, worn, dirty), tiling detail sets (prompts in `prompts.md`), tile
size and detail strengths.

## Scale model and rulers (if the domain has a scale)

- Units and asset sizes, and what drives them (gameplay data, real-world analogues).
- Rulers, identical on every asset of the style (e.g. door, window, fence, step, figure, crate).
  If proportions are deliberately exaggerated, state the factor.

## Emissives and lighting (or "none")

Fixture catalogue (type, physical size, colour, use), budgets per size class, window rules, what must
stay dark, behaviour at range. For a worked example see `../cqs-fleet/lighting-standard.md`.

## Look-dev lighting

Studio and scene rigs (values), tone map, bloom.

## Level of detail

How fine detail is relative to asset size: smallest detail, panel or plank size, bevel width, and how
detail density changes from the smallest to the largest asset.

## Geometry language

Construction (lofts, footprints, roofs, frames, modules), bevel sizes, recess types, symmetry, and which
kit parts are functional or exact.
