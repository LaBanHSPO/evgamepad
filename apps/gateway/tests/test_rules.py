"""Risk rules, and the one property everything else rests on: a close or a
panic is never gated.

Phase 7 moves this registry into method/rules.py. That extraction must be
behaviour-preserving, and this file is the regression gate for it.
"""

from __future__ import annotations

import pytest

from apps.gateway.protocol.catalog import SAFETY_EXIT_TYPES
from apps.gateway.risk import rules
from apps.gateway.risk.rules import OPEN_ONLY, Decision, RiskContext, evaluate

NOW = 1_700_000_000_000


def ctx(intent="intent.open", **kw) -> RiskContext:
    base = dict(
        now_ms=NOW, intent_type=intent, clutch=True, armed_at=NOW - 200,
        session_open=True, last_client_ms=NOW - 100,
    )
    base.update(kw)
    return RiskContext(**base)


def test_a_clean_open_passes():
    assert evaluate(ctx()) == Decision(allowed=True)


@pytest.mark.parametrize(
    "reason,kw",
    [
        ("no_clutch", {"clutch": False}),
        ("stale_arm", {"armed_at": NOW - 60_000}),
        ("stale_arm", {"armed_at": None}),
        ("stale_arm", {"armed_at": NOW + 5_000}),
        ("duplicate_cid", {"cid_seen": True}),
        ("unknown_symbol", {"symbol_known": False}),
        ("session_closed", {"session_open": False}),
        ("locked", {"locked": True}),
        ("dead_man", {"last_client_ms": NOW - 4_000}),
        ("max_positions", {"open_positions": 1, "max_positions": 1}),
        ("max_daily_loss", {"day_loss_usd": 250.0, "max_daily_loss_usd": 200.0}),
        ("max_lots", {"lots_ok": False}),
        ("spread_too_wide", {"spread": 1.2, "max_spread": 0.8}),
        ("rate_limited", {"last_order_ms": NOW - 500}),
        ("cooldown", {"cooldown_until_ms": NOW + 60_000}),
    ],
)
def test_each_rule_refuses_with_its_own_reason(reason, kw):
    d = evaluate(ctx(**kw))
    assert not d.allowed
    assert d.reason == reason
    assert d.rule_id


def test_a_fire_just_after_clutch_down_still_sends():
    """The clutch on the intent authorises the fire. A ping 50ms old that said
    clutch=false must not retroactively refuse it."""
    d = evaluate(ctx(armed_at=NOW - 50, last_client_ms=NOW - 50))
    assert d.allowed


@pytest.mark.parametrize("intent", sorted(SAFETY_EXIT_TYPES))
@pytest.mark.parametrize(
    "kw",
    [
        {"session_open": False},
        {"locked": True},
        {"last_client_ms": NOW - 30_000},
        {"day_loss_usd": 10_000.0, "max_daily_loss_usd": 200.0},
        {"open_positions": 99, "max_positions": 1},
        {"cooldown_until_ms": NOW + 3_600_000},
        {"spread": 99.0, "max_spread": 0.1},
        {"last_order_ms": NOW},
    ],
)
def test_close_and_panic_are_exempt_from_every_open_only_gate(intent, kw):
    assert evaluate(ctx(intent, **kw)).allowed


def test_close_and_panic_still_need_the_clutch():
    """Exempt from *risk* gates, not from the confirm contract. A stray frame
    must not flatten the account."""
    for intent in SAFETY_EXIT_TYPES:
        assert not evaluate(ctx(intent, clutch=False)).allowed
        assert not evaluate(ctx(intent, armed_at=None)).allowed


def test_no_open_only_rule_can_ever_reach_a_safety_exit():
    """Structural, not a spot check: asserted at boot too."""
    for rule in rules.RULES:
        if rule.applies_to == OPEN_ONLY:
            assert not (rule.applies_to & SAFETY_EXIT_TYPES)
    assert rules.safety_exits_are_ungated()


def test_cooldown_is_open_only_so_phase_nine_cannot_gate_an_exit():
    assert rules.RULES_BY_ID["risk.cooldown"].applies_to == OPEN_ONLY
    assert "cooldown" in rules.open_only_reasons()


def test_registry_is_exported_for_phase_six_adherence():
    """Phase 6 scores adherence against the rules that were enforced, so the
    registry has to be enumerable and stably identified."""
    ids = [r.id for r in rules.RULES]
    assert len(ids) == len(set(ids))
    assert all(r.consequence in {"risk", "playbook"} for r in rules.RULES)
    assert all(r.title for r in rules.RULES)


def test_rules_are_evaluated_in_a_stable_order():
    """Same situation, same reason, every time."""
    bad = ctx(clutch=False, session_open=False, locked=True)
    assert {evaluate(bad).reason for _ in range(20)} == {"no_clutch"}
