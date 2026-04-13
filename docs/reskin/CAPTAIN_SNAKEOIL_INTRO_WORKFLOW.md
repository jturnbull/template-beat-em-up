# Captain Snakeoil Throne Intro Workflow

This is separate from the normal combat reskin pipeline.

## Source of truth

- Config: `docs/reskin/captain_snakeoil_intro.toml`
- Runner: `scripts/captain_snakeoil_intro.py`

The config must contain exactly two clips:
- `seated_master`
- `engage_master`

## Required assets

Before running a clip, create its start and end stills at the exact paths referenced in the config.

For `seated_master`:
- `outputs/reskin/captain_snakeoil/intro/assets/seated_master_start.png`
- `outputs/reskin/captain_snakeoil/intro/assets/seated_master_end.png`

For `engage_master`:
- `outputs/reskin/captain_snakeoil/intro/assets/engage_master_start.png`
- `outputs/reskin/captain_snakeoil/intro/assets/engage_master_end.png`

Missing images are a hard error.

## Commands

Generate + review the seated A/B test:

```bash
python3 scripts/captain_snakeoil_intro.py --clip seated_master
```

Generate + review the engage A/B test:

```bash
python3 scripts/captain_snakeoil_intro.py --clip engage_master
```

Rebuild review outputs for an existing run:

```bash
python3 scripts/captain_snakeoil_intro.py --clip seated_master --make-review --run-id <run_id>
```

## Outputs

Per clip and run:

- videos: `outputs/reskin/captain_snakeoil/intro/<clip>/videos/<run_id>/<model_slug>/`
- review: `outputs/reskin/captain_snakeoil/intro/<clip>/review/<run_id>/<model_slug>/`

Each review folder contains:
- `contact.png`
- `full.gif`
- one GIF per configured window

The run review root also contains:
- `comparison_contact.png`

## Review rule

Do not install any seated intro frames into the game until one model wins on continuity:
- throne stays identical
- body scale and framing stay stable
- goblet continuity is readable
- loopable seated section exists
- drink and laugh beats are distinct
