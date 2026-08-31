"""Assembling the Process Score's inputs out of rows the other phases already wrote.

Phase 11 captures almost nothing new. Adherence comes from phase 7's grades, risk discipline from
the plan rows phase 2 froze at fire time, selectivity from phase 4's sentinel, declines from phase
3's stand-down counter, and the review evidence from the check-ins and the replay opens. The only
genuinely new capture is that a replay open is recorded at all.

Two things this module refuses to do, both for the same reason — a number you cannot audit is a
number you end up arguing with:

- It never reconstructs a fire's risk context from today's config. `trade_plan` froze the caps that
  were in force at the moment of the fire, and those are what the fire is scored against.
- It never stores only the total. The inputs go into the row, so changing `score.weights` recomputes
  every past evening rather than mixing two weightings in one chart.
"""

from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from score.session import (
    WEIGHTS_VERSION,
    FireInputs,
    SessionInputs,
    SessionScore,
    score_session,
)

# How far a fire's recorded R may sit from the configured unit before it stops counting as
# disciplined. Sizing is stepwise on a pad, so an exact match was never the bar.
R_TOLERANCE = 0.25

# Whether the build can actually capture a memo. `voice.enabled` says the feature is *wanted*;
# this says it *exists*. Phase 8 is deferred, so no capture path is wired, and treating a memo as
# a miss would score the install rather than the evening — which the plan explicitly forbids.
# Phase 8 flips this to True when it lands.
VOICE_CAPTURE_BUILT = False


@dataclass
class ScoreRepository:
    """`GET /api/score/*`, and the session-close write behind it."""

    db_path: Path
    trades_max: int = 6
    band_width: float = 1
    decline_credit_max: float = 15
    weights: dict[str, float] | None = None
    r_unit_usd: float = 20.0
    min_seconds_between_orders: float = 2.0
    voice_available: bool = False

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # -- inputs ------------------------------------------------------------------------

    def inputs_for(self, session_id: str) -> SessionInputs:
        """Everything `score_session` reads, gathered from the evening's own rows."""
        conn = self._connect()
        try:
            fires = self._fires(conn, session_id)
            process = conn.execute(
                "SELECT pre_rating, pre_at, post_rating, post_at, stood_down_count, "
                "opportunity_quality FROM session_process WHERE session_id = ?", (session_id,)
            ).fetchone()
            plan = conn.execute(
                "SELECT created_at FROM session_plan WHERE session_id = ?", (session_id,)
            ).fetchone()
            first_fire = conn.execute(
                "SELECT MIN(created_at) FROM trade_plan WHERE session_id = ?", (session_id,)
            ).fetchone()[0]
            replays = conn.execute(
                "SELECT COUNT(DISTINCT cid) FROM review_event "
                "WHERE session_id = ? AND kind = 'replay_open'", (session_id,)
            ).fetchone()[0]
            # A first session has no past trade to replay. Asking for one would be an impossible
            # requirement, so the item is dropped rather than failed.
            past_trades = conn.execute(
                "SELECT COUNT(*) FROM trade_closed WHERE session_id IS NOT ?", (session_id,)
            ).fetchone()[0]
            playbook_used = conn.execute(
                "SELECT COUNT(*) FROM trade_plan WHERE session_id = ? AND playbook_id IS NOT NULL",
                (session_id,),
            ).fetchone()[0]
        finally:
            conn.close()

        # The plan counts as acknowledged only if it existed *before* the first fire. A plan
        # written afterwards is a note, not preparation.
        acknowledged = plan is not None and (
            first_fire is None or plan["created_at"] <= first_fire
        )

        return SessionInputs(
            session_id=session_id,
            fires=fires,
            oq_mean=None if process is None else process["opportunity_quality"],
            declines=0 if process is None else int(process["stood_down_count"] or 0),
            plan_acknowledged=acknowledged,
            pre_checkin=process is not None and process["pre_at"] is not None,
            playbook_selected=playbook_used > 0,
            # Phase 8 is deferred, so no memo exists to find. `voice_available` being false is what
            # makes that a dropped sub-item rather than a miss.
            memo_tonight=False,
            post_checkin=process is not None and process["post_at"] is not None,
            replays_opened=int(replays or 0),
            past_trade_available=past_trades > 0,
            voice_available=self.voice_available,
        )

    def _fires(self, conn: sqlite3.Connection, session_id: str) -> tuple[FireInputs, ...]:
        rows = conn.execute(
            """
            SELECT p.cid, p.created_at, p.lots, p.max_lots_at_fire, p.planned_sl, p.r_usd,
                   p.positions_at_fire, p.max_positions_at_fire,
                   g.required_pass, g.required_total, g.results
            FROM trade_plan p
            LEFT JOIN trade_grade g ON g.cid = p.cid
            WHERE p.session_id = ?
            ORDER BY p.created_at
            """,
            (session_id,),
        ).fetchall()

        fires: list[FireInputs] = []
        previous_ms: int | None = None
        for row in rows:
            gap_ok = previous_ms is None or (
                (row["created_at"] - previous_ms) / 1000 >= self.min_seconds_between_orders
            )
            previous_ms = row["created_at"]

            cap = row["max_lots_at_fire"]
            positions = row["positions_at_fire"]
            max_positions = row["max_positions_at_fire"]
            fires.append(FireInputs(
                cid=row["cid"],
                required_pass=int(row["required_pass"] or 0),
                required_total=int(row["required_total"] or 0),
                # A cap that was never recorded cannot be judged, so the check passes rather than
                # inventing a failure out of a missing column.
                within_lot_cap=cap is None or row["lots"] <= cap,
                stop_at_entry=row["planned_sl"] is not None,
                r_within_tolerance=_within(row["r_usd"], self.r_unit_usd, R_TOLERANCE),
                within_max_positions=(
                    positions is None or max_positions is None or positions < max_positions
                ),
                respected_order_spacing=gap_ok,
                has_memo=False,
                checklist_answered=_checklist_answered(row["results"]),
            ))
        return tuple(fires)

    # -- scoring -----------------------------------------------------------------------

    def score(self, session_id: str, inputs: SessionInputs | None = None) -> SessionScore:
        """Recompute from stored inputs. Pure, and never cached in a way a weight change survives."""
        return score_session(
            inputs if inputs is not None else self.inputs_for(session_id),
            weights=self.weights, trades_max=self.trades_max,
            band_width=self.band_width, decline_credit_max=self.decline_credit_max,
        )

    def write(self, session_id: str, *, now_ms: int | None = None) -> SessionScore:
        """Compute and store the evening's score. Called at session close, never mid-session.

        There is deliberately no live score: a number you can watch mid-trade becomes the anxiety
        the P/L used to be.
        """
        inputs = self.inputs_for(session_id)
        result = self.score(session_id, inputs)
        conn = self._connect()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO session_score (session_id, computed_at, weights_version, "
                "adherence, selectivity, risk_discipline, preparation, review, na_axes, oq_mean, "
                "n_fires, total, inputs) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    session_id, now_ms if now_ms is not None else int(time.time() * 1000),
                    WEIGHTS_VERSION,
                    *[result.axis(name).value for name in
                      ("adherence", "selectivity", "risk_discipline", "preparation", "review")],
                    json.dumps(list(result.na_axes)), result.oq_mean, result.n_fires,
                    result.total, json.dumps(asdict(inputs), sort_keys=True),
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return result

    def record_replay_open(self, session_id: str | None, cid: str, *,
                           now_ms: int | None = None) -> None:
        """Evidence for the Review axis. The only new capture this phase adds."""
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO review_event (session_id, kind, cid, ts) VALUES (?, 'replay_open', ?, ?)",
                (session_id, cid, now_ms if now_ms is not None else int(time.time() * 1000)),
            )
            conn.commit()
        finally:
            conn.close()

    # -- serving -----------------------------------------------------------------------

    def session_payload(self, session_id: str) -> dict[str, Any]:
        """One evening, always recomputed from its inputs so a weight change is visible at once."""
        body = self.score(session_id).payload()
        body["weights"] = self.weights
        return body

    def month(self) -> dict[str, Any]:
        """The score's **distribution** by month, with n. Never a streak, never a `days since`.

        A distribution says "this is the shape of your evenings"; a streak says "do not break it",
        which is pressure to trade a dead tape.
        """
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT s.session_id, e.opened_at FROM session_score s "
                "JOIN session_equity e ON e.session_id = s.session_id ORDER BY e.opened_at"
            ).fetchall()
        finally:
            conn.close()

        months: dict[str, list[float]] = {}
        for row in rows:
            # Recomputed rather than read back, so an old row under an old weighting never appears
            # in the same chart as a new one.
            total = self.score(row["session_id"]).total
            month = time.strftime("%Y-%m", time.gmtime(row["opened_at"] / 1000))
            months.setdefault(month, []).append(total)

        return {"months": [
            {
                "month": month,
                "n": len(values),
                "mean": round(sum(values) / len(values), 1),
                "min": round(min(values), 1),
                "max": round(max(values), 1),
                # The distribution itself, so the deck can draw a shape rather than one number.
                "scores": [round(v, 1) for v in values],
            }
            for month, values in sorted(months.items())
        ]}

    def axes_summary(self, session_id: str | None) -> dict[str, Any]:
        """What the copilot's `get_progress` gains: the axes, so it can coach a named one."""
        if session_id is None:
            return {"available": False}
        result = self.score(session_id)
        return {
            "available": True,
            "total": result.displayed,
            "axes": {a.name: (None if a.value is None else round(a.value, 1)) for a in result.axes},
            "naAxes": list(result.na_axes),
        }


def _within(value: float | None, target: float, tolerance: float) -> bool:
    """A recorded R inside the configured unit's tolerance. An unrecorded R is not a failure."""
    if value is None or target <= 0:
        return True
    return abs(value - target) / target <= tolerance


def _checklist_answered(results: str | None) -> bool:
    """True when no manual rule is still unknown. Skipping the checklist costs the Review axis only."""
    if not results:
        return False
    try:
        parsed = json.loads(results)
    except (TypeError, ValueError):
        return False
    manual = [r for r in parsed if isinstance(r, dict) and r.get("kind") == "manual"]
    if not manual:
        return True
    return all(not r.get("unknown") for r in manual)
