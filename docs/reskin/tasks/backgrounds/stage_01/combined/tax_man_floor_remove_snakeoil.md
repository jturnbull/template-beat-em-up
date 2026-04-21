# TASK: tax_man_floor_remove_snakeoil

Status: TODO
Category: Background
Source: stages/stage_01/stage_elements/tax_man_area/tax_man_black_marble.png
Target: outputs/reskin/stage_01/tax_man_floor_remove_snakeoil/tax_man_black_marble.png
Size(px): 6581x794
Group/Set: stage_01/combined

## Brief
- Rebuild the floor-only asset from the approved floor-with-Snakeoil concept.
- Remove Captain Snakeoil completely and reconstruct the deck cleanly where he was standing.
- Preserve the exact source floor silhouette for drop-in use.

## AI Generation (fal.ai)
- Model: fal-ai/nano-banana/edit
- Prompt: Rebuild this floor as the same ship deck shown in the reference concept, but with no character present at all. Preserve the exact canvas size, floor silhouette, perspective, lighting direction, and gameplay readability from the source asset. Match the reference deck material language, board spacing, reinforcement bands, seams, and wear pattern, and reconstruct the floor cleanly underneath where the character had been standing. Output only the floor.
- Negative Prompt: character, person, pirate, skeleton, shadow of a character, marble, checkerboard, giant planks, oversized panels, blurry, low-res, cropped, extreme perspective changes, photorealistic, 3D render
- Seed(s): TBD
- Guidance/CFG: TBD
- Reference Images: TBD
- Variations: 4 options (`option_1.png`..`option_4.png`)

## Consistency Checks
- [ ] Size matches reference (6581x794)
- [ ] Transparency silhouette preserved exactly where source has alpha (use `--alpha-from-source`)
- [ ] Character removed completely
- [ ] Deck treatment matches approved concept
- [ ] In-game readability OK
