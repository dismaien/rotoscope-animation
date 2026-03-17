#!/usr/bin/env python3
import argparse
import math
import shutil
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a smaller paired dataset subset from an existing ai-toolkit prepared dataset."
    )
    parser.add_argument("--source-root", required=True, help="Existing prepared dataset root.")
    parser.add_argument("--output-root", required=True, help="Subset dataset root to create.")
    parser.add_argument("--train-count", type=int, default=128, help="Train examples to keep. Default: 128")
    parser.add_argument("--val-count", type=int, default=24, help="Validation examples to keep. Default: 24")
    parser.add_argument("--holdout-count", type=int, default=24, help="Holdout examples to keep. Default: 24")
    return parser.parse_args()


def ensure_clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def sorted_stems(directory: Path) -> list[str]:
    return sorted(path.stem for path in directory.glob("*.png"))


def evenly_spaced(items: list[str], count: int) -> list[str]:
    if count >= len(items):
        return items[:]
    if count <= 0:
        return []

    positions = []
    for i in range(count):
        position = round(i * (len(items) - 1) / max(count - 1, 1))
        positions.append(position)

    selected = []
    used = set()
    for position in positions:
        while position in used and position + 1 < len(items):
            position += 1
        if position not in used:
            used.add(position)
            selected.append(items[position])
    return selected


def link_file(source: Path, target: Path) -> None:
    if target.exists() or target.is_symlink():
        target.unlink()
    target.symlink_to(source)


def populate_split(source_root: Path, output_root: Path, split: str, count: int) -> int:
    source_styled = source_root / split / "styled"
    source_control = source_root / split / "control"

    target_styled = output_root / split / "styled"
    target_control = output_root / split / "control"
    target_styled.mkdir(parents=True, exist_ok=True)
    target_control.mkdir(parents=True, exist_ok=True)

    stems = sorted_stems(source_styled)
    chosen = evenly_spaced(stems, count)

    for stem in chosen:
        for ext in [".png", ".txt"]:
            source_file = source_styled / f"{stem}{ext}"
            if source_file.exists():
                link_file(source_file, target_styled / source_file.name)
        control_file = source_control / f"{stem}.png"
        if control_file.exists():
            link_file(control_file, target_control / control_file.name)

    return len(chosen)


def main() -> None:
    args = parse_args()
    source_root = Path(args.source_root).expanduser().resolve()
    output_root = Path(args.output_root).expanduser().resolve()
    ensure_clean_dir(output_root)

    counts = {
        "train": args.train_count,
        "val": args.val_count,
        "holdout": args.holdout_count,
    }

    summary = {}
    for split, count in counts.items():
        summary[split] = populate_split(source_root, output_root, split, count)

    for split, count in summary.items():
        print(f"{split}: {count}")


if __name__ == "__main__":
    main()
