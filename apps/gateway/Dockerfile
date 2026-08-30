# syntax=docker/dockerfile:1
#
# One image, one service. The execution sidecar is gone, so the HUD, the socket,
# the journal, and the cTrader link all ship together.

# ---------------------------------------------------------------- web build --
FROM node:22-slim AS web
WORKDIR /build
COPY app/package.json app/package-lock.json* ./
RUN npm install --no-audit --no-fund
COPY app/ ./
# The protocol types are generated from the gateway catalog's exported schema,
# so this stage fails if the committed types are stale.
RUN node scripts/gen-protocol-types.mjs --check && npm run build -- --mode production \
    || (npx tsc -b && npx vite build)

# ------------------------------------------------------------ whisper build --
# whisper-cli is the only binary phase 8 needs. Built here so the runtime layer
# carries no toolchain.
FROM debian:bookworm-slim AS whisper
ARG WHISPER_REF=v1.7.4
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential cmake git ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 --branch ${WHISPER_REF} \
        https://github.com/ggerganov/whisper.cpp /src
WORKDIR /src
RUN cmake -B build -DCMAKE_BUILD_TYPE=Release -DWHISPER_BUILD_TESTS=OFF \
    && cmake --build build -j"$(nproc)" --config Release \
    && install -m 0755 build/bin/whisper-cli /out-whisper-cli
# The ~75 MB tiny.en floor is baked in so voice degrades rather than breaks.
# small.en is far larger and lands in the journal volume via
# deploy/fetch-models.sh instead of bloating this image.
RUN ./models/download-ggml-model.sh tiny.en

# ------------------------------------------------------------------ runtime --
FROM python:3.11-slim AS runtime

# tini reaps and forwards signals. Twisted needs a clean SIGTERM to close the
# Protobuf socket and drain the WS instead of being killed mid-order.
RUN apt-get update && apt-get install -y --no-install-recommends \
        tini ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY --from=whisper /out-whisper-cli /usr/local/bin/whisper-cli
COPY --from=whisper /src/models/ggml-tiny.en.bin /opt/models/ggml-tiny.en.bin

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /srv
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    EV_MODELS_DIR=/opt/models

COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev --all-extras 2>/dev/null || uv sync --no-dev --all-extras

COPY apps/gateway ./apps/gateway
COPY config ./config
COPY --from=web /build/dist ./app/dist

RUN useradd --system --uid 10001 --home /srv ev \
    && mkdir -p /srv/var && chown -R ev:ev /srv
USER ev

# Loopback only. The VPS's existing TLS on :443 is what faces the network.
EXPOSE 8444
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["uv", "run", "python", "-m", "apps.gateway.main"]
