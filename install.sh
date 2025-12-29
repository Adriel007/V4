#!/usr/bin/env bash
set -e

echo "=== Installing host dependencies ==="

command -v python3 >/dev/null || { echo "python3 missing"; exit 1; }
command -v pip3 >/dev/null || { echo "pip3 missing"; exit 1; }
command -v docker >/dev/null || echo "⚠ Docker not found (required for TTS)"

python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

mkdir -p output

echo "=== Install completed ==="
