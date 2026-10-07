# Artifact packaging fix: progress note (resumable)

Job: fix the regression from 851093d (split-glb tiers + shared buffer + external WebP) in the published preview.
Scratch: $S = /tmp/claude-0/-home-user-cqs/e592383b-a9f6-5dde-82a6-4494b59b11a7/scratchpad/pf (this job's files).

## Found
- (attempt 3 start) Prior WIP 8703e98 added an EmbeddedImageBitmaps loader plugin in glbship.js on the theory that the
  host CSP blocks fetch(blob:) and tools/check-package.mjs; both UNVERIFIED. No note existed.

## Done

## Next
1. Baseline: worktree of 851093d -> build its dist (= published set), record hashes.
2. Reproduce pkg vs dev (desktop + phone) for fleet, spaceport shot, 6 studios, 18 buildings.

## Found (attempt 3, verified)
- Baseline: worktree $S/base851 (851093d) built -> dist identical (sha256) to the published files fetched earlier
  (scratchpad/resume/live); hashes in $S/published-hashes.json (387 files). Old package (decbb7d) in $S/old.
- Harness w/o CSP, SwiftShader (32 texture units): package == dev (fleet diff 0.9%, carrier/fighter 0%). No repro.
- tools/pkg-diff.mjs (new): pkg vs dev stills + diff; --csp 1 (host-like CSP, connect-src 'self' => fetch(blob:) refused),
  --units 16 (emulates 16 fragment texture units: >16 samplers => link fails, as on ANGLE D3D11/Metal, iOS, Android).
- REPRO: 851093d package with --csp 1 --units 16 shows EXACTLY the user's fleet: CV-50 hull gone (hull material 18
  samplers), bell-XL (17) gone => blue throat-glow spheres float alone, brown fighters/freighters. $S/before/desktop-csp16
- Old package (decbb7d) under the same conditions: hull present (untextured, all embedded textures blocked by CSP =>
  hull had 14 samplers). So: regression = 851093d moved >=2048 px textures to URI files that the CSP lets through; the
  hull's map/normal/rough/metal now load => 18 samplers => link fails on 16-unit GPUs. Embedded (<2048) textures still
  fail via fetch(blob:) => white stacks/shed while the furnace (URI texture) is textured.
- Dev path on a 16-unit GPU also drops the hull (same 18 samplers): the sampler budget is a latent renderer bug.
