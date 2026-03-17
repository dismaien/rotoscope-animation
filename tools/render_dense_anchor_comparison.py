#!/usr/bin/env python3
import argparse
import subprocess
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render side-by-side comparisons for source, 1 fps styled, and dense-anchor styled clips."
    )
    parser.add_argument("--source", required=True, help="Path to the source clip.")
    parser.add_argument("--hold", required=True, help="Path to the current 1 fps styled clip.")
    parser.add_argument("--dense", required=True, help="Path to the dense-anchor styled clip.")
    parser.add_argument("--outdir", required=True, help="Output directory.")
    parser.add_argument("--label", required=True, help="Label prefix for output files.")
    return parser.parse_args()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def run_ffmpeg(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def render_two_up(left: Path, right: Path, outpath: Path) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(left),
        "-i",
        str(right),
        "-filter_complex",
        "[0:v]fps=12,scale=960:540:force_original_aspect_ratio=decrease,pad=960:540:(ow-iw)/2:(oh-ih)/2[left];"
        "[1:v]fps=12,scale=960:540:force_original_aspect_ratio=decrease,pad=960:540:(ow-iw)/2:(oh-ih)/2[right];"
        "[left][right]hstack=inputs=2[v]",
        "-map",
        "[v]",
        "-an",
        str(outpath),
    ]
    run_ffmpeg(cmd)


def render_three_up(source: Path, hold: Path, dense: Path, outpath: Path) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(source),
        "-i",
        str(hold),
        "-i",
        str(dense),
        "-filter_complex",
        "[0:v]fps=12,scale=640:360:force_original_aspect_ratio=decrease,pad=640:360:(ow-iw)/2:(oh-ih)/2[src];"
        "[1:v]fps=12,scale=640:360:force_original_aspect_ratio=decrease,pad=640:360:(ow-iw)/2:(oh-ih)/2[hold];"
        "[2:v]fps=12,scale=640:360:force_original_aspect_ratio=decrease,pad=640:360:(ow-iw)/2:(oh-ih)/2[dense];"
        "[src][hold][dense]hstack=inputs=3[v]",
        "-map",
        "[v]",
        "-an",
        str(outpath),
    ]
    run_ffmpeg(cmd)


def main() -> None:
    args = parse_args()
    outdir = Path(args.outdir).expanduser().resolve()
    ensure_dir(outdir)

    source = Path(args.source).expanduser().resolve()
    hold = Path(args.hold).expanduser().resolve()
    dense = Path(args.dense).expanduser().resolve()

    render_two_up(hold, dense, outdir / f"{args.label}_1fps_vs_4fps.mp4")
    render_three_up(source, hold, dense, outdir / f"{args.label}_source_vs_1fps_vs_4fps.mp4")


if __name__ == "__main__":
    main()
