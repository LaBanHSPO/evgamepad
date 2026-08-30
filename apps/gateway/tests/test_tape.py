"""Tape ring, freeze, and the excursion asymmetry that would otherwise be silent."""

from __future__ import annotations

import pytest

from apps.gateway.journal.tape.freeze import (
    excursion,
    freeze,
    in_trade,
    pack_bars,
    unpack_bars,
)
from apps.gateway.journal.tape.ring import Bar, TapeRing

S = 1_700_000_000  # a round second
MS = S * 1000


def px(v: float) -> int:
    return int(round(v * 100_000))


def test_ring_conflates_ticks_into_one_bar_per_second():
    ring = TapeRing(ring_minutes=90, dt_s=1)
    for i in range(20):
        ring.on_tick("XAUUSD", px(2340.0 + i * 0.01), px(2340.2 + i * 0.01),
                     MS + i * 50, digits=2)
    ring.seal_all()
    bars = ring.ring("XAUUSD").bars()
    assert len(bars) == 1
    # n_ticks proves the ring is tapped before the browser conflation. If this
    # is ever 1, the tape has been moved to the wrong side of the conflator.
    assert bars[0].n_ticks == 20
    assert bars[0].bid_o == px(2340.0)
    assert bars[0].bid_c == px(2340.19)
    assert bars[0].bid_h == px(2340.19)


def test_ring_drops_the_oldest_beyond_its_capacity():
    ring = TapeRing(ring_minutes=1, dt_s=1)  # 60 slots
    for i in range(200):
        ring.on_tick("EURUSD", px(1.08), px(1.0801), MS + i * 1000)
    assert len(ring.ring("EURUSD")) <= 61


def test_out_of_order_tick_is_dropped_not_folded_backwards():
    ring = TapeRing()
    ring.on_tick("EURUSD", px(1.0800), px(1.0801), MS)
    ring.on_tick("EURUSD", px(1.0900), px(1.0901), MS + 5000)
    ring.on_tick("EURUSD", px(9.9999), px(9.9999), MS + 1000)  # late arrival
    ring.seal_all()
    assert all(b.bid_h < px(2.0) for b in ring.ring("EURUSD").bars())


def bars_between(low: float, high: float, entry_side: str = "both") -> list[Bar]:
    """Two bars: one that dips to `low`, one that spikes to `high`, with a
    0.20 spread so a side mix-up is visible."""
    return [
        Bar(S, px(low), px(low), px(low), px(low),
            px(low + 0.20), px(low + 0.20), px(low + 0.20), px(low + 0.20), 5),
        Bar(S + 1, px(high), px(high), px(high), px(high),
            px(high + 0.20), px(high + 0.20), px(high + 0.20), px(high + 0.20), 5),
    ]


def test_long_measures_excursion_on_the_bid():
    """A long exits by selling at the bid."""
    e = excursion(bars_between(2338.0, 2344.0), side="buy", entry=2340.0, digits=2)
    assert e.mfe == pytest.approx(4.0)   # 2344.00 bid - 2340.00
    assert e.mae == pytest.approx(-2.0)  # 2338.00 bid - 2340.00


def test_short_measures_excursion_on_the_ask():
    """A short exits by buying at the ask, which is 0.20 higher here. Using the
    bid for both sides would flatter every short by a full spread."""
    e = excursion(bars_between(2338.0, 2344.0), side="sell", entry=2340.0, digits=2)
    assert e.mfe == pytest.approx(1.8)   # 2340.00 - 2338.20 ask
    assert e.mae == pytest.approx(-4.2)  # 2340.00 - 2344.20 ask


def test_long_and_short_do_not_produce_the_same_numbers():
    bars = bars_between(2338.0, 2344.0)
    long_e = excursion(bars, side="buy", entry=2340.0, digits=2)
    short_e = excursion(bars, side="sell", entry=2340.0, digits=2)
    assert long_e != short_e


def test_excursion_is_zero_for_an_empty_window():
    e = excursion([], side="buy", entry=2340.0, digits=2)
    assert (e.mfe, e.mae) == (0.0, 0.0)


def test_excursion_in_r():
    e = excursion(bars_between(2338.0, 2344.0), side="buy", entry=2340.0, digits=2)
    mfe_r, mae_r = e.in_r(2.0)
    assert mfe_r == pytest.approx(2.0)
    assert mae_r == pytest.approx(-1.0)


def test_excursion_uses_only_the_bars_the_position_was_open_for():
    """Pre-roll and post-roll are context for the replay, not risk taken."""
    bars = [
        Bar(S - 10, px(9999.0), px(9999.0), px(9999.0), px(9999.0),
            px(9999.2), px(9999.2), px(9999.2), px(9999.2), 1),
        *bars_between(2338.0, 2344.0),
    ]
    window = in_trade(bars, opened_at_ms=S * 1000, closed_at_ms=(S + 1) * 1000)
    assert len(window) == 2
    assert excursion(window, side="buy", entry=2340.0, digits=2).mfe == pytest.approx(4.0)


def test_pack_round_trips():
    bars = bars_between(2338.0, 2344.0)
    assert unpack_bars(pack_bars(bars)) == bars


def test_a_typical_evening_of_five_trades_stays_small():
    """Success criterion: one evening of five trades adds under ~100 KB."""
    ring = TapeRing()
    for i in range(20 * 60):
        ring.on_tick("XAUUSD", px(2340 + (i % 40) * 0.01),
                     px(2340.2 + (i % 40) * 0.01), MS + i * 1000, digits=2)
    ring.seal_all()
    bars = ring.ring("XAUUSD").bars()
    total = 0
    for n in range(5):
        opened = MS + (n * 120) * 1000
        tape = freeze(
            sym="XAUUSD", bars=bars, opened_at_ms=opened,
            closed_at_ms=opened + 120_000, pre_roll_s=300, post_roll_s=300,
            dt_s=1, digits=2,
        )
        total += len(tape.bars_gz)
    assert total < 100_000, f"{total} bytes of tape for five trades"


def test_a_zero_trade_evening_writes_no_tape():
    """The ring runs all evening; nothing is persisted without a trade."""
    ring = TapeRing()
    for i in range(600):
        ring.on_tick("XAUUSD", px(2340.0), px(2340.2), MS + i * 1000, digits=2)
    assert len(ring.ring("XAUUSD")) > 0
    # No freeze() call happens without a close. Nothing to assert but the
    # absence, which is the point.


def test_short_post_roll_on_shutdown_still_freezes():
    """Shutdown inside the post-roll window must not lose the trade's tape."""
    ring = TapeRing()
    for i in range(60):
        ring.on_tick("XAUUSD", px(2340.0 + i * 0.01), px(2340.2), MS + i * 1000, digits=2)
    ring.seal_all()  # shutdown seals the in-progress bar
    tape = freeze(
        sym="XAUUSD", bars=ring.ring("XAUUSD").bars(),
        opened_at_ms=MS + 10_000, closed_at_ms=MS + 50_000,
        pre_roll_s=300, post_roll_s=300, dt_s=1, digits=2,
    )
    assert tape.n == 60          # the whole ring, which is all that existed
    assert tape.n < tape.to_ts - tape.from_ts  # a short window, stored as such
    assert unpack_bars(tape.bars_gz)[-1].ts_s == S + 59
