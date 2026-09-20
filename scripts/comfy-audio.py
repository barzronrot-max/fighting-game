"""Generate audio through the local ComfyUI API.

SFX mode (default): Stable Audio Open 1.0 — short sound effects.
Music mode (--music): ACE-Step 1.5 turbo — loops and stings (MP3).

Usage:
  python scripts/comfy-audio.py --prompt "punch impact" --seconds 1.0 --out tmp/hit.flac
  python scripts/comfy-audio.py --music --prompt "chiptune battle theme" --bpm 160 \
      --seconds 60 --out tmp/fight-theme.mp3
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

COMFY = "http://127.0.0.1:8188"

SFX_WORKFLOW = {
    "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "stable-audio-open-1.0.safetensors"}},
    "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "t5-base.safetensors", "type": "stable_audio"}},
    "3": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": ""}},
    "4": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": "music, melody, voice, speech"}},
    "5": {"class_type": "EmptyLatentAudio", "inputs": {"seconds": 1.0, "batch_size": 1}},
    "6": {"class_type": "KSampler", "inputs": {"model": ["1", 0], "positive": ["3", 0], "negative": ["4", 0], "latent_image": ["5", 0], "seed": 42, "steps": 50, "cfg": 4.98, "sampler_name": "dpmpp_3m_sde_gpu", "scheduler": "exponential", "denoise": 1}},
    "7": {"class_type": "VAEDecodeAudio", "inputs": {"samples": ["6", 0], "vae": ["1", 2]}},
    "8": {"class_type": "SaveAudio", "inputs": {"audio": ["7", 0], "filename_prefix": "fighting-game/sfx"}},
}

MUSIC_WORKFLOW = {
    "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "acestep_v1.5_xl_turbo_bf16.safetensors", "weight_dtype": "default"}},
    "2": {"class_type": "DualCLIPLoader", "inputs": {"clip_name1": "qwen_4b_ace15.safetensors", "clip_name2": "qwen_0.6b_ace15.safetensors", "type": "ace"}},
    "3": {"class_type": "VAELoader", "inputs": {"vae_name": "ace_1.5_vae.safetensors"}},
    "4": {"class_type": "TextEncodeAceStepAudio1.5", "inputs": {"clip": ["2", 0], "tags": "", "lyrics": "[inst]", "seed": 42, "bpm": 120, "duration": 40, "timesignature": "4", "language": "en", "keyscale": "C major", "generate_audio_codes": True, "cfg_scale": 2, "temperature": 0.85, "top_p": 0.9, "top_k": 0, "min_p": 0}},
    "5": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["4", 0]}},
    "6": {"class_type": "EmptyAceStep1.5LatentAudio", "inputs": {"seconds": 40, "batch_size": 1}},
    "7": {"class_type": "KSampler", "inputs": {"model": ["1", 0], "positive": ["4", 0], "negative": ["5", 0], "latent_image": ["6", 0], "seed": 42, "steps": 8, "cfg": 1, "sampler_name": "euler", "scheduler": "simple", "denoise": 1}},
    "8": {"class_type": "VAEDecodeAudio", "inputs": {"samples": ["7", 0], "vae": ["3", 0]}},
    "9": {"class_type": "SaveAudioMP3", "inputs": {"audio": ["8", 0], "filename_prefix": "fighting-game/music", "quality": "V0"}},
}


def submit(workflow: dict) -> str:
    body = json.dumps({"prompt": workflow}).encode("utf-8")
    request = urllib.request.Request(f"{COMFY}/prompt", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read())["prompt_id"]


def wait_for(prompt_id: str, timeout_s: int = 900) -> dict:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        with urllib.request.urlopen(f"{COMFY}/history/{prompt_id}", timeout=30) as response:
            history = json.loads(response.read())
        entry = history.get(prompt_id)
        if entry:
            status = entry.get("status", {})
            if status.get("status_str") == "error":
                raise RuntimeError(json.dumps(status, indent=2)[:2000])
            if entry.get("outputs"):
                return entry["outputs"]
        time.sleep(2)
    raise TimeoutError(f"ComfyUI job {prompt_id} did not finish in {timeout_s}s")


def download(outputs: dict, target: Path) -> None:
    for node_output in outputs.values():
        for audio in node_output.get("audio", []):
            query = urllib.parse.urlencode(
                {"filename": audio["filename"], "subfolder": audio.get("subfolder", ""), "type": audio.get("type", "output")}
            )
            with urllib.request.urlopen(f"{COMFY}/view?{query}", timeout=120) as response:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(response.read())
            return
    raise RuntimeError(f"No audio in ComfyUI outputs: {json.dumps(outputs)[:500]}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--seconds", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--music", action="store_true")
    parser.add_argument("--bpm", type=int, default=120)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    if args.music:
        workflow = json.loads(json.dumps(MUSIC_WORKFLOW))
        workflow["4"]["inputs"]["tags"] = args.prompt
        workflow["4"]["inputs"]["bpm"] = args.bpm
        workflow["4"]["inputs"]["duration"] = int(args.seconds)
        workflow["4"]["inputs"]["seed"] = args.seed
        workflow["6"]["inputs"]["seconds"] = int(args.seconds)
        workflow["7"]["inputs"]["seed"] = args.seed
    else:
        workflow = json.loads(json.dumps(SFX_WORKFLOW))
        workflow["3"]["inputs"]["text"] = args.prompt
        workflow["5"]["inputs"]["seconds"] = args.seconds
        workflow["6"]["inputs"]["seed"] = args.seed

    outputs = wait_for(submit(workflow))
    download(outputs, Path(args.out))
    print(f"saved {args.out}")


if __name__ == "__main__":
    main()
