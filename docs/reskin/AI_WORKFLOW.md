# AI Workflow (fal.ai) — This Repo

This repo uses fal.ai for:
- image generation (base idle stills)
- video generation (animation clips)
- background removal (selected frames only)

Rules:
- **Never** commit API keys. Use `FAL_KEY` in your environment.
- This is a **one-off pipeline** for this game; scripts are opinionated and strict.

---

## Primary Entry Point

Use the interactive wizard:
```bash
python3 scripts/reskin_interactive.py
```

It drives the full pipeline described in `docs/reskin/SPRITE_PIPELINE.md`.

---

## Helper Scripts (Internal Building Blocks)

### 1) Generate base stills (nano-banana edit)
Script: `scripts/fal_reskin_generate.py`

- Reads `Source:`, `- Model:`, and `Reference Images:` from the task file.
- Writes `option_1.png`..`option_4.png` into a fresh output folder.
- To use a cheaper/non-pro model, set `- Model: fal-ai/nano-banana/edit` in the task (or pass `--model ...` to override).

### 2) Build the anchor (solid greenscreen + border)
Script: `scripts/prepare_anchor_image.py`

- Uses `fal-ai/bria/background/remove` to get a clean cutout.
- Composites onto a solid `#00b140` background.
- Adds a 2px white border frame guide.
- Matches canvas size + baseline to `global.frame_guide_match`.

### 3) Generate videos (kling)
Script: `scripts/fal_video_generate.py`

Model: `fal-ai/kling-video/o1/image-to-video`

- Always sets `generate_audio=false`.
- Writes `.mp4` files into the given output dir.

### 4) Remove background (bria)
Script: `scripts/fal_bg_remove.py`

Model: `fal-ai/bria/background/remove`

- Used during `--apply-sprites` to BG-remove **only selected frames**.

---

## Batch Mode (No Finder Spam)

When scripts are run from batch drivers (like `scripts/nova_batch.py` / `scripts/reskin_interactive.py`),
we set:
```
RESKIN_BATCH=1
```
Helper scripts check this flag and skip `open ...` calls to avoid opening dozens of Finder windows.
