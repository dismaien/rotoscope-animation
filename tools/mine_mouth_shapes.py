#!/usr/bin/env python3
import argparse
import csv
import math
import subprocess
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


@dataclass
class Sample:
    frame_index: int
    timestamp_sec: float
    bbox: tuple[int, int, int, int]
    openness: float
    sharpness: float
    feature: np.ndarray


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Mine diverse mouth/expression frames from a mostly static interview video."
    )
    parser.add_argument("--video", required=True, help="Path to the source video.")
    parser.add_argument("--outdir", required=True, help="Directory for outputs.")
    parser.add_argument(
        "--sample-fps",
        type=float,
        default=2.0,
        help="Sampling rate for the scan pass. Default: 2.0",
    )
    parser.add_argument(
        "--num-candidates",
        type=int,
        default=80,
        help="How many candidate frames to export. Default: 80",
    )
    parser.add_argument(
        "--min-gap-sec",
        type=float,
        default=1.0,
        help="Minimum time gap between selected candidates. Default: 1.0",
    )
    parser.add_argument(
        "--contact-cols",
        type=int,
        default=5,
        help="Columns in the contact sheet. Default: 5",
    )
    return parser.parse_args()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


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
    faces = cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(80, 80),
    )
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


def feature_from_crop(crop_bgr: np.ndarray) -> tuple[np.ndarray, float, float]:
    gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    small = cv2.resize(gray, (48, 32), interpolation=cv2.INTER_AREA)
    feature = small.astype(np.float32).reshape(-1) / 255.0
    feature = feature - feature.mean()
    norm = np.linalg.norm(feature) + 1e-8
    feature = feature / norm

    center_band = small[10:24, 10:38]
    openness = float(np.mean(np.clip((110 - center_band) / 110.0, 0.0, 1.0)))
    sharpness = float(cv2.Laplacian(small, cv2.CV_32F).var())
    return feature, openness, sharpness


def scan_video(
    video_path: Path,
    cascade: cv2.CascadeClassifier,
    sample_fps: float,
) -> tuple[list[Sample], float]:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    native_fps = cap.get(cv2.CAP_PROP_FPS)
    if not native_fps or native_fps <= 0:
        raise RuntimeError("Could not determine source FPS.")

    step = max(1, int(round(native_fps / sample_fps)))
    samples: list[Sample] = []
    last_bbox: tuple[int, int, int, int] | None = None
    frame_index = 0

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if frame_index % step != 0:
            frame_index += 1
            continue

        bbox = detect_face(frame, cascade)
        if bbox is None:
            bbox = last_bbox
        if bbox is None:
            frame_index += 1
            continue

        crop = mouth_crop(frame, bbox)
        if crop.size == 0 or crop.shape[0] < 20 or crop.shape[1] < 20:
            frame_index += 1
            continue

        feature, openness, sharpness = feature_from_crop(crop)
        timestamp_sec = frame_index / native_fps
        samples.append(
            Sample(
                frame_index=frame_index,
                timestamp_sec=timestamp_sec,
                bbox=bbox,
                openness=openness,
                sharpness=sharpness,
                feature=feature,
            )
        )
        last_bbox = bbox
        frame_index += 1

    cap.release()
    return samples, native_fps


def cosine_distance(a: np.ndarray, b: np.ndarray) -> float:
    return float(1.0 - np.dot(a, b))


def farthest_point_selection(
    samples: list[Sample],
    count: int,
    min_gap_sec: float,
) -> list[Sample]:
    if not samples:
        return []

    openness = np.array([s.openness for s in samples], dtype=np.float32)
    sharpness = np.array([s.sharpness for s in samples], dtype=np.float32)
    op_norm = (openness - openness.mean()) / (openness.std() + 1e-6)
    sh_norm = (sharpness - sharpness.mean()) / (sharpness.std() + 1e-6)

    features = []
    for idx, sample in enumerate(samples):
        descriptor = np.concatenate(
            [sample.feature, np.array([0.35 * op_norm[idx], 0.15 * sh_norm[idx]], dtype=np.float32)]
        )
        descriptor = descriptor / (np.linalg.norm(descriptor) + 1e-8)
        features.append(descriptor)

    seed_indices = []
    seed_indices.append(int(np.argmax(openness)))
    seed_indices.append(int(np.argmin(openness)))
    seed_indices.append(int(np.argmax(sharpness)))

    selected: list[int] = []
    for idx in seed_indices:
        if idx not in selected:
            selected.append(idx)

    min_dists = np.full(len(samples), np.inf, dtype=np.float32)
    for idx in selected:
        dists = np.array([cosine_distance(features[idx], feat) for feat in features], dtype=np.float32)
        min_dists = np.minimum(min_dists, dists)

    while len(selected) < min(count, len(samples)):
        candidates = np.argsort(-min_dists)
        chosen = None
        for idx in candidates:
            if idx in selected:
                continue
            ts = samples[int(idx)].timestamp_sec
            if any(abs(ts - samples[s_idx].timestamp_sec) < min_gap_sec for s_idx in selected):
                continue
            chosen = int(idx)
            break
        if chosen is None:
            break
        selected.append(chosen)
        dists = np.array([cosine_distance(features[chosen], feat) for feat in features], dtype=np.float32)
        min_dists = np.minimum(min_dists, dists)

    return sorted([samples[idx] for idx in selected], key=lambda s: s.timestamp_sec)


def format_timestamp(seconds: float) -> str:
    total = int(round(seconds * 1000))
    ms = total % 1000
    total //= 1000
    s = total % 60
    total //= 60
    m = total % 60
    h = total // 60
    return f"{h:02d}-{m:02d}-{s:02d}-{ms:03d}"


def export_full_frame(video_path: Path, sample: Sample, output_path: Path) -> None:
    ts = max(sample.timestamp_sec, 0.0)
    cmd = [
        "ffmpeg",
        "-y",
        "-ss",
        f"{ts:.3f}",
        "-i",
        str(video_path),
        "-frames:v",
        "1",
        str(output_path),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def build_contact_sheet(image_paths: list[Path], output_path: Path, columns: int = 5) -> None:
    if not image_paths:
        return

    thumbs = []
    tile_h = 180
    tile_w = 320
    for path in image_paths:
        img = cv2.imread(str(path))
        if img is None:
            continue
        img = cv2.resize(img, (tile_w, tile_h), interpolation=cv2.INTER_AREA)
        label = path.stem.replace("frame_", "")
        cv2.rectangle(img, (0, tile_h - 32), (tile_w, tile_h), (0, 0, 0), -1)
        cv2.putText(
            img,
            label,
            (12, tile_h - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        thumbs.append(img)

    if not thumbs:
        return

    rows = math.ceil(len(thumbs) / columns)
    sheet = np.full((rows * tile_h, columns * tile_w, 3), 240, dtype=np.uint8)
    for i, thumb in enumerate(thumbs):
        row = i // columns
        col = i % columns
        sheet[row * tile_h : (row + 1) * tile_h, col * tile_w : (col + 1) * tile_w] = thumb
    cv2.imwrite(str(output_path), sheet)


def write_csv(samples: list[Sample], output_path: Path) -> None:
    with output_path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "rank",
                "timestamp",
                "timestamp_sec",
                "frame_index",
                "mouth_openness_proxy",
                "mouth_sharpness_proxy",
                "face_x",
                "face_y",
                "face_w",
                "face_h",
            ]
        )
        for rank, sample in enumerate(samples, start=1):
            x, y, w, h = sample.bbox
            writer.writerow(
                [
                    rank,
                    format_timestamp(sample.timestamp_sec).replace("-", ":"),
                    f"{sample.timestamp_sec:.3f}",
                    sample.frame_index,
                    f"{sample.openness:.6f}",
                    f"{sample.sharpness:.6f}",
                    x,
                    y,
                    w,
                    h,
                ]
            )


def main() -> None:
    args = parse_args()
    video_path = Path(args.video).expanduser().resolve()
    outdir = Path(args.outdir).expanduser().resolve()
    frames_dir = outdir / "frames"
    ensure_dir(frames_dir)

    cascade = face_detector()
    samples, native_fps = scan_video(video_path, cascade, args.sample_fps)
    if not samples:
        raise RuntimeError("No candidate face/mouth samples were detected.")

    selected = farthest_point_selection(samples, args.num_candidates, args.min_gap_sec)

    exported_paths: list[Path] = []
    for rank, sample in enumerate(selected, start=1):
        stamp = format_timestamp(sample.timestamp_sec)
        output_path = frames_dir / f"frame_{rank:03d}_{stamp}.jpg"
        export_full_frame(video_path, sample, output_path)
        exported_paths.append(output_path)

    write_csv(selected, outdir / "candidates.csv")
    build_contact_sheet(exported_paths, outdir / "contact_sheet.jpg", columns=args.contact_cols)

    summary = outdir / "README.txt"
    summary.write_text(
        "\n".join(
            [
                f"Video: {video_path}",
                f"Native FPS: {native_fps:.6f}",
                f"Scan sample FPS: {args.sample_fps}",
                f"Selected candidates: {len(selected)}",
                f"Frames directory: {frames_dir}",
                "Notes:",
                "- Candidates are selected for visual diversity in the mouth region, not phoneme labels.",
                "- Use candidates.csv to sort or filter timestamps.",
                "- contact_sheet.jpg is intended for quick human review before Nano Banana generation.",
            ]
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
