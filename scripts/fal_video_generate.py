#!/usr/bin/env python3
"""Generate an animation clip with the project-standard fal.ai image-to-video model."""
from __future__ import annotations

import argparse
import os
import subprocess
import time
import urllib.request
from pathlib import Path

import fal_client
from PIL import Image

SUPPORTED_MODELS = {
    "bytedance/seedance-2.0/fast/image-to-video": {
        "start_field": "image_url",
        "end_field": "end_image_url",
        "supports_negative": False,
        "supports_aspect_ratio": True,
        "supported_resolutions": {"480p", "720p"},
    },
}
DEFAULT_RESOLUTION = "720p"
POLL_SECONDS = 2.0
MAX_UPLOAD_BYTES = 10_485_760
DEFAULT_MAX_DIM = 1024
PRESET_CONSTRAINTS = {
    "walk_horizontal": (
        "walks straight left-to-right on a flat horizontal ground line, "
        "no diagonal drift, feet stay on the same baseline, "
        "no camera movement or tilt, no zoom"
    )
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, choices=sorted(SUPPORTED_MODELS.keys()))
    parser.add_argument("--image", required=True, help="Path to base image (anchor still)")
    parser.add_argument(
        "--end-image",
        default="same",
        help="Path to end image, or 'same' to reuse start, or 'none' to omit end image",
    )
    parser.add_argument("--prompt", required=True, help="Video prompt")
    parser.add_argument("--negative", default=None, help="Negative prompt")
    parser.add_argument("--resolution", default=DEFAULT_RESOLUTION, help="Resolution (480p or 720p)")
    parser.add_argument("--duration", required=True, help="Duration in seconds")
    parser.add_argument(
        "--aspect-ratio",
        default=None,
        help="Aspect ratio for models that support it (e.g. auto, 16:9)",
    )
    parser.add_argument(
        "--preset",
        choices=sorted(PRESET_CONSTRAINTS.keys()),
        default=None,
        help="Append a preset constraint block to the prompt",
    )
    parser.add_argument("--constraints", default=None, help="Append custom constraints to the prompt")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--output-name", default=None, help="Output mp4 filename")
    parser.add_argument("--no-download", action="store_true", help="Skip downloading video")
    parser.add_argument("--max-bytes", type=int, default=MAX_UPLOAD_BYTES, help="Max upload size in bytes")
    parser.add_argument("--max-dim", type=int, default=DEFAULT_MAX_DIM, help="Resize max dimension if too large")
    parser.add_argument("--poll", type=float, default=POLL_SECONDS, help="Polling interval seconds")
    return parser.parse_args()


def download_file(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as response:
        dest.write_bytes(response.read())


def open_folder(path: Path) -> None:
    if os.environ.get("RESKIN_BATCH") == "1":
        return
    subprocess.run(["open", str(path)], check=True)


def ensure_size_limit(image_path: Path, max_bytes: int, max_dim: int) -> Path:
    if image_path.stat().st_size <= max_bytes:
        return image_path
    tmp_dir = image_path.parent / "_resized"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    current_dim = max_dim
    for _ in range(6):
        out_path = tmp_dir / f"{image_path.stem}_max{current_dim}.png"
        with Image.open(image_path) as src:
            src = src.convert("RGBA")
            resized = src.copy()
            resized.thumbnail((current_dim, current_dim), Image.LANCZOS)
            resized.save(out_path, format="PNG", optimize=True)
        if out_path.exists() and out_path.stat().st_size <= max_bytes:
            return out_path
        current_dim = int(current_dim * 0.85)
        if current_dim < 256:
            break
    raise SystemExit(
        "Resized PNG still exceeds max upload size. "
        "Reduce input dimensions or raise --max-bytes."
    )


def resolve_duration(_model: str, raw_duration: str, _end_image_mode: str) -> str:
    return raw_duration


def build_arguments(args: argparse.Namespace, image_url: str, end_image_url: str | None) -> dict:
    model_spec = SUPPORTED_MODELS[args.model]

    prompt = args.prompt
    if args.preset:
        prompt = f"{prompt}. {PRESET_CONSTRAINTS[args.preset]}"
    if args.constraints:
        prompt = f"{prompt}. {args.constraints}"

    if args.aspect_ratio and not model_spec["supports_aspect_ratio"]:
        raise SystemExit(f"Model {args.model} does not support --aspect-ratio")

    negative = (args.negative or "").strip()
    if negative and not model_spec["supports_negative"]:
        raise SystemExit(f"Model {args.model} does not support --negative")

    duration = resolve_duration(args.model, args.duration, args.end_image)

    supported_resolutions = model_spec["supported_resolutions"]
    if args.resolution not in supported_resolutions:
        allowed = ", ".join(sorted(supported_resolutions))
        raise SystemExit(f"Model {args.model} supports only: {allowed}")

    arguments = {
        "prompt": prompt,
        model_spec["start_field"]: image_url,
        "resolution": args.resolution,
        "duration": duration,
        "generate_audio": False,
    }

    if args.aspect_ratio:
        arguments["aspect_ratio"] = args.aspect_ratio
    if negative:
        arguments["negative_prompt"] = negative

    if end_image_url is None and args.end_image == "same":
        arguments[model_spec["end_field"]] = image_url
    elif end_image_url is not None:
        arguments[model_spec["end_field"]] = end_image_url

    return arguments


def main() -> int:
    args = parse_args()
    if "FAL_KEY" not in os.environ:
        raise SystemExit("FAL_KEY is not set in the environment.")

    image_path = Path(args.image)
    if not image_path.exists():
        raise SystemExit(f"Image not found: {image_path}")

    safe_path = ensure_size_limit(image_path, args.max_bytes, args.max_dim)
    image_url = fal_client.upload_file(str(safe_path))

    end_image_url = None
    if args.end_image and args.end_image != "same":
        if args.end_image == "none":
            end_image_url = None
        else:
            end_path = Path(args.end_image)
            if not end_path.exists():
                raise SystemExit(f"End image not found: {end_path}")
            safe_end = ensure_size_limit(end_path, args.max_bytes, args.max_dim)
            end_image_url = fal_client.upload_file(str(safe_end))

    arguments = build_arguments(args, image_url, end_image_url)

    handler = fal_client.submit(args.model, arguments=arguments)
    request_id = handler.request_id
    print(f"Submitted {request_id}")

    while True:
        status = fal_client.status(args.model, request_id, with_logs=False)
        if isinstance(status, fal_client.Completed):
            result = fal_client.result(args.model, request_id)
            url = None
            if isinstance(result, dict):
                if "video" in result and isinstance(result["video"], dict):
                    url = result["video"].get("url")
                if url is None and "videos" in result and result["videos"]:
                    url = result["videos"][0].get("url")
            if not url:
                raise SystemExit(f"No video URL in result: {result}")

            if not args.no_download:
                out_dir = Path(args.output_dir)
                ensure_name = args.output_name or f"{image_path.stem}.mp4"
                if not ensure_name.endswith(".mp4"):
                    raise SystemExit("--output-name must end with .mp4")
                out_path = out_dir / ensure_name
                if out_path.exists():
                    raise SystemExit(
                        f"Refusing to overwrite existing output: {out_path}\n"
                        "Choose a fresh output name or fresh output dir."
                    )
                download_file(url, out_path)
                print(f"Saved {out_path}")
                open_folder(out_dir)
            else:
                print(f"Video URL: {url}")
            break
        if isinstance(status, (fal_client.Queued, fal_client.InProgress)):
            time.sleep(args.poll)
            continue
        time.sleep(args.poll)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
