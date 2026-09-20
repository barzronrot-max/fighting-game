"""Slice a chroma-key ( #00ff00 ) animation strip into normalized per-frame PNGs.

- Removes the green chroma background to alpha.
- Detects frame islands (rows first, then columns) so 1- or 2-row strips work.
- Scales every frame of the state uniformly so the tallest frame matches the
  fighter's existing idle sprite height (same pixel-per-unit scale).
- Writes <state>-<n>.png (+ <state>.png alias) on the shared 320x560 canvas,
  bottom-aligned with the same foot padding the rest of the pipeline uses.
- Updates the fighter's manifest.json states list.

Usage:
  python scripts/slice-state-strips.py --strip public/assets/generated/kai-block-001.png \
      --fighter kai --state block --frames 3 [--scale-tweak 1.0] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "public" / "assets" / "generated"
CANVAS_SIZE = (320, 560)
FOOT_PADDING = 6
MIN_COMPONENT_AREA = 400
ALPHA_THRESHOLD = 20


def chroma_to_alpha(image: Image.Image) -> Image.Image:
    rgba = np.array(image.convert("RGBA")).astype(np.int16)
    r, g, b = rgba[..., 0], rgba[..., 1], rgba[..., 2]
    green_mask = (g > 130) & (g - r > 70) & (g - b > 70)
    rgba[..., 3] = np.where(green_mask, 0, 255)
    return Image.fromarray(rgba.astype(np.uint8), mode="RGBA")


def detect_islands(alpha_mask: np.ndarray) -> list[tuple[int, int, int, int]]:
    """Return frame bounding boxes (x0, y0, x1, y1) sorted in reading order."""
    # Row bands
    row_has = alpha_mask.sum(axis=1) > 40
    row_bands = mask_runs(row_has, min_len=40)
    boxes: list[tuple[int, int, int, int]] = []
    for y0, y1 in row_bands:
        band = alpha_mask[y0:y1]
        col_has = band.sum(axis=0) > 12
        for x0, x1 in mask_runs(col_has, min_len=36):
            boxes.append((x0, y0, x1, y1))
    return boxes


def mask_runs(flags: np.ndarray, min_len: int) -> list[tuple[int, int]]:
    padded = np.pad(flags.astype(np.int8), (1, 1))
    starts = np.where(np.diff(padded) == 1)[0]
    ends = np.where(np.diff(padded) == -1)[0]
    return [(int(s), int(e)) for s, e in zip(starts, ends) if e - s >= min_len]


def clean_trim(image: Image.Image) -> Image.Image:
    alpha = np.array(image.getchannel("A"))
    labels, count = ndimage.label(alpha > ALPHA_THRESHOLD, structure=np.ones((3, 3), dtype=bool))
    if count == 0:
        raise RuntimeError("Frame crop had no visible pixels")
    areas = np.bincount(labels.ravel())
    keep = [label for label in range(1, count + 1) if areas[label] >= MIN_COMPONENT_AREA]
    if not keep:
        keep = [int(np.argmax(areas[1:]) + 1)]
    keep_mask = np.isin(labels, keep)
    cleaned = image.copy()
    cleaned.putalpha(Image.fromarray((np.array(image.getchannel("A")) * keep_mask).astype(np.uint8), mode="L"))
    bbox = cleaned.getbbox()
    if bbox is None:
        raise RuntimeError("Frame crop empty after cleanup")
    return cleaned.crop(bbox)


def idle_reference_height(fighter: str) -> int:
    idle = Image.open(GENERATED / fighter / "idle-0.png").convert("RGBA")
    bbox = idle.getchannel("A").getbbox()
    if bbox is None:
        raise RuntimeError(f"{fighter} idle-0 has no pixels")
    return bbox[3] - bbox[1]


def compose(frame: Image.Image, scale: float) -> Image.Image:
    new_size = (max(1, round(frame.width * scale)), max(1, round(frame.height * scale)))
    resized = frame.resize(new_size, Image.Resampling.LANCZOS)
    # Snap alpha back to hard edges to keep the pixel-art look
    alpha = np.array(resized.getchannel("A"))
    resized.putalpha(Image.fromarray(((alpha > 110) * 255).astype(np.uint8), mode="L"))

    if resized.width > CANVAS_SIZE[0]:
        # Keep the densest window (the character), clip sparse effect overflow.
        density = (np.array(resized.getchannel("A")) > 0).sum(axis=0)
        window = CANVAS_SIZE[0]
        cumulative = np.concatenate(([0], np.cumsum(density)))
        sums = cumulative[window:] - cumulative[:-window]
        start = int(np.argmax(sums))
        resized = resized.crop((start, 0, start + window, resized.height))

    canvas = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    paste_x = (CANVAS_SIZE[0] - resized.width) // 2
    paste_y = CANVAS_SIZE[1] - resized.height - FOOT_PADDING
    canvas.alpha_composite(resized, (max(0, paste_x), max(0, paste_y)))
    return canvas


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strip", required=True)
    parser.add_argument("--fighter", required=True, choices=["kai", "nova"])
    parser.add_argument("--state", required=True)
    parser.add_argument("--frames", type=int, required=True)
    parser.add_argument("--scale-tweak", type=float, default=1.0)
    parser.add_argument("--max-width-ratio", type=float, default=1.75)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    strip_path = ROOT / args.strip if not Path(args.strip).is_absolute() else Path(args.strip)
    source = chroma_to_alpha(Image.open(strip_path))
    alpha_mask = np.array(source.getchannel("A")) > ALPHA_THRESHOLD
    boxes = detect_islands(alpha_mask)

    # Detached effects (projectile orbs, dust) can register as extra islands.
    # Merge the closest horizontal neighbours until we match the expected count.
    while len(boxes) > args.frames:
        gaps = [
            (boxes[i + 1][0] - boxes[i][2], i)
            for i in range(len(boxes) - 1)
        ]
        smallest_gap, index = min(gaps)
        if smallest_gap > 120:
            break
        a, b = boxes[index], boxes[index + 1]
        boxes[index : index + 2] = [(a[0], min(a[1], b[1]), b[2], max(a[3], b[3]))]

    # Thin effect bridges (auras, energy trails) can weld neighbouring poses
    # into one island. Split the widest box at its weakest internal column
    # until we reach the expected count.
    while len(boxes) < args.frames:
        widths = [box[2] - box[0] for box in boxes]
        widest_index = max(range(len(boxes)), key=lambda i: widths[i])
        x0, y0, x1, y1 = boxes[widest_index]
        if x1 - x0 < 160:
            break
        column_density = alpha_mask[y0:y1, x0:x1].sum(axis=0)
        inner = slice(int((x1 - x0) * 0.25), int((x1 - x0) * 0.75))
        split_at = x0 + int(np.argmin(column_density[inner])) + inner.start
        print(f"splitting box {boxes[widest_index]} at x={split_at}")
        boxes[widest_index : widest_index + 1] = [(x0, y0, split_at, y1), (split_at + 1, y0, x1, y1)]
        boxes.sort(key=lambda box: box[0])

    print(f"detected {len(boxes)} islands (expected {args.frames})")
    if args.dry_run or len(boxes) != args.frames:
        for box in boxes:
            print(f"  box {box} size {box[2] - box[0]}x{box[3] - box[1]}")
        if len(boxes) != args.frames:
            raise SystemExit(2)
        return

    # Sanity: a merged pair of poses shows up as one abnormally wide box.
    widths = sorted(box[2] - box[0] for box in boxes)
    median_width = widths[len(widths) // 2]
    for box in boxes:
        if box[2] - box[0] > median_width * args.max_width_ratio:
            print(f"box {box} is {box[2] - box[0]}px wide vs median {median_width} - likely merged poses")
            raise SystemExit(2)

    frames = [clean_trim(source.crop(box)) for box in boxes]
    tallest = max(frame.height for frame in frames)
    scale = idle_reference_height(args.fighter) / tallest * args.scale_tweak
    # Never overflow the canvas height; width overflow is density-cropped in compose()
    scale = min(scale, (CANVAS_SIZE[1] - FOOT_PADDING - 4) / tallest)

    out_dir = GENERATED / args.fighter
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for index, frame in enumerate(frames):
        canvas = compose(frame, scale)
        output = out_dir / f"{args.state}-{index}.png"
        canvas.save(output)
        written.append(str(output.relative_to(ROOT)).replace("\\", "/"))
        if index == 0:
            canvas.save(out_dir / f"{args.state}.png")

    manifest_path = out_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["states"] = [entry for entry in manifest["states"] if entry["state"] != args.state]
    manifest["states"].append(
        {
            "state": args.state,
            "file": f"public/assets/generated/{args.fighter}/{args.state}.png",
            "variants": written,
            "source": str(strip_path.relative_to(ROOT)).replace("\\", "/") if strip_path.is_relative_to(ROOT) else str(strip_path),
            "scale": round(scale, 4),
        }
    )
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"wrote {len(written)} frames at scale {scale:.4f}")


if __name__ == "__main__":
    main()
