**Local AI Toolkit Patches**

The current local `FLUX.2 klein` training/eval path depends on patches inside the nested clone at:

- `/Users/leona/Documents/Playground/painterly-rotoscope-animation/external/ai-toolkit`

Those files are **not part of the top-level repo history**, because `external/` is gitignored and the toolkit is its own git repo. The working local setup currently depends on edits in these files:

- `extensions_built_in/diffusion_models/flux2/flux2_klein_model.py`
- `extensions_built_in/diffusion_models/flux2/flux2_model.py`
- `extensions_built_in/diffusion_models/flux2/src/pipeline.py`
- `extensions_built_in/diffusion_models/flux2/src/sampling.py`
- `jobs/process/GenerateProcess.py`
- `toolkit/assistant_lora.py`
- `toolkit/data_loader.py`
- `toolkit/models/base_model.py`

What those patches are doing, at a high level:

- fix Mac/MPS training and dataloader issues
- fix FLUX2 control-image device handling
- allow assistant LoRA loading for the FLUX2 checkpoint format
- preserve `--ctrl_img` during generation so evaluation actually conditions on the source frame
- fix parts of the local `klein` load/eval path that were blocking checkpoint-based inference

If we want these changes versioned remotely in the future, the clean options are:

- upstream them into the nested `ai-toolkit` clone and point this repo at that commit, or
- vendor a fork/submodule intentionally instead of relying on local ignored edits
