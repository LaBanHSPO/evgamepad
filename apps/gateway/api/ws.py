"""The ``/ws`` session: one socket, one token, monotonic seq, replayable.

Transport-agnostic on purpose. :class:`WsSession` takes a ``send`` coroutine and
nothing else, so the whole intent path is testable without a browser, a
websocket, or a broker.
"""

from __future__ import annotations

import logging
from collections import deque
from collections.abc import Awaitable, Callable
from typing import Any

from ..protocol import ProtocolError, decode, encode, new_cid, now_ms
from ..protocol.catalog import (
    Hello,
    Ping,
    Resync,
    Snap,
    Sub,
)
from .gateway import Gateway

log = logging.getLogger("ev.ws")


def _execution_frame(update: Any, lots: float = 0.0) -> tuple[str, dict, str | None] | None:
    """Translate one broker execution into the frame the HUD reads."""
    if update.kind == "filled":
        if not (update.cid and update.sym and update.side):
            # A fill we did not originate -- reconciled or server-side. It is
            # an update, not an acknowledgement of anything this socket sent.
            return ("order.upd", {"positionId": update.position_id,
                                  "status": "filled", "ts": update.ts}, None)
        return ("order.ack", {
            "cid": update.cid, "sym": update.sym, "side": update.side,
            "lots": lots, "price": update.price or 0.0, "ts": update.ts,
            "orderId": update.order_id, "positionId": update.position_id,
        }, update.cid)
    if update.kind in {"closed", "amended", "cancelled", "expired"}:
        status = {"closed": "closed", "amended": "amended",
                  "cancelled": "cancelled", "expired": "expired"}[update.kind]
        return ("order.upd", {
            "cid": update.cid, "orderId": update.order_id,
            "positionId": update.position_id, "status": status, "ts": update.ts,
        }, update.cid)
    if update.kind == "rejected":
        return ("order.reject", {
            "cid": update.cid, "reason": "broker_error", "detail": update.reason,
        }, update.cid)
    return None

Send = Callable[[str], Awaitable[None]]

#: Quotes are conflated to this rate before they reach the browser. The tape
#: ring already saw every tick; the HUD does not need 60 Hz of quote text, and
#: sending it would compete with the order acks this socket exists to deliver.
QUOTE_HZ = 15.0

#: The forming bar only needs to move often enough to look alive. Closed bars
#: are pushed the moment they close, so nothing is lost by being slow here.
CANDLE_HZ = 2.0

#: Frames kept for replay after a `resync`. A reconnect that has fallen further
#: behind than this gets a fresh snapshot instead of a partial history, which is
#: the honest answer -- a gap silently stitched over is worse than a resnap.
REPLAY_DEPTH = 512


class WsSession:
    def __init__(self, gw: Gateway, send: Send, *, session_id: str | None = None) -> None:
        self.gw = gw
        self.send = send
        self.session_id = session_id or new_cid()
        self.seq = 0
        self.authed = False
        self.subs: set[str] = set()
        self._replay: deque[tuple[int, str]] = deque(maxlen=REPLAY_DEPTH)
        self._last_quote_sent: dict[str, float] = {}
        self._last_candle_sent = 0.0
        self._resnap = False
        #: A stable cid for ARM previews, so the HUD can tell a preview from
        #: the grade of a fire that actually happened.
        self.preview_cid = new_cid()
        #: A stable cid for ARM previews, so the HUD can tell a preview from
        #: the grade of a fire that actually happened.
        self.preview_cid = new_cid()
        #: What the chart is showing. Set by `sub`; only this series is pushed.
        self.chart: tuple[str, str] = ("XAUUSD", "M5")
        self._pending: deque[tuple[str, Any, str | None]] = deque(maxlen=256)

    # -- outbound -----------------------------------------------------------

    async def emit(self, t: str, payload: Any = None, *, cid: str | None = None) -> int:
        self.seq += 1
        raw = encode(t, payload, seq=self.seq, cid=cid)
        self._replay.append((self.seq, raw))
        await self.send(raw)
        return self.seq

    async def error(self, reason: str, detail: str = "") -> None:
        await self.emit("error", {"reason": reason, "detail": detail or None})

    # -- pushes from the broker --------------------------------------------

    def enqueue_execution(self, update: Any) -> None:
        """Called from the broker's callback, which is synchronous. Queue here
        and drain on the socket's own task -- awaiting a send from inside a
        Protobuf callback is how the two runtimes deadlock."""
        frame = _execution_frame(update, self.gw.lots_for(update))
        if frame is not None:
            self._pending.append(frame)

    def enqueue_score(self, payload: dict) -> None:
        self._pending.append(("score.session", payload, None))

    def enqueue_grade(self, payload: dict) -> None:
        self._pending.append(("grade", payload, payload.get("cid")))

    def enqueue_resnap(self) -> None:
        """Ask this socket to re-send its snapshot after a broker reconnect."""
        self._resnap = True

    def enqueue_candle(self, payload: dict) -> None:
        """A closed bar. Pushed immediately -- a bar that closes late redraws
        the chart's last candle under the player."""
        if (payload["sym"], payload["tf"]) != self.chart:
            return
        self._pending.append(("candle", payload, None))

    def enqueue_forming(self, now_ms_: int) -> None:
        """The right-hand candle, throttled to CANDLE_HZ."""
        if now_ms_ - self._last_candle_sent < 1000 / CANDLE_HZ:
            return
        sym, tf = self.chart
        bar = self.gw.candles.forming(sym, tf)
        if bar is None:
            return
        self._last_candle_sent = now_ms_
        from .candles import payload as candle_payload

        self._pending.append(("candle", candle_payload(sym, tf, bar), None))

    def enqueue_quote(self, sym: str, bid: float, ask: float, ts: int, digits: int) -> None:
        """Conflate to QUOTE_HZ. The ring already has every tick."""
        now = ts / 1000.0
        last = self._last_quote_sent.get(sym, 0.0)
        if now - last < 1.0 / QUOTE_HZ:
            return
        self._last_quote_sent[sym] = now
        self._pending.append((
            "quote",
            {"sym": sym, "bid": bid, "ask": ask, "ts": ts, "digits": digits},
            None,
        ))

    async def flush(self) -> None:
        if self._resnap:
            self._resnap = False
            await self.emit("maint", {"reason": "broker_reconnected", "detail": "resynced"})
            await self._snapshot()
        while self._pending:
            t, payload, cid = self._pending.popleft()
            await self.emit(t, payload, cid=cid)

    # -- inbound ------------------------------------------------------------

    async def handle(self, raw: str | bytes) -> None:
        try:
            frame, payload = decode(raw, direction="c2s")
        except ProtocolError as exc:
            await self.error(exc.reason, exc.detail)
            return

        # Any frame from the client is proof of life for the dead-man gate.
        self.gw.state.last_client_ms = now_ms()

        if not self.authed and frame.t != "hello":
            await self.error("unauthenticated", frame.t)
            return

        handler = getattr(self, f"_on_{frame.t.replace('.', '_')}", None)
        if handler is None:
            await self.error("unhandled_type", frame.t)
            return
        await handler(frame, payload)

    # -- handlers -----------------------------------------------------------

    async def _on_hello(self, frame: Any, p: Hello) -> None:
        expected = self.gw.token
        if not expected or p.token != expected:
            await self.error("bad_token")
            return
        self.authed = True
        resumed = p.lastSeq > 0
        await self.emit(
            "welcome",
            {
                "sessionId": self.session_id,
                "seq": self.seq,
                "serverTs": now_ms(),
                "tz": self.gw.cfg.timezone,
                "symbols": self.gw.cfg.symbol_names,
                "resumed": resumed,
                "features": {
                    "broker": (await self.gw.broker.health()).connected,
                    "voice": self.gw.cfg.voice.enabled,
                    "copilot": self.gw.cfg.copilot.enabled,
                    "tilt": self.gw.cfg.tilt.enabled,
                },
            },
        )
        await self._emit_session()
        await self._emit_playbooks()

    async def _on_ping(self, frame: Any, p: Ping) -> None:
        # `clutch` here is dead-man evidence only. A fire is authorised by the
        # clutch on the intent itself, never by the last heartbeat -- otherwise
        # a press 50ms after clutch-down would be refused by a stale ping.
        await self.emit("pong", {"clutch": p.clutch, "serverTs": now_ms()})

    async def _on_sub(self, frame: Any, p: Sub) -> None:
        self.subs.add(p.ch)
        if p.ch != "quotes":
            return
        # A `sub` on quotes also selects the chart series, and replays its
        # history so the chart is populated within a frame of subscribing
        # rather than filling in one bar at a time.
        sym = p.syms[0] if p.syms else self.chart[0]
        tf = p.tf or self.chart[1]
        self.chart = (sym, tf)
        self._last_candle_sent = 0.0
        self._resnap = False
        #: A stable cid for ARM previews, so the HUD can tell a preview from
        #: the grade of a fire that actually happened.
        self.preview_cid = new_cid()
        #: A stable cid for ARM previews, so the HUD can tell a preview from
        #: the grade of a fire that actually happened.
        self.preview_cid = new_cid()
        from .candles import payload as candle_payload

        for bar in self.gw.candles.history(sym, tf, limit=300):
            await self.emit("candle", candle_payload(sym, tf, bar))

    async def _on_resync(self, frame: Any, p: Resync) -> None:
        pending = [raw for seq, raw in self._replay if seq > p.fromSeq]
        oldest = self._replay[0][0] if self._replay else self.seq + 1
        if p.fromSeq + 1 < oldest:
            await self.emit("maint", {"reason": "resync_gap", "detail": "resnap"})
            await self._snapshot()
            return
        for raw in pending:
            await self.send(raw)

    async def _on_snap(self, frame: Any, p: Snap) -> None:
        await self._snapshot(p.what or None)

    async def _on_session_lock(self, frame: Any, p: Any) -> None:
        self.gw.state.locked = True
        await self._emit_session()

    async def _on_session_unlock(self, frame: Any, p: Any) -> None:
        self.gw.state.locked = False
        await self._emit_session()

    async def _on_ai_ask(self, frame: Any, p: Any) -> None:
        await self.emit(
            "ai.advice",
            {"kind": p.kind, "ts": now_ms(), "disabled": True, "text": ""},
        )

    async def _on_pad_telemetry(self, frame: Any, p: Any) -> None:
        # Stored, not dropped. Phase 9 reads these rows, and telemetry that was
        # never written cannot be recovered from a session that already ended.
        session_id = self.gw.ensure_session(now_ms())
        self.gw.journal.append_pad_event(
            session_id, p.model_dump(by_alias=True, exclude_none=False)
        )

        # An ARM transition is what the confirm overlay is waiting on. The
        # protocol has no `arm` message -- it was frozen in phase 1 -- so the
        # telemetry batch's own `to` field is the signal, and the client
        # flushes a batch on the transition rather than waiting for its second.
        tilt = self.gw.observe_telemetry(p.model_dump(by_alias=True, exclude_none=False))
        if tilt is not None:
            await self.emit("tilt", tilt.as_message())

        if p.to == "ARMED" and p.sym:
            await self._preview_grade(p.sym, p.from_, p.lots)

    async def _preview_grade(self, sym: str, side_hint: str | None, lots: float | None) -> None:
        """Grade the prospective trade for the ARM overlay.

        Not persisted: this is a preview of a fire that may never happen, and a
        trade_grade row for a trade that was never taken would inflate every
        count that reads them. The FIRE grade, with the real cid, is the one
        that is recorded.
        """
        side = "buy" if (side_hint or "").lower().startswith("b") else None
        try:
            result, book = self.gw.grade(
                self.preview_cid, sym, side, lots, phase="arm", persist=False
            )
        except Exception as exc:
            log.warning("preview grade failed: %s", exc)
            return
        await self.emit(
            "grade", result.as_message(self.preview_cid, book.slug if book else None)
        )

    async def _on_voice_begin(self, frame: Any, p: Any) -> None:
        # Phase 8 records the memo. What phase 9 needs from it is here already:
        # starting one during a cooldown is the acknowledgement that halves the
        # recency terms, because narrating it is the intervention.
        self.gw.acknowledge_tilt()
        tilt = self.gw.recompute_tilt()
        if tilt is not None:
            await self.emit("tilt", tilt.as_message())
        await self.emit(
            "voice.transcript",
            {"voiceId": p.voiceId, "ok": False, "reason": "disabled", "durMs": 0, "sttMs": 0},
        )

    async def _on_voice_cancel(self, frame: Any, p: Any) -> None:
        return

    async def _on_journal_memo_link(self, frame: Any, p: Any) -> None:
        return

    async def _on_grade_answer(self, frame: Any, p: Any) -> None:
        """One tap of the post-trade checklist.

        Skipping is not modelled here at all -- an unanswered manual rule stays
        absent, which grades as unknown and drops out of the required count. A
        skip cannot cost the player anything because there is nothing to record.
        """
        answers = self.gw.state.grade_answers.setdefault(p.cid, {})
        answers[p.ruleId] = p.answer
        result, book = self.gw.grade(
            p.cid, self.gw.state.last_graded_sym or "XAUUSD", None, None,
            phase="settled",
        )
        await self.emit(
            "grade", result.as_message(p.cid, book.slug if book else None), cid=p.cid
        )

    async def _on_playbook_select(self, frame: Any, p: Any) -> None:
        """Selecting a playbook is session state, and never a broker action."""
        book = self.gw.playbooks.get(p.playbookId)
        if book is not None:
            self.gw.state.playbook_slug = book.slug
            self.gw.journal.set_active_playbook(
                self.gw.ensure_session(now_ms()), book.id
            )
        await self._emit_playbooks()

    async def _emit_playbooks(self) -> None:
        active = self.gw.state.playbook_slug
        await self.emit("playbook.list", {
            "playbooks": [
                {
                    "playbookId": b.slug,
                    "name": b.name + (" ✓" if b.slug == active else ""),
                    "ruleCount": len(b.rules),
                    "requiredCount": len(b.required_rules),
                }
                for b in self.gw.playbooks.list()
            ],
        })

    async def _on_intent_open(self, frame: Any, p: Any) -> None:
        await self._intent("intent.open", frame, p)

    async def _on_intent_close(self, frame: Any, p: Any) -> None:
        await self._intent("intent.close", frame, p)

    async def _on_intent_modify(self, frame: Any, p: Any) -> None:
        await self._intent("intent.modify", frame, p)

    async def _on_intent_panic(self, frame: Any, p: Any) -> None:
        await self._intent("intent.panic", frame, p)

    async def _intent(self, t: str, frame: Any, p: Any) -> None:
        cid = frame.cid
        ok, reason, detail = await self.gw.handle_intent(t, cid, p)
        if ok:
            return
        await self.emit(
            "order.reject", {"cid": cid, "reason": reason, "detail": detail or None}, cid=cid
        )
        if t in {"intent.close", "intent.panic"}:
            log.warning("safety exit %s refused for %s: %s", t, cid, reason)

    # -- snapshots ----------------------------------------------------------

    async def _emit_session(self) -> None:
        ts = now_ms()
        window = self.gw.session.window_containing(ts)
        opens_allowed = window is not None and not self.gw.state.locked
        await self.emit(
            "session",
            {
                "state": "locked"
                if self.gw.state.locked
                else ("open" if window else "closed"),
                "opensAllowed": opens_allowed,
                "tz": self.gw.cfg.timezone,
                "startsAt": window.start_ms if window else self.gw.session.next_open(ts),
                "endsAt": window.end_ms if window else None,
            },
        )

    async def _snapshot(self, what: list[str] | None = None) -> None:
        want = set(what or ["pos", "pnl", "session", "risk"])
        ts = now_ms()
        if "session" in want:
            await self._emit_session()
        if "pos" in want:
            positions = await self.gw.broker.positions()
            await self.emit(
                "pos.snap",
                {
                    "ts": ts,
                    "positions": [self.gw.position_payload(p) for p in positions],
                },
            )
        if "risk" in want:
            await self.emit(
                "risk",
                {
                    "locked": self.gw.state.locked,
                    "reasons": [],
                    "positions": self.gw.state.open_positions,
                    "maxPositions": self.gw.cfg.risk.max_positions,
                    "dayLossUsd": self.gw.day_loss_usd(),
                    "maxDailyLossUsd": self.gw.cfg.risk.max_daily_loss_usd,
                },
            )
