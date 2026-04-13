# TASK: captain_snakeoil/intro/seated_master_end_v2

Status: TODO
Category: Character
Source: characters/enemies/tax_man/resources/sprites/seated/wine_drink/wine_drink_01.png
Target: outputs/reskin/captain_snakeoil/intro/assets/seated_master_end.png
Group/Set: intro/seated_master
Size(px): 764x710

## Brief
- Build the seated end pose from the later Tax Man seated beat, keeping the same throne and overall composition as the seated start.
- End pose must still read as the same seated setup, just slightly more composed/smug than the start.

## AI Generation (fal.ai)
- Model: fal-ai/nano-banana-pro/edit
- Prompt: Replace the source character with Captain Snakeoil while keeping the exact in-game seated sprite framing, angle, scale, and seated body language from the source. Keep him on the same throne from the seated start reference, still holding the goblet, with a slightly more smug settled expression and pose than the start frame. No scenic background, no camera movement, no zoom, solid green background #00b140 outside the character and throne only, no extra characters.
- Negative Prompt: blurry, cropped, watermark, scenic background, deck background, close-up framing, wrong angle, wrong scale, realistic rendering, extra limbs, missing goblet, missing throne, mutated throne, drifting props
- Seed(s): characters/enemies/tax_man/resources/sprites/seated/wine_drink/wine_drink_01.png
- Guidance/CFG: TBD
- Reference Images: outputs/reskin/captain_snakeoil/intro/assets/seated_master_start.png; outputs/reskin/captain_snakeoil/intro/assets/throne_scene_standing.png; outputs/reskin/captain_snakeoil/base/chosen.png
- Variations: 4

## Consistency Checks
- [ ] Seated in-game sprite angle and scale are preserved
- [ ] Same throne design as seated start
- [ ] Snakeoil remains seated with goblet visible
- [ ] End pose is distinct but compatible with seated start
- [ ] No scenic background or cropped throne pieces

## Notes
- Output must stay on the 764x710 gameplay-style sprite canvas.
