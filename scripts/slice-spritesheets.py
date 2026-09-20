from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "public" / "assets" / "generated"
STATES = ["idle", "walk", "crouch", "jump", "light", "heavy", "kick", "hit"]
CANVAS_SIZE = (320, 560)
FOOT_PADDING = 6
ALPHA_THRESHOLD = 20
MIN_COMPONENT_AREA = 1200
VARIANT_SPECS = {
    "idle": [
        {"dx": 0, "dy": 0, "scale_y": 1.0},
        {"dx": 0, "dy": -1, "scale_y": 1.006},
        {"dx": 0, "dy": -2, "scale_y": 1.012},
        {"dx": 0, "dy": -2, "scale_y": 1.016},
        {"dx": 0, "dy": -1, "scale_y": 1.01},
        {"dx": 0, "dy": 0, "scale_y": 1.004},
        {"dx": 0, "dy": 1, "scale_y": 0.998},
        {"dx": 0, "dy": 0, "scale_y": 1.0},
    ],
    "walk": [
        {"dx": -3, "dy": 0, "angle": -1.0},
        {"dx": -1, "dy": -2, "angle": -0.4},
        {"dx": 1, "dy": -1, "angle": 0.3},
        {"dx": 3, "dy": 0, "angle": 0.8},
        {"dx": 2, "dy": -2, "angle": 0.4},
        {"dx": 0, "dy": -1, "angle": 0.0},
        {"dx": -2, "dy": 0, "angle": -0.7},
        {"dx": -3, "dy": -1, "angle": -0.2},
    ],
    "crouch": [
        {"dx": 0, "dy": 0, "scale_y": 1.0},
        {"dx": 0, "dy": 2, "scale_y": 0.99},
        {"dx": 0, "dy": 3, "scale_y": 0.982},
        {"dx": 0, "dy": 1, "scale_y": 0.994},
    ],
    "jump": [
        {"dx": -2, "dy": -5, "angle": -3.0, "scale_y": 1.01},
        {"dx": -1, "dy": -11, "angle": -1.2, "scale_y": 1.018},
        {"dx": 0, "dy": -16, "angle": 0.0, "scale_y": 1.02},
        {"dx": 1, "dy": -9, "angle": 1.4, "scale_y": 1.012},
        {"dx": 2, "dy": -2, "angle": 3.0, "scale_y": 1.004},
    ],
    "light": [
        {"dx": -6, "dy": 1, "angle": -1.0, "scale_x": 0.992},
        {"dx": -3, "dy": 0, "angle": -0.4, "scale_x": 1.0},
        {"dx": 2, "dy": -1, "angle": 0.0, "scale_x": 1.012},
        {"dx": 4, "dy": 0, "angle": 0.5, "scale_x": 1.006},
        {"dx": 0, "dy": 1, "angle": 0.0, "scale_x": 0.998},
    ],
    "heavy": [
        {"dx": -8, "dy": 2, "angle": -1.8, "scale_x": 0.986},
        {"dx": -4, "dy": 0, "angle": -0.8, "scale_x": 0.996},
        {"dx": 2, "dy": -2, "angle": 0.0, "scale_x": 1.018},
        {"dx": 5, "dy": -1, "angle": 0.8, "scale_x": 1.01},
        {"dx": 1, "dy": 1, "angle": 0.3, "scale_x": 0.998},
    ],
    "kick": [
        {"dx": -7, "dy": 2, "angle": -1.4, "scale_x": 0.99},
        {"dx": -3, "dy": 0, "angle": -0.5, "scale_x": 1.0},
        {"dx": 3, "dy": -2, "angle": 0.0, "scale_x": 1.018},
        {"dx": 6, "dy": -1, "angle": 0.8, "scale_x": 1.01},
        {"dx": 2, "dy": 1, "angle": 0.3, "scale_x": 0.996},
    ],
    "hit": [
        {"dx": 0, "dy": 0, "angle": 0.0},
        {"dx": 4, "dy": -1, "angle": 1.2},
        {"dx": 7, "dy": 1, "angle": 2.4},
    ],
}

SHEETS = {
    "kai": "kai-spritesheet-001-alpha.png",
    "nova": "nova-spritesheet-001-alpha.png",
}


def detect_pose_boxes(source: Image.Image) -> tuple[np.ndarray, list[dict[str, object]]]:
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

    width = source.width
    pose_components = []
    used_labels = set()
    for index in range(len(STATES)):
        expected_center = (index + 0.5) * width / len(STATES)
        candidates = [component for component in components if component["label"] not in used_labels]
        if not candidates:
            raise RuntimeError(f"No alpha component candidates left for frame {index}")

        component = min(candidates, key=lambda item: abs(item["center"] - expected_center))
        used_labels.add(component["label"])
        pose_components.append(component)

    return labels, pose_components


def alpha_crop(
    source: Image.Image,
    labels: np.ndarray,
    component: dict[str, object],
    padding: int = 10,
) -> Image.Image:
    box = component["box"]
    if not isinstance(box, tuple):
        raise RuntimeError("Component box was not detected")

    x0, y0, x1, y1 = box
    x0 = max(0, x0 - padding)
    y0 = max(0, y0 - padding)
    x1 = min(source.width, x1 + padding)
    y1 = min(source.height, y1 + padding)
    crop = source.crop((x0, y0, x1, y1))
    label = component["label"]
    label_mask = (labels[y0:y1, x0:x1] == label).astype(np.uint8) * 255
    mask = Image.fromarray(label_mask, mode="L")
    isolated = Image.new("RGBA", crop.size, (0, 0, 0, 0))
    isolated.alpha_composite(crop)
    isolated.putalpha(mask)
    return isolated


def center_on_canvas(trimmed: Image.Image, dx: int = 0, dy: int = 0) -> Image.Image:
    canvas = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    paste_x = (CANVAS_SIZE[0] - trimmed.width) // 2 + dx
    paste_y = CANVAS_SIZE[1] - trimmed.height - FOOT_PADDING + dy
    canvas.alpha_composite(trimmed, (paste_x, paste_y))
    return canvas


def transform_trimmed(trimmed: Image.Image, spec: dict[str, float]) -> Image.Image:
    scale_x = float(spec.get("scale_x", 1.0))
    scale_y = float(spec.get("scale_y", 1.0))
    angle = float(spec.get("angle", 0.0))
    dx = int(spec.get("dx", 0))
    dy = int(spec.get("dy", 0))

    transformed = trimmed
    if scale_x != 1.0 or scale_y != 1.0:
        width = max(1, round(transformed.width * scale_x))
        height = max(1, round(transformed.height * scale_y))
        transformed = transformed.resize((width, height), Image.Resampling.NEAREST)

    if angle:
        transformed = transformed.rotate(angle, resample=Image.Resampling.NEAREST, expand=True)

    bbox = transformed.getbbox()
    if bbox is not None:
        transformed = transformed.crop(bbox)

    return center_on_canvas(transformed, dx, dy)


def slice_sheet(name: str, filename: str) -> dict[str, object]:
    source = Image.open(GENERATED / filename).convert("RGBA")
    out_dir = GENERATED / name
    out_dir.mkdir(parents=True, exist_ok=True)
    for state in STATES:
        for output in [out_dir / f"{state}.png"] + [
            out_dir / f"{state}-{variant_index}.png"
            for variant_index in range(len(VARIANT_SPECS[state]))
        ]:
            output.unlink(missing_ok=True)

    labels, pose_components = detect_pose_boxes(source)

    frames = []
    for state, component in zip(STATES, pose_components):
        trimmed = alpha_crop(source, labels, component)
        bbox = trimmed.getbbox()
        if bbox is None:
            raise RuntimeError(f"{name}:{state} has no visible pixels")

        trimmed = trimmed.crop(bbox)
        canvas = center_on_canvas(trimmed)
        output = out_dir / f"{state}.png"
        canvas.save(output)

        variants = []
        for variant_index, spec in enumerate(VARIANT_SPECS[state]):
            variant = transform_trimmed(trimmed, spec)
            variant_output = out_dir / f"{state}-{variant_index}.png"
            variant.save(variant_output)
            variants.append(str(variant_output.relative_to(ROOT)).replace("\\", "/"))

        frames.append(
            {
                "state": state,
                "file": str(output.relative_to(ROOT)).replace("\\", "/"),
                "variants": variants,
                "sourceBox": list(component["box"]),
                "trimmedSize": [trimmed.width, trimmed.height],
            }
        )

    manifest = {
        "source": str((GENERATED / filename).relative_to(ROOT)).replace("\\", "/"),
        "canvasSize": list(CANVAS_SIZE),
        "footPadding": FOOT_PADDING,
        "states": frames,
    }

    with (out_dir / "manifest.json").open("w", encoding="utf-8") as file:
        json.dump(manifest, file, indent=2)

    return manifest


def main() -> None:
    manifests = {name: slice_sheet(name, filename) for name, filename in SHEETS.items()}
    print(json.dumps({name: data["canvasSize"] for name, data in manifests.items()}, indent=2))


if __name__ == "__main__":
    main()
