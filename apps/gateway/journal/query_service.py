"""Every read and every review write the journal cockpit needs.

The boundary this module exists to hold: **broker facts are immutable; review sits on top.** Every
write here targets a review table — readiness, analysis, attachments, trade review, mistakes,
principles. None of them can touch `trade_plan`, `trade_closed`, `position_event` or `trade_tape`,
and a test walks the statements to keep it that way.

Two other rules carried down from phase 6:

- **Outcome never leads.** The day and overview payloads carry process figures by default; the
  money is a separate call the player has to make.
- **A missing figure is a gap, never a zero.** Every query returns `None` for what was not
  measured, and the panels render that as an absence.
"""

from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from journal.metrics import (
    TradeFacts,
    actual_vs_plan,
    derive_intent,
    execution_scores,
    group_counts,
    process_consistency,
)
from journal.mistakes import BUILTINS, FireEvidence, derive, seed_rows, trend

# History pagination. The maximum is a real limit, not a suggestion — a journal that can be asked
# for every trade at once is a journal that times out on the evening it matters.
DEFAULT_PAGE = 50
MAX_PAGE = 200

READINESS_ITEMS = ("sleep", "calm", "focus", "risk_accepted", "plan_reviewed")

# The dimensions `/api/journal/history` filters on. Named here so the SQL cannot drift from the
# documented surface, and so an unknown filter is refused rather than silently ignored.
HISTORY_FILTERS = (
    "from_ms", "to_ms", "playbook", "setup", "symbol", "timeframe", "side", "market_session",
    "intent", "mistake", "result",
)


@dataclass
class JournalService:
    """`GET|PUT /api/journal/*`. Reads broker facts, writes only review."""

    db_path: Path
    max_lots: float = 0.10

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def seed_mistakes(self, ts_ms: int) -> int:
        """Built-in taxonomy, once. A custom mistake is the same table with `builtin = 0`."""
        conn = self._connect()
        try:
            before = conn.execute("SELECT COUNT(*) FROM mistake_definition").fetchone()[0]
            conn.executemany(
                "INSERT OR IGNORE INTO mistake_definition (code, label, builtin, active, "
                "created_at) VALUES (?,?,?,?,?)", seed_rows(ts_ms),
            )
            conn.commit()
            after = conn.execute("SELECT COUNT(*) FROM mistake_definition").fetchone()[0]
        finally:
            conn.close()
        return after - before

    # -- today ------------------------------------------------------------------------

    def today(self, session_id: str) -> dict[str, Any]:
        """Everything `/journal/today` needs to prepare an evening or land after one."""
        conn = self._connect()
        try:
            readiness = {
                row["item"]: {"ok": None if row["ok"] is None else bool(row["ok"]),
                              "note": row["note"]}
                for row in conn.execute(
                    "SELECT item, ok, note FROM readiness_check WHERE session_id = ?", (session_id,)
                ).fetchall()
            }
            analysis = conn.execute(
                "SELECT updated_at, thesis, instruments, key_levels, invalidation, event_risks, "
                "tags, notes FROM daily_analysis WHERE session_id = ?", (session_id,)
            ).fetchone()
            desk_plan = conn.execute(
                "SELECT created_at, bias, setup, text, offline FROM session_plan "
                "WHERE session_id = ?", (session_id,)
            ).fetchone()
            attachments = self._attachments(conn, session_id=session_id, cid=None)
            process = conn.execute(
                "SELECT pre_rating, post_rating, stood_down_count, opportunity_quality "
                "FROM session_process WHERE session_id = ?", (session_id,)
            ).fetchone()
        finally:
            conn.close()

        return {
            "sessionId": session_id,
            # Every item is present, so an unanswered one reads as a question rather than a gap.
            "readiness": [
                {"item": item, **readiness.get(item, {"ok": None, "note": None})}
                for item in READINESS_ITEMS
            ],
            "analysis": _analysis_payload(analysis),
            # The desk's plan sits beside the player's, never merged into it.
            "deskPlan": None if desk_plan is None else {
                "createdAt": desk_plan["created_at"], "bias": desk_plan["bias"],
                "setup": desk_plan["setup"], "text": desk_plan["text"],
                "offline": bool(desk_plan["offline"]),
            },
            "attachments": attachments,
            "checkin": None if process is None else {
                "pre": process["pre_rating"], "post": process["post_rating"],
                "declined": process["stood_down_count"],
                "opportunityQuality": process["opportunity_quality"],
            },
        }

    def put_readiness(self, session_id: str, items: list[dict[str, Any]], ts_ms: int) -> None:
        """Advisory, and it has never blocked anything. `None` records a declined item."""
        conn = self._connect()
        try:
            for item in items:
                name = str(item.get("item", ""))
                if name not in READINESS_ITEMS:
                    continue
                ok = item.get("ok")
                conn.execute(
                    "INSERT INTO readiness_check (session_id, item, ok, note, ts) "
                    "VALUES (?,?,?,?,?) ON CONFLICT (session_id, item) DO UPDATE SET "
                    "ok = excluded.ok, note = excluded.note, ts = excluded.ts",
                    (session_id, name, None if ok is None else int(bool(ok)),
                     _text(item.get("note")), ts_ms),
                )
            conn.commit()
        finally:
            conn.close()

    def put_analysis(self, session_id: str, body: dict[str, Any], ts_ms: int) -> None:
        """The player's own words. Nothing else in this codebase writes this row."""
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO daily_analysis (session_id, updated_at, thesis, instruments, "
                "key_levels, invalidation, event_risks, tags, notes) VALUES (?,?,?,?,?,?,?,?,?) "
                "ON CONFLICT (session_id) DO UPDATE SET updated_at = excluded.updated_at, "
                "thesis = excluded.thesis, instruments = excluded.instruments, "
                "key_levels = excluded.key_levels, invalidation = excluded.invalidation, "
                "event_risks = excluded.event_risks, tags = excluded.tags, notes = excluded.notes",
                (session_id, ts_ms, _text(body.get("thesis")), _json(body.get("instruments")),
                 _json(body.get("keyLevels")), _text(body.get("invalidation")),
                 _text(body.get("eventRisks")), _json(body.get("tags")), _text(body.get("notes"))),
            )
            conn.commit()
        finally:
            conn.close()

    # -- attachments ------------------------------------------------------------------

    def record_attachment(self, *, attachment_id: str, mime: str, size: int,
                          width: int | None, height: int | None, session_id: str | None,
                          cid: str | None, label: str | None, ts_ms: int) -> None:
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO journal_attachment (id, session_id, cid, mime, bytes, width, height, "
                "label, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (attachment_id, session_id, cid, mime, size, width, height, _text(label), ts_ms),
            )
            conn.commit()
        finally:
            conn.close()

    def attachment(self, attachment_id: str) -> dict[str, Any] | None:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT id, mime, bytes FROM journal_attachment WHERE id = ?", (attachment_id,)
            ).fetchone()
        finally:
            conn.close()
        return None if row is None else {"id": row["id"], "mime": row["mime"],
                                         "bytes": row["bytes"]}

    def _attachments(self, conn: sqlite3.Connection, *, session_id: str | None,
                     cid: str | None) -> list[dict[str, Any]]:
        if cid is not None:
            rows = conn.execute(
                "SELECT id, mime, bytes, width, height, label, created_at FROM journal_attachment "
                "WHERE cid = ? ORDER BY created_at", (cid,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, mime, bytes, width, height, label, created_at FROM journal_attachment "
                "WHERE session_id = ? AND cid IS NULL ORDER BY created_at", (session_id,)
            ).fetchall()
        return [dict(row) for row in rows]

    # -- overview and days -------------------------------------------------------------

    def overview(self, *, from_ms: int | None = None, to_ms: int | None = None) -> dict[str, Any]:
        """The dashboard. Process first; the money is a separate, deliberate call."""
        conn = self._connect()
        try:
            sessions = conn.execute(
                """
                SELECT e.session_id, e.opened_at, e.equity_open, e.equity_close,
                       p.pre_rating, p.post_rating, p.stood_down_count,
                       s.total AS score
                FROM session_equity e
                LEFT JOIN session_process p ON p.session_id = e.session_id
                LEFT JOIN session_score s ON s.session_id = e.session_id
                WHERE (? IS NULL OR e.opened_at >= ?) AND (? IS NULL OR e.opened_at <= ?)
                ORDER BY e.opened_at
                """,
                (from_ms, from_ms, to_ms, to_ms),
            ).fetchall()
            trades = self._trade_rows(conn, limit=10)
            mistakes = [dict(r) for r in conn.execute(
                "SELECT code, cid, source FROM mistake_occurrence"
            ).fetchall()]
            focus = conn.execute(
                "SELECT focus_code FROM system_principles WHERE id = 1"
            ).fetchone()
            groups = conn.execute(
                """
                SELECT r.intent, c.r_multiple, g.clean, p.playbook_id
                FROM trade_closed c
                LEFT JOIN trade_plan p ON p.cid = c.cid
                LEFT JOIN trade_grade g ON g.cid = c.cid
                LEFT JOIN trade_review r ON r.cid = c.cid
                """
            ).fetchall()
        finally:
            conn.close()

        scores = [row["score"] for row in sessions if row["score"] is not None]
        classified = [
            (derive_intent(grade_clean=None if row["clean"] is None else bool(row["clean"]),
                           playbook_id=row["playbook_id"], confirmed=row["intent"])[0],
             row["r_multiple"])
            for row in groups
        ]

        return {
            "account": {"broker": "IC Markets", "kind": "cTrader demo", "readOnly": True},
            "sessions": len(sessions),
            # Process Consistency always states its n, and refuses a confident number below five.
            "consistency": process_consistency(scores).payload(),
            "processScoreMean": round(sum(scores) / len(scores), 1) if scores else None,
            "latestTrades": trades,
            "groups": group_counts(classified),
            "mistakes": trend(mistakes, focus=None if focus is None else focus["focus_code"]),
        }

    def days(self, *, from_ms: int | None = None, to_ms: int | None = None) -> dict[str, Any]:
        """The heatmap. Colour is Process Score and activity — never P/L, which lives behind Outcome."""
        conn = self._connect()
        try:
            rows = conn.execute(
                """
                SELECT e.session_id, e.opened_at,
                       s.total AS score, s.n_fires,
                       p.stood_down_count, p.pre_rating, p.post_rating,
                       (SELECT COUNT(*) FROM trade_closed c WHERE c.session_id = e.session_id)
                           AS trades,
                       (SELECT COUNT(*) FROM mistake_occurrence m WHERE m.session_id = e.session_id)
                           AS mistakes,
                       (SELECT COUNT(*) FROM daily_analysis d WHERE d.session_id = e.session_id)
                           AS has_analysis
                FROM session_equity e
                LEFT JOIN session_score s ON s.session_id = e.session_id
                LEFT JOIN session_process p ON p.session_id = e.session_id
                WHERE (? IS NULL OR e.opened_at >= ?) AND (? IS NULL OR e.opened_at <= ?)
                ORDER BY e.opened_at
                """,
                (from_ms, from_ms, to_ms, to_ms),
            ).fetchall()
        finally:
            conn.close()

        return {"days": [
            {
                "sessionId": row["session_id"], "openedAt": row["opened_at"],
                "score": row["score"], "trades": row["trades"], "declined": row["stood_down_count"],
                "mistakes": row["mistakes"], "hasAnalysis": bool(row["has_analysis"]),
                "checkinPre": row["pre_rating"], "checkinPost": row["post_rating"],
            }
            for row in rows
        ]}

    def day(self, session_id: str) -> dict[str, Any]:
        """One day, drilled into. Analysis, readiness, score, mistakes and the day's trades."""
        conn = self._connect()
        try:
            score = conn.execute(
                "SELECT total, adherence, selectivity, risk_discipline, preparation, review, "
                "na_axes, n_fires FROM session_score WHERE session_id = ?", (session_id,)
            ).fetchone()
            trades = self._trade_rows(conn, session_id=session_id)
            mistakes = [dict(r) for r in conn.execute(
                "SELECT code, cid, source, note, ts FROM mistake_occurrence "
                "WHERE session_id = ? ORDER BY ts", (session_id,)
            ).fetchall()]
        finally:
            conn.close()

        body = self.today(session_id)
        body.update({
            "score": None if score is None else {
                "total": score["total"], "nFires": score["n_fires"],
                "axes": {name: score[name] for name in
                         ("adherence", "selectivity", "risk_discipline", "preparation", "review")},
                "naAxes": json.loads(score["na_axes"] or "[]"),
            },
            "trades": trades,
            "mistakes": mistakes,
        })
        return body

    # -- history ------------------------------------------------------------------------

    def history(self, filters: dict[str, Any], *, page: int = 0,
                size: int = DEFAULT_PAGE) -> dict[str, Any]:
        """Every requested dimension, combinable, parameterised and paginated.

        Filters are built from a fixed clause table rather than from the caller's keys, so an
        unrecognised filter cannot reach the SQL and a combination cannot return a trade outside
        the requested dimensions.
        """
        size = max(1, min(MAX_PAGE, size))
        clauses: list[str] = []
        params: list[Any] = []

        table = {
            "from_ms": ("c.closed_at >= ?", lambda v: int(v)),
            "to_ms": ("c.closed_at <= ?", lambda v: int(v)),
            "playbook": ("p.playbook_id = ?", str),
            "setup": ("COALESCE(c.setup_tag, p.setup_tag) = ?", str),
            "symbol": ("c.symbol = ?", str),
            "timeframe": ("p.timeframe = ?", str),
            "side": ("c.side = ?", str),
            "market_session": ("p.market_session = ?", str),
            "intent": ("COALESCE(r.intent, 'unknown') = ?", str),
            "mistake": (
                "EXISTS (SELECT 1 FROM mistake_occurrence m WHERE m.cid = c.cid AND m.code = ?)",
                str,
            ),
        }
        for key, value in filters.items():
            if value is None or key not in table:
                continue
            clause, cast = table[key]
            clauses.append(clause)
            params.append(cast(value))

        result = filters.get("result")
        if result in ("win", "loss", "breakeven"):
            clauses.append({"win": "c.r_multiple > 0", "loss": "c.r_multiple < 0",
                            "breakeven": "c.r_multiple = 0"}[result])

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        conn = self._connect()
        try:
            total = conn.execute(
                f"""
                SELECT COUNT(*) FROM trade_closed c
                LEFT JOIN trade_plan p ON p.cid = c.cid
                LEFT JOIN trade_review r ON r.cid = c.cid
                {where}
                """,
                params,
            ).fetchone()[0]
            rows = self._trade_rows(conn, where=where, params=params, limit=size,
                                    offset=page * size)
        finally:
            conn.close()

        return {"trades": rows, "total": total, "page": page, "size": size,
                "filters": {k: v for k, v in filters.items() if v is not None}}

    def _trade_rows(self, conn: sqlite3.Connection, *, session_id: str | None = None,
                    where: str = "", params: list[Any] | None = None, limit: int = 10,
                    offset: int = 0) -> list[dict[str, Any]]:
        """The list shape: symbol, side, timeframe, playbook, classification, R, scores, tape."""
        if session_id is not None:
            where, params = "WHERE c.session_id = ?", [session_id]
            limit = 500
        rows = conn.execute(
            f"""
            SELECT c.cid, c.session_id, c.symbol, c.side, c.lots, c.r_multiple, c.closed_at,
                   c.opened_at, c.mfe, c.mae,
                   p.timeframe, p.playbook_id, p.planned_sl, p.planned_tp, p.planned_rr,
                   b.name AS playbook_name,
                   g.clean, g.required_pass, g.required_total,
                   r.intent, r.intent_by,
                   t.cid IS NOT NULL AS has_tape
            FROM trade_closed c
            LEFT JOIN trade_plan p ON p.cid = c.cid
            LEFT JOIN playbook b ON b.id = p.playbook_id
            LEFT JOIN trade_grade g ON g.cid = c.cid
            LEFT JOIN trade_review r ON r.cid = c.cid
            LEFT JOIN trade_tape t ON t.cid = c.cid
            {where}
            ORDER BY c.closed_at DESC
            LIMIT ? OFFSET ?
            """,
            [*(params or []), limit, offset],
        ).fetchall()

        out: list[dict[str, Any]] = []
        for row in rows:
            intent, intent_by = derive_intent(
                grade_clean=None if row["clean"] is None else bool(row["clean"]),
                playbook_id=row["playbook_id"], confirmed=row["intent"],
            )
            facts = self._facts_for(conn, row)
            out.append({
                "cid": row["cid"], "sessionId": row["session_id"], "symbol": row["symbol"],
                "side": row["side"], "lots": row["lots"], "timeframe": row["timeframe"],
                "playbookId": row["playbook_id"], "playbookName": row["playbook_name"],
                "intent": intent, "intentBy": row["intent_by"] or intent_by,
                "rMultiple": row["r_multiple"], "closedAt": row["closed_at"],
                "clean": None if row["clean"] is None else bool(row["clean"]),
                "scores": execution_scores(facts),
                "hasTape": bool(row["has_tape"]),
            })
        return out

    # -- one trade ----------------------------------------------------------------------

    def trade(self, cid: str) -> dict[str, Any] | None:
        """The whole record for one trade: immutable facts, then everything reviewed on top."""
        conn = self._connect()
        try:
            row = conn.execute(
                """
                SELECT c.*, p.timeframe, p.playbook_id, p.planned_sl, p.planned_tp, p.planned_rr,
                       p.market_session, p.setup_tag AS plan_setup, p.lots AS planned_lots,
                       p.max_lots_at_fire, p.inside_window, p.seconds_to_high_impact,
                       p.r_usd AS plan_r_usd, p.r_method, p.armed_at, p.created_at AS fired_at,
                       b.name AS playbook_name,
                       g.clean, g.required_pass, g.required_total, g.results,
                       r.intent, r.intent_by, r.note AS review_note, r.early_exit,
                       t.cid IS NOT NULL AS has_tape
                FROM trade_closed c
                LEFT JOIN trade_plan p ON p.cid = c.cid
                LEFT JOIN playbook b ON b.id = p.playbook_id
                LEFT JOIN trade_grade g ON g.cid = c.cid
                LEFT JOIN trade_review r ON r.cid = c.cid
                LEFT JOIN trade_tape t ON t.cid = c.cid
                WHERE c.cid = ?
                """,
                (cid,),
            ).fetchone()
            if row is None:
                return None

            events = [
                {"kind": e["kind"], "ts": e["ts"], "payload": json.loads(e["payload"] or "{}")}
                for e in conn.execute(
                    "SELECT kind, payload, ts FROM position_event WHERE cid = ? ORDER BY ts, id",
                    (cid,),
                ).fetchall()
            ]
            mistakes = [dict(m) for m in conn.execute(
                "SELECT code, source, note, ts FROM mistake_occurrence WHERE cid = ? ORDER BY ts",
                (cid,),
            ).fetchall()]
            attachments = self._attachments(conn, session_id=None, cid=cid)
            facts = self._facts_for(conn, row)
        finally:
            conn.close()

        intent, intent_by = derive_intent(
            grade_clean=None if row["clean"] is None else bool(row["clean"]),
            playbook_id=row["playbook_id"], confirmed=row["intent"],
        )
        return {
            # Immutable. Nothing in this phase writes any of it.
            "plan": {
                "cid": cid, "symbol": row["symbol"], "side": row["side"],
                "lots": row["planned_lots"], "timeframe": row["timeframe"],
                "playbookId": row["playbook_id"], "playbookName": row["playbook_name"],
                "plannedSl": row["planned_sl"], "plannedTp": row["planned_tp"],
                "plannedRr": row["planned_rr"], "marketSession": row["market_session"],
                "setupTag": row["plan_setup"], "rUsd": row["plan_r_usd"],
                "rMethod": row["r_method"], "armedAt": row["armed_at"],
                "firedAt": row["fired_at"],
            },
            "execution": {
                "entry": row["entry_price"], "exit": row["exit_price"],
                "openedAt": row["opened_at"], "closedAt": row["closed_at"],
                "lots": row["lots"], "rMultiple": row["r_multiple"], "rUsd": row["r_usd"],
                "mfe": row["mfe"], "mae": row["mae"], "events": events,
            },
            "grade": None if row["clean"] is None else {
                "clean": bool(row["clean"]), "requiredPass": row["required_pass"],
                "requiredTotal": row["required_total"],
                "results": json.loads(row["results"] or "[]"),
            },
            "actualVsPlan": actual_vs_plan(facts, side=row["side"]),
            "scores": execution_scores(facts),
            "intent": {"value": intent, "by": row["intent_by"] or intent_by},
            "review": {"note": row["review_note"], "earlyExit": bool(row["early_exit"] or 0)},
            "mistakes": mistakes,
            "attachments": attachments,
            # Phase 8 fills this. An empty list is what "no memo" looks like, not an error.
            "memos": [],
            "hasTape": bool(row["has_tape"]),
        }

    def _facts_for(self, conn: sqlite3.Connection, row: sqlite3.Row) -> TradeFacts:
        """Assemble the execution-score inputs, leaving anything uncaptured as `None`."""
        cid = row["cid"]
        amendments = tuple(
            {"ts": e["ts"], **json.loads(e["payload"] or "{}")}
            for e in conn.execute(
                "SELECT payload, ts FROM position_event WHERE cid = ? AND kind = 'amend' "
                "ORDER BY ts", (cid,)
            ).fetchall()
        )
        session_id = row["session_id"]
        analysis = conn.execute(
            "SELECT 1 FROM daily_analysis WHERE session_id = ?", (session_id,)
        ).fetchone()
        readiness = conn.execute(
            "SELECT COUNT(*) FROM readiness_check WHERE session_id = ?", (session_id,)
        ).fetchone()[0]
        post = conn.execute(
            "SELECT post_at FROM session_process WHERE session_id = ?", (session_id,)
        ).fetchone()
        replay = conn.execute(
            "SELECT 1 FROM review_event WHERE cid = ? AND kind = 'replay_open'", (cid,)
        ).fetchone()

        keys = row.keys()
        results = json.loads(row["results"] or "[]") if "results" in keys else None
        planned_sl = row["planned_sl"]
        worse = _has_worse(amendments, row["side"], planned_sl)

        return TradeFacts(
            cid=cid,
            had_daily_analysis=analysis is not None,
            readiness_complete=readiness >= len(READINESS_ITEMS),
            playbook_selected=bool(row["playbook_id"]),
            grade_clean=None if row["clean"] is None else bool(row["clean"]),
            within_lot_cap=(
                None if ("max_lots_at_fire" not in keys or row["max_lots_at_fire"] is None)
                else row["lots"] <= row["max_lots_at_fire"]
            ),
            stop_at_entry=planned_sl is not None,
            stop_never_worsened=None if planned_sl is None else not worse,
            respected_rules=None if row["clean"] is None else bool(row["clean"]),
            checklist_answered=None if results is None else _checklist_done(results),
            # Phase 8 is deferred, so a memo was never capturable — `None`, not a miss.
            has_memo=None,
            post_checkin=post is not None and post["post_at"] is not None,
            replay_opened=replay is not None,
            planned_r=row["planned_rr"] if "planned_rr" in keys else None,
            realised_r=row["r_multiple"],
            planned_sl=planned_sl,
            planned_tp=row["planned_tp"] if "planned_tp" in keys else None,
            amendments=amendments,
        )

    # -- review writes ------------------------------------------------------------------

    def put_review(self, cid: str, body: dict[str, Any], ts_ms: int) -> None:
        """Annotate a trade. It can never rewrite one."""
        intent = body.get("intent")
        if intent not in (None, "planned", "impulsive", "revenge", "unknown"):
            raise ValueError(f"unknown intent `{intent}`")
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO trade_review (cid, updated_at, intent, intent_by, note, early_exit) "
                "VALUES (?,?,?,?,?,?) ON CONFLICT (cid) DO UPDATE SET "
                "updated_at = excluded.updated_at, intent = excluded.intent, "
                "intent_by = excluded.intent_by, note = excluded.note, "
                "early_exit = excluded.early_exit",
                (cid, ts_ms, intent, "player" if intent else None, _text(body.get("note")),
                 int(bool(body.get("earlyExit")))),
            )
            conn.commit()
        finally:
            conn.close()

    def sync_mistakes(self, cid: str, ts_ms: int) -> list[str]:
        """Re-derive the provable mistakes for one trade. Player-asserted ones are left alone."""
        conn = self._connect()
        try:
            row = conn.execute(
                """
                SELECT c.cid, c.session_id, c.side, p.lots, p.max_lots_at_fire, p.planned_sl,
                       p.seconds_to_high_impact, p.inside_window, p.playbook_id, g.results
                FROM trade_closed c
                LEFT JOIN trade_plan p ON p.cid = c.cid
                LEFT JOIN trade_grade g ON g.cid = c.cid
                WHERE c.cid = ?
                """,
                (cid,),
            ).fetchone()
            if row is None:
                return []
            amendments = tuple(
                {"ts": e["ts"], **json.loads(e["payload"] or "{}")}
                for e in conn.execute(
                    "SELECT payload, ts FROM position_event WHERE cid = ? AND kind = 'amend'",
                    (cid,)
                ).fetchall()
            )
            replay = conn.execute(
                "SELECT 1 FROM review_event WHERE cid = ? AND kind = 'replay_open'", (cid,)
            ).fetchone()
            results = json.loads(row["results"] or "[]")

            codes = derive(FireEvidence(
                cid=cid, session_id=row["session_id"], lots=row["lots"],
                max_lots=row["max_lots_at_fire"], planned_sl=row["planned_sl"],
                side=row["side"] or "buy", amendments=amendments,
                seconds_to_high_impact=row["seconds_to_high_impact"],
                inside_window=None if row["inside_window"] is None else bool(row["inside_window"]),
                playbook_id=row["playbook_id"],
                checklist_answered=_checklist_done(results) if results else False,
                replay_opened=replay is not None,
            ))
            # Only the `auto` rows are replaced; a player's own judgement is never overwritten.
            conn.execute("DELETE FROM mistake_occurrence WHERE cid = ? AND source = 'auto'", (cid,))
            conn.executemany(
                "INSERT OR IGNORE INTO mistake_occurrence (cid, session_id, code, source, ts) "
                "VALUES (?,?,?,'auto',?)",
                [(cid, row["session_id"], code, ts_ms) for code in codes],
            )
            conn.commit()
        finally:
            conn.close()
        return codes

    def add_mistake(self, cid: str, code: str, ts_ms: int, note: str | None = None) -> None:
        """A judgement the player made. Stored as `player` so the trend can keep the two apart."""
        conn = self._connect()
        try:
            session_id = conn.execute(
                "SELECT session_id FROM trade_closed WHERE cid = ?", (cid,)
            ).fetchone()
            conn.execute(
                "INSERT OR IGNORE INTO mistake_occurrence (cid, session_id, code, source, note, ts) "
                "VALUES (?,?,?,'player',?,?)",
                (cid, None if session_id is None else session_id["session_id"], code,
                 _text(note), ts_ms),
            )
            conn.commit()
        finally:
            conn.close()

    def remove_mistake(self, cid: str, code: str) -> None:
        """Only a player's own judgement can be withdrawn; derived rows come back on the next sync."""
        conn = self._connect()
        try:
            conn.execute(
                "DELETE FROM mistake_occurrence WHERE cid = ? AND code = ? AND source = 'player'",
                (cid, code),
            )
            conn.commit()
        finally:
            conn.close()

    def define_mistake(self, code: str, label: str, ts_ms: int) -> None:
        """A custom mistake is a built-in with `builtin = 0`; the same code counts and trends it."""
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO mistake_definition (code, label, builtin, active, created_at) "
                "VALUES (?,?,0,1,?) ON CONFLICT (code) DO UPDATE SET label = excluded.label",
                (code, label, ts_ms),
            )
            conn.commit()
        finally:
            conn.close()

    def taxonomy(self) -> dict[str, Any]:
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT code, label, builtin, active FROM mistake_definition ORDER BY builtin DESC, code"
            ).fetchall()
        finally:
            conn.close()
        derivable = {m.code for m in BUILTINS if m.derivable}
        return {"mistakes": [
            {"code": r["code"], "label": r["label"], "builtin": bool(r["builtin"]),
             "active": bool(r["active"]), "derivable": r["code"] in derivable}
            for r in rows
        ]}

    # -- system -------------------------------------------------------------------------

    def system(self) -> dict[str, Any]:
        """Philosophy and core principles. One row, because this is a statement, not a log."""
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT updated_at, philosophy, principles, focus_code FROM system_principles "
                "WHERE id = 1"
            ).fetchone()
        finally:
            conn.close()
        if row is None:
            return {"philosophy": None, "principles": [], "focusCode": None, "updatedAt": None}
        return {"philosophy": row["philosophy"],
                "principles": json.loads(row["principles"] or "[]"),
                "focusCode": row["focus_code"], "updatedAt": row["updated_at"]}

    def put_system(self, body: dict[str, Any], ts_ms: int) -> None:
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO system_principles (id, updated_at, philosophy, principles, focus_code) "
                "VALUES (1,?,?,?,?) ON CONFLICT (id) DO UPDATE SET updated_at = excluded.updated_at, "
                "philosophy = excluded.philosophy, principles = excluded.principles, "
                "focus_code = excluded.focus_code",
                (ts_ms, _text(body.get("philosophy")), _json(body.get("principles")),
                 _text(body.get("focusCode"))),
            )
            conn.commit()
        finally:
            conn.close()

    def aggregates(self) -> dict[str, Any]:
        """What the copilot's read-only context gains. Counts and codes; no player prose, no money."""
        overview = self.overview()
        return {
            "sessions": overview["sessions"],
            "consistency": overview["consistency"],
            "groups": overview["groups"]["groups"],
            "topMistakes": [m["code"] for m in overview["mistakes"]["mistakes"][:3]],
            "focus": overview["mistakes"]["focus"],
        }


# -- helpers ---------------------------------------------------------------------------

# Player prose is capped so one paste cannot fill the row, and stored as text so it renders as a
# text child. Nothing in this journal ever emits it as markup.
MAX_TEXT = 8_000


def _text(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)[:MAX_TEXT]


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else [], sort_keys=True)[:MAX_TEXT]


def _analysis_payload(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
        "updatedAt": row["updated_at"], "thesis": row["thesis"],
        "instruments": json.loads(row["instruments"] or "[]"),
        "keyLevels": json.loads(row["key_levels"] or "[]"),
        "invalidation": row["invalidation"], "eventRisks": row["event_risks"],
        "tags": json.loads(row["tags"] or "[]"), "notes": row["notes"],
    }


def _checklist_done(results: list[dict[str, Any]]) -> bool:
    manual = [r for r in results if isinstance(r, dict) and r.get("kind") == "manual"]
    return all(not r.get("unknown") for r in manual) if manual else True


def _has_worse(amendments: tuple[dict[str, Any], ...], side: str | None,
               planned_sl: float | None) -> bool:
    from journal.metrics import worsened_stops

    return bool(worsened_stops(amendments, side=side or "buy", original_sl=planned_sl))


def now_ms() -> int:
    return int(time.time() * 1000)
