# Style library

Styles keep assets consistent across creations. Each style holds an art bible in words, the prompts
that worked, the reusable parts kits, the scale rulers, the lighting fixture standard and the lessons
learned. Every new model starts by reading its style. Every accepted model feeds back into it.

The method that uses the library is the `model-forge` skill (`.claude/skills/model-forge/`), and the
library's layout is described in `.claude/skills/model-forge/references/style-library.md`.

| Style | For | Status |
|---|---|---|
| [`cqs-fleet`](styles/cqs-fleet/STYLE.md) | Conquer-Space reboot spacecraft: naval-industrial, hard-surface, dark operational livery, amber recess lights | five classes built (fighter to 900 m carrier); kits: 31 procedural + 24 fal parts |
| [`_template`](styles/_template/STYLE.md) | copy to start a new style | – |

To add a style: copy `_template/` to `styles/<id>/`, fill in `STYLE.md` (identity and scale first),
generate and approve the art bible, then build the style-reference part and the kit.
