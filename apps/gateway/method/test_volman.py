"""Volman M5 detectors, on synthetic fixture candles.

The fixtures are geometry we made up to exercise our own detectors. Nothing here reproduces book
text or book examples — the method is cited in the HUD, not copied into the repo.
"""

from __future__ import annotations

import pytest

from method.volman import (
    Candle,
    SetupTracker,
    bias,
    detect,
    detect_false_break,
    ema,
    find_range,
    is_buildup,
)


def bar(ts: int, o: float, h: float, low: float, c: float) -> Candle:
    return Candle(ts=ts, o=o, h=h, low=low, c=c)


def flat_range(count: int = 10, top: float = 2005.0, bottom: float = 2000.0) -> list[Candle]:
    """Bars oscillating inside a clean band."""
    out = []
    for i in range(count):
        high = top - (0.2 if i % 2 else 0.0)
        low = bottom + (0.2 if i % 2 else 0.0)
        out.append(bar(i, (high + low) / 2, high, low, (high + low) / 2))
    return out


def test_the_ema_has_no_warm_up_hole() -> None:
    line = ema([1.0, 2.0, 3.0, 4.0], period=3)
    assert len(line) == 4
    assert line[0] == 1.0
    assert line[-1] == pytest.approx(3.125, abs=1e-3)


def test_bias_reads_close_against_its_own_ema() -> None:
    rising = [bar(i, 100 + i, 100.5 + i, 99.5 + i, 100.4 + i) for i in range(30)]
    assert bias(rising) == "buy"

    falling = [bar(i, 200 - i, 200.5 - i, 199.5 - i, 199.6 - i) for i in range(30)]
    assert bias(falling) == "sell"

    assert bias(flat_range(5)) == "none", "too few bars to have a bias at all"


def test_a_band_of_bars_is_found_as_a_range() -> None:
    box = find_range(flat_range(12))
    assert box is not None
    assert box.top == pytest.approx(2005.0)
    assert box.bottom == pytest.approx(2000.0)
    assert box.bars >= 6


def test_a_trending_run_is_not_a_range() -> None:
    trending = [bar(i, 100 + i, 100.6 + i, 99.4 + i, 100.5 + i) for i in range(20)]
    assert find_range(trending) is None


def test_a_close_beyond_the_band_is_a_range_break() -> None:
    candles = flat_range(10) + [bar(10, 2004.0, 2009.0, 2003.9, 2008.5)]
    tag, box = detect(candles)
    assert tag is not None and box is not None
    assert tag.kind == "range_break"
    assert tag.side == "buy"
    assert tag.level == pytest.approx(box.top)


def test_a_break_that_closes_back_inside_points_the_other_way() -> None:
    """The failed break is the signal, and it points against the break."""
    candles = flat_range(10)
    candles.append(bar(10, 2004.0, 2009.0, 2003.5, 2008.0))   # breaks up
    candles.append(bar(11, 2008.0, 2008.2, 2002.0, 2002.5))   # closes back inside
    box = find_range(candles[:10])
    assert box is not None

    tag = detect_false_break(candles, box)
    assert tag is not None
    assert tag.kind == "false_break"
    assert tag.side == "sell", "a failed upside break is a sell signal"
    assert tag.level == pytest.approx(box.top)


def test_a_failed_downside_break_points_up() -> None:
    candles = flat_range(10)
    candles.append(bar(10, 2001.0, 2001.2, 1996.0, 1996.5))
    candles.append(bar(11, 1996.5, 2003.0, 1996.4, 2002.5))
    box = find_range(candles[:10])
    assert box is not None
    tag = detect_false_break(candles, box)
    assert tag is not None
    assert tag.side == "buy"


def test_shrinking_bars_inside_a_box_read_as_buildup() -> None:
    wide = [bar(i, 2002, 2005, 2000, 2002.5) for i in range(4)]
    tight = [bar(4 + i, 2002.4, 2002.9, 2002.0, 2002.5) for i in range(4)]
    assert is_buildup(wide + tight)
    assert not is_buildup(wide + wide)


def test_a_false_break_outranks_the_breakout_it_invalidates() -> None:
    candles = flat_range(10)
    candles.append(bar(10, 2004.0, 2009.0, 2003.5, 2008.0))
    candles.append(bar(11, 2008.0, 2008.2, 2002.0, 2002.5))
    tag, _ = detect(candles)
    assert tag is not None
    assert tag.kind == "false_break"


def test_a_pullback_to_the_ema_is_tagged_when_there_is_no_range() -> None:
    """A trend that comes back to its own 20 EMA, rather than one that merely keeps going."""
    trending = [bar(i, 100 + i * 0.5, 100.6 + i * 0.5, 99.4 + i * 0.5, 100.5 + i * 0.5)
                for i in range(30)]
    line = ema([c.c for c in trending])
    # One bar that dips back onto the average, which is what a pullback actually looks like.
    trending.append(bar(30, 115.5, 115.6, line[-1] - 0.3, line[-1] + 0.1))

    tag, box = detect(trending)
    assert box is None
    assert tag is not None
    assert tag.kind == "ema_pullback"
    assert tag.side == "buy"


def test_too_few_bars_produce_no_tag_at_all() -> None:
    assert detect(flat_range(3)) == (None, None)


def test_the_tracker_reports_a_setup_being_born_and_dying_once_each() -> None:
    """The socket says `signal.item` when a setup appears or dies, not every tick."""
    tracker = SetupTracker()
    ranging = flat_range(10)

    born = tracker.update(ranging)
    assert [kind for kind, _ in born] == ["born"]
    assert tracker.current is not None and tracker.current.kind == "range"

    assert tracker.update(ranging) == [], "a stable setup is not re-announced"

    broken = ranging + [bar(10, 2004.0, 2009.0, 2003.9, 2008.5)]
    events = tracker.update(broken)
    assert [kind for kind, _ in events] == ["died", "born"]
    assert tracker.current is not None and tracker.current.kind == "range_break"


def test_the_tracker_reports_a_death_when_the_tape_goes_quiet() -> None:
    tracker = SetupTracker()
    tracker.update(flat_range(10))
    events = tracker.update(flat_range(3))
    assert [kind for kind, _ in events] == ["died"]
    assert tracker.current is None
