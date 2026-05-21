#!/bin/zsh
set -euo pipefail

ROOT="${1:-/Users/leona/Documents/Playground/painterly-rotoscope-animation/runs/model_bundles}"
KLEIN_DIR="$ROOT/flux2_klein_base_9b"
QWEN_DIR="$ROOT/Qwen3-8B"
VAE_DIR="$ROOT/flux2_vae"

mkdir -p "$KLEIN_DIR" "$QWEN_DIR" "$VAE_DIR"

download() {
  local url="$1"
  local dest="$2"
  echo "Downloading $(basename "$dest")"
  curl -L --fail --continue-at - --output "$dest" "$url"
}

download \
  "https://huggingface.co/black-forest-labs/FLUX.2-klein-base-9B/resolve/main/flux-2-klein-base-9b.safetensors" \
  "$KLEIN_DIR/flux-2-klein-base-9b.safetensors"

download \
  "https://huggingface.co/ai-toolkit/flux2_vae/resolve/main/ae.safetensors" \
  "$VAE_DIR/ae.safetensors"

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
  download \
    "https://huggingface.co/Qwen/Qwen3-8B/resolve/main/$file" \
    "$QWEN_DIR/$file"
done

echo "Bundle ready under $ROOT"
