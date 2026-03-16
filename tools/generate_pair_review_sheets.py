#!/usr/bin/env python3
import argparse
import csv
import math
from pathlib import Path

import cv2
import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate side-by-side review sheets from a paired image manifest."
    )
    parser.add_argument("--manifest", required=True, help="CSV manifest with source_path and styled_path columns.")
    parser.add_argument(
        "--base-root",
        default=".",
        help="Base directory used to resolve relative manifest paths. Default: current directory",
    )
    parser.add_argument("--outdir", required=True, help="Output directory for review pages.")
    parser.add_argument("--columns", type=int, default=3, help="Pairs per row. Default: 3")
    parser.add_argument("--rows", type=int, default=4, help="Rows per page. Default: 4")
    parser.add_argument("--tile-width", type=int, default=360, help="Tile width in pixels. Default: 360")
    parser.add_argument("--tile-height", type=int, default=202, help="Tile height in pixels. Default: 202")
    return parser.parse_args()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def resolve_path(path_str: str, base_root: Path) -> Path:
    path = Path(path_str).expanduser()
    if path.is_absolute():
        return path
    return (base_root / path).resolve()


def read_manifest(manifest_path: Path, base_root: Path) -> list[dict]:
    rows = []
    with manifest_path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            source_path = resolve_path(row["source_path"], base_root)
            styled_path = resolve_path(row["styled_path"], base_root)
            if not source_path.exists() or not styled_path.exists():
                continue
            row["_source_path"] = source_path
            row["_styled_path"] = styled_path
            rows.append(row)
    return rows


def fit_image(image: np.ndarray, width: int, height: int) -> np.ndarray:
    h, w = image.shape[:2]
    scale = min(width / w, height / h)
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    canvas = np.full((height, width, 3), 245, dtype=np.uint8)
    x = (width - new_w) // 2
    y = (height - new_h) // 2
    canvas[y : y + new_h, x : x + new_w] = resized
    return canvas


def draw_label(canvas: np.ndarray, text: str, x: int, y: int, max_width: int) -> None:
    clipped = text if len(text) <= 34 else text[:31] + "..."
    cv2.putText(
        canvas,
        clipped,
        (x, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.52,
        (20, 20, 20),
        1,
        cv2.LINE_AA,
    )


def build_tile(row: dict, tile_width: int, tile_height: int) -> np.ndarray:
    label_h = 52
    gap = 8
    img_h = tile_height
    source = cv2.imread(str(row["_source_path"]))
    styled = cv2.imread(str(row["_styled_path"]))
    if source is None or styled is None:
        raise RuntimeError(f"Failed to read images for {row.get('pair_id', '<unknown>')}")

    source_fit = fit_image(source, tile_width, img_h)
    styled_fit = fit_image(styled, tile_width, img_h)

    tile = np.full((label_h + img_h * 2 + gap, tile_width, 3), 255, dtype=np.uint8)
    tile[:label_h] = (250, 250, 250)
    tile[label_h : label_h + img_h] = source_fit
    tile[label_h + img_h + gap : label_h + img_h + gap + img_h] = styled_fit

    pair_id = row.get("pair_id", "")
    frame_number = row.get("frame_number", "")
    draw_label(tile, f"{pair_id}  frame {frame_number}", 10, 20, tile_width - 20)
    draw_label(tile, "top: source", 10, 42, tile_width - 20)
    draw_label(tile, "bottom: styled", 180, 42, tile_width - 20)

    cv2.rectangle(tile, (0, 0), (tile_width - 1, tile.shape[0] - 1), (215, 215, 215), 1)
    return tile


def write_pages(rows: list[dict], outdir: Path, columns: int, rows_per_page: int, tile_width: int, tile_height: int) -> None:
    page_capacity = columns * rows_per_page
    pages = math.ceil(len(rows) / page_capacity)
    margin = 18
    gap = 14
    tile_total_h = 52 + tile_height * 2 + 8
    page_w = margin * 2 + columns * tile_width + (columns - 1) * gap
    page_h = margin * 2 + rows_per_page * tile_total_h + (rows_per_page - 1) * gap

    for page_idx in range(pages):
        page = np.full((page_h, page_w, 3), 238, dtype=np.uint8)
        subset = rows[page_idx * page_capacity : (page_idx + 1) * page_capacity]
        for idx, row in enumerate(subset):
            tile = build_tile(row, tile_width, tile_height)
            r = idx // columns
            c = idx % columns
            x = margin + c * (tile_width + gap)
            y = margin + r * (tile_total_h + gap)
            page[y : y + tile.shape[0], x : x + tile.shape[1]] = tile

        page_name = f"page_{page_idx + 1:02d}.jpg"
        cv2.imwrite(str(outdir / page_name), page)


def main() -> None:
    args = parse_args()
    manifest_path = Path(args.manifest).expanduser().resolve()
    base_root = Path(args.base_root).expanduser().resolve()
    outdir = Path(args.outdir).expanduser().resolve()
    ensure_dir(outdir)

    rows = read_manifest(manifest_path, base_root)
    rows.sort(key=lambda row: int(row.get("frame_number") or 0))

    write_pages(rows, outdir, args.columns, args.rows, args.tile_width, args.tile_height)

    summary_path = outdir / "README.txt"
    summary_path.write_text(
        "\n".join(
            [
                f"Manifest: {manifest_path}",
                f"Base root: {base_root}",
                f"Pairs rendered: {len(rows)}",
                f"Pages: {math.ceil(len(rows) / (args.columns * args.rows))}",
                "Each tile shows source on top and styled output on bottom.",
            ]
        )
        + "\n"
    )
    print(f"Wrote {len(rows)} review tiles to {outdir}")


if __name__ == "__main__":
    main()
