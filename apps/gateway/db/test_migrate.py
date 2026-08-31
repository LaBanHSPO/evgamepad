"""Migration runner: ordered, recorded once, and transactional on failure."""

from __future__ import annotations

from pathlib import Path

import pytest

from db.migrate import MigrationError, apply_all, connect, discover, migrate


def write(directory: Path, name: str, sql: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_text(sql, encoding="utf-8")


def test_fresh_db_applies_in_order_and_a_second_run_is_a_no_op(tmp_path: Path) -> None:
    migrations = tmp_path / "migrations"
    write(migrations, "002-second.sql", "CREATE TABLE b (id INTEGER PRIMARY KEY);")
    write(migrations, "001-first.sql", "CREATE TABLE a (id INTEGER PRIMARY KEY);")

    db = tmp_path / "journal.db"
    assert migrate(db, migrations) == ["001-first", "002-second"]
    assert migrate(db, migrations) == []

    conn = connect(db)
    try:
        ids = [r[0] for r in conn.execute("SELECT id FROM schema_migration ORDER BY id")]
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    finally:
        conn.close()
    assert ids == ["001-first", "002-second"]
    assert {"a", "b"} <= tables


def test_a_failed_migration_rolls_back_and_is_not_recorded(tmp_path: Path) -> None:
    migrations = tmp_path / "migrations"
    write(migrations, "001-good.sql", "CREATE TABLE a (id INTEGER PRIMARY KEY);")
    write(
        migrations,
        "002-bad.sql",
        "CREATE TABLE b (id INTEGER PRIMARY KEY);\nCREATE TABLE a (id INTEGER PRIMARY KEY);\n",
    )

    db = tmp_path / "journal.db"
    with pytest.raises(MigrationError, match="002-bad"):
        migrate(db, migrations)

    conn = connect(db)
    try:
        ids = [r[0] for r in conn.execute("SELECT id FROM schema_migration")]
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    finally:
        conn.close()
    # 001 stands; 002 left neither its table nor a ledger row.
    assert ids == ["001-good"]
    assert "b" not in tables


def test_editing_an_applied_migration_is_refused(tmp_path: Path) -> None:
    migrations = tmp_path / "migrations"
    write(migrations, "001-first.sql", "CREATE TABLE a (id INTEGER PRIMARY KEY);")
    db = tmp_path / "journal.db"
    migrate(db, migrations)

    write(migrations, "001-first.sql", "CREATE TABLE a (id INTEGER PRIMARY KEY, extra TEXT);")
    with pytest.raises(MigrationError, match="different body"):
        migrate(db, migrations)


def test_ambiguous_migration_sets_are_refused(tmp_path: Path) -> None:
    migrations = tmp_path / "migrations"
    write(migrations, "001-first.sql", "CREATE TABLE a (id INTEGER PRIMARY KEY);")
    write(migrations, "001-also-first.sql", "CREATE TABLE b (id INTEGER PRIMARY KEY);")
    with pytest.raises(MigrationError, match="duplicate migration prefix"):
        discover(migrations)

    bad = tmp_path / "bad"
    write(bad, "core.sql", "CREATE TABLE a (id INTEGER PRIMARY KEY);")
    with pytest.raises(MigrationError, match="NNN-kebab-slug"):
        discover(bad)


def test_the_real_migrations_directory_is_consistent() -> None:
    """Phase 1 owns the runner, later phases own the files; whatever is there must be valid."""
    discover()


def test_apply_all_is_idempotent_on_an_open_connection(tmp_path: Path) -> None:
    migrations = tmp_path / "migrations"
    write(migrations, "001-first.sql", "CREATE TABLE a (id INTEGER PRIMARY KEY);")
    conn = connect(tmp_path / "journal.db")
    try:
        assert apply_all(conn, migrations) == ["001-first"]
        assert apply_all(conn, migrations) == []
    finally:
        conn.close()
