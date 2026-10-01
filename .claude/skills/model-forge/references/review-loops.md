# Review loops

Quality came from looking at renders critically and repeatedly, and from independent judges who try to
refute a claim. Never from trusting a change because the code looks right.

## Render harness

- Headless Chromium plus three.js: `node tools/shoot.mjs "<query>" /ABS/out.png [...] --w 1600 --h 1000
  --timeout 900000`. Output paths must be **absolute**, because the tool changes directory into the
  scene folder.
- Each shot takes 45-240 s on CPU. Run one render process at a time, at most about 4 shots per call.
  Use `nohup` and poll the log for long batches.
- Standard views for every asset:
  - hero (az 35, el 18);
  - close (az 50, el 14, dist 0.72);
  - range (dist 2.5 and 5);
  - stern quarter;
  - broadside;
  - the lineup (`mode=lineup`, every asset at one scale with a metre ruler, a 1.8 m figure and a slot
    cube);
  - the scene shot (the asset in its intended context).
- Freeze time (`t=20`) so animated lights compare. Change one variable at a time.
- Compare at **matched resolution and camera**. Glow and point sizes change with resolution, so a
  1600 px after against a 2400 px before gives a wrong verdict.

## Evidence for yourself and the user

- **Before/after sheets:** PIL side-by-sides with labels, plus 1:1 crops (and 3-4x nearest-neighbour
  zooms) of the parts under discussion, and thumbnails at about 400 px for the "at a glance" read.
- **What the user gets:** HD images through the file-sending tool (downscale to about 1 MB if a send
  fails). Publish the interactive scene as an artifact. The user is often on a phone and cannot open
  GLBs.
- **Your own critique first:** look at the images yourself before asking anyone. Many problems (a
  grille of neon bars, a dotted ladder) are obvious at a glance.

## Multi-agent review (when the user opts in to workflows)

Pattern that worked, one agent per asset where possible:

1. **Survey:** read-only. Measure everything in real units, render at range, list findings ranked,
   with evidence (file:line, crop path) and a concrete suggestion. Give surveyors hypotheses to
   **test**, not conclusions.
2. **Standard:** two independent drafts through different lenses (real-world practice versus
   perception / art direction), then one synthesis that decides every disagreement and states why. Test
   budgets with harness overrides before writing them down.
3. **Shared changes:** one agent, before the per-asset agents, with opt-in fields whose defaults leave
   every asset unchanged. This avoids concurrent edits to shared files.
4. **Apply:** each agent edits only its own asset file. Back up first. Ray-cast every new authored
   position onto a real face. Iterate up to three render rounds with an honest self-review.
5. **Verify:** two lenses per asset that pull against each other, e.g. SCALE ("does it read at its
   true size and role?") and LIFE ("is it still as alive and concept-like as the user liked?").
   Verifiers default to refuted, render their own evidence, and return must-fix items with exact
   values they have **tested** by override, plus a keep list.
6. **Fix rounds:** at most two. Then the orchestrator applies the last narrow, tested items itself.
   Verifiers keep finding smaller things, so stop when the remaining items are cosmetic.
7. **Family check:** the lineup and scene shots, cross-asset consistency and ordering.

Practicalities:
- Concurrency is roughly CPUs minus 2: on 4 cores, two agents at a time. A 49-agent run took about
  11 hours.
- Keep workflows small and resumable, and checkpoint-commit finished files as they land.
- Container restarts kill background runs. A restarted run replays completed agents from its journal
  (`resumeFromRunId`); runs killed before any agent finished must be redone, so do short final checks
  inline.
- Save each agent's result JSON. When parsing results, read the journal, not the output file.

## Taste-to-metric translation

The generic table is in `readability.md`. Every translation that came up for a style is in that
style's `corrections.md`. Look there first: the same word usually comes back.
