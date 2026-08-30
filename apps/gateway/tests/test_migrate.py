"""The runner applies each migration exactly once, in order, atomically."""

from __future__ import annotations

import pytest

from apps.gateway.db import migrate as M


#: Which migration owns which tables. Each phase adds its own row; a table
#: appearing in the wrong one means a phase stopped owning its own migration.
OWNERSHIP = {
    "001": {"cid_ledger", "session", "session_equity", "trade_plan",
            "position_event", "trade_closed", "trade_tape"},
    "002": {"pad_event", "session_process"},
    "003": {"playbook", "playbook_rule", "trade_grade"},
    "004": {"tilt_sample"},
    "005": {"score_session"},
}


def test_shipped_migrations_apply_once(tmp_path):
    conn = M.connect(tmp_path / "ev.sqlite3")
    first = M.migrate(conn)
    assert [m.id for m in first] == ["001", "002", "003", "004", "005"]
    assert M.migrate(conn) == []

    tables = {
        r["name"]
        for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    for owned in OWNERSHIP.values():
        assert owned <= tables
    assert "schema_migration" in tables
    # Nothing a later phase owns has leaked in early. Phase 7 took `playbook`,
    # so this list shrinks as phases land.
    assert not tables & {"voice_memo", "voice_transcript"}


def test_each_migration_creates_only_what_it_owns(tmp_path):
    """Applied one at a time, each migration adds exactly its own tables."""
    conn = M.connect(tmp_path / "ev.sqlite3")
    seen: set[str] = set()
    for migration in M.discover():
        M.migrate(conn, _only(migration))
        tables = {
            r["name"]
            for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        added = tables - seen - {"schema_migration", "sqlite_sequence"}
        assert added == OWNERSHIP[migration.id], migration.id
        seen = tables


def _only(migration):
    """A directory view containing just this migration, for stepwise apply."""
    import types

    directory = types.SimpleNamespace()
    directory.glob = lambda _pattern: [migration.path]
    return directory


def test_failed_migration_rolls_back_and_is_not_recorded(tmp_path):
    d = tmp_path / "m"
    d.mkdir()
    (d / "001-good.sql").write_text("CREATE TABLE good (x);")
    (d / "002-bad.sql").write_text("CREATE TABLE half (x);\nCREATE TABLE oops (;")

    conn = M.connect(tmp_path / "ev.sqlite3")
    with pytest.raises(M.MigrationError):
        M.migrate(conn, d)

    tables = {r["name"] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    assert "good" in tables
    assert "half" not in tables, "a failed migration left a table behind"
    assert set(M.applied(conn)) == {"001"}


def test_edited_migration_is_refused(tmp_path):
    d = tmp_path / "m"
    d.mkdir()
    (d / "001-a.sql").write_text("CREATE TABLE a (x);")
    conn = M.connect(tmp_path / "ev.sqlite3")
    M.migrate(conn, d)
    (d / "001-a.sql").write_text("CREATE TABLE a (x, y);")
    with pytest.raises(M.MigrationError, match="append-only"):
        M.migrate(conn, d)


def test_misnamed_file_is_an_error(tmp_path):
    d = tmp_path / "m"
    d.mkdir()
    (d / "core.sql").write_text("SELECT 1;")
    with pytest.raises(M.MigrationError, match="NNN-kebab-name"):
        M.discover(d)


def test_migration_may_not_manage_its_own_transaction(tmp_path):
    d = tmp_path / "m"
    d.mkdir()
    (d / "001-a.sql").write_text("BEGIN;\nCREATE TABLE a (x);\nCOMMIT;")
    conn = M.connect(tmp_path / "ev.sqlite3")
    with pytest.raises(M.MigrationError, match="own transaction"):
        M.migrate(conn, d)
