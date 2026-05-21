#!/bin/zsh
set -euo pipefail

ROOT="/Users/leona/Documents/Playground/painterly-rotoscope-animation"
LOG_DIR="$ROOT/runs/logs"
mkdir -p "$LOG_DIR"

export PYTHONUNBUFFERED=1
export HF_HUB_DISABLE_XET=1
export HF_HUB_DOWNLOAD_TIMEOUT=120
export HF_HUB_ETAG_TIMEOUT=30

echo "== Downloading local FLUX.2 klein 9B bundle =="
"$ROOT/tools/download_flux2_klein9b_bundle.sh" | tee "$LOG_DIR/flux2_klein9b_bundle.log"

echo "== Running FLUX.2 klein 9B smoke =="
(
  cd "$ROOT/external/ai-toolkit"
  source "$ROOT/.venv-ai-toolkit/bin/activate"
  python -u run.py "$ROOT/configs/ai-toolkit/flux2-klein-9b-paired-lora-mps-smoke.yaml"
) | tee "$LOG_DIR/flux2_klein9b_smoke.log"

echo "== Running FLUX.2 klein 9B pilot =="
(
  cd "$ROOT/external/ai-toolkit"
  source "$ROOT/.venv-ai-toolkit/bin/activate"
  python -u run.py "$ROOT/configs/ai-toolkit/flux2-klein-9b-paired-lora-mps-pilot.yaml"
) | tee "$LOG_DIR/flux2_klein9b_pilot.log"

echo "== FLUX.2 klein 9B local chain finished =="
