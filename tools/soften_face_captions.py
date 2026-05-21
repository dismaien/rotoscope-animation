#!/usr/bin/env python3
from pathlib import Path


ROOT = Path("/Users/leona/Documents/Playground/painterly-rotoscope-animation")
DATASET_ROOTS = [
    ROOT / "runs/datasets/local_pilot_subset_v1",
    ROOT / "runs/datasets/flux2_klein_v0_plus_dense_three",
]

OLD_SNIPPETS = [
    (
        "Preserve natural lip fullness. Do not narrow the lips, deepen smile lines, "
        "exaggerate skin texture, or change facial proportions.",
        "Preserve natural lip fullness and a softly contoured jawline. Keep smile lines, "
        "nasolabial folds, forehead lines, glabellar 11s, and under-eye creases soft, "
        "simplified, and flattering. Favor smooth painted skin planes over crease carving. "
        "Reduce harsh facial shadowing and line emphasis across the whole face, especially "
        "in the lower face and forehead. Do not narrow the lips, deepen smile lines, "
        "nasolabial folds, or forehead/glabella lines, exaggerate skin texture, broaden "
        "the lower face, or change facial proportions.",
    ),
    (
        "Preserve natural lip fullness and a softly contoured jawline. Keep smile lines and "
        "nasolabial folds soft, simplified, and flattering. Reduce harsh lower-face shadowing "
        "and crease emphasis. Do not narrow the lips, deepen smile lines or nasolabial folds, "
        "exaggerate skin texture, broaden the lower face, or change facial proportions.",
        "Preserve natural lip fullness and a softly contoured jawline. Keep smile lines, "
        "nasolabial folds, forehead lines, glabellar 11s, and under-eye creases soft, "
        "simplified, and flattering. Favor smooth painted skin planes over crease carving. "
        "Reduce harsh facial shadowing and line emphasis across the whole face, especially "
        "in the lower face and forehead. Do not narrow the lips, deepen smile lines, "
        "nasolabial folds, or forehead/glabella lines, exaggerate skin texture, broaden "
        "the lower face, or change facial proportions.",
    ),
]

FINAL_SNIPPET = OLD_SNIPPETS[-1][1]


def update_caption(path: Path) -> bool:
    text = path.read_text()
    original = text
    for old, new in OLD_SNIPPETS:
        if old in text:
            text = text.replace(old, new)
    if FINAL_SNIPPET not in text:
        text = text.rstrip() + " " + FINAL_SNIPPET + "\n"
    if text != original:
        path.write_text(text)
        return True
    return False


def main() -> None:
    updated = 0
    scanned = 0
    for root in DATASET_ROOTS:
        for caption in root.rglob("styled/*.txt"):
            scanned += 1
            if update_caption(caption):
                updated += 1
    print({"scanned": scanned, "updated": updated})


if __name__ == "__main__":
    main()
