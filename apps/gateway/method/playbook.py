"""Playbooks: a named way of trading, and the rules that grade it.

The player starts with a real book rather than an empty one. The seeds are
Volman's M5 setups, each pointing at codes in the registry -- so a seeded
playbook and a hand-written one are graded by exactly the same machinery.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from typing import Any

from .rules import BY_CODE

#: Graded when no playbook is selected: risk rules only, and it reads honestly
#: as "unplanned" on the deck rather than as a clean trade.
UNPLANNED_SLUG = "__unplanned__"


@dataclass(frozen=True)
class PlaybookRule:
    code: str
    label: str
    kind: str
    required: bool = True
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Playbook:
    slug: str
    name: str
    method: str
    narrative: str
    rules: tuple[PlaybookRule, ...]
    symbols: tuple[str, ...] = ()
    detector_tag: str | None = None
    id: int | None = None
    active: bool = True

    @property
    def required_rules(self) -> tuple[PlaybookRule, ...]:
        return tuple(r for r in self.rules if r.required)


def _rule(code: str, required: bool = True, **params: Any) -> PlaybookRule:
    entry = BY_CODE[code]
    return PlaybookRule(
        code=code, label=entry.label, kind=entry.kind, required=required, params=params
    )


#: Volman's M5 book. Five setups, each a playbook of its own, because grading a
#: break the same way as a pullback would say nothing useful about either.
SEEDS: tuple[Playbook, ...] = (
    Playbook(
        slug="volman-range-box",
        name="Range box",
        method="volman_m5",
        detector_tag="range_box",
        narrative=(
            "Price is boxed between a clear high and low on the M5. Take the edge "
            "back into the range, not the middle."
        ),
        symbols=("XAUUSD", "EURUSD", "GBPUSD", "USDJPY"),
        rules=(
            _rule("pb.near_ema", max_atr_from_ema=1.0),
            _rule("pb.spread_ok", max_spread_atr=0.15),
            _rule("pb.flat_before_entry"),
            _rule("pb.stop_defined"),
            _rule("pb.outside_news", blackout_minutes=15),
            _rule("pb.waited_for_test"),
            _rule("pb.setup_was_named", required=False),
        ),
    ),
    Playbook(
        slug="volman-break",
        name="Range break",
        method="volman_m5",
        detector_tag="break",
        narrative=(
            "A decisive M5 close outside the box, in the direction of the EMA20. "
            "If it needs explaining, it is not a break."
        ),
        symbols=("XAUUSD", "EURUSD", "GBPUSD", "USDJPY"),
        rules=(
            _rule("pb.with_trend"),
            _rule("pb.near_ema", max_atr_from_ema=1.5),
            _rule("pb.spread_ok", max_spread_atr=0.15),
            _rule("pb.stop_defined"),
            _rule("pb.outside_news", blackout_minutes=15),
            _rule("pb.setup_was_named"),
            _rule("pb.exit_as_planned", required=False),
        ),
    ),
    Playbook(
        slug="volman-pullback-test",
        name="Pullback test",
        method="volman_m5",
        detector_tag="pullback_test",
        narrative=(
            "The break holds and price comes back to test it. This is the setup "
            "that rewards waiting, so waiting is a required rule."
        ),
        symbols=("XAUUSD", "EURUSD", "GBPUSD", "USDJPY"),
        rules=(
            _rule("pb.with_trend"),
            _rule("pb.near_ema", max_atr_from_ema=1.0),
            _rule("pb.waited_for_test"),
            _rule("pb.stop_defined"),
            _rule("pb.flat_before_entry"),
            _rule("pb.outside_news", blackout_minutes=15),
        ),
    ),
    Playbook(
        slug="volman-false-break",
        name="False break",
        method="volman_m5",
        detector_tag="false_break",
        narrative=(
            "The break fails and price snaps back inside. Trade the failure, "
            "against the break, back through the box."
        ),
        symbols=("XAUUSD", "EURUSD", "GBPUSD", "USDJPY"),
        rules=(
            _rule("pb.spread_ok", max_spread_atr=0.12),
            _rule("pb.flat_before_entry"),
            _rule("pb.stop_defined"),
            _rule("pb.outside_news", blackout_minutes=15),
            _rule("pb.waited_for_test"),
            _rule("pb.exit_as_planned", required=False),
        ),
    ),
    Playbook(
        slug="volman-block-break",
        name="Block break",
        method="volman_m5",
        detector_tag="block_break",
        narrative=(
            "A tight consolidation block breaks with the trend. Small stop, so "
            "size is the thing most likely to go wrong."
        ),
        symbols=("XAUUSD", "EURUSD", "GBPUSD", "USDJPY"),
        rules=(
            _rule("pb.with_trend"),
            _rule("pb.near_ema", max_atr_from_ema=0.8),
            _rule("pb.size_at_plan", max_lots=0.10),
            _rule("pb.stop_defined"),
            _rule("pb.spread_ok", max_spread_atr=0.12),
            _rule("pb.setup_was_named"),
        ),
    ),
)

#: The implicit book. No playbook rules, so a fire without a plan is graded on
#: risk alone and shows up as unplanned rather than as clean.
UNPLANNED = Playbook(
    slug=UNPLANNED_SLUG,
    name="Unplanned",
    method="custom",
    narrative="No playbook was selected for this fire.",
    rules=(),
    active=False,
)


class PlaybookStore:
    """Reads and writes playbooks. Seeding is idempotent."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def seed(self, now_ms: int, books: tuple[Playbook, ...] = SEEDS) -> int:
        """Install the seeds once. A player's edits to a seeded book survive a
        restart, so this never overwrites an existing slug."""
        installed = 0
        for book in books:
            row = self.conn.execute(
                "SELECT id FROM playbook WHERE slug = ?", (book.slug,)
            ).fetchone()
            if row:
                continue
            cur = self.conn.execute(
                "INSERT INTO playbook (slug, name, method, symbols_json, "
                "detector_tag, narrative, active, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, 1, ?)",
                (book.slug, book.name, book.method, json.dumps(list(book.symbols)),
                 book.detector_tag, book.narrative, now_ms),
            )
            playbook_id = int(cur.lastrowid)
            for ord_, rule in enumerate(book.rules):
                self.conn.execute(
                    "INSERT INTO playbook_rule (playbook_id, ord, kind, code, "
                    "params_json, label, required) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (playbook_id, ord_, rule.kind, rule.code,
                     json.dumps(rule.params), rule.label, int(rule.required)),
                )
            installed += 1
        return installed

    def _hydrate(self, row: sqlite3.Row) -> Playbook:
        rules = self.conn.execute(
            "SELECT * FROM playbook_rule WHERE playbook_id = ? ORDER BY ord",
            (row["id"],),
        ).fetchall()
        return Playbook(
            id=row["id"],
            slug=row["slug"],
            name=row["name"],
            method=row["method"],
            narrative=row["narrative"],
            symbols=tuple(json.loads(row["symbols_json"])),
            detector_tag=row["detector_tag"],
            active=bool(row["active"]) and row["retired_at"] is None,
            rules=tuple(
                PlaybookRule(
                    code=r["code"], label=r["label"], kind=r["kind"],
                    required=bool(r["required"]), params=json.loads(r["params_json"]),
                )
                for r in rules
            ),
        )

    def get(self, slug: str) -> Playbook | None:
        if slug == UNPLANNED_SLUG:
            return UNPLANNED
        row = self.conn.execute("SELECT * FROM playbook WHERE slug = ?", (slug,)).fetchone()
        return self._hydrate(row) if row else None

    def by_id(self, playbook_id: int) -> Playbook | None:
        """Resolves retired playbooks too -- a historical grade must keep
        naming the book it was graded against."""
        row = self.conn.execute(
            "SELECT * FROM playbook WHERE id = ?", (playbook_id,)
        ).fetchone()
        return self._hydrate(row) if row else None

    def list(self, include_retired: bool = False) -> list[Playbook]:
        sql = "SELECT * FROM playbook"
        if not include_retired:
            sql += " WHERE retired_at IS NULL AND active = 1"
        sql += " ORDER BY name"
        return [self._hydrate(r) for r in self.conn.execute(sql)]

    def retire(self, slug: str, now_ms: int) -> bool:
        cur = self.conn.execute(
            "UPDATE playbook SET retired_at = ? WHERE slug = ? AND retired_at IS NULL",
            (now_ms, slug),
        )
        return cur.rowcount > 0
