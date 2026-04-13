# TASK: captain_snakeoil/intro/engage_master_start_add_sword

Status: TODO
Category: Character
Source: outputs/reskin/captain_snakeoil/intro/assets/engage_master_start_base.png
Target: outputs/reskin/captain_snakeoil/intro/assets/engage_master_start.png
Group/Set: intro/engage_master
Size(px): 1280x960

## Brief
- Keep the padded seated start frame exactly as-is, but add the same sword from the standing end frame leaning against the throne.
- Do not change the seated pose, throne design, framing, or headroom.

## AI Generation (fal.ai)
- Model: fal-ai/nano-banana-pro/edit
- Prompt: Keep the seated Captain Snakeoil start frame exactly the same: same seated pose, same throne, same goblet, same framing, same headroom, same scale, same 2D arcade style, same green background. Add only the same pirate cutlass from the standing reference image, leaning naturally against the throne so it is clearly visible and ready to be picked up. The sword must match the standing reference exactly in style, size, and design. No other changes.
- Negative Prompt: blurry, cropped, watermark, different throne, different pose, changed goblet, changed framing, changed scale, changed character anatomy, floating sword, giant sword, tiny sword, extra props, extra limbs, scenic background
- Seed(s): outputs/reskin/captain_snakeoil/intro/assets/engage_master_start_base.png
- Guidance/CFG: TBD
- Reference Images: outputs/reskin/captain_snakeoil/intro/assets/engage_master_end.png
- Variations: 4

## Consistency Checks
- [ ] Start frame remains otherwise unchanged
- [ ] Sword matches the standing end frame
- [ ] Sword leans against the throne, not floating in space
- [ ] Headroom and horizontal room remain intact

## Notes
- Output must stay on the 1280x960 video-source canvas.
