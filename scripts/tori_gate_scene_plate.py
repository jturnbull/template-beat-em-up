#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFilter


CANVAS_SIZE = (1600, 900)
SCENE_PLATE = Path("tmp/flattened/tori_gate_scene_plate.png")
EXTRACT_SOURCE = Path("tmp/flattened/tori_gate_scene_extract_source.png")

SKY_SOURCE = Path("stages/stage_01/space_background_large.png")
CLOUDS_SOURCE = Path("stages/stage_01/clouds_3.png")
CAMINO_SOURCE = Path("stages/stage_01/caminoshop.png")
FLOOR_SOURCE = Path("stages/stage_01/stage_panel_large.png")
FLOOR_TRIM_SOURCE = Path("stages/stage_01/wood_floor.png")

GATE_SCENE_CROP = (260, 40, 1230, 860)
GREENSCREEN = (0, 177, 64, 255)


def _load_rgba(path: Path) -> Image.Image:
    if not path.exists():
        raise SystemExit(f"Missing image: {path}")
    return Image.open(path).convert("RGBA")


def _fit_cover(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    target_w, target_h = size
    src_w, src_h = image.size
    scale = max(target_w / src_w, target_h / src_h)
    resized = image.resize((round(src_w * scale), round(src_h * scale)), Image.Resampling.LANCZOS)
    left = (resized.width - target_w) // 2
    top = (resized.height - target_h) // 2
    return resized.crop((left, top, left + target_w, top + target_h))


def _repeat_strip(texture: Image.Image, size: tuple[int, int]) -> Image.Image:
    target_w, target_h = size
    strip = Image.new("RGBA", size, (0, 0, 0, 0))
    scaled = texture.resize((max(1, round(texture.width * (target_h / texture.height))), target_h), Image.Resampling.LANCZOS)
    x = 0
    while x < target_w:
        strip.alpha_composite(scaled, (x, 0))
        x += scaled.width
    return strip


def _clear_near_black(image: Image.Image, threshold: int = 8) -> Image.Image:
    rgba = image.convert("RGBA")
    pixels = rgba.load()
    width, height = rgba.size
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if a == 0:
                continue
            if r <= threshold and g <= threshold and b <= threshold:
                pixels[x, y] = (r, g, b, 0)
    return rgba


def _make_polygon_mask(size: tuple[int, int], polygon: list[tuple[int, int]], *, blur: float = 0.0) -> Image.Image:
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.polygon(polygon, fill=255)
    if blur > 0:
        mask = mask.filter(ImageFilter.GaussianBlur(blur))
    return mask


def _overlay_silhouette(canvas: Image.Image) -> None:
    draw = ImageDraw.Draw(canvas)

    magenta = (226, 42, 160, 255)
    magenta_dark = (125, 13, 84, 255)
    cyan = (84, 245, 230, 255)
    charcoal = (23, 27, 35, 255)
    glow = (255, 217, 98, 180)

    left_leg = [(650, 735), (742, 717), (770, 260), (698, 226), (626, 282), (600, 723)]
    right_leg = [(852, 730), (973, 753), (1001, 314), (941, 274), (870, 286), (823, 720)]
    top_beam = [(635, 220), (919, 220), (1018, 292), (907, 364), (684, 355), (592, 279)]
    header = [(706, 275), (862, 276), (889, 322), (724, 320)]
    left_scanner = [(615, 164), (730, 170), (764, 222), (655, 235), (597, 196)]
    right_scanner = [(869, 170), (971, 174), (1024, 222), (928, 245), (861, 201)]

    for poly in (left_leg, right_leg, top_beam, left_scanner, right_scanner):
        draw.polygon(poly, fill=magenta, outline=charcoal, width=6)
    draw.polygon(header, fill=cyan, outline=charcoal, width=5)

    draw.line((771, 224, 833, 728), fill=magenta_dark, width=10)
    draw.line((666, 354, 942, 366), fill=magenta_dark, width=10)
    draw.line((718, 320, 870, 322), fill=(11, 43, 55, 255), width=8)

    for box in [(642, 414, 700, 494), (890, 420, 956, 502), (664, 563, 713, 638), (882, 570, 938, 646)]:
        draw.rounded_rectangle(box, radius=10, fill=cyan, outline=charcoal, width=4)
    for x, y in [(662, 442), (910, 449), (680, 592), (900, 600)]:
        draw.ellipse((x, y, x + 18, y + 18), fill=glow)

    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.polygon([(585, 720), (1005, 738), (1125, 852), (545, 852)], fill=(26, 8, 20, 100))
    shadow = shadow.filter(ImageFilter.GaussianBlur(20))
    canvas.alpha_composite(shadow)


def build_scene_plate(*, with_placeholder: bool) -> Path:
    SCENE_PLATE.parent.mkdir(parents=True, exist_ok=True)
    canvas = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))

    sky = _fit_cover(_load_rgba(SKY_SOURCE), CANVAS_SIZE)
    canvas.alpha_composite(sky)

    clouds = _fit_cover(_load_rgba(CLOUDS_SOURCE), (1750, 540))
    clouds = clouds.resize((1750, 540), Image.Resampling.LANCZOS)
    canvas.alpha_composite(clouds, (-50, 210))

    walkway_back = _repeat_strip(_load_rgba(FLOOR_TRIM_SOURCE), (1020, 124))
    walkway_back = walkway_back.resize((1020, 116), Image.Resampling.LANCZOS)
    canvas.alpha_composite(walkway_back, (-20, 530))

    front_trim = _repeat_strip(_load_rgba(FLOOR_TRIM_SOURCE), (1760, 228))
    front_trim = front_trim.resize((1760, 210), Image.Resampling.LANCZOS)
    canvas.alpha_composite(front_trim, (-70, 636))

    floor_shadow = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    floor_shadow_draw = ImageDraw.Draw(floor_shadow)
    floor_shadow_draw.rectangle((0, 640, 1600, 900), fill=(17, 13, 20, 78))
    floor_shadow = floor_shadow.filter(ImageFilter.GaussianBlur(10))
    canvas.alpha_composite(floor_shadow)

    path_overlay = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    path_draw = ImageDraw.Draw(path_overlay)
    path_draw.polygon([(575, 646), (957, 657), (1430, 888), (663, 888)], fill=(124, 57, 53, 86))
    path_overlay = path_overlay.filter(ImageFilter.GaussianBlur(4))
    canvas.alpha_composite(path_overlay)

    shop = _clear_near_black(_load_rgba(CAMINO_SOURCE).crop((300, 120, 1240, 1120)))
    shop_box = (790, 150, 1420, 720)
    shop_layer = _fit_cover(shop, (shop_box[2] - shop_box[0], shop_box[3] - shop_box[1]))
    wall_fill = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    wall_fill_draw = ImageDraw.Draw(wall_fill)
    wall_fill_draw.polygon([(822, 154), (1078, 154), (1420, 720), (990, 720)], fill=(74, 48, 39, 255))
    canvas.alpha_composite(wall_fill)
    wall_mask = _make_polygon_mask(
        CANVAS_SIZE,
        [(822, 154), (1078, 154), (1420, 720), (990, 720)],
        blur=1.4,
    )
    canvas.paste(shop_layer, (shop_box[0], shop_box[1]), wall_mask.crop(shop_box))

    wall_frame = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    wall_draw = ImageDraw.Draw(wall_frame)
    wall_draw.polygon([(812, 145), (1088, 145), (1434, 723), (982, 723)], fill=(52, 30, 24, 150))
    wall_draw.line((1078, 145, 1428, 723), fill=(28, 16, 15, 235), width=7)
    wall_draw.line((812, 145, 982, 723), fill=(88, 56, 40, 160), width=4)
    wall_draw.line((812, 145, 1088, 145), fill=(34, 21, 19, 230), width=4)
    canvas.alpha_composite(wall_frame)

    rail = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    rail_draw = ImageDraw.Draw(rail)
    rail_draw.rectangle((0, 544, 170, 560), fill=(53, 57, 73, 255))
    for x in (26, 86, 146):
        rail_draw.rectangle((x, 518, x + 16, 560), fill=(45, 47, 59, 255))
    canvas.alpha_composite(rail)

    if with_placeholder:
        _overlay_silhouette(canvas)

    canvas.save(SCENE_PLATE)
    return SCENE_PLATE


def crop_generated_option(option_path: Path) -> Path:
    if not option_path.exists():
        raise SystemExit(f"Missing option image: {option_path}")
    image = _load_rgba(option_path)
    if image.size != CANVAS_SIZE:
        raise SystemExit(f"{option_path} has size {image.size}, expected {CANVAS_SIZE}")
    EXTRACT_SOURCE.parent.mkdir(parents=True, exist_ok=True)
    image.crop(GATE_SCENE_CROP).save(EXTRACT_SOURCE)
    return EXTRACT_SOURCE


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build-plate")
    build.add_argument(
        "--with-placeholder",
        action="store_true",
        help="Draw the old magenta scaffold for debugging. Default is a clean empty slot.",
    )
    crop = sub.add_parser("crop-option")
    crop.add_argument("--option", required=True, help="Path to the chosen in-scene generated option")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "build-plate":
        print(build_scene_plate(with_placeholder=bool(args.with_placeholder)))
        return 0
    if args.command == "crop-option":
        print(crop_generated_option(Path(args.option)))
        return 0
    raise SystemExit(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
