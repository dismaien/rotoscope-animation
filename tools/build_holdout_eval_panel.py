#!/usr/bin/env python3
import argparse
import math
from pathlib import Path

import cv2
import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a simple source/target holdout evaluation contact sheet."
    )
    parser.add_argument("--dataset-root", required=True, help="Prepared dataset root.")
    parser.add_argument("--outdir", required=True, help="Output directory.")
    parser.add_argument("--count", type=int, default=16, help="Number of holdout pairs to show. Default: 16")
    parser.add_argument("--columns", type=int, default=4, help="Columns in the panel. Default: 4")
    return parser.parse_args()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def sorted_stems(directory: Path) -> list[str]:
    return sorted(path.stem for path in directory.glob("*.png"))


def evenly_spaced(items: list[str], count: int) -> list[str]:
    if count >= len(items):
        return items[:]
    if count <= 0:
        return []
    result = []
    for i in range(count):
        position = round(i * (len(items) - 1) / max(count - 1, 1))
        result.append(items[position])
    return result


def load_image(path: Path, size: tuple[int, int]) -> np.ndarray:
    image = cv2.imread(str(path))
    if image is None:
        return np.full((size[1], size[0], 3), 200, dtype=np.uint8)
    return cv2.resize(image, size, interpolation=cv2.INTER_AREA)


def draw_tile(source_path: Path, styled_path: Path, label: str, tile_size: tuple[int, int]) -> np.ndarray:
    width, height = tile_size
    half_height = (height - 44) // 2
    source = load_image(source_path, (width, half_height))
    styled = load_image(styled_path, (width, half_height))
    tile = np.full((height, width, 3), 245, dtype=np.uint8)
    tile[:half_height, :] = source
    tile[half_height : half_height * 2, :] = styled
    cv2.rectangle(tile, (0, height - 44), (width, height), (0, 0, 0), -1)
    cv2.putText(tile, label, (12, height - 16), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
    return tile


def write_markdown(stems: list[str], outpath: Path) -> None:
    lines = [
        "# Holdout Eval Panel",
        "",
        "Each tile shows:",
        "",
        "- top: source control frame",
        "- bottom: Nano Banana target frame",
        "",
        "Use these pairs to judge whether the trained model preserves:",
        "",
        "- facial likeness",
        "- mouth shape and lip fullness",
        "- eye/gaze fidelity",
        "- contour quality",
        "- overall painterly beauty",
        "",
        "## Included Holdout Frames",
        "",
    ]
    for stem in stems:
        lines.append(f"- `{stem}`")
    outpath.write_text("\n".join(lines) + "\n")


def main() -> None:
    args = parse_args()
    dataset_root = Path(args.dataset_root).expanduser().resolve()
    outdir = Path(args.outdir).expanduser().resolve()
    ensure_dir(outdir)

    holdout_styled = dataset_root / "holdout" / "styled"
    holdout_control = dataset_root / "holdout" / "control"
    stems = evenly_spaced(sorted_stems(holdout_styled), args.count)

    tile_size = (320, 360)
    rows = math.ceil(len(stems) / args.columns)
    panel = np.full((rows * tile_size[1], args.columns * tile_size[0], 3), 230, dtype=np.uint8)

    for index, stem in enumerate(stems):
        row = index // args.columns
        col = index % args.columns
        tile = draw_tile(
            holdout_control / f"{stem}.png",
            holdout_styled / f"{stem}.png",
            stem,
            tile_size,
        )
        panel[
            row * tile_size[1] : (row + 1) * tile_size[1],
            col * tile_size[0] : (col + 1) * tile_size[0],
        ] = tile

    cv2.imwrite(str(outdir / "holdout_panel.jpg"), panel)
    write_markdown(stems, outdir / "README.md")
    print(f"Wrote holdout panel with {len(stems)} pairs to {outdir}")


if __name__ == "__main__":
    main()
