#!/usr/bin/env python3
"""Render side-by-side motion test clips for a rotoscope segment.

Methods:
- hold: duplicate 1 fps anchors to the target fps
- blend: ffmpeg blend interpolation on the 1 fps anchors
- mci: ffmpeg motion-compensated interpolation on the 1 fps anchors
- ebsynth: propagate each anchor onto nearby source frames and blend directions
"""

from __future__ import annotations

import argparse
import math
import shutil
import subprocess
from pathlib import Path


def run(cmd: list[str], *, quiet: bool = False) -> None:
    if quiet:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        print("+", " ".join(str(part) for part in cmd), flush=True)
        subprocess.run(cmd, check=True)


def ffprobe_size(image_path: Path) -> tuple[int, int]:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "stream=width,height",
        "-of",
        "csv=p=0:s=x",
        str(image_path),
    ]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    width, height = result.stdout.strip().split("x")
    return int(width), int(height)


def ensure_clean_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def extract_audio(source_video: Path, start: float, duration: float, output_audio: Path) -> None:
    run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            str(start),
            "-i",
            str(source_video),
            "-t",
            str(duration),
            "-vn",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(output_audio),
        ]
    )


def render_ffmpeg_method(
    anchor_video: Path,
    audio_path: Path,
    start: float,
    duration: float,
    video_filter: str,
    output_path: Path,
) -> None:
    temp_video = output_path.with_suffix(".video.mp4")
    run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            str(start),
            "-i",
            str(anchor_video),
            "-t",
            str(duration),
            "-an",
            "-vf",
            video_filter,
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
            str(audio_path),
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-shortest",
            str(output_path),
        ]
    )
    temp_video.unlink(missing_ok=True)


def extract_scaled_source_frames(
    source_video: Path,
    start: float,
    duration: float,
    fps: int,
    size: tuple[int, int],
    output_dir: Path,
) -> list[Path]:
    ensure_clean_dir(output_dir)
    width, height = size
    pattern = output_dir / "frame_%04d.png"
    run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            str(start),
            "-i",
            str(source_video),
            "-t",
            str(duration),
            "-an",
            "-vf",
            f"fps={fps},scale={width}:{height}:flags=lanczos",
            str(pattern),
        ]
    )
    return sorted(output_dir.glob("frame_*.png"))


def scale_key_guides(
    source_keyframe_dir: Path,
    start_sec: int,
    end_sec: int,
    size: tuple[int, int],
    output_dir: Path,
) -> None:
    ensure_clean_dir(output_dir)
    width, height = size
    for second in range(start_sec, end_sec + 1):
        src = source_keyframe_dir / f"frame_{second:04d}.png"
        out = output_dir / src.name
        if out.exists():
            continue
        run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(src),
                "-vf",
                f"scale={width}:{height}:flags=lanczos",
                str(out),
            ],
            quiet=True,
        )


def render_ebsynth(
    ebsynth_bin: Path,
    styled_dir: Path,
    guide_dir: Path,
    target_frames: list[Path],
    start_sec: int,
    duration_sec: int,
    fps: int,
    work_dir: Path,
    audio_path: Path,
    output_path: Path,
) -> None:
    forward_dir = work_dir / "ebsynth_forward"
    backward_dir = work_dir / "ebsynth_backward"
    blended_dir = work_dir / "ebsynth_blended"
    ensure_clean_dir(forward_dir)
    ensure_clean_dir(backward_dir)
    ensure_clean_dir(blended_dir)

    total_frames = len(target_frames)
    end_sec = start_sec + duration_sec

    for index, target_path in enumerate(target_frames):
        frame_number = index + 1
        local_time = index / fps
        left_sec = start_sec + math.floor(local_time)
        right_sec = min(left_sec + 1, end_sec)
        is_anchor_frame = (index % fps) == 0

        left_style = styled_dir / f"frame_{left_sec:04d}.png"
        right_style = styled_dir / f"frame_{right_sec:04d}.png"
        left_guide = guide_dir / left_style.name
        right_guide = guide_dir / right_style.name
        forward_out = forward_dir / f"frame_{frame_number:04d}.png"
        backward_out = backward_dir / f"frame_{frame_number:04d}.png"

        if not forward_out.exists():
            if is_anchor_frame:
                shutil.copy2(left_style, forward_out)
            else:
                run(
                    [
                        str(ebsynth_bin),
                        "-style",
                        str(left_style),
                        "-guide",
                        str(left_guide),
                        str(target_path),
                        "-output",
                        str(forward_out),
                        "-weight",
                        "1.0",
                        "-uniformity",
                        "3500",
                        "-patchsize",
                        "7",
                    ],
                    quiet=True,
                )

        if not backward_out.exists():
            if is_anchor_frame:
                shutil.copy2(left_style, backward_out)
            else:
                run(
                    [
                        str(ebsynth_bin),
                        "-style",
                        str(right_style),
                        "-guide",
                        str(right_guide),
                        str(target_path),
                        "-output",
                        str(backward_out),
                        "-weight",
                        "1.0",
                        "-uniformity",
                        "3500",
                        "-patchsize",
                        "7",
                    ],
                    quiet=True,
                )

        if frame_number == 1 or frame_number % 24 == 0 or frame_number == total_frames:
            print(f"ebsynth {frame_number}/{total_frames}", flush=True)

    blended_pattern = blended_dir / "frame_%04d.png"
    run(
        [
            "ffmpeg",
            "-y",
            "-framerate",
            str(fps),
            "-i",
            str(forward_dir / "frame_%04d.png"),
            "-framerate",
            str(fps),
            "-i",
            str(backward_dir / "frame_%04d.png"),
            "-filter_complex",
            f"[0:v][1:v]blend=all_expr='A*(1-(mod(N\\,{fps})/{fps}))+B*(mod(N\\,{fps})/{fps})'",
            str(blended_pattern),
        ]
    )

    temp_video = output_path.with_suffix(".video.mp4")
    run(
        [
            "ffmpeg",
            "-y",
            "-framerate",
            str(fps),
            "-i",
            str(blended_dir / "frame_%04d.png"),
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
            str(audio_path),
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-shortest",
            str(output_path),
        ]
    )
    temp_video.unlink(missing_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-video", required=True, type=Path)
    parser.add_argument("--anchor-video", required=True, type=Path)
    parser.add_argument("--styled-dir", required=True, type=Path)
    parser.add_argument("--source-keyframe-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--ebsynth-bin", required=True, type=Path)
    parser.add_argument("--start-sec", required=True, type=int)
    parser.add_argument("--duration-sec", required=True, type=int)
    parser.add_argument("--fps", type=int, default=12)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    anchor_probe = sorted(args.styled_dir.glob("frame_*.png"))
    if not anchor_probe:
        raise FileNotFoundError(f"No styled anchors found in {args.styled_dir}")
    size = ffprobe_size(anchor_probe[0])

    audio_path = args.output_dir / "audio.m4a"
    extract_audio(args.source_video, args.start_sec, args.duration_sec, audio_path)

    render_ffmpeg_method(
        args.anchor_video,
        audio_path,
        args.start_sec,
        args.duration_sec,
        f"fps={args.fps}",
        args.output_dir / "hold_12fps.mp4",
    )
    render_ffmpeg_method(
        args.anchor_video,
        audio_path,
        args.start_sec,
        args.duration_sec,
        f"minterpolate=fps={args.fps}:mi_mode=blend",
        args.output_dir / "blend_12fps.mp4",
    )
    render_ffmpeg_method(
        args.anchor_video,
        audio_path,
        args.start_sec,
        args.duration_sec,
        f"minterpolate=fps={args.fps}:mi_mode=mci:mc_mode=aobmc:me_mode=bilat:mb_size=8:search_param=32",
        args.output_dir / "mci_12fps.mp4",
    )

    work_dir = args.output_dir / "work"
    scaled_source_dir = work_dir / "source_frames"
    guide_dir = work_dir / "guide_frames"
    target_frames = extract_scaled_source_frames(
        args.source_video,
        args.start_sec,
        args.duration_sec,
        args.fps,
        size,
        scaled_source_dir,
    )
    scale_key_guides(
        args.source_keyframe_dir,
        args.start_sec,
        args.start_sec + args.duration_sec,
        size,
        guide_dir,
    )
    render_ebsynth(
        args.ebsynth_bin,
        args.styled_dir,
        guide_dir,
        target_frames,
        args.start_sec,
        args.duration_sec,
        args.fps,
        work_dir,
        audio_path,
        args.output_dir / "ebsynth_12fps.mp4",
    )


if __name__ == "__main__":
    main()
