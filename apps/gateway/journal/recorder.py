"""Turns broker execution events into the rows phase 6 measures.

The order path acks in milliseconds; this is what happens after. A fill writes the plan as it
stood at FIRE — including R and the conversion that produced it — and a close writes the trade's
facts plus the excursions read off the correct side of the book.

The tape freeze is deliberately late: a window is only worth keeping once its post-roll exists,
so a close schedules the freeze for `closed_at + post_roll_s` rather than cutting the tape at the
exit. Shutdown and session end flush whatever post-roll has accumulated instead of losing it.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from broker.conversion import AssetGraph, ConversionError
from broker.volume import SymbolSpec, volume_to_lots
from journal.tape import TapeRing, freeze_window
from journal.writer import ClosedTrade, JournalWriter
from risk.r import RRecord, r_at_entry, r_multiple
from risk.session import market_session

log = logging.getLogger(__name__)

PRICE_SCALE = 100_000


@dataclass
class OpenTrade:
    """What has to survive between a fill and its close."""

    cid: str
    position_id: int
    symbol: str
    side: str
    volume: int
    entry: float
    opened_at: int
    r: RRecord


@dataclass
class TradeRecorder:
    """Owns the plan/close/tape writes for one session."""

    journal: JournalWriter
    ring: TapeRing
    specs: Mapping[str, SymbolSpec]
    graph: AssetGraph | None
    session_id: str
    r_unit_usd: float
    pre_roll_s: int
    post_roll_s: int
    dt_s: int = 1

    open_trades: dict[int, OpenTrade] = field(default_factory=dict)
    _pending_freezes: list[tuple[int, OpenTrade, float]] = field(default_factory=list)

    # -- fill ------------------------------------------------------------------------

    def on_fill(
        self, *, cid: str, position_id: int, symbol: str, side: str, volume: int,
        entry: float, ts_ms: int, prices: Mapping[int, float],
        planned_sl: float | None = None, planned_tp: float | None = None,
        timeframe: str | None = None, playbook_id: str | None = None, armed_at: int | None = None,
    ) -> OpenTrade:
        """Write the plan and start tracking the position for its eventual close."""
        spec = self.specs[symbol]
        record = self._r_for(spec, volume, entry, planned_sl, ts_ms, prices)

        planned_rr = None
        if planned_sl is not None and planned_tp is not None and abs(entry - planned_sl) > 0:
            planned_rr = abs(planned_tp - entry) / abs(entry - planned_sl)

        plan: dict[str, Any] = {
            "cid": cid, "session_id": self.session_id, "symbol": symbol, "side": side,
            "timeframe": timeframe, "market_session": market_session(ts_ms),
            "playbook_id": playbook_id, "lots": volume_to_lots(volume, spec), "volume": volume,
            "planned_entry": entry,
            "relative_sl": None if planned_sl is None else int(round(abs(entry - planned_sl) * PRICE_SCALE)),
            "relative_tp": None if planned_tp is None else int(round(abs(planned_tp - entry) * PRICE_SCALE)),
            "planned_sl": planned_sl, "planned_tp": planned_tp, "planned_rr": planned_rr,
            "armed_at": armed_at, "created_at": ts_ms,
        }
        plan.update(record.as_row())
        self.journal.write_plan(plan)
        self.journal.append_event(kind="fill", ts_ms=ts_ms, cid=cid, position_id=position_id,
                                  payload={"entry": entry, "volume": volume, "side": side})

        trade = OpenTrade(cid=cid, position_id=position_id, symbol=symbol, side=side,
                          volume=volume, entry=entry, opened_at=ts_ms, r=record)
        self.open_trades[position_id] = trade
        return trade

    def _r_for(
        self, spec: SymbolSpec, volume: int, entry: float, stop: float | None,
        ts_ms: int, prices: Mapping[int, float],
    ) -> RRecord:
        """R, or the policy fallback when the graph cannot price the quote asset right now."""
        if stop is None or self.graph is None:
            return r_at_entry(volume=volume, entry=entry, stop=None, spec=spec,
                              graph=self.graph, prices=prices, ts_ms=ts_ms,
                              r_unit_usd=self.r_unit_usd)  # type: ignore[arg-type]
        try:
            return r_at_entry(volume=volume, entry=entry, stop=stop, spec=spec, graph=self.graph,
                              prices=prices, ts_ms=ts_ms, r_unit_usd=self.r_unit_usd)
        except ConversionError:
            # Better a recorded policy R than a trade with no measurable risk at all.
            log.warning("%s: no quote-to-USD path at entry; falling back to r_unit_usd", spec.name)
            return r_at_entry(volume=volume, entry=entry, stop=None, spec=spec, graph=self.graph,
                              prices=prices, ts_ms=ts_ms, r_unit_usd=self.r_unit_usd)

    # -- amend and close -------------------------------------------------------------

    def on_amend(self, *, position_id: int, ts_ms: int, sl: float | None, tp: float | None) -> None:
        self.journal.append_event(kind="amend", ts_ms=ts_ms, position_id=position_id,
                                  cid=self._cid_for(position_id), payload={"sl": sl, "tp": tp})

    def on_close(
        self, *, position_id: int, exit_price: float, ts_ms: int, gross_pnl: float | None = None,
        commission: float | None = None, swap: float | None = None,
    ) -> ClosedTrade | None:
        """Write the closed trade and queue its tape window for the post-roll."""
        trade = self.open_trades.pop(position_id, None)
        if trade is None:
            log.warning("close for unknown position %s; recorded as an event only", position_id)
            self.journal.append_event(kind="close", ts_ms=ts_ms, position_id=position_id,
                                      payload={"exit": exit_price})
            return None

        net = self._net_pnl(trade, exit_price, gross_pnl, commission, swap)
        excursions = self._excursions(trade, ts_ms)

        closed = ClosedTrade(
            cid=trade.cid, session_id=self.session_id, position_id=position_id,
            symbol=trade.symbol, side=trade.side,
            lots=volume_to_lots(trade.volume, self.specs[trade.symbol]), volume=trade.volume,
            entry_price=trade.entry, exit_price=exit_price, opened_at=trade.opened_at,
            closed_at=ts_ms, gross_pnl=gross_pnl, commission=commission, swap=swap,
            net_pnl_usd=net, r_usd=trade.r.r_usd, r_multiple=r_multiple(net, trade.r.r_usd),
            mfe=excursions[0], mae=excursions[1],
        )
        self.journal.append_event(kind="close", ts_ms=ts_ms, cid=trade.cid,
                                  position_id=position_id, payload={"exit": exit_price, "pnl": net})
        self.journal.write_closed(closed)
        self._pending_freezes.append((ts_ms + self.post_roll_s * 1000, trade, exit_price))
        return closed

    def _net_pnl(
        self, trade: OpenTrade, exit_price: float, gross: float | None,
        commission: float | None, swap: float | None,
    ) -> float:
        """Prefer the broker's own figures; fall back to price difference when it gave none."""
        if gross is None:
            spec = self.specs[trade.symbol]
            units = trade.volume / 100
            direction = 1 if trade.side.lower() == "buy" else -1
            gross = units * (exit_price - trade.entry) * direction
            if self.graph is not None:
                try:
                    audit = self.graph.quote_to_usd(spec.quote_asset_id, {}, ts_ms=trade.opened_at)
                    gross *= audit.rate
                except ConversionError:
                    pass
        return gross + (commission or 0.0) + (swap or 0.0)

    def _excursions(self, trade: OpenTrade, closed_at: int) -> tuple[float | None, float | None]:
        bars = self.ring.window(trade.symbol, trade.opened_at // 1000, closed_at // 1000)
        if not bars:
            return None, None
        _, result = freeze_window(bars, side=trade.side, entry=trade.entry,
                                  scale=PRICE_SCALE, dt_s=self.dt_s)
        return result.mfe, result.mae

    # -- tape freeze -----------------------------------------------------------------

    def due_freezes(self, now_ms: int | None = None) -> int:
        """Freeze every window whose post-roll has settled. Returns how many were written."""
        now = now_ms if now_ms is not None else int(time.time() * 1000)
        ready = [item for item in self._pending_freezes if item[0] <= now]
        self._pending_freezes = [item for item in self._pending_freezes if item[0] > now]
        for due_at, trade, _exit in ready:
            self._freeze(trade, due_at)
        return len(ready)

    def flush(self, now_ms: int | None = None) -> int:
        """Shutdown and session end: freeze with whatever post-roll exists rather than losing it."""
        now = now_ms if now_ms is not None else int(time.time() * 1000)
        self.ring.flush()
        pending = self._pending_freezes
        self._pending_freezes = []
        for _due_at, trade, _exit in pending:
            self._freeze(trade, now)
        return len(pending)

    def _freeze(self, trade: OpenTrade, until_ms: int) -> None:
        from_ts = trade.opened_at // 1000 - self.pre_roll_s
        to_ts = until_ms // 1000
        bars = self.ring.window(trade.symbol, from_ts, to_ts)
        blob, result = freeze_window(bars, side=trade.side, entry=trade.entry,
                                     scale=PRICE_SCALE, dt_s=self.dt_s)
        self.journal.write_tape(
            cid=trade.cid, position_id=trade.position_id, symbol=trade.symbol,
            from_ts=from_ts, to_ts=to_ts, dt_s=self.dt_s, bars=blob,
            events=self.journal.events_for(trade.position_id),
            mfe=result.mfe, mae=result.mae, created_at=until_ms,
        )

    def _cid_for(self, position_id: int) -> str | None:
        trade = self.open_trades.get(position_id)
        return trade.cid if trade else None
