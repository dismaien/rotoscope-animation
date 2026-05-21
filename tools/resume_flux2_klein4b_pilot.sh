#!/bin/zsh
set -euo pipefail

ROOT="/Users/leona/Documents/Playground/painterly-rotoscope-animation"
LOG_DIR="$ROOT/runs/logs"
mkdir -p "$LOG_DIR"

STAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/flux2_klein4b_pilot_resume_${STAMP}.log"
LATEST_FILE="$LOG_DIR/flux2_klein4b_pilot_resume.latest"

printf '%s\n' "$LOG_FILE" > "$LATEST_FILE"
exec >> "$LOG_FILE" 2>&1

echo "== $(date '+%Y-%m-%d %H:%M:%S') Starting FLUX.2 klein 4B pilot resume =="
echo "Root: $ROOT"
echo "Log:  $LOG_FILE"

export PYTHONUNBUFFERED=1
export HF_HUB_DISABLE_XET=1
export HF_HUB_DOWNLOAD_TIMEOUT=120
export HF_HUB_ETAG_TIMEOUT=30
export OMP_NUM_THREADS=7
export MKL_NUM_THREADS=7
export OPENBLAS_NUM_THREADS=7
export VECLIB_MAXIMUM_THREADS=7
export NUMEXPR_NUM_THREADS=7

cd "$ROOT/external/ai-toolkit"
source "$ROOT/.venv-ai-toolkit/bin/activate"

echo "Config: $ROOT/configs/ai-toolkit/flux2-klein-4b-paired-lora-mps-pilot.yaml"
echo "Latest checkpoint (if any) will be auto-detected from the training folder."

caffeinate -dimsu taskpolicy -b nice -n 20 \
  python -u run.py "$ROOT/configs/ai-toolkit/flux2-klein-4b-paired-lora-mps-pilot.yaml"

echo "== $(date '+%Y-%m-%d %H:%M:%S') FLUX.2 klein 4B pilot resume finished =="
