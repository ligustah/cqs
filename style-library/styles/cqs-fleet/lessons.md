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
