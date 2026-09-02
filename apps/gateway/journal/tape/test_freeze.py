"""Tape ring, freeze, and the side-of-book asymmetry in MFE/MAE."""

from __future__ import annotations

import pytest

from journal.tape import Bar, TapeRing, excursions, freeze_window, pack_bars, unpack_bars

SCALE = 100_000  # protocol prices are 1/100000


def price(value: float) -> int:
    return int(round(value * SCALE))


def feed(ring: TapeRing, symbol: str, ticks: list[tuple[int, float, float]]) -> None:
    for ts_ms, bid, ask in ticks:
        ring.tick(symbol, bid=price(bid), ask=price(ask), ts_ms=ts_ms)


def test_ticks_fold_into_one_second_bars() -> None:
    ring = TapeRing(ring_minutes=90)
    feed(ring, "XAUUSD", [
        (1_000_000, 2000.0, 2000.3),
        (1_000_400, 2001.0, 2001.4),
        (1_000_900, 1999.5, 1999.8),
        (1_001_200, 2002.0, 2002.2),
    ])
    ring.flush()
    bars = ring.window("XAUUSD", 1000, 1001)
    assert len(bars) == 2
    first = bars[0]
    assert first.n_ticks == 3
    assert first.bid_o == price(2000.0)
    assert first.bid_h == price(2001.0)
    assert first.bid_l == price(1999.5)
    assert first.bid_c == price(1999.5)
    assert first.ask_h == price(2001.4)


def test_the_ring_is_bounded() -> None:
    """90 minutes at 1 Hz, and no more — the ring is RAM, not storage."""
    ring = TapeRing(ring_minutes=1)
    feed(ring, "EURUSD", [(i * 1000, 1.1, 1.1001) for i in range(120)])
    ring.flush()
    assert ring.depth("EURUSD") == 60


def test_an_out_of_order_spot_after_a_reconnect_is_dropped() -> None:
    ring = TapeRing()
    feed(ring, "XAUUSD", [(5_000, 2000.0, 2000.2), (3_000, 1990.0, 1990.2)])
    ring.flush()
    bars = ring.window("XAUUSD", 0, 10)
    assert len(bars) == 1
    assert bars[0].bid_l == price(2000.0), "a stale tick must not widen a committed bar"


def test_a_buy_measures_excursions_on_the_bid() -> None:
    """Entry 2000. Bid reaches 2005 and dips to 1997 — that is the buy's +5 and -3."""
    bars = [
        Bar(1, price(2000), price(2005), price(1997), price(2001),
            price(2000.3), price(2005.3), price(1997.3), price(2001.3), 10)
    ]
    result = excursions(bars, side="buy", entry=2000.0, scale=SCALE)
    assert result.mfe == pytest.approx(5.0)
    assert result.mae == pytest.approx(3.0)


def test_a_sell_measures_excursions_on_the_ask() -> None:
    """Same bar, sell from 2000: the ask's low is the gain, the ask's high is the pain."""
    bars = [
        Bar(1, price(2000), price(2005), price(1997), price(2001),
            price(2000.3), price(2005.3), price(1997.3), price(2001.3), 10)
    ]
    result = excursions(bars, side="sell", entry=2000.0, scale=SCALE)
    assert result.mfe == pytest.approx(2.7), "entry 2000 minus the ask low 1997.3"
    assert result.mae == pytest.approx(5.3), "the ask high 2005.3 minus entry 2000"


def test_reading_a_sell_from_the_bid_would_understate_its_pain() -> None:
    """The regression this asymmetry exists to prevent: the two sides must not agree."""
    bars = [
        Bar(1, price(2000), price(2005), price(1997), price(2001),
            price(2000.3), price(2005.3), price(1997.3), price(2001.3), 10)
    ]
    buy_side = excursions(bars, side="buy", entry=2000.0, scale=SCALE)
    sell_side = excursions(bars, side="sell", entry=2000.0, scale=SCALE)
    assert sell_side.mae > buy_side.mae


def test_an_unknown_side_is_refused() -> None:
    with pytest.raises(ValueError, match="unknown side"):
        excursions([], side="both", entry=1.0, scale=SCALE)


def test_a_window_round_trips_through_the_packed_blob() -> None:
    ring = TapeRing()
    feed(ring, "XAUUSD", [(i * 1000 + 500, 2000 + i * 0.1, 2000.2 + i * 0.1) for i in range(60)])
    ring.flush()
    bars = ring.window("XAUUSD", 0, 60)
    blob, result = freeze_window(bars, side="buy", entry=2000.0, scale=SCALE, dt_s=1)

    header, restored = unpack_bars(blob)
    assert header["n"] == len(bars) == 60
    assert header["dt_s"] == 1
    assert restored[0].bid_o == bars[0].bid_o
    assert restored[-1].ask_c == bars[-1].ask_c
    assert result.mfe > 0


def test_an_evening_of_five_trades_stays_well_under_a_hundred_kilobytes() -> None:
    """Pre-roll 300s + a 5-minute trade + post-roll 300s, five times over."""
    ring = TapeRing()
    feed(ring, "XAUUSD", [(i * 1000 + 500, 2000 + (i % 40) * 0.25, 2000.2 + (i % 40) * 0.25)
                          for i in range(900)])
    ring.flush()
    bars = ring.window("XAUUSD", 0, 900)
    assert len(bars) == 900
    one_trade = len(pack_bars(bars, dt_s=1))
    assert one_trade * 5 < 100_000, f"five trades would be {one_trade * 5} bytes"


def test_a_short_post_roll_on_shutdown_still_freezes() -> None:
    """Shutdown mid-post-roll: freeze whatever post-roll exists rather than losing the window."""
    ring = TapeRing()
    feed(ring, "XAUUSD", [(i * 1000 + 500, 2000.0, 2000.2) for i in range(10)])
    # No flush: the last bar is still open, as it would be at a SIGTERM.
    bars = ring.window("XAUUSD", 0, 100)
    assert len(bars) == 10, "the in-progress bar belongs to the window too"
    blob, _ = freeze_window(bars, side="buy", entry=2000.0, scale=SCALE, dt_s=1)
    assert unpack_bars(blob)[0]["n"] == 10


def test_a_zero_trade_evening_freezes_nothing() -> None:
    ring = TapeRing()
    assert ring.window("XAUUSD", 0, 10) == []
    blob, result = freeze_window([], side="buy", entry=0.0, scale=SCALE, dt_s=1)
    assert unpack_bars(blob)[1] == []
    assert result.mfe == 0.0 and result.mae == 0.0
