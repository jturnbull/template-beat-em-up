# TASK: brick_building1_shop_body (combined)

Status: TODO
Category: Background
Source: tmp/flattened/brick_building1_shop_body.png
Target: tmp/flattened/brick_building1_shop_body.png
Size(px): 1376x1142
Group/Set: stage_01/combined

## Brief
- Convert this combined storefront into an **"Adventurers Tools"** shop that sells **sci‑fi fishing equipment** and **laser guns**.
- Preserve the exact canvas size and transparency silhouette so it can drop in.
- The **shop name text should NOT be on this image** (it will be on the separate banner task).

## AI Generation (fal.ai)
- Model: fal-ai/nano-banana/edit
- Prompt: Spaceport storefront conversion: turn this combined building facade into a sci‑fi tools shop (stocking fishing gear + laser guns). Keep the exact same silhouette/alpha edge, perspective, lighting direction, and overall composition; only change surface textures/decals/posters/props inside the existing silhouette. Do NOT add large storefront name text to this image. Transparent PNG; no added background behind the building; no extra objects outside the original silhouette.
- Negative Prompt: blurry, low-res, cropped, background, sky, stars, watermark, misspelled text, illegible text, extra buildings, extra props outside silhouette, photorealistic, 3D render
- Seed(s): TBD
- Guidance/CFG: TBD
- Reference Images: tmp/flattened/brick_building1_banner_love_yourself.png
- Variations: TBD (A/B/C)

## Consistency Checks
- [ ] Size matches reference (1376x1142)
- [ ] Transparency silhouette preserved (use `--alpha-from-source`)
- [ ] Lighting/palette matches art bible
- [ ] No shop-name text on the facade
- [ ] In‑game readability OK

## Review
- [ ] Option A
- [ ] Option B
- [ ] Option C

## Notes
- Run `python3 scripts/flatten_stage01_brick_building1.py` before generation to refresh the combined source + banner reference.
