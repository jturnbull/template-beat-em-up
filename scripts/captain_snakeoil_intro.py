#!/usr/bin/env python3
"""Generate and review Captain Snakeoil throne intro source videos."""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
from PIL import Image, ImageDraw, ImageFont

from fal_video_generate import SUPPORTED_MODELS


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_CLIPS = {"seated_master", "engage_master"}


def _abs(path_value: str) -> Path:
    path = Path(path_value)
    if not path.is_absolute():
        path = (PROJECT_ROOT / path).resolve()
    return path


def run(cmd: list[str], *, batch: bool = True) -> None:
    print("Running:", " ".join(cmd))
    env = os.environ.copy()
    if batch:
        env["RESKIN_BATCH"] = "1"
    subprocess.run(cmd, check=True, cwd=str(PROJECT_ROOT), env=env)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def open_folder(path: Path) -> None:
    if os.environ.get("RESKIN_BATCH") == "1":
        return
    subprocess.run(["open", str(path)], check=True)


def model_slug(model: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", model.strip("/"))
    return slug.strip("_").lower()


def clear_pngs(path: Path) -> None:
    ensure_dir(path)
    for png in path.glob("*.png"):
        png.unlink()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="docs/reskin/captain_snakeoil_intro.toml")
    parser.add_argument("--clip", required=True, choices=sorted(EXPECTED_CLIPS))
    parser.add_argument("--parallel", type=int, default=2)
    parser.add_argument("--make-videos", action="store_true")
    parser.add_argument("--make-review", action="store_true")
    parser.add_argument("--run-id", default=None, help="Required for --make-review without generation")
    return parser.parse_args()


def load_config(config_path: Path) -> tuple[dict, dict]:
    if not config_path.exists():
        raise SystemExit(f"Config not found: {config_path}")
    config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    global_cfg = config.get("global")
    if not isinstance(global_cfg, dict):
        raise SystemExit("Config missing [global] block")
    clip_cfgs = config.get("clip")
    if not isinstance(clip_cfgs, dict):
        raise SystemExit("Config missing [clip] block")
    if set(clip_cfgs.keys()) != EXPECTED_CLIPS:
        raise SystemExit(
            "Config [clip] block must contain exactly: "
            + ", ".join(sorted(EXPECTED_CLIPS))
        )
    return global_cfg, clip_cfgs


def create_gif_from_frames(frame_dir: Path, output_path: Path, frame_ms: int) -> None:
    frames = sorted(frame_dir.glob("*.png"))
    if not frames:
        raise SystemExit(f"No extracted frames found for GIF: {frame_dir}")
    images = [Image.open(path).convert("RGBA") for path in frames]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    first, rest = images[0], images[1:]
    first.save(
        output_path,
        save_all=True,
        append_images=rest,
        duration=frame_ms,
        loop=0,
        disposal=2,
    )


def build_comparison_contact(review_root: Path, model_contacts: list[tuple[str, Path]]) -> None:
    if not model_contacts:
        return
    font = ImageFont.load_default()
    padding = 24
    label_height = 20
    images = [(label, Image.open(path).convert("RGBA")) for label, path in model_contacts]
    total_width = sum(img.width for _, img in images) + (padding * (len(images) - 1))
    max_height = max(img.height for _, img in images)
    canvas = Image.new("RGBA", (total_width, max_height + label_height), (20, 20, 20, 255))
    draw = ImageDraw.Draw(canvas)

    x = 0
    for label, img in images:
        canvas.paste(img, (x, label_height))
        draw.rectangle([x, 0, x + img.width, label_height], fill=(0, 0, 0, 220))
        draw.text((x + 6, 4), label, fill=(255, 255, 255, 255), font=font)
        x += img.width + padding

    out_path = review_root / "comparison_contact.png"
    canvas.save(out_path)


def build_review_for_model(
    clip_name: str,
    model: str,
    clip_cfg: dict,
    global_cfg: dict,
    run_id: str,
) -> Path:
    video_root = _abs(str(clip_cfg.get("video_dir") or "").strip())
    review_root = _abs(str(clip_cfg.get("review_dir") or "").strip())
    if not str(clip_cfg.get("video_dir") or "").strip():
        raise SystemExit(f"{clip_name}.video_dir is required")
    if not str(clip_cfg.get("review_dir") or "").strip():
        raise SystemExit(f"{clip_name}.review_dir is required")

    slug = model_slug(model)
    video_path = video_root / run_id / slug / f"{clip_name}.mp4"
    if not video_path.exists():
        raise SystemExit(f"Missing generated video: {video_path}")

    review_dir = review_root / run_id / slug
    full_frames_dir = review_dir / "frames_full"
    clear_pngs(full_frames_dir)

    review_fps = int(global_cfg.get("review_fps") or 12)
    gif_frame_ms = int(global_cfg.get("gif_frame_ms") or 83)
    contact_cols = int(global_cfg.get("contact_cols") or 10)
    contact_scale = float(global_cfg.get("contact_scale") or 1.0)
    if review_fps <= 0:
        raise SystemExit("global.review_fps must be > 0")
    if gif_frame_ms <= 0:
        raise SystemExit("global.gif_frame_ms must be > 0")

    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-vf",
            f"fps={review_fps}",
            str(full_frames_dir / "frame_%03d.png"),
        ],
        batch=False,
    )

    contact_path = review_dir / "contact.png"
    run(
        [
            "python3",
            "scripts/make_contact_sheet.py",
            "--input",
            str(full_frames_dir),
            "--output",
            str(contact_path),
            "--cols",
            str(contact_cols),
            "--scale",
            str(contact_scale),
        ]
    )

    create_gif_from_frames(full_frames_dir, review_dir / "full.gif", gif_frame_ms)

    windows = clip_cfg.get("window")
    if not isinstance(windows, list) or not windows:
        raise SystemExit(f"{clip_name} must define at least one [[clip.{clip_name}.window]] block")
    for window in windows:
        if not isinstance(window, dict):
            raise SystemExit(f"{clip_name}.window entries must be tables")
        name = str(window.get("name") or "").strip()
        start = str(window.get("start") or "").strip()
        end = str(window.get("end") or "").strip()
        if not name or not start or not end:
            raise SystemExit(f"{clip_name}.window entries require name/start/end")

        window_dir = review_dir / f"frames_{name}"
        clear_pngs(window_dir)
        run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(video_path),
                "-ss",
                start,
                "-to",
                end,
                "-vf",
                f"fps={review_fps}",
                str(window_dir / "frame_%03d.png"),
            ],
            batch=False,
        )
        create_gif_from_frames(window_dir, review_dir / f"{name}.gif", gif_frame_ms)

    return contact_path


def main() -> int:
    args = parse_args()
    config_path = _abs(args.config)
    global_cfg, clip_cfgs = load_config(config_path)
    clip_cfg = clip_cfgs[args.clip]
    if not isinstance(clip_cfg, dict):
        raise SystemExit(f"clip.{args.clip} must be a table")

    requested_steps = [args.make_videos, args.make_review]
    if any(requested_steps) and sum(1 for flag in requested_steps if flag) != 1:
        raise SystemExit("Choose at most one of --make-videos or --make-review (or none for both).")

    if args.make_review and not args.run_id:
        raise SystemExit("--run-id is required with --make-review")

    start_image = _abs(str(clip_cfg.get("start_image") or "").strip())
    end_image = _abs(str(clip_cfg.get("end_image") or "").strip())
    prompt = str(clip_cfg.get("prompt") or "").strip()
    duration = str(clip_cfg.get("duration") or "").strip()
    resolution = str(clip_cfg.get("resolution") or "").strip()
    aspect_ratio = str(clip_cfg.get("aspect_ratio") or "").strip()
    video_dir = _abs(str(clip_cfg.get("video_dir") or "").strip())
    review_dir = _abs(str(clip_cfg.get("review_dir") or "").strip())
    models = clip_cfg.get("models")

    if not start_image.exists():
        raise SystemExit(f"Start image not found: {start_image}")
    if not end_image.exists():
        raise SystemExit(f"End image not found: {end_image}")
    if not prompt:
        raise SystemExit(f"clip.{args.clip}.prompt is required")
    if not duration:
        raise SystemExit(f"clip.{args.clip}.duration is required")
    if not resolution:
        raise SystemExit(f"clip.{args.clip}.resolution is required")
    if not str(clip_cfg.get("video_dir") or "").strip():
        raise SystemExit(f"clip.{args.clip}.video_dir is required")
    if not str(clip_cfg.get("review_dir") or "").strip():
        raise SystemExit(f"clip.{args.clip}.review_dir is required")
    if not isinstance(models, list) or not models:
        raise SystemExit(f"clip.{args.clip}.models must be a non-empty list")
    for model in models:
        if model not in SUPPORTED_MODELS:
            raise SystemExit(f"Unsupported model in clip.{args.clip}.models: {model}")

    run_id = args.run_id or time.strftime("%Y%m%d_%H%M%S")

    if args.make_review:
        contact_paths: list[tuple[str, Path]] = []
        for model in models:
            label = model_slug(model)
            contact_paths.append((label, build_review_for_model(args.clip, model, clip_cfg, global_cfg, run_id)))
        build_comparison_contact(review_dir / run_id, contact_paths)
        open_folder(review_dir / run_id)
        return 0

    ensure_dir(video_dir / run_id)
    ensure_dir(review_dir / run_id)

    def submit_model(model: str) -> None:
        slug = model_slug(model)
        out_dir = video_dir / run_id / slug
        ensure_dir(out_dir)
        cmd = [
            "python3",
            "scripts/fal_video_generate.py",
            "--model",
            model,
            "--image",
            str(start_image),
            "--end-image",
            str(end_image),
            "--prompt",
            prompt,
            "--resolution",
            resolution,
            "--duration",
            duration,
            "--output-dir",
            str(out_dir),
            "--output-name",
            f"{args.clip}.mp4",
        ]
        if aspect_ratio and SUPPORTED_MODELS[model]["supports_aspect_ratio"]:
            cmd += ["--aspect-ratio", aspect_ratio]
        run(cmd)

    with ThreadPoolExecutor(max_workers=max(1, int(args.parallel))) as executor:
        futures = [executor.submit(submit_model, model) for model in models]
        for future in as_completed(futures):
            future.result()

    contact_paths: list[tuple[str, Path]] = []
    for model in models:
        label = model_slug(model)
        contact_paths.append((label, build_review_for_model(args.clip, model, clip_cfg, global_cfg, run_id)))
    build_comparison_contact(review_dir / run_id, contact_paths)
    open_folder(review_dir / run_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
