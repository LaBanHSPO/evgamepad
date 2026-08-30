"""Protocol v1 message catalog — the single source of truth for every ``t``.

The web app's TypeScript types are generated from this catalog's JSON Schema
(``export_schema.py``), so a change here that is not regenerated fails the web
build rather than drifting silently.

Phases 7-14 (playbook, voice, tilt, replay, score) are declared here and
implemented later. That is deliberate: the catalog is frozen in phase 1.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from .envelope import Channel, Cid

Side = Literal["buy", "sell"]
Symbol = Literal["XAUUSD", "EURUSD", "GBPUSD", "USDJPY"]
Timeframe = Literal["M1", "M5", "M15", "H1", "H4", "D1"]

#: Every reason the gateway may refuse an intent. ``cooldown`` is reserved by
#: phase 1 for phase 9's tilt friction so adding it later is not a v2 change.
RejectReason = Literal[
    "not_wired",
    "no_clutch",
    "stale_arm",
    "duplicate_cid",
    "locked",
    "session_closed",
    "dead_man",
    "max_positions",
    "max_daily_loss",
    "max_lots",
    "lot_step",
    "unknown_symbol",
    "spread_too_wide",
    "rate_limited",
    "cooldown",
    "broker_error",
    "broker_down",
]


class Msg(BaseModel):
    """Base for every payload. ``extra='forbid'`` keeps an unknown field a
    protocol error instead of a silently ignored one."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


# ---------------------------------------------------------------------------
# Client -> server
# ---------------------------------------------------------------------------


class Hello(Msg):
    token: str
    lastSeq: int = Field(default=0, ge=0)
    protocolVersion: int = 1
    ua: str | None = None


class Ping(Msg):
    #: Dead-man only. A fire is authorised by ``intent.*.clutch``, never by this.
    clutch: bool = False
    padSeq: int | None = None


class Sub(Msg):
    ch: Channel
    syms: list[Symbol] = Field(default_factory=list)
    tf: Timeframe | None = None


class Resync(Msg):
    fromSeq: int = Field(ge=0)


class Snap(Msg):
    what: list[Literal["pos", "pnl", "session", "risk", "playbook", "tilt"]] = Field(
        default_factory=list
    )


class _Confirmed(Msg):
    """Every broker-changing intent carries the same clutch+confirm evidence."""

    clutch: Literal[True]
    armedAt: int = Field(ge=0, description="Unix ms the pad entered ARM")


class IntentOpen(_Confirmed):
    sym: Symbol
    side: Side
    type: Literal["market"] = "market"
    lots: float = Field(gt=0)
    #: cTrader relative distance units (1/100000). MARKET orders carry no
    #: absolute stopLoss/takeProfit -- see intent.modify for those.
    relativeSl: int | None = Field(default=None, gt=0)
    relativeTp: int | None = Field(default=None, gt=0)


class IntentClose(_Confirmed):
    positionId: int


class IntentModify(_Confirmed):
    """Absolute SL/TP on an existing position. Broker-changing, so it needs the
    same gate as an open."""

    positionId: int
    sl: float | None = None
    tp: float | None = None


class IntentPanic(_Confirmed):
    """Flatten every position, then lock."""


class SessionLock(Msg):
    pass


class SessionUnlock(Msg):
    pass


class AiAsk(Msg):
    kind: Literal["research", "plan", "advise", "news", "coach"]
    sym: Symbol | None = None
    tf: Timeframe | None = None


class PadTelemetry(Msg):
    """1 Hz batch, never per-frame. Phase 9 consumes it; phase 1 freezes it."""

    ts: int = Field(ge=0)
    from_: str | None = Field(default=None, alias="from")
    to: str | None = None
    sym: Symbol | None = None
    lots: float | None = None
    reason: str | None = None
    clutchMs: int = 0
    armMs: int = 0
    clutchCycles: int = 0
    armFlips: int = 0
    btnRateHz: float = 0.0
    lotStepsSince: int = 0
    ttfMs: int | None = None


class VoiceBegin(Msg):
    voiceId: Cid
    cid: Cid | None = None


class VoiceCancel(Msg):
    voiceId: Cid


class JournalMemoLink(Msg):
    voiceId: Cid
    cid: Cid


class GradeAnswer(Msg):
    cid: Cid
    ruleId: str
    answer: bool


class PlaybookSelect(Msg):
    playbookId: str


# ---------------------------------------------------------------------------
# Server -> client
# ---------------------------------------------------------------------------


class Welcome(Msg):
    sessionId: str
    seq: int = Field(ge=0)
    serverTs: int
    protocolVersion: int = 1
    tz: str
    symbols: list[Symbol]
    resumed: bool = False
    features: dict[str, bool] = Field(default_factory=dict)


class Pong(Msg):
    clutch: bool = False
    serverTs: int


class Quote(Msg):
    sym: Symbol
    bid: float
    ask: float
    ts: int
    digits: int


class Candle(Msg):
    sym: Symbol
    tf: Timeframe
    ts: int
    o: float
    h: float
    l: float
    c: float
    closed: bool = False


class OrderAck(Msg):
    cid: Cid
    sym: Symbol
    side: Side
    lots: float
    price: float
    ts: int
    orderId: int | None = None
    positionId: int | None = None


class OrderReject(Msg):
    cid: Cid | None = None
    reason: RejectReason
    detail: str | None = None


class OrderUpd(Msg):
    cid: Cid | None = None
    orderId: int | None = None
    positionId: int | None = None
    status: Literal["filled", "closed", "amended", "cancelled", "expired"]
    ts: int
    detail: str | None = None


class Position(Msg):
    positionId: int
    sym: Symbol
    side: Side
    lots: float
    entry: float
    sl: float | None = None
    tp: float | None = None
    openedAt: int
    pnl: float = 0.0
    rMultiple: float | None = None


class PosSnap(Msg):
    ts: int
    positions: list[Position] = Field(default_factory=list)


class Pnl(Msg):
    ts: int
    balance: float
    equity: float
    openPnl: float = 0.0
    dayPnl: float = 0.0


class SessionState(Msg):
    state: Literal["closed", "open", "locked", "cooldown"]
    opensAllowed: bool
    tz: str
    reason: str | None = None
    startsAt: int | None = None
    endsAt: int | None = None


class RiskState(Msg):
    locked: bool
    reasons: list[RejectReason] = Field(default_factory=list)
    positions: int = 0
    maxPositions: int = 1
    dayLossUsd: float = 0.0
    maxDailyLossUsd: float = 0.0


class SentinelTick(Msg):
    ts: int
    sym: Symbol
    spread: float
    spreadOk: bool
    sessionOk: bool
    newsOk: bool
    band: Literal["green", "amber", "red"]


class NewsItem(Msg):
    id: str
    ts: int
    title: str
    impact: Literal["low", "medium", "high"]
    currency: str
    sym: Symbol | None = None


class SignalItem(Msg):
    """TradingView webhook. Advisory only -- ``auto_trade`` is a boot-fail."""

    id: str
    ts: int
    source: Literal["tradingview"] = "tradingview"
    sym: Symbol
    tf: Timeframe | None = None
    text: str


class AiAdvice(Msg):
    kind: Literal["research", "plan", "advise", "news", "coach"]
    ts: int
    text: str = ""
    disabled: bool = False


class ErrorMsg(Msg):
    reason: str
    detail: str | None = None


class Maint(Msg):
    reason: str
    detail: str | None = None
    until: int | None = None


class VoiceTranscript(Msg):
    voiceId: Cid
    ok: bool
    cid: Cid | None = None
    text: str | None = None
    reason: str | None = None
    durMs: int = 0
    sttMs: int = 0


class VoiceStateMsg(Msg):
    busy: bool = False
    queued: int = 0


class TiltMsg(Msg):
    score: float = Field(ge=0.0, le=1.0)
    band: Literal["cool", "warm", "hot", "scorched"]
    top: list[str] = Field(default_factory=list)
    cooldownUntil: int | None = None


class GradeResult(Msg):
    ruleId: str
    required: bool
    passed: bool | None = None
    note: str | None = None


class GradeMsg(Msg):
    cid: Cid
    playbookId: str
    required_pass: int = 0
    required_total: int = 0
    clean: bool = False
    results: list[GradeResult] = Field(default_factory=list)


class PlaybookSummary(Msg):
    playbookId: str
    name: str
    ruleCount: int
    requiredCount: int


class PlaybookList(Msg):
    playbooks: list[PlaybookSummary] = Field(default_factory=list)


class ScoreSession(Msg):
    axes: dict[str, float] = Field(default_factory=dict)
    total: float = 0.0
    na: list[str] = Field(default_factory=list)
    weightsVersion: str = "1"


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

Direction = Literal["c2s", "s2c"]


class Spec(BaseModel):
    model_config = ConfigDict(frozen=True)

    t: str
    ch: Channel
    dir: Direction
    model: type[Msg]


def _spec(t: str, ch: Channel, direction: Direction, model: type[Msg]) -> Spec:
    return Spec(t=t, ch=ch, dir=direction, model=model)


_SPECS: tuple[Spec, ...] = (
    # client -> server
    _spec("hello", "session", "c2s", Hello),
    _spec("ping", "session", "c2s", Ping),
    _spec("sub", "session", "c2s", Sub),
    _spec("resync", "session", "c2s", Resync),
    _spec("snap", "session", "c2s", Snap),
    _spec("intent.open", "orders", "c2s", IntentOpen),
    _spec("intent.close", "orders", "c2s", IntentClose),
    _spec("intent.modify", "orders", "c2s", IntentModify),
    _spec("intent.panic", "orders", "c2s", IntentPanic),
    _spec("session.lock", "session", "c2s", SessionLock),
    _spec("session.unlock", "session", "c2s", SessionUnlock),
    _spec("ai.ask", "ai", "c2s", AiAsk),
    _spec("pad.telemetry", "session", "c2s", PadTelemetry),
    _spec("voice.begin", "voice", "c2s", VoiceBegin),
    _spec("voice.cancel", "voice", "c2s", VoiceCancel),
    _spec("journal.memo.link", "voice", "c2s", JournalMemoLink),
    _spec("grade.answer", "session", "c2s", GradeAnswer),
    _spec("playbook.select", "session", "c2s", PlaybookSelect),
    # server -> client
    _spec("welcome", "session", "s2c", Welcome),
    _spec("pong", "session", "s2c", Pong),
    _spec("quote", "quotes", "s2c", Quote),
    _spec("candle", "quotes", "s2c", Candle),
    _spec("order.ack", "orders", "s2c", OrderAck),
    _spec("order.reject", "orders", "s2c", OrderReject),
    _spec("order.upd", "orders", "s2c", OrderUpd),
    _spec("pos.snap", "orders", "s2c", PosSnap),
    _spec("pnl", "orders", "s2c", Pnl),
    _spec("session", "session", "s2c", SessionState),
    _spec("risk", "session", "s2c", RiskState),
    _spec("sentinel.tick", "ai", "s2c", SentinelTick),
    _spec("news.item", "ai", "s2c", NewsItem),
    _spec("signal.item", "ai", "s2c", SignalItem),
    _spec("ai.advice", "ai", "s2c", AiAdvice),
    _spec("error", "session", "s2c", ErrorMsg),
    _spec("maint", "session", "s2c", Maint),
    _spec("voice.transcript", "voice", "s2c", VoiceTranscript),
    _spec("voice.state", "voice", "s2c", VoiceStateMsg),
    _spec("tilt", "session", "s2c", TiltMsg),
    _spec("grade", "session", "s2c", GradeMsg),
    _spec("playbook.list", "session", "s2c", PlaybookList),
    _spec("score.session", "session", "s2c", ScoreSession),
)

CATALOG: dict[str, Spec] = {s.t: s for s in _SPECS}

#: Intents are the only messages that can change the broker's state.
INTENT_TYPES: frozenset[str] = frozenset(
    {"intent.open", "intent.close", "intent.modify", "intent.panic"}
)

#: Exempt from every open-only gate (dead-man, tilt cooldown, daily loss).
#: Asserted by tests so a later phase cannot quietly gate a safety exit.
SAFETY_EXIT_TYPES: frozenset[str] = frozenset({"intent.close", "intent.panic"})


def spec_for(t: str) -> Spec:
    try:
        return CATALOG[t]
    except KeyError:
        raise KeyError(t) from None


def model_for(t: str) -> type[Msg]:
    return spec_for(t).model


def types_for(direction: Direction) -> tuple[str, ...]:
    return tuple(s.t for s in _SPECS if s.dir == direction)


def json_schema() -> dict[str, Any]:
    """The whole catalog as one JSON Schema document, for TS type generation."""
    from .envelope import CHANNELS, MAX_FRAME_BYTES, PROTOCOL_VERSION

    defs: dict[str, Any] = {}
    messages: dict[str, Any] = {}
    for s in _SPECS:
        schema = s.model.model_json_schema(
            ref_template="#/$defs/{model}", by_alias=True
        )
        defs.update(schema.pop("$defs", {}))
        defs[s.model.__name__] = schema
        messages[s.t] = {
            "channel": s.ch,
            "direction": s.dir,
            "payload": {"$ref": f"#/$defs/{s.model.__name__}"},
        }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "ev-gateway protocol v1",
        "protocolVersion": PROTOCOL_VERSION,
        "maxFrameBytes": MAX_FRAME_BYTES,
        "channels": list(CHANNELS),
        "messages": messages,
        "$defs": defs,
    }
