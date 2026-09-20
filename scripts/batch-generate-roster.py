"""Generate 12 single-pose images per roster character via local ComfyUI.

One figure per image = zero crop-bleed by construction (no sheet splitting).
The idle pose is generated text-to-image; the other 11 poses are
reference-conditioned on it so the character stays on-model.

Outputs tmp/roster/<name>/<pose>.png

Usage: python scripts/batch-generate-roster.py [--only talon,ryu]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from roster import CHARACTERS, SIGNATURE  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tmp" / "roster"
PY = sys.executable

STYLE = (
    "Detailed 16-bit era arcade fighting game pixel art, crisp dark outlines, hand-placed pixel "
    "shading, limited palette, no anti-aliasing, no blur, no text, no labels, no watermark. "
    "A single full-body character, side view facing right, feet near the bottom of the frame, "
    "on a pure flat solid bright green chroma key background #00ff00 that fills the entire image, "
    "no floor, no ground shadow, nothing else in the image."
)
HEAD_REF = (
    "Using the EXACT SAME character as the reference image (identical design, colors, proportions "
    "and scale), draw the character in a new pose: "
)

# pose name -> (prompt fragment, width, height)
POSES: dict[str, tuple[str, int, int]] = {
    "idle": ("standing in a relaxed ready fighting stance", 832, 1024),
    "walk": ("mid walking step, one foot forward", 832, 1024),
    "heavy": ("throwing a heavy punch, fist fully extended forward", 1024, 1024),
    "kick": ("performing a high roundhouse kick", 1024, 1024),
    "hit": ("staggering backward from being hit, recoiling", 832, 1024),
    "knockdown": ("knocked down, lying flat on the ground on their back", 1024, 640),
    "crouch": ("in a deep crouch, ducking low", 832, 832),
    "jump": ("jumping upward with knees tucked", 832, 1024),
    "block": ("in a defensive block, both arms raised guarding the face and chest", 832, 1024),
    "cast": ("__SIGNATURE_CAST__", 1024, 1024),
    "super": ("__SIGNATURE_SUPER__", 1024, 1024),
    "victory": ("in a triumphant victory pose", 832, 1024),
}


def validate_pose(path: Path) -> str | None:
    im = np.array(Image.open(path).convert("RGB")).astype(int)
    h, w = im.shape[:2]
    corner = np.median(np.stack([im[5, 5], im[5, w - 6], im[5, w // 2]]), axis=0)
    if not (corner[1] > 150 and corner[1] - corner[0] > 60 and corner[1] - corner[2] > 60):
        return f"background not chroma green (corner {corner.astype(int).tolist()})"
    near_bg = np.abs(im - corner).max(axis=2) < 70
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    green_dom = (g > 120) & (g - r > 55) & (g - b > 55)
    char = ~(near_bg | green_dom)
    frac = char.mean()
    if frac < 0.05:
        return f"almost no character ({frac:.2f})"
    if frac > 0.7:
        return f"too little background ({frac:.2f})"
    rows = np.where(char.any(axis=1))[0]
    cols = np.where(char.any(axis=0))[0]
    if (rows[-1] - rows[0]) < h * 0.35 and (cols[-1] - cols[0]) < w * 0.35:
        return "figure too small"
    return None


def generate(prompt: str, out: Path, seed: int, width: int, height: int, ref: Path | None) -> bool:
    cmd = [PY, "scripts/comfy-generate.py", "--prompt", prompt, "--width", str(width),
           "--height", str(height), "--seed", str(seed), "--out", str(out)]
    if ref is not None:
        cmd += ["--ref", str(ref)]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-400:] + r.stderr[-400:], flush=True)
        return False
    return True


def make_pose(name: str, pose: str, prompt: str, ref: Path | None, base_seed: int, width: int, height: int) -> bool:
    out = OUT / name / f"{pose}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(3):
        seed = base_seed + attempt * 131
        if not generate(prompt, out, seed, width, height, ref):
            continue
        reason = validate_pose(out)
        if reason is None:
            print(f"{name}/{pose} OK", flush=True)
            return True
        print(f"{name}/{pose} rejected: {reason}", flush=True)
    return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", default=None)
    args = parser.parse_args()
    wanted = set(args.only.split(",")) if args.only else None

    failed = []
    for index, (name, desc) in enumerate(CHARACTERS.items()):
        if wanted and name not in wanted:
            continue
        cast, super_pose = SIGNATURE[name]
        base = 9000 + index * 977
        anchor = OUT / name / "idle.png"

        idle_fragment, iw, ih = POSES["idle"]
        idle_prompt = f"Character: {desc}, {idle_fragment}. {STYLE}"
        if not (anchor.exists() and validate_pose(anchor) is None):
            if not make_pose(name, "idle", idle_prompt, None, base, iw, ih):
                failed.append(f"{name}/idle")
                continue

        for step, (pose, (fragment, w, h)) in enumerate(POSES.items()):
            if pose == "idle":
                continue
            fragment = fragment.replace("__SIGNATURE_CAST__", cast).replace("__SIGNATURE_SUPER__", super_pose)
            prompt = HEAD_REF + fragment + ". " + STYLE
            target = OUT / name / f"{pose}.png"
            if not (target.exists() and validate_pose(target) is None):
                if not make_pose(name, pose, prompt, anchor, base + 13 * (step + 1), w, h):
                    failed.append(f"{name}/{pose}")

    print(f"DONE. failed: {failed if failed else 'none'}", flush=True)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
