#!/bin/zsh
set -euo pipefail

ROOT="/Users/leona/Documents/Playground/painterly-rotoscope-animation"
LOG_DIR="$ROOT/runs/logs"
RUN_DIR="$ROOT/runs/flux2_klein4b_paired_mps_pilot_bf16_nosample/wakinglife_flux2_klein4b_paired_mps_pilot_bf16_nosample"
PID_FILE="$LOG_DIR/flux2_klein4b_pilot_resume.pid"
LATEST_FILE="$LOG_DIR/flux2_klein4b_pilot_resume.latest"
STAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/flux2_klein4b_pilot_resume_${STAMP}.log"

mkdir -p "$LOG_DIR"

if [[ -f "$PID_FILE" ]]; then
  existing_pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [[ -n "${existing_pid}" ]] && kill -0 "${existing_pid}" 2>/dev/null; then
    echo "Trainer already running with PID ${existing_pid}"
    exit 0
  fi
fi

printf '%s\n' "$LOG_FILE" > "$LATEST_FILE"

cat > "$LOG_FILE" <<EOF
== $(date '+%Y-%m-%d %H:%M:%S') Starting FLUX.2 klein 4B pilot resume (detached) ==
Root: $ROOT
Log:  $LOG_FILE
Config: $ROOT/configs/ai-toolkit/flux2-klein-4b-paired-lora-mps-pilot.yaml
Latest checkpoint (if any) will be auto-detected from the training folder.
EOF

nohup /bin/zsh -lc "
  export PYTHONUNBUFFERED=1
  export HF_HUB_DISABLE_XET=1
  export HF_HUB_DOWNLOAD_TIMEOUT=120
  export HF_HUB_ETAG_TIMEOUT=30
  export OMP_NUM_THREADS=7
  export MKL_NUM_THREADS=7
  export OPENBLAS_NUM_THREADS=7
  export VECLIB_MAXIMUM_THREADS=7
  export NUMEXPR_NUM_THREADS=7
  cd '$ROOT/external/ai-toolkit'
  source '$ROOT/.venv-ai-toolkit/bin/activate'
  exec caffeinate -dimsu taskpolicy -b nice -n 20 \
    python -u run.py '$ROOT/configs/ai-toolkit/flux2-klein-4b-paired-lora-mps-pilot.yaml'
" >> "$LOG_FILE" 2>&1 < /dev/null &

trainer_pid=$!
echo "$trainer_pid" > "$PID_FILE"
echo "Started detached trainer PID $trainer_pid"
