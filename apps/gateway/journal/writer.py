"""SQLite writes for the phase 2 core: cid ledger, sessions, plans, events,
closed trades, tape.

cTrader is the money source of truth. Balance and equity are **recorded** from
the account, never re-derived by summing fills -- a journal that disagrees with
the broker about money is worse than no journal.
"""

from __future__ import annotations

import sqlite3
import threading
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
    """Single-writer SQLite, serialised.

    The connection is shared across threads (see ``db.migrate.connect``), so
    every statement goes through :meth:`_run` under one lock. Journal writes are
    short and infrequent next to the order path, so a lock costs nothing worth
    measuring and removes a whole class of "works until it doesn't" bug.
    """

    def __init__(self, db_path: str | Path, *, auto_migrate: bool = True) -> None:
        self._lock = threading.RLock()
        self.conn: sqlite3.Connection = connect(db_path)
        if auto_migrate:
            with self._lock:
                migrate(self.conn)

    def _run(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        with self._lock:
            return self.conn.execute(sql, params)

    def close(self) -> None:
        with self._lock:
            self.conn.close()

    # -- cid ledger ---------------------------------------------------------

    def reserve_cid(self, cid: str, kind: str, now_ms: int, sym: str | None = None) -> None:
        """Written PENDING **before** the order leaves the process. A crash
        between here and the broker leaves a pending row, which reconnect
        reconciles against cTrader rather than re-sending blind."""
        try:
            self._run(
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
        self._run(
            "UPDATE cid_ledger SET state = ?, resolved_at = ?, order_id = ?, "
            "position_id = ?, reject_reason = ? WHERE cid = ?",
            (state, now_ms, order_id, position_id, reject_reason, cid),
        )

    def cid_state(self, cid: str) -> str | None:
        row = self._run(
            "SELECT state FROM cid_ledger WHERE cid = ?", (cid,)
        ).fetchone()
        return row["state"] if row else None

    def pending_cids(self) -> list[sqlite3.Row]:
        return self._run(
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
        row = self._run(
            "SELECT id FROM session WHERE trading_day = ?", (trading_day,)
        ).fetchone()
        if row:
            return int(row["id"])
        cur = self._run(
            "INSERT INTO session (trading_day, tz, opened_at, equity_open, "
            "balance_open, currency) VALUES (?, ?, ?, ?, ?, ?)",
            (trading_day, tz, now_ms, equity, balance, currency),
        )
        return int(cur.lastrowid)

    def close_session(
        self, session_id: int, now_ms: int, equity: float | None, balance: float | None
    ) -> None:
        self._run(
            "UPDATE session SET closed_at = ?, equity_close = ?, balance_close = ? "
            "WHERE id = ?",
            (now_ms, equity, balance, session_id),
        )

    def session_row(self, session_id: int) -> sqlite3.Row | None:
        return self._run("SELECT * FROM session WHERE id = ?", (session_id,)).fetchone()

    def set_session_open_equity(
        self, session_id: int, equity: float, balance: float
    ) -> None:
        """Fill the opening equity if it is still unset.

        Written once, on the first snapshot of the evening. A restart mid-session
        must not overwrite the equity the session actually opened at -- that is
        the baseline every P/L figure for the day is measured against.
        """
        self._run(
            "UPDATE session SET equity_open = COALESCE(equity_open, ?), "
            "balance_open = COALESCE(balance_open, ?) WHERE id = ?",
            (equity, balance, session_id),
        )

    def record_equity(
        self,
        session_id: int,
        ts: int,
        equity: float,
        balance: float,
        open_pnl: float = 0.0,
    ) -> None:
        self._run(
            "INSERT OR REPLACE INTO session_equity "
            "(session_id, ts, equity, balance, open_pnl) VALUES (?, ?, ?, ?, ?)",
            (session_id, ts, equity, balance, open_pnl),
        )

    # -- trade --------------------------------------------------------------

    def write_plan(self, plan: PlanRow) -> None:
        fields = list(plan.__dataclass_fields__)
        placeholders = ", ".join("?" for _ in fields)
        self._run(
            f"INSERT INTO trade_plan ({', '.join(fields)}) VALUES ({placeholders})",
            tuple(getattr(plan, f) for f in fields),
        )

    def plan_for_position(self, position_id: int) -> sqlite3.Row | None:
        """The plan behind an open position, found through the cid the order
        was sent with. Returns ``None`` for a position this gateway did not
        open -- one reconciled from cTrader after a restart, say."""
        return self._run(
            "SELECT p.* FROM trade_plan p "
            "JOIN cid_ledger c ON c.cid = p.cid "
            "WHERE c.position_id = ? ORDER BY p.created_at DESC LIMIT 1",
            (position_id,),
        ).fetchone()

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
        self._run(
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
        self._run(
            f"INSERT OR REPLACE INTO trade_closed ({', '.join(fields)}) "
            f"VALUES ({placeholders})",
            tuple(row[f] for f in fields),
        )

    def write_tape(self, position_id: int, cid: str | None, tape: FrozenTape, now_ms: int) -> None:
        self._run(
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

    # -- phase 3: client session ------------------------------------------

    def append_pad_event(self, session_id: int | None, batch: dict[str, Any]) -> None:
        """One row per 1 Hz telemetry batch.

        Phase 9 reads these. Nothing does yet, which is exactly why they are
        written now -- an evening that was not recorded cannot be replayed.
        """
        self._run(
            "INSERT INTO pad_event (session_id, ts, from_state, to_state, sym, "
            "lots, reason, clutch_ms, arm_ms, clutch_cycles, arm_flips, "
            "btn_rate_hz, lot_steps, ttf_ms) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                session_id,
                batch.get("ts", 0),
                batch.get("from"),
                batch.get("to"),
                batch.get("sym"),
                batch.get("lots"),
                batch.get("reason"),
                batch.get("clutchMs", 0),
                batch.get("armMs", 0),
                batch.get("clutchCycles", 0),
                batch.get("armFlips", 0),
                batch.get("btnRateHz", 0.0),
                batch.get("lotStepsSince", 0),
                batch.get("ttfMs"),
            ),
        )

    def ensure_process(self, session_id: int) -> None:
        self._run(
            "INSERT OR IGNORE INTO session_process (session_id) VALUES (?)",
            (session_id,),
        )

    def write_check_in(
        self,
        session_id: int,
        phase: str,
        rating: int | None,
        at: int,
        note: str | None = None,
    ) -> None:
        """The pre/post 1-5 self rating.

        ``rating`` may be ``None``: the check-in is skippable, and a skip is
        recorded as a skip rather than as a missing row, so phase 6 can tell
        "declined" from "never asked".
        """
        if phase not in {"pre", "post"}:
            raise ValueError(f"phase must be pre or post, got {phase!r}")
        self.ensure_process(session_id)
        self._run(
            f"UPDATE session_process SET {phase}_rating = ?, {phase}_at = ?, "
            f"{phase}_note = ? WHERE session_id = ?",
            (rating, at, note, session_id),
        )

    def record_stand_downs(self, session_id: int, events: list[dict[str, Any]]) -> None:
        """The evening's stand-down tally. Phase 11's Selectivity axis reads
        this rather than counting its own."""
        import json

        self.ensure_process(session_id)
        self._run(
            "UPDATE session_process SET stand_downs = ?, stand_down_json = ? "
            "WHERE session_id = ?",
            (len(events), json.dumps(events, separators=(",", ":")), session_id),
        )

    def process_row(self, session_id: int) -> sqlite3.Row | None:
        return self._run(
            "SELECT * FROM session_process WHERE session_id = ?", (session_id,)
        ).fetchone()

    def update_excursion(
        self,
        position_id: int,
        *,
        mfe: float,
        mae: float,
        mfe_r: float | None,
        mae_r: float | None,
    ) -> None:
        """MFE/MAE land after the trade closes, once the post-roll has elapsed
        and the tape is frozen -- so they are an update, not part of the insert
        that had to happen at close time."""
        self._run(
            "UPDATE trade_closed SET mfe = ?, mae = ?, mfe_r = ?, mae_r = ? "
            "WHERE position_id = ?",
            (mfe, mae, mfe_r, mae_r, position_id),
        )

    # -- phase 7: playbook and grading -------------------------------------

    def write_grade(
        self,
        cid: str,
        playbook_id: int | None,
        session_id: int | None,
        phase: str,
        grade: Any,
        now_ms: int,
    ) -> None:
        """Keyed on the cid -- one fire -- not on a closed position, because a
        declined or rejected fire is gradeable too and phase 6's declined count
        depends on that. Re-grading the same cid at a later phase replaces the
        earlier row."""
        self._run(
            "INSERT OR REPLACE INTO trade_grade (cid, playbook_id, session_id, "
            "evaluated_at, phase, results_json, required_pass, required_total, clean) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (cid, playbook_id, session_id, now_ms, phase, grade.results_json(),
             grade.required_pass, grade.required_total, int(grade.clean)),
        )

    def grade_row(self, cid: str) -> sqlite3.Row | None:
        return self._run("SELECT * FROM trade_grade WHERE cid = ?", (cid,)).fetchone()

    def set_active_playbook(self, session_id: int, playbook_id: int | None) -> None:
        self.ensure_process(session_id)
        self._run(
            "UPDATE session_process SET playbook_id = ? WHERE session_id = ?",
            (playbook_id, session_id),
        )

    # -- phase 9: tilt ------------------------------------------------------

    def append_tilt(self, session_id: int | None, ts: int, tilt: Any) -> None:
        """A sample for the deck. Scoped to a session on purpose -- tilt is
        never stored as a property of the player."""
        import json

        self._run(
            "INSERT INTO tilt_sample (session_id, ts, score, band, top_json, "
            "components_json, cooldown_until) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                session_id, ts, tilt.score, tilt.band,
                json.dumps(list(tilt.top), separators=(",", ":")),
                json.dumps({c.key: round(c.score, 4) for c in tilt.components},
                           separators=(",", ":")),
                tilt.cooldown_until_ms,
            ),
        )

    def recent_grade_breaks(self, session_id: int | None, limit: int = 3) -> list[bool]:
        """Did each of the last few fires break a required rule? Phase 7's
        grades, read rather than recomputed."""
        rows = self._run(
            "SELECT required_pass, required_total FROM trade_grade "
            "WHERE session_id IS ? AND phase != 'arm' "
            "ORDER BY evaluated_at DESC LIMIT ?",
            (session_id, limit),
        ).fetchall()
        return [r["required_pass"] < r["required_total"] for r in reversed(rows)]

    def session_lots(self, session_id: int | None) -> list[float]:
        rows = self._run(
            "SELECT lots FROM trade_plan WHERE session_id IS ?", (session_id,)
        ).fetchall()
        return [float(r["lots"]) for r in rows]

    def last_losing_close_ms(self, session_id: int | None) -> int | None:
        row = self._run(
            "SELECT closed_at FROM trade_closed WHERE session_id IS ? AND net_pnl < 0 "
            "ORDER BY closed_at DESC LIMIT 1",
            (session_id,),
        ).fetchone()
        return int(row["closed_at"]) if row else None

    # -- phase 11: process score -------------------------------------------

    def write_score(self, session_id: int, now_ms: int, score: Any) -> None:
        import json

        self._run(
            "INSERT OR REPLACE INTO score_session (session_id, settled_at, total, "
            "axes_json, na_json, items_json, weights_version) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                session_id, now_ms, score.total,
                # Only axes with evidence. `na_json` lists the rest, so an axis
                # never appears in both -- the radar draws a dashed ring from
                # `na`, never a null spoke from here.
                json.dumps(
                    {a.key: a.value for a in score.axes if a.value is not None},
                    separators=(",", ":"),
                ),
                json.dumps(list(score.na), separators=(",", ":")),
                json.dumps(
                    [
                        {"axis": a.key, "key": i.key, "label": i.label,
                         "ok": i.ok, "note": i.note}
                        for a in score.axes for i in a.items
                    ],
                    separators=(",", ":"),
                ),
                score.weights_version,
            ),
        )

    def score_row(self, session_id: int) -> sqlite3.Row | None:
        return self._run(
            "SELECT * FROM score_session WHERE session_id = ?", (session_id,)
        ).fetchone()

    def grade_totals(self, session_id: int | None) -> tuple[int, int, int]:
        """(fires, required_passed, required_evaluated) for tonight."""
        row = self._run(
            "SELECT COUNT(*) n, COALESCE(SUM(required_pass), 0) p, "
            "COALESCE(SUM(required_total), 0) t FROM trade_grade "
            "WHERE session_id IS ? AND phase != 'arm'",
            (session_id,),
        ).fetchone()
        return int(row["n"]), int(row["p"]), int(row["t"])

    def risk_adherence(self, session_id: int | None) -> tuple[int, int]:
        """Per-fire risk checks passed over evaluated.

        Derived from the plan rather than re-judged: a plan exists only for a
        fire the gateway's own risk rules already allowed, so the question left
        is whether the player protected it -- a stop at entry, and an R the
        stop actually defined rather than the fallback unit.
        """
        rows = self._run(
            "SELECT planned_sl, r_source FROM trade_plan WHERE session_id IS ?",
            (session_id,),
        ).fetchall()
        if not rows:
            return 0, 0
        evaluated = len(rows) * 2
        passed = 0
        for r in rows:
            if r["planned_sl"] is not None:
                passed += 1
            if r["r_source"] == "stop":
                passed += 1
        return passed, evaluated

    def has_replayable_trade(self) -> bool:
        row = self._run("SELECT 1 FROM trade_tape LIMIT 1").fetchone()
        return row is not None

    def day_loss_usd(self, session_id: int) -> float:
        """Realised loss so far today, as a positive number. Feeds the
        ``max_daily_loss`` rule."""
        row = self._run(
            "SELECT COALESCE(SUM(net_pnl), 0) AS pnl FROM trade_closed "
            "WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        pnl = float(row["pnl"])
        return -pnl if pnl < 0 else 0.0
