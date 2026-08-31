"""The registry, and the guarantee that a playbook rule can never block a trade."""

from __future__ import annotations

import pytest

from method.rules import REGISTRY, RuleContext, get, manual_codes, rules_for
from risk.rules import OPEN_RULES, evaluate_open


def ctx(**over) -> RuleContext:
    base = dict(
        now_ms=1_788_000_000_000, symbol="XAUUSD", lots=0.01, clutch=True,
        session_open=True, session_label="tue 20:00", allowed_symbols=frozenset({"XAUUSD"}),
        positions_open=0, max_positions=1, max_lots=0.10,
        day_loss_usd=0.0, max_day_loss_usd=200.0,
        seconds_since_last_order=10.0, min_seconds_between_orders=2.0,
        heartbeat_age_s=0.5, heartbeat_dead_s=3.0,
    )
    base.update(over)
    return RuleContext(**base)  # type: ignore[arg-type]


# -- the structural guarantee ---------------------------------------------------------


def test_a_playbook_rule_can_never_reject_an_intent() -> None:
    """The failure mode this test exists for: the journal quietly becoming a trade blocker."""
    playbook_codes = {rule.code for rule in rules_for("playbook")}
    gate_codes = {rule.id for rule in OPEN_RULES}
    assert playbook_codes and gate_codes
    assert playbook_codes.isdisjoint(gate_codes), "a playbook rule reached the gate"


def test_no_playbook_rule_carries_a_rejection_reason() -> None:
    """A rule with no wire reason cannot produce a reject, whatever a later phase does."""
    for rule in rules_for("playbook"):
        assert rule.reason is None, f"`{rule.code}` has a rejection reason it must not have"


def test_every_failing_playbook_rule_still_lets_the_trade_through() -> None:
    """Fail all of them at once; the gate is still open."""
    hostile = ctx(setup_tag=None, setup_side="buy", side="sell", price=2100.0, ema20=2000.0,
                  atr=1.0, spread=5.0, spread_cap=0.8, seconds_to_high_impact=10)
    for rule in rules_for("playbook"):
        if rule.kind == "auto":
            assert rule.check(hostile, {"detector_tag": "range_break"}).ok is False

    decision = evaluate_open(hostile)
    assert decision.allowed is True, "playbook failures must not reject"


def test_the_gate_is_built_from_the_registry_rather_than_re_listed() -> None:
    """`risk/rules.py` contains no rule logic of its own — only registry calls."""
    from pathlib import Path

    source = Path(__file__).resolve().parents[1].joinpath("risk", "rules.py").read_text()
    assert "rules_for(\"risk\")" in source
    # Nothing in the gate module compares a context field itself any more.
    assert "ctx.lots" not in source
    assert "ctx.positions_open" not in source
    assert "heartbeat_age_s <" not in source


def test_the_risk_subset_still_bites() -> None:
    assert evaluate_open(ctx(clutch=False)).reason == "no_clutch"
    assert evaluate_open(ctx(lots=0.5)).reason == "max_lots"
    assert evaluate_open(ctx()).allowed is True


# -- individual rules -----------------------------------------------------------------


def test_setup_matches_the_playbooks_own_detector() -> None:
    rule = get("setup_matches")
    assert rule.check(ctx(setup_tag="range_break"), {"detector_tag": "range_break"}).ok
    result = rule.check(ctx(setup_tag="buildup"), {"detector_tag": "range_break"})
    assert result.ok is False
    assert result.actual == "buildup"
    assert result.expected == "range_break"
    # A playbook that names no detector does not fail on one.
    assert rule.check(ctx(setup_tag=None), {}).ok


def test_not_chasing_is_measured_in_atr_from_the_average() -> None:
    rule = get("ema_distance")
    close = rule.check(ctx(price=2001.0, ema20=2000.0, atr=1.0), {"max_atr": 1.5})
    assert close.ok is True
    assert close.actual == "1.00 ATR"

    far = rule.check(ctx(price=2003.0, ema20=2000.0, atr=1.0), {"max_atr": 1.5})
    assert far.ok is False
    assert far.actual == "3.00 ATR"


def test_a_rule_with_no_data_is_unknown_rather_than_failed() -> None:
    """No chart yet is not the same as a broken rule, and must not be scored as one."""
    result = get("ema_distance").check(ctx(price=None), {})
    assert result.unknown is True
    result = get("spread_under_cap").check(ctx(spread=None), {})
    assert result.unknown is True


def test_trading_against_the_setup_fails_with_trend() -> None:
    rule = get("with_trend")
    assert rule.check(ctx(setup_side="buy", side="buy"), {}).ok is True
    assert rule.check(ctx(setup_side="buy", side="sell"), {}).ok is False
    # A range has no side; it cannot be traded against.
    assert rule.check(ctx(setup_side="none", side="sell"), {}).ok is True
    assert rule.check(ctx(setup_side=None, side=None), {}).unknown is True


def test_the_event_guard_is_clear_when_nothing_is_coming() -> None:
    rule = get("event_guard")
    assert rule.check(ctx(seconds_to_high_impact=None), {}).ok is True
    assert rule.check(ctx(seconds_to_high_impact=1200), {"seconds": 900}).ok is True
    assert rule.check(ctx(seconds_to_high_impact=300), {"seconds": 900}).ok is False


def test_a_manual_rule_is_unknown_until_the_player_answers() -> None:
    """Skipping the checklist must cost nothing, so an unanswered rule is neither pass nor fail."""
    rule = get("waited_for_retest")
    unanswered = rule.check(ctx(), {})
    assert unanswered.unknown is True
    assert unanswered.ok is False

    assert rule.check(ctx(manual_answers={"waited_for_retest": True}), {}).ok is True
    answered_no = rule.check(ctx(manual_answers={"waited_for_retest": False}), {})
    assert answered_no.ok is False
    assert answered_no.unknown is False


def test_the_checklist_can_only_ask_about_manual_rules() -> None:
    codes = manual_codes()
    assert codes
    for code in codes:
        assert get(code).kind == "manual"
        assert get(code).scope == "playbook"


def test_every_registry_entry_is_reachable_by_its_code() -> None:
    for code, rule in REGISTRY.items():
        assert get(code) is rule


def test_an_unknown_code_is_refused_rather_than_silently_skipped() -> None:
    with pytest.raises(KeyError, match="not a rule"):
        get("invent_a_rule")
