from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "public" / "assets" / "generated"
UI = GENERATED / "ui"
VFX = GENERATED / "vfx"


def ensure_dirs() -> None:
    UI.mkdir(parents=True, exist_ok=True)
    VFX.mkdir(parents=True, exist_ok=True)


def rgba(hex_value: int, alpha: int = 255) -> tuple[int, int, int, int]:
    return ((hex_value >> 16) & 255, (hex_value >> 8) & 255, hex_value & 255, alpha)


def lerp(a: int, b: int, t: float) -> int:
    return round(a * (1 - t) + b * t)


def lerp_color(a: int, b: int, t: float, alpha: int = 255) -> tuple[int, int, int, int]:
    return (
        lerp((a >> 16) & 255, (b >> 16) & 255, t),
        lerp((a >> 8) & 255, (b >> 8) & 255, t),
        lerp(a & 255, b & 255, t),
        alpha,
    )


def shade(color: tuple[int, int, int, int], amount: float) -> tuple[int, int, int, int]:
    return (
        max(0, min(255, round(color[0] * amount))),
        max(0, min(255, round(color[1] * amount))),
        max(0, min(255, round(color[2] * amount))),
        color[3],
    )


def draw_beveled_panel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], accent: int) -> None:
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=5, fill=rgba(0x030712, 232))
    draw.rounded_rectangle((x0 + 2, y0 + 2, x1 - 2, y1 - 2), radius=4, outline=rgba(0xfef3c7, 170), width=1)
    draw.rounded_rectangle((x0 + 5, y0 + 5, x1 - 5, y1 - 5), radius=3, outline=rgba(0x111827, 255), width=2)
    draw.line((x0 + 8, y0 + 6, x1 - 8, y0 + 6), fill=rgba(accent, 135), width=2)
    draw.line((x0 + 8, y1 - 6, x1 - 8, y1 - 6), fill=rgba(0x000000, 120), width=2)


def make_health_frame() -> None:
    width, height = 306, 38
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    outer = [(5, 7), (14, 0), (292, 0), (301, 7), (301, 30), (292, 37), (14, 37), (5, 30)]
    draw.polygon(outer, fill=rgba(0x030712, 238))
    draw.line((15, 1, 291, 1), fill=rgba(0xfff7ad, 210), width=2)
    draw.line((15, 36, 291, 36), fill=rgba(0x000000, 180), width=2)
    draw.line((6, 9, 6, 29), fill=rgba(0xfff7ad, 130), width=2)
    draw.line((299, 9, 299, 29), fill=rgba(0x000000, 150), width=2)
    draw.line((20, 5, 120, 5), fill=rgba(0x2dd4bf, 120), width=2)
    draw.line((186, 32, 286, 32), fill=rgba(0xef476f, 110), width=2)
    image.paste((0, 0, 0, 0), (10, 7, width - 10, height - 7))
    draw.rectangle((8, 5, width - 9, height - 6), outline=rgba(0x111827, 255), width=2)
    draw.rectangle((10, 7, width - 11, height - 8), outline=rgba(0xfef3c7, 125), width=1)
    draw.rectangle((13, 10, width - 14, height - 11), outline=rgba(0x020617, 255), width=2)
    draw.rectangle((18, 4, 48, 5), fill=rgba(0xffffff, 75))
    draw.rectangle((258, 32, 287, 33), fill=rgba(0xffffff, 42))
    image.save(UI / "health-frame.png")


def make_health_track() -> None:
    width, height = 286, 24
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    for y in range(height):
        t = y / (height - 1)
        base = lerp_color(0x273244, 0x070b16, t)
        for x in range(width):
            inset = 1 if 1 <= y <= height - 2 and 1 <= x <= width - 2 else 0
            if inset == 0:
                image.putpixel((x, y), rgba(0x020617, 255))
                continue
            texture = 0.92 + (((x * 3 + y * 5) % 11) / 70)
            image.putpixel((x, y), shade(base, texture))

    draw.rectangle((1, 1, width - 2, height - 2), outline=rgba(0x4b5563, 175), width=1)
    draw.rectangle((2, 2, width - 3, 5), fill=rgba(0xffffff, 24))
    draw.rectangle((2, height - 7, width - 3, height - 3), fill=rgba(0x000000, 72))
    for x in range(18, width, 46):
        draw.line((x, 3, x + 22, 20), fill=rgba(0xffffff, 16), width=1)
    image.save(UI / "health-track.png")


def make_health_lag() -> None:
    width, height = 286, 24
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    for x in range(width):
        t = x / (width - 1)
        color = lerp_color(0xfff7ad, 0xf97316, t, 215)
        for y in range(height):
            if y in (0, height - 1) or x in (0, width - 1):
                image.putpixel((x, y), rgba(0x78350f, 170))
            else:
                vertical = 1.18 if y < 6 else 0.92 if y > 15 else 1.0
                image.putpixel((x, y), shade(color, vertical))

    draw.rectangle((2, 2, width - 3, 5), fill=rgba(0xffffff, 65))
    draw.rectangle((2, height - 7, width - 3, height - 3), fill=rgba(0x7c2d12, 78))
    image.save(UI / "health-lag.png")


def make_health_fill(name: str, stops: tuple[int, int, int]) -> None:
    width, height = 286, 24
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    for x in range(width):
        t = x / (width - 1)
        if t < 0.56:
            color = lerp_color(stops[0], stops[1], t / 0.56)
        else:
            color = lerp_color(stops[1], stops[2], (t - 0.56) / 0.44)

        for y in range(height):
            if y in (0, height - 1) or x in (0, width - 1):
                image.putpixel((x, y), rgba(0x020617, 210))
                continue

            vertical = 1.26 if 3 <= y <= 6 else 1.06 if y < 12 else 0.83 if y > 17 else 0.98
            sparkle = 1.0 + (((x * 7 + y * 3) % 17) == 0) * 0.12
            image.putpixel((x, y), shade(color, vertical * sparkle))

    draw.rectangle((2, 2, width - 3, 4), fill=rgba(0xffffff, 72))
    draw.rectangle((2, 5, width - 3, 6), fill=rgba(0xffffff, 38))
    draw.rectangle((2, height - 7, width - 3, height - 3), fill=rgba(0x000000, 70))
    draw.line((8, 18, width - 16, 18), fill=rgba(0xffffff, 28), width=1)
    image.save(UI / f"health-fill-{name}.png")


def make_health_parts() -> None:
    make_health_frame()
    make_health_track()
    make_health_lag()
    make_health_fill("p1", (0x0f766e, 0x22c55e, 0xf8f871))
    make_health_fill("p2", (0xbe123c, 0xf43f5e, 0xffb05f))


def make_meter_frame() -> None:
    width, height = 296, 16
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((0, 0, width - 1, height - 1), radius=3, fill=rgba(0x030712, 220))
    draw.rectangle((4, 4, width - 5, height - 5), outline=rgba(0xfef3c7, 120), width=1)
    draw.rectangle((9, 2, 56, 3), fill=rgba(0x7dd3fc, 130))
    draw.rectangle((width - 57, height - 4, width - 10, height - 3), fill=rgba(0xf0abfc, 110))
    image.save(UI / "meter-frame.png")


def make_timer_frame() -> None:
    width, height = 112, 66
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw_beveled_panel(draw, (0, 0, width - 1, height - 1), 0xfacc15)
    draw.rounded_rectangle((18, 18, width - 19, height - 12), radius=3, fill=rgba(0x111827, 235))
    draw.rectangle((23, 22, width - 24, 27), fill=rgba(0x3a2d54, 220))
    draw.rectangle((28, height - 16, width - 29, height - 14), fill=rgba(0xfacc15, 145))
    image.save(UI / "timer-frame.png")


def make_round_pips() -> None:
    for filled in [False, True]:
        image = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.rectangle((1, 1, 14, 14), fill=rgba(0x030712, 225), outline=rgba(0xfff7ad, 150))
        draw.rectangle((4, 4, 11, 11), fill=rgba(0xfacc15 if filled else 0x1f2937, 255))
        if filled:
            draw.rectangle((5, 5, 10, 6), fill=rgba(0xffffff, 95))
        image.save(UI / f"round-pip-{'full' if filled else 'empty'}.png")


DIGITS = {
    "0": ["111", "101", "101", "101", "101", "101", "111"],
    "1": ["010", "110", "010", "010", "010", "010", "111"],
    "2": ["111", "001", "001", "111", "100", "100", "111"],
    "3": ["111", "001", "001", "111", "001", "001", "111"],
    "4": ["101", "101", "101", "111", "001", "001", "001"],
    "5": ["111", "100", "100", "111", "001", "001", "111"],
    "6": ["111", "100", "100", "111", "101", "101", "111"],
    "7": ["111", "001", "001", "010", "010", "010", "010"],
    "8": ["111", "101", "101", "111", "101", "101", "111"],
    "9": ["111", "101", "101", "111", "001", "001", "111"],
}


def make_digits() -> None:
    for digit, glyph in DIGITS.items():
        scale = 4
        image = Image.new("RGBA", (18, 34), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        for row, line in enumerate(glyph):
            for col, value in enumerate(line):
                if value != "1":
                    continue
                x = col * scale + 3
                y = row * scale + 3
                color = 0xfff3a3 if row < 2 else 0xfacc15 if row < 5 else 0xd97706
                draw.rectangle((x + 2, y + 2, x + scale + 1, y + scale + 1), fill=rgba(0x020617, 180))
                draw.rectangle((x, y, x + scale - 1, y + scale - 1), fill=rgba(color, 255))
                draw.line((x, y, x + scale - 1, y), fill=rgba(0xffffff, 62))
        image.save(UI / f"digit-{digit}.png")


def draw_diamond(draw: ImageDraw.ImageDraw, x: int, y: int, radius: int, color: tuple[int, int, int, int]) -> None:
    draw.polygon([(x, y - radius), (x + radius, y), (x, y + radius), (x - radius, y)], fill=color)


def draw_burst_frame(size: int, frame: int, frames: int, primary: int, secondary: int, blocky: bool) -> Image.Image:
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    center = size // 2
    t = frame / max(1, frames - 1)
    fade = max(0, 1 - t)
    core_alpha = round(255 * fade)
    shard_alpha = round(235 * fade)
    shard_count = 8 if blocky else 10
    radius = 7 + round(t * 30)

    if core_alpha > 0:
        draw_diamond(draw, center, center, max(3, round(10 * fade)), rgba(0xffffff, core_alpha))
        draw.rectangle(
            (center - 14, center - 4, center + 14, center + 4),
            fill=rgba(primary, round(core_alpha * 0.88)),
        )

    for i in range(shard_count):
        angle = (math.tau * i) / shard_count + (0.22 if frame % 2 else 0)
        distance = radius + (i % 3) * 3
        x = center + round(math.cos(angle) * distance)
        y = center + round(math.sin(angle) * distance)
        size_px = max(2, round((6 if blocky else 8) * fade))
        color = rgba(primary if i % 2 == 0 else secondary, shard_alpha)
        if blocky:
            draw.rectangle((x - size_px, y - size_px, x + size_px, y + size_px), fill=color)
        else:
            draw_diamond(draw, x, y, size_px, color)

    ring = 8 + round(t * 17)
    if shard_alpha > 0:
        draw.rectangle(
            (center - ring, center - ring, center + ring, center + ring),
            outline=rgba(secondary, round(shard_alpha * 0.56)),
            width=2,
        )
    return image


def make_burst_sequence(kind: str, frames: int, primary: int, secondary: int, blocky: bool) -> None:
    for frame in range(frames):
        draw_burst_frame(80, frame, frames, primary, secondary, blocky).save(VFX / f"{kind}-{frame}.png")


def make_dust_sequence() -> None:
    frames = 7
    for frame in range(frames):
        image = Image.new("RGBA", (88, 42), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        t = frame / (frames - 1)
        alpha = round(125 * (1 - t))
        for i in range(7):
            x = 10 + i * 10 + round((i - 3) * t * 7)
            y = 27 + round((i % 3) * 3 - t * 11)
            w = round(7 + t * 14 + (i % 2) * 3)
            h = round(4 + t * 5)
            draw.rectangle((x, y, x + w, y + h), fill=rgba(0xdbeafe if i % 2 else 0xf8b58f, max(0, alpha - i * 6)))
        image.save(VFX / f"dust-{frame}.png")


def make_projectile(name: str, primary: int, secondary: int, width: int, height: int) -> None:
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    cy = height // 2
    draw.ellipse((4, cy - 12, width - 18, cy + 12), fill=rgba(primary, 75), outline=rgba(secondary, 145), width=2)
    draw.rectangle((width // 3, cy - 5, width - 10, cy + 5), fill=rgba(primary, 220))
    draw.rectangle((width // 3 + 9, cy - 2, width - 4, cy + 2), fill=rgba(0xffffff, 205))
    draw.rectangle((10, cy - 4, 27, cy + 4), fill=rgba(secondary, 190))
    draw.rectangle((3, cy - 2, 12, cy + 2), fill=rgba(primary, 105))
    image.save(VFX / f"projectile-{name}.png")


def main() -> None:
    ensure_dirs()
    make_health_parts()
    make_meter_frame()
    make_timer_frame()
    make_round_pips()
    make_digits()
    make_burst_sequence("hit", 8, 0xfacc15, 0xff3e7f, False)
    make_burst_sequence("block", 7, 0x7dd3fc, 0xffffff, True)
    make_burst_sequence("super-hit", 9, 0xf0abfc, 0x38bdf8, False)
    make_dust_sequence()
    make_projectile("special", 0x7dd3fc, 0xf0abfc, 78, 38)
    make_projectile("super", 0xf0abfc, 0xfacc15, 110, 52)
    print(f"wrote UI pack to {UI}")
    print(f"wrote VFX pack to {VFX}")


if __name__ == "__main__":
    main()
