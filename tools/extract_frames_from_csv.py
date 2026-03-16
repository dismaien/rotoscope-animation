#!/usr/bin/env python3
import argparse
import csv
import subprocess
from pathlib import Path


TIMESTAMP_COLUMNS = ("timestamp_sec", "timestamp", "timecode")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract full-frame screenshots from a video using timestamps stored in a CSV."
    )
    parser.add_argument("--video", required=True, help="Source video path.")
    parser.add_argument("--csv", required=True, help="CSV file containing timestamps.")
    parser.add_argument("--outdir", required=True, help="Directory for extracted frames.")
    parser.add_argument(
        "--prefix",
        default="frame",
        help="Filename prefix for extracted images. Default: frame",
    )
    return parser.parse_args()


def pick_timestamp(row: dict[str, str]) -> str | None:
    for column in TIMESTAMP_COLUMNS:
        value = row.get(column, "").strip()
        if value:
            return value
    return None


def safe_label(value: str) -> str:
    return value.replace(":", "-").replace("/", "-").replace(" ", "_")


def extract_frame(video: Path, timestamp: str, outpath: Path) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-ss",
        timestamp,
        "-i",
        str(video),
        "-frames:v",
        "1",
        str(outpath),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main() -> None:
    args = parse_args()
    video_path = Path(args.video).expanduser().resolve()
    csv_path = Path(args.csv).expanduser().resolve()
    outdir = Path(args.outdir).expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    extracted = 0
    with csv_path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for index, row in enumerate(reader, start=1):
            timestamp = pick_timestamp(row)
            if not timestamp:
                continue
            label = row.get("frame_number", "").strip() or row.get("pair_id", "").strip() or f"{index:04d}"
            outpath = outdir / f"{args.prefix}_{index:03d}_{safe_label(label)}_{safe_label(timestamp)}.jpg"
            extract_frame(video_path, timestamp, outpath)
            extracted += 1

    print(f"Extracted {extracted} frame(s) to {outdir}")


if __name__ == "__main__":
    main()
