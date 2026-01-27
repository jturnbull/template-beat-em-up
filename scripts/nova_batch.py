#!/usr/bin/env python3
"""Batch generate videos, extract frames, remove BG, and prepare sprite frames via a TOML config."""
from __future__ import annotations

import argparse
import subprocess
import time
from pathlib import Path
import tomllib


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> None:
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=str(PROJECT_ROOT))


def backup_existing(path: Path) -> None:
    if not path.exists():
        return
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup = path.with_name(f"{path.stem}_prev_{timestamp}{path.suffix}")
    path.rename(backup)


def parse_hex_color(value: str) -> tuple[int, int, int, int]:
    cleaned = value.strip().lstrip("#")
    if len(cleaned) != 6:
        raise ValueError(f"Expected 6-digit hex color, got: {value}")
    r = int(cleaned[0:2], 16)
    g = int(cleaned[2:4], 16)
    b = int(cleaned[4:6], 16)
    return (r, g, b, 255)


def pad_amount(value_pct: float | None, value_px: float | None, size: int) -> int:
    if value_px is not None:
        return max(0, int(round(float(value_px))))
    if value_pct is None:
        return 0
    return max(0, int(round(float(value_pct) * size)))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="docs/reskin/nova_animations.toml", help="Path to TOML config")
    parser.add_argument("--only", nargs="*", default=None, help="Only run these animation names")
    parser.add_argument(
        "--make-videos",
        action="store_true",
        help="Only generate videos (skip frames, bg remove, contact sheets)",
    )
    parser.add_argument(
        "--make-frames",
        action="store_true",
        help="Only extract frames (and optional bg remove/contact) from existing videos",
    )
    parser.add_argument("--skip-video", action="store_true", help="Skip video generation")
    parser.add_argument("--skip-extract", action="store_true", help="Skip frame extraction")
    parser.add_argument("--skip-bg-remove", action="store_true", help="Skip background removal")
    parser.add_argument("--skip-contact", action="store_true", help="Skip contact sheet")
    parser.add_argument("--apply-sprites", action="store_true", help="Write frames into sprite folders")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.apply_sprites:
        args.skip_video = True
        args.skip_extract = True
        args.skip_bg_remove = True
        args.skip_contact = True
    elif args.make_videos:
        args.skip_video = False
        args.skip_extract = True
        args.skip_bg_remove = True
        args.skip_contact = True
    elif args.make_frames:
        args.skip_video = True
        args.skip_extract = False
        args.skip_bg_remove = False
        args.skip_contact = False
    cfg_path = (PROJECT_ROOT / args.config).resolve()
    if not cfg_path.exists():
        raise SystemExit(f"Config not found: {cfg_path}")

    config = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    global_cfg = config.get("global", {})
    animations = config.get("animation", [])

    anchor_image = global_cfg.get("anchor_image")
    if not anchor_image:
        raise SystemExit("global.anchor_image is required")

    frames_dir = PROJECT_ROOT / global_cfg.get("frames_dir", "outputs/fal/frames")
    frames_dir.mkdir(parents=True, exist_ok=True)

    for anim in animations:
        name = anim.get("name")
        if not name:
            continue
        if args.only and name not in args.only:
            continue
        if not anim.get("enabled", False):
            print(f"Skipping {name} (disabled)")
            continue

        prompt = anim.get("prompt")
        if not prompt:
            print(f"Skipping {name} (missing prompt)")
            continue

        constraints = anim.get("constraints") or global_cfg.get("constraints")
        if constraints:
            prompt = f"{prompt}. {constraints}"

        negative = anim.get("negative") or global_cfg.get("negative")
        resolution = anim.get("resolution") or global_cfg.get("resolution") or "1080p"
        duration = str(anim.get("duration") or global_cfg.get("duration") or "3")
        extract_fps = anim.get("extract_fps") or global_cfg.get("extract_fps") or 6
        bg_remove = anim.get("bg_remove")
        if bg_remove is None:
            bg_remove = bool(global_cfg.get("bg_remove", True))

        video_path = PROJECT_ROOT / "outputs" / "fal" / "video" / f"{name}.mp4"
        raw_dir = frames_dir / f"{name}_raw"
        no_bg_dir = frames_dir / f"{name}_no_bg"
        contact_path = frames_dir / f"{name}_contact.png"

        if not args.skip_video:
            image_path = PROJECT_ROOT / anchor_image
            if not image_path.exists():
                raise SystemExit(f"Anchor image not found: {image_path}")
            pad_color = anim.get("pad_color") or global_cfg.get("pad_color") or "#00b140"
            pad_keys = (
                "pad_top_pct",
                "pad_bottom_pct",
                "pad_left_pct",
                "pad_right_pct",
                "pad_top_px",
                "pad_bottom_px",
                "pad_left_px",
                "pad_right_px",
            )
            has_padding = any(anim.get(k) for k in pad_keys)
            if has_padding:
                from PIL import Image

                src = Image.open(image_path).convert("RGBA")
                pad_top = pad_amount(anim.get("pad_top_pct"), anim.get("pad_top_px"), src.height)
                pad_bottom = pad_amount(anim.get("pad_bottom_pct"), anim.get("pad_bottom_px"), src.height)
                pad_left = pad_amount(anim.get("pad_left_pct"), anim.get("pad_left_px"), src.width)
                pad_right = pad_amount(anim.get("pad_right_pct"), anim.get("pad_right_px"), src.width)
                new_w = src.width + pad_left + pad_right
                new_h = src.height + pad_top + pad_bottom
                bg = parse_hex_color(str(pad_color))
                canvas = Image.new("RGBA", (new_w, new_h), bg)
                canvas.paste(src, (pad_left, pad_top))
                padded_dir = PROJECT_ROOT / "outputs" / "fal" / "padded"
                padded_dir.mkdir(parents=True, exist_ok=True)
                padded_path = padded_dir / f"{name}.png"
                backup_existing(padded_path)
                canvas.save(padded_path)
                image_for_video = padded_path
            else:
                image_for_video = image_path
            cmd = [
                "python3",
                "scripts/fal_video_generate.py",
                "--image",
                str(image_for_video),
                "--prompt",
                prompt,
                "--negative",
                negative,
                "--resolution",
                resolution,
                "--duration",
                duration,
            ]
            run(cmd)
            # The video script saves to outputs/fal/video/<anchor_stem>.mp4
            # Rename to animation-specific name if needed.
            anchor_stem = Path(anchor_image).stem
            default_video = PROJECT_ROOT / "outputs" / "fal" / "video" / f"{anchor_stem}.mp4"
            if default_video.exists() and default_video != video_path:
                backup_existing(video_path)
                video_path.parent.mkdir(parents=True, exist_ok=True)
                default_video.replace(video_path)

        if not args.skip_extract:
            raw_dir.mkdir(parents=True, exist_ok=True)
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(video_path),
                "-vf",
                f"fps={extract_fps}",
                str(raw_dir / "frame_%03d.png"),
            ]
            run(cmd)

        if bg_remove and not args.skip_bg_remove:
            cmd = [
                "python3",
                "scripts/fal_bg_remove.py",
                "--input",
                str(raw_dir),
                "--output-dir",
                str(no_bg_dir),
            ]
            run(cmd)

        if not args.skip_contact:
            cols = int(global_cfg.get("contact_cols", 10))
            scale = float(global_cfg.get("contact_scale", 0.25))
            source_dir = no_bg_dir if no_bg_dir.exists() else raw_dir
            cmd = [
                "python3",
                "scripts/make_contact_sheet.py",
                "--input",
                str(source_dir),
                "--output",
                str(contact_path),
                "--cols",
                str(cols),
                "--scale",
                str(scale),
            ]
            run(cmd)

        if args.apply_sprites:
            dest_dir = anim.get("dest_dir")
            frame_count = anim.get("frame_count")
            start_index = anim.get("start_index")
            stride = anim.get("stride", 1)
            prefix = anim.get("prefix", "")
            if not dest_dir or frame_count is None or start_index is None:
                print(f"Skipping sprite apply for {name} (missing dest/frame_count/start_index)")
                continue

            source_dir = no_bg_dir if no_bg_dir.exists() else raw_dir
            cmd = [
                "python3",
                "scripts/prepare_walk_frames.py",
                "--input",
                str(source_dir),
                "--dest",
                dest_dir,
                "--count",
                str(frame_count),
                "--mode",
                "contiguous",
                "--start-index",
                str(start_index),
                "--stride",
                str(stride),
                "--prefix",
                prefix,
                "--backup",
            ]
            run(cmd)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
