#!/usr/bin/env python3
"""Create a contact sheet with frame indices."""
from __future__ import annotations

import argparse
import math
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Folder with frames")
    parser.add_argument("--output", required=True, help="Output PNG path")
    parser.add_argument("--cols", type=int, default=10, help="Columns")
    parser.add_argument("--scale", type=float, default=1.0, help="Scale each frame")
    return parser.parse_args()


def frame_index(path: Path) -> int:
    match = re.search(r"(\d+)", path.stem)
    if match:
        return int(match.group(1))
    return 0


def main() -> int:
    args = parse_args()
    input_dir = Path(args.input)
    if not input_dir.exists():
        raise SystemExit(f"Input folder not found: {input_dir}")

    files = sorted([p for p in input_dir.iterdir() if p.suffix.lower() == ".png"], key=frame_index)
    if not files:
        raise SystemExit("No PNG frames found")

    images = [Image.open(p).convert("RGBA") for p in files]
    if args.scale != 1.0:
        images = [img.resize((int(img.width * args.scale), int(img.height * args.scale)), Image.NEAREST) for img in images]

    tile_w = max(img.width for img in images)
    tile_h = max(img.height for img in images)

    cols = max(1, args.cols)
    rows = math.ceil(len(images) / cols)

    sheet = Image.new("RGBA", (cols * tile_w, rows * tile_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()

    for idx, img in enumerate(images):
        row = idx // cols
        col = idx % cols
        x = col * tile_w
        y = row * tile_h
        sheet.paste(img, (x, y))
        label = f"{frame_index(files[idx]):03d}"
        draw.rectangle([x + 2, y + 2, x + 28, y + 16], fill=(0, 0, 0, 160))
        draw.text((x + 4, y + 3), label, fill=(255, 255, 255, 255), font=font)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
