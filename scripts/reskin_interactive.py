#!/usr/bin/env python3
"""One command to drive the reskin workflow (interactive).

This is intentionally *not* a general-purpose tool. It's a strict, one-off pipeline for this
repo and a single user:
- no fallbacks
- missing files are hard errors
- all state lives under outputs/reskin/<character>/... (gitignored)

Flow:
  1) Generate 4 base idle options (nano-banana edit) -> choose 1
  2) Build anchor (solid greenscreen + 2px white border) to match an existing sprite size/baseline
  3) Select animations (writes global.active)
  4) Generate video variants -> pick winners -> create chosen.mp4 per animation
  5) Extract frames + contact sheets from chosen.mp4
  6) Apply sprites (BG remove selected frames + write to game sprite folders)
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from pathlib import Path

try:
    import tomllib  # py>=3.11
except ModuleNotFoundError:  # py<=3.10 (our scripts venv)
    import tomli as tomllib


PROJECT_ROOT = Path(__file__).resolve().parents[1]


TAXMAN_PICK_META = {
    "idle": {"playground": "I", "state": "Ground/Move/IdleAi", "outline": "looped idle stance"},
    "walk": {"playground": "W", "state": "Ground/Move/Follow", "outline": "in-place walk cycle"},
    "turn": {"playground": "turn inside walk", "state": "Ground/Move/Follow", "outline": "pivot during follow/turn"},
    "hurt_light": {"playground": "H (damage-driven)", "state": "Ground/Hurt", "outline": "light flinch frame"},
    "hurt_medium": {"playground": "H (damage-driven)", "state": "Ground/Hurt", "outline": "medium flinch frame"},
    "hurt_knockout": {"playground": "H (damage-driven)", "state": "Ground/Hurt", "outline": "knockout impact frame"},
    "attack_retaliate": {"playground": "4", "state": "Ground/AttackRetaliate", "outline": "single retaliate slash sequence"},
    "attack_combo": {"playground": "2", "state": "Ground/AttackCombo", "outline": "multi-hit combo sequence"},
    "attack_dash_begin": {
        "playground": "5 (state) / 3 (combined)",
        "state": "Ground/AttackDash",
        "outline": "dash startup + acceleration",
    },
    "attack_dash_end": {
        "playground": "6 (state) / 3 (combined)",
        "state": "Ground/AttackDash",
        "outline": "dash hit/recovery phase",
    },
    "attack_area_body": {
        "playground": "1",
        "state": "Ground/AttackArea",
        "outline": "BODY clip only; engine layers lightning/ground/smoke/explosion VFX",
    },
    "death_explosion_body": {
        "playground": "D",
        "state": "DieAi",
        "outline": "BODY clip only; engine layers death VFX/smoke/explosions",
    },
    "seated_engage": {"playground": "E (state)", "state": "Seated", "outline": "seated engage beat"},
    "seated_laugh": {"playground": "L (state)", "state": "Seated", "outline": "seated laugh beat"},
    "seated_drink": {"playground": "R (state)", "state": "Seated", "outline": "seated goblet drink beat"},
    "seated_swirl": {"playground": "S (state)", "state": "Seated", "outline": "seated goblet swirl beat"},
}


def prompt(text: str, default: str | None = None) -> str:
    if default is None:
        return input(f"{text} ").strip()
    value = input(f"{text} [{default}] ").strip()
    return value or default


def run(cmd: list[str], *, batch: bool = True) -> None:
    print("Running:", " ".join(cmd))
    env = os.environ.copy()
    if batch:
        env["RESKIN_BATCH"] = "1"
    subprocess.run(cmd, check=True, cwd=str(PROJECT_ROOT), env=env)


def open_folder(path: Path) -> None:
    try:
        subprocess.run(["open", str(path)], check=False)
    except Exception:
        # Best-effort only; never fail the pipeline because Finder can't open.
        pass


def _abs(path_value: str) -> Path:
    p = Path(path_value)
    if not p.is_absolute():
        p = (PROJECT_ROOT / p).resolve()
    return p


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def replace_active_block(text: str, items: list[str]) -> str:
    block_re = re.compile(r"active\s*=\s*\[(.*?)\]", re.DOTALL)
    match = block_re.search(text)
    lines = ["active = ["]
    for item in items:
        lines.append(f' "{item}",')
    lines.append("]")
    new_block = "\n".join(lines)
    if match:
        return text[: match.start()] + new_block + text[match.end() :]

    # If missing, insert right after [global] (strict but self-healing for config).
    global_re = re.compile(r"^\[global\]\s*$", re.MULTILINE)
    gmatch = global_re.search(text)
    if not gmatch:
        raise SystemExit("Missing [global] block in config (required).")
    insert_at = gmatch.end()
    return text[:insert_at] + "\n" + new_block + "\n" + text[insert_at:]


def find_animation_names(config: dict) -> list[str]:
    names: list[str] = []
    for anim in config.get("animation", []):
        name = str(anim.get("name") or "").strip()
        if name:
            names.append(name)
    return names


def output_target_label(anim: dict, default_width: int = 2) -> str:
    prefix = str(anim.get("prefix") or "").strip()
    frame_count = int(anim.get("frame_count") or 0)
    if bool(anim.get("single_frame", False)):
        return prefix

    output_indices = str(anim.get("output_indices") or "").strip()
    if output_indices:
        raw = [p.strip() for p in output_indices.split(",") if p.strip()]
        if len(raw) <= 6:
            return f"{prefix}{','.join(raw)}"
        return f"{prefix}{raw[0]}..{raw[-1]} ({len(raw)} files)"

    start = anim.get("output_start")
    width = int(anim.get("output_width") or default_width)
    start_num = int(start) if start is not None else 0
    end = start_num + max(0, frame_count - 1)
    return f"{prefix}{start_num:0{width}d}..{end:0{width}d}"


def build_group_labels(config: dict, anim_names: list[str]) -> dict[str, list[str]]:
    groups = config.get("consistency_groups", {})
    if not isinstance(groups, dict) or not groups:
        return {}
    out: dict[str, list[str]] = {name: [] for name in anim_names}
    for group_name, members in groups.items():
        if not isinstance(members, list):
            raise SystemExit(f"consistency_groups.{group_name} must be a list")
        for raw_name in members:
            name = str(raw_name).strip()
            if not name:
                continue
            if name not in out:
                raise SystemExit(
                    f"consistency_groups.{group_name} has unknown animation: {name}"
                )
            out[name].append(str(group_name))
    return out


def apply_consistency_groups(chosen_names: list[str], anim_names: list[str], config: dict) -> list[str]:
    """Expand selection so linked animations are always generated together."""
    groups = config.get("consistency_groups", {})
    if not isinstance(groups, dict) or not groups:
        return chosen_names

    chosen = set(chosen_names)
    added: list[str] = []
    for group_name, members in groups.items():
        if not isinstance(members, list):
            raise SystemExit(f"consistency_groups.{group_name} must be a list")
        member_names = [str(m).strip() for m in members if str(m).strip()]
        if not member_names:
            continue
        unknown = [m for m in member_names if m not in anim_names]
        if unknown:
            raise SystemExit(
                f"consistency_groups.{group_name} has unknown animation(s): {', '.join(unknown)}"
            )
        intersects = any(m in chosen for m in member_names)
        if intersects:
            for m in member_names:
                if m not in chosen:
                    chosen.add(m)
                    added.append(m)

    if added:
        print(f"Added linked animations for consistency: {', '.join(added)}")
    # Preserve config animation ordering.
    return [name for name in anim_names if name in chosen]


def update_animation_string_field(toml_text: str, *, anim_name: str, key: str, value: str) -> str:
    """Replace `key = "..."` inside the matching [[animation]] block (no auto-add)."""
    block_re = re.compile(r"^\[\[animation\]\]\s*(.*?)(?=^\[\[animation\]\]|\Z)", re.DOTALL | re.MULTILINE)
    blocks = list(block_re.finditer(toml_text))
    if not blocks:
        raise SystemExit("No [[animation]] blocks found in config.")

    for m in blocks:
        block = toml_text[m.start() : m.end()]
        name_m = re.search(r'^name\s*=\s*"([^"]+)"\s*$', block, re.MULTILINE)
        if not name_m:
            continue
        if name_m.group(1) != anim_name:
            continue

        key_re = re.compile(rf'^\s*{re.escape(key)}\s*=\s*".*?"\s*$', re.MULTILINE)
        key_matches = list(key_re.finditer(block))
        if len(key_matches) != 1:
            raise SystemExit(
                f"Expected exactly one '{key} = \"...\"' inside animation '{anim_name}', found {len(key_matches)}."
            )
        start, end = key_matches[0].span()
        replaced_block = block[:start] + f'{key} = \"{value}\"' + block[end:]
        return toml_text[: m.start()] + replaced_block + toml_text[m.end() :]

    raise SystemExit(f"Animation block not found in config: {anim_name}")


def choose_numbered(options: list[str], *, header: str, default: int | None = None) -> int:
    if not options:
        raise SystemExit("No options to choose from.")
    print(f"\\n{header}:")
    for i, opt in enumerate(options, start=1):
        print(f"  {i}) {opt}")
    while True:
        d = str(default) if default is not None else None
        raw = prompt("Select a number", d)
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return int(raw)
        print("Out of range.")


def latest_run_dir(base_root: Path) -> Path | None:
    if not base_root.exists():
        return None
    runs = [p for p in base_root.iterdir() if p.is_dir() and p.name.startswith("run_")]
    if not runs:
        return None
    return max(runs, key=lambda p: p.stat().st_mtime)


def list_options(folder: Path) -> list[Path]:
    return sorted(folder.glob("option_*.png"))


def main() -> int:
    legacy_fal = PROJECT_ROOT / "outputs" / "fal"
    if legacy_fal.exists() and any(legacy_fal.iterdir()):
        print(
            "\nLegacy output folder detected: outputs/fal\n"
            "This wizard uses outputs/reskin/<character>/... only.\n"
        )
        if prompt("Archive outputs/fal into outputs/_archive/? (y/n)", "n").lower().startswith("y"):
            stamp = time.strftime("%Y%m%d_%H%M%S")
            archive_root = PROJECT_ROOT / "outputs" / "_archive" / stamp
            archive_root.mkdir(parents=True, exist_ok=True)
            dest = archive_root / "fal"
            if dest.exists():
                raise SystemExit(f"Archive destination already exists: {dest}")
            shutil.move(str(legacy_fal), str(dest))
            print(f"Archived to {dest.relative_to(PROJECT_ROOT)}")

    cfg_rel = prompt("Config path", "docs/reskin/captain_snakeoil_animations.toml")
    cfg_path = _abs(cfg_rel)
    if not cfg_path.exists():
        raise SystemExit(f"Config not found: {cfg_path}")

    cfg_text = read_text(cfg_path)
    cfg_data = tomllib.loads(cfg_text)
    global_cfg = cfg_data.get("global", {})
    animations = cfg_data.get("animation", [])
    anim_names = find_animation_names(cfg_data)
    if not anim_names:
        raise SystemExit("Config has no [[animation]] entries.")

    # Hard-required config fields for this pipeline.
    base_task = str(global_cfg.get("base_task") or "").strip()
    if not base_task:
        raise SystemExit("global.base_task is required (path to the idle_00 task file).")
    base_task_path = _abs(base_task)
    if not base_task_path.exists():
        raise SystemExit(f"Base task file not found: {base_task_path}")

    match_sprite = str(global_cfg.get("frame_guide_match") or "").strip()
    if not match_sprite:
        raise SystemExit("global.frame_guide_match is required (defines target size + baseline).")
    match_sprite_path = _abs(match_sprite)
    if not match_sprite_path.exists():
        raise SystemExit(f"Match sprite not found: {match_sprite_path}")

    anchor_base = str(global_cfg.get("anchor_image") or "").strip()
    anchor_framed = str(global_cfg.get("anchor_framed") or "").strip()
    if not anchor_base or not anchor_framed:
        raise SystemExit("global.anchor_image and global.anchor_framed are required.")
    anchor_base_path = _abs(anchor_base)
    anchor_framed_path = _abs(anchor_framed)

    # Derive character output root from anchor paths (no extra config needed).
    # outputs/reskin/<character>/anchor/anchor_base.png -> outputs/reskin/<character>
    if anchor_base_path.parent.name != "anchor":
        raise SystemExit(f"Expected anchor_image under outputs/reskin/<character>/anchor, got: {anchor_base_path}")
    character_root = anchor_base_path.parent.parent
    base_root = character_root / "base"
    base_chosen = base_root / "chosen.png"

    use_existing_anchor = prompt(
        "Use existing anchor (skip base generation + anchor build)? (y/n)", "y"
    ).lower().startswith("y")

    if use_existing_anchor:
        if not anchor_base_path.exists() or not anchor_framed_path.exists():
            raise SystemExit(
                "Anchor files not found.\n"
                f"- {anchor_base_path}\n"
                f"- {anchor_framed_path}\n"
                "Copy/create them first, then re-run."
            )
        open_folder(anchor_base_path.parent)
        print(f"Using existing anchor: {anchor_base_path.relative_to(PROJECT_ROOT)}")
    else:
        print("\nBase (idle) still:")
        base_source_pad_pct = float(global_cfg.get("base_source_pad_pct") or 0.0)
        base_source_pad_color = str(global_cfg.get("base_source_pad_color") or "#00b140").strip()
        base_prompt_append = str(global_cfg.get("base_prompt_append") or "").strip()
        gen = prompt("Generate 4 new base options now? (y/n)", "y").lower().startswith("y")
        if gen:
            run_id = time.strftime("run_%Y%m%d_%H%M%S")
            run_root = base_root / run_id
            base_cmd = [
                "python3",
                "scripts/fal_reskin_generate.py",
                "--task",
                str(base_task_path.relative_to(PROJECT_ROOT)),
                "--output-dir",
                str(run_root.relative_to(PROJECT_ROOT)),
                "--num-images",
                "4",
            ]
            if base_prompt_append:
                base_cmd += ["--append-prompt", base_prompt_append]
            if base_source_pad_pct > 0:
                base_cmd += ["--pad-pct", str(base_source_pad_pct), "--pad-color", base_source_pad_color]
            run(
                base_cmd,
                batch=False,
            )
            options_dir = run_root / base_task_path.stem
        else:
            latest = latest_run_dir(base_root)
            default_dir = str(latest) if latest else str(base_root / "run_<timestamp>")
            options_dir = _abs(prompt("Existing base options folder", default_dir))

        if not options_dir.exists():
            raise SystemExit(f"Base options folder not found: {options_dir}")

        options = list_options(options_dir)
        if len(options) != 4:
            raise SystemExit(f"Expected exactly 4 base options in {options_dir}, found {len(options)}.")

        open_folder(options_dir)
        idx = choose_numbered(
            [str(p.relative_to(PROJECT_ROOT)) for p in options], header="Choose base option", default=1
        )
        chosen_option = options[idx - 1]

        base_chosen.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(chosen_option, base_chosen)
        print(f"Selected base: {base_chosen.relative_to(PROJECT_ROOT)}")

        print("\nAnchor (solid greenscreen + border):")
        bbox_pad = str(global_cfg.get("anchor_bbox_pad_pct") or "0.08")
        if base_source_pad_pct > 0:
            # Source pre-padding already adds safety margin. Avoid shrinking twice.
            bbox_pad = "0.0"
            print("Source pre-padding is enabled; defaulting anchor bbox pad to 0.0 to avoid double-padding.")
        bbox_pad = prompt("Anchor bbox pad %", bbox_pad)
        scale_mult_default = str(global_cfg.get("anchor_scale_mult") or "1.0")
        if base_source_pad_pct > 0:
            scale_mult_default = "1.0"
        scale_mult = prompt("Anchor scale multiplier", scale_mult_default)

        anchor_base_path.parent.mkdir(parents=True, exist_ok=True)
        run(
            [
                "python3",
                "scripts/prepare_anchor_image.py",
                "--input",
                str(base_chosen.relative_to(PROJECT_ROOT)),
                "--match",
                str(match_sprite_path.relative_to(PROJECT_ROOT)),
                "--output",
                str(anchor_base_path.relative_to(PROJECT_ROOT)),
                "--framed-output",
                str(anchor_framed_path.relative_to(PROJECT_ROOT)),
                "--bbox-pad-pct",
                str(bbox_pad),
                "--scale-mult",
                str(scale_mult),
            ],
            batch=False,
        )
        open_folder(anchor_base_path.parent)

    # Animation selection -> writes global.active (required by this pipeline).
    active = [str(x) for x in global_cfg.get("active", []) if str(x).strip()]
    default_sel = ",".join(active) if active else "all"
    group_labels = build_group_labels(cfg_data, anim_names)
    anim_by_name = {
        str(a.get("name") or "").strip(): a for a in animations if str(a.get("name") or "").strip()
    }
    is_taxman_reskin = "captain_snakeoil_animations.toml" in str(cfg_path)
    default_output_width = int(global_cfg.get("output_width") or 2)
    print("\nAnimations:")
    for i, name in enumerate(anim_names, start=1):
        anim = anim_by_name.get(name, {})
        frame_count = int(anim.get("frame_count") or 0)
        target = output_target_label(anim, default_output_width)
        count_label = f"{frame_count}f" if frame_count > 0 else "?"
        labels = group_labels.get(name, [])
        extra_parts: list[str] = [count_label, f"-> {target}"]
        if is_taxman_reskin and name in TAXMAN_PICK_META:
            meta = TAXMAN_PICK_META[name]
            extra_parts.append(f"key {meta['playground']}")
            extra_parts.append(str(meta["state"]))
        if labels:
            extra_parts.append(f"group: {', '.join(labels)}")
        extra = " | ".join(extra_parts)
        print(f"  {i}) {name}  [{extra}]")
        if is_taxman_reskin and name in TAXMAN_PICK_META:
            print(f"      outline: {TAXMAN_PICK_META[name]['outline']}")
    raw_sel = prompt("Run which animations? (numbers comma or 'all')", "all" if not active else "keep")
    if raw_sel.strip().lower() == "keep":
        chosen_names = active
    elif raw_sel.strip().lower() == "all":
        chosen_names = anim_names
    else:
        chosen_names = []
        for part in raw_sel.split(","):
            part = part.strip()
            if not part.isdigit():
                raise SystemExit("Selection must be 'keep', 'all', or comma-separated numbers.")
            n = int(part)
            if n < 1 or n > len(anim_names):
                raise SystemExit("Selection out of range.")
            chosen_names.append(anim_names[n - 1])

    chosen_names = apply_consistency_groups(chosen_names, anim_names, cfg_data)

    cfg_text = replace_active_block(cfg_text, chosen_names)
    write_text(cfg_path, cfg_text)
    print(f"Updated global.active in {cfg_path.relative_to(PROJECT_ROOT)}")

    # Step menu
    print("\nNext step:")
    steps = [
        "Generate videos",
        "Pick video winners (set chosen.mp4)",
        "Extract frames + contact sheets",
        "Apply sprites",
        "Run 1->4 (full pipeline)",
    ]
    step = choose_numbered(steps, header="Steps", default=5)

    video_dir = _abs(str(global_cfg.get("video_dir") or "").strip())
    frames_dir = _abs(str(global_cfg.get("frames_dir") or "").strip())
    if not video_dir:
        raise SystemExit("global.video_dir missing")
    if not frames_dir:
        raise SystemExit("global.frames_dir missing")

    def pick_videos() -> None:
        for anim in chosen_names:
            anim_dir = video_dir / anim
            if not anim_dir.exists():
                raise SystemExit(f"Missing video folder for {anim}: {anim_dir} (run videos first)")
            runs = [p for p in anim_dir.iterdir() if p.is_dir()]
            if not runs:
                raise SystemExit(f"No video runs found for {anim}: {anim_dir}")
            runs_sorted = sorted(runs, key=lambda p: p.stat().st_mtime, reverse=True)
            run_labels = [p.name for p in runs_sorted[:10]]
            chosen_run_idx = choose_numbered(
                run_labels, header=f"{anim}: pick a run folder", default=1
            )
            run_folder = runs_sorted[chosen_run_idx - 1]
            mp4s = sorted(run_folder.glob("*.mp4"))
            if not mp4s:
                raise SystemExit(f"No mp4 files found in {run_folder}")
            open_folder(run_folder)
            mp4_labels = [p.name for p in mp4s]
            vid_idx = choose_numbered(mp4_labels, header=f"{anim}: choose winner", default=1)
            winner = mp4s[vid_idx - 1]
            dest = anim_dir / "chosen.mp4"
            shutil.copy2(winner, dest)
            print(f"{anim}: chosen -> {dest.relative_to(PROJECT_ROOT)}")

        open_folder(video_dir)

    def maybe_edit_frame_indices() -> None:
        nonlocal cfg_text
        cfg_data_now = tomllib.loads(cfg_text)
        frames_root = _abs(str(cfg_data_now.get("global", {}).get("frames_dir") or "").strip())
        if not frames_root:
            raise SystemExit("global.frames_dir missing")

        for anim in chosen_names:
            contact_path = frames_root / anim / "contact.png"
            if not contact_path.exists():
                raise SystemExit(f"Missing contact sheet for {anim}: {contact_path} (run make-frames first)")
            subprocess.run(["open", str(contact_path)], check=True)

            # Pull current value from the parsed config (strict: must exist).
            current = None
            for a in cfg_data_now.get("animation", []):
                if str(a.get("name") or "").strip() == anim:
                    current = str(a.get("frame_indices") or "").strip()
                    break
            if not current:
                raise SystemExit(f"Missing frame_indices for {anim} in config (required).")

            new_val = prompt(f"{anim} frame_indices", current)
            if new_val != current:
                cfg_text = update_animation_string_field(cfg_text, anim_name=anim, key="frame_indices", value=new_val)
                cfg_data_now = tomllib.loads(cfg_text)

        write_text(cfg_path, cfg_text)
        print(f"Updated frame_indices in {cfg_path.relative_to(PROJECT_ROOT)}")

    if step in {1, 5}:
        if is_taxman_reskin:
            print("\nVideo picking targets:")
            for name in chosen_names:
                anim = anim_by_name.get(name, {})
                frame_count = int(anim.get("frame_count") or 0)
                target = output_target_label(anim, default_output_width)
                meta = TAXMAN_PICK_META.get(name, {})
                action = str(meta.get("state") or "?")
                playground = str(meta.get("playground") or "-")
                outline = str(meta.get("outline") or "")
                print(
                    f"  - {name}: {frame_count} frames -> {target} | playground {playground} | {action}"
                )
                if outline:
                    print(f"      {outline}")
        run(["python3", "scripts/nova_batch.py", "--config", cfg_rel, "--make-videos"], batch=False)
        open_folder(video_dir)
    if step in {2, 5}:
        pick_videos()
    if step in {3, 5}:
        run(["python3", "scripts/nova_batch.py", "--config", cfg_rel, "--make-frames"], batch=False)
        open_folder(frames_dir)
        if prompt("Edit frame_indices now? (y/n)", "y" if step == 5 else "n").lower().startswith("y"):
            maybe_edit_frame_indices()
    if step in {4, 5}:
        run(["python3", "scripts/nova_batch.py", "--config", cfg_rel, "--apply-sprites"], batch=False)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
