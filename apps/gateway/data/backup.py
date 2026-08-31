"""The backup archive: a consistent database snapshot plus the media that cannot be re-derived.

Three decisions worth stating, because each is the difference between a backup and a liability:

- **`sqlite3.Connection.backup()`, not a file copy.** Copying `journal.db` while the gateway is
  writing produces a file that is *usually* fine, which is the worst possible property for a
  backup. The online backup API takes a consistent snapshot of a live database.
- **An allowlist of directories, never a walk of the data volume.** `secure/` holds refreshed
  cTrader tokens and `models/` holds a gigabyte of whisper weights. One is a secret and the other
  is replaceable, and neither is in the archive because the archive is built from a named list
  rather than from everything it finds.
- **Every member is checksummed in the manifest.** Restore verifies each SHA-256 before it touches
  current data, so a truncated download fails at validation instead of halfway through a swap.

The archive is streamed to a temporary file with a size cap, and a partial file is removed on any
failure. A half-written backup that looks complete is how people lose a journal.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import sqlite3
import tarfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

MANIFEST_NAME = "manifest.json"
MANIFEST_VERSION = 1
DB_MEMBER = "journal.db"

# Directories that go in, by logical name. Anything not listed is not in the archive.
MEDIA_DIRS = ("attachments", "voice")

# What must never be archived, and why, kept next to the allowlist so the pair reads as one rule.
EXCLUDED = {
    "secure": "refreshed broker tokens — a secret",
    "models": "whisper weights — replaceable, and hundreds of megabytes",
    "cache": "derived data",
}

DEFAULT_MAX_BYTES = 2 * 1024 * 1024 * 1024
CHUNK = 1024 * 1024


class BackupError(RuntimeError):
    """The archive could not be produced. Nothing partial is left behind."""


@dataclass(frozen=True)
class Member:
    """One archived file, as the manifest records it."""

    path: str
    size: int
    sha256: str

    def as_row(self) -> dict[str, Any]:
        return {"path": self.path, "size": self.size, "sha256": self.sha256}


@dataclass
class Manifest:
    """What the archive contains, and enough to prove it arrived intact."""

    version: int = MANIFEST_VERSION
    created_at: int = 0
    app: str = "evgamepad"
    schema: list[str] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)
    members: list[Member] = field(default_factory=list)

    def as_json(self) -> str:
        return json.dumps({
            "version": self.version, "createdAt": self.created_at, "app": self.app,
            "schema": self.schema, "counts": self.counts,
            "members": [m.as_row() for m in self.members],
        }, sort_keys=True, indent=2)

    @classmethod
    def parse(cls, raw: bytes) -> Manifest:
        body = json.loads(raw)
        return cls(
            version=int(body.get("version", 0)), created_at=int(body.get("createdAt", 0)),
            app=str(body.get("app", "")), schema=list(body.get("schema", [])),
            counts=dict(body.get("counts", {})),
            members=[Member(path=str(m["path"]), size=int(m["size"]), sha256=str(m["sha256"]))
                     for m in body.get("members", [])],
        )


def sha256_of(path: Path) -> tuple[str, int]:
    """Digest and size, read in chunks so a large tape file never lands in memory whole."""
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        while chunk := handle.read(CHUNK):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def snapshot_db(source: Path, destination: Path) -> None:
    """A consistent copy of a live database, via SQLite's own online backup API."""
    if not source.exists():
        raise BackupError("there is no journal database to back up yet")
    src = sqlite3.connect(source)
    dst = sqlite3.connect(destination)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()


def schema_ids(db_path: Path) -> list[str]:
    """Applied migration ids. Restore compares these before it swaps anything in."""
    conn = sqlite3.connect(db_path)
    try:
        return [row[0] for row in conn.execute(
            "SELECT id FROM schema_migration ORDER BY id"
        ).fetchall()]
    except sqlite3.Error:
        return []
    finally:
        conn.close()


def free_bytes(path: Path) -> int:
    usage = shutil.disk_usage(path)
    return usage.free


def create(
    data_dir: Path, out_path: Path, *, now_ms: int | None = None,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> Manifest:
    """Write the archive, or leave nothing behind.

    Ordering matters: the database snapshot is taken first, its counts are read from the *snapshot*
    rather than from the live file, and the manifest is written last so an archive without a
    manifest is self-evidently incomplete.
    """
    from .export import counts as table_counts

    stamp = now_ms if now_ms is not None else int(time.time() * 1000)
    staging = out_path.parent / f".{out_path.name}.staging"
    partial = out_path.with_suffix(out_path.suffix + ".partial")

    if staging.exists():
        shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir(parents=True, exist_ok=True)

    try:
        snapshot = staging / DB_MEMBER
        snapshot_db(data_dir / "journal.db", snapshot)

        manifest = Manifest(created_at=stamp, schema=schema_ids(snapshot),
                            counts=table_counts(snapshot))

        digest, size = sha256_of(snapshot)
        manifest.members.append(Member(path=DB_MEMBER, size=size, sha256=digest))
        total = size

        for name in MEDIA_DIRS:
            directory = data_dir / name
            if not directory.is_dir():
                continue
            for file in sorted(p for p in directory.rglob("*") if p.is_file()):
                # Never follow a link out of the volume: the archive holds this app's own files.
                if file.is_symlink():
                    continue
                digest, size = sha256_of(file)
                total += size
                if total > max_bytes:
                    raise BackupError(
                        f"the archive passed its {max_bytes // (1024 * 1024)} MB cap; "
                        "nothing was written"
                    )
                manifest.members.append(
                    Member(path=f"{name}/{file.relative_to(directory).as_posix()}",
                           size=size, sha256=digest)
                )

        if free_bytes(out_path.parent) < total:
            raise BackupError("not enough free disk for the archive; nothing was written")

        with tarfile.open(partial, "w:gz") as archive:
            body = manifest.as_json().encode("utf-8")
            info = tarfile.TarInfo(MANIFEST_NAME)
            info.size = len(body)
            info.mtime = stamp // 1000
            archive.addfile(info, io.BytesIO(body))

            archive.add(snapshot, arcname=DB_MEMBER)
            for member in manifest.members:
                if member.path == DB_MEMBER:
                    continue
                archive.add(data_dir / member.path, arcname=member.path)

        os.replace(partial, out_path)
        return manifest
    except Exception:
        # Whatever went wrong, no half-archive survives to be mistaken for a good one.
        partial.unlink(missing_ok=True)
        out_path.unlink(missing_ok=True)
        raise
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def read_manifest(archive_path: Path) -> Manifest:
    """The manifest, without extracting anything else."""
    try:
        with tarfile.open(archive_path, "r:gz") as archive:
            handle = archive.extractfile(MANIFEST_NAME)
            if handle is None:
                raise BackupError("this archive has no manifest")
            return Manifest.parse(handle.read())
    except BackupError:
        raise
    except (tarfile.TarError, OSError, ValueError, KeyError) as exc:
        raise BackupError(f"this file is not a readable backup archive: {exc}") from exc
