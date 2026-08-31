"""`GET|PUT /api/settings`, and the read-only identity beside it.

The account is a **chip, not a selector**. There is one configured cTrader demo account, its
credentials live in env, and this surface reports its shape without ever returning a value that
could authenticate as it. Adding a second account is not a missing feature; it is out of scope for
a product whose entire safety story is "one demo account, one set of caps".
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .schema import Setting, SettingsError, apply, build, clutch_hysteresis_holds, dumps, loads


@dataclass
class SettingsRepository:
    """Reads and writes the editable preferences, and nothing else."""

    db_path: Path
    server_symbols: Callable[[], set[str]]

    def __post_init__(self) -> None:
        self.defined: dict[str, Setting] = build(server_symbols=self.server_symbols)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def values(self) -> dict[str, Any]:
        """Stored values over defaults. A stored value the schema no longer knows is ignored."""
        conn = self._connect()
        try:
            rows = conn.execute("SELECT key, value FROM user_setting").fetchall()
        finally:
            conn.close()

        stored = {row["key"]: row["value"] for row in rows}
        return {
            key: loads(stored[key], setting.default) if key in stored else setting.default
            for key, setting in self.defined.items()
        }

    def payload(self, *, identity: dict[str, Any]) -> dict[str, Any]:
        return {
            "settings": self.values(),
            "schema": [
                {"key": key, "describe": setting.describe, "default": setting.default}
                for key, setting in self.defined.items()
            ],
            "symbols": sorted(self.server_symbols()),
            # What the account *is*, never anything that could act as it.
            "account": identity,
            # Named here so the UI can link rather than duplicate the two editors that already
            # exist. Two places to define a rule is one place too many.
            "elsewhere": [
                {"what": "Playbooks and their rules", "where": "/api/playbooks"},
                {"what": "Philosophy and principles", "where": "/api/journal/system"},
            ],
        }

    def put(self, incoming: dict[str, Any], ts_ms: int) -> dict[str, Any]:
        """Validate the whole batch, then write it. One bad key rejects all of it."""
        cleaned = apply(self.defined, incoming)
        # Checked against the merged result: sending only one half of the clutch pair must still be
        # judged against the half already stored.
        clutch_hysteresis_holds({**self.values(), **cleaned})

        conn = self._connect()
        try:
            conn.executemany(
                "INSERT INTO user_setting (key, value, updated_at) VALUES (?,?,?) "
                "ON CONFLICT (key) DO UPDATE SET value = excluded.value, "
                "updated_at = excluded.updated_at",
                [(key, dumps(value), ts_ms) for key, value in cleaned.items()],
            )
            conn.commit()
        finally:
            conn.close()
        return self.values()

    def reset(self, keys: list[str], ts_ms: int) -> dict[str, Any]:
        """Back to the shipped default. Deleting the row *is* the reset."""
        unknown = sorted(set(keys) - set(self.defined))
        if unknown:
            raise SettingsError(f"not an editable setting: {', '.join(unknown)}")
        conn = self._connect()
        try:
            conn.executemany("DELETE FROM user_setting WHERE key = ?", [(key,) for key in keys])
            conn.commit()
        finally:
            conn.close()
        return self.values()
