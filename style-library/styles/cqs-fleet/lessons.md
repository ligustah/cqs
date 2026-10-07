# Lessons (cqs-fleet), newest last

Each lesson gives what happened, why, and what to do instead. Build lessons for individual hulls are
in `Scene3D/tools/blender/hulls/README-<id>.md`.

1. **Franchise drift.** The first fighter concept read like a franchise fighter. Name the forms you
   want, list the forms you exclude, and have a judge check every concept.
2. **Scale drift.** The first concepts were drawn at 16-260 m; the game's slot model put the fleet at
   71-900 m. Everything was re-drawn. Fix the scale model before any image.
3. **Choosing the mesh model.** Image-to-3D bake-offs were decided by three independent judges
   (geometry, texture/PBR, production). Tripo H3.1 multiview won twice. Use multiview from a single 4K
   turnaround sheet, so the views agree.
4. **Mushy detail.** Generated meshes read as "mushy", "wobbly" and without clear structure. Patching
   them failed. Remodelling as parametric hard-surface geometry in headless Blender, with the mesh as a
   blueprint, fixed it.
5. **Reusable parts.** The user's direction was "design a window once, crew door once, then reuse". The
   kits made doors, ports and rails identical across hulls. That is the strongest scale cue the fleet
   has.
6. **Phone crash.** The first artifact crashed on a phone: about 2 GB of GPU textures. Fix: a lite tier
   (`device.js`) with capped textures, lite GLB copies, half the lights and no AO.
7. **Too clean.** The user said "Don't look so clean, a little rougher". Fix: the worn-finish PATINA
   sets, GTAO and a darker studio rig. Stay subtle: "not dirty".
8. **Dark ships.** Dark is the default livery, because dark ships are harder to spot. The lighter
   schemes (tone, bone) are opt-in.
9. **"Make it look alive."** Concept-style amber slits at block corners and recesses do this. The first
   pass made them neon: white cores and wide bloom. The second pass made them dead: thin and dim.
   What works: modest peak, pre-saturated amber, crisp edge, faint spill, about 3 px wide at the hero
   view.
10. **The fighter looked too big.** Causes:
    - half-size ports;
    - a 24-pane bridge grid;
    - about 130 scattered pins, the densest in the fleet;
    - warm bar rows that read as windows at range.

    Fix:
    - glass rebaked at fleet size (2 ports, a 5-pane canopy);
    - authored lights only, 26 lamps;
    - dark ports;
    - a dim canopy.

    Rule: a small craft gets fewer fixtures, never smaller ones.
11. **Fixtures scaled with the hull.** Carrier lamps were 2-3x the size of the corvette's, so the
    carrier read smaller. Fix: one physical size per fixture type fleet-wide.
12. **Dotted columns.** Evenly spaced lamps up a vertical edge read as floors and made an 84 m post
    look like a 7-storey building. Fix: one light per corner, no chains up long verticals.
13. **Range sparkle.** Geometry glass does not blur at range the way texture glass does, so the troop
    ship out-sparkled the destroyer. Fix: kit glass fades with its on-screen area.
14. **False glass.** The glass test lit dark stencils, sensor lenses and gun sights. Fix: a whitelist of
    real kit glass parts (`livery.glassParts`), and dark boxes for hull-texture glass that must stay
    dark.
15. **Split windows.** Compartment cell edges cut ports into two tones, which read as small windows.
    Fix: pick the cell and phase per axis with `tools/lights/cellcut.mjs` so no port is cut.
16. **Workflows.** Multi-agent reviews were thorough but slow: on 4 CPUs, 2 agents at a time, and 49
    agents took about 11 h. Container restarts killed runs. Checkpoint-commit as work lands, keep
    final checks short and inline, and schedule check-ins.
17. **Vehicles drawn too big.** nano-banana-pro draws armoured vehicles 1.2-1.6x too big against a
    1.8 m figure. Metric sizes and "roof 0.7 m above his head" did not fix it. What helped:
    - the figure standing ahead of the nose, clear of the vehicle;
    - body cues tied to the figure ("he could reach up and touch the roof edge", "tyre tops just below
      his hip", "3.5 times his height long").

    The remodel builds to the brief's size anyway.
18. **References leak their content.** The art bible leaked the old 50 m freighter, rainbow containers
    and a miniature carrier into station images. The full parts-kit sheet put its weapon row onto
    station piers as guns. The superseded destroyer concept brought back the tall tower the user
    rejected (correction 4). Use the **current remodel renders** of sister assets and task-specific
    kit crops as references, not the bible or superseded concepts.
19. **Relative scale between two objects** in one image (carrier and freighter, about 0.15) is not
    reached with words: freighters came out at about 0.45 of the carrier. A reference that fills its
    own frame makes its object big. Pass a lineup image at one scale, or no reference for the smaller
    object.
20. **Marking hue drift:** station and yard images took the references' salmon orange (hue about 22°),
    not the style's amber (about 34°). At remodel every mark uses the style's amber material, not the
    image colour.
21. **One-scale lineup reference.** Rulers (trucks, containers, figures) came out 2.5-3x too big next to
    the destroyer. A locally composed reference fixed most of it: the ship render with a 1.8 m person,
    20-ft containers and a 16.5 m semi at one true scale (`v17/shipyard/fix/lineup.py`). The oversize
    fell to about 1.5x in three-quarter views, but not in near top-down views (about 2x).
22. **Docks summon sea ships.** A berth, dry dock or hall made the model draw a sea-going warship or a
    container ship. What fixed it:
    - positive spaceship-hull wording ("flat-sided faceted box hull, the same width bow to stern,
      squared octagonal bow ring round the bore");
    - the octagonal bow turned toward the camera;
    - a short "nothing of a sea ship" list;
    - plain untextured ground, with no quay and no water.
23. **Station references leak hard** (see also 18):
    - the CT-4 render gave copied dark freighters with lit windows;
    - the full CV-50 concept gave turrets and its hangar tube;
    - the frame-filling kit crop gave giant doors and grilled box radiators.

    What worked: one turret-free CV-50 flank crop, with its markings hue-shifted to the style's amber.
    "Floating in a light-grey void" removed the floors and cast shadows (gravity cues) that "a
    physical model in a studio" had produced.
24. **A half-built carrier is hard to draw.** In every image the half-built keel went wrong: a small winged
    hull, toy rings, or a boom projecting past the station. Either show the bay empty, or describe a
    keel lying flat inside the station's outline. Station scale still reads 3-10x too small (coarse
    window rows, big flat panels): unsolved at concept stage. The remodel builds to true size.
25. **Ship-replacement edit.** A "ship under construction in a yard" still came out as a sea-going
    warship, even with the DD-12 reference. Cheaper than regenerating: keep the yard image and edit only
    the ship ("Edit image 1. Keep image 1 exactly as it is... Change ONLY the ship... the DD-12 SPACESHIP
    of image 2... nothing of a sea ship"), refs [yard, DD-12 render, lineup]. It kept the yard almost
    pixel-for-pixel and restored the octagonal bow every time.
26. **Dusk lighting wording** worked first time (prompts.md, Round 3). A dark ground close to the UI
    panel colour (#222d35) loses the icon's outline at 40 px: the icon needs its own lit backdrop.
27. **Lean stations vs icons.** Sizing the station to about 1.2-1.3x the carrier fixed the bulk, but the
    carrier then owns the silhouette and the icons run 1.55-1.73 wide. Anchoring words ("resting on its
    frames", "held only at its stern", "no frame, no ring, no portal surrounds the carrier") stop frames
    returning round the hull.
28. **Image 1 is the edit target.** Passing an earlier concept as image 1 for a FORM change returned it
    nearly unchanged (2 of 3 jobs). For a new form, describe the earlier design in words and pass only
    the ship references. For a local fix (replace the ship), image 1 is right.
29. **Ship replacement may need two passes.** The first fixed the bow; the stern stayed a sea ship.
    A second edit naming the leftovers ("round arched ribs, a curved pointed stern, a propeller, a
    rudder, red-brown bottom paint... the stern ends square at the last octagonal frame, open") fixed it.
30. **"Exactly once" does not hold for station codes.** Three of four r5 images drew SP-3 twice. Paint
    numbers at remodel; do not spend retries on lettering.
31. **Small ships at true scale need a paste.** Words never shrank docked freighters below about 0.3 of
    the carrier. What worked: erase them (OpenCV inpaint), paste light CT-4 cut-outs, then one short,
    narrow edit ("their size and position are exactly right, do not enlarge them... clean up"). The
    model still grows pastes about 1.5x, so paste at about 0.67x the target. A "busier" request
    re-renders the whole image, camera included: do it as a separate step. A luminance-inverted CT-4
    render gives light paint and dark windows (no lit-window leak). Without "a CLOSED boxy crew module
    at the front (no open front, no bore)" freighters copy the carrier's bow.
32. **Ground-vehicle layout follows the hardware rule, not the concept's doors.** A 2.5 m vehicle has only about
    1.45 m of vertical flank, so the brief's 0.9 x 1.3 m doors cannot sit over the wheel arches as concept A drew them
    (its doors were small). Both flank doors went between the arches and the wheelbase opened from 3.5 to 3.8 m; the
    markings took the remaining fields. Check the true-size hardware against the flank before fixing the axles.
33. **Round pins read as headlamps.** 0.2 m lightscape pins on a vehicle nose read as a pair of round headlamps
    (excluded by the brief). Covered lamps are short dim slits at the kit lens (0.16 x 0.05 m).
34. **Turnaround sheets ignore "no labels" and the view count.** The 4K vehicle sheet came back with five views
    and captions; front, left, back and right were still consistent, so they were cropped at one common scale and fed
    to H3.1 rather than paying for a retry.
32. **Phone tier was already over budget.** Lite copies at 1024-2048 px held about 584 MB of GPU
    textures in the default view; the spaceport in the fleet view tipped it over. Fix: per-view loading
    (buildings only in their own view on phones), a `mini` tier (256-512 px) for every ship that is not
    the subject, lite building copies without small dressing, streaming base64 decode, ImageBitmaps
    closed after upload, a failure overlay. Check every view with `tools/phone-check.mjs` before publishing.
35. **Ship finish on a ground unit read as clean and glossy** (correction 34: "way too smooth and clean. Too shiny").
    Causes, measured: the ships' 6 m PATINA tile spanned the 6.5 m body (no surface texture at all), and the ship
    finish's 24 m / 110 m wear scales were one flat value across it; paint roughness ~0.78 gave a broad key-light
    sheen on the bonnet and flanks; no dirt anywhere; and through the dark livery a light-paint bake can only add grey
    tone, never dust, mud or primer. Fix: a reusable `ground` finish preset (matte 0.84-1.0, wear at 2.5 / 9 m, grit
    0.35 m, groundPaint detail at 1.5 m) with a true-albedo ground layer (dust graded up from the ground, mud clumps
    low) applied after the livery so it is continuous over the hull and every kit part; plus baked chips, wheelhouse
    mud, recess grime, run-off streaks and scuffed marks, written with base-colour alpha < 1 so the livery keeps their
    colour (`keep: 1`). Two traps: paint.py's warm crease grime had shifted the recessed windscreen off blue, so the
    livery never treated it as glass (it only looked dark because it was rough); once restored it mirrored the key
    light, so ground units use hazy glass (`glassRough: 0.8`) and the scratch normals skip glass. And PATINA flattens
    "subtle" prompts to nothing: ask for dense, evenly spread damage, then normalise the maps (its normals also carry
    a mean tilt to remove). Ship shaders are untouched (every new option is opt-in; DD-12 studio PSNR 60.7 dB).
36. **Ship bake grime greys a building.** The kit bake's AO grime (full below AO 0.35, gone at 0.985, 0.35 m reach) is
    right for a hull with sparse proud parts; on a building wall framed by proud gunmetal posts, bands and parapets
    every point sits under 0.985 and the whole wall went dark (deuterium depot r1: black pump houses). Buildings use
    grime full only below AO 0.45, gone by 0.88, at 0.6 strength, with a 1.2 m reach (`bkit` sets `lib.BAKE`).
37. **The studio key decides which face reads light.** The ship studio key sits 85 degrees round from the camera; on
    the steel mill that left the long shed face, the one the concept shows lit, in shadow. Building modules set the key
    in their own frame (`studio.sunaz` / `sunel`, colony.js default front-left) to match the concept's light.
38. **+Y-mount parts need `along`.** assemble.py lays a +Y part's +X along `along`, defaulting to the projected `up`;
    passing only `up` (as for +Z parts) turned the yard truck 90 degrees. bkit's helpers take a `heading`.
39. **A perspective concept as image 1 ghosts into a building turnaround.** Both colony turnarounds (deuterium depot,
    steel mill; two tries each, the second with boxed views and "no perspective view anywhere") came back with a
    faded copy of the concept smeared across the middle of the grid, and the depot's TOP view drew four spheres
    instead of three. The elevations were usable for heights and the left-to-right order; the plans were not. For
    buildings, take the plan from the concept by eye (slab edges, the camera estimate in README-colony.md) and use the
    turnaround only as a height reference; do not spend more retries on it.
40. **Isolated component images reconstruct cleanly; whole buildings do not.** All nine pilot components (sphere tank,
    plant house, manifold and filter skids, blast furnace, banded stack, pour bay, skip gallery, shed segment) came
    out of nano-banana-pro/edit (the concept as the only reference, true dimensions stated, light-grey studio, "nothing
    else in frame") and Tripo H3.1 image-to-3d first time, Y-up with the long axis on Z, with the concept's paint,
    frames and wear in the texture. Composing them with the parametric kit took the depot and the mill much closer to
    their concepts than the kit alone (v1 vs v2 sheets).
41. **Make the concept's glow real.** Tripo bakes molten metal, furnace glow and the image's tiny amber lamps into the
    base colour, where they render unlit. `component.py --hot 0.8` copies bright, saturated orange texels into an
    emissive map (darker amber paint stays unlit). And Tripo paint reads a step darker than the concept's off-white
    under the detail layer and worn finish: v2 lifted `colony_*` albedo by 1.25 at runtime (superseded by 48).
42. **A Tripo component's front is usually its +X, and its baked paint can read dark in the dusk studio.** All
    thirteen components of the silicon depot, military base, radio telescope and transmitter came out with the image's
    main face on +X (the civic batch saw the same): check the part sheet (`render-glb.mjs --angles "35:20,0:89"`) and
    turn it with heading -90 rather than trusting the pilots' +Z. A depth the image cannot show is guessed (the vault
    bay came out 17.5 m wide for an 11 m prompt; the ring girder's section square): fix it with `--size` at ingest. And a
    light surface Tripo bakes as mid grey-tan (the radio dish, sRGB ~80 mean) renders brown and dark in the dusk studio
    even after the 1.25 lift: v2 lifted that one material per building (superseded by lesson 48:
    every part is normalised at ingest against its image).
43. **`--hot` can light a whole wall.** An image drawn with a warm-lit interior (the armoured hangar) has large
    bright amber areas, not just lamps: at `--hot 0.8` the back wall became one flat orange panel. Raise the threshold
    (0.93) or prompt the interior dark with small lamps; check the part on `--bg dark`.
44. **Civic massing: read each block's run on the concept, then stretch the part to the concept's proportions.** The
    residence r1-r3 laid its three curved blocks along Z, side by side; the concept wraps them diagonally round the
    courtyard (the tallest from the front-left corner to the back), and only r4 (headings 315 / 300 / 0) read like it.
    Trace each long block's base line on the concept against the two slab-edge directions before placing it. A component
    whose proportions are wrong for the building (the university's faceted wing came out 40 x 17 x 16 m, low and long)
    can be stretched at placement: `K.component(..., scale=[x, y, z])` (Blender part axes: length, depth, height), which
    assemble_place.py already supports; the wings at [0.8, 1.3, 1.35] matched the concept's chunky blocks. Separate
    mirrored masses (the library's two stepped wings) read as two buildings until they overlap behind the centre piece.
    And a glow box placed at a component's facade floats outside its recessed glazing as a flat orange panel: give a
    component's interior light only as a dim box well inside it (radiance <= 0.3) and rely on its `--hot` texels.
45. **Check a raw Tripo mesh's long axis before `--size`, and its glass will be opaque.** Tripo usually puts the long
    axis on Z, but the roof monitor came back long along X: `--size 10,5.5,40` squashed it into a block with its louvre
    band crushed onto one end. Read the raw accessor bbox first and add `--rot 0,90,0` when X is long. The silicon
    foundry's reactor came back with solid light-grey glass: show it through an open mullion grid (no glass pane, bkit
    `glassW` is opaque) and light it with glow boxes inside (violet core, cool wash on the walls and ceiling).
46. **`sunaz` is the key light's azimuth in the building frame, like the camera's `az`.** The refinery's key at -30
    with the camera at 58 lit the faces the camera cannot see and left the block and columns black; a key 0-30 degrees
    toward -X from the camera's azimuth lights the two visible faces like the concepts (refinery 62 / 58, processing
    plant 20 / 50, oil tanks 15 / 45, silicon foundry 0 / 30, steel depot 30 / 38). And mind the sight line under a
    deep roof girder: at 24-26 degrees down the steel depot's crane 16 m behind the front girder was invisible; it sits
    1-5 m behind it now, on lowered runways.
47. **Run `component.py` one at a time.** Each ingest reads, updates and rewrites `assets/parts-colony/parts.json`;
    three parallel ingests (and other agents' ingests) can drop each other's rows. Re-read the manifest after a batch.
48. **Tripo's albedo is darker, warmer and flatter than its own image: normalise it once at ingest, never lift at
    runtime.** v2 compensated with lifts of every size (factory 1.25, modules 1.2-1.6, the radio dish 2.5 with a cool
    tint). Measured over all 50 colony components (surface-weighted texel samples vs the component image's foreground):
    0.84-4.2x darker (median 1.6x), about twice the saturation on neutral paint (the brown cast), and a flattened tonal
    range (the dish face near white, its yoke near black). The ingest itself preserved the values exactly. `component.py`
    now white-balances on neutral texels, pulls near-neutral chroma to the image's, applies one gain to the trimmed
    mean, matches the luminance quantiles at 60 % and caps mean metalness at 0.15 (README-colony.md "Paint calibration").
49. **Calibrate the studio before the paint.** The colony dusk key at 0.5 of the ship studio's rendered even the kit's
    calibrated panel paint at 0.55-0.8x the concepts' light-paint luminance, so every component looked "too dark" twice
    over. Over all 16 buildings key 0.85, fill 0.4, env 0.45 puts the light band at a median 0.95x (key 1.0 alone
    over-lit the big light roofs and slabs and flattened the shadows); six roof- or slab-dominated buildings trim the
    key in their own hint (0.5-0.62) and two low-key ones raise it (1.15), lighting only, never a paint lift. Measure with a real mask: a border-colour or row-median backdrop
    mask counts the radial backdrop's lighter centre as building and reads every shadow as blue; GrabCut seeded by the
    frame border works on both the concepts and the renders (`tools/buildings/paint-check.py`).
50. **A component's per-axis scale is in the part frame (x, y = up, z).** v2's notes said "length, depth, height", so
    the silicon foundry's [1, 1, 0.75] shortened its roof monitors instead of lowering them and the steel depot's crane
    [1, 1.5, 1] grew 1.5x taller instead of spanning 1.5x wider (heavy, and hidden behind the girder).
51. **A big flat glow box reads as a flat panel.** The trade center's 22 x 16 m arcade floor glow became one orange
    slab, the university atrium's warm interior box showed through the glazing as amber-brown panes (its texture was
    cool blue). Use small warm pools and pendant lamps, and a dim cool volume behind glass.
52. **A component mesh is a blueprint; the part is rebuilt (corrections 40-42).** Ingested Tripo components read
    "mushy" at the building camera and "low res" up close however well they are cleaned: the chamfers are soft, the
    facets wavy, rails and lacing melt, and one 2048 texture is stretched over a 60 m furnace. The steel mill v4 rebuilt
    its five components as parametric hard-surface parts measured off the blueprints (`cmeasure.py`: ortho sheets on a
    metre grid, the radial profile and its stations, ledge heights), modelled on the building kit (`ckit.py`: vessel
    from stations, banded stack, gable shed, pour bay, inclined gallery; 2-6 cm bevels, real flanges, laced columns,
    I-beams, railings, ladders, exact openings) and painted in texture space from the kit's calibrated colours
    (`cpaint.py`: plate seams and bolts, corrugation, PATINA tone, AO grime, rust and run-off streaks, edge wear, a
    normal map), same names and anchors, so the building scripts did not change (`remodel.py`).
53. **Weight the UV atlas by what carries texture.** A lattice-heavy part is mostly thin dark structure: with 3 px
    island margins the furnace used 16 % of its atlas (6.5 px/m). 1.5 px margins and per-zone island scales before
    packing (frames 0.45, grating 0.35, interiors 0.25, light shells 1.0) gave the shell 31 px/m at 4096 and the shed's
    cladding 47 px/m. One-sided cladding plates (no inside faces) saved another 17 % of the shed's surface.
54. **Hot zones: dark albedo, bright emission.** The remodelled tuyere windows painted with a light orange albedo took
    the dusk studio's cool fill and tone-mapped to salmon pink; the albedo is now the hot colour at 0.18 and the light
    comes from the emissive map (plus a thin runtime glow box). A 1.8 m tall glow "haze" box over the runner drew as an
    opaque orange slab (lesson 51 again): glow boxes stay thin.
55. **Do not hide the signature behind its own platforms.** The furnace's first full square grating decks (one per
    tower level) covered the shaft from the game camera; the concept shows rings round the shell and walkways along the
    frame with open corners. Likewise the pour bay's solid roof hid the crane: the bay is open on top, the runway lowered
    so the amber bridge girder shows under the front eaves girder (lesson 46).

