"""Grading: score a fire against its playbook.

Two properties define this module:

* **It never rejects.** Grading scores; the gateway's risk rules are the only
  thing that refuses a fire. A `scope: "playbook"` rule has no `reason` and no
  `applies_to`, so it structurally cannot.
* **It is a pure function over context.** No LLM grades a trade. The same
  context always produces the same grade, which is what makes a month of them
  comparable.

An unanswered manual rule is **unknown**, not failed: it drops out of
``required_total`` entirely, so skipping the post-trade checklist costs the
player nothing.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Literal

from .playbook import UNPLANNED, Playbook, PlaybookRule
from .rules import BY_CODE, Outcome

Phase = Literal["arm", "fire", "settled"]


@dataclass
class GradeContext:
    """Everything a graded rule may look at.

    Deliberately flat and optional: a rule whose input is missing returns
    `unknown` rather than passing, so a half-wired context understates the
    grade instead of flattering it.
    """

    now_ms: int
    side: str | None = None
    sym: str | None = None
    lots: float | None = None
    price: float | None = None
    ema: float | None = None
    atr: float | None = None
    spread: float | None = None
    open_positions: int = 0
    has_stop: bool = False
    minutes_to_news: float | None = None
    session_open: bool = True
    #: Answers to manual rules, by code. Absent means unanswered.
    answers: dict[str, bool] = field(default_factory=dict)
    #: Params of the rule currently being evaluated, injected by `grade`.
    _params: dict[str, Any] = field(default_factory=dict)

    def param(self, name: str, default: Any = None) -> Any:
        return self._params.get(name, default)

    def answer(self, code: str) -> bool | None:
        return self.answers.get(code)


@dataclass(frozen=True)
class RuleResult:
    code: str
    label: str
    required: bool
    kind: str
    ok: bool | None
    actual: str = ""
    expected: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "ruleId": self.code,
            "label": self.label,
            "required": self.required,
            "kind": self.kind,
            "passed": self.ok,
            "actual": self.actual,
            "expected": self.expected,
        }


@dataclass(frozen=True)
class Grade:
    playbook_slug: str
    playbook_name: str
    phase: Phase
    results: tuple[RuleResult, ...]
    required_pass: int
    required_total: int
    clean: bool
    unknown: int

    def as_message(self, cid: str, playbook_id: str | None = None) -> dict[str, Any]:
        return {
            "cid": cid,
            "playbookId": playbook_id or self.playbook_slug,
            "required_pass": self.required_pass,
            "required_total": self.required_total,
            "clean": self.clean,
            "results": [
                {"ruleId": r.code, "required": r.required, "passed": r.ok,
                 "note": r.actual or None}
                for r in self.results
            ],
        }

    def results_json(self) -> str:
        return json.dumps([r.as_dict() for r in self.results], separators=(",", ":"))

    @property
    def headline(self) -> str:
        """What the ARM overlay shows: `4/5 rules OK`."""
        return f"{self.required_pass}/{self.required_total} rules OK"


def _evaluate(rule: PlaybookRule, ctx: GradeContext) -> RuleResult:
    entry = BY_CODE.get(rule.code)
    if entry is None:
        # A playbook referencing a code the registry no longer has. Unknown is
        # the honest answer; guessing would silently change a historical grade.
        return RuleResult(rule.code, rule.label, rule.required, rule.kind, None,
                          expected="rule no longer defined")

    ctx._params = rule.params
    try:
        outcome: Outcome = entry.evaluate(ctx)
    except Exception as exc:  # a broken rule must not lose the whole grade
        outcome = Outcome(ok=None, actual=f"error: {exc}"[:120])
    finally:
        ctx._params = {}

    return RuleResult(
        code=rule.code,
        label=rule.label,
        required=rule.required,
        kind=rule.kind,
        ok=outcome.ok,
        actual=outcome.actual,
        expected=outcome.expected,
    )


def grade(playbook: Playbook | None, ctx: GradeContext, phase: Phase = "fire") -> Grade:
    """Score one fire. Never raises, never rejects."""
    book = playbook or UNPLANNED
    results = tuple(_evaluate(rule, ctx) for rule in book.rules)

    required = [r for r in results if r.required]
    known = [r for r in required if r.ok is not None]
    passed = [r for r in known if r.ok]

    return Grade(
        playbook_slug=book.slug,
        playbook_name=book.name,
        phase=phase,
        results=results,
        required_pass=len(passed),
        # Unknown rules drop out of the denominator, so a skipped checklist is
        # neither pass nor fail and never costs the player anything.
        required_total=len(known),
        clean=bool(known) and len(passed) == len(known),
        unknown=len([r for r in results if r.ok is None]),
    )


def unanswered_manual_codes(playbook: Playbook | None, answers: dict[str, bool]) -> list[str]:
    """What the post-trade checklist should still ask. Capped by the caller to
    the three taps the plan allows."""
    book = playbook or UNPLANNED
    return [
        r.code for r in book.rules
        if r.kind == "manual" and r.code not in answers
    ]
