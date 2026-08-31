# One image, one service. The web bundle, the Python gateway, and the media tools the journal
# layer needs all land here, because the process that owns risk is the process that talks to the
# broker — there is no execution sidecar to keep alive.

# --- web build -------------------------------------------------------------------------------
FROM node:22-slim AS web
WORKDIR /build
COPY app/package.json app/package-lock.json ./
RUN npm ci
COPY app/ ./
RUN npm run build

# --- whisper.cpp build -----------------------------------------------------------------------
# whisper-cli is a binary, so it stays a spawned child of the gateway in any language.
FROM debian:bookworm-slim AS whisper
ARG WHISPER_REF=v1.7.4
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential cmake git ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 --branch ${WHISPER_REF} https://github.com/ggerganov/whisper.cpp /src
WORKDIR /src
RUN cmake -B build -DCMAKE_BUILD_TYPE=Release -DWHISPER_BUILD_TESTS=OFF -DWHISPER_BUILD_EXAMPLES=ON \
    && cmake --build build --config Release -j "$(nproc)" \
    && cp build/bin/whisper-cli /usr/local/bin/whisper-cli

# --- model floor -----------------------------------------------------------------------------
# Only the ~75 MB tiny.en floor is baked. small.en lands in the journal volume via
# deploy/fetch-models.sh, so the image does not carry a multi-hundred-MB model.
FROM debian:bookworm-slim AS models
ARG TINY_SHA256=921e4cf8686fdd993dcd081a5da5b6c365bfde1162e72b08d75ac75289920b1f
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL -o /ggml-tiny.en.bin \
        https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.en.bin \
    && echo "${TINY_SHA256}  /ggml-tiny.en.bin" | sha256sum -c -

# --- runtime ---------------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

# tini reaps the whisper child and turns SIGTERM into a clean protobuf-socket close (phase 2).
RUN apt-get update && apt-get install -y --no-install-recommends \
        tini ffmpeg libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.8.17 /uv /usr/local/bin/uv

WORKDIR /app/apps/gateway
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

# Dependency layer first: source edits do not re-resolve the environment.
COPY apps/gateway/pyproject.toml apps/gateway/uv.lock* ./
RUN uv sync --no-dev --no-install-project

COPY apps/gateway/ ./
COPY config/ /app/config/
COPY --from=web /build/dist /app/app/dist
# Second gate on generated-type drift: `npm run build` above checks types.ts against the schema
# it was generated from; this checks both against the live Pydantic catalog. A catalog change
# that was never regenerated fails the image build here.
RUN python -m protocol.export_ts --check

COPY --from=whisper /usr/local/bin/whisper-cli /usr/local/bin/whisper-cli
COPY --from=models /ggml-tiny.en.bin /opt/models/ggml-tiny.en.bin

# Docker can only forward a published port to a process bound on the container's 0.0.0.0.
# The loopback guarantee moves out to compose (127.0.0.1:8444:8444) and the host firewall.
ENV EV_CONFIG=/app/config/default.yaml \
    EV_LISTEN=0.0.0.0:8444 \
    EV_CONTAINER_BIND=1

EXPOSE 8444
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "main.py"]
