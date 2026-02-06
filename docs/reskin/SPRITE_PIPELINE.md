# Character Reskin Pipeline (Video → Frames → Game)

This is the **strict** pipeline for reskinning a character in this repo.

Key rules:
- This is a **one-off** pipeline for this game. No fallbacks or backwards compatibility.
- Missing files are hard errors — fix the source of truth instead of auto-guessing.
- All working state goes under `outputs/reskin/<character>/...` (gitignored).

---

## Files You Edit

- Config: `docs/reskin/<character>_animations.toml`
  - `global.base_task` points to the idle task used to generate the first still.
  - `global.anchor_image` / `global.anchor_framed` are the canonical anchor outputs.
  - `global.frames_dir` / `global.video_dir` / `global.padded_dir` define per-character working dirs.
  - `global.active` is required; it defines which animation names run.
  - Each `[[animation]]` must set:
    - `name`
    - `prompt_variations` (preferred) or `prompt`
    - `duration`
    - `frame_indices` (1-based contact-sheet labels)
    - `dest_dir`, `prefix`, `match`
    - `output_start` (unless `single_frame = true`)

---

## Recommended: Run The Interactive Wizard

This is the intended entrypoint:
```bash
python3 scripts/reskin_interactive.py
```

It guides you through:
1) generate 4 base idle options
2) choose 1 + build the anchor (solid greenscreen + 2px white border)
3) choose animations (`global.active`)
4) generate video variants
5) pick winners (`chosen.mp4`)
6) extract frames + contact sheets
7) apply sprites into the game

---

## Manual Commands (If You Prefer)

### 1) Generate videos
```bash
python3 scripts/nova_batch.py --config docs/reskin/<character>_animations.toml --make-videos
```

Videos are written to:
```
outputs/reskin/<character>/videos/<anim>/<run_id>/*.mp4
```

After reviewing, copy your winner to:
```
outputs/reskin/<character>/videos/<anim>/chosen.mp4
```

### 2) Extract frames + contact sheets
```bash
python3 scripts/nova_batch.py --config docs/reskin/<character>_animations.toml --make-frames
```

Outputs:
```
outputs/reskin/<character>/frames/<anim>/raw/frame_###.png
outputs/reskin/<character>/frames/<anim>/contact.png
```

Frame indices are **1-based** labels from the contact sheet (001 is top-left).

### 3) Apply sprites (BG remove selected + write into game folders)
```bash
python3 scripts/nova_batch.py --config docs/reskin/<character>_animations.toml --apply-sprites
```

This will:
- BG-remove **only selected frames** into:
  ```
  outputs/reskin/<character>/frames/<anim>/final/
  ```
- Write numbered sprite PNGs into `dest_dir` and prune stale numbered leftovers for the same prefix.

---

## Prompt Workarounds (Keeping Motion In-Frame)

We rely on specific phrasing to keep the character **centered** and avoid translation:
- Walk: include “treadmill walk in place” / “no translation”
- Turn: “pivot/turn in place” / “no translation”
- Jump/uppercut/air: “levitate/jump in place without translating within the frame”
- Knockout: “collapse/fall in place, keep centered; no dust/debris”

The anchor includes a 2px white border and the prompt should explicitly say not to cross it.

---

## Re-Run Rules

- Changed prompts → `--make-videos` → pick winners → `--make-frames` → update `frame_indices` → `--apply-sprites`
- Changed only `frame_indices` → `--apply-sprites`
- Changed only `scale_multiplier` → `--apply-sprites` (BG removal is cached; it should not re-run)
