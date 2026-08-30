#!/usr/bin/env bash
# Fetch a whisper.cpp model into the journal volume, checksum-verified.
#
# The gateway image bakes only the ~75 MB ggml-tiny.en floor. Anything larger
# lives here so the image stays small and a model swap does not mean a rebuild.
#
#   ./deploy/fetch-models.sh                    # small.en into ./var/models
#   ./deploy/fetch-models.sh base.en /opt/models
#   docker compose run --rm -v ev-models:/opt/models ev-gateway \
#       bash deploy/fetch-models.sh small.en /opt/models

set -euo pipefail

MODEL="${1:-small.en}"
DEST="${2:-${EV_MODELS_DIR:-./var/models}}"
BASE_URL="https://huggingface.co/ggerganov/whisper.cpp/resolve/main"

# sha256 of the published ggml-<model>.bin, verified before the file is moved
# into place: a truncated download that still "works" would silently degrade
# every transcript for a month before anyone noticed.
#
# UNPINNED. Fill these in once, from the LFS pointer HuggingFace serves for the
# exact file this script downloads:
#
#     curl -sS https://huggingface.co/ggerganov/whisper.cpp/raw/main/ggml-small.en.bin
#     # -> oid sha256:<the value that goes below>
#
# Deliberately left empty rather than filled with a plausible-looking hash: a
# wrong checksum here is worse than none, because it looks like verification.
declare -A SHA256=(
  [tiny.en]=""
  [base.en]=""
  [small.en]=""
)

if [[ ! -v SHA256[$MODEL] ]]; then
  echo "unknown model '$MODEL'. Known: ${!SHA256[*]}" >&2
  exit 2
fi

if [[ -z "${SHA256[$MODEL]}" ]]; then
  cat >&2 <<MSG
ggml-$MODEL.bin has no pinned checksum in $0.

Pin it once, then re-run:
  curl -sS https://huggingface.co/ggerganov/whisper.cpp/raw/main/ggml-$MODEL.bin
  # read the 'oid sha256:<hash>' line and put <hash> in the SHA256 table

Refusing to install an unverified model.
MSG
  exit 3
fi

mkdir -p "$DEST"
target="$DEST/ggml-$MODEL.bin"

if [[ -f "$target" ]] && echo "${SHA256[$MODEL]}  $target" | sha256sum -c --status; then
  echo "ggml-$MODEL.bin already present and verified"
  exit 0
fi

tmp="$(mktemp "${target}.XXXXXX")"
trap 'rm -f "$tmp"' EXIT

echo "downloading ggml-$MODEL.bin -> $DEST"
curl -fL --retry 3 --retry-delay 2 -o "$tmp" "$BASE_URL/ggml-$MODEL.bin"

actual="$(sha256sum "$tmp" | cut -d' ' -f1)"
if [[ "$actual" != "${SHA256[$MODEL]}" ]]; then
  echo "checksum mismatch for ggml-$MODEL.bin" >&2
  echo "  expected ${SHA256[$MODEL]}" >&2
  echo "  actual   $actual" >&2
  echo "Refusing to install. Update the table in this script if upstream" >&2
  echo "republished the model, after checking why." >&2
  exit 1
fi

chmod 0644 "$tmp"
mv "$tmp"  "$target"
trap - EXIT
echo "installed $target"
