#!/usr/bin/env python3
"""Batch generate videos, extract frames, remove BG, and prepare sprite frames via a TOML config."""
from __future__ import annotations

import argparse
import subprocess
import time
from pathlib import Path
import tomllib
from concurrent.futures import ThreadPoolExecutor, as_completed
import shutil
import re
from PIL import Image, ImageDraw


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VIDEO_DIR = PROJECT_ROOT / "outputs" / "fal" / "video"


def run(cmd: list[str]) -> None:
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=str(PROJECT_ROOT))


def backup_existing(path: Path) -> None:
    if not path.exists():
        return
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup = path.with_name(f"{path.stem}_prev_{timestamp}{path.suffix}")
    path.rename(backup)


def find_video_for_action(name: str) -> Path:
    candidates = sorted(VIDEO_DIR.glob(f"{name}_*.mp4"))
    if not candidates:
        raise SystemExit(
            f"Video not found for {name} in {VIDEO_DIR}. "
            f"Expected a file named {name}_*.mp4."
        )
    chosen = max(candidates, key=lambda p: (p.stat().st_mtime, p.name))
    if len(candidates) > 1:
        print(f"Using video for {name}: {chosen.name}")
    return chosen


def resize_frames_to_match(raw_dir: Path, target_size: tuple[int, int]) -> None:
    target_w, target_h = target_size
    for frame_path in sorted(raw_dir.glob("*.png")):
        img = Image.open(frame_path).convert("RGBA")
        if img.size == (target_w, target_h):
            continue
        img = img.resize((target_w, target_h), Image.LANCZOS)
        img.save(frame_path)


 


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


def frame_label(path: Path) -> int:
    match = re.search(r"(\d+)", path.stem)
    if match:
        return int(match.group(1))
    return 0


def is_greenscreen(path: Path, key: tuple[int, int, int] = (0, 177, 64), tol: int = 12) -> bool:
    img = Image.open(path).convert("RGB")
    w, h = img.size
    samples = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
    for x, y in samples:
        r, g, b = img.getpixel((x, y))
        if abs(r - key[0]) <= tol and abs(g - key[1]) <= tol and abs(b - key[2]) <= tol:
            return True
    return False


def pad_amount(value_pct: float | None, value_px: float | None, size: int) -> int:
    if value_px is not None:
        return max(0, int(round(float(value_px))))
    if value_pct is None:
        return 0
    return max(0, int(round(float(value_pct) * size)))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="docs/reskin/nova_animations.toml", help="Path to TOML config")
    parser.add_argument("--only", nargs="*", default=None, help="Only run these animation names")
    parser.add_argument("--parallel", type=int, default=10, help="Max concurrent Fal jobs")
    parser.add_argument(
        "--make-videos",
        action="store_true",
        help="Only generate videos (skip frames, bg remove, contact sheets)",
    )
    parser.add_argument(
        "--make-frames",
        action="store_true",
        help="Only extract frames (and contact sheets) from existing videos",
    )
    parser.add_argument("--skip-video", action="store_true", help="Skip video generation")
    parser.add_argument("--skip-extract", action="store_true", help="Skip frame extraction")
    parser.add_argument("--skip-bg-remove", action="store_true", help="Skip background removal")
    parser.add_argument("--skip-contact", action="store_true", help="Skip contact sheet")
    parser.add_argument("--apply-sprites", action="store_true", help="Write frames into sprite folders")
    return parser.parse_args()


def resolve_match_path(
    anim: dict,
    dest_dir: str,
    prefix: str,
    output_start: int | None,
    output_width: int | None,
    single_frame: bool,
) -> Path:
    match_override = anim.get("match")
    if match_override:
        match_path = Path(match_override)
        if not match_path.is_absolute():
            match_path = (PROJECT_ROOT / match_path).resolve()
        if not match_path.exists():
            raise SystemExit(f"Match sprite not found: {match_path}")
        return match_path

    dest_path = Path(dest_dir)
    dest_str = str(dest_path)
    if "/playable/chad/" in dest_str:
        dest_str = dest_str.replace("/playable/chad/", "/playable/mark/")
    else:
        raise SystemExit(
            f"Missing match for {anim.get('name')}. Add match= to TOML or use a chad dest_dir."
        )
    match_dir = Path(dest_str)
    if single_frame:
        match_name = f"{prefix}.png"
    else:
        if output_start is None or output_width is None:
            raise SystemExit(f"Missing output_start/output_width for match on {anim.get('name')}")
        match_name = f"{prefix}{int(output_start):0{int(output_width)}d}.png"
    match_path = match_dir / match_name
    if not match_path.exists():
        raise SystemExit(f"Match sprite not found: {match_path}")
    return match_path


def main() -> int:
    args = parse_args()
    if args.apply_sprites:
        args.skip_video = True
        args.skip_extract = True
        args.skip_bg_remove = True
        args.skip_contact = True
    elif args.make_videos:
        args.skip_video = False
        args.skip_extract = True
        args.skip_bg_remove = True
        args.skip_contact = True
    elif args.make_frames:
        args.skip_video = True
        args.skip_extract = False
        args.skip_bg_remove = True
        args.skip_contact = False
    # Background removal is only done during apply-sprites.
    args.skip_bg_remove = True
    cfg_path = (PROJECT_ROOT / args.config).resolve()
    if not cfg_path.exists():
        raise SystemExit(f"Config not found: {cfg_path}")

    config = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    global_cfg = config.get("global", {})
    animations = config.get("animation", [])
    active_list = [str(name) for name in global_cfg.get("active", [])]

    anchor_image = global_cfg.get("anchor_image")
    if not anchor_image:
        raise SystemExit("global.anchor_image is required")
    scale_ref = global_cfg.get("scale_ref")
    if not scale_ref:
        raise SystemExit("global.scale_ref is required")
    scale_ref_path = Path(scale_ref)
    if not scale_ref_path.is_absolute():
        scale_ref_path = (PROJECT_ROOT / scale_ref_path).resolve()
    if not scale_ref_path.exists():
        raise SystemExit(f"Scale reference not found: {scale_ref_path}")

    frame_guide_enabled = bool(global_cfg.get("frame_guide", False))
    frame_guide_color = str(global_cfg.get("frame_guide_color", "#ffffff"))
    frame_guide_thickness = int(global_cfg.get("frame_guide_thickness", 2))
    frame_guide_match = global_cfg.get("frame_guide_match")
    if frame_guide_enabled and not frame_guide_match:
        raise SystemExit("global.frame_guide_match is required when frame_guide is enabled")
    frame_guide_match_path = None
    frame_guide_size: tuple[int, int] | None = None
    if frame_guide_match:
        frame_guide_match_path = Path(frame_guide_match)
        if not frame_guide_match_path.is_absolute():
            frame_guide_match_path = (PROJECT_ROOT / frame_guide_match_path).resolve()
        if not frame_guide_match_path.exists():
            raise SystemExit(f"Frame guide match sprite not found: {frame_guide_match_path}")
        match_img = Image.open(frame_guide_match_path).convert("RGBA")
        frame_guide_size = match_img.size

    frames_dir = PROJECT_ROOT / global_cfg.get("frames_dir", "outputs/fal/frames")
    frames_dir.mkdir(parents=True, exist_ok=True)

    selected_anims: list[dict] = []
    for anim in animations:
        name = anim.get("name")
        if not name:
            continue
        if args.only and name not in args.only:
            continue
        if active_list and name not in active_list:
            continue
        selected_anims.append(anim)

    def build_padded_image(anim: dict) -> Path:
        name = anim.get("name")
        image_path = PROJECT_ROOT / anchor_image
        if not image_path.exists():
            raise SystemExit(f"Anchor image not found: {image_path}")
        pad_color = anim.get("pad_color") or global_cfg.get("pad_color") or "#00b140"
        pad_keys = (
            "pad_top_pct",
            "pad_bottom_pct",
            "pad_left_pct",
            "pad_right_pct",
            "pad_top_px",
            "pad_bottom_px",
            "pad_left_px",
            "pad_right_px",
        )
        has_padding = any(anim.get(k) for k in pad_keys)
        padded_dir = PROJECT_ROOT / "outputs" / "fal" / "padded"
        padded_dir.mkdir(parents=True, exist_ok=True)
        padded_path = padded_dir / f"{name}.png"
        backup_existing(padded_path)
        if has_padding:
            src = Image.open(image_path).convert("RGBA")
            pad_top = pad_amount(anim.get("pad_top_pct"), anim.get("pad_top_px"), src.height)
            pad_bottom = pad_amount(anim.get("pad_bottom_pct"), anim.get("pad_bottom_px"), src.height)
            pad_left = pad_amount(anim.get("pad_left_pct"), anim.get("pad_left_px"), src.width)
            pad_right = pad_amount(anim.get("pad_right_pct"), anim.get("pad_right_px"), src.width)
            new_w = src.width + pad_left + pad_right
            new_h = src.height + pad_top + pad_bottom
            bg = parse_hex_color(str(pad_color))
            canvas = Image.new("RGBA", (new_w, new_h), bg)
            canvas.paste(src, (pad_left, pad_top))
            canvas.save(padded_path)
        else:
            shutil.copy2(image_path, padded_path)
        if not frame_guide_enabled:
            return padded_path

        if frame_guide_match_path is None:
            raise SystemExit("frame_guide_match_path not set")

        key_color = (0, 177, 64)
        tol = 12
        match_img = Image.open(frame_guide_match_path).convert("RGBA")
        match_bbox = visible_bbox(match_img, key_color, tol)
        if not match_bbox:
            raise SystemExit("No visible pixels found in frame guide match sprite.")
        match_visible_h = match_bbox[3] - match_bbox[1]
        if match_visible_h <= 0:
            raise SystemExit("Frame guide match visible height is invalid.")
        match_bottom = match_bbox[3] - 1
        target_w, target_h = match_img.size
        baseline_pad = (target_h - 1) - match_bottom

        scale_ref_img = Image.open(scale_ref_path).convert("RGBA")
        scale_ref_bbox = visible_bbox(scale_ref_img, key_color, tol)
        if not scale_ref_bbox:
            raise SystemExit("No visible pixels found in scale reference.")
        scale_ref_visible_h = scale_ref_bbox[3] - scale_ref_bbox[1]
        if scale_ref_visible_h <= 0:
            raise SystemExit("Scale reference visible height is invalid.")

        scale_mult = anim.get("scale_multiplier") or global_cfg.get("scale_multiplier")
        if scale_mult is None:
            raise SystemExit(f"Missing scale_multiplier for {name}. Add scale_multiplier to the TOML.")
        scale_factor = (match_visible_h / scale_ref_visible_h) * float(scale_mult)

        src = Image.open(padded_path).convert("RGBA")
        src_bbox = visible_bbox(src, key_color, tol)
        if not src_bbox:
            raise SystemExit(f"No visible pixels found in anchor image for {name}.")
        src = src.crop(src_bbox)
        new_w = max(1, int(round(src.width * scale_factor)))
        new_h = max(1, int(round(src.height * scale_factor)))
        safe_w = target_w - (frame_guide_thickness * 2)
        safe_h = target_h - (frame_guide_thickness * 2)
        if new_w > safe_w or new_h > safe_h:
            raise SystemExit(
                f"Frame guide overflow for {name}: scaled {new_w}x{new_h} "
                f"exceeds safe {safe_w}x{safe_h}. Adjust scale_ref/scale_multiplier."
            )
        src = src.resize((new_w, new_h), Image.LANCZOS)

        bg = parse_hex_color(str(pad_color))
        canvas = Image.new("RGBA", (target_w, target_h), bg)
        x = int((target_w - src.width) / 2)
        y = (target_h - baseline_pad) - src.height
        canvas.paste(src, (x, y))

        border = parse_hex_color(frame_guide_color)
        draw = ImageDraw.Draw(canvas)
        t = frame_guide_thickness
        if t > 0:
            draw.rectangle([0, 0, target_w - 1, t - 1], fill=border)
            draw.rectangle([0, target_h - t, target_w - 1, target_h - 1], fill=border)
            draw.rectangle([0, 0, t - 1, target_h - 1], fill=border)
            draw.rectangle([target_w - t, 0, target_w - 1, target_h - 1], fill=border)

        framed_path = padded_dir / f"{name}_framed.png"
        backup_existing(framed_path)
        canvas.save(framed_path)
        return framed_path

    def resolve_end_image_arg(anim: dict, image_for_video: Path) -> str | None:
        name = anim.get("name")
        end_image_mode = anim.get("end_image") or "same"
        if end_image_mode == "none":
            return "none"
        if end_image_mode == "flip":
            from PIL import Image

            src = Image.open(image_for_video).convert("RGBA")
            flipped = src.transpose(Image.FLIP_LEFT_RIGHT)
            end_dir = PROJECT_ROOT / "outputs" / "fal" / "padded"
            end_dir.mkdir(parents=True, exist_ok=True)
            end_path = end_dir / f"{name}_end_flip.png"
            backup_existing(end_path)
            flipped.save(end_path)
            return str(end_path)
        if end_image_mode != "same":
            end_path = Path(end_image_mode)
            if not end_path.is_absolute():
                end_path = (PROJECT_ROOT / end_path).resolve()
            return str(end_path)
        return None

    def run_video(anim: dict) -> None:
        name = anim.get("name")
        prompt = anim.get("prompt")
        prompt_variations = anim.get("prompt_variations") or anim.get("prompt_variants")
        if not prompt and not prompt_variations:
            print(f"Skipping {name} (missing prompt)")
            return
        constraints = anim.get("constraints") or global_cfg.get("constraints")
        negative = anim.get("negative") or global_cfg.get("negative")
        resolution = anim.get("resolution") or global_cfg.get("resolution") or "1080p"
        duration = str(anim.get("duration") or global_cfg.get("duration") or "3")

        image_for_video = build_padded_image(anim)
        end_image_arg = resolve_end_image_arg(anim, image_for_video)

        prompts: list[str] = []
        if prompt_variations:
            prompts = [str(p).strip() for p in prompt_variations if str(p).strip()]
        elif prompt:
            prompts = [str(prompt)]
        if not prompts:
            print(f"Skipping {name} (empty prompt list)")
            return

        for idx, base_prompt in enumerate(prompts, start=1):
            final_prompt = base_prompt
            if constraints:
                final_prompt = f"{final_prompt}. {constraints}"
            if len(prompts) > 1:
                variant_image = image_for_video.parent / f"{image_for_video.stem}_v{idx}.png"
                if not variant_image.exists():
                    shutil.copy2(image_for_video, variant_image)
                image_path = variant_image
            else:
                image_path = image_for_video

            cmd = [
                "python3",
                "scripts/fal_video_generate.py",
                "--image",
                str(image_path),
            ]
            if end_image_arg is not None:
                cmd += ["--end-image", end_image_arg]
            cmd += [
                "--prompt",
                final_prompt,
                "--negative",
                negative,
                "--resolution",
                resolution,
                "--duration",
                duration,
            ]
            run(cmd)

    if not args.skip_video and selected_anims:
        with ThreadPoolExecutor(max_workers=max(1, args.parallel)) as executor:
            futures = [executor.submit(run_video, anim) for anim in selected_anims]
            for future in as_completed(futures):
                future.result()

    for anim in selected_anims:
        name = anim.get("name")
        prompt = anim.get("prompt")
        prompt_variations = anim.get("prompt_variations") or anim.get("prompt_variants")
        if not prompt and not prompt_variations:
            continue

        extract_fps = anim.get("extract_fps") or global_cfg.get("extract_fps") or 6
        bg_remove = anim.get("bg_remove")
        if bg_remove is None:
            bg_remove = bool(global_cfg.get("bg_remove", True))

        video_path = find_video_for_action(name)
        raw_dir = frames_dir / f"{name}_raw"
        no_bg_dir = frames_dir / f"{name}_no_bg"
        contact_path = frames_dir / f"{name}_contact.png"

        if not args.skip_extract:
            raw_dir.mkdir(parents=True, exist_ok=True)
            for p in raw_dir.glob("*.png"):
                p.unlink()
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(video_path),
                "-vf",
                f"fps={extract_fps}",
                str(raw_dir / "frame_%03d.png"),
            ]
            run(cmd)
            if frame_guide_enabled:
                if frame_guide_size is None:
                    raise SystemExit("frame_guide_size not set")
                resize_frames_to_match(raw_dir, frame_guide_size)
                cmd = [
                    "python3",
                    "scripts/remove_frame_border.py",
                    "--input",
                    str(raw_dir),
                    "--thickness",
                    str(frame_guide_thickness),
                    "--fill",
                    str(global_cfg.get("pad_color", "#00b140")),
                ]
                run(cmd)

        if bg_remove and not args.skip_bg_remove:
            cmd = [
                "python3",
                "scripts/fal_bg_remove.py",
                "--input",
                str(raw_dir),
                "--output-dir",
                str(no_bg_dir),
                "--max-inflight",
                str(max(1, args.parallel)),
            ]
            run(cmd)
        elif args.skip_bg_remove and no_bg_dir.exists():
            for p in no_bg_dir.glob("*.png"):
                p.unlink()

        if not args.skip_contact:
            cols = int(global_cfg.get("contact_cols", 10))
            scale = float(global_cfg.get("contact_scale", 0.25))
            cmd = [
                "python3",
                "scripts/make_contact_sheet.py",
                "--input",
                str(raw_dir),
                "--output",
                str(contact_path),
                "--cols",
                str(cols),
                "--scale",
                str(scale),
            ]
            run(cmd)

        if args.apply_sprites:
            dest_dir = anim.get("dest_dir")
            frame_count = anim.get("frame_count")
            prefix = anim.get("prefix", "")
            frame_indices = anim.get("frame_indices")
            single_frame = bool(anim.get("single_frame", False))
            output_start = anim.get("output_start")
            output_width = anim.get("output_width") or global_cfg.get("output_width")
            scale_mult = anim.get("scale_multiplier") or global_cfg.get("scale_multiplier")
            flip_h = bool(anim.get("flip_h", False))
            if not dest_dir:
                print(f"Skipping sprite apply for {name} (missing dest_dir)")
                continue
            if not frame_indices:
                raise SystemExit(f"Missing frame_indices for {name}. Add frame_indices to the TOML.")
            if not prefix:
                print(f"Skipping sprite apply for {name} (missing prefix)")
                continue
            if not single_frame and output_start is None:
                raise SystemExit(f"Missing output_start for {name}. Add output_start to the TOML.")
            if not single_frame and output_width is None:
                raise SystemExit(f"Missing output_width for {name}. Add output_width to the TOML.")
            if scale_mult is None:
                raise SystemExit(f"Missing scale_multiplier for {name}. Add scale_multiplier to the TOML.")

            source_dir = raw_dir
            if not source_dir.exists():
                raise SystemExit(f"Missing frames for {name}: {source_dir}")

            selected_dir = frames_dir / f"{name}_selected"
            bg_dir = frames_dir / "final" / name
            selected_dir.mkdir(parents=True, exist_ok=True)
            bg_dir.mkdir(parents=True, exist_ok=True)

            dest_path = Path(dest_dir)
            selected_labels = parse_indices(str(frame_indices))
            if single_frame and len(selected_labels) != 1:
                raise SystemExit(f"single_frame requires exactly one frame for {name}")

            output_indices: list[int] | None = None
            if not single_frame:
                start_value = int(output_start)
                output_indices = [n for n in range(start_value, start_value + len(selected_labels))]

            if single_frame:
                expected_names = [f"{prefix}.png"]
            else:
                width = int(output_width)
                expected_names = [f"{prefix}{n:0{width}d}.png" for n in output_indices]

            raw_files = sorted(
                [p for p in source_dir.iterdir() if p.suffix.lower() == ".png"],
                key=frame_label,
            )
            label_to_path = {frame_label(p): p for p in raw_files}

            selected_names: list[str] = []
            selected_sources: list[Path] = []
            for label in selected_labels:
                if label not in label_to_path:
                    raise SystemExit(f"Frame label not found in raw frames for {name}: {label}")
                src = label_to_path[label]
                selected_sources.append(src)
                selected_names.append(src.name)

            for p in selected_dir.glob("*.png"):
                if p.name not in selected_names:
                    p.unlink()
            for p in bg_dir.glob("*.png"):
                if p.name not in selected_names:
                    p.unlink()

            for src in selected_sources:
                dest = selected_dir / src.name
                if dest.exists():
                    if dest.stat().st_mtime >= src.stat().st_mtime and is_greenscreen(dest):
                        continue
                shutil.copy2(src, dest)

            def bg_is_current() -> bool:
                for fname in selected_names:
                    sel_path = selected_dir / fname
                    bg_path = bg_dir / fname
                    if not sel_path.exists() or not bg_path.exists():
                        return False
                    if bg_path.stat().st_mtime < sel_path.stat().st_mtime:
                        return False
                return True

            if not bg_is_current():
                cmd = [
                    "python3",
                    "scripts/fal_bg_remove.py",
                    "--input",
                    str(selected_dir),
                    "--output-dir",
                    str(bg_dir),
                    "--max-inflight",
                    str(max(1, args.parallel)),
                ]
                run(cmd)
                missing = [fname for fname in selected_names if not (bg_dir / fname).exists()]
                if missing:
                    raise SystemExit(f"Missing bg-removed frames for {name}: {', '.join(missing)}")

            cmd = [
                "python3",
                "scripts/prepare_walk_frames.py",
                "--input",
                str(bg_dir),
                "--dest",
                str(dest_path),
                "--prefix",
                prefix,
                "--match",
                str(
                    resolve_match_path(
                        anim,
                        dest_dir,
                        prefix,
                        int(output_start) if output_start is not None else None,
                        int(output_width) if output_width is not None else None,
                        single_frame,
                    )
                ),
                "--scale-ref",
                str(scale_ref_path),
                "--scale-mult",
                str(scale_mult),
            ]
            if frame_guide_enabled:
                cmd.append("--use-canvas")
            if flip_h:
                cmd.append("--flip-h")
            if single_frame:
                cmd += ["--indices", str(selected_labels[0]), "--single-frame"]
            else:
                cmd += ["--indices", ",".join(str(n) for n in selected_labels)]
                cmd += ["--output-indices", ",".join(str(n) for n in output_indices)]
                cmd += ["--output-width", str(int(output_width))]
            run(cmd)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
