#!/usr/bin/env python3
"""Prepare a paired edit dataset for ai-toolkit from the manifest CSV.

The script creates split folders with:
- styled/   target images plus `.txt` captions
- control/  matching source images

If a row has no `split`, one is assigned deterministically from the frame number.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path


YES_VALUES = {"1", "true", "yes", "y", "include", ""}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--prompt-file", required=True, type=Path)
    parser.add_argument(
        "--relative-root",
        type=Path,
        default=None,
        help="Resolve relative source/styled paths against this root if needed.",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--val-fraction", type=float, default=0.10)
    parser.add_argument("--holdout-fraction", type=float, default=0.15)
    return parser.parse_args()


def slug(value: str) -> str:
    return " ".join(value.strip().split())


def include_row(row: dict[str, str]) -> bool:
    include = row.get("include", "").strip().lower()
    return include in YES_VALUES


def deterministic_split(frame_number: int, seed: int, val_fraction: float, holdout_fraction: float) -> str:
    digest = hashlib.sha1(f"{seed}:{frame_number}".encode("utf-8")).hexdigest()
    bucket = int(digest[:8], 16) / 0xFFFFFFFF
    if bucket < holdout_fraction:
        return "holdout"
    if bucket < holdout_fraction + val_fraction:
        return "val"
    return "train"


def build_caption(row: dict[str, str], base_prompt: str) -> str:
    tags = []
    for field, prefix in [
        ("expression", "expression"),
        ("mouth", "mouth"),
        ("eyes", "eyes"),
        ("head", "head"),
        ("hands", "hands"),
        ("lighting", "lighting"),
    ]:
        value = slug(row.get(field, ""))
        if value:
            tags.append(f"{prefix}: {value}")
    if tags:
        return f"{base_prompt} " + " ".join(tags)
    return base_prompt


def safe_link(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() or dst.is_symlink():
        dst.unlink()
    dst.symlink_to(src.resolve())


def resolve_media_path(path_str: str, relative_root: Path | None) -> Path:
    path = Path(path_str).expanduser()
    if path.is_absolute():
        return path.resolve()
    if relative_root is not None:
        return (relative_root / path).resolve()
    return path.resolve()


def main() -> None:
    args = parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)

    base_prompt = slug(args.prompt_file.read_text())

    with args.manifest.open() as handle:
        reader = csv.DictReader(handle)
        rows = [row for row in reader if include_row(row)]

    prepared_rows = []
    split_counts = {"train": 0, "val": 0, "holdout": 0}

    for row in rows:
        frame_number = int(row["frame_number"])
        split = slug(row.get("split", "")).lower()
        if split not in split_counts:
            split = deterministic_split(
                frame_number,
                args.seed,
                args.val_fraction,
                args.holdout_fraction,
            )

        source_path = resolve_media_path(row["source_path"], args.relative_root)
        styled_path = resolve_media_path(row["styled_path"], args.relative_root)

        if not source_path.exists() or not styled_path.exists():
            continue

        name = styled_path.name
        styled_out = args.output_root / split / "styled" / name
        control_out = args.output_root / split / "control" / name
        caption_out = styled_out.with_suffix(".txt")

        safe_link(styled_path, styled_out)
        safe_link(source_path, control_out)
        caption_out.write_text(build_caption(row, base_prompt) + "\n")

        row = dict(row)
        row["split"] = split
        row["prepared_styled_path"] = str(styled_out)
        row["prepared_control_path"] = str(control_out)
        prepared_rows.append(row)
        split_counts[split] += 1

    prepared_manifest = args.output_root / "prepared_manifest.csv"
    fieldnames = list(prepared_rows[0].keys()) if prepared_rows else []
    if prepared_rows:
        with prepared_manifest.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(prepared_rows)

    summary = {
        "manifest": str(args.manifest.resolve()),
        "output_root": str(args.output_root.resolve()),
        "seed": args.seed,
        "base_prompt_file": str(args.prompt_file.resolve()),
        "counts": split_counts,
    }
    (args.output_root / "summary.json").write_text(json.dumps(summary, indent=2))

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
