#!/bin/zsh
set -euo pipefail

ROOT="/Users/leona/Documents/Playground/painterly-rotoscope-animation"
LOG_DIR="$ROOT/runs/logs"
mkdir -p "$LOG_DIR"

chmod +x \
  "$ROOT/tools/download_flux2_klein4b_bundle.sh" \
  "$ROOT/tools/download_flux2_klein9b_bundle.sh" \
  "$ROOT/tools/run_flux2_klein4b_local_chain.sh" \
  "$ROOT/tools/run_flux2_klein9b_local_chain.sh"

echo "== Starting overnight local training chain =="

if ! "$ROOT/tools/run_flux2_klein4b_local_chain.sh" | tee "$LOG_DIR/overnight_4b_chain.log"; then
  echo "4B chain failed; continuing to 9B bundle/training attempt" | tee -a "$LOG_DIR/overnight_status.log"
fi

if ! "$ROOT/tools/run_flux2_klein9b_local_chain.sh" | tee "$LOG_DIR/overnight_9b_chain.log"; then
  echo "9B chain failed" | tee -a "$LOG_DIR/overnight_status.log"
fi

echo "== Overnight local training chain finished ==" | tee -a "$LOG_DIR/overnight_status.log"
