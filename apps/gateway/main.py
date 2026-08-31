"""Gateway entrypoint.

One process, one container: WebSocket, REST, risk, cid ledger, journal, the static HUD, and the
cTrader link. The reactor is installed before anything can import Twisted's default one, and
uvicorn is run on that same loop so the broker client and the web server never fight over it.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from broker import reactor_setup

# Before FastAPI, before uvicorn, before anything that might reach Twisted.
_LOOP = asyncio.new_event_loop()
asyncio.set_event_loop(_LOOP)
_REACTOR = reactor_setup.install(_LOOP)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from api.conflate import Conflator  # noqa: E402
from api.ws import GameSocket, GatewayState, origin_allowed  # noqa: E402
from broker import Broker, StubBroker  # noqa: E402
from broker.ctrader import CTraderBroker  # noqa: E402
from broker.events import normalise_execution  # noqa: E402
from config import AppConfig, ConfigError, load_config  # noqa: E402
from db.migrate import connect, migrate  # noqa: E402
from journal.recorder import TradeRecorder  # noqa: E402
from journal.tape import TapeRing  # noqa: E402
from journal.writer import JournalWriter  # noqa: E402
from protocol import PROTOCOL_VERSION  # noqa: E402
from risk.session import SessionWindow  # noqa: E402

log = logging.getLogger("ev-gateway")

DEFAULT_CONFIG = "config/default.yaml"
RECONNECT_BACKOFF_S = (2, 5, 15, 30, 60)

# How often settled tape windows are swept to disk.
FREEZE_SWEEP_S = 30

ROOT = Path(__file__).resolve().parents[2]


class CheckInRequest(BaseModel):
    """Pre/post self-rating. `rating: null` is a deliberate skip, not a low score."""

    phase: Literal["pre", "post"]
    rating: int | None = Field(default=None, ge=1, le=5)


class StandDownRequest(BaseModel):
    """The conditions that were live when the player chose not to fire."""

    conditions: list[str] = Field(default_factory=list)


def boot_config() -> AppConfig:
    """Load config or exit non-zero with a named reason. Never half-start."""
    path = Path(os.environ.get("EV_CONFIG", ROOT / DEFAULT_CONFIG))
    try:
        return load_config(path)
    except ConfigError as exc:
        print(f"boot-fail: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


def build_broker(config: AppConfig, loop: asyncio.AbstractEventLoop) -> Broker:
    """A real cTrader link when credentials are present, the phase 1 stub when they are not."""
    env = os.environ
    account_id = env.get(config.broker.account_id_env)
    if not account_id:
        return StubBroker()
    return CTraderBroker(
        host=config.broker.host,
        port=config.broker.port,
        client_id=env[config.broker.client_id_env],
        client_secret=env[config.broker.client_secret_env],
        access_token=env[config.broker.token_env],
        account_id=int(account_id),
        symbol_names=tuple(s.name for s in config.symbols),
        loop=loop,
    )


def _attach_recorder(broker: CTraderBroker, recorder: TradeRecorder) -> None:
    """Route execution events into the journal, through the containment boundary.

    The handler translates once and dispatches; anything the journal does not care about (swaps,
    deposits, bare acceptances) falls through without touching a table.
    """

    def handle(event: object) -> None:
        fact = normalise_execution(event)
        spec = broker.by_symbol_id.get(fact.symbol_id or -1)
        if fact.kind == "fill" and spec is not None and fact.cid:
            prices = {name: q.mid for name, q in broker.quotes.items()}
            recorder.on_fill(
                cid=fact.cid, position_id=fact.position_id or 0, symbol=spec.name,
                side=fact.side or "buy", volume=fact.volume or 0, entry=fact.price or 0.0,
                ts_ms=fact.ts_ms or 0,
                prices={s.symbol_id: prices[s.name] for s in broker.specs.values()
                        if s.name in prices},
            )
        elif fact.kind == "close" and fact.position_id:
            recorder.on_close(
                position_id=fact.position_id, exit_price=fact.price or 0.0,
                ts_ms=fact.ts_ms or 0, gross_pnl=fact.gross_pnl,
                commission=fact.commission, swap=fact.swap,
            )
        elif fact.kind == "reject" and fact.cid:
            recorder.journal.append_event(kind="reject", ts_ms=fact.ts_ms or 0, cid=fact.cid,
                                          payload={"reason": fact.reason})

    broker.on_event(handle)


async def _freeze_sweep(recorder: TradeRecorder) -> None:
    """Windows whose post-roll has settled become `trade_tape` rows."""
    while True:
        await asyncio.sleep(FREEZE_SWEEP_S)
        try:
            recorder.due_freezes()
        except Exception:
            log.exception("tape freeze sweep failed")


async def _connect_with_backoff(broker: Broker, ring: TapeRing, recorder: TradeRecorder) -> None:
    """Keep trying to reach Spotware without ever blocking the HUD from being served.

    The reconnect state machine has one axis now: there is no exec link that can be up while the
    broker link is down. On success, reconcile — cTrader is the truth about what is open.
    """
    if not isinstance(broker, CTraderBroker):
        return
    for delay in (0, *RECONNECT_BACKOFF_S):
        if delay:
            await asyncio.sleep(delay)
        try:
            await broker.connect()
            broker.on_spot(
                lambda quote: ring.tick(quote.symbol, bid=quote.bid, ask=quote.ask,
                                        ts_ms=quote.ts_ms)
            )
            await broker.subscribe()
            recorder.specs = broker.specs
            recorder.graph = broker.graph
            _attach_recorder(broker, recorder)
            positions = await broker.positions()
            log.info("broker link up; reconciled %d open position(s)", len(positions))
            return
        except Exception:
            log.exception("broker connect failed; retrying")
    log.error("broker link could not be established; the HUD stays up and trading stays refused")


async def _account_snapshot(broker: Broker) -> dict[str, float | None]:
    """Balance and equity straight from cTrader. Never re-derived from summed fills.

    A snapshot the broker cannot supply is stored as null rather than as a guess — phase 6 would
    rather see a gap than a fabricated equity curve.
    """
    try:
        account = await broker.account()
    except Exception:
        log.exception("account snapshot failed; recording the session without one")
        return {"balance": None, "equity": None}
    return {"balance": account.get("balance"), "equity": account.get("equity", account.get("balance"))}


def create_app(cfg: AppConfig | None = None, *, loop: asyncio.AbstractEventLoop | None = None) -> FastAPI:
    """Build the ASGI app. Migrations run at startup, before anything is served."""
    config = cfg or boot_config()
    active_loop = loop or _LOOP
    broker = build_broker(config, active_loop)
    ring = TapeRing(ring_minutes=config.tape.ring_minutes, dt_s=int(config.tape.dt_s))
    conflator = Conflator()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        applied = migrate(config.paths.db)
        if applied:
            log.info("applied migrations: %s", ", ".join(applied))
        reactor_setup.start(_REACTOR)

        journal = JournalWriter(connect(config.paths.db))
        window = SessionWindow.from_config(
            config.timezone, config.session.days, config.session.start, config.session.end
        )
        recorder = TradeRecorder(
            journal=journal, ring=ring, specs={}, graph=None,
            session_id=window.local(int(time.time() * 1000)).strftime("%Y-%m-%d"),
            r_unit_usd=config.risk.r_unit_usd, pre_roll_s=config.tape.pre_roll_s,
            post_roll_s=config.tape.post_roll_s, dt_s=int(config.tape.dt_s),
        )
        app.state.recorder = recorder

        tasks = [
            asyncio.ensure_future(_connect_with_backoff(broker, ring, recorder)),
            asyncio.ensure_future(_freeze_sweep(recorder)),
        ]
        try:
            yield
        finally:
            for task in tasks:
                task.cancel()
            # Freeze with whatever post-roll exists rather than losing the windows.
            recorder.flush()
            journal.conn.close()
            if isinstance(broker, CTraderBroker):
                await broker.disconnect()

    app = FastAPI(title="ev-gateway", version="0.2.0", lifespan=lifespan)
    app.state.config = config
    app.state.broker = broker
    app.state.ring = ring
    app.state.conflator = conflator

    @app.get("/healthz")
    def healthz() -> dict[str, object]:
        return {
            "ok": True,
            "mode": config.mode,
            "protocol": PROTOCOL_VERSION,
            "broker": broker.snapshot(),
        }

    def session_id_now() -> str:
        window = SessionWindow.from_config(
            config.timezone, config.session.days, config.session.start, config.session.end
        )
        return window.local(int(time.time() * 1000)).strftime("%Y-%m-%d")

    @app.post("/api/journal/checkin")
    def checkin(body: CheckInRequest) -> dict[str, object]:
        """Pre/post self-rating, 1-5, skippable.

        This rides HTTP rather than the game socket on purpose. Protocol v1 was frozen in phase 1
        with no check-in message, and a journal write has no business on the socket whose job is
        prioritising order acks — the same reasoning that puts voice audio and the decks here.
        """
        session_id = session_id_now()
        journal = JournalWriter(connect(config.paths.db))
        try:
            journal.open_session(session_id, timezone=config.timezone,
                                 opened_at=int(time.time() * 1000), balance=None, equity=None)
            journal.write_checkin(session_id, phase=body.phase, rating=body.rating,
                                  ts_ms=int(time.time() * 1000))
            return {"ok": True, "sessionId": session_id, "skipped": body.rating is None}
        finally:
            journal.conn.close()

    @app.post("/api/journal/stand-down")
    def stand_down(body: StandDownRequest) -> dict[str, object]:
        """A cancelled arm under a live stand-down condition. Standing down reads as a win."""
        session_id = session_id_now()
        journal = JournalWriter(connect(config.paths.db))
        try:
            journal.open_session(session_id, timezone=config.timezone,
                                 opened_at=int(time.time() * 1000), balance=None, equity=None)
            count = journal.increment_stood_down(session_id)
            journal.append_event(kind="stand_down", ts_ms=int(time.time() * 1000),
                                 payload={"conditions": body.conditions})
            return {"ok": True, "stoodDown": count}
        finally:
            journal.conn.close()

    @app.websocket(config.gateway.ws_path)
    async def game_socket(websocket: WebSocket) -> None:
        """One socket per token, same origin as the HUD."""
        origin = websocket.headers.get("origin")
        if not origin_allowed(origin, config.gateway.public_origin):
            await websocket.close(code=4403)
            return
        expected = os.environ.get(config.gateway.token_env)
        if not expected or websocket.query_params.get("token") != expected:
            await websocket.close(code=4401)
            return

        await websocket.accept()
        journal = JournalWriter(connect(config.paths.db))
        window = SessionWindow.from_config(
            config.timezone, config.session.days, config.session.start, config.session.end
        )
        now_ms = int(time.time() * 1000)
        # One session row per evening in the configured zone, so a reconnect resumes the same
        # session rather than opening a second one with a second equity snapshot.
        session_id = window.local(now_ms).strftime("%Y-%m-%d")
        opening = await _account_snapshot(broker)
        journal.open_session(
            session_id, timezone=config.timezone, opened_at=now_ms,
            balance=opening.get("balance"), equity=opening.get("equity"),
        )
        game = GameSocket(
            send=websocket.send_text,
            broker=broker,
            journal=journal,
            window=window,
            state=GatewayState(session_id=session_id),
            allowed_symbols=frozenset(s.name for s in config.symbols),
            max_positions=config.risk.max_positions,
            max_lots_by_symbol={s.name: s.max_lots for s in config.symbols},
            max_day_loss_usd=config.risk.max_daily_loss_usd,
            min_seconds_between_orders=config.risk.min_seconds_between_orders,
            heartbeat_dead_s=config.gateway.heartbeat_dead_s,
        )
        try:
            while True:
                await game.handle_raw(await websocket.receive_text())
        except WebSocketDisconnect:
            log.info("game socket closed")
        finally:
            closing = await _account_snapshot(broker)
            journal.close_session(
                session_id, closed_at=int(time.time() * 1000),
                balance=closing.get("balance"), equity=closing.get("equity"),
            )
            journal.conn.close()

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
    server = uvicorn.Server(
        uvicorn.Config(
            create_app(config, loop=_LOOP),
            host=config.gateway.host,
            port=config.gateway.port,
            log_level=os.environ.get("EV_LOG_LEVEL", "info").lower(),
            loop="none",  # the loop is ours; the reactor is already installed on it
        )
    )
    _LOOP.run_until_complete(server.serve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
