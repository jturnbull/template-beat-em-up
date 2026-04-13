# TASK: tori_gate_scene_plate

Status: TODO
Category: Background
Source: tmp/flattened/tori_gate_scene_plate.png
Target: tmp/flattened/tori_gate_scene_plate.png
Size(px): 1600x900
Group/Set: stage_01/combined

## Brief
- Insert a proper spaceport checkpoint gate into the empty slot in this stage scene.
- Keep the scene angle, stage style, floor perspective, and wall perspective locked so the gate lands at the right scale.
- This is the approval pass. Do not extract the gate yet.

## AI Generation (fal.ai)
- Model: fal-ai/nano-banana-pro/edit
- Prompt: Edit this exact 2D arcade stage crop. Add a broad retro-futuristic spaceport checkpoint gate into the open slot between the deck and the shop wall. Keep the camera angle, floor perspective, wall perspective, sky, clouds, storefront, and overall painted arcade-background style unchanged. Use the reference screenshots only to understand the true in-game angle, proportions, and placement of the original gate. Ignore all HUD, health bars, version text, editor overlays, guide lines, collision shapes, and grey layout background visible in the reference screenshots. The new gate must sit on the deck and against the wall at this exact in-scene angle and scale. Make it read as a dock or port checkpoint with worn industrial metal, scanner lights, signal hardware, cables, docking tech, and subtle readable checkpoint signage. It must not read as a shrine, torii, or Japanese gate. Preserve the open passage through the middle. No full-scene repaint, no black box fill, no extra buildings, no moving the floor or wall, no poster composition.
- Negative Prompt: shrine, torii, temple gate, Japanese gate, fantasy gate, black rectangle, opaque box, scenic repaint, concept poster, changed camera angle, wrong perspective, wrong scale, tiny gate, giant gate, photorealistic, 3D render, blurry, cropped, extra props, moved storefront, moved floor, health bar, UI, HUD, version text, editor grid, collision overlay, grey layout background
- Seed(s): tmp/flattened/tori_gate_scene_plate.png
- Guidance/CFG: TBD
- Reference Images: source_images/tori_gate_refs/far.jpg; source_images/tori_gate_refs/close.jpg; stages/stage_01/caminoshop.png
- Variations: 4 options (`option_1.png`..`option_4.png`)

## Consistency Checks
- [ ] Scene perspective is preserved
- [ ] Gate reads as a spaceport checkpoint immediately
- [ ] Gate angle and scale feel correct in-scene
- [ ] Floor and wall remain stable
- [ ] No black box or opaque fill appears

## Notes
- Build the source plate with `python3 scripts/tori_gate_scene_plate.py build-plate`
- Review only the combined in-scene result here. Extraction happens in a second pass after one option is approved.
