#!/usr/bin/env python3
"""Select N frames from a folder, resize, and write to a destination sprite folder."""
from __future__ import annotations

import argparse
import datetime
import os
import re
import subprocess
from PIL import Image
from pathlib import Path


DEFAULT_KEY_COLOR = (0, 177, 64)
DEFAULT_TOL = 12


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Folder with source PNG frames")
    parser.add_argument("--dest", required=True, help="Destination folder for walk_XX.png")
    parser.add_argument("--prefix", default="walk_", help="Filename prefix")
    parser.add_argument(
        "--match",
        required=True,
        help="Reference sprite to match size + baseline padding",
    )
    parser.add_argument(
        "--scale-ref",
        required=True,
        help="Reference image used to compute a single scale factor for all frames",
    )
    parser.add_argument("--scale-mult", type=float, required=True, help="Scale multiplier (e.g., 1.25)")
    parser.add_argument("--backup", action="store_true", help="Backup destination folder before overwrite")
    parser.add_argument(
        "--indices",
        required=True,
        help="Explicit frame indices, e.g. '2,4-6,8' (1-based, from contact sheet labels)",
    )
    parser.add_argument(
        "--output-indices",
        default=None,
        help="Explicit output frame numbers, e.g. '00,01,02,04'",
    )
    parser.add_argument("--output-width", type=int, default=2, help="Zero-pad width for output indices")
    parser.add_argument("--single-frame", action="store_true", help="Write a single file named <prefix>.png")
    parser.add_argument("--flip-h", action="store_true", help="Flip frames horizontally before writing")
    parser.add_argument(
        "--use-canvas",
        action="store_true",
        help="Skip bbox/scale and write frames on the full canvas size",
    )
    return parser.parse_args()


def frame_label(path: Path) -> int:
    match = re.search(r"(\d+)", path.stem)
    if match:
        return int(match.group(1))
    return 0


def parse_indices(value: str) -> list[int]:
    parts = [p.strip() for p in value.split(",") if p.strip()]
    indices: list[int] = []
    for part in parts:
        if "-" in part:
            start_str, end_str = part.split("-", 1)
            start = int(start_str.strip())
            end = int(end_str.strip())
            if start <= end:
                indices.extend(range(start, end + 1))
            else:
                indices.extend(range(start, end - 1, -1))
        else:
            indices.append(int(part))
    return indices


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


def canvas_scale_on_baseline(
    img: Image.Image,
    *,
    scale: float,
    baseline_y: int,
    target_w: int,
    target_h: int,
) -> Image.Image:
    """Scale a full-canvas frame around the baseline (keeps feet on the same ground line).

    This avoids per-frame bbox jitter while still allowing a single global size knob.
    """
    if scale == 1.0:
        return img
    new_w = max(1, int(round(target_w * scale)))
    new_h = max(1, int(round(target_h * scale)))
    scaled = img.resize((new_w, new_h), Image.LANCZOS)

    # Keep the baseline line at the same Y after scaling.
    baseline_scaled = int(round(baseline_y * scale))
    x0 = int(round((target_w - new_w) / 2))
    y0 = int(round(baseline_y - baseline_scaled))

    out = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    out.paste(scaled, (x0, y0), scaled)
    return out


def fit_canvas_no_scale(img: Image.Image, *, target_w: int, target_h: int) -> Image.Image:
    """Crop/pad to the target canvas size without scaling the pixels.

    Rules:
    - Horizontal: center-crop / center-pad
    - Vertical: bottom-crop / bottom-pad (preserves the ground line)
    """
    src_w, src_h = img.size

    # Crop first (no scaling).
    if src_w > target_w:
        x0 = int((src_w - target_w) / 2)
        img = img.crop((x0, 0, x0 + target_w, src_h))
        src_w = target_w
    if src_h > target_h:
        y0 = src_h - target_h
        img = img.crop((0, y0, src_w, y0 + target_h))
        src_h = target_h

    # Pad if needed.
    if src_w < target_w or src_h < target_h:
        out = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
        px = int((target_w - src_w) / 2)
        py = target_h - src_h
        out.paste(img, (px, py), img)
        img = out

    if img.size != (target_w, target_h):
        raise SystemExit(f"Internal canvas fit error: got {img.size}, expected {(target_w, target_h)}")
    return img


def main() -> int:
    args = parse_args()
    input_dir = Path(args.input)
    dest_dir = Path(args.dest)
    match_path = Path(args.match)
    scale_ref_path = Path(args.scale_ref)
    if not input_dir.exists():
        raise SystemExit(f"Input folder not found: {input_dir}")
    if not dest_dir.exists():
        raise SystemExit(f"Destination folder not found: {dest_dir}")
    if not match_path.exists():
        raise SystemExit(f"Match sprite not found: {match_path}")
    if not scale_ref_path.exists():
        raise SystemExit(f"Scale reference not found: {scale_ref_path}")

    files = sorted(
        [p for p in input_dir.iterdir() if p.suffix.lower() == ".png"],
        key=frame_label,
    )
    if not files:
        raise SystemExit("No PNG frames found in input folder")

    match_img = Image.open(match_path).convert("RGBA")
    target_w, target_h = match_img.size

    # Baseline derived from the reference sprite (used in both bbox and canvas modes).
    key_color = DEFAULT_KEY_COLOR
    tol = DEFAULT_TOL
    match_bbox = visible_bbox(match_img, key_color, tol)
    if not match_bbox:
        raise SystemExit("No visible pixels found in match sprite.")
    match_visible_h = match_bbox[3] - match_bbox[1]
    if match_visible_h <= 0:
        raise SystemExit("Match sprite visible height is invalid.")
    match_bottom = match_bbox[3] - 1
    baseline_pad = (target_h - 1) - match_bottom
    baseline_y = (target_h - baseline_pad) - 1

    if args.backup:
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = dest_dir / f"_backup_{stamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        for p in dest_dir.glob(f"{args.prefix}[0-9][0-9].png"):
            p.replace(backup_dir / p.name)

    selected_files: list[Path] | None = None
    labels = parse_indices(args.indices)
    label_to_index = {frame_label(p): i for i, p in enumerate(files)}
    selected_files = []
    for label in labels:
        if label not in label_to_index:
            raise SystemExit(f"Frame label not found: {label}")
        selected_files.append(files[label_to_index[label]])

    output_indices: list[str] | None = None
    if args.output_indices:
        labels = parse_indices(args.output_indices)
        if len(labels) != len(selected_files):
            raise SystemExit(
                "Output indices count does not match selected frames "
                f"({len(labels)} != {len(selected_files)})"
            )
        output_indices = [f"{label:0{args.output_width}d}" for label in labels]

    expected_names: set[str] = set()
    if args.single_frame:
        expected_names.add(f"{args.prefix}.png")
    else:
        for out_index in range(len(selected_files)):
            if output_indices:
                suffix = output_indices[out_index]
            else:
                suffix = f"{out_index:0{args.output_width}d}"
            expected_names.add(f"{args.prefix}{suffix}.png")

        # Prune stale frames for this prefix before writing new ones.
        pattern = re.compile(rf"^{re.escape(args.prefix)}\\d{{{args.output_width}}}\\.png$")
        for p in dest_dir.iterdir():
            if p.is_file() and pattern.match(p.name) and p.name not in expected_names:
                p.unlink()

    if args.single_frame:
        # Remove any numbered leftovers for single-frame outputs.
        pattern = re.compile(rf"^{re.escape(args.prefix)}\\d+\\.png$")
        for p in dest_dir.iterdir():
            if p.is_file() and pattern.match(p.name):
                p.unlink()

    if args.single_frame:
        if len(selected_files) != 1:
            raise SystemExit("single-frame mode requires exactly one selected frame")
        src = selected_files[0]
        dest = dest_dir / f"{args.prefix}.png"
        img = Image.open(src).convert("RGBA")
        if args.use_canvas:
            img = fit_canvas_no_scale(img, target_w=target_w, target_h=target_h)
            if args.flip_h:
                img = img.transpose(Image.FLIP_LEFT_RIGHT)
            out = canvas_scale_on_baseline(
                img,
                scale=float(args.scale_mult),
                baseline_y=baseline_y,
                target_w=target_w,
                target_h=target_h,
            )
        else:
            scale_ref_img = Image.open(scale_ref_path).convert("RGBA")
            scale_ref_bbox = visible_bbox(scale_ref_img, key_color, tol)
            if not scale_ref_bbox:
                raise SystemExit("No visible pixels found in scale reference.")
            scale_ref_visible_h = scale_ref_bbox[3] - scale_ref_bbox[1]
            if scale_ref_visible_h <= 0:
                raise SystemExit("Scale reference visible height is invalid.")
            scale_factor = (match_visible_h / scale_ref_visible_h) * args.scale_mult

            bbox = visible_bbox(img, key_color, tol)
            if not bbox:
                raise SystemExit("No visible pixels after green-screen mask.")
            img = img.crop(bbox)
            new_w = max(1, int(round(img.width * scale_factor)))
            new_h = max(1, int(round(img.height * scale_factor)))
            img = img.resize((new_w, new_h), Image.LANCZOS)
            if img.width > target_w:
                left = int((img.width - target_w) / 2)
                img = img.crop((left, 0, left + target_w, img.height))
            if img.height > target_h:
                top = img.height - target_h
                img = img.crop((0, top, img.width, img.height))
            out = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
            x = int((target_w - img.width) / 2)
            y = (target_h - baseline_pad) - img.height
            if args.flip_h:
                img = img.transpose(Image.FLIP_LEFT_RIGHT)
            out.paste(img, (x, y))
        tmp = dest_dir / f".{dest.name}.tmp.png"
        out.save(tmp)
        if dest.exists():
            dest.unlink()
        tmp.replace(dest)
        print(f"Wrote 1 frame to {dest_dir}")
        return 0

    scale_ref_img = Image.open(scale_ref_path).convert("RGBA")
    scale_ref_bbox = visible_bbox(scale_ref_img, key_color, tol)
    if not scale_ref_bbox:
        raise SystemExit("No visible pixels found in scale reference.")
    scale_ref_visible_h = scale_ref_bbox[3] - scale_ref_bbox[1]
    if scale_ref_visible_h <= 0:
        raise SystemExit("Scale reference visible height is invalid.")
    scale_factor = (match_visible_h / scale_ref_visible_h) * args.scale_mult

    for out_index, src in enumerate(selected_files):
        if output_indices:
            suffix = output_indices[out_index]
        else:
            suffix = f"{out_index:0{args.output_width}d}"
        dest_name = f"{args.prefix}{suffix}.png"
        dest = dest_dir / dest_name
        img = Image.open(src).convert("RGBA")
        if args.use_canvas:
            img = fit_canvas_no_scale(img, target_w=target_w, target_h=target_h)
            if args.flip_h:
                img = img.transpose(Image.FLIP_LEFT_RIGHT)
            out = canvas_scale_on_baseline(
                img,
                scale=float(args.scale_mult),
                baseline_y=baseline_y,
                target_w=target_w,
                target_h=target_h,
            )
        else:
            bbox = visible_bbox(img, key_color, tol)
            if not bbox:
                raise SystemExit("No visible pixels after green-screen mask.")
            img = img.crop(bbox)
            new_w = max(1, int(round(img.width * scale_factor)))
            new_h = max(1, int(round(img.height * scale_factor)))
            img = img.resize((new_w, new_h), Image.LANCZOS)
            if img.width > target_w:
                left = int((img.width - target_w) / 2)
                img = img.crop((left, 0, left + target_w, img.height))
            if img.height > target_h:
                top = img.height - target_h
                img = img.crop((0, top, img.width, img.height))
            out = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
            x = int((target_w - img.width) / 2)
            y = (target_h - baseline_pad) - img.height
            if args.flip_h:
                img = img.transpose(Image.FLIP_LEFT_RIGHT)
            out.paste(img, (x, y))
        tmp = dest_dir / f".{dest_name}.tmp.png"
        out.save(tmp)
        if dest.exists():
            dest.unlink()
        tmp.replace(dest)

    print(f"Wrote {len(selected_files)} frames to {dest_dir}")
    if os.environ.get("RESKIN_BATCH") != "1":
        subprocess.run(["open", str(dest_dir)], check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
