# Parts-kit tools (fal parts)

The fal half of the parts kits (`assets/parts/`); the procedural half is `tools/blender/kit.py` ->
`assets/parts-blender/`. Method: `.claude/skills/model-forge/references/parts-kits.md`.

| Script | Use |
|---|---|
| `normalize.mjs raw.glb out.glb --rot rx,ry,rz --size w,h,d --anchor back\|base\|backbase [--tex 1024] [--tris N]` | Tripo GLB -> kit mount frame, per-axis scale to the brief (`-` = free axis) |
| `normalize-uniform.mjs` | same, uniform scale from the key dimension (weapons, engines, large parts) |
| `sheet.mjs out.jpg cell a.png b.png ...` | tile renders into a contact sheet |
| `kit-sheet.mjs out.webp` | render the whole fal kit at one scale (reads `assets/parts/parts.json`) |
