# ===== Piper TTS pt-BR Dockerfile =====
FROM debian:stable-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8

# Dependências básicas
RUN apt-get update && apt-get install -y \
    wget \
    ca-certificates \
    libsndfile1 \
    alsa-utils \
    pulseaudio-utils \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Diretório de trabalho principal
WORKDIR /data

# Criar estrutura de diretórios
RUN mkdir -p /data/piper/models/pt_BR-faber-medium /data/tmp

# Baixar e extrair Piper
RUN cd /data/piper \
    && wget -q https://github.com/rhasspy/piper/releases/latest/download/piper_linux_x86_64.tar.gz \
    && tar -xzf piper_linux_x86_64.tar.gz --strip-components=1 \
    && rm piper_linux_x86_64.tar.gz \
    && chmod +x piper

# Baixar modelo pt-BR
RUN wget -q -P /data/piper/models/pt_BR-faber-medium \
    https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx \
    && wget -q -P /data/piper/models/pt_BR-faber-medium \
    https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx.json

WORKDIR /data

# Container fica em sleep infinito
CMD ["sleep", "infinity"]