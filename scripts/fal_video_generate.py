#!/usr/bin/env python3
"""Generate an animation clip with fal-ai/kling-video/v2.6/pro/image-to-video."""
from __future__ import annotations

import argparse
import os
import subprocess
import time
import urllib.request
from pathlib import Path

import fal_client

MODEL = "fal-ai/kling-video/v2.6/pro/image-to-video"
DEFAULT_RESOLUTION = "1080p"
DEFAULT_DURATION = "5"
DEFAULT_NEGATIVE = "low resolution, error, worst quality, low quality, defects"
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
    parser.add_argument("--image", required=True, help="Path to base image (anchor still)")
    parser.add_argument("--prompt", required=True, help="Video prompt")
    parser.add_argument("--negative", default=DEFAULT_NEGATIVE, help="Negative prompt")
    parser.add_argument("--resolution", default=DEFAULT_RESOLUTION, help="Resolution (e.g., 1080p)")
    parser.add_argument("--duration", default=DEFAULT_DURATION, help="Duration in seconds")
    parser.add_argument(
        "--preset",
        choices=sorted(PRESET_CONSTRAINTS.keys()),
        default=None,
        help="Append a preset constraint block to the prompt",
    )
    parser.add_argument("--constraints", default=None, help="Append custom constraints to the prompt")
    parser.add_argument("--output-dir", default="outputs/fal/video", help="Output directory")
    parser.add_argument("--no-download", action="store_true", help="Skip downloading video")
    parser.add_argument("--max-bytes", type=int, default=MAX_UPLOAD_BYTES, help="Max upload size in bytes")
    parser.add_argument("--max-dim", type=int, default=DEFAULT_MAX_DIM, help="Resize max dimension if too large")
    parser.add_argument("--poll", type=float, default=POLL_SECONDS, help="Polling interval seconds")
    return parser.parse_args()


def download_file(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as response:
        dest.write_bytes(response.read())


def ensure_size_limit(image_path: Path, max_bytes: int, max_dim: int) -> Path:
    if image_path.stat().st_size <= max_bytes:
        return image_path
    # Create resized PNG to reduce size; shrink dimensions until under limit.
    tmp_dir = image_path.parent / "_resized"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    current_dim = max_dim
    for _ in range(6):
        out_path = tmp_dir / f"{image_path.stem}_max{current_dim}.png"
        cmd = [
            "sips",
            "-Z",
            str(current_dim),
            "-s",
            "format",
            "png",
            str(image_path),
            "--out",
            str(out_path),
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if out_path.exists() and out_path.stat().st_size <= max_bytes:
            return out_path
        current_dim = int(current_dim * 0.85)
        if current_dim < 256:
            break
    raise SystemExit(
        "Resized PNG still exceeds max upload size. "
        "Reduce input dimensions or raise --max-bytes."
    )


def main() -> int:
    args = parse_args()
    if "FAL_KEY" not in os.environ:
        raise SystemExit("FAL_KEY is not set in the environment.")

    image_path = Path(args.image)
    if not image_path.exists():
        raise SystemExit(f"Image not found: {image_path}")

    safe_path = ensure_size_limit(image_path, args.max_bytes, args.max_dim)
    image_url = fal_client.upload_file(str(safe_path))

    prompt = args.prompt
    if args.preset:
        prompt = f"{prompt}. {PRESET_CONSTRAINTS[args.preset]}"
    if args.constraints:
        prompt = f"{prompt}. {args.constraints}"

    arguments = {
        "prompt": prompt,
        "image_url": image_url,
        "resolution": args.resolution,
        "duration": args.duration,
    }
    if args.negative:
        arguments["negative_prompt"] = args.negative

    handler = fal_client.submit(MODEL, arguments=arguments)
    request_id = handler.request_id
    print(f"Submitted {request_id}")

    while True:
        status = fal_client.status(MODEL, request_id, with_logs=False)
        if isinstance(status, fal_client.Completed):
            result = fal_client.result(MODEL, request_id)
            # Try common shapes: {"video": {"url": ...}} or {"videos": [{"url": ...}]}
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
                out_path = out_dir / f"{image_path.stem}.mp4"
                download_file(url, out_path)
                print(f"Saved {out_path}")
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
