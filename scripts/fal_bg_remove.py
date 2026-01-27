#!/usr/bin/env python3
"""Remove background using fal-ai/bria/background/remove."""
from __future__ import annotations

import argparse
import os
import time
import urllib.request
from pathlib import Path

import fal_client

MODEL = "fal-ai/bria/background/remove"
POLL_SECONDS = 2.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Image file or directory")
    parser.add_argument("--output-dir", default="outputs/fal/bg_removed", help="Output directory")
    parser.add_argument("--no-download", action="store_true", help="Skip downloading images")
    parser.add_argument("--poll", type=float, default=POLL_SECONDS, help="Polling interval seconds")
    return parser.parse_args()


def download_file(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as response:
        dest.write_bytes(response.read())


def iter_images(path: Path) -> list[Path]:
    if path.is_dir():
        return [p for p in sorted(path.iterdir()) if p.suffix.lower() in {".png", ".jpg", ".jpeg"}]
    return [path]


def main() -> int:
    args = parse_args()
    if "FAL_KEY" not in os.environ:
        raise SystemExit("FAL_KEY is not set in the environment.")

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Input not found: {input_path}")

    for image_path in iter_images(input_path):
        image_url = fal_client.upload_file(str(image_path))
        handler = fal_client.submit(MODEL, arguments={"image_url": image_url})
        request_id = handler.request_id
        print(f"Submitted {request_id} for {image_path.name}")

        while True:
            status = fal_client.status(MODEL, request_id, with_logs=False)
            if isinstance(status, fal_client.Completed):
                result = fal_client.result(MODEL, request_id)
                url = None
                if isinstance(result, dict):
                    if "image" in result and isinstance(result["image"], dict):
                        url = result["image"].get("url")
                    if url is None and "images" in result and result["images"]:
                        url = result["images"][0].get("url")
                if not url:
                    raise SystemExit(f"No image URL in result: {result}")

                if not args.no_download:
                    out_dir = Path(args.output_dir)
                    out_path = out_dir / f"{image_path.stem}.png"
                    download_file(url, out_path)
                    print(f"Saved {out_path}")
                else:
                    print(f"Image URL: {url}")
                break
            if isinstance(status, (fal_client.Queued, fal_client.InProgress)):
                time.sleep(args.poll)
                continue
            time.sleep(args.poll)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
