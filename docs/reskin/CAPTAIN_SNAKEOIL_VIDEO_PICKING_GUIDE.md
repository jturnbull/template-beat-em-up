# Captain Snakeoil Video Picking Guide

Use this to map TOML actions to what you test in `res://debug_tools/test_scenes/tax_man/tax_man_animation_preview.tscn`.

## Quick Mapping (TOML -> playground -> game)

- `idle` -> `I` -> `Ground/Move/IdleAi` -> `8` frames -> `idle_00..07`
- `walk` -> `W` -> `Ground/Move/Follow` -> `16` frames -> `walk_00..15`
- `turn` -> (inside follow/turn flow) -> `Ground/Move/Follow` -> `3` frames -> `turnaround_00..02`
- `hurt_light` -> `H` (damage-driven) -> `Ground/Hurt` -> `1` frame -> `injury_small`
- `hurt_medium` -> `H` (damage-driven) -> `Ground/Hurt` -> `1` frame -> `injury_medium`
- `hurt_knockout` -> `H` (damage-driven) -> `Ground/Hurt` -> `1` frame -> `injury_knockout_impact`
- `attack_retaliate` -> `4` -> `Ground/AttackRetaliate` -> `4` frames -> `slap_2_01,02,04,05`
- `attack_combo` -> `2` -> `Ground/AttackCombo` -> `15` frames -> `attack_00..14`
- `attack_dash_begin` -> `5` (state), or `3` combined -> `Ground/AttackDash` -> `7` frames -> `dash_00,01,02,04,06,08,09`
- `attack_dash_end` -> `6` (state), or `3` combined -> `Ground/AttackDash` -> `8` frames -> `dash_10,11,13,14,15,16,17,18`
- `attack_area_body` -> `1` -> `Ground/AttackArea` -> `34` body frames -> mapped non-contiguous `area_attack0000..0076`
- `death_explosion_body` -> `D` -> `DieAi` -> `15` body frames -> mapped non-contiguous `grenade_finisher0000..0063`
- `seated_engage` -> `E` (state) -> `Seated` -> `3` frames -> `engage_00..02`
- `seated_laugh` -> `L` (state) -> `Seated` -> `4` frames -> `laughter_00..03`
- `seated_drink` -> `R` (state) -> `Seated` -> `2` frames -> `wine_drink_00..01`
- `seated_swirl` -> `S` (state) -> `Seated` -> `2` frames -> `wine_swirl_00..01`

## Composite Actions (important)

- `attack_area_body` is **body-only generation**. Gameplay also layers:
  - `Lightining/back_lightning` (`16`), `Lightining/back_lightning_explosion` (`26`)
  - `FrontLightining/front_lightining` (`5`)
  - `GroundLightining/area_attak` (`4`)
  - `Smoke/vertical_area_attack` (`13`)
  - `Explosion/area_attack` (`26`)
- `death_explosion_body` is **body-only generation**. Gameplay also layers:
  - `Lightining/back_lightning_explosion` (`26`)
  - `FrontLightining/front_lightining_explostion` (`5`)
  - `GroundLightining/explosion` (`8`)
  - `SmokeVertical/vertical_grenade` (`13`)
  - `SmokeHorizontal/horizontal` (`17`)
  - `Explosion/grenade` (`26`)

## How to pick winning videos so frame extraction works

- Keep motion readable in one clean phase per action:
  - `attack_dash_begin`: startup/launch only.
  - `attack_dash_end`: strike/recovery only.
  - `attack_retaliate`: short retaliate beat; avoid extra follow-up.
  - `attack_combo`: full multi-hit arc with clear start and settle.
- Pick clips where the number of distinct readable poses is at least `frame_count` for that action.
- For grouped actions, pick all together with matching style:
  - `seated_block`: `seated_engage`, `seated_laugh`, `seated_drink`, `seated_swirl`
  - `dash_block`: `attack_dash_begin`, `attack_dash_end`
- For body-only composite actions (`attack_area_body`, `death_explosion_body`), prioritize body silhouette readability and timing; existing VFX layers supply the rest.
