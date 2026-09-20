"""Slice a chroma-key VFX strip (projectiles, bursts, word-art) into frames.

Unlike character strips there is no scale reference: each frame is trimmed and
centered on a shared square canvas sized to the largest frame in the strip.

Usage:
  python scripts/slice-vfx-strip.py --strip tmp/pulse-travel.png \
      --name projectile-special --frames 4 [--single]
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
VFX_DIR = ROOT / "public" / "assets" / "generated" / "vfx"
ALPHA_THRESHOLD = 20


def chroma_to_alpha(image: Image.Image) -> Image.Image:
    rgba = np.array(image.convert("RGBA")).astype(np.int16)
    r, g, b = rgba[..., 0], rgba[..., 1], rgba[..., 2]
    green_mask = (g > 130) & (g - r > 70) & (g - b > 70)
    rgba[..., 3] = np.where(green_mask, 0, 255)
    return Image.fromarray(rgba.astype(np.uint8), mode="RGBA")


def mask_runs(flags: np.ndarray, min_len: int) -> list[tuple[int, int]]:
    padded = np.pad(flags.astype(np.int8), (1, 1))
    starts = np.where(np.diff(padded) == 1)[0]
    ends = np.where(np.diff(padded) == -1)[0]
    return [(int(s), int(e)) for s, e in zip(starts, ends) if e - s >= min_len]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strip", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--frames", type=int, required=True)
    parser.add_argument("--single", action="store_true", help="whole image is one frame")
    parser.add_argument("--max-side", type=int, default=None, help="downscale output canvases to this side length")
    args = parser.parse_args()

    source = chroma_to_alpha(Image.open(ROOT / args.strip if not Path(args.strip).is_absolute() else Path(args.strip)))
    mask = np.array(source.getchannel("A")) > ALPHA_THRESHOLD

    if args.single:
        boxes = [source.getbbox()]
    else:
        col_has = mask.sum(axis=0) > 6
        boxes = [(x0, 0, x1, source.height) for x0, x1 in mask_runs(col_has, min_len=24)]
        while len(boxes) > args.frames:
            gaps = [(boxes[i + 1][0] - boxes[i][2], i) for i in range(len(boxes) - 1)]
            gap, index = min(gaps)
            if gap > 100:
                break
            a, b = boxes[index], boxes[index + 1]
            boxes[index : index + 2] = [(a[0], 0, b[2], source.height)]
        # Split tail-bridged frames at their weakest internal column.
        while len(boxes) < args.frames:
            widths = [box[2] - box[0] for box in boxes]
            widest = max(range(len(boxes)), key=lambda i: widths[i])
            x0, _, x1, _ = boxes[widest]
            if x1 - x0 < 120:
                break
            density = mask[:, x0:x1].sum(axis=0)
            inner = slice(int((x1 - x0) * 0.25), int((x1 - x0) * 0.75))
            split_at = x0 + int(np.argmin(density[inner])) + inner.start
            print(f"splitting box {boxes[widest]} at x={split_at}")
            boxes[widest : widest + 1] = [(x0, 0, split_at, source.height), (split_at + 1, 0, x1, source.height)]
            boxes.sort(key=lambda box: box[0])

    if len(boxes) != args.frames:
        print(f"detected {len(boxes)} frames (expected {args.frames})")
        for box in boxes:
            print(f"  box {box}")
        raise SystemExit(2)

    trimmed = []
    for box in boxes:
        crop = source.crop(box)
        bbox = crop.getbbox()
        if bbox is None:
            raise SystemExit("empty frame")
        trimmed.append(crop.crop(bbox))

    VFX_DIR.mkdir(parents=True, exist_ok=True)
    if args.single:
        # Keep the natural aspect for single images (word-art, banners).
        frame = trimmed[0]
        if args.max_side and frame.width > args.max_side:
            ratio = args.max_side / frame.width
            frame = frame.resize((args.max_side, max(1, round(frame.height * ratio))), Image.Resampling.LANCZOS)
            alpha = np.array(frame.getchannel("A"))
            frame.putalpha(Image.fromarray(((alpha > 110) * 255).astype(np.uint8), mode="L"))
        output = VFX_DIR / f"{args.name}.png"
        frame.save(output)
        print(f"wrote {output.relative_to(ROOT)} ({frame.width}x{frame.height})")
        return

    side = max(max(f.width, f.height) for f in trimmed)
    side = int(side * 1.06)  # small margin
    for index, frame in enumerate(trimmed):
        canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        canvas.alpha_composite(frame, ((side - frame.width) // 2, (side - frame.height) // 2))
        if args.max_side and side > args.max_side:
            canvas = canvas.resize((args.max_side, args.max_side), Image.Resampling.LANCZOS)
            alpha = np.array(canvas.getchannel("A"))
            canvas.putalpha(Image.fromarray(((alpha > 110) * 255).astype(np.uint8), mode="L"))
        suffix = "" if args.single else f"-{index}"
        output = VFX_DIR / f"{args.name}{suffix}.png"
        canvas.save(output)
        print(f"wrote {output.relative_to(ROOT)} ({canvas.width}x{canvas.height})")


if __name__ == "__main__":
    main()
