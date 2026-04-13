# TASK: captain_snakeoil/intro/seated_master_start_v2

Status: TODO
Category: Character
Source: characters/enemies/tax_man/resources/sprites/seated/wine_swirl/wine_swirl_00.png
Target: outputs/reskin/captain_snakeoil/intro/assets/seated_master_start.png
Group/Set: intro/seated_master
Size(px): 764x710

## Brief
- Build the seated reveal start pose in the same framing as the Tax Man seated sprite.
- Snakeoil must be seated on the throne holding a goblet, with the throne baked into the same sprite canvas.

## AI Generation (fal.ai)
- Model: fal-ai/nano-banana-pro/edit
- Prompt: Replace the source character with Captain Snakeoil while keeping the exact in-game seated sprite framing, angle, scale, and goblet-hand pose from the source. Add the same throne from the reference image directly behind him, baked into the same sprite canvas. Keep him seated facing left in a smug villain pose, keep the goblet readable, and keep the throne design consistent. No scenic background, no camera movement, no zoom, solid green background #00b140 outside the character and throne only, no extra characters.
- Negative Prompt: blurry, cropped, watermark, scenic background, deck background, close-up framing, wrong angle, wrong scale, realistic rendering, extra limbs, multiple characters, missing goblet, missing throne, mutated throne, drifting props
- Seed(s): characters/enemies/tax_man/resources/sprites/seated/wine_swirl/wine_swirl_00.png
- Guidance/CFG: TBD
- Reference Images: outputs/reskin/captain_snakeoil/intro/assets/throne_scene_standing.png; outputs/reskin/captain_snakeoil/base/chosen.png; source_images/AIP_Captain_Snakeoil.jpg
- Variations: 4

## Consistency Checks
- [ ] Seated in-game sprite angle and scale are preserved
- [ ] Same throne design as the standing-throne anchor
- [ ] Snakeoil is clearly seated
- [ ] Goblet reads cleanly
- [ ] No scenic background or cropped throne pieces

## Notes
- Output must stay on the 764x710 gameplay-style sprite canvas.
