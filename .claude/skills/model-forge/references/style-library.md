# Style library

The library keeps a family of assets consistent across creations, sessions and agents. It lives in the
repo at `style-library/` so every agent and every future session sees it:

```
style-library/
  README.md                 index of styles, how to use and extend
  styles/<style-id>/
    STYLE.md                art bible in words: identity, forms, palette and livery, materials, scale
                            model and rulers, fixture and lighting standard, hard rules, budgets
    prompts.md              prompts that worked (bible, concept, edit, turnaround, part, material),
                            with model, params and what to avoid
    kits.md                 catalogue of reusable parts (source, size, mount, file), with a pointer to parts.json
    references.md           reference images (paths) and what each is the reference for
    lessons.md              dated lessons: surprise, cause, fix
    assets.md               assets built in this style (size, crew, role, status, files)
```

## Using a style

1. Read `STYLE.md` and `kits.md` before designing anything.
2. Pass the style's reference images to every nano-banana-pro/edit call (the bible sheet plus the
   closest sister asset). For parts, pass the kit's style-reference part.
3. Reuse kit parts at their true size. Follow the scale rulers and the fixture standard.
4. Check new work against `lessons.md` before a reviewer finds the same thing again.

## Starting a new style

When the user starts a new creation that should not look like an existing one:
1. Copy `styles/_template/`, or the closest style, to `styles/<new-id>/`.
2. Write the identity first: three to five sentences on forms, materials, the colour story and the
   mood. Then the scale model: units, sizes of the human-scale rulers.
3. Generate the art bible sheet (nano-banana-pro) and get the user's approval. It becomes the root
   reference.
4. Design the kit's style-reference part, then the rest of the kit. Record them in `kits.md`.
5. Record every prompt that got approved in `prompts.md`.

Styles can share kits. A human-scale door or port can be common to several styles, repainted by
livery. When they share, note it in both `kits.md` files and do not fork the part.

## Feeding it back (after every accepted asset)

- New parts go into the kit (files, parts.json entry, kit sheet thumbnail) and into `kits.md`.
- Approved prompts go into `prompts.md`, with the job ids and why they worked.
- Any rule a reviewer or the user had to enforce goes into `STYLE.md`. Write it as a rule with its
  reason, e.g. "A small craft gets fewer windows, never smaller ones: half-size ports made the
  fighter read 1.5x too big."
- Surprises go into `lessons.md`.
- Add the asset to `assets.md`.

Keep entries short and factual. The library is read at the start of every job, so every line has to
earn its place.
