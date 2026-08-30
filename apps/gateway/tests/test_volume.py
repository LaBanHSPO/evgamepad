"""Volume and price scaling. A wrong scale on gold is a margin call on 0.01."""

from __future__ import annotations

import pytest

from apps.gateway.broker import fixtures
from apps.gateway.broker.volume import (
    VolumeError,
    lots_to_volume,
    price_distance_to_relative,
    relative_to_price_distance,
    scale_price,
    unscale_price,
    volume_to_lots,
    volume_to_units,
)


def test_gold_minimum_lot_is_one_ounce():
    # 0.01 lot of gold is 1 ounce. If this ever comes out as 1000 the HUD is
    # about to send a margin call.
    v = lots_to_volume(0.01, fixtures.XAUUSD)
    assert v == 100
    assert volume_to_units(v) == 1
    assert volume_to_lots(v, fixtures.XAUUSD) == pytest.approx(0.01)


def test_one_fx_lot_is_a_hundred_thousand_units():
    v = lots_to_volume(1.0, fixtures.EURUSD)
    assert volume_to_units(v) == 100_000


def test_lots_round_trip_for_every_symbol():
    for spec in fixtures.SPECS.values():
        for lots in (0.01, 0.05, 0.10):
            v = lots_to_volume(lots, spec)
            assert volume_to_lots(v, spec) == pytest.approx(lots)


def test_volume_snaps_to_the_broker_step():
    spec = fixtures.EURUSD
    # 0.015 lots is not on a 0.01 grid for this step; it snaps, it does not
    # silently truncate to a smaller order.
    v = lots_to_volume(0.015, spec)
    assert v % spec.step_volume == 0


def test_below_minimum_is_refused_not_clamped():
    with pytest.raises(VolumeError) as exc:
        lots_to_volume(0.0001, fixtures.XAUUSD)
    assert exc.value.reason == "lot_step"


def test_above_broker_max_is_refused():
    with pytest.raises(VolumeError) as exc:
        lots_to_volume(500.0, fixtures.XAUUSD)
    assert exc.value.reason == "max_lots"


def test_zero_and_negative_lots_refused():
    for bad in (0, -0.01):
        with pytest.raises(VolumeError):
            lots_to_volume(bad, fixtures.XAUUSD)


def test_price_scaling_matches_the_documented_example():
    """`123000` -> `1.23` at 1/100000."""
    assert scale_price(123_000, fixtures.EURUSD) == pytest.approx(1.23)
    assert unscale_price(1.23, fixtures.EURUSD) == 123_000


def test_price_scaling_respects_digits():
    assert scale_price(233_456_789, fixtures.XAUUSD) == pytest.approx(2334.57)
    assert scale_price(115_432_100, fixtures.USDJPY) == pytest.approx(1154.321)


def test_relative_distance_units():
    assert price_distance_to_relative(2.00) == 200_000
    assert relative_to_price_distance(200_000) == pytest.approx(2.00)
    assert price_distance_to_relative(0.0010) == 100
