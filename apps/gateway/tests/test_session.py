"""The evening window, across a DST boundary."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from apps.gateway.config import SessionCfg
from apps.gateway.risk.session import SessionWindow

TZ = "Asia/Ho_Chi_Minh"
CFG = SessionCfg(days=["sun", "mon", "tue", "wed", "thu", "fri"],
                 start="18:00", end="23:30")


def ms(y, m, d, hh, mm, tz=TZ) -> int:
    return int(datetime(y, m, d, hh, mm, tzinfo=ZoneInfo(tz)).timestamp() * 1000)


def test_inside_and_outside_the_window():
    w = SessionWindow(CFG, TZ)
    assert w.is_open(ms(2026, 8, 27, 19, 0))       # Thursday evening
    assert not w.is_open(ms(2026, 8, 27, 17, 59))
    assert not w.is_open(ms(2026, 8, 27, 23, 30))  # end is exclusive
    assert w.is_open(ms(2026, 8, 27, 23, 29))


def test_saturday_is_closed():
    w = SessionWindow(CFG, TZ)
    assert datetime.fromtimestamp(ms(2026, 8, 29, 20, 0) / 1000,
                                  tz=ZoneInfo(TZ)).weekday() == 5
    assert not w.is_open(ms(2026, 8, 29, 20, 0))


def test_the_window_follows_local_time_through_dst():
    """A DST zone must open at 18:00 local on both sides of the change, not at
    a UTC offset frozen in October."""
    tz = "Europe/London"
    w = SessionWindow(CFG, tz)
    before = ms(2026, 10, 23, 19, 0, tz)   # Friday, BST
    after = ms(2026, 10, 26, 19, 0, tz)    # Monday, GMT -- the clocks moved
    assert w.local(before).utcoffset() != w.local(after).utcoffset()
    assert w.is_open(before) and w.is_open(after)
    assert not w.is_open(ms(2026, 10, 26, 17, 30, tz))


def test_trading_day_is_the_local_date():
    w = SessionWindow(CFG, TZ)
    assert w.trading_day(ms(2026, 8, 27, 19, 0)) == "2026-08-27"
    assert w.trading_day(ms(2026, 8, 27, 10, 0)) == "2026-08-27"


def test_a_midnight_spanning_window_belongs_to_the_day_it_opened():
    cfg = SessionCfg(days=["mon"], start="22:00", end="02:00")
    w = SessionWindow(cfg, TZ)
    assert w.spans_midnight
    assert w.is_open(ms(2026, 8, 24, 23, 0))            # Monday night
    assert w.is_open(ms(2026, 8, 25, 1, 0))             # Tuesday 01:00
    assert w.trading_day(ms(2026, 8, 25, 1, 0)) == "2026-08-24"
    assert not w.is_open(ms(2026, 8, 25, 3, 0))


def test_next_open_finds_the_following_session():
    w = SessionWindow(CFG, TZ)
    nxt = w.next_open(ms(2026, 8, 29, 12, 0))  # Saturday
    assert nxt == ms(2026, 8, 30, 18, 0)       # Sunday evening
