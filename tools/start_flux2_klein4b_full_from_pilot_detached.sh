#!/bin/zsh
set -euo pipefail

ROOT="/Users/leona/Documents/Playground/painterly-rotoscope-animation"
LOG_DIR="$ROOT/runs/logs"
GEN_CONFIG_DIR="$ROOT/runs/generated_configs"
PILOT_RUN_DIR="$ROOT/runs/flux2_klein4b_paired_mps_pilot_bf16_nosample/wakinglife_flux2_klein4b_paired_mps_pilot_bf16_nosample"
BASE_CONFIG="$ROOT/configs/ai-toolkit/flux2-klein-4b-paired-lora-mps-v0.yaml"
PID_FILE="$LOG_DIR/flux2_klein4b_full.pid"
LATEST_FILE="$LOG_DIR/flux2_klein4b_full.latest"
SCREEN_NAME="flux2_klein4b_full"
STAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/flux2_klein4b_full_${STAMP}.log"
CONFIG_OUT="$GEN_CONFIG_DIR/flux2_klein4b_full_from_pilot_${STAMP}.yaml"

mkdir -p "$LOG_DIR" "$GEN_CONFIG_DIR"

if [[ -f "$PID_FILE" ]]; then
  existing_pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [[ -n "${existing_pid}" ]] && kill -0 "${existing_pid}" 2>/dev/null; then
    echo "Full trainer already running with PID ${existing_pid}"
    exit 0
  fi
fi

if screen -ls | grep -q "[.]${SCREEN_NAME}[[:space:]]"; then
  echo "Screen session ${SCREEN_NAME} already exists"
  exit 0
fi

LATEST_PILOT="$(ls -1 "$PILOT_RUN_DIR"/*.safetensors 2>/dev/null | sort | tail -n 1 || true)"
if [[ -z "${LATEST_PILOT}" ]]; then
  echo "No pilot checkpoint found in $PILOT_RUN_DIR" >&2
  exit 1
fi

source "$ROOT/.venv-ai-toolkit/bin/activate"
python - <<PY
from pathlib import Path
import yaml

base_config = Path("${BASE_CONFIG}")
config_out = Path("${CONFIG_OUT}")
pretrained = Path("${LATEST_PILOT}")

with base_config.open("r") as f:
    data = yaml.safe_load(f)

process = data["config"]["process"][0]
process["network"]["pretrained_lora_path"] = str(pretrained)

with config_out.open("w") as f:
    yaml.safe_dump(data, f, sort_keys=False)
PY

printf '%s\n' "$LOG_FILE" > "$LATEST_FILE"

cat > "$LOG_FILE" <<EOF
== $(date '+%Y-%m-%d %H:%M:%S') Starting FLUX.2 klein 4B full-data run from pilot checkpoint ==
Root: $ROOT
Log:  $LOG_FILE
Config: $CONFIG_OUT
Base config: $BASE_CONFIG
Warm-start checkpoint: $LATEST_PILOT
Screen session: $SCREEN_NAME
EOF

screen -dmS "$SCREEN_NAME" /bin/zsh -lc "
  export PYTHONUNBUFFERED=1
  export HF_HUB_DISABLE_XET=1
  export HF_HUB_DOWNLOAD_TIMEOUT=120
  export HF_HUB_ETAG_TIMEOUT=30
  export OMP_NUM_THREADS=7
  export MKL_NUM_THREADS=7
  export OPENBLAS_NUM_THREADS=7
  export VECLIB_MAXIMUM_THREADS=7
  export NUMEXPR_NUM_THREADS=7
  exec >> '$LOG_FILE' 2>&1
  cd '$ROOT/external/ai-toolkit'
  source '$ROOT/.venv-ai-toolkit/bin/activate'
  exec caffeinate -dimsu taskpolicy -b nice -n 20 \
    python -u run.py '$CONFIG_OUT'
"

sleep 2
trainer_pid="$(pgrep -f \"run.py ${CONFIG_OUT}\" | head -n 1 || true)"
if [[ -n "${trainer_pid}" ]]; then
  echo "$trainer_pid" > "$PID_FILE"
  echo "Started full trainer PID $trainer_pid"
else
  echo "Started screen session $SCREEN_NAME; trainer PID not detected yet"
fi
