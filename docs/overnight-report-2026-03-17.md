# Overnight Report - 2026-03-17

This report captures the overnight work completed toward a painterly rotoscope `v0`.

## What Finished

- Full local transcript of `/Users/leona/Downloads/SUN_7901.MP4` with JSON, TXT, and SRT outputs in `/Users/leona/Documents/Playground/painterly-rotoscope-animation/analysis/transcripts/full_interview_mlx/`
- Editorial chapter map and hero clip picks in `/Users/leona/Documents/Playground/painterly-rotoscope-animation/docs/interview-content-map.md`
- Source and styled hero clip extracts in `/Users/leona/Documents/Playground/painterly-rotoscope-animation/analysis/hero_clips/`
- Three local motion baselines for a `30s` segment in `/Users/leona/Documents/Playground/painterly-rotoscope-animation/analysis/motion_tests/segment_0060_0090/`
  - `hold_12fps.mp4`
  - `blend_12fps.mp4`
  - `mci_12fps.mp4`
  - `hold_blend_mci_triptych.mp4`
- Three local motion baselines for a `5s` hero segment in `/Users/leona/Documents/Playground/painterly-rotoscope-animation/analysis/motion_tests/segment_0166_0171/`
  - `hold_12fps.mp4`
  - `blend_12fps.mp4`
  - `mci_12fps.mp4`
  - `hold_blend_mci_triptych.mp4`
- Three dense Gemini `4 fps` hero-clip tests, each with generated frames, preview video, and hold-vs-dense comparison:
  - `/Users/leona/Documents/Playground/painterly-rotoscope-animation/analysis/gemini_dense_tests/clip_0166_0181_4fps/`
  - `/Users/leona/Documents/Playground/painterly-rotoscope-animation/analysis/gemini_dense_tests/clip_0606_0621_4fps/`
  - `/Users/leona/Documents/Playground/painterly-rotoscope-animation/analysis/gemini_dense_tests/clip_0774_0786_4fps/`
- Dense-anchor `12 fps` upsample tests for all three hero clips:
  - each clip now has `upsample_tests/hold_12fps.mp4`
  - `upsample_tests/blend_12fps.mp4`
  - `upsample_tests/mci_12fps.mp4`
  - `upsample_tests/hold_vs_mci_12fps.mp4`
- FLUX.2 klein `9B` paired-training prep assets:
  - `/Users/leona/Documents/Playground/painterly-rotoscope-animation/configs/ai-toolkit/flux2-klein-9b-paired-lora.yaml`
  - `/Users/leona/Documents/Playground/painterly-rotoscope-animation/docs/flux2-klein-v0-runbook.md`
  - `/Users/leona/Documents/Playground/painterly-rotoscope-animation/tools/prepare_ai_toolkit_paired_dataset.py`
  - `/Users/leona/Documents/Playground/painterly-rotoscope-animation/tools/check_gcp_training_readiness.sh`

## Most Important Outputs To Review First

1. `/Users/leona/Documents/Playground/painterly-rotoscope-animation/analysis/gemini_dense_tests/clip_0166_0181_4fps/comparisons/hold_vs_dense_4fps.mp4`
2. `/Users/leona/Documents/Playground/painterly-rotoscope-animation/analysis/gemini_dense_tests/clip_0606_0621_4fps/comparisons/hold_vs_dense_4fps.mp4`
3. `/Users/leona/Documents/Playground/painterly-rotoscope-animation/analysis/gemini_dense_tests/clip_0774_0786_4fps/comparisons/hold_vs_dense_4fps.mp4`
4. `/Users/leona/Documents/Playground/painterly-rotoscope-animation/analysis/gemini_dense_tests/clip_0166_0181_4fps/upsample_tests/hold_vs_mci_12fps.mp4`
5. `/Users/leona/Documents/Playground/painterly-rotoscope-animation/analysis/gemini_dense_tests/clip_0606_0621_4fps/upsample_tests/hold_vs_mci_12fps.mp4`
6. `/Users/leona/Documents/Playground/painterly-rotoscope-animation/analysis/gemini_dense_tests/clip_0774_0786_4fps/upsample_tests/hold_vs_mci_12fps.mp4`
7. `/Users/leona/Documents/Playground/painterly-rotoscope-animation/analysis/motion_tests/segment_0060_0090/hold_blend_mci_triptych.mp4`
8. `/Users/leona/Documents/Playground/painterly-rotoscope-animation/analysis/motion_tests/segment_0166_0171/hold_blend_mci_triptych.mp4`
9. `/Users/leona/Documents/Playground/painterly-rotoscope-animation/analysis/motion_tests/segment_0166_0171/hold_12fps.mp4`
10. `/Users/leona/Documents/Playground/painterly-rotoscope-animation/docs/interview-content-map.md`

## Recommended Content Targets

Best current hero clips:

- `02:46-04:26` easeful productivity
- `09:58-11:59` transmission vs communication
- `12:54-13:12` stop muting / free the energy

Strong later editorial targets that are not yet covered by current styled anchors:

- `20:38-22:07` own gravity
- `27:23-29:01` boundaries as dance

## Training State

Current paired datasets prepared so far:

- Base expanded set from the accidental batch:
  - manifest: `/Users/leona/Documents/Playground/painterly-rotoscope-animation/manifests/nano_pairs_expanded.csv`
  - prepared dataset: `/Users/leona/Documents/Playground/painterly-rotoscope-animation/runs/datasets/flux2_klein_v0`
  - counts: `586 train / 80 val / 125 holdout`
- Expanded set plus first two dense hero clips:
  - manifest: `/Users/leona/Documents/Playground/painterly-rotoscope-animation/analysis/gemini_dense_tests/nano_pairs_expanded_plus_dense_both.csv`
  - prepared dataset: `/Users/leona/Documents/Playground/painterly-rotoscope-animation/runs/datasets/flux2_klein_v0_plus_dense_both`
  - counts: `655 train / 86 val / 140 holdout`
- Expanded set plus all three dense hero clips:
  - manifest: `/Users/leona/Documents/Playground/painterly-rotoscope-animation/analysis/gemini_dense_tests/nano_pairs_expanded_plus_dense_three.csv`
  - prepared dataset: `/Users/leona/Documents/Playground/painterly-rotoscope-animation/runs/datasets/flux2_klein_v0_plus_dense_three`
  - counts: `684 train / 86 val / 147 holdout`

## Spend Summary

Approved overnight Gemini cap: `$10.00`

Confirmed call plan already executed before this report:

- Clip `0166-0181` at `4 fps`: `45` new images x `$0.067` = about `$3.015`
- Clip `0606-0621` at `4 fps`: `45` new images x `$0.067` = about `$3.015`
- One retry for a missing frame: `1` image x `$0.067` = about `$0.067`
- Clip `0774-0786` at `4 fps`: `36` new images x `$0.067` = about `$2.412`

Subtotal so far: about `$8.509`

Important:

- This is an estimate from successful output-image counts times published per-image pricing.
- It is not a billing-console confirmation.

## Blockers / Caveats

- The real cloud training run has not started yet.
- In the current shell environment, `gcloud` is not available on `PATH`, so the new readiness check cannot inspect auth/project/API status from here.
- Earlier checks in a different shell context also showed the visible project was not yet ready for GPU training because required APIs were disabled.
- A local `FLUX.2 klein 9B` training run on the Mac is not the recommended production path.
- The styled anchor folder has numbering gaps around `frame_0774` and `frame_0775`; the dense clip tooling now supports falling back to the rendered `1 fps` styled video for missing anchor frames.

## In Progress

- A resumed `EbSynth` propagation pass for the `60s-90s` motion test segment
- A short `EbSynth` propagation pass for the `166s-171s` hero segment

Status note:

- The dense hero-clip work is complete and stayed under the approved `$10` cap.
- The `EbSynth` passes are progressing locally but much more slowly than the ffmpeg baselines, so they may still be running when the morning review starts.
