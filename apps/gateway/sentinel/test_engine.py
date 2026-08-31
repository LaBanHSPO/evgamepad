"""The sentinel runs with no API key, and a dead tape reads as dead."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from method.volman import Candle
from sentinel.engine import SentinelEngine, band_for, spread_state
from signals.calendar import CalendarCache, currencies_for

NOW = 1_700_000_000_000


def bar(ts: int, o: float, h: float, low: float, c: float) -> Candle:
    return Candle(ts=ts, o=o, h=h, low=low, c=c)


def flat_range(count: int = 10) -> list[Candle]:
    out = []
    for i in range(count):
        high = 2005.0 - (0.2 if i % 2 else 0.0)
        low = 2000.0 + (0.2 if i % 2 else 0.0)
        out.append(bar(i, (high + low) / 2, high, low, (high + low) / 2))
    return out


def engine(**kw) -> SentinelEngine:
    return SentinelEngine(timezone="Asia/Ho_Chi_Minh", spread_caps={"XAUUSD": 0.8}, **kw)


def test_the_strip_updates_with_no_api_key_and_no_network() -> None:
    """The whole point of the sentinel: it never waits on the desk."""
    tick = engine().tick(symbol="XAUUSD", bid=2000.0, ask=2000.3, now_ms=NOW,
                         session_remaining_s=3600, locked=False)
    assert tick.sym == "XAUUSD"
    assert tick.state == "tight"
    assert 0.0 <= tick.quality <= 1.0
    assert tick.payload().keys() == {"sym", "spread", "state", "ts"}


def test_spread_reads_against_the_symbols_own_cap() -> None:
    assert spread_state(0.3, 0.8) == "tight"
    assert spread_state(0.7, 0.8) == "fair"
    assert spread_state(1.2, 0.8) == "wide"


def test_a_dead_tape_scores_worse_than_a_live_one() -> None:
    """Standing down on a dead evening should look like the correct read, not a missed one."""
    dead = engine()
    dead_tick = dead.tick(symbol="XAUUSD", bid=2000.0, ask=2001.5, now_ms=NOW,
                          session_remaining_s=120, locked=False)

    live = engine()
    live.observe("XAUUSD", flat_range(10) + [bar(10, 2004.0, 2009.0, 2003.9, 2008.5)])
    live_tick = live.tick(symbol="XAUUSD", bid=2000.0, ask=2000.2, now_ms=NOW,
                          session_remaining_s=5400, locked=False)

    assert live_tick.quality > dead_tick.quality
    assert dead_tick.quality_band == "dead"
    assert live_tick.quality_band == "live"


def test_every_component_is_reported_so_a_low_score_can_be_explained() -> None:
    tick = engine().tick(symbol="XAUUSD", bid=2000.0, ask=2001.5, now_ms=NOW,
                         session_remaining_s=60, locked=False)
    assert set(tick.components) == {"spread", "setup", "session", "calendar"}
    assert all(0.0 <= value <= 1.0 for value in tick.components.values())
    assert tick.components["spread"] < 0.5, "a wide spread is visible as its own component"


def test_the_bucket_fallback_covers_the_whole_range() -> None:
    assert band_for(0.9) == "live"
    assert band_for(0.5) == "thin"
    assert band_for(0.0) == "dead"


def test_a_setup_appearing_is_announced_once() -> None:
    sentinel = engine()
    events = sentinel.observe("XAUUSD", flat_range(10))
    assert [kind for kind, _ in events] == ["born"]
    assert sentinel.observe("XAUUSD", flat_range(10)) == []


def test_a_high_impact_event_inside_the_guard_window_zeroes_the_calendar_component(
    tmp_path: Path,
) -> None:
    """The desk's honest answer right before NFP is `wait`, and the number has to say so."""
    feed = [{"title": "Non-Farm Payrolls", "country": "USD", "impact": "High",
             "date": "2023-11-14T22:20:00Z"}]
    cache = tmp_path / "ff.json"
    cache.write_text(json.dumps(feed), encoding="utf-8")

    calendar = CalendarCache(cache_path=cache, timezone="UTC", source="off",
                             fallback_path=None)
    calendar._events = None
    # Point the fallback at the same rows so no network is touched.
    fallback = tmp_path / "calendar.yaml"
    fallback.write_text("events:\n  - title: Non-Farm Payrolls\n    country: USD\n"
                        "    impact: High\n    date: '2023-11-14T22:20:00Z'\n", encoding="utf-8")
    calendar.fallback_path = fallback

    sentinel = engine(calendar=calendar)
    # 10 minutes before the 2023-11-14T22:20:00Z print.
    now_ms = 1_700_000_400_000 - 600_000
    tick = sentinel.tick(symbol="XAUUSD", bid=2000.0, ask=2000.2, now_ms=now_ms,
                         session_remaining_s=3600, locked=False, currencies=["USD"])
    assert tick.next_event == "Non-Farm Payrolls"
    assert 0 <= (tick.next_event_t_minus_s or 0) <= 900
    assert tick.components["calendar"] == 0.0


def test_a_symbol_basket_resolves_to_the_currencies_it_exposes_you_to() -> None:
    assert currencies_for(["XAUUSD"]) == ["USD", "XAU"]
    assert currencies_for(["EURUSD", "USDJPY"]) == ["EUR", "JPY", "USD"]


def test_news_age_is_none_until_news_has_ever_arrived() -> None:
    sentinel = engine()
    assert sentinel.tick(symbol="XAUUSD", bid=1, ask=1.1, now_ms=NOW,
                         session_remaining_s=60, locked=False).news_age_s is None

    sentinel.last_news_ms = NOW - 30_000
    assert sentinel.tick(symbol="XAUUSD", bid=1, ask=1.1, now_ms=NOW,
                         session_remaining_s=60, locked=False).news_age_s == pytest.approx(30.0)
