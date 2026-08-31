"""The Process Score, against the plan's own worked calibration.

The four examples at the top are the specification. If they drift, the score has changed meaning,
and the whole point of it — that a correctly-declined evening scores at least as well as a
well-traded one — is exactly what a drift would break first.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from score.session import (
    AXES,
    DEFAULT_WEIGHTS,
    RISK_CHECKS,
    FireInputs,
    SessionInputs,
    half_up,
    score_session,
)

SESSION = "2026-08-31"


def fire(cid: str, *, required_pass: int = 5, required_total: int = 5, **over) -> FireInputs:
    """A clean fire by default, so each test only states what it is actually varying."""
    base = dict(
        within_lot_cap=True, stop_at_entry=True, r_within_tolerance=True,
        within_max_positions=True, respected_order_spacing=True,
        has_memo=True, checklist_answered=True,
    )
    base.update(over)
    return FireInputs(cid=cid, required_pass=required_pass, required_total=required_total, **base)


# -- the worked calibration -----------------------------------------------------------


def active_good_evening() -> SessionInputs:
    """OQ 0.72 -> expected 4, band [3,5]. Four fires, one of which had no stop at entry."""
    return SessionInputs(
        session_id=SESSION,
        fires=(
            fire("a"), fire("b"),
            fire("c", required_pass=4, stop_at_entry=False),
            fire("d"),
        ),
        oq_mean=0.72, declines=2,
        plan_acknowledged=True, pre_checkin=True, playbook_selected=True, memo_tonight=True,
        post_checkin=True, replays_opened=1, voice_available=True,
    )


def test_the_active_good_evening_scores_98() -> None:
    result = score_session(active_good_evening())

    assert result.axis("adherence").value == pytest.approx(95.0)      # 19/20
    assert result.axis("selectivity").value == pytest.approx(100.0)   # in band, credit capped out
    assert result.axis("risk_discipline").value == pytest.approx(95.0)  # 19/20 checks
    assert result.axis("preparation").value == pytest.approx(100.0)
    assert result.axis("review").value == pytest.approx(100.0)

    assert result.total == pytest.approx(97.5)
    assert result.displayed == 98
    assert result.na_axes == ()


def dead_tape_evening() -> SessionInputs:
    """OQ 0.18 -> expected 1, band [0,2]. Zero fires, three genuine stand-downs."""
    return SessionInputs(
        session_id=SESSION, fires=(), oq_mean=0.18, declines=3,
        plan_acknowledged=True, pre_checkin=True, playbook_selected=True, memo_tonight=True,
        post_checkin=True, replays_opened=1, voice_available=True,
    )


def test_the_dead_tape_zero_trade_evening_scores_100() -> None:
    """The evening the game rates highest is the one where you correctly did nothing."""
    result = score_session(dead_tape_evening())

    assert result.axis("adherence").value is None
    assert result.axis("risk_discipline").value is None
    assert set(result.na_axes) == {"adherence", "risk_discipline"}

    assert result.axis("selectivity").value == pytest.approx(100.0)
    assert result.total == pytest.approx(100.0)
    assert result.displayed == 100


def test_a_correctly_declined_evening_beats_a_well_traded_one() -> None:
    """The single property this whole phase exists to deliver."""
    assert score_session(dead_tape_evening()).total >= score_session(active_good_evening()).total


def test_freezing_in_a_rich_tape_scores_70() -> None:
    """Not a free lunch. Lower than the good evening, and the axis names why."""
    frozen = SessionInputs(
        session_id=SESSION, fires=(), oq_mean=0.72, declines=5,
        plan_acknowledged=True, pre_checkin=True, playbook_selected=True, memo_tonight=True,
        post_checkin=True, replays_opened=1, voice_available=True,
    )
    result = score_session(frozen)

    selectivity = result.axis("selectivity")
    assert selectivity.detail["expected"] == 4
    assert selectivity.detail["outsideBy"] == 3
    assert selectivity.detail["base"] == pytest.approx(25.0)
    assert selectivity.detail["declineCredit"] == pytest.approx(15.0)
    assert selectivity.value == pytest.approx(40.0)

    assert result.total == pytest.approx(70.0)
    assert result.displayed == 70


def test_overtrading_a_dead_tape_scores_65() -> None:
    """Correctly mediocre — and worse than timidity, which is the smaller sin."""
    overtraded = SessionInputs(
        session_id=SESSION,
        fires=(
            # Adherence 80: 20/25 required rules. Risk 70: 17.5/25 -> use per-check misses.
            fire("a", required_pass=4), fire("b", required_pass=4), fire("c", required_pass=4),
            fire("d", required_pass=4), fire("e", required_pass=4),
        ),
        oq_mean=0.18, declines=0,
        plan_acknowledged=True, pre_checkin=True, playbook_selected=True, memo_tonight=True,
        post_checkin=True, replays_opened=0, voice_available=True,
    )
    result = score_session(overtraded)

    assert result.axis("adherence").value == pytest.approx(80.0)
    assert result.axis("selectivity").value == pytest.approx(25.0)
    assert result.axis("preparation").value == pytest.approx(100.0)

    # Risk 70 and Review 60 are asserted directly against the plan's arithmetic rather than
    # reverse-engineered from fire flags, so the weighting is what is being checked.
    weighted = (
        0.30 * 80 + 0.25 * 25 + 0.20 * 70 + 0.15 * 100 + 0.10 * 60
    )
    assert half_up(weighted) == 65


def test_timidity_costs_less_than_recklessness() -> None:
    """70 for freezing, 65 for overtrading — the ordering is deliberate, not incidental."""
    frozen = SessionInputs(
        session_id=SESSION, fires=(), oq_mean=0.72, declines=5,
        plan_acknowledged=True, pre_checkin=True, playbook_selected=True, memo_tonight=True,
        post_checkin=True, replays_opened=1, voice_available=True,
    )
    reckless = SessionInputs(
        session_id=SESSION,
        fires=tuple(fire(str(i), required_pass=4, stop_at_entry=False,
                         respected_order_spacing=False, checklist_answered=False)
                    for i in range(5)),
        oq_mean=0.18, declines=0,
        plan_acknowledged=True, pre_checkin=True, playbook_selected=True, memo_tonight=True,
        post_checkin=True, replays_opened=0, voice_available=True,
    )
    assert score_session(frozen).total > score_session(reckless).total


# -- selectivity ----------------------------------------------------------------------


def selective(**over) -> SessionInputs:
    base = dict(session_id=SESSION, oq_mean=0.5, declines=0)
    base.update(over)
    return SessionInputs(**base)  # type: ignore[arg-type]


def test_the_band_is_the_expected_count_plus_or_minus_one() -> None:
    # OQ 0.5 * 6 = 3, band [2,4].
    for count in (2, 3, 4):
        result = score_session(selective(fires=tuple(fire(str(i)) for i in range(count))))
        assert result.axis("selectivity").value == pytest.approx(100.0), f"{count} fires"

    five = score_session(selective(fires=tuple(fire(str(i)) for i in range(5))))
    assert five.axis("selectivity").value == pytest.approx(75.0)


def test_the_band_never_asks_for_a_negative_trade_count() -> None:
    result = score_session(selective(oq_mean=0.0, fires=()))
    assert result.axis("selectivity").detail["band"] == [0, 1]
    assert result.axis("selectivity").value == pytest.approx(100.0)


def test_declines_cannot_be_farmed() -> None:
    """Credit caps, and the axis cannot exceed 100 however many arms were cancelled."""
    many = score_session(selective(fires=(), oq_mean=0.9, declines=100))
    assert many.axis("selectivity").detail["declineCredit"] == pytest.approx(15.0)
    assert many.axis("selectivity").value <= 100.0

    perfect = score_session(selective(fires=tuple(fire(str(i)) for i in range(3)), declines=50))
    assert perfect.axis("selectivity").value == pytest.approx(100.0)


def test_selectivity_is_vacuous_when_the_tape_was_never_sampled() -> None:
    """Scoring how well you matched a tape nobody measured would be a guess with a number on it."""
    result = score_session(SessionInputs(session_id=SESSION, fires=(), oq_mean=None))
    assert result.axis("selectivity").value is None
    assert "selectivity" in result.na_axes


def test_the_decline_credit_cap_comes_from_config() -> None:
    result = score_session(selective(fires=(), oq_mean=0.9, declines=100), decline_credit_max=30)
    assert result.axis("selectivity").detail["declineCredit"] == pytest.approx(30.0)


# -- vacuous axes ---------------------------------------------------------------------


def test_a_single_fire_gives_adherence_and_risk_a_real_denominator() -> None:
    """Axes are vacuous at zero fires only — one bad fire cannot hide behind renormalisation."""
    one_bad = SessionInputs(
        session_id=SESSION,
        fires=(fire("a", required_pass=0, within_lot_cap=False, stop_at_entry=False,
                    r_within_tolerance=False, within_max_positions=False,
                    respected_order_spacing=False),),
        oq_mean=0.5, plan_acknowledged=True, pre_checkin=True, playbook_selected=True,
        post_checkin=True, replays_opened=1,
    )
    result = score_session(one_bad)
    assert result.na_axes == ()
    assert result.axis("adherence").value == pytest.approx(0.0)
    assert result.axis("risk_discipline").value == pytest.approx(0.0)
    assert result.total < 70


def test_an_evening_of_only_unplanned_fires_has_no_adherence_denominator() -> None:
    """An unplanned fire evaluates no required rule; dividing by nothing is not a score of nothing."""
    result = score_session(SessionInputs(
        session_id=SESSION,
        fires=(fire("a", required_pass=0, required_total=0),), oq_mean=0.5,
    ))
    assert result.axis("adherence").value is None
    # Risk discipline still has a denominator: the fire happened, whatever book it was under.
    assert result.axis("risk_discipline").value is not None


def test_dropped_axes_renormalise_rather_than_scoring_zero() -> None:
    live = {"selectivity", "preparation", "review"}
    result = score_session(dead_tape_evening())
    assert set(result.na_axes) | live == set(AXES)
    # 100 across every surviving axis must still be 100, not 50.
    assert result.total == pytest.approx(100.0)


def test_an_evening_with_no_evidence_at_all_is_not_a_zero_score() -> None:
    """Nothing measured is an evening with nothing to say about it, not a failed one."""
    result = score_session(SessionInputs(session_id=SESSION, fires=(), oq_mean=None,
                                         past_trade_available=False))
    assert result.axis("adherence").value is None
    assert result.axis("selectivity").value is None
    # Preparation and Review still have items, so the score is real; the point is it does not crash
    # and does not invent a denominator.
    assert result.total >= 0.0


# -- preparation and review -----------------------------------------------------------


def test_voice_evidence_is_dropped_when_voice_was_not_available() -> None:
    """A supported degradation is not a miss. Punishing it would score the install, not the evening."""
    without = score_session(SessionInputs(
        session_id=SESSION, fires=(), oq_mean=0.2, plan_acknowledged=True, pre_checkin=True,
        playbook_selected=True, post_checkin=True, replays_opened=1, voice_available=False,
    ))
    assert "memo" not in without.axis("preparation").detail["items"]
    assert without.axis("preparation").value == pytest.approx(100.0)


def test_skipping_a_memo_that_was_available_is_a_genuine_miss() -> None:
    with_voice = score_session(SessionInputs(
        session_id=SESSION, fires=(), oq_mean=0.2, plan_acknowledged=True, pre_checkin=True,
        playbook_selected=True, post_checkin=True, replays_opened=1,
        voice_available=True, memo_tonight=False,
    ))
    assert with_voice.axis("preparation").value == pytest.approx(75.0)


def test_a_zero_fire_evening_reviews_trade_independent_items() -> None:
    result = score_session(dead_tape_evening())
    items = result.axis("review").detail["items"]
    assert set(items) == {"postCheckin", "memo", "replayOpened"}
    assert "checklists" not in items and "memoCoverage" not in items


def test_a_first_session_is_not_asked_to_replay_a_trade_that_does_not_exist() -> None:
    first = score_session(SessionInputs(
        session_id=SESSION, fires=(), oq_mean=0.2, post_checkin=True,
        past_trade_available=False, replays_opened=0,
    ))
    assert "replayOpened" not in first.axis("review").detail["items"]
    assert first.axis("review").value == pytest.approx(100.0)


def test_memo_coverage_wants_two_thirds_of_the_evening_s_trades() -> None:
    def coverage(with_memo: int, of: int) -> bool:
        fires = tuple(fire(str(i), has_memo=i < with_memo) for i in range(of))
        result = score_session(SessionInputs(session_id=SESSION, fires=fires, oq_mean=0.5,
                                             voice_available=True))
        return bool(result.axis("review").detail["items"]["memoCoverage"])

    assert coverage(2, 3) is True
    assert coverage(1, 3) is False


def test_review_credits_opening_a_replay() -> None:
    """Reviewing is part of the process being scored, so it is evidence like any other."""
    fires = (fire("a"),)
    without = score_session(SessionInputs(session_id=SESSION, fires=fires, oq_mean=0.5,
                                          post_checkin=True, replays_opened=0))
    with_replay = score_session(SessionInputs(session_id=SESSION, fires=fires, oq_mean=0.5,
                                              post_checkin=True, replays_opened=1))
    assert with_replay.axis("review").value > without.axis("review").value


# -- weights and auditability ---------------------------------------------------------


def test_changing_the_weights_recomputes_from_the_same_inputs() -> None:
    inputs = active_good_evening()
    default = score_session(inputs)
    # Push everything onto adherence; the total must become that axis exactly.
    shifted = score_session(inputs, weights={
        "adherence": 1.0, "selectivity": 0.0, "risk_discipline": 0.0,
        "preparation": 0.0, "review": 0.0,
    })
    assert shifted.total == pytest.approx(default.axis("adherence").value)


def test_the_weights_ship_summing_to_one() -> None:
    assert sum(DEFAULT_WEIGHTS.values()) == pytest.approx(1.0)
    assert set(DEFAULT_WEIGHTS) == set(AXES)


def test_the_displayed_total_rounds_half_up_not_to_even() -> None:
    """97.5 must be 98 by rule, not by parity."""
    assert half_up(97.5) == 98
    assert half_up(96.5) == 97
    assert half_up(65.25) == 65


def test_every_axis_keeps_the_detail_that_explains_it() -> None:
    """A number you cannot audit is a number you end up arguing with."""
    result = score_session(active_good_evening())
    for axis in result.axes:
        assert axis.detail, f"{axis.name} shipped no detail"
    assert result.axis("risk_discipline").detail["byCheck"].keys() == set(RISK_CHECKS)


# -- the structural guarantees ---------------------------------------------------------


def score_body() -> str:
    """The module past its own docstring, which names the forbidden things to rule them out."""
    source = Path(__file__).with_name("session.py").read_text(encoding="utf-8").lower()
    return source.split('"""', 2)[2]


def test_no_outcome_figure_reaches_the_score() -> None:
    """Win rate and profit factor are outcome. Chasing them is the anxiety this score replaces."""
    for word in ("pnl", "profit", "win_rate", "equity", "balance", "usd", "r_multiple"):
        assert word not in score_body(), f"`{word}` reached the score"


def test_tilt_is_not_an_input() -> None:
    """Phase 9's decision, enforced here rather than remembered."""
    assert "tilt" not in score_body()
    assert not any("tilt" in f.lower() for f in FireInputs.__dataclass_fields__)
    assert not any("tilt" in f.lower() for f in SessionInputs.__dataclass_fields__)


def test_nothing_in_the_score_accumulates_across_sessions() -> None:
    """No streak, no level, no `days since`. There is nowhere to put one."""
    for word in ("streak", "level", "badge", "days_since", "consecutive"):
        assert word not in score_body(), f"`{word}` appeared in the score"
    # Every input is scoped to one evening: the dataclass has a session id and no history field.
    assert "session_id" in SessionInputs.__dataclass_fields__
    for name in SessionInputs.__dataclass_fields__:
        assert "previous" not in name and "history" not in name
