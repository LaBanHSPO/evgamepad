"""Open gates reject; exits never do. That asymmetry is the safety property of the whole product."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from risk.rules import (
    OPEN_REJECT_REASONS,
    OPEN_RULES,
    REJECT_COOLDOWN,
    OpenContext,
    evaluate_exit,
    evaluate_open,
)
from risk.session import SessionWindow, market_session

TZ = "Asia/Ho_Chi_Minh"
WINDOW = SessionWindow.from_config(TZ, ["sun", "mon", "tue", "wed", "thu", "fri"], "18:00", "23:30")


def ms(year: int, month: int, day: int, hour: int, minute: int = 0) -> int:
    return int(datetime(year, month, day, hour, minute, tzinfo=ZoneInfo(TZ)).timestamp() * 1000)


def ctx(**over: object) -> OpenContext:
    base = dict(
        now_ms=ms(2026, 9, 1, 20), symbol="XAUUSD", lots=0.01, clutch=True,
        session_open=True, session_label="tue 20:00 Asia/Ho_Chi_Minh",
        allowed_symbols=frozenset({"XAUUSD", "EURUSD"}),
        positions_open=0, max_positions=1, max_lots=0.10,
        day_loss_usd=0.0, max_day_loss_usd=200.0,
        seconds_since_last_order=10.0, min_seconds_between_orders=2.0,
        heartbeat_age_s=0.5, heartbeat_dead_s=3.0,
    )
    base.update(over)
    return OpenContext(**base)  # type: ignore[arg-type]


def test_a_clean_clutched_intent_is_allowed() -> None:
    decision = evaluate_open(ctx())
    assert decision.allowed
    assert decision.reason is None
    assert all(o.passed for o in decision.outcomes)


@pytest.mark.parametrize(
    ("over", "reason"),
    [
        ({"clutch": False}, "no_clutch"),
        ({"heartbeat_age_s": 3.5}, "dead_man"),
        ({"session_open": False}, "session_closed"),
        ({"symbol": "BTCUSD"}, "symbol_not_allowed"),
        ({"positions_open": 1}, "max_positions"),
        ({"lots": 0.5}, "max_lots"),
        ({"day_loss_usd": 200.0}, "daily_loss"),
        ({"seconds_since_last_order": 0.4}, "rate_limited"),
    ],
)
def test_each_gate_rejects_with_its_own_reason(over: dict, reason: str) -> None:
    decision = evaluate_open(ctx(**over))
    assert not decision.allowed
    assert decision.reason == reason


def test_every_outcome_is_reported_even_after_the_first_failure() -> None:
    """The journal records what was evaluated, not just what fired first."""
    decision = evaluate_open(ctx(clutch=False, lots=0.5))
    failed = {o.id for o in decision.outcomes if not o.passed}
    assert failed == {"clutch", "max_lots"}
    # Every enforced rule reports, not just the ones that bit. Counted from the registry so a new
    # gate does not silently stop being reported.
    assert len(decision.outcomes) == len(OPEN_RULES)


def test_exits_are_exempt_from_every_open_gate() -> None:
    """3 s of silence, a blown daily loss, a closed session — a close still goes through."""
    assert evaluate_exit().allowed
    assert evaluate_exit().reason is None
    assert evaluate_exit().outcomes == ()


def test_cooldown_is_reserved_for_phase_nine() -> None:
    """Reserved now so phase 9 adds a gate, not a new wire contract."""
    assert REJECT_COOLDOWN in OPEN_REJECT_REASONS
    assert REJECT_COOLDOWN not in {o.reason for o in evaluate_open(ctx()).outcomes}


def test_all_rules_are_risk_scoped_in_this_phase() -> None:
    """Phase 7 adds playbook-scoped rules; a playbook rule may never reject."""
    assert {o.scope for o in evaluate_open(ctx()).outcomes} == {"risk"}


def test_the_window_is_evaluated_in_the_configured_zone() -> None:
    assert WINDOW.is_open(ms(2026, 9, 1, 20))
    assert not WINDOW.is_open(ms(2026, 9, 1, 17, 59))
    assert not WINDOW.is_open(ms(2026, 9, 1, 23, 30))
    assert not WINDOW.is_open(ms(2026, 9, 5, 20)), "saturday is not a trading day"
    assert "Asia/Ho_Chi_Minh" in WINDOW.describe(ms(2026, 9, 1, 20))


def test_a_window_crossing_midnight_stays_one_window() -> None:
    night = SessionWindow.from_config(TZ, ["mon"], "22:00", "02:00")
    assert night.is_open(ms(2026, 8, 31, 23))
    assert not night.is_open(ms(2026, 8, 31, 21))


def test_trades_are_labelled_with_a_market_session() -> None:
    assert market_session(int(datetime(2026, 9, 1, 9, 0).timestamp() * 1000)) in {
        "asia", "london", "ny", "late"
    }
