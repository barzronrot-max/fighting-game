"""Generate an image through the local ComfyUI API.

Text-to-image: Qwen-Image 2512 + Lightning 8-step.
With --ref <image>: Qwen-Image-Edit 2511 + Lightning 4-step, reference-conditioned
so the character stays on-model.

Usage:
  python scripts/comfy-generate.py --prompt "..." --width 1536 --height 768 \
      --seed 7 --ref public/assets/generated/kai-ref.png \
      --out public/assets/generated/kai-block-001.png
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

COMFY = "http://127.0.0.1:8188"

WORKFLOW = {
    "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "qwen_image_2512_fp8_e4m3fn.safetensors", "weight_dtype": "default"}},
    "2": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["1", 0], "lora_name": "Qwen-Image-2512-Lightning-8steps-V1.0-bf16.safetensors", "strength_model": 1}},
    "3": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_2.5_vl_7b_fp8_scaled.safetensors", "type": "qwen_image"}},
    "4": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["3", 0], "text": ""}},
    "5": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["4", 0]}},
    "6": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
    "7": {"class_type": "EmptyLatentImage", "inputs": {"width": 1536, "height": 768, "batch_size": 1}},
    "8": {"class_type": "KSampler", "inputs": {"model": ["2", 0], "positive": ["4", 0], "negative": ["5", 0], "latent_image": ["7", 0], "seed": 42, "steps": 8, "cfg": 1, "sampler_name": "euler", "scheduler": "simple", "denoise": 1}},
    "9": {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["6", 0]}},
    "10": {"class_type": "SaveImage", "inputs": {"images": ["9", 0], "filename_prefix": "fighting-game/strip"}},
}


REF_WORKFLOW = {
    "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "qwen_image_edit_2511_fp8mixed.safetensors", "weight_dtype": "default"}},
    "2": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["1", 0], "lora_name": "Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors", "strength_model": 1}},
    "3": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["2", 0], "shift": 3.1}},
    "4": {"class_type": "CFGNorm", "inputs": {"model": ["3", 0], "strength": 1}},
    "5": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_2.5_vl_7b_fp8_scaled.safetensors", "type": "qwen_image"}},
    "6": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
    "7": {"class_type": "LoadImage", "inputs": {"image": ""}},
    "9": {"class_type": "TextEncodeQwenImageEditPlus", "inputs": {"clip": ["5", 0], "prompt": "", "vae": ["6", 0], "image1": ["7", 0]}},
    "10": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["9", 0]}},
    "11": {"class_type": "EmptySD3LatentImage", "inputs": {"width": 1536, "height": 768, "batch_size": 1}},
    "12": {"class_type": "KSampler", "inputs": {"model": ["4", 0], "positive": ["9", 0], "negative": ["10", 0], "latent_image": ["11", 0], "seed": 42, "steps": 4, "cfg": 1, "sampler_name": "euler", "scheduler": "simple", "denoise": 1}},
    "13": {"class_type": "VAEDecode", "inputs": {"samples": ["12", 0], "vae": ["6", 0]}},
    "14": {"class_type": "SaveImage", "inputs": {"images": ["13", 0], "filename_prefix": "fighting-game/strip"}},
}


def upload_image(path: Path) -> str:
    boundary = uuid.uuid4().hex
    name = f"{path.stem}-{boundary[:8]}.png"
    payload = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="image"; filename="{name}"\r\n'
        f"Content-Type: image/png\r\n\r\n"
    ).encode() + path.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    request = urllib.request.Request(
        f"{COMFY}/upload/image",
        data=payload,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read())["name"]


def submit(prompt: str, width: int, height: int, seed: int, ref: Path | None) -> str:
    if ref is not None:
        workflow = json.loads(json.dumps(REF_WORKFLOW))
        workflow["7"]["inputs"]["image"] = upload_image(ref)
        workflow["9"]["inputs"]["prompt"] = prompt
        workflow["11"]["inputs"]["width"] = width
        workflow["11"]["inputs"]["height"] = height
        workflow["12"]["inputs"]["seed"] = seed
    else:
        workflow = json.loads(json.dumps(WORKFLOW))
        workflow["4"]["inputs"]["text"] = prompt
        workflow["7"]["inputs"]["width"] = width
        workflow["7"]["inputs"]["height"] = height
        workflow["8"]["inputs"]["seed"] = seed
    body = json.dumps({"prompt": workflow}).encode("utf-8")
    request = urllib.request.Request(f"{COMFY}/prompt", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read())["prompt_id"]


def wait_for(prompt_id: str, timeout_s: int = 600) -> dict:
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
        for image in node_output.get("images", []):
            query = urllib.parse.urlencode(
                {"filename": image["filename"], "subfolder": image.get("subfolder", ""), "type": image.get("type", "output")}
            )
            with urllib.request.urlopen(f"{COMFY}/view?{query}", timeout=60) as response:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(response.read())
            return
    raise RuntimeError("No image in ComfyUI outputs")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--width", type=int, default=1536)
    parser.add_argument("--height", type=int, default=768)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--ref", default=None)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    prompt_id = submit(args.prompt, args.width, args.height, args.seed, Path(args.ref) if args.ref else None)
    outputs = wait_for(prompt_id)
    download(outputs, Path(args.out))
    print(f"saved {args.out}")


if __name__ == "__main__":
    main()
