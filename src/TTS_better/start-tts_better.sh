#!/usr/bin/env bash
set -e

IMAGE_NAME="piper-ptbr"
CONTAINER_NAME="tts"
DOCKERFILE_DIR="$(cd "$(dirname "$0")" && pwd)"

# Verifica Docker
if ! command -v docker >/dev/null; then
  echo "❌ Docker not installed"
  exit 1
fi

# Build da imagem se não existir
if ! docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
  echo "🔧 Docker image not found. Building..."
  docker build -t "$IMAGE_NAME" "$DOCKERFILE_DIR"
else
  echo "✔ Docker image exists"
fi

# Remove container antigo se existir
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  docker rm -f "$CONTAINER_NAME"
fi

# Start do container
echo "🚀 Starting TTS container..."
docker run -d \
  --name "$CONTAINER_NAME" \
  --restart unless-stopped \
  -v "$(pwd)/tmp:/data/tmp" \
  "$IMAGE_NAME"

echo "✅ TTS container started! WAVs vão para ./tmp"
