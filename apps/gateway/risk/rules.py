"""The enforced risk rules, as data.

Two things depend on this being a **list of named rules** rather than a pile of
``if`` statements:

1. Phase 6 scores adherence against the rules the gateway actually enforced,
   never a second copy of the same intent.
2. Phase 7 moves this registry to ``method/rules.py`` and has this module import
   it. That extraction must be behaviour-preserving, and ``test_rules.py`` is
   the regression gate for it.

``consequence`` is why one registry can hold both kinds: ``risk`` rules are
enforced and can refuse a fire; ``playbook`` rules are graded and can never
block one.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Literal

from ..protocol.catalog import SAFETY_EXIT_TYPES, RejectReason

OPEN = "intent.open"
CLOSE = "intent.close"
MODIFY = "intent.modify"
PANIC = "intent.panic"

#: Gates that may only ever apply to opening risk. A close or a panic is a
#: safety exit: the player is *reducing* exposure, and standing between them and
#: that is the one failure this product refuses to have.
OPEN_ONLY = frozenset({OPEN})
BROKER_CHANGING = frozenset({OPEN, CLOSE, MODIFY, PANIC})


@dataclass
class RiskContext:
    """Everything a rule may look at. No rule reaches outside this."""

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
class Rule:
    id: str
    title: str
    consequence: Literal["risk", "playbook"]
    applies_to: frozenset[str]
    reason: RejectReason
    check: Callable[[RiskContext], bool]
    detail: Callable[[RiskContext], str] = field(
        default=lambda ctx: "", compare=False, repr=False
    )

    def applies(self, intent_type: str) -> bool:
        return intent_type in self.applies_to


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: RejectReason | None = None
    rule_id: str | None = None
    detail: str = ""


def _dead_man_ok(ctx: RiskContext) -> bool:
    if ctx.last_client_ms is None:
        return True
    return (ctx.now_ms - ctx.last_client_ms) <= ctx.heartbeat_dead_s * 1000


def _arm_fresh(ctx: RiskContext) -> bool:
    if ctx.armed_at is None:
        return False
    age = ctx.now_ms - ctx.armed_at
    return 0 <= age <= ctx.arm_max_age_ms


def _spread_ok(ctx: RiskContext) -> bool:
    if ctx.max_spread is None or ctx.spread is None:
        return True
    return ctx.spread <= ctx.max_spread


def _rate_ok(ctx: RiskContext) -> bool:
    if ctx.last_order_ms is None:
        return True
    gap = (ctx.now_ms - ctx.last_order_ms) / 1000.0
    return gap >= ctx.min_seconds_between_orders


def _cooldown_ok(ctx: RiskContext) -> bool:
    return ctx.cooldown_until_ms is None or ctx.now_ms >= ctx.cooldown_until_ms


RULES: tuple[Rule, ...] = (
    Rule(
        id="risk.clutch",
        title="Nothing fires without the clutch held",
        consequence="risk",
        applies_to=BROKER_CHANGING,
        reason="no_clutch",
        check=lambda ctx: ctx.clutch is True,
    ),
    Rule(
        id="risk.arm_fresh",
        title="ARM must be recent and not from the future",
        consequence="risk",
        applies_to=BROKER_CHANGING,
        reason="stale_arm",
        check=_arm_fresh,
        detail=lambda ctx: f"armedAt {ctx.armed_at} vs now {ctx.now_ms}",
    ),
    Rule(
        id="risk.duplicate_cid",
        title="One cid, one broker action",
        consequence="risk",
        applies_to=BROKER_CHANGING,
        reason="duplicate_cid",
        check=lambda ctx: not ctx.cid_seen,
    ),
    Rule(
        id="risk.symbol_allowlist",
        title="Only configured symbols",
        consequence="risk",
        applies_to=frozenset({OPEN}),
        reason="unknown_symbol",
        check=lambda ctx: ctx.symbol_known,
    ),
    Rule(
        id="risk.session_window",
        title="Opens only inside the evening window",
        consequence="risk",
        applies_to=OPEN_ONLY,
        reason="session_closed",
        check=lambda ctx: ctx.session_open,
    ),
    Rule(
        id="risk.locked",
        title="A locked session opens nothing",
        consequence="risk",
        applies_to=OPEN_ONLY,
        reason="locked",
        check=lambda ctx: not ctx.locked,
    ),
    Rule(
        id="risk.dead_man",
        title="Silence from the client locks opens",
        consequence="risk",
        applies_to=OPEN_ONLY,
        reason="dead_man",
        check=_dead_man_ok,
        detail=lambda ctx: f"last client frame {ctx.last_client_ms}",
    ),
    Rule(
        id="risk.max_positions",
        title="At most risk.max_positions open",
        consequence="risk",
        applies_to=OPEN_ONLY,
        reason="max_positions",
        check=lambda ctx: ctx.open_positions < ctx.max_positions,
        detail=lambda ctx: f"{ctx.open_positions}/{ctx.max_positions}",
    ),
    Rule(
        id="risk.daily_loss",
        title="Past the daily loss the evening is close-only",
        consequence="risk",
        applies_to=OPEN_ONLY,
        reason="max_daily_loss",
        check=lambda ctx: ctx.day_loss_usd < ctx.max_daily_loss_usd,
        detail=lambda ctx: f"{ctx.day_loss_usd:.2f}/{ctx.max_daily_loss_usd:.2f} USD",
    ),
    Rule(
        id="risk.lot_size",
        title="Lots within the symbol's configured and broker limits",
        consequence="risk",
        applies_to=OPEN_ONLY,
        reason="max_lots",
        check=lambda ctx: ctx.lots_ok,
    ),
    Rule(
        id="risk.spread",
        title="Spread within the symbol's max",
        consequence="risk",
        applies_to=OPEN_ONLY,
        reason="spread_too_wide",
        check=_spread_ok,
        detail=lambda ctx: f"{ctx.spread} > {ctx.max_spread}",
    ),
    Rule(
        id="risk.order_rate",
        title="Minimum gap between orders",
        consequence="risk",
        applies_to=OPEN_ONLY,
        reason="rate_limited",
        check=_rate_ok,
    ),
    Rule(
        id="risk.cooldown",
        title="Tilt cooldown (phase 9) blocks opens only",
        consequence="risk",
        applies_to=OPEN_ONLY,
        reason="cooldown",
        check=_cooldown_ok,
        detail=lambda ctx: f"until {ctx.cooldown_until_ms}",
    ),
)

RULES_BY_ID: dict[str, Rule] = {r.id: r for r in RULES}


def enforced_rules(intent_type: str) -> tuple[Rule, ...]:
    return tuple(r for r in RULES if r.consequence == "risk" and r.applies(intent_type))


def evaluate(ctx: RiskContext) -> Decision:
    """First failing rule wins, in registry order. Deterministic on purpose --
    the player should get the same reason for the same situation every time."""
    for rule in enforced_rules(ctx.intent_type):
        if not rule.check(ctx):
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
        r.reason for r in RULES if r.consequence == "risk" and r.applies_to == OPEN_ONLY
    )


def safety_exits_are_ungated() -> bool:
    """Asserted by the test suite, and cheap enough to assert at boot too."""
    return all(
        not (rule.applies_to == OPEN_ONLY and t in rule.applies_to)
        for rule in RULES
        for t in SAFETY_EXIT_TYPES
    )
