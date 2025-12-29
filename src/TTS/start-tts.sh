#!/usr/bin/env bash
set -e

IMAGE_NAME="tts-espeak"
CONTAINER_NAME="tts"
DOCKERFILE_DIR="$(cd "$(dirname "$0")" && pwd)"

if ! command -v docker >/dev/null; then
  echo "❌ Docker not installed"
  exit 1
fi

# Build image if it does not exist
if ! docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
  echo "🔧 Docker image not found. Building..."
  docker build -t "$IMAGE_NAME" "$DOCKERFILE_DIR"
else
  echo "✔ Docker image exists"
fi

# Start container if it does not exist
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  echo "✔ TTS container already exists"
  exit 0
fi

echo "🚀 Starting TTS container..."

docker run -d \
  --name tts \
  --restart unless-stopped \
  -v "$(pwd)/src/TTS/tmp:/data" \
  tts-espeak