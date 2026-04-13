from __future__ import annotations

from collections import deque
from pathlib import Path

from PIL import Image
import numpy as np


PROJECT_ROOT = Path("/Users/jcdt/Projects/template-beat-em-up")

CANVAS_SIZE = (1280, 960)
SEATED_OFFSET = (256, 172)
ENGAGE_OFFSET = (96, 64)
THRONE_OFFSET = (188, 160)
BG_TOLERANCE = 80
IDLE_SOURCE = PROJECT_ROOT / "characters/enemies/tax_man/resources/sprites/idle/idle_00.png"
SEATED_START_SOURCE = PROJECT_ROOT / "outputs/reskin/captain_snakeoil/intro/assets/seated_master_start.png"

SEATED_SWIRL_SOURCE = PROJECT_ROOT / (
    "outputs/reskin/captain_snakeoil/intro/seated_master/review/20260412_162918/"
    "bytedance_seedance_2_0_fast_image_to_video/frames_swirl_loop"
)
SEATED_DRINK_SOURCE = PROJECT_ROOT / (
    "outputs/reskin/captain_snakeoil/intro/seated_master/review/20260412_162918/"
    "bytedance_seedance_2_0_fast_image_to_video/frames_drink"
)
ENGAGE_THROW_SOURCE = PROJECT_ROOT / (
    "outputs/reskin/captain_snakeoil/intro/engage_master/review/20260412_161222/"
    "bytedance_seedance_2_0_fast_image_to_video/frames_throw"
)
ENGAGE_REACH_SOURCE = PROJECT_ROOT / (
    "outputs/reskin/captain_snakeoil/intro/engage_master/review/20260412_161222/"
    "bytedance_seedance_2_0_fast_image_to_video/frames_reach_sword"
)
ENGAGE_STAND_SOURCE = PROJECT_ROOT / (
    "outputs/reskin/captain_snakeoil/intro/engage_master/review/20260412_161222/"
    "bytedance_seedance_2_0_fast_image_to_video/frames_stand_up"
)
THRONE_SOURCE = PROJECT_ROOT / "outputs/reskin/captain_snakeoil/intro/assets/throne_only.png"

OUTPUT_ROOT = PROJECT_ROOT / "outputs/reskin/captain_snakeoil/intro/aligned"
SWIRL_OUTPUT = OUTPUT_ROOT / "wine_swirl"
ENGAGE_OUTPUT = OUTPUT_ROOT / "engage"
THRONE_OUTPUT = OUTPUT_ROOT / "throne"

LIVE_SWIRL_DIR = PROJECT_ROOT / "characters/enemies/tax_man/resources/sprites/seated/wine_swirl"
LIVE_ENGAGE_DIR = PROJECT_ROOT / "characters/enemies/tax_man/resources/sprites/seated/engage"
LIVE_THRONE_DIR = PROJECT_ROOT / "characters/enemies/tax_man/resources/sprites/seated/throne"

# User-approved seated loop selection from the first 10 swirl frames.
SWIRL_FRAMES = [1, 2, 4, 5, 7, 8, 10]
ENGAGE_CHAIN = [
    ("swirl", 11),
    ("swirl", 12),
    ("drink", 1),
    ("drink", 4),
    ("drink", 7),
    ("drink", 10),
    ("drink", 12),
    ("throw", 1),
    ("throw", 4),
    ("throw", 7),
    ("throw", 10),
    ("throw", 13),
    ("throw", 14),
    ("reach", 1),
    ("reach", 4),
    ("reach", 7),
    ("reach", 10),
    ("reach", 13),
    ("reach", 14),
    ("stand", 1),
    ("stand", 4),
    ("stand", 7),
    ("stand", 10),
    ("stand", 12),
]


def key_image(path: Path, tolerance: int = BG_TOLERANCE) -> Image.Image:
    img = Image.open(path).convert("RGBA")
    arr = np.array(img)
    rgb = arr[:, :, :3].astype(np.int16)
    height, width, _ = rgb.shape
    border = np.concatenate([rgb[0, :, :], rgb[-1, :, :], rgb[:, 0, :], rgb[:, -1, :]], axis=0)
    bg = np.median(border, axis=0)

    bg_mask = np.zeros((height, width), dtype=bool)
    queue: deque[tuple[int, int]] = deque()
    for x in range(width):
        queue.append((0, x))
        queue.append((height - 1, x))
    for y in range(height):
        queue.append((y, 0))
        queue.append((y, width - 1))

    while queue:
        y, x = queue.popleft()
        if bg_mask[y, x]:
            continue
        if np.linalg.norm(rgb[y, x] - bg) > tolerance:
            continue
        bg_mask[y, x] = True
        if y > 0:
            queue.append((y - 1, x))
        if y < height - 1:
            queue.append((y + 1, x))
        if x > 0:
            queue.append((y, x - 1))
        if x < width - 1:
            queue.append((y, x + 1))

    arr[:, :, 3] = np.where(bg_mask, 0, 255)
    return Image.fromarray(arr, "RGBA")


def compose_on_canvas(source: Path, offset: tuple[int, int]) -> Image.Image:
    subject = key_image(source)
    canvas = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    canvas.alpha_composite(subject, offset)
    return canvas


def alpha_bbox(image: Image.Image) -> tuple[int, int, int, int]:
    bbox = image.getbbox()
    assert bbox is not None, "Expected an image with visible alpha."
    return bbox


def bbox_height(image: Image.Image) -> int:
    bbox = alpha_bbox(image)
    return bbox[3] - bbox[1]


def scale_about_anchor(image: Image.Image, scale: float, anchor: tuple[float, float]) -> Image.Image:
    if abs(scale - 1.0) < 1e-6:
        return image

    width, height = image.size
    scaled_size = (
        max(1, int(round(width * scale))),
        max(1, int(round(height * scale))),
    )
    scaled = image.resize(scaled_size, Image.Resampling.LANCZOS)

    anchor_x, anchor_y = anchor
    paste_x = int(round(anchor_x - (anchor_x * scale)))
    paste_y = int(round(anchor_y - (anchor_y * scale)))

    canvas = Image.new("RGBA", image.size, (0, 0, 0, 0))
    canvas.alpha_composite(scaled, (paste_x, paste_y))
    return canvas


def normalize_height(image: Image.Image, target_height: float, anchor: tuple[float, float]) -> Image.Image:
    current_height = bbox_height(image)
    assert current_height > 0, "Expected a visible frame to normalize."
    scale = target_height / current_height
    return scale_about_anchor(image, scale, anchor)


def chair_anchor(image: Image.Image) -> tuple[float, float]:
    bbox = alpha_bbox(image)
    return ((bbox[0] + bbox[2]) / 2.0, float(bbox[3]))


def save_sequence(images: list[Image.Image], output_dir: Path, live_dir: Path, prefix: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    live_dir.mkdir(parents=True, exist_ok=True)

    for stale in sorted(live_dir.glob(f"{prefix}_*.png")):
        stale.unlink()
    for stale_import in sorted(live_dir.glob(f"{prefix}_*.png.import")):
        stale_import.unlink()

    for index, img in enumerate(images):
        name = f"{prefix}_{index:02d}.png"
        img.save(output_dir / name)
        img.save(live_dir / name)


def save_gif(images: list[Image.Image], path: Path, duration_ms: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    images[0].save(
        path,
        save_all=True,
        append_images=images[1:],
        duration=duration_ms,
        loop=0,
        disposal=2,
    )


def build_swirl() -> list[Image.Image]:
    throne = build_throne()
    anchor = chair_anchor(throne)
    frames = [compose_on_canvas(SEATED_SWIRL_SOURCE / f"frame_{index:03d}.png", SEATED_OFFSET) for index in SWIRL_FRAMES]
    target_height = float(bbox_height(key_image(SEATED_START_SOURCE)))
    reference_height = float(bbox_height(compose_on_canvas(SEATED_SWIRL_SOURCE / "frame_001.png", SEATED_OFFSET)))
    seated_scale = target_height / reference_height
    return [scale_about_anchor(frame, seated_scale, anchor) for frame in frames]


def build_engage() -> list[Image.Image]:
    source_map = {
        "swirl": (SEATED_SWIRL_SOURCE, SEATED_OFFSET),
        "drink": (SEATED_DRINK_SOURCE, SEATED_OFFSET),
        "throw": (ENGAGE_THROW_SOURCE, ENGAGE_OFFSET),
        "reach": (ENGAGE_REACH_SOURCE, ENGAGE_OFFSET),
        "stand": (ENGAGE_STAND_SOURCE, ENGAGE_OFFSET),
    }
    throne = build_throne()
    anchor = chair_anchor(throne)
    seated_target = float(bbox_height(key_image(SEATED_START_SOURCE)))
    idle_target = float(bbox_height(Image.open(IDLE_SOURCE).convert("RGBA")))
    stand_count = sum(1 for section, _index in ENGAGE_CHAIN if section == "stand")
    stand_targets = np.linspace(seated_target, idle_target, stand_count).tolist()

    frames: list[Image.Image] = []
    stand_index = 0
    for section, index in ENGAGE_CHAIN:
        folder, offset = source_map[section]
        frame = compose_on_canvas(folder / f"frame_{index:03d}.png", offset)
        target_height = seated_target
        if section == "stand":
            target_height = stand_targets[stand_index]
            stand_index += 1
        frames.append(normalize_height(frame, target_height, anchor))
    return frames


def build_throne() -> Image.Image:
    return compose_on_canvas(THRONE_SOURCE, THRONE_OFFSET)


def main() -> int:
    swirl_images = build_swirl()
    engage_images = build_engage()
    throne_image = build_throne()

    save_sequence(swirl_images, SWIRL_OUTPUT, LIVE_SWIRL_DIR, "wine_swirl")
    save_sequence(engage_images, ENGAGE_OUTPUT, LIVE_ENGAGE_DIR, "engage")

    THRONE_OUTPUT.mkdir(parents=True, exist_ok=True)
    LIVE_THRONE_DIR.mkdir(parents=True, exist_ok=True)
    throne_output = THRONE_OUTPUT / "throne_only.png"
    live_throne = LIVE_THRONE_DIR / "throne_only.png"
    throne_image.save(throne_output)
    throne_image.save(live_throne)

    reveal_output = OUTPUT_ROOT / "reveal"
    reveal_output.mkdir(parents=True, exist_ok=True)
    swirl_images[0].save(reveal_output / "reveal_00.png")
    save_gif(swirl_images, OUTPUT_ROOT / "swirl_preview.gif", 125)
    save_gif(engage_images, OUTPUT_ROOT / "engage_preview.gif", 125)

    print(f"Built {len(swirl_images)} swirl frames -> {LIVE_SWIRL_DIR}")
    print(f"Built {len(engage_images)} engage frames -> {LIVE_ENGAGE_DIR}")
    print(f"Built throne asset -> {live_throne}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
