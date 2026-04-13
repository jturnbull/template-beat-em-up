# TASK: tori_gate_direct_replace

Status: TODO
Category: Background
Source: source_images/tori_gate_refs/far.jpg
Target: source_images/tori_gate_refs/far.jpg
Size(px): 1354x676
Group/Set: stage_01/combined

## Brief
- Directly edit the provided far screenshot.
- Replace only the current torii gate with a wider spaceport checkpoint gate.
- Remove the Godot/editor/layout noise from the final image.

## AI Generation (fal.ai)
- Model: fal-ai/nano-banana-pro/edit
- Prompt: Edit this exact screenshot. Replace only the existing orange torii gate with a broader retro-futuristic spaceport checkpoint gate that matches the in-game camera angle, perspective, and scale from the provided screenshots. Keep the deck, shop wall, rock, fence, sky, and overall painted arcade style consistent with the source image. The new gate should read clearly as a port or dock checkpoint with worn industrial metal, scanner lights, signal hardware, cables, and subtle readable checkpoint signage. It must not read as a shrine, torii, or Japanese gate. Also clean up the source image by removing all Godot/editor/layout noise: grey empty editor background, guide lines, red translucent overlays, collision/selection tint, and the label text over the gate. Do not add HUD, health bars, version text, or any UI from the close screenshot. Do not repaint the whole scene; change only the gate and the editor noise.
- Negative Prompt: torii, shrine, temple gate, Japanese gate, fantasy gate, HUD, health bar, version text, UI, editor grid, guide lines, selection overlay, collision overlay, grey background, black box, wrong perspective, wrong angle, tiny gate, giant gate, blurry, cropped, photorealistic, 3D render, full-scene repaint
- Seed(s): source_images/tori_gate_refs/far.jpg
- Guidance/CFG: TBD
- Reference Images: source_images/tori_gate_refs/close.jpg; stages/stage_01/caminoshop.png
- Variations: 4 options (`option_1.png`..`option_4.png`)

## Consistency Checks
- [ ] Gate angle matches the screenshots
- [ ] Gate scale fits the scene
- [ ] Gate reads as a spaceport checkpoint
- [ ] Godot/editor noise is removed
- [ ] No HUD or UI is introduced
