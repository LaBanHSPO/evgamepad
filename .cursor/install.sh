#!/usr/bin/env bash
# Idempotent Cloud Agent bootstrap for the Evening Forex Gold Gamepad monorepo.
# Installs the Python gateway deps (via uv) and the React PWA deps (via npm), and seeds a
# local dev .env with non-functional placeholder credentials so the gateway can boot for
# development. Replace the placeholders (or supply real values via secrets) to exercise the
# live cTrader demo link.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# --- uv (Python package manager) ---
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi
export PATH="$HOME/.local/bin:$PATH"

# --- Backend gateway deps ---
( cd apps/gateway && uv sync --group dev )

# --- Frontend PWA deps ---
( cd app && npm install )

# --- Dev .env (placeholders only; never overwrite an existing file) ---
if [ ! -f .env ]; then
  cat > .env <<'EOF'
# Local dev placeholders — NOT real credentials. The gateway boots with these; the cTrader
# broker link fails gracefully in the background ("HUD stays up and trading stays refused").
# Replace with real IC Markets cTrader demo values to exercise live trading. Never commit.
CT_CLIENT_ID=dev-client-id
CT_CLIENT_SECRET=dev-client-secret
CT_ACCESS_TOKEN=dev-access-token
CT_REFRESH_TOKEN=dev-refresh-token
CT_ACCOUNT_ID=1000000

EV_WS_TOKEN=dev-ws-token
EOF
  echo "wrote dev .env with placeholder credentials"
fi

echo "install complete"
