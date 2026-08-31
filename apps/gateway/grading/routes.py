"""Playbook CRUD and the post-trade checklist, over plain HTTP.

Same origin, behind the token the socket already uses. Editing a playbook is not realtime and has
no business on the order socket.

Player prose (`narrative`, rule labels) is stored and returned verbatim. It is text, and the
client renders it as text — the API does not sanitise it into something else, because that would
quietly change what the player wrote.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from journal.writer import JournalWriter
from method.rules import REGISTRY, manual_codes, rules_for

from .grade import Playbook, PlaybookRule
from .seed import starter_playbooks


class PlaybookRuleRequest(BaseModel):
    """One rule of a playbook. `code` must name a registry entry."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(max_length=64)
    params: dict[str, Any] = Field(default_factory=dict)
    required: bool = True
    label: str | None = Field(default=None, max_length=120)
    ord: int = 0


class PlaybookRequest(BaseModel):
    """A playbook as the editor submits it."""

    model_config = ConfigDict(extra="forbid")

    id: str | None = Field(default=None, max_length=64)
    name: str = Field(max_length=120)
    slug: str = Field(max_length=64, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    method: str = Field(default="volman_m5", max_length=32)
    symbols: list[str] = Field(default_factory=list, max_length=16)
    detector_tag: str | None = Field(default=None, max_length=64)
    narrative: str | None = Field(default=None, max_length=2000)
    rules: list[PlaybookRuleRequest] = Field(default_factory=list, max_length=32)


class ChecklistRequest(BaseModel):
    """The 3-tap post-trade checklist. Only manual rules can be answered, and skipping is fine."""

    model_config = ConfigDict(extra="forbid")

    cid: str = Field(max_length=32)
    answers: dict[str, bool] = Field(default_factory=dict)


def to_domain(row: dict[str, Any]) -> Playbook:
    """A stored row becomes the immutable object grading works with."""
    return Playbook(
        id=row["id"],
        name=row["name"],
        slug=row["slug"],
        method=row["method"],
        symbols=tuple(row.get("symbols") or ()),
        detector_tag=row.get("detector_tag"),
        narrative=row.get("narrative"),
        active=bool(row.get("active", True)),
        retired_at=row.get("retired_at"),
        rules=tuple(
            PlaybookRule(
                code=r["code"],
                params=r.get("params") or {},
                required=bool(r.get("required", True)),
                label=r.get("label"),
                ord=r.get("ord", 0),
            )
            for r in row.get("rules", [])
        ),
    )


def unknown_codes(rules: list[PlaybookRuleRequest]) -> list[str]:
    """Codes that name nothing in the registry. Refused rather than silently never evaluated."""
    return [rule.code for rule in rules if rule.code not in REGISTRY]


class PlaybookRepository:
    """Reads and writes playbooks. Opens a connection per call; holds none between them."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def _writer(self) -> tuple[JournalWriter, sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return JournalWriter(conn), conn

    def seed_if_empty(self, *, ts_ms: int) -> int:
        """Give a new player a real book on night one. Never overwrites an edited one."""
        journal, conn = self._writer()
        try:
            existing = conn.execute("SELECT COUNT(*) FROM playbook").fetchone()[0]
            if existing:
                return 0
            for book in starter_playbooks():
                journal.upsert_playbook(
                    {
                        "id": book.id, "name": book.name, "slug": book.slug,
                        "method": book.method, "symbols": list(book.symbols),
                        "detector_tag": book.detector_tag, "narrative": book.narrative,
                        "active": True, "created_at": ts_ms,
                    },
                    [
                        {"ord": r.ord, "kind": r.rule.kind, "code": r.code, "params": r.params,
                         "label": r.label, "required": r.required}
                        for r in book.rules
                    ],
                )
            conn.commit()
            return len(starter_playbooks())
        finally:
            conn.close()

    def list(self, *, include_retired: bool = False) -> list[dict[str, Any]]:
        journal, conn = self._writer()
        try:
            return journal.playbooks(include_retired=include_retired)
        finally:
            conn.close()

    def get(self, playbook_id: str) -> Playbook | None:
        for row in self.list(include_retired=True):
            if row["id"] == playbook_id:
                return to_domain(row)
        return None

    def save(self, request: PlaybookRequest, *, ts_ms: int) -> dict[str, Any]:
        journal, conn = self._writer()
        try:
            playbook_id = request.id or f"pb-{request.slug}"
            journal.upsert_playbook(
                {
                    "id": playbook_id, "name": request.name, "slug": request.slug,
                    "method": request.method, "symbols": request.symbols,
                    "detector_tag": request.detector_tag, "narrative": request.narrative,
                    "active": True, "created_at": ts_ms,
                },
                [r.model_dump() | {"kind": REGISTRY[r.code].kind} for r in request.rules],
            )
            conn.commit()
            return next(b for b in journal.playbooks(include_retired=True)
                        if b["id"] == playbook_id)
        finally:
            conn.close()

    def retire(self, playbook_id: str, *, ts_ms: int) -> bool:
        journal, conn = self._writer()
        try:
            retired = journal.retire_playbook(playbook_id, ts_ms=ts_ms)
            conn.commit()
            return retired
        finally:
            conn.close()

    def save_grade(self, row: dict[str, Any]) -> None:
        journal, conn = self._writer()
        try:
            journal.write_grade(row)
            conn.commit()
        finally:
            conn.close()

    def grade_for(self, cid: str) -> dict[str, Any] | None:
        journal, conn = self._writer()
        try:
            return journal.grade_for(cid)
        finally:
            conn.close()


def registry_view() -> dict[str, Any]:
    """What the editor may offer. A rule the registry does not have cannot be authored."""
    return {
        "playbook": [
            {"code": r.code, "label": r.label, "kind": r.kind, "describe": r.describe}
            for r in rules_for("playbook")
        ],
        # Listed so the editor can explain what the gateway enforces, not so it can be edited.
        "riskEnforced": [
            {"code": r.code, "label": r.label, "describe": r.describe} for r in rules_for("risk")
        ],
        "manual": list(manual_codes()),
    }
