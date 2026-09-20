"""Build the Dragon Warrior fighter from two GPT Image 2 pose sheets.

Sheet 1 poses (left->right): idle, walk, heavy punch, kick, hit, knockdown.
Sheet 2 poses:               crouch, jump, block, ki-cast, super-aura, victory.

Each sheet is chroma-keyed (targeted to the exact bright-green bg so the lime
super aura survives), split into 6 poses by density valleys, scaled by a single
per-sheet factor so standing height matches a target, then every engine state
frame is emitted (poses duplicated across each state's frame count).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "public" / "assets" / "generated"
OUT = GEN / "dragon"
CANVAS = (320, 560)
FOOT_PAD = 6
TARGET_STANDING = 384  # trimmed px height of a standing pose on the canvas
BG = np.array([10, 249, 14])
BG_TOL = 60


def key_and_split(sheet_path: Path, n: int) -> list[Image.Image]:
    im = Image.open(sheet_path).convert("RGBA")
    a = np.array(im)
    rgb = a[..., :3].astype(int)
    bg = (np.abs(rgb - BG).max(axis=2) < BG_TOL)
    a[..., 3] = np.where(bg, 0, 255)
    rgba = Image.fromarray(a, "RGBA")

    char = ~bg
    dens = char.sum(axis=0).astype(float)
    sm = np.convolve(dens, np.ones(15) / 15, mode="same")
    occ = np.where(sm > 8)[0]
    x0, x1 = occ.min(), occ.max()
    span = x1 - x0
    cuts = []
    for i in range(1, n):
        c = x0 + int(span * i / n)
        lo, hi = max(x0 + 40, c - 100), min(x1 - 40, c + 100)
        cuts.append(lo + int(np.argmin(sm[lo:hi])))
    bounds = [x0 - 5] + cuts + [x1 + 5]
    poses = []
    for i in range(n):
        crop = rgba.crop((bounds[i], 0, bounds[i + 1], rgba.height))
        bb = crop.getbbox()
        poses.append(crop.crop(bb))
    return poses


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
    OUT.mkdir(parents=True, exist_ok=True)
    s1 = key_and_split(ROOT / "tmp" / "dragon-sheet-gpt.png", 6)
    s2 = key_and_split(ROOT / "tmp" / "dragon-sheet2-gpt.png", 6)
    idle, walk, heavy, kick, hit, down = s1
    crouch, jump, block, cast, aura, victory = s2

    scale1 = TARGET_STANDING / idle.height
    scale2 = TARGET_STANDING / block.height  # block is a standing pose

    # state -> (pose, source-scale, frame count)
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
            out = OUT / f"{state}-{i}.png"
            frame.save(out)
            variants.append(f"public/assets/generated/dragon/{state}-{i}.png")
        frame.save(OUT / f"{state}.png")
        manifest_states.append({"state": state, "file": f"public/assets/generated/dragon/{state}.png", "variants": variants})

    # portrait: crop head/upper-body from the scaled idle
    idle_full = place(idle, scale1)
    bb = idle_full.getchannel("A").getbbox()
    top = bb[1]
    head = idle_full.crop((bb[0], top, bb[2], top + int((bb[3] - top) * 0.42)))
    side = max(head.width, head.height)
    sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    sq.alpha_composite(head, ((side - head.width) // 2, 0))
    sq.resize((224, 224), Image.Resampling.LANCZOS).save(OUT / "portrait.png")

    (OUT / "manifest.json").write_text(
        json.dumps({"source": "gpt-image-2 (2 sheets)", "canvasSize": list(CANVAS), "states": manifest_states}, indent=2),
        encoding="utf-8",
    )
    print(f"built dragon: {len(plan)} states, scale1={scale1:.3f} scale2={scale2:.3f}")


if __name__ == "__main__":
    main()
