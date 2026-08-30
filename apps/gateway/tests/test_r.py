"""R is defined once. These tests are what keeps it that way."""

from __future__ import annotations

import pytest

from apps.gateway.broker import fixtures
from apps.gateway.broker.conversion import AssetGraph, ConversionError
from apps.gateway.broker.volume import lots_to_volume
from apps.gateway.risk.r import lots_for_risk, r_fallback, r_for_entry, r_from_stop

TS = 1_700_000_000_000


def graph(with_jpy: bool = True) -> AssetGraph:
    g = AssetGraph()
    g.set_assets(fixtures.ASSETS)
    for spec in fixtures.SPECS.values():
        g.add_symbol(spec)
    g.observe("EURUSD", 1.0850, 1.0851, TS)
    if with_jpy:
        g.observe("USDJPY", 150.00, 150.02, TS)
    return g


def test_gold_uses_identity_conversion():
    """XAUUSD is quoted in USD. 1 oz with a $2.00 stop is $2.00 of risk."""
    volume = lots_to_volume(0.01, fixtures.XAUUSD)
    r = r_from_stop(
        protocol_volume=volume, entry=2340.00, stop=2338.00,
        spec=fixtures.XAUUSD, graph=graph(), ts=TS,
    )
    assert r.usd == pytest.approx(2.00)
    assert r.source == "stop"
    assert r.rate == 1.0
    assert r.chain == "USD"


def test_usdjpy_converts_jpy_to_usd():
    """0.10 lot = 10_000 units. A 0.15 stop is 1500 JPY, which is NOT 1500 USD.
    At 150.01 mid that is about $10."""
    volume = lots_to_volume(0.10, fixtures.USDJPY)
    r = r_from_stop(
        protocol_volume=volume, entry=150.00, stop=149.85,
        spec=fixtures.USDJPY, graph=graph(), ts=TS,
    )
    assert r.usd == pytest.approx(1500 / 150.01, rel=1e-6)
    assert "1/USDJPY" in r.chain
    assert r.rate_ts == TS


def test_conversion_inputs_are_kept_for_audit():
    volume = lots_to_volume(0.10, fixtures.USDJPY)
    r = r_from_stop(
        protocol_volume=volume, entry=150.00, stop=149.85,
        spec=fixtures.USDJPY, graph=graph(), ts=TS,
    )
    for field in (r.rate, r.chain, r.rate_ts):
        assert field is not None
    assert r.rate == pytest.approx(1 / 150.01)


def test_missing_rate_refuses_rather_than_guessing():
    volume = lots_to_volume(0.10, fixtures.USDJPY)
    with pytest.raises(ConversionError):
        r_from_stop(
            protocol_volume=volume, entry=150.0, stop=149.85,
            spec=fixtures.USDJPY, graph=graph(with_jpy=False), ts=TS,
        )


def test_no_stop_at_entry_falls_back_to_the_configured_unit():
    r = r_for_entry(
        protocol_volume=lots_to_volume(0.01, fixtures.XAUUSD),
        entry=2340.0, stop=None, spec=fixtures.XAUUSD,
        graph=graph(), ts=TS, r_unit_usd=20.0,
    )
    assert r.usd == 20.0
    assert r.source == "r_unit_fallback"


def test_r_is_never_null_so_r_multiple_is_never_null():
    """The closed-trade schema has r_multiple NOT NULL. This is why it can."""
    for stop in (2338.0, None, 2340.0):
        r = r_for_entry(
            protocol_volume=lots_to_volume(0.01, fixtures.XAUUSD),
            entry=2340.0, stop=stop, spec=fixtures.XAUUSD,
            graph=graph(), ts=TS, r_unit_usd=20.0,
        )
        assert r.usd > 0
        assert r.multiple(-r.usd) == pytest.approx(-1.0)


def test_r_multiple_is_signed_pnl_over_r():
    r = r_fallback(20.0, TS)
    assert r.multiple(40.0) == pytest.approx(2.0)
    assert r.multiple(-10.0) == pytest.approx(-0.5)


def test_calculator_is_the_exact_inverse_of_r():
    """Phase 12's position sizer and phase 2's R must agree, or the HUD tells
    the player one thing and the journal records another."""
    lots = lots_for_risk(
        risk_usd=20.0, entry=2340.0, stop=2338.0,
        spec=fixtures.XAUUSD, graph=graph(), ts=TS,
    )
    volume = lots_to_volume(lots, fixtures.XAUUSD)
    back = r_from_stop(
        protocol_volume=volume, entry=2340.0, stop=2338.0,
        spec=fixtures.XAUUSD, graph=graph(), ts=TS,
    )
    assert back.usd == pytest.approx(20.0, rel=1e-6)


def test_calculator_inverse_holds_through_a_conversion():
    lots = lots_for_risk(
        risk_usd=50.0, entry=150.00, stop=149.85,
        spec=fixtures.USDJPY, graph=graph(), ts=TS,
    )
    volume = lots_to_volume(lots, fixtures.USDJPY)
    back = r_from_stop(
        protocol_volume=volume, entry=150.00, stop=149.85,
        spec=fixtures.USDJPY, graph=graph(), ts=TS,
    )
    # Broker step rounding moves it slightly; it must not move it far.
    assert back.usd == pytest.approx(50.0, rel=0.02)
