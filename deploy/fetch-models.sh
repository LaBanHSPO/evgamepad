#!/usr/bin/env bash
# Download the checksum-verified small.en whisper model into the journal volume.
#
# The image bakes only the ~74 MB tiny.en floor. small.en is ~465 MB, so it lives on the volume
# instead — run this once per box, after the volume exists. Phase 8 owns the runtime benchmark
# that decides whether small.en is actually the tier this VPS can serve.
#
# Usage:  deploy/fetch-models.sh [target-dir]        (default: /var/lib/evgamepad/data/models)

set -euo pipefail

MODEL="ggml-small.en.bin"
# sha256 of the file content, from the HuggingFace LFS metadata for ggerganov/whisper.cpp.
SHA256="c6138d6d58ecc8322097e0f987c32f1be8bb0a18532a3f88f734d1bbf9c41e5d"
URL="https://huggingface.co/ggerganov/whisper.cpp/resolve/main/${MODEL}"

TARGET_DIR="${1:-/var/lib/evgamepad/data/models}"
TARGET="${TARGET_DIR}/${MODEL}"

mkdir -p "${TARGET_DIR}"

if [[ -f "${TARGET}" ]] && echo "${SHA256}  ${TARGET}" | sha256sum -c - >/dev/null 2>&1; then
    echo "already present and verified: ${TARGET}"
    exit 0
fi

echo "downloading ${MODEL} -> ${TARGET_DIR}"
# Stage under a temp name so an interrupted download never looks like a verified model.
TMP="$(mktemp "${TARGET_DIR}/.${MODEL}.XXXXXX")"
trap 'rm -f "${TMP}"' EXIT

curl -fL --progress-bar -o "${TMP}" "${URL}"
echo "${SHA256}  ${TMP}" | sha256sum -c -
mv "${TMP}" "${TARGET}"
trap - EXIT

echo "verified: ${TARGET}"
