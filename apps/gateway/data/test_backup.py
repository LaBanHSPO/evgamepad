"""Backup, export, and delete — with the emphasis on what they refuse to include.

The archive is the thing most likely to be copied somewhere less careful than the VPS, so the
tests that matter most here are the ones proving what is *not* in it.
"""

from __future__ import annotations

import json
import re
import sqlite3
import tarfile
from pathlib import Path

import pytest

from data.backup import (
    DB_MEMBER,
    EXCLUDED,
    MANIFEST_NAME,
    MEDIA_DIRS,
    BackupError,
    Manifest,
    create,
    read_manifest,
    sha256_of,
    snapshot_db,
)
from data.delete import CONFIRMATION, HOLD_MS, Confirmation, DeleteRefused, delete_all, residue
from data.export import JSON_TABLES, TRADE_COLUMNS, journal_json, redactions, trades_csv
from db.migrate import connect, migrate

SESSION = "2026-08-31"
T0 = 1_788_000_000_000
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 40


@pytest.fixture()
def data_dir(tmp_path: Path) -> Path:
    """A data volume shaped like the real one, secrets and models included."""
    migrate(tmp_path / "journal.db")
    conn = connect(tmp_path / "journal.db")
    conn.execute(
        "INSERT INTO session_equity (session_id, timezone, opened_at, equity_open) "
        "VALUES (?,?,?,?)", (SESSION, "Asia/Ho_Chi_Minh", T0, 10_000.0),
    )
    conn.execute("INSERT INTO cid_reservation (cid, intent, symbol, state, created_at, updated_at) "
                 "VALUES ('c1','open','XAUUSD','acked',?,?)", (T0, T0))
    conn.execute(
        "INSERT INTO trade_plan (cid, session_id, symbol, side, lots, volume, r_usd, r_method, "
        "r_units, planned_sl, created_at) VALUES ('c1',?, 'XAUUSD','buy',0.01,100,20.0,'stop',"
        "100.0,2456.0,?)", (SESSION, T0),
    )
    conn.execute(
        "INSERT INTO trade_closed (cid, session_id, position_id, symbol, side, lots, volume, "
        "entry_price, exit_price, opened_at, closed_at, r_usd, r_multiple) "
        "VALUES ('c1',?,7,'XAUUSD','buy',0.01,100,2458.0,2461.0,?,?,20.0,1.2)",
        (SESSION, T0, T0 + 60_000),
    )
    conn.execute(
        "INSERT INTO daily_analysis (session_id, updated_at, thesis) VALUES (?,?,?)",
        (SESSION, T0, "a private thought about the range"),
    )
    conn.commit()
    conn.close()

    (tmp_path / "attachments").mkdir()
    (tmp_path / "attachments" / "01ABC.png").write_bytes(PNG)
    (tmp_path / "voice").mkdir()
    (tmp_path / "voice" / "01DEF.ogg").write_bytes(b"OggS" + b"\x00" * 20)

    # The two things that must never be archived.
    (tmp_path / "secure").mkdir()
    (tmp_path / "secure" / "ctrader-token.json").write_text('{"refresh_token":"super-secret"}')
    (tmp_path / "models").mkdir()
    (tmp_path / "models" / "ggml-tiny.en.bin").write_bytes(b"\x00" * 4096)
    return tmp_path


# -- the archive ------------------------------------------------------------------------


def test_the_archive_carries_the_database_and_the_media(data_dir: Path) -> None:
    manifest = create(data_dir, data_dir / "backup.tar.gz", now_ms=T0)

    paths = {member.path for member in manifest.members}
    assert DB_MEMBER in paths
    assert "attachments/01ABC.png" in paths
    assert "voice/01DEF.ogg" in paths
    assert manifest.counts["trade_closed"] == 1


def test_the_archive_excludes_the_token_and_the_models(data_dir: Path) -> None:
    """One is a secret and the other is replaceable. Neither belongs in a file you might email."""
    archive = data_dir / "backup.tar.gz"
    create(data_dir, archive, now_ms=T0)

    with tarfile.open(archive, "r:gz") as handle:
        names = handle.getnames()
        blob = b"".join(
            handle.extractfile(name).read() for name in names
            if handle.getmember(name).isfile()
        )

    for excluded in EXCLUDED:
        assert not any(name.startswith(excluded) for name in names), f"{excluded} was archived"
    assert b"super-secret" not in blob
    # The allowlist is what makes that true, not luck.
    assert MEDIA_DIRS == ("attachments", "voice")


def test_every_member_is_checksummed(data_dir: Path) -> None:
    archive = data_dir / "backup.tar.gz"
    manifest = create(data_dir, archive, now_ms=T0)

    assert manifest.members, "an archive with no members is not a backup"
    for member in manifest.members:
        assert len(member.sha256) == 64
        assert member.size > 0
    assert read_manifest(archive).as_json() == manifest.as_json()


def test_the_snapshot_is_consistent_rather_than_a_file_copy(data_dir: Path) -> None:
    """Copying a live SQLite file usually works, which is the worst property a backup can have."""
    source = data_dir / "journal.db"
    live = sqlite3.connect(source)
    try:
        # An open write transaction: a naive copy could catch the file mid-write.
        live.execute("BEGIN")
        live.execute("INSERT INTO user_setting (key, value, updated_at) VALUES ('a','1',1)")

        snapshot_db(source, data_dir / "snap.db")
        snapped = sqlite3.connect(data_dir / "snap.db")
        try:
            assert snapped.execute("SELECT COUNT(*) FROM trade_closed").fetchone()[0] == 1
        finally:
            snapped.close()
    finally:
        live.rollback()
        live.close()


def test_a_cap_leaves_no_partial_archive_behind(data_dir: Path) -> None:
    """A half-written backup that looks complete is how people lose a journal."""
    archive = data_dir / "backup.tar.gz"
    with pytest.raises(BackupError, match="cap"):
        create(data_dir, archive, now_ms=T0, max_bytes=64)

    assert not archive.exists()
    assert not archive.with_suffix(archive.suffix + ".partial").exists()
    assert not any(p.name.startswith(".backup") for p in data_dir.iterdir())


def test_backing_up_a_missing_database_says_so(tmp_path: Path) -> None:
    with pytest.raises(BackupError, match="no journal database"):
        create(tmp_path, tmp_path / "backup.tar.gz")


def test_the_manifest_round_trips(data_dir: Path) -> None:
    manifest = create(data_dir, data_dir / "backup.tar.gz", now_ms=T0)
    parsed = Manifest.parse(manifest.as_json().encode())
    assert parsed.created_at == T0
    assert [m.path for m in parsed.members] == [m.path for m in manifest.members]
    assert parsed.schema == manifest.schema


def test_a_symlink_out_of_the_volume_is_not_followed(data_dir: Path) -> None:
    outside = data_dir.parent / "elsewhere.txt"
    outside.write_text("not ours")
    (data_dir / "attachments" / "link.png").symlink_to(outside)

    manifest = create(data_dir, data_dir / "backup.tar.gz", now_ms=T0)
    assert "attachments/link.png" not in {m.path for m in manifest.members}


# -- exports ------------------------------------------------------------------------------


def test_the_csv_streams_a_header_then_rows(data_dir: Path) -> None:
    chunks = list(trades_csv(data_dir / "journal.db"))
    assert chunks[0].strip().split(",") == list(TRADE_COLUMNS)
    assert len(chunks) == 2  # header plus the one closed trade
    assert "c1" in chunks[1]


def test_the_csv_windows_by_close_time(data_dir: Path) -> None:
    assert len(list(trades_csv(data_dir / "journal.db", from_ms=T0 + 999_999))) == 1  # header only


def test_the_json_export_is_a_valid_document_with_the_journal_in_it(data_dir: Path) -> None:
    body = json.loads("".join(journal_json(data_dir / "journal.db")))
    assert body["format"] == "evgamepad-journal"
    assert body["tables"]["trade_closed"][0]["cid"] == "c1"
    # The player's own words are theirs to export.
    assert "private thought" in body["tables"]["daily_analysis"][0]["thesis"]


def test_no_export_can_carry_a_secret_or_a_path(data_dir: Path) -> None:
    """Built from an allowlist, so a column added later cannot silently join the file."""
    exported = "".join(trades_csv(data_dir / "journal.db")) + "".join(
        journal_json(data_dir / "journal.db")
    )
    lowered = exported.lower()
    for fragment in redactions():
        assert fragment not in lowered, f"`{fragment}` reached an export"
    assert str(data_dir).lower() not in lowered
    assert "super-secret" not in lowered


def test_the_export_allowlists_name_no_secret_column() -> None:
    columns = set(TRADE_COLUMNS) | {c for cols in JSON_TABLES.values() for c in cols}
    for fragment in redactions():
        assert not any(fragment in column for column in columns)


def module_code(name: str) -> str:
    """A module past its docstrings and comments.

    They name the forbidden things in order to forbid them, so a raw substring scan would fail on
    the very prose that documents the rule.
    """
    source = Path(__file__).with_name(name).read_text(encoding="utf-8")
    stripped = re.sub(r'"""[\s\S]*?"""', "", source)
    return re.sub(r"#.*", "", stripped).lower()


def test_there_is_no_import_path_anywhere_in_the_data_module() -> None:
    """MT5 and broker-history import are explicitly out of scope."""
    for name in ("export.py", "backup.py", "restore.py", "delete.py"):
        source = module_code(name)
        for word in ("mt5", "metatrader", "broker_history", "import_trades", "csv_import"):
            assert word not in source, f"{name} mentions {word}"


# -- delete ---------------------------------------------------------------------------------


def ready() -> Confirmation:
    return Confirmation(phrase=CONFIRMATION, held_ms=HOLD_MS, locked=True, positions_open=0)


def test_delete_refuses_during_a_live_session(data_dir: Path) -> None:
    for bad, message in (
        (Confirmation(CONFIRMATION, HOLD_MS, True, 1), "position"),
        (Confirmation(CONFIRMATION, HOLD_MS, False, 0), "lock"),
        (Confirmation("delete everything", HOLD_MS, True, 0), "exactly"),
        (Confirmation(CONFIRMATION, 100, True, 0), "hold"),
    ):
        with pytest.raises(DeleteRefused, match=message):
            delete_all(data_dir, confirmation=bad)

    # Nothing was touched by any of the refusals.
    assert residue(data_dir)["rows"]["trade_closed"] == 1


def test_delete_removes_every_journal_row_and_file(data_dir: Path) -> None:
    result = delete_all(data_dir, confirmation=ready(), now_ms=T0)
    assert result["ok"] is True
    assert result["rows"] > 0

    left = residue(data_dir)
    assert all(count == 0 for count in left["rows"].values()), left["rows"]
    assert all(count == 0 for count in left["files"].values())


def test_delete_leaves_one_content_free_audit_row(data_dir: Path) -> None:
    """A row that quoted a deleted note would mean the delete did not happen."""
    delete_all(data_dir, confirmation=ready(), now_ms=T0)

    conn = sqlite3.connect(data_dir / "journal.db")
    try:
        rows = conn.execute(
            "SELECT action, counts, note FROM data_operation"
        ).fetchall()
    finally:
        conn.close()

    assert len(rows) == 1
    action, counts, note = rows[0]
    assert action == "delete_all"
    assert set(json.loads(counts)) == {"rows", "files", "tables"}
    assert "private thought" not in f"{counts}{note}"


def test_delete_keeps_the_credentials_and_the_models(data_dir: Path) -> None:
    """Not journal content: one is replaceable, the other is how the app reaches the broker."""
    delete_all(data_dir, confirmation=ready(), now_ms=T0)

    assert (data_dir / "secure" / "ctrader-token.json").exists()
    assert (data_dir / "models" / "ggml-tiny.en.bin").exists()


def test_delete_reclaims_the_space_rather_than_leaving_the_pages(data_dir: Path) -> None:
    before = (data_dir / "journal.db").stat().st_size
    delete_all(data_dir, confirmation=ready(), now_ms=T0)
    assert (data_dir / "journal.db").stat().st_size <= before


def test_the_confirmation_phrase_is_case_sensitive() -> None:
    assert CONFIRMATION == "DELETE EVERYTHING"
    with pytest.raises(DeleteRefused):
        Confirmation("Delete Everything", HOLD_MS, True, 0).check()


def test_nothing_takes_a_hidden_copy_after_the_final_confirmation() -> None:
    """A recovery copy made after "delete" is not a safety net, it is a lie about the word."""
    body = module_code("delete.py")
    for word in ("create(", "backup(", "snapshot_db", "copytree", "copy2"):
        assert word not in body


def test_a_checksum_survives_the_round_trip(data_dir: Path) -> None:
    original = sha256_of(data_dir / "attachments" / "01ABC.png")
    manifest = create(data_dir, data_dir / "backup.tar.gz", now_ms=T0)
    member = next(m for m in manifest.members if m.path == "attachments/01ABC.png")
    assert (member.sha256, member.size) == original


def test_the_manifest_is_the_first_thing_in_the_archive(data_dir: Path) -> None:
    """So a truncated download fails validation rather than extracting half a journal."""
    archive = data_dir / "backup.tar.gz"
    create(data_dir, archive, now_ms=T0)
    with tarfile.open(archive, "r:gz") as handle:
        assert handle.getnames()[0] == MANIFEST_NAME
