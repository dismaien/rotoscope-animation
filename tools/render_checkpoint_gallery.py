#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw
import yaml


ROOT = Path("/Users/leona/Documents/Playground/painterly-rotoscope-animation")
AI_TOOLKIT = ROOT / "external/ai-toolkit"
VENV_PYTHON = ROOT / ".venv-ai-toolkit/bin/python"
CHECKPOINT_DIR = ROOT / "runs/flux2_klein4b_paired_mps_pilot_bf16_nosample/wakinglife_flux2_klein4b_paired_mps_pilot_bf16_nosample"
CONTROL_IMAGE = ROOT / "runs/datasets/flux2_klein_v0_plus_dense_three/holdout/control/frame_0167.png"
TARGET_IMAGE = ROOT / "runs/datasets/flux2_klein_v0_plus_dense_three/holdout/styled/frame_0167.png"

PROMPT = (
    "Repaint this interview frame as a cinematic painted rotoscope image with bold dark outlines, "
    "visible brushstrokes, soft color blocking, preserved facial structure, preserved lip fullness, "
    "and the same courtyard pool setting. Keep smile lines, nasolabial folds, forehead lines, "
    "glabellar 11s, and under-eye creases soft, simplified, and flattering. Favor smooth painted skin "
    "planes over crease carving. Reduce harsh facial shadowing and line emphasis across the whole face. "
    "Keep exact facial proportions and a gently defined jawline; preserve cheekbone and jaw definition "
    "without heaviness. Keep the face elegant, lightly chiseled, ageless, and true to source rather "
    "than bulky or widened. Do not broaden the cheeks or widen the jaw. "
    f"--ctrl_img {CONTROL_IMAGE}"
)


def write_eval_config(step: int, checkpoint: Path, output_dir: Path) -> Path:
    width = int(os.environ.get("GALLERY_WIDTH", "672"))
    height = int(os.environ.get("GALLERY_HEIGHT", "384"))
    sample_steps = int(os.environ.get("GALLERY_SAMPLE_STEPS", "8"))
    config = {
        "job": "generate",
        "config": {
            "name": f"wakinglife_flux2_klein4b_gallery_step{step}",
            "process": [
                {
                    "type": "to_folder",
                    "output_folder": str(output_dir),
                    "device": "mps",
                    "dtype": "bf16",
                    "generate": {
                        "sampler": "flowmatch",
                        "width": width,
                        "height": height,
                        "neg": "",
                        "seed": 42,
                        "guidance_scale": 3.5,
                        "sample_steps": sample_steps,
                        "ext": "png",
                        "prompt_file": True,
                        "prompts": [PROMPT],
                    },
                    "model": {
                        "name_or_path": str(ROOT / "runs/model_bundles/flux2_klein_base_4b"),
                        "te_name_or_path": str(ROOT / "runs/model_bundles/Qwen3-4B"),
                        "vae_path": str(ROOT / "runs/model_bundles/flux2_vae/ae.safetensors"),
                        "arch": "flux2_klein_4b",
                        "dtype": "bf16",
                        "inference_lora_path": str(checkpoint),
                        "quantize": True,
                        "quantize_te": False,
                        "qtype": "uint4",
                        "qtype_te": "uint4",
                        "low_vram": True,
                        "model_kwargs": {"match_target_res": False},
                    },
                }
            ],
        },
    }
    cfg_path = output_dir.parent / f"step_{step:03d}.yaml"
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(yaml.safe_dump(config, sort_keys=False))
    return cfg_path


def run_eval(cfg_path: Path, log_path: Path) -> None:
    env = os.environ.copy()
    env.update(
        {
            "PYTHONUNBUFFERED": "1",
            "HF_HUB_DISABLE_XET": "1",
            "HF_HUB_DOWNLOAD_TIMEOUT": "120",
            "HF_HUB_ETAG_TIMEOUT": "30",
            "OMP_NUM_THREADS": "4",
            "MKL_NUM_THREADS": "4",
            "OPENBLAS_NUM_THREADS": "4",
            "VECLIB_MAXIMUM_THREADS": "4",
            "NUMEXPR_NUM_THREADS": "4",
        }
    )
    cmd = [
        "/usr/sbin/taskpolicy",
        "-b",
        "/usr/bin/nice",
        "-n",
        "20",
        str(VENV_PYTHON),
        "-u",
        "run.py",
        str(cfg_path),
    ]
    with log_path.open("w") as log:
        subprocess.run(cmd, cwd=AI_TOOLKIT, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)


def fit_image(img: Image.Image, width: int, height: int, bg: str = "white") -> Image.Image:
    canvas = Image.new("RGB", (width, height), bg)
    img = img.convert("RGB")
    img.thumbnail((width, height), Image.Resampling.LANCZOS)
    x = (width - img.width) // 2
    y = (height - img.height) // 2
    canvas.paste(img, (x, y))
    return canvas


def placeholder(width: int, height: int, title: str, body: str) -> Image.Image:
    img = Image.new("RGB", (width, height), "#f3f3f3")
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, width - 1, height - 1), outline="#cccccc", width=2)
    draw.text((20, 20), title, fill="black")
    draw.multiline_text((20, 60), textwrap.fill(body, 28), fill="#555555", spacing=6)
    return img


def latest_png(folder: Path) -> Path | None:
    pngs = sorted(folder.glob("*.png"), key=lambda p: p.stat().st_mtime)
    return pngs[-1] if pngs else None


def build_panel(out_path: Path, renders: dict[int, Path | None], tile_w: int = 320, tile_h: int = 210) -> None:
    steps = sorted(renders)
    cols = 3
    rows = 1 + ((len(steps) + cols - 1) // cols)
    margin = 24
    header_h = 32
    panel_w = margin * (cols + 1) + tile_w * cols
    panel_h = margin * (rows + 1) + rows * (tile_h + header_h)
    panel = Image.new("RGB", (panel_w, panel_h), "white")
    draw = ImageDraw.Draw(panel)

    # First row: source + target
    source = fit_image(Image.open(CONTROL_IMAGE), tile_w, tile_h)
    target = fit_image(Image.open(TARGET_IMAGE), tile_w, tile_h)
    x0 = margin
    y0 = margin + header_h
    draw.text((x0, margin), "source", fill="black")
    panel.paste(source, (x0, y0))
    draw.text((x0 + tile_w + margin, margin), "nano target", fill="black")
    panel.paste(target, (x0 + tile_w + margin, y0))
    draw.text((x0 + 2 * (tile_w + margin), margin), "checkpoint progression", fill="black")
    panel.paste(placeholder(tile_w, tile_h, "steps", "60, 80, 100, 120, 140, 160, 180"), (x0 + 2 * (tile_w + margin), y0))

    # Remaining rows: step outputs/placeholders
    for idx, step in enumerate(steps):
        row = 1 + idx // cols
        col = idx % cols
        x = margin + col * (tile_w + margin)
        y = margin + row * (tile_h + header_h + margin)
        draw.text((x, y), f"step {step}", fill="black")
        y_img = y + header_h
        path = renders[step]
        if path and path.exists():
            tile = fit_image(Image.open(path), tile_w, tile_h)
        else:
            tile = placeholder(tile_w, tile_h, f"step {step}", "checkpoint was pruned before we built this gallery")
        panel.paste(tile, (x, y_img))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    panel.save(out_path, quality=95)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", nargs="+", type=int, default=[60, 80, 100, 120, 140, 160, 180])
    parser.add_argument("--out-dir", type=Path, default=ROOT / "analysis/checkpoint_gallery_v1")
    parser.add_argument("--skip-render", action="store_true")
    args = parser.parse_args()

    raw_root = args.out_dir / "raw"
    cfg_root = args.out_dir / "configs"
    log_root = args.out_dir / "logs"
    renders: dict[int, Path | None] = {}

    for step in args.steps:
        ckpt = CHECKPOINT_DIR / f"wakinglife_flux2_klein4b_paired_mps_pilot_bf16_nosample_{step:09d}.safetensors"
        out_folder = raw_root / f"step_{step:03d}"
        if not ckpt.exists():
            renders[step] = None
            continue
        out_folder.mkdir(parents=True, exist_ok=True)
        existing = latest_png(out_folder)
        if existing is not None:
            renders[step] = existing
            continue
        cfg_path = write_eval_config(step, ckpt, out_folder)
        log_path = log_root / f"step_{step:03d}.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        if not args.skip_render:
            run_eval(cfg_path, log_path)
        renders[step] = latest_png(out_folder)

    build_panel(args.out_dir / "checkpoint_gallery.jpg", renders)


if __name__ == "__main__":
    main()
