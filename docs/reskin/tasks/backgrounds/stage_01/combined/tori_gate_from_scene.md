# TASK: tori_gate_from_scene

Status: TODO
Category: Prop
Source: tmp/flattened/tori_gate_scene_extract_source.png
Target: tmp/flattened/tori_gate_scene_extract_source.png
Size(px): 970x820
Group/Set: stage_01/combined

## Brief
- Extract only the approved gate from the chosen in-scene result.
- Keep the exact same gate design, angle, and scale from the scene edit.
- Remove the floor, wall, sky, and all surrounding scene context.

## AI Generation (fal.ai)
- Model: fal-ai/nano-banana-pro/edit
- Prompt: Keep the exact same spaceport checkpoint gate from this source image in the same angle, same scale, and same 2D arcade art style, but remove the surrounding scene entirely. Return only the gate on a solid green background #00b140. Do not redesign the gate, do not change its proportions, and do not add any floor, wall, sky, cables outside the gate, or extra props. The result should be a standalone gameplay prop ready for later slicing.
- Negative Prompt: changed gate design, changed angle, changed scale, floor, wall, sky, scenic background, black background, transparent smoke, extra props, extra posts, shrine gate, torii, blurry, cropped, photorealistic, 3D render
- Seed(s): tmp/flattened/tori_gate_scene_extract_source.png
- Guidance/CFG: TBD
- Reference Images: tmp/flattened/tori_gate_scene_extract_source.png
- Variations: 4 options (`option_1.png`..`option_4.png`)

## Consistency Checks
- [ ] Gate matches the chosen in-scene design
- [ ] Angle and scale are unchanged from the scene edit
- [ ] Only the gate remains
- [ ] Background is solid greenscreen
- [ ] No extra props or floor fragments remain

## Notes
- Create the extraction source crop with `python3 scripts/tori_gate_scene_plate.py crop-option --option <chosen-scene-option>`
