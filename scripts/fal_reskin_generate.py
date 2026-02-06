#!/usr/bin/env python3
"""Generate reskin images for a task using fal.ai (image-only)."""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Optional

import fal_client
from PIL import Image

# --------------------------------------------------------------------------------------
# Project-specific defaults (reskin pipeline)
# --------------------------------------------------------------------------------------

OUTPUT_FORMAT = "png"
NUM_IMAGES = 4
RESOLUTION = "4K"
REF_DIR = None
DEFAULT_NEGATIVE = "blurry, cropped, background, watermark, extra limbs, multiple characters"
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
    parser.add_argument("--model", default=None, help="Fal model id (overrides task file)")
    parser.add_argument("--num-images", type=int, default=NUM_IMAGES, help="Number of images")
    parser.add_argument(
        "--aspect-ratio",
        default=None,
        help="Override aspect ratio (auto, 21:9, 16:9, 3:2, 4:3, 5:4, 1:1, 4:5, 3:4, 2:3, 9:16)",
    )
    parser.add_argument("--ref", action="append", default=[], help="Additional reference image (repeatable)")
    parser.add_argument("--ref-dir", default=None, help="Directory of reference images to add")
    parser.add_argument("--output-dir", default="outputs/reskin/_tmp", help="Where to save images")
    parser.add_argument("--no-download", action="store_true", help="Skip downloading images")
    parser.add_argument(
        "--alpha-from-source",
        action="store_true",
        help="Apply the source asset alpha channel to downloaded images (preserves transparency for drop-in).",
    )
    parser.add_argument("--poll", type=float, default=POLL_SECONDS, help="Polling interval seconds")
    return parser.parse_args()


def parse_task(task_path: Path) -> dict:
    text = task_path.read_text(encoding="utf-8")
    data = {}
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("Source:"):
            data["source"] = line.split(":", 1)[1].strip()
        if line.startswith("- Model:"):
            data["model"] = line.split(":", 1)[1].strip()
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


def resolve_model(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = value.strip()
    if cleaned.upper() == "TBD" or cleaned == "":
        return None
    return cleaned


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


def resize_to_task_size(image_path: Path, task_size: tuple[int, int]) -> None:
    img = Image.open(image_path).convert("RGBA")
    if img.size == task_size:
        return
    img.resize(task_size, Image.LANCZOS).save(image_path)


def apply_alpha_from_source(source_path: Path, image_path: Path) -> None:
    source = Image.open(source_path).convert("RGBA")
    dest = Image.open(image_path).convert("RGBA")
    if source.size != dest.size:
        raise SystemExit(
            f"Alpha source size mismatch for {image_path.name}: expected {source.size}, got {dest.size}."
        )
    dest.putalpha(source.getchannel("A"))
    dest.save(image_path)


def maybe_open(path: Path) -> None:
    if os.environ.get("RESKIN_BATCH") == "1":
        return
    subprocess.run(["open", str(path)], check=True)


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

    model = resolve_model(args.model) or resolve_model(task.get("model"))
    if not model:
        raise SystemExit("No model provided. Use --model or set - Model: in the task file.")

    project_root = find_project_root(Path(__file__).resolve())
    source_path = (project_root / source).resolve()
    if not source_path.exists():
        raise SystemExit(f"Source asset not found: {source}")

    prompt = resolve_prompt(args.prompt) or resolve_prompt(task.get("prompt"))
    if not prompt:
        raise SystemExit("No prompt provided. Use --prompt or set - Prompt: in the task file.")
    negative = resolve_prompt(args.negative) or resolve_prompt(task.get("negative")) or DEFAULT_NEGATIVE

    task_size = parse_size(task.get("size"))
    if task_size:
        source_size = Image.open(source_path).size
        if source_size != task_size:
            raise SystemExit(
                f"Task Size(px) does not match source asset size: task={task_size}, source={source_size} ({source})."
            )
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
        if not ref_path.exists():
            raise SystemExit(f"Reference not found: {ref_path}")
        if not ref_path.is_file():
            raise SystemExit(f"Reference is not a file: {ref_path}")
        reference_paths.append(ref_path)

    ref_dir = args.ref_dir
    if ref_dir:
        ref_dir_path = Path(ref_dir).expanduser()
        if not ref_dir_path.is_absolute():
            ref_dir_path = (Path.cwd() / ref_dir_path).resolve()
        if not ref_dir_path.exists():
            raise SystemExit(f"Reference dir not found: {ref_dir_path}")
        if not ref_dir_path.is_dir():
            raise SystemExit(f"Reference dir is not a directory: {ref_dir_path}")
        refs = []
        for p in sorted(ref_dir_path.iterdir()):
            if p.suffix.lower() in {".png", ".jpg", ".jpeg"}:
                refs.append(p)
        if not refs:
            raise SystemExit(f"Reference dir contains no images: {ref_dir_path}")
        reference_paths.extend(refs)

    task_refs = resolve_reference_list(task.get("references"))
    for ref in task_refs:
        ref_path = Path(ref).expanduser()
        if not ref_path.is_absolute():
            ref_path = (project_root / ref_path).resolve()
        if not ref_path.exists():
            raise SystemExit(f"Reference not found: {ref_path}")
        if not ref_path.is_file():
            raise SystemExit(f"Reference is not a file: {ref_path}")
        reference_paths.append(ref_path)

    reference_urls = []
    for ref_path in reference_paths:
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

    handler = fal_client.submit(model, arguments=arguments)
    request_id = handler.request_id
    print(f"Submitted {request_id}")

    while True:
        status = fal_client.status(model, request_id, with_logs=False)
        if isinstance(status, fal_client.Completed):
            result = fal_client.result(model, request_id)
            images = result.get("images", [])
            if not images:
                raise SystemExit("No images in result")
            print(f"Completed: {len(images)} image(s)")
            if not args.no_download:
                out_dir = Path(args.output_dir)
                task_dir = out_dir / task_path.stem
                for i, item in enumerate(images, start=1):
                    url = item.get("url")
                    if not url:
                        continue
                    out_path = task_dir / f"option_{i}.{OUTPUT_FORMAT}"
                    if out_path.exists():
                        raise SystemExit(
                            f"Refusing to overwrite existing output: {out_path}\n"
                            "Choose a fresh --output-dir (recommended: a new timestamped folder)."
                        )
                    download_file(url, out_path)
                    if task_size:
                        resize_to_task_size(out_path, task_size)
                    if args.alpha_from_source:
                        apply_alpha_from_source(source_path, out_path)
                    print(f"Saved {out_path}")
                maybe_open(task_dir)
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
