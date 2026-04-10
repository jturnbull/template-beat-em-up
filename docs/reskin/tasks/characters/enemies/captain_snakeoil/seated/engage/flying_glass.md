# TASK: captain_snakeoil/seated/engage/flying_glass

Status: TODO
Category: Character
Source: characters/enemies/tax_man/resources/sprites/seated/engage/flying_glass.png
Target: characters/enemies/tax_man/resources/sprites/seated/engage/flying_glass.png
Size(px): 1034x710
Group/Set: seated/engage

## Brief
- Replacement projectile for the thrown wine glass.
- Replace Tax Man seated sprite content with Captain Snakeoil while preserving exact canvas size and drop-in gameplay wiring.

## AI Generation (fal.ai)
- Model: fal-ai/nano-banana-pro/edit
- Prompt: A thrown crystal wine goblet flying fast across a wide side-view frame, red wine spilling from the glass, strong motion read, no character visible, clean silhouette, fully inside frame, solid green background #00b140.
- Negative Prompt: blurry, cropped, background, watermark, extra limbs, multiple characters
- Seed(s): existing Tax Man sprite at Source path
- Guidance/CFG: TBD
- Reference Images: source_images/AIP_Captain_Snakeoil.jpg
- Variations: 4

## Consistency Checks
- [ ] Exact canvas size matches target
- [ ] Seated baseline and throne relationship are preserved
- [ ] Silhouette reads clearly in game
- [ ] Wine/glass action is readable
- [ ] Style matches chosen Captain Snakeoil look
- [ ] Drops in without animation rewiring

## Review
- [ ] Option A
- [ ] Option B
- [ ] Option C

## Notes
- Add `outputs/reskin/captain_snakeoil/anchor/anchor_base.png` as an extra ref when running generation if available.
