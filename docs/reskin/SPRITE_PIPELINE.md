# Character Sprite Pipeline (AI Video → Frames → Game)

This is the **repeatable, strict** pipeline for reskinning a character. It assumes **no fallbacks**: missing files or mismatched inputs are errors you must fix.

---

## 0) Files You Will Edit

### Config
- `docs/reskin/nova_animations.toml`

Global fields you should understand:
- `global.anchor_image`: base still used to seed videos.
- `global.scale_ref`: **single frame** (greenscreen or transparent) used to compute the **global scale factor** for all poses.
- `global.scale_multiplier`: tweak knob (e.g. `1.05` to slightly enlarge).
- `global.frames_dir`: defaults to `outputs/fal/frames`.
- `global.constraints`: appended to each prompt (baseline, no zoom, etc).
- `global.extract_fps`: frame extraction rate for contact sheets.

Per‑animation fields you should edit:
- `enabled`: only run the ones you need.
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

---

## 1) Generate Videos (AI)

Model used: `fal-ai/kling-video/o1/image-to-video`

Command:
```
python3 scripts/nova_batch.py --make-videos
```

Notes:
- The script auto‑builds padded seed images when `pad_*` fields are set.
- Prompts always append `global.constraints`.

---

## 2) Extract Frames + Contact Sheets

Command:
```
python3 scripts/nova_batch.py --make-frames
```

Outputs:
- `outputs/fal/frames/<anim>_raw/` → raw PNG frames
- `outputs/fal/frames/<anim>_contact.png` → contact sheet

**Frame indices are 1‑based labels** from the contact sheet (top‑left is `001`).

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
1. Copies the chosen raw frames into `outputs/fal/frames/<anim>_selected`.
2. Background‑removes **only those frames** into `<anim>_selected_bg`.
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
- If `dest_dir` is `characters/playable/chad/...`, the script automatically uses the matching **Mark** sprite as the reference.
- Otherwise, set `match = "path/to/reference.png"` per animation in the TOML.

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
