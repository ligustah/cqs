# Style library

The library holds everything that is specific to a family of assets: what it must look like, how big
things are, which parts exist, which prompts worked, and every correction the user made. The skill
stays generic; the library carries the constraints. It lives in the repo at `style-library/`, so
every session and agent sees it:

```
style-library/
  README.md                 index of styles
  styles/<style-id>/
    STYLE.md                the constraints: identity, forms, palette and runtime look, materials,
                            rulers and scale model, lighting and emissives, level of detail, budgets,
                            hard rules. Each line is a rule with its reason
    corrections.md          the user's corrections, rejections, preferences and praise, in order,
                            each with the rule it became
    prompts.md              prompts that produced approved images (model, params, job ids), and what
                            to avoid
    kits.md                 reusable parts: source, true size, mount frame, file
    references.md           approved images (art bible, concepts, kit sheets) and what each is the
                            reference for
    lessons.md              technical surprises: cause and fix
    assets.md               assets built in the style: size, role, status, files, open items
    images/                 spread sheets, chosen concepts, the art bible (listed in references.md)
    (optional)              detailed standards, e.g. a lighting standard
```

`styles/_template/` is the starting point. `styles/cqs-fleet/` is a fully worked example: a spacecraft
family with a scale model, two parts kits, a lighting standard and sixteen recorded corrections.

## Using a style

1. Before designing anything, read `STYLE.md`, `corrections.md` and `kits.md`.
2. Pass the style's reference images to every image-edit call: the art bible plus the closest sister
   asset. For parts, pass the kit's style-reference part.
3. Reuse kit parts at their true size, and follow the rulers and standards.
4. When delegating, give each agent the style paths, and quote the constraints that bear on its task.
5. Check `lessons.md` before a known pitfall bites again.

## Capturing corrections (continuous)

Record a correction in the same turn the user makes it.

1. **Append a row to `corrections.md`:**
   - the asset and stage;
   - the user's words, short and verbatim;
   - what was wrong;
   - the fix;
   - the rule, and where it went.
2. **Promote the rule** into `STYLE.md`, if it applies beyond this one asset. `STYLE.md` describes what
   it takes to get an asset right, as positive, measurable rules in the right section. It holds no history:
   no correction numbers, no list of past mistakes, no "the old version did X". Example: "A small asset
   gets fewer windows, never smaller ones." The history stays in `corrections.md`. Rewrite or merge the
   existing rules so the section stays a clean specification, and update any detailed standard that a
   changed number affects.
3. **Record praise as a constraint** ("keep X"), so later passes do not strip what the user liked.
4. **Ask when a correction conflicts with an existing rule.** Do not silently override it. When the user
   decides, mark the old rule superseded, with the date.
5. **Tell the user in one line** what was recorded, so they can correct the rule itself.

Corrections from independent reviewers can be logged too. Mark them "(reviewer)", and only promote
them to `STYLE.md` once the user has accepted the result.

## After every accepted asset

- New parts go into the kit (file, catalogue entry, kit sheet) and `kits.md`.
- Approved prompts go into `prompts.md`, with job ids.
- Technical surprises go into `lessons.md`.
- The asset goes into `assets.md`, with any open items.

Keep entries short and factual. The library is read at the start of every job, so every line must
earn its place.

## Sharing between styles

Styles can share kits or rulers: a human-scale door can be common to several styles, repainted at
runtime. Note the sharing in both `kits.md` files, and do not fork the part. A style variant (e.g. a
civilian sub-language) can be a section in `STYLE.md` instead of a new style.
