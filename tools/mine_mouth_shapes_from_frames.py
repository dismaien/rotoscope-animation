#!/usr/bin/env python3
import argparse
import csv
import math
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


@dataclass
class Sample:
    image_path: Path
    sequence_index: int
    frame_number: int | None
    bbox: tuple[int, int, int, int]
    openness: float
    sharpness: float
    feature: np.ndarray


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Mine diverse mouth and expression candidates from extracted keyframes."
    )
    parser.add_argument("--frames-dir", required=True, help="Directory of extracted frames.")
    parser.add_argument("--outdir", required=True, help="Directory for CSV and copied candidates.")
    parser.add_argument(
        "--num-candidates",
        type=int,
        default=60,
        help="How many candidate frames to export. Default: 60",
    )
    parser.add_argument(
        "--min-gap-frames",
        type=int,
        default=3,
        help="Minimum gap in sequence index between chosen samples. Default: 3",
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


def iter_images(directory: Path) -> list[Path]:
    return sorted(
        path for path in directory.rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )


def frame_number_from_name(path: Path) -> int | None:
    matches = re.findall(r"(\d+)", path.stem)
    if not matches:
        return None
    return int(matches[-1])


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


def feature_from_crop(crop_bgr: np.ndarray) -> tuple[np.ndarray, float, float]:
    gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    small = cv2.resize(gray, (48, 32), interpolation=cv2.INTER_AREA)
    feature = small.astype(np.float32).reshape(-1) / 255.0
    feature = feature - feature.mean()
    feature = feature / (np.linalg.norm(feature) + 1e-8)

    center_band = small[10:24, 10:38]
    openness = float(np.mean(np.clip((110 - center_band) / 110.0, 0.0, 1.0)))
    sharpness = float(cv2.Laplacian(small, cv2.CV_32F).var())
    return feature, openness, sharpness


def cosine_distance(a: np.ndarray, b: np.ndarray) -> float:
    return float(1.0 - np.dot(a, b))


def load_samples(frames_dir: Path, cascade: cv2.CascadeClassifier) -> list[Sample]:
    image_paths = iter_images(frames_dir)
    samples: list[Sample] = []
    last_bbox: tuple[int, int, int, int] | None = None

    for sequence_index, image_path in enumerate(image_paths):
        frame = cv2.imread(str(image_path))
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

        feature, openness, sharpness = feature_from_crop(crop)
        samples.append(
            Sample(
                image_path=image_path,
                sequence_index=sequence_index,
                frame_number=frame_number_from_name(image_path),
                bbox=bbox,
                openness=openness,
                sharpness=sharpness,
                feature=feature,
            )
        )
        last_bbox = bbox

    return samples


def farthest_point_selection(samples: list[Sample], count: int, min_gap_frames: int) -> list[Sample]:
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
            idx = int(idx)
            if idx in selected:
                continue
            seq = samples[idx].sequence_index
            if any(abs(seq - samples[s_idx].sequence_index) < min_gap_frames for s_idx in selected):
                continue
            chosen = idx
            break
        if chosen is None:
            break
        selected.append(chosen)
        dists = np.array([cosine_distance(features[chosen], feat) for feat in features], dtype=np.float32)
        min_dists = np.minimum(min_dists, dists)

    return sorted([samples[idx] for idx in selected], key=lambda s: s.sequence_index)


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
        label = path.stem.replace("candidate_", "")
        cv2.rectangle(img, (0, tile_h - 32), (tile_w, tile_h), (0, 0, 0), -1)
        cv2.putText(
            img,
            label,
            (12, tile_h - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        thumbs.append(img)

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
                "source_frame_path",
                "sequence_index",
                "frame_number",
                "mouth_openness_proxy",
                "mouth_sharpness_proxy",
                "face_x",
                "face_y",
                "face_w",
                "face_h",
                "notes",
            ]
        )
        for rank, sample in enumerate(samples, start=1):
            x, y, w, h = sample.bbox
            writer.writerow(
                [
                    rank,
                    str(sample.image_path.resolve()),
                    sample.sequence_index,
                    "" if sample.frame_number is None else sample.frame_number,
                    f"{sample.openness:.6f}",
                    f"{sample.sharpness:.6f}",
                    x,
                    y,
                    w,
                    h,
                    "",
                ]
            )


def main() -> None:
    args = parse_args()
    frames_dir = Path(args.frames_dir).expanduser().resolve()
    outdir = Path(args.outdir).expanduser().resolve()
    candidates_dir = outdir / "frames"
    ensure_dir(candidates_dir)

    samples = load_samples(frames_dir, face_detector())
    if not samples:
        raise RuntimeError("No candidate face/mouth samples were detected.")

    selected = farthest_point_selection(samples, args.num_candidates, args.min_gap_frames)

    copied_paths = []
    for rank, sample in enumerate(selected, start=1):
        frame_label = "na" if sample.frame_number is None else f"{sample.frame_number:04d}"
        outpath = candidates_dir / f"candidate_{rank:03d}_frame_{frame_label}.jpg"
        shutil.copy2(sample.image_path, outpath)
        copied_paths.append(outpath)

    write_csv(selected, outdir / "candidates.csv")
    build_contact_sheet(copied_paths, outdir / "contact_sheet.jpg", columns=args.contact_cols)


if __name__ == "__main__":
    main()
