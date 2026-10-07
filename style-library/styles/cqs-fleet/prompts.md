# Prompts that worked (cqs-fleet)

Every job id and parameter is recorded in `Scene3D/pipeline/fal-pipeline.json`, and the per-part jobs
in `Scene3D/assets/parts/parts.json`. This file keeps the reusable wording. Paste the `{style}` block
into every concept prompt.

## {style} block

> Photorealistic spacecraft in a credible near-future 'naval-industrial' design language, as in a
> high-end aerospace concept photograph: faceted hard-surface hull with chamfered edges and layered
> armour plates, off-white thermal-control paint with realistic weathering, scuffs and panel-to-panel
> colour variation, amber hazard and identification markings and stencilled hull numbers like on
> real naval ships, small painted cobalt-blue identification bands, bare brushed-metal and gunmetal
> structural frames, gold and silver multi-layer insulation blankets on sensor and electronics boxes,
> dark ceramic heat tiles on the belly, radiator panels, RCS thruster quads, antennas and hand rails at
> human scale, hatches, ladders and small windows that make each ship read as a real engineered object at
> its true size, large fusion-drive engine bells with magnetic-nozzle coils, heavy radiation shielding
> between the drive and the crew sections. Physically based materials, real-world engineering logic, no
> aerodynamic wings, no neon, no glowing trim, no glowing panel lines, no emissive strips, engines and
> emitters switched off, not a video game, not stylised, not a toy. Original design, not based on any
> existing franchise.

Keep this sentence up to date with the rulers. The real scale is now much larger than the first bible's
(the fighter is 71.7 m, not 16 m), so state the true length and the anchors in every prompt: "2 m crew
doors, 1 m windows in 3 m deck rows, 1.1 m rails, 20-ft containers".

## Art bible (nano-banana-pro, 4K, 16:9)

> A professional concept art design sheet for an original science-fiction space fleet on a clean neutral
> light-grey studio background. Five ship classes arranged in a tidy grid, each large enough to read its
> details (not to scale), each with a small clean sans-serif caption: <CLASS (one-line description with
> length and signature features)> ... {style} Photorealistic, like a professional studio photograph of
> highly detailed physical models, soft even studio lighting, three-quarter views, natural materials and
> wear.

## Isolated concept (nano-banana-pro/edit, refs: bible and approved sister ships; 4:3, 2K, 2 images)

> Using the attached concept sheet only as the design-language reference, render ONLY the {class} as one
> isolated object: {description} Three-quarter view from the front-left and slightly above (camera about
> 35 degrees off the bow, 20 degrees up). The entire ship is visible and centred with generous empty
> margin, filling about 70% of the frame. Plain seamless light-grey studio background, soft even
> lighting, no floor, no cast shadow, no environment, no stars, no text, no labels, no engine exhaust
> plumes, no motion blur. Photorealistic, like a studio photograph of a highly detailed physical model
> with real materials and subtle weathering, sharp focus, suitable for 3D reconstruction. {style}

The `{description}` names the forms positively (e.g. "one elongated faceted armoured fuselage shaped
like a flattened hexagonal pod ... two compact weapon sponsons hugging the lower flanks each carrying a
single long railgun barrel"). It lists what must not appear ("no wings, no tail fins, nothing
projecting outward from the sides") and ends with the paint, the bands and the hull number.

## Beauty shot (edit, refs: the approved isolated concept)

> The same ship in orbit above a planet, in its dark matte operational livery (dark charcoal-grey paint
> over the same panels, markings kept faint), lit by one hard sun from the side, black space, a thin
> bright atmosphere limb, a few small amber recess lights at block corners, engines off.

## Turnaround (edit at 4K, refs: the approved concept)

The worked text is in `model-forge/references/fal-models.md`: six ortho views in a 3 x 2 grid, one
scale, light-grey, no labels. For a bay or recess that must stay open in 3D, add "the hangar bays are
open and see-through in every view".

## Parts kit (edit, ref: the door concept `assets/parts` door image)

> Isolated hull component for an original sci-fi spacecraft parts kit, in the same style, materials and
> weathering as the reference door: <part with exact metric dimensions>. Three-quarter view from the
> front, on a plain light-grey studio background, light off-white weathered paint, dark blue-grey glass,
> no hull around it, nothing else in frame.

Tripo H3.1 image-to-3D with texture and PBR on, detailed quality, `face_limit` 2000-5000. Glass parts
(ports, panes) came back as holes twice; the shipped glass is procedural.

## PATINA materials (all five maps, 2x upscale, tiling both)

- `hull`: Photoreal off-white spacecraft thermal-control paint over composite hull panels, rectangular
  panels of varied sizes with thin recessed seams, flush fasteners, small access hatches, realistic
  weathering, scuffs, slight panel-to-panel colour variation, seamless.
- `armor`: Gunmetal grey heavy warship armour plating, thick bolted plates with chamfered edges, weld
  seams, worn edges showing bare steel, seamless.
- `deck`: Spaceship hangar deck plating, dark grey non-slip tread steel plates with painted yellow
  safety lines and recessed tie-down points, seamless.
- `radiator`: Spacecraft radiator panel, dense parallel cooling fins, dark anodised metal with faint
  blue heat discolouration, seamless.
- Others (`orange`, `ceramic`, `foil`, `hullWear`, `hullGrit`, `sootStreak`): see the pipeline record.

## Weathering library (v27, the colony buildings' photographic grime; PATINA, square_hd, upscale 2, tiling both)

All four use "Top-down orthographic photograph of ..., flat and evenly lit with no shadows and no lighting gradient,
seamless tileable texture ... Realistic photographic heavy industrial weathering. No text, no markings." with:
- `wxCladding` (seed 60612): off-white to warm light-grey painted steel cladding panels about 1 x 2-3 m, thin dark
  joints, long vertical grime and soot streaks down from every horizontal joint, thin orange-brown rust drips under bolts
  and seams, darker grime at panel edges, uneven panel tone, chalky matte paint, a few dents. Good: streaks and drips.
  Its panel joints must be removed before use (`cpaint._unline`).
- `wxSteel` (60613): grimy dark grey painted structural steel, neutral gunmetal, mottled soot, scratches, chipped
  flakes of bare steel, faint rust spots, weld beads, bolts; "neutral grey colour, not brown". Came back nearly uniform:
  a subtle layer only.
- `wxConcrete` (60614): stained industrial concrete slab, mid grey, large dark damp patches and oil stains several
  metres across, black oil spots, tyre scuffs, fine cracks, dust. Good.
- `wxRoof` (60615): sooty light-grey trapezoidal roof sheeting, ribs one way, dark laps, soot streaks down the ribs.
  Came back diagonal and bluish: luminance only, low strength.

## Ground units and installations (v16 concept spreads)

Every prompt and job id is in `Scene3D/pipeline/fal-pipeline.json` (`v16_concepts_vehicle_shipyard_spaceport`).

- **The `{style}` block, adapted:** "ground vehicle" or "orbital station" in place of "spacecraft". Keep
  the paint, markings, materials, engineering realism and "original design, not based on any existing
  franchise".
- **Vehicle:** an isolated three-quarter view on light grey with a 1.8 m crew member **in front of the
  nose**, plus body cues tied to him (see lessons 17). List the fleet cues explicitly: a gunmetal
  chamfered octagonal nose collar, a dark gunmetal belly band, hatched amber corner blocks, one
  vertical amber band, a small cobalt square, the upright stencil V-31 and a gold-foil sensor cube.
  Ban automotive cues: no mirrors, wipers, round lamps or grille slats.
- **Shipyard:** an elevated aerial three-quarter view on flat light-grey terrain, like an
  architectural model in overcast daylight. Put a true DD-12 in a berth, and use the **v9 remodel
  render** as its reference. Use ratio rulers: "a semi-trailer is about 1/12 of the ship's length".
- **Spaceport:** a studio three-quarter view on light grey. References: the CV-50 concept, the CT-4
  remodel render and a civil-only crop of the fal kit (no weapon row). Leave the bible out.

## Round 2 (v17): compact installations, thumbnail-first

Every job is in `Scene3D/pipeline/fal-pipeline.json` (`v17_concepts_r2_shipyard_spaceport`). The
prompts are in `scratchpad/v17/<asset>/prompts.json` and the fix prompts in `.../spaceport-fix/prompts-fix.json`.
- **Framing for icons:**
  - shipyard: an elevated three-quarter view of the whole compact facility as an island on plain flat
    light-grey ground, filling about 70% of the frame;
  - station: floating in a light-grey void, with a three-quarter camera at about 30°.
- **Signature first:** name the one shape that must read at 40 px, then the forms, then the bans.
- **Shipyard refs:** DD-12 v9 render, K-214 concept, and the one-scale lineup (lesson 21).
- **Station refs:** one turret-free CV-50 flank crop, hue-shifted to amber (lesson 23). No ship docked.
- **Lettering:** ask for "the number exactly once". The model otherwise adds words like "BERTH 01" or
  "ORBITAL DOCK".

## Round 3 (v18)

Full prompts: `scratchpad/v18/<asset>/jobs.json`; records in `fal-pipeline.json` (`v18_...`).
- **Dusk, lights on (installations):** "a dim overcast dusk, low overall exposure, deep shadows; strong
  depth from layered structure... working lights ON: white floods on slim masts, small hard-edged deep
  golden-amber lamps at corners, crane cabs and jib tips, a few warm lit windows, two or three tiny
  welding sparks. Small crisp fixtures with soft spill: not neon, no glowing trim, no beams, no fog; not
  a night scene." Drop "lights off" from the style block.
- **Real unit, part-built:** name the reference as "the real ship this station builds... draw THAT
  ship, part-built", then the build state (front plated, rear bare octagonal ring frames on the keel).
- **Lean sizing:** "the carrier dominates the volume... the station's whole outline about 1.1-1.3x the
  carrier's length... trusses 15-30 m thick... no bulky mass several times the ship's size."
