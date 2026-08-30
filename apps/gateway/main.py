"""ev-gateway entrypoint. One process owns WS, REST, risk, journal, static HUD,
and the broker link.

Import order matters here and only here: the Twisted asyncio reactor has to be
installed before anything can import ``twisted.internet.reactor`` transitively.
"""

from __future__ import annotations

from apps.gateway.broker import reactor_setup  # noqa: F401  (must be first)

reactor_setup.install()

import asyncio  # noqa: E402
import contextlib  # noqa: E402
import json  # noqa: E402
import logging  # noqa: E402
import os  # noqa: E402
from contextlib import asynccontextmanager  # noqa: E402
from pathlib import Path  # noqa: E402
from urllib.parse import urlparse  # noqa: E402

from fastapi import FastAPI, WebSocket, WebSocketDisconnect  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

from apps.gateway.api.gateway import Gateway  # noqa: E402
from apps.gateway.api.ws import WsSession  # noqa: E402
from apps.gateway.config import Config, load  # noqa: E402
from apps.gateway.protocol import PROTOCOL_VERSION, now_ms  # noqa: E402
from apps.gateway.risk import rules  # noqa: E402

log = logging.getLogger("ev.main")


def create_app(cfg: Config) -> FastAPI:
    # Cheap enough to assert at boot, and it is the one property the whole
    # safety story rests on: a close or a panic is never gated.
    assert rules.safety_exits_are_ungated(), "a safety exit became gateable"

    gw = Gateway(cfg)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        log.info(
            "ev-gateway up on %s (%s, %s, broker=%s)",
            cfg.gateway.listen, cfg.mode, cfg.timezone, cfg.broker.transport,
        )
        await gw.start()
        yield
        await gw.shutdown()

    app = FastAPI(title="ev-gateway", version="0.1.0", lifespan=lifespan)
    app.state.gw = gw

    @app.get("/healthz")
    async def healthz() -> JSONResponse:
        health = await gw.broker.health()
        return JSONResponse(
            {
                # `ok` is about the process, not the broker. A gateway serving
                # the HUD with the broker down is degraded, not dead, and the
                # container should not be restarted out from under it.
                "ok": True,
                "mode": cfg.mode,
                "protocol": PROTOCOL_VERSION,
                "tz": cfg.timezone,
                "broker": {
                    "adapter": cfg.broker.adapter,
                    "transport": cfg.broker.transport,
                    # Loud on purpose: anything but `real` means no order
                    # reaches a broker, and that must never be a surprise.
                    "simulated": cfg.broker.transport != "real",
                    "connected": health.connected,
                    "authed": health.authed,
                    "account": health.account_id,
                    "symbols": health.symbols,
                    "detail": health.detail,
                },
                "faults": gw.containment.faults,
            }
        )

    @app.post("/api/session/checkin")
    async def check_in(body: dict) -> JSONResponse:
        """The pre/post 1-5 self rating.

        Skippable by design: a null rating is recorded as a deliberate skip, and
        this endpoint never blocks the session starting or closing -- a bad
        answer here must not cost the player their evening.
        """
        phase = body.get("phase")
        if phase not in {"pre", "post"}:
            return JSONResponse({"ok": False, "reason": "phase must be pre or post"}, 400)
        rating = body.get("rating")
        if rating is not None and not (isinstance(rating, int) and 1 <= rating <= 5):
            return JSONResponse({"ok": False, "reason": "rating must be 1-5 or null"}, 400)

        ts = now_ms()
        session_id = gw.ensure_session(ts)
        gw.journal.write_check_in(session_id, phase, rating, ts, body.get("note"))
        return JSONResponse({"ok": True, "sessionId": session_id, "skipped": rating is None})

    @app.get("/api/score/session/{session_id}")
    async def score_session(session_id: int) -> JSONResponse:
        """The settled Process Score for one session.

        Deliberately a REST read for the deck rather than a live socket push:
        the plan puts the score on the deck, not the HUD, precisely so there is
        no live score to watch mid-session.
        """
        row = gw.journal.score_row(session_id)
        if row is None:
            return JSONResponse({"ok": False, "reason": "not settled"}, 404)
        return JSONResponse({
            "ok": True,
            "sessionId": session_id,
            "settledAt": row["settled_at"],
            "total": row["total"],
            "axes": json.loads(row["axes_json"]),
            "na": json.loads(row["na_json"]),
            "items": json.loads(row["items_json"]),
            "weightsVersion": row["weights_version"],
        })

    @app.post("/api/score/settle")
    async def settle_score() -> JSONResponse:
        """Settle tonight now. Called at session close; exposed so the deck can
        force it after a late check-in."""
        result = gw.settle_score()
        return JSONResponse({"ok": True, **result.as_message()})

    @app.post("/api/session/standdown")
    async def stand_down(body: dict) -> JSONResponse:
        """The evening's stand-down tally, with the conditions each one met.
        Phase 11's Selectivity axis reads these rather than counting its own."""
        events = body.get("events")
        if not isinstance(events, list):
            return JSONResponse({"ok": False, "reason": "events must be a list"}, 400)
        session_id = gw.ensure_session(now_ms())
        gw.journal.record_stand_downs(session_id, events)
        return JSONResponse({"ok": True, "count": len(events)})

    @app.websocket(cfg.gateway.ws_path)
    async def ws(sock: WebSocket) -> None:
        origin = sock.headers.get("origin")
        if origin and not _origin_allowed(origin, cfg, sock.headers.get("host")):
            await sock.close(code=4403)
            return
        await sock.accept()
        session = WsSession(gw, sock.send_text)
        gw.sessions.add(session)
        pump = asyncio.create_task(_pump(session, gw))
        try:
            while True:
                raw = await sock.receive_text()
                await session.handle(raw)
        except WebSocketDisconnect:
            return
        finally:
            gw.sessions.discard(session)
            pump.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await pump

    static_dir = Path(cfg.gateway.static_dir)
    if static_dir.is_dir():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="hud")
    else:
        log.warning(
            "static_dir %s does not exist; build the HUD with "
            "`pnpm -C app build` or the gateway serves no UI",
            static_dir,
        )
    return app


async def _pump(session: WsSession, gw: Gateway) -> None:
    """Drain broker pushes onto the socket.

    Broker callbacks are synchronous and run on the shared reactor, so they
    queue rather than send. This task is the only thing that writes them out.
    """
    while True:
        for sym, (bid, ask, ts) in list(gw.state.last_quote.items()):
            spec = gw.broker.symbol_spec(sym)
            session.enqueue_quote(sym, bid, ask, ts, spec.digits if spec else 5)
        session.enqueue_forming(int(asyncio.get_running_loop().time() * 1000))
        try:
            await session.flush()
        except Exception:
            return
        await asyncio.sleep(1.0 / 30.0)


def _origin_allowed(origin: str, cfg: Config, host_header: str | None = None) -> bool:
    """Same origin as the HUD, plus the Vite dev server in dev.

    Same-origin is decided against the request's own ``Host`` header, not
    against the configured port: the gateway may be reached on a different port
    than ``gateway.listen`` names (a tunnel, a proxy, a test server), and
    refusing the page's own origin would break the HUD it just served.
    """
    origin = origin.rstrip("/")
    if host_header and urlparse(origin).netloc == host_header:
        return True

    allowed = {cfg.gateway.public_origin.rstrip("/")}
    if cfg.dev:
        # Vite serves the HUD on 5173 and proxies /ws here.
        allowed |= {"http://localhost:5173", "http://127.0.0.1:5173"}
    return origin in allowed


def run() -> None:
    import uvicorn

    logging.basicConfig(
        level=os.environ.get("EV_LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    cfg = load(os.environ.get("EV_CONFIG", "config/default.yaml"), secrets=True)
    uvicorn.run(create_app(cfg), host=cfg.gateway.host, port=cfg.gateway.port)


if __name__ == "__main__":
    run()
