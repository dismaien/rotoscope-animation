# FLUX.2 klein 4B Paired LoRA Build Log

This document records how we built the local painterly rotoscope LoRA for the interview footage, what changed over time, and how to continue the training safely.

## Goal

Train a local paired-edit LoRA that learns the `source frame -> Nano Banana styled frame` transformation for the interview footage, with priorities:

- painterly beauty
- strong likeness preservation
- flattering / slightly ageless face treatment
- local reuse without paying per frame

## Current Model Path

- Base model: `FLUX.2 klein 4B`
- Training type: paired LoRA
- Device: Apple `MPS`
- Precision: `bf16`
- Quantization: `uint4`
- Training objective: source/control frame plus caption -> styled target frame

## Datasets

### Pilot dataset

Used to prove the local training path and shape early face/style behavior.

- Train pairs: `128`
- Path:
  - `/Users/leona/Documents/Playground/painterly-rotoscope-animation/runs/datasets/local_pilot_subset_v1/train/styled`
  - `/Users/leona/Documents/Playground/painterly-rotoscope-animation/runs/datasets/local_pilot_subset_v1/train/control`

### Full curated dataset

Used for the real run after the pilot proved stable.

- Train pairs: `684`
- Validation pairs: `86`
- Holdout pairs: `147`
- Path:
  - `/Users/leona/Documents/Playground/painterly-rotoscope-animation/runs/datasets/flux2_klein_v0_plus_dense_three/train/styled`
  - `/Users/leona/Documents/Playground/painterly-rotoscope-animation/runs/datasets/flux2_klein_v0_plus_dense_three/train/control`

## Key Training Decisions

### 1. Paired training, not style-only SDXL LoRA

We abandoned the earlier `SDXL` style-only LoRA approach because it learned a vague painterly bias but not the actual frame-to-frame transformation we need.

### 2. Face-softening / beautifying caption bias

We reinforced the captions to encourage:

- soft painted skin planes
- preserved lip fullness
- softened nasolabial folds
- softened forehead lines and glabellar `11s`
- less harsh shadow carving
- less bulky lower-face treatment
- more exact / lightly chiseled facial structure

The reusable tool for that is:

- `/Users/leona/Documents/Playground/painterly-rotoscope-animation/tools/soften_face_captions.py`

### 3. Low-impact local execution

To keep the machine usable during training, runs are launched with:

- `OMP_NUM_THREADS=7`
- `MKL_NUM_THREADS=7`
- `OPENBLAS_NUM_THREADS=7`
- `VECLIB_MAXIMUM_THREADS=7`
- `NUMEXPR_NUM_THREADS=7`
- `taskpolicy -b`
- `nice -n 20`
- `caffeinate -dimsu`

### 4. Detached launcher

We stopped relying on an attached interactive session after several interruptions. Long runs now launch in a detached `screen` session so they survive tool/session cleanup.

## Important Fixes We Made

### Mac / MPS stability fixes

We got the local path working by fixing several blockers:

- dataloader multiprocessing issue on macOS
- CPU/MPS tensor mismatch in the control-conditioning path
- unstable float16 path; switched training to `bf16`
- training preview sampling was misleading and ugly, so we disabled in-training sampling for the pilot/full runs

### Checkpoint retention

We increased checkpoint retention so progress is not silently pruned away:

- pilot saves every `10` steps
- full run saves every `10` steps
- retention increased substantially vs the early runs

## Pilot Run

Config:

- `/Users/leona/Documents/Playground/painterly-rotoscope-animation/configs/ai-toolkit/flux2-klein-4b-paired-lora-mps-pilot.yaml`

Training folder:

- `/Users/leona/Documents/Playground/painterly-rotoscope-animation/runs/flux2_klein4b_paired_mps_pilot_bf16_nosample`

Latest durable pilot checkpoint used for warm start:

- `/Users/leona/Documents/Playground/painterly-rotoscope-animation/runs/flux2_klein4b_paired_mps_pilot_bf16_nosample/wakinglife_flux2_klein4b_paired_mps_pilot_bf16_nosample/wakinglife_flux2_klein4b_paired_mps_pilot_bf16_nosample_000000250.safetensors`

The pilot was useful for:

- proving local training is feasible on this Mac
- shaping the face-preservation / beautification direction
- generating a non-random LoRA initialization for the full dataset run

It was *not* intended to be the final dataset regime, because it only used `128` pairs.

## Full Run

Base config:

- `/Users/leona/Documents/Playground/painterly-rotoscope-animation/configs/ai-toolkit/flux2-klein-4b-paired-lora-mps-v0.yaml`

Generated run config for the live full-data job:

- `/Users/leona/Documents/Playground/painterly-rotoscope-animation/runs/generated_configs/flux2_klein4b_full_from_pilot_20260614_235402.yaml`

Detached launcher:

- `/Users/leona/Documents/Playground/painterly-rotoscope-animation/tools/start_flux2_klein4b_full_from_pilot_detached.sh`

Training folder:

- `/Users/leona/Documents/Playground/painterly-rotoscope-animation/runs/flux2_klein4b_paired_mps_v0_nosample`

Live log:

- `/Users/leona/Documents/Playground/painterly-rotoscope-animation/runs/logs/flux2_klein4b_full_20260614_235402.log`

### Full-run settings

- Train pairs: `684`
- Steps: `500`
- Save every: `10`
- Warm start: pilot step-250 LoRA
- Fresh optimizer state for the full run

This means the full run gets the benefit of what the pilot already learned, without being trapped in the tiny pilot dataset regime.

## Checkpoint Gallery / Evaluation Artifacts

Useful evaluation outputs created so far:

- Checkpoint gallery:
  - `/Users/leona/Documents/Playground/painterly-rotoscope-animation/analysis/checkpoint_gallery_v1/checkpoint_gallery.jpg`
- Step 250 quick preview:
  - `/Users/leona/Documents/Playground/painterly-rotoscope-animation/analysis/current_step250_preview/raw/step_250/1781472843051_0.png`

These previews are useful for direction, but they are lower-quality eval renders than the eventual higher-quality test renders we should use for aesthetic judgment.

## How To Continue

### Check whether the full run is still alive

```bash
ps -Ao pid,etime,pcpu,command | grep 'flux2_klein4b_full_from_pilot' | grep -v grep
tail -n 80 /Users/leona/Documents/Playground/painterly-rotoscope-animation/runs/logs/flux2_klein4b_full_20260614_235402.log
screen -ls
```

### Relaunch the full run if needed

```bash
/Users/leona/Documents/Playground/painterly-rotoscope-animation/tools/start_flux2_klein4b_full_from_pilot_detached.sh
```

### Pilot relaunch, if ever needed

```bash
/Users/leona/Documents/Playground/painterly-rotoscope-animation/tools/resume_flux2_klein4b_pilot.sh
```

## What We Expect Next

The full run should be judged on:

- painterly richness vs cartooniness
- facial exactness
- whether the lower face stays less bulky
- whether the model preserves beauty while staying true to the subject

If the full `684`-pair run still feels too cartoony after a meaningful number of steps, the next likely levers are:

- higher-quality eval renders before overreacting
- more training steps
- possibly higher rank (`32`)
- possibly multi-resolution training
- targeted face refinement continuation
