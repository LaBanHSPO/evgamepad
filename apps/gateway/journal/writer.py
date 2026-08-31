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
            "setup_tag", "inside_window", "positions_at_fire", "seconds_to_high_impact",
            "max_lots_at_fire", "max_positions_at_fire",
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

    # -- client session (phase 3) ----------------------------------------------------

    def write_pad_event(self, session_id: str | None, sample: dict[str, Any]) -> None:
        """One 1 Hz telemetry batch. Phase 9 reads these; nothing else does."""
        self.conn.execute(
            "INSERT INTO pad_event (session_id, ts, from_phase, to_phase, reason, symbol, lots, "
            "clutch_ms, arm_ms, clutch_cycles, arm_flips, btn_rate_hz, lot_steps, ttf_ms) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                session_id, sample.get("ts", 0), str(sample.get("from", "")),
                str(sample.get("to", "")), sample.get("reason"), sample.get("sym"),
                sample.get("lots"), sample.get("clutchMs", 0), sample.get("armMs", 0),
                sample.get("clutchCycles", 0), sample.get("armFlips", 0),
                sample.get("btnRateHz", 0.0), sample.get("lotStepsSince", 0), sample.get("ttfMs"),
            ),
        )

    def write_checkin(
        self, session_id: str, *, phase: str, rating: int | None, ts_ms: int
    ) -> None:
        """Pre/post self-rating. A null rating records a deliberate skip, not a low score."""
        column = "pre" if phase == "pre" else "post"
        self.conn.execute(
            "INSERT INTO session_process (session_id) VALUES (?) "
            "ON CONFLICT (session_id) DO NOTHING",
            (session_id,),
        )
        self.conn.execute(
            f"UPDATE session_process SET {column}_rating = ?, {column}_at = ? WHERE session_id = ?",
            (rating, ts_ms, session_id),
        )

    def increment_stood_down(self, session_id: str) -> int:
        """A cancelled arm under a stand-down condition. Phase 11's Selectivity axis reuses this."""
        self.conn.execute(
            "INSERT INTO session_process (session_id) VALUES (?) "
            "ON CONFLICT (session_id) DO NOTHING",
            (session_id,),
        )
        self.conn.execute(
            "UPDATE session_process SET stood_down_count = stood_down_count + 1 WHERE session_id = ?",
            (session_id,),
        )
        row = self.conn.execute(
            "SELECT stood_down_count FROM session_process WHERE session_id = ?", (session_id,)
        ).fetchone()
        return int(row[0]) if row else 0

    def process_row(self, session_id: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT session_id, pre_rating, pre_at, post_rating, post_at, stood_down_count "
            "FROM session_process WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        if row is None:
            return None
        keys = ("session_id", "pre_rating", "pre_at", "post_rating", "post_at", "stood_down_count")
        return dict(zip(keys, row, strict=True))

    # -- tilt (phase 9) ----------------------------------------------------------------

    def write_tilt_sample(self, row: dict[str, Any]) -> None:
        """One sample. Tilt is never stored as a trait — this is a record of an evening."""
        self.conn.execute(
            "INSERT INTO tilt_sample (session_id, ts, score, band, components, missing, "
            "top_driver) VALUES (?,?,?,?,?,?,?)",
            (row["session_id"], row["ts"], row["score"], row["band"], row["components"],
             row["missing"], row["top_driver"]),
        )

    def tilt_samples(self, session_id: str) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT ts, score, band, top_driver FROM tilt_sample WHERE session_id = ? ORDER BY ts",
            (session_id,),
        ).fetchall()
        return [{"ts": r[0], "score": r[1], "band": r[2], "topDriver": r[3]} for r in rows]

    # -- playbooks and grading (phase 7) -----------------------------------------------

    def upsert_playbook(self, playbook: dict[str, Any], rules: list[dict[str, Any]]) -> None:
        """Write a playbook and replace its rule list. Retiring is a separate, softer act."""
        self.conn.execute(
            "INSERT INTO playbook (id, name, slug, method, symbols, detector_tag, narrative, "
            "active, created_at, retired_at) VALUES (?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT (id) DO UPDATE SET name=excluded.name, slug=excluded.slug, "
            "method=excluded.method, symbols=excluded.symbols, "
            "detector_tag=excluded.detector_tag, narrative=excluded.narrative, "
            "active=excluded.active",
            (
                playbook["id"], playbook["name"], playbook["slug"],
                playbook.get("method", "volman_m5"),
                json.dumps(list(playbook.get("symbols", []))),
                playbook.get("detector_tag"), playbook.get("narrative"),
                int(playbook.get("active", True)), playbook.get("created_at", 0),
                playbook.get("retired_at"),
            ),
        )
        self.conn.execute("DELETE FROM playbook_rule WHERE playbook_id = ?", (playbook["id"],))
        for rule in rules:
            self.conn.execute(
                "INSERT INTO playbook_rule (playbook_id, ord, kind, code, params, label, required) "
                "VALUES (?,?,?,?,?,?,?)",
                (playbook["id"], rule.get("ord", 0), rule.get("kind", "auto"), rule["code"],
                 json.dumps(rule.get("params", {}), sort_keys=True), rule.get("label"),
                 int(rule.get("required", True))),
            )

    def playbooks(self, *, include_retired: bool = False) -> list[dict[str, Any]]:
        """Playbooks and their rules. Retired ones stay resolvable so old grades still read."""
        where = "" if include_retired else "WHERE retired_at IS NULL AND active = 1"
        books = self.conn.execute(
            f"SELECT id, name, slug, method, symbols, detector_tag, narrative, active, "
            f"created_at, retired_at FROM playbook {where} ORDER BY created_at, name"
        ).fetchall()
        keys = ("id", "name", "slug", "method", "symbols", "detector_tag", "narrative", "active",
                "created_at", "retired_at")
        out: list[dict[str, Any]] = []
        for row in books:
            book = dict(zip(keys, row, strict=True))
            book["symbols"] = json.loads(book["symbols"] or "[]")
            book["active"] = bool(book["active"])
            book["rules"] = [
                {"ord": r[0], "kind": r[1], "code": r[2], "params": json.loads(r[3]),
                 "label": r[4], "required": bool(r[5])}
                for r in self.conn.execute(
                    "SELECT ord, kind, code, params, label, required FROM playbook_rule "
                    "WHERE playbook_id = ? ORDER BY ord",
                    (book["id"],),
                )
            ]
            out.append(book)
        return out

    def retire_playbook(self, playbook_id: str, *, ts_ms: int) -> bool:
        """Hide a playbook from selection without deleting it — the deck must not lose a month."""
        cursor = self.conn.execute(
            "UPDATE playbook SET retired_at = ?, active = 0 WHERE id = ? AND retired_at IS NULL",
            (ts_ms, playbook_id),
        )
        return cursor.rowcount > 0

    def write_grade(self, row: dict[str, Any]) -> None:
        """One grade per cid. A re-grade at FIRE replaces the ARM row for the same fire."""
        self.conn.execute(
            "INSERT INTO trade_grade (cid, playbook_id, stage, evaluated_at, results, "
            "required_pass, required_total, clean) VALUES (?,?,?,?,?,?,?,?) "
            "ON CONFLICT (cid) DO UPDATE SET stage=excluded.stage, "
            "evaluated_at=excluded.evaluated_at, results=excluded.results, "
            "required_pass=excluded.required_pass, required_total=excluded.required_total, "
            "clean=excluded.clean",
            (row["cid"], row["playbook_id"], row["stage"], row["evaluated_at"], row["results"],
             row["required_pass"], row["required_total"], row["clean"]),
        )

    def grade_for(self, cid: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT cid, playbook_id, stage, evaluated_at, results, required_pass, "
            "required_total, clean FROM trade_grade WHERE cid = ?",
            (cid,),
        ).fetchone()
        if row is None:
            return None
        keys = ("cid", "playbook_id", "stage", "evaluated_at", "results", "required_pass",
                "required_total", "clean")
        grade = dict(zip(keys, row, strict=True))
        grade["results"] = json.loads(grade["results"])
        grade["clean"] = bool(grade["clean"])
        return grade

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
