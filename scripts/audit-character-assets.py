from __future__ import annotations

from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "public" / "assets" / "generated"
FIGHTERS = ("kai", "nova")
CANVAS_SIZE = (320, 560)
MIN_EDGE_MARGIN = 4
MAX_BOTTOM_SWING = 8
MAX_CENTER_SWING = 28

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

WIDE_ATTACK_STATES = {"light", "kick"}


def frame_paths(fighter: str, state: str, count: int) -> list[Path]:
    directory = GENERATED / fighter
    return [directory / f"{state}-{index}.png" for index in range(count)]


def audit_frame(path: Path) -> tuple[tuple[int, int, int, int], dict[str, int]]:
    if not path.exists():
        raise AssertionError(f"missing frame: {path}")

    image = Image.open(path).convert("RGBA")
    if image.size != CANVAS_SIZE:
        raise AssertionError(f"{path} is {image.size}; expected {CANVAS_SIZE}")

    bbox = image.getchannel("A").getbbox()
    if bbox is None:
        raise AssertionError(f"empty frame: {path}")

    width, height = image.size
    left, top, right, bottom = bbox
    margins = {
        "left": left,
        "top": top,
        "right": width - right,
        "bottom": height - bottom,
    }
    for edge, margin in margins.items():
        if margin < MIN_EDGE_MARGIN:
            raise AssertionError(f"{path} touches {edge} edge: margin={margin}, bbox={bbox}")

    return bbox, margins


def main() -> None:
    checked = 0
    for fighter in FIGHTERS:
        for state, count in FRAME_COUNTS.items():
            boxes = []
            for path in frame_paths(fighter, state, count):
                bbox, _ = audit_frame(path)
                boxes.append(bbox)
                checked += 1

            bottoms = [bottom for _, _, _, bottom in boxes]
            centers = [(left + right) / 2 for left, _, right, _ in boxes]
            bottom_swing = max(bottoms) - min(bottoms)
            center_swing = max(centers) - min(centers)

            if bottom_swing > MAX_BOTTOM_SWING:
                raise AssertionError(f"{fighter}:{state} baseline jumps by {bottom_swing}px")

            if state not in WIDE_ATTACK_STATES and center_swing > MAX_CENTER_SWING:
                raise AssertionError(f"{fighter}:{state} center jumps by {center_swing:.1f}px")

    print(f"character asset audit passed: {checked} frames")


if __name__ == "__main__":
    main()
