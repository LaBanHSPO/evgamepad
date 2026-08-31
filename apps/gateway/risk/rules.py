"""The enforced subset of the rule registry.

Phase 7 moved the rule *definitions* into `method/rules.py`. This module is now the thing that
decides what a failing rule **does**: it imports the `scope="risk"` subset and rejects an intent
when one fails. It holds no rule logic of its own — that was the point of the extraction, and
phase 2's tests passing unchanged is the proof it was behaviour-preserving.

The asymmetry that survives every phase: every rule here gates **opens**. A close and a panic are
exits, and an exit is never blocked — not by the session window, not by the daily loss, not by
tilt (phase 9), not by a dead-man heartbeat.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from method.rules import RuleContext, rules_for

Scope = Literal["risk", "playbook"]

# Reserved here so phase 9 adds a cooldown without inventing a new wire reason later.
REJECT_COOLDOWN = "cooldown"

# What the gate reads. The registry's context is a superset; the grading fields simply stay unset
# on the order path, where no chart data is needed to decide whether a fire is allowed.
OpenContext = RuleContext


@dataclass(frozen=True)
class Rule:
    """One enforced gate, projected from the registry entry it came from."""

    id: str
    scope: Scope
    reason: str
    describe: str

    def passes(self, ctx: OpenContext) -> bool:
        from method.rules import get

        return get(self.id).check(ctx).ok


@dataclass(frozen=True)
class RuleOutcome:
    id: str
    scope: Scope
    passed: bool
    reason: str | None


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str | None
    outcomes: tuple[RuleOutcome, ...] = field(default_factory=tuple)


# Built from the registry, never re-listed. Adding a risk rule there adds a gate here.
OPEN_RULES: tuple[Rule, ...] = tuple(
    Rule(id=entry.code, scope="risk", reason=entry.reason or entry.code, describe=entry.describe)
    for entry in rules_for("risk")
)

# Rejection reasons the socket may send. `cooldown` is unused until phase 9 but reserved now.
OPEN_REJECT_REASONS: frozenset[str] = frozenset(
    [rule.reason for rule in OPEN_RULES] + [REJECT_COOLDOWN]
)


def evaluate_open(ctx: OpenContext) -> Decision:
    """Run every open gate. The first failing rule names the rejection."""
    outcomes: list[RuleOutcome] = []
    reason: str | None = None
    for rule in OPEN_RULES:
        passed = rule.passes(ctx)
        outcomes.append(RuleOutcome(id=rule.id, scope=rule.scope, passed=passed,
                                    reason=None if passed else rule.reason))
        if not passed and reason is None and rule.scope == "risk":
            reason = rule.reason
    return Decision(allowed=reason is None, reason=reason, outcomes=tuple(outcomes))


def evaluate_exit() -> Decision:
    """A close or a panic. Always allowed — there is no gate, by design.

    Kept as a function rather than a constant so the exemption is a call site the tests can point
    at, and so a future phase cannot quietly add a condition to it without changing this file.
    """
    return Decision(allowed=True, reason=None, outcomes=())
