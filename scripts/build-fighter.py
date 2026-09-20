"""Build a fighter's full engine frame set from two 6-pose sheets.

Consumes 12 single-pose images from tmp/roster/<name>/<pose>.png
(idle, walk, heavy, kick, hit, knockdown, crouch, jump, block, cast, super,
victory) — one figure per image, so no splitting and no crop bleed.

Background color is sampled from the sheet's top-left corner (works for both
GPT Image 2 and local ComfyUI chroma greens). Poses are split by density
valleys, scaled so standing height matches TARGET_STANDING, and every engine
state frame is emitted (held poses across each state's frame count).

Usage:
  python scripts/build-fighter.py --name talon \
      --sheet1 tmp/roster/talon-sheet1.png --sheet2 tmp/roster/talon-sheet2.png
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "public" / "assets" / "generated"
CANVAS = (320, 560)
FOOT_PAD = 6
TARGET_STANDING = 384
BG_TOL = 70


def key_and_split(sheet_path: Path, n: int) -> list[Image.Image]:
    im = Image.open(sheet_path).convert("RGBA")
    a = np.array(im)
    rgb = a[..., :3].astype(int)
    w = rgb.shape[1]
    corners = np.stack([rgb[5, 5], rgb[5, w // 2], rgb[5, w - 6]])
    bg_color = np.median(corners, axis=0)
    near_bg = np.abs(rgb - bg_color).max(axis=2) < BG_TOL
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    green_dominant = (g > 120) & (g - r > 55) & (g - b > 55)
    bg = near_bg | green_dominant
    a[..., 3] = np.where(bg, 0, 255)
    rgba = Image.fromarray(a, "RGBA")

    char = ~bg
    dens = char.sum(axis=0).astype(float)
    sm = np.convolve(dens, np.ones(15) / 15, mode="same")
    col = sm > max(12.0, 0.04 * sm.max())
    padded = np.pad(col.astype(np.int8), (1, 1))
    starts = np.where(np.diff(padded) == 1)[0]
    ends = np.where(np.diff(padded) == -1)[0]
    islands = [(int(s), int(e)) for s, e in zip(starts, ends) if e - s >= 30]
    merged: list[tuple[int, int]] = []
    for s, e in islands:
        if merged and s - merged[-1][1] < 45:
            merged[-1] = (merged[-1][0], e)
        else:
            merged.append((s, e))

    if len(merged) == n:
        bounds = [(max(0, s - 4), min(rgba.width, e + 4)) for s, e in merged]
    else:
        # fall back to even valley split across the occupied span
        occ = np.where(col)[0]
        x0, x1 = occ.min(), occ.max()
        span = x1 - x0
        cuts = []
        for i in range(1, n):
            c = x0 + int(span * i / n)
            lo, hi = max(x0 + 40, c - 100), min(x1 - 40, c + 100)
            cuts.append(lo + int(np.argmin(sm[lo:hi])))
        edges = [x0 - 5] + cuts + [x1 + 5]
        bounds = [(edges[i], edges[i + 1]) for i in range(n)]

    poses = []
    for left, right in bounds:
        crop = rgba.crop((left, 0, right, rgba.height))
        bb = crop.getbbox()
        poses.append(crop.crop(bb))
    return poses


def key_single(path: Path) -> Image.Image:
    """Chroma-key a single-figure image and return the trimmed figure."""
    im = Image.open(path).convert("RGBA")
    a = np.array(im)
    rgb = a[..., :3].astype(int)
    w = rgb.shape[1]
    corners = np.stack([rgb[5, 5], rgb[5, w // 2], rgb[5, w - 6]])
    bg_color = np.median(corners, axis=0)
    near_bg = np.abs(rgb - bg_color).max(axis=2) < BG_TOL
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    green_dominant = (g > 120) & (g - r > 55) & (g - b > 55)
    bg = near_bg | green_dominant
    a[..., 3] = np.where(bg, 0, 255)
    rgba = Image.fromarray(a, "RGBA")
    bb = rgba.getbbox()
    return rgba.crop(bb)


def place(pose: Image.Image, scale: float) -> Image.Image:
    w = max(1, round(pose.width * scale))
    h = max(1, round(pose.height * scale))
    resized = pose.resize((w, h), Image.Resampling.LANCZOS)
    alpha = np.array(resized.getchannel("A"))
    resized.putalpha(Image.fromarray(((alpha > 110) * 255).astype(np.uint8), "L"))
    if resized.width > CANVAS[0]:
        density = (np.array(resized.getchannel("A")) > 0).sum(axis=0)
        win = CANVAS[0]
        cum = np.concatenate(([0], np.cumsum(density)))
        start = int(np.argmax(cum[win:] - cum[:-win]))
        resized = resized.crop((start, 0, start + win, resized.height))
    if resized.height > CANVAS[1] - FOOT_PAD:
        ratio = (CANVAS[1] - FOOT_PAD) / resized.height
        resized = resized.resize((max(1, round(resized.width * ratio)), CANVAS[1] - FOOT_PAD), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    px = (CANVAS[0] - resized.width) // 2
    py = CANVAS[1] - resized.height - FOOT_PAD
    canvas.alpha_composite(resized, (max(0, px), max(0, py)))
    return canvas


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    args = parser.parse_args()

    out = GEN / args.name
    out.mkdir(parents=True, exist_ok=True)
    base = ROOT / "tmp" / "roster" / args.name
    idle = key_single(base / "idle.png")
    walk = key_single(base / "walk.png")
    heavy = key_single(base / "heavy.png")
    kick = key_single(base / "kick.png")
    hit = key_single(base / "hit.png")
    down = key_single(base / "knockdown.png")
    crouch = key_single(base / "crouch.png")
    jump = key_single(base / "jump.png")
    block = key_single(base / "block.png")
    cast = key_single(base / "cast.png")
    aura = key_single(base / "super.png")
    victory = key_single(base / "victory.png")

    scale1 = TARGET_STANDING / idle.height
    scale2 = TARGET_STANDING / max(block.height, victory.height)

    plan: dict[str, tuple[Image.Image, float, int]] = {
        "idle": (idle, scale1, 8),
        "run": (walk, scale1, 5),
        "walk": (walk, scale1, 8),
        "crouch": (crouch, scale2, 4),
        "jump": (jump, scale2, 7),
        "jump-tuck": (jump, scale2, 6),
        "light": (heavy, scale1, 5),
        "heavy": (heavy, scale1, 5),
        "kick": (kick, scale1, 5),
        "crouch-punch": (heavy, scale1, 5),
        "crouch-kick": (kick, scale1, 5),
        "hit": (hit, scale1, 3),
        "crouch-hit": (hit, scale1, 4),
        "air-hit": (hit, scale1, 4),
        "block": (block, scale2, 3),
        "landing": (crouch, scale2, 3),
        "knockdown": (down, scale1, 5),
        "wake": (crouch, scale2, 4),
        "ko": (down, scale1, 4),
        "victory": (victory, scale2, 5),
        "special": (cast, scale2, 5),
        "super": (aura, scale2, 5),
        "throw": (heavy, scale1, 4),
    }

    manifest_states = []
    for state, (pose, scale, count) in plan.items():
        frame = place(pose, scale)
        variants = []
        for i in range(count):
            frame.save(out / f"{state}-{i}.png")
            variants.append(f"public/assets/generated/{args.name}/{state}-{i}.png")
        frame.save(out / f"{state}.png")
        manifest_states.append({"state": state, "file": f"public/assets/generated/{args.name}/{state}.png", "variants": variants})

    idle_full = place(idle, scale1)
    bb = idle_full.getchannel("A").getbbox()
    top = bb[1]
    head = idle_full.crop((bb[0], top, bb[2], top + int((bb[3] - top) * 0.42)))
    side = max(head.width, head.height)
    sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    sq.alpha_composite(head, ((side - head.width) // 2, 0))
    sq.resize((224, 224), Image.Resampling.LANCZOS).save(out / "portrait.png")

    (out / "manifest.json").write_text(
        json.dumps({"source": f"tmp/roster/{args.name}-s[abcd].png", "canvasSize": list(CANVAS), "states": manifest_states}, indent=2),
        encoding="utf-8",
    )
    print(f"built {args.name}: {len(plan)} states, scale1={scale1:.3f} scale2={scale2:.3f}")


if __name__ == "__main__":
    main()
