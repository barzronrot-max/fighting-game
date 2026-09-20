from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "public" / "assets" / "generated"
FRAME_COUNT = 5

CROUCH_SEQUENCE = [0, 1, 2, 1, 0]

FIGHTERS = {
    "kai": {
        "punch_dx": 76,
        "punch_dy": -3,
        "kick_dx": 72,
        "kick_dy": 8,
        "punch_tint": (255, 197, 92),
        "kick_tint": (120, 218, 255),
    },
    "nova": {
        "punch_dx": 80,
        "punch_dy": -2,
        "kick_dx": 76,
        "kick_dy": 8,
        "punch_tint": (255, 187, 124),
        "kick_tint": (170, 228, 255),
    },
}

PUNCH_FRAMES = [
    {"strength": 0.05, "body_dx": 0, "body_dy": 0, "tint": 0.00},
    {"strength": 0.45, "body_dx": 2, "body_dy": 0, "tint": 0.05},
    {"strength": 1.00, "body_dx": 4, "body_dy": 1, "tint": 0.10},
    {"strength": 0.58, "body_dx": 1, "body_dy": 0, "tint": 0.05},
    {"strength": 0.12, "body_dx": -1, "body_dy": 0, "tint": 0.00},
]

KICK_FRAMES = [
    {"strength": 0.08, "body_dx": 0, "body_dy": 0, "tint": 0.00},
    {"strength": 0.46, "body_dx": -1, "body_dy": 1, "tint": 0.04},
    {"strength": 1.00, "body_dx": -3, "body_dy": 2, "tint": 0.08},
    {"strength": 0.60, "body_dx": -1, "body_dy": 1, "tint": 0.04},
    {"strength": 0.15, "body_dx": 0, "body_dy": 0, "tint": 0.00},
]


def alpha_bbox(image: Image.Image) -> tuple[int, int, int, int]:
    alpha = np.array(image.getchannel("A")) > 20
    ys, xs = np.where(alpha)
    if len(xs) == 0 or len(ys) == 0:
        raise RuntimeError("Sprite frame has no visible pixels")
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def smoothstep(edge0: float, edge1: float, value: np.ndarray) -> np.ndarray:
    value = np.clip((value - edge0) / (edge1 - edge0), 0.0, 1.0)
    return value * value * (3.0 - 2.0 * value)


def crouch_source(fighter: str, index: int) -> Image.Image:
    frame_index = CROUCH_SEQUENCE[index]
    return Image.open(GENERATED / fighter / f"crouch-{frame_index}.png").convert("RGBA")


def translate(image: Image.Image, dx: int, dy: int) -> Image.Image:
    if dx == 0 and dy == 0:
        return image.copy()

    output = Image.new("RGBA", image.size, (0, 0, 0, 0))
    output.alpha_composite(image, (dx, dy))
    return output


def warp_crouch_pose(
    image: Image.Image,
    *,
    action: str,
    strength: float,
    max_dx: int,
    max_dy: int,
) -> Image.Image:
    arr = np.array(image.convert("RGBA"))
    height, width = arr.shape[:2]
    x0, y0, x1, y1 = alpha_bbox(image)
    yy, xx = np.mgrid[0:height, 0:width]
    xn = (xx - x0) / max(1, x1 - x0)
    yn = (yy - y0) / max(1, y1 - y0)

    if action == "punch":
        arm_band = smoothstep(0.22, 0.34, yn) * (1.0 - smoothstep(0.44, 0.60, yn))
        front = smoothstep(0.48, 0.98, xn)
        shoulder = 0.16 * smoothstep(0.30, 0.43, yn) * (1.0 - smoothstep(0.52, 0.70, yn))
        shift = strength * max_dx * np.maximum(arm_band * front, shoulder * smoothstep(0.36, 0.82, xn))
        drop = strength * max_dy * arm_band * front
    elif action == "kick":
        lower = smoothstep(0.48, 0.83, yn)
        front = smoothstep(0.36, 0.98, xn)
        foot = smoothstep(0.69, 0.98, yn)
        thigh = smoothstep(0.42, 0.63, yn) * (1.0 - smoothstep(0.66, 0.82, yn))
        shift = strength * max_dx * np.maximum(lower * front, 0.55 * thigh * smoothstep(0.42, 0.95, xn))
        drop = strength * max_dy * foot * front
    else:
        raise RuntimeError(f"Unknown crouch action: {action}")

    source_x = np.rint(xx - shift).astype(np.int32)
    source_y = np.rint(yy - drop).astype(np.int32)
    valid = (source_x >= 0) & (source_x < width) & (source_y >= 0) & (source_y < height)

    output = np.zeros_like(arr)
    output[valid] = arr[source_y[valid], source_x[valid]]
    return Image.fromarray(output, "RGBA")


def tint_visible(image: Image.Image, color: tuple[int, int, int], amount: float) -> Image.Image:
    if amount <= 0:
        return image

    arr = np.array(image.convert("RGBA")).astype(np.float32)
    alpha = arr[:, :, 3] > 20
    tint = np.array(color, dtype=np.float32)
    arr[:, :, :3][alpha] = arr[:, :, :3][alpha] * (1.0 - amount) + tint * amount
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")


def write_attack_frames(fighter: str, action: str) -> None:
    config = FIGHTERS[fighter]
    frame_configs = PUNCH_FRAMES if action == "punch" else KICK_FRAMES
    out_dir = GENERATED / fighter

    for index in range(FRAME_COUNT):
        pose = frame_configs[index]
        frame = crouch_source(fighter, index)
        frame = translate(frame, int(pose["body_dx"]), int(pose["body_dy"]))
        frame = warp_crouch_pose(
            frame,
            action=action,
            strength=float(pose["strength"]),
            max_dx=int(config[f"{action}_dx"]),
            max_dy=int(config[f"{action}_dy"]),
        )
        frame = tint_visible(frame, config[f"{action}_tint"], float(pose["tint"]))
        frame.save(out_dir / f"crouch-{action}-{index}.png")


def main() -> None:
    for fighter in FIGHTERS:
        write_attack_frames(fighter, "punch")
        write_attack_frames(fighter, "kick")
        print(f"wrote integrated crouch attacks for {fighter}")


if __name__ == "__main__":
    main()
