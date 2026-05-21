#!/bin/zsh
set -euo pipefail

ROOT="${1:-/Users/leona/Documents/Playground/painterly-rotoscope-animation/runs/model_bundles}"
KLEIN_DIR="$ROOT/flux2_klein_base_9b"
QWEN_DIR="$ROOT/Qwen3-8B"
VAE_DIR="$ROOT/flux2_vae"
CACHE_ROOT="$HOME/.cache/huggingface/hub/models--black-forest-labs--FLUX.2-klein-base-9B/snapshots"

mkdir -p "$KLEIN_DIR" "$QWEN_DIR" "$VAE_DIR"

download() {
  local url="$1"
  local dest="$2"
  echo "Downloading $(basename "$dest")"
  curl -L --fail --continue-at - --output "$dest" "$url"
}

if [[ ! -e "$KLEIN_DIR/flux-2-klein-base-9b.safetensors" ]]; then
  local_snapshot=""
  local_weight=""
  for snapshot in "$CACHE_ROOT"/*; do
    if [[ -e "$snapshot/flux-2-klein-base-9b.safetensors" ]]; then
      local_snapshot="$snapshot"
      local_weight="$snapshot/flux-2-klein-base-9b.safetensors"
      break
    fi
  done

  if [[ -n "$local_weight" ]]; then
    ln -sf "$local_weight" "$KLEIN_DIR/flux-2-klein-base-9b.safetensors"
    if [[ -e "$local_snapshot/transformer/config.json" ]]; then
      mkdir -p "$KLEIN_DIR/transformer"
      ln -sf "$local_snapshot/transformer/config.json" "$KLEIN_DIR/transformer/config.json"
    fi
    echo "Linked FLUX.2 klein 9B transformer from local HF cache"
  else
    download \
      "https://huggingface.co/black-forest-labs/FLUX.2-klein-base-9B/resolve/main/flux-2-klein-base-9b.safetensors" \
      "$KLEIN_DIR/flux-2-klein-base-9b.safetensors"
  fi
fi

if [[ ! -f "$VAE_DIR/ae.safetensors" ]]; then
  download \
    "https://huggingface.co/ai-toolkit/flux2_vae/resolve/main/ae.safetensors" \
    "$VAE_DIR/ae.safetensors"
fi

for file in \
  config.json \
  generation_config.json \
  merges.txt \
  model.safetensors.index.json \
  tokenizer.json \
  tokenizer_config.json \
  vocab.json \
  model-00001-of-00005.safetensors \
  model-00002-of-00005.safetensors \
  model-00003-of-00005.safetensors \
  model-00004-of-00005.safetensors \
  model-00005-of-00005.safetensors
do
  if [[ ! -f "$QWEN_DIR/$file" ]]; then
    download \
      "https://huggingface.co/Qwen/Qwen3-8B/resolve/main/$file" \
      "$QWEN_DIR/$file"
  fi
done

echo "9B bundle ready under $ROOT"
