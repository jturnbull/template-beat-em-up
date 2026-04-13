# TASK: captain_snakeoil/intro/sword_only

Status: TODO
Category: Prop
Source: outputs/reskin/captain_snakeoil/intro/assets/throne_scene_standing.png
Target: outputs/reskin/captain_snakeoil/intro/assets/sword_only.png
Group/Set: intro/throne_scene
Size(px): 1034x710

## Brief
- Extract just Captain Snakeoil's sword as a clean prop on the gameplay canvas.
- This will be composited leaning against the throne in the engage start frame.

## AI Generation (fal.ai)
- Model: fal-ai/nano-banana-pro/edit
- Prompt: Keep the exact same pirate cutlass from the source image, in the same 2D arcade style, but remove Captain Snakeoil and remove the throne. Return only the sword as a clean prop on the same gameplay sprite canvas, with no hands, no arms, no character, and no extra props. Solid green background #00b140 outside the sword only.
- Negative Prompt: blurry, cropped, watermark, character, skeleton, pirate, hand, arm, throne, goblet, extra props, different sword, wrong angle, wrong scale, realistic rendering, scenic background
- Seed(s): outputs/reskin/captain_snakeoil/intro/assets/throne_scene_standing.png
- Guidance/CFG: TBD
- Reference Images: outputs/reskin/captain_snakeoil/intro/assets/throne_scene_standing.png
- Variations: 4

## Consistency Checks
- [ ] Sword matches the chosen standing-throne asset
- [ ] No hands or character remnants remain
- [ ] Sword stays fully inside the 1034x710 canvas
- [ ] No extra props appear

## Notes
- Output must stay on the 1034x710 gameplay-style sprite canvas.
