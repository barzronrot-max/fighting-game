from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "public" / "assets" / "generated"
SIZE = 64

FIGHTERS = {
    "kai": {
        "source": "idle-0.png",
        "rim": (45, 212, 191, 255),
        "trim": (255, 209, 102, 255),
        "shadow": (3, 7, 18, 220),
        "glow": (34, 197, 94, 120),
        "crop": (0.22, -0.02, 0.78, 0.38),
    },
    "nova": {
        "source": "idle-0.png",
        "rim": (239, 71, 111, 255),
        "trim": (125, 211, 252, 255),
        "shadow": (17, 7, 22, 220),
        "glow": (244, 114, 182, 118),
        "crop": (0.14, -0.01, 0.86, 0.43),
    },
}


def alpha_bbox(image: Image.Image) -> tuple[int, int, int, int]:
    alpha = np.array(image.getchannel("A")) > 20
    ys, xs = np.where(alpha)
    if len(xs) == 0 or len(ys) == 0:
        raise RuntimeError("Sprite frame has no visible pixels")
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def mix(a: int, b: int, t: float) -> int:
    return round(a * (1.0 - t) + b * t)


def draw_pixel_backplate(draw: ImageDraw.ImageDraw, config: dict[str, object]) -> None:
    rim = config["rim"]
    trim = config["trim"]
    if not isinstance(rim, tuple) or not isinstance(trim, tuple):
        raise RuntimeError("Invalid fighter color config")

    for y in range(SIZE):
        t = y / (SIZE - 1)
        color = (
            mix(11, 26, t),
            mix(18, 26, t),
            mix(32, 47, t),
            255,
        )
        draw.line((0, y, SIZE, y), fill=color)

    for y in range(8, SIZE - 8, 4):
        draw.line((8, y, SIZE - 9, y), fill=(255, 255, 255, 14))
    for x in range(8, SIZE - 8, 8):
        draw.line((x, 8, x, SIZE - 9), fill=(0, 0, 0, 30))

    draw.rectangle((0, 0, SIZE - 1, SIZE - 1), fill=None, outline=(2, 6, 23, 255), width=3)
    draw.rectangle((4, 4, SIZE - 5, SIZE - 5), fill=None, outline=rim, width=2)
    draw.rectangle((7, 7, SIZE - 8, SIZE - 8), fill=None, outline=(255, 255, 255, 50), width=1)
    draw.rectangle((8, 8, 24, 11), fill=trim)
    draw.rectangle((SIZE - 25, SIZE - 12, SIZE - 9, SIZE - 9), fill=trim)
    draw.rectangle((4, SIZE - 16, 7, SIZE - 5), fill=rim)
    draw.rectangle((SIZE - 8, 4, SIZE - 5, 16), fill=rim)


def fighter_crop(fighter: str, config: dict[str, object]) -> Image.Image:
    source_name = config["source"]
    crop = config["crop"]
    if not isinstance(source_name, str) or not isinstance(crop, tuple):
        raise RuntimeError("Invalid fighter portrait config")

    source = Image.open(GENERATED / fighter / source_name).convert("RGBA")
    x0, y0, x1, y1 = alpha_bbox(source)
    width = x1 - x0
    height = y1 - y0
    left = max(0, round(x0 + width * float(crop[0])))
    top = max(0, round(y0 + height * float(crop[1])))
    right = min(source.width, round(x0 + width * float(crop[2])))
    bottom = min(source.height, round(y0 + height * float(crop[3])))
    portrait = source.crop((left, top, right, bottom))
    bbox = portrait.getbbox()
    if bbox is None:
        raise RuntimeError(f"{fighter} portrait crop is empty")
    return portrait.crop(bbox)


def add_shadow(canvas: Image.Image, sprite: Image.Image, x: int, y: int, color: tuple[int, int, int, int]) -> None:
    alpha = sprite.getchannel("A")
    shadow = Image.new("RGBA", sprite.size, color)
    shadow.putalpha(alpha.filter(ImageFilter.GaussianBlur(1)))
    canvas.alpha_composite(shadow, (x + 2, y + 3))


def make_portrait(fighter: str, config: dict[str, object]) -> Image.Image:
    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    draw_pixel_backplate(draw, config)

    glow = config["glow"]
    shadow = config["shadow"]
    if not isinstance(glow, tuple) or not isinstance(shadow, tuple):
        raise RuntimeError("Invalid fighter portrait color config")

    draw.ellipse((10, 10, SIZE - 10, SIZE - 8), fill=glow)
    portrait = fighter_crop(fighter, config)
    scale = min(52 / portrait.width, 55 / portrait.height)
    scaled = portrait.resize(
        (max(1, round(portrait.width * scale)), max(1, round(portrait.height * scale))),
        Image.Resampling.NEAREST,
    )
    x = (SIZE - scaled.width) // 2
    y = SIZE - scaled.height - 5
    add_shadow(canvas, scaled, x, y, shadow)
    canvas.alpha_composite(scaled, (x, y))

    draw = ImageDraw.Draw(canvas)
    draw.rectangle((8, 8, SIZE - 9, 13), fill=(255, 255, 255, 28))
    draw.rectangle((10, SIZE - 14, SIZE - 11, SIZE - 10), fill=(0, 0, 0, 66))
    draw.rectangle((0, 0, SIZE - 1, SIZE - 1), fill=None, outline=(254, 243, 199, 180), width=1)
    return canvas


def main() -> None:
    for fighter, config in FIGHTERS.items():
        portrait = make_portrait(fighter, config)
        output = GENERATED / fighter / "portrait.png"
        portrait.save(output)
        print(f"wrote {output}")


if __name__ == "__main__":
    main()
