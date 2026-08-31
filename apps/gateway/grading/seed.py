"""Starter playbooks, seeded from the phase 4 detectors.

The player begins with a real book rather than an empty one. Each of these is a setup the
detectors can actually recognise, so the grade in the confirm overlay says something on night one.

The rules are ours; the approach they encode is Volman's and is cited in the desk prompt.
"""

from __future__ import annotations

from .grade import Playbook, PlaybookRule


# Every starter book shares this spine: a named setup, the right side, not chased, payable
# spread, and clear of the calendar.
def _common(detector: str, ord_from: int = 0) -> tuple[PlaybookRule, ...]:
    return (
        PlaybookRule(code="named_setup", ord=ord_from + 0),
        PlaybookRule(code="setup_matches", params={"detector_tag": detector}, ord=ord_from + 1),
        PlaybookRule(code="with_trend", ord=ord_from + 2),
        PlaybookRule(code="ema_distance", params={"max_atr": 1.5}, ord=ord_from + 3),
        PlaybookRule(code="spread_under_cap", ord=ord_from + 4),
        PlaybookRule(code="event_guard", params={"seconds": 900}, ord=ord_from + 5),
    )


STARTERS: tuple[Playbook, ...] = (
    Playbook(
        id="pb-range-break",
        name="M5 range break",
        slug="m5-range-break",
        detector_tag="range_break",
        narrative=(
            "Price has been respecting a band and closes beyond it. Take the break in the "
            "direction it left, not the one you hoped for."
        ),
        rules=(*_common("range_break"), PlaybookRule(code="no_chase", required=True, ord=10)),
    ),
    Playbook(
        id="pb-false-break",
        name="M5 false break",
        slug="m5-false-break",
        detector_tag="false_break",
        narrative=(
            "A break of the band that closed back inside. The failure is the signal, and it "
            "points the other way from the break."
        ),
        rules=(
            *_common("false_break"),
            PlaybookRule(code="waited_for_retest", required=True, ord=10),
        ),
    ),
    Playbook(
        id="pb-buildup",
        name="M5 buildup break",
        slug="m5-buildup-break",
        detector_tag="buildup",
        narrative=(
            "Bars tightening against a level. Trade the release, and only when the spread still "
            "leaves room for the move to pay."
        ),
        rules=(
            *_common("buildup"),
            PlaybookRule(code="plan_before_fire", required=True, ord=10),
        ),
    ),
    Playbook(
        id="pb-ema-pullback",
        name="M5 pullback to the 20 EMA",
        slug="m5-ema-pullback",
        detector_tag="ema_pullback",
        narrative=(
            "A trend that comes back to its own average. The 20 EMA is where you join it, not "
            "where you predict it turns."
        ),
        rules=(
            *_common("ema_pullback"),
            PlaybookRule(code="waited_for_retest", required=True, ord=10),
        ),
    ),
    Playbook(
        id="pb-range-fade",
        name="M5 range hold",
        slug="m5-range-hold",
        detector_tag="range",
        narrative=(
            "Price respecting the band and not leaving it. The edges are the trade; the middle "
            "is where accounts go to die."
        ),
        rules=(
            # A range has no side, so `with_trend` is graded but not required here.
            PlaybookRule(code="named_setup", ord=0),
            PlaybookRule(code="setup_matches", params={"detector_tag": "range"}, ord=1),
            PlaybookRule(code="with_trend", required=False, ord=2),
            PlaybookRule(code="ema_distance", params={"max_atr": 1.0}, ord=3),
            PlaybookRule(code="spread_under_cap", ord=4),
            PlaybookRule(code="event_guard", params={"seconds": 900}, ord=5),
            PlaybookRule(code="no_chase", required=True, ord=10),
        ),
    ),
)


def starter_playbooks() -> tuple[Playbook, ...]:
    return STARTERS
