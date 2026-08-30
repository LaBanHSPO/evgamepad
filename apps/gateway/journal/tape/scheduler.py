"""Freeze a trade's tape once its post-roll has elapsed.

The ring is always running; nothing is persisted until a position closes. At
``closed_at + tape.post_roll_s`` this cuts the window out of the ring, computes
MFE/MAE from the bars the position was actually open for, and writes one
``trade_tape`` row.

Two failure modes shape the design:

* **The gateway shuts down inside a post-roll window.** Every pending freeze is
  flushed with whatever post-roll exists rather than lost -- ``n`` is stored, so
  a short window renders as a short window instead of missing data.
* **The ring has already rolled past the window.** A 90-minute ring cannot hold
  a trade that closed two hours ago, so a freeze that arrives too late writes
  what it can and says how much it got.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from decimal import Decimal

from .freeze import Excursion, excursion, freeze, in_trade
from .ring import TapeRing

log = logging.getLogger("ev.tape")


@dataclass(frozen=True)
class PendingFreeze:
    position_id: int
    cid: str | None
    sym: str
    side: str
    entry: float
    digits: int
    opened_at: int
    closed_at: int
    r_usd: float
    protocol_volume: int
    r_rate: float


def r_per_price(pending: PendingFreeze) -> float | None:
    """How much price movement is one R, for expressing MFE/MAE in R.

    Inverts ``risk/r.py``: ``r_usd = units * distance * rate``, so
    ``distance = r_usd / (units * rate)``. Derived rather than stored, because
    storing it would be a second place R could drift.
    """
    units = Decimal(pending.protocol_volume) / Decimal(100)
    rate = Decimal(str(pending.r_rate or 1.0))
    if units <= 0 or rate <= 0:
        return None
    return float(Decimal(str(pending.r_usd)) / (units * rate))


class FreezeScheduler:
    """Owns the timers and the flush-on-shutdown guarantee."""

    def __init__(
        self,
        ring: TapeRing,
        writer,
        *,
        pre_roll_s: int,
        post_roll_s: int,
        dt_s: int,
    ) -> None:
        self.ring = ring
        self.writer = writer
        self.pre_roll_s = pre_roll_s
        self.post_roll_s = post_roll_s
        self.dt_s = dt_s
        self._tasks: dict[int, asyncio.Task] = {}
        self._pending: dict[int, PendingFreeze] = {}

    def schedule(self, pending: PendingFreeze, now_ms: int) -> None:
        """Queue a freeze for after the post-roll. Re-closing the same position
        replaces the pending freeze rather than adding a second."""
        self.cancel(pending.position_id)
        self._pending[pending.position_id] = pending

        delay = max(0.0, (pending.closed_at + self.post_roll_s * 1000 - now_ms) / 1000)
        try:
            self._tasks[pending.position_id] = asyncio.create_task(
                self._wait_and_freeze(pending, delay)
            )
        except RuntimeError:
            # No running loop (a test, a synchronous shutdown path). Freeze now
            # rather than silently dropping the tape.
            self.flush_one(pending)

    def cancel(self, position_id: int) -> None:
        task = self._tasks.pop(position_id, None)
        if task is not None:
            task.cancel()
        self._pending.pop(position_id, None)

    async def _wait_and_freeze(self, pending: PendingFreeze, delay: float) -> None:
        try:
            await asyncio.sleep(delay)
        except asyncio.CancelledError:
            return
        self._tasks.pop(pending.position_id, None)
        self._pending.pop(pending.position_id, None)
        self.flush_one(pending)

    def flush_one(self, pending: PendingFreeze) -> Excursion | None:
        """Cut the window, measure the excursion, write both rows."""
        ring = self.ring.ring(pending.sym)
        if ring is None:
            log.warning("no tape ring for %s; position %s", pending.sym, pending.position_id)
            return None

        # Seal so a freeze inside the current second still sees it.
        ring.seal()
        bars = ring.bars()

        tape = freeze(
            sym=pending.sym,
            bars=bars,
            opened_at_ms=pending.opened_at,
            closed_at_ms=pending.closed_at,
            pre_roll_s=self.pre_roll_s,
            post_roll_s=self.post_roll_s,
            dt_s=self.dt_s,
            digits=pending.digits,
            events=[
                {"kind": "open", "ts": pending.opened_at, "price": pending.entry},
                {"kind": "close", "ts": pending.closed_at},
            ],
        )
        self.writer.write_tape(pending.position_id, pending.cid, tape, pending.closed_at)

        # Excursion is measured over the bars the position was open for. The
        # pre/post roll is context for the replay, not risk that was taken.
        window = in_trade(bars, pending.opened_at, pending.closed_at)
        ex = excursion(window, side=pending.side, entry=pending.entry, digits=pending.digits)

        per_r = r_per_price(pending)
        mfe_r = mae_r = None
        if per_r and per_r > 0:
            mfe_r, mae_r = ex.in_r(per_r)

        self.writer.update_excursion(
            pending.position_id, mfe=ex.mfe, mae=ex.mae, mfe_r=mfe_r, mae_r=mae_r
        )
        log.info(
            "froze tape for position %s: %s bars, mfe %.5f mae %.5f",
            pending.position_id, tape.n, ex.mfe, ex.mae,
        )
        return ex

    async def flush_all(self) -> int:
        """Freeze everything still waiting, now.

        Called on shutdown and at session end. A trade with no tape because the
        process stopped inside its post-roll is the failure this prevents.
        """
        pending = list(self._pending.values())
        for task in self._tasks.values():
            task.cancel()
        self._tasks.clear()
        self._pending.clear()
        for item in pending:
            try:
                self.flush_one(item)
            except Exception:
                log.exception("flush failed for position %s", item.position_id)
        return len(pending)

    @property
    def pending_count(self) -> int:
        return len(self._pending)
