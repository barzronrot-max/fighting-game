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
MIN_COMPONENT_AREA = 1200
FRAME_COUNT = 7

SHEETS = {
    "kai": "kai-jump-bent-001-alpha.png",
    "nova": "nova-jump-bent-001-alpha.png",
}


def detect_boxes(source: Image.Image) -> tuple[np.ndarray, list[dict[str, object]]]:
    alpha = np.array(source.getchannel("A"))
    labels, count = ndimage.label(alpha > ALPHA_THRESHOLD, structure=np.ones((3, 3), dtype=bool))
    objects = ndimage.find_objects(labels)
    components = []

    for label in range(1, count + 1):
        bounds = objects[label - 1]
        if bounds is None:
            continue

        ys, xs = bounds
        area = int(np.count_nonzero(labels[bounds] == label))
        if area < MIN_COMPONENT_AREA:
            continue

        x0, x1 = xs.start, xs.stop
        y0, y1 = ys.start, ys.stop
        components.append(
            {
                "label": label,
                "area": area,
                "box": (x0, y0, x1, y1),
                "center": (x0 + x1) / 2,
            }
        )

    # Use the largest visible character components, ordered left-to-right.
    components = sorted(components, key=lambda item: item["area"], reverse=True)[:FRAME_COUNT]
    if len(components) != FRAME_COUNT:
        raise RuntimeError(f"Expected {FRAME_COUNT} jump poses, found {len(components)}")

    return labels, sorted(components, key=lambda item: item["center"])


def isolate(source: Image.Image, labels: np.ndarray, component: dict[str, object]) -> Image.Image:
    x0, y0, x1, y1 = component["box"]
    crop = source.crop((x0, y0, x1, y1))
    label = component["label"]
    mask = Image.fromarray(((labels[y0:y1, x0:x1] == label).astype(np.uint8) * 255), mode="L")
    isolated = Image.new("RGBA", crop.size, (0, 0, 0, 0))
    isolated.alpha_composite(crop)
    isolated.putalpha(mask)
    bbox = isolated.getbbox()
    if bbox is None:
        raise RuntimeError("Detected jump pose had no visible pixels after isolation")
    return isolated.crop(bbox)


def write_frame(trimmed: Image.Image, output: Path, dx: int = 0, dy: int = 0) -> None:
    canvas = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    paste_x = (CANVAS_SIZE[0] - trimmed.width) // 2 + dx
    paste_y = CANVAS_SIZE[1] - trimmed.height - FOOT_PADDING + dy
    canvas.alpha_composite(trimmed, (paste_x, paste_y))
    canvas.save(output)


def slice_sheet(name: str, filename: str) -> dict[str, object]:
    source = Image.open(GENERATED / filename).convert("RGBA")
    labels, components = detect_boxes(source)
    out_dir = GENERATED / name
    frames = []

    for index, component in enumerate(components):
        trimmed = isolate(source, labels, component)
        output = out_dir / f"jump-{index}.png"
        write_frame(trimmed, output)
        if index == 2:
            write_frame(trimmed, out_dir / "jump.png")
        frames.append(
            {
                "index": index,
                "file": str(output.relative_to(ROOT)).replace("\\", "/"),
                "sourceBox": list(component["box"]),
                "trimmedSize": [trimmed.width, trimmed.height],
            }
        )

    manifest_path = out_dir / "jump-manifest.json"
    with manifest_path.open("w", encoding="utf-8") as file:
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
