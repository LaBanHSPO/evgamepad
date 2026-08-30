"""SQLite writes for the phase 2 core: cid ledger, sessions, plans, events,
closed trades, tape.

cTrader is the money source of truth. Balance and equity are **recorded** from
the account, never re-derived by summing fills -- a journal that disagrees with
the broker about money is worse than no journal.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..db.migrate import connect, migrate
from .tape.freeze import FrozenTape


class DuplicateCid(RuntimeError):
    """The cid is already reserved. This is the guard that stops a retry, a
    double-press, or a reboot replay from opening a second position."""


@dataclass(frozen=True)
class PlanRow:
    cid: str
    session_id: int | None
    created_at: int
    sym: str
    side: str
    lots: float
    protocol_volume: int
    r_usd: float
    r_source: str
    timeframe: str | None = None
    market_session: str | None = None
    playbook_id: str | None = None
    setup: str | None = None
    planned_entry: float | None = None
    relative_sl: int | None = None
    relative_tp: int | None = None
    planned_sl: float | None = None
    planned_tp: float | None = None
    planned_rr: float | None = None
    r_rate: float | None = None
    r_rate_chain: str | None = None
    r_rate_ts: int | None = None
    armed_at: int | None = None
    time_to_fire_ms: int | None = None


class JournalWriter:
    def __init__(self, db_path: str | Path, *, auto_migrate: bool = True) -> None:
        self.conn: sqlite3.Connection = connect(db_path)
        if auto_migrate:
            migrate(self.conn)

    def close(self) -> None:
        self.conn.close()

    # -- cid ledger ---------------------------------------------------------

    def reserve_cid(self, cid: str, kind: str, now_ms: int, sym: str | None = None) -> None:
        """Written PENDING **before** the order leaves the process. A crash
        between here and the broker leaves a pending row, which reconnect
        reconciles against cTrader rather than re-sending blind."""
        try:
            self.conn.execute(
                "INSERT INTO cid_ledger (cid, kind, state, sym, reserved_at) "
                "VALUES (?, ?, 'pending', ?, ?)",
                (cid, kind, sym, now_ms),
            )
        except sqlite3.IntegrityError:
            raise DuplicateCid(cid) from None

    def mark_cid(
        self,
        cid: str,
        state: str,
        now_ms: int,
        *,
        order_id: int | None = None,
        position_id: int | None = None,
        reject_reason: str | None = None,
    ) -> None:
        self.conn.execute(
            "UPDATE cid_ledger SET state = ?, resolved_at = ?, order_id = ?, "
            "position_id = ?, reject_reason = ? WHERE cid = ?",
            (state, now_ms, order_id, position_id, reject_reason, cid),
        )

    def cid_state(self, cid: str) -> str | None:
        row = self.conn.execute(
            "SELECT state FROM cid_ledger WHERE cid = ?", (cid,)
        ).fetchone()
        return row["state"] if row else None

    def pending_cids(self) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM cid_ledger WHERE state IN ('pending','sent') "
            "ORDER BY reserved_at"
        ).fetchall()

    # -- session ------------------------------------------------------------

    def open_session(
        self,
        trading_day: str,
        tz: str,
        now_ms: int,
        *,
        equity: float | None = None,
        balance: float | None = None,
        currency: str = "USD",
    ) -> int:
        row = self.conn.execute(
            "SELECT id FROM session WHERE trading_day = ?", (trading_day,)
        ).fetchone()
        if row:
            return int(row["id"])
        cur = self.conn.execute(
            "INSERT INTO session (trading_day, tz, opened_at, equity_open, "
            "balance_open, currency) VALUES (?, ?, ?, ?, ?, ?)",
            (trading_day, tz, now_ms, equity, balance, currency),
        )
        return int(cur.lastrowid)

    def close_session(
        self, session_id: int, now_ms: int, equity: float | None, balance: float | None
    ) -> None:
        self.conn.execute(
            "UPDATE session SET closed_at = ?, equity_close = ?, balance_close = ? "
            "WHERE id = ?",
            (now_ms, equity, balance, session_id),
        )

    def record_equity(
        self,
        session_id: int,
        ts: int,
        equity: float,
        balance: float,
        open_pnl: float = 0.0,
    ) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO session_equity "
            "(session_id, ts, equity, balance, open_pnl) VALUES (?, ?, ?, ?, ?)",
            (session_id, ts, equity, balance, open_pnl),
        )

    # -- trade --------------------------------------------------------------

    def write_plan(self, plan: PlanRow) -> None:
        fields = list(plan.__dataclass_fields__)
        placeholders = ", ".join("?" for _ in fields)
        self.conn.execute(
            f"INSERT INTO trade_plan ({', '.join(fields)}) VALUES ({placeholders})",
            tuple(getattr(plan, f) for f in fields),
        )

    def append_event(
        self,
        position_id: int,
        ts: int,
        kind: str,
        *,
        cid: str | None = None,
        price: float | None = None,
        lots: float | None = None,
        sl: float | None = None,
        tp: float | None = None,
        detail: str | None = None,
    ) -> None:
        self.conn.execute(
            "INSERT INTO position_event "
            "(position_id, cid, ts, kind, price, lots, sl, tp, detail) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (position_id, cid, ts, kind, price, lots, sl, tp, detail),
        )

    def write_closed(self, row: dict[str, Any]) -> None:
        """One row per full close. ``r_multiple`` is NOT NULL by schema, so a
        caller that forgot to compute R fails here rather than shipping a
        null into the deck."""
        fields = list(row)
        placeholders = ", ".join("?" for _ in fields)
        self.conn.execute(
            f"INSERT OR REPLACE INTO trade_closed ({', '.join(fields)}) "
            f"VALUES ({placeholders})",
            tuple(row[f] for f in fields),
        )

    def write_tape(self, position_id: int, cid: str | None, tape: FrozenTape, now_ms: int) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO trade_tape (position_id, cid, sym, from_ts, "
            "to_ts, dt_s, n, digits, bars_gz, events_json, frozen_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                position_id,
                cid,
                tape.sym,
                tape.from_ts,
                tape.to_ts,
                tape.dt_s,
                tape.n,
                tape.digits,
                tape.bars_gz,
                tape.events_json,
                now_ms,
            ),
        )

    def day_loss_usd(self, session_id: int) -> float:
        """Realised loss so far today, as a positive number. Feeds the
        ``max_daily_loss`` rule."""
        row = self.conn.execute(
            "SELECT COALESCE(SUM(net_pnl), 0) AS pnl FROM trade_closed "
            "WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        pnl = float(row["pnl"])
        return -pnl if pnl < 0 else 0.0
