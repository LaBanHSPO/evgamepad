"""Reading one trade back out of the journal.

Replay is a single-row read by design. A trade's whole window — 600-odd bars, both sides of the
book, every event — lives in one `trade_tape` row, so reviewing a trade is one SELECT, one gunzip,
and one response. A per-sample table would have bought ~9,000 rows an evening and an index to
serve exactly the same query.

Everything here is a read. Nothing on this path writes, and nothing on it touches the broker.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from journal.tape import normalise, unpack_bars

log = logging.getLogger(__name__)

# Prices are stored as the protocol's scaled integers. They stay integers over the wire too — the
# client divides once, at the point of drawing, rather than the tape being rounded twice.
PRICE_SCALE = 100_000

CLOSED_COLUMNS = (
    "cid", "session_id", "position_id", "symbol", "side", "lots", "entry_price", "exit_price",
    "opened_at", "closed_at", "net_pnl_usd", "r_usd", "r_multiple", "mfe", "mae", "adherence",
    "tilt_at_entry",
)


@dataclass
class ReplayRepository:
    """`GET /api/replay/*`, straight off the journal."""

    db_path: Path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # -- the trade list ----------------------------------------------------------------

    def index(self, *, from_ms: int | None = None, to_ms: int | None = None) -> dict[str, Any]:
        """The trades LB/RB step through, newest evening first but chronological within it.

        Stepping order has to match the order they were taken, or "previous trade" means nothing.
        """
        clauses, params = [], []
        if from_ms is not None:
            clauses.append("closed_at >= ?")
            params.append(from_ms)
        if to_ms is not None:
            clauses.append("closed_at <= ?")
            params.append(to_ms)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        conn = self._connect()
        try:
            rows = conn.execute(
                f"""
                SELECT c.cid, c.session_id, c.symbol, c.side, c.lots, c.opened_at, c.closed_at,
                       c.r_multiple, c.net_pnl_usd,
                       g.clean AS clean,
                       t.cid IS NOT NULL AS has_tape
                FROM trade_closed c
                LEFT JOIN trade_grade g ON g.cid = c.cid
                LEFT JOIN trade_tape t ON t.cid = c.cid
                {where}
                ORDER BY c.closed_at
                """,
                params,
            ).fetchall()
        finally:
            conn.close()

        return {"trades": [
            {
                "cid": r["cid"], "sessionId": r["session_id"], "symbol": r["symbol"],
                "side": r["side"], "lots": r["lots"], "openedAt": r["opened_at"],
                "closedAt": r["closed_at"], "rMultiple": r["r_multiple"],
                "netPnlUsd": r["net_pnl_usd"],
                "clean": None if r["clean"] is None else bool(r["clean"]),
                "hasTape": bool(r["has_tape"]),
            }
            for r in rows
        ]}

    # -- one trade ----------------------------------------------------------------------

    def trade(self, cid: str) -> dict[str, Any] | None:
        """Bars, events, the closed-trade facts, and the grade. `None` if the trade never existed.

        A trade with **no tape** is not `None`: it returns everything but the bars, and the client
        renders the marker-only view. A pre-phase-2 trade is still worth reviewing.
        """
        conn = self._connect()
        try:
            closed = conn.execute(
                f"SELECT {', '.join(CLOSED_COLUMNS)} FROM trade_closed WHERE cid = ?", (cid,)
            ).fetchone()
            if closed is None:
                return None

            tape = conn.execute(
                "SELECT from_ts, to_ts, dt_s, bars, events, mfe, mae FROM trade_tape WHERE cid = ?",
                (cid,),
            ).fetchone()
            grade = conn.execute(
                "SELECT playbook_id, stage, results, required_pass, required_total, clean "
                "FROM trade_grade WHERE cid = ?", (cid,)
            ).fetchone()
            plan = conn.execute(
                "SELECT planned_sl, planned_tp, timeframe, playbook_id, armed_at "
                "FROM trade_plan WHERE cid = ?", (cid,)
            ).fetchone()
        finally:
            conn.close()

        body: dict[str, Any] = {
            "trade": _trade_payload(closed, plan),
            "grade": _grade_payload(grade),
            "scale": PRICE_SCALE,
            # Phase 8 fills this in. An empty index is what "this trade has no memo" looks like,
            # and the replay surface is required to render identically without one.
            "memos": [],
        }
        body.update(_tape_payload(tape, cid))
        return body


def _trade_payload(row: sqlite3.Row, plan: sqlite3.Row | None) -> dict[str, Any]:
    """The facts the markers are drawn from.

    Entry and exit come from here, never from the bars: at 1 Hz the entry bar is context, and the
    fill is truth.
    """
    payload = {
        "cid": row["cid"], "sessionId": row["session_id"], "positionId": row["position_id"],
        "symbol": row["symbol"], "side": row["side"], "lots": row["lots"],
        "entry": row["entry_price"], "exit": row["exit_price"],
        "openedAt": row["opened_at"], "closedAt": row["closed_at"],
        "netPnlUsd": row["net_pnl_usd"], "rUsd": row["r_usd"], "rMultiple": row["r_multiple"],
        "mfe": row["mfe"], "mae": row["mae"], "adherence": row["adherence"],
        "tiltAtEntry": row["tilt_at_entry"],
    }
    if plan is not None:
        payload.update({
            "plannedSl": plan["planned_sl"], "plannedTp": plan["planned_tp"],
            "timeframe": plan["timeframe"], "playbookId": plan["playbook_id"],
            "armedAt": plan["armed_at"],
        })
    return payload


def _grade_payload(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
        "playbookId": row["playbook_id"], "stage": row["stage"],
        "results": _loads(row["results"], default=[]),
        "requiredPass": row["required_pass"], "requiredTotal": row["required_total"],
        "clean": bool(row["clean"]),
    }


def _tape_payload(row: sqlite3.Row | None, cid: str) -> dict[str, Any]:
    """Columnar bars for the chart, or an honest empty tape.

    A corrupt or unreadable blob degrades to the marker-only view for the same reason a missing one
    does: a trade you cannot chart is still a trade you can review.
    """
    if row is None:
        return {"tape": None, "events": []}

    events = normalise(_loads(row["events"], default=[]))
    try:
        header, bars = unpack_bars(row["bars"])
    except (ValueError, OSError, EOFError):
        log.exception("replay %s: tape blob unreadable; serving the marker-only view", cid)
        return {"tape": None, "events": events}

    return {
        "tape": {
            "fromTs": row["from_ts"], "toTs": row["to_ts"], "dtS": row["dt_s"],
            "n": len(bars),
            "mfe": row["mfe"], "mae": row["mae"],
            # Columnar, because the client reads whole series and JSON of 600 objects would be
            # roughly three times the bytes for the same numbers.
            "ts": [b.ts_s for b in bars],
            "bidO": [b.bid_o for b in bars], "bidH": [b.bid_h for b in bars],
            "bidL": [b.bid_l for b in bars], "bidC": [b.bid_c for b in bars],
            "askO": [b.ask_o for b in bars], "askH": [b.ask_h for b in bars],
            "askL": [b.ask_l for b in bars], "askC": [b.ask_c for b in bars],
            "nTicks": [b.n_ticks for b in bars],
            "version": header.get("v"),
        },
        "events": events,
    }


def _loads(raw: Any, *, default: Any) -> Any:
    if not raw:
        return default
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return default
