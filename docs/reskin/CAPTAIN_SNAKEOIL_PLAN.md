# Captain Snakeoil Reskin Plan (Tax Man Base, final shape-aware)

## Goal
Replace Tax Man body sprites with Captain Snakeoil while preserving existing gameplay wiring, hitboxes, and state-machine behavior.

## Critical constraint
Do not design motion as "camera tracks character across frame". For Tax Man, movement-heavy states (especially dash) are driven by gameplay movement + hitbox tracks, not by translating the whole body sprite from one edge of the canvas to the other.

## Shape inventory (current game targets)

- Core idle canvas: `541x668` (`idle_00`)
- Walk canvas: `469x612` (`walk_00`)
- Turn canvas: variable files (`413x571` to `468x586`) but output target is turn folder/prefix.
- Hurt canvases: `544x632`
- Retaliate (`attack_retaliate`): `795x625`
- Combo (`attack_combo`): `1258x636`
- Dash (`attack_dash_begin` + `attack_dash_end`): `2558x1008`
- Area body (`attack_area_body`): `844x985`
- Death body (`death_explosion_body`): `864x968`
- Seated:
  - engage target `764x710` (some legacy files include wider variants)
  - laugh/drink/swirl target `764x710`

## Section-by-section plan

### 1) Base locomotion block (idle/walk/turn/hurt)

- Actions: `idle`, `walk`, `turn`, `hurt_light`, `hurt_medium`, `hurt_knockout`
- Objective: stable anatomy and readable silhouette with minimal cinematic effects.
- Motion rule:
  - idle/walk: in-place loop language (`treadmill` for walk).
  - turn: pivot in place, not a translation.
  - hurt_*: impact poses only, centered.
- Canvas rule: use each action `match` as authoritative size.
- Picking rule: prioritize consistency over drama.

### 2) Sword attack block

- Actions: `attack_retaliate`, `attack_combo`
- Objective: clear sword-readability frames that fit existing attack timings.
- Motion rule:
  - retaliate: short, single retaliation beat.
  - combo: 15 distinct beats with anticipation, contact, recovery.
- Canvas rule:
  - `attack_retaliate` uses `795x625`.
  - `attack_combo` uses `1258x636`.
- Picking rule: ensure enough distinct pose beats to satisfy frame counts.

### 3) Dash block (most sensitive)

- Actions: `attack_dash_begin`, `attack_dash_end`
- Objective: preserve existing dash feel without breaking hitbox/travel timing.
- Motion rule:
  - Do **not** animate full-frame left->right traversal.
  - `attack_dash_begin`: startup/launch body language.
  - `attack_dash_end`: strike/recovery body language.
- Canvas rule:
  - both use wide `2558x1008` targets.
  - body framing must remain compatible with existing dash hitbox tracks.
- Picking rule:
  - review begin/end separately and as combined sequence in preview (`3`, `5`, `6`).

### 4) Area attack block (composite)

- Action: `attack_area_body`
- Objective: body choreography for sword-powered lightning attack.
- Motion rule: body drives the ritual; keep action readable and contained.
- Canvas rule: `844x985`.
- Important: this is body-only. Final in-game look includes layered VFX (lightning/smoke/explosion sprite sets).
- Picking rule: choose body poses that sync well with layered VFX timing.

### 5) Death block (composite)

- Action: `death_explosion_body`
- Objective: wail-and-crumble body sequence (no self-explosion body pose language).
- Canvas rule: `864x968`.
- Important: body-only; existing explosion/smoke/lightning layers still play.
- Picking rule: body readability first; VFX layers provide spectacle.

### 6) Seated behavior block (linked)

- Actions: `seated_engage`, `seated_laugh`, `seated_drink`, `seated_swirl`
- Objective: consistent seated character performance set.
- Grouping rule: always generate/pick as one set (`seated_block` consistency group).
- Canvas rule: seated targets (`764x710` family).
- Direct-replacement rule: do not use the video pipeline for the seated drink/throw set. Generate exact target files as still-image tasks because the engage throw uses mixed widths and auxiliary prop sprites.
- Required direct-replacement files for the drink/throw sequence:
  - `wine_swirl_00.png`, `wine_swirl_01.png` at `764x710`
  - `wine_drink_00.png`, `wine_drink_01.png` at `764x710`
  - `engage_00.png` at `764x710`
  - `engage_01.png`, `engage_02.png`, `flying_glass.png` at `1034x710`
  - `glass_shards_00.png`, `glass_shards_02.png` at `245x224`
- Task source of truth: `docs/reskin/tasks/characters/enemies/captain_snakeoil/seated/...`
- Picking rule: all four should look like one contiguous performance capture.

## Pipeline decisions

1. Keep action names aligned with gameplay names in TOML:
   - `attack_retaliate`, `attack_combo`, `attack_dash_begin`, `attack_dash_end`, `attack_area_body`, `death_explosion_body`.
2. Use per-action `match` dimensions as canonical frame guides.
3. Generate videos by section, not all at once:
   - locomotion -> sword -> dash -> area -> death -> seated.
4. Use preview scene keys to validate before frame picking:
   - `1/2/3/4/5/6`, `E/L/R/S`, etc.
5. Only after preview validation: choose `frame_indices`, then apply sprites.

## Non-negotiables

- No fallback logic.
- Missing files are hard errors.
- Keep existing Tax Man auxiliary VFX layers untouched in this pass.
