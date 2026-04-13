# TASK: captain_snakeoil/intro/seated_master_start

Status: TODO
Category: Character
Source: source_images/AIP_Captain_Snakeoil.jpg
Target: outputs/reskin/captain_snakeoil/intro/assets/seated_master_start.png
Group/Set: intro/seated_master

## Brief
- Captain Snakeoil already seated on the command throne of his space galleon before the reveal begins.
- This is the first visible pose for the seated boss intro, so it must read cleanly and stay stable for the video model.

## AI Generation (fal.ai)
- Model: fal-ai/nano-banana-pro/edit
- Prompt: Captain Snakeoil already seated on the command throne of his space galleon, goblet in hand, sword parked by the throne, smug villainous pose, clean 2D cartoon boss illustration, throne fully visible and baked into frame, locked camera, no motion blur, centered composition, mirror-safe throne design, solid green background #00b140 outside the throne/deck set, no extra characters.
- Negative Prompt: blurry, cropped, watermark, extra limbs, multiple characters, missing goblet, missing sword, mutated throne, drifting props, camera tilt, zoomed-in framing
- Seed(s): source_images/AIP_Captain_Snakeoil.jpg
- Guidance/CFG: TBD
- Reference Images: outputs/reskin/captain_snakeoil/base/chosen.png
- Variations: 4

## Consistency Checks
- [ ] Snakeoil is already seated
- [ ] Throne reads clearly and consistently
- [ ] Goblet and sword are both visible
- [ ] Wide composition leaves room for seated animation
- [ ] Camera is locked and usable for video start frame

## Notes
- Output should be landscape for the intro video source.
