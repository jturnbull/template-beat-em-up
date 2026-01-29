#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import time
import urllib.request
from pathlib import Path
from io import BytesIO
from PIL import Image, ImageDraw

import fal_client


def parse_hex_color(value: str) -> tuple[int, int, int, int]:
    cleaned = value.strip().lstrip("#")
    if len(cleaned) != 6:
        raise ValueError(f"Expected 6-digit hex color, got: {value}")
    r = int(cleaned[0:2], 16)
    g = int(cleaned[2:4], 16)
    b = int(cleaned[4:6], 16)
    return (r, g, b, 255)


def visible_bbox(img: Image.Image, key_color: tuple[int, int, int], tol: int) -> tuple[int, int, int, int] | None:
    pixels = img.get_flattened_data()
    mask = Image.new("L", img.size, 0)
    out = []
    key_r, key_g, key_b = key_color
    for r, g, b, a in pixels:
        if a == 0:
            out.append(0)
            continue
        if abs(r - key_r) <= tol and abs(g - key_g) <= tol and abs(b - key_b) <= tol:
            out.append(0)
        else:
            out.append(255)
    mask.putdata(out)
    return mask.getbbox()


def median_color(pixels: list[tuple[int, int, int]]) -> tuple[int, int, int]:
    rs = sorted(p[0] for p in pixels)
    gs = sorted(p[1] for p in pixels)
    bs = sorted(p[2] for p in pixels)
    mid = len(rs) // 2
    return (rs[mid], gs[mid], bs[mid])


def remove_bg_with_fal(path: Path, poll: float = 2.0) -> Image.Image:
    if "FAL_KEY" not in os.environ:
        raise SystemExit("FAL_KEY is not set; required for background removal.")
    image_url = fal_client.upload_file(str(path))
    handler = fal_client.submit("fal-ai/bria/background/remove", arguments={"image_url": image_url})
    request_id = handler.request_id
    while True:
        status = fal_client.status("fal-ai/bria/background/remove", request_id, with_logs=False)
        if isinstance(status, fal_client.Completed):
            result = fal_client.result("fal-ai/bria/background/remove", request_id)
            url = None
            if isinstance(result, dict):
                if "image" in result and isinstance(result["image"], dict):
                    url = result["image"].get("url")
                if url is None and "images" in result and result["images"]:
                    url = result["images"][0].get("url")
            if not url:
                raise SystemExit(f"No image URL in result: {result}")
            with urllib.request.urlopen(url) as response:
                data = response.read()
            return Image.open(BytesIO(data)).convert("RGBA")
        if isinstance(status, (fal_client.Queued, fal_client.InProgress)):
            time.sleep(poll)
            continue
        time.sleep(poll)


def ensure_transparency(img: Image.Image, tol: int = 12) -> Image.Image:
    # Remove a solid background color by flood-filling from the corners.
    w, h = img.size
    sample = []
    band = max(1, min(w, h) // 30)
    corners = [
        (0, 0, band, band),
        (w - band, 0, w, band),
        (0, h - band, band, h),
        (w - band, h - band, w, h),
    ]
    px = img.load()
    for x0, y0, x1, y1 in corners:
        for y in range(y0, y1):
            for x in range(x0, x1):
                r, g, b, a = px[x, y]
                sample.append((r, g, b))
    if not sample:
        return img
    bg = median_color(sample)
    bg_r, bg_g, bg_b = bg

    def near_bg(r: int, g: int, b: int) -> bool:
        dr = r - bg_r
        dg = g - bg_g
        db = b - bg_b
        return (dr * dr + dg * dg + db * db) ** 0.5 <= tol

    visited = [[False] * w for _ in range(h)]
    stack = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
    while stack:
        x, y = stack.pop()
        if x < 0 or y < 0 or x >= w or y >= h:
            continue
        if visited[y][x]:
            continue
        visited[y][x] = True
        r, g, b, a = px[x, y]
        if not near_bg(r, g, b):
            continue
        # mark as background and expand
        px[x, y] = (r, g, b, 0)
        stack.extend([(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)])

    return img


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="outputs/fal/idle_00/option_1.png",
        help="Source image (default: outputs/fal/idle_00/option_1.png)",
    )
    parser.add_argument(
        "--match",
        default="characters/enemies/sargent/resources/sprites/idle/idle_00.png",
        help="Reference sprite for size + baseline (default: Sargent idle)",
    )
    parser.add_argument(
        "--output",
        default="outputs/fal/idle_00/sargent_anchor_base.png",
        help="Output path for base anchor (no border)",
    )
    parser.add_argument(
        "--framed-output",
        default="outputs/fal/idle_00/sargent_anchor_framed.png",
        help="Output path for framed anchor (with border)",
    )
    parser.add_argument("--bg", default="#00b140", help="Background fill color")
    parser.add_argument("--key", default="#00b140", help="Key color for masking")
    parser.add_argument("--border-color", default="#ffffff", help="Border color for framed output")
    parser.add_argument("--border-thickness", type=int, default=2, help="Border thickness in px")
    parser.add_argument("--scale-mult", type=float, default=1.0, help="Scale multiplier")
    args = parser.parse_args()

    input_path = Path(args.input)
    match_path = Path(args.match)
    output_path = Path(args.output)

    if not input_path.exists():
        raise SystemExit(f"Input image not found: {input_path}")
    if not match_path.exists():
        raise SystemExit(f"Match sprite not found: {match_path}")

    bg = parse_hex_color(args.bg)
    key = parse_hex_color(args.key)
    key_rgb = (key[0], key[1], key[2])

    match_img = Image.open(match_path).convert("RGBA")
    match_bbox = visible_bbox(match_img, key_rgb, 12)
    if not match_bbox:
        raise SystemExit("No visible pixels found in match sprite.")
    match_visible_h = match_bbox[3] - match_bbox[1]
    if match_visible_h <= 0:
        raise SystemExit("Match sprite visible height is invalid.")
    match_bottom = match_bbox[3] - 1
    target_w, target_h = match_img.size
    baseline_pad = (target_h - 1) - match_bottom

    # Use Fal background removal for reliable keying.
    src = remove_bg_with_fal(input_path)
    src = ensure_transparency(src)
    src_bbox = src.getbbox()
    if not src_bbox:
        raise SystemExit("No visible pixels found in input image.")
    src = src.crop(src_bbox)
    scale_factor = (match_visible_h / src.height) * float(args.scale_mult)
    new_w = max(1, int(round(src.width * scale_factor)))
    new_h = max(1, int(round(src.height * scale_factor)))
    src = src.resize((new_w, new_h), Image.LANCZOS)

    canvas = Image.new("RGBA", (target_w, target_h), bg)
    x = int((target_w - src.width) / 2)
    y = (target_h - baseline_pad) - src.height
    canvas.paste(src, (x, y))

    # Flatten alpha onto solid green to ensure no transparency in the anchor.
    flattened = Image.new("RGBA", (target_w, target_h), bg)
    flattened.alpha_composite(canvas)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    flattened.save(output_path)
    print(f"Saved base anchor: {output_path}")

    if args.framed_output:
        framed_path = Path(args.framed_output)
        framed = flattened.copy()
        draw = ImageDraw.Draw(framed)
        t = max(0, int(args.border_thickness))
        border = parse_hex_color(args.border_color)
        if t > 0:
            draw.rectangle([0, 0, target_w - 1, t - 1], fill=border)
            draw.rectangle([0, target_h - t, target_w - 1, target_h - 1], fill=border)
            draw.rectangle([0, 0, t - 1, target_h - 1], fill=border)
            draw.rectangle([target_w - t, 0, target_w - 1, target_h - 1], fill=border)
        framed_path.parent.mkdir(parents=True, exist_ok=True)
        framed.save(framed_path)
        print(f"Saved framed anchor: {framed_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
