from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "public" / "assets" / "generated"
CANVAS_SIZE = (320, 560)

FIGHTERS = {
    "kai": {
        "flash": (255, 230, 158),
        "crouch_sources": [0, 1, 2, 1],
        "air_sources": [2, 3, 4, 5],
    },
    "nova": {
        "flash": (174, 226, 255),
        "crouch_sources": [0, 1, 2, 1],
        "air_sources": [2, 3, 4, 5],
    },
}

CROUCH_REACTIONS = [
    {"dx": 0, "dy": 0, "tint": 0.08},
    {"dx": -3, "dy": 1, "tint": 0.18},
    {"dx": -6, "dy": 2, "tint": 0.28},
    {"dx": -2, "dy": 1, "tint": 0.14},
]

AIR_REACTIONS = [
    {"angle": -8, "dx": -7, "dy": 2, "scale_x": 1.00, "scale_y": 1.00, "tint": 0.18},
    {"angle": -16, "dx": -14, "dy": 6, "scale_x": 1.01, "scale_y": 0.99, "tint": 0.32},
    {"angle": -23, "dx": -20, "dy": 8, "scale_x": 1.03, "scale_y": 0.98, "tint": 0.42},
    {"angle": -12, "dx": -10, "dy": 5, "scale_x": 1.00, "scale_y": 1.00, "tint": 0.22},
]


def alpha_bbox(image: Image.Image) -> tuple[int, int, int, int]:
    alpha = np.array(image.getchannel("A")) > 20
    ys, xs = np.where(alpha)
    if len(xs) == 0 or len(ys) == 0:
        raise RuntimeError("Sprite frame has no visible pixels")
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def tint_visible(image: Image.Image, color: tuple[int, int, int], amount: float) -> Image.Image:
    if amount <= 0:
        return image

    data = np.array(image).astype(np.float32)
    alpha = data[:, :, 3] > 20
    tint = np.array(color, dtype=np.float32)
    data[:, :, :3][alpha] = data[:, :, :3][alpha] * (1 - amount) + tint * amount
    return Image.fromarray(np.clip(data, 0, 255).astype(np.uint8), "RGBA")


def offset_full_sprite(source: Image.Image, dx: int, dy: int) -> Image.Image:
    source = source.convert("RGBA")
    frame = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    frame.alpha_composite(source, (dx, dy))
    return frame


def make_air_pose(source: Image.Image, spec: dict[str, float], flash: tuple[int, int, int]) -> Image.Image:
    source = source.convert("RGBA")
    x0, y0, x1, y1 = alpha_bbox(source)
    crop = source.crop((x0, y0, x1, y1))

    width = max(1, round(crop.width * spec["scale_x"]))
    height = max(1, round(crop.height * spec["scale_y"]))
    crop = crop.resize((width, height), Image.Resampling.NEAREST)
    crop = tint_visible(crop, flash, spec["tint"])

    padded = Image.new("RGBA", (crop.width + 84, crop.height + 84), (0, 0, 0, 0))
    padded.alpha_composite(crop, (42, 42))
    rotated = padded.rotate(spec["angle"], resample=Image.Resampling.NEAREST, expand=True)
    bbox = rotated.getbbox()
    if bbox is None:
        raise RuntimeError("Rotated sprite lost all visible pixels")
    rotated = rotated.crop(bbox)

    original_center = (x0 + x1) / 2
    original_bottom = y1
    paste_x = round(original_center - rotated.width / 2 + spec["dx"])
    paste_y = round(original_bottom - rotated.height + spec["dy"])

    frame = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    frame.alpha_composite(rotated, (paste_x, paste_y))
    return frame


def write_reactions(fighter: str) -> None:
    out_dir = GENERATED / fighter
    config = FIGHTERS[fighter]

    for index, spec in enumerate(CROUCH_REACTIONS):
        source_index = config["crouch_sources"][index]
        source = Image.open(out_dir / f"crouch-{source_index}.png")
        frame = offset_full_sprite(source, int(spec["dx"]), int(spec["dy"]))
        tint_visible(frame, config["flash"], float(spec["tint"])).save(out_dir / f"crouch-hit-{index}.png")

    for index, spec in enumerate(AIR_REACTIONS):
        source_index = config["air_sources"][index]
        source = Image.open(out_dir / f"jump-{source_index}.png")
        make_air_pose(source, spec, config["flash"]).save(out_dir / f"air-hit-{index}.png")


def main() -> None:
    for fighter in FIGHTERS:
        write_reactions(fighter)
        print(f"wrote hit reactions for {fighter}")


if __name__ == "__main__":
    main()
