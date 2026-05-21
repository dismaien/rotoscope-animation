#!/bin/zsh
set -euo pipefail

cd /Users/leona/Documents/Playground/painterly-rotoscope-animation
export PYTHONUNBUFFERED=1
export HF_HUB_DISABLE_XET=1
export HF_HUB_DOWNLOAD_TIMEOUT=120
export HF_HUB_ETAG_TIMEOUT=30
LOG_DIR="$PWD/runs/logs"
mkdir -p "$LOG_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Waiting for the full 4B chain to finish..." | tee -a "$LOG_DIR/continue_after_4b_training.log"
while pgrep -f '/Users/leona/Documents/Playground/painterly-rotoscope-animation/tools/continue_after_4b_download.sh|/Users/leona/Documents/Playground/painterly-rotoscope-animation/tools/download_flux2_klein4b_bundle.sh|flux2-klein-4b-paired-lora-mps-smoke.yaml|flux2-klein-4b-paired-lora-mps-pilot.yaml' >/dev/null; do
  sleep 30
done

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Preparing 9B bundle" | tee -a "$LOG_DIR/continue_after_4b_training.log"
"$PWD/tools/prepare_flux2_klein9b_bundle.sh" 2>&1 | tee "$LOG_DIR/flux2_klein9b_bundle_prepare.log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running 9B smoke" | tee -a "$LOG_DIR/continue_after_4b_training.log"
source .venv-ai-toolkit/bin/activate
python external/ai-toolkit/run.py /Users/leona/Documents/Playground/painterly-rotoscope-animation/configs/ai-toolkit/flux2-klein-9b-paired-lora-mps-smoke.yaml 2>&1 | tee "$LOG_DIR/flux2_klein9b_smoke_autorun.log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running 9B pilot" | tee -a "$LOG_DIR/continue_after_4b_training.log"
python external/ai-toolkit/run.py /Users/leona/Documents/Playground/painterly-rotoscope-animation/configs/ai-toolkit/flux2-klein-9b-paired-lora-mps-pilot.yaml 2>&1 | tee "$LOG_DIR/flux2_klein9b_pilot_autorun.log"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running 9B full v0" | tee -a "$LOG_DIR/continue_after_4b_training.log"
python external/ai-toolkit/run.py /Users/leona/Documents/Playground/painterly-rotoscope-animation/configs/ai-toolkit/flux2-klein-9b-paired-lora-mps-v0.yaml 2>&1 | tee "$LOG_DIR/flux2_klein9b_v0_autorun.log"
