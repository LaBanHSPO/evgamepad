"""Journal writes: the cid ledger, session equity, plans, position events, closes, and tape.

Two rules run through all of it. **cTrader is the money source of truth** — balance and equity are
snapshots taken from the account, never sums of local fills. And **the cid ledger is reserved
before the order is sent**, so a retry, a reconnect replay, or a double-fire collides on a UNIQUE
constraint instead of opening a second position.

Every statement is parameterised; nothing here interpolates a value into SQL.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Any

PENDING = "pending"
ACKED = "acked"
REJECTED = "rejected"


@dataclass(frozen=True)
class ClosedTrade:
    """The facts phase 6 measures. `r_multiple` is non-null for every closed trade."""

    cid: str
    session_id: str | None
    position_id: int
    symbol: str
    side: str
    lots: float
    volume: int
    entry_price: float | None
    exit_price: float | None
    opened_at: int | None
    closed_at: int
    gross_pnl: float | None
    commission: float | None
    swap: float | None
    net_pnl_usd: float | None
    r_usd: float
    r_multiple: float
    mfe: float | None = None
    mae: float | None = None
    adherence: float | None = None


class JournalWriter:
    """Owns every write to the journal DB. Holds no broker state and makes no network call."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    # -- cid ledger ------------------------------------------------------------------

    def reserve_cid(self, cid: str, *, intent: str, symbol: str | None, ts_ms: int) -> bool:
        """Claim a cid before sending. Returns False when it was already claimed.

        A False here is the duplicate-fire guard doing its job — the caller acks the original
        rather than sending a second order.
        """
        try:
            self.conn.execute(
                "INSERT INTO cid_reservation (cid, intent, symbol, state, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (cid, intent, symbol, PENDING, ts_ms, ts_ms),
            )
        except sqlite3.IntegrityError:
            return False
        return True

    def settle_cid(
        self,
        cid: str,
        *,
        state: str,
        ts_ms: int,
        reason: str | None = None,
        order_id: int | None = None,
        position_id: int | None = None,
    ) -> None:
        self.conn.execute(
            "UPDATE cid_reservation SET state = ?, reason = ?, order_id = ?, position_id = ?, "
            "updated_at = ? WHERE cid = ?",
            (state, reason, order_id, position_id, ts_ms, cid),
        )

    def cid_state(self, cid: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT cid, intent, symbol, state, reason, order_id, position_id FROM cid_reservation "
            "WHERE cid = ?",
            (cid,),
        ).fetchone()
        if row is None:
            return None
        keys = ("cid", "intent", "symbol", "state", "reason", "order_id", "position_id")
        return dict(zip(keys, row, strict=True))

    def pending_cids(self) -> list[str]:
        """Claims that never settled — what a reboot has to reconcile against the broker."""
        return [
            r[0]
            for r in self.conn.execute(
                "SELECT cid FROM cid_reservation WHERE state = ? ORDER BY created_at", (PENDING,)
            )
        ]

    # -- session equity --------------------------------------------------------------

    def open_session(
        self, session_id: str, *, timezone: str, opened_at: int,
        balance: float | None, equity: float | None,
    ) -> None:
        """Snapshot the account at session open. Figures come from cTrader, not from us."""
        self.conn.execute(
            "INSERT OR IGNORE INTO session_equity "
            "(session_id, timezone, opened_at, balance_open, equity_open) VALUES (?, ?, ?, ?, ?)",
            (session_id, timezone, opened_at, balance, equity),
        )

    def close_session(
        self, session_id: str, *, closed_at: int, balance: float | None, equity: float | None
    ) -> None:
        self.conn.execute(
            "UPDATE session_equity SET closed_at = ?, balance_close = ?, equity_close = ? "
            "WHERE session_id = ?",
            (closed_at, balance, equity, session_id),
        )

    def session_row(self, session_id: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT session_id, timezone, opened_at, closed_at, balance_open, equity_open, "
            "balance_close, equity_close FROM session_equity WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        if row is None:
            return None
        keys = ("session_id", "timezone", "opened_at", "closed_at", "balance_open",
                "equity_open", "balance_close", "equity_close")
        return dict(zip(keys, row, strict=True))

    # -- trade plan, events, close ----------------------------------------------------

    def write_plan(self, plan: dict[str, Any]) -> None:
        """The plan as it stood at FIRE, including R and the conversion that produced it."""
        columns = (
            "cid", "session_id", "symbol", "side", "timeframe", "market_session", "playbook_id",
            "lots", "volume", "planned_entry", "relative_sl", "relative_tp", "planned_sl",
            "planned_tp", "planned_rr", "r_usd", "r_method", "r_units", "r_stop_distance",
            "r_rate", "r_rate_chain", "r_rate_source", "r_rate_ts", "armed_at", "created_at",
        )
        placeholders = ", ".join("?" for _ in columns)
        self.conn.execute(
            f"INSERT INTO trade_plan ({', '.join(columns)}) VALUES ({placeholders})",
            tuple(plan.get(c) for c in columns),
        )

    def append_event(
        self, *, kind: str, ts_ms: int, cid: str | None = None,
        position_id: int | None = None, payload: dict[str, Any] | None = None,
    ) -> None:
        """Append-only. Nothing in this table is ever updated in place."""
        self.conn.execute(
            "INSERT INTO position_event (cid, position_id, kind, payload, ts) VALUES (?, ?, ?, ?, ?)",
            (cid, position_id, kind, json.dumps(payload or {}, sort_keys=True), ts_ms),
        )

    def events_for(self, position_id: int) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT kind, payload, ts FROM position_event WHERE position_id = ? ORDER BY ts, id",
            (position_id,),
        ).fetchall()
        return [{"kind": k, "payload": json.loads(p), "ts": t} for k, p, t in rows]

    def write_closed(self, trade: ClosedTrade) -> None:
        columns = (
            "cid", "session_id", "position_id", "symbol", "side", "lots", "volume", "entry_price",
            "exit_price", "opened_at", "closed_at", "gross_pnl", "commission", "swap",
            "net_pnl_usd", "r_usd", "r_multiple", "mfe", "mae", "adherence",
        )
        placeholders = ", ".join("?" for _ in columns)
        self.conn.execute(
            f"INSERT INTO trade_closed ({', '.join(columns)}) VALUES ({placeholders})",
            tuple(getattr(trade, c) for c in columns),
        )

    def write_tape(
        self, *, cid: str, position_id: int | None, symbol: str, from_ts: int, to_ts: int,
        dt_s: int, bars: bytes, events: list[dict[str, Any]], mfe: float | None,
        mae: float | None, created_at: int,
    ) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO trade_tape (cid, position_id, symbol, from_ts, to_ts, dt_s, "
            "bars, events, mfe, mae, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (cid, position_id, symbol, from_ts, to_ts, dt_s, bars,
             json.dumps(events, sort_keys=True), mfe, mae, created_at),
        )
