# Research Update - Better Paths For Painterly Rotoscope v0

This note captures the higher-signal research findings after the overnight render and dataset work.

## Biggest Takeaway

The strongest updated direction is:

- treat `v0` as an **editing** problem first
- treat video as **anchor generation + propagation** second
- treat a reusable house model as a **content-preserving stylization edit model**, not a plain text-to-image style LoRA

That is a meaningful shift.

My inference from the sources and local tooling:

- `FLUX.2 klein 9B` is still a serious candidate because it offers high resolution, multi-reference capability, and local fine-tuning support
- but `FLUX.1 Kontext` now looks like the **more natural first training target** for this exact interview, because it is explicitly built for image editing and the local training stack already has a paired `control_path` example for it

## Why This Changed

Two things matter more now than they did at the start:

1. We are not training a general "rotoscope vibe" model.
2. We now have a large paired dataset of source frame -> styled frame edits.

That means the question is no longer:

- "what open model makes the coolest pictures?"

It is:

- "what model family best learns faithful frame repainting while preserving facial structure and expression?"

That favors edit-native bases.

## Updated Model Ranking

### 1. `FLUX.1 Kontext [dev]` paired LoRA

Why it just moved up:

- BFL positions Kontext as a unified image generation and editing model.
- BFL's own prompting docs emphasize character consistency and identity preservation across iterative edits.
- The local `ai-toolkit` stack already includes an explicit `train_lora_flux_kontext_24gb.yaml` example using `control_path` for paired datasets.
- The local code path for Kontext hard-requires a control image at generation time, which matches our real problem better than a style-only setup.

Why it is not an automatic winner:

- Official BFL docs say Kontext is fixed at about `1MP`, which is lower than the `FLUX.2` family ceiling.
- License is non-commercial unless separately licensed.
- Inference and training are still heavier than the cheap options.

Best use:

- `v0` benchmark for highest likelihood of "same frame, same person, better painted rendering"

### 2. `FLUX.2 klein 9B` paired LoRA

Why it still matters:

- BFL positions `FLUX.2 [klein]` as a unified generation/editing architecture with up to `4MP` resolution and up to `4` references.
- `FLUX.2 klein base 9B` remains BFL's strongest trainable local-ish base in the `klein` family.
- The local `ai-toolkit` code path for `flux2` also supports control images, so paired supervision is real here too.

Why it drops to second:

- The family is broader and more flexible, but less obviously aligned to "faithful repaint of this exact input frame" than Kontext.
- For this project, edit fidelity is more important than model generality in run 1.

Best use:

- `v0.5` or parallel benchmark, especially if Kontext wins on likeness but loses on final painterly beauty or resolution

### 3. `Qwen-Image-Edit-2509 / 2511` and the Qwen-style stylization branch

Why this became more interesting:

- Qwen's official repo positions Qwen-Image-Edit as a precise editing model, with the later `2509` and `2511` releases improving consistency.
- Qwen explicitly recommends `2509` over the original edit release for better consistency, and `2511` for improved consistency again.
- The repo notes that `DiffSynth-Studio` supports Qwen-Image inference plus LoRA / full training.
- The local `ai-toolkit` checkout already includes `Qwen-Image-Edit`, `Qwen-Image-Edit-2509`, and `Qwen-Image-Edit-2511` training examples, so this is less blocked than it first looked.
- New papers like `QwenStyle` and `TeleStyle` show that content-preserving style transfer on top of Qwen-Image-Edit is now an active, strong research direction.

Why it is not the immediate first move:

- This route is newer and more moving-target than the BFL path.
- The overnight repo and configs are already much closer to a `FLUX` training run than a Qwen fine-tune run.
- I do not want to bounce us to a whole new training stack before testing the cleaner Kontext path.

Best use:

- strongest medium-term research branch for a reusable house stylization model

## What This Means For v0

If the goal is the best chance of a good first trained model on this interview, I would now benchmark in this order:

1. `FLUX.1 Kontext [dev]` paired LoRA
2. `FLUX.2 klein 9B` paired LoRA
3. only after that, consider a Qwen-Image-Edit stylization branch

This is an inference from the combined evidence, not a guaranteed outcome.

## Video Strategy Update

The overnight motion tests reinforced a practical split:

- dense anchor generation works
- simple interpolation on dense anchors is worth checking
- pure `1 fps -> 12 fps` interpolation from the styled video is still a rough fallback, not a final answer
- `EbSynth` remains conceptually right, but in practice it is slow and brittle in the current local setup

### Immediate Production Path

For beautiful proof-of-concept output:

1. pick `2-3` hero clips
2. generate dense anchors only for those clips
3. compare:
   - `4 fps` anchor video as-is
   - `4 fps -> 12 fps` hold/blend/mci upsample
   - `EbSynth` or source-guided propagation where it actually completes
4. keep the best result per clip, not one universal method

### Better Long-Term Video Research

Recent papers point to stronger training-free stylization frameworks than raw framewise editing:

- `UniVST` proposes point-matching mask propagation, AdaIN-guided stylization, and sliding-window smoothing with optical flow
- `FreeViS` proposes multi-reference training-free video stylization with flow-based motion cues and high-frequency compensation

These do **not** immediately replace the current pipeline, but they are the right reference class for "better than EbSynth" research.

## Concrete Next Experiments

### A. Fastest high-value model benchmark

Run two pilot trainings on the same narrowed paired set:

1. `FLUX.1 Kontext [dev]` paired LoRA
2. `FLUX.2 klein 9B` paired LoRA

Keep them intentionally small:

- `512/768` training resolutions
- `1000-1500` steps
- same train/val/holdout split
- same captions
- same sample panel

Judge only on:

- likeness
- mouth/expression fidelity
- painterly beauty
- structural faithfulness

Do not burn time on long runs before this comparison.

### B. Hero-clip production benchmark

For the three dense hero clips already prepared:

- compare `hold_vs_dense_4fps`
- compare `hold_vs_mci_12fps`
- choose one clip to push through a cleaner source-guided propagation attempt

This will tell us whether the near-term film path is:

- more dense anchors
- better propagation
- or both

### C. House-model research branch

If `Kontext` or `klein` is promising but still not beautiful enough, the next serious research move is:

- test `Qwen-Image-Edit` as the base editing model
- or test a `QwenStyle / TeleStyle` style-transfer branch

That is a stronger `v1` direction than another SDXL-era LoRA.

## Recommendation Summary

If I were optimizing for your actual hierarchy right now, I would do this:

### Best next training benchmark

`FLUX.1 Kontext [dev]` paired LoRA

### Best fallback / parallel benchmark

`FLUX.2 klein 9B` paired LoRA

### Best future reusable stylization research direction

`Qwen-Image-Edit` based stylization, likely informed by `QwenStyle` / `TeleStyle`

### Best near-term film path

keep using dense high-quality anchors on hero clips and propagate from there, rather than waiting for one perfect video model

## Sources

- BFL FLUX model overview: <https://help.bfl.ai/articles/9364115800-flux-models-overview>
- BFL Kontext overview: <https://docs.bfl.ai/kontext/kontext_overview>
- BFL Kontext image editing: <https://docs.bfl.ai/kontext/kontext_image_editing>
- BFL Kontext prompting guide: <https://docs.bfl.ai/guides/prompting_guide_kontext_i2i>
- BFL FLUX.2 klein training example: <https://docs.bfl.ai/flux_2/flux2_klein_training_example>
- FLUX.1 Kontext model card: <https://huggingface.co/black-forest-labs/FLUX.1-Kontext-dev>
- FLUX.1 Kontext paper: <https://arxiv.org/abs/2506.15742>
- Qwen-Image official repo: <https://github.com/QwenLM/Qwen-Image>
- DiffSynth-Studio official repo: <https://github.com/modelscope/DiffSynth-Studio>
- UniVST paper: <https://arxiv.org/abs/2410.20084>
- FreeViS paper: <https://arxiv.org/abs/2510.01686>
- QwenStyle paper: <https://arxiv.org/abs/2601.06202>
- TeleStyle paper: <https://arxiv.org/abs/2601.20175>
