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
