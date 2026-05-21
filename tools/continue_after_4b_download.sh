#!/bin/zsh
set -euo pipefail
cd /Users/leona/Documents/Playground/painterly-rotoscope-animation
export PYTHONUNBUFFERED=1
export HF_HUB_DISABLE_XET=1
export HF_HUB_DOWNLOAD_TIMEOUT=120
export HF_HUB_ETAG_TIMEOUT=30
LOG_DIR="$PWD/runs/logs"
mkdir -p "$LOG_DIR"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Waiting for active 4B bundle download to finish..." | tee -a "$LOG_DIR/continue_after_4b_download.log"
while pgrep -f '/Users/leona/Documents/Playground/painterly-rotoscope-animation/tools/download_flux2_klein4b_bundle.sh' >/dev/null; do
  sleep 30
done
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running 4B smoke" | tee -a "$LOG_DIR/continue_after_4b_download.log"
source .venv-ai-toolkit/bin/activate
python external/ai-toolkit/run.py /Users/leona/Documents/Playground/painterly-rotoscope-animation/configs/ai-toolkit/flux2-klein-4b-paired-lora-mps-smoke.yaml 2>&1 | tee "$LOG_DIR/flux2_klein4b_smoke_autorun.log"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running 4B pilot" | tee -a "$LOG_DIR/continue_after_4b_download.log"
python external/ai-toolkit/run.py /Users/leona/Documents/Playground/painterly-rotoscope-animation/configs/ai-toolkit/flux2-klein-4b-paired-lora-mps-pilot.yaml 2>&1 | tee "$LOG_DIR/flux2_klein4b_pilot_autorun.log"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running 4B full v0" | tee -a "$LOG_DIR/continue_after_4b_download.log"
python external/ai-toolkit/run.py /Users/leona/Documents/Playground/painterly-rotoscope-animation/configs/ai-toolkit/flux2-klein-4b-paired-lora-mps-v0.yaml 2>&1 | tee "$LOG_DIR/flux2_klein4b_v0_autorun.log"
