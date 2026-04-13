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
- `attack_area_body` -> `1` -> `Ground/AttackArea` -> `33` body frames -> mapped non-contiguous `area_attack0000..0061`
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
- Prompt target: sword raised straight up, pulling electricity down from above into the blade.
- `death_explosion_body` is **body-only generation**. Gameplay also layers:
  - `Lightining/back_lightning_explosion` (`26`)
  - `FrontLightining/front_lightining_explostion` (`5`)
  - `GroundLightining/explosion` (`8`)
  - `SmokeVertical/vertical_grenade` (`13`)
  - `SmokeHorizontal/horizontal` (`17`)
  - `Explosion/grenade` (`26`)
- Prompt target: crumble onto the deck as a pile of bones.
- Follow-up cleanup required after body generation: strip the old grenade / explosion / coin payoff from the death animation resources, otherwise the move still reads like Tax Man.

## How to pick winning videos so frame extraction works

- Keep motion readable in one clean phase per action:
  - `attack_retaliate`: short retaliate beat; avoid extra follow-up.
  - `attack_combo`: full multi-hit arc with clear start and settle.
  - `hurt_*`: one chest-hit recoil frame per action; do not try to turn these into mini animations.
  - `attack_area_body`: dramatic skyward sword-point, electrical summon, release.
  - `death_explosion_body`: stagger, collapse, bone pile; no bomb toss or self-destruct acting.
- Pick clips where the number of distinct readable poses is at least `frame_count` for that action.
- For grouped actions, pick all together with matching style:
  - `seated_block`: `seated_engage`, `seated_laugh`, `seated_drink`, `seated_swirl`
- For body-only composite actions:
  - `attack_area_body`: prioritize body silhouette readability and timing; the existing VFX layers supply the strike spectacle.
  - `death_explosion_body`: prioritize readable collapse-to-bones staging; after frame selection, remove the old Tax Man death VFX layers that no longer fit Snakeoil.

## Disabled move

- Rush / dash attack is disabled for Snakeoil in gameplay AI. Do not spend more generation time on `attack_dash_begin` or `attack_dash_end`.
