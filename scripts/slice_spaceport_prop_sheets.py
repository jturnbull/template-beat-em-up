#!/usr/bin/env python3
"""Slice generated spaceport prop sheets into constituent prop PNGs."""
from __future__ import annotations

import argparse
import json
import re
from collections import deque
from pathlib import Path

from PIL import Image

DEFAULT_INPUT_GLOB = "outputs/reskin/_tmp/spaceport_props_*/spaceport_props_spritesheet_bg_removed/option_*.png"
DEFAULT_OUTPUT_ROOT = "outputs/reskin/_tmp/spaceport_props_sliced"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-glob",
        default=DEFAULT_INPUT_GLOB,
        help="Glob pattern for input sheets (default: %(default)s)",
    )
    parser.add_argument(
        "--output-root",
        default=DEFAULT_OUTPUT_ROOT,
        help="Root directory for sliced outputs (default: %(default)s)",
    )
    parser.add_argument(
        "--alpha-threshold",
        type=int,
        default=16,
        help="Pixel considered foreground if alpha >= threshold (0-255).",
    )
    parser.add_argument(
        "--min-area",
        type=int,
        default=96,
        help="Discard connected components smaller than this many pixels.",
    )
    parser.add_argument(
        "--min-width",
        type=int,
        default=6,
        help="Discard connected components narrower than this many pixels.",
    )
    parser.add_argument(
        "--min-height",
        type=int,
        default=6,
        help="Discard connected components shorter than this many pixels.",
    )
    parser.add_argument(
        "--pad",
        type=int,
        default=2,
        help="Extra transparent padding around each crop.",
    )
    return parser.parse_args()


def find_input_sheets(input_glob: str) -> list[Path]:
    sheets = sorted(Path(".").glob(input_glob))
    if not sheets:
        raise SystemExit(f"No input sheets found for glob: {input_glob}")
    for sheet in sheets:
        if not sheet.exists():
            raise SystemExit(f"Missing input sheet: {sheet}")
    return sheets


def connected_components(alpha: Image.Image, threshold: int) -> list[tuple[int, int, int, int, int]]:
    width, height = alpha.size
    data = alpha.tobytes()
    visited = bytearray(width * height)
    components: list[tuple[int, int, int, int, int]] = []

    def idx(x: int, y: int) -> int:
        return y * width + x

    for y in range(height):
        for x in range(width):
            i = idx(x, y)
            if visited[i] or data[i] < threshold:
                continue

            queue: deque[tuple[int, int]] = deque()
            queue.append((x, y))
            visited[i] = 1

            min_x = x
            min_y = y
            max_x = x
            max_y = y
            area = 0

            while queue:
                cx, cy = queue.popleft()
                area += 1
                if cx < min_x:
                    min_x = cx
                if cy < min_y:
                    min_y = cy
                if cx > max_x:
                    max_x = cx
                if cy > max_y:
                    max_y = cy

                if cx > 0:
                    nx, ny = cx - 1, cy
                    ni = idx(nx, ny)
                    if not visited[ni] and data[ni] >= threshold:
                        visited[ni] = 1
                        queue.append((nx, ny))
                if cx + 1 < width:
                    nx, ny = cx + 1, cy
                    ni = idx(nx, ny)
                    if not visited[ni] and data[ni] >= threshold:
                        visited[ni] = 1
                        queue.append((nx, ny))
                if cy > 0:
                    nx, ny = cx, cy - 1
                    ni = idx(nx, ny)
                    if not visited[ni] and data[ni] >= threshold:
                        visited[ni] = 1
                        queue.append((nx, ny))
                if cy + 1 < height:
                    nx, ny = cx, cy + 1
                    ni = idx(nx, ny)
                    if not visited[ni] and data[ni] >= threshold:
                        visited[ni] = 1
                        queue.append((nx, ny))

            components.append((min_x, min_y, max_x, max_y, area))
    return components


def parse_run_id(sheet: Path) -> str:
    match = re.search(r"(spaceport_props_\d{8}_\d{6})", str(sheet))
    if not match:
        raise SystemExit(f"Could not parse run id from path: {sheet}")
    return match.group(1)


def slice_sheet(
    sheet: Path,
    output_root: Path,
    threshold: int,
    min_area: int,
    min_w: int,
    min_h: int,
    pad: int,
) -> None:
    image = Image.open(sheet).convert("RGBA")
    alpha = image.getchannel("A")
    alpha_extrema = alpha.getextrema()
    if alpha_extrema[0] == 255:
        raise SystemExit(
            f"Sheet has no transparency: {sheet}\n"
            "Run background removal first, then slice the *_bg_removed outputs."
        )
    width, height = image.size
    components = connected_components(alpha, threshold)
    if not components:
        raise SystemExit(f"No foreground components found in sheet: {sheet}")

    filtered: list[tuple[int, int, int, int, int]] = []
    for min_x, min_y, max_x, max_y, area in components:
        comp_w = (max_x - min_x) + 1
        comp_h = (max_y - min_y) + 1
        if area < min_area:
            continue
        if comp_w < min_w or comp_h < min_h:
            continue
        filtered.append((min_x, min_y, max_x, max_y, area))

    if not filtered:
        raise SystemExit(
            f"All components filtered out in {sheet}. "
            f"Try lowering --min-area/--min-width/--min-height."
        )

    filtered.sort(key=lambda c: (c[1], c[0]))

    run_id = parse_run_id(sheet)
    option_name = sheet.stem
    out_dir = output_root / run_id / option_name
    if out_dir.exists():
        raise SystemExit(f"Refusing to overwrite existing directory: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=False)

    manifest_items = []
    for index, (min_x, min_y, max_x, max_y, area) in enumerate(filtered, start=1):
        x0 = max(0, min_x - pad)
        y0 = max(0, min_y - pad)
        x1 = min(width - 1, max_x + pad)
        y1 = min(height - 1, max_y + pad)
        crop = image.crop((x0, y0, x1 + 1, y1 + 1))
        out_name = f"prop_{index:03d}.png"
        out_path = out_dir / out_name
        crop.save(out_path)
        manifest_items.append(
            {
                "file": out_name,
                "bbox": [x0, y0, x1, y1],
                "size": [crop.width, crop.height],
                "pixel_area": area,
            }
        )

    manifest = {
        "source_sheet": str(sheet),
        "sheet_size": [width, height],
        "alpha_threshold": threshold,
        "min_area": min_area,
        "min_width": min_w,
        "min_height": min_h,
        "pad": pad,
        "component_count": len(manifest_items),
        "components": manifest_items,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"{sheet} -> {out_dir} ({len(manifest_items)} props)")


def main() -> int:
    args = parse_args()
    if args.alpha_threshold < 0 or args.alpha_threshold > 255:
        raise SystemExit("--alpha-threshold must be between 0 and 255")
    if args.min_area < 1:
        raise SystemExit("--min-area must be >= 1")
    if args.min_width < 1:
        raise SystemExit("--min-width must be >= 1")
    if args.min_height < 1:
        raise SystemExit("--min-height must be >= 1")
    if args.pad < 0:
        raise SystemExit("--pad must be >= 0")

    sheets = find_input_sheets(args.input_glob)
    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    for sheet in sheets:
        slice_sheet(
            sheet=sheet,
            output_root=output_root,
            threshold=args.alpha_threshold,
            min_area=args.min_area,
            min_w=args.min_width,
            min_h=args.min_height,
            pad=args.pad,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
