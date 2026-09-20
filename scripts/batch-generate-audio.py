"""Generate the full SFX + music set via local ComfyUI and post-process.

SFX: Stable Audio Open -> trim silence, mono, peak-normalize -> public/assets/audio/<name>.wav
Music: ACE-Step 1.5 turbo -> public/assets/audio/music-<name>.mp3

Usage: python scripts/batch-generate-audio.py [--only hit,ko,music-fight]
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
AUDIO_DIR = ROOT / "public" / "assets" / "audio"
PY = sys.executable

STYLE = ", fighting game sound effect, clean, punchy"

SFX: dict[str, tuple[str, float, int]] = {
    "menu": ("retro arcade UI menu blip, short synth click, video game interface sound", 1.0, 101),
    "round": ("deep taiko drum hit with short reverb tail, dramatic fight announcement drum", 1.2, 102),
    "start": ("boxing ring bell single ding, fight start bell", 1.2, 103),
    "jump": ("quick short air whoosh, jump swish" + STYLE, 1.0, 104),
    "dash": ("fast sharp whoosh, quick dash swish" + STYLE, 1.0, 105),
    "hit": ("single punch impact, flesh smack, short percussive hit, dry, no reverb tail" + STYLE, 1.0, 7),
    "block": ("short metallic clank, blocked strike on shield, parry impact" + STYLE, 1.0, 107),
    "throw": ("heavy body slam on the ground, wrestling throw thud" + STYLE, 1.2, 108),
    "ko": ("heavy dramatic knockout impact, deep slam with sub bass boom", 1.5, 109),
    "special": ("energy fireball launch, sci-fi projectile whoosh with a zap" + STYLE, 1.0, 110),
    "super": ("powerful sci-fi energy beam blast, rising charge then explosion, dramatic super attack", 1.8, 111),
    "superHit": ("massive explosion, deep cinematic boom impact", 1.8, 112),
    "deny": ("negative UI buzz, short low error beep, video game denial sound", 1.0, 113),
}

MUSIC: dict[str, tuple[str, int, int, int]] = {
    "fight": ("energetic chiptune arcade fighting game battle theme, fast driving synth arpeggios, "
              "punchy drums, 8-bit retro, intense, instrumental", 160, 64, 201),
    "menu": ("retro arcade character select screen music, upbeat chiptune synthwave, catchy loop, "
             "instrumental", 128, 48, 202),
    "victory": ("short triumphant victory fanfare, chiptune jingle, celebratory, bright, instrumental",
                140, 12, 203),
}

TRIM_DB = -50.0


def post_process_sfx(source: Path, target: Path) -> str:
    data, sr = sf.read(source)
    if data.ndim > 1:
        data = data.mean(axis=1)
    threshold = 10 ** (TRIM_DB / 20)
    loud = np.where(np.abs(data) > threshold)[0]
    if len(loud) == 0:
        return "EMPTY"
    start = max(0, loud[0] - int(0.005 * sr))
    end = min(len(data), loud[-1] + int(0.03 * sr))
    data = data[start:end]
    peak = np.abs(data).max()
    data = data / peak * 0.9
    # short fade-out to avoid clicks
    fade = min(len(data), int(0.02 * sr))
    data[-fade:] *= np.linspace(1, 0, fade)
    sf.write(target, data.astype(np.float32), sr)
    return f"{len(data) / sr:.2f}s"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", default=None)
    args = parser.parse_args()
    wanted = set(args.only.split(",")) if args.only else None

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    failed = []

    for name, (prompt, seconds, seed) in SFX.items():
        if wanted and name not in wanted:
            continue
        raw = ROOT / "tmp" / f"sfx-{name}.flac"
        print(f"--- sfx {name}", flush=True)
        if not raw.exists():
            result = subprocess.run(
                [PY, "scripts/comfy-audio.py", "--prompt", prompt, "--seconds", str(seconds),
                 "--seed", str(seed), "--out", str(raw)],
                cwd=ROOT, capture_output=True, text=True,
            )
            print(result.stdout + result.stderr, flush=True)
            if result.returncode != 0:
                failed.append(name)
                continue
        info = post_process_sfx(raw, AUDIO_DIR / f"{name}.wav")
        print(f"{name}.wav {info}", flush=True)
        if info == "EMPTY":
            failed.append(name)

    for name, (tags, bpm, seconds, seed) in MUSIC.items():
        key = f"music-{name}"
        if wanted and key not in wanted:
            continue
        raw = ROOT / "tmp" / f"{key}.mp3"
        print(f"--- {key}", flush=True)
        result = subprocess.run(
            [PY, "scripts/comfy-audio.py", "--music", "--prompt", tags, "--bpm", str(bpm),
             "--seconds", str(seconds), "--seed", str(seed), "--out", str(raw)],
            cwd=ROOT, capture_output=True, text=True,
        )
        print(result.stdout + result.stderr, flush=True)
        if result.returncode != 0:
            failed.append(key)
            continue
        shutil.copyfile(raw, AUDIO_DIR / f"{key}.mp3")
        print(f"{key}.mp3 copied", flush=True)

    print(f"DONE. failed: {failed if failed else 'none'}", flush=True)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
