#!/usr/bin/env python3
"""Transcribe an audio file with mlx-whisper and save JSON, TXT, and SRT outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import mlx_whisper


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audio", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--model",
        default="mlx-community/whisper-large-v3-turbo",
        help="MLX Whisper model repo or local path",
    )
    parser.add_argument("--language", default="en")
    parser.add_argument("--word-timestamps", action="store_true")
    return parser.parse_args()


def format_srt_time(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis == 1000:
        secs += 1
        millis = 0
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    result = mlx_whisper.transcribe(
        str(args.audio),
        path_or_hf_repo=args.model,
        language=args.language,
        verbose=False,
        word_timestamps=args.word_timestamps,
    )

    json_path = args.output_dir / "transcript.json"
    txt_path = args.output_dir / "transcript.txt"
    srt_path = args.output_dir / "transcript.srt"

    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))

    segments = result.get("segments", [])
    txt_lines = []
    srt_lines = []
    for idx, segment in enumerate(segments, start=1):
        start = float(segment["start"])
        end = float(segment["end"])
        text = segment["text"].strip()
        txt_lines.append(f"[{start:8.2f} - {end:8.2f}] {text}")
        srt_lines.extend(
            [
                str(idx),
                f"{format_srt_time(start)} --> {format_srt_time(end)}",
                text,
                "",
            ]
        )

    txt_path.write_text("\n".join(txt_lines) + "\n")
    srt_path.write_text("\n".join(srt_lines))

    print(f"Saved {json_path}")
    print(f"Saved {txt_path}")
    print(f"Saved {srt_path}")


if __name__ == "__main__":
    main()
