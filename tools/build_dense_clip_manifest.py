#!/usr/bin/env python3
"""Build a manifest CSV for dense Gemini clip outputs."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


PATTERN = re.compile(r"frame_s(\d{4})_q(\d+)\.png$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clip-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--pair-prefix", default="dense")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    generated_dir = args.clip_dir / "generated"
    inputs_dir = args.clip_dir / "inputs"
    styled_files = sorted(generated_dir.glob("frame_s*_q*.png"))
    matches = [(path, PATTERN.match(path.name)) for path in styled_files]
    seconds = [int(match.group(1)) for _, match in matches if match]
    if not seconds:
        raise RuntimeError(f"No dense clip frames found in {generated_dir}")
    clip_start = min(seconds)

    rows = []
    for idx, (styled_path, match) in enumerate(matches, start=1):
        if match is None:
            continue
        second = int(match.group(1))
        quarter = int(match.group(2))
        input_index = (second - clip_start) * 4 + quarter + 1
        source_path = inputs_dir / f"frame_{input_index:04d}.png"
        frame_number = int(f"{second}{quarter:02d}")
        rows.append(
            {
                "pair_id": f"{args.pair_prefix}_{idx:04d}",
                "frame_number": frame_number,
                "source_path": str(source_path.resolve()),
                "styled_path": str(styled_path.resolve()),
                "include": "yes",
                "split": "",
                "style_score": "",
                "likeness_score": "",
                "expression_score": "",
                "structure_score": "",
                "expression": "",
                "mouth": "",
                "eyes": "",
                "head": "",
                "hands": "",
                "lighting": "",
                "priority": "normal",
                "notes": "dense_clip",
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
