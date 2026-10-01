# Corrections (cqs-fleet)

Every user correction, rejection, preference or praise, in order. The user's words come first (verbatim
where possible), then what was wrong, the fix, and the rule it became. The rule is promoted into
`STYLE.md` (or the noted file). Re-read this file before generating anything for this style.

| # | Asset / stage | The user said | What was wrong | Fix | Rule (where) |
|---|---|---|---|---|---|
| 1 | all / brief | Original IP; never use the old art (`Artwork/**`, `Html/Design/pack/units/*`, `*.blend`) | – | – | Hard rules (STYLE.md) |
| 2 | all / concept | Don't imitate franchise ships (Star Wars, Star Trek, The Expanse, Halo, BSG, Homeworld, EVE) | the first fighter read like a franchise fighter | redesigned as a faceted pod with flank railguns, no wings | Hard rules; name forms positively, never franchises in prompts (prompts.md) |
| 3 | all / scale | (scale model from the game's slots) | concepts were drawn at 16-260 m | fleet re-drawn at 71-900 m | Scale model (STYLE.md) |
| 4 | destroyer / design | "Looks a little weird with that massive tower and relatively little weaponisation" | the tower dominated; it looked under-armed from the side | low armoured command block, broadside sponsons, VLS on open deck | Superstructure low and tiered; armament readable in silhouette (Geometry language) |
| 5 | all / mesh | "Looks very wobbly... lost its clear structure"; "still somewhat mushy in a lot of places" | image-to-3D detail is soft | hard-surface remodel in Blender, generated mesh as blueprint only | Remodel every hero asset (skill) |
| 6 | all / parts | "Design a window once, crew door once, then reuse on all ships" | details differed per hull | parts kits at true size | Kits (kits.md); rulers identical on every hull (STYLE.md) |
| 7 | all / process | "I'm on my phone. I can't open glb files. Can you please show HD renders?" | – | HD renders and an artifact | Show images, not files (skill) |
| 8 | artifact / runtime | "The artifact crashed on my phone" | about 2 GB of textures | lite tier | Phone tier required (lessons.md) |
| 9 | all / finish | "Materials for the hull that don't look so clean... not dirty, a little rougher, or change the lighting so it looks more realistic" | too clean | worn-finish PATINA, GTAO, studio rig | Finish level "worn, not dirty" (Materials) |
| 10 | all / livery | "Realistically it makes sense to have black ships to be harder to spot... it does look better with the lighter touches" | – | dark default; tone and bone opt-in | Dark is the default; light schemes opt-in (Palette) |
| 11 | all / lights | "The main thing would be the lighting... all the small lights the concept art shows. Make it look alive" | hulls looked dead | lightscape: amber slits, pins, windows, beacons | Signature lights (Lights) |
| 12 | all / lights | (verifiers on the user's goal) "neon", "Christmas tree" | white cores, halos, too many bars | hard-edged amber, modest peak, faint spill | Signature look (Lights) |
| 13 | all / lights | "The lights make them look _much_ better" | – (praise) | – | Keep the amber slit language in every later pass (Lights) |
| 14 | fighter / scale | "On the fighter it kind of looks like windows, which distorts scale perception... the fighter looks too big with the small random lights" | half-size ports, a 24-pane bridge, about 130 scattered pins | fleet-size glass (2 ports, 5 panes), 26 authored lamps, dark ports | A small craft gets fewer fixtures, never smaller ones; small craft lit by authored fixtures only (Scale, Lights) |
| 15 | all / scale | "Review all models to ensure the light spots make sense scale-wise" | fixtures grew with the hull; dotted columns; range sparkle | one size per fixture, no dot chains, range fade | Fixture standard F1-F17 / R1-R12 (lighting-standard.md) |
| 16 | freighter / paint | (reviewer) the reactor CT-4 / CT-7 stencil reads like a row of small windows at steep angles | stencil seen edge-on | open | Hull numbers must not read as windows at oblique angles (Palette) |
| 17 | all / budget (2026-10-01) | "We have just about $100 left in credits that we can use on that account" | the library assumed a $120 cap with about $42 left | budget updated | Hard cap: about $100 of fal credit remaining; check spend before each batch (STYLE.md, Hard rules) |
