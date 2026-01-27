#!/usr/bin/env python3
"""Generate reskin images for a task using fal.ai (image-only, nano-banana-pro/edit)."""
from __future__ import annotations

import argparse
import os
import re
import time
import urllib.request
from pathlib import Path
from typing import Optional

import fal_client

# --------------------------------------------------------------------------------------
# Project-specific defaults (reskin pipeline)
# --------------------------------------------------------------------------------------

MODEL = "fal-ai/nano-banana-pro/edit"
OUTPUT_FORMAT = "png"
NUM_IMAGES = 3
RESOLUTION = "4K"
REF_DIR = "source_images"
POLL_SECONDS = 2.0
ALLOWED_ASPECT_RATIOS = {
    "21:9": 21 / 9,
    "16:9": 16 / 9,
    "3:2": 3 / 2,
    "4:3": 4 / 3,
    "5:4": 5 / 4,
    "1:1": 1.0,
    "4:5": 4 / 5,
    "3:4": 3 / 4,
    "2:3": 2 / 3,
    "9:16": 9 / 16,
}


# --------------------------------------------------------------------------------------


def find_project_root(start: Path) -> Path:
    current = start.resolve()
    for parent in [current] + list(current.parents):
        if (parent / "project.godot").exists():
            return parent
    return start.resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True, help="Path to a task .md file")
    parser.add_argument("--prompt", default=None, help="Override prompt text")
    parser.add_argument("--negative", default=None, help="Override negative prompt")
    parser.add_argument("--num-images", type=int, default=NUM_IMAGES, help="Number of images")
    parser.add_argument(
        "--aspect-ratio",
        default=None,
        help="Override aspect ratio (auto, 21:9, 16:9, 3:2, 4:3, 5:4, 1:1, 4:5, 3:4, 2:3, 9:16)",
    )
    parser.add_argument("--ref", action="append", default=[], help="Additional reference image (repeatable)")
    parser.add_argument("--ref-dir", default=None, help="Directory of reference images to add")
    parser.add_argument("--output-dir", default="outputs/fal", help="Where to save images")
    parser.add_argument("--no-download", action="store_true", help="Skip downloading images")
    parser.add_argument("--poll", type=float, default=POLL_SECONDS, help="Polling interval seconds")
    return parser.parse_args()


def parse_task(task_path: Path) -> dict:
    text = task_path.read_text(encoding="utf-8")
    data = {}
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("Source:"):
            data["source"] = line.split(":", 1)[1].strip()
        if line.startswith("- Prompt:"):
            data["prompt"] = line.split(":", 1)[1].strip()
        if line.startswith("- Negative Prompt:"):
            data["negative"] = line.split(":", 1)[1].strip()
        if line.startswith("- Reference Images:"):
            data["references"] = line.split(":", 1)[1].strip()
        if line.startswith("Size(px):"):
            data["size"] = line.split(":", 1)[1].strip()
    return data


def resolve_prompt(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if value.strip().upper() == "TBD" or value.strip() == "":
        return None
    return value


def resolve_reference_list(value: Optional[str]) -> list[str]:
    if not value:
        return []
    cleaned = value.strip()
    if cleaned.upper() == "TBD":
        return []
    parts = re.split(r"[;,]", cleaned)
    return [p.strip() for p in parts if p.strip()]


def parse_size(size_value: Optional[str]) -> Optional[tuple[int, int]]:
    if not size_value:
        return None
    cleaned = size_value.strip()
    if cleaned.upper() == "TBD" or cleaned == "":
        return None
    match = re.match(r"^(\d+)x(\d+)$", cleaned)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def nearest_aspect_ratio(width: int, height: int) -> str:
    ratio = width / height
    best = "1:1"
    best_delta = float("inf")
    for key, value in ALLOWED_ASPECT_RATIOS.items():
        delta = abs(ratio - value)
        if delta < best_delta:
            best_delta = delta
            best = key
    return best


def download_file(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as response:
        dest.write_bytes(response.read())


def main() -> int:
    args = parse_args()
    if "FAL_KEY" not in os.environ:
        raise SystemExit("FAL_KEY is not set in the environment.")

    task_path = Path(args.task)
    if not task_path.exists():
        raise SystemExit(f"Task file not found: {task_path}")

    task = parse_task(task_path)
    source = task.get("source")
    if not source:
        raise SystemExit("Task file missing Source: entry")

    project_root = find_project_root(Path(__file__).resolve())
    source_path = (project_root / source).resolve()
    if not source_path.exists():
        raise SystemExit(f"Source asset not found: {source}")

    prompt = resolve_prompt(args.prompt) or resolve_prompt(task.get("prompt"))
    if not prompt:
        raise SystemExit("No prompt provided. Use --prompt or set - Prompt: in the task file.")
    negative = resolve_prompt(args.negative) or resolve_prompt(task.get("negative"))

    task_size = parse_size(task.get("size"))
    if args.aspect_ratio:
        aspect_ratio = args.aspect_ratio
    elif task_size:
        aspect_ratio = nearest_aspect_ratio(task_size[0], task_size[1])
    else:
        aspect_ratio = "auto"

    base_image_url = fal_client.upload_file(str(source_path))

    reference_paths: list[Path] = []
    for ref in args.ref:
        ref_path = Path(ref).expanduser()
        if not ref_path.is_absolute():
            ref_path = (Path.cwd() / ref_path).resolve()
        reference_paths.append(ref_path)

    ref_dir = args.ref_dir
    if not ref_dir:
        default_ref_dir = (project_root / REF_DIR).resolve()
        if default_ref_dir.exists():
            ref_dir = str(default_ref_dir)

    if ref_dir:
        ref_dir_path = Path(ref_dir).expanduser()
        if not ref_dir_path.is_absolute():
            ref_dir_path = (Path.cwd() / ref_dir_path).resolve()
        if ref_dir_path.exists():
            for p in sorted(ref_dir_path.iterdir()):
                if p.suffix.lower() in {".png", ".jpg", ".jpeg"}:
                    reference_paths.append(p)

    task_refs = resolve_reference_list(task.get("references"))
    for ref in task_refs:
        ref_path = Path(ref).expanduser()
        if not ref_path.is_absolute():
            ref_path = (project_root / ref_path).resolve()
        reference_paths.append(ref_path)

    reference_urls = []
    for ref_path in reference_paths:
        if not ref_path.exists():
            print(f"Warning: reference not found: {ref_path}")
            continue
        reference_urls.append(fal_client.upload_file(str(ref_path)))

    arguments = {
        "prompt": prompt,
        "image_urls": [base_image_url] + reference_urls,
        "num_images": args.num_images,
        "output_format": OUTPUT_FORMAT,
        "reference_image_url": base_image_url,
    }
    if negative:
        arguments["negative_prompt"] = negative
    if RESOLUTION:
        arguments["resolution"] = RESOLUTION
    if aspect_ratio:
        arguments["aspect_ratio"] = aspect_ratio

    handler = fal_client.submit(MODEL, arguments=arguments)
    request_id = handler.request_id
    print(f"Submitted {request_id}")

    while True:
        status = fal_client.status(MODEL, request_id, with_logs=False)
        if isinstance(status, fal_client.Completed):
            result = fal_client.result(MODEL, request_id)
            images = result.get("images", [])
            if not images:
                raise SystemExit("No images in result")
            print(f"Completed: {len(images)} image(s)")
            if not args.no_download:
                out_dir = Path(args.output_dir)
                for i, item in enumerate(images, start=1):
                    url = item.get("url")
                    if not url:
                        continue
                    out_path = out_dir / task_path.stem / f"option_{i}.{OUTPUT_FORMAT}"
                    download_file(url, out_path)
                    print(f"Saved {out_path}")
            break
        if isinstance(status, fal_client.Queued):
            time.sleep(args.poll)
            continue
        if isinstance(status, fal_client.InProgress):
            time.sleep(args.poll)
            continue
        time.sleep(args.poll)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
