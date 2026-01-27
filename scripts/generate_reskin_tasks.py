#!/usr/bin/env python3
"""Generate reskin task files for every sprite/background/title asset."""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(PROJECT_ROOT), help="Project root")
    parser.add_argument("--out", default="docs/reskin", help="Output root (relative to project root)")
    parser.add_argument("--include-sizes", action="store_true", help="Include pixel sizes")
    parser.add_argument("--overwrite", action="store_true", help="Delete existing output directory")
    return parser.parse_args()


def img_size(path: Path) -> tuple[int, int] | None:
    """Return (w,h) for png using macOS sips; returns None on failure."""
    try:
        out = subprocess.check_output(
            ["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)],
            stderr=subprocess.DEVNULL,
        ).decode("utf-8")
        w = re.search(r"pixelWidth:\s*(\d+)", out)
        h = re.search(r"pixelHeight:\s*(\d+)", out)
        if w and h:
            return int(w.group(1)), int(h.group(1))
    except Exception:
        return None
    return None


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def normalize_rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def task_template(title: str, category: str, source: str, size: str, group: str, notes: str = "") -> str:
    return f"""# TASK: {title}

Status: TODO
Category: {category}
Source: {source}
Target: {source}
Size(px): {size}
Group/Set: {group}

## Brief
- Replace with new reskin asset(s) while preserving scale, anchor, and readability.
- Keep consistent style with the reskin art bible.

## AI Generation (fal.ai)
- Model: TBD
- Prompt: TBD
- Negative Prompt: TBD
- Seed(s): TBD
- Guidance/CFG: TBD
- Reference Images: TBD
- Variations: TBD (A/B/C)

## Consistency Checks
- [ ] Size matches reference
- [ ] Ground/contact point aligned
- [ ] Silhouette matches base
- [ ] Palette/lighting matches art bible
- [ ] In‑game readability OK
- [ ] Pose matches original intent

## Review
- [ ] Option A
- [ ] Option B
- [ ] Option C

## Notes
{notes}
"""


def main() -> int:
    args = parse_args()
    root = Path(args.root)
    out_root = root / args.out

    if args.overwrite and out_root.exists():
        tasks_dir = out_root / "tasks"
        if tasks_dir.exists():
            shutil.rmtree(tasks_dir)
        index_path = out_root / "SPRITE_TASKS_INDEX.md"
        if index_path.exists():
            index_path.unlink()
    out_root.mkdir(parents=True, exist_ok=True)

    index_lines = ["# Reskin Tasks Index", "", "Generated task files for every sprite/background/title asset.", ""]

    def add_index(path: Path) -> None:
        index_lines.append(f"- {normalize_rel(path, root)}")

    # Character sprites
    char_pngs = sorted(root.glob("characters/**/resources/sprites/**/*.png"))
    for p in char_pngs:
        rel = normalize_rel(p, root)
        parts = p.parts
        # character name is after characters/<type>/<name>/
        try:
            idx = parts.index("characters")
            char_type = parts[idx + 1]
            char_name = parts[idx + 2]
        except Exception:
            char_type = "unknown"
            char_name = "unknown"
        # group = path under resources/sprites
        try:
            group = normalize_rel(p.parent, root).split("resources/sprites/")[1]
        except Exception:
            group = p.parent.name
        size = ""
        if args.include_sizes:
            sz = img_size(p)
            if sz:
                size = f"{sz[0]}x{sz[1]}"
        title = f"{char_name}/{group}/{p.stem}"
        out_path = out_root / "tasks" / "characters" / char_type / char_name / group / f"{p.stem}.md"
        write_text(out_path, task_template(title, "Character", rel, size, group))
        add_index(out_path)

    # Backgrounds & stage elements
    bg_pngs = set()
    bg_pngs.update(root.glob("stages/**/stage_elements/**/*.png"))
    bg_pngs.update(root.glob("stages/**/skyboxes/**/*.png"))
    for p in sorted(bg_pngs):
        rel = normalize_rel(p, root)
        group = normalize_rel(p.parent, root).replace("stages/", "")
        size = ""
        if args.include_sizes:
            sz = img_size(p)
            if sz:
                size = f"{sz[0]}x{sz[1]}"
        title = p.stem
        out_path = out_root / "tasks" / "backgrounds" / group / f"{p.stem}.md"
        write_text(out_path, task_template(title, "Background", rel, size, group))
        add_index(out_path)

    # Title screens / main menu UI
    title_pngs = sorted(root.glob("ui/main_menu/pngs/**/*.png"))
    for p in title_pngs:
        rel = normalize_rel(p, root)
        group = normalize_rel(p.parent, root).replace("ui/", "")
        size = ""
        if args.include_sizes:
            sz = img_size(p)
            if sz:
                size = f"{sz[0]}x{sz[1]}"
        title = p.stem
        out_path = out_root / "tasks" / "title" / group / f"{p.stem}.md"
        write_text(out_path, task_template(title, "Title Screen", rel, size, group))
        add_index(out_path)

    # Write index
    write_text(out_root / "SPRITE_TASKS_INDEX.md", "\n".join(index_lines) + "\n")

    print(f"Generated {len(index_lines)-4} task files in {normalize_rel(out_root, root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
