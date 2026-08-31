"""Ordered, transactional, idempotent SQLite migration runner.

Later phases own their own tables. Phase 1 owns only the mechanism and the ledger, so no phase
has to pretend the final schema exists on day one.

Each migration runs inside one explicit transaction together with its ledger row: a migration
that raises rolls back completely and is *not* recorded, so a re-run retries it from scratch.
"""

from __future__ import annotations

import hashlib
import re
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).parent / "migrations"

# `001-core-trading.sql` — the numeric prefix is the ordering key and the ledger id stem.
MIGRATION_NAME = re.compile(r"^(\d{3})-[a-z0-9]+(?:-[a-z0-9]+)*\.sql$")

LEDGER_DDL = """
CREATE TABLE IF NOT EXISTS schema_migration (
    id         TEXT PRIMARY KEY,
    checksum   TEXT NOT NULL,
    applied_at TEXT NOT NULL
)
"""


class MigrationError(RuntimeError):
    """A migration set that cannot be trusted, or a migration that failed to apply."""


@dataclass(frozen=True)
class Migration:
    id: str
    path: Path
    sql: str

    @property
    def checksum(self) -> str:
        return hashlib.sha256(self.sql.encode("utf-8")).hexdigest()


def discover(directory: Path = MIGRATIONS_DIR) -> list[Migration]:
    """Read migrations in numeric order, refusing anything ambiguous."""
    if not directory.is_dir():
        return []
    found: dict[str, Migration] = {}
    for path in sorted(directory.glob("*.sql")):
        match = MIGRATION_NAME.match(path.name)
        if match is None:
            raise MigrationError(f"migration `{path.name}` must be named NNN-kebab-slug.sql")
        prefix = match.group(1)
        if prefix in found:
            raise MigrationError(
                f"duplicate migration prefix {prefix}: {found[prefix].path.name} and {path.name}"
            )
        found[prefix] = Migration(id=path.stem, path=path, sql=path.read_text(encoding="utf-8"))
    return [found[k] for k in sorted(found)]


def _statements(sql: str) -> list[str]:
    """Split a migration into individual statements.

    `executescript` would commit our explicit transaction out from under us, so statements are
    executed one at a time instead. Statement-level BEGIN/END blocks (triggers) are not split
    correctly by `complete_statement`; migrations that need one should live in their own file.
    """
    statements: list[str] = []
    buffer = ""
    for line in sql.splitlines(keepends=True):
        buffer += line
        if sqlite3.complete_statement(buffer):
            if buffer.strip():
                statements.append(buffer)
            buffer = ""
    if buffer.strip():
        raise MigrationError(f"trailing incomplete SQL statement: {buffer.strip()[:80]!r}")
    return statements


def _applied(conn: sqlite3.Connection) -> dict[str, str]:
    rows = conn.execute("SELECT id, checksum FROM schema_migration").fetchall()
    return {row[0]: row[1] for row in rows}


def connect(db_path: str | Path) -> sqlite3.Connection:
    """Open the journal DB with the settings the gateway relies on."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # isolation_level=None hands transaction control to us, which is what makes a failed
    # migration roll back instead of half-applying.
    conn = sqlite3.connect(path, isolation_level=None)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def apply_all(conn: sqlite3.Connection, directory: Path = MIGRATIONS_DIR) -> list[str]:
    """Apply every unapplied migration in order. Returns the ids applied by this call."""
    conn.execute(LEDGER_DDL)
    migrations = discover(directory)
    applied = _applied(conn)

    for migration in migrations:
        recorded = applied.get(migration.id)
        if recorded is not None and recorded != migration.checksum:
            raise MigrationError(
                f"migration `{migration.id}` was applied with a different body; "
                "edit history instead of rewriting an applied migration"
            )

    newly_applied: list[str] = []
    for migration in migrations:
        if migration.id in applied:
            continue
        conn.execute("BEGIN")
        try:
            for statement in _statements(migration.sql):
                conn.execute(statement)
            conn.execute(
                "INSERT INTO schema_migration (id, checksum, applied_at) VALUES (?, ?, ?)",
                (migration.id, migration.checksum, datetime.now(UTC).isoformat()),
            )
            conn.execute("COMMIT")
        except Exception as exc:
            conn.execute("ROLLBACK")
            raise MigrationError(f"migration `{migration.id}` failed and was rolled back: {exc}") from exc
        newly_applied.append(migration.id)
    return newly_applied


def migrate(db_path: str | Path, directory: Path = MIGRATIONS_DIR) -> list[str]:
    """Open the DB and bring it up to date. The gateway calls this at boot."""
    conn = connect(db_path)
    try:
        return apply_all(conn, directory)
    finally:
        conn.close()
