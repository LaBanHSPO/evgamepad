"""Grading: score a fire against the playbook that was active when it fired.

Pure evaluation over context. No model grades a trade, and grading never rejects one — the
registry's `scope` decides that, and this module only ever *reads* it.

Three details that matter more than they look:

* Grading is keyed on the **cid**, one fire, not on a closed position. An arm that was cancelled
  and an intent that was rejected are both gradeable, and phase 6's declined count depends on it.
* An **unknown** rule — no chart data yet, or a manual rule the player skipped — is neither a pass
  nor a fail. It leaves `required_total`, so skipping the checklist costs nothing.
* With no playbook selected the fire is graded against `__unplanned__`, which holds no rules at
  all. That reads honestly on the deck as "unplanned" rather than as a failure.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from method.rules import Rule, RuleContext, RuleResult, get

# The implicit playbook a fire lands on when the player selected none.
UNPLANNED_ID = "__unplanned__"
UNPLANNED_NAME = "Unplanned"


@dataclass(frozen=True)
class PlaybookRule:
    """One rule of a playbook: a registry code, its parameters, and whether it counts."""

    code: str
    params: dict[str, Any] = field(default_factory=dict)
    required: bool = True
    label: str | None = None
    ord: int = 0

    @property
    def rule(self) -> Rule:
        return get(self.code)


@dataclass(frozen=True)
class Playbook:
    """A named setup. `detector_tag` is what the phase 4 detectors must be showing."""

    id: str
    name: str
    slug: str
    rules: tuple[PlaybookRule, ...] = ()
    method: str = "volman_m5"
    symbols: tuple[str, ...] = ()
    detector_tag: str | None = None
    narrative: str | None = None
    active: bool = True
    retired_at: int | None = None

    def applies_to(self, symbol: str) -> bool:
        """An empty symbol list means the setup is not symbol-specific."""
        return not self.symbols or symbol.upper() in {s.upper() for s in self.symbols}


UNPLANNED = Playbook(id=UNPLANNED_ID, name=UNPLANNED_NAME, slug="unplanned", rules=())


@dataclass(frozen=True)
class RuleGrade:
    """One rule's verdict, in the shape the overlay and the deck both read."""

    code: str
    label: str
    kind: str
    required: bool
    ok: bool
    unknown: bool
    actual: str | None
    expected: str | None

    def as_row(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "label": self.label,
            "kind": self.kind,
            "required": self.required,
            "ok": self.ok,
            "unknown": self.unknown,
            "actual": self.actual,
            "expected": self.expected,
        }


@dataclass(frozen=True)
class Grade:
    """A fire's grade. `clean` means every *required, answered* rule passed."""

    cid: str
    playbook_id: str
    playbook_name: str
    stage: str
    evaluated_at: int
    results: tuple[RuleGrade, ...]
    required_pass: int
    required_total: int
    clean: bool

    @property
    def summary(self) -> str:
        """What the confirm overlay prints: `4/5 rules OK`."""
        if self.required_total == 0:
            return "no rules to check"
        return f"{self.required_pass}/{self.required_total} rules OK"

    def first_failure(self) -> RuleGrade | None:
        """The one line the overlay has room for beneath the summary."""
        for result in self.results:
            if result.required and not result.ok and not result.unknown:
                return result
        return None

    def payload(self) -> dict[str, Any]:
        """The frozen `grade` message shape from protocol v1."""
        return {
            "cid": self.cid,
            "playbookId": self.playbook_id,
            "required_pass": self.required_pass,
            "required_total": self.required_total,
            "clean": self.clean,
            "results": [r.as_row() for r in self.results],
        }

    def as_db_row(self) -> dict[str, Any]:
        return {
            "cid": self.cid,
            # The implicit book is not a row in `playbook`, so it is stored as null.
            "playbook_id": None if self.playbook_id == UNPLANNED_ID else self.playbook_id,
            "stage": self.stage,
            "evaluated_at": self.evaluated_at,
            "results": json.dumps([r.as_row() for r in self.results], sort_keys=True),
            "required_pass": self.required_pass,
            "required_total": self.required_total,
            "clean": int(self.clean),
        }


def _grade_one(entry: PlaybookRule, ctx: RuleContext) -> RuleGrade:
    rule = entry.rule
    result: RuleResult = rule.check(ctx, entry.params)
    return RuleGrade(
        code=rule.code,
        label=entry.label or rule.label,
        kind=rule.kind,
        required=entry.required,
        ok=result.ok,
        unknown=result.unknown,
        actual=result.actual,
        expected=result.expected,
    )


def grade_fire(
    *, cid: str, playbook: Playbook | None, ctx: RuleContext, stage: str = "arm"
) -> Grade:
    """Score one fire. Never raises for a missing playbook, and never rejects anything."""
    book = playbook or UNPLANNED
    results = tuple(_grade_one(entry, ctx) for entry in sorted(book.rules, key=lambda r: r.ord))

    # Unknown rules leave the denominator entirely — a skipped checklist is not a bad trade.
    answered = [r for r in results if r.required and not r.unknown]
    required_pass = sum(1 for r in answered if r.ok)
    required_total = len(answered)

    return Grade(
        cid=cid,
        playbook_id=book.id,
        playbook_name=book.name,
        stage=stage,
        evaluated_at=ctx.now_ms,
        results=results,
        required_pass=required_pass,
        required_total=required_total,
        clean=required_total > 0 and required_pass == required_total,
    )


def regrade_with_answers(grade: Grade, playbook: Playbook | None, ctx: RuleContext,
                         answers: dict[str, bool]) -> Grade:
    """Re-score after the post-trade checklist, with the player's manual answers folded in."""
    merged = RuleContext(**{**ctx.__dict__, "manual_answers": {**ctx.manual_answers, **answers}})
    return grade_fire(cid=grade.cid, playbook=playbook, ctx=merged, stage="fire")
