#!/usr/bin/env python3
import argparse
import csv
import re
from pathlib import Path


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a CSV manifest matching source frames to styled frames."
    )
    parser.add_argument("--source-dir", required=True, help="Directory of source frames.")
    parser.add_argument("--styled-dir", required=True, help="Directory of styled frames.")
    parser.add_argument("--output", required=True, help="Output CSV path.")
    parser.add_argument(
        "--path-mode",
        choices=("absolute", "relative"),
        default="absolute",
        help="Whether to write absolute or repo-relative paths. Default: absolute",
    )
    parser.add_argument(
        "--relative-root",
        default=".",
        help="Root to use when --path-mode relative. Default: current directory",
    )
    return parser.parse_args()


def iter_images(directory: Path) -> list[Path]:
    return sorted(
        path for path in directory.rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )


def frame_number_from_name(path: Path) -> int | None:
    matches = re.findall(r"(\d+)", path.stem)
    if not matches:
        return None
    return int(matches[-1])


def format_path(path: Path, mode: str, relative_root: Path) -> str:
    if mode == "absolute":
        return str(path.resolve())
    return str(path.resolve().relative_to(relative_root.resolve()))


def main() -> None:
    args = parse_args()
    source_dir = Path(args.source_dir).expanduser().resolve()
    styled_dir = Path(args.styled_dir).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    relative_root = Path(args.relative_root).expanduser().resolve()

    source_by_frame = {}
    for path in iter_images(source_dir):
        frame_number = frame_number_from_name(path)
        if frame_number is not None and frame_number not in source_by_frame:
            source_by_frame[frame_number] = path

    styled_rows = []
    missing_sources = []
    for styled_path in iter_images(styled_dir):
        frame_number = frame_number_from_name(styled_path)
        if frame_number is None:
            continue
        source_path = source_by_frame.get(frame_number)
        if source_path is None:
            missing_sources.append(styled_path)
            continue
        styled_rows.append((frame_number, source_path, styled_path))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "pair_id",
                "frame_number",
                "source_path",
                "styled_path",
                "include",
                "split",
                "style_score",
                "likeness_score",
                "expression_score",
                "structure_score",
                "expression",
                "mouth",
                "eyes",
                "head",
                "hands",
                "lighting",
                "priority",
                "notes",
            ]
        )
        for idx, (frame_number, source_path, styled_path) in enumerate(sorted(styled_rows), start=1):
            writer.writerow(
                [
                    f"pair_{idx:04d}",
                    frame_number,
                    format_path(source_path, args.path_mode, relative_root),
                    format_path(styled_path, args.path_mode, relative_root),
                    "yes",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "normal",
                    "",
                ]
            )

    print(f"Source frames discovered: {len(source_by_frame)}")
    print(f"Styled frames matched: {len(styled_rows)}")
    print(f"Styled frames missing sources: {len(missing_sources)}")
    print(f"Wrote manifest: {output_path}")
    if missing_sources:
        print("Missing source matches:")
        for path in missing_sources[:10]:
            print(f"  - {path}")


if __name__ == "__main__":
    main()
