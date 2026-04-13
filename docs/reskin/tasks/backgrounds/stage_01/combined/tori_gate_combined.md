# TASK: tori_gate_combined (combined)

Status: TODO
Category: Background
Source: tmp/flattened/tori_gate_blockout.png
Target: tmp/flattened/tori_gate_blockout.png
Size(px): 1600x1800
Group/Set: stage_01/combined

## Brief
- Convert the gate into a **spaceport security scanner arch** as one combined isometric gameplay prop.
- Preserve the exact canvas size and the broad in-game footprint, but do **not** preserve the old torii silhouette literally.
- Keep the material language consistent with the nearby spaceport storefront / CAMINO signage treatment.

## AI Generation (fal.ai)
- Model: fal-ai/nano-banana/edit
- Prompt: Isometric arcade game prop redesign: turn this rough blockout into a retro-futuristic spaceport checkpoint gate for the dock approach. Keep the same 1600x1800 canvas, the open passage through the center, the broad wide-arch footprint, and the isometric game-prop read. Redesign it as one coherent industrial security gate with heavy metal uprights, scanner heads, signal lights, checkpoint hardware, cables, docking tech, and worn spaceport materials. It must read clearly as a port gate or checkpoint, not a shrine or torii. Include only subtle readable signage if it helps the checkpoint read. No scenic background, no full-frame opaque fill, and do not turn it into a concept-art poster; this should look like a single gameplay prop on a flat keyed background.
- Negative Prompt: shrine, torii, temple, Japanese gate, feudal gate, fantasy gate, scenic background, skybox, environment painting, full-frame opaque background, blurry, low-res, cropped, detached floating parts, photorealistic, 3D render, poster composition, unreadable silhouette
- Seed(s): TBD
- Guidance/CFG: TBD
- Reference Images: tmp/flattened/tori_gate_blockout.png; stages/stage_01/caminoshop.png
- Variations: 4 options (`option_1.png`..`option_4.png`)

## Consistency Checks
- [ ] Size matches reference (1600x1800)
- [ ] Overall footprint remains compatible with the scene placement
- [ ] Gate reads as one coherent isometric gameplay prop
- [ ] Palette/lighting matches art bible
- [ ] In-game readability OK

## Review
- [ ] Option A
- [ ] Option B
- [ ] Option C
- [ ] Option D

## Notes
- Build the blockout source with `python3 scripts/tori_gate_combined.py blockout`
- Do not slice generated options until a combined concept is good enough to fit back into the scene.
