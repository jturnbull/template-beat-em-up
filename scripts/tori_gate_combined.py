#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from PIL import Image
from PIL import ImageDraw


SCENE_SCALE = 0.75
COMBINED_MIN_X = -395
COMBINED_MIN_Y = -1742
COMBINED_WIDTH = 818
COMBINED_HEIGHT = 2290
BLOCKOUT_WIDTH = 1600
BLOCKOUT_HEIGHT = 1800
GREENSCREEN = (0, 177, 64, 255)
BLOCKOUT_SLICE_LEFT = (120, 120, 860, 1710)
BLOCKOUT_SLICE_RIGHT = (740, 120, 1480, 1710)

BACK_SOURCE = Path("stages/stage_01/stage_elements/gates/tori_gate/tori_gate_back.png")
FRONT_SOURCE = Path("stages/stage_01/stage_elements/gates/tori_gate/tori_gate_front.png")

COMBINED_SOURCE = Path("tmp/flattened/tori_gate_combined.png")
BLOCKOUT_SOURCE = Path("tmp/flattened/tori_gate_blockout.png")
SLICED_OUTPUT_DIR = Path("outputs/reskin/stage_01/tori_gate_sliced")
BLOCKOUT_SLICED_OUTPUT_DIR = Path("outputs/reskin/stage_01/tori_gate_blockout_sliced")


@dataclass(frozen=True)
class Piece:
    name: str
    source: Path
    center_x: float
    center_y: float


PIECES = (
    Piece(
        name="back",
        source=BACK_SOURCE,
        center_x=(-220 - 83) * SCENE_SCALE,
        center_y=(-96 - 954) * SCENE_SCALE,
    ),
    Piece(
        name="front",
        source=FRONT_SOURCE,
        center_x=(254.667 - 91) * SCENE_SCALE,
        center_y=(368 - 1037) * SCENE_SCALE,
    ),
)


def _load_rgba(path: Path) -> Image.Image:
    if not path.exists():
        raise SystemExit(f"Missing image: {path}")
    return Image.open(path).convert("RGBA")


def _piece_bounds(piece: Piece) -> tuple[int, int, int, int]:
    img = _load_rgba(piece.source)
    left = round(piece.center_x - img.width / 2.0)
    top = round(piece.center_y - img.height / 2.0)
    return left, top, left + img.width, top + img.height


def flatten() -> Path:
    COMBINED_SOURCE.parent.mkdir(parents=True, exist_ok=True)
    canvas = Image.new("RGBA", (COMBINED_WIDTH, COMBINED_HEIGHT), (0, 0, 0, 0))
    for piece in PIECES:
        img = _load_rgba(piece.source)
        left, top, _, _ = _piece_bounds(piece)
        paste_x = left - COMBINED_MIN_X
        paste_y = top - COMBINED_MIN_Y
        canvas.alpha_composite(img, (paste_x, paste_y))
    canvas.save(COMBINED_SOURCE)
    return COMBINED_SOURCE


def blockout() -> Path:
    BLOCKOUT_SOURCE.parent.mkdir(parents=True, exist_ok=True)
    canvas = Image.new("RGBA", (BLOCKOUT_WIDTH, BLOCKOUT_HEIGHT), GREENSCREEN)
    draw = ImageDraw.Draw(canvas)

    dark = (53, 59, 75, 255)
    mid = (74, 83, 104, 255)
    orange = (201, 101, 33, 255)
    orange_dark = (148, 55, 34, 255)
    cyan = (43, 230, 218, 255)
    red = (220, 88, 63, 255)
    yellow = (232, 183, 62, 255)
    black = (26, 28, 34, 255)

    # Left leg
    draw.polygon(
        [
            (260, 1520),
            (360, 1500),
            (455, 540),
            (365, 500),
            (290, 560),
            (225, 1485),
        ],
        fill=dark,
    )
    draw.polygon(
        [(305, 640), (382, 600), (426, 1120), (342, 1150)],
        fill=orange,
    )

    # Right leg
    draw.polygon(
        [
            (1160, 1510),
            (1270, 1535),
            (1368, 565),
            (1294, 505),
            (1202, 518),
            (1100, 1478),
        ],
        fill=dark,
    )
    draw.polygon(
        [(1195, 650), (1274, 670), (1233, 1160), (1157, 1140)],
        fill=orange,
    )

    # Top beam and header
    draw.polygon(
        [
            (412, 452),
            (1215, 468),
            (1310, 568),
            (1188, 650),
            (455, 628),
            (350, 548),
        ],
        fill=dark,
    )
    draw.polygon(
        [
            (448, 523),
            (1182, 540),
            (1118, 592),
            (488, 575),
        ],
        fill=orange,
    )
    draw.rounded_rectangle((610, 488, 1002, 612), radius=18, fill=mid, outline=black, width=4)
    draw.text((680, 530), "PORT CHECKPOINT", fill=cyan)

    # Scanner heads / signal blocks
    for x, y in [(405, 392), (1170, 404)]:
        draw.rounded_rectangle((x, y, x + 130, y + 96), radius=16, fill=mid, outline=black, width=4)
        draw.rounded_rectangle((x + 24, y + 24, x + 106, y + 56), radius=8, fill=cyan)
        draw.rectangle((x + 38, y + 66, x + 92, y + 78), fill=yellow)

    # Feet / bases
    draw.polygon([(205, 1512), (392, 1476), (420, 1592), (228, 1624)], fill=mid)
    draw.polygon([(1088, 1476), (1362, 1514), (1320, 1632), (1060, 1588)], fill=mid)

    # Attached modules, lights, and cables to sell "game prop"
    for box in [
        (292, 890, 370, 1045, mid),
        (1234, 890, 1310, 1048, mid),
        (275, 1225, 354, 1360, mid),
        (1206, 1218, 1286, 1358, mid),
    ]:
        draw.rounded_rectangle(box[:4], radius=10, fill=box[4], outline=black, width=4)
    for x, y in [(318, 930), (1256, 930), (302, 1260), (1232, 1260)]:
        draw.rounded_rectangle((x, y, x + 24, y + 78), radius=6, fill=cyan)
        draw.rectangle((x + 4, y + 90, x + 20, y + 102), fill=red)

    # Open center marker so the model keeps the passage open.
    draw.rectangle((585, 675, 1012, 1490), outline=(160, 255, 160, 255), width=10)

    # Structural braces to reinforce the wider arch shape.
    draw.polygon([(468, 640), (560, 650), (470, 820), (392, 795)], fill=orange_dark)
    draw.polygon([(1126, 650), (1208, 648), (1270, 808), (1192, 824)], fill=orange_dark)

    canvas.save(BLOCKOUT_SOURCE)
    return BLOCKOUT_SOURCE


def slice_variants(input_dir: Path) -> list[Path]:
    if not input_dir.exists():
        raise SystemExit(f"Missing input dir: {input_dir}")

    option_paths = sorted(input_dir.glob("option_*.png"))
    if not option_paths:
        raise SystemExit(f"No option_*.png files found in {input_dir}")

    saved: list[Path] = []
    for option_path in option_paths:
        combined = _load_rgba(option_path)
        if combined.size != (COMBINED_WIDTH, COMBINED_HEIGHT):
            raise SystemExit(
                f"{option_path} has size {combined.size}, expected {(COMBINED_WIDTH, COMBINED_HEIGHT)}"
            )

        option_dir = SLICED_OUTPUT_DIR / option_path.stem
        option_dir.mkdir(parents=True, exist_ok=True)

        for piece in PIECES:
            source = _load_rgba(piece.source)
            source_alpha = source.getchannel("A")
            left, top, right, bottom = _piece_bounds(piece)
            crop_box = (
                left - COMBINED_MIN_X,
                top - COMBINED_MIN_Y,
                right - COMBINED_MIN_X,
                bottom - COMBINED_MIN_Y,
            )
            cropped = combined.crop(crop_box).convert("RGBA")
            cropped.putalpha(source_alpha)
            out_path = option_dir / f"tori_gate_{piece.name}.png"
            cropped.save(out_path)
            saved.append(out_path)

    return saved


def _key_greenscreen(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    pixels = rgba.load()
    width, height = rgba.size
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if a == 0:
                continue
            if g >= 120 and g > r * 1.35 and g > b * 1.35:
                pixels[x, y] = (r, g, b, 0)
    return rgba


def slice_blockout_option(option_path: Path) -> list[Path]:
    if not option_path.exists():
        raise SystemExit(f"Missing option image: {option_path}")

    image = _key_greenscreen(_load_rgba(option_path))
    if image.size != (BLOCKOUT_WIDTH, BLOCKOUT_HEIGHT):
        raise SystemExit(
            f"{option_path} has size {image.size}, expected {(BLOCKOUT_WIDTH, BLOCKOUT_HEIGHT)}"
        )

    option_dir = BLOCKOUT_SLICED_OUTPUT_DIR / option_path.stem
    option_dir.mkdir(parents=True, exist_ok=True)

    crops = {
        "back": BLOCKOUT_SLICE_LEFT,
        "front": BLOCKOUT_SLICE_RIGHT,
    }
    saved: list[Path] = []
    for name, crop_box in crops.items():
        cropped = image.crop(crop_box)
        out_path = option_dir / f"tori_gate_{name}.png"
        cropped.save(out_path)
        saved.append(out_path)
    return saved


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("flatten")
    sub.add_parser("blockout")

    slice_parser = sub.add_parser("slice")
    slice_parser.add_argument(
        "--input-dir",
        required=True,
        help="Directory containing generated option_*.png files for the combined gate",
    )
    slice_blockout = sub.add_parser("slice-blockout")
    slice_blockout.add_argument(
        "--option",
        required=True,
        help="Path to a single generated combined option from the blockout workflow",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "flatten":
        out = flatten()
        print(out)
        return 0
    if args.command == "blockout":
        out = blockout()
        print(out)
        return 0
    if args.command == "slice":
        for path in slice_variants(Path(args.input_dir)):
            print(path)
        return 0
    if args.command == "slice-blockout":
        for path in slice_blockout_option(Path(args.option)):
            print(path)
        return 0
    raise SystemExit(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
