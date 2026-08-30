"""The Process Score. Every axis is process-side; none of them is about money."""

from __future__ import annotations

import pytest

from apps.gateway.method import score as S

W = {"adherence": 0.30, "selectivity": 0.25, "risk_discipline": 0.20,
     "preparation": 0.15, "review": 0.10}


def inputs(**over) -> S.ScoreInputs:
    return S.ScoreInputs(**over)


# -- what is deliberately not an input ---------------------------------------


def test_no_axis_reads_money_or_tilt():
    fields = set(S.ScoreInputs.__dataclass_fields__)
    for forbidden in ("pnl", "net_pnl", "win_rate", "profit_factor", "r_multiple",
                      "tilt", "tilt_score", "balance", "equity"):
        assert forbidden not in fields, forbidden


def test_the_five_axes_are_the_plan_s_five():
    assert S.AXES == ("adherence", "selectivity", "risk_discipline",
                      "preparation", "review")


# -- vacuous axes ------------------------------------------------------------


def test_a_zero_trade_evening_drops_the_trade_axes(caplog):
    """Scoring them 0 punishes standing down; scoring them 100 is free points."""
    result = S.compute(inputs(fires=0, pre_check_in=True, playbook_selected=True), W)
    assert "adherence" in result.na
    assert "risk_discipline" in result.na
    # And no zero spoke: the axis has no value at all.
    by_key = {a.key: a for a in result.axes}
    assert by_key["adherence"].value is None
    assert by_key["adherence"].reason == "no trades"


def test_dropped_weight_redistributes():
    """Preparation alone should carry the whole score, not 15% of it."""
    result = S.compute(inputs(fires=0, pre_check_in=True, playbook_selected=True,
                              post_check_in=True), W)
    assert result.total == pytest.approx(100.0)


def test_standing_down_correctly_can_still_score_well():
    """The product's stated goal: a good evening on a dead tape."""
    result = S.compute(inputs(fires=0, pre_check_in=True, playbook_selected=True,
                              post_check_in=True, stand_downs=3), W)
    assert result.total > 90


def test_an_evening_with_nothing_at_all_scores_zero_not_a_crash():
    result = S.compute(inputs(), W)
    assert result.total >= 0
    assert len(result.na) >= 2


# -- adherence ---------------------------------------------------------------


def test_adherence_is_rules_passed_over_rules_evaluated():
    result = S.compute(inputs(fires=3, required_passed=9, required_evaluated=12), W)
    by_key = {a.key: a for a in result.axes}
    assert by_key["adherence"].value == pytest.approx(75.0)


# -- selectivity -------------------------------------------------------------


def test_selectivity_is_vacuous_without_a_sentinel():
    """Phase 4 supplies opportunity quality. Guessing it would be worse than
    saying nothing."""
    result = S.compute(inputs(fires=2, opportunity_quality=None), W)
    assert "selectivity" in result.na


def test_trading_the_expected_amount_scores_full():
    # OQ 0.5 over trades_max 6 -> expected 3, band 2-4.
    for fires in (2, 3, 4):
        result = S.compute(inputs(fires=fires, opportunity_quality=0.5), W)
        by_key = {a.key: a for a in result.axes}
        assert by_key["selectivity"].value == pytest.approx(100.0), fires


def test_overtrading_a_dead_tape_costs_the_axis():
    # OQ 0 -> expected 0, band 0-1. Six fires is five outside.
    result = S.compute(inputs(fires=6, opportunity_quality=0.0), W)
    by_key = {a.key: a for a in result.axes}
    assert by_key["selectivity"].value == pytest.approx(0.0)


def test_undertrading_a_live_tape_costs_it_too():
    result = S.compute(inputs(fires=0, opportunity_quality=1.0), W)
    by_key = {a.key: a for a in result.axes}
    # expected 6, band 5-7, zero fires is five below.
    assert by_key["selectivity"].value == pytest.approx(0.0)


def test_decline_credit_rewards_standing_down():
    plain = S.compute(inputs(fires=5, opportunity_quality=0.0), W)
    credited = S.compute(inputs(fires=5, opportunity_quality=0.0, stand_downs=2), W)
    by_plain = {a.key: a for a in plain.axes}["selectivity"].value
    by_credit = {a.key: a for a in credited.axes}["selectivity"].value
    assert by_credit == pytest.approx(by_plain + 10)


def test_decline_credit_caps_so_cancels_cannot_be_farmed():
    result = S.compute(inputs(fires=6, opportunity_quality=0.0, stand_downs=99), W)
    by_key = {a.key: a for a in result.axes}
    assert by_key["selectivity"].value == pytest.approx(S.DECLINE_CREDIT_MAX)


def test_selectivity_never_exceeds_one_hundred():
    result = S.compute(inputs(fires=3, opportunity_quality=0.5, stand_downs=99), W)
    by_key = {a.key: a for a in result.axes}
    assert by_key["selectivity"].value == pytest.approx(100.0)


# -- supported degradation ---------------------------------------------------


def test_unavailable_voice_drops_the_memo_items_rather_than_punishing():
    """Voice off, or no usable microphone, is a supported degradation."""
    without = S.compute(inputs(fires=0, pre_check_in=True, playbook_selected=True,
                               voice_available=False), W)
    by_key = {a.key: a for a in without.axes}
    memo = [i for i in by_key["preparation"].items if i.key == "memo"][0]
    assert memo.ok is None
    assert "voice unavailable" in memo.note
    assert by_key["preparation"].value == pytest.approx(100.0)


def test_available_voice_that_was_skipped_is_a_genuine_miss():
    result = S.compute(inputs(fires=0, pre_check_in=True, playbook_selected=True,
                              voice_available=True, memos_tonight=0), W)
    by_key = {a.key: a for a in result.axes}
    memo = [i for i in by_key["preparation"].items if i.key == "memo"][0]
    assert memo.ok is False
    assert by_key["preparation"].value < 100


def test_a_first_session_is_not_failed_for_having_nothing_to_replay():
    result = S.compute(inputs(fires=0, post_check_in=True,
                              replayable_trades_exist=False), W)
    by_key = {a.key: a for a in result.axes}
    replay = [i for i in by_key["review"].items if i.key == "replay"][0]
    assert replay.ok is None
    assert by_key["review"].value == pytest.approx(100.0)


def test_a_zero_trade_review_uses_trade_independent_items():
    result = S.compute(inputs(fires=0, post_check_in=True), W)
    by_key = {a.key: a for a in result.axes}
    keys = {i.key for i in by_key["review"].items}
    assert "memos" not in keys      # the "most trades" ratio needs trades
    assert "post_check_in" in keys


# -- review with trades ------------------------------------------------------


def test_review_wants_memos_on_most_trades():
    good = S.compute(inputs(fires=3, trades_with_memo=2, voice_available=True,
                            post_check_in=True, replays_opened=1,
                            checklists_answered=3, checklists_available=3), W)
    by_key = {a.key: a for a in good.axes}
    assert by_key["review"].value == pytest.approx(100.0)

    thin = S.compute(inputs(fires=3, trades_with_memo=1, voice_available=True,
                            post_check_in=True, replays_opened=1,
                            checklists_answered=3, checklists_available=3), W)
    assert {a.key: a for a in thin.axes}["review"].value < 100


def test_the_message_shape():
    msg = S.compute(inputs(fires=0, pre_check_in=True), W).as_message()
    assert set(msg) == {"axes", "total", "na", "weightsVersion"}
    # An n/a axis is absent from `axes`, so the radar draws a dashed ring
    # rather than a zero spoke.
    assert not set(msg["axes"]) & set(msg["na"])
