# TASK: captain_snakeoil/seated/wine_drink/wine_drink_01

Status: TODO
Category: Character
Source: characters/enemies/tax_man/resources/sprites/seated/wine_drink/wine_drink_01.png
Target: characters/enemies/tax_man/resources/sprites/seated/wine_drink/wine_drink_01.png
Size(px): 764x710
Group/Set: seated/wine_drink

## Brief
- Captain Snakeoil completes the drink beat, ready to snap into the throw/engage sequence.
- Replace Tax Man seated sprite content with Captain Snakeoil while preserving exact canvas size and drop-in gameplay wiring.

## AI Generation (fal.ai)
- Model: fal-ai/nano-banana-pro/edit
- Prompt: Captain Snakeoil seated on the command throne of his space galleon deck, side-view 2D sprite, finishing a sip of red wine from the goblet and drawing it away ready to throw, same seated scale and framing, fully inside frame, solid green background #00b140.
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
