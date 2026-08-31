"""Gateway entrypoint.

One process, one container: WebSocket, REST, risk, cid ledger, journal, the static HUD, and the
broker link all live here. Phase 1 boots it far enough to answer `/healthz` on the loopback
bind; phase 2 attaches the cTrader link and the game socket.
"""

from __future__ import annotations

import logging
import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from broker import StubBroker
from config import AppConfig, ConfigError, load_config
from db.migrate import migrate
from protocol import PROTOCOL_VERSION

log = logging.getLogger("ev-gateway")

DEFAULT_CONFIG = "config/default.yaml"

# Repo root, so relative paths in config resolve the same from a container or a dev checkout.
ROOT = Path(__file__).resolve().parents[2]


def boot_config() -> AppConfig:
    """Load config or exit non-zero with a named reason. Never half-start."""
    path = Path(os.environ.get("EV_CONFIG", ROOT / DEFAULT_CONFIG))
    try:
        return load_config(path)
    except ConfigError as exc:
        print(f"boot-fail: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


def create_app(cfg: AppConfig | None = None) -> FastAPI:
    """Build the ASGI app. Migrations run at startup, before anything is served."""
    config = cfg or boot_config()
    broker = StubBroker()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        applied = migrate(config.paths.db)
        if applied:
            log.info("applied migrations: %s", ", ".join(applied))
        yield

    app = FastAPI(title="ev-gateway", version="0.1.0", lifespan=lifespan)
    app.state.config = config
    app.state.broker = broker

    @app.get("/healthz")
    def healthz() -> dict[str, object]:
        return {
            "ok": True,
            "mode": config.mode,
            "protocol": PROTOCOL_VERSION,
            "broker": broker.snapshot(),
        }

    static_dir = (ROOT / config.gateway.static_dir).resolve()
    if static_dir.is_dir():
        # The gateway serves the HUD itself: one origin for the page and the socket.
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="hud")
    else:
        log.warning("static_dir %s does not exist yet; build the web app to serve the HUD", static_dir)

    return app


def main() -> int:
    logging.basicConfig(level=os.environ.get("EV_LOG_LEVEL", "INFO"))
    import uvicorn

    config = boot_config()
    uvicorn.run(
        create_app(config),
        host=config.gateway.host,
        port=config.gateway.port,
        log_level=os.environ.get("EV_LOG_LEVEL", "info").lower(),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
