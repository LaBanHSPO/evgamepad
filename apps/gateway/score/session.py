"""The Process Score: one number to chase, computed only from things you control.

TradeZella's Zella Score is the right game mechanic pointed at the wrong inputs. Win rate and
profit factor are *outcome*, and chasing an outcome number is exactly the anxiety this whole design
exists to treat. So the mechanic stays and the inputs change: five axes, every one of them process.

The property that makes it work, and the one the tests exist to defend: **a correctly-declined
evening scores at least as well as a well-traded one.** A dead tape you left alone scores 100. A
busy evening you executed well scores 98. Freezing in a rich tape scores 70. Overtrading a dead
tape scores 65.

Two structural rules:

1. **No outcome input, anywhere.** Not P/L, not R, not win rate. `test_session.py` reads this module
   and fails if a money word appears in it.
2. **Nothing accumulates across sessions.** No streak, no level, no "days since". Every number here
   is about one evening, and the schema has nowhere to put a running total.

Vacuous axes are the subtle part. With zero fires, Adherence and Risk Discipline have no
denominator. Scoring them 0 punishes standing down; scoring them 100 is free points for doing
nothing. Both are wrong, so the axis is **dropped** and its weight renormalises across the axes that
actually have evidence.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

# The five axes, in the order the radar draws them.
AXES = ("adherence", "selectivity", "risk_discipline", "preparation", "review")

DEFAULT_WEIGHTS: dict[str, float] = {
    "adherence": 0.30,
    "selectivity": 0.25,
    "risk_discipline": 0.20,
    "preparation": 0.15,
    "review": 0.10,
}

# Bumping this makes stored rows recompute on read rather than silently mixing weightings.
WEIGHTS_VERSION = 1

# Each trade outside the selectivity band costs this much.
SELECTIVITY_STEP = 25.0

# What one genuine stand-down is worth, and the cap that stops cancels being farmed.
DECLINE_CREDIT_PER = 5.0

# How much of the evening's memo coverage the Review axis asks for.
MEMO_COVERAGE = 2 / 3


def half_up(value: float) -> int:
    """Round half away from zero.

    Python's `round` is banker's rounding, which would turn the plan's 97.5 into 98 by luck and
    some other evening's 96.5 into 96. The displayed score should not depend on parity.
    """
    return int(math.floor(value + 0.5)) if value >= 0 else -int(math.floor(-value + 0.5))


@dataclass(frozen=True)
class FireInputs:
    """One fire, as the score sees it. Every field is process-side; none of them is money."""

    cid: str
    # Phase 7's grade. `required_total == 0` is an unplanned fire, which evaluates no required rule.
    required_pass: int = 0
    required_total: int = 0
    # Risk discipline, one boolean per check.
    within_lot_cap: bool = True
    stop_at_entry: bool = False
    r_within_tolerance: bool = True
    within_max_positions: bool = True
    respected_order_spacing: bool = True
    # Review evidence.
    has_memo: bool = False
    checklist_answered: bool = False


@dataclass(frozen=True)
class SessionInputs:
    """Everything the score reads about one evening. Stored, so a weight change recomputes."""

    session_id: str
    fires: tuple[FireInputs, ...] = ()

    # Selectivity.
    oq_mean: float | None = None
    declines: int = 0

    # Preparation.
    plan_acknowledged: bool = False
    pre_checkin: bool = False
    playbook_selected: bool = False
    memo_tonight: bool = False

    # Review.
    post_checkin: bool = False
    replays_opened: int = 0
    # False on a first session: there is no past trade to replay, so the item is dropped rather
    # than failed. Only meaningful on a zero-fire evening, where Review has no trades of its own.
    past_trade_available: bool = True

    # Voice is evidence only when it was actually available. A supported degradation is not a miss;
    # skipping capture that *was* available is.
    voice_available: bool = False


@dataclass(frozen=True)
class Axis:
    """One axis, its value, and the sub-items that produced it."""

    name: str
    value: float | None
    detail: dict[str, Any] = field(default_factory=dict)

    @property
    def vacuous(self) -> bool:
        return self.value is None


@dataclass(frozen=True)
class SessionScore:
    """The evening's five axes, the total, and which axes had no evidence."""

    session_id: str
    axes: tuple[Axis, ...]
    total: float
    na_axes: tuple[str, ...]
    oq_mean: float | None
    n_fires: int
    weights_version: int = WEIGHTS_VERSION

    @property
    def displayed(self) -> int:
        """What the radar prints. The unrounded value is what gets stored."""
        return half_up(self.total)

    def axis(self, name: str) -> Axis:
        return next(a for a in self.axes if a.name == name)

    def payload(self) -> dict[str, Any]:
        return {
            "sessionId": self.session_id,
            "total": self.displayed,
            "totalExact": round(self.total, 4),
            "weightsVersion": self.weights_version,
            "oqMean": self.oq_mean,
            "nFires": self.n_fires,
            "naAxes": list(self.na_axes),
            "axes": [
                {"name": a.name, "value": None if a.value is None else round(a.value, 2),
                 "detail": a.detail}
                for a in self.axes
            ],
        }


# -- axes -----------------------------------------------------------------------------


def adherence_axis(inputs: SessionInputs) -> Axis:
    """Required playbook rules passed over required rules evaluated, across the whole evening.

    Vacuous with no fires — and equally vacuous when every fire was unplanned, because an unplanned
    fire evaluates no required rule and dividing by nothing is not a score of nothing.
    """
    total = sum(f.required_total for f in inputs.fires)
    if total == 0:
        return Axis("adherence", None, {"reason": "no required rules were evaluated"})
    passed = sum(f.required_pass for f in inputs.fires)
    return Axis("adherence", 100.0 * passed / total, {"passed": passed, "evaluated": total})


def selectivity_axis(
    inputs: SessionInputs, *, trades_max: int, band_width: float, decline_credit_max: float,
) -> Axis:
    """How well the trade count matched what the tape actually offered.

    This is the axis that makes standing down pay. The credit is capped so cancels cannot be
    farmed, and the axis cannot exceed 100, so no amount of declining buys a perfect evening on
    its own.
    """
    fires = len(inputs.fires)
    if inputs.oq_mean is None:
        # No sentinel samples at all. Scoring "how well you matched the tape" against a tape nobody
        # measured would be a guess with a number on it.
        return Axis("selectivity", None, {"reason": "the tape's quality was never sampled"})

    expected = half_up(inputs.oq_mean * trades_max)
    low = max(0, expected - band_width)
    high = expected + band_width
    distance = 0.0
    if fires < low:
        distance = low - fires
    elif fires > high:
        distance = fires - high

    base = 100.0 if distance == 0 else max(0.0, min(100.0, 100.0 - SELECTIVITY_STEP * distance))
    credit = min(decline_credit_max, DECLINE_CREDIT_PER * inputs.declines)
    return Axis("selectivity", min(100.0, base + credit), {
        "expected": expected, "band": [low, high], "fires": fires,
        "outsideBy": distance, "base": base, "declineCredit": credit,
    })


# The five per-fire risk checks, named so the deck can say which one an evening failed.
RISK_CHECKS = ("within_lot_cap", "stop_at_entry", "r_within_tolerance",
               "within_max_positions", "respected_order_spacing")


def risk_axis(inputs: SessionInputs) -> Axis:
    """Five checks per fire. Vacuous with no fires — nothing was risked, so nothing was risked badly."""
    if not inputs.fires:
        return Axis("risk_discipline", None, {"reason": "no fires"})

    results = {check: sum(1 for f in inputs.fires if getattr(f, check)) for check in RISK_CHECKS}
    passed = sum(results.values())
    total = len(inputs.fires) * len(RISK_CHECKS)
    return Axis("risk_discipline", 100.0 * passed / total,
                {"passed": passed, "checks": total, "byCheck": results})


def preparation_axis(inputs: SessionInputs) -> Axis:
    """Did you set the evening up before trading it. Never vacuous — preparation is always possible."""
    items: dict[str, bool] = {
        "planAcknowledged": inputs.plan_acknowledged,
        "preCheckin": inputs.pre_checkin,
        "playbookSelected": inputs.playbook_selected,
    }
    # A memo is evidence only when voice was actually available. Punishing a supported degradation
    # would make the score a measure of the install rather than of the evening.
    if inputs.voice_available:
        items["memo"] = inputs.memo_tonight
    return _from_items("preparation", items)


def review_axis(inputs: SessionInputs) -> Axis:
    """Did you look at the evening afterwards.

    With no fires there is nothing of tonight's to review, so the trade-dependent items are replaced
    by trade-independent ones. A first session with no past trade to replay drops that item too,
    rather than failing an impossible requirement.
    """
    items: dict[str, bool] = {"postCheckin": inputs.post_checkin}

    if inputs.fires:
        items["checklists"] = all(f.checklist_answered for f in inputs.fires)
        items["replayOpened"] = inputs.replays_opened >= 1
        if inputs.voice_available:
            covered = sum(1 for f in inputs.fires if f.has_memo)
            items["memoCoverage"] = covered / len(inputs.fires) >= MEMO_COVERAGE
        return _from_items("review", items)

    if inputs.voice_available:
        items["memo"] = inputs.memo_tonight
    if inputs.past_trade_available:
        items["replayOpened"] = inputs.replays_opened >= 1
    return _from_items("review", items)


def _from_items(name: str, items: dict[str, bool]) -> Axis:
    if not items:
        return Axis(name, None, {"reason": "no evidence was available to ask for"})
    met = sum(1 for value in items.values() if value)
    return Axis(name, 100.0 * met / len(items), {"met": met, "of": len(items), "items": items})


# -- composition ----------------------------------------------------------------------


def score_session(
    inputs: SessionInputs, *, weights: dict[str, float] | None = None, trades_max: int = 6,
    band_width: float = 1, decline_credit_max: float = 15,
) -> SessionScore:
    """The whole evening, as one number and the five that made it.

    Pure: same rows in, same score out, forever. No model computes any number that appears on the
    deck, and a weight change re-derives every historical score from the stored inputs.
    """
    weights = weights or DEFAULT_WEIGHTS

    axes = (
        adherence_axis(inputs),
        selectivity_axis(inputs, trades_max=trades_max, band_width=band_width,
                         decline_credit_max=decline_credit_max),
        risk_axis(inputs),
        preparation_axis(inputs),
        review_axis(inputs),
    )

    present = [a for a in axes if not a.vacuous]
    live_weight = sum(weights.get(a.name, 0.0) for a in present)
    if live_weight <= 0:
        # Every axis vacuous. That is not a zero — it is an evening with nothing to say about it.
        return SessionScore(inputs.session_id, axes, 0.0,
                            tuple(a.name for a in axes if a.vacuous), inputs.oq_mean,
                            len(inputs.fires))

    total = sum((a.value or 0.0) * weights.get(a.name, 0.0) for a in present) / live_weight
    return SessionScore(
        session_id=inputs.session_id,
        axes=axes,
        total=total,
        na_axes=tuple(a.name for a in axes if a.vacuous),
        oq_mean=inputs.oq_mean,
        n_fires=len(inputs.fires),
    )
