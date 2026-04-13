# TASK: captain_snakeoil/intro/throne_only

Status: TODO
Category: Prop
Source: outputs/reskin/captain_snakeoil/intro/assets/throne_scene_standing.png
Target: outputs/reskin/captain_snakeoil/intro/assets/throne_only.png
Group/Set: intro/throne_scene
Size(px): 1034x710

## Brief
- Extract just the throne from the chosen standing-throne sprite.
- Keep the throne on the same 1034x710 gameplay-style canvas so it can be left behind when Snakeoil stands up.

## AI Generation (fal.ai)
- Model: fal-ai/nano-banana-pro/edit
- Prompt: Keep the exact same throne from the source image, in the same position, angle, scale, and 2D arcade style, but remove Captain Snakeoil entirely. Return only the throne on the same gameplay sprite canvas, with no character, no sword, no goblet, and no extra props. Solid green background #00b140 outside the throne only.
- Negative Prompt: blurry, cropped, watermark, character, skeleton, pirate, sword, goblet, hands, arms, extra props, different throne, wrong angle, wrong scale, realistic rendering, scenic background
- Seed(s): outputs/reskin/captain_snakeoil/intro/assets/throne_scene_standing.png
- Guidance/CFG: TBD
- Reference Images: outputs/reskin/captain_snakeoil/intro/assets/throne_scene_standing.png
- Variations: 4

## Consistency Checks
- [ ] Throne matches the chosen standing-throne asset
- [ ] No character remnants remain
- [ ] Throne stays fully inside the 1034x710 canvas
- [ ] No extra props appear

## Notes
- Output must stay on the 1034x710 gameplay-style sprite canvas.
