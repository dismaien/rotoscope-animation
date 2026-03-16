# FLUX.2 klein v0 Runbook

This is the concrete path from the current paired CSV to the first serious `FLUX.2 klein 9B` LoRA attempt.

## Current State

- Paired manifest: `manifests/nano_pairs_expanded.csv`
- Prepared ai-toolkit dataset root: `/Users/leona/Documents/Playground/painterly-rotoscope-animation/runs/datasets/flux2_klein_v0`
- ai-toolkit config: `configs/ai-toolkit/flux2-klein-9b-paired-lora.yaml`
- Current prepared counts:
  - `train`: `586`
  - `val`: `80`
  - `holdout`: `125`

## 1. Rebuild The Prepared Dataset

Run this if the manifest changes or we narrow the pairs further:

```bash
python3 tools/prepare_ai_toolkit_paired_dataset.py \
  --manifest manifests/nano_pairs_expanded.csv \
  --prompt-file configs/prompts/paired_edit_prompt_v0.txt \
  --relative-root "/Users/leona/Downloads/waking life interview" \
  --output-root runs/datasets/flux2_klein_v0
```

What it does:
- assigns deterministic splits when `split` is blank
- creates `train`, `val`, and `holdout` folders
- symlinks styled targets and source control images
- writes caption `.txt` files for the styled images

## 2. Sanity Check The Dataset

Make sure the folder counts still match the summary:

```bash
python3 - <<'PY'
from pathlib import Path
root = Path("runs/datasets/flux2_klein_v0")
for split in ["train", "val", "holdout"]:
    styled = len(list((root / split / "styled").glob("*.png")))
    control = len(list((root / split / "control").glob("*.png")))
    print(split, styled, control)
PY
```

## 3. Make Sure The Model Access Is Ready

Before training:
- Hugging Face access for `black-forest-labs/FLUX.2-klein-base-9B` must be accepted
- the machine must be logged in to Hugging Face
- the ai-toolkit dependency install must be complete

## 4. Launch The Training Run

From the ai-toolkit checkout:

```bash
python run.py /Users/leona/Documents/Playground/painterly-rotoscope-animation/configs/ai-toolkit/flux2-klein-9b-paired-lora.yaml
```

## 5. Evaluate The Samples

During training:
- inspect the samples saved every `250` steps
- compare against the `holdout` control frames
- prioritize likeness, lip fullness, mouth-shape accuracy, and painterly contour quality

## 6. Current Blocker

The code/config side is ready, but the first cloud run is still blocked by project setup:

- the visible Google project currently has `Compute Engine API` disabled
- it also has `Service Usage API` disabled

Until those are enabled, the real cloud GPU run cannot be launched from the current credentials.
