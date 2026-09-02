"""Sizing, execution scores, Actual vs Plan, the four groups, mistakes, and Process Consistency.

Every number here is deterministic. The tests that matter most are the ones asserting what the
journal *refuses* to say: no counterfactual, no inferred intent, no zero standing in for unknown.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from broker.conversion import AssetGraph
from broker.volume import SymbolSpec
from journal.metrics import (
    CONSISTENCY_WINDOW,
    GROUPS,
    MIN_SESSIONS_FOR_CONSISTENCY,
    TradeFacts,
    actual_vs_plan,
    after_score,
    before_score,
    derive_intent,
    during_score,
    group_counts,
    group_for,
    process_consistency,
    worsened_stops,
)
from journal.mistakes import BUILTIN_CODES, DERIVABLE, FireEvidence, derive, seed_rows, trend
from journal.sizing import risk_from, size_position


def _metrics_code() -> str:
    """`metrics.py` with its comments and docstrings stripped.

    They name the forbidden phrasings in order to forbid them, so a plain substring scan over the
    raw file would fail on the very prose that documents the rule.
    """
    source = Path(__file__).with_name("metrics.py").read_text(encoding="utf-8")
    stripped = re.sub(r'"""[\s\S]*?"""', "", source)
    return re.sub(r"#.*", "", stripped).lower()


USD, JPY, XAU = 1, 3, 4
ASSETS = {USD: "USD", JPY: "JPY", XAU: "XAU"}

GOLD = SymbolSpec(symbol_id=41, name="XAUUSD", digits=2, pip_position=1, lot_size=10_000,
                  min_volume=100, step_volume=100, max_volume=1_000_000,
                  base_asset_id=XAU, quote_asset_id=USD)
USDJPY = SymbolSpec(symbol_id=4, name="USDJPY", digits=3, pip_position=2, lot_size=10_000_000,
                    min_volume=100_000, step_volume=100_000, max_volume=100_000_000,
                    base_asset_id=USD, quote_asset_id=JPY)

GRAPH = AssetGraph(assets=ASSETS, symbols={GOLD.symbol_id: GOLD, USDJPY.symbol_id: USDJPY})
# USDJPY at 150: one JPY is 1/150 USD.
PRICES = {USDJPY.symbol_id: 150.0}


# -- position sizing ------------------------------------------------------------------


def test_a_usd_quoted_symbol_converts_by_identity() -> None:
    """XAUUSD: $200 of risk over a $2 stop is 100 ounces, which is one lot."""
    result = size_position(spec=GOLD, entry=2458.0, stop=2456.0, risk_usd=200.0,
                           graph=GRAPH, prices=PRICES)

    assert result.ok
    assert result.rate == pytest.approx(1.0)
    assert result.requested_lots == pytest.approx(1.0)
    assert result.rounded_lots == pytest.approx(1.0)
    assert result.actual_risk_usd == pytest.approx(200.0)


def test_a_jpy_quoted_symbol_goes_through_the_phase_2_conversion() -> None:
    """USDJPY: the risk is in USD, the stop distance is in JPY, and only the graph joins them."""
    result = size_position(spec=USDJPY, entry=150.00, stop=149.50, risk_usd=200.0,
                           graph=GRAPH, prices=PRICES)

    assert result.ok
    # One JPY is 1/150 USD, so the rate must be that and not 1.0.
    assert result.rate == pytest.approx(1 / 150)
    # units = 200 / (0.5 * 1/150) = 60,000 units = 0.6 lots.
    assert result.requested_lots == pytest.approx(0.6)
    assert result.rate_chain is not None and "JPY" in result.rate_chain


def test_sizing_rounds_down_to_the_broker_step_never_up() -> None:
    """Rounding up would hand back more risk than was asked for — the one forbidden direction."""
    result = size_position(spec=GOLD, entry=2458.0, stop=2456.0, risk_usd=250.0,
                           graph=GRAPH, prices=PRICES)

    assert result.requested_lots == pytest.approx(1.25)
    assert result.rounded_lots == pytest.approx(1.25)  # step is 0.01 lots, so 1.25 is exact

    # A request that lands between steps must land below it.
    fine = size_position(spec=GOLD, entry=2458.0, stop=2456.0, risk_usd=251.0,
                         graph=GRAPH, prices=PRICES)
    assert fine.rounded_lots is not None and fine.rounded_lots <= fine.requested_lots


def test_the_actual_risk_is_recomputed_from_the_rounded_volume() -> None:
    """A calculator that reports the risk you asked for rather than the one you will carry lies."""
    result = size_position(spec=GOLD, entry=2458.0, stop=2456.0, risk_usd=251.0,
                           graph=GRAPH, prices=PRICES)
    assert result.actual_risk_usd is not None
    assert result.actual_risk_usd <= result.risk_usd
    assert result.actual_risk_usd == pytest.approx(result.rounded_lots * 100 * 2.0)


def test_a_percent_needs_an_equity_to_mean_anything() -> None:
    assert risk_from(10_000.0, None, 2.0) == pytest.approx(200.0)
    assert risk_from(None, None, 2.0) is None
    # An explicit USD figure wins over a percent.
    assert risk_from(10_000.0, 50.0, 2.0) == pytest.approx(50.0)


def test_the_cap_lowers_the_size_and_says_so() -> None:
    result = size_position(spec=GOLD, entry=2458.0, stop=2456.0, risk_usd=2000.0,
                           graph=GRAPH, prices=PRICES, max_lots=0.10)
    assert result.rounded_lots == pytest.approx(0.10)
    assert result.capped_at == pytest.approx(0.10)
    assert result.actual_risk_usd is not None and result.actual_risk_usd < 2000.0


def test_a_stop_at_the_entry_is_refused_rather_than_sized() -> None:
    """Not a small risk — an unmeasurable one."""
    result = size_position(spec=GOLD, entry=2458.0, stop=2458.0, risk_usd=200.0,
                           graph=GRAPH, prices=PRICES)
    assert not result.ok
    assert "risk cannot be measured" in (result.reason or "")


def test_a_risk_below_the_brokers_minimum_says_so_rather_than_rounding_to_zero() -> None:
    result = size_position(spec=USDJPY, entry=150.0, stop=149.5, risk_usd=0.10,
                           graph=GRAPH, prices=PRICES)
    assert not result.ok
    assert "minimum" in (result.reason or "")


def test_an_unpriceable_quote_refuses_rather_than_guessing_a_rate_of_one() -> None:
    """Guessing 1.0 would size a JPY trade as if it were a USD one."""
    result = size_position(spec=USDJPY, entry=150.0, stop=149.5, risk_usd=200.0,
                           graph=GRAPH, prices={})
    assert not result.ok
    assert result.rounded_lots is None


# -- execution scores ------------------------------------------------------------------


def test_unknown_inputs_drop_out_instead_of_scoring_zero() -> None:
    """A missing memo would otherwise make the score a measure of what the build supports."""
    partial = TradeFacts(cid="c1", checklist_answered=True, has_memo=None, post_checkin=True,
                         replay_opened=None)
    after = after_score(partial)

    assert after.value == pytest.approx(100.0)
    assert set(after.dropped) == {"memo", "replayOpened"}
    assert set(after.items) == {"checklist", "postCheckin"}


def test_a_captured_miss_is_different_from_an_uncaptured_one() -> None:
    missed = after_score(TradeFacts(cid="c1", checklist_answered=True, has_memo=False))
    absent = after_score(TradeFacts(cid="c1", checklist_answered=True, has_memo=None))

    assert missed.value == pytest.approx(50.0)
    assert absent.value == pytest.approx(100.0)


def test_a_stage_with_nothing_measured_is_none_rather_than_zero() -> None:
    assert before_score(TradeFacts(cid="c1")).value is None


def test_each_stage_reads_its_own_inputs() -> None:
    facts = TradeFacts(
        cid="c1", had_daily_analysis=True, readiness_complete=True, playbook_selected=True,
        grade_clean=False, within_lot_cap=True, stop_at_entry=False, stop_never_worsened=True,
        respected_rules=True, checklist_answered=True, has_memo=True, post_checkin=True,
        replay_opened=True,
    )
    assert before_score(facts).value == pytest.approx(75.0)
    assert during_score(facts).value == pytest.approx(75.0)
    assert after_score(facts).value == pytest.approx(100.0)


# -- actual vs plan --------------------------------------------------------------------


def test_a_stop_moved_further_away_is_the_only_one_counted() -> None:
    """Trailing a stop up on a buy is correct. Counting it as a mistake would punish good practice."""
    trailed = worsened_stops(({"ts": 1, "sl": 2457.0}, {"ts": 2, "sl": 2458.5}),
                             side="buy", original_sl=2456.0)
    assert trailed == []

    widened = worsened_stops(({"ts": 1, "sl": 2454.0},), side="buy", original_sl=2456.0)
    assert len(widened) == 1
    assert widened[0]["from"] == 2456.0 and widened[0]["to"] == 2454.0


def test_the_direction_flips_for_a_sell() -> None:
    worse = worsened_stops(({"ts": 1, "sl": 152.0},), side="sell", original_sl=151.0)
    assert len(worse) == 1
    assert worsened_stops(({"ts": 1, "sl": 150.0},), side="sell", original_sl=151.0) == []


def test_actual_vs_plan_never_claims_the_target_would_have_been_hit() -> None:
    """The tape after your exit is not evidence about a trade you were no longer in."""
    facts = TradeFacts(cid="c1", planned_r=2.0, realised_r=0.6, planned_sl=2456.0,
                       planned_tp=2462.0)
    view = actual_vs_plan(facts, side="buy")

    assert view["deltaR"] == pytest.approx(-1.4)
    assert view["label"] == "Actual vs Plan"
    flat = str(view).lower()
    for claim in ("would have", "theoretical", "missed profit", "could have"):
        assert claim not in flat

    # The same claim, checked against the code rather than one payload: no docstring, comment or
    # string in the module may promise what the market would have done.
    assert "would have" not in _metrics_code()


def test_a_missing_plan_leaves_the_delta_absent_rather_than_zero() -> None:
    view = actual_vs_plan(TradeFacts(cid="c1", realised_r=0.6), side="buy")
    assert view["deltaR"] is None


# -- the four groups -------------------------------------------------------------------


def test_a_clean_planned_fire_defaults_to_planned() -> None:
    intent, by = derive_intent(grade_clean=True, playbook_id="pb-range", confirmed=None)
    assert (intent, by) == ("planned", "derived")


def test_a_dirty_or_unplanned_fire_stays_unknown_until_the_player_says() -> None:
    """The difference between a marginal setup and chasing is not on the chart."""
    assert derive_intent(grade_clean=False, playbook_id="pb-range", confirmed=None)[0] == "unknown"
    assert derive_intent(grade_clean=True, playbook_id=None, confirmed=None)[0] == "unknown"
    assert derive_intent(grade_clean=True, playbook_id="__unplanned__", confirmed=None)[0] == "unknown"


def test_only_the_player_can_assert_revenge() -> None:
    intent, by = derive_intent(grade_clean=False, playbook_id=None, confirmed="revenge")
    assert (intent, by) == ("revenge", "player")


def test_no_combination_of_evidence_ever_derives_impulsive_or_revenge() -> None:
    """Checked across the whole input space, not by reading the source for a word."""
    for clean in (True, False, None):
        for book in ("pb-range", "__unplanned__", None, ""):
            derived, by = derive_intent(grade_clean=clean, playbook_id=book, confirmed=None)
            assert derived in ("planned", "unknown"), f"{clean}/{book} derived {derived}"
            assert by == "derived"


def test_unknown_intent_is_excluded_from_the_chart_rather_than_guessed() -> None:
    counts = group_counts([
        ("planned", 1.2), ("planned", -1.0), ("revenge", -0.8), ("impulsive", 0.4),
        ("unknown", 2.0), ("planned", None),
    ])
    assert counts["groups"] == {
        "planned-win": 1, "planned-loss": 1,
        "impulsive/revenge-loss": 1, "impulsive/revenge-win": 1,
    }
    assert counts["unclassified"] == 2
    assert set(counts["groups"]) == set(GROUPS)


def test_a_trade_with_no_result_yet_belongs_to_no_group() -> None:
    assert group_for("planned", None) is None


# -- mistakes --------------------------------------------------------------------------


def test_the_taxonomy_ships_the_plans_built_ins() -> None:
    for code in ("oversize", "no_initial_sl", "worsened_sl", "early_exit", "chased_entry",
                 "revenge_entry", "event_window", "outside_session", "no_playbook",
                 "skipped_review"):
        assert code in BUILTIN_CODES
    assert len(seed_rows(0)) == len(BUILTIN_CODES)


def test_intent_mistakes_are_never_derivable() -> None:
    """No amount of evidence turns a tape into a state of mind."""
    for code in ("early_exit", "chased_entry", "revenge_entry"):
        assert code not in DERIVABLE


def test_derived_mistakes_come_off_rows_that_prove_them() -> None:
    found = derive(FireEvidence(
        cid="c1", lots=0.5, max_lots=0.1, planned_sl=None, seconds_to_high_impact=60,
        inside_window=False, playbook_id=None, checklist_answered=False, replay_opened=False,
    ))
    assert set(found) == {"oversize", "no_initial_sl", "event_window", "outside_session",
                          "no_playbook", "skipped_review"}


def test_a_clean_fire_derives_nothing() -> None:
    assert derive(FireEvidence(
        cid="c1", lots=0.01, max_lots=0.1, planned_sl=2456.0, seconds_to_high_impact=3600,
        inside_window=True, playbook_id="pb-range", checklist_answered=True, replay_opened=True,
    )) == []


def test_a_missing_cap_is_not_an_oversize() -> None:
    """Treating a null column as a breach would invent a violation that never happened."""
    assert "oversize" not in derive(FireEvidence(cid="c1", lots=99.0, max_lots=None,
                                                 planned_sl=2456.0, playbook_id="pb"))


def test_a_worsened_stop_is_derived_from_the_amendments() -> None:
    found = derive(FireEvidence(cid="c1", planned_sl=2456.0, side="buy", playbook_id="pb",
                                amendments=({"ts": 1, "sl": 2454.0},)))
    assert "worsened_sl" in found


def test_the_trend_counts_and_never_penalises() -> None:
    result = trend([
        {"code": "no_initial_sl", "cid": "a", "source": "auto"},
        {"code": "no_initial_sl", "cid": "b", "source": "auto"},
        {"code": "early_exit", "cid": "a", "source": "player"},
    ], focus="no_initial_sl")

    assert result["mistakes"][0] == {"code": "no_initial_sl", "count": 2, "trades": 2,
                                     "auto": 2, "player": 0}
    assert result["focus"] == "no_initial_sl"
    flat = str(result).lower()
    for word in ("streak", "badge", "penalty applied", "level"):
        assert word not in flat.replace("no streak, badge, or penalty", "")


def test_the_trend_separates_what_was_proved_from_what_was_asserted() -> None:
    result = trend([
        {"code": "early_exit", "cid": "a", "source": "player"},
        {"code": "no_initial_sl", "cid": "a", "source": "auto"},
    ])
    by_code = {m["code"]: m for m in result["mistakes"]}
    assert by_code["early_exit"]["player"] == 1 and by_code["early_exit"]["auto"] == 0
    assert by_code["no_initial_sl"]["auto"] == 1


# -- process consistency ---------------------------------------------------------------


def test_consistency_refuses_a_confident_answer_below_five_sessions() -> None:
    """Four evenings is not a process, it is a week."""
    result = process_consistency([90.0, 85.0, 95.0, 88.0])
    assert result.value is None
    assert result.n == 4
    assert result.reason == "not enough sessions yet"


def test_consistency_rewards_steadiness_over_the_same_average() -> None:
    steady = process_consistency([80.0] * 8)
    swinging = process_consistency([100.0, 60.0] * 4)

    assert steady.mean == pytest.approx(swinging.mean)
    assert steady.value is not None and swinging.value is not None
    assert steady.value > swinging.value


def test_consistency_matches_the_formula_exactly() -> None:
    scores = [100.0, 60.0, 100.0, 60.0, 100.0]
    result = process_consistency(scores)
    # median 100, mean 84, mean |x - median| = 16 -> 0.5*84 + 0.5*(100-16) = 84.
    assert result.mad == pytest.approx(16.0)
    assert result.value == pytest.approx(84.0)


def test_consistency_reads_only_the_latest_window() -> None:
    result = process_consistency([0.0] * 40 + [100.0] * CONSISTENCY_WINDOW)
    assert result.n == CONSISTENCY_WINDOW
    assert result.value == pytest.approx(100.0)


def test_consistency_always_reports_n() -> None:
    for scores in ([], [50.0] * 3, [50.0] * MIN_SESSIONS_FOR_CONSISTENCY):
        assert "n" in process_consistency(scores).payload()


def test_consistency_stays_inside_zero_and_one_hundred() -> None:
    assert process_consistency([0.0, 100.0] * 5).value >= 0.0
    assert process_consistency([100.0] * 10).value <= 100.0
