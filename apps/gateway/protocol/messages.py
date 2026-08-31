"""Frozen protocol v1 message catalog.

Every message the game socket will ever carry in v1 is declared here, including the journal
layer (phases 7-14) whose implementations are deferred. Declaring them now costs a few models;
adding them later would be a v2 migration for a client that is already deployed.

Wire field names follow the plan verbatim, which mixes camelCase (`relativeSl`) with snake_case
(`required_pass`). The contract is frozen as written rather than tidied, so the generated TS
types and the HUD agree with the plan documents.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from .envelope import Channel

Direction = Literal["c2s", "s2c"]


class Message(BaseModel):
    """Base for every payload: unknown fields are a contract violation, not a warning."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


# --------------------------------------------------------------------------------------
# Client -> VPS
# --------------------------------------------------------------------------------------


class Hello(Message):
    """Opens a socket. `lastSeq` asks the gateway to replay from where the client dropped."""

    token: str
    lastSeq: int | None = Field(default=None, ge=0)
    clientVersion: str | None = None


class Ping(Message):
    """1 Hz heartbeat. The clutch here is dead-man only — it can lock opens, never a close."""

    visible: bool
    pad: bool
    clutch: bool


class Sub(Message):
    """Subscribe to symbols on a channel."""

    ch: Channel
    syms: list[str] = Field(default_factory=list)


class Resync(Message):
    """Ask for missed frames after a reconnect."""

    lastSeq: int = Field(ge=0)


class Snap(Message):
    """Ask for a full state snapshot instead of a delta replay."""

    what: Literal["positions", "session", "all"] = "all"


class IntentOpen(Message):
    """MARKET open. Protection is *relative* — cTrader rejects absolute SL/TP on market orders."""

    sym: str
    side: Literal["buy", "sell"]
    type: Literal["market"] = "market"
    lots: float = Field(gt=0)
    relativeSl: int | None = Field(default=None, gt=0, description="1/100000 price distance")
    relativeTp: int | None = Field(default=None, gt=0, description="1/100000 price distance")
    clutch: Literal[True]
    armedAt: int = Field(ge=0, description="Unix ms the pad reached ARM")


class IntentClose(Message):
    """Full close. Never gated by tilt, cooldown, or any open-only rule."""

    positionId: int
    clutch: Literal[True]
    armedAt: int = Field(ge=0)


class IntentModify(Message):
    """Absolute SL/TP on an existing position — broker-changing, so same clutch+confirm gate."""

    positionId: int
    sl: float | None = None
    tp: float | None = None
    clutch: Literal[True]
    armedAt: int = Field(ge=0)


class IntentPanic(Message):
    """Flatten everything. Exempt from every open-only gate, by design and by test."""

    clutch: Literal[True]
    armedAt: int = Field(ge=0)


class SessionLock(Message):
    """Player stands down for the evening."""

    reason: str | None = None


class SessionUnlock(Message):
    """Release a self-imposed lock."""

    reason: str | None = None


class AiAsk(Message):
    """Desk request. Off the order hot path, always."""

    kind: Literal["research", "plan", "advise", "news", "coach"]
    sym: str | None = None
    tf: str | None = None


class PadTelemetry(Message):
    """1 Hz batch, never per-frame. An idle heartbeat still reports the FSM state pair."""

    ts: int = Field(ge=0)
    from_: str = Field(alias="from")
    to: str
    sym: str | None = None
    lots: float | None = None
    reason: str | None = None
    clutchMs: int = Field(ge=0)
    armMs: int = Field(ge=0)
    clutchCycles: int = Field(ge=0)
    armFlips: int = Field(ge=0)
    btnRateHz: float = Field(ge=0)
    lotStepsSince: int = Field(ge=0)
    ttfMs: int | None = Field(default=None, ge=0, description="Time to fire, ARM -> FIRE")


class VoiceBegin(Message):
    """Client started recording a memo. Audio itself uploads over HTTP, not this socket."""

    voiceId: str
    cid: str | None = None


class VoiceCancel(Message):
    """Abandon an in-flight memo."""

    voiceId: str


class JournalMemoLink(Message):
    """Attach a finished memo to a trade after the fact."""

    voiceId: str
    cid: str


class GradeAnswer(Message):
    """Player's answer to one playbook grading question."""

    cid: str
    ruleId: str
    answer: bool


class PlaybookSelect(Message):
    """Choose the setup being traded, before the fire."""

    playbookId: str
    cid: str | None = None


# --------------------------------------------------------------------------------------
# VPS -> client
# --------------------------------------------------------------------------------------


class Welcome(Message):
    """Accepted socket. `resumed` tells the HUD whether it replayed or started clean."""

    seq: int = Field(ge=0)
    serverTime: int = Field(ge=0)
    resumed: bool = False
    mode: Literal["demo"] = "demo"


class Pong(Message):
    """Heartbeat reply. Round-trip feeds the HUD's link indicator."""

    ts: int = Field(ge=0)


class Quote(Message):
    """Conflated bid/ask, 10-20 Hz. Sourced from cTrader spots, never synthesised."""

    sym: str
    bid: float
    ask: float
    ts: int = Field(ge=0)


class Candle(Message):
    """M5 trendbar."""

    sym: str
    tf: str
    o: float
    h: float
    low: float = Field(alias="l")
    c: float
    ts: int = Field(ge=0)


class OrderAck(Message):
    """Broker accepted the intent carrying this `cid`."""

    cid: str
    orderId: int | None = None
    positionId: int | None = None
    sym: str
    side: Literal["buy", "sell"]
    lots: float
    price: float | None = None
    ts: int = Field(ge=0)


class OrderReject(Message):
    """Refused by risk or by the broker. `cooldown` is reserved for phase 9."""

    cid: str
    reason: str
    detail: str | None = None
    ts: int = Field(ge=0)


class OrderUpd(Message):
    """Lifecycle update on a known order: partial fill, amendment, close."""

    cid: str | None = None
    orderId: int | None = None
    positionId: int | None = None
    state: str
    ts: int = Field(ge=0)


class PosSnap(Message):
    """Authoritative position list. cTrader is the source of truth, not local accounting."""

    positions: list[dict[str, Any]] = Field(default_factory=list)
    ts: int = Field(ge=0)


class Pnl(Message):
    """Account figures pulled from the broker, never re-derived from summed fills."""

    balance: float
    equity: float
    openPnl: float
    dayPnl: float | None = None
    ts: int = Field(ge=0)


class SessionState(Message):
    """Trading window, lock state, and why the gateway is or is not accepting opens."""

    open: bool
    locked: bool
    reason: str | None = None
    startsAt: int | None = None
    endsAt: int | None = None


class RiskState(Message):
    """Live view of the enforced gates, so the HUD can grey a control before it is pressed."""

    maxLots: float
    maxPositions: int
    positions: int
    dayLossUsd: float
    maxDayLossUsd: float
    blocked: list[str] = Field(default_factory=list)


class SentinelTick(Message):
    """Cheap local market-state paint. Never waits on the AI provider."""

    sym: str
    spread: float
    state: str
    ts: int = Field(ge=0)


class NewsItem(Message):
    """Cited headline from the allowlisted domains. Rendered as text, never as raw HTML."""

    id: str
    title: str
    url: str
    source: str
    ts: int = Field(ge=0)


class SignalItem(Message):
    """Volman detector hit, or a TradingView webhook. `tv` can never auto-trade."""

    id: str
    kind: Literal["volman", "tv"]
    sym: str
    text: str
    ts: int = Field(ge=0)


class AiAdvice(Message):
    """Desk answer. Advisory only — it holds no order tool."""

    cid: str | None = None
    kind: Literal["research", "plan", "advise", "news", "coach"]
    text: str
    citations: list[str] = Field(default_factory=list)
    ts: int = Field(ge=0)


class ErrorMsg(Message):
    """Protocol or handler failure the client should surface, not swallow."""

    code: str
    message: str
    cid: str | None = None


class Maint(Message):
    """Broker or gateway maintenance window; the HUD stops offering opens."""

    active: bool
    until: int | None = None
    note: str | None = None


class VoiceTranscript(Message):
    """Result of one whisper.cpp run. `ok=false` still keeps the audio linked to the trade."""

    voiceId: str
    cid: str | None = None
    ok: bool
    text: str | None = None
    reason: str | None = None
    durMs: int = Field(ge=0)
    sttMs: int = Field(ge=0)


class VoiceState(Message):
    """STT concurrency is 1; this is how the HUD shows the queue."""

    busy: bool
    queued: int = Field(ge=0)


class Tilt(Message):
    """Tilt band and its top drivers. May add friction to opens; may never gate a close."""

    score: float = Field(ge=0, le=1)
    band: Literal["calm", "warm", "hot", "scorched"]
    top: list[str] = Field(default_factory=list)
    cooldownUntil: int | None = None


class Grade(Message):
    """Playbook grading for one fire. Graded after the fact; it never blocks the fire."""

    cid: str
    playbookId: str
    required_pass: int = Field(ge=0)
    required_total: int = Field(ge=0)
    clean: bool
    results: list[dict[str, Any]] = Field(default_factory=list)


class PlaybookList(Message):
    """Available setups, seeded from the Volman profile plus any custom ones."""

    playbooks: list[dict[str, Any]] = Field(default_factory=list)


class ScoreSession(Message):
    """Process score. A vacuous axis lands in `na` and its weight is redistributed, not zeroed."""

    axes: dict[str, float] = Field(default_factory=dict)
    total: float = Field(ge=0, le=100)
    na: list[str] = Field(default_factory=list)
    weightsVersion: str


# --------------------------------------------------------------------------------------
# Catalog
# --------------------------------------------------------------------------------------


class CatalogEntry(BaseModel):
    """One frozen message type: its direction, its channel, and the model that validates it."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    t: str
    direction: Direction
    ch: Channel
    model: type[Message]


def _entry(t: str, direction: Direction, ch: Channel, model: type[Message]) -> CatalogEntry:
    return CatalogEntry(t=t, direction=direction, ch=ch, model=model)


CATALOG: dict[str, CatalogEntry] = {
    e.t: e
    for e in (
        # client -> VPS
        _entry("hello", "c2s", "session", Hello),
        _entry("ping", "c2s", "session", Ping),
        _entry("sub", "c2s", "session", Sub),
        _entry("resync", "c2s", "session", Resync),
        _entry("snap", "c2s", "session", Snap),
        _entry("intent.open", "c2s", "orders", IntentOpen),
        _entry("intent.close", "c2s", "orders", IntentClose),
        _entry("intent.modify", "c2s", "orders", IntentModify),
        _entry("intent.panic", "c2s", "orders", IntentPanic),
        _entry("session.lock", "c2s", "session", SessionLock),
        _entry("session.unlock", "c2s", "session", SessionUnlock),
        _entry("ai.ask", "c2s", "ai", AiAsk),
        _entry("pad.telemetry", "c2s", "session", PadTelemetry),
        _entry("voice.begin", "c2s", "voice", VoiceBegin),
        _entry("voice.cancel", "c2s", "voice", VoiceCancel),
        _entry("journal.memo.link", "c2s", "voice", JournalMemoLink),
        _entry("grade.answer", "c2s", "session", GradeAnswer),
        _entry("playbook.select", "c2s", "session", PlaybookSelect),
        # VPS -> client
        _entry("welcome", "s2c", "session", Welcome),
        _entry("pong", "s2c", "session", Pong),
        _entry("quote", "s2c", "quotes", Quote),
        _entry("candle", "s2c", "quotes", Candle),
        _entry("order.ack", "s2c", "orders", OrderAck),
        _entry("order.reject", "s2c", "orders", OrderReject),
        _entry("order.upd", "s2c", "orders", OrderUpd),
        _entry("pos.snap", "s2c", "orders", PosSnap),
        _entry("pnl", "s2c", "session", Pnl),
        _entry("session", "s2c", "session", SessionState),
        _entry("risk", "s2c", "session", RiskState),
        _entry("sentinel.tick", "s2c", "ai", SentinelTick),
        _entry("news.item", "s2c", "ai", NewsItem),
        _entry("signal.item", "s2c", "ai", SignalItem),
        _entry("ai.advice", "s2c", "ai", AiAdvice),
        _entry("error", "s2c", "session", ErrorMsg),
        _entry("maint", "s2c", "session", Maint),
        _entry("voice.transcript", "s2c", "voice", VoiceTranscript),
        _entry("voice.state", "s2c", "voice", VoiceState),
        _entry("tilt", "s2c", "session", Tilt),
        _entry("grade", "s2c", "session", Grade),
        _entry("playbook.list", "s2c", "session", PlaybookList),
        _entry("score.session", "s2c", "session", ScoreSession),
    )
}
