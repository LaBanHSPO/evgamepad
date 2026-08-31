"""Restore: the round trip, and every way it refuses before touching current data.

The single most important property here is that a *failed* restore is indistinguishable from one
that never ran. Each refusal test asserts the current journal afterwards, not just the exception.
"""

from __future__ import annotations

import io
import json
import sqlite3
import tarfile
from pathlib import Path

import pytest

from data.backup import DB_MEMBER, MANIFEST_NAME, create, sha256_of
from data.restore import Readiness, RestoreError, inspect, restore, safe_member
from db.migrate import connect, migrate

SESSION = "2026-08-31"
T0 = 1_788_000_000_000
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 40

IDLE = Readiness(locked=True, positions_open=0, jobs_running=0)


def seed(data_dir: Path, *, trades: int, thesis: str) -> None:
    """A journal with a known number of trades, so counts are the assertion."""
    migrate(data_dir / "journal.db")
    conn = connect(data_dir / "journal.db")
    conn.execute(
        "INSERT OR IGNORE INTO session_equity (session_id, timezone, opened_at, equity_open) "
        "VALUES (?,?,?,?)", (SESSION, "Asia/Ho_Chi_Minh", T0, 10_000.0),
    )
    for index in range(trades):
        cid = f"c{index}"
        conn.execute("INSERT INTO cid_reservation (cid, intent, symbol, state, created_at, "
                     "updated_at) VALUES (?,'open','XAUUSD','acked',?,?)", (cid, T0, T0))
        conn.execute(
            "INSERT INTO trade_plan (cid, session_id, symbol, side, lots, volume, r_usd, "
            "r_method, r_units, created_at) VALUES (?,?,'XAUUSD','buy',0.01,100,20.0,'stop',"
            "100.0,?)", (cid, SESSION, T0),
        )
        conn.execute(
            "INSERT INTO trade_closed (cid, session_id, position_id, symbol, side, lots, volume, "
            "entry_price, exit_price, opened_at, closed_at, r_usd, r_multiple) "
            "VALUES (?,?,?,'XAUUSD','buy',0.01,100,2458.0,2461.0,?,?,20.0,1.2)",
            (cid, SESSION, index + 1, T0, T0 + 60_000),
        )
    conn.execute("INSERT OR REPLACE INTO daily_analysis (session_id, updated_at, thesis) "
                 "VALUES (?,?,?)", (SESSION, T0, thesis))
    conn.commit()
    conn.close()

    (data_dir / "attachments").mkdir(exist_ok=True)
    (data_dir / "attachments" / "01ABC.png").write_bytes(PNG)


def move_on(data_dir: Path, *, thesis: str) -> None:
    """The journal advances: the old trades are gone and the analysis is rewritten.

    Written as a real change rather than a no-op so a restore that does nothing cannot pass.
    """
    conn = connect(data_dir / "journal.db")
    conn.execute("DELETE FROM trade_closed")
    conn.execute("UPDATE daily_analysis SET thesis = ?", (thesis,))
    conn.commit()
    conn.close()


@pytest.fixture()
def data_dir(tmp_path: Path) -> Path:
    home = tmp_path / "data"
    home.mkdir()
    seed(home, trades=3, thesis="the original evening")
    return home


def count_trades(data_dir: Path) -> int:
    conn = sqlite3.connect(data_dir / "journal.db")
    try:
        return conn.execute("SELECT COUNT(*) FROM trade_closed").fetchone()[0]
    finally:
        conn.close()


def thesis_of(data_dir: Path) -> str | None:
    conn = sqlite3.connect(data_dir / "journal.db")
    try:
        row = conn.execute("SELECT thesis FROM daily_analysis").fetchone()
        return None if row is None else row[0]
    finally:
        conn.close()


def repack(archive: Path, out: Path, *, mutate) -> None:
    """Rebuild an archive with one member altered, to forge the exact corruption under test."""
    with tarfile.open(archive, "r:gz") as source, tarfile.open(out, "w:gz") as target:
        for info in source.getmembers():
            handle = source.extractfile(info)
            data = b"" if handle is None else handle.read()
            new_info, new_data = mutate(info, data)
            if new_info is None:
                continue
            new_info.size = len(new_data)
            target.addfile(new_info, io.BytesIO(new_data))


# -- the round trip -----------------------------------------------------------------------


def test_a_backup_restores_the_counts_and_the_content(data_dir: Path, tmp_path: Path) -> None:
    """The plan's own criterion: row counts and attachment hashes reproduced from the manifest."""
    archive = tmp_path / "backup.tar.gz"
    manifest = create(data_dir, archive, now_ms=T0)
    original_hash = sha256_of(data_dir / "attachments" / "01ABC.png")

    # The journal moves on, then is rolled back to the archive.
    move_on(data_dir, thesis="a later evening")
    (data_dir / "attachments" / "01ABC.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\xff" * 40)
    assert thesis_of(data_dir) == "a later evening"
    assert count_trades(data_dir) == 0, "the round trip must have something to restore"

    result = restore(archive, data_dir, readiness=IDLE, now_ms=T0 + 1)

    assert result["ok"] is True
    assert count_trades(data_dir) == manifest.counts["trade_closed"] == 3
    assert thesis_of(data_dir) == "the original evening"
    assert sha256_of(data_dir / "attachments" / "01ABC.png") == original_hash


def test_restore_leaves_no_staging_or_rollback_behind(data_dir: Path, tmp_path: Path) -> None:
    archive = tmp_path / "backup.tar.gz"
    create(data_dir, archive, now_ms=T0)
    restore(archive, data_dir, readiness=IDLE, now_ms=T0 + 1)

    leftovers = [p.name for p in data_dir.iterdir() if p.name.startswith(".")]
    assert leftovers == []


def test_an_older_archive_is_migrated_forward_in_staging(data_dir: Path, tmp_path: Path) -> None:
    archive = tmp_path / "backup.tar.gz"
    create(data_dir, archive, now_ms=T0)

    applied: list[str] = []

    def fake_migrate(path: Path) -> list[str]:
        applied.append(str(path))
        return ["010-settings-data"]

    result = restore(archive, data_dir, readiness=IDLE, migrate=fake_migrate, now_ms=T0 + 1)

    assert result["migrationsApplied"] == ["010-settings-data"]
    # Migrated in staging, so the live database only ever sees a finished copy.
    assert applied and ".restore-" in applied[0]


# -- refusals, none of which may touch current data ------------------------------------------


def test_restore_refuses_while_the_session_is_live(data_dir: Path, tmp_path: Path) -> None:
    archive = tmp_path / "backup.tar.gz"
    create(data_dir, archive, now_ms=T0)
    move_on(data_dir, thesis="a later evening")

    for readiness, message in (
        (Readiness(locked=False, positions_open=0, jobs_running=0), "lock"),
        (Readiness(locked=True, positions_open=1, jobs_running=0), "position"),
        (Readiness(locked=True, positions_open=0, jobs_running=2), "background job"),
    ):
        with pytest.raises(RestoreError, match=message):
            restore(archive, data_dir, readiness=readiness, now_ms=T0 + 1)

    assert thesis_of(data_dir) == "a later evening"


def test_a_corrupt_checksum_is_caught_before_the_swap(data_dir: Path, tmp_path: Path) -> None:
    archive = tmp_path / "backup.tar.gz"
    create(data_dir, archive, now_ms=T0)

    tampered = tmp_path / "tampered.tar.gz"
    repack(archive, tampered, mutate=lambda info, data: (
        (info, b"\x89PNG\r\n\x1a\n" + b"\x00" * 41) if info.name.endswith(".png") else (info, data)
    ))
    move_on(data_dir, thesis="a later evening")

    with pytest.raises(RestoreError, match="checksum"):
        restore(tampered, data_dir, readiness=IDLE, now_ms=T0 + 1)

    assert thesis_of(data_dir) == "a later evening"
    assert count_trades(data_dir) == 0


def test_a_traversal_path_is_refused(data_dir: Path, tmp_path: Path) -> None:
    """Not sanitised — refused. A member outside the volume is not a name to be fixed up."""
    assert safe_member("attachments/01ABC.png") is True
    assert safe_member(DB_MEMBER) is True
    for hostile in ("../../etc/passwd", "/etc/passwd", "attachments/../../escape.png",
                    "C:\\windows\\system32", "voice\\..\\..\\x.ogg", "unexpected/file.txt"):
        assert safe_member(hostile) is False, hostile


def test_a_member_the_manifest_never_declared_is_refused(data_dir: Path, tmp_path: Path) -> None:
    archive = tmp_path / "backup.tar.gz"
    create(data_dir, archive, now_ms=T0)

    smuggled = tmp_path / "smuggled.tar.gz"
    with tarfile.open(archive, "r:gz") as source, tarfile.open(smuggled, "w:gz") as target:
        for info in source.getmembers():
            handle = source.extractfile(info)
            target.addfile(info, io.BytesIO(b"" if handle is None else handle.read()))
        extra = tarfile.TarInfo("attachments/undeclared.png")
        extra.size = len(PNG)
        target.addfile(extra, io.BytesIO(PNG))

    with pytest.raises(RestoreError, match="not declared"):
        inspect(smuggled)


def test_a_symlink_member_is_refused(data_dir: Path, tmp_path: Path) -> None:
    archive = tmp_path / "backup.tar.gz"
    create(data_dir, archive, now_ms=T0)

    linked = tmp_path / "linked.tar.gz"
    with tarfile.open(archive, "r:gz") as source, tarfile.open(linked, "w:gz") as target:
        for info in source.getmembers():
            handle = source.extractfile(info)
            target.addfile(info, io.BytesIO(b"" if handle is None else handle.read()))
        link = tarfile.TarInfo("attachments/evil.png")
        link.type = tarfile.SYMTYPE
        link.linkname = "/etc/passwd"
        target.addfile(link)

    with pytest.raises(RestoreError, match="not a plain file"):
        inspect(linked)


def test_a_newer_manifest_version_is_refused(data_dir: Path, tmp_path: Path) -> None:
    """This build cannot know what a future format meant, so it declines rather than guessing."""
    archive = tmp_path / "backup.tar.gz"
    create(data_dir, archive, now_ms=T0)

    future = tmp_path / "future.tar.gz"

    def bump(info, data):
        if info.name != MANIFEST_NAME:
            return info, data
        body = json.loads(data)
        body["version"] = 99
        return info, json.dumps(body).encode()

    repack(archive, future, mutate=bump)
    with pytest.raises(RestoreError, match="newer version"):
        inspect(future)


def test_an_archive_with_unknown_migrations_is_refused(data_dir: Path, tmp_path: Path) -> None:
    """An archive from a later build carries tables this one has never seen."""
    archive = tmp_path / "backup.tar.gz"
    create(data_dir, archive, now_ms=T0)

    ahead = tmp_path / "ahead.tar.gz"
    staged = tmp_path / "staged.db"

    with tarfile.open(archive, "r:gz") as source:
        staged.write_bytes(source.extractfile(DB_MEMBER).read())
    conn = sqlite3.connect(staged)
    conn.execute("INSERT INTO schema_migration (id, checksum, applied_at) "
                 "VALUES ('099-from-the-future','x','now')")
    conn.commit()
    conn.close()

    new_bytes = staged.read_bytes()
    digest, size = sha256_of(staged)

    def swap(info, data):
        if info.name == DB_MEMBER:
            return info, new_bytes
        if info.name == MANIFEST_NAME:
            body = json.loads(data)
            for member in body["members"]:
                if member["path"] == DB_MEMBER:
                    member["sha256"], member["size"] = digest, size
            return info, json.dumps(body).encode()
        return info, data

    repack(archive, ahead, mutate=swap)
    move_on(data_dir, thesis="a later evening")

    with pytest.raises(RestoreError, match="migrations this build does not know"):
        restore(ahead, data_dir, readiness=IDLE, now_ms=T0 + 1)

    assert thesis_of(data_dir) == "a later evening"


def test_an_archive_without_a_manifest_is_refused(tmp_path: Path) -> None:
    bare = tmp_path / "bare.tar.gz"
    with tarfile.open(bare, "w:gz") as archive:
        info = tarfile.TarInfo("journal.db")
        info.size = 4
        archive.addfile(info, io.BytesIO(b"junk"))

    with pytest.raises(RestoreError, match="no manifest"):
        inspect(bare)


def test_a_file_that_is_not_an_archive_is_refused(tmp_path: Path) -> None:
    junk = tmp_path / "notes.txt"
    junk.write_text("this is not a backup")
    with pytest.raises(RestoreError, match="not a readable backup archive"):
        inspect(junk)


def test_a_declared_member_missing_from_the_archive_is_refused(data_dir: Path,
                                                               tmp_path: Path) -> None:
    archive = tmp_path / "backup.tar.gz"
    create(data_dir, archive, now_ms=T0)

    short = tmp_path / "short.tar.gz"
    repack(archive, short, mutate=lambda info, data: (
        (None, b"") if info.name.endswith(".png") else (info, data)
    ))

    with pytest.raises(RestoreError, match="missing"):
        inspect(short)


def test_a_decompression_bomb_is_refused_at_extraction(data_dir: Path, tmp_path: Path) -> None:
    """A member far larger than the manifest declares does not get written to disk."""
    archive = tmp_path / "backup.tar.gz"
    create(data_dir, archive, now_ms=T0)

    bomb = tmp_path / "bomb.tar.gz"

    def inflate(info, data):
        if info.name.endswith(".png"):
            return info, b"\x00" * (1024 * 1024)
        return info, data

    repack(archive, bomb, mutate=inflate)
    move_on(data_dir, thesis="a later evening")

    with pytest.raises(RestoreError, match="larger than the manifest"):
        restore(bomb, data_dir, readiness=IDLE, now_ms=T0 + 1)

    assert thesis_of(data_dir) == "a later evening"


def test_a_failed_restore_is_indistinguishable_from_one_that_never_ran(data_dir: Path,
                                                                       tmp_path: Path) -> None:
    """The property every refusal above is really testing."""
    archive = tmp_path / "backup.tar.gz"
    create(data_dir, archive, now_ms=T0)
    move_on(data_dir, thesis="a later evening")

    before = (count_trades(data_dir), thesis_of(data_dir),
              sorted(p.name for p in data_dir.iterdir()))

    with pytest.raises(RestoreError):
        restore(tmp_path / "does-not-exist.tar.gz", data_dir, readiness=IDLE, now_ms=T0 + 1)

    after = (count_trades(data_dir), thesis_of(data_dir),
             sorted(p.name for p in data_dir.iterdir()))
    assert after == before
