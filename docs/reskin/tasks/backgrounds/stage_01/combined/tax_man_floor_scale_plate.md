# TASK: tax_man_floor_scale_plate

Status: TODO
Category: Background
Source: tmp/flattened/tax_man_floor_scale_plate.png
Target: outputs/reskin/stage_01/tax_man_floor_scale_plate/tax_man_floor_scale_plate.png
Size(px): 6581x794
Group/Set: stage_01/combined

## Brief
- Redesign the boss-room floor as a more convincing ship deck while keeping Captain Snakeoil standing on it at the same gameplay scale.
- The character is a temporary scale anchor only.
- Preserve the exact floor footprint and perspective flow from the source plate.

## AI Generation (fal.ai)
- Model: fal-ai/nano-banana/edit
- Prompt: Redesign this boss-room floor into a readable ship deck for a pirate spaceship command room while keeping Captain Snakeoil standing in exactly the same place and at exactly the same scale. Preserve the long floor footprint, perspective, lighting direction, and gameplay readability. The deck surface should read clearly at game camera distance: narrower plank rhythm, finer board detail, subtle seams, fasteners, metal reinforcement bands, and durable high-traffic wear. Do not change the character pose, character proportions, or the floor silhouette. Treat the character as a scale reference and redesign the floor under and around him so the board size feels believable for that character scale.
- Negative Prompt: marble, checkerboard, giant planks, oversized panels, carpet, blurry, low-res, cropped, extreme perspective changes, extra characters, changed pose, changed scale, photorealistic, 3D render
- Seed(s): TBD
- Guidance/CFG: TBD
- Reference Images: stages/stage_01/stage_elements/tax_man_area/tax_man_black_marble.png; outputs/reskin/captain_snakeoil/frames/idle/final/frame_010.png
- Variations: 4 options (`option_1.png`..`option_4.png`)

## Consistency Checks
- [ ] Size matches reference (6581x794)
- [ ] Character scale and placement preserved
- [ ] Floor perspective and footprint preserved
- [ ] Board/plating size reads correctly under the character
- [ ] In-game readability OK

## Notes
- The character is not part of the final asset. This pass is only to lock floor detail scale.
