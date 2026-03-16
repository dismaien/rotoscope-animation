# Kontext vs klein Benchmark

This is the next benchmark I would actually run after the overnight work.

## Goal

Find the best first trainable editing base for this exact interview:

- preserve the same face
- preserve mouth shapes and expression
- repaint the frame with stronger painterly rotoscope treatment
- stay close enough to the source that anchor propagation still works

## Updated Recommendation

Benchmark in this order:

1. `FLUX.1 Kontext [dev]` paired LoRA
2. `FLUX.2 klein 9B` paired LoRA
3. `Qwen-Image-Edit-2509` paired LoRA only if one of these is true:
   - Kontext wins on fidelity but not beauty
   - klein wins on painterly quality but not identity
   - we want the strongest reusable open-license edit branch

This ranking is an inference from the current evidence, not a confirmed leaderboard result on this dataset.

## Why Kontext Moved Up

What changed:

- the task is now clearly an editing task, not a pure style task
- we have a much larger paired dataset than we had at the start
- the local trainer already supports paired Kontext LoRA training with `control_path`

Why that matters:

- Kontext is explicitly built around image editing
- Black Forest Labs positions it around identity-preserving iterative edits
- the local trainer path is closer to the problem we actually have: source frame in, painted restyle out

Main tradeoff:

- Kontext is fixed at about `1MP`, so it may lose the final-beauty shootout if resolution ceiling matters more than edit faithfulness

## Candidate Scorecard

### `FLUX.1 Kontext [dev]`

Best for:

- exact frame repainting
- preserving facial geometry
- preserving expression and scene layout

Risks:

- lower output ceiling than the `FLUX.2` family
- non-commercial license

Pilot config:

- `/Users/leona/Documents/Playground/painterly-rotoscope-animation/configs/ai-toolkit/flux-kontext-dev-paired-lora-pilot.yaml`

### `FLUX.2 klein 9B`

Best for:

- stronger painterly beauty ceiling
- more room for later reusable house-model work
- higher output resolution ceiling

Risks:

- may still behave more like a broad generator than a precise editor
- non-commercial license on `9B`

Pilot config:

- `/Users/leona/Documents/Playground/painterly-rotoscope-animation/configs/ai-toolkit/flux2-klein-9b-paired-lora.yaml`

### `Qwen-Image-Edit-2509`

Best for:

- open-license future branch
- precise editing base with a strong recent release cadence
- likely best long-term research branch if we want a reusable in-house edit stack

Risks:

- more moving parts than the FLUX path right now
- less ready in this repo than the BFL path, even though ai-toolkit supports it

Pilot config:

- `/Users/leona/Documents/Playground/painterly-rotoscope-animation/configs/ai-toolkit/qwen-image-edit-2509-paired-lora-pilot.yaml`

## Shared Dataset

Use the same narrowed paired dataset for the first pilot comparison:

- prepared root:
  `/Users/leona/Documents/Playground/painterly-rotoscope-animation/runs/datasets/flux2_klein_v0_plus_dense_three`
- counts:
  `684 train / 86 val / 147 holdout`

Why keep the dataset identical:

- model differences become easier to judge
- we avoid moving-target confusion from changing both the data and the base model at the same time

## Pilot Rules

Keep the first benchmark intentionally small:

- `1250` steps each
- `batch_size: 1`
- same three sample frames
- same caption template
- save and sample every `250` steps

The point is not to finish training. The point is to answer:

- which base learns the transformation fastest
- which base best preserves the mouth and jaw
- which base produces the most beautiful painted contour treatment

## Evaluation Panel

Judge every checkpoint on:

1. likeness
2. lip fullness and mouth-shape fidelity
3. eye/gaze fidelity
4. overall painterly beauty
5. contour line quality
6. composition preservation
7. usefulness as a future anchor frame

If one model is clearly better by checkpoint `500-750`, stop wasting time on the weaker branch.

## What Would Change My Mind

I would demote Kontext again if:

- it preserves identity well but looks too airbrushed or too bland
- the `1MP` ceiling clearly hurts the painterly final look
- klein catches up on fidelity while looking more like the Nano Banana reference style

I would promote Qwen earlier if:

- both FLUX pilots still feel too generic
- the edit behavior we want still looks underfit after paired training
- we decide licensing and future in-house reuse matter more than staying inside the BFL family

## Current Recommendation

If we are choosing the next training attempt from scratch today:

1. run the `Kontext` pilot first
2. run the `klein 9B` pilot second
3. keep `Qwen-Image-Edit-2509` as the stronger `v1` branch unless the first two disappoint

## Sources

- BFL model overview: <https://help.bfl.ai/articles/9364115800-flux-models-overview>
- BFL Kontext overview: <https://docs.bfl.ai/kontext/kontext_overview>
- BFL Kontext image editing docs: <https://docs.bfl.ai/kontext/kontext_image_editing>
- Kontext resolution note: <https://help.bfl.ai/articles/9589283133-why-does-flux-kontext-can-alter-output-dimensions>
- FLUX.1 Kontext model card: <https://huggingface.co/black-forest-labs/FLUX.1-Kontext-dev>
- Qwen-Image official repo: <https://github.com/QwenLM/Qwen-Image>
