# Fleet lighting scale standard (v14)

> **How to read this file.** Sections 1-5 and 8 are the standing standard: fleet rules R1-R12, fixture
> catalogue F1-F17 and tiers, window rules, per-class budgets, shared renderer behaviour, verification. This
> table is authoritative over the summaries in `STYLE.md` and the skill. Sections 0, 6 and 7 are the historical
> work order of the v14 scale pass: the per-ship actions are done, and their line numbers and the working-tree
> notes are stale. The drafts and overrides it mentions were scratch files and were not kept. The audit tools
> are in `Scene3D/tools/lights/` (`audit.mjs` calls this file "STANDARD.md"). Budgets for a new class are set
> by the rule in `STYLE.md` (Lights).

Merges `draft-practice.md` (real-craft practice) and `draft-perception.md` (how viewers read size from lights).
Checked against the five ship surveys, the light harness and the current renders. Read-only pass: no repo file
was edited. Every per-ship count below was measured with the audit harness on a tested override (section 8).

The user's request: keep the amber slit language and the sense of life, but every light must make sense for the
ship's real size, crew and role. No light may make a ship read bigger or smaller than it is.

## 0. Diagnosis and the standard in one paragraph

Three light cues set the size a viewer reads. Today all three are wrong somewhere:

1. **The ruler.** A lit rectangle reads as a 1 m window, and a viewer measures the hull in windows. The fighter
   had 36 ports of 0.55 m glass and a grid of 0.58-0.7x panes, so it read 1.4-1.8x its length. The carrier's
   0.87 m brow bars and its frame-post "window box" read as windows and doors, so it read smaller.
2. **The grain.** A fine, even scatter of small lights reads as a big inhabited structure. The fighter carried
   20 lamps per 1000 m2 against the corvette's 13, the destroyer's 6 and the carrier's 1.2.
3. **The fixture size.** Lamps were sized with the hull, as on a scale model. Pins ran from 0.16 m (fighter) to
   0.70 m (carrier) and bar widths from 0.20 m (corvette) to 0.87 m (carrier). The renderer's far-field floors
   then turned every distant bar into a 3 x 1.3 px window-shaped box at near-full energy.

**The standard:**
- One engineering standard for the fleet: every fixture type has one physical size on every hull, so a lamp's
  share of the hull shrinks as the ship grows.
- Lamps exist only where a fixture has a job (door, dock, block extremity, drive status, deck edge, mast).
- Windows exist only on real glass in crew spaces, at the fleet port size.
- Lamp counts grow with the class.
- The renderer never lets a distant lamp turn into a window.

**What stays**, because the user liked it:
- every authored amber corner and joint bar;
- the beacons, strobes and chasers;
- per-compartment window glow on crewed hulls.

---

## 1. Fleet rules

- **R1 One fixture, one size.** The sizes in section 2 hold on every hull. A lamp is never scaled with the hull.
  Ships of 200 m or more get one extra fixture, the joint strip. Its cross-section is fixed; only its length
  follows the joint.
- **R2 Rhythm.**
  - Static lamp rows use a pitch of 4 m or more. Walkway and deck-edge rows use 5-15 m.
  - No static row runs at the port pitch.
  - No lamp row runs parallel to a port row within 2.5 m of it (that reads as an extra deck).
  - Chasers (animated) use a pitch of 1.0 m or more and hold 8 lamps or fewer per run.
  - Docking rings have 4-6 pins.
- **R3 Function first.** Every lamp marks one of these:
  - a door, hatch or airlock;
  - a docking point;
  - a block extremity or outer corner;
  - drive or system status;
  - a walkable deck edge (ships of 100 m or more);
  - a mast.

  Uncrewed structure (drive pods, weapons decks, radiators, cargo bays, reactors, lattices, louvres, grilles)
  gets corner markers and at most one status fixture. It gets no rows and no scatter.
- **R4 Small craft are authored.** Ships under 100 m carry no automatic crease pins. Their lamps are authored,
  mirrored pairs, like an aircraft's formation lights.
- **R5 Windows only on real glass, only where people live** (section 3).
- **R6 Colour grammar.**
  - `warm`, `port`, `portDim` and `portCool` are lit interior colours. They appear only on glass and inside a
    hangar volume.
  - Exterior lamps are `amber`, `amberDeep`, `white`, `cool`, `ice`, red or green.
  - A process glow (an intake) uses `amberDeep`.
  - A cream bar in a window row reads as a window.
- **R7 Nav lights stand alone.**
  - No lamp within 2 m of a sidelight, stern light or obstruction light (hard limit, audited). Aim for 3 m
    wherever the face allows.
  - Sidelights sit at the beam extremity, never inside a lit port grid.
  - A stern-plate drive chaser runs outboard of the stern light on both sides, not through it.
- **R8 Bridges run dark.** Bridge, cockpit and CIC glass is one uniform compartment at 0.45-0.5x the cabin
  glow, with no flicker.
- **R9 Lit share by role.**

  | Role | Lit glass |
  |---|---|
  | Combat craft | Bridge, plus up to 2 ports per side beside the crew door, all dim |
  | Warships | 0.45 |
  | Civil crew spaces | 0.55 |
  | Troop habitats | 0.45 |
  | Carrier island | 0.4 |
  | Carrier keel runs | About 10-15 % |

- **R10 `lights[]` is the conspicuity path only.** Its entries are never thinned or dimmed. It holds only:
  - the 5 nav lights (2 sidelights, 2 strobes, 1 stern light), all 0.4 m;
  - red obstruction lights of 0.28-0.3 m (up to 3; carrier up to 6);
  - on ships of 500 m or more, white outline markers 50 m or more apart (carrier: the existing 18).

  Amber running lights, window points and deck lamps go into the lightscape, where they fade and thin with range.
- **R11 Range.**
  - A lamp drawn at the pixel floor carries no more light than its true area allows. The only exceptions are the
    nav path and the class `keep` set.
  - A distant bar is a dash of 3:1 or longer, or a dot. It is never a window-shaped box.
  - Window marks fade with their area.
- **R12 Signs of life at every budget.** Every hull keeps:
  - 2 strobes;
  - 2-4 slow amber beacons (the carrier 8-16);
  - one drive-status fixture;
  - window flicker on civil crew spaces only (warships 0.08 or less).
- **R13 `keep` budgets** (lamps that survive to fleet range; nav lights excluded):

  | Ship | Max `keep` |
  |---|---|
  | Fighter | 8 |
  | Corvette | 16 |
  | Freighter and troops | 16 |
  | Destroyer | 24 |
  | Carrier | 60 |

---

## 2. Fixture catalogue and brightness tiers

Sizes are in metres in the ship frame. For a pin, the module `size` is the lamp. effects.js draws its sprite 2x
(PIN_SPRITE), with a visible core of about 0.7x size.

| # | Fixture | Size (m) | Colour | Tier | Where / what for | Field |
|---|---|---|---|---|---|---|
| F1 | Sidelight | 0.4 | red (port, +X) / green | T0 | Beam extremity, one per side, steady (R7) | `lights[]` |
| F2 | Stern light | 0.4 | white | T0 | Stern plate, steady | `lights[]` |
| F3 | Anti-collision strobe | 0.4; period 1.3 s, duty 0.1 | white | T0 | 2 (dorsal/masthead and keel), alternating | `lights[]` |
| F4 | Obstruction light | 0.28-0.3 | red, steady | T0 | Mast and whip tips more than 5 m above the hull; up to 3 (carrier up to 6) | `lights[]` |
| F5 | Outline marker (ships of 500 m or more) | 0.4 | white | T0 | Deck-edge outline, 50 m or more apart (carrier: 18 at 75 m) | `lights[]` |
| F6 | Beacon | 0.26-0.30 pin; pulse 3-4.5 s | amber | T1 | Dorsal centreline, roof or dock. 2-4 per ship under 250 m (docking beacons extra), 8-16 on the carrier | `points` / `surface` + `pulse` |
| F7 | Marker / corner bar (the concept's amber slit) | 0.18-0.22 wide x 0.6-1.8 long, 3.5:1 or more; radiance 1.0-1.8 | amber | T1 if `keep`, else T2 | Block extremities and outer corners, mirrored, at most one pair per corner (stacks of 2-3 at a joint, 2 m or more apart) | `slit` / `slitRow` |
| F8 | Recess and corner bar (automatic) | **0.20 wide** x 0.8-1.4 long (ships of 200 m or more: up to 2.4 long); radiance 0.9-1.6 | amber only | T2 | Concave corners of real recesses on crewed blocks and armour joints. Never on a port or glazing lip, louvre, lattice or machinery deck | `slits`, `slits.corner` |
| F9 | Joint strip (ships of 200 m or more only) | **0.26-0.30 wide** x 1.8-13 long; radiance 1.4-2.0 | amber (hangar lanes amber or white) | T1 | Major armour joints, frame gaps, bay sills and lintels, the bow brow and chin. Never fills the lower edge of a rectangular recess | `slit` / `slitRow` |
| F10 | Door / hatch lamp | 0.5-0.6 x 0.14 bar at the jamb or lintel, or one 0.22-0.26 pin | amber (white allowed) | T2 | 1-2 per visible crew door or airlock on every class: the human ruler beside the 1 x 2 m door | `slit` / `points` |
| F11 | Marker pin (crease pin) | **0.20-0.28**; intensity 0.7-1.0 | amber (white up to 15 %) | T3 | Crease ends at block corners and chines of crewed blocks, 2 m or more apart. Automatic on ships of 100 m or more; authored mirrored pairs below that | `creases` / `points` |
| F12 | Walkway / deck-edge light | 0.22-0.28 | white or amber | T3 | Walkable ledges and catwalks on ships of 100 m or more; pitch 5-15 m; 2.5 m or more clear of port rows | `row` / `surface` |
| F13 | Docking marker | ring of 4-6 pins of 0.22 m, plus 1 beacon | white (chase about 4 s) + amber | T2 | Docking ports and airlock tubes | `ring` + `points` |
| F14 | Sill / guidance chaser | pins 0.22-0.26 or bars 0.26 wide; pitch 1.0 m or more; 8 lamps or fewer per run (hangar lanes excepted) | amber, white | T2 | Boat-hatch sills, cargo-bay guidance, hangar launch lanes | `row` / `slitRow` + `chase` |
| F15 | Drive / system status | cluster of 4 or fewer pins of 0.18-0.22 m, or one bar 0.15 x 0.8-2.4 | cool | T4 | One per drive housing, reactor or stern plate. No rings on bell lips below 200 m | `points` / `row` + `chase` / `slit` |
| F16 | Hangar lamp (interior only) | pin heads 0.26; lamp bars 1.5-2 m at 4 m pitch or wider | warm allowed | interior | Hangar ceilings, walls and lanes: sized like the parked ships' lamps | `patterns`, `fixtures` |
| F17 | Floodlight | kit housing 0.5; lamp point 0.3 or less; spot pool | warm-white | interior | Hangar and cargo work areas; off in transit | `interiorLights` |
| W1 | Cabin port glow | glass 0.86-1.0 (frame 1.14-1.4), pitch 1.45 m or more, decks 3.0 m | fleet `glassGlow` [0.52, 0.42, 0.28] | T5 | Crew compartments only, lit by role (R9), no port split by a compartment edge | `livery` |
| W2 | Bridge / cockpit / CIC glass | pane 1.0 x 1.2 at 1.12 pitch, or armoured slits 0.55-0.85 tall | 0.45-0.5x the cabin glow, uniform | T5 | Bridges, cockpits, CIC | `livery.glassZones` |
| W3 | Window point (carrier only) | size 0.5 (sprite 1.0 = the glass) | `port` / `portDim` | T5 | Only on real hull-texture glass the livery keeps dark, in runs of 3-6. Never `keep`, never in `lights[]` | lightscape `points` |
| X1 | Glint (field coil, muzzle rim) | 0.04-0.12 wide; radiance 0.1 or less | cool | none | Not a lamp; unrestricted | `fixtures` |

Hard limits (audited):
- lightscape pins are 0.16-0.30 m, except window points of 0.5 m;
- automatic crease pins are 0.20-0.28 m;
- automatic bars are 0.18-0.22 m wide;
- authored bars are 0.22 m wide or less below 200 m, and 0.30 m or less at 200 m and above;
- every bar is 3.5:1 or longer;
- nothing warm sits outside the carrier's hangar and bays.

### Brightness tiers (near field, and far field after section 5)

| Tier | Members | Near | Far (effects.js after S1-S3) |
|---|---|---|---|
| T0 conspicuity | `lights[]` | full | never thinned, never dimmed |
| T1 signature | `keep` bars and strips, animated bars; `keep` pins, beacons, chasers | bars radiance 1.4-2.0; beacons intensity 1.0 | always drawn; bar energy floor 0.45 of its true-area fade; pin floor 0.4 |
| T2 lamp bars | recess and corner bars, door lamps, sill bars | radiance 0.9-1.6 | thinned by rank with the ship's screen size; floor 0.2 |
| T3 lamp pins | marker, walkway and docking pins | intensity 0.7-1.0 | thinned by rank (true size and ship size); floor 0.25 |
| T4 status | cool pins and bars | intensity 0.7-0.9 | as T3 |
| T5 glass | livery glow; window points | cabin [0.52, 0.42, 0.28]; bridges x0.45-0.5 | livery: area-averaged texture; window points fade with area (quadratic), floor 0.05 |

---

## 3. Window rules

1. **One ruler.** All lit glass is one of three kinds:
   - a port of 0.86-1.0 m glass;
   - a pane of 1.0 x 1.2 m;
   - an armoured slit 0.55-0.85 m tall with mullions 1.4 m or more apart.

   No lit glass is under 0.8 m anywhere. A small ship gets fewer windows, never smaller ones. The fighter's glass
   is already at fleet size: the parallel rebake has landed in the working tree (section 6.1).
2. **Real glass only.**
   - Ships whose glass is all kit parts (fighter, corvette, freighter, troops) set `livery.glassParts` (S7). Only
     those part meshes glow. Hull stencils, sensor lenses, gun sights and containers stay dark without boxes.
   - Ships with hull-texture ports (destroyer, carrier) use `glassDark` boxes for glass that must stay dark: glass
     under weapon mounts, around sidelights, and the keel wedge.
3. **Crew spaces only, lit by role** (R9). Bridges are dim and uniform through `glassZones` (S5).
4. **No split panes.** A compartment edge (`floor(p / glassCell + glassPhase)`) must never cross a pane. The
   tested grids, with bridge boxes excluded because their uniform zones have no edges:

   | Ship | Setting | Panes cut |
   |---|---|---|
   | Corvette | `glassCell: 5.1, glassPhase: 0.54` | 0 of 86 (today 40) |
   | Freighter | `glassCell: [5.8, 3.0, 5.85], glassPhase: [0.0, 0.47, 0.49]` | 0 of 130 (today 26) |
   | Troops | `glassCell: [5.8, 6.1, 5.8], glassPhase: [0.0, 0.69, 0.86]` | 0 of 386 (today 114) |
   | Fighter | all glass in one uniform zone | not applicable |
   | Destroyer, carrier | hull glass: not measurable with the tool | none were reported split |

   Check with `cellcut.mjs` (section 8).
5. **No lamp touches glass.**
   - No automatic pin or bar within 1.5 m of a glass frame. Use zone `slits: null` or `creases.exclude` boxes.
   - No bar on a port or glazing lip.
   - No lamp row within 2.5 m of a port row, parallel to it.
   - No lit transom row over a door-shaped recess.
6. **Window points** (carrier only):
   - lightscape `points`, `port` / `portDim`, size 0.5;
   - in compartment runs of 3-6 on one deck;
   - never `keep`, never in `lights[]`.

---

## 4. Per-class budgets

"Lamps" means pins plus bars in the lightscape. It excludes `lights[]` and window points. "Tested" is the
audit-harness count with the reference override in `v14/standard/ov2/` (section 8), which encodes exactly the
section 6 lightscape actions. Each ship moves from the current count to the tested count.

| Class | Length / crew | Lamps now | **Budget** | Tested | Bars (budget / tested) | `keep` max (tested) | `lights[]` | Lamps per 1000 m2 after |
|---|---|---|---|---|---|---|---|---|
| Fighter | 71.7 m / 40 | 173 | **26-34** | 28 | 16-22 / 20 | 8 (8) | 5 | 3.2 (the darkest) |
| Corvette | 108 m / 350 | 260 | **115-145** | 133 | 55-70 / 67 | 16 (16) | 5 | 6.8 |
| Freighter | 134 m / 80 | 366 | **160-195** | 185 | 45-60 / 56 | 16 (8) | 8 | 5.9 |
| Troops | 129 m / 80 + 750 | 358 | **160-195** | 178 | 45-60 / 53 | 16 (6) | 8 | 5.1 |
| Destroyer | 203 m / 2,000 | 350 | **205-250** | 227 | 60-75 / 70 | 24 (24) | 5 (+2 red optional) | 4.0 |
| Carrier exterior | 900 m / 20,000 | 821 | **550-800** | 599 | 150-200 / 171 | 60 (54) | 23 (5 nav + 18 white outline) | 0.4 |
| Carrier hangar and open bays | | 888 | **650-900** | 876 | | | | |

Class order of lamp totals: 28 < 133 < 178-185 < 227 < 599 + 876. The steps are 4.8x, 1.35x, 1.23x and 6.5x.
The fighter moves from the densest hull per area to the darkest, as a combat craft should.

### What each view must communicate

- **Fighter.**
  - Hero: one dark armoured machine. It shows about 20 hard amber lamps at its block extremities (sponson heads,
    bow bezels, stern-block corners), an aircraft-style nav set, one dim 5-pane canopy, and 2 dim ports beside
    each crew door. Nothing in rows.
  - Close: the 2.4 m door with one amber lamp; 1 m ports; 1.0 x 1.2 m panes.
  - Range: the nav set plus the 8 `keep` bars as faint dots or dashes.
- **Corvette.**
  - Hero: two decks of cabin ports in the fore and aft crew blocks, a dim bridge band and tower, and amber bars
    at the torpedo frame, stern frame, deckhouse base and pod-bay corners. The pods are dark machinery: corner
    lamps, one status bar and the sidelight.
  - Range: bow-frame bars, pod corner lamps, the nav set, and a faint window band.
- **Freighter.**
  - Hero: one lit accommodation block (6 decks, about 55 % lit) over a dark working spine. The truss is marked
    every other node plus one guidance chaser. The reactor is dark but for its corner bars and sequencer. The
    radiators are marked at their ends.
  - Troops: additionally, railcar rows of lit berths on the habitats (about 45 %) with no lamps on the cylinders.
- **Destroyer.**
  - Hero: three decks of true 1 m ports (about 45 % lit) on the hull blocks. Amber joint strips at the bow
    cheeks, gun gap, engine bands and stern plate. A dark weapons deck and mast, and dim bridge and CIC slits.
  - Range: the joint strips and the nav set; the ports fade to grain.
- **Carrier.**
  - Hero: a city-scale warship. Lit hangar bays seen through the frames, an island of 40 decks mostly dark
    (about 40 %), amber joint strips at every frame ring and on the brow, and a hull that is otherwise dark.
    Every lamp is at fleet size.
  - Close and hangar: the carrier's lamps match the parked ships' lamps size for size.
  - Range: hangar and island glow, frame strips and the white outline. No glitter, and no mark bigger than the
    keep strips.

---

## 5. Shared code changes

One agent makes these before the per-ship agents run. Nothing else in shared code changes: PIN_SPRITE 2.0,
uMinPx 3, SLIT_GAIN and the pin thinning rule stay as they are, and so does lightscape generation. Per-ship
agents may rely on everything in this section.

### S1 `src/lib/effects.js` slitVS (about :206-209): far-field bar shape and energy

Replace the `grow` / `stretch` / `vC` lines with:

```glsl
float grow = min(max(1.0, 1.3 / max(wPx, 1e-4)), 8.0);
// a bar that cannot hold >= 3:1 on screen is drawn as a 1.3 px dot (never a window-shaped 3 x 1.3 px box); the
// stretch is capped at 2.5x, so a far bar is a short dash or a dot, not a lit slot
float stretch = lPx >= 1.5 ? min(max(1.0, 3.9 / lPx), 2.5) : max(1.0, 1.3 / max(lPx, 1e-4));
// energy follows the bar's true area (drawn / true = grow * stretch): signature bars (rank 0: keep, animated) keep
// at least 0.45 of their radiance, the rest 0.2
float fade = clamp(inversesqrt(grow * stretch), iRank < 0.01 ? 0.45 : 0.2, 1.0);
vec3 p = position; p.y *= grow; p.x *= stretch;
vL = position.xy * 2.0;
vC = iColor * on * uGain * fade;
```

Also update the comment block above `slitGeometry` (the one ending "pins, by contrast, are thinned ...") to
describe this behaviour.

**Why:** today a far bar is stretched up to 6x and dimmed only for its widening (floor 0.4). At fleet range every
bar becomes a 3 x 1.3 px near-square at several times its true light. That is a distant window: the fighter's
cream bars, and carrier lamps at 1 % of the hull at dist 5.

### S2 `src/lib/effects.js` slitKeep (about :190-193): range thinning of bars

In `slitKeep()`, replace `clamp(shipPx / 250.0, 0.25, 1.0)` with `clamp(shipPx / 900.0, 0.15, 1.0)`. Keep the rest
of the expression. Update its comment ("all of them from ~900 px up; below that corner and keep bars last").

**Why:** today every bar is drawn from 250 px up, so a 280 px ship at dist 5 shows all of its bars. Bars now thin
like the pins already do (the pins' `shipPx / 900` term): a distant hull keeps its `keep` and corner bars.

### S3 `src/lib/effects.js`: pin energy floor by type

In `attachEffects` (about :318), change the pin mapping to:

```js
...(info.pins || []).map((l) => ({ ...l, floor: l.floor ?? (/^port/.test(l.color) ? -0.05 : l.keep || l.blink?.period > 0 ? 0.4 : 0.25) }))
```

In `lightVS`, change the energy line to:

```glsl
float e = min(1.0, truePx / 2.0);
// floorE < 0: a window (an area source) fades with its area, (truePx / 2)^2, down to -floorE
float energy = floorE >= 1.0 ? 1.0 : floorE < 0.0 ? max(-floorE, e * e) : max(floorE, e);
```

The `keep` / `rank` thinning line is unchanged (`floorE >= 1.0` tests still work with negative floors).

**Why:** a sub-pixel lamp drawn at the 3 px floor at 0.4 energy carries many times its true light. Plain lamps drop
to 0.25. `keep` and animated pins (beacons, chasers) keep 0.4, so the signs of life stay. Window points fade with
their area, so a distant 1 m port never draws as a 5-10 m blob.

### S4 `src/lib/glbship.js` (after the `lights` mapping, about :448): nav-path audit warning

```js
{ const cap = (cfg.length ?? 0) >= 500 ? 30 : 12;
  const bad = lights.filter((l) => !['red', 'green', 'white'].includes(l.color) || l.size < 0.25 || l.size > 0.45);
  if (bad.length || lights.length > cap) console.warn(`[glbship] ${cfg.name}: lights[] is the never-dimmed nav path (STANDARD R10): ${lights.length} entries (cap ${cap}), ${bad.length} not a red / green / white 0.25-0.45 m nav light`); }
```

**Why:** `lights[]` entries get energy floor 1 and rank 0. The carrier's 990 window points and 76 amber lamps, the
destroyer's 16 and the freighter's 8 amber running lights sit there and dominate at range. The data is fixed per
ship; this warning keeps it from coming back.

### S5 `src/lib/livery.js`: glassDark cap 8, and glassZones

1. **glassDark cap 4 to 8.** Covers `:88` slice, `:94-95` arrays, the shader declarations and the loop.
2. **New option `glassZones: [{ box, mirrorX?, gain = 1, uniform = false, lit? }]`.**
   - It shares one list of up to 8 boxes with glassDark. Build `[...glassDark.map((box) => ({ box, gain: 0 })),
     ...expand(glassZones)].slice(0, 8)`, where `mirrorX` adds the reflected box.
   - The first box containing the texel wins.
   - Inside it:
     - the glow is multiplied by `gain` (0 = today's glassDark: no glow at all);
     - `uniform: true` sets `level = 1`, `fl = 1`, `lit = 1` and the neutral-warm tint `vec3(1.0, 0.95, 0.86)`
       for every pane in the box (one steady compartment);
     - `lit` (0..1), if given, replaces `glassLit` in the box.
3. **Shader.**
   - Uniforms `uLivZoneN`, `uLivZoneMin[8]`, `uLivZoneMax[8]`, `uLivZoneP[8]` (vec4: gain, lit or -1, uniform
     0/1, 0). They replace the glassDark uniforms.
   - Final line: `totalEmissiveRadiance += uLivGlassGlow * tint * pane * zGain * (0.06 + 0.94 * lit * level * fl);`
4. **Cache key.** The program key carries the box count (`-zones${n}` instead of `-dark${n}`).

**Why:**
- R8 (dim bridges) and R9 (lit share by region) cannot be expressed with one `glassGlow` / `glassLit` per ship.
  Today the fighter, corvette, destroyer and carrier bridges are among their brightest glass.
- The carrier needs a fifth dark box (keel) plus a bridge zone. The destroyer needs 4 dark boxes plus a zone.

### S6 `src/lib/livery.js`: compartment grid per axis

- `glassCell` accepts a number or `[x, y, z]`.
- New `glassPhase` accepts a number or `[x, y, z]`; the default is 0.37, so ships that do not set it are unchanged.
- Both become `vec3` uniforms (a scalar is splatted).
- Shader: `livNoise(vLivPos / uLivCell)` (vec3 division) and `vec3 cell = floor(vLivPos / uLivCell + uLivPhase);`.

**Why:** the hard cell edge at `:185` cuts ports into two-tone halves: corvette 40 of 86, freighter 26 of 130, troop
ship 114 of 386. A split 1 m port reads as a half-size window, so the hull reads bigger. Grids aligned to decks
and port columns cut none (section 3.4).

### S7 `src/lib/glbship.js` material loop (about :322): `livery.glassParts`

```js
// livery.glassParts: kit part names whose glass may glow (real windows); hull texels and every other part keep the
// dark glass look but no interior light (stencils, sensor lenses, gun sights, containers)
const liv = cfg.livery?.glassGlow && cfg.livery.glassParts && !(role.part && cfg.livery.glassParts.includes(role.part))
  ? { ...cfg.livery, glassGlow: null } : cfg.livery;
if (cfg.livery) applyLivery(mm, liv, zoned ? { scheme, zones: cfg.liveryZones, toShip: o.matrixWorld } : { toShip: o.matrixWorld });
```

Part names in the GLBs:
- fighter and corvette: `port`, `pane`;
- freighter and troops: `portlite`, `pane`;
- destroyer and carrier: no kit glass (hull-texture ports), so they do not set the option.

**Why:** the glass test also catches dark stencil paint, lens and sight texels. Examples: the freighter's 0.1-0.55 m
reactor specks, the corvette's turret sights, the fighter's bow lenses. These are sub-port "windows" on uncrewed
parts: the fighter's failure again. This replaces both drafts' `glassHull` / `glassNodes` with one whitelist.

### S8 `src/lib/lightscape.js`: comments only

In the header:
- pins are "0.2-0.3 m (fleet standard: v14 STANDARD)";
- slit ranks read "authored `keep` / animated 0, other authored hashed".

No code change.

### Not in shared code (rejected or moved to data plus audit)

These are handled by each module's data and caught by the audit instead:
- per-zone `max`;
- symmetric crease pins;
- a runtime colour guard;
- a runtime nav-isolation guard;
- an exported FIXTURES table;
- automatic glass clearance.

Where a zone's freed budget refills elsewhere, the per-ship action lowers the global `max` (tested).

---

## 6. Per-ship actions

Line numbers are for the current branch. Values not named stay as they are. After editing, run the audit and cell
checks (section 8), then render.

Every ship: its nav lights are `size: 0.4` (obstruction 0.28-0.3), and `glassGlow` stays the fleet cabin value
[0.52, 0.42, 0.28]. Bridges dim through zones.

### 6.1 Fighter: `src/ships/fighter.js` (tested: 28 lamps = 8 pins + 20 bars, 8 keep, PASS)

The glass rebake has landed, uncommitted in the working tree:
- files: `tools/blender/hulls/fighter_spec.py`, `tools/blender/specs/fighter-v3.json`, `assets/ships/fighter.glb`
  (11:38) and `tools/blender/hulls/README-fighter.md`;
- 2 kit ports of 1.0 m glass per side beside the crew door: ship frame x ±11.5..12.4, y -3.35..-1.95,
  z 10.7..14.1;
- one row of 5 kit panes at x1.0 in the bridge recess: x ±2.8, y 3.44..4.58, z 15.4..16.3;
- no side panes.

This meets section 3. Do not re-edit the spec.

1. `:19` meta.blurb: "glazed in a band of small panes" becomes "with a five-pane canopy". `:129` surface
   comment: "kit panes x1.0 (five)".
2. `:31-32` livery:
   `{ gain: 0.05, glassGlow: [0.52, 0.42, 0.28], glassFlicker: 0, glassParts: ['port', 'pane'], glassZones: [{ box: [[-13, -4, 10], [13, 5, 17]], gain: 0.45, uniform: true }] }`.
   - Every fighter window is one steady, dim compartment (R8, R9).
   - The bow-lens glassDark can go: lenses are not glass parts.
3. `:39` `creases: null` (R4).
4. `:40` slits: `width: 0.2, max: 4, mix: { amber: 1 }, corner: { share: 0.3, width: 0.2, len: [0.8, 1.3], radiance: [1.2, 1.6], max: 4 }`.
   This gives 8 automatic bars at the stern block and pylon.
5. `:53` bridge-recess zone: `slits: null` (no bar inside the glazing).
6. Delete:
   - `:62` shoulder pin row;
   - `:63` shoulder-end pulse beacons;
   - `:65` lower-chine row;
   - `:68` warm pylon-riser slitRow (the "window row" at every range);
   - `:75` sponson status row (1.2 m over the red sidelight);
   - `:80` bell-lip rings.
7. `:60` bridge sill lamps: `keep: false`.
8. `:66` door lintel becomes an F10 door lamp: `color: 'amber', len: 0.6, width: 0.14, radiance: 1.4, keep: false`.
9. `:79` stern-plate chaser: it runs through the stern light at [0, 3.95, -26.26]. Replace it with 2 status lamps
   outboard of the light:
   `{ points: [[2.1, 3.95, -26.13]], color: 'cool', size: 0.2, intensity: 0.8, pulse: 2.4, mirrorX: true }`.
10. Add mirrored extremity markers (from the verified crease dump: chin and forward belly chine):
    `{ points: [[4.67, 0.28, 32.41], [10.61, -8.35, 10.20]], color: 'amber', size: 0.24, intensity: 0.9, mirrorX: true }`.
11. Unchanged:
    - `:71-73` sponson heads and `:77` bow bezels: the 8 `keep` bars;
    - `:82` dorsal beacons: the 2 beacons;
    - nav `:107-113`.

### 6.2 Corvette: `src/ships/corvette.js` (tested: 133 = 66 pins + 67 bars, keep 6 + 10, PASS)

1. `:28` livery:
   `{ gain: 0.05, glassGlow: [0.52, 0.42, 0.28], glassLit: 0.45, glassFlicker: 0.08, glassCell: 5.1, glassPhase: 0.54, glassParts: ['port', 'pane'], glassZones: [{ box: [[-10.5, 0.2, 10.5], [10.5, 2.7, 25.5]], gain: 0.5, uniform: true }, { box: [[-8, 10.5, -18], [8, 12.5, -3]], gain: 0.5, uniform: true }] }`.
   - The zones are the bridge band and the tower.
   - The turret sights go dark through `glassParts`.
   - 0 ports cut.
2. `:35` creases: `size: [0.2, 0.25], mix: { amber: 0.85, white: 0.15 }, max: 40`.
3. `:36` slits: `mix: { amber: 1 }, max: 30`.
4. Zones:
   - Insert after `:41` (radiator bay): `{ box: [[24.2, -20.8, -29.2], [35.0, -9.1, -0.3]], mirrorX: true, creases: { share: 0, corners: 0.12 } }` (the drive pods).
   - Insert before `:57` (key-lit top; the first match wins): `{ box: [[-8, 10, -18], [8, 30, -3]], creases: { share: 0, corners: 0.15 } }` (tower and mast).
5. Delete:
   - `:61` tower sill pins;
   - `:64` shoulder row;
   - `:76` flank bar on the port frame;
   - `:83`-`:84` pod radiator sill and head rows;
   - `:89`-`:90` pod status rows.
6. `:63` belt row: `edge: 'bottom', pitch: 10` (away from the port grid).
7. `:77` bar: `slit: [16.16, -5.0, 18.8]` (clear of the port frame).
8. `:86` pod fore corner lamps: `size: 0.3` (keep). `:87` pod aft corner lamps: `size: 0.3, keep: false`.
9. Add one pod status bar:
   `{ slit: [34.47, -12.85, -5.0], u: [0, 0, 1], n: [1, 0, 0], len: 0.8, width: 0.15, radiance: 1.1, color: 'cool', mirrorX: true }`.
10. `:100` warm vent-slat row: replace it with two amber end bars per bay:
    `{ slit: [14.627, -3.147, 7.375], ... }` and `{ slit: [14.627, -3.147, 16.575], ... }`, each with
    `u: [0, 0, 1], n: [0.752, 0.659, 0], len: 0.55, width: 0.14, radiance: 0.9, color: 'amber', mirrorX: true`.
11. `:103` stern chaser: it runs through the stern light at [0, -3.075, -49.47]. Replace it with runs outboard of
    the light:
    `{ row: [[2.0, -2.88, -49.34], [3.6, -2.88, -49.34]], pitch: 1.6, color: 'cool', size: 0.2, intensity: 0.85, chase: 2.6, mirrorX: true }`.
12. `keep: false` on `:66` (deckhouse base row) and on the door-jamb lamps `:69` and `:72`. The keep set is then:
    - pod fore corners (4);
    - torpedo lip lamps (2);
    - torpedo-frame bars (4);
    - pod-bay corner bars (4);
    - bow-flank foot bars (2).
13. `:136-140` nav: all `size: 0.4`.
14. Unchanged: door jambs, torpedo frame, stern frame (`:97-98`), `:101` aft vent bars, bow beacons (`:104-105`).
15. Optional: 2 tower-band end lamps
    `{ slit: [4.9, 11.04, -5.59], u: [1, 0, 0], n: [0, -0.605, 0.796], len: 0.6, width: 0.14, radiance: 0.9, color: 'amber', mirrorX: true }`.

### 6.3 Freighter and troop ship: `src/ships/freighter.js` (tested: cargo 185 = 129 + 56, troops 178 = 125 + 53, PASS)

Shared constants:

1. `:33` CIVIL_CREASES: `size: [0.2, 0.28], intensity: [0.7, 1.0], mix: { amber: 0.85, white: 0.15 }, max: 45`.
2. `:34` CIVIL_SLITS: `width: 0.2, len: [0.8, 1.3], mix: { amber: 1 }, max: 24, corner: { width: 0.2, len: [0.8, 1.2], radiance: [1.1, 1.5] }`.
3. `:36` CIVIL_LIVERY: add `glassParts: ['portlite', 'pane']`. This kills the reactor stencil specks and the
   specks beside the crew ports. The containers are not glass parts, so the cargo container glassDark `:47` may
   stay or go.

Cargo livery (`:47`):

4. Set `{ ...CIVIL_LIVERY, glassCell: [5.8, 3.0, 5.85], glassPhase: [0.0, 0.47, 0.49], glassZones: [{ box: [[-9.5, -2.5, 56.5], [9.5, 2.5, 67.0]], gain: 0.5, uniform: true }] }`.
   - The zone is the bridge panes.
   - 0 of 130 portlites cut.

Troops livery (`:157`):

5. Set `{ ...CIVIL_LIVERY, glassLit: 0.45, glassCell: [5.8, 6.1, 5.8], glassPhase: [0.0, 0.69, 0.86], glassZones: [{ box: [[-9.5, -2.5, 54.0], [9.5, 2.5, 64.5]], gain: 0.5, uniform: true }] }`.
   - 0 of 386 cut.
   - 0.45 keeps the troop ship's lit share at the destroyer's, not above it.

Zones:

6. Bay zones `:61` / `:169`: `creases: null` (84 / 64 pins on rack posts today).
7. Insert after each bay zone a reactor and engine zone, `creases: { share: 0.05, corners: 0.2 }`:
   - cargo box `[[-15, -15, -64], [15, 20, -22.3]]`;
   - troops box `[[-17, -15, -60], [17, 20, -20.3]]`.

Patterns (the same edit on each variant's own line):

8. Ledge row `:67` / `:173`: `pitch: 5`. Chine row `:68` / `:174`: `pitch: 6`.
9. All authored bars `:71`, `:72`, `:81`, `:82`, `:83`, `:86` (troops `:176`, `:177`, `:183`, `:184`, `:185`):
   `width: 0.2`, lengths unchanged.
10. The warm bars `:72` / `:177` (collar lower) and `:83` / `:185` (reactor lintel) become `color: 'amber'`.
11. Top-chord node pins `:77` / `:180`: `pitch: 10.9` / `9.64`, `size: 0.24`.
12. Bottom-chord bars `:78` / `:181`: `pitch: 10.9` / `9.64`, `skip: 0`, `keep: false`. Keep the chaser
    `:79` / `:182`.
13. Reactor sequencer `:87` / `:187`: `keep: false` (animated pins keep their 0.4 floor).
14. Engine-face rings `:89` / `:188`: `n: 4`.
15. Radiator top rows `:91` / `:189`: replace each with 2 lamps per radiator, the aft corner and one mid-edge,
    `color: 'amber', size: 0.26, intensity: 0.7`, no keep:
    - cargo `{ points: [[26.9, 3.2, -58.0], [26.9, 3.2, -47.0]], mirrorX: true }`;
    - troops `{ points: [[28.3, 3.3, -54.0], [28.3, 3.3, -44.0]], mirrorX: true }`.

    Both are 3 m or more from the sidelight.

lights[]:

16. Delete the 4 crew-module amber running lights (`:119-120` / `:215-216`, on the ledge between port rows).
17. Move the 4 reactor-flank ones (`:121-122` / `:217-218`) into the lightscape:
    `{ points: [[13.55, 4.6, -32.05], [13.45, 4.6, -24.45]], color: 'amber', size: 0.26, intensity: 0.9, mirrorX: true }`
    (troops `[[15.59, 4.6, -29.3], [15.59, 4.6, -21.7]]`).
18. `lights[]` is then 5 nav + 3 red obstruction.

The keep set is then the collar, reactor-face and reactor-flank bars (8 cargo, 6 troops).

### 6.4 Destroyer: `src/ships/destroyer.js` (tested: 227 = 157 + 70, keep 24, PASS)

1. `:54` livery: `glassLit: 0.45, glassFlicker: 0.08`.
   - glassDark:
     - `[[13, -4.5, 75], [16.5, -1, 83]]` and `[[-16.5, -4.5, 75], [-13, -1, 83]]`: ports under the bow
       point-defence mounts;
     - `[[26.5, -16.6, -54.0], [29.0, -9.1, -46.0]]` and `[[-29.0, -16.6, -54.0], [-26.5, -9.1, -46.0]]`: a dark
       8 x 7.5 m panel round each sidelight, which today sits in the port grid's one-port skip.
   - glassZones: `[{ box: [[-7, 8.2, -42], [7, 12.2, -32]], gain: 0.5, uniform: true }]` for the bridge and CIC
     slits. Verify on the close render that no deckhouse port falls inside.
2. Append the survey's tested zones (from `v14/survey/destroyer/ov-proposal3.mjs`):
   - spine `{ box: [[-12, -1.5, -13], [12, 4.5, 44]], creases: { share: 0.04, corners: 0.08 }, slits: { share: 0.08, corner: { share: 0.1 } } }`;
   - deckhouse roof `{ box: [[-10, 8.5, -31], [10, 12, -12.5]], creases: { share: 0.04, corners: 0.08 }, slits: null }`;
   - engine deck `{ box: [[-16, 2, -84], [16, 10, -60]], creases: { share: 0.05, corners: 0.1 }, slits: { share: 0.1, corner: { share: 0.1 } } }`;
   - bow roof `{ box: [[-11, 1.6, 55], [11, 6, 101]], creases: { share: 0.05, corners: 0.1 }, slits: null }`;
   - mast `{ box: [[-4.5, 14, -57], [4.5, 33, -45]], creases: null, slits: null }`;
   - taper port lip `{ box: [[13, -17.5, 22], [16.8, -14.5, 41.8]], mirrorX: true, slits: null }`.
3. `:62` creases: `max: 120, size: [0.2, 0.28], mix: { amber: 0.85, white: 0.15 }`.
4. `:63` slits: `max: 30, width: 0.2, mix: { amber: 1 }, corner: { width: 0.2, radiance: [1.1, 1.6] }`. Lengths
   stay `[1.1, 2.0]`: F8 allows up to 2.4 on ships of 200 m or more.
5. Authored bars `:81`, `:84`, `:85`, `:86`, `:89`, `:90`, `:91`, `:92`, `:93` become F9 joint strips: `width: 0.26`,
   lengths unchanged. Also:
   - `:92` intake glow: `color: 'amberDeep', keep: false`;
   - `:85` and `:90`: `keep: false` (keep is then 24).
6. Delete:
   - `:95` command brow band (a third window row);
   - `:98` mid-flank amber row (it runs between the two port rows at y -11.74).
7. `:100` boat-hatch sill chaser: `pitch: 1.0`. `:101` hatch status row: `pitch: 5.6` (2 lamps).
8. `:103` command-aft row: `pitch: 4.6, skip: 0, size: 0.22` (one lamp over each door).
9. `:109-110` engine-deck cool rows: `pitch: 3.0`.
10. `:112` gap-face row: `color: 'amber', pitch: 2.5`.
11. `:108` stern chaser: it runs through the stern light at [0, -0.44, -85.21]. Replace it with
    `{ row: [[2.0, -0.64, -85.08], [3.6, -0.64, -85.08]], pitch: 1.6, color: 'cool', size: 0.2, intensity: 0.85, chase: 2.6, mirrorX: true }`.
12. `:159-167`: delete the 16 amber running lights. They are nav-path lamps that sit 0.4-1.4 m from port rows and
    never dim.
13. Optional: 2 red obstruction lights on the mast gallery in `lights[]`,
    `{ p: [2.2, 23.6, -51.5], color: 'red', size: 0.28, mirrorX: true }`.
14. Sidelights `:152-153` stay at 0.4 m where they are; the glassDark panel (item 1) isolates them. Moving the
    kit housing is optional and needs a rebake.

### 6.5 Carrier: `src/ships/carrier.js` (tested: exterior 599 = 428 + 171, hangar 876, keep 54, lights[] 23, PASS)

Nav path and window points:

1. `:57-62` OUTER: drop `ISLAND_PORTS` (566 points on already-lit glass) and the keel `HULL_PORTS` (210 points,
   100 % lit at 10 m pitch).
2. `:244` `lights[]` keeps the 5 nav lights and `DECK_EDGE` (18 white outline markers at 75 m). Everything else
   moves into the lightscape:
   - `GALLERY`, `BOW_WALL`: `{ points, color: 'portDim', size: 0.5, skip: 0.5 }`, no keep. A distinct `seed` per
     list keeps the faces from matching.
   - `EDGE_RUN`, `FLANK`, `SPONSON_RUN`, `MOUTH_RIM`: `{ points, color: 'amber', size: 0.3, intensity: 0.9 }`, no
     keep. The pitch stays 25 m.
3. `:188` WINDOW_RUNS: `size: 0.5, keep: false`. Intensity stays 1.25.

Fixtures to fleet size:

4. `:186` frame-post window box (40 warm lamp-bright panes with no glass, which read as a door with a lit
   transom): delete. Optional: one vertical amber joint strip of 6 x 0.26 on the recess's outer edge.
5. `:137` creases: `size: [0.22, 0.28], intensity: [0.8, 1.1], mix: { amber: 0.85, white: 0.15 }, max: 560`. The
   hangar zone `:159-161` keeps its warm mix.
6. `:138-139` slits: `len: [1.2, 2.4], width: 0.2, mix: { amber: 1 }, max: 120`. corner:
   `len: [1.4, 2.4], width: 0.2, max: 60`.
7. Authored bars (lengths unchanged):

   | Lines | Bars | New width | Other change |
   |---|---|---|---|
   | `:168` / `:169` / `:172` | brow, chin, waist | 0.30 | |
   | `:173-174` | corner bars | 0.30 | warm becomes `amber` |
   | `:180`, `:182-183` | frame gaps, end blocks | 0.30 | |
   | `:177` | louvre lips | 0.26 | |
   | `:191` | bay lintels | 0.26 | stays warm: inside the bays |
   | `:194` | sills | 0.26 | |
   | `:201` | lane bars | 0.26 | |
   | `:202` | bow-lane chasers | 0.26 | |

8. `:197` ice intake (a 14 x 1.4 m visor): replace it with 4 lamps,
   `{ slitRow: [[160.0, -50.0, -280.12], [170.5, -50.0, -280.12]], pitch: 3.5, len: 2.5, width: 0.3, u: [1, 0, 0], n: [0, 0, 1], color: 'ice', radiance: 1.0, mirrorX: true, keep: true }`.
9. Hangar pin rows `:192-193`, `:203-214` (0.34-0.45 m): `size: 0.26`. Drop `keep` from `:211`. The keep set is
   then:
   - brow 6, chin 8, waist 4, corners 4;
   - frame gaps 20, end blocks 4;
   - ice 8.

   That is 54 in total.
10. `:73-76` STRIPS: each 18 m ceiling bar becomes 5 lamps of 2 x 0.3 m at 4 m pitch, and each 6 m post tube
    becomes 2 lamps of 1.5 m. Keep the radiance. If the bays read dimmer at hero, raise it to 1.8 at most.

Zones:

11. Changes:
    - `:146` (vent grilles) and `:148` (louvre chamfer): `creases: null`.
    - `:156` island: `creases: { share: 0.06, corners: 0.12 }, slits: { share: 0.05 }`. That is 77 island pins,
      down from 186.
    - Add at the front of the list: `{ box: [[140, -70, -345], [210, -30, -275]], mirrorX: true, slits: null }`
      (the sponson recess end bars).

Livery (`:123-124`):

12. `glassLit: 0.4`.
    - Add a fifth glassDark box, the keel wedge `[[-125, -150, -320], [125, -112, 220]]`.
    - glassZones: `[{ box: [[-60, 102, -250], [60, 109, 25]], gain: 0.5, uniform: true }]` (the hammerhead
      bridge).
13. Relight the keel with runs like WINDOW_RUNS: 6-8 runs of 3-5 neighbouring ports per side on one deck, about
    10-15 % of the glass, as `{ points, color: 'portDim', size: 0.5 }`, no keep. The glass lies on:
    - row A: x ±90.21, y -125.21, z = -309 + 2.5k;
    - row B: x ±82.21, y -133.21, z = -303.95 + 2.5k.

    Spot-check a few with `rc.mjs`.

Hero risk and levers:

14. With fleet-size pins, only corner-rank pins survive at the hero's 1.45 px/m, and joint strips lose about 40 % of
    their far-field energy (S1). If the hero looks dead, use these levers in this order:
    1. raise joint-strip radiance to 2.0 at most;
    2. add authored joint strips at frame rings and block ends;
    3. raise `creases.max` within the budget.

    Never re-enlarge pins or bars.

---

## 7. Where the drafts disagreed, and the decision

| Question | Practice | Perception | Decision and why |
|---|---|---|---|
| Pin thinning | distance only: drop the `shipPx / 900` term | keep today's rule | **Keep today's rule.** At equal framing (the test shots), distance-only thinning lets small ships keep every lamp and big ones shed most. With practice's own budgets it inverts the order at dist 5 (corvette 124 marks vs destroyer 115, freighter 81 vs destroyer 75, computed). S1 and S3 give the physical "fainter with range" cue instead. |
| Bar thinning | `pxm / 2`, floor 0.2 | `shipPx / 900`, floor 0.15 | **`shipPx / 900`, floor 0.15.** It matches the pins' rule and keeps the class order at equal framing. |
| Far-bar floors | 0.35 / 0.2, stretch cap 2.5 | 0.45 / 0.25, cap 2.6 | **0.45 signature / 0.2 other, cap 2.5, dot under 1.5 px.** The concept's bars must stay the brightest mark at range; plain bars may fade. |
| Pin floors | 0.2; pulse 0.4; windows quadratic, floor 0.05 | crease runs 0.25; windows 0.15; others 0.4 | **0.25 plain; 0.4 `keep` and animated; windows quadratic, floor 0.05.** Beacons and chasers are the sign of life. Windows are area sources, and the ruler must not grow with range. |
| Nav-path guard | dev warning | reroute non-nav entries as pins | **Warning plus data fix.** Smaller shared code; the audit catches regressions. |
| Corvette budget | 140-165 | 80-110 | **115-145 (tested 133).** Perception's own action list yields about 150, so 80-110 would cut concept bars and crewed-hull corners that the survey says read right. Crease max 40 (not 55) keeps a 1.35x step to the freighter. |
| Freighter budget | 170-200 | 130-170 | **160-195 (tested 185 / 178).** Crease max 45. The bay goes dark and the truss rhythm halves, which leaves a 1.23x step below the destroyer. |
| Destroyer budget | 220-260 | 190-250 | **205-250 (tested 227).** Crease max 120, plus the survey's tested zones. |
| Carrier budget | exterior 450-700 | exterior 900-1,300 | **Exterior 550-800 (tested 599), hangar 650-900.** At hero, fleet-size pins survive only at corner ranks, so a bigger cap adds nothing at hero and glitter up close. The hero relies on strips, hangar and island. |
| Warship lit share | 30-40 % | 40-50 % | **0.45.** Lit window count is the population cue that keeps the 2,000-crew destroyer above the troop ship. 0.45 against the civil 0.55 still marks the role, and it keeps the life the user liked. |
| Troop habitats | 55 % | 45 % | **0.45.** It holds the troop ship's lit share at or below the destroyer's. |
| Hull-glass guard | `glassNodes` (optional) | `glassHull: false` | **`glassParts` whitelist (S7).** One rule that also darkens turret sights and bow lenses, with no boxes. |
| Split panes | `glassPhase` + a check | smooth levels (or `glassPhase`) | **Per-axis `glassCell` / `glassPhase` (S6), tested grids with 0 cuts on 3 ships.** Smooth tint needs thresholds that recreate edges, and today's lit mask is already smooth. |
| Automatic bar size on big ships | 0.20 x 0.8-1.4 everywhere | 0.24 x 1.2-2.4 on destroyer and carrier | **0.20 wide everywhere; up to 2.4 long at 200 m and above.** The cross-section is the fixture; the length follows the joint. |
| Joint strip width | 0.26 | 0.26-0.40 (brow 0.35) | **0.26-0.30:** destroyer 0.26, carrier signature 0.30. That is a 3x cut from the carrier's 0.87 while it keeps its hero read. |
| Hangar pin size | 0.26 | 0.30 | **0.26:** the parked ships' lamps are 0.2-0.3. |
| Radiator lamps | rows at 6.5 m | 2 points per radiator | **2 points.** Uncrewed structure gets corners only (R3). |
| Truss bottom chord | skip 0.5 | pitch x2 | **Pitch x2:** deterministic and even. |
| Engine-face rings | n 4 | n 6 | **4:** corner markers, not a necklace. |
| Docking rings | unchanged (6) | n 4 | **Unchanged 6** (F13 allows 4-6). |
| Carrier ice intake | 0.4 wide, or segments | 0.5 wide, or segments | **4 lamps of 2.5 x 0.3:** reads as lamps, not a visor. |
| Fighter glass | 4 panes, ports optional | 4 panes, 0-1 port | **As rebaked: 5 panes at x1.0 and 2 ports per side at x1.0 beside the door.** It meets R5; uniform and dim. |
| Fighter drive status | chaser at 1.4-1.5 m pitch | the same, plus a sponson cool pin | **2 cool pins outboard of the stern light.** The chaser crossed the stern light (neither draft noticed; the corvette and destroyer have the same fault). The sponson pin sat 1.15 m from the red sidelight. |
| Nav clearance | 3 m hard | 3 m from glass and lamps | **2 m hard (audited), 3 m target.** The 5 m fighter stern plate cannot hold 3 m. |
| Destroyer sidelights | move the housing (rebake) or widen the skip (rebake) | move (rebake) | **Runtime glassDark panel round each light.** No rebake needed. |
| Per-zone `max`, symmetric creases, colour and nav guards in code, FIXTURES table | yes | partly | **Not in code.** Data plus the audit do the job. The one refill case (carrier island, then hangar) is handled by a lower global max. |
| `keep` budgets | 8 / 12 / 12 / 16 / 32 | 8 / 24 / 30 / 40 / 170 | **8 / 16 / 16 / 24 / 60** (lights[] excluded). Enough signature marks to read each class at range, and few enough that the fighter shows the fewest. |

---

## 8. Verification

### Tools

The tools are in `Scene3D/tools/lights/` (audit.mjs, dump.mjs, raycast.mjs, marks.py). Run them from `Scene3D/`.

- **`node audit.mjs <ship> [troops]`**
  - Prints the lamp, pin, bar and keep counts, the `lights[]` composition, colours, sizes and nav clearance.
  - Ends with PASS or FAIL against this standard's budgets and fixture limits. The carrier is split into
    exterior and hangar with its bays.
  - With `OV=<override.mjs>` it tests a change without editing the repo.
- **`node cellcut.mjs <ship> [troops] <cell> <phase> <parts>`**
  - Counts glass panes cut by a compartment edge. `cell` and `phase` accept `a,b,c` per axis.
  - Options:
    - `EX='[box, ...]'` excludes uniform bridge boxes;
    - `SHRINK=0` for portlites (0.2 for kit ports and panes: frame to glass);
    - `SEARCH=1` searches zero-cut grids per axis.
- **`node partbox.mjs <ship> [troops] <part>`**: ship-frame boxes of a kit part (glass, doors, nav housings).
- **Reference overrides**: (harness overrides, not kept: write an `OV=<module.mjs>` override exporting `default(asset, variant)` to test a change without editing the repo)
  encode the section 6 lightscape and `lights[]` actions. All pass the audit. Per-ship agents edit the module
  files, and may use these to cross-check a count.

### Before rendering

- Every ship's audit passes.
- `cellcut` reports 0 cuts:
  - corvette `5.1 0.54 port,pane` with the two bridge boxes excluded;
  - freighter `5.8,3,5.85 0,0.47,0.49 portlite`;
  - troops `5.8,6.1,5.8 0,0.69,0.86 portlite`.

### Renders

One `shoot.mjs` at a time.

1. Each ship: hero, close and `dist=5`. Troops: hero.
2. Eye checks:
   - **Fighter:** no lit rows; a dim 5-pane canopy; 2 dim ports per side beside the lit door; about 20 amber
     lamps at extremities. At `dist=5`, amber dashes or dots and nav colours only.
   - **Corvette:** whole (not two-tone) ports; dark pods; a dim bridge band and tower; no dotted rows over the
     vent bays.
   - **Freighter:** no reactor specks; a dark bay with a node rhythm.
   - **Destroyer:** a dark weapons deck and mast at `dist=5`; the sidelights on dark panels; no brow band.
   - **Carrier:** posts with no transoms; no keel rope lights; the island not a solid block at `dist=5`; amber
     strips still visible at hero (else see 6.5 item 14).
3. `mode=lineup&lineup=small`, `mode=lineup` and `mode=fleet&shot=hero`:
   - the fighter shows the fewest marks and no cream rectangles at fleet range;
   - no hull's lamps look larger than another's.
4. `marks.py` (`v14/standard/marks.py`) on the hero, `dist=2.5` and `dist=5` shots:
   - At every range: fighter < corvette < freighter ≈ troops (within 25 %) < destroyer < carrier. The steps are at
     least 1.8x, 1.2x, 1.1x and 1.5x.
   - Fighter: 35 or fewer at hero, 18 or fewer at `dist=5`.
   - If a step fails, move the offending ship's `creases.max` within its budget. Do not change fixture sizes.
