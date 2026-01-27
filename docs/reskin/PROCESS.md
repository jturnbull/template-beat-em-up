# Full Reskin Process (Complete)

This document is the master plan for reskinning **all sprites** in the project: characters, backgrounds, and title screens. It is designed to be repeatable, auditable, and suitable for a mixed AI + manual pipeline.

## 0) Inputs & Art Bible
- Define the new world: theme, era, location, palette, materials, lighting, and mood.
- Establish a **Style Bible** (single source of truth):
  - Palette: primary/secondary/accent + neutrals
  - Lighting rules: direction, rim light, shadow softness
  - Line/edge rules: pixel‑sharp, painterly, or outlined
  - Texture density: how detailed at gameplay scale
  - Silhouette hierarchy: characters should pop from backgrounds
- Collect references per category:
  - Characters (front/side orthos)
  - Environment (buildings, street props, signage)
  - UI (logo and button aesthetics)

## 1) Asset Inventory (Automated)
We generate **one task per sprite** plus an index.
- Generator script: `scripts/generate_reskin_tasks.py`
- Output:
  - `docs/reskin/SPRITE_TASKS_INDEX.md`
  - `docs/reskin/tasks/…`

Each task includes:
- Source file path
- Size in pixels
- Group/set (animation group or environment set)
- AI prompt metadata section
- Consistency checklist
- Review checklist

## 2) Character Sprite Requirements (from CLAUDE.md)
The existing checklist in `CLAUDE.md` is the baseline spec. Key highlights:

### Animation Sets (All Characters)
- Idle (3–4 frames, 8 FPS)
- Walk (8–12 frames, 24 FPS)
- Turnaround (2–3 frames, 24 FPS)
- Hurt mid/high (1 frame each, 5 FPS)
- Die (1 frame)
- Jump (4 frames, 24 FPS)
- Knockout (6 frames, 24 FPS)

### Playable‑only
- Punch 1 (2–6 frames, 24 FPS)
- Punch 2 (6–11 frames, 24 FPS)
- Punch 3 (10–17 frames, 24 FPS)
- Air attack (2–4 frames, 24 FPS)

### Enemy‑only
- Attack 1/2/3 (variable frames, 24 FPS)
- Getting up (2–3 frames, 24 FPS)

### Looping Rules
- Idle, Walk, Hurt: **loop true**
- Attacks, Jump, Knockout: **loop false**

### Import Rules
- Filter: **Off**
- Mipmaps: **Off**

These requirements are already captured in the task files via groups, but **CLAUDE.md is the authoritative reference** for frame counts and animation names.

## 3) AI Generation Strategy (fal.ai)
### Per‑Character Consistency
- Target **4:5 aspect ratio** for all character stills/video frames.
- Fix target pixel height (use current sprite sizes as ground truth).
- Use the **same prompt + seed family** across all poses.
- Use reference images: one base sprite + pose sketch.

### Per‑Environment Consistency
- Group by location/area (e.g., `stage_01/stage_elements/buildings`).
- Maintain horizon line and perspective consistency.
- Reduce micro‑details that shimmer at gameplay scale.

### Title Screen
- Preserve **exact pixel sizes** for UI masks and hit‑areas.
- Keep logo legible at 1080p.

## 4) AI Review Pipeline
Each task file has a review section:
- Validate **size** and **baseline alignment**.
- Confirm **silhouette** matches the pose intent.
- Verify **palette + lighting direction** against art bible.
- Compare multiple variants (A/B/C) and select best.

## 5) Manual Refinement (Photoshop)
- Fix anatomy/edges, align feet to baseline.
- Ensure consistent outline weight and shadow direction.
- Remove artifacts (background bleed, halo, text errors).
- Save final PNG **without changing dimensions**.

## 6) Integration into Godot
- Replace PNG in the same path, same filename.
- Let Godot re‑import; verify no size drift.
- Spot check in game:
  - Idle loop quality
  - Walk cycle cadence
  - Attack readability
  - Hurt/knockout readability

## 7) QA Checklist (Per Character)
- Ground line alignment consistent across frames.
- No jitters between frames.
- Attacks read clearly at gameplay speed.
- Left/right mirroring still valid (don’t embed asymmetry if mirroring is used).

## 8) QA Checklist (Backgrounds)
- Character readability maintained (avoid busy textures).
- Parallax layers remain coherent.
- No seams at tile edges.

## 9) Task Tracking
- Task status: TODO → IN‑PROGRESS → DONE
- Record prompt, seed, and model per asset.
- Final selection noted in task file.

## 10) Output Acceptance
The reskin is “complete” when:
- Every task file is marked DONE.
- Every sprite has a matching replacement.
- QA pass is green for characters + backgrounds + title screen.

---

## Notes & References
- The detailed checklists for character creation are in `CLAUDE.md`.
- The fal.ai script example (`fal_api_service.py`) should be referenced in `AI_WORKFLOW.md` once provided.

---

## New Video‑First Workflow (Updated Plan)

### A) Base Still (Anchor Pose)
- Generate a **single idle** on a flat, greenscreen background (`#00b140`).
- Requirements:
  - side‑view
  - feet on ground
  - **not flying**
  - clean silhouette
  - consistent proportions
  - 4:5 aspect ratio

### B) Video Generation (Moves)
- Use `fal-ai/wan/v2.6/image-to-video` with the base still as `image_url`.
- Prompt should include:
  - “same outfit/proportions/lighting”
  - “no camera movement, no zoom”
  - “start and end in matching pose” (for loops)

### C) Extract Frames
- Split the video into frames at the target FPS.
- Select only the frames that read cleanly.

### D) Background Removal
- Use `fal-ai/bria/background/remove` on selected frames.
- This replaces manual chroma keying.

### E) Looping / Frame Counts
- Frame counts are flexible (not fixed to legacy counts).
- Ensure loops reset cleanly (idle/walk) and hits read well (attacks).
