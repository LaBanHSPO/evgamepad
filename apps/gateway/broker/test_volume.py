"""Volume, price scaling, and quote-to-USD conversion.

The numbers here come from documented protocol semantics (volume in cents of units, prices in
1/100000) and not from IC Markets. `test_ctrader.py` holds the fixture-backed test that closes
the remaining gap once a real `SymbolById` dump is captured.
"""

from __future__ import annotations

import pytest

from broker.conversion import AssetGraph, ConversionError
from broker.volume import (
    SymbolSpec,
    VolumeError,
    lots_to_volume,
    relative_distance,
    scale_price,
    unscale_price,
    volume_to_lots,
    volume_to_units,
)

USD, EUR, JPY, XAU, GBP = 1, 2, 3, 4, 5
ASSETS = {USD: "USD", EUR: "EUR", JPY: "JPY", XAU: "XAU", GBP: "GBP"}


def spec(name: str, base: int, quote: int, **kw: int) -> SymbolSpec:
    defaults = dict(
        symbol_id=abs(hash(name)) % 1000,
        name=name,
        digits=5,
        pip_position=4,
        lot_size=10_000_000,
        min_volume=100_000,
        step_volume=100_000,
        max_volume=100_000_000,
        base_asset_id=base,
        quote_asset_id=quote,
    )
    defaults.update(kw)
    return SymbolSpec(**defaults)  # type: ignore[arg-type]


GOLD = spec("XAUUSD", XAU, USD, symbol_id=41, digits=2, pip_position=1,
            lot_size=10_000, min_volume=100, step_volume=100, max_volume=1_000_000)
EURUSD = spec("EURUSD", EUR, USD, symbol_id=1)
USDJPY = spec("USDJPY", USD, JPY, symbol_id=4, digits=3, pip_position=2)


def test_lots_convert_through_lot_size_not_through_a_guess() -> None:
    assert lots_to_volume(0.01, GOLD) == 100
    assert lots_to_volume(0.10, GOLD) == 1000
    assert lots_to_volume(1.0, EURUSD) == 10_000_000
    assert volume_to_lots(100, GOLD) == pytest.approx(0.01)


def test_protocol_volume_is_cents_of_units() -> None:
    """0.01 lots of a 100-unit contract is 1 unit — the quantity R is measured on."""
    assert volume_to_units(lots_to_volume(0.01, GOLD)) == pytest.approx(1.0)
    assert volume_to_units(lots_to_volume(1.0, EURUSD)) == pytest.approx(100_000.0)


def test_size_rounds_down_to_the_broker_step() -> None:
    """A player never gets more size than they asked for."""
    stepped = spec("STEP", EUR, USD, lot_size=10_000_000, min_volume=100_000, step_volume=300_000)
    assert lots_to_volume(0.05, stepped) == 300_000  # 500_000 raw -> one whole step


def test_a_size_the_broker_would_refuse_is_a_reject_not_a_resize() -> None:
    with pytest.raises(VolumeError, match="below minVolume"):
        lots_to_volume(0.001, GOLD)
    with pytest.raises(VolumeError, match="above maxVolume"):
        lots_to_volume(1000.0, GOLD)
    with pytest.raises(VolumeError, match="must be positive"):
        lots_to_volume(0, GOLD)


def test_an_inconsistent_symbol_spec_is_refused_on_construction() -> None:
    with pytest.raises(VolumeError, match="minVolume"):
        spec("BAD", EUR, USD, min_volume=500, max_volume=100)
    with pytest.raises(VolumeError, match="lot_size must be positive"):
        spec("BAD", EUR, USD, lot_size=0)


def test_prices_scale_by_one_hundred_thousand() -> None:
    assert scale_price(123_000) == pytest.approx(1.23)
    assert unscale_price(1.23) == 123_000
    assert relative_distance(2000.00, 1998.00) == 200_000
    with pytest.raises(VolumeError, match="at the entry price"):
        relative_distance(2000.0, 2000.0)


def test_usd_quoted_symbols_convert_by_identity() -> None:
    graph = AssetGraph(assets=ASSETS, symbols={s.symbol_id: s for s in (GOLD, EURUSD, USDJPY)})
    audit = graph.quote_to_usd(GOLD.quote_asset_id, {}, ts_ms=1)
    assert audit.rate == 1.0
    assert audit.source == "identity"


def test_jpy_converts_to_usd_through_the_usdjpy_leg() -> None:
    """1 JPY is 1/150 USD when USDJPY trades at 150 — the inverse of the quoted price."""
    graph = AssetGraph(assets=ASSETS, symbols={s.symbol_id: s for s in (GOLD, EURUSD, USDJPY)})
    audit = graph.quote_to_usd(JPY, {USDJPY.symbol_id: 150.0}, ts_ms=1_700_000_000_000)
    assert audit.rate == pytest.approx(1 / 150)
    assert audit.chain == ("JPY", "USD")
    assert "USDJPY" in audit.source
    assert audit.ts_ms == 1_700_000_000_000


def test_a_conversion_with_no_price_is_refused_rather_than_guessed() -> None:
    graph = AssetGraph(assets=ASSETS, symbols={USDJPY.symbol_id: USDJPY})
    with pytest.raises(ConversionError, match="no path"):
        graph.quote_to_usd(JPY, {}, ts_ms=1)


def test_an_unknown_quote_asset_is_refused() -> None:
    graph = AssetGraph(assets=ASSETS, symbols={GOLD.symbol_id: GOLD})
    with pytest.raises(ConversionError, match="unknown quote asset"):
        graph.quote_to_usd(999, {}, ts_ms=1)
