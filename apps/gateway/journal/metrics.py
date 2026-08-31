"""Trade quality, execution scores, and Process Consistency — all deterministic.

Everything here is a pure function over rows the other phases already wrote. No model computes a
number that reaches this journal, for the same reason phase 6 established: a figure you cannot
re-derive from the rows is a figure you end up arguing with.

Three rules the analytics obey, each guarding against a specific way a journal starts lying:

1. **Never assert a counterfactual.** Actual vs Plan compares what you planned with what you did.
   It does not claim the target "would have been hit" — the tape after your exit is not evidence
   about a trade you were no longer in.
2. **Unknown is not zero.** An input that was never captured drops out and the remaining weights
   renormalise. Scoring a missing memo as nought would make the score a measure of what the build
   supports rather than of what you did.
3. **Intent is confirmed, never inferred.** `impulsive` and `revenge` describe a state of mind.
   Evidence can *suggest* one; only the player can assert it, because the cost of libelling a clean
   discretionary trade is that you stop trusting the whole journal.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Any, Literal

Intent = Literal["planned", "impulsive", "revenge", "unknown"]
Stage = Literal["before", "during", "after"]

# The four evidence-backed groups. `unknown` is deliberately not one of them — it is excluded from
# the chart rather than folded into a guess.
GROUPS = ("planned-win", "planned-loss", "impulsive/revenge-loss", "impulsive/revenge-win")

# Process Consistency asks for a real sample before it says anything confident.
MIN_SESSIONS_FOR_CONSISTENCY = 5
CONSISTENCY_WINDOW = 20


# -- execution scores ------------------------------------------------------------------


@dataclass(frozen=True)
class StageScore:
    """One execution stage, its score, and the sub-items behind it."""

    stage: Stage
    value: float | None
    items: dict[str, bool] = field(default_factory=dict)
    dropped: tuple[str, ...] = ()

    def payload(self) -> dict[str, Any]:
        return {"stage": self.stage, "value": None if self.value is None else round(self.value, 1),
                "items": self.items, "dropped": list(self.dropped)}


def _score(stage: Stage, items: dict[str, bool | None]) -> StageScore:
    """Drop what was never measured, then score what is left.

    `None` means *not captured*; `False` means captured and missed. Collapsing the two is the most
    common way a journal turns a limitation of the build into a criticism of the player.
    """
    measured = {name: bool(value) for name, value in items.items() if value is not None}
    dropped = tuple(name for name, value in items.items() if value is None)
    if not measured:
        return StageScore(stage, None, {}, dropped)
    met = sum(1 for value in measured.values() if value)
    return StageScore(stage, 100.0 * met / len(measured), measured, dropped)


@dataclass(frozen=True)
class TradeFacts:
    """One trade as the journal sees it. `None` everywhere means *not captured*."""

    cid: str
    # Before: what existed at the moment of the fire.
    had_daily_analysis: bool | None = None
    readiness_complete: bool | None = None
    playbook_selected: bool | None = None
    grade_clean: bool | None = None

    # During: what the execution actually did.
    within_lot_cap: bool | None = None
    stop_at_entry: bool | None = None
    stop_never_worsened: bool | None = None
    respected_rules: bool | None = None

    # After: whether it was reviewed.
    checklist_answered: bool | None = None
    has_memo: bool | None = None
    post_checkin: bool | None = None
    replay_opened: bool | None = None

    # Actual vs Plan.
    planned_r: float | None = None       # planned reward in R, from the plan's own SL and TP
    realised_r: float | None = None
    planned_sl: float | None = None
    planned_tp: float | None = None
    amendments: tuple[dict[str, Any], ...] = ()

    intent: Intent | None = None
    intent_by: str | None = None


def before_score(facts: TradeFacts) -> StageScore:
    """Was the trade set up before it was taken."""
    return _score("before", {
        "dailyAnalysis": facts.had_daily_analysis,
        "readiness": facts.readiness_complete,
        "playbook": facts.playbook_selected,
        "gradeClean": facts.grade_clean,
    })


def during_score(facts: TradeFacts) -> StageScore:
    """Was it executed the way it was set up."""
    return _score("during", {
        "withinLotCap": facts.within_lot_cap,
        "stopAtEntry": facts.stop_at_entry,
        "stopNeverWorsened": facts.stop_never_worsened,
        "respectedRules": facts.respected_rules,
    })


def after_score(facts: TradeFacts) -> StageScore:
    """Was it reviewed afterwards."""
    return _score("after", {
        "checklist": facts.checklist_answered,
        "memo": facts.has_memo,
        "postCheckin": facts.post_checkin,
        "replayOpened": facts.replay_opened,
    })


def execution_scores(facts: TradeFacts) -> dict[str, Any]:
    return {stage.stage: stage.payload()
            for stage in (before_score(facts), during_score(facts), after_score(facts))}


# -- actual vs plan --------------------------------------------------------------------


def worsened_stops(amendments: tuple[dict[str, Any], ...], *, side: str,
                   original_sl: float | None) -> list[dict[str, Any]]:
    """Amendments that moved the stop **away** from the entry — further risk, not less.

    Direction matters: for a long, a lower stop is worse; for a short, a higher one is. Counting
    every amendment as a mistake would penalise the entirely correct act of trailing a stop up.
    """
    if original_sl is None:
        return []
    long = side.lower() == "buy"
    worse: list[dict[str, Any]] = []
    current = original_sl
    for amendment in amendments:
        moved = amendment.get("sl")
        if moved is None:
            continue
        if (moved < current) if long else (moved > current):
            worse.append({"ts": amendment.get("ts"), "from": current, "to": moved})
        current = moved
    return worse


def actual_vs_plan(facts: TradeFacts, *, side: str) -> dict[str, Any]:
    """What was planned, beside what happened. Never a claim about what would have happened.

    The one thing deliberately absent is any statement that the planned target *would* have been
    reached. Where price went after the exit is not evidence about a position that was closed.
    """
    worse = worsened_stops(facts.amendments, side=side, original_sl=facts.planned_sl)
    delta = (
        None if facts.planned_r is None or facts.realised_r is None
        else facts.realised_r - facts.planned_r
    )
    return {
        "plannedR": facts.planned_r,
        "realisedR": facts.realised_r,
        "deltaR": delta,
        "plannedSl": facts.planned_sl,
        "plannedTp": facts.planned_tp,
        "amendments": [dict(a) for a in facts.amendments],
        "worsenedStops": worse,
        # Named so nobody reads it as a counterfactual. This is the label, not a description of it.
        "label": "Actual vs Plan",
    }


# -- the four groups -------------------------------------------------------------------


def derive_intent(*, grade_clean: bool | None, playbook_id: str | None,
                  confirmed: Intent | None) -> tuple[Intent, str]:
    """The trade's group, and who decided it.

    A clean fire under a real playbook defaults to `planned` — that is what the evidence says.
    Anything dirty or unplanned stays `unknown` until the player says otherwise, because the
    difference between "I took a marginal setup" and "I was chasing" is not on the chart.
    """
    if confirmed is not None:
        return confirmed, "player"
    planned_book = bool(playbook_id) and playbook_id != "__unplanned__"
    if grade_clean and planned_book:
        return "planned", "derived"
    return "unknown", "derived"


def group_for(intent: Intent, realised_r: float | None) -> str | None:
    """One of the four groups, or `None` when the evidence does not support any of them."""
    if intent == "unknown" or realised_r is None:
        return None
    won = realised_r > 0
    if intent == "planned":
        return "planned-win" if won else "planned-loss"
    return "impulsive/revenge-win" if won else "impulsive/revenge-loss"


def group_counts(trades: list[tuple[Intent, float | None]]) -> dict[str, Any]:
    """The four-group chart. Unknowns are counted separately and never distributed into the four."""
    counts = dict.fromkeys(GROUPS, 0)
    unknown = 0
    for intent, realised in trades:
        group = group_for(intent, realised)
        if group is None:
            unknown += 1
            continue
        counts[group] += 1
    return {"groups": counts, "unclassified": unknown,
            "note": "unclassified trades are excluded rather than guessed"}


# -- process consistency ---------------------------------------------------------------


@dataclass(frozen=True)
class Consistency:
    """How steady the process has been, and how much data that claim rests on."""

    value: float | None
    n: int
    mean: float | None
    mad: float | None
    reason: str | None = None

    def payload(self) -> dict[str, Any]:
        return {
            "value": None if self.value is None else round(self.value, 1),
            "n": self.n,
            "mean": None if self.mean is None else round(self.mean, 1),
            "meanAbsoluteDeviation": None if self.mad is None else round(self.mad, 2),
            "reason": self.reason,
        }


def process_consistency(scores: list[float]) -> Consistency:
    """`0.5 * mean + 0.5 * (100 - mean absolute deviation from the median)`, over the last 20.

    Two halves, doing different jobs: the mean says how well you played, the deviation says how
    *reliably*. A player at a steady 80 is ahead of one who alternates 100 and 60, and that is the
    whole point of measuring consistency rather than an average.

    Below five sessions it refuses to answer. Four evenings is not a process, it is a week.
    """
    window = scores[-CONSISTENCY_WINDOW:]
    if len(window) < MIN_SESSIONS_FOR_CONSISTENCY:
        return Consistency(None, len(window), None, None, reason="not enough sessions yet")

    mean = statistics.fmean(window)
    median = statistics.median(window)
    mad = statistics.fmean(abs(value - median) for value in window)
    return Consistency(max(0.0, min(100.0, 0.5 * mean + 0.5 * (100 - mad))),
                       len(window), mean, mad)
