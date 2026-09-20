from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "public" / "assets" / "generated"
FIGHTERS = ("kai", "nova")
CANVAS_SIZE = (320, 560)
SIDE_MARGIN = 4
BOTTOM_MARGIN = 4

FRAME_COUNTS = {
    "idle": 8,
    "walk": 8,
    "run": 5,
    "crouch": 4,
    "jump": 7,
    "jump-tuck": 6,
    "light": 5,
    "heavy": 5,
    "kick": 5,
    "crouch-punch": 5,
    "crouch-kick": 5,
    "hit": 3,
    "crouch-hit": 4,
    "air-hit": 4,
}


@dataclass(frozen=True)
class FrameInfo:
    path: Path
    image: Image.Image
    bbox: tuple[int, int, int, int]


def frame_paths(fighter: str, state: str, count: int) -> list[Path]:
    directory = GENERATED / fighter
    paths = [directory / f"{state}-{index}.png" for index in range(count)]
    alias = directory / f"{state}.png"
    if alias.exists():
        paths.append(alias)
    return paths


def load_frame(path: Path) -> FrameInfo:
    if not path.exists():
        raise FileNotFoundError(path)

    image = Image.open(path).convert("RGBA")
    if image.size != CANVAS_SIZE:
        raise ValueError(f"{path} is {image.size}; expected {CANVAS_SIZE}")

    bbox = image.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError(f"{path} has no visible pixels")

    return FrameInfo(path=path, image=image, bbox=bbox)


def state_transform(frames: list[FrameInfo]) -> tuple[float, bool, int]:
    width, height = CANVAS_SIZE
    max_box_width = max(right - left for left, _, right, _ in (frame.bbox for frame in frames))
    min_left = min(left for left, _, _, _ in (frame.bbox for frame in frames))
    min_right = min(width - right for _, _, right, _ in (frame.bbox for frame in frames))
    min_bottom = min(height - bottom for _, _, _, bottom in (frame.bbox for frame in frames))

    scale = 1.0
    if min_left < SIDE_MARGIN or min_right < SIDE_MARGIN:
        scale = min(scale, (width - SIDE_MARGIN * 2) / max_box_width)

    needs_bottom_lift = min_bottom < BOTTOM_MARGIN
    if needs_bottom_lift:
        scale = min(scale, (height - BOTTOM_MARGIN) / height)

    scaled_width = round(width * scale)
    paste_x = (width - scaled_width) // 2
    scaled_left = min(paste_x + left * scale for left, _, _, _ in (frame.bbox for frame in frames))
    scaled_right_margin = min(width - (paste_x + right * scale) for _, _, right, _ in (frame.bbox for frame in frames))
    shift_x = 0
    if scaled_left < SIDE_MARGIN:
        shift_x += math.ceil(SIDE_MARGIN - scaled_left)
    if scaled_right_margin < SIDE_MARGIN:
        shift_x -= math.ceil(SIDE_MARGIN - scaled_right_margin)

    return scale, needs_bottom_lift, shift_x


def normalize_frame(frame: FrameInfo, scale: float, needs_bottom_lift: bool, shift_x: int) -> None:
    if scale >= 0.999 and not needs_bottom_lift and shift_x == 0:
        return

    width, height = CANVAS_SIZE
    scaled_width = max(1, round(width * scale))
    scaled_height = max(1, round(height * scale))
    resized = frame.image.resize((scaled_width, scaled_height), Image.Resampling.NEAREST)
    canvas = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    paste_x = (width - scaled_width) // 2 + shift_x
    paste_y = height - scaled_height - (BOTTOM_MARGIN if needs_bottom_lift else 0)
    canvas.alpha_composite(resized, (paste_x, paste_y))
    canvas.save(frame.path)


def main() -> None:
    changed: list[str] = []
    for fighter in FIGHTERS:
        for state, count in FRAME_COUNTS.items():
            frames = [load_frame(path) for path in frame_paths(fighter, state, count)]
            scale, needs_bottom_lift, shift_x = state_transform(frames)
            if scale >= 0.999 and not needs_bottom_lift and shift_x == 0:
                continue

            for frame in frames:
                normalize_frame(frame, scale, needs_bottom_lift, shift_x)
                changed.append(str(frame.path.relative_to(ROOT)).replace("\\", "/"))

            print(f"{fighter}:{state} scale={scale:.4f} bottomLift={needs_bottom_lift} shiftX={shift_x}")

    print(f"normalized {len(changed)} files")


if __name__ == "__main__":
    main()
