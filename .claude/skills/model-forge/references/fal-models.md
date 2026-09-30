# fal models: what to use for what

Prices are fal list prices at the time (autumn 2026). Check them with the fal connector's pricing tool
before a big batch. Record every job, with its id, prompt and params, in the pipeline record.

## Summary

| Job | Model | Why | Cost (approx) |
|---|---|---|---|
| Art bible / first concept | `fal-ai/nano-banana-pro` | best design sense, clean studio sheets, readable captions | ~$0.15 / image, 4K ~$0.30 |
| Every further concept, part, fix | `fal-ai/nano-banana-pro/edit` | reference images (bible, sister assets, style part) keep the family coherent | same |
| Turnaround sheet | nano-banana-pro/edit at 4K | six ortho views in one sheet, cropped into cells | ~$0.30 |
| Blueprint mesh (large asset) | `tripo3d/h3.1/multiview-to-3d` | won both bake-offs | ~$0.60 |
| Small part mesh | `tripo3d/h3.1/image-to-3d` with `face_limit` 2000-5000, texture, pbr, texture_quality and geometry_quality `detailed` | clean enough at part scale | ~$0.60 |
| Tiling PBR material | `fal-ai/patina/material` (all five maps, 2x upscale) | seamless basecolor, normal, roughness, metalness, height | ~$0.11 / set |

Lost the bake-offs (do not default to them):
- `tripo3d/p2/image-to-3d`: CAD-like and clean, but only single-view, so the unseen sides are
  hallucinated.
- `fal-ai/hunyuan-3d/v3.1/pro` (single and multiview): softer facets, mirrored or garbled markings.
- H3.1 single-view: lost to H3.1 multiview on both pilot assets. Use multiview whenever you have a
  turnaround.

Typical cost for one new asset in an existing style (kits reused):

| Item | Cost |
|---|---|
| concept (about 4-6 images) and beauty shot | $1-1.5 |
| 4K turnaround (1-2 tries) | $0.3-0.6 |
| blueprint mesh | $0.6 |
| 2-3 new fal parts (image + mesh each) | $2-3 |
| 1-2 PATINA sets | $0.1-0.3 |
| **Total** | **about $4-6** |

A redesign after review roughly doubles it. A new style costs its art bible and a starter kit on top: the
fleet's two kits were about $19.5.

A full five-asset family with parts kits cost about $78 across seven rounds. The first build was about
$27.50. Most of the spend went on re-draws after design changes, so fix the brief (stage 1) before you
generate.

## Prompting nano-banana-pro

- **Studio shots:** isolated subject, three-quarter view, clean neutral **light-grey** seamless
  background, soft even studio light, no text unless you want captions. Light background plus light
  paint gives the best reconstructions.
- **Light paint in generation:** ask for off-white or light-grey weathered paint with dark blue-grey
  glass. The runtime livery maps neutral luminance to the operational colour (dark hull) and keeps
  saturated markings. Dark generation paint loses detail in reconstruction.
- **State true size:** give the length or height in metres, plus the human-scale anchors: "2 m crew
  doors, 1 m windows, 20-ft containers, railings 1.1 m". Without them, the model invents detail at the
  wrong frequency, and the asset reads too big or too small.
- **Originality:** say "original design". Name the forms you want (e.g. "faceted armoured pod",
  "spinal railgun", "open-flank through-deck hangar"). Do not name franchises, not even negatively: the
  word itself pulls the image toward them. A judge checks every concept for franchise look-alikes; the
  first fighter read like a franchise fighter and was redesigned.
- **Edits:** with `/edit`, pass the style's art bible plus one or two approved sister assets. Describe
  the change and restate what must stay (proportions, livery, markings).
- **Openings:** anything that must stay open in 3D (bays, recesses, see-through structure) must be
  drawn visibly open in every turnaround view.

### Turnaround prompt (worked)

> Technical orthographic turnaround sheet of EXACTLY this spacecraft (same design, proportions, livery,
> markings, weathering). Six views in a clean 3 x 2 grid of equal cells on a plain seamless light-grey
> background: top row: FRONT view (straight at the bow, camera level), PORT SIDE view (straight at the
> left side, bow pointing left), STERN view (straight at the engines from behind, camera level); bottom
> row: STARBOARD SIDE view, TOP view, BOTTOM view. Orthographic, no perspective, no shadows on the
> background, every view at the same scale, no labels.

Crop the cells (PIL), check each is square to its axis, and feed front / port / stern / starboard to
H3.1 multiview. If the sheet mirrors a marking or drifts in proportion between views, regenerate it
rather than feed it: the mesh inherits every inconsistency.

### Part prompt pattern (worked)

Design the first part (the crew door) with plain nano-banana-pro. Make every other part with `/edit`,
using the door image as the **style reference**, so the kit shares one industrial language. Per part:

> Isolated hull component for an original sci-fi spacecraft parts kit, in the same style, materials
> and weathering as the reference door: <part description with exact dimensions: "a 1.0 m square
> viewport with a 0.2 m chamfered frame, dark blue-grey glass, four bolts">. Three-quarter view from the
> front, on a plain light-grey studio background, light off-white weathered paint, no hull around it,
> nothing else in frame.

Glass parts need a second try more often than not (see below).

## Reconstruction failure modes (seen, with fixes)

- **Glass becomes a hole plus a wedge** (ports, panes): ask for opaque glass with a visible glass
  sheen and a solid backplate, or build glass parts procedurally. The fleet's final ports and panes
  come from the procedural kit.
- **The back is mirrored from the front** (doors): harmless when the back is mounted against the hull.
  Check before using the part free-standing.
- **Thickness is squashed or inflated:** normalise per axis only where the brief fixes all three
  dimensions. Otherwise use uniform scale from the key dimension and record the true bbox.
- **Markings:** a hull number comes out rounded, mirrored or different on each flank, or as a relief
  under the paint. Re-project the stencil onto the texture, flatten the relief (paint has none), or
  paint it in Blender.
- **Hallucinated underside and stern:** the reason multiview wins. For a remodel, trust only the views
  you supplied.
- **Soft, lumpy detail everywhere:** the reason to remodel (stage 6). Patching it (straightening, texture
  fixes, pressed features) only moved the problems around.

## PATINA materials

`fal-ai/patina/material` with a short, physical prompt, e.g. "worn painted steel hull plating, subtle
plate-to-plate tone variation, fine grit, faint streaks", with all five maps and a 2x upscale. Uses:
- **Tri-planar detail layer:** normal, roughness and cavity at one absolute tile size on every asset
  (6 m per repeat on the fleet), so plating reads at the same scale everywhere.
- **Worn-finish sets:** `hullWear` (two-scale plate tone), `hullGrit` (micro grit), `sootStreak`
  (drive soot).
- **Full sets for scene-built parts:** deck, radiator, armour, foil, ceramic.

Lite (phone) copies of every set at 512 px.

## Ingest

Use `tools/ingest-fal.mjs` to download results by job id. Keep raw meshes out of git (`assets/*/raw/`,
gitignored) and keep the job ids in the pipeline record so anything can be re-downloaded.
