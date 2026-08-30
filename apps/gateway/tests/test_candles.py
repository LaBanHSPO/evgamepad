"""Chart bars: local aggregation, and the delta-encoded history from cTrader."""

from __future__ import annotations

import pytest

from apps.gateway.api.candles import Bar, CandleBook, bucket, payload

T0 = 1_700_000_000  # a round second
MS = T0 * 1000


def test_buckets_align_to_the_timeframe():
    assert bucket(1_700_000_123, "M1") == 1_700_000_100
    assert bucket(1_700_000_123, "M5") == 1_700_000_100
    assert bucket(1_700_000_400, "M5") == 1_700_000_400


def test_ticks_inside_one_bucket_build_one_bar():
    book = CandleBook(["M1"])
    for i, px in enumerate([2340.0, 2341.5, 2339.0, 2340.5]):
        book.on_price("XAUUSD", px, MS + i * 1000)
    bar = book.forming("XAUUSD", "M1")
    assert bar is not None
    assert (bar.o, bar.h, bar.l, bar.c) == (2340.0, 2341.5, 2339.0, 2340.5)
    assert bar.closed is False


def test_crossing_a_boundary_closes_the_bar_and_opens_the_next():
    book = CandleBook(["M1"])
    book.on_price("XAUUSD", 2340.0, MS)
    closed = book.on_price("XAUUSD", 2345.0, MS + 61_000)

    assert [tf for tf, _ in closed] == ["M1"]
    assert closed[0][1].closed is True
    assert closed[0][1].c == 2340.0
    assert book.forming("XAUUSD", "M1").o == 2345.0


def test_one_tick_can_close_several_timeframes():
    book = CandleBook(["M1", "M5"])
    book.on_price("XAUUSD", 2340.0, MS)
    closed = book.on_price("XAUUSD", 2345.0, MS + 3_600_000)
    assert sorted(tf for tf, _ in closed) == ["M1", "M5"]


def test_only_closed_bars_are_returned():
    """The forming bar changes on every tick; pushing it here would make the
    chart a second quote-rate stream on the order socket."""
    book = CandleBook(["M1"])
    for i in range(50):
        assert book.on_price("XAUUSD", 2340.0 + i * 0.01, MS + i * 100) == []


def test_an_out_of_order_tick_does_not_corrupt_a_published_bar():
    book = CandleBook(["M1"])
    book.on_price("XAUUSD", 2340.0, MS)
    book.on_price("XAUUSD", 2350.0, MS + 120_000)
    book.on_price("XAUUSD", 9999.0, MS + 30_000)  # late arrival
    assert book.forming("XAUUSD", "M1").h == 2350.0


def test_history_ends_with_the_forming_bar():
    """So the chart's right edge is live rather than a timeframe behind."""
    book = CandleBook(["M1"])
    book.on_price("XAUUSD", 2340.0, MS)
    book.on_price("XAUUSD", 2345.0, MS + 61_000)
    history = book.history("XAUUSD", "M1")
    assert len(history) == 2
    assert history[-1].closed is False


def test_the_ring_is_bounded():
    book = CandleBook(["M1"], max_bars=10)
    for i in range(40):
        book.on_price("XAUUSD", 2340.0, MS + i * 61_000)
    assert len(book.history("XAUUSD", "M1")) <= 11  # 10 closed + forming


def test_seeding_is_idempotent():
    """The history endpoint is rate-limited, and re-seeding would also discard
    bars built since the seed."""
    book = CandleBook(["M5"])
    book.seed("XAUUSD", "M5", [Bar(T0, 1, 2, 0.5, 1.5)])
    book.seed("XAUUSD", "M5", [Bar(T0, 9, 9, 9, 9), Bar(T0 + 300, 9, 9, 9, 9)])
    history = book.history("XAUUSD", "M5")
    assert len(history) == 1
    assert history[0].o == 1
    assert book.is_seeded("XAUUSD", "M5")


def test_seeded_bars_are_marked_closed():
    book = CandleBook(["M5"])
    book.seed("XAUUSD", "M5", [Bar(T0, 1, 2, 0.5, 1.5)])
    assert book.history("XAUUSD", "M5")[0].closed is True


def test_payload_sends_milliseconds():
    """Every other timestamp in the protocol is ms; the chart converts once."""
    p = payload("XAUUSD", "M5", Bar(T0, 1, 2, 0.5, 1.5, closed=True))
    assert p["ts"] == T0 * 1000
    assert p["closed"] is True
    assert p["sym"] == "XAUUSD"


# -- history from the broker ------------------------------------------------


async def test_trendbars_decode_the_delta_encoding():
    """ProtoOATrendbar sends `low` absolute and open/high/close as offsets
    above it. Reading deltaOpen as a price draws a chart pinned near zero."""
    from apps.gateway.tests.test_ctrader import started

    broker, _ = await started()
    bars = await broker.trendbars("XAUUSD", "M5", count=50)
    assert bars

    for ts, o, h, lo, c in bars:
        assert ts > 0
        # Gold trades near 2340, not near 0 -- which is what a raw delta reads as.
        assert 1000 < o < 5000, o
        assert lo <= min(o, c) and h >= max(o, c)
        assert lo <= h


async def test_trendbars_come_back_in_time_order():
    from apps.gateway.tests.test_ctrader import started

    broker, _ = await started()
    bars = await broker.trendbars("XAUUSD", "M5", count=30)
    assert [b[0] for b in bars] == sorted(b[0] for b in bars)


async def test_an_unresolved_symbol_is_refused():
    from apps.gateway.broker.base import BrokerFault
    from apps.gateway.tests.test_ctrader import started

    broker, _ = await started()
    with pytest.raises(BrokerFault, match="not a resolved symbol"):
        await broker.trendbars("BTCUSD")


async def test_an_unsupported_period_is_refused():
    from apps.gateway.broker.base import BrokerFault
    from apps.gateway.tests.test_ctrader import started

    broker, _ = await started()
    with pytest.raises(BrokerFault, match="trendbar period"):
        await broker.trendbars("XAUUSD", "M7")
