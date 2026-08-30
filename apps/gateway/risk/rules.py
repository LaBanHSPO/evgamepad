"""Enforcement: the ``scope: "risk"`` subset of the registry, and the decision.

The rules themselves live in ``method/rules.py`` as of phase 7. This module is
the enforcement half -- it turns a failing rule into a rejected intent. It
imports; it does not redefine. Phase 2's ``test_rules.py`` passes unchanged,
which is what makes the extraction behaviour-preserving rather than a rewrite
that happens to look similar.

Nothing here can reach a playbook rule: ``enforced_rules`` filters on scope, so
a graded rule cannot refuse a fire even by mistake.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ..method.rules import (
    BROKER_CHANGING,
    OPEN,
    OPEN_ONLY,
    REGISTRY,
    Rule,
    playbook_rules_never_reject,
    safety_exits_are_ungated,
)
from ..protocol.catalog import RejectReason

__all__ = [
    "BROKER_CHANGING",
    "Decision",
    "OPEN",
    "OPEN_ONLY",
    "RULES",
    "RULES_BY_ID",
    "RiskContext",
    "Rule",
    "enforced_rules",
    "evaluate",
    "open_only_reasons",
    "playbook_rules_never_reject",
    "safety_exits_are_ungated",
]

#: Phase 2's name for the enforced set. Still the enforced set.
RULES: tuple[Rule, ...] = tuple(r for r in REGISTRY if r.scope == "risk")
RULES_BY_ID: dict[str, Rule] = {r.id: r for r in RULES}


@dataclass
class RiskContext:
    """Everything an enforced rule may look at. No rule reaches outside this."""

    now_ms: int
    intent_type: str
    session_open: bool = True
    locked: bool = False
    clutch: bool = False
    armed_at: int | None = None
    arm_max_age_ms: int = 5_000
    open_positions: int = 0
    max_positions: int = 1
    day_loss_usd: float = 0.0
    max_daily_loss_usd: float = 200.0
    last_order_ms: int | None = None
    min_seconds_between_orders: float = 2.0
    last_client_ms: int | None = None
    heartbeat_dead_s: float = 3.0
    cid_seen: bool = False
    symbol_known: bool = True
    lots_ok: bool = True
    lots_reason: RejectReason = "max_lots"
    spread: float | None = None
    max_spread: float | None = None
    #: Phase 9 sets this. Reserved in phase 1 so adding tilt friction later is
    #: not a protocol change.
    cooldown_until_ms: int | None = None


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: RejectReason | None = None
    rule_id: str | None = None
    detail: str = ""


Consequence = Literal["risk", "playbook"]


def enforced_rules(intent_type: str) -> tuple[Rule, ...]:
    return tuple(r for r in RULES if r.applies(intent_type))


def evaluate(ctx: RiskContext) -> Decision:
    """First failing rule wins, in registry order. Deterministic on purpose --
    the player should get the same reason for the same situation every time."""
    for rule in enforced_rules(ctx.intent_type):
        if rule.check is not None and not rule.check(ctx):
            return Decision(
                allowed=False,
                reason=rule.reason,
                rule_id=rule.id,
                detail=rule.detail(ctx),
            )
    return Decision(allowed=True)


def open_only_reasons() -> frozenset[RejectReason]:
    """Reject reasons that must never be reachable by a close or a panic."""
    return frozenset(
        r.reason for r in RULES if r.applies_to == OPEN_ONLY and r.reason is not None
    )
