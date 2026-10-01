# Readability: true size, life, and behaviour at range

These principles are general. The **numbers** (ruler sizes, fixture sizes, budgets, colours) belong to
the style. They live in `STYLE.md`, plus a detailed standard file if the style has one, e.g.
`styles/cqs-fleet/lighting-standard.md`, which is a worked example. If the style does not define a
number you need, propose one, show it on a render, and record the user's decision.

## How viewers judge size

- **Rulers:** objects of known size (doors, windows, railings, steps, crates, people, vehicles) set the
  scale. A smaller ruler implies a bigger object. Use the style's rulers at their true size on every
  asset. Never shrink them to fit a small asset; give it fewer.
- **Detail frequency:** many fine, evenly spaced details read as a large structure. A row of small
  lights reads as windows or floors. A column of evenly spaced dots reads as storeys: one light per
  floor. A small asset needs few, bold, purposeful details.
- **Fixture consistency:** a fixture type (lamp, window, panel line, bolt) must have one physical size
  across the family. If fixtures grow with the asset, the big asset reads small and the small one reads
  big.
- **Lineup test:** always view assets side by side at one scale. The detail density and fineness should
  rise monotonically with true size.

## Proportion and silhouette

From the game camera, silhouette and the big proportions read before any detail does: roof-to-wall
ratio, turret-to-hull ratio, head-to-body ratio. A stylised style may exaggerate them on purpose (big
roofs, chunky doors). That is fine when `STYLE.md` states the exaggeration, so every asset uses the
same factor, and the rulers are then exaggerated consistently too.

## Thumbnail readability

Most games also show each asset as a small icon or thumbnail (often square, 40-128 px). The asset must
be identifiable there and distinct from its siblings, while keeping rich detail for large shots:
- **Compact massing.** The silhouette from the icon camera should fill the icon's frame. A wide, flat
  sprawl (a site of many similar buildings) becomes a smear in a square icon; give it one dominant
  structure with a clear outline and keep the rest tight round it.
- **One or two signature shapes** carry the identity at icon size; detail is the second layer.
- **Value contrast** that survives downscaling (a light / dark split or one bright element), shown on
  the UI's own background colour.
- **Test it on concepts, before a pick, and again at review:** downscale the icon view to the game's
  icon sizes, put the sibling assets on one sheet, and have a judge name each one.

The style records the icon sizes, the background and the frame aspect limit in `STYLE.md`.

## Making it look alive without making it look neon

(Only when the style has emissives, e.g. night scenes or lit machinery. A daylight-only style can skip
this section; the same "purpose, hierarchy, no scatter" rule then applies to small props and decals.)

Emissive detail (lamps, slits, windows, screens) sells an operating, inhabited object. Two ways it
fails:
- **Dead:** too few, too dim, too thin to read at the hero view.
- **Neon or Christmas tree:** too bright, so cores clip to white under the tone map and bloom halos
  spread; or too many, evenly spread, with no job.

What worked:
- **Purpose:** every light has a job: a corner, an entrance, a drive or machine status, a beacon, a
  window in an inhabited space. Scattered automatic dots on open surfaces read as random.
- **Placement:** the signature light sits in real geometry: recesses, block corners, joints. Never on
  grilles, louvres or other repeated-fin families, which read as a sheet of dots. Never just beside
  glass, where it reads as another window. Never grazing a face, where it becomes a 1 px seam.
- **Look:** a crisp edge, a modest peak, the colour pre-saturated slightly so it survives the tone map,
  and a faint halo, not a bloom. Size it to read (a few pixels) at the hero view.
- **Windows:** only real glass glows. Whitelist the actual glass parts, or dark paint, sensor lenses
  and stencils will glow too. Vary windows by compartment, but never split one pane across two
  compartments, or it reads as two small windows. Control rooms and cockpits run dimmer than living
  spaces. Small craft keep glass dark or nearly dark.
- **Every pass:** measure both directions. Counts and visibility of marks keep it alive; peak
  luminance, core whiteness and halo radius keep it from going neon.

## At range

The renderer decides what happens when an asset is small on screen, and that changes the scale read:
- **Pixel floors:** minimum point and bar sizes make every distant light the same blob, and stretch
  bars into little window-shaped boxes. Fade lights by their true area instead, cap the stretch, and
  thin lights by rank as the asset shrinks: corners and signature lights go last.
- **Geometry glass:** it does not blur at range the way texture-painted glass does under mip-mapping,
  so a distant inhabited block becomes a sparkle field. Fade geometry glass by its on-screen area.
- **The check:** look at range shots and the lineup, not only the hero view. Count marks per asset at
  several distances, and keep the order.

## Translating taste into properties

| The user says | Property to measure and fix |
|---|---|
| mushy, wobbly, no clear structure | facet flatness, bevel size, silhouette IoU against the blueprint |
| too clean | plate-tone variance, roughness breakup, contact AO |
| too dirty | grime coverage, streak contrast |
| looks too big | ruler size, detail frequency, lit-window count |
| looks too small, toy-like | detail too coarse, rulers missing |
| dead | count and visibility of signature lights at hero and range |
| neon | peak luminance, white core, halo radius, colour saturation after tone map |
| looks like windows | lights shaped and coloured like glass, rows at window pitch, lights next to glass |
| messy, busy, cluttered | too many small lights, props or parts without a job; no hierarchy |
| roofs or tops too small, too squat, too tall | proportion ratios at the game camera, silhouette share |
| doesn't read from the game camera | silhouette contrast and big-shape value contrast at gameplay distance |

Record the user's word and the property in `corrections.md` (see `style-library.md`). The same word
usually comes back for the next asset.
