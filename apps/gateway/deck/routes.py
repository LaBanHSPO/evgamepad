"""`GET /api/deck/*`.

Plain HTTP, same origin, behind the token the socket already uses. The deck is not realtime and
has no business on the socket whose job is prioritising order acks — the same reasoning that puts
voice audio and the replay tape on HTTP.

Every number served here comes from `deck.metrics`, which is pure. Nothing on this path asks a
model for a figure.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from .metrics import (
    CITATION,
    DISCLAIMER,
    Fire,
    PlaybookRow,
    SessionRow,
    _mean,
    adherence_for,
    by_setup,
    capture_efficiency,
    month_over_month,
    opportunity_verdict,
    outcome_month,
    process_month,
    sharpe,
    tilt_against_adherence,
)

PROCESS_DELTA_KEYS = ["adherence", "declinedRate", "checkinAverage", "opportunityQuality"]
OUTCOME_DELTA_KEYS = ["returnPct", "averageR", "winRate", "profitFactor"]


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def load_sessions(conn: sqlite3.Connection) -> list[SessionRow]:
    """Every evening, with its process row folded in where one exists."""
    rows = conn.execute(
        """
        SELECT e.session_id, e.opened_at, e.closed_at, e.equity_open, e.equity_close,
               p.pre_rating, p.post_rating, p.stood_down_count, p.opportunity_quality, p.note
        FROM session_equity e
        LEFT JOIN session_process p ON p.session_id = e.session_id
        ORDER BY e.opened_at
        """
    ).fetchall()
    return [
        SessionRow(
            session_id=row["session_id"],
            opened_at=row["opened_at"],
            closed_at=row["closed_at"],
            equity_open=row["equity_open"],
            equity_close=row["equity_close"],
            pre_rating=row["pre_rating"],
            post_rating=row["post_rating"],
            stood_down_count=row["stood_down_count"] or 0,
            opportunity_quality=row["opportunity_quality"],
            note=row["note"],
        )
        for row in rows
    ]


def load_fires(conn: sqlite3.Connection, *, default_max_lots: float,
               default_max_positions: int) -> list[Fire]:
    """Fires that closed, with the adherence inputs captured at the time of the fire.

    A plan row that predates the deck migration has null adherence inputs; those fall back to
    today's caps, which is the best available answer and is visible as such because `setup_tag`
    will also be null.
    """
    rows = conn.execute(
        """
        SELECT p.cid, p.session_id, p.symbol, p.lots, p.setup_tag AS plan_setup,
               p.inside_window, p.positions_at_fire, p.seconds_to_high_impact,
               p.max_lots_at_fire, p.max_positions_at_fire,
               c.r_multiple, c.net_pnl_usd, c.closed_at, c.setup_tag AS closed_setup
        FROM trade_plan p
        JOIN trade_closed c ON c.cid = p.cid
        ORDER BY c.closed_at
        """
    ).fetchall()
    return [
        Fire(
            cid=row["cid"],
            session_id=row["session_id"] or "",
            symbol=row["symbol"],
            setup_tag=row["closed_setup"] or row["plan_setup"],
            lots=row["lots"],
            max_lots=row["max_lots_at_fire"] if row["max_lots_at_fire"] is not None
            else default_max_lots,
            # An unrecorded window is treated as inside it: the gateway would have refused the
            # fire otherwise, so assuming a breach would invent a violation that never happened.
            inside_window=True if row["inside_window"] is None else bool(row["inside_window"]),
            positions_at_fire=row["positions_at_fire"] or 0,
            max_positions=row["max_positions_at_fire"] if row["max_positions_at_fire"] is not None
            else default_max_positions,
            seconds_to_high_impact=row["seconds_to_high_impact"],
            r_multiple=row["r_multiple"],
            pnl_usd=row["net_pnl_usd"],
            closed_at=row["closed_at"],
        )
        for row in rows
    ]


def process_view(sessions: list[SessionRow], fires: list[Fire]) -> dict[str, Any]:
    """The default panel. Not one dollar figure appears anywhere in it."""
    latest = sessions[-1] if sessions else None
    latest_fires = [f for f in fires if latest and f.session_id == latest.session_id]
    adherence = adherence_for(fires)

    return {
        "panel": "process",
        "disclaimer": DISCLAIMER,
        "citation": CITATION,
        "allTime": {
            "sessions": len(sessions),
            "adherence": adherence.score,
            "adherenceByRule": adherence.by_rule,
            "fires": adherence.fires,
            "declined": sum(s.stood_down_count for s in sessions),
        },
        "months": month_over_month(sessions, fires, PROCESS_DELTA_KEYS, process_month),
        "latestSession": None if latest is None else {
            "sessionId": latest.session_id,
            "openedAt": latest.opened_at,
            "checkinPre": latest.pre_rating,
            "checkinPost": latest.post_rating,
            "declined": latest.stood_down_count,
            "opportunityQuality": latest.opportunity_quality,
            "verdict": opportunity_verdict(latest.opportunity_quality, len(latest_fires)),
            # Player text. Rendered as text, never as markup.
            "note": latest.note,
        },
    }


def outcome_view(sessions: list[SessionRow], fires: list[Fire],
                 min_sessions_for_sharpe: int) -> dict[str, Any]:
    """The second tab. Reached by a deliberate click, and never linked from the process panel."""
    result = sharpe(sessions, min_sessions=min_sessions_for_sharpe)
    return {
        "panel": "outcome",
        "disclaimer": DISCLAIMER,
        "sharpe": {
            "value": result.value,
            "display": result.display,
            "sessions": result.sessions,
            "enough": result.enough,
            "note": result.note,
        },
        "months": month_over_month(sessions, fires, OUTCOME_DELTA_KEYS, outcome_month),
        "bySetup": by_setup(fires),
    }


def summary_view(sessions: list[SessionRow], fires: list[Fire]) -> dict[str, Any]:
    """What the HUD and the desk may read. Process only — no money field exists here."""
    adherence = adherence_for(fires)
    latest = sessions[-1] if sessions else None
    latest_fires = [f for f in fires if latest and f.session_id == latest.session_id]
    return {
        "sessions": len(sessions),
        "adherence": adherence.score,
        "declined": sum(s.stood_down_count for s in sessions),
        "checkinPre": latest.pre_rating if latest else None,
        "opportunityQuality": latest.opportunity_quality if latest else None,
        "verdict": opportunity_verdict(latest.opportunity_quality if latest else None,
                                       len(latest_fires)),
        "disclaimer": DISCLAIMER,
    }


class DeckRepository:
    """Reads the journal for the deck. Holds no connection open between requests."""

    def __init__(self, db_path: Path, *, max_lots: float, max_positions: int,
                 min_sessions_for_sharpe: int) -> None:
        self.db_path = db_path
        self.max_lots = max_lots
        self.max_positions = max_positions
        self.min_sessions_for_sharpe = min_sessions_for_sharpe

    def _rows(self) -> tuple[list[SessionRow], list[Fire]]:
        conn = _connect(self.db_path)
        try:
            return (
                load_sessions(conn),
                load_fires(conn, default_max_lots=self.max_lots,
                           default_max_positions=self.max_positions),
            )
        finally:
            conn.close()

    def process(self) -> dict[str, Any]:
        sessions, fires = self._rows()
        return process_view(sessions, fires)

    def outcome(self) -> dict[str, Any]:
        sessions, fires = self._rows()
        return outcome_view(sessions, fires, self.min_sessions_for_sharpe)

    def summary(self) -> dict[str, Any]:
        sessions, fires = self._rows()
        return summary_view(sessions, fires)

    # -- phase 11 panels -------------------------------------------------------------

    def playbooks(self, *, outcome: bool = False) -> dict[str, Any]:
        """Per-playbook record. Process figures by default; outcome only on the deliberate ask."""
        conn = _connect(self.db_path)
        try:
            rows = conn.execute(
                """
                SELECT COALESCE(p.playbook_id, '__unplanned__') AS pid,
                       COALESCE(b.name, 'unplanned')            AS name,
                       COUNT(*)                                 AS n,
                       AVG(g.clean)                             AS clean_rate,
                       SUM(g.required_pass)                     AS passed,
                       SUM(g.required_total)                    AS evaluated,
                       AVG(c.r_multiple)                        AS expectancy_r,
                       AVG(c.mfe)                               AS avg_mfe,
                       AVG(c.mae)                               AS avg_mae
                FROM trade_plan p
                JOIN trade_closed c ON c.cid = p.cid
                LEFT JOIN trade_grade g ON g.cid = p.cid
                LEFT JOIN playbook b ON b.id = p.playbook_id
                GROUP BY pid, name
                ORDER BY n DESC
                """
            ).fetchall()
            efficiencies = conn.execute(
                """
                SELECT COALESCE(p.playbook_id, '__unplanned__') AS pid,
                       c.entry_price, c.exit_price, c.mfe, c.side
                FROM trade_plan p JOIN trade_closed c ON c.cid = p.cid
                """
            ).fetchall()
        finally:
            conn.close()

        captured: dict[str, list[float]] = {}
        for row in efficiencies:
            value = capture_efficiency(row["entry_price"], row["exit_price"], row["mfe"],
                                       row["side"])
            if value is not None:
                captured.setdefault(row["pid"], []).append(value)

        playbooks = [
            PlaybookRow(
                playbook_id=row["pid"], name=row["name"], n=row["n"],
                clean_rate=row["clean_rate"],
                adherence=(row["passed"] / row["evaluated"]) if row["evaluated"] else None,
                expectancy_r=row["expectancy_r"], avg_mfe=row["avg_mfe"], avg_mae=row["avg_mae"],
                efficiency=_mean(captured.get(row["pid"], [])),
            )
            for row in rows
        ]
        return {
            "playbooks": [p.outcome_payload() if outcome else p.process_payload()
                          for p in playbooks],
            "disclaimer": DISCLAIMER,
        }

    def tilt_retro(self, session_id: str) -> dict[str, Any]:
        """Tilt as a record of an evening. Never a score input, never against P/L."""
        conn = _connect(self.db_path)
        try:
            samples = [
                {"ts": r["ts"], "score": r["score"], "band": r["band"], "topDriver": r["top_driver"]}
                for r in conn.execute(
                    "SELECT ts, score, band, top_driver FROM tilt_sample "
                    "WHERE session_id = ? ORDER BY ts", (session_id,)
                ).fetchall()
            ]
            fires = [f for f in load_fires(conn, default_max_lots=self.max_lots,
                                           default_max_positions=self.max_positions)
                     if f.session_id == session_id]
        finally:
            conn.close()
        return tilt_against_adherence(samples, fires)
