#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import re
from pathlib import Path

from PIL import Image, ImageDraw
import yaml


CTRL_RE = re.compile(r"--ctrl_img\s+(\S+)")


def load_prompts(config_path: Path) -> list[str]:
    data = yaml.safe_load(config_path.read_text())
    process = data["config"]["process"][0]
    return process.get("sample", {}).get("prompts", [])


def find_ctrl_paths(prompts: list[str]) -> list[Path]:
    ctrl_paths: list[Path] = []
    for prompt in prompts:
        match = CTRL_RE.search(prompt)
        if not match:
            raise ValueError(f"Prompt missing --ctrl_img path: {prompt}")
        ctrl_paths.append(Path(match.group(1)))
    return ctrl_paths


def latest_sample_images(run_dir: Path, count: int) -> list[Path]:
    sample_dir = run_dir / "samples"
    if not sample_dir.exists():
        raise FileNotFoundError(f"No sample directory found at {sample_dir}")
    images = sorted(
        [p for p in sample_dir.iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}],
        key=lambda p: p.stat().st_mtime,
    )
    if len(images) < count:
        raise RuntimeError(f"Need {count} sample images, found {len(images)} in {sample_dir}")
    return images[-count:]


def fit_image(img: Image.Image, width: int, height: int) -> Image.Image:
    canvas = Image.new("RGB", (width, height), "white")
    img = img.convert("RGB")
    img.thumbnail((width, height), Image.Resampling.LANCZOS)
    x = (width - img.width) // 2
    y = (height - img.height) // 2
    canvas.paste(img, (x, y))
    return canvas


def label(draw: ImageDraw.ImageDraw, x: int, y: int, text: str) -> None:
    draw.text((x, y), text, fill="black")


def infer_target_path(ctrl_path: Path) -> Path:
    if "/control/" not in str(ctrl_path):
        raise ValueError(f"Expected control path to include /control/: {ctrl_path}")
    return Path(str(ctrl_path).replace("/control/", "/styled/"))


def build_panel(config_path: Path, run_dir: Path, out_path: Path, tile_w: int, tile_h: int) -> None:
    prompts = load_prompts(config_path)
    ctrl_paths = find_ctrl_paths(prompts)
    sample_paths = latest_sample_images(run_dir, len(ctrl_paths))

    rows = len(ctrl_paths)
    margin = 24
    header_h = 26
    panel = Image.new("RGB", (margin * 4 + tile_w * 3, margin * (rows + 1) + rows * (tile_h + header_h)), "white")
    draw = ImageDraw.Draw(panel)

    label(draw, margin, 6, "control")
    label(draw, margin * 2 + tile_w, 6, "target")
    label(draw, margin * 3 + tile_w * 2, 6, "sample")

    for idx, (ctrl_path, sample_path) in enumerate(zip(ctrl_paths, sample_paths)):
        target_path = infer_target_path(ctrl_path)
        if not target_path.exists():
            raise FileNotFoundError(f"Expected target image at {target_path}")
        y = margin + idx * (tile_h + header_h + margin)
        label(draw, margin, y, ctrl_path.stem)
        y_img = y + header_h

        ctrl_img = fit_image(Image.open(ctrl_path), tile_w, tile_h)
        target_img = fit_image(Image.open(target_path), tile_w, tile_h)
        sample_img = fit_image(Image.open(sample_path), tile_w, tile_h)

        panel.paste(ctrl_img, (margin, y_img))
        panel.paste(target_img, (margin * 2 + tile_w, y_img))
        panel.paste(sample_img, (margin * 3 + tile_w * 2, y_img))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    panel.save(out_path, quality=95)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a control/target/sample review panel from an ai-toolkit training run.")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--tile-width", type=int, default=320)
    parser.add_argument("--tile-height", type=int, default=180)
    args = parser.parse_args()

    build_panel(args.config, args.run_dir, args.out, args.tile_width, args.tile_height)


if __name__ == "__main__":
    main()
