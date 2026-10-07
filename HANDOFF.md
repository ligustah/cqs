# Handoff: CQS Orbital Fleet session state

Branch `claude/vibrant-knuth-tx4hru` of `ligustah/cqs`. Read this file first when you resume the work in a new
session or on a new machine.

## What this is

`Scene3D/` is a three.js preview of the Conquer-Space reboot's 3D assets. It contains:
- the fleet in orbit and a scale lineup;
- the V-31 ground vehicle;
- 18 buildings, including the shipyard and the spaceport.

All of it is original IP, built with the **model-forge** skill (`.claude/skills/model-forge/`) and constrained by the
**cqs-fleet** style (`style-library/styles/cqs-fleet/`).

## Read first

| File | What it holds |
|---|---|
| `style-library/styles/cqs-fleet/STYLE.md` | The specification: rules per asset type, quality bar, review protocol and checklist |
| `style-library/styles/cqs-fleet/corrections.md` | Every user correction (1-46), in their words |
| `Scene3D/tools/blender/buildings/BUILDING-GUIDE.md` | The recipe for colony buildings, its gotchas and the family checklist |
| `Scene3D/tools/blender/buildings/REMODEL-PROGRESS.md` | The steel mill iteration log and the state at handoff |
| `Scene3D/README.md` | Runtime, tiers, phone budget, packaging |

## The published preview

- **Artifact:** https://claude.ai/artifact/7ixC6jhUuHyV4Q5mGkYdFd (private to the user). Republish to the same URL;
  never create a new artifact for the preview.
- **Build the package:**

  ```sh
  cd Scene3D
  node tools/build-artifact.mjs
  ```

  This writes `dist/` and `dist/files.json`, and runs `check-package.mjs`.
- **Stage and publish:**
  1. Run `python3 tools/stage-artifact.py <stage-dir> --out plan.json`. It mirrors the package into a stage dir and
     writes the incremental `files` map (changed, added, and removed = null).
  2. Publish with the Artifact tool:
     - `url` = the artifact above;
     - `root` = the stage dir;
     - `file_path` = `<stage>/orbital-fleet.html`;
     - `files` = `plan.json`.
- **First publish from a fresh machine:** the stage dir is empty, so every path counts as added. One publish holds at
  most 255 files and 64 MB; the package has about 400 files and 210 MB, so split the map over several publishes to
  the same URL. A version holds at most 256 MiB and 511 files.
- **Before reporting:** verify the published package with
  - `node tools/pkg-diff.mjs <view>`;
  - `node tools/pkg-diff.mjs --device phone <view>`;
  - `node tools/phone-check.mjs <view>`.

  Then look at the published page itself (STYLE.md section 8).

## Tools the session used

- **fal** (MCP connector "fal_ai"): image models (`nano-banana-pro/edit`), image-to-3D (`tripo3d/h3.1`), and PATINA
  materials.
  - The user pre-approved spending, with no cap.
  - Record every job in `Scene3D/pipeline/fal-pipeline.json`.
  - The allow rules are in `.claude/settings.json`.
- **Blender:** headless `bpy` 5.x in a Python venv with numpy, pillow, scipy and opencv. The exact setup steps are in
  BUILDING-GUIDE.md.
- **Chromium and Playwright** for the renders and checks (`tools/shoot.mjs`, `tools/buildings/compare.mjs`).

## State at handoff

- **Fleet, vehicle, shipyard, spaceport:** done and published.
- **Packaging fix** (host CSP and the 16-texture-unit limit): published as artifact version 24.
- **Steel mill:** the remodel pilot for all colony buildings. It is in its last iteration rounds (capped at 25 by the
  user); round 25 is the final 4096 build with its evidence. See REMODEL-PROGRESS.md for the final state.
- **The other 15 colony buildings:** built in v3, from raw fal components. That is below the quality bar. They are
  to be rebuilt with the steel mill recipe in BUILDING-GUIDE.md, the transmitter included.
- **User preferences:**
  - HD images, not file paths (they are often on a phone);
  - push notifications for long runs;
  - light paint for buildings and a dark livery for ships;
  - the phone must work;
  - check the published page before reporting.
