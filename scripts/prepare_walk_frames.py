#!/usr/bin/env python3
"""Select N frames from a folder, resize, and write to a destination sprite folder."""
from __future__ import annotations

import argparse
import datetime
import re
import subprocess
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Folder with source PNG frames")
    parser.add_argument("--dest", required=True, help="Destination folder for walk_XX.png")
    parser.add_argument("--count", type=int, default=12, help="Number of frames to export")
    parser.add_argument("--prefix", default="walk_", help="Filename prefix")
    parser.add_argument("--width", type=int, default=None, help="Target width")
    parser.add_argument("--height", type=int, default=None, help="Target height")
    parser.add_argument("--match", default=None, help="Match size from this file (e.g., walk_00.png)")
    parser.add_argument("--backup", action="store_true", help="Backup destination folder before overwrite")
    parser.add_argument("--mode", choices=["even", "contiguous"], default="even", help="Frame selection mode")
    parser.add_argument("--start-index", type=int, default=0, help="Start index for contiguous mode (0-based)")
    parser.add_argument("--stride", type=int, default=1, help="Stride for contiguous mode")
    return parser.parse_args()


def image_size(path: Path) -> tuple[int, int]:
    out = subprocess.check_output(["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)])
    text = out.decode("utf-8")
    w = int(re.search(r"pixelWidth:\s*(\d+)", text).group(1))
    h = int(re.search(r"pixelHeight:\s*(\d+)", text).group(1))
    return w, h


def pick_indices(total: int, count: int) -> list[int]:
    if count >= total:
        return list(range(total))
    # Evenly spaced indices
    indices = []
    for i in range(count):
        idx = round(i * (total - 1) / (count - 1))
        indices.append(idx)
    # Ensure unique and sorted
    indices = sorted(set(indices))
    # If de-duped reduced count, pad by adding next indices
    while len(indices) < count:
        for i in range(total):
            if i not in indices:
                indices.append(i)
            if len(indices) == count:
                break
    return sorted(indices)


def main() -> int:
    args = parse_args()
    input_dir = Path(args.input)
    dest_dir = Path(args.dest)
    if not input_dir.exists():
        raise SystemExit(f"Input folder not found: {input_dir}")
    if not dest_dir.exists():
        raise SystemExit(f"Destination folder not found: {dest_dir}")

    files = sorted([p for p in input_dir.iterdir() if p.suffix.lower() == ".png"])
    if not files:
        raise SystemExit("No PNG frames found in input folder")

    target_w = args.width
    target_h = args.height
    if target_w is None or target_h is None:
        match_path = None
        if args.match:
            match_path = Path(args.match)
        else:
            candidate = dest_dir / f"{args.prefix}00.png"
            if candidate.exists():
                match_path = candidate
        if match_path is None or not match_path.exists():
            raise SystemExit("Target size unknown. Provide --width/--height or --match.")
        target_w, target_h = image_size(match_path)

    if args.backup:
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = dest_dir / f"_backup_{stamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        for p in dest_dir.glob(f"{args.prefix}[0-9][0-9].png"):
            p.replace(backup_dir / p.name)

    if args.mode == "contiguous":
        start = max(0, args.start_index)
        stride = max(1, args.stride)
        indices = []
        idx = start
        while len(indices) < args.count and idx < len(files):
            indices.append(idx)
            idx += stride
        if len(indices) < args.count:
            raise SystemExit(
                "Not enough frames for contiguous selection. "
                "Choose an earlier --start-index or lower --count."
            )
    else:
        indices = pick_indices(len(files), args.count)

    for out_index, src_index in enumerate(indices):
        src = files[src_index]
        dest_name = f"{args.prefix}{out_index:02d}.png"
        dest = dest_dir / dest_name
        tmp = dest_dir / f".{dest_name}.tmp.png"
        subprocess.run(
            [
                "sips",
                "-z",
                str(target_h),
                str(target_w),
                str(src),
                "--out",
                str(tmp),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if dest.exists():
            dest.unlink()
        tmp.replace(dest)

    print(f"Wrote {args.count} frames to {dest_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
