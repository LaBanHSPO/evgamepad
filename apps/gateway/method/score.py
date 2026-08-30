"""The Process Score: five axes, none of them about money.

Win rate, profit factor, P/L and R are **not** inputs. Neither is tilt -- it
renders on the deck as a retrospective, never as a score. Every input is
something the player did, which is the whole point: a good evening on a dead
tape should score well, and standing down should be one of the ways to earn it.

Two rules do most of the work here:

* **A vacuous axis is dropped, not scored.** With zero fires, Adherence has no
  denominator. Scoring it 0 punishes standing down, which is forbidden; scoring
  it 100 is free points for doing nothing. It is dropped and its weight
  redistributes over the axes that have evidence.
* **A supported degradation is never a penalty.** If voice is disabled or the
  browser had no usable microphone, the memo sub-items are dropped and the axis
  renormalises. If voice *was* available and the player skipped it, that stays a
  genuine miss.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

AxisKey = Literal["adherence", "selectivity", "risk_discipline", "preparation", "review"]

AXES: tuple[AxisKey, ...] = (
    "adherence", "selectivity", "risk_discipline", "preparation", "review",
)

WEIGHTS_VERSION = "1"

#: Selectivity's decline credit caps here so cancels cannot be farmed.
DECLINE_CREDIT_PER = 5
DECLINE_CREDIT_MAX = 15


@dataclass(frozen=True)
class SubItem:
    """One piece of evidence. ``ok=None`` means not applicable -- it drops out
    of the axis rather than counting against it."""

    key: str
    label: str
    ok: bool | None
    note: str = ""


@dataclass(frozen=True)
class Axis:
    key: AxisKey
    label: str
    #: None when the axis has no evidence at all: it is dropped, not zeroed.
    value: float | None
    weight: float
    items: tuple[SubItem, ...] = ()
    reason: str = ""

    @property
    def vacuous(self) -> bool:
        return self.value is None


def _from_items(
    key: AxisKey, label: str, weight: float, items: tuple[SubItem, ...], reason: str = ""
) -> Axis:
    evaluated = [i for i in items if i.ok is not None]
    if not evaluated:
        return Axis(key, label, None, weight, items, reason or "no evidence")
    passed = sum(1 for i in evaluated if i.ok)
    return Axis(key, label, 100.0 * passed / len(evaluated), weight, items)


@dataclass
class ScoreInputs:
    """Everything the score reads. All process-side, by construction."""

    fires: int = 0
    #: Phase 7 grades, summed over tonight's fires.
    required_passed: int = 0
    required_evaluated: int = 0
    #: Phase 4's sentinel. None until it exists -- Selectivity is then vacuous
    #: rather than guessed at.
    opportunity_quality: float | None = None
    trades_max: int = 6
    band_width: int = 1
    stand_downs: int = 0
    #: Per-fire risk checks: (passed, evaluated) across tonight.
    risk_passed: int = 0
    risk_evaluated: int = 0
    # Preparation
    pre_check_in: bool = False
    playbook_selected: bool = False
    plan_before_first_fire: bool = False
    # Review
    post_check_in: bool = False
    trades_with_memo: int = 0
    replays_opened: int = 0
    checklists_answered: int = 0
    checklists_available: int = 0
    memos_tonight: int = 0
    #: False when voice is disabled or no microphone was usable. The memo
    #: sub-items then drop instead of scoring against the player.
    voice_available: bool = False
    #: Whether any past trade exists to replay. A first session must not fail
    #: an impossible requirement.
    replayable_trades_exist: bool = False


def adherence(i: ScoreInputs, weight: float) -> Axis:
    """Required playbook rules passed over required rules evaluated."""
    if i.required_evaluated == 0:
        return Axis(
            "adherence", "Adherence", None, weight, (),
            "no trades" if i.fires == 0 else "no required rules evaluated",
        )
    return Axis(
        "adherence", "Adherence",
        100.0 * i.required_passed / i.required_evaluated, weight,
        (SubItem("rules", "Required rules passed", True,
                 f"{i.required_passed}/{i.required_evaluated}"),),
    )


def selectivity(i: ScoreInputs, weight: float) -> Axis:
    """How well the trade count matched the tape's opportunity quality.

    This is the mechanism that makes standing down pay: an ARM cancelled while
    a stand-down condition was live earns credit, using phase 3's existing
    counter rather than a second one.
    """
    if i.opportunity_quality is None:
        return Axis(
            "selectivity", "Selectivity", None, weight, (),
            "no sentinel opportunity quality yet",
        )

    expected = round(i.opportunity_quality * i.trades_max)
    low = max(0, expected - i.band_width)
    high = expected + i.band_width

    if low <= i.fires <= high:
        base = 100.0
    else:
        distance = low - i.fires if i.fires < low else i.fires - high
        base = max(0.0, min(100.0, 100.0 - 25.0 * distance))

    credit = min(DECLINE_CREDIT_MAX, DECLINE_CREDIT_PER * i.stand_downs)
    value = min(100.0, base + credit)

    return Axis(
        "selectivity", "Selectivity", value, weight,
        (
            SubItem("count", "Trades matched the tape", low <= i.fires <= high,
                    f"{i.fires} fires, expected {low}-{high}"),
            SubItem("declines", "Stood down when it was right", i.stand_downs > 0,
                    f"+{credit} credit from {i.stand_downs}"),
        ),
    )


def risk_discipline(i: ScoreInputs, weight: float) -> Axis:
    if i.risk_evaluated == 0:
        return Axis("risk_discipline", "Risk discipline", None, weight, (), "no trades")
    return Axis(
        "risk_discipline", "Risk discipline",
        100.0 * i.risk_passed / i.risk_evaluated, weight,
        (SubItem("checks", "Per-fire risk checks passed", True,
                 f"{i.risk_passed}/{i.risk_evaluated}"),),
    )


def preparation(i: ScoreInputs, weight: float) -> Axis:
    items = (
        SubItem("pre_check_in", "Pre-session check-in", i.pre_check_in),
        SubItem("playbook", "A playbook was selected", i.playbook_selected),
        SubItem("plan", "Plan acknowledged before the first fire",
                i.plan_before_first_fire if i.fires > 0 else None,
                "" if i.fires else "no trades"),
        SubItem("memo", "At least one memo",
                (i.memos_tonight > 0) if i.voice_available else None,
                "" if i.voice_available else "voice unavailable"),
    )
    return _from_items("preparation", "Preparation", weight, items)


def review(i: ScoreInputs, weight: float) -> Axis:
    """On a zero-trade evening the trade-dependent items are replaced by
    trade-independent ones, so an evening spent correctly not trading can still
    be reviewed well."""
    if i.fires == 0:
        items = (
            SubItem("post_check_in", "Post-session check-in", i.post_check_in),
            SubItem("memo", "At least one memo tonight",
                    (i.memos_tonight > 0) if i.voice_available else None,
                    "" if i.voice_available else "voice unavailable"),
            SubItem("replay", "Replayed a past trade",
                    (i.replays_opened > 0) if i.replayable_trades_exist else None,
                    "" if i.replayable_trades_exist else "no past trades yet"),
        )
        return _from_items("review", "Review", weight, items)

    memo_ratio = i.trades_with_memo / i.fires
    items = (
        SubItem("post_check_in", "Post-session check-in", i.post_check_in),
        SubItem("memos", "Memos on most trades",
                (memo_ratio >= 2 / 3) if i.voice_available else None,
                f"{i.trades_with_memo}/{i.fires}" if i.voice_available else "voice unavailable"),
        SubItem("replay", "Opened a replay", i.replays_opened > 0),
        SubItem("checklists", "Post-trade checklists answered",
                (i.checklists_answered >= i.checklists_available)
                if i.checklists_available else None,
                f"{i.checklists_answered}/{i.checklists_available}"),
    )
    return _from_items("review", "Review", weight, items)


@dataclass(frozen=True)
class ProcessScore:
    total: float
    axes: tuple[Axis, ...]
    na: tuple[AxisKey, ...]
    weights_version: str = WEIGHTS_VERSION

    def as_message(self) -> dict:
        return {
            "axes": {a.key: round(a.value, 1) for a in self.axes if a.value is not None},
            "total": round(self.total, 1),
            "na": list(self.na),
            "weightsVersion": self.weights_version,
        }


def compute(inputs: ScoreInputs, weights: dict[str, float]) -> ProcessScore:
    """Weighted mean over the axes that have evidence.

    Vacuous axes are dropped and their weight redistributes. They render as a
    dashed "n/a" ring on the radar, never as a zero spoke -- a zero spoke would
    read as a bad evening rather than an absent measurement.
    """
    axes = (
        adherence(inputs, weights.get("adherence", 0.30)),
        selectivity(inputs, weights.get("selectivity", 0.25)),
        risk_discipline(inputs, weights.get("risk_discipline", 0.20)),
        preparation(inputs, weights.get("preparation", 0.15)),
        review(inputs, weights.get("review", 0.10)),
    )
    scored = [a for a in axes if a.value is not None]
    na = tuple(a.key for a in axes if a.value is None)

    if not scored:
        return ProcessScore(total=0.0, axes=axes, na=na)

    total_weight = sum(a.weight for a in scored)
    if total_weight <= 0:
        return ProcessScore(total=0.0, axes=axes, na=na)

    total = sum(a.value * a.weight for a in scored) / total_weight  # type: ignore[operator]
    return ProcessScore(total=total, axes=axes, na=na)
