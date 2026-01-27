# AI Generation Workflow (fal.ai)

This workflow standardizes how we generate and evaluate assets using fal.ai. It is image‑only (no video models).

## Inputs
- Task file for each sprite (`docs/reskin/tasks/...`).
- Art bible (palette, lighting, silhouette rules).
- Reference images for pose + scale.

## Script Integration (fal_api_service.py)
You mentioned `fal_api_service.py` from another project (contains keys + concepts). Once provided (with keys removed), we’ll:
- Extract the request structure and parameter fields.
- Standardize prompts, negative prompts, seed handling.
- Add a “task → batch generation” helper.

**Important:** Do not commit API keys into this repo.

## Local Helper Script
We now have a local, image‑only helper:
- `scripts/fal_reskin_generate.py`

Example usage:
```bash
FAL_KEY=... python3 scripts/fal_reskin_generate.py \\
  --task docs/reskin/tasks/characters/playable/chad/idle/idle_00.md \\
  --prompt \"[your prompt]\" \\
  --negative \"[your negative]\" \\
  --model fal-ai/flux-pulid \\
  --num-images 3 \\
  --ref /path/to/style_ref_01.png \\
  --ref /path/to/style_ref_02.png \\
  --download
```

## Video Generation (kling-video v2.6)
Helper script:
- `scripts/fal_video_generate.py`

Example:
```bash
FAL_KEY=... python3 scripts/fal_video_generate.py \
  --image outputs/fal/idle_anchor/option_1.png \
  --prompt \"Nova performs a grounded idle with slight motion, same outfit/proportions/lighting, no camera movement, solid #00b140 background\" \
  --negative \"low resolution, error, worst quality, low quality, defects\" \
  --resolution 1080p \
  --duration 5
```

Note: this model does not expose fps control; extract fewer frames with ffmpeg to match target frame counts.

## Background Removal (bria)
Helper script:
- `scripts/fal_bg_remove.py`

Example:
```bash
FAL_KEY=... python3 scripts/fal_bg_remove.py \
  --input outputs/fal/frames/idle \
  --output-dir outputs/fal/frames/idle_no_bg
```

You can also pass a folder of reference images:
```bash
FAL_KEY=... python3 scripts/fal_reskin_generate.py \\
  --task docs/reskin/tasks/characters/playable/chad/idle/idle_00.md \\
  --prompt \"[your prompt]\" \\
  --ref-dir /path/to/reference_set \\
  --download
```

## Example: nano-banana-pro/edit
```bash
FAL_KEY=... python3 scripts/fal_reskin_generate.py \\
  --task docs/reskin/tasks/characters/playable/chad/idle/idle_00.md \\
  --prompt \"Nova grounded idle pose, not flying\" \\
  --model fal-ai/nano-banana-pro/edit \\
  --aspect-ratio auto \\
  --resolution 4K \\
  --num-images 1 \\
  --ref source_images/AIP_Nova.png \\
  --ref source_images/AIP_Nova_pose2.jpg \\
  --download
```

## Prompt Template
- Prompt: `"[subject], side‑view 2D sprite, [style], clean silhouette, consistent lighting, transparent PNG"`
- Negative: `"blurry, cropped, background, watermark, extra limbs"`

## Consistency Rules
- **Pixel size must match** the existing sprite file.
- **Ground line alignment** must match the original.
- Use the **same seed family** for related frames.

## Review Flow
- Generate 3–5 variants.
- Compare in‑engine or as strips.
- Select best option and record metadata in the task file.

## Metadata to Record
- Model
- Prompt + negative
- Seed(s)
- CFG/Guidance
- Reference images used

## Notes
- This workflow intentionally excludes video generation.
