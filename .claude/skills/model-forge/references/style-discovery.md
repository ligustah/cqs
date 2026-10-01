# Stage 0: defining a style with the user

The goal is an approved art bible (images) and a `STYLE.md` (written constraints) that every later
asset is built against. Users rarely know the style in words up front. They recognise it in images.
So show them options early and cheaply, and write down what they decide.

## 1. Short interview (one message, answers optional)

- What is being built (asset types, how many, the biggest and the smallest)?
- Where will it be seen: the game camera (isometric, third person, orbital...), its distance, close-ups,
  phone or desktop, real-time or offline? Daylight only, or night and lit interiors?
- Mood, period, realism versus stylisation?
- References liked or disliked, and why?
- Hard taboos: IP or franchises to avoid, legacy art that must not be opened or copied, content limits.
- Budget for generation.
- Real-world anchors: is there a human scale (doors, people) or another ruler the assets must agree
  on? Are proportions realistic, or deliberately exaggerated (big roofs, chunky doors)? An exaggeration
  is fine as long as the style states it, so every asset exaggerates the same way.

Do not block on answers. Make reasonable defaults, say what they are, and let the images do the asking.

## 2. Spread: three to five divergent directions

- Use one subject: the family's most characteristic asset, or a key asset plus a small one, so scale
  shows.
- Use one prompt skeleton, and vary **one or two axes per direction** so the user can tell what they
  are reacting to:
  - form language: faceted versus rounded versus modular versus organic; tall versus squat; symmetric
    versus irregular;
  - construction logic: industrial, civil, military, handcrafted, vernacular, grown;
  - material and finish: for example painted metal, bare alloy, ceramic, composite, timber, stone,
    brick, plaster, thatch, slate, fabric; clean versus weathered;
  - colour story: monochrome with accent, two-tone, high-chroma;
  - realism: photoreal studio model, painterly, stylised low-detail;
  - level of detail and the size of detail relative to the asset.
- **Model:** `fal-ai/nano-banana-pro`, 2K, 4:3 (about $0.15 per image). Show the subject from the
  **game's own camera**: isometric, top-down, third-person. If there is no game camera yet, use a
  three-quarter view. Use a plain background, or a minimal ground plane for buildings and terrain
  pieces. Use the same camera across directions.
- **Avoid named franchises** in prompts, even negatively. Describe forms positively, and add
  "original design".
- **Present** the directions as one labelled sheet (PIL contact sheet, A/B/C/D) with one line each on
  what differs. Send the image, not a path.

## 3. React, mix, repeat

Ask per direction what works and what does not. Users answer with things like "B's shapes with D's
colours, less clutter". Then:
- regenerate with `nano-banana-pro/edit`, passing the liked images as references and stating the mix;
- log every reaction in `corrections.md` while you go (see `style-library.md`): early reactions are the
  most valuable constraints;
- stop when the lock checklist below is complete and the user approves. Two or three rounds is
  typical, at about $2-4 in total. Suggest a budget up front; about $5 for exploration is a sensible
  default.

## 4. Lock the art bible

The lock checklist. Every item has been decided on images and recorded:
- the camera and viewing distance;
- form language and proportions (realistic or a stated exaggeration);
- materials and finish level;
- palette, plus the runtime look if it differs from generation;
- level of detail relative to size;
- emissives or night look (or "none");
- rulers and scale (if any);
- taboos;
- budget.

Then:

1. Generate one sheet with the family: several asset types in the approved language, each captioned, on
   light grey. This sheet is the root reference for every later `/edit` call. Save it in
   `style-library/styles/<id>/images/` and list it in `references.md`.
2. Generate the first small part as the style reference for the parts kit (a door, a panel, a fixture),
   so the kit starts in the right language.
3. Get explicit approval for both.

## 5. Write STYLE.md

Create the style first:
- copy `style-library/styles/_template/` to `style-library/styles/<id>/`;
- add a row to `style-library/README.md`;
- move the spread sheets, the chosen concepts and the art bible into `images/`.

Then fill in `STYLE.md`.

Fill in the template (`style-library/styles/_template/STYLE.md`) from the decisions, not from
imagination:
- identity and what the style is NOT;
- forms and construction logic;
- palette:
  - the generation paint (light, for reconstruction);
  - the runtime look (which may be darker or tinted);
  - marking colours;
- materials and finish level;
- rulers and scale model (if the domain has one);
- lighting and emissive language;
- level of detail per asset size;
- budgets;
- taboos.

Write each line as a constraint with its reason, ideally citing the correction that produced it. Show
the user a short summary and ask what is wrong. That answer is the first correction.

## Changing an existing style

When the user wants a style change that affects assets already built:
1. **Branch the style:** copy it to a new id, or add a dated "v2" section.
2. **Run a smaller spread** around the change only.
3. **Record the decision** in `corrections.md`.
4. **List the assets** that now violate the style in `assets.md` as "needs update". Do not silently
   leave them inconsistent.
