# Brief: Vehicle (ground unit)

**Game source (code only; legacy art not opened):**
- `UnitEnum.VEHICLE` ("jeep"), class `UnitClassEnum.VEHICLE`.
- Class description: "Armoured they are usually track vehicles, which can overcome areas with an
  aclivity of up to 60%. Depending on the design of the vehicle, it can be a fast moving jeep or a very
  resistant tank."
- Modules: SURFACE_SPEED, SURFACE_ATTACK (research: rocket battery), SURFACE_DEFENSE (research: plating).
  Ten variants. The DEFENSE builds switch to a "panzer" (tank) chassis.
- Built in the MILITARY_BASE. Ground-transport size 3: infantry 1, aircraft 4. A CT-7 transport carries
  750 units.

**What to build:** the base unit only, the "jeep" chassis. It is a fast, armoured, all-terrain combat
vehicle with a crew of 2-4. **Modules are out of scope for now** (user, 2026-10-01, correction 18; the
ships ignored them too).
- No rocket-battery pods, no drop-in mission beds, no add-on armour kits, no speed packs.
- No "modular platform" as a design theme.
- At most one modest integral weapon mount (e.g. a small remote weapon station) as part of the chassis.
- Judges: fail a direction whose main idea is a module or launcher. The tank chassis and the module
  variants come later.

**Scale:** real-world, anchored by the style's human rulers (1 x 2 m door, 1.8 m crew figure, 1.1 m
rails).
- **Cross-check against the game's numbers:**
  - the CT-7's habitats hold about 10,600 m³ for 750 ground units, about 14 m³ per unit;
  - a vehicle (3 units) is therefore about 42 m³ of envelope, roughly 6.5 x 2.6 x 2.5 m. That is a
    light armoured vehicle, so the game's numbers and real-world size agree.
- **Target:** length 6-7 m, width about 2.6 m, height about 2.5 m.

**Must read as:** a compact, fast, armoured ground vehicle from the same shipyards as the fleet. Signals:
- faceted armour, chamfers and layered plates;
- the fleet's rulers (hatches, rails and lamps at true size);
- hull-number stencil, amber hazard marks, small cobalt band.

It must not read as a spaceship, or as any franchise's vehicle.

**Chosen direction (user, 2026-10-01, correction 19): A, the tall-cab wheeled 4x4.** No turnaround or
modelling until the shipyard and spaceport concepts are settled too (correction 23). Concept:
`images/spread-vehicle-r1-A.jpg` (full size: fal `Dkvm0JP61YPXyEqM0fJZB_jqd1dpC9.png`, job
01a0f526-d773-7b82-893b-b221ac520902).
- **Keep:** a tall faceted crew cab whose roof runs unbroken to the tail; a chamfered octagonal cross-section;
  four big tyres in faceted arches, with independent suspension visible; the gunmetal octagonal nose
  collar and belly band; a small remote weapon station behind two round roof hatches; a louvred side
  vent; a rear-flank door; amber corner hatching, one amber flank band, the cobalt square and V-31.
- **Fix at remodel:** the image drew it about 1.5x too big against the figure. Build it to 6.5 x 2.6 x
  2.5 m (body), with the weapon station to about 2.9 m and tyres about 1.1-1.2 m.
- **Hardware at real vehicle size:** side and rear doors about 0.9 x 1.3-1.4 m, roof hatches 0.7-0.8 m,
  armoured panes about 0.6-0.9 m wide. The ship's 2 m crew door does not fit a 2.5 m vehicle and is not
  used. Rails (1.1 m where free-standing, grab rails elsewhere), lamp sizes, the stencil font and the
  1.8 m figure stay the fleet's.
- **Livery:** the ground-livery question was not answered, so the fleet default stands: dark
  operational grey (correction 10). Sand stays an opt-in scheme.
- **Lights:** authored fixtures only (small-craft rule), a handful: covered convoy and marker lamps,
  no round headlamps, no light bars.
- **Thumbnail:** the tall cab, the big wheels and the weapon station must read at 80 px and stay
  distinct from the ships at 40 px (STYLE.md, Thumbnail readability).

**Open design choices in r1** (decided above):
- tracked vs wheeled vs hybrid;
- the body form (low wedge, tall cab, sponsoned);
- the ground livery: the fleet's dark operational grey, or a terrain tone.

**Where it is seen:** the game's square unit icon (80 and 40 px); the studio view (`mode=ship`) and the
lineup beside a 1.8 m figure. A ground diorama scene does not exist yet (not decided by the user).
