"""Gateway state: the one object that owns config, broker, session, and journal.

Everything an intent touches on its way to the broker lives here, in one
process. An approved intent reaches the broker by direct call -- there is no
socket, no framing, and no two-process failure matrix in between.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field

from ..broker import Broker, Containment, NotWiredBroker
from ..broker.conversion import AssetGraph
from ..config import Config
from ..journal.tape.ring import TapeRing
from ..journal.writer import DuplicateCid, JournalWriter
from ..protocol import now_ms
from ..protocol.catalog import IntentClose, IntentModify, IntentOpen, IntentPanic
from ..risk import rules
from ..risk.session import SessionWindow

log = logging.getLogger("ev.gateway")

_KIND = {
    "intent.open": "open",
    "intent.close": "close",
    "intent.modify": "modify",
    "intent.panic": "panic",
}


@dataclass
class LiveState:
    """Mutable per-evening state. Nothing here survives a restart on purpose --
    cTrader is reconciled on reconnect and is the source of truth."""

    locked: bool = False
    open_positions: int = 0
    last_order_ms: int | None = None
    last_client_ms: int | None = None
    cooldown_until_ms: int | None = None
    session_id: int | None = None
    spreads: dict[str, float] = field(default_factory=dict)


class Gateway:
    def __init__(
        self,
        cfg: Config,
        *,
        broker: Broker | None = None,
        journal: JournalWriter | None = None,
    ) -> None:
        self.cfg = cfg
        self.containment = Containment()
        self.broker = broker or NotWiredBroker(self.containment)
        self.journal = journal or JournalWriter(cfg.db_path)
        self.session = SessionWindow(cfg.session, cfg.timezone)
        self.assets = AssetGraph()
        self.tape = TapeRing(cfg.tape.ring_minutes, cfg.tape.dt_s)
        self.state = LiveState()
        self.token = os.environ.get(cfg.gateway.token_env, "")

    # -- risk ---------------------------------------------------------------

    def risk_context(self, intent_type: str, payload: object, ts: int) -> rules.RiskContext:
        cfg = self.cfg
        sym = getattr(payload, "sym", None)
        sym_cfg = cfg.symbol(sym) if sym else None
        lots = getattr(payload, "lots", None)

        lots_ok = True
        if intent_type == "intent.open" and sym_cfg is not None and lots is not None:
            lots_ok = lots <= sym_cfg.max_lots

        return rules.RiskContext(
            now_ms=ts,
            intent_type=intent_type,
            session_open=self.session.is_open(ts),
            locked=self.state.locked,
            clutch=bool(getattr(payload, "clutch", False)),
            armed_at=getattr(payload, "armedAt", None),
            open_positions=self.state.open_positions,
            max_positions=cfg.risk.max_positions,
            day_loss_usd=self.day_loss_usd(),
            max_daily_loss_usd=cfg.risk.max_daily_loss_usd,
            last_order_ms=self.state.last_order_ms,
            min_seconds_between_orders=cfg.risk.min_seconds_between_orders,
            last_client_ms=self.state.last_client_ms,
            heartbeat_dead_s=cfg.gateway.heartbeat_dead_s,
            cid_seen=False,
            symbol_known=sym is None or sym_cfg is not None,
            lots_ok=lots_ok,
            spread=self.state.spreads.get(sym) if sym else None,
            max_spread=sym_cfg.max_spread if sym_cfg else None,
            cooldown_until_ms=self.state.cooldown_until_ms,
        )

    def day_loss_usd(self) -> float:
        if self.state.session_id is None:
            return 0.0
        return self.journal.day_loss_usd(self.state.session_id)

    def ensure_session(self, ts: int) -> int:
        if self.state.session_id is None:
            day = self.session.trading_day(ts)
            self.state.session_id = self.journal.open_session(
                day, self.cfg.timezone, ts
            )
        return self.state.session_id

    # -- intents ------------------------------------------------------------

    async def handle_intent(
        self,
        intent_type: str,
        cid: str,
        payload: IntentOpen | IntentClose | IntentModify | IntentPanic,
        ts: int | None = None,
    ) -> tuple[bool, str | None, str]:
        """Risk, then cid reservation, then the broker. Returns
        ``(ok, reject_reason, detail)``.

        Reservation happens **after** risk and **before** the broker call: a
        refused intent should not burn a cid, and a sent one must never be
        sendable twice.
        """
        ts = now_ms() if ts is None else ts
        ctx = self.risk_context(intent_type, payload, ts)
        decision = rules.evaluate(ctx)
        if not decision.allowed:
            assert decision.reason is not None
            return False, decision.reason, decision.detail

        try:
            self.journal.reserve_cid(cid, _KIND[intent_type], ts, getattr(payload, "sym", None))
        except DuplicateCid:
            return False, "duplicate_cid", cid

        self.ensure_session(ts)

        try:
            result = await self._dispatch(intent_type, cid, payload)
        except Exception as exc:  # containment: the socket outlives the broker
            self.containment.report("intent", f"{intent_type}: {exc}", cid)
            self.journal.mark_cid(cid, "rejected", ts, reject_reason="broker_error")
            return False, "broker_error", str(exc)[:200]

        if result.ok:
            self.state.last_order_ms = ts
            self.journal.mark_cid(
                cid, "acked", ts, order_id=result.order_id, position_id=result.position_id
            )
            return True, None, ""

        self.journal.mark_cid(cid, "rejected", ts, reject_reason=result.reason)
        return False, result.reason or "broker_error", result.detail or ""

    async def _dispatch(self, intent_type: str, cid: str, payload: object):
        from ..broker.types import OpenRequest
        from ..broker.volume import lots_to_volume

        if intent_type == "intent.open":
            assert isinstance(payload, IntentOpen)
            spec = self.broker.symbol_spec(payload.sym)
            # Without a symbol spec there is no honest lots->volume conversion,
            # and guessing one is the wrong-volume-on-gold bug. Phase 2 fills
            # this in at connect; until then the broker refuses anyway.
            volume = lots_to_volume(payload.lots, spec) if spec else 0
            return await self.broker.place(
                OpenRequest(
                    cid=cid,
                    sym=payload.sym,
                    side=payload.side,
                    volume=volume,
                    relative_sl=payload.relativeSl,
                    relative_tp=payload.relativeTp,
                )
            )
        if intent_type == "intent.close":
            assert isinstance(payload, IntentClose)
            return await self.broker.close(payload.positionId, cid)
        if intent_type == "intent.modify":
            assert isinstance(payload, IntentModify)
            return await self.broker.amend_position_sl_tp(
                payload.positionId, cid, payload.sl, payload.tp
            )
        if intent_type == "intent.panic":
            return await self._panic(cid)
        raise ValueError(intent_type)

    async def _panic(self, cid: str):
        """Flatten everything, then lock. Never gated -- see rules.OPEN_ONLY."""
        from ..broker.types import BrokerResult

        positions = await self.broker.positions()
        failures: list[str] = []
        for pos in positions:
            result = await self.broker.close(pos.position_id, cid)
            if not result.ok:
                failures.append(f"{pos.position_id}:{result.reason}")
        self.state.locked = True
        if failures:
            return BrokerResult(
                ok=False, cid=cid, reason="broker_error", detail=";".join(failures)
            )
        return BrokerResult(ok=True, cid=cid)

    def shutdown(self) -> None:
        self.tape.seal_all()
        self.journal.close()
