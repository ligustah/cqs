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

## Done
- pkg-diff.mjs (render diff, --csp, --units). Sampler budget fix (uncommitted->committed in this checkpoint):
  patina.js packRoughHeight (detail + interior rough/height in one RGBA texture: -2 samplers), finish.js uses
  detRough()/detHeight() + METAL_IN_ROUGHNESSMAP, glbship.js shareMetalRough (metalness from the roughness texel when
  glTF shares the texture: -1). Hull 18 -> 15, colony 15 -> 13. Dev carrier still vs 851093d dev: 0.01% px differ.
- glbship.js EmbeddedImageBitmaps (from WIP 8703e98) kept for embedded textures under CSP: still to verify.

## Next
3. Decide steel mill GLB (current vs 851093d), rebuild dist, check-package, pkg-diff all views desktop+phone with
   --csp 1 --units 16, phone-check, scale-check, file diff vs published hashes.
- split-glb names external textures by their own type; loadB64 checks the shared length against the tier JSON;
  check-package.mjs gained a glTF-level tier check (counts incl. primitives, bit-identical geometry, images). Verified
  that the check FAILS on the 851093d package (fighter: textures 0/5 of 21 under CSP) and passes on the fixed build.
- Steel mill: current GLB (8703e98 remodel) renders complete in dev ($S/after-dev/desktop/b_steel_mill.dev.png) =>
  not broken/missing => packaged as current (with its matching src/buildings/steel_mill.js).
- dist rebuilt: 399 files, 208.7 MB (199.0 MiB); check-package 57 tiers OK.
- pkg-diff defaults now --csp 1 --units 16.
- Desktop pkg-diff (csp+16 units) running -> $S/after/desktop, log $S/after-desktop.log. fleet/spaceport/6 studios OK
  (spaceport diff = planet cloud speckle only; metric now "solid" share, 2% threshold; broken 851093d fleet = 23%).
- dist vs published: $S/filediff1.txt (7 changed: 4 src + 3 steel_mill tier files; 20 tex added, 8 removed, all steel mill).
- Brown fighters = carrier's parked fighters, lit by the amber hangar lights, exposed when the hull failed to link.
- Desktop pkg-diff DONE: 26/26 pass (solid<=2%), zero console errors. Next: phone pkg-diff (/tmp/claude-0/-home-user-cqs/e592383b-a9f6-5dde-82a6-4494b59b11a7/scratchpad/pf/after/phone), phone-check, scale-check.
- Phone pkg-diff DONE: 26/26 pass, no errors (shipyard/spaceport building diffs = lite tier framing/dressing, checked side by side). Next: phone-check, scale-check.
- phone-check: all 26 views ok, retained heap + GPU max 264 MB (carrier); transient peak + GPU carrier 350 / lineup 314,
  same as the published 851093d package (344 / 294), GPU estimate unchanged. scale-check PASSED.
- Evidence copied to Scene3D/shots/pkg-fix (gitignored). DONE; final commit "Artifact packaging fix: ...".
