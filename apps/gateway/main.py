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
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from broker import reactor_setup

# Before FastAPI, before uvicorn, before anything that might reach Twisted.
_LOOP = asyncio.new_event_loop()
asyncio.set_event_loop(_LOOP)
_REACTOR = reactor_setup.install(_LOOP)

from fastapi import FastAPI, HTTPException, Request, Response, WebSocket, WebSocketDisconnect  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel, ConfigDict, Field  # noqa: E402

from api.conflate import Conflator  # noqa: E402
from api.ws import GameSocket, GatewayState, origin_allowed  # noqa: E402
from broker import Broker, StubBroker  # noqa: E402
from broker.ctrader import CTraderBroker  # noqa: E402
from broker.events import normalise_execution  # noqa: E402
from config import AppConfig, ConfigError, load_config  # noqa: E402
from copilot.client import SpaceXaiClient  # noqa: E402
from copilot.loops import DeskLoops  # noqa: E402
from copilot.tools import build_registry  # noqa: E402
from db.migrate import connect, migrate  # noqa: E402
from deck.routes import DeckRepository  # noqa: E402
from grading.grade import grade_fire  # noqa: E402
from grading.routes import (  # noqa: E402
    ChecklistRequest,
    PlaybookRepository,
    PlaybookRequest,
    registry_view,
    unknown_codes,
)
from journal.attachments import AttachmentError, path_for, store, usage  # noqa: E402
from journal.query_service import DEFAULT_PAGE, HISTORY_FILTERS, JournalService  # noqa: E402
from journal.recorder import TradeRecorder  # noqa: E402
from journal.sizing import size_position  # noqa: E402
from journal.tape import TapeRing  # noqa: E402
from journal.writer import JournalWriter  # noqa: E402
from method.rules import RuleContext  # noqa: E402
from protocol import PROTOCOL_VERSION  # noqa: E402
from replay import ReplayRepository  # noqa: E402
from risk.session import SessionWindow  # noqa: E402
from score import ScoreRepository  # noqa: E402
from score.opportunity import OpportunitySampler  # noqa: E402
from score.repository import VOICE_CAPTURE_BUILT  # noqa: E402
from sentinel.engine import SentinelEngine  # noqa: E402
from signals.calendar import CalendarCache, currencies_for  # noqa: E402
from signals.tv_webhook import TvAlert, WebhookGuard, to_signal  # noqa: E402
from tilt.baseline import load_baseline  # noqa: E402
from tilt.score import Bands  # noqa: E402
from tilt.tracker import TiltTracker  # noqa: E402

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


def build_deck(config: AppConfig) -> DeckRepository:
    """The deck reads the journal; it never writes and never touches the broker."""
    return DeckRepository(
        config.paths.db,
        max_lots=max((s.max_lots for s in config.symbols), default=0.1),
        max_positions=config.risk.max_positions,
        min_sessions_for_sharpe=config.deck.min_sessions_for_sharpe,
    )


def build_desk(config: AppConfig, sentinel: SentinelEngine, broker: Broker,
               deck: DeckRepository, tilt_view: dict[str, object] | None = None,
               score: ScoreRepository | None = None,
               session_id: Callable[[], str] | None = None,
               journal: JournalService | None = None) -> DeskLoops:
    """Assemble the desk from read-only tools.

    Everything it can see is passed in through the registry; it has no reference to the broker's
    order methods and no way to acquire one.
    """
    client = SpaceXaiClient(
        api_key=os.environ.get("XAI_API_KEY"),
        model=config.copilot.model,
        allowed_domains=list(config.copilot.allowed_domains),
    )
    symbols = [s.name for s in config.symbols]

    def sentinel_state() -> dict[str, object]:
        first = symbols[0]
        setup = sentinel.tracker(first).current
        return {"symbol": first, "setup": setup.kind if setup else None}

    tools = build_registry(
        get_sentinel=sentinel_state,
        get_positions=lambda: [],
        get_account=lambda: {"note": "account figures are read at session open and close"},
        get_calendar=lambda: [
            {"title": e.title, "currency": e.currency, "local": e.local}
            for e in (sentinel.calendar.upcoming(int(time.time() * 1000),
                                                 currencies=currencies_for(symbols))
                      if sentinel.calendar else [])
        ],
        get_setup=lambda: sentinel_state(),
        # Process aggregates only. No account credentials, no raw journal, no money field.
        # Phase 11 folds the five axes in, so the desk can coach a named axis rather than a mood.
        get_progress=(
            deck.summary if score is None or session_id is None
            else lambda: {**deck.summary(), "score": score.axes_summary(session_id())}
        ),
        # Phase 9. Band, score, and driver sentences — never a component value or a pad frame.
        get_tilt=None if tilt_view is None else (lambda: dict(tilt_view)),
        get_journal=None if journal is None else journal.aggregates,
    )

    async def publish(_t: str, _ch: str, _payload: dict) -> None:
        """Phase 4 keeps desk output on the ask path; the news rail lands with the desk HUD."""
        return None

    return DeskLoops(client=client, tools=tools, publish=publish, symbols=symbols)


class TodayRequest(BaseModel):
    """Readiness and daily analysis. Both optional: a PUT may carry either or both."""

    model_config = ConfigDict(extra="forbid")

    sessionId: str | None = None
    readiness: list[dict] | None = None
    analysis: dict | None = None


class TradeReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: str | None = None
    note: str | None = None
    earlyExit: bool = False


class MistakeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    note: str | None = None


class MistakeDefinitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9_]+$")
    label: str = Field(min_length=1, max_length=120)


class SystemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    philosophy: str | None = None
    principles: list[str] = Field(default_factory=list)
    focusCode: str | None = None


class SizeRequest(BaseModel):
    """What the calculator needs. Nothing here can become an order."""

    model_config = ConfigDict(extra="forbid")

    symbol: str
    entry: float
    stop: float
    equity: float | None = None
    riskUsd: float | None = None
    riskPercent: float | None = None


class ReplayOpenedRequest(BaseModel):
    """Evidence that a closed trade was opened for review."""

    model_config = ConfigDict(extra="forbid")

    cid: str
    sessionId: str | None = None


class GradePreviewRequest(BaseModel):
    """What the HUD knows at ARM. Anything it cannot supply grades as unknown, never as failed."""

    model_config = ConfigDict(extra="forbid")

    cid: str = Field(max_length=32)
    sym: str = Field(max_length=16)
    side: Literal["buy", "sell"]
    lots: float = Field(gt=0)
    playbookId: str | None = Field(default=None, max_length=64)
    price: float | None = None
    ema20: float | None = None
    atr: float | None = None
    spread: float | None = None


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
            recorder.on_fill(
                cid=fact.cid, position_id=fact.position_id or 0, symbol=spec.name,
                side=fact.side or "buy", volume=fact.volume or 0, entry=fact.price or 0.0,
                ts_ms=fact.ts_ms or 0, prices=mid_prices(broker),
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


def _merge_manual(stored: dict, regraded: dict) -> dict:
    """Keep the ARM verdicts for the auto rules; take the manual ones from the checklist.

    Re-running the auto rules now would score the trade against a chart that has moved on, so the
    only thing the checklist is allowed to change is what the player answered.
    """
    import json as _json

    by_code = {r["code"]: r for r in stored["results"]}
    for result in regraded["results"]:
        if result["kind"] == "manual":
            by_code[result["code"]] = result
    results = list(by_code.values())

    answered = [r for r in results if r["required"] and not r["unknown"]]
    required_pass = sum(1 for r in answered if r["ok"])
    required_total = len(answered)
    payload = {
        **stored, "results": results, "required_pass": required_pass,
        "required_total": required_total,
        "clean": required_total > 0 and required_pass == required_total,
    }
    return {
        "payload": payload,
        "row": {
            "results": _json.dumps(results, sort_keys=True),
            "required_pass": required_pass,
            "required_total": required_total,
            "clean": int(payload["clean"]),
            "playbook_id": stored["playbook_id"],
        },
    }


def mid_prices(broker: Broker) -> dict[int, float]:
    """Mid prices keyed by symbol id, the shape `AssetGraph.quote_to_usd` reads.

    One builder for both callers — the fill path and the size calculator must price a quote the
    same way, or a trade would be sized against one rate and recorded against another.
    """
    quotes = getattr(broker, "quotes", None) or {}
    specs = getattr(broker, "specs", None) or {}
    mids = {name: quote.mid for name, quote in quotes.items()}
    return {spec.symbol_id: mids[spec.name] for spec in specs.values() if spec.name in mids}


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

    calendar = CalendarCache(
        cache_path=config.paths.data_dir_path / "calendar" / "ff_weekly.json",
        timezone=config.timezone,
        source=config.signals.calendar.source,
        fallback_path=Path(__file__).parent / "signals" / "calendar.yaml",
    )
    sentinel = SentinelEngine(
        timezone=config.timezone,
        spread_caps={s.name: s.max_spread for s in config.symbols if s.max_spread},
        calendar=calendar,
    )
    deck = build_deck(config)
    playbooks = PlaybookRepository(config.paths.db)
    replay = ReplayRepository(config.paths.db)
    journal_service = JournalService(
        config.paths.db, max_lots=max((s.max_lots for s in config.symbols), default=0.1),
    )
    attachments_dir = config.paths.data_dir_path / "attachments"
    score = ScoreRepository(
        config.paths.db,
        trades_max=config.score.trades_max,
        band_width=config.score.band_width,
        decline_credit_max=config.score.decline_credit_max,
        weights=dict(config.score.weights),
        r_unit_usd=config.risk.r_unit_usd,
        min_seconds_between_orders=config.risk.min_seconds_between_orders,
        # Both halves matter: the feature must be wanted *and* built. Phase 8 is deferred, so
        # `VOICE_CAPTURE_BUILT` is False and the memo sub-items drop out instead of failing.
        voice_available=config.voice.enabled and VOICE_CAPTURE_BUILT,
    )
    def _session_id_now() -> str:
        window = SessionWindow.from_config(
            config.timezone, config.session.days, config.session.start, config.session.end
        )
        return window.local(int(time.time() * 1000)).strftime("%Y-%m-%d")

    # One cell per process: the live socket writes it, the desk's read-only tool reads it.
    tilt_view: dict[str, object] = {"band": "calm", "score": 0.0, "top": []}
    desk = build_desk(config, sentinel, broker, deck, tilt_view, score, _session_id_now,
                      journal_service)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        applied = migrate(config.paths.db)
        if applied:
            log.info("applied migrations: %s", ", ".join(applied))
        seeded = playbooks.seed_if_empty(ts_ms=int(time.time() * 1000))
        if seeded:
            log.info("seeded %d starter playbooks", seeded)
        taxonomy = journal_service.seed_mistakes(int(time.time() * 1000))
        if taxonomy:
            log.info("seeded %d built-in mistakes", taxonomy)
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
    app.state.sentinel = sentinel
    app.state.desk = desk
    app.state.calendar = calendar
    app.state.deck = deck
    app.state.playbooks = playbooks
    app.state.replay = replay
    app.state.score = score
    app.state.journal_service = journal_service
    app.state.tv_guard = WebhookGuard(secret=os.environ.get(config.tradingview.webhook_secret_env, ""))
    app.state.last_tv_signal = None

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

    @app.get("/api/playbooks")
    def list_playbooks(include_retired: bool = False) -> dict[str, object]:
        """The book. Retired playbooks are hidden from selection but stay resolvable."""
        return {"playbooks": playbooks.list(include_retired=include_retired),
                "registry": registry_view()}

    @app.post("/api/playbooks")
    def save_playbook(body: PlaybookRequest) -> dict[str, object]:
        """Create or replace a playbook. A rule code the registry lacks is refused outright."""
        missing = unknown_codes(body.rules)
        if missing:
            raise HTTPException(status_code=422,
                                detail=f"unknown rule codes: {', '.join(missing)}")
        return {"playbook": playbooks.save(body, ts_ms=int(time.time() * 1000))}

    @app.post("/api/playbooks/{playbook_id}/retire")
    def retire_playbook(playbook_id: str) -> dict[str, object]:
        """Hide it from selection. Historical grades keep resolving, so the deck keeps its months."""
        if not playbooks.retire(playbook_id, ts_ms=int(time.time() * 1000)):
            raise HTTPException(status_code=404, detail="no such active playbook")
        return {"ok": True, "retired": playbook_id}

    @app.post("/api/playbooks/grade-preview")
    def grade_preview(body: GradePreviewRequest) -> dict[str, object]:
        """The grade the confirm overlay shows **before** the fire.

        Protocol v1 was frozen without an `intent.arm` message, so the pre-commit grade rides HTTP
        like the rest of the playbook surface rather than forcing a v2 migration. Nothing is
        persisted here — the socket still writes and pushes the authoritative `grade` at FIRE.
        """
        book = playbooks.get(body.playbookId) if body.playbookId else None
        setup = sentinel.tracker(body.sym).current
        now_ms = int(time.time() * 1000)
        symbol_cfg = next((s for s in config.symbols if s.name == body.sym), None)

        ctx = RuleContext(
            now_ms=now_ms, symbol=body.sym, lots=body.lots, clutch=True,
            session_open=True, session_label="",
            allowed_symbols=frozenset(s.name for s in config.symbols),
            positions_open=0, max_positions=config.risk.max_positions,
            max_lots=symbol_cfg.max_lots if symbol_cfg else 0.0,
            day_loss_usd=0.0, max_day_loss_usd=config.risk.max_daily_loss_usd,
            seconds_since_last_order=float("inf"),
            min_seconds_between_orders=config.risk.min_seconds_between_orders,
            heartbeat_age_s=0.0, heartbeat_dead_s=config.gateway.heartbeat_dead_s,
            setup_tag=setup.kind if setup else None,
            setup_side=setup.side if setup else None,
            side=body.side,
            price=body.price, ema20=body.ema20, atr=body.atr,
            spread=body.spread,
            spread_cap=symbol_cfg.max_spread if symbol_cfg else None,
        )
        grade = grade_fire(cid=body.cid, playbook=book, ctx=ctx, stage="arm")
        failure = grade.first_failure()
        return {
            "grade": grade.payload(),
            "playbookName": grade.playbook_name,
            "summary": grade.summary,
            "firstFailure": None if failure is None else failure.as_row(),
        }

    @app.post("/api/playbooks/checklist")
    def post_trade_checklist(body: ChecklistRequest) -> dict[str, object]:
        """The 3-tap checklist. Skipping leaves rules unknown, which costs the player nothing."""
        stored = playbooks.grade_for(body.cid)
        if stored is None:
            raise HTTPException(status_code=404, detail="no grade for that fire")

        book = None if stored["playbook_id"] is None else playbooks.get(stored["playbook_id"])
        # The chart context is gone by now, so the re-grade answers only what the player just
        # told us; every auto rule that needed live data stays unknown rather than being invented.
        ctx = RuleContext(
            now_ms=int(time.time() * 1000), symbol="", lots=0.0, clutch=True,
            session_open=True, session_label="", allowed_symbols=frozenset(),
            positions_open=0, max_positions=1, max_lots=0.0,
            day_loss_usd=0.0, max_day_loss_usd=0.0,
            seconds_since_last_order=0.0, min_seconds_between_orders=0.0,
            heartbeat_age_s=0.0, heartbeat_dead_s=1.0,
            manual_answers=dict(body.answers),
        )
        regraded = grade_fire(cid=body.cid, playbook=book, ctx=ctx, stage="fire")
        merged = _merge_manual(stored, regraded.payload())
        playbooks.save_grade({**regraded.as_db_row(), **merged["row"]})
        return {"ok": True, "grade": merged["payload"]}

    @app.get("/api/deck/summary")
    def deck_summary() -> dict[str, object]:
        """Process figures the HUD and the desk may read. Deliberately money-free."""
        return deck.summary()

    @app.get("/api/deck/process")
    def deck_process() -> dict[str, object]:
        """The default panel: adherence, declined trades, opportunity quality, check-ins."""
        return deck.process()

    @app.get("/api/deck/outcome")
    def deck_outcome() -> dict[str, object]:
        """The second tab. Reached by a deliberate click, never linked from the process panel."""
        return deck.outcome()

    @app.get("/api/replay/index")
    def replay_index(from_ms: int | None = None, to_ms: int | None = None) -> dict[str, object]:
        """The trade list LB/RB step through. Same origin, same token as the deck."""
        return replay.index(from_ms=from_ms, to_ms=to_ms)

    @app.get("/api/replay/{cid}")
    def replay_trade(cid: str) -> dict[str, object]:
        """One trade's window: bars, events, the closed-trade facts and its grade.

        A trade with no tape still answers 200 with `tape: null` — the client falls back to the
        marker-only view rather than blanking on a pre-phase-2 trade.
        """
        body = replay.trade(cid)
        if body is None:
            raise HTTPException(status_code=404, detail="no such trade")
        return body

    @app.get("/api/deck/playbooks")
    def deck_playbooks() -> dict[str, object]:
        """Per-playbook record, process figures only. n and adherence, no money."""
        return deck.playbooks(outcome=False)

    @app.get("/api/deck/playbooks/outcome")
    def deck_playbooks_outcome() -> dict[str, object]:
        """The same table with expectancy, excursions and efficiency, behind the deliberate click."""
        return deck.playbooks(outcome=True)

    @app.get("/api/deck/tilt/{session_id}")
    def deck_tilt_retro(session_id: str) -> dict[str, object]:
        """Tilt as a retrospective: bands over the evening, against adherence, never against P/L."""
        return deck.tilt_retro(session_id)

    @app.get("/api/score/session/{session_id}")
    def score_session_route(session_id: str) -> dict[str, object]:
        """One evening's five axes and its total, always recomputed from the stored inputs.

        Recomputing rather than reading the total back is what makes a `score.weights` change show
        up on every historical evening instead of mixing two weightings in one chart.
        """
        return score.session_payload(session_id)

    @app.get("/api/score/month")
    def score_month() -> dict[str, object]:
        """The score's distribution by month, with n. Never a streak, never a `days since`."""
        return score.month()

    @app.post("/api/score/evidence/replay")
    def score_replay_evidence(body: ReplayOpenedRequest) -> dict[str, object]:
        """Records that a trade was reviewed. The Review axis credits it.

        This lives on the score surface rather than on `/api/replay/*` deliberately: replay itself
        stays a read, and the write that says "you reviewed this" belongs to the thing doing the
        scoring.
        """
        journal = JournalWriter(connect(config.paths.db))
        try:
            journal.write_review_event(body.sessionId or session_id_now(), kind="replay_open",
                                       cid=body.cid, ts_ms=int(time.time() * 1000))
            journal.conn.commit()
        finally:
            journal.conn.close()
        return {"ok": True}

    # -- journal cockpit (phase 12) --------------------------------------------------
    #
    # Plain same-origin HTTP behind the existing token, like every other non-realtime surface.
    # Every write below targets a review table; nothing here can reach a fill or an execution event.

    @app.get("/api/journal/today")
    def journal_today(session_id: str | None = None) -> dict[str, object]:
        """The prepare-and-land page. Defaults to tonight."""
        return journal_service.today(session_id or session_id_now())

    @app.put("/api/journal/today")
    def journal_put_today(body: TodayRequest) -> dict[str, object]:
        """Readiness and the daily analysis. Advisory: neither has ever blocked an unlock."""
        session_id = body.sessionId or session_id_now()
        stamp = int(time.time() * 1000)
        if body.readiness is not None:
            journal_service.put_readiness(session_id, body.readiness, stamp)
        if body.analysis is not None:
            journal_service.put_analysis(session_id, body.analysis, stamp)
        return journal_service.today(session_id)

    @app.get("/api/journal/overview")
    def journal_overview(from_ms: int | None = None, to_ms: int | None = None) -> dict[str, object]:
        """The dashboard. Process first — the money lives behind the deck's Outcome tab."""
        return journal_service.overview(from_ms=from_ms, to_ms=to_ms)

    @app.get("/api/journal/days")
    def journal_days(from_ms: int | None = None, to_ms: int | None = None) -> dict[str, object]:
        """The heatmap, coloured by Process Score and activity."""
        return journal_service.days(from_ms=from_ms, to_ms=to_ms)

    @app.get("/api/journal/day/{session_id}")
    def journal_day(session_id: str) -> dict[str, object]:
        return journal_service.day(session_id)

    @app.get("/api/journal/history")
    def journal_history(
        page: int = 0, size: int = DEFAULT_PAGE, from_ms: int | None = None,
        to_ms: int | None = None, playbook: str | None = None, setup: str | None = None,
        symbol: str | None = None, timeframe: str | None = None, side: str | None = None,
        market_session: str | None = None, intent: str | None = None, mistake: str | None = None,
        result: str | None = None,
    ) -> dict[str, object]:
        """Every dimension, combinable, parameterised and paginated."""
        filters = {name: value for name, value in locals().items() if name in HISTORY_FILTERS}
        return journal_service.history(filters, page=max(0, page), size=size)

    @app.get("/api/journal/trade/{cid}")
    def journal_trade(cid: str) -> dict[str, object]:
        """The immutable record, then everything reviewed on top of it."""
        body = journal_service.trade(cid)
        if body is None:
            raise HTTPException(status_code=404, detail="no such trade")
        return body

    @app.put("/api/journal/trade/{cid}")
    def journal_put_trade(cid: str, body: TradeReviewRequest) -> dict[str, object]:
        """Annotate a trade. `impulsive` and `revenge` only ever arrive from here, never derived."""
        try:
            journal_service.put_review(cid, body.model_dump(), int(time.time() * 1000))
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return journal_service.trade(cid) or {}

    @app.post("/api/journal/trade/{cid}/mistakes")
    def journal_add_mistake(cid: str, body: MistakeRequest) -> dict[str, object]:
        journal_service.add_mistake(cid, body.code, int(time.time() * 1000), body.note)
        return {"ok": True}

    @app.delete("/api/journal/trade/{cid}/mistakes/{code}")
    def journal_remove_mistake(cid: str, code: str) -> dict[str, object]:
        """Withdraws a judgement. A derived mistake returns on the next sync — it is a fact."""
        journal_service.remove_mistake(cid, code)
        return {"ok": True}

    @app.post("/api/journal/trade/{cid}/mistakes/sync")
    def journal_sync_mistakes(cid: str) -> dict[str, object]:
        return {"derived": journal_service.sync_mistakes(cid, int(time.time() * 1000))}

    @app.get("/api/journal/mistakes")
    def journal_taxonomy() -> dict[str, object]:
        return journal_service.taxonomy()

    @app.post("/api/journal/mistakes")
    def journal_define_mistake(body: MistakeDefinitionRequest) -> dict[str, object]:
        journal_service.define_mistake(body.code, body.label, int(time.time() * 1000))
        return journal_service.taxonomy()

    @app.get("/api/journal/system")
    def journal_system() -> dict[str, object]:
        return journal_service.system()

    @app.put("/api/journal/system")
    def journal_put_system(body: SystemRequest) -> dict[str, object]:
        journal_service.put_system(body.model_dump(), int(time.time() * 1000))
        return journal_service.system()

    @app.post("/api/journal/size")
    def journal_size(body: SizeRequest) -> dict[str, object]:
        """Position sizing through phase 2's own conversion and the broker's volume step.

        Applying the answer changes the HUD's preview only. LT+RT is still the only thing that
        trades, and this route has no path to an order.
        """
        spec = _spec_for(body.symbol)
        if spec is None:
            raise HTTPException(status_code=404, detail=f"no spec for {body.symbol}")
        symbol_cfg = next((s for s in config.symbols if s.name == body.symbol), None)
        return size_position(
            spec=spec, entry=body.entry, stop=body.stop, equity=body.equity,
            risk_usd=body.riskUsd, risk_percent=body.riskPercent,
            graph=getattr(broker, "graph", None), prices=mid_prices(broker),
            ts_ms=int(time.time() * 1000),
            max_lots=symbol_cfg.max_lots if symbol_cfg else None,
        ).payload()

    def _spec_for(symbol: str):
        """The broker's own spec, which is the only source that knows the real volume step."""
        specs = getattr(broker, "specs", None) or {}
        return specs.get(symbol)

    @app.post("/api/journal/attachments")
    async def journal_attach(request: Request, session_id: str | None = None,
                             cid: str | None = None, label: str | None = None) -> dict[str, object]:
        """A chart screenshot, as a raw image body.

        The client never names the file: the server reads the magic bytes, generates a ULID, and
        writes that. A client-supplied name is stored as a label and never becomes a path.
        """
        data = await request.body()
        try:
            attachment = store(data, directory=attachments_dir)
        except AttachmentError as exc:
            raise HTTPException(status_code=415, detail=str(exc)) from exc
        journal_service.record_attachment(
            attachment_id=attachment.id, mime=attachment.mime, size=attachment.bytes,
            width=attachment.width, height=attachment.height,
            session_id=session_id or (None if cid else session_id_now()), cid=cid, label=label,
            ts_ms=int(time.time() * 1000),
        )
        return {"id": attachment.id, "mime": attachment.mime, "bytes": attachment.bytes,
                "width": attachment.width, "height": attachment.height,
                "usage": usage(attachments_dir)}

    @app.get("/api/journal/attachments/{attachment_id}")
    def journal_attachment(attachment_id: str) -> Response:
        """Resolved from the row, never from the URL."""
        row = journal_service.attachment(attachment_id)
        if row is None:
            raise HTTPException(status_code=404, detail="no such attachment")
        extension = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}[row["mime"]]
        try:
            path = path_for(attachment_id, extension, directory=attachments_dir)
        except AttachmentError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        if not path.exists():
            raise HTTPException(status_code=404, detail="the file is gone")
        return Response(content=path.read_bytes(), media_type=row["mime"])

    @app.post("/hooks/tv")
    def tradingview_webhook(alert: TvAlert) -> dict[str, object]:
        """A VIP alert becomes a hint on the desk. It can never become an order.

        The route is public because TradingView posts to it, so it is rate limited before the
        secret is compared, and the secret is compared in constant time.
        """
        guard: WebhookGuard = app.state.tv_guard
        if not guard.allow():
            raise HTTPException(status_code=429, detail="slow down")
        if not guard.verify(alert.secret):
            raise HTTPException(status_code=401, detail="bad secret")
        if not config.tradingview.enabled:
            raise HTTPException(status_code=404, detail="tradingview intake is off")

        signal = to_signal(alert, ts_ms=int(time.time() * 1000))
        app.state.last_tv_signal = signal
        return {"ok": True, "signal": signal}

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
        opportunity = OpportunitySampler()
        tilt = TiltTracker(
            bands=Bands(warm=config.tilt.warm, hot=config.tilt.hot,
                        scorched=config.tilt.scorched),
            baseline=load_baseline(config.paths.db),
            cooldown_s=config.tilt.cooldown_s,
            enabled=config.tilt.enabled,
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
            desk=desk,
            sentinel=sentinel,
            playbooks=playbooks,
            tilt=tilt,
            tilt_view=tilt_view,
            opportunity=opportunity,
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
            # The Process Score is computed at close and nowhere else. A number you can watch
            # mid-trade becomes the anxiety the P/L used to be, so there is no live one to watch.
            try:
                journal.write_opportunity_quality(session_id, opportunity.mean)
                journal.conn.commit()
                score.write(session_id)
            except Exception:
                log.exception("session score failed; the evening's rows are still intact")
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
