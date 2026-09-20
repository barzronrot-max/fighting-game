"""Generate + slice all missing character state strips via the local ComfyUI.

Runs sequentially (single GPU). For every state: generate with the fighter's
reference sheet, slice; if the detected frame count is wrong, re-roll with a
new seed (up to 4 attempts).

Usage: python scripts/batch-generate-states.py [--only kai-block,nova-super]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable

KAI = (
    "Kai: young male fighter with spiky black anime hair, teal sleeveless open vest with gold trim "
    "worn over a black tank top, golden sash tied at the waist with hanging tails, dark navy baggy "
    "pants with golden ornamental embroidery, teal-and-orange sneakers, black fingerless gloves, warm skin"
)
NOVA = (
    "Nova: young female kickboxer with a long dark-burgundy high ponytail tied with a light blue band, "
    "crimson-red cropped open jacket over a dark sports top, bare midriff, red sash at the waist, dark "
    "violet leggings with red ornamental patterns, light blue hand wraps on both hands, light blue ankle "
    "cuffs and red-and-blue sneakers, warm skin, cool determined expression"
)

SIZES = {3: (1536, 768), 4: (1792, 768), 5: (2048, 704), 6: (2304, 640)}

ANIMATIONS: dict[str, tuple[int, str]] = {
    "block": (3, "high guard BLOCK: "
        "Frame 1 - raising both forearms across the face and chest, weight settling back. "
        "Frame 2 - braced full guard, elbows tucked, slight lean away from an incoming attack. "
        "Frame 3 - guard absorbing an impact, body pushed back slightly, forearms tight. "
        "Defensive grounded poses, no attacking limbs extended."),
    "landing": (3, "LANDING from a jump: "
        "Frame 1 - feet touching down, knees beginning to bend to absorb the impact. "
        "Frame 2 - deep absorbing crouch, arms slightly out for balance. "
        "Frame 3 - rising back toward neutral fighting stance."),
    "knockdown": (5, "KNOCKDOWN, launched and falling backward: "
        "Frame 1 - struck and recoiling, feet leaving the ground. "
        "Frame 2 - airborne, body tilting backward, limbs trailing. "
        "Frame 3 - nearly horizontal in the air, back toward the ground. "
        "Frame 4 - hitting the floor on the back. "
        "Frame 5 - lying flat on the back on the ground, dazed. Dramatic, readable, no blood."),
    "wake": (4, "WAKE-UP, getting back to the feet: "
        "Frame 1 - lying on the ground starting to push up. "
        "Frame 2 - up on one knee, one hand on the floor. "
        "Frame 3 - rising, regaining balance. "
        "Frame 4 - back to neutral fighting stance, determined expression."),
    "ko": (4, "KO DEFEAT collapse: "
        "Frame 1 - final hit recoil, head snapping back. "
        "Frame 2 - legs buckling, falling. "
        "Frame 3 - crumpling toward the floor. "
        "Frame 4 - lying motionless on the ground, defeated. Dramatic, stylized, no gore."),
    "victory": (5, ""),  # per-fighter, filled below
    "special": (5, "casting a cyan energy PULSE projectile forward: "
        "Frame 1 - winding up, drawing the rear hand back as bright cyan energy gathers in the palm. "
        "Frame 2 - cyan energy charging brighter at the hip. "
        "Frame 3 - thrusting both palms forward releasing the pulse. "
        "Frame 4 - follow-through, arms fully extended, a bright cyan energy orb just past the hands. "
        "Frame 5 - recovering toward fighting stance."),
    "super": (5, "OVERDRIVE super move with magenta-pink energy aura. The character's full "
        "body must be clearly visible in every pose; the magenta energy only forms a glowing "
        "aura around the body and fists, never a separate beam, never a projectile, never an "
        "energy blast panel on its own: "
        "Pose 1 - dramatic charge stance, faint magenta aura outlining the body. "
        "Pose 2 - the aura flaring stronger, hair and clothes lifted by the energy. "
        "Pose 3 - explosive forward lunge, aura trailing behind the body. "
        "Pose 4 - a powerful punch at full extension with a compact magenta glow around the fist only. "
        "Pose 5 - recovering to fighting stance, aura fading. High drama, bold readable silhouette."),
    "throw": (4, "close-range THROW grab, exactly 4 clearly separated poses with wide green "
        "background gaps between them: "
        "Pose 1 - stepping in, arms reaching forward to grab. "
        "Pose 2 - both hands gripping at collar height, elbows bent. "
        "Pose 3 - twisting the torso, heaving and hurling motion. "
        "Pose 4 - follow-through after the release, arms swung across the body. "
        "Only this one character is shown, alone, nobody else in the image."),
}

VICTORY = {
    "kai": "VICTORY celebration: Frame 1 - lowering guard, relaxing. Frame 2 - turning toward the viewer. "
        "Frames 3 and 4 - raising one fist high in triumph, golden sash flowing. "
        "Frame 5 - holding the fist-raised pose with a confident grin.",
    "nova": "VICTORY celebration: Frame 1 - lowering guard, relaxing. Frame 2 - turning toward the viewer. "
        "Frames 3 and 4 - crossing the arms with a confident smirk while the ponytail flicks. "
        "Frame 5 - holding the arms-crossed pose.",
}


def build_prompt(fighter: str, state: str) -> tuple[int, str]:
    frames, animation = ANIMATIONS[state]
    if state == "victory":
        animation = VICTORY[fighter]
    description = KAI if fighter == "kai" else NOVA
    prompt = (
        f"Using the pixel art fighting game character from the reference image ({description}), draw a "
        f"sprite sheet animation strip: exactly {frames} frames arranged in one horizontal row, evenly "
        f"spaced with clear gaps between frames, on a pure flat solid bright green chroma key background "
        f"#00ff00, no floor, no shadows. Keep the exact same character design, costume colors, pixel art "
        f"style, proportions and scale as the reference. Side view, facing right, full body visible, feet "
        f"on the same baseline in every frame. Animation: {animation} "
        f"Detailed 16-bit era pixel art, crisp dark outlines, no anti-aliasing, no blur, no text."
    )
    return frames, prompt


def run(fighter: str, state: str) -> bool:
    frames, prompt = build_prompt(fighter, state)
    width, height = SIZES[frames]
    strip = f"public/assets/generated/{fighter}-{state}-gen.png"
    for attempt in range(4):
        seed = 100 + attempt * 37 + hash(f"{fighter}{state}") % 1000
        print(f"--- {fighter}/{state} attempt {attempt + 1} seed {seed}", flush=True)
        generate = subprocess.run(
            [PY, "scripts/comfy-generate.py", "--prompt", prompt, "--width", str(width),
             "--height", str(height), "--seed", str(seed), "--ref", f"tmp/{fighter}-ref.png",
             "--out", strip],
            cwd=ROOT, capture_output=True, text=True,
        )
        if generate.returncode != 0:
            print(generate.stdout + generate.stderr, flush=True)
            continue
        width_ratio = "2.4" if state == "super" else "1.75"
        slice_run = subprocess.run(
            [PY, "scripts/slice-state-strips.py", "--strip", strip, "--fighter", fighter,
             "--state", state, "--frames", str(frames), "--max-width-ratio", width_ratio],
            cwd=ROOT, capture_output=True, text=True,
        )
        print(slice_run.stdout + slice_run.stderr, flush=True)
        if slice_run.returncode == 0:
            return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", default=None)
    args = parser.parse_args()

    jobs = [
        (fighter, state)
        for fighter in ("kai", "nova")
        for state in ANIMATIONS
    ]
    if args.only:
        wanted = set(args.only.split(","))
        jobs = [(f, s) for f, s in jobs if f"{f}-{s}" in wanted]

    failed = [f"{f}-{s}" for f, s in jobs if not run(f, s)]
    print(f"DONE. failed: {failed if failed else 'none'}", flush=True)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
