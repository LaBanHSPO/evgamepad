"""The rule registry. One definition, two consequences.

``scope: "risk"`` rules are **enforced** by ``risk/rules.py`` -- a failure
rejects the intent server-side. ``scope: "playbook"`` rules are **graded** and
can never reject anything; a test asserts that, because a journal that quietly
became a trade blocker is the failure this separation exists to prevent.

This module is where phase 2's risk rules moved to. ``risk/rules.py`` imports
them and its behaviour is unchanged -- ``test_rules.py`` is the regression gate
for that, and it passes without edits.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

from ..protocol.catalog import SAFETY_EXIT_TYPES, RejectReason

OPEN = "intent.open"
CLOSE = "intent.close"
MODIFY = "intent.modify"
PANIC = "intent.panic"

#: Gates that may only ever apply to opening risk. A close or a panic is a
#: safety exit: the player is reducing exposure, and standing between them and
#: that is the one failure this product refuses to have.
OPEN_ONLY = frozenset({OPEN})
BROKER_CHANGING = frozenset({OPEN, CLOSE, MODIFY, PANIC})

Scope = Literal["risk", "playbook"]
Kind = Literal["auto", "manual"]


@dataclass(frozen=True)
class Outcome:
    """One rule's verdict.

    ``ok=None`` is **unknown**, not failed: a manual rule the player skipped is
    neither pass nor fail and is excluded from the required count, so skipping
    never costs anything.
    """

    ok: bool | None
    actual: str = ""
    expected: str = ""

    @property
    def known(self) -> bool:
        return self.ok is not None


UNKNOWN = Outcome(ok=None)


@dataclass(frozen=True)
class Rule:
    code: str
    label: str
    scope: Scope
    kind: Kind = "auto"
    #: Grading. Every rule has one; risk rules wrap their enforcement check.
    evaluate: Callable[[Any], Outcome] = field(default=lambda ctx: UNKNOWN, repr=False)
    #: Enforcement. Empty for playbook rules, which never reject.
    applies_to: frozenset[str] = frozenset()
    reason: RejectReason | None = None
    check: Callable[[Any], bool] | None = field(default=None, repr=False)
    detail: Callable[[Any], str] = field(default=lambda ctx: "", compare=False, repr=False)

    # Phase 2 called these id / title / consequence. Aliased rather than
    # renamed so the extraction stays behaviour-preserving and phase 2's tests
    # keep passing unchanged.
    @property
    def id(self) -> str:
        return self.code

    @property
    def title(self) -> str:
        return self.label

    @property
    def consequence(self) -> Scope:
        return self.scope

    def applies(self, intent_type: str) -> bool:
        return intent_type in self.applies_to


# ---------------------------------------------------------------------------
# Risk rules -- enforced. Moved verbatim from phase 2's risk/rules.py.
# ---------------------------------------------------------------------------


def _dead_man_ok(ctx: Any) -> bool:
    if ctx.last_client_ms is None:
        return True
    return (ctx.now_ms - ctx.last_client_ms) <= ctx.heartbeat_dead_s * 1000


def _arm_fresh(ctx: Any) -> bool:
    if ctx.armed_at is None:
        return False
    age = ctx.now_ms - ctx.armed_at
    return 0 <= age <= ctx.arm_max_age_ms


def _spread_ok(ctx: Any) -> bool:
    if ctx.max_spread is None or ctx.spread is None:
        return True
    return ctx.spread <= ctx.max_spread


def _rate_ok(ctx: Any) -> bool:
    if ctx.last_order_ms is None:
        return True
    return (ctx.now_ms - ctx.last_order_ms) / 1000.0 >= ctx.min_seconds_between_orders


def _cooldown_ok(ctx: Any) -> bool:
    return ctx.cooldown_until_ms is None or ctx.now_ms >= ctx.cooldown_until_ms


def _from_check(check: Callable[[Any], bool], expected: str) -> Callable[[Any], Outcome]:
    """Grade a risk rule with the same predicate that enforces it. One
    definition; the scope decides whether a failure rejects or only scores."""

    def evaluate(ctx: Any) -> Outcome:
        try:
            return Outcome(ok=bool(check(ctx)), expected=expected)
        except AttributeError:
            # Graded against a context that does not carry this rule's inputs.
            return UNKNOWN

    return evaluate


def _risk(
    code: str,
    label: str,
    applies_to: frozenset[str],
    reason: RejectReason,
    check: Callable[[Any], bool],
    expected: str,
    detail: Callable[[Any], str] = lambda ctx: "",
) -> Rule:
    return Rule(
        code=code, label=label, scope="risk", kind="auto",
        evaluate=_from_check(check, expected),
        applies_to=applies_to, reason=reason, check=check, detail=detail,
    )


RISK_RULES: tuple[Rule, ...] = (
    _risk("risk.clutch", "Nothing fires without the clutch held", BROKER_CHANGING,
          "no_clutch", lambda ctx: ctx.clutch is True, "clutch held"),
    _risk("risk.arm_fresh", "ARM must be recent and not from the future", BROKER_CHANGING,
          "stale_arm", _arm_fresh, "armed within 5s",
          lambda ctx: f"armedAt {ctx.armed_at} vs now {ctx.now_ms}"),
    _risk("risk.duplicate_cid", "One cid, one broker action", BROKER_CHANGING,
          "duplicate_cid", lambda ctx: not ctx.cid_seen, "cid unused"),
    _risk("risk.symbol_allowlist", "Only configured symbols", frozenset({OPEN}),
          "unknown_symbol", lambda ctx: ctx.symbol_known, "a configured symbol"),
    _risk("risk.session_window", "Opens only inside the evening window", OPEN_ONLY,
          "session_closed", lambda ctx: ctx.session_open, "inside the session"),
    _risk("risk.locked", "A locked session opens nothing", OPEN_ONLY,
          "locked", lambda ctx: not ctx.locked, "unlocked"),
    _risk("risk.dead_man", "Silence from the client locks opens", OPEN_ONLY,
          "dead_man", _dead_man_ok, "client alive",
          lambda ctx: f"last client frame {ctx.last_client_ms}"),
    _risk("risk.max_positions", "At most risk.max_positions open", OPEN_ONLY,
          "max_positions", lambda ctx: ctx.open_positions < ctx.max_positions,
          "under the position cap",
          lambda ctx: f"{ctx.open_positions}/{ctx.max_positions}"),
    _risk("risk.daily_loss", "Past the daily loss the evening is close-only", OPEN_ONLY,
          "max_daily_loss", lambda ctx: ctx.day_loss_usd < ctx.max_daily_loss_usd,
          "under the daily loss",
          lambda ctx: f"{ctx.day_loss_usd:.2f}/{ctx.max_daily_loss_usd:.2f} USD"),
    _risk("risk.lot_size", "Lots within the symbol's configured and broker limits",
          OPEN_ONLY, "max_lots", lambda ctx: ctx.lots_ok, "lot at or under cap"),
    _risk("risk.spread", "Spread within the symbol's max", OPEN_ONLY,
          "spread_too_wide", _spread_ok, "spread inside the cap",
          lambda ctx: f"{ctx.spread} > {ctx.max_spread}"),
    _risk("risk.order_rate", "Minimum gap between orders", OPEN_ONLY,
          "rate_limited", _rate_ok, "gap since the last order"),
    _risk("risk.cooldown", "Tilt cooldown (phase 9) blocks opens only", OPEN_ONLY,
          "cooldown", _cooldown_ok, "not in cooldown",
          lambda ctx: f"until {ctx.cooldown_until_ms}"),
)


# ---------------------------------------------------------------------------
# Playbook rules -- graded, never enforced.
# ---------------------------------------------------------------------------


def _num(value: float | None, digits: int = 5) -> str:
    return "—" if value is None else f"{value:.{digits}f}".rstrip("0").rstrip(".")


def _with_trend(ctx: Any) -> Outcome:
    if ctx.ema is None or ctx.price is None or ctx.side is None:
        return UNKNOWN
    ok = ctx.price > ctx.ema if ctx.side == "buy" else ctx.price < ctx.ema
    return Outcome(
        ok=ok,
        actual=f"price {_num(ctx.price)} vs EMA20 {_num(ctx.ema)}",
        expected="price on the trade's side of the EMA20",
    )


def _near_ema(ctx: Any) -> Outcome:
    """Volman's point: chasing a move already extended from the mean is where
    the bad fills live."""
    limit = ctx.param("max_atr_from_ema", 1.5)
    if ctx.ema is None or ctx.price is None or not ctx.atr:
        return UNKNOWN
    distance = abs(ctx.price - ctx.ema) / ctx.atr
    return Outcome(
        ok=distance <= limit,
        actual=f"{distance:.2f} ATR from EMA20",
        expected=f"within {limit} ATR",
    )


def _spread_within(ctx: Any) -> Outcome:
    limit = ctx.param("max_spread_atr", 0.15)
    if ctx.spread is None or not ctx.atr:
        return UNKNOWN
    ratio = ctx.spread / ctx.atr
    return Outcome(
        ok=ratio <= limit,
        actual=f"spread {ratio:.2f} ATR",
        expected=f"under {limit} ATR",
    )


def _flat_before_entry(ctx: Any) -> Outcome:
    return Outcome(
        ok=ctx.open_positions == 0,
        actual=f"{ctx.open_positions} open",
        expected="flat before a new setup",
    )


def _size_at_plan(ctx: Any) -> Outcome:
    planned = ctx.param("max_lots", None)
    if planned is None or ctx.lots is None:
        return UNKNOWN
    return Outcome(
        ok=ctx.lots <= planned,
        actual=f"{ctx.lots:.2f} lot",
        expected=f"at or under {planned:.2f}",
    )


def _stop_defined(ctx: Any) -> Outcome:
    return Outcome(
        ok=bool(ctx.has_stop),
        actual="stop set" if ctx.has_stop else "no stop at entry",
        expected="a stop at entry",
    )


def _outside_news(ctx: Any) -> Outcome:
    window = ctx.param("blackout_minutes", 15)
    if ctx.minutes_to_news is None:
        # No calendar yet (phase 4). Unknown, not a free pass -- a rule that
        # silently passes when its input is missing is worse than no rule.
        return UNKNOWN
    return Outcome(
        ok=abs(ctx.minutes_to_news) > window,
        actual=f"T{ctx.minutes_to_news:+.0f} min",
        expected=f"outside T±{window}",
    )


def _manual(code: str, label: str) -> Rule:
    """A rule only the player can answer, asked as a post-trade tap."""

    def evaluate(ctx: Any) -> Outcome:
        answer = ctx.answer(code)
        if answer is None:
            return UNKNOWN
        return Outcome(ok=answer, actual="yes" if answer else "no", expected="yes")

    return Rule(code=code, label=label, scope="playbook", kind="manual", evaluate=evaluate)


PLAYBOOK_RULES: tuple[Rule, ...] = (
    Rule(code="pb.with_trend", label="Trading with the M5 EMA20",
         scope="playbook", evaluate=_with_trend),
    Rule(code="pb.near_ema", label="Not extended from the EMA20",
         scope="playbook", evaluate=_near_ema),
    Rule(code="pb.spread_ok", label="Spread small against volatility",
         scope="playbook", evaluate=_spread_within),
    Rule(code="pb.flat_before_entry", label="Flat before taking the setup",
         scope="playbook", evaluate=_flat_before_entry),
    Rule(code="pb.size_at_plan", label="Size at or under the planned lot",
         scope="playbook", evaluate=_size_at_plan),
    Rule(code="pb.stop_defined", label="A stop was set at entry",
         scope="playbook", evaluate=_stop_defined),
    Rule(code="pb.outside_news", label="Outside the news blackout",
         scope="playbook", evaluate=_outside_news),
    _manual("pb.waited_for_test", "Waited for the test rather than chasing"),
    _manual("pb.setup_was_named", "Could name the setup before entering"),
    _manual("pb.exit_as_planned", "Exited where the plan said, not where fear said"),
)


REGISTRY: tuple[Rule, ...] = RISK_RULES + PLAYBOOK_RULES
BY_CODE: dict[str, Rule] = {r.code: r for r in REGISTRY}


def rules_for_scope(scope: Scope) -> tuple[Rule, ...]:
    return tuple(r for r in REGISTRY if r.scope == scope)


def playbook_rules_never_reject() -> bool:
    """The separation this module exists for, as an assertion.

    A playbook rule with an `applies_to` or a `reason` could reject an intent,
    which would turn the journal into a trade blocker.
    """
    return all(
        not r.applies_to and r.reason is None
        for r in REGISTRY
        if r.scope == "playbook"
    )


def safety_exits_are_ungated() -> bool:
    return all(
        not (rule.applies_to == OPEN_ONLY and t in rule.applies_to)
        for rule in REGISTRY
        for t in SAFETY_EXIT_TYPES
    )
