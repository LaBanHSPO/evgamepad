"""The game socket.

One WebSocket per token, protocol v1 frames both ways, and the order path from intent to broker
call living entirely inside this process. An intent arrives, the risk rules judge it, the cid is
reserved before anything is sent, the broker is called by direct function call, and the journal
records what happened — no local RPC hop anywhere in that sentence.

The asymmetry from `risk/rules.py` is enforced here at the routing layer too: `intent.open` runs
the gates, `intent.close` and `intent.panic` do not.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from broker import Broker
from journal.writer import ACKED, PENDING, REJECTED, JournalWriter
from protocol import Envelope, ProtocolError, decode, validate_frame
from risk.rules import OpenContext, evaluate_exit, evaluate_open
from risk.session import SessionWindow

log = logging.getLogger(__name__)

Send = Callable[[str], Awaitable[None]]

# What `ai.ask` says when no desk is attached at all (phase 1-3 shape, kept for the tests).
AI_DISABLED = {"disabled": True, "reason": "copilot lands in phase 4"}


@dataclass
class GatewayState:
    """Live session facts the gates read. Owned here, never by a rule."""

    session_id: str
    locked: bool = False
    last_order_ms: int = 0
    last_ping_ms: int = 0
    day_loss_usd: float = 0.0
    positions_open: int = 0

    def heartbeat_age_s(self, now_ms: int) -> float:
        if self.last_ping_ms == 0:
            return 0.0
        return max(0.0, (now_ms - self.last_ping_ms) / 1000)

    def seconds_since_last_order(self, now_ms: int) -> float:
        if self.last_order_ms == 0:
            return float("inf")
        return max(0.0, (now_ms - self.last_order_ms) / 1000)


@dataclass
class GameSocket:
    """One connection's protocol state and the intent routing behind it.

    Transport-agnostic on purpose: it takes a `send` coroutine, so the whole order path can be
    exercised in tests without a browser or a broker.
    """

    send: Send
    broker: Broker
    journal: JournalWriter
    window: SessionWindow
    state: GatewayState
    allowed_symbols: frozenset[str]
    max_positions: int
    max_lots_by_symbol: dict[str, float]
    max_day_loss_usd: float
    min_seconds_between_orders: float
    heartbeat_dead_s: float

    # Phase 4. Both optional: the socket must work with the desk absent, offline, or unconfigured.
    desk: Any | None = None
    sentinel: Any | None = None

    # Phase 7. Absent means every fire grades as `__unplanned__`, which is a valid state.
    playbooks: Any | None = None
    active_playbook_id: str | None = None

    # Phase 9. Absent, or disabled in config, removes tilt entirely.
    tilt: Any | None = None
    # A shared cell the desk's read-only `get_tilt` tool reads. Aggregates only, and it is written
    # here rather than handed to the desk directly so the copilot never holds the tracker.
    tilt_view: dict[str, Any] | None = None

    # Phase 11. The evening's opportunity quality, sampled on the same 1 Hz clock as tilt and
    # written once at session close. There is no live score anywhere — only this input to it.
    opportunity: Any | None = None

    seq: int = 0
    subscriptions: set[str] = field(default_factory=set)
    _outbox: list[Envelope] = field(default_factory=list, init=False)
    _band: str = field(default="calm", init=False)
    _desk_tasks: set[Any] = field(default_factory=set, init=False)
    _last_quote: dict[str, tuple[float, float]] = field(default_factory=dict, init=False)

    def now_ms(self) -> int:
        return int(time.time() * 1000)

    # -- framing ---------------------------------------------------------------------

    async def emit(self, t: str, ch: str, payload: dict[str, Any], cid: str | None = None) -> Envelope:
        """Send one server frame and remember it, so `resync` can replay from `lastSeq`."""
        self.seq += 1
        envelope = Envelope(t=t, seq=self.seq, ts=self.now_ms(), ch=ch, cid=cid, p=payload)
        self._outbox.append(envelope)
        await self.send(envelope.encode())
        return envelope

    async def error(self, code: str, message: str, cid: str | None = None) -> None:
        await self.emit("error", "session", {"code": code, "message": message}, cid=cid)

    async def handle_raw(self, raw: str) -> None:
        """Decode, validate against the frozen catalog, and route. Never raises at the transport."""
        try:
            envelope = decode(raw)
            validate_frame(envelope, expect="c2s")
        except ProtocolError as exc:
            await self.error("bad_frame", str(exc))
            return
        await self.route(envelope)

    # -- routing ---------------------------------------------------------------------

    async def route(self, envelope: Envelope) -> None:
        handlers = {
            "hello": self._hello,
            "ping": self._ping,
            "sub": self._sub,
            "resync": self._resync,
            "snap": self._snap,
            "intent.open": self._intent_open,
            "intent.close": self._intent_close,
            "intent.modify": self._intent_modify,
            "intent.panic": self._intent_panic,
            "session.lock": self._session_lock,
            "session.unlock": self._session_unlock,
            "ai.ask": self._ai_ask,
            "pad.telemetry": self._pad_telemetry,
            "playbook.select": self._playbook_select,
        }
        handler = handlers.get(envelope.t)
        if handler is None:
            # Frozen-but-unimplemented journal-layer types (voice, grading) land here until their
            # phase ships. They are accepted by the catalog and answered honestly.
            await self.error("not_implemented", f"`{envelope.t}` lands in a later phase", envelope.cid)
            return
        await handler(envelope)

    async def _hello(self, envelope: Envelope) -> None:
        last_seq = envelope.p.get("lastSeq")
        resumed = bool(last_seq)
        await self.emit(
            "welcome", "session",
            {"seq": self.seq, "serverTime": self.now_ms(), "resumed": resumed, "mode": "demo"},
        )
        if resumed:
            await self._replay(int(last_seq))

    async def _ping(self, envelope: Envelope) -> None:
        """The dead-man heartbeat. Its clutch flag locks opens only."""
        self.state.last_ping_ms = self.now_ms()
        await self.emit("pong", "session", {"ts": self.now_ms()})

    async def _sub(self, envelope: Envelope) -> None:
        for symbol in envelope.p.get("syms", []):
            if symbol in self.allowed_symbols:
                self.subscriptions.add(symbol)

    async def _resync(self, envelope: Envelope) -> None:
        await self._replay(int(envelope.p["lastSeq"]))

    async def _replay(self, last_seq: int) -> None:
        for envelope in [e for e in self._outbox if e.seq > last_seq]:
            await self.send(envelope.encode())

    async def _snap(self, envelope: Envelope) -> None:
        """Full state, straight from the broker — cTrader is the truth about what is open."""
        positions = await self.broker.positions()
        self.state.positions_open = len(positions)
        await self.emit("pos.snap", "orders", {"positions": positions, "ts": self.now_ms()})
        await self.emit("session", "session", self._session_payload())

    def _session_payload(self) -> dict[str, Any]:
        now = self.now_ms()
        return {
            "open": self.window.is_open(now) and not self.state.locked,
            "locked": self.state.locked,
            "reason": "locked" if self.state.locked else None,
        }

    # -- intents ---------------------------------------------------------------------

    def _open_context(self, symbol: str, lots: float, clutch: bool) -> OpenContext:
        now = self.now_ms()
        # The cooldown reaches the gate as a plain field. It gates opens only, because every risk
        # rule does — `evaluate_exit` runs none of them.
        cooldown_until = self.tilt.cooldown_until if self.tilt is not None else None
        return OpenContext(
            now_ms=now,
            symbol=symbol,
            lots=lots,
            clutch=clutch,
            session_open=self.window.is_open(now) and not self.state.locked,
            session_label=self.window.describe(now),
            allowed_symbols=self.allowed_symbols,
            positions_open=self.state.positions_open,
            max_positions=self.max_positions,
            max_lots=self.max_lots_by_symbol.get(symbol, 0.0),
            day_loss_usd=self.state.day_loss_usd,
            max_day_loss_usd=self.max_day_loss_usd,
            seconds_since_last_order=self.state.seconds_since_last_order(now),
            min_seconds_between_orders=self.min_seconds_between_orders,
            heartbeat_age_s=self.state.heartbeat_age_s(now),
            heartbeat_dead_s=self.heartbeat_dead_s,
            cooldown_until_ms=cooldown_until,
        )

    async def _reject(self, cid: str | None, reason: str, detail: str | None = None) -> None:
        await self.emit(
            "order.reject", "orders",
            {"cid": cid or "", "reason": reason, "detail": detail, "ts": self.now_ms()}, cid=cid,
        )

    async def _claim(self, cid: str | None, intent: str, symbol: str | None) -> bool:
        """Reserve the cid before anything is sent. A duplicate is acked, never re-sent."""
        if cid is None:
            await self._reject(cid, "missing_cid")
            return False
        if not self.journal.reserve_cid(cid, intent=intent, symbol=symbol, ts_ms=self.now_ms()):
            existing = self.journal.cid_state(cid) or {}
            await self.emit(
                "order.upd", "orders",
                {"cid": cid, "state": f"duplicate:{existing.get('state', PENDING)}",
                 "positionId": existing.get("position_id"), "ts": self.now_ms()}, cid=cid,
            )
            return False
        return True

    async def _intent_open(self, envelope: Envelope) -> None:
        payload = envelope.p
        symbol = str(payload["sym"])
        lots = float(payload["lots"])

        clutch = bool(payload.get("clutch"))
        side = str(payload["side"])
        decision = evaluate_open(self._open_context(symbol, lots, clutch))

        # Graded before the gate decides. A refused fire is still a fire that happened, and the
        # deck's declined count depends on a row existing for it.
        if envelope.cid:
            await self.grade_and_push(str(envelope.cid), symbol, lots, side, clutch, stage="fire")

        if not decision.allowed:
            await self._reject(envelope.cid, decision.reason or "refused")
            return

        if not await self._claim(envelope.cid, "open", symbol):
            return

        cid = str(envelope.cid)
        result = await self.broker.place(
            cid=cid, sym=symbol, side=side, lots=lots,
            relative_sl=payload.get("relativeSl"), relative_tp=payload.get("relativeTp"),
        )
        now = self.now_ms()
        if not result.ok:
            self.journal.settle_cid(cid, state=REJECTED, ts_ms=now, reason=result.reason)
            self.journal.append_event(kind="reject", ts_ms=now, cid=cid, payload=result.detail)
            await self._reject(cid, result.reason or "broker_reject")
            return

        self.state.last_order_ms = now
        if self.tilt is not None:
            grade = self.playbooks.grade_for(cid) if self.playbooks else None
            self.tilt.observe_fire(lots=lots, clean=None if grade is None else grade["clean"])
        self.journal.settle_cid(cid, state=ACKED, ts_ms=now)
        self.journal.append_event(kind="fill", ts_ms=now, cid=cid, payload=result.detail)
        await self.emit(
            "order.ack", "orders",
            {"cid": cid, "sym": symbol, "side": payload["side"], "lots": lots, "ts": now},
            cid=cid,
        )

    async def _intent_close(self, envelope: Envelope) -> None:
        """No gates. A close is an exit, and an exit always executes."""
        assert evaluate_exit().allowed
        if not await self._claim(envelope.cid, "close", None):
            return
        cid = str(envelope.cid)
        position_id = int(envelope.p["positionId"])
        result = await self.broker.close(cid=cid, position_id=position_id)
        await self._settle_exit(cid, result.ok, result.reason, {"positionId": position_id})

    async def _intent_modify(self, envelope: Envelope) -> None:
        """Absolute SL/TP on an open position — broker-changing, same clutch+confirm contract."""
        if not envelope.p.get("clutch"):
            await self._reject(envelope.cid, "no_clutch")
            return
        if not await self._claim(envelope.cid, "modify", None):
            return
        cid = str(envelope.cid)
        result = await self.broker.amend_position_sl_tp(
            cid=cid, position_id=int(envelope.p["positionId"]),
            sl=envelope.p.get("sl"), tp=envelope.p.get("tp"),
        )
        await self._settle_exit(cid, result.ok, result.reason, {"kind": "amend"})

    async def _intent_panic(self, envelope: Envelope) -> None:
        """Flatten everything, then lock. Exempt from every open-only gate, by design."""
        assert evaluate_exit().allowed
        if not await self._claim(envelope.cid, "panic", None):
            return
        cid = str(envelope.cid)
        positions = await self.broker.positions()
        failures: list[str] = []
        for position in positions:
            result = await self.broker.close(cid=cid, position_id=position["positionId"])
            if not result.ok:
                failures.append(str(result.reason))
        self.state.locked = True
        await self._settle_exit(cid, not failures, ";".join(failures) or None,
                                {"kind": "panic", "closed": len(positions)})
        await self.emit("session", "session", self._session_payload())

    async def _settle_exit(
        self, cid: str, ok: bool, reason: str | None, detail: dict[str, Any]
    ) -> None:
        now = self.now_ms()
        self.journal.settle_cid(cid, state=ACKED if ok else REJECTED, ts_ms=now, reason=reason)
        self.journal.append_event(kind="close" if ok else "reject", ts_ms=now, cid=cid, payload=detail)
        if ok:
            await self.emit("order.upd", "orders",
                            {"cid": cid, "state": "closed", **detail, "ts": now}, cid=cid)
        else:
            await self._reject(cid, reason or "broker_reject")

    # -- session and desk ------------------------------------------------------------

    async def _session_lock(self, envelope: Envelope) -> None:
        self.state.locked = True
        await self.emit("session", "session", self._session_payload())

    async def _session_unlock(self, envelope: Envelope) -> None:
        self.state.locked = False
        await self.emit("session", "session", self._session_payload())

    async def _ai_ask(self, envelope: Envelope) -> None:
        """The desk answers off the hot path. An unreachable desk is an answer, not a failure."""
        kind = str(envelope.p.get("kind", "advise"))
        if self.desk is None:
            text, citations = str(AI_DISABLED["reason"]), []
        else:
            answer = await self.desk.ask(kind, question=envelope.p.get("sym"))
            text, citations = answer.text, answer.sources
        await self.emit(
            "ai.advice", "ai",
            {"cid": envelope.cid, "kind": kind, "text": text, "citations": citations,
             "ts": self.now_ms()},
            cid=envelope.cid,
        )

    async def push_sentinel(self, tick: Any) -> None:
        """The strip, painted from local state. It never waits on the desk."""
        await self.emit("sentinel.tick", "ai", tick.payload())

    async def push_signal(self, signal: dict[str, Any]) -> None:
        """A method tag, a calendar guard, or a TradingView hint. Never an order."""
        await self.emit("signal.item", "ai", signal)

    async def _playbook_select(self, envelope: Envelope) -> None:
        """The active playbook is part of session state, chosen in the GameOverlay."""
        self.active_playbook_id = str(envelope.p.get("playbookId") or "") or None
        await self.emit("session", "session", self._session_payload())

    def grade_context(self, symbol: str, lots: float, side: str, clutch: bool) -> Any:
        """Assemble what the rules read.

        Chart fields that are not available right now stay `None`, and the affected rules grade as
        *unknown* rather than failing — a missing EMA is not a broken rule.
        """
        from method.rules import RuleContext

        now = self.now_ms()
        setup = None
        spread = None
        spread_cap = None
        if self.sentinel is not None:
            tracker = self.sentinel.tracker(symbol)
            setup = tracker.current
            spread_cap = self.sentinel.spread_caps.get(symbol)

        return RuleContext(
            now_ms=now, symbol=symbol, lots=lots, clutch=clutch,
            session_open=self.window.is_open(now) and not self.state.locked,
            session_label=self.window.describe(now),
            allowed_symbols=self.allowed_symbols,
            positions_open=self.state.positions_open,
            max_positions=self.max_positions,
            max_lots=self.max_lots_by_symbol.get(symbol, 0.0),
            day_loss_usd=self.state.day_loss_usd,
            max_day_loss_usd=self.max_day_loss_usd,
            seconds_since_last_order=self.state.seconds_since_last_order(now),
            min_seconds_between_orders=self.min_seconds_between_orders,
            heartbeat_age_s=self.state.heartbeat_age_s(now),
            heartbeat_dead_s=self.heartbeat_dead_s,
            setup_tag=setup.kind if setup else None,
            setup_side=setup.side if setup else None,
            side=side,
            spread=spread,
            spread_cap=spread_cap,
        )

    async def grade_and_push(self, cid: str, symbol: str, lots: float, side: str,
                             clutch: bool, stage: str) -> None:
        """Grade one fire and push it. Scoring only — this can never stop the order."""
        if self.playbooks is None:
            return
        from grading.grade import grade_fire

        book = (
            self.playbooks.get(self.active_playbook_id)
            if self.active_playbook_id else None
        )
        grade = grade_fire(cid=cid, playbook=book,
                           ctx=self.grade_context(symbol, lots, side, clutch), stage=stage)
        self.playbooks.save_grade(grade.as_db_row())
        await self.emit("grade", "session", grade.payload(), cid=cid)

    async def _pad_telemetry(self, envelope: Envelope) -> None:
        """Journalled, then scored.

        The client batches at 1 Hz, so this is one row per second per session at most — cheap
        enough to keep always-on, and impossible to reconstruct later if it is not.
        """
        sample = dict(envelope.p)
        self.journal.write_pad_event(self.state.session_id, sample)
        if self.tilt is None:
            return

        self.tilt.observe_telemetry(sample)
        self.sample_opportunity()
        await self.push_tilt()

    def sample_opportunity(self) -> None:
        """One opportunity-quality reading, on the telemetry clock.

        A dead tape is a fact about the night, not about the player, so this is measured whether or
        not anything was traded. A symbol with no quote yet contributes nothing rather than a zero —
        an unsampled tape and a dead one must stay distinguishable.
        """
        if self.opportunity is None or self.sentinel is None:
            return
        for symbol in sorted(self.subscriptions):
            quote = self._last_quote.get(symbol)
            if quote is None:
                continue
            now = self.now_ms()
            try:
                tick = self.sentinel.tick(
                    symbol=symbol, bid=quote[0], ask=quote[1], now_ms=now,
                    session_remaining_s=None, locked=self.state.locked,
                )
            except Exception:
                log.exception("sentinel tick failed; the evening is sampled one reading short")
                return
            self.opportunity.observe(tick.quality)
            return

    async def push_tilt(self) -> None:
        """Score, record the sample, and tell the HUD. Never touches the FSM."""
        if self.tilt is None:
            return
        result = self.tilt.score(self.now_ms())
        self.journal.write_tilt_sample(
            self.tilt.sample_row(result, self.state.session_id, self.now_ms())
        )
        payload = result.payload()
        if self.tilt_view is not None:
            # What the desk may see: the band, the score, and the sentences already on screen.
            self.tilt_view.clear()
            self.tilt_view.update(
                {"band": result.band, "score": payload["score"], "top": result.top[:3]}
            )
        await self.emit("tilt", "session", payload)

        crossed_into_hot = result.band in ("hot", "scorched") and self._band in ("calm", "warm")
        self._band = result.band
        if crossed_into_hot:
            self._spawn_hot_advice()

    def _spawn_hot_advice(self) -> None:
        """One monitor advice on the way into the hot band, off the socket's read loop.

        Fire-and-forget on purpose: the desk speaks over the network, and nothing it does may sit
        between an intent and the broker. Its own rate limit keeps it from nagging.
        """
        if self.desk is None:
            return
        task = asyncio.ensure_future(self._hot_advice())
        self._desk_tasks.add(task)
        task.add_done_callback(self._desk_tasks.discard)

    async def _hot_advice(self) -> None:
        try:
            answer = await self.desk.monitor(self.now_ms())
        except Exception:
            log.exception("desk monitor failed at the hot band; the HUD keeps its own driver line")
            return
        if answer is None:
            return
        await self.emit(
            "ai.advice", "ai",
            {"cid": None, "kind": "advise", "text": answer.text,
             "citations": answer.sources, "ts": self.now_ms()},
        )

    async def drain_desk(self) -> None:
        """Await any in-flight desk work. Tests use it; the socket never needs to."""
        while self._desk_tasks:
            await asyncio.gather(*tuple(self._desk_tasks), return_exceptions=True)

    # -- quotes ----------------------------------------------------------------------

    async def push_quote(self, symbol: str, bid: float, ask: float) -> None:
        """Called from the conflator's tick, never from the raw spot callback."""
        if symbol not in self.subscriptions:
            return
        # Kept so the 1 Hz sampler can price a sentinel tick without asking the broker again.
        self._last_quote[symbol] = (bid, ask)
        await self.emit("quote", "quotes", {"sym": symbol, "bid": bid, "ask": ask, "ts": self.now_ms()})

    async def push_maint(self, note: str, until: int | None = None) -> None:
        """What a contained broker failure surfaces as when it is not tied to one order."""
        await self.emit("maint", "session", {"active": True, "until": until, "note": note})


def origin_allowed(origin: str | None, public_origin: str) -> bool:
    """One origin: the HUD and the socket are served from the same place."""
    if origin is None:
        return False
    return origin.rstrip("/") == public_origin.rstrip("/")
