# TASK: captain_snakeoil/intro/throne_scene_standing

Status: TODO
Category: Character
Source: characters/enemies/tax_man/resources/sprites/seated/engage/engage_01.png
Target: outputs/reskin/captain_snakeoil/intro/assets/throne_scene_standing.png
Group/Set: intro/throne_scene
Size(px): 1034x710

## Brief
- Build the canonical Captain Snakeoil standing-throne scene in the same framing as the Tax Man engage sprite.
- Snakeoil must stand facing left with the throne directly behind him, all baked into the same sprite canvas.

## AI Generation (fal.ai)
- Model: fal-ai/nano-banana-pro/edit
- Prompt: Replace the source character with Captain Snakeoil while keeping the exact in-game beat-em-up sprite framing, angle, scale, and left-facing standing pose from the source. Add a throne directly behind him, baked into the same sprite canvas, readable in the same 2D arcade style, with the sword visible and no goblet. Keep the throne simple and mirror-safe. No scenic deck background, no camera movement, no zoom, solid green background #00b140 outside the character and throne only, no extra characters.
- Negative Prompt: blurry, cropped, watermark, scenic background, deck background, close-up framing, wrong angle, wrong scale, realistic rendering, extreme perspective, extra limbs, duplicate weapons, missing throne, mutated throne, missing legs
- Seed(s): characters/enemies/tax_man/resources/sprites/seated/engage/engage_01.png
- Guidance/CFG: TBD
- Reference Images: outputs/reskin/captain_snakeoil/base/chosen.png; source_images/AIP_Captain_Snakeoil.jpg
- Variations: 4

## Consistency Checks
- [ ] Snakeoil stands facing left
- [ ] In-game engage sprite angle and scale are preserved
- [ ] Throne reads directly behind him and stays inside the 1034x710 canvas
- [ ] Sword reads clearly
- [ ] No scenic background or cropped throne pieces

## Notes
- Output must stay on the 1034x710 gameplay-style sprite canvas.
