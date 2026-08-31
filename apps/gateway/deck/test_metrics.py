"""Deck metrics on fixture months.

The two behaviours worth defending: a quiet evening is never scored as a failure, and a Sharpe
below the sample threshold is refused rather than printed.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from deck.metrics import (
    ADHERENCE_RULES,
    GATEWAY_ADHERENCE_RULES,
    PROCESS_ADHERENCE_RULES,
    Fire,
    SessionRow,
    adherence_for,
    average_r,
    by_setup,
    evaluate_fire,
    max_drawdown,
    month_over_month,
    opportunity_verdict,
    outcome_month,
    process_month,
    profit_factor,
    returns_series,
    rule_origin,
    sharpe,
    win_rate,
)
from risk.rules import OPEN_RULES


def ms(year: int, month: int, day: int) -> int:
    return int(datetime(year, month, day, 18, 0, tzinfo=UTC).timestamp() * 1000)


def fire(**over) -> Fire:
    base = dict(
        cid="01ABC", session_id="S-1", symbol="XAUUSD", setup_tag="range_break",
        lots=0.01, max_lots=0.10, inside_window=True, positions_at_fire=0, max_positions=1,
        seconds_to_high_impact=None, r_multiple=1.0, pnl_usd=20.0, closed_at=ms(2026, 9, 1),
    )
    base.update(over)
    return Fire(**base)  # type: ignore[arg-type]


def session(**over) -> SessionRow:
    base = dict(
        session_id="S-1", opened_at=ms(2026, 9, 1), closed_at=ms(2026, 9, 1) + 3600,
        equity_open=10_000.0, equity_close=10_100.0, pre_rating=4, post_rating=4,
        stood_down_count=0, opportunity_quality=0.8,
    )
    base.update(over)
    return SessionRow(**base)  # type: ignore[arg-type]


def month_of(count: int, *, year: int = 2026, month: int = 9, step: float = 0.005) -> list[SessionRow]:
    return [
        session(session_id=f"S-{i}", opened_at=ms(year, month, (i % 28) + 1),
                equity_open=10_000.0, equity_close=10_000.0 * (1 + step * (1 if i % 3 else -1)))
        for i in range(count)
    ]


# -- adherence reuses the gateway's own rules -----------------------------------------


def test_the_gateway_rules_are_imported_not_re_listed() -> None:
    """One rule set. The deck cannot claim a rule the gateway never had."""
    gateway_ids = {rule.id for rule in OPEN_RULES}
    for rule_id in GATEWAY_ADHERENCE_RULES:
        assert rule_id in gateway_ids, f"`{rule_id}` is not a gateway rule"


def test_process_rules_are_labelled_as_not_enforced() -> None:
    """The deck may hold you to habits the gate never blocked — but it must say which."""
    for rule_id in GATEWAY_ADHERENCE_RULES:
        assert rule_origin(rule_id) == "gateway"
    for rule_id in PROCESS_ADHERENCE_RULES:
        assert rule_origin(rule_id) == "process"
    assert set(ADHERENCE_RULES) == set(GATEWAY_ADHERENCE_RULES) | set(PROCESS_ADHERENCE_RULES)


def test_a_clean_fire_satisfies_every_rule() -> None:
    assert all(evaluate_fire(fire()).values())


@pytest.mark.parametrize(
    ("over", "broken"),
    [
        ({"inside_window": False}, "session_window"),
        ({"lots": 0.5}, "max_lots"),
        ({"positions_at_fire": 1}, "max_positions"),
        ({"setup_tag": None}, "named_setup"),
        ({"seconds_to_high_impact": 300}, "event_guard"),
    ],
)
def test_each_rule_can_fail_on_its_own(over: dict, broken: str) -> None:
    result = evaluate_fire(fire(**over))
    assert result[broken] is False
    assert sum(1 for value in result.values() if not value) == 1


def test_adherence_is_the_fraction_of_clean_fires() -> None:
    fires = [fire(), fire(lots=0.5), fire(), fire()]
    result = adherence_for(fires)
    assert result.score == pytest.approx(0.75)
    assert result.fires == 4
    assert result.clean_fires == 3
    assert result.by_rule["max_lots"] == pytest.approx(0.75)
    assert result.by_rule["session_window"] == 1.0


def test_an_evening_with_no_fires_has_no_score_rather_than_a_zero() -> None:
    """Scoring a stand-down at zero would punish the exact behaviour this deck rewards."""
    result = adherence_for([])
    assert result.score is None
    assert result.has_data is False


# -- a quiet evening is a result ------------------------------------------------------


def test_a_dead_tape_with_no_trades_reads_as_discipline() -> None:
    assert "standing down was the read" in opportunity_verdict(0.1, fires=0)
    assert "thin tape" in opportunity_verdict(0.5, fires=0)
    assert "worth reviewing" in opportunity_verdict(0.9, fires=0)
    assert opportunity_verdict(0.1, fires=3) == "traded"
    assert "no opportunity reading" in opportunity_verdict(None, fires=0)


def test_declined_trades_are_counted_per_session_so_months_compare() -> None:
    sessions = [session(session_id="S-1", stood_down_count=4),
                session(session_id="S-2", stood_down_count=2)]
    summary = process_month(sessions, [])
    assert summary["declined"] == 6
    assert summary["declinedRate"] == pytest.approx(3.0)


# -- outcome --------------------------------------------------------------------------


def test_session_return_comes_from_the_account_not_from_fills() -> None:
    assert session(equity_open=10_000.0, equity_close=10_100.0).session_return == pytest.approx(0.01)
    # No account snapshot means no return — not a zero that would pollute the series.
    assert session(equity_close=None).session_return is None
    assert session(equity_open=None).session_return is None
    assert returns_series([session(equity_close=None), session()]) == [pytest.approx(0.01)]


def test_profit_factor_average_r_and_win_rate() -> None:
    fires = [fire(pnl_usd=40.0, r_multiple=2.0), fire(pnl_usd=-20.0, r_multiple=-1.0),
             fire(pnl_usd=10.0, r_multiple=0.5)]
    assert profit_factor(fires) == pytest.approx(2.5)
    assert average_r(fires) == pytest.approx(0.5)
    assert win_rate(fires) == pytest.approx(2 / 3)


def test_metrics_are_none_rather_than_zero_when_there_is_nothing_to_measure() -> None:
    assert profit_factor([]) is None
    assert average_r([]) is None
    assert win_rate([]) is None
    assert max_drawdown([]) is None


def test_max_drawdown_walks_the_compounded_curve() -> None:
    sessions = [
        session(session_id="a", opened_at=ms(2026, 9, 1), equity_close=11_000.0),   # +10%
        session(session_id="b", opened_at=ms(2026, 9, 2), equity_close=8_000.0),    # -20%
        session(session_id="c", opened_at=ms(2026, 9, 3), equity_close=10_500.0),   # +5%
    ]
    assert max_drawdown(sessions) == pytest.approx(-0.2, abs=1e-9)


def test_setups_are_broken_out_and_untagged_fires_are_kept() -> None:
    fires = [fire(setup_tag="false_break", pnl_usd=30.0), fire(setup_tag=None, pnl_usd=-10.0)]
    table = by_setup(fires)
    assert set(table) == {"false_break", "untagged"}
    assert table["false_break"]["trades"] == 1


# -- the Sharpe guard -----------------------------------------------------------------


def test_a_short_month_refuses_to_print_a_sharpe() -> None:
    """Two sessions is noise. The deck says how far off it is instead of guessing."""
    result = sharpe(month_of(2), min_sessions=30)
    assert result.enough is False
    assert result.value is None
    assert result.display == "not enough sessions yet"
    assert "2 of 30" in result.note


def test_the_sample_size_travels_with_the_number() -> None:
    result = sharpe(month_of(40), min_sessions=30)
    assert result.enough is True
    assert result.value is not None
    assert result.sessions == 40
    assert "40 sessions" in result.note


def test_a_flat_return_series_is_refused_rather_than_dividing_by_zero() -> None:
    flat = [session(session_id=f"S-{i}", opened_at=ms(2026, 9, (i % 28) + 1),
                    equity_open=10_000.0, equity_close=10_000.0) for i in range(40)]
    result = sharpe(flat, min_sessions=30)
    assert result.enough is False
    assert "no variation" in result.note


# -- month over month -----------------------------------------------------------------


def test_this_month_against_last_month_on_the_process_figures() -> None:
    last = [session(session_id=f"A-{i}", opened_at=ms(2026, 8, i + 1), stood_down_count=1)
            for i in range(5)]
    this = [session(session_id=f"B-{i}", opened_at=ms(2026, 9, i + 1), stood_down_count=3)
            for i in range(5)]
    fires = [fire(session_id="A-0", lots=0.5), fire(session_id="B-0")]

    result = month_over_month(last + this, fires,
                              ["adherence", "declinedRate", "checkinAverage"], process_month)
    assert result["month"] == "2026-09"
    assert result["previousMonth"] == "2026-08"
    assert result["delta"]["declinedRate"] == pytest.approx(2.0)
    assert result["delta"]["adherence"] == pytest.approx(1.0), "0.0 last month, 1.0 this month"


def test_a_first_month_has_no_previous_and_says_so_rather_than_showing_zero() -> None:
    result = month_over_month(month_of(3), [], ["adherence"], process_month)
    assert result["previousMonth"] is None
    assert result["previous"] is None
    assert result["delta"]["adherence"] is None


def test_the_outcome_month_compounds_the_session_returns() -> None:
    sessions = [session(session_id="a", opened_at=ms(2026, 9, 1), equity_close=10_100.0),
                session(session_id="b", opened_at=ms(2026, 9, 2), equity_close=10_100.0)]
    summary = outcome_month(sessions, [])
    assert summary["returnPct"] == pytest.approx(1.01 * 1.01 - 1)
    assert summary["sessions"] == 2
