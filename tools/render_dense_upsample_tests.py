#!/usr/bin/env python3
"""Render upsample tests from a dense 4 fps preview clip.

Outputs:
- hold_<fps>fps.mp4
- blend_<fps>fps.mp4
- mci_<fps>fps.mp4
- hold_vs_mci_<fps>fps.mp4
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clip-dir", required=True, type=Path)
    parser.add_argument("--fps", type=int, default=12)
    return parser.parse_args()


def run(cmd: list[str]) -> None:
    print("+", " ".join(str(part) for part in cmd), flush=True)
    subprocess.run(cmd, check=True)


def render_method(input_video: Path, filter_expr: str, output_path: Path) -> None:
    temp_video = output_path.with_suffix(".video.mp4")
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(input_video),
            "-an",
            "-vf",
            filter_expr,
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            str(temp_video),
        ]
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(temp_video),
            "-i",
            str(input_video),
            "-map",
            "0:v",
            "-map",
            "1:a?",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-shortest",
            str(output_path),
        ]
    )
    temp_video.unlink(missing_ok=True)


def render_comparison(left_video: Path, right_video: Path, output_path: Path) -> None:
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(left_video),
            "-i",
            str(right_video),
            "-filter_complex",
            "[0:v][1:v]hstack=inputs=2[v]",
            "-map",
            "[v]",
            "-map",
            "1:a?",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-c:a",
            "aac",
            "-shortest",
            str(output_path),
        ]
    )


def main() -> None:
    args = parse_args()
    preview = args.clip_dir / "preview_4fps.mp4"
    if not preview.exists():
        raise FileNotFoundError(f"Missing dense preview video: {preview}")

    outdir = args.clip_dir / "upsample_tests"
    outdir.mkdir(parents=True, exist_ok=True)

    hold = outdir / f"hold_{args.fps}fps.mp4"
    blend = outdir / f"blend_{args.fps}fps.mp4"
    mci = outdir / f"mci_{args.fps}fps.mp4"
    compare = outdir / f"hold_vs_mci_{args.fps}fps.mp4"

    render_method(preview, f"fps={args.fps}", hold)
    render_method(preview, f"minterpolate=fps={args.fps}:mi_mode=blend", blend)
    render_method(
        preview,
        f"minterpolate=fps={args.fps}:mi_mode=mci:mc_mode=aobmc:me_mode=bilat:mb_size=8:search_param=32",
        mci,
    )
    render_comparison(hold, mci, compare)


if __name__ == "__main__":
    main()
