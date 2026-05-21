#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a control/target/generated evaluation panel.")
    parser.add_argument("--dataset-root", required=True, help="Prepared paired dataset root.")
    parser.add_argument("--generated-dir", required=True, help="Directory containing generated images.")
    parser.add_argument("--stems", nargs="+", required=True, help="Ordered frame stems to include.")
    parser.add_argument("--out", required=True, help="Output panel image path.")
    parser.add_argument("--tile-width", type=int, default=320)
    parser.add_argument("--tile-height", type=int, default=180)
    return parser.parse_args()


def fit_image(path: Path, size: tuple[int, int]) -> Image.Image:
    width, height = size
    canvas = Image.new("RGB", (width, height), "white")
    if not path.exists():
        return canvas
    image = Image.open(path).convert("RGB")
    image.thumbnail((width, height), Image.Resampling.LANCZOS)
    x = (width - image.width) // 2
    y = (height - image.height) // 2
    canvas.paste(image, (x, y))
    return canvas


def latest_generated_images(directory: Path, count: int) -> list[Path]:
    images = sorted(
        [p for p in directory.iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}],
        key=lambda p: p.stat().st_mtime,
    )
    if len(images) < count:
        raise RuntimeError(f"Need {count} generated images, found {len(images)} in {directory}")
    return images[-count:]


def main() -> None:
    args = parse_args()
    dataset_root = Path(args.dataset_root).expanduser().resolve()
    generated_dir = Path(args.generated_dir).expanduser().resolve()
    stems = args.stems
    generated = latest_generated_images(generated_dir, len(stems))

    pad = 20
    label_h = 28
    tile_w = args.tile_width
    tile_h = args.tile_height
    cols = 3
    panel_h = pad + len(stems) * (label_h + tile_h + pad)
    panel_w = pad + cols * (tile_w + pad)
    panel = Image.new("RGB", (panel_w, panel_h), (245, 245, 245))
    draw = ImageDraw.Draw(panel)

    headers = ["control", "target", "generated"]
    for i, header in enumerate(headers):
        x = pad + i * (tile_w + pad)
        draw.text((x, 5), header, fill=(20, 20, 20))

    for row, (stem, gen_path) in enumerate(zip(stems, generated)):
        y = pad + row * (label_h + tile_h + pad)
        y_img = y + label_h

        ctrl = fit_image(dataset_root / "holdout" / "control" / f"{stem}.png", (tile_w, tile_h))
        target = fit_image(dataset_root / "holdout" / "styled" / f"{stem}.png", (tile_w, tile_h))
        sample = fit_image(gen_path, (tile_w, tile_h))

        draw.text((pad, y + 6), stem, fill=(20, 20, 20))
        panel.paste(ctrl, (pad, y_img))
        panel.paste(target, (pad * 2 + tile_w, y_img))
        panel.paste(sample, (pad * 3 + tile_w * 2, y_img))

    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    panel.save(out_path, quality=95)
    print(f"Wrote evaluation panel to {out_path}")


if __name__ == "__main__":
    main()
