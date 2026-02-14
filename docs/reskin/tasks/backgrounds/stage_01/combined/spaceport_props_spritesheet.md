# TASK: spaceport_props_spritesheet

Status: TODO
Category: Background
Source: tmp/flattened/spaceport_props_sheet_seed.png
Target: tmp/flattened/spaceport_props_sheet_seed.png
Size(px): 2048x1024
Group/Set: stage_01/combined

## Brief
- Build a dense retro-futuristic shipping-port props spritesheet for Stage 01.
- Keep postbox + vending machine scale believable and use them as world-size anchors.
- Keep exact canvas size so exports can be sliced predictably.
- Output on solid greenscreen (`#00b140`) so background removal can run after generation.

## AI Generation (fal.ai)
- Model: fal-ai/nano-banana/edit
- Prompt: Create a 2D game-ready prop spritesheet for a retro-futuristic space shipping port. Use the included postbox and vending machine as real-world scale anchors and keep them in-scene style. Fill the remaining canvas with many separate, non-overlapping props laid out in clear grid-like spacing with visible gaps for slicing. Include varied prop categories: cargo crates stamped "AI TOKENS", sealed cargo canisters, magnetic pallet stacks, dock bollards, mooring hooks, coiled energy ropes, fishing gear crates, strange sci-fi lures, antenna buoys, maintenance toolboxes, hazard cones, dock lights, warning beacons, small forklift drones, compact loading cranes, cargo net bundles, fuel cells, spare thruster parts, ship gangplank segments, railing pieces, and signage placards. Style should match a worn arcade-pixel/painted look consistent with CAMINO shop aesthetics. Keep text legible where present ("AI TOKENS"). Use a single flat solid chroma-key greenscreen background color (#00b140) for all empty space; no gradients, shadows, textures, or environmental backdrop. No perspective scene composition: this must read as a flat spritesheet of separate props.
- Negative Prompt: blurry, low-res, transparent background, textured background, gradient background, sky, stars, full scene composition, overlapping props, merged silhouettes, photorealistic, 3D render, illegible text, misspelled text, watermark
- Seed(s): TBD
- Guidance/CFG: TBD
- Reference Images: stages/stage_01/caminoshop.png; stages/stage_01/stage_elements/street_poles/post_box/postbox_clean.png; stages/stage_01/stage_elements/vending_machines/vending_machines_clean_separated_blue_50.png
- Variations: TBD (A/B/C)

## Consistency Checks
- [ ] Size matches reference (2048x1024)
- [ ] Greenscreen background is flat `#00b140`
- [ ] Props are separate/non-overlapping for slicing
- [ ] Postbox/vending machine scale remains believable
- [ ] "AI TOKENS" text is readable and spelled correctly

## Review
- [ ] Option A
- [ ] Option B
- [ ] Option C

## Notes
- Run `python3 scripts/flatten_stage01_brick_building1.py` only if you need to refresh storefront references.
- Generate with `--num-images` > 1 and pick the sheet with the cleanest prop separation.
