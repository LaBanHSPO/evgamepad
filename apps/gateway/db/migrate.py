"""Ordered, transactional, idempotent migration runner.

Each phase owns one additive migration file. The runner tracks **every applied
id**, not a single high-water mark, so a phase landing out of order is a visible
error rather than a silently skipped table.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).parent / "migrations"

#: ``001-core-trading.sql`` -> id ``001``, name ``core-trading``.
_NAME_RE = re.compile(r"^(?P<id>\d{3})-(?P<name>[a-z0-9-]+)\.sql$")

#: Migration files are DDL only; the runner owns the transaction.
_TXN_RE = re.compile(r"^\s*(BEGIN|COMMIT|ROLLBACK|END)\b", re.I | re.M)

LEDGER_DDL = """
CREATE TABLE IF NOT EXISTS schema_migration (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    applied_at  TEXT NOT NULL DEFAULT (datetime('now')),
    sha256      TEXT NOT NULL
)
"""


class MigrationError(RuntimeError):
    pass


@dataclass(frozen=True)
class Migration:
    id: str
    name: str
    path: Path

    @property
    def sql(self) -> str:
        return self.path.read_text()

    @property
    def sha256(self) -> str:
        import hashlib

        return hashlib.sha256(self.sql.encode()).hexdigest()


def discover(directory: Path = MIGRATIONS_DIR) -> list[Migration]:
    """Every migration in the directory, in id order. A misnamed file is an
    error -- silently ignoring it would ship a missing table."""
    found: list[Migration] = []
    seen: set[str] = set()
    for path in sorted(directory.glob("*.sql")):
        m = _NAME_RE.match(path.name)
        if not m:
            raise MigrationError(f"{path.name}: expected NNN-kebab-name.sql")
        mid = m.group("id")
        if mid in seen:
            raise MigrationError(f"duplicate migration id {mid}")
        seen.add(mid)
        found.append(Migration(id=mid, name=m.group("name"), path=path))
    return found


def connect(db_path: str | Path) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # check_same_thread=False because the connection outlives the thread that
    # opened it: the app is constructed on one thread and served on the loop's,
    # and the documented Twisted fallback (running OpenApiPy on its own thread
    # with a run_coroutine_threadsafe bridge) would cross threads again.
    # JournalWriter serialises every statement behind a lock; nothing else may
    # use this connection concurrently.
    conn = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def applied(conn: sqlite3.Connection) -> dict[str, str]:
    conn.execute(LEDGER_DDL)
    rows = conn.execute("SELECT id, sha256 FROM schema_migration").fetchall()
    return {r["id"]: r["sha256"] for r in rows}


def migrate(
    conn: sqlite3.Connection, directory: Path = MIGRATIONS_DIR
) -> list[Migration]:
    """Apply what is missing and return it. A second call is a no-op.

    Each migration runs inside its own transaction together with its ledger row,
    so a failure rolls the whole thing back and is *not* recorded as applied.
    """
    done = applied(conn)
    pending = [m for m in discover(directory) if m.id not in done]

    for m in discover(directory):
        if m.id in done and done[m.id] != m.sha256:
            raise MigrationError(
                f"migration {m.id}-{m.name} changed after it was applied; "
                "migrations are append-only"
            )

    run: list[Migration] = []
    for m in pending:
        sql = m.sql
        if _TXN_RE.search(sql):
            raise MigrationError(
                f"{m.id}-{m.name} manages its own transaction; the runner owns that"
            )
        try:
            # The BEGIN has to live *inside* the script: executescript commits any
            # transaction that is already open before it runs, so a BEGIN issued
            # beforehand would be thrown away and a half-applied migration would
            # survive its own failure. No COMMIT here -- the ledger row below
            # joins the same transaction, which is the point.
            conn.executescript("BEGIN;\n" + sql)
            conn.execute(
                "INSERT INTO schema_migration (id, name, sha256) VALUES (?, ?, ?)",
                (m.id, m.name, m.sha256),
            )
            conn.execute("COMMIT")
        except Exception as exc:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise MigrationError(f"{m.id}-{m.name} failed: {exc}") from exc
        run.append(m)
    return run


def main(argv: list[str] | None = None) -> int:
    import argparse

    from ..config import load

    ap = argparse.ArgumentParser(description="Apply ev-gateway migrations")
    ap.add_argument("--config", default="config/default.yaml")
    ap.add_argument("--db", default=None, help="override config db_path")
    args = ap.parse_args(argv)

    db = args.db or load(args.config).db_path
    conn = connect(db)
    try:
        run = migrate(conn)
    finally:
        conn.close()
    if run:
        for m in run:
            print(f"applied {m.id}-{m.name}")
    else:
        print("up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
