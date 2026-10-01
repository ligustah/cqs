# Style library

Styles keep assets consistent across creations. A style holds the constraints for a family of assets:
- the art bible in words and images;
- every correction the user has made (`corrections.md`) and the rule it became;
- the prompts that worked;
- the reusable parts kits;
- the scale rulers and detailed standards (e.g. lighting);
- the lessons learned.

A new style starts from concept-art exploration with the user. Every new model starts by reading its
style. Every correction and accepted model feeds back into it.

The method that uses the library is the `model-forge` skill (`.claude/skills/model-forge/`), and the
library's layout is described in `.claude/skills/model-forge/references/style-library.md`.

| Style | For | Status |
|---|---|---|
| [`cqs-fleet`](styles/cqs-fleet/STYLE.md) | Conquer-Space reboot spacecraft: naval-industrial, hard-surface, dark operational livery, amber recess lights | five classes built (fighter to 900 m carrier); kits: 31 procedural + 24 fal parts |
| [`_template`](styles/_template/STYLE.md) | copy to start a new style | – |

To add a style, follow stage 0 of the skill (`references/style-discovery.md`):
1. interview the user;
2. generate a spread of concept directions, then react and mix;
3. lock an approved art bible;
4. copy `_template/` to `styles/<id>/` and write `STYLE.md` from the decisions.
