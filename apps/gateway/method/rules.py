"""The rule registry: one definition, two consequences.

Every rule in the product lives here exactly once. What differs is what happens when one fails:

* `scope="risk"` — the gateway **enforces** it. A failing risk rule rejects the intent.
* `scope="playbook"` — grading **scores** it. A failing playbook rule is recorded and shown, and
  the trade goes through anyway.

That asymmetry is the whole point. A player-authored playbook rule must never become a trade
blocker, or the journal quietly turns into a gate nobody agreed to. `risk/rules.py` imports only
the risk subset and cannot reach the rest; a test asserts a playbook rule can never reject.

Grading is a pure function over context. No model grades a trade.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

Scope = Literal["risk", "playbook"]

# `auto` evaluates from live context at ARM and again at FIRE. `manual` is answered by the player
# in the post-trade checklist, and skipping it costs nothing.
Kind = Literal["auto", "manual"]


@dataclass(frozen=True)
class RuleContext:
    """Everything any rule may read.

    A superset on purpose: the gate fields are always present, the grading fields are optional and
    default to `None` so a risk rule never has to care whether the chart was available.
    """

    # -- what the gate knows ---------------------------------------------------------
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

    # -- what grading adds, when it is available --------------------------------------
    setup_tag: str | None = None
    setup_side: str | None = None
    side: str | None = None
    price: float | None = None
    ema20: float | None = None
    atr: float | None = None
    spread: float | None = None
    spread_cap: float | None = None
    seconds_to_high_impact: float | None = None
    # Manual answers, keyed by rule code. Absent means the player has not answered yet.
    manual_answers: dict[str, bool] = field(default_factory=dict)


@dataclass(frozen=True)
class RuleResult:
    """One rule's verdict, with enough detail for the overlay to say *why*."""

    ok: bool
    actual: str | None = None
    expected: str | None = None
    unknown: bool = False


@dataclass(frozen=True)
class Rule:
    """A rule, its consequence, and how to check it."""

    code: str
    label: str
    scope: Scope
    kind: Kind
    describe: str
    evaluate: Callable[[RuleContext, dict[str, Any]], RuleResult]
    # The wire reason a failing *risk* rule sends back. Playbook rules have none, by construction.
    reason: str | None = None

    def check(self, ctx: RuleContext, params: dict[str, Any] | None = None) -> RuleResult:
        return self.evaluate(ctx, params or {})


def _ok(condition: bool, actual: Any = None, expected: Any = None) -> RuleResult:
    return RuleResult(
        ok=bool(condition),
        actual=None if actual is None else str(actual),
        expected=None if expected is None else str(expected),
    )


# -- risk rules: the gateway enforces these -------------------------------------------


def _clutch(ctx: RuleContext, _p: dict[str, Any]) -> RuleResult:
    return _ok(ctx.clutch, ctx.clutch, "clutch held")


def _dead_man(ctx: RuleContext, _p: dict[str, Any]) -> RuleResult:
    return _ok(ctx.heartbeat_age_s < ctx.heartbeat_dead_s,
               f"{ctx.heartbeat_age_s:.1f}s", f"< {ctx.heartbeat_dead_s}s")


def _session_window(ctx: RuleContext, _p: dict[str, Any]) -> RuleResult:
    return _ok(ctx.session_open, ctx.session_label, "inside the evening window")


def _symbol_allowlist(ctx: RuleContext, _p: dict[str, Any]) -> RuleResult:
    return _ok(ctx.symbol in ctx.allowed_symbols, ctx.symbol, "a configured symbol")


def _max_positions(ctx: RuleContext, _p: dict[str, Any]) -> RuleResult:
    return _ok(ctx.positions_open < ctx.max_positions, ctx.positions_open,
               f"< {ctx.max_positions}")


def _max_lots(ctx: RuleContext, _p: dict[str, Any]) -> RuleResult:
    return _ok(ctx.lots <= ctx.max_lots, ctx.lots, f"<= {ctx.max_lots}")


def _daily_loss(ctx: RuleContext, _p: dict[str, Any]) -> RuleResult:
    return _ok(ctx.day_loss_usd < ctx.max_day_loss_usd, ctx.day_loss_usd,
               f"< {ctx.max_day_loss_usd}")


def _order_rate(ctx: RuleContext, _p: dict[str, Any]) -> RuleResult:
    return _ok(ctx.seconds_since_last_order >= ctx.min_seconds_between_orders,
               f"{ctx.seconds_since_last_order:.1f}s", f">= {ctx.min_seconds_between_orders}s")


# -- playbook rules: grading scores these, and they never reject -----------------------


def _named_setup(ctx: RuleContext, _p: dict[str, Any]) -> RuleResult:
    return _ok(bool(ctx.setup_tag), ctx.setup_tag or "none", "a named setup on the chart")


def _setup_matches(ctx: RuleContext, params: dict[str, Any]) -> RuleResult:
    """The chart is showing the setup this playbook is actually for."""
    wanted = params.get("detector_tag")
    if wanted is None:
        return RuleResult(ok=True, actual="no detector required", unknown=False)
    return _ok(ctx.setup_tag == wanted, ctx.setup_tag or "none", wanted)


def _with_trend(ctx: RuleContext, _p: dict[str, Any]) -> RuleResult:
    """Trading the side the detector is pointing at, rather than against it."""
    if ctx.setup_side is None or ctx.side is None:
        return RuleResult(ok=False, actual="unknown", expected="side matches the setup",
                          unknown=True)
    if ctx.setup_side == "none":
        return RuleResult(ok=True, actual="setup has no side", expected="either side")
    return _ok(ctx.setup_side == ctx.side, ctx.side, ctx.setup_side)


def _ema_distance(ctx: RuleContext, params: dict[str, Any]) -> RuleResult:
    """Not chasing: price within N ATR of the 20 EMA.

    This is the rule the confirm overlay most often has something to say about, which is why the
    result carries the actual multiple rather than just a boolean.
    """
    limit = float(params.get("max_atr", 1.5))
    if ctx.price is None or ctx.ema20 is None or not ctx.atr:
        return RuleResult(ok=False, actual="no chart data", expected=f"<= {limit} ATR from EMA20",
                          unknown=True)
    multiple = abs(ctx.price - ctx.ema20) / ctx.atr
    return _ok(multiple <= limit, f"{multiple:.2f} ATR", f"<= {limit} ATR")


def _spread_under_cap(ctx: RuleContext, params: dict[str, Any]) -> RuleResult:
    cap = params.get("cap", ctx.spread_cap)
    if ctx.spread is None or not cap:
        return RuleResult(ok=False, actual="no spread reading", expected="under the cap",
                          unknown=True)
    return _ok(ctx.spread <= float(cap), f"{ctx.spread:.5f}", f"<= {cap}")


def _event_guard(ctx: RuleContext, params: dict[str, Any]) -> RuleResult:
    """Outside T-minus-N of a high-impact print."""
    guard = float(params.get("seconds", 900))
    if ctx.seconds_to_high_impact is None:
        return _ok(True, "no event ahead", f"> {guard}s away")
    return _ok(ctx.seconds_to_high_impact > guard,
               f"{ctx.seconds_to_high_impact:.0f}s", f"> {guard}s")


def _manual(code: str) -> Callable[[RuleContext, dict[str, Any]], RuleResult]:
    """A rule only the player can answer. Unanswered is `unknown`, which costs nothing."""

    def evaluate(ctx: RuleContext, _p: dict[str, Any]) -> RuleResult:
        if code not in ctx.manual_answers:
            return RuleResult(ok=False, actual="not answered", expected="yes", unknown=True)
        answer = ctx.manual_answers[code]
        return _ok(answer, "yes" if answer else "no", "yes")

    return evaluate


_RULES: tuple[Rule, ...] = (
    # risk — enforced
    Rule("clutch", "Clutch held", "risk", "auto",
         "the intent itself must carry the clutch", _clutch, reason="no_clutch"),
    Rule("dead_man", "Link alive", "risk", "auto",
         "a stale heartbeat locks opens; it never locks an exit", _dead_man, reason="dead_man"),
    Rule("session_window", "Inside the session", "risk", "auto",
         "opens only inside the evening window, in the configured zone", _session_window,
         reason="session_closed"),
    Rule("symbol_allowlist", "Configured symbol", "risk", "auto",
         "only configured symbols may be traded", _symbol_allowlist,
         reason="symbol_not_allowed"),
    Rule("max_positions", "Position cap", "risk", "auto",
         "never more concurrent positions than configured", _max_positions,
         reason="max_positions"),
    Rule("max_lots", "Size cap", "risk", "auto", "per-symbol size cap", _max_lots,
         reason="max_lots"),
    Rule("daily_loss", "Daily loss", "risk", "auto",
         "past the daily loss the evening is close-only", _daily_loss, reason="daily_loss"),
    Rule("order_rate", "Order spacing", "risk", "auto",
         "a minimum gap between orders, so one twitch is not two fires", _order_rate,
         reason="rate_limited"),
    # playbook — graded, never enforced
    Rule("named_setup", "A named setup is present", "playbook", "auto",
         "the chart is showing something you recognise", _named_setup),
    Rule("setup_matches", "The setup this playbook is for", "playbook", "auto",
         "the detector tag matches the playbook's own setup", _setup_matches),
    Rule("with_trend", "Trading the setup's side", "playbook", "auto",
         "the fire agrees with the direction the setup points", _with_trend),
    Rule("ema_distance", "Not chasing", "playbook", "auto",
         "price is still within reach of the 20 EMA", _ema_distance),
    Rule("spread_under_cap", "Spread is payable", "playbook", "auto",
         "the spread is not eating the setup", _spread_under_cap),
    Rule("event_guard", "Clear of the calendar", "playbook", "auto",
         "outside the window before a high-impact print", _event_guard),
    Rule("waited_for_retest", "Waited for the retest", "playbook", "manual",
         "you let it come back before entering", _manual("waited_for_retest")),
    Rule("no_chase", "Did not chase", "playbook", "manual",
         "you entered at your level, not after it left", _manual("no_chase")),
    Rule("plan_before_fire", "Planned before firing", "playbook", "manual",
         "the trade existed in your head before your hands moved", _manual("plan_before_fire")),
)

REGISTRY: dict[str, Rule] = {rule.code: rule for rule in _RULES}


def rules_for(scope: Scope) -> tuple[Rule, ...]:
    """Every rule of one scope, in registry order."""
    return tuple(rule for rule in _RULES if rule.scope == scope)


def get(code: str) -> Rule:
    rule = REGISTRY.get(code)
    if rule is None:
        raise KeyError(f"`{code}` is not a rule in the registry")
    return rule


def manual_codes() -> tuple[str, ...]:
    """What the post-trade checklist may ask about. Nothing else is answerable by hand."""
    return tuple(rule.code for rule in _RULES if rule.kind == "manual")
