"""R is defined once. These tests are what stops a second definition appearing."""

from __future__ import annotations

import pytest

from broker.conversion import AssetGraph
from broker.volume import SymbolSpec, lots_to_volume
from risk.r import r_at_entry, r_multiple

USD, JPY, XAU = 1, 3, 4
ASSETS = {USD: "USD", JPY: "JPY", XAU: "XAU"}

GOLD = SymbolSpec(symbol_id=41, name="XAUUSD", digits=2, pip_position=1, lot_size=10_000,
                  min_volume=100, step_volume=100, max_volume=1_000_000,
                  base_asset_id=XAU, quote_asset_id=USD)
USDJPY = SymbolSpec(symbol_id=4, name="USDJPY", digits=3, pip_position=2, lot_size=10_000_000,
                    min_volume=100_000, step_volume=100_000, max_volume=100_000_000,
                    base_asset_id=USD, quote_asset_id=JPY)
GRAPH = AssetGraph(assets=ASSETS, symbols={GOLD.symbol_id: GOLD, USDJPY.symbol_id: USDJPY})


def test_gold_risk_is_units_times_stop_distance_in_usd() -> None:
    """0.01 lots = 1 ounce; a $2.00 stop is $2.00 of risk. Identity conversion."""
    record = r_at_entry(
        volume=lots_to_volume(0.01, GOLD), entry=2000.00, stop=1998.00, spec=GOLD,
        graph=GRAPH, prices={}, ts_ms=1_700_000_000_000, r_unit_usd=20.0,
    )
    assert record.r_usd == pytest.approx(2.00)
    assert record.method == "stop"
    assert record.units == pytest.approx(1.0)
    assert record.conversion is not None and record.conversion.source == "identity"


def test_usdjpy_risk_converts_yen_to_usd_at_the_entry_rate() -> None:
    """1000 units with a 0.150 yen stop is 150 JPY, which is $1.00 at USDJPY 150."""
    volume = 1000 * 100  # 1000 units, expressed in cents of units
    record = r_at_entry(
        volume=volume, entry=150.000, stop=149.850, spec=USDJPY,
        graph=GRAPH, prices={USDJPY.symbol_id: 150.0}, ts_ms=1_700_000_000_000, r_unit_usd=20.0,
    )
    assert record.r_usd == pytest.approx(1.00)
    assert record.conversion is not None
    assert record.conversion.rate == pytest.approx(1 / 150)


def test_the_conversion_audit_travels_with_the_trade() -> None:
    """Rate, chain, source, and timestamp are stored, so last week's R keeps last week's rate."""
    record = r_at_entry(
        volume=100_000, entry=150.000, stop=149.850, spec=USDJPY,
        graph=GRAPH, prices={USDJPY.symbol_id: 150.0}, ts_ms=1_700_000_000_000, r_unit_usd=20.0,
    )
    row = record.as_row()
    assert row["r_rate_chain"] == "JPY -> USD"
    assert row["r_rate_source"] == "USDJPY"
    assert row["r_rate_ts"] == 1_700_000_000_000
    assert row["r_method"] == "stop"


def test_no_stop_at_entry_falls_back_to_the_policy_r() -> None:
    """The one case where R is a policy number — and it is recorded as one."""
    record = r_at_entry(
        volume=lots_to_volume(0.01, GOLD), entry=2000.00, stop=None, spec=GOLD,
        graph=GRAPH, prices={}, ts_ms=1, r_unit_usd=20.0,
    )
    assert record.r_usd == 20.0
    assert record.method == "fallback"
    assert record.conversion is None
    assert record.as_row()["r_stop_distance"] is None


def test_a_stop_at_the_entry_price_is_refused() -> None:
    with pytest.raises(ValueError, match="sits at the entry"):
        r_at_entry(volume=100, entry=2000.0, stop=2000.0, spec=GOLD, graph=GRAPH,
                   prices={}, ts_ms=1, r_unit_usd=20.0)


def test_r_multiple_reads_both_ways() -> None:
    assert r_multiple(40.0, 20.0) == pytest.approx(2.0)
    assert r_multiple(-20.0, 20.0) == pytest.approx(-1.0)
    with pytest.raises(ValueError, match="must be positive"):
        r_multiple(10.0, 0.0)
