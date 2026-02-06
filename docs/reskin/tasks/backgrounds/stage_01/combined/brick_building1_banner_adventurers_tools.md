# TASK: brick_building1_banner_adventurers_tools

Status: TODO
Category: Background
Source: tmp/flattened/brick_building1_banner_love_yourself.png
Target: tmp/flattened/brick_building1_banner_love_yourself.png
Size(px): 790x328
Group/Set: stage_01/combined

## Brief
- Replace the banner/sign with **ADVENTURERS TOOLS** branding in the same style/lighting.
- Theme: **spaceport gear shop** selling **sci‑fi fishing equipment** + **laser guns**.
- Preserve exact canvas size + transparency silhouette.

## AI Generation (fal.ai)
- Model: fal-ai/nano-banana/edit
- Prompt: Neon banner/sign conversion: re-theme this sign into a spaceport shop banner that reads ADVENTURERS TOOLS (spelled exactly). Add subtle sci‑fi fishing + laser‑gun motifs (e.g., hook/line, lure, tackle box, ray pistol silhouette) while keeping the exact same silhouette/alpha edge, perspective, and lighting direction. Text must be legible and centered. Transparent PNG; no added background; no extra elements outside the original sign silhouette.
- Negative Prompt: blurry, low-res, cropped, background, sky, stars, watermark, misspelled text, illegible text, extra text, extra props outside silhouette, photorealistic, 3D render
- Seed(s): TBD
- Guidance/CFG: TBD
- Reference Images: TBD (recommend passing the selected shop-body option via `--ref`)
- Variations: TBD (A/B/C)

## Consistency Checks
- [ ] Size matches reference (790x328)
- [ ] Transparency silhouette preserved (use `--alpha-from-source`)
- [ ] Text reads exactly: ADVENTURERS TOOLS
- [ ] In‑game readability OK

## Review
- [ ] Option A
- [ ] Option B
- [ ] Option C

## Notes
- Run `python3 scripts/flatten_stage01_brick_building1.py` before generation to refresh the banner source.
