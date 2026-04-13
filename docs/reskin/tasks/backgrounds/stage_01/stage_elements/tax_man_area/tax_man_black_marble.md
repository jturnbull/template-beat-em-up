# TASK: tax_man_black_marble

Status: TODO
Category: Background
Source: stages/stage_01/stage_elements/tax_man_area/tax_man_black_marble.png
Target: stages/stage_01/stage_elements/tax_man_area/tax_man_black_marble.png
Size(px): 6581x794
Group/Set: stage_01/stage_elements/tax_man_area

## Brief
- Convert this floor base into a **ship's deck** for the pirate-space boss area.
- Preserve the exact canvas size, perspective flow, and gameplay readability.
- Keep it consistent with the boss-room art bible.

## AI Generation (fal.ai)
- Model: fal-ai/nano-banana/edit
- Prompt: Convert this long floor texture from black marble into a readable ship's deck for a pirate galleon in space. Keep the exact same canvas size, horizon/perspective flow, lighting direction, and broad value structure so it still supports the existing stage layout. Replace polished stone with deck planks or deck plating that still reads as a command deck: worn wood boards, metal tie-bands, embedded fasteners, subtle seams, and durable high-traffic wear. The result should feel like a villain ship interior floor, readable under characters, and not overly busy.
- Negative Prompt: marble, checkerboard, carpet, blurry, low-res, cropped, extreme perspective changes, overly dense texture noise, photorealistic, 3D render, wet reflections that hurt gameplay readability
- Seed(s): TBD
- Guidance/CFG: TBD
- Reference Images: stages/stage_01/stage_elements/tax_man_area/tax_man_black_marble.png
- Variations: 4 options (`option_1.png`..`option_4.png`)

## Consistency Checks
- [ ] Size matches reference (6581x794)
- [ ] Transparency silhouette preserved exactly where source has alpha (use `--alpha-from-source`)
- [ ] Ground/contact point aligned
- [ ] Silhouette matches base
- [ ] Palette/lighting matches art bible
- [ ] In‑game readability OK
- [ ] Pose matches original intent

## Review
- [ ] Option A
- [ ] Option B
- [ ] Option C
- [ ] Option D

## Notes
- Prioritize a strong deck read over decorative detail. This floor needs to stay clear under combat.
