#!/usr/bin/env python3
"""Generate dense Gemini image edits for a short hero clip.

The script only generates non-anchor frames for a fixed clip and can render
an immediate preview video by interleaving existing 1 fps anchors with the new
quarter-second frames.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path


DEFAULT_PROMPT = (
    "Transform this interview frame into a hand-painted rotoscope animation inspired by "
    "Waking Life (2001) and A Scanner Darkly. Bold dark contour lines, painterly color "
    "blocking, visible brushstrokes, cinematic color, and a hand-painted motion feel. "
    "Preserve the woman exactly: same facial structure, same lip fullness, same expression, "
    "same gaze, same head angle, same red hair, same clothing, same jewelry, and the same "
    "pool background and framing. Flatter through paint handling and finish, not by changing "
    "identity. Keep the mouth shape accurate. Do not thin the lips, deepen smile lines, "
    "exaggerate skin texture, or alter facial proportions."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-video", required=True, type=Path)
    parser.add_argument("--anchor-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--start-sec", required=True, type=int)
    parser.add_argument("--duration-sec", required=True, type=int)
    parser.add_argument("--fps", type=int, default=4)
    parser.add_argument("--model", default="gemini-3.1-flash-image-preview")
    parser.add_argument("--unit-cost", type=float, default=0.067)
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--render-preview", action="store_true")
    return parser.parse_args()


def run(cmd: list[str]) -> None:
    print("+", " ".join(str(c) for c in cmd), flush=True)
    subprocess.run(cmd, check=True)


def extract_inputs(source_video: Path, start: int, duration: int, fps: int, outdir: Path) -> list[Path]:
    outdir.mkdir(parents=True, exist_ok=True)
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
            f"fps={fps}",
            str(outdir / "frame_%04d.png"),
        ]
    )
    return sorted(outdir.glob("frame_*.png"))


def extract_audio(source_video: Path, start: int, duration: int, outpath: Path) -> None:
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
            str(outpath),
        ]
    )


def request_image(api_key: str, model: str, prompt: str, image_path: Path, output_path: Path) -> bool:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    image_data = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {"inlineData": {"mimeType": "image/png", "data": image_data}},
                ]
            }
        ],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {"aspectRatio": "16:9"},
        },
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read(), strict=False)
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", errors="ignore")[:400]
        print(f"HTTP {err.code} for {image_path.name}: {body}", flush=True)
        return False
    except Exception as err:
        print(f"Error for {image_path.name}: {err}", flush=True)
        return False

    for part in result.get("candidates", [{}])[0].get("content", {}).get("parts", []):
        if "inlineData" in part:
            output_path.write_bytes(base64.b64decode(part["inlineData"]["data"]))
            return True
    print(f"No image returned for {image_path.name}", flush=True)
    return False


def interleave_frames(
    anchor_dir: Path,
    generated_dir: Path,
    start_sec: int,
    duration_sec: int,
    fps: int,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for second in range(start_sec, start_sec + duration_sec):
        anchor = anchor_dir / f"frame_{second:04d}.png"
        local_sec = second - start_sec
        for sub in range(fps):
            out_idx = local_sec * fps + sub + 1
            out_path = output_dir / f"frame_{out_idx:04d}.png"
            if sub == 0:
                if out_path.exists():
                    out_path.unlink()
                out_path.symlink_to(anchor.resolve())
            else:
                dense = generated_dir / f"frame_s{second:04d}_q{sub}.png"
                if not dense.exists():
                    raise FileNotFoundError(f"Missing dense frame {dense}")
                if out_path.exists():
                    out_path.unlink()
                out_path.symlink_to(dense.resolve())


def render_preview(frames_dir: Path, audio_path: Path, fps: int, output_path: Path) -> None:
    temp_video = output_path.with_suffix(".video.mp4")
    run(
        [
            "ffmpeg",
            "-y",
            "-framerate",
            str(fps),
            "-i",
            str(frames_dir / "frame_%04d.png"),
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


def main() -> None:
    args = parse_args()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("Set GEMINI_API_KEY before running this script.")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    inputs_dir = args.output_dir / "inputs"
    dense_dir = args.output_dir / "generated"
    preview_dir = args.output_dir / "preview_frames"
    audio_path = args.output_dir / "audio.m4a"
    dense_dir.mkdir(parents=True, exist_ok=True)

    source_frames = extract_inputs(args.source_video, args.start_sec, args.duration_sec, args.fps, inputs_dir)
    extract_audio(args.source_video, args.start_sec, args.duration_sec, audio_path)

    to_generate: list[tuple[Path, Path, int, int]] = []
    for frame_idx, input_path in enumerate(source_frames):
        second = args.start_sec + (frame_idx // args.fps)
        sub = frame_idx % args.fps
        if sub == 0:
            continue
        output_path = dense_dir / f"frame_s{second:04d}_q{sub}.png"
        if output_path.exists() and output_path.stat().st_size > 10_000:
            continue
        to_generate.append((input_path, output_path, second, sub))

    estimated_cost = len(to_generate) * args.unit_cost
    metadata = {
        "model": args.model,
        "unit_cost": args.unit_cost,
        "frames_to_generate": len(to_generate),
        "estimated_cost": round(estimated_cost, 4),
        "start_sec": args.start_sec,
        "duration_sec": args.duration_sec,
        "fps": args.fps,
    }
    (args.output_dir / "request_plan.json").write_text(json.dumps(metadata, indent=2))
    print(json.dumps(metadata, indent=2), flush=True)

    ok = 0
    failed = 0
    start_time = time.time()
    for i, (input_path, output_path, second, sub) in enumerate(to_generate, start=1):
        success = request_image(api_key, args.model, args.prompt, input_path, output_path)
        if success:
            ok += 1
        else:
            failed += 1
        print(f"[{i}/{len(to_generate)}] second={second} q={sub} ok={ok} failed={failed}", flush=True)

    summary = {
        **metadata,
        "completed": ok,
        "failed": failed,
        "elapsed_sec": round(time.time() - start_time, 2),
    }
    (args.output_dir / "result_summary.json").write_text(json.dumps(summary, indent=2))

    if args.render_preview:
        interleave_frames(
            args.anchor_dir,
            dense_dir,
            args.start_sec,
            args.duration_sec,
            args.fps,
            preview_dir,
        )
        render_preview(preview_dir, audio_path, args.fps, args.output_dir / "preview_4fps.mp4")

    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
