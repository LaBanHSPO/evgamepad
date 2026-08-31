"""Streamed CSV and JSON exports of the journal.

Two rules, and the second is the one with teeth:

1. **Streamed.** Rows are yielded as they are read, so a two-year journal does not have to fit in
   memory before the first byte reaches the browser.
2. **Never a secret, never a path.** The export is built from an explicit column allowlist, so a
   column added to the schema later cannot silently start appearing in a file the player emails to
   someone. `redactions()` is the test's entry point for proving it.

What is deliberately absent: any import. There is no CSV-in, no MT5 reader, no broker-history
parser. This journal describes what *this* gateway executed; a row it did not fill is a row it
cannot vouch for.
"""

from __future__ import annotations

import csv
import io
import json
import sqlite3
from collections.abc import Iterator
from pathlib import Path
from typing import Any

# The trade columns a CSV export carries, with the review dimensions flattened alongside them.
# Adding a column here is a deliberate act; nothing is exported by wildcard.
TRADE_COLUMNS = (
    "cid", "session_id", "symbol", "side", "lots", "timeframe", "market_session", "playbook_id",
    "setup_tag", "opened_at", "closed_at", "entry_price", "exit_price", "planned_sl", "planned_tp",
    "planned_rr", "r_usd", "r_multiple", "mfe", "mae", "net_pnl_usd", "clean", "required_pass",
    "required_total", "intent", "intent_by", "mistakes",
)

# Every table a JSON export walks, and the columns it takes from each. `secure`, config and env
# appear nowhere because they are not in this database at all — but the allowlist is what keeps a
# future table from joining the export by accident.
JSON_TABLES: dict[str, tuple[str, ...]] = {
    "session_equity": ("session_id", "timezone", "opened_at", "closed_at", "equity_open",
                       "equity_close"),
    "session_process": ("session_id", "pre_rating", "pre_at", "post_rating", "post_at",
                        "stood_down_count", "note", "adherence_score", "opportunity_quality"),
    "session_score": ("session_id", "computed_at", "weights_version", "adherence", "selectivity",
                      "risk_discipline", "preparation", "review", "na_axes", "oq_mean", "n_fires",
                      "total"),
    "trade_plan": ("cid", "session_id", "symbol", "side", "timeframe", "market_session",
                   "playbook_id", "lots", "planned_entry", "planned_sl", "planned_tp",
                   "planned_rr", "r_usd", "r_method", "armed_at", "created_at"),
    "trade_closed": ("cid", "session_id", "symbol", "side", "lots", "entry_price", "exit_price",
                     "opened_at", "closed_at", "net_pnl_usd", "r_usd", "r_multiple", "mfe", "mae",
                     "tilt_at_entry"),
    "trade_grade": ("cid", "playbook_id", "stage", "evaluated_at", "results", "required_pass",
                    "required_total", "clean"),
    "trade_review": ("cid", "updated_at", "intent", "intent_by", "note", "early_exit"),
    "daily_analysis": ("session_id", "updated_at", "thesis", "instruments", "key_levels",
                       "invalidation", "event_risks", "tags", "notes"),
    "readiness_check": ("session_id", "item", "ok", "note", "ts"),
    "mistake_occurrence": ("cid", "session_id", "code", "source", "note", "ts"),
    "mistake_definition": ("code", "label", "builtin", "active"),
    "playbook": ("id", "name", "slug", "method", "symbols", "narrative", "active", "retired_at"),
    "tilt_sample": ("session_id", "ts", "score", "band", "top_driver"),
    # Metadata only. The image bytes are in the backup archive, not in a JSON export.
    "journal_attachment": ("id", "session_id", "cid", "mime", "bytes", "width", "height", "label",
                           "created_at"),
    "system_principles": ("updated_at", "philosophy", "principles", "focus_code"),
}


def redactions() -> tuple[str, ...]:
    """Column-name fragments that must never appear in an export.

    Kept beside the allowlists so the test that proves it and the lists it checks live together.
    """
    return ("secret", "token", "password", "credential", "client_id", "access", "refresh",
            "bearer", "env", "data_dir", "bind")


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _window(from_ms: int | None, to_ms: int | None, column: str) -> tuple[str, list[Any]]:
    clauses, params = [], []
    if from_ms is not None:
        clauses.append(f"{column} >= ?")
        params.append(from_ms)
    if to_ms is not None:
        clauses.append(f"{column} <= ?")
        params.append(to_ms)
    return (f"WHERE {' AND '.join(clauses)}" if clauses else ""), params


def trades_csv(db_path: Path, *, from_ms: int | None = None,
               to_ms: int | None = None) -> Iterator[str]:
    """One row per closed trade, with its grade, review and mistakes flattened in.

    Yields the header first and then a row at a time, so the response starts immediately and the
    whole journal is never held in memory.
    """
    where, params = _window(from_ms, to_ms, "c.closed_at")
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")

    def flush() -> str:
        value = buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)
        return value

    writer.writerow(TRADE_COLUMNS)
    yield flush()

    conn = _connect(db_path)
    try:
        rows = conn.execute(
            f"""
            SELECT c.cid, c.session_id, c.symbol, c.side, c.lots,
                   p.timeframe, p.market_session, p.playbook_id,
                   COALESCE(c.setup_tag, p.setup_tag) AS setup_tag,
                   c.opened_at, c.closed_at, c.entry_price, c.exit_price,
                   p.planned_sl, p.planned_tp, p.planned_rr,
                   c.r_usd, c.r_multiple, c.mfe, c.mae, c.net_pnl_usd,
                   g.clean, g.required_pass, g.required_total,
                   r.intent, r.intent_by,
                   (SELECT GROUP_CONCAT(m.code, ' ') FROM mistake_occurrence m WHERE m.cid = c.cid)
                       AS mistakes
            FROM trade_closed c
            LEFT JOIN trade_plan p ON p.cid = c.cid
            LEFT JOIN trade_grade g ON g.cid = c.cid
            LEFT JOIN trade_review r ON r.cid = c.cid
            {where}
            ORDER BY c.closed_at
            """,
            params,
        )
        for row in rows:
            writer.writerow([row[column] for column in TRADE_COLUMNS])
            yield flush()
    finally:
        conn.close()


def journal_json(db_path: Path, *, from_ms: int | None = None,
                 to_ms: int | None = None) -> Iterator[str]:
    """The whole journal as one streamed JSON document.

    Assembled table by table rather than built as one object, for the same reason as the CSV: a
    long history should not need to fit in memory to be exported.
    """
    yield '{"format":"evgamepad-journal","version":1,"tables":{'

    conn = _connect(db_path)
    try:
        first_table = True
        for table, columns in JSON_TABLES.items():
            if not first_table:
                yield ","
            first_table = False
            yield f"{json.dumps(table)}:["

            try:
                rows = conn.execute(f"SELECT {', '.join(columns)} FROM {table}")
            except sqlite3.Error:
                # A table this build does not have yet exports as empty rather than failing the
                # whole document.
                yield "]"
                continue

            first_row = True
            for row in rows:
                if not first_row:
                    yield ","
                first_row = False
                yield json.dumps({column: row[column] for column in columns}, sort_keys=True)
            yield "]"
    finally:
        conn.close()

    yield "}}"


def counts(db_path: Path) -> dict[str, int]:
    """Row counts per exported table — what an audit row records, and what restore verifies."""
    conn = _connect(db_path)
    try:
        out: dict[str, int] = {}
        for table in JSON_TABLES:
            try:
                out[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            except sqlite3.Error:
                continue
        return out
    finally:
        conn.close()
