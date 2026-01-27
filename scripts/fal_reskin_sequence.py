#!/usr/bin/env python3
"""Run a sequence of reskin tasks with optional reference chaining."""
from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", nargs="+", required=True, help="Task .md files in order")
    parser.add_argument("--prompt", required=True, help="Prompt for all tasks")
    parser.add_argument("--negative", default=None, help="Negative prompt for all tasks")
    parser.add_argument("--num-images", type=int, default=None, help="Override num images")
    parser.add_argument("--aspect-ratio", default=None, help="Override aspect ratio")
    parser.add_argument("--chain", action="store_true", help="Use previous output as extra reference")
    parser.add_argument("--option-index", type=int, default=1, help="Which option to chain from")
    parser.add_argument("--no-download", action="store_true", help="Skip downloading images")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = Path(__file__).resolve().parents[1]
    output_root = project_root / "outputs" / "fal"

    chained_ref: Path | None = None

    for task in args.tasks:
        cmd = ["python3", "scripts/fal_reskin_generate.py", "--task", task, "--prompt", args.prompt]
        if args.negative:
            cmd.extend(["--negative", args.negative])
        if args.num_images is not None:
            cmd.extend(["--num-images", str(args.num_images)])
        if args.aspect_ratio:
            cmd.extend(["--aspect-ratio", args.aspect_ratio])
        if args.no_download:
            cmd.append("--no-download")
        if args.chain and chained_ref is not None:
            cmd.extend(["--ref", str(chained_ref)])

        print("Running:", " ".join(cmd))
        result = subprocess.run(cmd, cwd=str(project_root))
        if result.returncode != 0:
            return result.returncode

        if args.chain:
            task_stem = Path(task).stem
            candidate = output_root / task_stem / f"option_{args.option_index}.png"
            if candidate.exists():
                chained_ref = candidate
            else:
                print(f"Warning: chained reference not found: {candidate}")
                chained_ref = None

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
