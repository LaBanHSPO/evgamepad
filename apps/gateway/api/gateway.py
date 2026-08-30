"""Gateway state: the one object that owns config, broker, session, and journal.

Everything an intent touches on its way to the broker lives here, in one
process. An approved intent reaches the broker by direct call -- there is no
socket, no framing, and no two-process failure matrix in between.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any

from ..broker import Broker, Containment
from ..broker.conversion import AssetGraph
from ..broker.factory import build_broker
from ..config import Config
from ..journal.tape.ring import TapeRing
from ..journal.writer import DuplicateCid, JournalWriter
from ..protocol import now_ms
from ..protocol.catalog import IntentClose, IntentModify, IntentOpen, IntentPanic
from ..risk.r import r_fallback, r_from_distance
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
    last_quote: dict[str, tuple[float, float, int]] = field(default_factory=dict)


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
        self.assets = AssetGraph()
        self.broker = broker or build_broker(
            cfg, containment=self.containment, graph=self.assets
        )
        self.journal = journal or JournalWriter(cfg.db_path)
        self.session = SessionWindow(cfg.session, cfg.timezone)
        self.tape = TapeRing(cfg.tape.ring_minutes, cfg.tape.dt_s)
        self.state = LiveState()
        self.token = os.environ.get(cfg.gateway.token_env, "")
        #: Live sockets. Quotes, fills and P/L are pushed to all of them; the
        #: WS layer registers and removes itself.
        self.sessions: set[Any] = set()
        self._wire_broker()

    # -- broker lifecycle ---------------------------------------------------

    def _wire_broker(self) -> None:
        """Attach the spot and execution taps, if this broker has them.

        NotWiredBroker does not, which is why these are checked rather than
        assumed -- phase 1's stub has to keep working.
        """
        if hasattr(self.broker, "set_spot_sink"):
            self.broker.set_spot_sink(self.containment("spot")(self._on_spot))
        if hasattr(self.broker, "set_execution_sink"):
            self.broker.set_execution_sink(
                self.containment("execution")(self._on_execution)
            )

    async def start(self) -> None:
        start = getattr(self.broker, "start", None)
        if start is None:
            return
        try:
            await start()
        except Exception as exc:
            # A broker that will not come up must not take the HUD with it. The
            # socket stays serving, the session shows maint, and the operator
            # gets a reason instead of a dead container.
            self.containment.report("startup", str(exc))
            self.state.locked = True

    def _on_spot(self, sym: str, bid_raw: int, ask_raw: int, ts_ms: int) -> None:
        """The raw spot tap: tape ring first, then the derived state.

        This runs before any conflation, which is what makes the tape's
        n_ticks real. What reaches the browser is throttled by the WS layer.
        """
        spec = self.broker.symbol_spec(sym)
        digits = spec.digits if spec else 5
        self.tape.on_tick(sym, bid_raw, ask_raw, ts_ms, digits=digits)
        scale = 10 ** 5
        self.state.spreads[sym] = (ask_raw - bid_raw) / scale
        self.state.last_quote[sym] = (bid_raw / scale, ask_raw / scale, ts_ms)

    def _on_execution(self, update: Any) -> None:
        """Journal every broker fact, then tell the sockets.

        Append-only and in arrival order: position_event is the record of what
        the broker said, not a summary of what we think happened.
        """
        if update.position_id is None:
            return
        kind = {
            "filled": "fill", "closed": "close", "amended": "amend",
            "rejected": "reject",
        }.get(update.kind)
        if kind is None:
            return

        spec = self.broker.symbol_spec(update.sym) if update.sym else None
        lots = self.lots_for(update)

        self.journal.append_event(
            update.position_id, update.ts, kind, cid=update.cid,
            price=update.price, lots=lots, sl=update.sl, tp=update.tp,
            detail=update.reason,
        )
        if kind == "fill":
            self.state.open_positions += 1
        elif kind == "close":
            self.state.open_positions = max(0, self.state.open_positions - 1)
            self._record_close(update, lots, spec)

        self.broadcast(update)

    def _record_close(self, update: Any, lots: float, spec: Any) -> None:
        """One trade_closed row per full close, with a non-null r_multiple.

        R comes from risk/r.py via the stored plan, so the deck and the HUD
        cannot end up with two different ideas of the same trade.
        """
        plan = self.journal.plan_for_position(update.position_id)
        r_usd = plan["r_usd"] if plan and plan["r_usd"] else self.cfg.risk.r_unit_usd
        net = (update.gross_pnl or 0.0) + update.commission + update.swap
        self.journal.write_closed({
            "position_id": update.position_id,
            "cid": update.cid,
            "session_id": self.state.session_id,
            "sym": update.sym or "",
            "side": update.side or "buy",
            "lots": lots,
            "opened_at": plan["created_at"] if plan else update.ts,
            "closed_at": update.ts,
            "entry": update.entry or 0.0,
            "exit": update.price or 0.0,
            "sl_at_entry": plan["planned_sl"] if plan else None,
            "tp_at_entry": plan["planned_tp"] if plan else None,
            "gross_pnl": update.gross_pnl or 0.0,
            "commission": update.commission,
            "swap": update.swap,
            "net_pnl": net,
            "r_usd": r_usd,
            "r_multiple": net / r_usd if r_usd else 0.0,
            "exit_reason": "manual",
        })

    def lots_for(self, update: Any) -> float:
        """Protocol volume back into the lots the HUD speaks."""
        spec = self.broker.symbol_spec(update.sym) if update.sym else None
        if spec is None or not update.volume:
            return 0.0
        from ..broker.volume import volume_to_lots

        return volume_to_lots(update.volume, spec)

    def position_payload(self, position: Any) -> dict[str, Any]:
        """One open position, as the HUD reads it.

        ``rMultiple`` comes from the plan's stored R, never from a constant the
        HUD divides into the dollars -- a second R definition in the browser is
        how the HUD and the journal end up disagreeing about one trade. It is
        null for a position this gateway did not open (one reconciled from
        cTrader after a restart), and the HUD then shows dollars rather than a
        number it cannot justify.
        """
        spec = self.broker.symbol_spec(position.sym)
        lots = 0.0
        if spec is not None:
            from ..broker.volume import volume_to_lots

            lots = volume_to_lots(position.volume, spec)

        plan = self.journal.plan_for_position(position.position_id)
        r_usd = plan["r_usd"] if plan else None
        pnl = getattr(position, "pnl", 0.0)
        return {
            "positionId": position.position_id,
            "sym": position.sym,
            "side": position.side,
            "lots": lots,
            "entry": position.entry,
            "sl": position.sl,
            "tp": position.tp,
            "openedAt": position.opened_at,
            "pnl": pnl,
            "rMultiple": (pnl / r_usd) if r_usd else None,
        }

    def broadcast(self, update: Any) -> None:
        for session in list(self.sessions):
            enqueue = getattr(session, "enqueue_execution", None)
            if enqueue is not None:
                enqueue(update)

    def plan_r(self, payload: IntentOpen, ts: int):
        """The one R call for an open, used at FIRE.

        Computed from the stop *distance* the order carries, so it does not
        depend on having seen a quote first -- R is a property of the size and
        the stop, and waiting for a fill price to know it would leave the first
        trade of an evening scored against the fallback for no reason.
        """
        spec = self.broker.symbol_spec(payload.sym)
        if spec is None:
            return None
        from ..broker.volume import lots_to_volume, relative_to_price_distance

        volume = lots_to_volume(payload.lots, spec)
        if not payload.relativeSl:
            return r_fallback(self.cfg.risk.r_unit_usd, ts)
        return r_from_distance(
            protocol_volume=volume,
            distance=relative_to_price_distance(payload.relativeSl),
            spec=spec, graph=self.assets, ts=ts,
        )

    # -- risk ---------------------------------------------------------------

    def risk_context(
        self, intent_type: str, payload: object, ts: int, cid: str | None = None
    ) -> rules.RiskContext:
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
            # Ask the ledger, not a placeholder. The UNIQUE constraint below
            # is the backstop; this is what lets a double-press come back as
            # `duplicate_cid` rather than as whatever gate it happens to trip
            # once the first order is already open.
            cid_seen=cid is not None and self.journal.cid_state(cid) is not None,
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
        ctx = self.risk_context(intent_type, payload, ts, cid)
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
            if intent_type == "intent.open":
                self._write_plan(cid, payload, ts)
            return True, None, ""

        self.journal.mark_cid(cid, "rejected", ts, reject_reason=result.reason)
        return False, result.reason or "broker_error", result.detail or ""

    def _write_plan(self, cid: str, payload: IntentOpen, ts: int) -> None:
        """Snapshot the intent at FIRE, before the market answers.

        Written after the ack so ``planned_entry`` is the price the order
        actually got rather than a guess, but it records what was *intended*:
        the plan is never rewritten by what happened next.
        """
        from ..broker.volume import lots_to_volume, relative_to_price_distance
        from ..journal.writer import PlanRow

        spec = self.broker.symbol_spec(payload.sym)
        if spec is None:
            return
        entry = self.state.last_quote.get(payload.sym, (0.0, 0.0, ts))
        price = entry[1] if payload.side == "buy" else entry[0]
        r = self.plan_r(payload, ts)

        sl = tp = None
        if price and payload.relativeSl:
            d = relative_to_price_distance(payload.relativeSl)
            sl = price - d if payload.side == "buy" else price + d
        if price and payload.relativeTp:
            d = relative_to_price_distance(payload.relativeTp)
            tp = price + d if payload.side == "buy" else price - d

        try:
            self.journal.write_plan(PlanRow(
                cid=cid,
                session_id=self.state.session_id,
                created_at=ts,
                sym=payload.sym,
                side=payload.side,
                lots=payload.lots,
                protocol_volume=lots_to_volume(payload.lots, spec),
                planned_entry=price or None,
                relative_sl=payload.relativeSl,
                relative_tp=payload.relativeTp,
                planned_sl=sl,
                planned_tp=tp,
                planned_rr=(abs(tp - price) / abs(price - sl))
                if (sl and tp and price and sl != price) else None,
                r_usd=r.usd if r else self.cfg.risk.r_unit_usd,
                r_source=r.source if r else "r_unit_fallback",
                r_rate=r.rate if r else None,
                r_rate_chain=r.chain if r else None,
                r_rate_ts=r.rate_ts if r else None,
                armed_at=payload.armedAt,
                time_to_fire_ms=ts - payload.armedAt,
                market_session=self.session.trading_day(ts),
            ))
        except Exception as exc:
            # A journal failure must never unwind a placed order. The position
            # is real; losing its plan row is a reporting gap, not a trade bug.
            self.containment.report("journal", f"plan for {cid}: {exc}", cid)

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

    async def shutdown(self) -> None:
        stop = getattr(self.broker, "stop", None)
        if stop is not None:
            try:
                await stop()
            except Exception as exc:
                log.warning("broker stop: %s", exc)
        # Seal the in-progress bar so a shutdown inside a post-roll window still
        # freezes what the tape actually had.
        self.tape.seal_all()
        self.journal.close()
