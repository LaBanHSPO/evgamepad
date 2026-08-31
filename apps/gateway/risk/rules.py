"""The enforced risk rule set — exported, not private.

Phase 6 scores adherence with *these* rules, and phase 7 moves them into
`method/rules.py` while `risk/rules.py` keeps importing them. Two definitions of "was that
trade within the rules" would let the score disagree with the gate that actually fired.

The asymmetry is the whole point: every rule here gates **opens**. A close and a panic are exits,
and an exit is never blocked — not by the session window, not by the daily loss, not by tilt
(phase 9), not by a dead-man heartbeat.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Literal

Scope = Literal["risk", "playbook"]

# Reserved here so phase 9 adds a cooldown without inventing a new wire reason later.
REJECT_COOLDOWN = "cooldown"


@dataclass(frozen=True)
class OpenContext:
    """Everything the open gates read. Built by the socket, never by a rule."""

    now_ms: int
    symbol: str
    lots: float
    clutch: bool
    session_open: bool
    session_label: str
    allowed_symbols: frozenset[str]
    positions_open: int
    max_positions: int
    max_lots: float
    day_loss_usd: float
    max_day_loss_usd: float
    seconds_since_last_order: float
    min_seconds_between_orders: float
    heartbeat_age_s: float
    heartbeat_dead_s: float


@dataclass(frozen=True)
class Rule:
    """One gate. `scope='risk'` rejects; `scope='playbook'` may only ever be graded."""

    id: str
    scope: Scope
    reason: str
    describe: str
    passes: Callable[[OpenContext], bool]


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


OPEN_RULES: tuple[Rule, ...] = (
    Rule(
        id="clutch",
        scope="risk",
        reason="no_clutch",
        describe="the intent itself must carry the clutch",
        passes=lambda c: c.clutch,
    ),
    Rule(
        id="dead_man",
        scope="risk",
        reason="dead_man",
        describe="a stale heartbeat locks opens; it never locks an exit",
        passes=lambda c: c.heartbeat_age_s < c.heartbeat_dead_s,
    ),
    Rule(
        id="session_window",
        scope="risk",
        reason="session_closed",
        describe="opens only inside the evening window, in the configured zone",
        passes=lambda c: c.session_open,
    ),
    Rule(
        id="symbol_allowlist",
        scope="risk",
        reason="symbol_not_allowed",
        describe="only configured symbols may be traded",
        passes=lambda c: c.symbol in c.allowed_symbols,
    ),
    Rule(
        id="max_positions",
        scope="risk",
        reason="max_positions",
        describe="never more concurrent positions than configured",
        passes=lambda c: c.positions_open < c.max_positions,
    ),
    Rule(
        id="max_lots",
        scope="risk",
        reason="max_lots",
        describe="per-symbol size cap",
        passes=lambda c: c.lots <= c.max_lots,
    ),
    Rule(
        id="daily_loss",
        scope="risk",
        reason="daily_loss",
        describe="past the daily loss the evening is close-only",
        passes=lambda c: c.day_loss_usd < c.max_day_loss_usd,
    ),
    Rule(
        id="order_rate",
        scope="risk",
        reason="rate_limited",
        describe="a minimum gap between orders, so one twitch is not two fires",
        passes=lambda c: c.seconds_since_last_order >= c.min_seconds_between_orders,
    ),
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
        passed = bool(rule.passes(ctx))
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
