from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "public" / "assets" / "generated"
CANVAS_SIZE = (320, 560)
FOOT_PADDING = 6
ALPHA_THRESHOLD = 20
MIN_COLUMN_PIXELS = 30
MIN_FRAME_WIDTH = 36
FRAME_COUNT = 11
RUN_FRAME_COUNT = 5
MIN_COMPONENT_AREA = 500

SHEETS = {
    "kai": "kai-movement-001-alpha.png",
    "nova": "nova-movement-001-alpha.png",
}


def find_runs(mask: np.ndarray) -> list[tuple[int, int]]:
    column_has_pixels = mask.sum(axis=0) > MIN_COLUMN_PIXELS
    padded = np.pad(column_has_pixels.astype(np.int8), (1, 1))
    starts = np.where(np.diff(padded) == 1)[0]
    ends = np.where(np.diff(padded) == -1)[0]
    return [
        (int(start), int(end))
        for start, end in zip(starts, ends)
        if end - start >= MIN_FRAME_WIDTH
    ]


def expand_box(
    mask: np.ndarray,
    x0: int,
    x1: int,
    x_padding: int = 2,
    y_padding: int = 14,
) -> tuple[int, int, int, int]:
    height, width = mask.shape
    x0 = max(0, x0 - x_padding)
    x1 = min(width, x1 + x_padding)
    rows = np.where(mask[:, x0:x1].any(axis=1))[0]
    if len(rows) == 0:
        raise RuntimeError("Detected movement frame had no visible pixels")
    y0 = max(0, int(rows[0]) - y_padding)
    y1 = min(height, int(rows[-1]) + y_padding + 1)
    return x0, y0, x1, y1


def frame_boxes(source: Image.Image) -> list[tuple[int, int, int, int]]:
    mask = np.array(source.getchannel("A")) > ALPHA_THRESHOLD
    runs = find_runs(mask)

    if len(runs) != FRAME_COUNT:
        raise RuntimeError(f"Expected {FRAME_COUNT} movement frames, found {len(runs)}")

    return [expand_box(mask, x0, x1) for x0, x1 in runs]


def trim_alpha(image: Image.Image) -> Image.Image:
    alpha = np.array(image.getchannel("A"))
    labels, count = ndimage.label(alpha > ALPHA_THRESHOLD, structure=np.ones((3, 3), dtype=bool))
    if count == 0:
        raise RuntimeError("Movement frame crop had no visible pixels")

    areas = np.bincount(labels.ravel())
    keep_labels = [label for label in range(1, count + 1) if areas[label] >= MIN_COMPONENT_AREA]
    if not keep_labels:
        keep_labels = [int(np.argmax(areas[1:]) + 1)]

    keep_mask = np.isin(labels, keep_labels)
    cleaned = Image.new("RGBA", image.size, (0, 0, 0, 0))
    cleaned.alpha_composite(image)
    cleaned.putalpha(Image.fromarray((keep_mask.astype(np.uint8) * 255), mode="L"))

    bbox = cleaned.getbbox()
    if bbox is None:
        raise RuntimeError("Movement frame crop had no visible pixels after cleanup")
    return cleaned.crop(bbox)


def write_frame(trimmed: Image.Image, output: Path) -> None:
    canvas = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    paste_x = (CANVAS_SIZE[0] - trimmed.width) // 2
    paste_y = CANVAS_SIZE[1] - trimmed.height - FOOT_PADDING
    canvas.alpha_composite(trimmed, (paste_x, paste_y))
    canvas.save(output)


def slice_sheet(name: str, filename: str) -> dict[str, object]:
    source = Image.open(GENERATED / filename).convert("RGBA")
    out_dir = GENERATED / name
    out_dir.mkdir(parents=True, exist_ok=True)
    boxes = frame_boxes(source)
    frames = []

    for index, box in enumerate(boxes):
        motion = "run" if index < RUN_FRAME_COUNT else "jump-tuck"
        motion_index = index if index < RUN_FRAME_COUNT else index - RUN_FRAME_COUNT
        frame = trim_alpha(source.crop(box))
        output = out_dir / f"{motion}-{motion_index}.png"
        write_frame(frame, output)
        if motion_index == 0:
            write_frame(frame, out_dir / f"{motion}.png")
        frames.append(
            {
                "motion": motion,
                "index": motion_index,
                "file": str(output.relative_to(ROOT)).replace("\\", "/"),
                "sourceBox": list(box),
                "trimmedSize": [frame.width, frame.height],
            }
        )

    with (out_dir / "movement-manifest.json").open("w", encoding="utf-8") as file:
        json.dump(
            {
                "source": str((GENERATED / filename).relative_to(ROOT)).replace("\\", "/"),
                "canvasSize": list(CANVAS_SIZE),
                "frames": frames,
            },
            file,
            indent=2,
        )

    return {"fighter": name, "frames": len(frames)}


def main() -> None:
    print(json.dumps([slice_sheet(name, filename) for name, filename in SHEETS.items()], indent=2))


if __name__ == "__main__":
    main()
