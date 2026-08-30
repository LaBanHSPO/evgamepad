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

Send = Callable[[str], Awaitable[None]]

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

    # -- outbound -----------------------------------------------------------

    async def emit(self, t: str, payload: Any = None, *, cid: str | None = None) -> int:
        self.seq += 1
        raw = encode(t, payload, seq=self.seq, cid=cid)
        self._replay.append((self.seq, raw))
        await self.send(raw)
        return self.seq

    async def error(self, reason: str, detail: str = "") -> None:
        await self.emit("error", {"reason": reason, "detail": detail or None})

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

    async def _on_ping(self, frame: Any, p: Ping) -> None:
        # `clutch` here is dead-man evidence only. A fire is authorised by the
        # clutch on the intent itself, never by the last heartbeat -- otherwise
        # a press 50ms after clutch-down would be refused by a stale ping.
        await self.emit("pong", {"clutch": p.clutch, "serverTs": now_ms()})

    async def _on_sub(self, frame: Any, p: Sub) -> None:
        self.subs.add(p.ch)

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
        # Phase 9 consumes this. Accepted and dropped until then so the client
        # can ship the batch now without a protocol change later.
        return

    async def _on_voice_begin(self, frame: Any, p: Any) -> None:
        await self.emit(
            "voice.transcript",
            {"voiceId": p.voiceId, "ok": False, "reason": "disabled", "durMs": 0, "sttMs": 0},
        )

    async def _on_voice_cancel(self, frame: Any, p: Any) -> None:
        return

    async def _on_journal_memo_link(self, frame: Any, p: Any) -> None:
        return

    async def _on_grade_answer(self, frame: Any, p: Any) -> None:
        return

    async def _on_playbook_select(self, frame: Any, p: Any) -> None:
        await self.emit("playbook.list", {"playbooks": []})

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
                    "positions": [
                        {
                            "positionId": p.position_id,
                            "sym": p.sym,
                            "side": p.side,
                            "lots": 0.0,
                            "entry": p.entry,
                            "sl": p.sl,
                            "tp": p.tp,
                            "openedAt": p.opened_at,
                        }
                        for p in positions
                    ],
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
