# TASK: brick_building1_shop_body (combined)

Status: TODO
Category: Background
Source: tmp/flattened/brick_building1_shop_body.png
Target: tmp/flattened/brick_building1_shop_body.png
Size(px): 1376x1142
Group/Set: stage_01/combined

## Brief
- Convert this combined storefront into a **spaceport sci‑fi tools shop** (selling **fishing equipment** and **laser guns**).
- Preserve the exact canvas size and transparency silhouette so it can drop in.
- The banner already has the **CAMINO** logo burned in (from `source_images/logos/camino.png`): keep the text readable as **CAMINO**, but blend it into the visual style of the building/signage.

## AI Generation (fal.ai)
- Model: fal-ai/nano-banana/edit
- Prompt: Spaceport storefront conversion: turn this combined building facade into a sci-fi tools shop (stocking fishing gear + laser guns). Keep the exact same silhouette/alpha edge, perspective, lighting direction, and overall composition; only change surface textures/decals/posters/props inside the existing silhouette. Integrate the CAMINO banner into the same in-world art style as the rest of the storefront: allow stylized treatment (pixelated LED board, painted metal sign, worn neon, textured vinyl) while keeping the word CAMINO clearly readable and correctly spelled. Transparent PNG; no added background behind the building; no extra objects outside the original silhouette.
- Negative Prompt: blurry, low-res, cropped, background, sky, stars, watermark, misspelled text, illegible text, extra buildings, extra props outside silhouette, photorealistic, 3D render, detached clean corporate logo sticker look
- Seed(s): TBD
- Guidance/CFG: TBD
- Reference Images: tmp/flattened/brick_building1_banner_camino.png
- Variations: TBD (A/B/C)

## Consistency Checks
- [ ] Size matches reference (1376x1142)
- [ ] Transparency silhouette preserved (use `--alpha-from-source`)
- [ ] Lighting/palette matches art bible
- [ ] Banner still reads exactly: CAMINO
- [ ] In‑game readability OK

## Review
- [ ] Option A
- [ ] Option B
- [ ] Option C

## Notes
- Run `python3 scripts/flatten_stage01_brick_building1.py` before generation to refresh the combined source + banner.
