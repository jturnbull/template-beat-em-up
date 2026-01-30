# Character Sprite Pipeline (AI Video → Frames → Game)

This is the **repeatable, strict** pipeline for reskinning a character. It assumes **no fallbacks**: missing files or mismatched inputs are errors you must fix.

---

## 0) Files You Will Edit

### Config
- `docs/reskin/<character>_animations.toml`

Global fields you should understand:
- `global.anchor_image`: base still used to seed videos.
- `global.scale_ref`: **single frame** (greenscreen or transparent) used to compute the **global scale factor** for all poses.
- `global.scale_multiplier`: tweak knob (e.g. `1.05` to slightly enlarge).
- `global.frames_dir`: defaults to `outputs/fal/frames`.
- `global.video_dir`: per‑character video folder (recommended), defaults to `outputs/fal/video`.
- `global.padded_dir`: per‑character padded image folder (recommended), defaults to `outputs/fal/padded`.
- `global.constraints`: appended to each prompt (baseline, no zoom, etc).
- `global.extract_fps`: frame extraction rate for contact sheets.
- `global.extract_start` / `global.extract_end` / `global.extract_duration`: optional time window (seconds or `MM:SS`) for frame extraction.
- `global.frame_guide`: enable fixed canvas + border constraint for video.
- `global.frame_guide_color`: border color (use `#ffffff`).
- `global.frame_guide_thickness`: border thickness in px (use `2`).
- `global.frame_guide_match`: sprite whose **size + baseline** define the frame (use the **current character’s idle**).
- `global.active`: optional list to limit which animations run (e.g. `["walk", "punch1"]`).
- `prompt_variations` (per animation): list of full prompt strings. If present, multiple video jobs are submitted at once.

Per‑animation fields you should edit:
- `prompt`: action description.
- `duration`: video length for the model (3/4/5 seconds for kling).
- `frame_count`: guidance only (not used for selection).
- `frame_indices`: **contact‑sheet labels** (1‑based), e.g. `2,4-6,8`.
- `prefix`: output sprite prefix.
- `output_start`: first output frame index for filenames.
- `dest_dir`: output sprite folder.
- `pad_*`: optional per‑animation padding for video seed.
- `end_image`: `same` / `flip` / `none`.
- `single_frame`: for hurt/one‑shot poses.
- `match`: reference sprite for **all** outputs. For consistent size, set this to the same idle sprite for every action.

---

## 0.5) Preparing the Anchor (Start) Image

Use **`scripts/fal_reskin_generate.py`** to generate the base idle still. Source images
(e.g., `source_images/Sentries.png`) should be passed as references.

Steps:
1. **Generate candidates** with `fal_reskin_generate.py` using the source sheet as reference.
2. **Pick a single character** (no extra characters/props).
3. **Ensure greenscreen** (`#00b140`) behind the character.
4. **Match the frame** to the target sprite size and baseline:
   - Use the **current character’s idle sprite** as the reference size/baseline.
   - Center the character horizontally.
   - Align the feet to the same baseline (bottom padding should match Mark).
5. **Add the frame guide**:
   - 2px white border on all edges.
   - The character should not touch or cross the border.
6. Run `scripts/prepare_anchor_image.py` to size + baseline the anchor:
   ```
   python3 scripts/prepare_anchor_image.py
   ```
   Defaults:
   - input: `outputs/fal/idle_00/option_1.png`
   - match: `<character idle sprite>`
   - outputs: `outputs/fal/idle_00/<character>_anchor_base.png` + `<character>_anchor_framed.png`
   - bg: `#00b140`, border: white 2px
   - note: the script uses **fal-ai/bria/background/remove** to key the anchor
     before compositing onto solid green. Requires `FAL_KEY`.
7. Set `global.anchor_image` to your `<character>_anchor_base.png` and
   `global.scale_ref` to the same file.

This anchor is the **source of truth** for scale and framing across all animations.

---

## 1) Generate Videos (AI)

Model used: `fal-ai/kling-video/o1/image-to-video`

Command:
```
python3 scripts/nova_batch.py --make-videos
```

Notes:
- The script auto‑builds padded seed images when `pad_*` fields are set.
- If `global.frame_guide = true`, the seed image is framed to the **Mark sprite size**
  with a **2px white border**. This is the hard constraint for the video model.
- Prompts always append `global.constraints`.

---

## 2) Extract Frames + Contact Sheets

Command:
```
python3 scripts/nova_batch.py --make-frames
```

Outputs:
- `outputs/fal/frames/<character>/<anim>_raw/` → raw PNG frames
- `outputs/fal/frames/<character>/<anim>_contact.png` → contact sheet

**Frame indices are 1‑based labels** from the contact sheet (top‑left is `001`).

If frame‑guide is enabled, the **border is auto‑removed** from raw frames right after extraction.

Examples:
- `2,4-6,8` → 5 frames
- `4,8,11,15` → 4 frames

---

## 3) Choose Frames

Edit `frame_indices` for each animation in `docs/reskin/nova_animations.toml`.

Do **not** rename or edit files inside `*_raw` or `*_selected`. The pipeline relies on their names.

---

## 4) Apply Sprites (BG Remove + Scale + Place)

Command:
```
python3 scripts/nova_batch.py --apply-sprites
```

This step does all of the following:
1. Copies the chosen raw frames into `outputs/fal/frames/<character>/<anim>_selected`.
2. Background‑removes **only those frames** into `outputs/fal/frames/<character>/final/<anim>/`.
3. Scales, crops, and places into the final sprite folder.

No backups are created in the character folders.

---

## 5) Scaling & Baseline Rules (Critical)

This is how we keep every pose consistent:

### Global scale factor (single number for all frames)
Computed once per run:
```
scale_factor = (match_visible_height / scale_ref_visible_height) * global.scale_multiplier
```

Where:
- **match_visible_height** = visible height of the **reference sprite** in the old character.
- **scale_ref_visible_height** = visible height of your **chosen `global.scale_ref`** frame.

### Match sprite (baseline + canvas)
The output canvas size and baseline padding are taken from the **reference sprite**.

Rules:
- **Always** set `match` per animation (no fallbacks).
- For consistent size, point **every** `match` at the **same idle sprite** for that character.

### Placement
Each output frame is:
- center‑aligned horizontally
- bottom‑aligned to the **reference baseline**

This is what prevents “floating” or “sinking” in‑game.

---

## 6) When to Re‑Run What

**Changed prompts or padding:**  
→ `--make-videos`, then `--make-frames`, then re‑pick indices.

**Changed only `frame_indices`:**  
→ `--apply-sprites` only.

**Changed only scale/placement:**  
→ `--apply-sprites` only.

**Only want a subset of animations:**  
→ set `global.active` in the TOML and run as normal.

**Want higher/lower sampling or a specific time slice:**  
→ set per‑animation `extract_fps`, `extract_start`, `extract_end` (or `extract_duration`).

**Avoid clobbering another character’s frames:**  
→ set `global.frames_dir = "outputs/fal/frames/<character>"`.

**Using multiple prompt variations (prompt_variations):**  
Pick the best video and ensure it lives in `global.video_dir` as `<animation>_framed*.mp4`.  
If there are multiple matches, the newest file by modified time is used.

**Final selected frames location:**  
BG‑removed selected frames are written to `outputs/fal/frames/<character>/final/<animation>/`.

**Frame guide note:**  
Extracted frames are resized to the `frame_guide_match` sprite size before the border is removed. This normalizes resolution so scaling doesn’t explode (no “just feet” crops).

**Frame guide + apply step:**  
When `frame_guide` is enabled, sprite application uses the full frame canvas (`--use-canvas`). This preserves consistent scale across actions instead of re‑scaling per frame.

**Uniform canvas per character:**  
Point every animation’s `match` at the same reference sprite (usually the idle frame). This forces all outputs to the same canvas size, preventing walk/punch frames from “growing” due to legacy sprite sizes.

**Normalize animation offsets (once per character):**  
Legacy animation `.tres` files often compensate for off‑center art by shifting `AnimatedSprite2D:position`.  
When using centered, consistent sprites, zero out X offsets and normalize Y for ground actions:
- **Set X = 0** for idle/walk/turn/attacks/hurt (and other non‑special ground actions).
- **Set Y = idle baseline** for idle/walk/turn/attacks/hurt.
- **Keep X/Y offsets** for jump/air/knockout/die/getting_up where motion is intentional.

---

## 7) Troubleshooting

**“Frame label not found”**  
Your `frame_indices` do not exist in the raw frames. Check the contact sheet and indices.

**Character looks tiny/huge**  
Update `global.scale_ref` to a better representative frame and/or tweak `global.scale_multiplier`.

**Baseline is off**  
Your match reference is wrong. Ensure the match sprite exists and reflects the old baseline.

**Frames cropped**  
The character exceeded the reference canvas. Regenerate the pose or plan a larger canvas for that move.

---

## 8) Next Character Checklist

1. Generate base idle → pick best still.
2. Update `global.anchor_image`.
3. Generate idle video → pick frame → set `global.scale_ref`.
4. Run videos for all moves.
5. Use contact sheets to set `frame_indices`.
6. Apply sprites, test in game.
7. Tweak scale or re‑generate poses that crop or feel inconsistent.
