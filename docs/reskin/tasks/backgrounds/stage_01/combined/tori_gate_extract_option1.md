# TASK: tori_gate_extract_option1

Status: TODO
Category: Prop
Source: tmp/flattened/tori_gate_direct_option1_extract_source.png
Target: tmp/flattened/tori_gate_direct_option1_extract_source.png
Size(px): 834x676
Group/Set: stage_01/combined

## Brief
- Extract only the gate from direct replace `option_1`.
- Keep the exact same gate design, same angle, same perspective, and same proportions.
- Remove the floor, wall, sky, fence, and all other scene context.

## AI Generation (fal.ai)
- Model: fal-ai/nano-banana-pro/edit
- Prompt: Keep the exact same spaceport checkpoint gate from this source image in the exact same angle, perspective, scale, proportions, and 2D arcade painted style. Remove the surrounding scene entirely and return only the gate on a solid green background #00b140. Do not redesign the gate. Do not change the beam angle, the post tilt, the sign placement, or the overall silhouette. Remove the deck, wall, sky, rock, fence, and every other background element. Keep the gate fully visible and intact inside the same 834x676 canvas.
- Negative Prompt: changed gate design, changed angle, changed perspective, changed scale, torii, shrine gate, Japanese gate, floor, wall, sky, fence, rock, scenic background, black background, cropped gate, extra props, extra posts, extra cables outside the gate, blurry, photorealistic, 3D render
- Seed(s): tmp/flattened/tori_gate_direct_option1_extract_source.png
- Guidance/CFG: TBD
- Reference Images: outputs/reskin/stage_01/tori_gate_direct_replace_pass1/tori_gate_direct_replace/option_1.png; source_images/tori_gate_refs/close.jpg
- Variations: 4 options (`option_1.png`..`option_4.png`)

## Consistency Checks
- [ ] Same gate as direct replace option 1
- [ ] Angle and perspective preserved
- [ ] Only the gate remains
- [ ] Background is solid greenscreen
- [ ] Gate is fully intact within the canvas
