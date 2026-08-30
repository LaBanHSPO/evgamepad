"""The evening window, in the configured IANA zone.

DST is the reason this is not ``18 <= hour < 23``: the session must land at
18:00 local on the day it happens, not at a UTC offset frozen in October.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from ..config import SessionCfg

_DAYS = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}


def _parse_hhmm(value: str) -> time:
    hh, mm = value.split(":")
    return time(int(hh), int(mm))


@dataclass(frozen=True)
class Window:
    start_ms: int
    end_ms: int
    trading_day: str

    def contains(self, ms: int) -> bool:
        return self.start_ms <= ms < self.end_ms


class SessionWindow:
    def __init__(self, cfg: SessionCfg, tz: str) -> None:
        self.tz = ZoneInfo(tz)
        self.tz_name = tz
        self.days = frozenset(_DAYS[d] for d in cfg.days)
        self.start = _parse_hhmm(cfg.start)
        self.end = _parse_hhmm(cfg.end)
        #: A window written end <= start spans midnight and belongs to the day
        #: it opened on.
        self.spans_midnight = self.end <= self.start

    def local(self, ms: int) -> datetime:
        return datetime.fromtimestamp(ms / 1000, tz=self.tz)

    def _window_for(self, day: date) -> Window:
        start = datetime.combine(day, self.start, tzinfo=self.tz)
        end_day = day + timedelta(days=1) if self.spans_midnight else day
        end = datetime.combine(end_day, self.end, tzinfo=self.tz)
        return Window(
            start_ms=int(start.timestamp() * 1000),
            end_ms=int(end.timestamp() * 1000),
            trading_day=day.isoformat(),
        )

    def window_containing(self, ms: int) -> Window | None:
        """The session window this instant falls inside, or ``None``.

        Checks yesterday as well as today so an instant after midnight inside a
        midnight-spanning window is still attributed to the day it opened on.
        """
        today = self.local(ms).date()
        for day in (today, today - timedelta(days=1)):
            if day.weekday() not in self.days:
                continue
            window = self._window_for(day)
            if window.contains(ms):
                return window
        return None

    def is_open(self, ms: int) -> bool:
        return self.window_containing(ms) is not None

    def trading_day(self, ms: int) -> str:
        """The day a trade belongs to for journalling. Falls back to the local
        calendar date outside the window, so an out-of-session event is still
        filed somewhere sensible."""
        window = self.window_containing(ms)
        if window:
            return window.trading_day
        return self.local(ms).date().isoformat()

    def next_open(self, ms: int) -> int | None:
        """Start of the next session, searching a week ahead."""
        today = self.local(ms).date()
        for offset in range(0, 8):
            day = today + timedelta(days=offset)
            if day.weekday() not in self.days:
                continue
            window = self._window_for(day)
            if window.start_ms > ms:
                return window.start_ms
        return None
