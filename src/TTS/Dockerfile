FROM debian:stable-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8

# Enable contrib and non-free repositories (Debian 12+)
RUN sed -i 's/Components: main/Components: main contrib non-free non-free-firmware/' \
    /etc/apt/sources.list.d/debian.sources

# Install TTS dependencies
RUN apt-get update && apt-get install -y \
    espeak-ng \
    espeak-ng-data \
    mbrola \
    mbrola-br1 \
    mbrola-br2 \
    mbrola-br3 \
    mbrola-br4 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /data

WORKDIR /data

CMD ["sleep", "infinity"]
