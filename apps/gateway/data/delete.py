"""Delete everything, on purpose and only on purpose.

The gate is deliberately awkward: an exact confirmation phrase, a two-second hold, a locked
session, and no open position. Nothing here is friction for its own sake — each condition exists
because the alternative is losing a year of journal to a mis-click during a live trade.

What survives, and why: the config, the whisper models, the app itself, the broker credentials, and
**one audit row** recording the action, the time and the counts. What does not survive: every
journal row, every memo, every screenshot, every tape.

The audit row is content-free on purpose. A row that quoted a deleted note would mean the delete
did not happen.

The UI offers a backup before this runs. It never takes one afterwards: a hidden recovery copy
made after the final confirmation is not a safety net, it is a lie about what "delete" means.
"""

from __future__ import annotations

import shutil
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Typed exactly, including the case. A phrase you can pass with a stray keystroke is not a gate.
CONFIRMATION = "DELETE EVERYTHING"

# How long the pad or key must be held. Long enough to be a decision, short enough not to be theatre.
HOLD_MS = 2000

# Every table whose rows are journal content. Order matters: children before parents, because the
# foreign keys are real.
CONTENT_TABLES = (
    "mistake_occurrence", "trade_review", "readiness_check", "daily_analysis",
    "journal_attachment", "review_event", "tilt_sample", "session_score", "trade_grade",
    "trade_tape", "position_event", "trade_closed", "trade_plan", "cid_reservation",
    "signal_item", "session_plan", "session_process", "session_equity",
    "playbook_rule", "playbook", "pad_event", "system_principles", "mistake_definition",
)

# Media directories emptied alongside the rows. `models` and `secure` are untouched: one is
# replaceable and the other is a credential, and neither is journal content.
CONTENT_DIRS = ("attachments", "voice", "backups")


class DeleteRefused(RuntimeError):
    """The gate said no. Nothing was deleted."""


@dataclass(frozen=True)
class Confirmation:
    """Everything the player had to do to get here."""

    phrase: str
    held_ms: int
    locked: bool
    positions_open: int

    def check(self) -> None:
        # Ordered cheapest-first so the message names the most fixable problem.
        if self.positions_open:
            raise DeleteRefused(f"{self.positions_open} position(s) are still open")
        if not self.locked:
            raise DeleteRefused("lock the session first")
        if self.phrase != CONFIRMATION:
            raise DeleteRefused(f"type `{CONFIRMATION}` exactly")
        if self.held_ms < HOLD_MS:
            raise DeleteRefused(f"hold the confirm for {HOLD_MS / 1000:g} seconds")


def delete_all(data_dir: Path, *, confirmation: Confirmation,
               now_ms: int | None = None) -> dict[str, Any]:
    """Empty the journal. Returns counts only — never anything that was in it."""
    confirmation.check()
    stamp = now_ms if now_ms is not None else int(time.time() * 1000)
    db_path = data_dir / "journal.db"

    removed: dict[str, int] = {}
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = OFF")
        for table in CONTENT_TABLES:
            try:
                before = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                conn.execute(f"DELETE FROM {table}")
                if before:
                    removed[table] = before
            except sqlite3.Error:
                # A table this build does not have is not an error; it is simply not there.
                continue
        conn.commit()
        conn.execute("PRAGMA foreign_keys = ON")

        files = 0
        for name in CONTENT_DIRS:
            directory = data_dir / name
            if not directory.is_dir():
                continue
            files += sum(1 for p in directory.rglob("*") if p.is_file())
            shutil.rmtree(directory, ignore_errors=True)
            directory.mkdir(parents=True, exist_ok=True)

        # One content-free row: what happened, when, and how much. Written before the vacuum so
        # the space it needs is already accounted for.
        conn.execute(
            "INSERT INTO data_operation (action, started_at, finished_at, ok, counts, note) "
            "VALUES ('delete_all', ?, ?, 1, ?, 'confirmed by the player')",
            (stamp, stamp, _counts_json({"rows": sum(removed.values()), "files": files,
                                         "tables": len(removed)})),
        )
        conn.commit()

        # Reclaims the pages the deleted rows held. Without it the file still contains them.
        conn.execute("VACUUM")
        conn.commit()
    finally:
        conn.close()

    return {"ok": True, "rows": sum(removed.values()), "tables": len(removed),
            "files": files, "byTable": removed}


def _counts_json(counts: dict[str, int]) -> str:
    import json

    return json.dumps(counts, sort_keys=True)


def residue(data_dir: Path) -> dict[str, Any]:
    """What is left afterwards. The delete test asserts against this rather than trusting the return."""
    db_path = data_dir / "journal.db"
    conn = sqlite3.connect(db_path)
    try:
        rows = {}
        for table in CONTENT_TABLES:
            try:
                rows[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            except sqlite3.Error:
                continue
        audit = conn.execute("SELECT COUNT(*) FROM data_operation").fetchone()[0]
    finally:
        conn.close()

    files = {
        name: sum(1 for p in (data_dir / name).rglob("*") if p.is_file())
        for name in CONTENT_DIRS if (data_dir / name).is_dir()
    }
    return {"rows": rows, "auditRows": audit, "files": files}
