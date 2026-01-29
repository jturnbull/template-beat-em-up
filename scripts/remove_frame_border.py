#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from PIL import Image, ImageDraw


def parse_hex_color(value: str) -> tuple[int, int, int, int]:
    cleaned = value.strip().lstrip("#")
    if len(cleaned) != 6:
        raise ValueError(f"Expected 6-digit hex color, got: {value}")
    r = int(cleaned[0:2], 16)
    g = int(cleaned[2:4], 16)
    b = int(cleaned[4:6], 16)
    return (r, g, b, 255)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Folder with source PNG frames")
    parser.add_argument("--thickness", type=int, default=2, help="Border thickness in pixels")
    parser.add_argument("--fill", default="#00b140", help="Fill color to overwrite border")
    args = parser.parse_args()

    input_dir = Path(args.input)
    if not input_dir.exists():
        raise SystemExit(f"Input folder not found: {input_dir}")

    thickness = max(0, int(args.thickness))
    fill = parse_hex_color(args.fill)

    for path in sorted(input_dir.glob("*.png")):
        img = Image.open(path).convert("RGBA")
        w, h = img.size
        if thickness <= 0 or w == 0 or h == 0:
            continue
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, 0, w - 1, thickness - 1], fill=fill)
        draw.rectangle([0, h - thickness, w - 1, h - 1], fill=fill)
        draw.rectangle([0, 0, thickness - 1, h - 1], fill=fill)
        draw.rectangle([w - thickness, 0, w - 1, h - 1], fill=fill)
        tmp = path.with_suffix(".tmp.png")
        img.save(tmp)
        tmp.replace(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
