#!/usr/bin/env python3
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from PIL import Image
from PIL import ImageChops


CANVAS_MIN_X = -798.0
CANVAS_MIN_Y = -1122.0
CANVAS_WIDTH = 1376
CANVAS_HEIGHT = 1142

BANNER_LOGO_PATH = Path("source_images/logos/camino.png")
BANNER_BOX_WIDTH_PCT = 0.86
BANNER_BOX_HEIGHT_PCT = 0.58
BANNER_LOGO_SCALE = 0.75
BANNER_LOGO_INNER_MARGIN_PCT = 0.90


@dataclass(frozen=True)
class DrawOp:
    name: str
    source: str
    x: float
    y: float
    scale_x: float = 1.0
    scale_y: float = 1.0
    centered: bool = False
    offset_x: float = 0.0
    offset_y: float = 0.0


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _gradient_color_at(
    value_0_1: float,
    offsets: list[float],
    colors_rgba_0_1: list[tuple[float, float, float, float]],
) -> tuple[int, int, int, int]:
    if value_0_1 <= offsets[0]:
        r, g, b, a = colors_rgba_0_1[0]
        return (round(r * 255), round(g * 255), round(b * 255), round(a * 255))
    for i in range(len(offsets) - 1):
        left = offsets[i]
        right = offsets[i + 1]
        if value_0_1 <= right:
            t = (value_0_1 - left) / (right - left) if right > left else 0.0
            r0, g0, b0, a0 = colors_rgba_0_1[i]
            r1, g1, b1, a1 = colors_rgba_0_1[i + 1]
            r = _lerp(r0, r1, t)
            g = _lerp(g0, g1, t)
            b = _lerp(b0, b1, t)
            a = _lerp(a0, a1, t)
            return (round(r * 255), round(g * 255), round(b * 255), round(a * 255))
    r, g, b, a = colors_rgba_0_1[-1]
    return (round(r * 255), round(g * 255), round(b * 255), round(a * 255))


def _build_gradient_luts(
    offsets: list[float],
    colors_rgba_0_1: list[tuple[float, float, float, float]],
) -> tuple[list[int], list[int], list[int], list[int]]:
    lut_r: list[int] = []
    lut_g: list[int] = []
    lut_b: list[int] = []
    lut_a: list[int] = []
    for i in range(256):
        rgba = _gradient_color_at(i / 255.0, offsets, colors_rgba_0_1)
        lut_r.append(rgba[0])
        lut_g.append(rgba[1])
        lut_b.append(rgba[2])
        lut_a.append(rgba[3])
    return lut_r, lut_g, lut_b, lut_a


def _tile_texture(texture: Image.Image, size: tuple[int, int]) -> Image.Image:
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    w, h = texture.size
    for y in range(0, size[1], h):
        for x in range(0, size[0], w):
            out.alpha_composite(texture, dest=(x, y))
    return out


def _bake_brick_wall_region() -> Image.Image:
    # BrickWall in BrickBuilding1 is a tiled + gradient-mapped grayscale texture.
    pattern_path = Path(
        "stages/stage_01/stage_elements/buildings/walls/brick_wall/brick_pattern_grayscale.png"
    )
    if not pattern_path.exists():
        raise SystemExit(f"Missing brick pattern: {pattern_path}")

    region_w, region_h = 2146, 2200
    pattern = Image.open(pattern_path).convert("RGBA")
    tiled = _tile_texture(pattern, (region_w, region_h))

    # Shader: gradient_map.gdshader + brick_wall.gd sets 4 colors on the gradient.
    # We bake an approximate linear gradient to match the in-game look closely enough.
    offsets = [0.0, 0.268817, 0.575269, 0.854839]
    colors = [
        (0.0823529, 0.027451, 0.027451, 1.0),
        (0.505882, 0.137255, 0.121569, 1.0),
        (0.596078, 0.313726, 0.188235, 1.0),
        (0.745098, 0.572549, 0.411765, 1.0),
    ]
    lut_r, lut_g, lut_b, lut_a = _build_gradient_luts(offsets, colors)

    luma = tiled.convert("L")
    r = luma.point(lut_r)
    g = luma.point(lut_g)
    b = luma.point(lut_b)
    a = tiled.getchannel("A")
    return Image.merge("RGBA", (r, g, b, a))


def _quiver_repeater_ops_pipe() -> list[DrawOp]:
    main = "stages/stage_01/stage_elements/buildings/pipes/drainpipe_body.png"
    cap = "stages/stage_01/stage_elements/buildings/pipes/drainpipe_exit.png"
    for p in [Path(main), Path(cap)]:
        if not p.exists():
            raise SystemExit(f"Missing texture: {p}")

    base_x, base_y = 489.0, -1122.0
    scale_x, scale_y = 0.5, 0.5
    length = 3
    separation = -38
    cap_end_offset_x, cap_end_offset_y = 7, -21

    main_img = Image.open(main)
    step = main_img.size[1] + separation

    ops: list[DrawOp] = []
    for i in range(length):
        ops.append(
            DrawOp(
                name=f"Pipe/main_{i}",
                source=main,
                x=base_x,
                y=base_y + step * i * scale_y,
                scale_x=scale_x,
                scale_y=scale_y,
                centered=False,
            )
        )

    ops.append(
        DrawOp(
            name="Pipe/cap_end",
            source=cap,
            x=base_x + cap_end_offset_x * scale_x,
            y=base_y + (step * length + cap_end_offset_y) * scale_y,
            scale_x=scale_x,
            scale_y=scale_y,
            centered=False,
        )
    )
    return ops


def _quiver_repeater_ops_windows() -> list[DrawOp]:
    tex = "stages/stage_01/stage_elements/buildings/windows/standard/windows_1_1_50.png"
    if not Path(tex).exists():
        raise SystemExit(f"Missing texture: {tex}")
    base_x, base_y = -798.0, -1032.0
    length = 2
    separation = 180
    img = Image.open(tex)
    step = img.size[0] + separation
    return [
        DrawOp(name=f"Windows/{i}", source=tex, x=base_x + step * i, y=base_y, centered=False)
        for i in range(length)
    ]


def _sprite_op(
    name: str,
    source: str,
    x: float,
    y: float,
    scale_x: float = 1.0,
    scale_y: float = 1.0,
    centered: bool = True,
) -> DrawOp:
    if not Path(source).exists():
        raise SystemExit(f"Missing texture: {source}")
    return DrawOp(
        name=name,
        source=source,
        x=x,
        y=y,
        scale_x=scale_x,
        scale_y=scale_y,
        centered=centered,
    )


def _build_ops() -> list[DrawOp]:
    ops: list[DrawOp] = []

    # Brick wall base (baked region, scaled + positioned like the scene instance).
    baked_wall = _bake_brick_wall_region()
    baked_path = Path("tmp/flattened/brick_building1__baked_brick_wall.png")
    baked_path.parent.mkdir(parents=True, exist_ok=True)
    baked_wall.save(baked_path)
    ops.append(
        DrawOp(
            name="BrickWall/baked_region",
            source=str(baked_path),
            x=-4.5,
            y=-550.0,
            scale_x=0.5,
            scale_y=0.5,
            centered=True,
        )
    )

    ops.extend(_quiver_repeater_ops_windows())

    ops.append(
        _sprite_op(
            "Door1",
            "stages/stage_01/stage_elements/buildings/doors/door_2_revised_50.png",
            x=-297.0,
            y=-207.0,
            centered=True,
        )
    )

    # Door2 base, plus its nested sprites.
    door2_x, door2_y = 166.0, -207.0
    ops.append(
        _sprite_op(
            "Door2",
            "stages/stage_01/stage_elements/buildings/doors/door_3_50.png",
            x=door2_x,
            y=door2_y,
            centered=True,
        )
    )
    ops.append(
        _sprite_op(
            "Door2/AnimePoster",
            "stages/stage_01/stage_elements/buildings/signs/anime_girl/anime_girl_poster_red.png",
            x=door2_x - 211.5,
            y=door2_y - 29.425,
            scale_x=0.81875,
            scale_y=0.81875,
            centered=True,
        )
    )
    ops.append(
        _sprite_op(
            "Door2/AnimePoster2",
            "stages/stage_01/stage_elements/buildings/signs/anime_girl/anime_girl_poster_purlple.png",
            x=door2_x + 211.5,
            y=door2_y - 29.425,
            scale_x=0.81875,
            scale_y=0.81875,
            centered=True,
        )
    )

    return ops


def _write_banner_logo(out_path: Path) -> None:
    love_base = Path(
        "stages/stage_01/stage_elements/buildings/signs/love_yourself/pngs/love_yourself_sign_base.png"
    )
    if not love_base.exists():
        raise SystemExit(f"Missing texture: {love_base}")
    if not BANNER_LOGO_PATH.exists():
        raise SystemExit(
            "Missing banner logo.\n"
            f"Expected: {BANNER_LOGO_PATH}\n"
            "Save the provided CAMINO logo as a transparent PNG at that path."
        )

    base = Image.open(love_base).convert("RGBA")
    sign_alpha = base.getchannel("A")

    logo = Image.open(BANNER_LOGO_PATH).convert("RGBA")
    logo_bbox = logo.getchannel("A").getbbox()
    if logo_bbox is None:
        raise SystemExit(f"Logo has no visible pixels: {BANNER_LOGO_PATH}")
    logo_trimmed = logo.crop(logo_bbox)

    banner = Image.new("RGBA", base.size, (0, 0, 0, 0))

    panel_w = int(base.size[0] * BANNER_BOX_WIDTH_PCT)
    panel_h = int(base.size[1] * BANNER_BOX_HEIGHT_PCT)
    if panel_w <= 0 or panel_h <= 0:
        raise SystemExit(f"Invalid panel size: {(panel_w, panel_h)}")
    panel_x = (base.size[0] - panel_w) // 2
    panel_y = (base.size[1] - panel_h) // 2
    white_panel = Image.new("RGBA", (panel_w, panel_h), (255, 255, 255, 255))
    banner.alpha_composite(white_panel, dest=(panel_x, panel_y))

    fit_w = panel_w * BANNER_LOGO_INNER_MARGIN_PCT
    fit_h = panel_h * BANNER_LOGO_INNER_MARGIN_PCT
    scale = min(fit_w / logo_trimmed.size[0], fit_h / logo_trimmed.size[1]) * BANNER_LOGO_SCALE
    if scale <= 0:
        raise SystemExit(f"Invalid logo size: {logo_trimmed.size}")
    target = (max(1, round(logo_trimmed.size[0] * scale)), max(1, round(logo_trimmed.size[1] * scale)))
    logo_resized = logo_trimmed.resize(target, Image.LANCZOS)
    logo_x = panel_x + (panel_w - target[0]) // 2
    logo_y = panel_y + (panel_h - target[1]) // 2
    banner.alpha_composite(logo_resized, dest=(logo_x, logo_y))

    # Constrain the logo to the original sign silhouette (keeps drop-in transparency).
    merged_alpha = ImageChops.multiply(banner.getchannel("A"), sign_alpha)
    banner.putalpha(merged_alpha)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    banner.save(out_path)


def _draw_ops_bounds(ops: list[DrawOp]) -> tuple[float, float, float, float]:
    min_x = float("inf")
    min_y = float("inf")
    max_x = float("-inf")
    max_y = float("-inf")
    for op in ops:
        img = Image.open(op.source).convert("RGBA")
        w, h = img.size
        anchor_x = -w / 2 if op.centered else 0.0
        anchor_y = -h / 2 if op.centered else 0.0
        x1 = op.x + (anchor_x + op.offset_x) * op.scale_x
        y1 = op.y + (anchor_y + op.offset_y) * op.scale_y
        x2 = x1 + w * op.scale_x
        y2 = y1 + h * op.scale_y
        min_x = min(min_x, x1)
        min_y = min(min_y, y1)
        max_x = max(max_x, x2)
        max_y = max(max_y, y2)
    return min_x, min_y, max_x, max_y


def _composite_op(canvas: Image.Image, op: DrawOp, min_x: float, min_y: float) -> dict:
    img = Image.open(op.source).convert("RGBA")
    w, h = img.size
    anchor_x = -w / 2 if op.centered else 0.0
    anchor_y = -h / 2 if op.centered else 0.0
    x1 = (op.x + (anchor_x + op.offset_x) * op.scale_x) - min_x
    y1 = (op.y + (anchor_y + op.offset_y) * op.scale_y) - min_y

    # Affine: output -> input, so invert the translation + scale.
    sx = float(op.scale_x)
    sy = float(op.scale_y)
    if sx == 0.0 or sy == 0.0:
        raise SystemExit(f"Invalid scale for {op.name}: ({sx}, {sy})")
    a = 1.0 / sx
    e = 1.0 / sy
    c = -x1 / sx
    f = -y1 / sy

    layer = img.transform(canvas.size, Image.AFFINE, (a, 0, c, 0, e, f), resample=Image.BICUBIC)
    canvas.alpha_composite(layer)

    return {
        "name": op.name,
        "source": op.source,
        "x": op.x,
        "y": op.y,
        "scale_x": op.scale_x,
        "scale_y": op.scale_y,
        "centered": op.centered,
        "top_left_in_canvas": [x1, y1],
        "size_in_canvas": [w * op.scale_x, h * op.scale_y],
    }


def main() -> int:
    ops = _build_ops()

    min_x, min_y, max_x, max_y = _draw_ops_bounds(ops)
    fixed_min_x = CANVAS_MIN_X
    fixed_min_y = CANVAS_MIN_Y
    fixed_max_x = fixed_min_x + CANVAS_WIDTH
    fixed_max_y = fixed_min_y + CANVAS_HEIGHT
    if min_x < fixed_min_x - 0.001 or min_y < fixed_min_y - 0.001 or max_x > fixed_max_x + 0.001 or max_y > fixed_max_y + 0.001:
        raise SystemExit(
            "Unexpected ops bounds after flattening.\n"
            f"Computed bounds: min=({min_x:.3f},{min_y:.3f}) max=({max_x:.3f},{max_y:.3f})\n"
            f"Fixed canvas:   min=({fixed_min_x:.3f},{fixed_min_y:.3f}) max=({fixed_max_x:.3f},{fixed_max_y:.3f})"
        )
    out_w = CANVAS_WIDTH
    out_h = CANVAS_HEIGHT
    min_x = fixed_min_x
    min_y = fixed_min_y

    out_dir = Path("tmp/flattened")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "brick_building1_shop_body.png"
    manifest_path = out_dir / "brick_building1_shop_body_manifest.json"
    banner_path = out_dir / "brick_building1_banner_camino.png"

    canvas = Image.new("RGBA", (out_w, out_h), (0, 0, 0, 0))
    manifest_ops = []
    for op in ops:
        manifest_ops.append(_composite_op(canvas, op, min_x, min_y))

    _write_banner_logo(banner_path)

    # Original LoveYourselfSign placement (center point) relative to BrickBuilding1 root:
    # Door2 at (166, -207) and sign at (-9, -385) relative to Door2 => (157, -592).
    banner_center_local = (157.0, -592.0)
    banner_size = Image.open(banner_path).size
    banner_top_left_local = (
        banner_center_local[0] - (banner_size[0] / 2),
        banner_center_local[1] - (banner_size[1] / 2),
    )
    banner_top_left_in_canvas = (banner_top_left_local[0] - min_x, banner_top_left_local[1] - min_y)

    # Burn the banner into the combined shop-body image so the next AI pass sees it.
    banner_img = Image.open(banner_path).convert("RGBA")
    canvas.alpha_composite(
        banner_img,
        dest=(round(banner_top_left_in_canvas[0]), round(banner_top_left_in_canvas[1])),
    )
    canvas.save(out_path)

    manifest = {
        "canvas": {
            "min_x": min_x,
            "min_y": min_y,
            "width": out_w,
            "height": out_h,
        },
        "banner": {
            "source": str(banner_path),
            "logo_source": str(BANNER_LOGO_PATH),
            "center_local": [banner_center_local[0], banner_center_local[1]],
            "size": [banner_size[0], banner_size[1]],
            "top_left_local": [banner_top_left_local[0], banner_top_left_local[1]],
            "top_left_in_shop_body_canvas": [banner_top_left_in_canvas[0], banner_top_left_in_canvas[1]],
        },
        "ops": manifest_ops,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")
    print(f"Wrote {banner_path}")
    print(f"Wrote {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
