#!/usr/bin/env python3
"""Run the character reskin pipeline from a TOML config.

This is a one-off pipeline for this game:
- No fallbacks / no backwards compatibility
- Missing or unexpected files are hard errors

Pipeline:
  --make-videos  -> generate video variants per animation
  --make-frames  -> extract frames + contact sheets from chosen videos
  --apply-sprites -> BG remove selected frames + write sprites into the game folders

Video selection rule:
  For each animation, you must copy your winner to:
    <global.video_dir>/<animation>/chosen.mp4
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import tomllib
from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _abs(path_value: str) -> Path:
    p = Path(path_value)
    if not p.is_absolute():
        p = (PROJECT_ROOT / p).resolve()
    return p


def run(cmd: list[str], *, batch: bool = True) -> None:
    """Run a command from the project root.

    If batch=True, we set RESKIN_BATCH=1 so helper scripts don't spam Finder windows.
    """

    print("Running:", " ".join(cmd))
    env = os.environ.copy()
    if batch:
        env["RESKIN_BATCH"] = "1"
    subprocess.run(cmd, check=True, cwd=str(PROJECT_ROOT), env=env)


def open_folder(path: Path) -> None:
    subprocess.run(["open", str(path)], check=True)


def frame_label(path: Path) -> int:
    match = re.search(r"(\d+)", path.stem)
    return int(match.group(1)) if match else 0


def parse_indices(value: str) -> list[int]:
    parts = [p.strip() for p in value.split(",") if p.strip()]
    indices: list[int] = []
    for part in parts:
        if "-" in part:
            start_str, end_str = part.split("-", 1)
            start = int(start_str.strip())
            end = int(end_str.strip())
            step = 1 if start <= end else -1
            indices.extend(list(range(start, end + step, step)))
        else:
            indices.append(int(part))
    return indices


def parse_time_seconds(value: str) -> float:
    raw = value.strip()
    if raw == "":
        raise ValueError("Empty time value")
    if ":" not in raw:
        return float(raw)
    parts = [p.strip() for p in raw.split(":")]
    if len(parts) > 3:
        raise ValueError(f"Invalid time format: {value}")
    vals = [float(p) for p in parts]
    while len(vals) < 3:
        vals.insert(0, 0.0)
    hours, minutes, seconds = vals
    return hours * 3600 + minutes * 60 + seconds


def is_greenscreen(path: Path, key: tuple[int, int, int] = (0, 177, 64), tol: int = 12) -> bool:
    img = Image.open(path).convert("RGB")
    w, h = img.size
    samples = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
    for x, y in samples:
        r, g, b = img.getpixel((x, y))
        if abs(r - key[0]) <= tol and abs(g - key[1]) <= tol and abs(b - key[2]) <= tol:
            return True
    return False


def ensure_dirs(*dirs: Path) -> None:
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def chosen_video_path(video_dir: Path, anim_name: str) -> Path:
    p = video_dir / anim_name / "chosen.mp4"
    if not p.exists():
        raise SystemExit(
            f"Missing chosen video for {anim_name}: {p}\n"
            "Generate variants with --make-videos, then copy your winner to chosen.mp4."
        )
    return p


def resize_frames_to_match(raw_dir: Path, target_size: tuple[int, int]) -> None:
    target_w, target_h = target_size
    for frame_path in sorted(raw_dir.glob("*.png")):
        img = Image.open(frame_path).convert("RGBA")
        if img.size == (target_w, target_h):
            continue
        img = img.resize((target_w, target_h), Image.LANCZOS)
        img.save(frame_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="docs/reskin/nova_animations.toml", help="Path to TOML config")
    parser.add_argument("--parallel", type=int, default=10, help="Max concurrent Fal jobs")
    parser.add_argument("--make-videos", action="store_true", help="Generate video variants")
    parser.add_argument("--make-frames", action="store_true", help="Extract frames + contact sheets")
    parser.add_argument("--apply-sprites", action="store_true", help="BG remove selected + write sprites")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    cfg_path = _abs(args.config)
    if not cfg_path.exists():
        raise SystemExit(f"Config not found: {cfg_path}")

    config = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    global_cfg = config.get("global", {})
    animations: list[dict] = config.get("animation", [])
    if not animations:
        raise SystemExit("Config has no [[animation]] entries")

    # Required globals (no fallbacks).
    anchor_image = str(global_cfg.get("anchor_image") or "").strip()
    if not anchor_image:
        raise SystemExit("global.anchor_image is required")
    anchor_image_path = _abs(anchor_image)
    if not anchor_image_path.exists():
        raise SystemExit(f"Anchor image not found: {anchor_image_path}")

    scale_ref = str(global_cfg.get("scale_ref") or "").strip()
    if not scale_ref:
        raise SystemExit("global.scale_ref is required")
    scale_ref_path = _abs(scale_ref)
    if not scale_ref_path.exists():
        raise SystemExit(f"Scale reference not found: {scale_ref_path}")

    frames_dir = _abs(str(global_cfg.get("frames_dir") or "").strip())
    if not str(global_cfg.get("frames_dir") or "").strip():
        raise SystemExit("global.frames_dir is required")
    video_dir = _abs(str(global_cfg.get("video_dir") or "").strip())
    if not str(global_cfg.get("video_dir") or "").strip():
        raise SystemExit("global.video_dir is required")
    padded_dir = _abs(str(global_cfg.get("padded_dir") or "").strip())
    if not str(global_cfg.get("padded_dir") or "").strip():
        raise SystemExit("global.padded_dir is required")
    ensure_dirs(frames_dir, video_dir, padded_dir)

    # Frame guide is the default workflow; if enabled, we seed videos from the framed anchor
    # and normalize extracted frames to the match sprite size before border removal.
    frame_guide_enabled = bool(global_cfg.get("frame_guide", False))
    frame_guide_thickness = int(global_cfg.get("frame_guide_thickness", 2))
    frame_guide_match = str(global_cfg.get("frame_guide_match") or "").strip()
    anchor_framed_path: Path | None = None
    target_frame_size: tuple[int, int] | None = None
    if frame_guide_enabled:
        if not frame_guide_match:
            raise SystemExit("global.frame_guide_match is required when global.frame_guide = true")
        match_path = _abs(frame_guide_match)
        if not match_path.exists():
            raise SystemExit(f"Frame guide match sprite not found: {match_path}")
        target_frame_size = Image.open(match_path).convert("RGBA").size

        anchor_framed = str(global_cfg.get("anchor_framed") or "").strip()
        if not anchor_framed:
            raise SystemExit("global.anchor_framed is required when global.frame_guide = true")
        anchor_framed_path = _abs(anchor_framed)
        if not anchor_framed_path.exists():
            raise SystemExit(f"Framed anchor not found: {anchor_framed_path}")

    constraints = str(global_cfg.get("constraints") or "").strip()
    negative = str(global_cfg.get("negative") or "").strip()
    if not negative:
        raise SystemExit("global.negative is required")
    resolution = str(global_cfg.get("resolution") or "").strip() or "1080p"

    # Step selection: if no flags, run everything.
    requested_steps = [args.make_videos, args.make_frames, args.apply_sprites]
    if any(requested_steps) and not (sum(1 for s in requested_steps if s) == 1):
        raise SystemExit("Choose exactly one of: --make-videos, --make-frames, --apply-sprites (or none for all).")

    def selected_anims() -> list[dict]:
        active = [str(x) for x in global_cfg.get("active", []) if str(x).strip()]
        if active:
            names = set(active)
            out = [a for a in animations if str(a.get("name") or "").strip() in names]
            missing = [name for name in active if name not in {str(a.get('name') or '') for a in out}]
            if missing:
                raise SystemExit(f"global.active references missing animations: {', '.join(missing)}")
            return out
        # No active list: run all.
        return [a for a in animations if str(a.get("name") or "").strip()]

    def seed_base_image() -> Path:
        if frame_guide_enabled:
            if anchor_framed_path is None:
                raise SystemExit("Internal error: anchor_framed_path missing")
            return anchor_framed_path
        return anchor_image_path

    def make_videos(anims: list[dict]) -> None:
        run_id = time.strftime("%Y%m%d_%H%M%S")
        jobs: list[list[str]] = []

        for anim in anims:
            name = str(anim.get("name") or "").strip()
            if not name:
                raise SystemExit("Animation missing name")

            prompt_variations = anim.get("prompt_variations")
            prompt = str(anim.get("prompt") or "").strip()
            prompts: list[str]
            if prompt_variations:
                prompts = [str(p).strip() for p in prompt_variations if str(p).strip()]
            elif prompt:
                prompts = [prompt]
            else:
                raise SystemExit(f"Animation {name} missing prompt/prompt_variations")
            if not prompts:
                raise SystemExit(f"Animation {name} has an empty prompt list")

            duration = str(anim.get("duration") or global_cfg.get("duration") or "3")
            end_mode = str(anim.get("end_image") or "same").strip().lower()
            if end_mode not in {"same", "flip", "none"}:
                raise SystemExit(f"Animation {name} invalid end_image: {end_mode} (use same|flip|none)")

            seed_dir = padded_dir / name / run_id
            out_dir = video_dir / name / run_id
            ensure_dirs(seed_dir, out_dir)

            end_image_arg: str | None = None
            if end_mode == "none":
                end_image_arg = "none"
            elif end_mode == "flip":
                end_path = seed_dir / "end_flip.png"
                src = Image.open(seed_base_image()).convert("RGBA")
                src = src.transpose(Image.FLIP_LEFT_RIGHT)
                src.save(end_path)
                end_image_arg = str(end_path)

            for idx, base_prompt in enumerate(prompts, start=1):
                seed_path = seed_dir / f"v{idx}.png"
                if not seed_path.exists():
                    shutil.copy2(seed_base_image(), seed_path)

                final_prompt = f"{base_prompt}. {constraints}" if constraints else base_prompt

                cmd = [
                    "python3",
                    "scripts/fal_video_generate.py",
                    "--image",
                    str(seed_path),
                    "--output-dir",
                    str(out_dir),
                    "--prompt",
                    final_prompt,
                    "--negative",
                    negative,
                    "--resolution",
                    resolution,
                    "--duration",
                    duration,
                ]
                if end_image_arg is not None:
                    cmd += ["--end-image", end_image_arg]
                jobs.append(cmd)

        with ThreadPoolExecutor(max_workers=max(1, int(args.parallel))) as executor:
            futures = [executor.submit(run, cmd) for cmd in jobs]
            for future in as_completed(futures):
                future.result()

        print(f"Videos complete. Pick winners and copy to: {video_dir}/<anim>/chosen.mp4")
        open_folder(video_dir)

    def make_frames(anims: list[dict]) -> None:
        pad_color = str(global_cfg.get("pad_color") or "#00b140")
        contact_cols = int(global_cfg.get("contact_cols") or 10)
        contact_scale = float(global_cfg.get("contact_scale") or 1.0)

        for anim in anims:
            name = str(anim.get("name") or "").strip()
            if not name:
                raise SystemExit("Animation missing name")

            extract_fps = int(anim.get("extract_fps") or global_cfg.get("extract_fps") or 6)
            extract_start = anim.get("extract_start") or global_cfg.get("extract_start")
            extract_end = anim.get("extract_end") or global_cfg.get("extract_end")
            extract_duration = anim.get("extract_duration") or global_cfg.get("extract_duration")

            video_path = chosen_video_path(video_dir, name)

            raw_dir = frames_dir / name / "raw"
            contact_path = frames_dir / name / "contact.png"
            ensure_dirs(raw_dir)
            for p in raw_dir.glob("*.png"):
                p.unlink()

            cmd = ["ffmpeg", "-y", "-i", str(video_path)]
            start_seconds: float | None = None
            end_seconds: float | None = None
            duration_seconds: float | None = None

            if extract_start:
                start_seconds = parse_time_seconds(str(extract_start))
                cmd += ["-ss", f"{start_seconds:.3f}"]
            if extract_end:
                end_seconds = parse_time_seconds(str(extract_end))
            if extract_duration:
                duration_seconds = parse_time_seconds(str(extract_duration))
            if start_seconds is not None and end_seconds is not None:
                duration_seconds = max(0.0, end_seconds - start_seconds)
                end_seconds = None
            if duration_seconds is not None:
                cmd += ["-t", f"{duration_seconds:.3f}"]
            elif end_seconds is not None:
                cmd += ["-to", f"{end_seconds:.3f}"]

            cmd += ["-vf", f"fps={extract_fps}", str(raw_dir / "frame_%03d.png")]
            run(cmd, batch=False)

            if frame_guide_enabled:
                if target_frame_size is None:
                    raise SystemExit("Internal error: target_frame_size missing")
                resize_frames_to_match(raw_dir, target_frame_size)
                run(
                    [
                        "python3",
                        "scripts/remove_frame_border.py",
                        "--input",
                        str(raw_dir),
                        "--thickness",
                        str(frame_guide_thickness),
                        "--fill",
                        pad_color,
                    ]
                )

            run(
                [
                    "python3",
                    "scripts/make_contact_sheet.py",
                    "--input",
                    str(raw_dir),
                    "--output",
                    str(contact_path),
                    "--cols",
                    str(contact_cols),
                    "--scale",
                    str(contact_scale),
                ]
            )

        open_folder(frames_dir)

    def apply_sprites(anims: list[dict]) -> None:
        scale_mult = float(global_cfg.get("scale_multiplier") or 1.0)
        output_width = int(global_cfg.get("output_width") or 2)

        for anim in anims:
            name = str(anim.get("name") or "").strip()
            if not name:
                raise SystemExit("Animation missing name")

            dest_dir = str(anim.get("dest_dir") or "").strip()
            if not dest_dir:
                raise SystemExit(f"Animation {name} missing dest_dir")
            dest_path = _abs(dest_dir)
            if not dest_path.exists():
                raise SystemExit(f"Destination folder not found: {dest_path}")

            prefix = str(anim.get("prefix") or "").strip()
            if not prefix:
                raise SystemExit(f"Animation {name} missing prefix")

            match = str(anim.get("match") or "").strip()
            if not match:
                raise SystemExit(f"Animation {name} missing match (no fallbacks)")
            match_path = _abs(match)
            if not match_path.exists():
                raise SystemExit(f"Match sprite not found: {match_path}")

            frame_indices = str(anim.get("frame_indices") or "").strip()
            if not frame_indices:
                raise SystemExit(f"Animation {name} missing frame_indices")
            selected_labels = parse_indices(frame_indices)
            if not selected_labels:
                raise SystemExit(f"Animation {name} has empty frame_indices")

            single_frame = bool(anim.get("single_frame", False))
            output_start = anim.get("output_start")
            if not single_frame and output_start is None:
                raise SystemExit(f"Animation {name} missing output_start")

            flip_h = bool(anim.get("flip_h", False))
            anim_scale_mult = float(anim.get("scale_multiplier") or scale_mult)

            raw_dir = frames_dir / name / "raw"
            if not raw_dir.exists():
                raise SystemExit(f"Missing frames for {name}: {raw_dir} (run --make-frames)")

            selected_dir = frames_dir / name / "selected"
            final_dir = frames_dir / name / "final"
            ensure_dirs(selected_dir, final_dir)

            raw_files = sorted([p for p in raw_dir.iterdir() if p.suffix.lower() == ".png"], key=frame_label)
            if not raw_files:
                raise SystemExit(f"No raw frames found for {name}: {raw_dir}")
            label_to_path = {frame_label(p): p for p in raw_files}

            selected_sources: list[Path] = []
            for label in selected_labels:
                if label not in label_to_path:
                    raise SystemExit(f"Frame label not found for {name}: {label}")
                selected_sources.append(label_to_path[label])

            # Keep selected/ final folders in sync with chosen labels.
            selected_names = {p.name for p in selected_sources}
            for p in selected_dir.glob("*.png"):
                if p.name not in selected_names:
                    p.unlink()
            for p in final_dir.glob("*.png"):
                if p.name not in selected_names:
                    p.unlink()

            for src in selected_sources:
                dest = selected_dir / src.name
                if dest.exists() and dest.stat().st_mtime >= src.stat().st_mtime and is_greenscreen(dest):
                    continue
                shutil.copy2(src, dest)

            def final_is_current() -> bool:
                for fname in selected_names:
                    src = selected_dir / fname
                    out = final_dir / fname
                    if not out.exists():
                        return False
                    if out.stat().st_mtime < src.stat().st_mtime:
                        return False
                return True

            if not final_is_current():
                run(
                    [
                        "python3",
                        "scripts/fal_bg_remove.py",
                        "--input",
                        str(selected_dir),
                        "--output-dir",
                        str(final_dir),
                        "--max-inflight",
                        str(max(1, int(args.parallel))),
                    ]
                )
                missing = [n for n in selected_names if not (final_dir / n).exists()]
                if missing:
                    raise SystemExit(f"Missing BG-removed frames for {name}: {', '.join(sorted(missing))}")

            # Build output index mapping so filenames match the game's expected numbering.
            output_indices: list[int] | None = None
            if not single_frame:
                start = int(output_start)
                output_indices = list(range(start, start + len(selected_labels)))

            cmd = [
                "python3",
                "scripts/prepare_walk_frames.py",
                "--input",
                str(final_dir),
                "--dest",
                str(dest_path),
                "--prefix",
                prefix,
                "--match",
                str(match_path),
                "--scale-ref",
                str(scale_ref_path),
                "--scale-mult",
                str(anim_scale_mult),
            ]
            if frame_guide_enabled:
                cmd.append("--use-canvas")
            if flip_h:
                cmd.append("--flip-h")
            if single_frame:
                if len(selected_labels) != 1:
                    raise SystemExit(f"Animation {name} is single_frame but has {len(selected_labels)} indices")
                cmd += ["--indices", str(selected_labels[0]), "--single-frame"]
            else:
                cmd += ["--indices", frame_indices]
                cmd += ["--output-indices", ",".join(str(i) for i in output_indices)]
                cmd += ["--output-width", str(output_width)]

            run(cmd)

        open_folder(frames_dir)

    anims = selected_anims()

    if args.make_videos:
        make_videos(anims)
    elif args.make_frames:
        make_frames(anims)
    elif args.apply_sprites:
        apply_sprites(anims)
    else:
        make_videos(anims)
        make_frames(anims)
        apply_sprites(anims)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

