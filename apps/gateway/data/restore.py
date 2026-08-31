"""Restore: validate everything, stage everything, and only then swap.

The failure this module exists to prevent is a restore that half-succeeds. Every check runs
*before* current data is touched:

1. **The gateway must be idle** — session locked, no position open, no background job running.
   Restoring underneath a live socket would swap the database out from under an in-flight fill.
2. **The archive must be structurally sound** — a real manifest, a supported version, and every
   member path safe. Absolute paths, `..`, symlinks, device files, duplicate members and members
   the manifest never declared are all refused before a single byte is extracted.
3. **Every checksum must match**, verified after extraction into a staging directory and before
   anything is moved.
4. **The schema must be compatible** — the archive may be older (it gets migrated forward) but
   never newer, because this build cannot know what a future migration meant.

Only then: the current data is moved aside as a rollback snapshot, the staged copy is swapped in,
the row counts are verified against the manifest, and the rollback is removed. If the verification
fails, the rollback goes back and the restore reports failure with the original data intact.
"""

from __future__ import annotations

import shutil
import sqlite3
import tarfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .backup import DB_MEMBER, MANIFEST_NAME, MANIFEST_VERSION, Manifest, sha256_of

# Members that may appear at all. Anything else in the tar is refused, not skipped.
ALLOWED_ROOTS = (DB_MEMBER, "attachments/", "voice/")

# A gzip member that expands far beyond its declared size is a decompression bomb.
MAX_EXPANSION = 4


class RestoreError(RuntimeError):
    """A refused restore. Current data has not been touched."""


@dataclass(frozen=True)
class Readiness:
    """Whether the gateway is quiet enough to have its data replaced underneath it."""

    locked: bool
    positions_open: int
    jobs_running: int

    def check(self) -> None:
        if not self.locked:
            raise RestoreError("lock the session before restoring")
        if self.positions_open:
            raise RestoreError(f"{self.positions_open} position(s) still open")
        if self.jobs_running:
            raise RestoreError(f"{self.jobs_running} background job(s) still running")


def safe_member(name: str) -> bool:
    """Whether a tar member name may be extracted at all.

    Deliberately a whitelist of shapes rather than a blacklist of attacks: absolute paths, parent
    traversal, drive letters and backslashes are all simply *not* the shape of a name this archive
    writes.
    """
    if name == MANIFEST_NAME:
        return True
    if name.startswith("/") or name.startswith("\\") or ".." in Path(name).parts:
        return False
    if ":" in name or "\\" in name:
        return False
    return name == DB_MEMBER or any(name.startswith(root) for root in ALLOWED_ROOTS[1:])


def inspect(archive_path: Path) -> Manifest:
    """Read and structurally validate the archive without extracting anything.

    Every failure leaves as a `RestoreError` with a reason the player can act on. A missing file
    and a member that is not there are both ordinary answers to "is this a backup?", not crashes.
    """
    try:
        with tarfile.open(archive_path, "r:gz") as archive:
            try:
                handle = archive.extractfile(MANIFEST_NAME)
            except KeyError as exc:
                raise RestoreError("this archive has no manifest") from exc
            if handle is None:
                raise RestoreError("this archive has no manifest")
            manifest = Manifest.parse(handle.read())

            if manifest.version > MANIFEST_VERSION:
                raise RestoreError(
                    f"this archive was written by a newer version (manifest v{manifest.version})"
                )
            if manifest.app != "evgamepad":
                raise RestoreError("this archive was not written by this application")

            declared = {member.path for member in manifest.members}
            seen: set[str] = set()
            for info in archive.getmembers():
                if info.name == MANIFEST_NAME:
                    continue
                if not info.isfile():
                    # Directories, symlinks, hard links and device nodes have no business here.
                    raise RestoreError(f"`{info.name}` is not a plain file")
                if not safe_member(info.name):
                    raise RestoreError(f"`{info.name}` is not a path this archive may contain")
                if info.name in seen:
                    raise RestoreError(f"`{info.name}` appears twice")
                if info.name not in declared:
                    raise RestoreError(f"`{info.name}` is not declared in the manifest")
                seen.add(info.name)

            missing = declared - seen
            if missing:
                raise RestoreError(f"the archive is missing {len(missing)} declared file(s)")
            return manifest
    except FileNotFoundError as exc:
        raise RestoreError("there is no archive at that path") from exc
    except (tarfile.TarError, OSError, ValueError) as exc:
        raise RestoreError(f"this file is not a readable backup archive: {exc}") from exc


def _extract(archive_path: Path, manifest: Manifest, staging: Path) -> None:
    """Extract into staging, refusing a member that expands far beyond its declared size."""
    sizes = {member.path: member.size for member in manifest.members}
    with tarfile.open(archive_path, "r:gz") as archive:
        for info in archive.getmembers():
            if info.name == MANIFEST_NAME:
                continue
            declared = sizes.get(info.name, 0)
            if info.size > max(1024, declared * MAX_EXPANSION):
                raise RestoreError(f"`{info.name}` is far larger than the manifest declares")
            target = (staging / info.name).resolve()
            # Belt and braces: even after `safe_member`, nothing lands outside staging.
            if not str(target).startswith(str(staging.resolve())):
                raise RestoreError(f"`{info.name}` would land outside the staging directory")
            target.parent.mkdir(parents=True, exist_ok=True)
            source = archive.extractfile(info)
            if source is None:
                raise RestoreError(f"`{info.name}` could not be read")
            with target.open("wb") as out:
                shutil.copyfileobj(source, out)


def _verify_checksums(manifest: Manifest, staging: Path) -> None:
    for member in manifest.members:
        path = staging / member.path
        if not path.is_file():
            raise RestoreError(f"`{member.path}` did not extract")
        digest, size = sha256_of(path)
        if digest != member.sha256 or size != member.size:
            raise RestoreError(f"`{member.path}` failed its checksum")


def _schema_compatible(staged_db: Path, current_ids: list[str]) -> None:
    """The archive may be older; it may not be newer."""
    conn = sqlite3.connect(staged_db)
    try:
        archived = [row[0] for row in conn.execute(
            "SELECT id FROM schema_migration ORDER BY id"
        ).fetchall()]
    except sqlite3.Error as exc:
        raise RestoreError("the archived database has no migration ledger") from exc
    finally:
        conn.close()

    ahead = sorted(set(archived) - set(current_ids))
    if ahead:
        raise RestoreError(
            f"the archive has migrations this build does not know: {', '.join(ahead)}"
        )


def _counts(db_path: Path, tables: dict[str, int]) -> dict[str, int]:
    conn = sqlite3.connect(db_path)
    try:
        out: dict[str, int] = {}
        for table in tables:
            try:
                out[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            except sqlite3.Error:
                continue
        return out
    finally:
        conn.close()


def restore(
    archive_path: Path, data_dir: Path, *, readiness: Readiness,
    migrate: Any = None, now_ms: int | None = None,
) -> dict[str, Any]:
    """Replace the journal from an archive, or change nothing at all."""
    from db.migrate import migrate as run_migrations

    migrate = migrate or run_migrations
    stamp = now_ms if now_ms is not None else int(time.time() * 1000)
    readiness.check()

    manifest = inspect(archive_path)

    staging = data_dir / f".restore-{stamp}"
    rollback = data_dir / f".rollback-{stamp}"
    if staging.exists():
        shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir(parents=True, exist_ok=True)

    try:
        _extract(archive_path, manifest, staging)
        _verify_checksums(manifest, staging)

        staged_db = staging / DB_MEMBER
        current_ids = _current_schema(data_dir / "journal.db")
        _schema_compatible(staged_db, current_ids)

        # Migrated in staging, so an older archive arrives already forward-migrated and the swap
        # is the only moment anything visible changes.
        applied = migrate(staged_db)

        rollback.mkdir(parents=True, exist_ok=True)
        moved = _swap_in(data_dir, staging, rollback)

        verified = _counts(data_dir / "journal.db", manifest.counts)
        mismatched = {
            table: (manifest.counts[table], verified.get(table))
            for table in manifest.counts
            if verified.get(table) != manifest.counts[table]
        }
        if mismatched:
            _swap_back(data_dir, rollback, moved)
            raise RestoreError(
                f"row counts did not match after the swap ({len(mismatched)} table(s)); "
                "the previous data has been put back"
            )

        # Only now, with the counts verified, is the previous data thrown away.
        shutil.rmtree(rollback, ignore_errors=True)
        return {
            "ok": True,
            "restoredFrom": manifest.created_at,
            "migrationsApplied": list(applied),
            "counts": verified,
            "files": len(manifest.members),
        }
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        if rollback.exists():
            shutil.rmtree(rollback, ignore_errors=True)
        raise
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def _current_schema(db_path: Path) -> list[str]:
    """Migration ids this build knows — from the code, not from the current database.

    Read from disk so a fresh install with no database can still accept a restore.
    """
    from db.migrate import discover

    return [migration.id for migration in discover()]


def _swap_in(data_dir: Path, staging: Path, rollback: Path) -> list[str]:
    """Move current data aside and the staged copy into place. Records what moved."""
    moved: list[str] = []
    for name in (DB_MEMBER, "attachments", "voice"):
        current = data_dir / name
        staged = staging / name
        if current.exists():
            shutil.move(str(current), str(rollback / name))
            moved.append(name)
        if staged.exists():
            shutil.move(str(staged), str(current))
    return moved


def _swap_back(data_dir: Path, rollback: Path, moved: list[str]) -> None:
    """Put the previous data back. Runs only when the post-swap verification failed."""
    for name in moved:
        restored = rollback / name
        current = data_dir / name
        if current.exists():
            shutil.rmtree(current, ignore_errors=True) if current.is_dir() else current.unlink()
        if restored.exists():
            shutil.move(str(restored), str(current))
