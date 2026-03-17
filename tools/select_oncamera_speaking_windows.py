#!/usr/bin/env python3
import argparse
import csv
import math
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


@dataclass
class FrameMetric:
    frame_path: Path
    second_index: int
    bbox: tuple[int, int, int, int]
    openness: float
    sharpness: float
    face_ratio: float
    center_score: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Find better short windows where the on-camera subject appears to be actively speaking."
    )
    parser.add_argument("--frames-dir", required=True, help="1 fps extracted source keyframes directory.")
    parser.add_argument("--source-video", required=True, help="Original source video path.")
    parser.add_argument("--styled-video", required=True, help="Rendered styled video path.")
    parser.add_argument("--outdir", required=True, help="Directory for CSV, contact sheet, and preview clips.")
    parser.add_argument(
        "--max-seconds",
        type=int,
        default=792,
        help="Only consider the first N seconds. Default: 792",
    )
    parser.add_argument(
        "--window-seconds",
        type=int,
        default=12,
        help="Length of each candidate window. Default: 12",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=6,
        help="How many non-overlapping windows to keep. Default: 6",
    )
    parser.add_argument(
        "--min-gap-seconds",
        type=int,
        default=12,
        help="Minimum distance between selected window starts. Default: 12",
    )
    return parser.parse_args()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def frame_number_from_name(path: Path) -> int | None:
    matches = re.findall(r"(\d+)", path.stem)
    if not matches:
        return None
    return int(matches[-1])


def iter_images(directory: Path, max_seconds: int) -> list[Path]:
    images = []
    for path in sorted(directory.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        number = frame_number_from_name(path)
        if number is None or number >= max_seconds:
            continue
        images.append(path)
    return images


def face_detector() -> cv2.CascadeClassifier:
    cascade = cv2.CascadeClassifier(
        str(Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml")
    )
    if cascade.empty():
        raise RuntimeError("Failed to load OpenCV Haar cascade for face detection.")
    return cascade


def detect_face(frame_bgr: np.ndarray, cascade: cv2.CascadeClassifier) -> tuple[int, int, int, int] | None:
    height, width = frame_bgr.shape[:2]
    scale = 960 / width if width > 960 else 1.0
    resized = cv2.resize(frame_bgr, (int(width * scale), int(height * scale)))
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))
    if len(faces) == 0:
        return None
    x, y, w, h = max(faces, key=lambda box: box[2] * box[3])
    if scale != 1.0:
        inv = 1.0 / scale
        x, y, w, h = [int(v * inv) for v in (x, y, w, h)]
    return (x, y, w, h)


def mouth_crop(frame_bgr: np.ndarray, bbox: tuple[int, int, int, int]) -> np.ndarray:
    x, y, w, h = bbox
    mx = x + int(0.18 * w)
    my = y + int(0.58 * h)
    mw = int(0.64 * w)
    mh = int(0.24 * h)
    return frame_bgr[my : my + mh, mx : mx + mw]


def openness_and_sharpness(crop_bgr: np.ndarray) -> tuple[float, float]:
    gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    small = cv2.resize(gray, (48, 32), interpolation=cv2.INTER_AREA)
    center_band = small[10:24, 10:38]
    openness = float(np.mean(np.clip((110 - center_band) / 110.0, 0.0, 1.0)))
    sharpness = float(cv2.Laplacian(small, cv2.CV_32F).var())
    return openness, sharpness


def center_score(frame_shape: tuple[int, int, int], bbox: tuple[int, int, int, int]) -> float:
    height, width = frame_shape[:2]
    x, y, w, h = bbox
    cx = x + (w / 2.0)
    cy = y + (h / 2.0)
    dx = (cx - (width / 2.0)) / max(width / 2.0, 1.0)
    dy = (cy - (height / 2.0)) / max(height / 2.0, 1.0)
    distance = math.sqrt(dx * dx + dy * dy)
    return max(0.0, 1.0 - distance)


def collect_metrics(frames_dir: Path, max_seconds: int) -> list[FrameMetric]:
    images = iter_images(frames_dir, max_seconds)
    cascade = face_detector()
    metrics: list[FrameMetric] = []
    last_bbox: tuple[int, int, int, int] | None = None

    for path in images:
        frame = cv2.imread(str(path))
        if frame is None:
            continue
        bbox = detect_face(frame, cascade)
        if bbox is None:
            bbox = last_bbox
        if bbox is None:
            continue

        crop = mouth_crop(frame, bbox)
        if crop.size == 0 or crop.shape[0] < 20 or crop.shape[1] < 20:
            continue

        second_index = frame_number_from_name(path)
        if second_index is None:
            continue

        openness, sharpness = openness_and_sharpness(crop)
        face_ratio = float((bbox[2] * bbox[3]) / (frame.shape[0] * frame.shape[1]))
        metrics.append(
            FrameMetric(
                frame_path=path,
                second_index=second_index,
                bbox=bbox,
                openness=openness,
                sharpness=sharpness,
                face_ratio=face_ratio,
                center_score=center_score(frame.shape, bbox),
            )
        )
        last_bbox = bbox

    return metrics


def format_timestamp(seconds: int) -> str:
    minutes, sec = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{sec:02d}"
    return f"{minutes:02d}:{sec:02d}"


def score_windows(metrics: list[FrameMetric], window_seconds: int) -> list[dict[str, object]]:
    by_second = {metric.second_index: metric for metric in metrics}
    max_second = max(by_second) if by_second else -1
    scored: list[dict[str, object]] = []

    for start in range(0, max_second - window_seconds + 2):
        window = [by_second.get(second) for second in range(start, start + window_seconds)]
        present = [metric for metric in window if metric is not None]
        if len(present) < max(window_seconds - 1, 4):
            continue

        openness = np.array([metric.openness for metric in present], dtype=np.float32)
        face_ratio = np.array([metric.face_ratio for metric in present], dtype=np.float32)
        center = np.array([metric.center_score for metric in present], dtype=np.float32)

        speaking_energy = float(np.mean(openness) + 1.2 * np.mean(np.abs(np.diff(openness))) + 0.8 * np.std(openness))
        framing = float(1.5 * np.mean(face_ratio) + 0.7 * np.mean(center))
        score = speaking_energy + framing

        peak_index = int(np.argmax(openness))
        representative = present[peak_index]
        scored.append(
            {
                "start_sec": start,
                "end_sec": start + window_seconds,
                "timestamp": format_timestamp(start),
                "score": score,
                "speaking_energy": speaking_energy,
                "avg_openness": float(np.mean(openness)),
                "openness_delta": float(np.mean(np.abs(np.diff(openness)))) if len(openness) > 1 else 0.0,
                "avg_face_ratio": float(np.mean(face_ratio)),
                "avg_center_score": float(np.mean(center)),
                "representative_frame": representative.frame_path,
            }
        )

    return sorted(scored, key=lambda row: row["score"], reverse=True)


def select_non_overlapping(rows: list[dict[str, object]], top_k: int, min_gap_seconds: int) -> list[dict[str, object]]:
    selected: list[dict[str, object]] = []
    for row in rows:
        start = int(row["start_sec"])
        if any(abs(start - int(existing["start_sec"])) < min_gap_seconds for existing in selected):
            continue
        selected.append(row)
        if len(selected) >= top_k:
            break
    return selected


def write_csv(rows: list[dict[str, object]], outpath: Path) -> None:
    with outpath.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "rank",
                "start_sec",
                "end_sec",
                "timestamp",
                "score",
                "speaking_energy",
                "avg_openness",
                "openness_delta",
                "avg_face_ratio",
                "avg_center_score",
                "representative_frame",
            ]
        )
        for index, row in enumerate(rows, start=1):
            writer.writerow(
                [
                    index,
                    row["start_sec"],
                    row["end_sec"],
                    row["timestamp"],
                    f"{row['score']:.6f}",
                    f"{row['speaking_energy']:.6f}",
                    f"{row['avg_openness']:.6f}",
                    f"{row['openness_delta']:.6f}",
                    f"{row['avg_face_ratio']:.6f}",
                    f"{row['avg_center_score']:.6f}",
                    str(row["representative_frame"]),
                ]
            )


def build_contact_sheet(rows: list[dict[str, object]], outpath: Path) -> None:
    if not rows:
        return

    thumbs = []
    tile_w = 420
    tile_h = 240
    columns = 2

    for rank, row in enumerate(rows, start=1):
        frame = cv2.imread(str(row["representative_frame"]))
        if frame is None:
            continue
        frame = cv2.resize(frame, (tile_w, tile_h), interpolation=cv2.INTER_AREA)
        cv2.rectangle(frame, (0, tile_h - 56), (tile_w, tile_h), (0, 0, 0), -1)
        label = f"#{rank} {row['timestamp']}  score {row['score']:.2f}"
        label2 = f"open {row['avg_openness']:.2f}  delta {row['openness_delta']:.2f}"
        cv2.putText(frame, label, (12, tile_h - 28), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, label2, (12, tile_h - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.54, (255, 255, 255), 1, cv2.LINE_AA)
        thumbs.append(frame)

    rows_count = math.ceil(len(thumbs) / columns)
    sheet = np.full((rows_count * tile_h, columns * tile_w, 3), 240, dtype=np.uint8)
    for index, thumb in enumerate(thumbs):
        row = index // columns
        col = index % columns
        sheet[row * tile_h : (row + 1) * tile_h, col * tile_w : (col + 1) * tile_w] = thumb
    cv2.imwrite(str(outpath), sheet)


def ffmpeg_extract_clip(video_path: Path, start_sec: int, duration_sec: int, outpath: Path, fps: int | None = None) -> None:
    cmd = ["ffmpeg", "-y", "-ss", str(start_sec), "-t", str(duration_sec), "-i", str(video_path)]
    if fps is not None:
        cmd += ["-vf", f"fps={fps}"]
    cmd += ["-an", str(outpath)]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def ffmpeg_stack(left_path: Path, right_path: Path, outpath: Path) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(left_path),
        "-i",
        str(right_path),
        "-filter_complex",
        "[0:v]fps=12,scale=960:540:force_original_aspect_ratio=decrease,pad=960:540:(ow-iw)/2:(oh-ih)/2[left];"
        "[1:v]fps=12,scale=960:540:force_original_aspect_ratio=decrease,pad=960:540:(ow-iw)/2:(oh-ih)/2[right];"
        "[left][right]hstack=inputs=2[v]",
        "-map",
        "[v]",
        "-an",
        str(outpath),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def write_markdown(rows: list[dict[str, object]], outpath: Path) -> None:
    lines = [
        "# On-Camera Speaking Shortlist",
        "",
        "This shortlist was selected from the first `13:12` of coverage by scoring the `1 fps` source keyframes for:",
        "",
        "- face presence and size",
        "- face centering",
        "- mouth openness",
        "- second-to-second mouth change as a proxy for active speaking",
        "",
        "These are better benchmark candidates than transcript-picked clips because they are chosen from picture first.",
        "",
        "## Recommended Windows",
        "",
    ]

    for rank, row in enumerate(rows, start=1):
        lines.extend(
            [
                f"### `#{rank}` `{format_timestamp(int(row['start_sec']))}-{format_timestamp(int(row['end_sec']))}`",
                "",
                f"- score: `{row['score']:.3f}`",
                f"- speaking energy: `{row['speaking_energy']:.3f}`",
                f"- average mouth openness proxy: `{row['avg_openness']:.3f}`",
                f"- average mouth-change proxy: `{row['openness_delta']:.3f}`",
                f"- representative frame: `{row['representative_frame']}`",
                "",
            ]
        )

    outpath.write_text("\n".join(lines) + "\n")


def export_previews(
    rows: list[dict[str, object]],
    source_video: Path,
    styled_video: Path,
    outdir: Path,
    window_seconds: int,
) -> None:
    clips_dir = outdir / "clips"
    ensure_dir(clips_dir)

    for rank, row in enumerate(rows, start=1):
        start_sec = int(row["start_sec"])
        label = f"rank_{rank:02d}_{start_sec:04d}_{format_timestamp(start_sec).replace(':', '-')}"
        source_clip = clips_dir / f"{label}_source.mp4"
        styled_clip = clips_dir / f"{label}_styled.mp4"
        compare_clip = clips_dir / f"{label}_source_vs_styled.mp4"

        ffmpeg_extract_clip(source_video, start_sec, window_seconds, source_clip)
        ffmpeg_extract_clip(styled_video, start_sec, window_seconds, styled_clip, fps=12)
        ffmpeg_stack(source_clip, styled_clip, compare_clip)


def main() -> None:
    args = parse_args()
    frames_dir = Path(args.frames_dir).expanduser().resolve()
    source_video = Path(args.source_video).expanduser().resolve()
    styled_video = Path(args.styled_video).expanduser().resolve()
    outdir = Path(args.outdir).expanduser().resolve()
    ensure_dir(outdir)

    metrics = collect_metrics(frames_dir, args.max_seconds)
    scored = score_windows(metrics, args.window_seconds)
    selected = select_non_overlapping(scored, args.top_k, args.min_gap_seconds)

    write_csv(scored, outdir / "all_speaking_windows.csv")
    write_csv(selected, outdir / "speaking_windows.csv")
    build_contact_sheet(selected, outdir / "contact_sheet.jpg")
    write_markdown(selected, outdir / "README.md")
    export_previews(selected, source_video, styled_video, outdir, args.window_seconds)

    print(f"Selected {len(selected)} speaking window(s) in {outdir}")


if __name__ == "__main__":
    main()
